"""Synthetic-only independent-sleeve oracle for the OHLCV 20-slot strategy.

No data admission, signal calculation, real execution or returns reporting is
provided here. Cash means economic buying power, NOT settled bank cash. Real
use requires a separate admission gate, settlement/entitlement ledger and
verified market, liquidity and price-definition adapters.

Signals are known at signal_date close: code, turnover, mean_turnover20,
limit_price, eligible. mean_turnover20 is the verified mean actual turnover
over 20 completed sessions, including signal_date; incomplete windows fail
upstream. Full cost-affordable orders above 1% of that mean are skipped.
Bars require explicit can_buy/can_sell/order_eligible/mark_valid booleans;
these must incorporate market rules and execution feasibility externally.
Costs(side, day, market, notional) returns nonnegative total fees and tax and
must be monotone in notional. Levels(side, day, market, price) rounds an order
level; tests may explicitly use identity rounding. No implicit cost or tick
assumptions are made. Corporate events touching a holding or assigned order
block the run because this module does not implement entitlements.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR
from typing import Callable

import pandas as pd


def _d(value):
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("NONFINITE_AMOUNT")
    return result


def _day(value):
    result = pd.Timestamp(value)
    if pd.isna(result) or result.tzinfo is not None or result != result.normalize():
        raise ValueError("INVALID_SESSION_DATE")
    if not pd.Timestamp("2014-01-01") <= result < pd.Timestamp("2024-01-01"):
        raise ValueError("DATE_OUTSIDE_LOCKED_WINDOW")
    return result


@dataclass
class Sleeve:
    slot_id: int
    cash: Decimal
    idle_since: pd.Timestamp
    reusable_from: pd.Timestamp
    position: dict | None = None


def simulate_ohlcv20(
    prices,
    signals,
    calendar,
    *,
    start,
    end,
    stop_pct,
    target_pct,
    holding_months,
    costs: Callable,
    levels: Callable,
    events=None,
    source_kind="SYNTHETIC",
    initial_cash=100_000_000,
    optimistic=False,
):
    """Run one fixed 20-sleeve synthetic experiment with explicit inputs.

    A blocked path retains orders/fills for diagnosis but withholds equity and
    positions. Signals require the previous exchange session in ``calendar``;
    the first evaluation day can therefore execute a warmup-day signal.
    """
    if source_kind != "SYNTHETIC":
        raise ValueError("REAL_EXECUTION_NOT_ADMITTED")
    if holding_months not in (1, 3) or isinstance(holding_months, bool):
        raise ValueError("HOLDING_MONTHS_MUST_BE_1_OR_3")
    stop, target, cash = _d(stop_pct), _d(target_pct), _d(initial_cash)
    if not 0 < stop < 1 or target <= 0 or cash <= 0:
        raise ValueError("INVALID_STRATEGY_AMOUNTS")
    first, last = _day(start), _day(end)
    days = [_day(value) for value in calendar]
    if (
        days != sorted(set(days))
        or not days
        or first > last
        or first < days[0]
        or last > days[-1]
    ):
        raise ValueError("INVALID_CALENDAR_COVERAGE")
    evaluation = [day for day in days if first <= day <= last]
    if not evaluation:
        raise ValueError("EMPTY_EVALUATION")
    next_day = dict(zip(days[:-1], days[1:]))
    bars = {}
    for row in pd.DataFrame(prices).to_dict("records"):
        day, code = _day(row["date"]), str(row["code"])
        if day not in days or (day, code) in bars:
            raise ValueError("DUPLICATE_OR_OFF_CALENDAR_BAR")
        for field in ("can_buy", "can_sell", "order_eligible", "mark_valid"):
            if type(row[field]) is not bool:
                raise ValueError("EXPLICIT_BOOLEAN_REQUIRED:" + field)
        if (
            "regular_session_trigger_valid" in row
            and type(row["regular_session_trigger_valid"]) is not bool
        ):
            raise ValueError("EXPLICIT_TRIGGER_VALIDITY_REQUIRED")
        row.setdefault("regular_session_trigger_valid", False)
        for field in ("open", "high", "low", "close", "volume"):
            row[field] = _d(row[field])
        if row["volume"] < 0:
            raise ValueError("NEGATIVE_VOLUME")
        if row["can_buy"] or row["can_sell"]:
            if (
                row["volume"] <= 0
                or row["low"] <= 0
                or not row["low"] <= min(row["open"], row["close"])
                or not row["high"] >= max(row["open"], row["close"])
            ):
                raise ValueError("INVALID_EXECUTABLE_OHLCV")
        if row["mark_valid"] and row["close"] <= 0:
            raise ValueError("INVALID_VALID_MARK")
        bars[day, code] = row
    by_day, seen = {}, set()
    for row in pd.DataFrame(signals).to_dict("records"):
        day, code = _day(row["signal_date"]), str(row["code"])
        if (day, code) in seen or day not in days:
            raise ValueError("DUPLICATE_OR_OFF_CALENDAR_SIGNAL")
        seen.add((day, code))
        if type(row["eligible"]) is not bool:
            raise ValueError("EXPLICIT_SIGNAL_ELIGIBILITY_REQUIRED")
        if "mean_turnover20" not in row:
            raise ValueError("MISSING_MEAN_TURNOVER20")
        turnover, limit = _d(row["turnover"]), _d(row["limit_price"])
        mean_turnover20 = _d(row["mean_turnover20"])
        if turnover < 0 or limit <= 0 or mean_turnover20 <= 0:
            raise ValueError("INVALID_SIGNAL_AMOUNT")
        if row["eligible"]:
            by_day.setdefault(day, []).append(
                dict(
                    code=code,
                    turnover=turnover,
                    limit=limit,
                    mean_turnover20=mean_turnover20,
                )
            )
    event_rows = []
    for row in pd.DataFrame(events if events is not None else []).to_dict("records"):
        event_rows.append((_day(row["effective_date"]), str(row["code"])))
    sleeves = [Sleeve(i, cash / 20, first, first) for i in range(20)]
    fills, orders, equity, positions, issues, diagnostics = [], [], [], [], [], []
    assignments = {}
    sold_by_day_code = {}
    attempted_exits = set()

    def fee(side, day, market, value):
        charge = _d(costs(side, day, market, value))
        if charge < 0:
            raise ValueError("NEGATIVE_COST")
        return charge

    def level(side, day, market, value):
        rounded = _d(levels(side, day, market, value))
        if rounded <= 0:
            raise ValueError("NONPOSITIVE_ORDER_LEVEL")
        return rounded

    def sell(sleeve, day, price, reason):
        pos = sleeve.position
        pos["pending_exit"] = True
        attempted_exits.add((day, sleeve.slot_id))
        key = (day, pos["code"])
        capacity = int(
            (bars[key]["volume"] * Decimal("0.01")).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        available = max(0, capacity - sold_by_day_code.get(key, 0))
        quantity = min(pos["size"], available)
        if quantity < pos["size"]:
            diagnostics.append(
                dict(
                    date=day,
                    slot_id=sleeve.slot_id,
                    code=pos["code"],
                    kind="daily_sell_volume_cap",
                    action="DEFER_REMAINDER",
                )
            )
        if quantity == 0:
            return
        amount = quantity * price
        charge = fee("SELL", day, pos["market"], amount)
        if sleeve.cash + amount - charge < 0:
            raise ValueError("SELL_COST_EXCEEDS_SLOT_ASSETS")
        sleeve.cash += amount - charge
        fills.append(
            dict(
                date=day,
                slot_id=sleeve.slot_id,
                code=pos["code"],
                side="SELL",
                size=quantity,
                price=price,
                cost=charge,
                reason=reason,
            )
        )
        sold_by_day_code[key] = sold_by_day_code.get(key, 0) + quantity
        pos["size"] -= quantity
        if pos["size"]:
            return
        sleeve.position = None
        sleeve.idle_since = day
        sleeve.reusable_from = next_day.get(day, day + pd.Timedelta(days=1))

    def assign(signal_day):
        order_day = next_day.get(signal_day)
        if order_day is None:
            return
        held = {s.position["code"] for s in sleeves if s.position is not None}
        candidates = sorted(
            (r for r in by_day.get(signal_day, []) if r["code"] not in held),
            key=lambda r: (-r["turnover"], r["code"]),
        )
        empty = sorted(
            (s for s in sleeves if s.position is None and s.reusable_from <= order_day),
            key=lambda s: (s.idle_since, s.slot_id),
        )
        assignments[order_day] = [
            (s, dict(r, signal_date=signal_day)) for s, r in zip(empty, candidates)
        ]

    index = days.index(evaluation[0])
    if index:
        assign(days[index - 1])
    prior_day = days[index - 1] if index else evaluation[0] - pd.Timedelta(days=1)
    for day in evaluation:
        assigned = assignments.get(day, [])
        touched = {s.position["code"] for s in sleeves if s.position}
        for _, plan in assigned:
            touched.add(plan["code"])
        relevant_events = [
            (d, c) for d, c in event_rows if prior_day < d <= day and c in touched
        ]
        if relevant_events:
            issues.append("UNSUPPORTED_CORPORATE_EVENT:" + str(relevant_events))
            break
        for sleeve in sleeves:
            pos = sleeve.position
            if pos is None:
                continue
            row = bars.get((day, pos["code"]))
            if row is None or not row["mark_valid"]:
                issues.append(f"UNKNOWN_HELD_MARK:{day}:{pos['code']}")
                break
            if row["market"] != pos["market"]:
                issues.append(f"UNSUPPORTED_HELD_MARKET_CHANGE:{day}:{pos['code']}")
                break
            if not row["can_sell"]:
                if day >= pos["expiry"] or (
                    row["regular_session_trigger_valid"]
                    and row["volume"] > 0
                    and (0 < row["low"] <= pos["stop"] or row["high"] >= pos["target"])
                ):
                    pos["pending_exit"] = True
                continue
            if pos["pending_exit"] or day >= pos["expiry"]:
                sell(sleeve, day, row["open"], "deferred_or_expiry_open")
            elif row["open"] <= pos["stop"]:
                sell(sleeve, day, row["open"], "stop_gap_open")
            elif row["open"] >= pos["target"]:
                sell(sleeve, day, row["open"], "target_gap_open")
        if issues:
            break
        entered = {}
        for sleeve, plan in assigned:
            code, limit = plan["code"], plan["limit"]
            order = dict(
                date=day,
                signal_date=plan["signal_date"],
                slot_id=sleeve.slot_id,
                code=code,
                limit=limit,
                status="UNFILLED",
            )
            orders.append(order)
            row = bars.get((day, code))
            if row is None:
                issues.append(f"UNKNOWN_ORDER_BAR:{day}:{code}")
                break
            if not row["order_eligible"] or not row["can_buy"]:
                order["status"] = "INELIGIBLE_OR_UNTRADEABLE"
                continue
            if sleeve.position is not None or sleeve.reusable_from > day:
                raise ValueError("INVALID_SLOT_ASSIGNMENT")
            # Quantity is reserved at the limit before observing the fill.
            lo, hi = (
                0,
                int((sleeve.cash / limit).to_integral_value(rounding=ROUND_FLOOR)),
            )
            while lo < hi:
                mid = (lo + hi + 1) // 2
                if (
                    mid * limit + fee("BUY", day, row["market"], mid * limit)
                    <= sleeve.cash
                ):
                    lo = mid
                else:
                    hi = mid - 1
            if lo == 0:
                order["status"] = "INSUFFICIENT_CASH"
                continue
            order["planned_size"] = lo
            order["liquidity_limit"] = plan["mean_turnover20"] * Decimal("0.01")
            if lo * limit > order["liquidity_limit"]:
                order["status"] = "BUY_LIQUIDITY_LIMIT_EXCEEDED"
                continue
            if row["open"] <= limit:
                price, phase = row["open"], "OPEN"
            elif row["low"] < limit:
                price, phase = limit, "INTRADAY"
            else:
                continue
            charge = fee("BUY", day, row["market"], lo * price)
            sleeve.cash -= lo * price + charge
            if sleeve.cash < 0:
                raise ValueError("COST_FUNCTION_NOT_MONOTONE")
            stop_level = level("STOP", day, row["market"], price * (1 - stop))
            target_level = level("TARGET", day, row["market"], price * (1 + target))
            if not stop_level < price < target_level:
                raise ValueError("INVALID_ROUNDED_EXIT_LEVELS")
            sleeve.position = dict(
                code=code,
                market=row["market"],
                size=lo,
                entry_price=price,
                stop=stop_level,
                target=target_level,
                expiry=day + pd.DateOffset(months=holding_months),
                pending_exit=False,
            )
            entered[sleeve.slot_id] = phase
            order["status"] = "FILLED"
            fills.append(
                dict(
                    date=day,
                    slot_id=sleeve.slot_id,
                    code=code,
                    side="BUY",
                    size=lo,
                    price=price,
                    cost=charge,
                    reason=phase,
                )
            )
        if issues:
            break
        for sleeve in sleeves:
            pos = sleeve.position
            if pos is None:
                continue
            if (day, sleeve.slot_id) in attempted_exits:
                continue
            row = bars[day, pos["code"]]
            if not row["mark_valid"]:
                issues.append(f"UNKNOWN_HELD_MARK:{day}:{pos['code']}")
                break
            stop_hit = 0 < row["low"] <= pos["stop"]
            intraday_entry = entered.get(sleeve.slot_id) == "INTRADAY"
            target_hit = (row["close"] if intraday_entry else row["high"]) >= pos[
                "target"
            ]
            if not row["can_sell"]:
                if day >= pos["expiry"] or (
                    row["regular_session_trigger_valid"]
                    and row["volume"] > 0
                    and (stop_hit or target_hit)
                ):
                    pos["pending_exit"] = True
                continue
            if (
                intraday_entry
                and row["high"] >= pos["target"]
                and row["close"] < pos["target"]
            ):
                diagnostics.append(
                    dict(
                        date=day,
                        slot_id=sleeve.slot_id,
                        code=pos["code"],
                        kind="intraday_preentry_high_possible",
                        action="STOP" if stop_hit else "HOLD",
                    )
                )
            if stop_hit and row["high"] >= pos["target"]:
                diagnostics.append(
                    dict(
                        date=day,
                        slot_id=sleeve.slot_id,
                        code=pos["code"],
                        kind="simultaneous_stop_target",
                        action="TARGET"
                        if optimistic and not intraday_entry
                        else "STOP",
                    )
                )
            # Optimistic tie order is a sensitivity for positions known to
            # exist at the open, never permission to use pre-entry highs.
            if stop_hit and target_hit and optimistic and not intraday_entry:
                sell(sleeve, day, pos["target"], "ambiguous_target_first")
            elif stop_hit:
                sell(
                    sleeve,
                    day,
                    pos["stop"],
                    "ambiguous_stop_first" if target_hit else "stop_intraday",
                )
            elif target_hit:
                sell(sleeve, day, pos["target"], "target_intraday")
        if issues:
            break
        total = Decimal(0)
        for sleeve in sleeves:
            pos = sleeve.position
            exposure = (
                Decimal(0)
                if pos is None
                else pos["size"] * bars[day, pos["code"]]["close"]
            )
            total += sleeve.cash + exposure
            positions.append(
                dict(
                    date=day,
                    slot_id=sleeve.slot_id,
                    cash=sleeve.cash,
                    code=None if pos is None else pos["code"],
                    size=0 if pos is None else pos["size"],
                    exposure=exposure,
                    equity=sleeve.cash + exposure,
                )
            )
        equity.append(
            dict(
                date=day,
                equity=total,
                cash=sum(s.cash for s in sleeves),
                positions_count=sum(s.position is not None for s in sleeves),
            )
        )
        assign(day)
        prior_day = day
    return dict(
        status="BLOCKED" if issues else "SUCCEEDED",
        source_kind="SYNTHETIC",
        performance_valid=False,
        issues=issues,
        fills=pd.DataFrame(fills),
        orders=pd.DataFrame(orders),
        diagnostics=pd.DataFrame(
            diagnostics, columns=["date", "slot_id", "code", "kind", "action"]
        ),
        equity=pd.DataFrame([] if issues else equity),
        positions=pd.DataFrame([] if issues else positions),
        limitations=[
            "SYNTHETIC_ONLY",
            "ECONOMIC_BUYING_POWER_NOT_SETTLED_CASH",
            "EXTERNAL_MARKET_AND_LIQUIDITY_FLAGS",
            "NO_CORPORATE_ENTITLEMENT_MODEL",
            "DAILY_VOLUME_CAP_DOES_NOT_PROVE_INTRADAY_FILL_CAPACITY",
        ],
    )
