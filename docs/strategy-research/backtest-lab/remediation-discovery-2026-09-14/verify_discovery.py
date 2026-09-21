"""Verify saved sample/log evidence, generated requests and local document links without network access."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from build_sample_request import build
from collect_samples import PRIOR


ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify():
    evidence = ROOT / "evidence" / "samples"
    raw = (evidence / "stdout.txt").read_text(encoding="utf-8")
    require(PRIOR.parse_output(raw) == json.loads((evidence / "results.json").read_text(encoding="utf-8")),
            "Sample output/JSON mismatch")
    require((ROOT / "samples.sql").read_text(encoding="utf-8-sig") ==
            (evidence / "query.sql").read_text(encoding="utf-8"), "Sample SQL source mismatch")
    request = build(evidence)
    require(request == json.loads((ROOT / "sample-request.json").read_text(encoding="utf-8")), "Request mismatch")
    server_checks = 0
    for folder in (ROOT / "evidence").iterdir():
        if folder.name == "samples":
            continue
        receipts = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
        for receipt in receipts:
            require(receipt["returncode"] == 0, f"Failed metadata command: {receipt['name']}")
            for stream in ("stdout", "stderr"):
                content = (folder / f"{receipt['name']}.{stream}.txt").read_bytes()
                require(hashlib.sha256(content).hexdigest() == receipt[f"{stream}_sha256"], "Metadata hash mismatch")
            server_checks += 1
    log_path = ROOT / "evidence/container-log-archive/container_backfill_log_full.stdout.txt"
    log_bytes = log_path.read_bytes()
    log_hash = hashlib.sha256(log_bytes).hexdigest()
    metadata = (ROOT / "evidence/container-original-log/container_backfill_log.stdout.txt").read_text(encoding="utf-8")
    require(log_hash + "  /tmp/backfill_delisted.log" in metadata, "Archived log differs from remote hash")
    log = log_bytes.decode("utf-8")
    rows = re.findall(r"적재 완료 stock_code=([^ ]+) rows=(\d+)", log)
    summary_stocks = int(re.search(r"적재한 종목\s*:\s*(\d+)", log)[1])
    summary_rows = int(re.search(r"적재한 행\s*:\s*(\d+)", log)[1])
    require(len(rows) == summary_stocks and sum(int(row[1]) for row in rows) == summary_rows, "Log totals differ")
    require(log.rstrip().endswith("EXIT=0"), "Missing successful exit marker")
    link_count = 0
    for doc in ROOT.glob("*.md"):
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if target.startswith(("https://", "http://", "#")):
                continue
            require((doc.parent / target.split("#")[0]).exists(), f"Broken local link: {doc.name}: {target}")
            link_count += 1
    json_count = 0
    for file in ROOT.rglob("*.json"):
        if file.name == "verification.json":
            continue
        json.loads(file.read_text(encoding="utf-8"))
        json_count += 1
    return {
        "verified_at": datetime.now(timezone.utc).isoformat(), "verification_status": "PASS",
        "data_admission": "BLOCKED", "sample_rows": len(request["samples"]),
        "server_metadata_commands": server_checks, "archived_log_bytes": len(log_bytes), "archived_log_sha256": log_hash,
        "log_stocks": summary_stocks, "log_ingested_rows": summary_rows,
        "local_links_checked": link_count, "json_files_parsed": json_count,
        "limits": ["Saved-evidence consistency only; not an independent historical source or execution identity proof",
                   "The original log covers a broader ingestion period than the 2015-2023 price audit",
                   "External documentation access is recorded by the source review, not re-fetched by this verifier"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Optional new output JSON path")
    args = parser.parse_args()
    content = json.dumps(verify(), ensure_ascii=False, indent=2) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8") as file:
            file.write(content)
    print(content)
