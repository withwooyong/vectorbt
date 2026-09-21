"""Run reviewed, read-only audit SQL through the existing SSH connection; save JSON evidence."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time


TARGETS = {
    "core": ("kiwoom-db", "kiwoom", "kiwoom_db"),
    "inventory": ("ted-signal-db", "signal", "signal_db"),
    "auxiliary": ("ted-signal-db", "signal", "signal_db"),
}


def parse_output(raw):
    # PostgreSQL json_agg(composite) can insert physical newlines inside a JSON value.
    records = []
    decoder = json.JSONDecoder()
    offset = 0
    while offset < len(raw):
        if raw[offset].isspace():
            offset += 1
            continue
        record, offset = decoder.raw_decode(raw, offset)
        records.append(record)
    names = [row["check"] for row in records]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate check IDs")
    context = next(row["data"] for row in records if row["check"] == "context")
    if context["read_only"] != "on":
        raise ValueError("Read-only transaction was not confirmed")
    if not records or records[-1]["check"] != "audit_complete" or records[-1]["data"] is not True:
        raise ValueError("Missing audit completion marker")
    return records


def run(target, out, sql_path=None):
    source = Path(sql_path) if sql_path is not None else Path(__file__).with_name(f"{target}.sql")
    sql = source.read_text(encoding="utf-8-sig")
    if "READ ONLY" not in sql or "ON_ERROR_STOP on" not in sql:
        raise ValueError("Required SQL transaction/error guards missing")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    payload = sql.encode("utf-8")
    (out / "query.sql").write_bytes(payload)
    container, user, database = TARGETS[target]
    command = [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "home",
        f"docker exec -i -e PGCLIENTENCODING=UTF8 {container} "
        f"psql -X -q -A -t -v ON_ERROR_STOP=1 -U {user} -d {database}",
    ]
    receipt = {
        "target": target, "database": database,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "sql_sha256": hashlib.sha256(payload).hexdigest(),
        "status": "RUNNING", "holdout_prices_queried": False,
        "scope": "2015-01-02 through 2023-12-31 prices; current reference metadata separately labelled",
    }
    started = time.monotonic()
    try:
        with (out / "stdout.txt").open("wb") as stdout, (out / "stderr.txt").open("wb") as stderr:
            result = subprocess.run(command, input=payload, stdout=stdout, stderr=stderr, timeout=600, check=False)
        receipt["returncode"] = result.returncode
        if result.returncode:
            raise RuntimeError("SSH/psql failed; inspect saved stderr")
        records = parse_output((out / "stdout.txt").read_text(encoding="utf-8"))
        (out / "results.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt.update(status="COMPLETE", checks=len(records))
    except Exception as exc:
        receipt.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        receipt["elapsed_seconds"] = round(time.monotonic() - started, 3)
        receipt["finished_at"] = datetime.now(timezone.utc).isoformat()
        receipt["evidence_sha256"] = {
            name: hashlib.sha256((out / name).read_bytes()).hexdigest()
            for name in ("stdout.txt", "stderr.txt", "results.json") if (out / name).exists()
        }
        (out / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=TARGETS)
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory; existing directories are refused")
    parser.add_argument("--sql", type=Path, help="Reviewed read-only SQL; same development-period scope required")
    args = parser.parse_args()
    run(args.target, args.out, args.sql)
