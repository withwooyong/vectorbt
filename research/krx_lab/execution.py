"""Causal, shared-cash daily-bar execution simulator for KRX lab research."""

from __future__ import annotations

import calendar as _calendar
import hashlib
import numbers
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd


_PRICE_COLUMNS = ("date", "code", "open", "high", "low", "close", "volume")
_SIGNAL_COLUMNS = ("date", "code", "atr14", "avg_volume20")


def _empty(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _as_bool(value: object) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "t", "yes", "y"}
    return bool(value)


def _fee(value: float, rate: float) -> float:
    return float(value) * rate


def _add_month_clamp(day: pd.Timestamp) -> pd.Timestamp:
    year = day.year + (day.month == 12)
    month = 1 if day.month == 12 else day.month + 1
    return pd.Timestamp(year=year, month=month, day=min(day.day, _calendar.monthrange(year, month)[1]))


def _tick_floor(price: float, tick: float) -> float:
    return float(np.floor((price + 1e-12) / tick) * tick)


def _tick_ceil(price: float, tick: float) -> float:
    return float(np.ceil((price - 1e-12) / tick) * tick)


@dataclass
class _Position:
    code: str
    size: int
    entry_date: pd.Timestamp
    entry_price: float
    entry_fees: float
    stop_price: float
    target_price: float
    expiry_anchor: pd.Timestamp
    sector: str
    last_price: float
    stale: bool = False


