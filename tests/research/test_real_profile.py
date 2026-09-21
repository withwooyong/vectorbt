"""The REAL daily profile precheck cannot grant an execution path."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from research.krx_lab.contracts import ContractError
from research.krx_lab.real_profile import precheck_real_daily_profile


FIXTURE = Path(__file__).parent / "fixtures" / "contracts_v1" / "delivery.json"


def delivery():
    value = json.loads(FIXTURE.read_text(encoding="utf-8"))
    value["source_kind"] = "REAL"
    value["metadata"]["currency"] = "KRW"
    value["sources"][0]["historical_capture"] = "original"
    for section in ("instruments", "calendar", "market_profiles"):
        for row in value[section]:
            row["market"] = "KRX"
    return value


def codes(result):
    return {item["code"] for item in result["issues"]}


def test_complete_looking_c1_still_fails_closed_without_real_profile():
    value = delivery()
    before = deepcopy(value)
    result = precheck_real_daily_profile(value)
    assert value == before
    assert result["grade"] == "BLOCKED"
    assert result["admission"] == "PRECHECK_ONLY"
    assert result["execution_allowed"] is False
    assert "SYNTHETIC_PROFILE_IN_REAL" in codes(result)
    assert "COST_AND_MARKET_RULE_PROVENANCE_UNVERIFIED" in codes(result)
    assert "REAL_FILL_AND_LEDGER_UNVERIFIED" in codes(result)


def test_unknown_market_model_is_rejected_by_c1_before_precheck():
    value = delivery()
    value["market_profiles"][0]["model"] = "BROKER_DAILY_V1"
    with pytest.raises(ContractError, match="UNSUPPORTED_MARKET_PROFILE"):
        precheck_real_daily_profile(value)


def test_missing_status_price_and_factor_evidence_reported():
    value = delivery()
    value["statuses"].clear()
    value["prices"] = value["prices"][1:]
    value["prices"][0]["adjusted_close"] = 999
    value["events"].clear()
    result = precheck_real_daily_profile(value)
    assert {"MISSING_OR_AMBIGUOUS_STATUS", "ADJUSTED_PRICE_FACTOR_MISMATCH"} <= codes(result)
    # A missing status cannot establish which trading prices ought to exist.
    assert "NONUNIT_FACTOR_WITHOUT_EVENT" not in codes(result)
    assert result["execution_allowed"] is False


def test_missing_trading_price_and_factor_event_are_reported():
    value = delivery()
    value["prices"] = value["prices"][1:]
    value["events"].clear()
    value["prices"][0]["price_factor"] = 0.5
    result = precheck_real_daily_profile(value)
    assert {"TRADING_PRICE_MISSING", "ADJUSTED_PRICE_FACTOR_MISMATCH", "NONUNIT_FACTOR_WITHOUT_EVENT",
            "NONUNIT_FACTOR_EVENT_LINKAGE_UNVERIFIED"} <= codes(result)


def test_distant_event_does_not_establish_factor_lineage():
    value = delivery()
    value["events"] = value["events"][:1]
    value["events"][0]["effective_date"] = "2023-12-01"
    result = precheck_real_daily_profile(value)
    assert "NONUNIT_FACTOR_WITHOUT_EVENT" not in codes(result)
    assert "NONUNIT_FACTOR_EVENT_LINKAGE_UNVERIFIED" in codes(result)
    assert result["execution_allowed"] is False


def test_out_of_scope_and_missing_calendar_boundary():
    value = delivery()
    value["metadata"]["start"] = "2014-12-31"
    value["calendar"] = value["calendar"][1:]
    result = precheck_real_daily_profile(value)
    assert {"OUTSIDE_2015_2023_DAILY_SCOPE", "CALENDAR_BOUNDARY_MISSING",
            "PRICE_WITHOUT_OPEN_KRX_SESSION"} <= codes(result)


def test_invalid_c1_is_rejected_before_precheck():
    value = delivery()
    value["metadata"]["real_data_admitted"] = True
    with pytest.raises(ContractError, match="REAL_ADMISSION_NOT_GRANTED"):
        precheck_real_daily_profile(value)


def test_synthetic_source_never_promoted():
    value = delivery()
    value["source_kind"] = "SYNTHETIC"
    value["sources"][0]["historical_capture"] = "synthetic"
    result = precheck_real_daily_profile(value)
    assert "REAL_SOURCE_REQUIRED" in codes(result)
    assert result["execution_allowed"] is False
