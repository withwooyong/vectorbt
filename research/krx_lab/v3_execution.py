"""Causal, read-only numerical execution for admitted v3 KRX inputs.

This module does not admit data or open a REAL run. The caller must verify the
sealed source, revision, universe, calendar, and signal construction first.
"""
from __future__ import annotations

import calendar as month_calendar
from bisect import bisect_right
from collections import OrderedDict
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import hashlib
from types import MappingProxyType

import pandas as pd

from .execution import _ATR_EXITS, _PERCENT_EXITS
from .strategies import V2_ENTRY_IDS
from .v3_market import raw_bar_eligibility


_PRICE_NAMES = {"open": ("raw_open", "open_price"), "high": ("raw_high", "high_price"),
                "low": ("raw_low", "low_price"), "close": ("raw_close", "close_price"),
                "volume": ("trade_volume",)}
_CACHE_MISS = object()
_BAR_CACHE_LIMIT = 50_000
_DAY_ARRAY_LIMIT = 32
_TABLES = {
    "signals": ["date", "code", "entry_id", "entry_signal"],
    "plans": ["signal_date", "entry_date", "code", "entry_cap", "stop_price", "target_price",
              "expiry_date", "avg_volume20", "status", "reason", "size", "fill_seq"],
    "orders": ["date", "code", "side", "size", "price", "fee", "fees", "tax", "phase", "status", "reason"],
    "fills": ["fill_seq", "date", "code", "side", "size", "price", "fee", "fees", "tax", "phase"],
    "positions": ["date", "code", "size", "entry_price", "stop_price", "target_price", "mark_price", "expiry"],
    "equity": ["date", "settled_cash", "receivables", "payables", "cash", "exposure", "equity", "positions_count"],
    "trades": ["code", "pnl", "entry_date", "exit_date"],
    "cashflows": ["date", "due_date", "code", "kind", "cash_delta", "receivable_delta", "payable_delta",
                  "fee", "tax", "fill_seq"],
    "events": ["date", "code", "event_id", "event_type", "quantity_delta", "receivable_delta"],
}


def _dec(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"Invalid execution amount: {value!r}") from exc
    if not result.is_finite():
        raise ValueError("Nonfinite execution amount")
    return result


def _tick_floor(price: Decimal, tick: Decimal) -> Decimal:
    return (price / tick).to_integral_value(rounding=ROUND_FLOOR) * tick


def _tick_ceil(price: Decimal, tick: Decimal) -> Decimal:
    return (price / tick).to_integral_value(rounding=ROUND_CEILING) * tick


def _level(rules, day, market, price: Decimal, *, upward=False) -> Decimal:
    if price <= 0:
        raise ValueError("Nonpositive execution level")
    tick = rules.tick(day, market, price)
    return _tick_ceil(price, tick) if upward else _tick_floor(price, tick)


def _on_tick(rules, day, market, price: Decimal) -> bool:
    tick = rules.tick(day, market, price)
    return price % tick == 0


def _month_after(day: pd.Timestamp) -> pd.Timestamp:
    year = day.year + (day.month == 12)
    month = 1 if day.month == 12 else day.month + 1
    return pd.Timestamp(year, month, min(day.day, month_calendar.monthrange(year, month)[1]))


def _true(value) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, str):
        return value.lower() in {"true", "t", "1", "yes"}
    return bool(value)


@dataclass
class _Position:
    code: str
    market: str
    size: int
    entry_date: pd.Timestamp
    entry_price: Decimal
    entry_fee: Decimal
    stop: Decimal
    target: Decimal
    expiry: pd.Timestamp
    mark: Decimal
    action_cash: Decimal = Decimal(0)


