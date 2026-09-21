"""Versioned sector policy preserves v1 and permits the 20-slot experiment."""

import pandas as pd
import pytest

from research.krx_lab.execution import simulate


def _run(**kwargs):
    codes = [f"{i:06d}" for i in range(25)]
    days = ["2020-01-02", "2020-01-03"]
    prices = pd.DataFrame([
        {"date": day, "code": code, "open": 100, "high": 101, "low": 99,
         "close": 100, "volume": 100_000_000, "tick_size": 1, "eligible": True}
        for day in days for code in codes
    ])
    signals = pd.DataFrame([
        {"date": days[0], "code": code, "close": 100, "atr14": 2,
         "avg_volume20": 100_000_000, "entry": True} for code in codes
    ])
    return simulate(prices, signals, entry_id="entry", exit_id="PCT_3_6",
                    start=days[0], end=days[-1], calendar=days, cost_bps=0, **kwargs)


def test_disabled_sector_cap_fills_twenty_slots_and_preserves_cash():
    result = _run(sector_cap=None)
    buys = result["fills"].query("side == 'buy'")
    assert len(buys) == 20
    assert result["plans"]["reason"].eq("SLOT_LIMIT").sum() == 5
    assert "MISSING_SECTOR" not in result["issues"]
    last = result["equity"].iloc[-1]
    assert last["cash"] == 20_000_000
    assert last["equity"] == 100_000_000
    assert (buys["size"] * buys["price"]).sum() + last["cash"] == last["equity"]


def test_default_preserves_v1_sector_limit():
    default = _run()
    explicit = _run(sector_cap=0.25)
    for key in ("fills", "equity", "plans"):
        pd.testing.assert_frame_equal(default[key], explicit[key])
    assert len(default["fills"]) == 7
    assert "MISSING_SECTOR" in default["issues"]
    assert default["equity"].iloc[-1]["exposure"] == 25_000_000


@pytest.mark.parametrize("cap", [True, False, 0, -0.1, 1.1, float("nan"), float("inf"), "0.25"])
def test_invalid_sector_cap_fails_before_execution(cap):
    with pytest.raises(ValueError, match="sector_cap"):
        _run(sector_cap=cap)
