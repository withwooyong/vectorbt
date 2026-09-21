"""Wider exits remain causal and use the same shared-account risk budget."""

import pandas as pd
import pytest

from research.krx_lab.execution import simulate


def _run(exit_id, *, atr=400, high=10001, low=9999, next_open=10000):
    prices = pd.DataFrame([
        {"date": "2020-01-02", "code": "A", "open": 10000, "high": 10001,
         "low": 9999, "close": 10000, "volume": 100_000_000},
        {"date": "2020-01-03", "code": "A", "open": next_open, "high": high,
         "low": low, "close": next_open, "volume": 100_000_000},
    ])
    signals = pd.DataFrame([{"date": "2020-01-02", "code": "A", "close": 10000,
                             "atr14": atr, "avg_volume20": 100_000_000, "entry": True}])
    return simulate(prices, signals, entry_id="entry", exit_id=exit_id, start="2020-01-02",
                    end="2020-01-03", calendar=["2020-01-02", "2020-01-03"],
                    cost_bps=0, sector_cap=None)


@pytest.mark.parametrize("exit_id,stop,target", [
    ("PCT_8_16", 9200, 11600), ("PCT_10_20", 9000, 12000),
    ("ATR_3_6", 8800, 12400), ("ATR_4_8", 8400, 13200),
])
def test_wide_thresholds_use_signal_close_and_stop_wins(exit_id, stop, target):
    result = _run(exit_id, low=stop-1, high=target+1)
    plan = result["plans"].iloc[0]
    assert (plan["stop_price"], plan["target_price"]) == (stop, target)
    assert result["fills"].iloc[-1]["price"] == stop
    assert result["fills"].iloc[-1]["phase"] == "stop_intraday_ambiguous"


def test_wider_stop_reduces_size_under_unchanged_risk_budget():
    narrow, wide = _run("PCT_3_6"), _run("ATR_4_8")
    assert narrow["fills"].iloc[0]["size"] == 400
    assert wide["fills"].iloc[0]["size"] == 312
    assert 312 * (10000 - 8400) <= 500_000
    assert 313 * (10000 - 8400) > 500_000


def test_entry_gap_does_not_reset_exit_thresholds():
    result = _run("PCT_8_16", next_open=10050, high=10051)
    assert result["fills"].iloc[0]["price"] == 10050
    assert result["plans"].iloc[0]["stop_price"] == 9200
    assert result["plans"].iloc[0]["target_price"] == 11600


def test_nonpositive_atr_stop_rejects_entry():
    result = _run("ATR_4_8", atr=3000)
    assert result["fills"].empty
    assert result["plans"].iloc[0]["reason"] == "ENTRY_RANGE_OR_PRICE_RELATION"
