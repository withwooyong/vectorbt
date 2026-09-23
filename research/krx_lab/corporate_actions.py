"""Synthetic pre-open corporate actions and independently replayable ledger deltas."""

from __future__ import annotations

import math

import pandas as pd

from .contracts import CONTRACT_VERSION, ContractError, validate_ledger


QUANTITY_RATIO_EVENTS = {"SPLIT", "REVERSE_SPLIT"}
STOCK_ISSUE_EVENTS = {"BONUS_ISSUE", "STOCK_DIVIDEND"}
ENTITLEMENT_EVENTS = QUANTITY_RATIO_EVENTS | STOCK_ISSUE_EVENTS


def entitlement_ratio(event):
    """Total-quantity multiplier shared by splits and new-share entitlements.

    Splits express it directly (``quantity_ratio``); stock issues express a
    per-share allotment (``allotment_ratio``), so the equivalent total
    multiplier is ``1 + allotment_ratio``.
    """
    if event["event_type"] in QUANTITY_RATIO_EVENTS:
        return event["quantity_ratio"]
    return 1 + event["allotment_ratio"]


def split_quantities(quantity, ratio, fractional_policy):
    """Return whole new shares and fraction; never silently discard a fraction."""
    exact = quantity * ratio
    nearest = round(exact)
    if math.isclose(exact, nearest, abs_tol=1e-10, rel_tol=1e-12):
        return int(nearest), 0.0
    if fractional_policy != "CASH_IN_LIEU":
        raise ContractError("FRACTIONAL_SHARES_UNSUPPORTED")
    whole = math.floor(exact)
    return whole, exact - whole


