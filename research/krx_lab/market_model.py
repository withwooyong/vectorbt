"""Explicit dated synthetic market policies; no inferred real-market defaults."""

from __future__ import annotations

import pandas as pd
import math

from .contracts import ContractError, validate_delivery


def active(rows, day, **keys):
    day = pd.Timestamp(day).date().isoformat()
    matches = [row for row in rows if all(row.get(k) == v for k, v in keys.items())
               and row["effective_from"] <= day
               and (row["effective_to"] is None or day <= row["effective_to"])]
    if len(matches) != 1:
        raise ContractError("MISSING_OR_AMBIGUOUS_INTERVAL", f"{day}: {keys}")
    return matches[0]


class MarketModel:
    """Resolve one profile per instrument/date, rejecting unsupported policies."""

    def __init__(self, delivery):
        self.delivery = validate_delivery(delivery)
        if self.delivery["source_kind"] != "SYNTHETIC":
            raise ContractError("REAL_EXECUTION_NOT_ADMITTED")
        for row in self.delivery["market_profiles"]:
            if row["settlement_delay_days"] != 0 or row["slippage_bps"] != 0 or row["lot_size"] != 1:
                raise ContractError("UNSUPPORTED_EXECUTION_PROFILE", row["profile_id"])
        markets = {row["market"] for row in self.delivery["instruments"]}
        if len(markets) != 1:
            raise ContractError("MULTI_MARKET_EXECUTION_UNSUPPORTED")
        self.market = next(iter(markets))
        self.sessions = {row["date"]: row for row in self.delivery["calendar"] if row["market"] == self.market}
        self.trading_dates = sorted(day for day, row in self.sessions.items() if row["is_open"])

    def instrument(self, instrument_id, day):
        return active(self.delivery["instruments"], day, instrument_id=instrument_id)

    def profile(self, instrument_id, day):
        return active(self.delivery["market_profiles"], day,
                      market=self.instrument(instrument_id, day)["market"])

    def status(self, instrument_id, day):
        return active(self.delivery["statuses"], day, instrument_id=instrument_id)["status"]

    def prepare_prices(self):
        rows = []
        observed = {(row["instrument_id"], row["date"]) for row in self.delivery["prices"]}
        for day in self.trading_dates:
            if not self.delivery["metadata"]["start"] <= day <= self.delivery["metadata"]["end"]:
                continue
            for instrument_id in {row["instrument_id"] for row in self.delivery["instruments"]}:
                intervals = [row for row in self.delivery["instruments"] if row["instrument_id"] == instrument_id
                             and row["effective_from"] <= day and (row["effective_to"] is None or day <= row["effective_to"])]
                if not intervals:
                    continue  # before listing / after the explicitly bounded identity interval
                self.instrument(instrument_id, day)
                self.profile(instrument_id, day)
                if self.status(instrument_id, day) == "TRADING" and (instrument_id, day) not in observed:
                    raise ContractError("UNEXPLAINED_MISSING_TRADING_PRICE", f"{instrument_id}: {day}")
        for row in self.delivery["prices"]:
            item = dict(row)
            instrument_id, day = item["instrument_id"], item["date"]
            instrument = self.instrument(instrument_id, day)
            if item["code"] != instrument["code"]:
                raise ContractError("CODE_MAPPING_MISMATCH", f"{instrument_id}: {day}")
            session = self.sessions.get(day)
            if session is None:
                raise ContractError("MISSING_CALENDAR", day)
            profile = self.profile(instrument_id, day)
            status = self.status(instrument_id, day)
            if status == "TRADING" and session["is_open"]:
                if min(item[k] for k in ("open", "high", "low", "close")) <= 0:
                    raise ContractError("INVALID_TRADING_PRICE", f"{instrument_id}: {day}")
                if item["high"] < max(item["open"], item["close"], item["low"]) or item["low"] > min(item["open"], item["close"], item["high"]):
                    raise ContractError("INVALID_OHLC", f"{instrument_id}: {day}")
                for name in ("open", "high", "low", "close"):
                    units = item[name] / profile["tick_size"]
                    if not math.isclose(units, round(units), abs_tol=1e-9, rel_tol=1e-12):
                        raise ContractError("OFF_TICK_PRICE", f"{instrument_id}: {day}: {name}")
            item.update(code=instrument_id, sector=instrument["sector"], tick_size=profile["tick_size"],
                        eligible=status == "TRADING" and session["is_open"])
            rows.append(item)
        return pd.DataFrame(rows, columns=list(rows[0]) if rows else [
            "date", "code", "instrument_id", "open", "high", "low", "close", "volume", "sector", "tick_size", "eligible"])
