"""Date-bound KRX market rules for the sealed v3 backtest window.

The source rules specify commission rounding, but no rounding convention for
transaction tax. Tax therefore remains an exact Decimal product in this model.
The T+2 rule counts exchange sessions; a caller must supply the actual calendar.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_DOWN
import json
from math import isfinite
from typing import Mapping

import pandas as pd


_FIRST_DAY = date(2014, 1, 1)
_LAST_DAY = date(2023, 12, 31)
_MARKETS = {"KOSPI", "KOSDAQ"}


def _date(value) -> date:
    if isinstance(value, datetime):
        result = value.date()
    elif isinstance(value, date):
        result = value
    else:
        result = date.fromisoformat(str(value)[:10])
    if not _FIRST_DAY <= result <= _LAST_DAY:
        raise ValueError(f"Market rule date outside sealed v3 window: {result}")
    return result


def _decimal(value) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"Invalid numeric value: {value!r}") from exc
    if not result.is_finite():
        raise ValueError(f"Nonfinite numeric value: {value!r}")
    return result


class V3MarketRules:
    """Apply exactly one sealed execution rule per kind, market, and date."""

    assumptions = (
        "Commission is the user-assumed 0.015% per side, truncated below 10 KRW.",
        "Sell tax uses the source total rate without invented tax rounding.",
        "Settlement is T+2 exchange business sessions; calendar resolution belongs to the caller.",
        "Tick returns the legal price increment; fill price/limit rounding belongs to the caller.",
    )

    def __init__(self, rows):
        if isinstance(rows, pd.DataFrame):
            rows = rows.to_dict("records")
        self.rows = []
        for row in rows:
            row = dict(row)
            value = row["rule_value"]
            if isinstance(value, str):
                value = json.loads(value, parse_float=Decimal)
            if not isinstance(value, dict):
                raise ValueError("Rule value must be a JSON object")
            row["rule_value"] = value
            row["effective_from"] = _date(row["effective_from"])
            row["effective_to"] = _date(row["effective_to"])
            if row["effective_from"] > row["effective_to"]:
                raise ValueError("Rule has reversed effective dates")
            self.rows.append(row)

    def _rule(self, kind, day, market):
        day = _date(day)
        market = str(market).upper()
        if market not in _MARKETS:
            raise ValueError(f"Unsupported v3 market: {market}")
        matches = [row for row in self.rows
                   if row["rule_kind"] == kind and row["market"] in ("ALL", market)
                   and row["effective_from"] <= day <= row["effective_to"]]
        if len(matches) != 1:
            raise ValueError(f"Expected one {kind} rule for {market} on {day}; found {len(matches)}")
        return matches[0]["rule_value"]

    def fees(self, day, market, side, value):
        """Return commission, sell tax, and total in exact KRW Decimal amounts."""
        side = str(side).upper()
        if side not in ("BUY", "SELL"):
            raise ValueError(f"Unsupported order side: {side}")
        value = _decimal(value)
        if value < 0:
            raise ValueError("Trade value must be nonnegative")
        rule = self._rule("COMMISSION", day, market)
        if rule.get("rounding_rule") != "TRUNCATE_BELOW_10_KRW":
            raise ValueError("Unsupported commission rounding rule")
        rate = _decimal(rule["buy_fee_rate" if side == "BUY" else "sell_fee_rate"])
        if rate < 0:
            raise ValueError("Commission rate must be nonnegative")
        fee = (value * rate / Decimal(10)).to_integral_value(rounding=ROUND_DOWN) * Decimal(10)
        tax = Decimal(0)
        if side == "SELL":
            tax_rate = _decimal(self._rule("SELL_TAX", day, market)["total_sell_tax_rate"])
            if tax_rate < 0:
                raise ValueError("Sell-tax rate must be nonnegative")
            tax = value * tax_rate
        return {"fee": fee, "tax": tax, "total": fee + tax}

    def tick(self, day, market, price):
        """Return the tick for a positive price; bands are lower-inclusive."""
        price = _decimal(price)
        if price <= 0:
            raise ValueError("Price must be positive")
        bands = self._rule("TICK_SIZE", day, market)["bands"]
        matches = [band for band in bands
                   if len(band) == 3 and _decimal(band[0]) <= price
                   and (band[1] is None or price < _decimal(band[1]))]
        if len(matches) != 1:
            raise ValueError(f"Expected one tick band for {price}; found {len(matches)}")
        tick = _decimal(matches[0][2])
        if tick <= 0:
            raise ValueError("Tick must be positive")
        return tick

    def price_limit(self, day, market):
        """Return the allowed price move as a fraction of the reference price."""
        value = _decimal(self._rule("PRICE_LIMIT", day, market)["percent"]) / Decimal(100)
        if not 0 < value < 1:
            raise ValueError("Invalid price-limit percentage")
        return value

    def settlement_sessions(self, day, market):
        """Return the number of exchange sessions after the trade date."""
        rule = self._rule("SETTLEMENT", day, market)
        if rule.get("calendar") != "exchange_business_day":
            raise ValueError("Unsupported settlement calendar")
        cycle = rule.get("cycle")
        if not isinstance(cycle, str) or not cycle.startswith("T+") or not cycle[2:].isdigit():
            raise ValueError("Unsupported settlement cycle")
        return int(cycle[2:])


def raw_bar_eligibility(row: Mapping, status="TRADING") -> bool:
    """Whether an unadjusted daily bar can supply an order or mark.

    Accept either database field names or local OHLCV aliases. An inconsistent
    high/low is rejected even when all five values are positive and finite.
    """
    if status != "TRADING":
        return False
    if row.get("daily_state", "TRADING") != "TRADING":
        return False
    values = []
    for name, alias in (("open_price", "open"), ("high_price", "high"),
                        ("low_price", "low"), ("close_price", "close"),
                        ("trade_volume", "volume")):
        value = row.get(name, row.get(alias))
        try:
            number = float(value)
        except (ValueError, TypeError, OverflowError):
            return False
        if not isfinite(number) or number <= 0:
            return False
        values.append(number)
    open_, high, low, close, _ = values
    return high >= max(open_, low, close) and low <= min(open_, high, close)
