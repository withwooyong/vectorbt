"""Collect bounded read-only price samples; reuse the previous audit output validator."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parent
PARSER_PATH = ROOT.parent / "table-audit-2026-09-13" / "run_audit.py"
SPEC = importlib.util.spec_from_file_location("prior_table_audit", PARSER_PATH)
PRIOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRIOR)


def collect(out):
    payload = (ROOT / "samples.sql").read_text(encoding="utf-8-sig").encode("utf-8")
    out.mkdir(parents=True, exist_ok=False)
    (out / "query.sql").write_bytes(payload)
    receipt = {
        "started_at": datetime.now(timezone.utc).isoformat(), "status": "RUNNING",
        "source": "ssh home / kiwoom-db / kiwoom_db", "holdout_prices_queried": False,
        "sql_sha256": hashlib.sha256(payload).hexdigest(),
        "parser_sha256": hashlib.sha256(PARSER_PATH.read_bytes()).hexdigest(),
    }
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "home",
               "docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db "
               "psql -X -q -A -t -v ON_ERROR_STOP=1 -U kiwoom -d kiwoom_db"]
    started = time.monotonic()
    try:
        with (out / "stdout.txt").open("wb") as stdout, (out / "stderr.txt").open("wb") as stderr:
            result = subprocess.run(command, input=payload, stdout=stdout, stderr=stderr, timeout=300, check=False)
        receipt["returncode"] = result.returncode
        if result.returncode:
            raise RuntimeError("SSH/psql failed; inspect saved stderr")
        records = PRIOR.parse_output((out / "stdout.txt").read_text(encoding="utf-8"))
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
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory")
    args = parser.parse_args()
    collect(args.out)
