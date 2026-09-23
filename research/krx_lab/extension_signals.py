"""Causal extension signals for the sealed KRX v3 research inputs.

These helpers prepare signals only.  They neither alter the sealed prepared
inputs nor model fills, capital allocation, or portfolio holdings.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .v3_tables import iter_v3_tables


_PRICE_COLUMNS = ("stock_id", "trading_date", "market", "adjusted", "low_price", "close_price")
_BENCHMARK_COLUMNS = ("benchmark_code", "trading_date", "close_value", "source_record_id")
_KEYS = ("date", "instrument_id")


def load_adjusted_prices(source, typed, *, instrument_ids=None) -> pd.DataFrame:
    """Read adjusted lows and closes from a pinned typed v3 source without using prepared raw prices."""
    wanted = None if instrument_ids is None else {str(value) for value in instrument_ids}
    frames = []
    for frame in iter_v3_tables(source, typed, "PRICE", columns=list(_PRICE_COLUMNS)):
        frame = frame.loc[frame["adjusted"].astype(bool)]
        if wanted is not None:
            frame = frame.loc[frame["stock_id"].astype(str).isin(wanted)]
        if not frame.empty:
            frames.append(frame)
    value = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_PRICE_COLUMNS)
    value = value.loc[:, list(_PRICE_COLUMNS)].copy()
    value["date"] = pd.to_datetime(value.pop("trading_date"), errors="raise").dt.normalize()
    value["instrument_id"] = value.pop("stock_id").astype("string")
    value = value.rename(columns={"low_price": "adjusted_low", "close_price": "adjusted_close"})
    return value[["date", "instrument_id", "market", "adjusted_low", "adjusted_close"]].sort_values(list(_KEYS), kind="stable").reset_index(drop=True)


def load_v3_benchmarks(source, typed) -> pd.DataFrame:
    """Read the sealed benchmark member; its official provenance is not asserted here."""
    frames = list(iter_v3_tables(source, typed, "BENCHMARK", columns=list(_BENCHMARK_COLUMNS)))
    value = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=_BENCHMARK_COLUMNS)
    value["date"] = pd.to_datetime(value.pop("trading_date"), errors="raise").dt.normalize()
    value = value.rename(columns={"benchmark_code": "market", "close_value": "close"})
    return value[["date", "market", "close", "source_record_id"]].sort_values(["market", "date"], kind="stable").reset_index(drop=True)


def monthly_relative_momentum(prices: pd.DataFrame, calendar: pd.DataFrame, *, top_n: int = 20) -> pd.DataFrame:
    """Return combined-market 12-1 momentum targets and completed-month signals.

    At each completed calendar month-end, return is ``C(t-1) / C(t-12) - 1``.
    A candidate needs a finite, positive
    adjusted close on every supplied KRX session in that interval.  Rankings
    are deterministic: return descending, then instrument id ascending.
    """
    _validate_prices(prices)
    sessions = _sessions(calendar)
    if top_n < 1:
        raise ValueError("top_n must be positive")
    work = prices.loc[:, list(_KEYS) + ["adjusted_close"]].copy()
    work["adjusted_close"] = pd.to_numeric(work["adjusted_close"], errors="coerce")
    work["_order"] = np.arange(len(work))
    months = pd.Series(sessions, index=sessions).groupby(sessions.to_period("M")).max()
    rebalance_dates = months
    target_dates: dict[pd.Timestamp, set[str]] = {}
    for rebalance in rebalance_dates:
        previous_month = rebalance.to_period("M") - 1
        start_month = rebalance.to_period("M") - 12
        if previous_month not in months.index or start_month not in months.index:
            continue
        target_dates[rebalance] = set()
        end_date, start_date = months.loc[previous_month], months.loc[start_month]
        interval = sessions[(sessions >= start_date) & (sessions <= end_date)]
        sample = work.loc[work["date"].between(start_date, end_date)]
        valid_close = sample["adjusted_close"].gt(0) & np.isfinite(sample["adjusted_close"])
        counts = sample.loc[valid_close].groupby("instrument_id", sort=False)["date"].nunique()
        endpoints = sample.loc[sample["date"].isin([start_date, end_date])].pivot(
            index="instrument_id", columns="date", values="adjusted_close"
        )
        current = prices.loc[prices["date"].eq(rebalance), ["instrument_id", "adjusted_close", "eligible",
                                                              "input_blocked", "issue_blocked"]]
        current = current.loc[current["adjusted_close"].gt(0) & np.isfinite(current["adjusted_close"])
                              & current["eligible"].astype(bool) & ~current["input_blocked"].astype(bool)
                              & ~current["issue_blocked"].astype(bool), "instrument_id"]
        valid_ids = counts.index[counts.eq(len(interval)) & counts.index.isin(current)]
        endpoints = endpoints.reindex(valid_ids)
        if start_date not in endpoints or end_date not in endpoints:
            continue
        returns = endpoints[end_date] / endpoints[start_date] - 1.0
        returns = returns.replace([np.inf, -np.inf], np.nan).dropna()
        selected = (returns.rename("momentum_return").reset_index()
                    .sort_values(["momentum_return", "instrument_id"], ascending=[False, True], kind="stable")
                    .head(top_n)["instrument_id"].astype(str))
        target_dates[rebalance] = set(selected)

    result = work.loc[:, list(_KEYS) + ["_order"]].copy()
    current: set[str] = set()
    target_rows = []
    entry_rows = []
    for date in sessions:
        if date in target_dates:
            current = target_dates[date]
            entry_rows.extend((date, instrument_id) for instrument_id in current)
        target_rows.extend((date, instrument_id) for instrument_id in current)
    target = pd.DataFrame(target_rows, columns=list(_KEYS)).assign(target=True)
    entries = pd.DataFrame(entry_rows, columns=list(_KEYS)).assign(MOMENTUM_ENTRY=True)
    result = result.merge(target, on=list(_KEYS), how="left", validate="one_to_one")
    result = result.merge(entries, on=list(_KEYS), how="left", validate="one_to_one")
    result["target"] = result["target"].fillna(False).astype(bool)
    result["MOMENTUM_ENTRY"] = result["MOMENTUM_ENTRY"].fillna(False).astype(bool)
    result["MOMENTUM_EXIT"] = (result["date"].isin(target_dates) & ~result["target"]).astype(bool)
    return result.sort_values("_order", kind="stable").drop(columns="_order").reset_index(drop=True)


def prior_20_low_exit(prices: pd.DataFrame, *, calendar: pd.DataFrame) -> pd.DataFrame:
    """Return a calendar-aware validity flag and exit below the prior twenty adjusted lows."""
    required = set(_KEYS) | {"adjusted_close", "adjusted_low"}
    missing = sorted(required - set(prices.columns))
    if missing:
        raise ValueError(f"MISSING_COLUMNS: {missing}")
    if prices.duplicated(list(_KEYS)).any():
        raise ValueError("DUPLICATE_PRICE_KEY")
    sessions = _sessions(calendar)
    work = prices.loc[:, list(_KEYS) + ["adjusted_close", "adjusted_low"]].copy()
    work["_order"] = np.arange(len(work))
    work = work.sort_values(["instrument_id", "date"], kind="stable")
    def one(frame):
        original_dates = frame["date"]
        frame = frame.set_index("date").reindex(sessions[(sessions >= original_dates.min()) & (sessions <= original_dates.max())])
        close = pd.to_numeric(frame["adjusted_close"], errors="coerce")
        low = pd.to_numeric(frame["adjusted_low"], errors="coerce")
        close = close.where(np.isfinite(close) & close.gt(0))
        low = low.where(np.isfinite(low) & low.gt(0))
        prior_low = low.shift(1).rolling(20, min_periods=20).min()
        frame["LOW20_VALID"] = (close.notna() & prior_low.notna()).fillna(False).astype(bool)
        frame["LOW20_EXIT"] = (frame["LOW20_VALID"] & (close < prior_low)).astype(bool)
        return frame.loc[original_dates].reset_index(names="date")
    result = pd.concat([one(group.copy()) for _, group in work.groupby("instrument_id", sort=False)], ignore_index=True)
    return result.sort_values("_order", kind="stable").drop(columns=["_order", "adjusted_close", "adjusted_low"]).reset_index(drop=True)


def benchmark_above_sma200(benchmarks: pd.DataFrame) -> pd.DataFrame:
    """Calculate causal 200-session benchmark filters for KOSPI and KOSDAQ."""
    required = {"date", "market", "close"}
    missing = sorted(required - set(benchmarks.columns))
    if missing:
        raise ValueError(f"MISSING_COLUMNS: {missing}")
    value = benchmarks.loc[benchmarks["market"].isin(["KOSPI", "KOSDAQ"]), ["date", "market", "close"]].copy()
    if value.duplicated(["date", "market"]).any():
        raise ValueError("DUPLICATE_BENCHMARK_KEY")
    # Arrow Decimal columns materialize as Python Decimal objects; NumPy's
    # isfinite does not accept their object dtype.
    value["close"] = pd.to_numeric(value["close"], errors="coerce").astype(float)
    value["close"] = value["close"].where(np.isfinite(value["close"]) & value["close"].gt(0))
    value = value.sort_values(["market", "date"], kind="stable")
    value["MARKET_ABOVE_SMA200"] = value.groupby("market", sort=False)["close"].transform(
        lambda close: (close > close.rolling(200, min_periods=200).mean()).fillna(False)
    ).astype(bool)
    return value.drop(columns="close").reset_index(drop=True)


def apply_breakout_market_filter(signals: pd.DataFrame, benchmark_filter: pd.DataFrame) -> pd.DataFrame:
    """Gate existing breakout entries with their respective market benchmark filter."""
    required = set(_KEYS) | {"market", "BREAKOUT_20", "BREAKOUT_60"}
    if missing := sorted(required - set(signals.columns)):
        raise ValueError(f"MISSING_COLUMNS: {missing}")
    allowed = benchmark_filter.loc[:, ["date", "market", "MARKET_ABOVE_SMA200"]]
    result = signals.loc[:, [* _KEYS, "market"]].merge(allowed, on=["date", "market"], how="left", validate="many_to_one")
    flag = result.pop("MARKET_ABOVE_SMA200").fillna(False).astype(bool).to_numpy()
    result["BREAKOUT_20_MARKET200"] = signals["BREAKOUT_20"].astype(bool).to_numpy() & flag
    result["BREAKOUT_60_MARKET200"] = signals["BREAKOUT_60"].astype(bool).to_numpy() & flag
    return result.drop(columns="market")


def _validate_prices(prices: pd.DataFrame) -> None:
    required = set(_KEYS) | {"adjusted_close", "eligible", "input_blocked", "issue_blocked"}
    missing = sorted(required - set(prices.columns))
    if missing:
        raise ValueError(f"MISSING_COLUMNS: {missing}")
    if prices.duplicated(list(_KEYS)).any():
        raise ValueError("DUPLICATE_PRICE_KEY")


def _sessions(calendar: pd.DataFrame) -> pd.DatetimeIndex:
    if "date" not in calendar:
        raise ValueError("MISSING_COLUMNS: ['date']")
    dates = pd.DatetimeIndex(pd.to_datetime(calendar["date"], errors="raise")).normalize().unique().sort_values()
    if dates.empty:
        raise ValueError("EMPTY_CALENDAR")
    return dates
