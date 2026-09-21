"""Build a reproducible source-comparison request from saved, verified DB samples; no network calls."""

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def build(evidence):
    receipt = json.loads((evidence / "receipt.json").read_text(encoding="utf-8"))
    if receipt["status"] != "COMPLETE" or receipt["returncode"] != 0 or receipt["holdout_prices_queried"]:
        raise ValueError("Sample audit did not complete within the permitted scope")
    for name, expected in receipt["evidence_sha256"].items():
        if hashlib.sha256((evidence / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"Evidence hash mismatch: {name}")
    if hashlib.sha256((evidence / "query.sql").read_bytes()).hexdigest() != receipt["sql_sha256"]:
        raise ValueError("SQL hash mismatch")
    results = json.loads((evidence / "results.json").read_text(encoding="utf-8"))
    checks = {item["check"]: item["data"] for item in results}
    if len(checks) != len(results) or checks["context"]["read_only"] != "on" or checks["audit_complete"] is not True:
        raise ValueError("Result contract mismatch")
    rows = []
    seen = set()
    for check in ("krx_fixed_samples", "kiwoom_transition_samples"):
        for sample in checks[check]:
            if not "2015-01-02" <= sample["trading_date"] <= "2023-12-31" or sample["adjusted"] is not True:
                raise ValueError("Sample outside the approved price scope")
            sample_id = f"{sample['data_vendor']}-{sample['stock_code']}-{sample['trading_date']}-adjusted"
            if sample_id in seen:
                raise ValueError("Duplicate sample key")
            seen.add(sample_id)
            canonical = json.dumps(sample, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            rows.append({"sample_id": sample_id, "reason": sample.get("anomaly", "KIWOOM_ZERO_POSITIVE_TRANSITION"),
                         "db_row": sample, "db_row_sha256": hashlib.sha256(canonical).hexdigest()})
    return {
        "schema_version": "source-comparison-request-v1", "request_only": True, "transmitted": False,
        "scope": {"start": "2015-01-02", "end": "2023-12-31", "holdout_prices_included": False},
        "evidence_results_sha256": receipt["evidence_sha256"]["results.json"],
        "sample_count": len(rows), "samples": rows,
        "selection_rule": "KRX: first three (stock_id,date) per anomaly; KIWOOM: +/-3 calendar days around zero/positive transitions and first bar",
        "selection_limit": "Deterministic diagnostic samples, not a statistically representative sample of all anomalies",
        "required_per_sample": [
            "original_capture_or_new_observation_label", "source_endpoint_and_request_parameters_without_credentials",
            "captured_at_with_timezone", "original_response_file_and_sha256", "raw_unadjusted_and_adjusted_values",
            "pre_transform_dataframe_values_and_dtypes", "price_volume_amount_units",
            "adjustment_definition_and_factors", "rounding_and_nontrading_conventions",
            "ingestion_run_id_commit_image_package_versions", "mapped_db_row_and_comparison_result",
            "unavailable_fields_and_reason",
        ],
        "acceptance": [
            "Every requested key has evidence or an explicit unavailable reason",
            "Replaying the supplied transform from original values reproduces the saved row or records the exact mismatch",
            "New observations never replace missing historical capture evidence",
            "Nontrading/status explanations require dated source evidence",
            "A sample explanation does not certify the entire dataset; affected keys and revision scope must be enumerated",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=ROOT / "evidence" / "samples")
    parser.add_argument("--out", type=Path, required=True, help="New request JSON file; existing files are refused")
    args = parser.parse_args()
    document = build(args.evidence)
    with args.out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sample_count": document["sample_count"], "output": str(args.out)}, ensure_ascii=False))
