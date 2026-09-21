"""Prepare C1 REAL adjusted-price entry signals without admitting execution.

This pure adapter preserves every declared KRX session, including a missing bar.
It neither checks upstream provenance nor calculates orders or returns.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

import numpy as np
import pandas as pd

from .contracts import validate_delivery
from .strategies import build_signals


_PRICE_FIELDS = ("open", "high", "low", "close")


def prepare_real_signals(delivery: Mapping, *, start: str | None = None,
                         end: str | None = None) -> pd.DataFrame:
    """Return adjusted OHLCV and 12 signals for a pre-2024 REAL C1 delivery.

    ``end`` limits the input before indicator calculation; ``start`` trims only
    the output, retaining earlier bars for indicator warmup. Missing sessions
    remain NaN bars with false signals. This is inspection/preparation only.
    """
    if not isinstance(delivery, Mapping) or delivery.get("source_kind") != "REAL":
        raise ValueError("REAL_SOURCE_REQUIRED")
    checked = validate_delivery(delivery)
    meta = checked["metadata"]
    first = _day(start or meta["start"])
    last = _day(end or meta["end"])
    if first > last or first < _day(meta["start"]) or last > _day(meta["end"]):
        raise ValueError("WINDOW_OUTSIDE_DELIVERY")
    if last >= pd.Timestamp("2024-01-01"):
        raise ValueError("HOLDOUT_LOCKED")

    calendar = sorted({_day(row["date"]) for row in checked["calendar"]
                       if row["market"] == "KRX" and row["is_open"]
                       and _day(meta["start"]) <= _day(row["date"]) <= last})
    if not calendar:
        raise ValueError("KRX_CALENDAR_EMPTY")
    if not checked["instruments"]:
        raise ValueError("INSTRUMENTS_EMPTY")
    raw = {(row["instrument_id"], _day(row["date"])): row for row in checked["prices"]
           if _day(row["date"]) <= last}
    sessions = set(calendar)
    if any(day not in sessions for _, day in raw):
        raise ValueError("PRICE_OUTSIDE_OPEN_KRX_SESSION")
    instruments = _group_intervals(checked["instruments"], "INSTRUMENT_INTERVAL_OVERLAP")
    statuses = _group_intervals(checked["statuses"], "STATUS_INTERVAL_OVERLAP")
    rows = []
    used_prices = set()
    codes = {}
    signal_group = 0
    for instrument in checked["instruments"]:
        if instrument["market"] != "KRX":
            raise ValueError("UNSUPPORTED_MARKET")
        identity = instrument["instrument_id"]
        code = instrument["code"]
        if identity in codes and codes[identity] != code:
            raise ValueError("INSTRUMENT_CODE_CHANGED")
        codes[identity] = code
    for identity, intervals in instruments.items():
        code = codes[identity]
        state_intervals = statuses.get(identity, [])
        instrument_at = 0
        status_at = 0
        was_active = False
        for day in calendar:
            while instrument_at < len(intervals) and intervals[instrument_at][1] < day:
                instrument_at += 1
            if instrument_at == len(intervals) or intervals[instrument_at][0] > day:
                was_active = False
                continue
            if not was_active:
                signal_group += 1
                was_active = True
            while status_at < len(state_intervals) and state_intervals[status_at][1] < day:
                status_at += 1
            if status_at == len(state_intervals) or state_intervals[status_at][0] > day:
                raise ValueError("STATUS_COVERAGE_INVALID")
            if state_intervals[status_at][2]["status"] != "TRADING":
                raise ValueError("UNSUPPORTED_STATUS_FOR_SIGNALS")
            key = (identity, day)
            price = raw.get(key)
            if price is not None and price["code"] != code:
                raise ValueError("PRICE_CODE_MISMATCH")
            if price is not None:
                used_prices.add(key)
            row = {"date": day, "code": code, "instrument_id": identity, "_signal_group": signal_group,
                   **{name: np.nan if price is None else price[f"adjusted_{name}"] for name in _PRICE_FIELDS},
                   "volume": np.nan if price is None else price["volume"]}
            rows.append(row)
    if not rows:
        raise ValueError("NO_ACTIVE_KRX_SESSIONS")
    prices = pd.DataFrame(rows)
    if raw.keys() - used_prices:
        raise ValueError("PRICE_OUTSIDE_ACTIVE_INSTRUMENT")
    if prices.duplicated(["date", "code"]).any():
        raise ValueError("DUPLICATE_ACTIVE_CODE")
    # build_signals partitions by code. Give each active instrument interval an
    # internal key so reused display codes and inactive gaps cannot seed history.
    prices["_display_code"] = prices["code"]
    prices["code"] = prices["_signal_group"]
    signals = build_signals(prices)
    signals["code"] = signals.pop("_display_code")
    signals = signals.drop(columns="_signal_group")
    result = signals.loc[signals["date"] >= first].reset_index(drop=True)
    if result.empty:
        raise ValueError("WINDOW_HAS_NO_ACTIVE_SESSIONS")
    # Keep an explicit source label so downstream callers cannot mistake this
    # preparatory frame for the synthetic runner's executable input.
    result.insert(0, "source_kind", "REAL")
    return result


def _day(value: str) -> pd.Timestamp:
    day = pd.Timestamp(value)
    if day.tzinfo is not None or day != day.normalize():
        raise ValueError("INVALID_DAY")
    return day


def _group_intervals(items: list[dict], overlap_error: str) -> dict:
    grouped = defaultdict(list)
    for row in items:
        start = _day(row["effective_from"])
        end = _day(row["effective_to"]) if row["effective_to"] is not None else pd.Timestamp.max.normalize()
        grouped[row["instrument_id"]].append((start, end, row))
    for intervals in grouped.values():
        intervals.sort(key=lambda item: item[0])
        if any(previous[1] >= current[0] for previous, current in zip(intervals, intervals[1:])):
            raise ValueError(overlap_error)
    return grouped