class PreparedExecution:
    """Index large price and signal frames once for repeated strategy slots.

    The optional period bounds must come from separately verified source
    coverage; they only allow non-session boundary dates around this calendar.
    """

    def __init__(self, prices: pd.DataFrame, signals: pd.DataFrame, calendar, events=None,
                 *, period_start=None, period_end=None):
        if isinstance(calendar, pd.DataFrame):
            if "date" not in calendar:
                raise ValueError("Calendar frame missing date")
            calendar = calendar.loc[calendar["market"].eq("KRX"), "date"] if "market" in calendar else calendar["date"]
        self.calendar = tuple(sorted(pd.Timestamp(day).normalize() for day in calendar))
        if not self.calendar or len(set(self.calendar)) != len(self.calendar):
            raise ValueError("Calendar must have unique ordered sessions")
        if self.calendar[-1] >= pd.Timestamp("2024-01-01"):
            raise ValueError("Post-2023 sessions are locked")
        self.period_start = pd.Timestamp(period_start).normalize() if period_start is not None else self.calendar[0]
        self.period_end = pd.Timestamp(period_end).normalize() if period_end is not None else self.calendar[-1]
        if (self.period_start < pd.Timestamp("2014-01-01") or self.period_end >= pd.Timestamp("2024-01-01")
                or self.period_start > self.calendar[0] or self.period_end < self.calendar[-1]):
            raise ValueError("Invalid verified calendar coverage bounds")
        self.date_index = {day: index for index, day in enumerate(self.calendar)}

        price_names = {"date", "trading_date", "instrument_id", "stock_id", "code", "market", "status",
                       "eligible", "open", "high", "low", "close", "volume", "trade_volume",
                       "raw_open", "raw_high", "raw_low", "raw_close",
                       "open_price", "high_price", "low_price", "close_price"}
        price = prices.loc[:, [name for name in prices if name in price_names]].copy()
        signal_names = {"date", "trading_date", "instrument_id", "stock_id", "code", "close", "atr14",
                        "avg_volume20"}
        signal = signals.loc[:, [name for name in signals if name in signal_names
                                or name in V2_ENTRY_IDS
                                or signals[name].dtype == bool]].copy()
        for frame in (price, signal):
            if "date" not in frame:
                if "trading_date" not in frame:
                    raise ValueError("Input missing date/trading_date")
                frame.rename(columns={"trading_date": "date"}, inplace=True)
            if "instrument_id" in frame:
                frame["code"] = frame["instrument_id"].astype(str)
            elif "code" not in frame:
                if "stock_id" not in frame:
                    raise ValueError("Input missing code/stock_id/instrument_id")
                frame["code"] = frame["stock_id"].astype(str)
            frame["code"] = frame["code"].astype(str)
            frame["date"] = pd.to_datetime(frame["date"]).dt.normalize()
            if frame.duplicated(["date", "code"]).any():
                raise ValueError("Duplicate date/code input")
            if frame["date"].ge("2024-01-01").any():
                raise ValueError("Post-2023 input is locked")
        for name, aliases in _PRICE_NAMES.items():
            if name not in price:
                matched = next((alias for alias in aliases if alias in price), None)
                if matched is None:
                    raise ValueError(f"Price input missing {name}/{aliases}")
                price[name] = price[matched]
        if "market" not in price:
            raise ValueError("Price input missing point-in-time market")
        if "eligible" not in price:
            price["eligible"] = True
        if "close" not in signal:
            raise ValueError("Signal input requires raw-unit close")
        for name in ("atr14", "avg_volume20"):
            if name not in signal:
                raise ValueError(f"Signal input missing {name}")
        self.prices_by_day = {day: frame.set_index("code", drop=False)
                              for day, frame in price.groupby("date", sort=False)}
        # Only bars touched by a strategy are materialized as immutable scalars.
        # A bounded cache avoids retaining all multi-million source rows twice.
        self._price_cache = OrderedDict()
        self._limit_cache = OrderedDict()
        self._price_arrays = OrderedDict()
        self.signals = signal
        self.signals_by_entry = {}
        self.events_by_day = {}
        if events is not None:
            event_frame = pd.DataFrame(events).copy()
            if not event_frame.empty:
                if "instrument_id" in event_frame:
                    event_frame["code"] = event_frame["instrument_id"].astype(str)
                elif "code" not in event_frame:
                    event_frame["code"] = event_frame["stock_id"].astype(str)
                event_frame["code"] = event_frame["code"].astype(str)
                event_frame["effective_date"] = pd.to_datetime(event_frame["effective_date"]).dt.normalize()
                if "sequence_no" not in event_frame:
                    event_frame["sequence_no"] = None
                for day, frame in event_frame.groupby("effective_date", sort=False):
                    self.events_by_day[day] = frame.sort_values(["code", "sequence_no"], kind="stable").to_dict("records")

    def entry_signals(self, entry_id: str) -> pd.DataFrame:
        if entry_id not in self.signals:
            raise ValueError(f"Unknown entry_id: {entry_id}")
        if entry_id not in self.signals_by_entry:
            self.signals_by_entry[entry_id] = self.signals.loc[self.signals[entry_id].map(_true)].sort_values(
                ["date", "code"], kind="stable")
        return self.signals_by_entry[entry_id]

    def price(self, day, code):
        key = (day, code)
        cached = self._price_cache.get(key, _CACHE_MISS)
        if cached is not _CACHE_MISS:
            self._price_cache.move_to_end(key)
            return cached
        frame = self.prices_by_day.get(day)
        if frame is None or code not in frame.index:
            bar = None
        else:
            arrays = self._price_arrays.get(day)
            if arrays is None:
                arrays = tuple((name, frame[name].to_numpy(copy=False)) for name in frame.columns)
                self._price_arrays[day] = arrays
                if len(self._price_arrays) > _DAY_ARRAY_LIMIT:
                    self._price_arrays.popitem(last=False)
            else:
                self._price_arrays.move_to_end(day)
            position = frame.index.get_loc(code)
            values = {name: array[position] for name, array in arrays}
            values["__eligible_cached__"] = _eligible(values)
            values["__mark_cached__"] = _mark(values)
            bar = MappingProxyType(values)
        self._price_cache[key] = bar
        if len(self._price_cache) > _BAR_CACHE_LIMIT:
            self._price_cache.popitem(last=False)
        return bar


