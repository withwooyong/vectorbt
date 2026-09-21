"""Reconcile saved audit evidence without querying the database again."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from run_audit import parse_output


ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify():
    records = {}
    for name in ("inventory-v2", "auxiliary", "core"):
        folder = ROOT / "evidence" / name
        receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
        require(receipt["status"] == "COMPLETE" and receipt["returncode"] == 0, f"Failed run: {name}")
        require(not receipt["holdout_prices_queried"], f"Holdout scope: {name}")
        query = (folder / "query.sql").read_bytes()
        require(hashlib.sha256(query).hexdigest() == receipt["sql_sha256"], f"Query hash: {name}")
        source = (ROOT / f"{receipt['target']}.sql").read_text(encoding="utf-8-sig").encode("utf-8")
        require(query == source, f"Executed SQL differs from current source: {name}")
        for file, expected in receipt["evidence_sha256"].items():
            require(hashlib.sha256((folder / file).read_bytes()).hexdigest() == expected, f"Evidence hash: {name}/{file}")
        parsed = parse_output((folder / "stdout.txt").read_text(encoding="utf-8"))
        require(parsed == json.loads((folder / "results.json").read_text(encoding="utf-8")), f"Parsed output: {name}")
        require(len(parsed) == receipt["checks"], f"Check count: {name}")
        records[name] = {row["check"]: row["data"] for row in parsed}

    core = records["core"]
    require(core["context"]["date_from"] == "2015-01-02", "Start scope")
    require(core["context"]["date_to"] == "2023-12-31", "End scope")
    profile = core["price_profile_before_join"]
    total, = [r for r in profile if r["grouping_mask"] == 7]
    vendors = [r for r in profile if r["grouping_mask"] == 1]
    years = [r for r in profile if r["grouping_mask"] == 0]
    counts = [k for k, v in total.items() if isinstance(v, int) and k not in ("grouping_mask", "stock_ids")]
    for column in counts:
        require(total[column] == sum(r[column] for r in vendors), f"Total/vendor: {column}")
        require(total[column] == sum(r[column] for r in years), f"Total/year: {column}")
    for row in profile:
        require("2015-01-02" <= row["first_date"] <= row["last_date"] <= "2023-12-31", "Observed dates")
        for column in counts:
            require(0 <= row[column] <= row["rows"], f"Count bounds: {column}")
    for vendor in vendors:
        matching = [r for r in years if (r["data_vendor"], r["adjusted"]) == (vendor["data_vendor"], vendor["adjusted"])]
        for column in counts:
            require(vendor[column] == sum(r[column] for r in matching), f"Vendor/year: {column}")
    relation = core["price_stock_relationships"]
    require(total["rows"] == relation["summary"]["joined_rows"], "Join changed row count")
    require(relation["summary"]["orphan_rows"] == 0, "Orphan price rows found")
    require(total["stock_ids"] == core["observed_calendar_internal_gap_candidates"]["stock_adjustment_groups"],
            "Current fixture must have one adjustment state per stock")
    require(all(row["adjusted"] is True for row in vendors), "Unexpected unadjusted data; update admission review")
    require(total["stock_ids"] == sum(r["stock_ids"] for r in vendors), "Vendor stock-count overlap")
    require(relation["mixed_vendor_stock_adjustment_groups"] == 0, "Within-stock vendor mixing")

    baseline = json.loads((ROOT.parent / "admission-audit-2026-09-13" / "live-check.json").read_text(encoding="utf-8"))
    prior = baseline["rows_by_vendor"]
    comparison = {
        "vendor_rows_equal": {r["data_vendor"]: r["rows"] for r in vendors}
        == {r["data_vendor"]: r["rows"] for r in prior},
        "invalid_ohlcv_count_equal": relation["summary"]["invalid_ohlcv_rows"] == sum(r["invalid_ohlcv"] for r in prior),
        "zero_close_count_equal": total["zero_close"] == sum(r["zero_close"] for r in prior),
        "row_level_equality_checked": False,
    }
    aux = records["auxiliary"]
    event_rows = aux["event_availability"]["development_decision_rows"]
    require(event_rows == sum(r["rows"] for r in aux["development_events"]), "Event type total")
    require(event_rows == aux["event_links"]["rows"], "Event join amplification")
    require(aux["current_stock"]["rows"] == aux["current_stock_mapping"]["stock_rows"], "Stock mapping amplification")
    require(aux["current_stock"]["active"] + aux["current_stock"]["inactive"] == aux["current_stock"]["rows"],
            "Active/inactive total")
    require(aux["disclosure_availability"]["development_rows"] == aux["development_disclosures"]["rows"],
            "Disclosure scope totals")
    return {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "verification_status": "PASS", "data_admission": "BLOCKED",
        "successful_runs": 3, "sql_result_records": sum(len(r) for r in records.values()),
        "price_rows": total["rows"], "price_stock_ids": total["stock_ids"],
        "invalid_ohlcv_rows": relation["summary"]["invalid_ohlcv_rows"],
        "invalid_ohlcv_percent": round(relation["summary"]["invalid_ohlcv_rows"] / total["rows"] * 100, 4),
        "prior_aggregate_comparison": comparison,
        "limits": ["This checks saved evidence consistency, not market-source accuracy or complete data admission",
                   "Read-only and date scope are checked in reviewed SQL; receipt flags alone do not enforce scope",
                   "No row-by-row cross-database or snapshot equivalence was tested"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="Optional new JSON result path")
    args = parser.parse_args()
    result = json.dumps(verify(), ensure_ascii=False, indent=2) + "\n"
    if args.out:
        with args.out.open("x", encoding="utf-8") as file:
            file.write(result)
    print(result)