def simulate(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    *,
    entry_id: str,
    exit_id: str,
    start: str,
    end: str,
    cost_bps: float = 30,
    delay: int = 1,
    initial_cash: float = 100_000_000,
    policy: str = "fixed20",
    calendar: Sequence[str] | None = None,
    optimistic: bool = False,
) -> dict:
    """Simulate one technical variant with causal OHLCV access and shared cash.

    Signal-day close and ATR create an immutable next-entry plan.  The simulator
    never reads a later day's OHLCV while constructing that plan; it consumes a
    row only when processing that trading date.
    """

    if policy not in {"fixed20", "staged10_15_20"}:
        raise ValueError("policy must be 'fixed20' or 'staged10_15_20'")
    if not isinstance(delay, numbers.Integral) or isinstance(delay, bool) or delay < 1:
        raise ValueError("delay must be at least 1 trading day")
    if not np.isfinite(cost_bps) or cost_bps < 0:
        raise ValueError("cost_bps must be finite and non-negative")
    if not np.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be positive")
    if exit_id not in {"PCT_3_6", "PCT_5_10", "ATR_1_5_3", "ATR_2_4"}:
        raise ValueError(f"Unsupported exit_id: {exit_id}")
    missing_prices = set(_PRICE_COLUMNS).difference(prices.columns)
    missing_signals = set(_SIGNAL_COLUMNS).difference(signals.columns)
    if missing_prices:
        raise ValueError(f"prices missing required columns: {sorted(missing_prices)}")
    if missing_signals or entry_id not in signals.columns:
        needed = sorted(missing_signals | ({entry_id} if entry_id not in signals.columns else set()))
        raise ValueError(f"signals missing required columns: {needed}")

    issues: list[str] = []
    price_columns = list(_PRICE_COLUMNS) + [name for name in ("sector", "tick_size", "eligible") if name in prices.columns]
    signal_columns = list(_SIGNAL_COLUMNS) + [entry_id] + (["close"] if "close" in signals.columns else [])
    # Keep only the columns that execution consumes; source frames remain untouched.
    price_df = prices.loc[:, price_columns].copy()
    signal_df = signals.loc[:, signal_columns].copy()
    price_df["date"] = pd.to_datetime(price_df["date"]).dt.normalize()
    signal_df["date"] = pd.to_datetime(signal_df["date"]).dt.normalize()
    start_ts, end_ts = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if end_ts < start_ts:
        raise ValueError("end must be on or after start")
    if price_df.duplicated(["date", "code"]).any():
        raise ValueError("prices must have at most one row per date and code")
    if signal_df.duplicated(["date", "code"]).any():
        raise ValueError("signals must have at most one row per date and code")

    optional_defaults = {"sector": "__UNKNOWN__", "tick_size": 1.0, "eligible": True}
    for name, default in optional_defaults.items():
        if name not in price_df.columns:
            issues.append(f"MISSING_{name.upper()}")
            price_df[name] = default
    price_df["sector"] = price_df["sector"].fillna("__UNKNOWN__").astype(str)
    price_df["tick_size"] = pd.to_numeric(price_df["tick_size"], errors="coerce").fillna(1.0)
    price_df["eligible"] = price_df["eligible"].map(_as_bool)
    for col in ("open", "high", "low", "close", "volume", "tick_size"):
        price_df[col] = pd.to_numeric(price_df[col], errors="coerce")
    signal_df["atr14"] = pd.to_numeric(signal_df["atr14"], errors="coerce")
    signal_df["avg_volume20"] = pd.to_numeric(signal_df["avg_volume20"], errors="coerce")

    if calendar is None:
        all_dates = sorted(price_df["date"].unique())
        issues.append("CALENDAR_UNVERIFIED")
    else:
        all_dates = sorted(pd.to_datetime(pd.Series(calendar)).dt.normalize().unique())
    all_dates = [pd.Timestamp(day) for day in all_dates]
    dates = [day for day in all_dates if start_ts <= day <= end_ts]
    if not dates:
        return {
            "signals": _empty(["date", "code", "entry_id", "entry_signal"]),
            "plans": _empty(["signal_date", "entry_date", "code", "expiry_date", "decision_at", "data_cutoff", "fill_seq", "status", "reason"]),
            "orders": _empty(["date", "code", "side", "size", "price", "fees", "phase", "status", "reason"]),
            "fills": _empty(["fill_seq", "date", "code", "side", "size", "price", "fees", "phase"]),
            "positions": _empty(["date", "code", "size", "entry_price", "stop_price", "target_price", "mark_price", "expiry", "overdue", "stale"]),
            "equity": _empty(["date", "cash", "equity", "exposure", "positions_count"]),
            "trades": _empty(["code", "pnl", "entry_date", "exit_date"]),
            "issues": issues + ["NO_TRADING_DATES"],
        }

    date_index = {day: idx for idx, day in enumerate(all_dates)}
    rows_by_day = {day: day_df.set_index("code", drop=False) for day, day_df in price_df.groupby("date", sort=False)}
    signal_events: list[dict] = []
    plans: list[dict] = []
    plans_by_day: dict[pd.Timestamp, list[dict]] = {}
    for row in signal_df.sort_values(["date", "code"], kind="stable").itertuples(index=False):
        signal_date = getattr(row, "date")
        if not _as_bool(getattr(row, entry_id)):
            continue
        idx = date_index.get(signal_date)
        if idx is None or idx + delay >= len(all_dates):
            if start_ts <= signal_date <= end_ts:
                event = {"date": signal_date, "code": str(getattr(row, "code")), "entry_id": entry_id, "entry_signal": True}
                signal_events.append(event)
                plans.append({**event, "signal_date": signal_date, "entry_date": pd.NaT, "status": "rejected", "reason": "NO_FUTURE_TRADING_DAY"})
            continue
        entry_date = all_dates[idx + delay]
        if not (start_ts <= entry_date <= end_ts):
            continue
        event = {"date": signal_date, "code": str(getattr(row, "code")), "entry_id": entry_id, "entry_signal": True}
        signal_events.append(event)
        close, atr = getattr(row, "close", np.nan), getattr(row, "atr14", np.nan)
        # Signals may carry close; if absent use only the same-day price row.
        if pd.isna(close):
            same_day = rows_by_day.get(signal_date)
            close = same_day.loc[str(getattr(row, "code")), "close"] if same_day is not None and str(getattr(row, "code")) in same_day.index else np.nan
        if not np.isfinite(close) or not np.isfinite(atr) or close <= 0 or atr < 0:
            plans.append({**event, "signal_date": signal_date, "entry_date": entry_date, "status": "rejected", "reason": "INVALID_SIGNAL_INPUT"})
            continue
        same_day = rows_by_day.get(signal_date)
        signal_row = same_day.loc[str(getattr(row, "code"))] if same_day is not None and str(getattr(row, "code")) in same_day.index else None
        tick = float(signal_row["tick_size"]) if signal_row is not None and np.isfinite(signal_row["tick_size"]) and signal_row["tick_size"] > 0 else 1.0
        cap = min(float(close) + 0.5 * float(atr), 1.01 * float(close))
        if exit_id == "PCT_3_6":
            stop, target = 0.97 * float(close), 1.06 * float(close)
        elif exit_id == "PCT_5_10":
            stop, target = 0.95 * float(close), 1.10 * float(close)
        elif exit_id == "ATR_1_5_3":
            stop, target = float(close) - 1.5 * float(atr), float(close) + 3.0 * float(atr)
        elif exit_id == "ATR_2_4":
            stop, target = float(close) - 2.0 * float(atr), float(close) + 4.0 * float(atr)
        else:
            raise ValueError(f"Unsupported exit_id: {exit_id}")
        cap, stop, target = _tick_floor(cap, tick), _tick_floor(stop, tick), _tick_ceil(target, tick)
        expiry_raw = _add_month_clamp(entry_date)
        expiry_candidates = [candidate for candidate in all_dates if entry_date <= candidate <= expiry_raw]
        if all_dates[-1] < expiry_raw:
            expiry_date = expiry_raw
            issues.append(f"EXPIRY_CALENDAR_UNAVAILABLE:{entry_date.date()}:{expiry_raw.date()}")
        else:
            expiry_date = max(expiry_candidates) if expiry_candidates else expiry_raw
        plan = {
            **event,
            "signal_date": signal_date,
            "entry_date": entry_date,
            "entry_cap": cap,
            "stop_price": stop,
            "target_price": target,
            "expiry_date": expiry_date,
            "decision_at": signal_date,
            "data_cutoff": signal_date,
            "avg_volume20": float(getattr(row, "avg_volume20")),
            "fill_seq": None,
            "status": "planned",
            "reason": "",
        }
        plans.append(plan)
        if start_ts <= entry_date <= end_ts:
            plans_by_day.setdefault(entry_date, []).append(plan)

    cash = float(initial_cash)
    fee_rate = float(cost_bps) / 10_000.0
    positions: dict[str, _Position] = {}
    orders: list[dict] = []
    fills: list[dict] = []
    daily_positions: list[dict] = []
    equity_rows: list[dict] = []
    trades: list[dict] = []
    previous_equity = float(initial_cash)
    fill_sequence = 0

    def open_valid(row: pd.Series | None) -> bool:
        if row is None:
            return False
        return bool(row["eligible"]) and np.isfinite(row["open"]) and row["open"] > 0

    def intrabar_valid(row: pd.Series | None) -> bool:
        if row is None or not bool(row["eligible"]):
            return False
        values = [row["open"], row["high"], row["low"], row["close"]]
        return all(np.isfinite(value) and value > 0 for value in values) and row["high"] >= max(row["open"], row["close"], row["low"]) and row["low"] <= min(row["open"], row["close"], row["high"])

    def close_valid(row: pd.Series | None) -> bool:
        return row is not None and np.isfinite(row["close"]) and row["close"] > 0

    def close_position(day: pd.Timestamp, pos: _Position, price: float, phase: str) -> None:
        nonlocal cash, fill_sequence
        proceeds = pos.size * price
        fees = _fee(proceeds, fee_rate)
        cash += proceeds - fees
        orders.append({"date": day, "code": pos.code, "side": "sell", "size": pos.size, "price": price, "fees": fees, "phase": phase, "status": "filled", "reason": ""})
        fills.append({"fill_seq": fill_sequence, "date": day, "code": pos.code, "side": "sell", "size": pos.size, "price": price, "fees": fees, "phase": phase})
        fill_sequence += 1
        pnl = proceeds - fees - (pos.size * pos.entry_price + pos.entry_fees)
        trades.append({"code": pos.code, "pnl": pnl, "entry_date": pos.entry_date, "exit_date": day})
        del positions[pos.code]

    for day in dates:
        day_rows = rows_by_day.get(day)
        exited_today: set[str] = set()
        # Existing positions: time exit, then gap exits.  No later OHLC is read.
        for code, pos in list(positions.items()):
            row = day_rows.loc[code] if day_rows is not None and code in day_rows.index else None
            if not open_valid(row):
                pos.stale = not close_valid(row)
                if close_valid(row):
                    issues.append(f"INELIGIBLE_NO_TRADE:{day.date()}:{code}")
                else:
                    issues.append(f"STALE_PRICE:{day.date()}:{code}")
                continue
            pos.stale = False
            open_price = float(row["open"])
            if day >= pos.expiry_anchor:
                close_position(day, pos, open_price, "time_open")
                exited_today.add(code)
            elif open_price <= pos.stop_price:
                close_position(day, pos, open_price, "stop_gap_open")
                exited_today.add(code)
            elif open_price >= pos.target_price:
                close_position(day, pos, pos.target_price if not optimistic else open_price, "target_gap_open")
                exited_today.add(code)

        sector_value: dict[str, float] = {}
        existing_exposure = 0.0
        for pos in positions.values():
            position_value = pos.size * pos.last_price
            existing_exposure += position_value
            sector_value[pos.sector] = sector_value.get(pos.sector, 0.0) + position_value
        # New entries use only their current open and previously fixed plan.
        def candidate_key(value: dict) -> str:
            value_to_hash = f"lab-v1|20260913|{value['signal_date'].date().isoformat()}|{value['code']}"
            return hashlib.sha256(value_to_hash.encode("utf-8")).hexdigest()

        for plan in sorted(plans_by_day.get(day, []), key=candidate_key):
            code = plan["code"]
            row = day_rows.loc[code] if day_rows is not None and code in day_rows.index else None
            if code in positions or code in exited_today:
                plan["status"], plan["reason"] = "rejected", "ALREADY_HELD_OR_EXITED"
                continue
            slot_limit = 20 if policy == "fixed20" else (10 if previous_equity < 150_000_000 else 15 if previous_equity < 200_000_000 else 20)
            if len(positions) >= slot_limit:
                plan["status"], plan["reason"] = "rejected", "SLOT_LIMIT"
                continue
            if not open_valid(row):
                plan["status"], plan["reason"] = "rejected", "INELIGIBLE_OR_INVALID_ENTRY_ROW"
                continue
            entry_price, tick = float(row["open"]), float(row["tick_size"])
            if entry_price > plan["entry_cap"] or not (0 < plan["stop_price"] < entry_price <= plan["entry_cap"] < plan["target_price"]):
                plan["status"], plan["reason"] = "rejected", "ENTRY_RANGE_OR_PRICE_RELATION"
                continue
            avg_volume_value = float(plan["avg_volume20"])
            if not np.isfinite(avg_volume_value) or avg_volume_value <= 0:
                plan["status"], plan["reason"] = "rejected", "INVALID_AVG_VOLUME20"
                continue
            sector = str(row["sector"])
            target_cash = previous_equity * 0.80 / slot_limit
            sector_remaining = max(previous_equity * 0.25 - sector_value.get(sector, 0.0), 0.0)
            risk_per_share = max(entry_price - float(plan["stop_price"]), 0.0) + entry_price * fee_rate + float(plan["stop_price"]) * fee_rate
            risk_cash = previous_equity * 0.005
            exposure_remaining = max(previous_equity * 0.80 - existing_exposure, 0.0)
            limits = [target_cash, previous_equity * 0.05, sector_remaining, exposure_remaining, cash]
            quantity_limits = [int(limit / (entry_price * (1.0 + fee_rate))) for limit in limits]
            quantity_limits.append(int(risk_cash / risk_per_share) if risk_per_share > 0 else 0)
            quantity_limits.append(int(np.floor(avg_volume_value * 0.001)))
            size = max(0, min(quantity_limits))
            if size < 1:
                plan["status"], plan["reason"] = "rejected", "RISK_CASH_SECTOR_OR_VOLUME_LIMIT"
                continue
            fees = _fee(size * entry_price, fee_rate)
            total_cost = size * entry_price + fees
            cash -= total_cost
            positions[code] = _Position(code, size, day, entry_price, fees, float(plan["stop_price"]), float(plan["target_price"]), pd.Timestamp(plan["expiry_date"]), sector, entry_price)
            sector_value[sector] = sector_value.get(sector, 0.0) + size * entry_price
            existing_exposure += size * entry_price
            plan["status"], plan["reason"], plan["size"], plan["fill_seq"] = "filled", "", size, fill_sequence
            orders.append({"date": day, "code": code, "side": "buy", "size": size, "price": entry_price, "fees": fees, "phase": "entry_open", "status": "filled", "reason": ""})
            fills.append({"fill_seq": fill_sequence, "date": day, "code": code, "side": "buy", "size": size, "price": entry_price, "fees": fees, "phase": "entry_open"})
            fill_sequence += 1

        # Intraday exits.  Stop wins an ambiguous daily candle unless optimistic is requested.
        for code, pos in list(positions.items()):
            row = day_rows.loc[code] if day_rows is not None and code in day_rows.index else None
            if not intrabar_valid(row):
                if close_valid(row):
                    pos.last_price = float(row["close"])
                    pos.stale = False
                    issues.append(f"INELIGIBLE_MARK:{day.date()}:{code}")
                else:
                    pos.stale = True
                    issues.append(f"STALE_PRICE:{day.date()}:{code}")
                continue
            low, high, close = float(row["low"]), float(row["high"]), float(row["close"])
            stop_hit, target_hit = low <= pos.stop_price, high >= pos.target_price
            if stop_hit and target_hit:
                if optimistic:
                    close_position(day, pos, pos.target_price, "target_intraday_ambiguous_optimistic")
                else:
                    close_position(day, pos, pos.stop_price, "stop_intraday_ambiguous")
            elif stop_hit:
                close_position(day, pos, pos.stop_price, "stop_intraday")
            elif target_hit:
                close_position(day, pos, pos.target_price, "target_intraday")
            elif not pos.stale:
                pos.last_price = close

        exposure = 0.0
        for pos in positions.values():
            exposure += pos.size * pos.last_price
            daily_positions.append({"date": day, "code": pos.code, "size": pos.size, "entry_price": pos.entry_price, "stop_price": pos.stop_price, "target_price": pos.target_price, "mark_price": pos.last_price, "expiry": pos.expiry_anchor, "overdue": day > pos.expiry_anchor, "stale": pos.stale})
        current_equity = cash + exposure
        equity_rows.append({"date": day, "cash": cash, "equity": current_equity, "exposure": exposure, "positions_count": len(positions)})
        previous_equity = current_equity

    return {
        "signals": pd.DataFrame(signal_events, columns=["date", "code", "entry_id", "entry_signal"]),
        "plans": pd.DataFrame(plans),
        "orders": pd.DataFrame(orders, columns=["date", "code", "side", "size", "price", "fees", "phase", "status", "reason"]),
        "fills": pd.DataFrame(fills, columns=["fill_seq", "date", "code", "side", "size", "price", "fees", "phase"]),
        "positions": pd.DataFrame(daily_positions, columns=["date", "code", "size", "entry_price", "stop_price", "target_price", "mark_price", "expiry", "overdue", "stale"]),
        "equity": pd.DataFrame(equity_rows, columns=["date", "cash", "equity", "exposure", "positions_count"]),
        "trades": pd.DataFrame(trades, columns=["code", "pnl", "entry_date", "exit_date"]),
        "issues": list(dict.fromkeys(issues)),
    }
