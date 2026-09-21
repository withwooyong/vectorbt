"""Cohort exclusions are fixed before results and retain unresolved issues."""

from types import SimpleNamespace

import pandas as pd

from research.krx_lab.v3_scope import clean_cohort


def inputs():
    prices = pd.DataFrame([
        dict(date=day, instrument_id=str(i), open=100, high=101, low=99, close=100, volume=100000,
             adjusted_open=50, adjusted_high=50.5, adjusted_low=49.5, adjusted_close=50,
             raw_source_code="KRX_OPEN_API", adjusted_source_code="KIWOOM_REST")
        for day in pd.bdate_range("2019-01-01", periods=250) for i in range(5)
    ])
    issues = pd.DataFrame(columns=["issue_code", "decision", "instrument_id", "affected_scope"])
    events = pd.DataFrame(columns=["instrument_id", "event_type", "resolution_status", "effective_date"])
    adjustments = pd.DataFrame(columns=["stock_id", "trading_date", "explanation_status"])
    return SimpleNamespace(prices=prices, issues=issues, events=events), adjustments


def test_zero_volume_is_nontrade_but_missing_mark_and_invalid_traded_prices_exclude():
    data, adjustments = inputs()
    data.prices.loc[0, ["open", "high", "low", "volume"]] = 0
    data.prices.loc[1, "close"] = 0
    data.prices.loc[2, "high"] = 1
    data.prices.loc[3, "adjusted_close"] = float("nan")
    result = clean_cohort(data, adjustments)
    assert result["decision"] == "PASS"
    assert result["instrument_ids"] == ["0", "4"]
    assert result["excluded_instruments"] == 3


def test_historical_issue_source_mismatch_needs_proof_and_current_price_validation():
    data, adjustments = inputs()
    data.issues = pd.DataFrame([dict(issue_code="ADJUSTED_OHLC_ORDER_VIOLATION", decision="REJECT",
                                    instrument_id=None, affected_scope="DAILY_PRICE_ROW",
                                    details={"source_id": "PYKRX_KRX_UNADJUSTED",
                                             "adjusted_source_id": "PYKRX_NAVER_ADJUSTED"})])
    assert clean_cohort(data, adjustments)["decision"] == "PASS"
    data.prices.loc[0, "adjusted_source_code"] = "UNPROVEN"
    result = clean_cohort(data, adjustments)
    assert result["decision"] == "BLOCKED"
    assert len(result["unresolved_issues"]) == 1
    data.prices.loc[0, "adjusted_source_code"] = None
    assert clean_cohort(data, adjustments)["decision"] == "BLOCKED"


def test_only_supported_split_retained_and_unknown_issue_blocks_all_runs():
    data, adjustments = inputs()
    data.events = pd.DataFrame([
        dict(instrument_id="0", event_type="LISTED_SHARE_CHANGE", resolution_status="REFERENCE_FACT"),
        dict(instrument_id="1", event_type="DIVIDEND_OFF", resolution_status="REFERENCE_FACT"),
        dict(instrument_id="2", event_type="SPLIT", resolution_status="RESOLVED", quantity_ratio=2,
             settlement_policy="NONE", announced_at="2019-01-01", effective_date="2019-01-02",
             reference_price=50, sequence_no=1),
        dict(instrument_id="3", event_type="SPLIT", resolution_status="PARTIAL"),
    ])
    assert clean_cohort(data, adjustments)["instrument_ids"] == ["0", "2", "4"]
    data.issues = pd.DataFrame([dict(issue_code="UNKNOWN_ISSUE", decision="REJECT",
                                    instrument_id=None, affected_scope="ALL")])
    assert clean_cohort(data, adjustments)["decision"] == "BLOCKED"
