"""기술 명세의 12개 종가 신호. 달력축 reindex와 체결은 호출자의 책임이다."""
from __future__ import annotations

import numpy as np
import pandas as pd

from research.krx_lab.indicators import atr14, ema_sma_seeded, wilder_rsi14


ENTRY_IDS = (
    "CROSS_5_20",
    "CROSS_10_20",
    "BREAKOUT_20",
    "BREAKOUT_60",
    "TREND_PULLBACK_3",
    "TREND_PULLBACK_5",
    "RSI_REENTRY_30",
    "RSI_REENTRY_40",
    "BOLLINGER_REENTRY_1_5",
    "BOLLINGER_REENTRY_2",
    "MACD_CROSS_SMA60",
    "MACD_CROSS_SMA120",
)
RVOL_ENTRY_IDS = (
    "BREAKOUT_20_RVOL_1_5",
    "BREAKOUT_60_RVOL_1_5",
)
V2_ENTRY_IDS = (*ENTRY_IDS, *RVOL_ENTRY_IDS)
REQUIRED_COLUMNS = ("date", "code", "open", "high", "low", "close", "volume")


def build_signals(prices: pd.DataFrame, *, entry_ids: tuple[str, ...] = ENTRY_IDS) -> pd.DataFrame:
    """Return input rows plus ATR, current 20-day average volume, and requested entries.

    Rows are calculated independently for each code in date order and returned in the
    original order.  Missing prices create an invalid interval: rolling, EMA, and RSI
    state does not bridge it.  ``ENTRY_IDS`` is the v1 default.  Passing
    ``V2_ENTRY_IDS`` opts in to the two separately versioned RVOL entries.  No calendar
    dates are inserted here.
    """
    _validate_prices(prices)
    _validate_entry_ids(entry_ids)
    source_columns = list(prices.columns)
    work = prices.copy()
    work["_input_order"] = np.arange(len(work))
    work = work.sort_values(["code", "date"], kind="stable")
    pieces = [_build_one(group.copy(), entry_ids) for _, group in work.groupby("code", sort=False, group_keys=False)]
    result = pd.concat(pieces, ignore_index=True).sort_values("_input_order", kind="stable")
    result = result.drop(columns="_input_order")
    return result[source_columns + ["atr14", "avg_volume20", *entry_ids]].reset_index(drop=True)


def _validate_entry_ids(entry_ids: tuple[str, ...]) -> None:
    if not isinstance(entry_ids, tuple) or not entry_ids:
        raise ValueError("entry_ids는 비어 있지 않은 tuple이어야 합니다")
    if len(set(entry_ids)) != len(entry_ids) or any(entry_id not in V2_ENTRY_IDS for entry_id in entry_ids):
        raise ValueError("지원하지 않는 entry_id가 있습니다")


def _validate_prices(prices: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_COLUMNS if column not in prices.columns]
    if missing:
        raise ValueError(f"prices에 필요한 열이 없습니다: {', '.join(missing)}")
    if prices.empty:
        raise ValueError("prices는 비어 있을 수 없습니다")
    if not pd.api.types.is_datetime64_any_dtype(prices["date"]):
        raise TypeError("date는 datetime64 열이어야 합니다")
    if prices.date.isna().any() or prices.code.isna().any() or (prices.code.astype(str).str.len() == 0).any():
        raise ValueError("date/code는 비어 있을 수 없습니다")
    if prices.duplicated(["date", "code"]).any():
        raise ValueError("같은 date/code 행은 하나만 허용됩니다")
    for column in REQUIRED_COLUMNS[2:]:
        if not pd.api.types.is_numeric_dtype(prices[column]):
            raise TypeError(f"{column}은 숫자 열이어야 합니다")
        values = prices[column].to_numpy(dtype=float, na_value=np.nan)
        if np.isinf(values).any():
            raise ValueError(f"{column}에 무한대가 있습니다")
        if column == "volume":
            if (values[np.isfinite(values)] < 0).any():
                raise ValueError("volume은 음수일 수 없습니다")
        elif (values[np.isfinite(values)] <= 0).any():
            raise ValueError(f"{column}은 양수이거나 결측이어야 합니다")
    complete_ohlc = prices[["open", "high", "low", "close"]].notna().all(axis=1)
    check = prices.loc[complete_ohlc]
    invalid_high_low = (
        (check.high < check[["open", "close"]].max(axis=1))
        | (check.low > check[["open", "close"]].min(axis=1))
        | (check.high < check.low)
    )
    if invalid_high_low.any():
        raise ValueError("OHLC 고가/저가 관계가 맞지 않습니다")


