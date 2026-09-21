from __future__ import annotations

import numpy as np
import pandas as pd

from research.krx_lab.strategies import V2_ENTRY_IDS
from research.krx_lab.v3_inputs import prepare_v3_inputs


def _tables(*, missing_raw=False, issue=False):
    days = pd.bdate_range("2023-01-02", periods=252)
    prices = []
    for index, day in enumerate(days):
        adjusted_close = 100 + index
        raw_close = adjusted_close * 2
        for adjusted, close in ((False, raw_close), (True, adjusted_close)):
            if missing_raw and not adjusted and index == 251:
                continue
            prices.append({"stock_id": 1, "stock_code": "000001", "trading_date": day, "market": "KOSPI",
                           "adjusted": adjusted, "open_price": close - 1, "high_price": close + 2,
                           "low_price": close - 2, "close_price": close, "trade_volume": 200_000,
                           "source_code": "KIWOOM_REST" if adjusted else "KRX_OPEN_API"})
    calendar_days = pd.date_range(days.min(), days.max(), freq="D")
    issue_rows = []
    if issue:
        issue_rows.append({"issue_code": "UNKNOWN_FACTOR", "severity": "ERROR", "affected_scope": "stock:000001",
                           "affected_from": days[250], "affected_to": days[250], "decision": "QUARANTINE"})
    return {
        "PRICE": pd.DataFrame(prices),
        "UNIVERSE": pd.DataFrame([{"stock_id": 1, "stock_code": "000001", "market": "KOSPI",
                                     "security_type": "COMMON_STOCK", "valid_from": days.min(), "valid_to": days.max()}]),
        "CALENDAR": pd.DataFrame({"market": "KRX", "trading_date": calendar_days, "is_open": calendar_days.isin(days)}),
        "STATUS": pd.DataFrame(columns=["stock_id", "trading_date", "daily_state"]),
        "ADJUSTMENT": pd.DataFrame(columns=["stock_id", "trading_date", "explanation_status"]),
        "ADMISSION_ISSUE": pd.DataFrame(issue_rows, columns=["issue_code", "severity", "affected_scope", "affected_from", "affected_to", "decision"]),
        "CORPORATE_ACTION": pd.DataFrame(columns=["stock_id", "effective_date"]),
    }


def test_calendar_missing_raw_bar_remains_and_cannot_fill():
    result = prepare_v3_inputs(_tables(missing_raw=True), start="2023-01-02", end="2023-12-31")
    assert len(result.prices) == 252
    last = result.prices.iloc[-1]
    assert pd.isna(last.close)
    assert not last.eligible
    assert len(result.signals) == 252
    assert not result.signals.iloc[-1][list(V2_ENTRY_IDS)].any()


def test_adjusted_signal_values_convert_to_raw_unit_and_use_raw_volume():
    result = prepare_v3_inputs(_tables(), start="2023-01-02", end="2023-12-31")
    last = result.signals.iloc[-1]
    # True range on adjusted bars is 4; ATR converted with raw/adjusted=2.
    assert last.close == 2 * (100 + 251)
    assert np.isclose(last.atr14, 8.0)
    assert result.prices.iloc[-1].volume == 200_000
    assert result.prices.iloc[-1].code == "1"
    assert result.prices.iloc[-1].display_code == "000001"
    assert result.prices.iloc[-1].raw_source_code == "KRX_OPEN_API"
    assert result.prices.iloc[-1].adjusted_source_code == "KIWOOM_REST"
    assert result.prices.iloc[-1].status == "TRADING"
    assert result.prices.iloc[-1].eligible


def test_evaluation_start_does_not_remove_earlier_warmup_rows():
    result = prepare_v3_inputs(_tables(), start="2023-10-02", end="2023-12-31")
    assert len(result.prices) == 252
    assert result.signals.date.min() == pd.Timestamp("2023-01-02")
    assert result.signals.iloc[-1].volume == 200_000


def test_future_bar_cannot_change_prior_signals():
    tables = _tables()
    baseline = prepare_v3_inputs(tables, start="2023-01-02", end="2023-12-31")
    changed = _tables()
    future_day = changed["PRICE"].trading_date.max()
    changed["PRICE"].loc[changed["PRICE"].trading_date == future_day, "close_price"] *= 100
    rerun = prepare_v3_inputs(changed, start="2023-01-02", end="2023-12-31")
    pd.testing.assert_frame_equal(baseline.signals.iloc[:-1].reset_index(drop=True),
                                  rerun.signals.iloc[:-1].reset_index(drop=True))


def test_stock_scoped_issue_maps_key_and_resets_signal_history():
    result = prepare_v3_inputs(_tables(issue=True), start="2023-01-02", end="2023-12-31")
    issue = result.issues.iloc[0]
    assert issue.instrument_id == "1"
    assert issue.code == "000001"
    assert issue.mapped and issue.signal_blocking
    blocked = result.signals.loc[result.signals.date == pd.Timestamp("2023-12-18")].iloc[0]
    assert blocked.issue_blocked
    assert not blocked[list(V2_ENTRY_IDS)].any()
    # A quarantined adjusted bar is a discontinuity, so later rows cannot use
    # its prior history until another complete 250-bar warmup exists.
    assert not result.signals.iloc[-1][list(V2_ENTRY_IDS)].any()
