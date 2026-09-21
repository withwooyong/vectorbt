"""Execute pre-holdout conditional slots on explicit synthetic C1 deliveries only."""

from __future__ import annotations

import math
import numbers
from collections.abc import Mapping
from copy import deepcopy

import pandas as pd

from .contracts import ContractError, ExecutionHooks, validate_delivery
from .corporate_actions import CorporateActionBook, contract_ledger
from .execution import _Position, simulate_delivery
from .market_model import MarketModel
from .vectorbt_check import reconcile_ledger


_SPEC_FIELDS = (
    "phase", "conditional_slot", "strategy_id", "entry_id", "exit_id", "policy", "period",
    "start", "end", "cost_bps", "delay", "optimistic", "control", "requires_holdout",
)


def _pre_holdout_dates(value):
    """Reject future dates even in unused calendar, event, or provenance rows."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            if item is not None and (key in {"date", "start", "end"}
                                     or key.endswith(("_date", "_from", "_to", "_at"))):
                day = pd.Timestamp(item)
                if pd.isna(day):
                    raise ContractError("INVALID_DATE", key)
                if day.year >= 2024:
                    raise ContractError("HOLDOUT_LOCKED", key)
            elif isinstance(item, (Mapping, list)):
                _pre_holdout_dates(item)
    elif isinstance(value, list):
        for item in value:
            _pre_holdout_dates(item)


def _validate_slot(delivery, signals, spec, initial_cash):
    if not isinstance(spec, Mapping):
        raise ValueError("spec must be a mapping")
    missing = set(_SPEC_FIELDS) - set(spec)
    if missing:
        raise ValueError(f"spec missing required fields: {sorted(missing)}")
    if delivery.get("source_kind") != "SYNTHETIC":
        raise ContractError("REAL_EXECUTION_NOT_ADMITTED")
    checked = validate_delivery(delivery)
    _pre_holdout_dates(checked)
    _pre_holdout_dates(spec)
    if type(spec["requires_holdout"]) is not bool:
        raise ValueError("requires_holdout must be boolean")
    if spec["control"] not in {None, "cash", "buy_hold"}:
        raise ValueError("unsupported control")
    if type(spec["optimistic"]) is not bool:
        raise ValueError("optimistic must be boolean")
    if not isinstance(spec["delay"], numbers.Integral) or isinstance(spec["delay"], bool) or spec["delay"] < 1:
        raise ValueError("delay must be at least 1 trading day")
    if not isinstance(initial_cash, numbers.Real) or isinstance(initial_cash, bool) or not math.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be finite and positive")
    for key in ("phase", "strategy_id"):
        if not isinstance(spec[key], str) or not spec[key].strip():
            raise ValueError(f"{key} must be nonempty text")
    if type(spec["conditional_slot"]) is not int or spec["conditional_slot"] < 0:
        raise ValueError("conditional_slot must be a nonnegative integer")
    if spec["control"] is None and spec["policy"] not in {"fixed20", "staged10_15_20"}:
        raise ValueError("unsupported strategy policy")
    start, end = pd.Timestamp(spec["start"]), pd.Timestamp(spec["end"])
    if start.tzinfo is not None or end.tzinfo is not None or start != start.normalize() or end != end.normalize():
        raise ValueError("slot bounds must be timezone-naive dates")
    if start > end:
        raise ValueError("end must be on or after start")
    if start < pd.Timestamp(checked["metadata"]["start"]) or end > pd.Timestamp(checked["metadata"]["end"]):
        raise ValueError("EXECUTION_OUTSIDE_DELIVERY_RANGE")
    if not isinstance(signals, pd.DataFrame):
        raise ValueError("signals must be a pandas DataFrame")
    if not signals.empty and "date" not in signals:
        raise ValueError("signals requires date")
    if "date" in signals:
        _pre_holdout_dates(signals[["date"]].to_dict("records"))
    realistic = spec["phase"] == "realistic-costs"
    cost = spec["cost_bps"]
    if realistic:
        if cost is not None:
            raise ValueError("realistic-costs requires null cost_bps")
    elif not isinstance(cost, numbers.Real) or isinstance(cost, bool) or not math.isfinite(cost) or not 0 <= cost <= 10_000:
        raise ValueError("cost_bps must be finite and between 0 and 10000")
    # validate_delivery returns a deep copy; replacement never changes C1 input.
    if not realistic:
        for profile in checked["market_profiles"]:
            profile.update(buy_fee_rate=float(cost) / 10_000, sell_fee_rate=float(cost) / 10_000,
                           sell_tax_rate=0.0)
    return checked, start, end


def _control(market, prices, spec, start, end, initial_cash, hooks):
    account = CorporateActionBook(market)
    buy_hold = spec["control"] == "buy_hold"
    benchmark = spec.get("benchmark_id")
    if buy_hold and (not isinstance(benchmark, str) or benchmark not in {
            row["instrument_id"] for row in market.delivery["instruments"]}):
        raise ValueError("UNSUPPORTED_BENCHMARK: benchmark_id must identify a C1 instrument")
    dates = {pd.Timestamp(day) for day in market.trading_dates if start <= pd.Timestamp(day) <= end}
    dates |= {pd.Timestamp(event["pay_date"]) for event in market.delivery["events"]
              if event.get("pay_date") is not None and start <= pd.Timestamp(event["pay_date"]) <= end}
    # Explicit end snapshot carries the last mark on non-session end dates.
    dates.add(end)
    rows = {(pd.Timestamp(row["date"]), row["code"]): row for row in prices.to_dict("records")}
    cash, bought = float(initial_cash), False
    positions, fills, orders, snapshots, equities, trades, issues = {}, [], [], [], [], [], []
    for day in sorted(dates):
        hooks("simulation_day", {"date": day.date().isoformat()})
        if buy_hold:
            cash += account.process(day, positions, [], trades)
        session = market.sessions.get(day.date().isoformat())
        is_open = session is not None and session["is_open"]
        row = rows.get((day, benchmark)) if buy_hold else None
        if buy_hold and not bought and row is not None and row["eligible"] and benchmark not in account.delisted:
            price = float(row["open"])
            rate = market.profile(benchmark, day)["buy_fee_rate"]
            size = math.floor(cash / (price * (1 + rate)))
            # Avoid a rounded quotient spending more than actual available cash.
            while size > 0 and size * price + size * price * rate > cash:
                size -= 1
            if size < 1:
                raise ValueError("BENCHMARK_UNAFFORDABLE")
            fee = size * price * rate
            cash -= size * price + fee
            fill_id, order_id = "fill-00000000", "order-00000000"
            sequence = account.record(day, benchmark, "BUY", cash_delta=-size * price - fee,
                                      fee=fee, fill_id=fill_id)
            common = dict(date=day, code=benchmark, side="buy", size=size, price=price,
                          fees=fee, phase="benchmark_entry_open", order_id=order_id)
            orders.append(dict(common, status="FILLED", reason=""))
            fills.append(dict(common, fill_seq=0, ledger_seq=sequence, fill_id=fill_id, fee=fee, tax=0.0))
            positions[benchmark] = _Position(benchmark, size, day, price, fee, 0.0, 0.0,
                                             pd.NaT, market.instrument(benchmark, day)["sector"], price)
            bought = True
        exposure = 0.0
        for code, pos in positions.items():
            if is_open:
                status = market.status(code, day)
                if status == "DELISTED" and code not in account.delisted:
                    raise ValueError(f"UNSETTLED_DELISTING:{day.date()}:{code}")
                if row is not None and math.isfinite(row["close"]) and row["close"] > 0:
                    pos.last_price, pos.stale = float(row["close"]), False
                else:
                    pos.stale = True
                    issues.append(f"STALE_PRICE:{day.date()}:{code}")
            exposure += pos.size * pos.last_price
            snapshots.append(dict(date=day, code=code, size=pos.size, entry_price=pos.entry_price,
                                  mark_price=pos.last_price, cost_basis=pos.size * pos.entry_price + pos.entry_fees,
                                  stale=pos.stale))
        equities.append(dict(date=day, cash=cash, receivables=account.receivables, payables=0.0,
                             exposure=exposure, equity=cash + account.receivables + exposure,
                             positions_count=len(positions)))
    if buy_hold and not bought:
        raise ValueError("NO_VALID_BENCHMARK_OPEN")
    result = dict(
        signals=pd.DataFrame(columns=["date", "code", "entry_id", "entry_signal"]),
        plans=pd.DataFrame(columns=["signal_date", "entry_date", "code", "status", "reason"]),
        orders=pd.DataFrame(orders, columns=["date", "code", "side", "size", "price", "fees", "phase", "order_id", "status", "reason"]),
        fills=pd.DataFrame(fills, columns=["date", "code", "side", "size", "price", "fees", "phase", "order_id", "fill_seq", "ledger_seq", "fill_id", "fee", "tax"]),
        positions=pd.DataFrame(snapshots, columns=["date", "code", "size", "entry_price", "mark_price", "cost_basis", "stale"]),
        equity=pd.DataFrame(equities),
        trades=pd.DataFrame(trades, columns=["code", "pnl", "entry_date", "exit_date"]),
        issues=list(dict.fromkeys(issues)),
    )
    return account.result(result, initial_cash)


def simulate_slot(delivery, signals, spec, *, initial_cash=100_000_000, hooks=None, run_id):
    """Return save_result-compatible frames and an independently reconciled C2 ledger.

    Standard/ambiguity costs replace both dated fee rates with aggregate bps per
    side and zero sell tax. ``realistic-costs`` preserves the supplied synthetic
    profiles; neither mode adds a second cost layer. ``benchmark_id`` is an
    explicit permanent instrument ID, never a fabricated index. Buy-hold spends
    affordable cash once and has no strategy exits or expiry; corporate-action
    settlement can still remove its holding. All results remain synthetic.
    ``requires_holdout`` is trace metadata: the owning runner must authorize the
    synthetic lifecycle gate before calling; it never permits dates from 2024.
    """
    checked, start, end = _validate_slot(delivery, signals, spec, initial_cash)
    hooks = hooks or ExecutionHooks()
    hooks("run_start", {"run_id": run_id, "conditional_slot": spec["conditional_slot"]})
    if spec["control"] is None:
        result = simulate_delivery(
            checked, signals, entry_id=spec["entry_id"], exit_id=spec["exit_id"],
            start=spec["start"], end=spec["end"], initial_cash=initial_cash,
            delay=spec["delay"], optimistic=spec["optimistic"], policy=spec["policy"], hooks=hooks, run_id=run_id,
        )
    else:
        market = MarketModel(checked)
        result = _control(market, market.prepare_prices(), spec, start, end, initial_cash, hooks)
        result["contract_ledger"] = contract_ledger(result, checked, run_id)
    trace = {key: deepcopy(spec[key]) for key in _SPEC_FIELDS}
    trace.update(growth_policy=spec["policy"], benchmark_id=spec.get("benchmark_id"),
                 cost_model="delivery_profiles" if spec["phase"] == "realistic-costs" else "aggregate_bps_per_side")
    result["slot_spec"] = deepcopy(trace)
    result["strategy_id"], result["growth_policy"] = spec["strategy_id"], spec["policy"]
    result["contract_ledger"].update(trace)
    result["reconciliation"] = reconcile_ledger(result["contract_ledger"])
    if not result["reconciliation"]["ok"]:
        raise ContractError("CONDITIONAL_LEDGER_RECONCILIATION_FAILED", str(result["reconciliation"]["mismatches"]))
    return result