def _eligible(row) -> bool:
    if row is None:
        return False
    cached = row.get("__eligible_cached__", _CACHE_MISS)
    if cached is not _CACHE_MISS:
        return cached
    status = row.get("status", "TRADING")
    return not pd.isna(status) and raw_bar_eligibility(row, status=status) and _true(row["eligible"])


def _mark(row) -> Decimal | None:
    """A known raw close can value a held share on a day with no trade."""
    if row is None:
        return None
    cached = row.get("__mark_cached__", _CACHE_MISS)
    if cached is not _CACHE_MISS:
        return cached
    status = row.get("status", "TRADING")
    if pd.isna(status) or status not in {"TRADING", "NO_TRADE", "HALTED", "PARTIAL_TRADING",
                                      "NON_TRADING_OBSERVED"}:
        return None
    try:
        close = _dec(row["close"])
    except (ValueError, TypeError):
        return None
    return close if close > 0 else None


def _price_limit_state(prepared, rules, day, code, row, references):
    """Return OK, UNKNOWN_REFERENCE, or OUT_OF_LIMIT for a consumed raw bar."""
    market = str(row["market"])
    reference = references.get((day, code))
    if reference is None:
        index = prepared.date_index[day]
        if index == 0:
            return "UNKNOWN_REFERENCE"
        reference = _mark(prepared.price(prepared.calendar[index - 1], code))
    if reference is None:
        return "UNKNOWN_REFERENCE"
    # A PreparedExecution may be reused with another rule set; retain the
    # actual rules object in the key so cached decisions cannot cross models.
    key = (rules, day, code, reference)
    cached = prepared._limit_cache.get(key, _CACHE_MISS)
    if cached is not _CACHE_MISS:
        prepared._limit_cache.move_to_end(key)
        return cached
    limit = rules.price_limit(day, market)
    # Round inward: an out-of-band legal tick is never accepted merely because
    # the percentage limit fell between ticks.
    lower = _level(rules, day, market, reference * (1 - limit), upward=True)
    upper = _level(rules, day, market, reference * (1 + limit))
    fields = ("open", "high", "low", "close") if _eligible(row) else ("close",)
    try:
        values = [_dec(row[name]) for name in fields]
    except (ValueError, TypeError):
        return "OUT_OF_LIMIT"
    state = "OK" if all(lower <= value <= upper for value in values) else "OUT_OF_LIMIT"
    prepared._limit_cache[key] = state
    if len(prepared._limit_cache) > _BAR_CACHE_LIMIT:
        prepared._limit_cache.popitem(last=False)
    return state


