import numpy as np
import pandas as pd
import pytest

from research.krx_lab.indicators import atr14, ema_sma_seeded, wilder_rsi14
from research.krx_lab.strategies import ENTRY_IDS, build_signals


def make_prices(n=300, codes=("A",)):
    dates = pd.bdate_range("2024-01-02", periods=n)
    rows = []
    for number, code in enumerate(codes):
        close = 100 + number * 10 + np.linspace(0, 25, n) + 6 * np.sin(np.arange(n) * 0.23)
        rows.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "code": code,
                    "open": close * 0.998,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": 200_000,
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def test_contract_and_independent_group_calculation():
    source = make_prices(codes=("B", "A")).sample(frac=1, random_state=7).reset_index(drop=True)
    result = build_signals(source)
    assert list(result.columns[-14:]) == ["atr14", "avg_volume20", *ENTRY_IDS]
    assert result[["date", "code"]].equals(source[["date", "code"]])
    assert all(result[entry_id].dtype == bool for entry_id in ENTRY_IDS)
    ordered = result[result.code == "A"].sort_values("date")
    assert not ordered.iloc[:249][list(ENTRY_IDS)].to_numpy().any()
    expected = ordered.close > ordered.close.shift(1).rolling(20, min_periods=20).max()
    expected &= ordered.volume.shift(1) >= 100_000
    expected_complete = ordered[["open", "high", "low", "close", "volume"]].notna().all(axis=1).astype(int)
    expected &= expected_complete.rolling(250, min_periods=250).sum() == 250
    pd.testing.assert_series_equal(
        ordered.BREAKOUT_20.reset_index(drop=True),
        expected.fillna(False).astype(bool).reset_index(drop=True),
        check_names=False,
    )


def test_future_prefix_cannot_change_existing_signals():
    source = make_prices(n=280)
    prefix = build_signals(source)
    future = make_prices(n=40).assign(date=lambda frame: frame.date + pd.offsets.BDay(400))
    extended = build_signals(pd.concat([source, future], ignore_index=True))
    pd.testing.assert_frame_equal(prefix, extended.iloc[: len(prefix)].reset_index(drop=True))


def test_indicators_seed_and_reset_after_missing_close():
    close = pd.Series([10.0] * 15 + [np.nan] + list(range(20, 36)))
    ema = ema_sma_seeded(close, 5)
    rsi = wilder_rsi14(close)
    assert ema.iloc[4] == pytest.approx(10.0)
    assert pd.isna(ema.iloc[16 + 3]) and ema.iloc[20] == pytest.approx(22.0)
    assert pd.isna(rsi.iloc[14]) is False
    assert rsi.iloc[14] == pytest.approx(50.0)
    assert rsi.iloc[16:30].isna().all() and rsi.iloc[30] == pytest.approx(100.0)


def test_atr_needs_previous_close_and_full_contiguous_window():
    close = pd.Series(np.arange(100.0, 117.0))
    high, low = close + 2, close - 1
    value = atr14(high, low, close)
    assert value.iloc[:14].isna().all()
    assert value.iloc[14] == pytest.approx(3.0)
    close.iloc[15] = np.nan
    assert pd.isna(atr14(high, low, close).iloc[-1])


def test_no_signal_crosses_a_missing_interval_and_invalid_input_rejected():
    source = make_prices()
    source.loc[80, "close"] = np.nan
    result = build_signals(source)
    assert not result.loc[81:, list(ENTRY_IDS)].to_numpy().any()
    with pytest.raises(ValueError, match="date/code"):
        build_signals(pd.concat([source, source.iloc[[0]]], ignore_index=True))
    bad = make_prices()
    bad.loc[1, "high"] = bad.loc[1, "low"] / 2
    with pytest.raises(ValueError, match="고가/저가"):
        build_signals(bad)