def _build_one(frame: pd.DataFrame, entry_ids: tuple[str, ...]) -> pd.DataFrame:
    close = frame.close.astype(float)
    high = frame.high.astype(float)
    low = frame.low.astype(float)
    volume = frame.volume.astype(float)
    sma5, sma10, sma20, sma60, sma120 = (
        close.rolling(window, min_periods=window).mean() for window in (5, 10, 20, 60, 120)
    )
    frame["atr14"] = atr14(high, low, close)
    frame["avg_volume20"] = volume.rolling(20, min_periods=20).mean()
    prior_avg_volume20 = volume.shift(1).rolling(20, min_periods=20).mean()
    rvol20 = volume / prior_avg_volume20
    valid_volume = volume.shift(1) >= 100_000
    complete_bar = frame[["open", "high", "low", "close", "volume"]].notna().all(axis=1).astype(int)
    ready = complete_bar.rolling(250, min_periods=250).sum() == 250
    rsi = wilder_rsi14(close)
    lower_15 = sma20 - 1.5 * close.rolling(20, min_periods=20).std(ddof=0)
    lower_20 = sma20 - 2.0 * close.rolling(20, min_periods=20).std(ddof=0)
    fast, slow = ema_sma_seeded(close, 12), ema_sma_seeded(close, 26)
    macd = fast - slow
    macd_signal = ema_sma_seeded(macd, 9)
    raw = {
        "CROSS_5_20": (sma5.shift(1) < sma20.shift(1)) & (sma5 > sma20),
        "CROSS_10_20": (sma10.shift(1) < sma20.shift(1)) & (sma10 > sma20),
        "BREAKOUT_20": close > close.shift(1).rolling(20, min_periods=20).max(),
        "BREAKOUT_60": close > close.shift(1).rolling(60, min_periods=60).max(),
        "BREAKOUT_20_RVOL_1_5": (
            (close > close.shift(1).rolling(20, min_periods=20).max()) & (rvol20 >= 1.5)
        ),
        "BREAKOUT_60_RVOL_1_5": (
            (close > close.shift(1).rolling(60, min_periods=60).max()) & (rvol20 >= 1.5)
        ),
        "TREND_PULLBACK_3": (close > sma60) & ((close / close.shift(3) - 1) * 100 <= -3),
        "TREND_PULLBACK_5": (close > sma60) & ((close / close.shift(3) - 1) * 100 <= -5),
        "RSI_REENTRY_30": (close > sma60) & (rsi.shift(1) < 30) & (rsi >= 30),
        "RSI_REENTRY_40": (close > sma60) & (rsi.shift(1) < 40) & (rsi >= 40),
        "BOLLINGER_REENTRY_1_5": (close > sma60) & (close.shift(1) < lower_15.shift(1)) & (close >= lower_15),
        "BOLLINGER_REENTRY_2": (close > sma60) & (close.shift(1) < lower_20.shift(1)) & (close >= lower_20),
        "MACD_CROSS_SMA60": (close > sma60) & (macd.shift(1) <= macd_signal.shift(1)) & (macd > macd_signal),
        "MACD_CROSS_SMA120": (close > sma120) & (macd.shift(1) <= macd_signal.shift(1)) & (macd > macd_signal),
    }
    for entry_id in entry_ids:
        frame[entry_id] = (raw[entry_id] & valid_volume & ready).fillna(False).astype(bool)
    return frame
