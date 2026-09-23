"""Recheck sealed local benchmark parts and read-only KRX source lineage.

Usage: python verify_benchmark.py --snapshot <v3-raw-dir> --typed <v3-typed-dir>
       --out <new-or-replaceable-evidence.json>

Only aggregate provenance and four boundary source-record references are saved.
The SQL is sent through the existing SSH configuration; no credentials or raw
payload bodies are read or printed.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess

import pandas as pd


SQL = Path(__file__).with_name("benchmark_provenance.sql")
REMOTE = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "home",
          "docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db "
          "psql -X -q -U kiwoom -d kiwoom_db -At"]
REVISION_ID = "0eeed564-0b89-587c-b8f9-d8eea981bb9e"
REVISION_SHA256 = "e95066aa516971ff63e4d6da19a7639b0eab18783eca159a428dc268a2bd13c2"


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def part(manifest, kind):
    matches = [item for item in manifest["parts"] if item["member_kind"] == kind]
    require(len(matches) == 1, f"Expected one {kind} part")
    return matches[0]


_CORE = ("benchmark_code", "trading_date", "source_record_id", "open_value",
         "high_value", "low_value", "close_value")


def rows_digest(rows, fields):
    """Canonical digest over ordered compact observations, independent of JSON key order."""
    value = hashlib.sha256()
    for row in sorted(rows, key=lambda item: (item["benchmark_code"], item["trading_date"])):
        line = json.dumps([str(row[field]) for field in fields], ensure_ascii=False,
                          separators=(",", ":"))
        value.update(line.encode("utf-8") + b"\n")
    return value.hexdigest()


def verify(snapshot: Path, typed: Path):
    source_manifest_path = snapshot / "manifest.json"
    typed_manifest_path = typed / "manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    typed_manifest = json.loads(typed_manifest_path.read_text(encoding="utf-8"))
    require(source_manifest["status"] == typed_manifest["status"] == "COMPLETE", "Incomplete local snapshots")
    require(source_manifest["revision_id"] == typed_manifest["revision_id"] == REVISION_ID,
            "Revision id mismatch")
    require(source_manifest["revision_content_sha256"] == typed_manifest["revision_content_sha256"]
            == REVISION_SHA256, "Revision hash mismatch")
    require(typed_manifest["source_manifest_sha256"] == digest(source_manifest_path),
            "Typed snapshot does not pin this raw snapshot")
    raw_part = part(source_manifest, "BENCHMARK")
    typed_part = part(typed_manifest, "BENCHMARK")
    require(raw_part["sha256"] == digest(snapshot / raw_part["file"]), "Raw benchmark part hash mismatch")
    require(typed_part["sha256"] == digest(typed / typed_part["file"]), "Typed benchmark part hash mismatch")
    require(typed_part["source_sha256"] == raw_part["sha256"], "Typed benchmark source hash mismatch")
    raw = [json.loads(value, parse_float=Decimal) for value in
           pd.read_parquet(snapshot / raw_part["file"])["pg_json"]]
    frame = pd.read_parquet(typed / typed_part["file"])
    require(len(raw) == len(frame) == raw_part["rows"] == typed_part["rows"] == 4918,
            "Benchmark row count mismatch")
    source = {(row["benchmark_code"], row["trading_date"]): row for row in raw}
    require(len(source) == len(raw), "Duplicate raw benchmark date/code")
    for row in frame.itertuples(index=False):
        key = (row.benchmark_code, row.trading_date)
        require(key in source, f"Typed benchmark key absent from raw snapshot: {key}")
        original = source[key]
        require(row.source_record_id == original["source_record_id"], "Source record id changed")
        for name in ("open_value", "high_value", "low_value", "close_value"):
            require(getattr(row, name) == original[name], f"Raw/typed benchmark {name} mismatch: {key}")
    calendar_part = part(typed_manifest, "CALENDAR")
    require(calendar_part["sha256"] == digest(typed / calendar_part["file"]),
            "Typed calendar part hash mismatch")
    open_dates = set(pd.read_parquet(typed / calendar_part["file"])
                     .loc[lambda value: value.market.eq("KRX") & value.is_open, "trading_date"])
    actual = {(row.benchmark_code, row.trading_date) for row in frame.itertuples(index=False)}
    expected = {(code, day) for code in ("KOSPI", "KOSDAQ") for day in open_dates}
    require(actual == expected, "Local benchmark does not exactly cover KRX open sessions")
    require(all(min(row.open_value, row.high_value, row.low_value, row.close_value) > 0
                and row.high_value >= max(row.open_value, row.close_value, row.low_value)
                and row.low_value <= min(row.open_value, row.close_value, row.high_value)
                for row in frame.itertuples(index=False)), "Invalid local benchmark OHLC")
    member = next(item for item in source_manifest["members"] if item["member_kind"] == "BENCHMARK")
    require(member["row_count"] == len(frame), "Sealed member row count mismatch")
    payload_part = part(typed_manifest, "SOURCE_PAYLOAD")
    require(payload_part["sha256"] == digest(typed / payload_part["file"]),
            "Typed source payload part hash mismatch")
    payloads = pd.read_parquet(typed / payload_part["file"])
    payload_hashes = set(payloads["payload_sha256"])

    sql = SQL.read_text(encoding="utf-8")
    completed = subprocess.run(REMOTE, input=sql, text=True, capture_output=True,
                               encoding="utf-8", timeout=120, check=True)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    require(len(lines) == 1, "Expected one JSON result from read-only query")
    query = json.loads(lines[0], parse_float=Decimal)
    require(query["revision"]["revision_id"] == REVISION_ID
            and query["revision"]["status"] == "SEALED"
            and query["revision"]["content_sha256"] == REVISION_SHA256,
            "Operational revision changed")
    require(query["benchmark_member"]["content_sha256"] == member["content_sha256"]
            and query["benchmark_member"]["row_count"] == len(frame),
            "Operational benchmark member changed")
    require(query["calendar_open_sessions"] == len(open_dates)
            and query["missing_calendar_pairs"] == query["extra_noncalendar_pairs"] == 0,
            "Operational benchmark calendar gap")
    groups = query["groups"]
    require(len(groups) == 2 and {group["benchmark_code"] for group in groups} == {"KOSPI", "KOSDAQ"},
            "Unexpected operational benchmark groups")
    for group in groups:
        require(group["rows"] == group["distinct_dates"] == group["distinct_source_records"] == len(open_dates),
                "Benchmark date/source count mismatch")
        require(group["source_code"] == "KRX_OPEN_API" and group["authority_kind"] == "PRIMARY"
                and group["base_url"] == "https://openapi.krx.co.kr"
                and group["endpoint"] == f"idx/{group['benchmark_code'].lower()}_dd_trd"
                and group["response_status"] == 200 and group["entity_kind"] == "BENCHMARK_DAILY",
                "Benchmark is not the expected official index feed")
        for field in ("missing_lineage", "missing_available_at", "invalid_prices", "invalid_ohlc",
                      "source_ohlc_mismatches", "source_identity_mismatches"):
            require(group[field] == 0, f"Benchmark {field} is nonzero")
        require(group["capture_kind"] == "new_observation" and group["historical_capture"] is False
                and group["missing_published_at"] == group["rows"],
                "Retrospective-capture limitation changed")
    remote_rows = query["benchmark_rows"]
    remote = {(row["benchmark_code"], row["trading_date"]): row for row in remote_rows}
    require(len(remote_rows) == len(remote) == len(source) == 4918
            and set(remote) == set(source), "Local/operational benchmark keys differ")
    for key, row in remote.items():
        original = source[key]
        for field in _CORE:
            require(row[field] == original[field], f"Local/operational benchmark {field} differs: {key}")
        require(row["payload_sha256"] in payload_hashes,
                f"Operational payload hash absent from sealed local payload member: {key}")
    local_core_sha = rows_digest(raw, _CORE)
    remote_core_sha = rows_digest(remote_rows, _CORE)
    require(local_core_sha == remote_core_sha, "Local/operational benchmark digest differs")
    remote_lineage_sha = rows_digest(remote_rows, (*_CORE, "payload_sha256"))
    for sample in query["samples"]:
        key = (sample["benchmark_code"], sample["trading_date"])
        require(key in source and sample["source_record_id"] == source[key]["source_record_id"]
                and sample["close_value"] == source[key]["close_value"]
                and sample["payload_sha256"] in payload_hashes,
                f"Source lineage sample mismatch: {key}")

    return {
        "status": "PASS_RETROSPECTIVE",
        "scope": "KOSPI_KOSDAQ_OFFICIAL_INDEX_2014_2023",
        "revision_id": REVISION_ID,
        "revision_content_sha256": REVISION_SHA256,
        "source_manifest_hash": digest(source_manifest_path),
        "typed_manifest_hash": digest(typed_manifest_path),
        "sql_sha256": digest(SQL),
        "source_benchmark_part": {"file": raw_part["file"], "sha256": raw_part["sha256"]},
        "typed_benchmark_part": {"file": typed_part["file"], "sha256": typed_part["sha256"]},
        "benchmark_member_content_sha256": member["content_sha256"],
        "content_checks": {"rows": len(frame), "codes": ["KOSDAQ", "KOSPI"],
                           "open_sessions_per_code": len(open_dates),
                           "raw_typed_value_mismatches": 0,
                           "local_remote_compared_rows": len(remote_rows),
                           "local_core_sha256": local_core_sha,
                           "remote_core_sha256": remote_core_sha,
                           "remote_lineage_sha256": remote_lineage_sha,
                           "remote_payload_hashes_in_local_member": len(remote_rows),
                           "local_calendar_missing_pairs": 0,
                           "local_calendar_extra_pairs": 0,
                           "operational_calendar_missing_pairs": query["missing_calendar_pairs"],
                           "operational_calendar_extra_pairs": query["extra_noncalendar_pairs"]},
        "lineage_summary": groups,
        "lineage_samples": query["samples"],
        "limitation": ("Official KRX historical index observations were downloaded in 2026 as "
                       "new_observation; historical_capture=false and published_at is absent. "
                       "This validates a bounded retrospective experiment, not archived point-in-time vintage."),
        "execution_note": "Use the signal day's index close only for the next session's entry decision.",
        "query_mode": "REPEATABLE_READ_READ_ONLY_ROLLBACK",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--typed", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = verify(args.snapshot, args.typed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"{result['status']}: {result['content_checks']['rows']} benchmark rows")


if __name__ == "__main__":
    main()