class CorporateActionBook:
    def __init__(self, market):
        self.market = market
        self.events = []
        self.cashflows = []
        self.pending = []
        self.receivables = 0.0
        self.sequence = 0
        self.delisted = set()
        self.stock_issue_processed = False
        seen = set()
        for event in market.delivery["events"]:
            key = (event["instrument_id"], event["effective_date"])
            if key in seen:
                raise ContractError("SAME_DAY_EVENT_ORDER_UNSUPPORTED", str(key))
            seen.add(key)
            session = market.sessions.get(event["effective_date"])
            if session is None or not session["is_open"]:
                raise ContractError("NON_SESSION_EVENT_UNSUPPORTED", event["event_id"])
            if pd.Timestamp(event["announced_at"]) >= pd.Timestamp(session["opens_at"]):
                raise ContractError("EVENT_NOT_KNOWN_AT_OPEN", event["event_id"])
            if event["event_type"] in QUANTITY_RATIO_EVENTS:
                ratio = event["quantity_ratio"]
                if (event["event_type"] == "SPLIT" and ratio <= 1) or (event["event_type"] == "REVERSE_SPLIT" and ratio >= 1):
                    raise ContractError("INVALID_SPLIT_DIRECTION", event["event_id"])
            elif event["event_type"] in STOCK_ISSUE_EVENTS:
                if event.get("allotment_ratio_admitted") is not True:
                    raise ContractError("UNADMITTED_ALLOTMENT_RATIO", event["event_id"])
                if event["allotment_ratio"] <= 0:
                    raise ContractError("INVALID_FACTOR", event["event_id"])

    def record(self, day, instrument_id, kind, *, quantity_delta=0, cost_basis_delta=0.0,
               cash_delta=0.0, receivable_delta=0.0, fee=0.0, tax=0.0, event_id=None, fill_id=None):
        seq = self.sequence
        self.sequence += 1
        common = dict(ledger_seq=seq, date=pd.Timestamp(day), instrument_id=instrument_id,
                      cash_delta=float(cash_delta), receivable_delta=float(receivable_delta),
                      payable_delta=0.0, fee=float(fee), tax=float(tax))
        self.cashflows.append(dict(common, cashflow_id=f"cashflow-{seq:08d}", event_id=event_id,
                                   fill_id=fill_id, kind=kind))
        if event_id is not None and kind != "PAYMENT":
            self.events.append(dict(common, event_id=event_id, event_type=kind,
                                    quantity_delta=int(quantity_delta), cost_basis_delta=float(cost_basis_delta)))
        return seq

    def _accrue(self, event, amount):
        if amount:
            self.receivables += amount
            self.pending.append(dict(event_id=event["event_id"], instrument_id=event["instrument_id"],
                                     pay_date=pd.Timestamp(event["pay_date"]), amount=amount))

    @staticmethod
    def adjust_plans(event, plans):
        day, ratio = pd.Timestamp(event["effective_date"]), entitlement_ratio(event)
        for plan in plans:
            if (plan.get("status") == "planned" and plan["code"] == event["instrument_id"]
                    and plan["signal_date"] < day <= plan["entry_date"]):
                for name in ("entry_cap", "stop_price", "target_price"):
                    plan[name] /= ratio
                plan["avg_volume20"] *= ratio

    def prepare_plans(self, start, plans):
        for event in sorted(self.market.delivery["events"], key=lambda row: row["effective_date"]):
            if event["event_type"] in ENTITLEMENT_EVENTS and pd.Timestamp(event["effective_date"]) < start:
                self.adjust_plans(event, plans)

    def process(self, day, positions, plans, trades):
        """Apply entitlement before new orders, then pay due receivables once."""
        for event in self.market.delivery["events"]:
            if pd.Timestamp(event["effective_date"]) != day:
                continue
            code, kind = event["instrument_id"], event["event_type"]
            pos = positions.get(code)
            quantity = pos.size if pos else 0
            basis = quantity * pos.entry_price + pos.entry_fees if pos else 0.0
            delta, basis_delta, amount, tax = 0, 0.0, 0.0, 0.0
            if kind in ENTITLEMENT_EVENTS:
                if kind in STOCK_ISSUE_EVENTS:
                    self.stock_issue_processed = True
                ratio = entitlement_ratio(event)
                # Transform only pre-event decisions; event-day close signals are already new units.
                self.adjust_plans(event, plans)
                if pos:
                    whole, fraction = split_quantities(quantity, ratio, event["fractional_policy"])
                    retained = whole / (quantity * ratio)
                    basis_delta = -basis * (1 - retained)
                    amount = fraction * event.get("fractional_cash_price", 0.0)
                    delta = whole - quantity
                    pos.size = whole
                    pos.entry_price /= ratio
                    pos.entry_fees *= retained
                    pos.stop_price /= ratio
                    pos.target_price /= ratio
                    pos.last_price /= ratio
                    pos.action_pnl += amount + basis_delta
                    self._accrue(event, amount)
                    if whole == 0:
                        trades.append(dict(code=code, pnl=pos.action_pnl, entry_date=pos.entry_date, exit_date=day))
                        del positions[code]
            else:
                gross = quantity * event["cash_per_share"]
                tax = gross * event["withholding_rate"]
                amount = gross - tax
                self._accrue(event, amount)
                if kind == "CASH_DIVIDEND" and pos:
                    pos.action_pnl += amount
                elif kind == "DELIST_CASH":
                    self.delisted.add(code)
                    if pos:
                        delta, basis_delta = -quantity, -basis
                        trades.append(dict(code=code, pnl=amount - basis + pos.action_pnl,
                                           entry_date=pos.entry_date, exit_date=day))
                        del positions[code]
            self.record(day, code, kind, event_id=event["event_id"], quantity_delta=delta,
                        cost_basis_delta=basis_delta, receivable_delta=amount, tax=tax)
        cash = 0.0
        for item in list(self.pending):
            if item["pay_date"] <= day:
                amount = item["amount"]
                cash += amount
                self.receivables -= amount
                self.record(day, item["instrument_id"], "PAYMENT", event_id=item["event_id"],
                            cash_delta=amount, receivable_delta=-amount)
                self.pending.remove(item)
        return cash

    def result(self, result, initial_cash):
        """Add C2 fields without changing the legacy simulator's transport."""
        for name in ("orders", "fills", "positions", "trades"):
            frame = result[name]
            frame["instrument_id"] = frame["code"]
            if "size" in frame:
                frame["quantity"] = frame["size"]
        result["events"] = pd.DataFrame(self.events, columns=["ledger_seq", "event_id", "date", "instrument_id",
            "event_type", "quantity_delta", "cost_basis_delta", "cash_delta", "receivable_delta", "payable_delta", "fee", "tax"])
        result["cashflows"] = pd.DataFrame(self.cashflows, columns=["ledger_seq", "cashflow_id", "date", "instrument_id",
            "event_id", "fill_id", "kind", "cash_delta", "receivable_delta", "payable_delta", "fee", "tax"])
        result["initial_cash"] = initial_cash
        result["schema_version"] = CONTRACT_VERSION
        result["source_kind"] = "SYNTHETIC"
        result["limitations"] = ["SYNTHETIC_EXECUTION_ONLY", "SINGLE_MARKET_ZERO_SLIPPAGE_IMMEDIATE_TRADE_SETTLEMENT",
                                 "PAYMENT_ON_EXPLICIT_CALENDAR_DATE"]
        if self.stock_issue_processed:
            result["limitations"].append("DEEMED_DIVIDEND_TAX_ON_STOCK_ISSUES_NOT_MODELLED")
        return result


def contract_ledger(result, delivery, run_id):
    """Convert additive simulator artifacts into JSON-native C2 transport."""
    import json

    ledger = dict(schema_version=CONTRACT_VERSION, source_kind="SYNTHETIC", run_id=run_id,
                  dataset_id=delivery["metadata"]["dataset_id"], revision=delivery["metadata"]["revision"],
                  currency=delivery["metadata"]["currency"], initial_cash=result["initial_cash"],
                  issues=result["issues"], limitations=result["limitations"], files=[])
    for name in ("orders", "fills", "events", "cashflows", "positions", "equity"):
        frame = result[name].copy()
        for column in ("date", "expiry"):
            if column in frame:
                frame[column] = pd.to_datetime(frame[column]).dt.strftime("%Y-%m-%d")
        ledger[name] = json.loads(frame.to_json(orient="records", double_precision=15))
    return validate_ledger(ledger)
