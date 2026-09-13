import copy

import pandas as pd
import pytest

from research.krx_lab.execution import simulate
from research.krx_lab.vectorbt_check import reconcile


def _result():
    dates = pd.to_datetime(["2026-01-02", "2026-01-05"])
    return {
        "fills": pd.DataFrame(
            [
                {
                    "date": dates[0], "code": "A", "side": "buy", "size": 10, "price": 100,
                    "fees": 3.0, "phase": "entry_open", "fill_seq": 0,
                },
                {
                    "date": dates[1], "code": "A", "side": "sell", "size": 10, "price": 90,
                    "fees": 2.7, "phase": "stop_gap_open", "fill_seq": 1,
                },
                {
                    "date": dates[1], "code": "B", "side": "buy", "size": 20, "price": 50,
                    "fees": 3.0, "phase": "entry_open", "fill_seq": 2,
                },
            ]
        ),
        "positions": pd.DataFrame(
            [
                {"date": dates[0], "code": "A", "size": 10, "mark_price": 100},
                {"date": dates[1], "code": "B", "size": 20, "mark_price": 55},
            ]
        ),
        "equity": pd.DataFrame(
            [
                {"date": dates[0], "cash": 8997.0, "exposure": 1000.0, "equity": 9997.0, "positions_count": 1},
                {"date": dates[1], "cash": 8891.3, "exposure": 1100.0, "equity": 9991.3, "positions_count": 1},
            ]
        ),
    }


def test_reconcile_gap_exit_then_new_entry_with_shared_cash():
    check = reconcile(_result(), initial_cash=10_000)
    assert check == {
        "ok": True,
        "engine": "numba",
        "order_source": "fill_seq",
        "mismatches": [],
        "orders_checked": 3,
        "eod_checked": 2,
    }


def test_reconcile_detects_eod_and_quantity_disagreement():
    bad = copy.deepcopy(_result())
    bad["equity"].loc[1, "cash"] += 1
    bad["positions"].loc[1, "size"] += 1
    check = reconcile(bad, initial_cash=10_000)
    assert check["ok"] is False
    assert any(item.startswith("eod_value:") for item in check["mismatches"])
    assert any(item.startswith("eod_qty:") for item in check["mismatches"])


def test_reconcile_requires_nonnegative_integer_chronological_sequence():
    result = _result()
    result["fills"] = result["fills"].drop(columns="fill_seq")
    with pytest.raises(ValueError, match="fill_seq"):
        reconcile(result, initial_cash=10_000)
    result = _result()
    result["fills"].loc[0, "fill_seq"] = -1
    with pytest.raises(ValueError, match="nonnegative"):
        reconcile(result, initial_cash=10_000)


def test_reconcile_rejects_fill_without_eod_row():
    result = _result()
    result["fills"].loc[0, "date"] = pd.Timestamp("2026-01-01")
    with pytest.raises(ValueError, match="matching EOD"):
        reconcile(result, initial_cash=10_000)


def test_reconcile_zero_trade_cash_contract_and_negative_cash_failure():
    equity = pd.DataFrame(
        [
            {"date": "2026-01-02", "cash": 10_000.0, "equity": 10_000.0, "exposure": 0.0, "positions_count": 0},
            {"date": "2026-01-05", "cash": 10_000.0, "equity": 10_000.0, "exposure": 0.0, "positions_count": 0},
        ]
    )
    result = {
        "fills": pd.DataFrame(columns=["fill_seq", "date", "code", "side", "size", "price", "fees", "phase"]),
        "positions": pd.DataFrame(columns=["date", "code", "size", "mark_price"]),
        "equity": equity,
    }
    assert reconcile(result, initial_cash=10_000)["ok"] is True
    result["equity"].loc[1, "cash"] = -1
    assert "negative_cash_longonly_contract" in reconcile(result, initial_cash=10_000)["mismatches"]


def test_reconcile_current_execution_result_with_same_day_entry_and_exit():
    prices = pd.DataFrame(
        [
            {
                "date": "2026-01-02", "code": "A", "open": 100, "high": 101, "low": 99,
                "close": 100, "volume": 1_000_000, "sector": "S", "tick_size": 1, "eligible": True,
            },
            {
                "date": "2026-01-05", "code": "A", "open": 100, "high": 108, "low": 99,
                "close": 105, "volume": 1_000_000, "sector": "S", "tick_size": 1, "eligible": True,
            },
        ]
    )
    signals = pd.DataFrame([{"date": "2026-01-02", "code": "A", "atr14": 4, "avg_volume20": 1_000_000, "entry": True}])
    prices["date"], signals["date"] = pd.to_datetime(prices["date"]), pd.to_datetime(signals["date"])
    result = simulate(
        prices, signals, entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-05",
        calendar=["2026-01-02", "2026-01-05"],
    )
    assert reconcile(result)["ok"] is True