def simulate_real_slot(prepared: PreparedExecution, rules, *, entry_id, exit_id, start, end,
                       cost_bps=None, delay=1, initial_cash=100_000_000, hooks=None):
    """Run one price-return slot, failing closed on unresolved held exposures."""
    if exit_id not in _PERCENT_EXITS and exit_id not in _ATR_EXITS:
        raise ValueError(f"Unknown exit_id: {exit_id}")
    if not isinstance(delay, int) or isinstance(delay, bool) or delay < 1:
        raise ValueError("delay must be a positive session count")
    start, end = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    if start > end or start < pd.Timestamp("2014-01-01") or end >= pd.Timestamp("2024-01-01"):
        raise ValueError("Slot outside sealed 2014-2023 dates")
    if start < prepared.period_start or end > prepared.period_end:
        raise ValueError("Requested window exceeds prepared calendar coverage")
    cash = _dec(initial_cash)
    if cash <= 0:
        raise ValueError("initial_cash must be positive")
    stress_rate = None if cost_bps is None else _dec(cost_bps) / Decimal(10000)
    if stress_rate is not None and stress_rate < 0:
        raise ValueError("cost_bps must be nonnegative")
    output = {name: [] for name in _TABLES}
    issues = []
    positions = {}
    pending = []
    settled_cash = cash
    receivables = Decimal(0)
    payables = Decimal(0)
    prior_equity = cash
    fill_seq = 0
    blocked = False
    price_references = {}

    def costs(day, market, side, amount):
        if stress_rate is not None:
            fee = amount * stress_rate
            return {"fee": fee, "tax": Decimal(0), "total": fee}
        return rules.fees(day, market, side, amount)

    def record_fill(day, pos, side, size, price, phase, plan=None):
        nonlocal settled_cash, receivables, payables, fill_seq
        amount = size * price
        charge = costs(day, pos.market, side, amount)
        due_index = prepared.date_index[day] + rules.settlement_sessions(day, pos.market)
        due = prepared.calendar[due_index] if due_index < len(prepared.calendar) else pd.NaT
        if pd.isna(due):
            issues.append(f"SETTLEMENT_DATE_AFTER_CALENDAR:{day.date()}:{pos.code}")
        delta = amount - charge["total"] if side == "SELL" else -(amount + charge["total"])
        if side == "SELL":
            receivables += delta
        else:
            payables -= delta
        pending.append({"due_date": due, "code": pos.code, "side": side, "amount": abs(delta), "fill_seq": fill_seq})
        item = dict(date=day, code=pos.code, side=side.lower(), size=size, price=price,
                    fee=charge["fee"], fees=charge["fee"], tax=charge["tax"], phase=phase)
        output["orders"].append({**item, "status": "filled", "reason": ""})
        output["fills"].append({**item, "fill_seq": fill_seq})
        output["cashflows"].append(dict(date=day, due_date=due, code=pos.code, kind=side,
                                       cash_delta=Decimal(0), receivable_delta=delta if side == "SELL" else Decimal(0),
                                       payable_delta=-delta if side == "BUY" else Decimal(0),
                                       fee=charge["fee"], tax=charge["tax"], fill_seq=fill_seq))
        if plan is not None:
            plan["fill_seq"] = fill_seq
        fill_seq += 1
        return charge

    def close_position(day, pos, price, phase):
        charge = record_fill(day, pos, "SELL", pos.size, price, phase)
        pnl = pos.size * (price - pos.entry_price) - pos.entry_fee - charge["total"] + pos.action_cash
        output["trades"].append(dict(code=pos.code, pnl=pnl, entry_date=pos.entry_date, exit_date=day))
        del positions[pos.code]

    signal_rows = prepared.entry_signals(entry_id)
    plans_by_day = {}
    plans_by_code = {}
    for row in signal_rows.itertuples(index=False):
        signal_day, code = row.date, str(row.code)
        if signal_day not in prepared.date_index:
            continue
        index = prepared.date_index[signal_day]
        if index + delay >= len(prepared.calendar):
            continue
        entry_day = prepared.calendar[index + delay]
        if not start <= entry_day <= end:
            continue
        output["signals"].append(dict(date=signal_day, code=code, entry_id=entry_id, entry_signal=True))
        plan = dict(signal_date=signal_day, entry_date=entry_day, code=code, status="rejected", reason="",
                    size=None, fill_seq=None)
        output["plans"].append(plan)
        source = prepared.price(signal_day, code)
        if not _eligible(source):
            plan["reason"] = "INVALID_SIGNAL_DAY_RAW_BAR"
            continue
        try:
            close, atr, avg_volume = _dec(row.close), _dec(row.atr14), _dec(row.avg_volume20)
            raw_close = _dec(source["close"])
        except (ValueError, TypeError):
            plan["reason"] = "INVALID_SIGNAL_INPUT"
            continue
        if close != raw_close or close <= 0 or atr < 0 or avg_volume <= 0:
            plan["reason"] = "SIGNAL_RAW_BASIS_OR_INDICATOR"
            continue
        market = str(source["market"])
        raw_cap = min(close + atr / 2, close * Decimal("1.01"))
        if exit_id in _PERCENT_EXITS:
            stop_pct, target_pct = (_dec(v) for v in _PERCENT_EXITS[exit_id])
            stop, target = close * (1 - stop_pct), close * (1 + target_pct)
        else:
            stop_atr, target_atr = (_dec(v) for v in _ATR_EXITS[exit_id])
            stop, target = close - stop_atr * atr, close + target_atr * atr
        if stop <= 0:
            plan["reason"] = "NONPOSITIVE_SIGNAL_STOP"
            continue
        cap = _level(rules, signal_day, market, raw_cap)
        stop = _level(rules, signal_day, market, stop)
        target = _level(rules, signal_day, market, target, upward=True)
        anchor = _month_after(entry_day)
        expiry_index = bisect_right(prepared.calendar, anchor) - 1
        expiry = prepared.calendar[expiry_index] if prepared.calendar[-1] >= anchor else anchor
        plan.update(entry_cap=cap, stop_price=stop, target_price=target, expiry_date=expiry,
                    avg_volume20=avg_volume, market=market, status="planned")
        plans_by_day.setdefault(entry_day, []).append(plan)
        plans_by_code.setdefault(code, []).append(plan)

    def key(plan):
        source = f"lab-v1|20260913|{plan['signal_date'].date().isoformat()}|{plan['code']}"
        return hashlib.sha256(source.encode()).hexdigest()

    event_days = sorted(prepared.events_by_day)
    event_cursor = 0
    for day in (day for day in prepared.calendar if start <= day <= end):
        if hooks is not None:
            hooks("simulation_day", {"date": day.date().isoformat()})
        # Settlement moves claims into bank cash. Economic cash is unchanged.
        for item in list(pending):
            if pd.isna(item["due_date"]) or item["due_date"] > day:
                continue
            if item["side"] == "SELL":
                receivables -= item["amount"]
                settled_cash += item["amount"]
                recv_delta, payable_delta, cash_delta = -item["amount"], Decimal(0), item["amount"]
            else:
                payables -= item["amount"]
                settled_cash -= item["amount"]
                recv_delta, payable_delta, cash_delta = Decimal(0), -item["amount"], -item["amount"]
            output["cashflows"].append(dict(date=day, due_date=day, code=item["code"], kind="SETTLEMENT",
                                           cash_delta=cash_delta, receivable_delta=recv_delta,
                                           payable_delta=payable_delta, fee=Decimal(0), tax=Decimal(0),
                                           fill_seq=item["fill_seq"]))
            pending.remove(item)
        economic_cash = settled_cash + receivables - payables

        # Corporate actions are applied before the open. Only fully resolved
        # share splits with determinable whole-share/fractional cash are used.
        daily_events = []
        while event_cursor < len(event_days) and event_days[event_cursor] <= day:
            effective_day = event_days[event_cursor]
            daily_events.extend((effective_day, event) for event in prepared.events_by_day[effective_day])
            event_cursor += 1
        for effective_day, event in daily_events:
            code = str(event["code"])
            pos = positions.get(code)
            pending_plans = [plan for plan in plans_by_code.get(code, [])
                             if plan["status"] == "planned"
                             and plan["signal_date"] < effective_day <= plan["entry_date"]]
            if pos is None and not pending_plans:
                continue
            kind = event.get("event_type")
            if event.get("resolution_status") == "SUPERSEDED" or kind == "LISTED_SHARE_CHANGE":
                continue
            if effective_day not in prepared.date_index:
                if pos is not None:
                    issues.append(f"NONSESSION_HELD_EVENT:{effective_day.date()}:{code}:{event.get('event_id')}")
                    blocked = True
                    break
                for plan in pending_plans:
                    plan.update(status="rejected", reason="NONSESSION_ENTRY_EVENT")
                continue
            ratio_value = event.get("quantity_ratio")
            try:
                ratio = _dec(ratio_value)
                announced = pd.Timestamp(event["announced_at"])
                sequence = event.get("sequence_no")
                resolved = (kind in {"SPLIT", "REVERSE_SPLIT"}
                            and event.get("resolution_status") == "RESOLVED"
                            and pd.notna(announced) and announced.date() < effective_day.date()
                            and sequence is not None and int(sequence) >= 0
                            and _dec(event["reference_price"]) > 0
                            and sum(item_day == effective_day and item["code"] == code
                                    and item.get("sequence_no") == sequence
                                    and item.get("resolution_status") != "SUPERSEDED"
                                    and item.get("event_type") != "LISTED_SHARE_CHANGE"
                                    for item_day, item in daily_events) == 1
                            and ratio > 0 and ((kind == "SPLIT" and ratio > 1)
                                               or (kind == "REVERSE_SPLIT" and ratio < 1)))
            except (ValueError, TypeError, KeyError):
                resolved = False
            if not resolved:
                if pos is not None:
                    issues.append(f"UNRESOLVED_HELD_EVENT:{effective_day.date()}:{code}:{event.get('event_id')}")
                    blocked = True
                    break
                for plan in pending_plans:
                    plan.update(status="rejected", reason="UNRESOLVED_ENTRY_EVENT")
                continue
            for plan in pending_plans:
                for name in ("entry_cap", "stop_price", "target_price"):
                    plan[name] /= ratio
                plan["avg_volume20"] *= ratio
            price_references[(effective_day, code)] = _dec(event["reference_price"])
            if pos is not None:
                exact = pos.size * ratio
                whole = int(exact.to_integral_value(rounding=ROUND_FLOOR))
                fraction = exact - whole
                fractional_cash = Decimal(0)
                if fraction:
                    if (event.get("settlement_policy") != "CASH_IN_LIEU"
                            or event.get("settlement_cash_price") is None or event.get("pay_date") is None):
                        issues.append(f"UNRESOLVED_FRACTION:{effective_day.date()}:{code}:{event.get('event_id')}")
                        blocked = True
                        break
                    fractional_cash = fraction * _dec(event["settlement_cash_price"])
                    pay_day = pd.Timestamp(event["pay_date"]).normalize()
                    if pay_day < effective_day or not pd.notna(pay_day):
                        issues.append(f"INVALID_FRACTION_PAYMENT:{effective_day.date()}:{code}:{event.get('event_id')}")
                        blocked = True
                        break
                    receivables += fractional_cash
                    pending.append(dict(due_date=pay_day, code=code, side="SELL", amount=fractional_cash,
                                        fill_seq=None))
                    # The fractional entitlement carries its share of original
                    # basis; retain it in realized P&L instead of losing it.
                    fractional_basis = fraction * pos.entry_price / ratio
                    pos.action_cash += fractional_cash - fractional_basis
                    output["cashflows"].append(dict(date=effective_day, due_date=pay_day, code=code, kind="FRACTIONAL_CASH",
                                                   cash_delta=Decimal(0), receivable_delta=fractional_cash,
                                                   payable_delta=Decimal(0), fee=Decimal(0), tax=Decimal(0),
                                                   fill_seq=None))
                old_size = pos.size
                pos.size = whole
                pos.entry_price /= ratio
                pos.mark /= ratio
                pos.stop = _level(rules, effective_day, pos.market, pos.stop / ratio)
                pos.target = _level(rules, effective_day, pos.market, pos.target / ratio, upward=True)
                output["events"].append(dict(date=effective_day, code=code, event_id=event.get("event_id"),
                                             event_type=kind, quantity_delta=whole - old_size,
                                             receivable_delta=fractional_cash))
                if whole == 0:
                    issues.append(f"ZERO_SHARE_SPLIT_POSITION:{effective_day.date()}:{code}")
                    blocked = True
                    break
        if blocked:
            break

        exited = set()
        for code, pos in list(positions.items()):
            row = prepared.price(day, code)
            mark = _mark(row)
            if mark is None:
                issues.append(f"UNKNOWN_HELD_MARK:{day.date()}:{code}")
                blocked = True
                break
            if str(row["market"]) != pos.market:
                issues.append(f"HELD_MARKET_CHANGED:{day.date()}:{code}")
                blocked = True
                break
            limit_state = _price_limit_state(prepared, rules, day, code, row, price_references)
            if limit_state != "OK":
                issues.append(f"HELD_{limit_state}:{day.date()}:{code}")
                blocked = True
                break
            if not _eligible(row):
                pos.mark = mark
                issues.append(f"UNTRADEABLE_HELD_MARK:{day.date()}:{code}")
                continue
            opened = _dec(row["open"])
            if not _on_tick(rules, day, pos.market, opened):
                pos.mark = mark
                issues.append(f"OFF_TICK_HELD_OPEN:{day.date()}:{code}")
                continue
            if day >= pos.expiry:
                close_position(day, pos, opened, "time_open")
                exited.add(code)
            elif opened <= pos.stop:
                close_position(day, pos, opened, "stop_gap_open")
                exited.add(code)
            elif opened >= pos.target:
                close_position(day, pos, pos.target, "target_gap_open")
                exited.add(code)
        if blocked:
            break

        exposure = sum((pos.size * pos.mark for pos in positions.values()), Decimal(0))
        for plan in sorted(plans_by_day.get(day, []), key=key):
            if plan["status"] != "planned":
                continue
            code = plan["code"]
            if code in positions or code in exited:
                plan.update(status="rejected", reason="ALREADY_HELD_OR_EXITED")
                continue
            if len(positions) >= 20:
                plan.update(status="rejected", reason="SLOT_LIMIT")
                continue
            row = prepared.price(day, code)
            if not _eligible(row):
                plan.update(status="rejected", reason="INVALID_ENTRY_RAW_BAR")
                continue
            market = str(row["market"])
            if market != plan["market"]:
                plan.update(status="rejected", reason="MARKET_CHANGED")
                continue
            limit_state = _price_limit_state(prepared, rules, day, code, row, price_references)
            if limit_state != "OK":
                plan.update(status="rejected", reason=limit_state)
                continue
            opened = _dec(row["open"])
            if not _on_tick(rules, day, market, opened):
                plan.update(status="rejected", reason="OFF_TICK_ENTRY_OPEN")
                continue
            cap = _level(rules, day, market, plan["entry_cap"])
            stop = _level(rules, day, market, plan["stop_price"])
            target = _level(rules, day, market, plan["target_price"], upward=True)
            if opened > cap or not (0 < stop < opened <= cap < target):
                plan.update(status="rejected", reason="ENTRY_RANGE_OR_PRICE_RELATION")
                continue
            economic_cash = settled_cash + receivables - payables
            volume_limit = int((plan["avg_volume20"] * Decimal("0.001")).to_integral_value(rounding=ROUND_FLOOR))
            caps = [prior_equity * Decimal("0.04"), prior_equity * Decimal("0.05"),
                    max(prior_equity * Decimal("0.80") - exposure, Decimal(0)), economic_cash]
            upper = min([volume_limit, *(int((limit / opened).to_integral_value(rounding=ROUND_FLOOR))
                                          for limit in caps)])
            if upper <= 0:
                plan.update(status="rejected", reason="CASH_EXPOSURE_RISK_OR_VOLUME")
                continue
            # Exact binary search accounts for piecewise commission truncation.
            def fits(size):
                buy_value, stop_value = size * opened, size * stop
                buy = costs(day, market, "BUY", buy_value)["total"]
                sell = costs(day, market, "SELL", stop_value)["total"]
                return (buy_value + buy <= economic_cash
                        and buy_value + buy <= caps[0] and buy_value <= caps[1]
                        and buy_value <= caps[2]
                        and size * (opened - stop) + buy + sell <= prior_equity * Decimal("0.005"))
            low, high = 0, upper
            while low < high:
                mid = (low + high + 1) // 2
                if fits(mid):
                    low = mid
                else:
                    high = mid - 1
            size = low
            if size == 0:
                plan.update(status="rejected", reason="CASH_EXPOSURE_RISK_OR_VOLUME")
                continue
            pos = _Position(code, market, size, day, opened, Decimal(0), stop, target, plan["expiry_date"], opened)
            charge = record_fill(day, pos, "BUY", size, opened, "entry_open", plan)
            pos.entry_fee = charge["total"]
            positions[code] = pos
            exposure += size * opened
            plan.update(status="filled", reason="", size=size)

        for code, pos in list(positions.items()):
            row = prepared.price(day, code)
            if _mark(row) is None:
                issues.append(f"UNKNOWN_HELD_MARK:{day.date()}:{code}")
                blocked = True
                break
            if not _eligible(row) or not _on_tick(rules, day, pos.market, _dec(row["open"])):
                pos.mark = _mark(row)
                continue
            low, high, close = _dec(row["low"]), _dec(row["high"]), _dec(row["close"])
            if low <= pos.stop:
                close_position(day, pos, pos.stop, "stop_intraday_ambiguous" if high >= pos.target else "stop_intraday")
            elif high >= pos.target:
                close_position(day, pos, pos.target, "target_intraday")
            else:
                pos.mark = close
        if blocked:
            break
        economic_cash = settled_cash + receivables - payables
        exposure = sum((pos.size * pos.mark for pos in positions.values()), Decimal(0))
        for pos in positions.values():
            output["positions"].append(dict(date=day, code=pos.code, size=pos.size, entry_price=pos.entry_price,
                                            stop_price=pos.stop, target_price=pos.target, mark_price=pos.mark,
                                            expiry=pos.expiry))
        prior_equity = economic_cash + exposure
        output["equity"].append(dict(date=day, settled_cash=settled_cash, receivables=receivables,
                                     payables=payables, cash=economic_cash, exposure=exposure,
                                     equity=prior_equity, positions_count=len(positions)))

    if blocked:
        # Retain transactional evidence for diagnosis, but withhold incomplete
        # equity/trades so callers cannot turn an unresolved path into returns.
        output["equity"] = []
        output["positions"] = []
        output["trades"] = []
    result = {name: pd.DataFrame(rows, columns=columns) for name, (rows, columns) in
              ((name, (output[name], columns)) for name, columns in _TABLES.items())}
    result.update(status="BLOCKED" if blocked else "SUCCEEDED", source_kind="REAL",
                  performance_valid=not blocked, cost_model="FLAT_BPS_STRESS_ONLY" if stress_rate is not None else "DATED_RULES",
                  issues=list(dict.fromkeys(issues)), initial_cash=cash)
    return result


