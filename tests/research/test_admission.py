from copy import deepcopy
import json
from pathlib import Path

from research.krx_lab.admission import inspect_delivery


FIXTURES = Path(__file__).parent / "fixtures" / "contracts_v1"


def delivery():
    return json.loads((FIXTURES / "delivery.json").read_text(encoding="utf-8"))


def test_synthetic_fixture_is_inspected_but_not_execution_admitted():
    result = inspect_delivery(delivery(), FIXTURES)
    assert result["grade"] == "SYNTHETIC"
    assert result["admission"] == "INSPECTION_ONLY"
    assert result["issues"] == []


def test_file_hash_and_source_lineage_fail_closed(tmp_path):
    value = delivery()
    (tmp_path / "source.json").write_text('{"different": true}', encoding="utf-8")
    result = inspect_delivery(value, tmp_path)
    assert {issue["code"] for issue in result["issues"]} >= {"ARTIFACT_HASH_MISMATCH", "SOURCE_RAW_HASH_UNLINKED"}


def test_unknown_artifact_schema_is_explicitly_unverified():
    value = delivery()
    value["metadata"]["files"][0]["schema"] = "vendor-export-v9"
    result = inspect_delivery(value, FIXTURES)
    assert result["grade"] == "BLOCKED"
    assert "ARTIFACT_SCHEMA_UNVERIFIED" in {issue["code"] for issue in result["issues"]}


def test_effective_code_session_status_factor_and_event_timing_are_checked():
    value = delivery()
    value["prices"][0]["code"] = "WRONG"
    value["prices"][1]["adjusted_close"] = 99
    value["calendar"][2]["is_open"] = False
    value["calendar"][2]["opens_at"] = value["calendar"][2]["closes_at"] = None
    value["events"][0]["announced_at"] = "2023-01-03T10:00:00+09:00"
    result = inspect_delivery(value, FIXTURES)
    codes = {issue["code"] for issue in result["issues"]}
    assert {"INVALID_EFFECTIVE_CODE", "ADJUSTED_PRICE_FACTOR_MISMATCH", "PRICE_OUTSIDE_OPEN_SESSION",
            "EVENT_ANNOUNCED_AFTER_EFFECTIVE_OPEN"} <= codes


def test_halted_prices_and_unresolved_source_time_are_blocked():
    value = delivery()
    value["statuses"][0].update(status="HALTED")
    value["sources"][0].update(time_precision="unknown", published_at=None, unavailable_reason="missing")
    result = inspect_delivery(value, FIXTURES)
    codes = {issue["code"] for issue in result["issues"]}
    assert {"HALTED_NONZERO_VOLUME", "SOURCE_TIME_UNRESOLVED"} <= codes


def test_halted_mark_and_expected_trading_profile_coverage_are_classified():
    value = delivery()
    value["statuses"][0].update(status="HALTED")
    for price in value["prices"]:
        price["volume"] = 0
        for field in ("open", "high", "low", "close", "adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close"):
            price[field] = 0
    result = inspect_delivery(value, FIXTURES)
    assert result["grade"] == "SYNTHETIC"  # HALTED zero-volume marks are classified, not trading OHLC.

    value = delivery()
    value["prices"].pop()
    value["market_profiles"][0]["effective_to"] = "2023-01-04"
    result = inspect_delivery(value, FIXTURES)
    codes = {issue["code"] for issue in result["issues"]}
    assert {"MISSING_TRADING_PRICE", "MARKET_PROFILE_COVERAGE_INVALID"} <= codes


def test_revision_link_and_changed_keys_are_reported():
    previous = delivery()
    current = deepcopy(previous)
    current["metadata"].update(revision="2", previous_revision="1")
    current["prices"][0]["close"] = 51
    current["prices"][0]["adjusted_close"] = 25.5
    current["prices"][0]["high"] = 51
    current["prices"][0]["adjusted_high"] = 25.5
    result = inspect_delivery(current, FIXTURES, previous)
    assert result["grade"] == "SYNTHETIC"
    assert result["revision_summary"]["previous_revision"] == "1"
    assert "('SYN-ID-001', '2023-01-02')" in result["revision_summary"]["changed_keys"]["prices"]


def test_code_reuse_source_time_and_revision_reuse_fail_closed():
    previous = delivery()
    value = deepcopy(previous)
    value["instruments"].append({**value["instruments"][0], "instrument_id": "SYN-ID-002", "effective_from": "2023-01-03"})
    value["sources"][0]["published_at"] = "2023-01-02T10:00:00+09:00"
    value["sources"][0]["captured_at"] = "2023-01-02T11:00:00+09:00"
    value["metadata"]["previous_revision"] = "1"
    result = inspect_delivery(value, FIXTURES, previous)
    codes = {issue["code"] for issue in result["issues"]}
    assert {"OVERLAPPING_EFFECTIVE_INTERVAL", "EVENT_ANNOUNCEMENT_BEFORE_SOURCE", "REVISION_NOT_ADVANCED"} <= codes


def test_real_delivery_stays_blocked_after_clean_inspection():
    value = delivery()
    value["source_kind"] = "REAL"
    value["sources"][0]["historical_capture"] = "original"
    result = inspect_delivery(value, FIXTURES)
    assert result["grade"] == "BLOCKED"
    assert result["admission"] == "INSPECTION_ONLY"


def test_missing_calendar_and_price_together_do_not_hide_missing_session():
    from pathlib import Path
    from research.krx_lab.io import read_json
    root = Path(__file__).parent / "fixtures/contracts_v1"
    delivery = read_json(root / "delivery.json")
    delivery["calendar"] = [row for row in delivery["calendar"] if row["date"] != "2023-01-02"]
    delivery["prices"] = [row for row in delivery["prices"] if row["date"] != "2023-01-02"]
    report = inspect_delivery(delivery, root)
    assert report["grade"] == "BLOCKED"
    assert any(issue["code"] == "CALENDAR_DATE_MISSING" for issue in report["issues"])
