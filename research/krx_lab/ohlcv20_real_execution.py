"""Rights-aware 20-slot portfolio execution on explicitly admitted daily facts.

The fixture and real paths share calculations. Real execution requires every
input-admission flag to be positively set by an external verified adapter;
the currently delivered corrected-v4 package does not meet that gate. A
position is marked every session or the result is blocked without performance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_FLOOR, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable

import pandas as pd

from .ohlcv20_execution import _d, _day
from .ohlcv20_rights import RightsLedger


_ADMISSION_FLAGS = (
    "immutable_input_verified",
    "daily_universe_admitted",
    "adjusted_price_admitted",
    "volume_factors_admitted",
    "corporate_coverage_admitted",
    "rights_admitted",
    "market_rules_admitted",
    "real_execution_admitted",
)
# Explicit non-admitted exploration. It never sets performance_valid and needs
# a caller-supplied rule that voids a held trade at the session it meets an
# event the unadmitted ledgers cannot settle.
EXPLORATORY_SOURCE_KIND = "EXPLORATORY_NOT_ADMITTED"


def _verify_real_admission(admission: dict | None, rights_ledger: RightsLedger) -> None:
    if not isinstance(admission, dict) or any(
        admission.get(key) is not True for key in _ADMISSION_FLAGS
    ):
        raise ValueError("REAL_EXECUTION_NOT_ADMITTED")
    try:
        source_path = Path(admission["source_manifest_path"])
        receipt_path = Path(admission["admission_evidence_path"])
        expected_receipt_sha = admission["admission_evidence_sha256"]
        source_bytes, receipt_bytes = (
            source_path.read_bytes(),
            receipt_path.read_bytes(),
        )
    except (KeyError, TypeError, OSError) as exc:
        raise ValueError("REAL_ADMISSION_EVIDENCE_MISSING") from exc
    if sha256(receipt_bytes).hexdigest() != expected_receipt_sha:
        raise ValueError("REAL_ADMISSION_EVIDENCE_HASH_MISMATCH")
    source, receipt = json.loads(source_bytes), json.loads(receipt_bytes)
    if (
        receipt.get("schema") != "ohlcv20-real-admission-v1"
        or receipt.get("status") != "ADMITTED"
        or any(receipt.get(key) is not True for key in _ADMISSION_FLAGS)
        or source.get("real_execution_admitted") is not True
        or receipt.get("source_manifest_sha256") != sha256(source_bytes).hexdigest()
        or not rights_ledger.source_sha256
        or receipt.get("rights_terms_sha256") != rights_ledger.source_sha256
    ):
        raise ValueError("REAL_ADMISSION_EVIDENCE_NOT_BOUND")


def _fraction(value: Decimal | Fraction | int) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def _money(value: Fraction) -> Decimal:
    with localcontext() as context:
        context.prec = 38
        return Decimal(value.numerator) / Decimal(value.denominator)


@dataclass
class _Sleeve:
    slot_id: int
    cash: Fraction
    idle_since: pd.Timestamp
    reusable_from: pd.Timestamp
    positions: dict[str, dict] = field(default_factory=dict)
    captured_event: str | None = None


def run_ohlcv20_portfolio(
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
    rights_ledger: RightsLedger,
    event_schedule=None,
    admission: dict | None = None,
    source_kind: str = "REAL",
    initial_cash=100_000_000,
    optimistic: bool = False,
    exploratory_void: Callable | None = None,
) -> dict:
    """Execute confirmed rules, including two-leg forced corporate exits.

    `event_schedule` requires event_code, capture_on and available_on. The
    external adapter must prove the capture session has qualifying settled
    ownership and that all replacement shares are available on available_on.

    Only `source_kind=EXPLORATORY_SOURCE_KIND` accepts `exploratory_void`,
    called as (day, code, bar_or_None) for every trade held into a session
    before any order. A returned dict voids that trade: its fills leave the
    ledger, the slot gets its pre-entry cash back, the equity curve carries
    the slot at that cash from entry, and the slot is reusable from `day`.
    """
    if source_kind not in {"REAL", "SYNTHETIC_FIXTURE", EXPLORATORY_SOURCE_KIND}:
        raise ValueError("UNKNOWN_EXECUTION_SOURCE_KIND")
    if source_kind == "REAL":
        _verify_real_admission(admission, rights_ledger)
    exploratory = source_kind == EXPLORATORY_SOURCE_KIND
    if exploratory != (exploratory_void is not None):
        raise ValueError("EXPLORATORY_VOID_RULE_ONLY_WITH_EXPLORATORY_SOURCE")
    if exploratory and event_schedule is not None:
        raise ValueError("EXPLORATORY_RUN_VOIDS_INSTEAD_OF_RIGHTS_SCHEDULE")
    if holding_months not in (1, 3) or type(holding_months) is not int:
        raise ValueError("HOLDING_MONTHS_MUST_BE_1_OR_3")
    stop, target, capital = _d(stop_pct), _d(target_pct), _d(initial_cash)
    if not 0 < stop < 1 or target <= 0 or capital <= 0:
        raise ValueError("INVALID_STRATEGY_AMOUNTS")
    first, last = _day(start), _day(end)
    days = [_day(day) for day in calendar]
    if (
        not days
        or days != sorted(set(days))
        or first > last
        or first < days[0]
        or last > days[-1]
    ):
        raise ValueError("INVALID_CALENDAR_COVERAGE")
    evaluation = [day for day in days if first <= day <= last]
    if not evaluation:
        raise ValueError("EMPTY_EVALUATION")
    next_day = dict(zip(days[:-1], days[1:]))
    rights_book = RightsLedger(
        rights_ledger.events, source_sha256=rights_ledger.source_sha256
    )

    bars = {}
    for row in pd.DataFrame(prices).to_dict("records"):
        day, code = _day(row["date"]), str(row["code"])
        if day not in days or (day, code) in bars:
            raise ValueError("DUPLICATE_OR_OFF_CALENDAR_BAR")
        for flag in ("can_buy", "can_sell", "order_eligible", "mark_valid"):
            if type(row[flag]) is not bool:
                raise ValueError("EXPLICIT_BOOLEAN_REQUIRED:" + flag)
        if row.get("listing_status") not in {"LISTED", "DELISTED"}:
            raise ValueError("EXPLICIT_LISTING_STATUS_REQUIRED")
        if (
            row.get("listing_status_verified") is not True
            or type(row["listing_status_verified"]) is not bool
        ):
            raise ValueError("VERIFIED_LISTING_STATUS_REQUIRED")
        sell_status = row.get("sell_status")
        if sell_status not in {
            "SELLABLE",
            "HALTED",
            "NO_TRADE",
            "LOWER_LIMIT_LOCKED",
        }:
            raise ValueError("EXPLICIT_SELL_STATUS_REQUIRED")
        if (
            row.get("sell_status_verified") is not True
            or type(row["sell_status_verified"]) is not bool
        ):
            raise ValueError("VERIFIED_SELL_STATUS_REQUIRED")
        if row["can_sell"] != (sell_status == "SELLABLE"):
            raise ValueError("SELL_STATUS_CAN_SELL_CONFLICT")
        if row["listing_status"] == "DELISTED" and (row["can_buy"] or row["can_sell"]):
            raise ValueError("DELISTED_TRADE_STATUS_CONFLICT")
        for optional_flag in (
            "regular_session_trigger_valid",
            "rights_suspension_verified",
        ):
            value = row.get(optional_flag, False)
            if pd.isna(value):
                value = False
            if type(value) is not bool:
                raise ValueError("EXPLICIT_BOOLEAN_REQUIRED:" + optional_flag)
            row[optional_flag] = value
        for key in ("open", "high", "low", "close", "volume"):
            row[key] = _d(row[key])
        lower_limit = row.get("lower_limit_price")
        if lower_limit is None or pd.isna(lower_limit):
            if source_kind == "REAL" and (row["can_buy"] or row["can_sell"]):
                raise ValueError("VERIFIED_LOWER_LIMIT_PRICE_REQUIRED")
        else:
            if row.get("lower_limit_price_verified") is not True:
                raise ValueError("VERIFIED_LOWER_LIMIT_PRICE_REQUIRED")
            row["lower_limit_price"] = _d(lower_limit)
            if row["lower_limit_price"] <= 0:
                raise ValueError("INVALID_LOWER_LIMIT_PRICE")
            if (
                row["can_sell"]
                and row["open"]
                == row["high"]
                == row["low"]
                == row["close"]
                == row["lower_limit_price"]
            ):
                raise ValueError("LOWER_LIMIT_LOCKED_SELL_STATUS_CONFLICT")
        if row["volume"] < 0 or (row["mark_valid"] and row["close"] <= 0):
            raise ValueError("INVALID_BAR_MARK_OR_VOLUME")
        if row["can_buy"] or row["can_sell"]:
            if (
                row["volume"] <= 0
                or row["low"] <= 0
                or row["low"] > min(row["open"], row["close"])
                or row["high"] < max(row["open"], row["close"])
            ):
                raise ValueError("INVALID_EXECUTABLE_OHLCV")
        bars[day, code] = row

    signal_days: dict[pd.Timestamp, list[dict]] = {}
    signal_keys = set()
    for row in pd.DataFrame(signals).to_dict("records"):
        day, code = _day(row["signal_date"]), str(row["code"])
        if day not in days or (day, code) in signal_keys:
            raise ValueError("DUPLICATE_OR_OFF_CALENDAR_SIGNAL")
        signal_keys.add((day, code))
        if type(row["eligible"]) is not bool:
            raise ValueError("EXPLICIT_SIGNAL_ELIGIBILITY_REQUIRED")
        turnover, mean, limit = (
            _d(row["turnover"]),
            _d(row["mean_turnover20"]),
            _d(row["limit_price"]),
        )
        if turnover < 0 or mean <= 0 or limit <= 0:
            raise ValueError("INVALID_SIGNAL_AMOUNTS")
        if row["eligible"]:
            signal_days.setdefault(day, []).append(
                dict(code=code, turnover=turnover, mean=mean, limit=limit)
            )

    schedule = {}
    for row in pd.DataFrame(
        event_schedule if event_schedule is not None else []
    ).to_dict("records"):
        code = str(row["event_code"])
        capture, available = _day(row["capture_on"]), _day(row["available_on"])
        if code in schedule or code not in rights_book.events:
            raise ValueError("DUPLICATE_OR_UNKNOWN_RIGHTS_EVENT")
        record = pd.Timestamp(rights_book.events[code].record_date)
        if (
            capture not in days
            or available not in days
            or not capture <= record < available
        ):
            raise ValueError("INVALID_RIGHTS_EVENT_SCHEDULE")
        schedule[code] = dict(capture=capture, available=available, record=record)
    if source_kind == "REAL" and set(schedule) != set(rights_book.events):
        raise ValueError("INCOMPLETE_RIGHTS_EVENT_SCHEDULE")

    sleeves = [_Sleeve(i, _fraction(capital) / 20, first, first) for i in range(20)]
    fills, orders, equity, positions, issues, diagnostics = [], [], [], [], [], []
    rights_events, cash_receipts = [], []
    assignments: dict[pd.Timestamp, list[tuple[_Sleeve, dict]]] = {}
    sold_by_day_code: dict[tuple[pd.Timestamp, str], int] = {}
    attempted_exits: set[tuple[pd.Timestamp, int, str]] = set()
    converted_rights: set[tuple[str, int]] = set()
    # Exploratory-only books: per-session exact totals and per-slot
    # (cash, value) so a voided trade can be carried at pre-entry cash.
    evaluation_index = {day: i for i, day in enumerate(evaluation)}
    exact_equity: list[Fraction] = []
    exact_cash: list[Fraction] = []
    slot_history: list[list[tuple[Fraction, Fraction]]] = []
    exclusions: list[dict] = []

    def void_trade(sleeve: _Sleeve, pos: dict, day: pd.Timestamp, reason: dict) -> None:
        code, entry_day, restored = pos["code"], pos["entry_day"], pos["pre_entry_cash"]
        for i in range(evaluation_index[entry_day], len(equity)):
            cash_i, value_i = slot_history[i][sleeve.slot_id]
            exact_equity[i] += restored - value_i
            exact_cash[i] += restored - cash_i
            slot_history[i][sleeve.slot_id] = (restored, restored)
            equity[i]["equity"] = _money(exact_equity[i])
            equity[i]["cash"] = _money(exact_cash[i])
            equity[i]["positions_count"] -= 1

        def owned(item: dict) -> bool:
            return (
                item["slot_id"] == sleeve.slot_id
                and item["code"] == code
                and item["date"] >= entry_day
            )

        voided_fills = [item for item in fills if owned(item)]
        fills[:] = [item for item in fills if not owned(item)]
        positions[:] = [
            dict(
                item,
                code=None,
                size=0,
                mark_price=None,
                exposure=Decimal(0),
                pending_exit=False,
                forced_event=None,
            )
            if owned(item)
            else item
            for item in positions
        ]
        exclusions.append(
            dict(
                date=day,
                slot_id=sleeve.slot_id,
                code=code,
                entry_date=entry_day,
                entry_price=pos["entry_price"],
                restored_cash=_money(restored),
                voided_fills=len(voided_fills),
                **reason,
            )
        )
        del sleeve.positions[code]
        sleeve.cash = restored
        sleeve.captured_event = None
        sleeve.idle_since = day
        sleeve.reusable_from = day

    def fee(side, day, market, amount: Decimal) -> Fraction:
        charge = _d(costs(side, day, market, amount))
        if charge < 0:
            raise ValueError("NEGATIVE_COST")
        return _fraction(charge)

    def level(side, day, market, value: Decimal) -> Decimal:
        rounded = _d(levels(side, day, market, value))
        if rounded <= 0:
            raise ValueError("NONPOSITIVE_ORDER_LEVEL")
        return rounded

    def finalize_slot(sleeve: _Sleeve, day: pd.Timestamp) -> None:
        if sleeve.positions:
            return
        sleeve.captured_event = None
        sleeve.idle_since = day
        sleeve.reusable_from = next_day.get(day, day + pd.Timedelta(days=1))

    def sell(
        sleeve: _Sleeve, pos: dict, day: pd.Timestamp, price: Decimal, reason: str
    ) -> None:
        code = pos["code"]
        pos["pending_exit"] = True
        attempted_exits.add((day, sleeve.slot_id, code))
        key = (day, code)
        capacity = int(
            (bars[key]["volume"] * Decimal("0.01")).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        remaining_capacity = max(0, capacity - sold_by_day_code.get(key, 0))
        quantity = min(pos["size"], remaining_capacity)
        if quantity < pos["size"]:
            diagnostics.append(
                dict(
                    date=day,
                    slot_id=sleeve.slot_id,
                    code=code,
                    kind="daily_sell_volume_cap",
                    action="DEFER_REMAINDER",
                )
            )
        if quantity == 0:
            return
        amount = quantity * price
        charge = fee("SELL", day, pos["market"], amount)
        sleeve.cash += _fraction(amount) - charge
        if sleeve.cash < 0:
            raise ValueError("SELL_COST_EXCEEDS_SLOT_ASSETS")
        fills.append(
            dict(
                date=day,
                slot_id=sleeve.slot_id,
                code=code,
                side="SELL",
                size=quantity,
                price=price,
                cost=_money(charge),
                reason=reason,
            )
        )
        sold_by_day_code[key] = sold_by_day_code.get(key, 0) + quantity
        pos["size"] -= quantity
        if pos["size"] == 0:
            del sleeve.positions[code]
            finalize_slot(sleeve, day)

    def assign(signal_day: pd.Timestamp) -> None:
        order_day = next_day.get(signal_day)
        if order_day is None:
            return
        held = {code for sleeve in sleeves for code in sleeve.positions}
        candidates = sorted(
            (r for r in signal_days.get(signal_day, []) if r["code"] not in held),
            key=lambda r: (-r["turnover"], r["code"]),
        )
        idle = sorted(
            (s for s in sleeves if not s.positions and s.reusable_from <= order_day),
            key=lambda s: (s.idle_since, s.slot_id),
        )
        assignments[order_day] = [
            (s, dict(r, signal_date=signal_day)) for s, r in zip(idle, candidates)
        ]

    index = days.index(evaluation[0])
    if index:
        assign(days[index - 1])
    for day in evaluation:
        # Rights cash belongs to its original slot even if it was reused.
        for receipt in rights_book.due_cash(day):
            sleeves[receipt.slot_id].cash += receipt.amount
            cash_receipts.append(
                dict(
                    date=day,
                    due_date=receipt.due_date,
                    slot_id=receipt.slot_id,
                    event_code=receipt.event_code,
                    code=receipt.leg_code,
                    amount=_money(receipt.amount),
                    exact_numerator=receipt.amount.numerator,
                    exact_denominator=receipt.amount.denominator,
                )
            )

        if exploratory:
            for sleeve in sleeves:
                for pos in list(sleeve.positions.values()):
                    reason = exploratory_void(day, pos["code"], bars.get((day, pos["code"])))
                    if reason is not None:
                        void_trade(sleeve, pos, day, dict(reason))

        for code, event in schedule.items():
            if day != event["available"]:
                continue
            for sleeve in sleeves:
                if sleeve.captured_event != code:
                    continue
                old = sleeve.positions.get(code)
                if old is None:
                    issues.append(
                        f"CAPTURED_RIGHTS_POSITION_MISSING:{day}:{code}:{sleeve.slot_id}"
                    )
                    break
                conversion = rights_book.convert(code, sleeve.slot_id, available_on=day)
                if conversion.old_shares_removed != old["size"]:
                    issues.append(
                        f"RIGHTS_QUANTITY_MISMATCH:{day}:{code}:{sleeve.slot_id}"
                    )
                    break
                converted_rights.add((code, sleeve.slot_id))
                del sleeve.positions[code]
                sleeve.captured_event = None
                for leg in conversion.allocations:
                    if leg.shares == 0:
                        continue
                    row = bars.get((day, leg.code))
                    if row is None or not row["mark_valid"]:
                        issues.append(f"UNKNOWN_RIGHTS_LEG_MARK:{day}:{leg.code}")
                        break
                    sleeve.positions[leg.code] = dict(
                        code=leg.code,
                        market=row["market"],
                        size=leg.shares,
                        entry_price=None,
                        stop=None,
                        target=None,
                        expiry=day,
                        pending_exit=True,
                        forced_event=code,
                    )
                    rights_events.append(
                        dict(
                            date=day,
                            slot_id=sleeve.slot_id,
                            event_code=code,
                            code=leg.code,
                            old_shares_removed=conversion.old_shares_removed,
                            new_shares=leg.shares,
                            fractional_numerator=leg.fractional_shares.numerator,
                            fractional_denominator=leg.fractional_shares.denominator,
                        )
                    )
                if issues:
                    break
                finalize_slot(sleeve, day)
            if issues:
                break
        if issues:
            break

        # Existing holdings and forced new legs sell before next-day entry orders.
        for sleeve in sleeves:
            for pos in list(sleeve.positions.values()):
                code = pos["code"]
                row = bars.get((day, code))
                if (
                    row is None
                    or not row["mark_valid"]
                    or row["market"] != pos["market"]
                ):
                    issues.append(f"UNKNOWN_HELD_MARK:{day}:{code}")
                    break
                if row["listing_status"] == "DELISTED":
                    issues.append(f"UNVALUED_DELISTED_HOLDING:{day}:{code}")
                    break
                if sleeve.captured_event == code:
                    if row["can_sell"] or not row["rights_suspension_verified"]:
                        issues.append(
                            f"CAPTURED_RIGHTS_SUSPENSION_NOT_VERIFIED:{day}:{code}"
                        )
                        break
                    continue  # Verified suspension until replacement shares arrive.
                if not row["can_sell"]:
                    if day >= pos["expiry"] or (
                        row["regular_session_trigger_valid"]
                        and row["volume"] > 0
                        and pos["stop"] is not None
                        and (row["low"] <= pos["stop"] or row["high"] >= pos["target"])
                    ):
                        pos["pending_exit"] = True
                    continue
                if pos["pending_exit"] or day >= pos["expiry"]:
                    sell(
                        sleeve,
                        pos,
                        day,
                        row["open"],
                        "rights_or_deferred_or_expiry_open",
                    )
                elif row["open"] <= pos["stop"]:
                    sell(sleeve, pos, day, row["open"], "stop_gap_open")
                elif row["open"] >= pos["target"]:
                    sell(sleeve, pos, day, row["open"], "target_gap_open")
            if issues:
                break
        if issues:
            break

        entered: dict[tuple[int, str], str] = {}
        for sleeve, plan in assignments.get(day, []):
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
            if sleeve.positions or sleeve.reusable_from > day:
                raise ValueError("INVALID_SLOT_ASSIGNMENT")
            if any(code in other.positions for other in sleeves):
                order["status"] = "ALREADY_HELD"
                continue
            if sum(len(other.positions) for other in sleeves) >= 20:
                order["status"] = "POSITION_LIMIT_EXCESS"
                continue
            lo, hi = (
                0,
                int(
                    (sleeve.cash / _fraction(limit)).numerator
                    // (sleeve.cash / _fraction(limit)).denominator
                ),
            )
            while lo < hi:
                mid = (lo + hi + 1) // 2
                amount = mid * limit
                if (
                    _fraction(amount) + fee("BUY", day, row["market"], amount)
                    <= sleeve.cash
                ):
                    lo = mid
                else:
                    hi = mid - 1
            if lo == 0:
                order["status"] = "INSUFFICIENT_CASH"
                continue
            order["planned_size"] = lo
            order["liquidity_limit"] = plan["mean"] * Decimal("0.01")
            if lo * limit > order["liquidity_limit"]:
                # Assignment was fixed at signal close. Do not pass this candidate
                # to a smaller slot or replace it with another candidate today.
                order["status"] = "BUY_LIQUIDITY_LIMIT_EXCEEDED"
                continue
            if row["open"] <= limit:
                price, phase = row["open"], "OPEN"
            elif row["low"] < limit:
                price, phase = limit, "INTRADAY"
            else:
                continue
            amount = lo * price
            charge = fee("BUY", day, row["market"], amount)
            pre_entry_cash = sleeve.cash
            sleeve.cash -= _fraction(amount) + charge
            if sleeve.cash < 0:
                raise ValueError("COST_FUNCTION_NOT_MONOTONE")
            stop_level = level("STOP", day, row["market"], price * (1 - stop))
            target_level = level("TARGET", day, row["market"], price * (1 + target))
            if not stop_level < price < target_level:
                raise ValueError("INVALID_ROUNDED_EXIT_LEVELS")
            sleeve.positions[code] = dict(
                code=code,
                market=row["market"],
                size=lo,
                entry_price=price,
                stop=stop_level,
                target=target_level,
                expiry=day + pd.DateOffset(months=holding_months),
                pending_exit=False,
                forced_event=None,
                entry_day=day,
                pre_entry_cash=pre_entry_cash,
            )
            entered[sleeve.slot_id, code] = phase
            order["status"] = "FILLED"
            fills.append(
                dict(
                    date=day,
                    slot_id=sleeve.slot_id,
                    code=code,
                    side="BUY",
                    size=lo,
                    price=price,
                    cost=_money(charge),
                    reason=phase,
                )
            )
        if issues:
            break

        for sleeve in sleeves:
            for pos in list(sleeve.positions.values()):
                code = pos["code"]
                if (
                    sleeve.captured_event == code
                    or (day, sleeve.slot_id, code) in attempted_exits
                ):
                    continue
                row = bars[day, code]
                if pos["forced_event"] is not None:
                    continue  # Forced leg exits are always at the next sellable open.
                stop_hit = row["low"] <= pos["stop"]
                intraday_entry = entered.get((sleeve.slot_id, code)) == "INTRADAY"
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
                if stop_hit and target_hit and optimistic and not intraday_entry:
                    sell(sleeve, pos, day, pos["target"], "ambiguous_target_first")
                elif stop_hit:
                    sell(
                        sleeve,
                        pos,
                        day,
                        pos["stop"],
                        "ambiguous_stop_first" if target_hit else "stop_intraday",
                    )
                elif target_hit:
                    sell(sleeve, pos, day, pos["target"], "target_intraday")

        for code, event in schedule.items():
            if event["capture"] != day:
                continue
            for sleeve in sleeves:
                pos = sleeve.positions.get(code)
                if pos is None:
                    continue
                if sleeve.captured_event is not None:
                    issues.append(
                        f"OVERLAPPING_RIGHTS_EVENTS:{day}:{code}:{sleeve.slot_id}"
                    )
                    break
                rights_book.capture(
                    code, sleeve.slot_id, pos["size"], record_date=event["record"]
                )
                sleeve.captured_event = code
            if issues:
                break
        if issues:
            break

        receivables = sum(
            (
                item.amount
                for item in rights_book.pending_cash()
                if (item.event_code, item.slot_id) in converted_rights
            ),
            Fraction(),
        )
        total = receivables
        slot_values: list[tuple[Fraction, Fraction]] = []
        for sleeve in sleeves:
            exposure = Fraction()
            for pos in sleeve.positions.values():
                row = bars.get((day, pos["code"]))
                if row is None or not row["mark_valid"]:
                    issues.append(f"UNKNOWN_HELD_MARK:{day}:{pos['code']}")
                    break
                mark = _fraction(pos["size"] * row["close"])
                exposure += mark
                positions.append(
                    dict(
                        date=day,
                        slot_id=sleeve.slot_id,
                        code=pos["code"],
                        size=pos["size"],
                        mark_price=row["close"],
                        exposure=_money(mark),
                        pending_exit=pos["pending_exit"],
                        forced_event=pos["forced_event"],
                    )
                )
            if issues:
                break
            total += sleeve.cash + exposure
            slot_values.append((sleeve.cash, sleeve.cash + exposure))
            if not sleeve.positions:
                positions.append(
                    dict(
                        date=day,
                        slot_id=sleeve.slot_id,
                        code=None,
                        size=0,
                        mark_price=None,
                        exposure=Decimal(0),
                        pending_exit=False,
                        forced_event=None,
                    )
                )
        if issues:
            break
        if exploratory:
            slot_history.append(slot_values)
            exact_equity.append(total)
            exact_cash.append(sum((s.cash for s in sleeves), Fraction()))
        equity.append(
            dict(
                date=day,
                equity=_money(total),
                cash=_money(sum((s.cash for s in sleeves), Fraction())),
                receivables=_money(receivables),
                positions_count=sum(len(s.positions) for s in sleeves),
            )
        )
        assign(day)

    if not issues and any(sleeve.captured_event is not None for sleeve in sleeves):
        issues.append("UNCONVERTED_RIGHTS_AT_EVALUATION_END")
    blocked = bool(issues)
    result = dict(
        status="BLOCKED" if blocked else "SUCCEEDED",
        source_kind=source_kind,
        performance_valid=source_kind == "REAL" and not blocked,
        issues=issues,
        fills=pd.DataFrame(fills),
        orders=pd.DataFrame(orders),
        equity=pd.DataFrame([] if blocked else equity),
        positions=pd.DataFrame([] if blocked else positions),
        rights_events=pd.DataFrame(rights_events),
        cash_receipts=pd.DataFrame(cash_receipts),
        diagnostics=pd.DataFrame(diagnostics),
        limitations=[
            "CASH_DIVIDENDS_EXCLUDED",
            "DAILY_VOLUME_PROXY_NOT_INTRADAY_PROOF",
            "FRACTIONAL_WON_CASH_MODELLED_AS_EXACT_RATIONAL",
            "CORPORATE_SUSPENSION_MARKS_REQUIRE_EXTERNAL_VALIDATION",
        ],
    )
    if exploratory:
        result["exclusions"] = pd.DataFrame(exclusions)
    return result