def audit_execution_ledger(result) -> None:
    """Independently replay cash claims and fill charges before reporting returns."""
    if result.get("status") != "SUCCEEDED" or not result.get("performance_valid"):
        raise ValueError("Incomplete execution cannot pass ledger audit")
    flows = result["cashflows"]
    fills = result["fills"]
    bank = _dec(result["initial_cash"])
    receivables = payables = Decimal(0)
    by_date = {day: frame for day, frame in flows.groupby("date", sort=False)}
    for row in result["equity"].itertuples(index=False):
        day_flows = by_date.get(row.date)
        if day_flows is not None:
            for flow in day_flows.itertuples(index=False):
                bank += _dec(flow.cash_delta)
                receivables += _dec(flow.receivable_delta)
                payables += _dec(flow.payable_delta)
        economic = bank + receivables - payables
        if (bank != _dec(row.settled_cash) or receivables != _dec(row.receivables)
                or payables != _dec(row.payables) or economic != _dec(row.cash)
                or economic + _dec(row.exposure) != _dec(row.equity)):
            raise ValueError(f"Ledger identity mismatch on {row.date}")
        if receivables < 0 or payables < 0:
            raise ValueError(f"Negative unsettled claim on {row.date}")
    booked = flows.loc[flows["kind"].isin(["BUY", "SELL"])]
    if len(booked) != len(fills) or booked["fill_seq"].duplicated().any():
        raise ValueError("Fill and booked cashflow counts differ")
    booked = booked.set_index("fill_seq")
    for fill in fills.itertuples(index=False):
        if fill.fill_seq not in booked.index:
            raise ValueError("Fill lacks booked cashflow")
        flow = booked.loc[fill.fill_seq]
        amount = _dec(fill.size) * _dec(fill.price)
        fee, tax = _dec(fill.fee), _dec(fill.tax)
        if _dec(flow.fee) != fee or _dec(flow.tax) != tax:
            raise ValueError("Fill charges differ from booked cashflow")
        if fill.side == "buy":
            valid = flow.kind == "BUY" and _dec(flow.payable_delta) == amount + fee + tax
        else:
            valid = flow.kind == "SELL" and _dec(flow.receivable_delta) == amount - fee - tax
        if not valid:
            raise ValueError("Fill amount differs from booked cashflow")
