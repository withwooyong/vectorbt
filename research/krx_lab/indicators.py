"""NaN 구간을 넘겨 상태를 이어가지 않는 KRX 일봉 연구용 지표."""
from __future__ import annotations

import numpy as np
import pandas as pd


def atr14(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """전일 종가가 있는 연속 구간에서만 계산하는 14봉 단순 ATR."""
    previous_close = close.shift(1)
    tr = pd.concat([high - low, (high - previous_close).abs(), (low - previous_close).abs()], axis=1).max(axis=1)
    tr = tr.where(high.notna() & low.notna() & close.notna() & previous_close.notna())
    return tr.rolling(14, min_periods=14).mean()


def ema_sma_seeded(values: pd.Series, window: int) -> pd.Series:
    """각 연속 유효 구간의 첫 EMA를 SMA로 정하고 결측 뒤 다시 시작한다."""
    values = values.astype(float)
    data = values.to_numpy(dtype=float, na_value=np.nan)
    out = np.full(len(data), np.nan)
    alpha = 2.0 / (window + 1)
    start = 0
    while start < len(data):
        while start < len(data) and np.isnan(data[start]):
            start += 1
        end = start
        while end < len(data) and np.isfinite(data[end]):
            end += 1
        if end - start >= window:
            current = float(data[start : start + window].mean())
            out[start + window - 1] = current
            for i in range(start + window, end):
                current = alpha * data[i] + (1 - alpha) * current
                out[i] = current
        start = end + 1
    return pd.Series(out, index=values.index, dtype=float)


def wilder_rsi14(close: pd.Series) -> pd.Series:
    """14개 등락 SMA로 시작해 Wilder 방식으로 갱신하며, 결측에서 재초기화한다."""
    close = close.astype(float)
    data = close.to_numpy(dtype=float, na_value=np.nan)
    out = np.full(len(data), np.nan)
    start = 0
    while start < len(data):
        while start < len(data) and np.isnan(data[start]):
            start += 1
        end = start
        while end < len(data) and np.isfinite(data[end]):
            end += 1
        if end - start >= 15:
            changes = np.diff(data[start:end])
            gains, losses = np.maximum(changes, 0), np.maximum(-changes, 0)
            avg_gain, avg_loss = float(gains[:14].mean()), float(losses[:14].mean())
            out[start + 14] = _rsi_value(avg_gain, avg_loss)
            for i in range(14, len(gains)):
                avg_gain = (avg_gain * 13 + gains[i]) / 14
                avg_loss = (avg_loss * 13 + losses[i]) / 14
                out[start + i + 1] = _rsi_value(avg_gain, avg_loss)
        start = end + 1
    return pd.Series(out, index=close.index, dtype=float)


def _rsi_value(avg_gain: float, avg_loss: float) -> float:
    if avg_gain == 0 and avg_loss == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    return 100 - 100 / (1 + avg_gain / avg_loss)
