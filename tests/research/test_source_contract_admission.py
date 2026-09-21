from __future__ import annotations

import pandas as pd
import pytest

from research.krx_lab.source_contract_admission import (
    DATASET_NAME,
    REVISION_ID,
    REVISION_LABEL,
    REVISION_SHA256,
    SourceContractAdmissionError,
    profile_source_contract,
)


def manifest():
    return {
        "dataset_name": DATASET_NAME,
        "revision_id": REVISION_ID,
        "revision_label": REVISION_LABEL,
        "revision_content_sha256": REVISION_SHA256,
        "revision_status": "SEALED",
        "period_start": "2014-01-01",
        "period_end": "2023-12-31",
    }


def tables(*, invalid_pair=False, partial=False, factor=False):
    days = pd.bdate_range("2014-01-01", periods=380)
    prices = []
    for stock_id, code in ((1, "000001"), (2, "000002")):
        for index, day in enumerate(days):
            for adjusted in (False, True):
                if invalid_pair and stock_id == 2 and index == 300 and adjusted:
                    continue
                prices.append({"stock_id": stock_id, "stock_code": code, "trading_date": day,
                               "adjusted": adjusted, "open_price": 100, "high_price": 110,
                               "low_price": 90, "close_price": 105})
    calendar_days = pd.date_range(days.min(), days.max(), freq="D")
    return {
        "PRICE": pd.DataFrame(prices),
        "UNIVERSE": pd.DataFrame([
            {"stock_id": 1, "stock_code": "000001", "security_type": "COMMON_STOCK",
             "valid_from": days.min(), "valid_to": days.max()},
            {"stock_id": 2, "stock_code": "000002", "security_type": "COMMON_STOCK",
             "valid_from": days.min(), "valid_to": days.max()},
        ]),
        "CALENDAR": pd.DataFrame({"market": "KRX", "trading_date": calendar_days,
                                  "is_open": calendar_days.isin(days)}),
        "STATUS": pd.DataFrame(columns=["stock_id", "trading_date", "daily_state"]),
        "CORPORATE_ACTION": pd.DataFrame([
            {"stock_id": 2, "resolution_status": "PARTIAL" if partial else "RESOLVED"}
        ]),
        "ADJUSTMENT": pd.DataFrame([
            {"stock_id": 2, "explanation_status": "OBSERVED_VENDOR_FACTOR" if factor else "EXPLAINED"}
        ]),
        "EXECUTION_RULE": pd.DataFrame([{"rule_kind": "SETTLEMENT"}]),
        "ADMISSION_ISSUE": pd.DataFrame(columns=["issue_code", "severity", "affected_scope", "decision"]),
    }


def test_profiles_conservative_scope_without_sector_requirement():
    result = profile_source_contract(tables(), manifest())
    assert result["decision"] == "CONDITIONALLY_ADMITTED"
    assert result["execution_allowed"] is False
    assert len(result["scope"]) == 2
    assert result["execution_policy"] == {"sector_cap": None, "sector_data_used": False}
    assert "POINT_IN_TIME_SECTOR_UNAVAILABLE" in result["limitations"]


@pytest.mark.parametrize("kwargs,reason", [
    ({"invalid_pair": True}, "RAW_ADJUSTED_PAIR_MISSING"),
    ({"partial": True}, "CORPORATE_ACTION_PARTIAL"),
    ({"factor": True}, "UNEXPLAINED_VENDOR_FACTOR"),
])
def test_excludes_whole_instrument_for_unresolved_source_fact(kwargs, reason):
    result = profile_source_contract(tables(**kwargs), manifest())
    assert [row["code"] for row in result["scope"]] == ["000001"]
    excluded = next(row for row in result["exclusions"] if row["code"] == "000002")
    assert reason in excluded["reasons"]


def test_halt_explains_missing_price_pair():
    value = tables(invalid_pair=True)
    missing_day = pd.bdate_range("2014-01-01", periods=380)[300]
    value["PRICE"] = value["PRICE"].loc[
        ~((value["PRICE"]["stock_id"] == 2) & (value["PRICE"]["trading_date"] == missing_day))
    ]
    value["STATUS"] = pd.DataFrame([{"stock_id": 2, "trading_date": missing_day, "daily_state": "HALTED"}])
    result = profile_source_contract(value, manifest())
    assert {row["code"] for row in result["scope"]} == {"000001", "000002"}


def test_stock_scoped_reject_is_applied():
    value = tables()
    value["ADMISSION_ISSUE"] = pd.DataFrame([{
        "issue_code": "ADJUSTED_PRICE_UNAVAILABLE", "severity": "ERROR",
        "affected_scope": "stock:000002", "decision": "REJECT",
    }])
    result = profile_source_contract(value, manifest())
    assert [row["code"] for row in result["scope"]] == ["000001"]


def test_revision_mismatch_fails_closed():
    bad = manifest()
    bad["revision_label"] = "2014-2023-v2"
    with pytest.raises(SourceContractAdmissionError, match="REVISION_BINDING_MISMATCH"):
        profile_source_contract(tables(), bad)


def test_missing_relation_fails_closed():
    value = tables()
    del value["STATUS"]
    with pytest.raises(SourceContractAdmissionError, match="MISSING_RELATIONS"):
        profile_source_contract(value, manifest())


def test_duplicate_price_key_fails_closed():
    value = tables()
    value["PRICE"] = pd.concat([value["PRICE"], value["PRICE"].iloc[[0]]], ignore_index=True)
    with pytest.raises(SourceContractAdmissionError, match="DUPLICATE_PRICE_KEY"):
        profile_source_contract(value, manifest())
