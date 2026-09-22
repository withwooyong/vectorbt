"""Slot-local corporate rights ledger for the OHLCV 20-slot experiment.

The caller supplies legally eligible record-date holdings and the first date on
which replacement shares become available. This ledger does not infer either
fact from a price bar. Cash in lieu is credited on the documented event date;
unknown rounding retains an exact rational amount as a declared model choice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

import pandas as pd


def _date(value: object) -> date:
    stamp = pd.Timestamp(value)
    if pd.isna(stamp) or stamp.tzinfo is not None or stamp != stamp.normalize():
        raise ValueError("INVALID_RIGHTS_DATE")
    return stamp.date()


@dataclass(frozen=True)
class RightsLeg:
    code: str
    ratio: Fraction
    cash_price: int
    cash_rounding: str
    payment_date: date | None


@dataclass(frozen=True)
class RightsEvent:
    code: str
    event_type: str
    record_date: date
    legs: tuple[RightsLeg, ...]


@dataclass(frozen=True)
class ShareAllocation:
    code: str
    shares: int
    fractional_shares: Fraction


@dataclass(frozen=True)
class Conversion:
    event_code: str
    slot_id: int
    old_shares_removed: int
    converted_on: date
    allocations: tuple[ShareAllocation, ...]


@dataclass(frozen=True)
class CashReceipt:
    event_code: str
    slot_id: int
    leg_code: str
    amount: Fraction
    due_date: date


def _optional_date(value: object) -> date | None:
    return None if pd.isna(value) else _date(value)


def load_v4_terms(path: Path, expected_sha256: str) -> dict[str, RightsEvent]:
    """Load a sealed settlement table; a reviewed SHA must be supplied."""
    if not expected_sha256 or sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("RIGHTS_INPUT_HASH_MISMATCH")
    frame = pd.read_parquet(path)
    required = {
        "event_stock_code",
        "event_type",
        "stock_code",
        "rights_record_date",
        "ratio_numerator",
        "ratio_denominator",
        "fractional_cash_price",
        "official_event_payment_date",
        "cash_rounding",
        "execution_admitted",
    }
    if not required <= set(frame.columns) or frame.empty:
        raise ValueError("INVALID_RIGHTS_SCHEMA")
    events = {}
    for code, rows in frame.groupby("event_stock_code", sort=True):
        if rows.stock_code.duplicated().any():
            raise ValueError("DUPLICATE_RIGHTS_LEG")
        kinds, dates = set(rows.event_type), set(rows.rights_record_date)
        if len(kinds) != 1 or len(dates) != 1:
            raise ValueError("INCONSISTENT_RIGHTS_EVENT")
        kind = kinds.pop()
        if (
            (kind == "SPIN_OFF" and len(rows) != 2)
            or (kind == "CAPITAL_REDUCTION" and len(rows) != 1)
            or kind not in {"SPIN_OFF", "CAPITAL_REDUCTION"}
        ):
            raise ValueError("INVALID_RIGHTS_EVENT_LEGS")
        legs = []
        for row in rows.itertuples(index=False):
            numerator, denominator, price = (
                int(row.ratio_numerator),
                int(row.ratio_denominator),
                int(row.fractional_cash_price),
            )
            if numerator <= 0 or denominator <= 0 or price < 0:
                raise ValueError("INVALID_RIGHTS_RATIO_OR_PRICE")
            if type(row.execution_admitted) is not bool or row.execution_admitted:
                raise ValueError("RIGHTS_TABLE_ADMISSION_FLAG_INVALID")
            policy, payable = (
                row.cash_rounding,
                _optional_date(row.official_event_payment_date),
            )
            if policy not in {
                "FLOOR_TO_WHOLE_KRW",
                "UNSPECIFIED_PRESERVE_EXACT_RATIONAL",
                "NOT_APPLICABLE_ZERO_COMPENSATION",
            }:
                raise ValueError("UNKNOWN_RIGHTS_CASH_ROUNDING")
            if (price == 0) != (policy == "NOT_APPLICABLE_ZERO_COMPENSATION"):
                raise ValueError("INCONSISTENT_RIGHTS_CASH_POLICY")
            if (price > 0 and payable is None) or (price == 0 and payable is not None):
                raise ValueError("INCONSISTENT_RIGHTS_PAYMENT_DATE")
            legs.append(
                RightsLeg(
                    str(row.stock_code),
                    Fraction(numerator, denominator),
                    price,
                    policy,
                    payable,
                )
            )
        if kind == "SPIN_OFF" and {leg.code for leg in legs} == {str(code)}:
            raise ValueError("MISSING_SUCCESSOR_CODE")
        if kind == "CAPITAL_REDUCTION" and legs[0].code != str(code):
            raise ValueError("WRONG_REDUCTION_CODE")
        events[str(code)] = RightsEvent(
            str(code), kind, _date(next(iter(dates))), tuple(legs)
        )
    return events


class RightsLedger:
    """Convert each captured record-date position once and pay cash once."""

    def __init__(
        self, events: dict[str, RightsEvent], *, source_sha256: str | None = None
    ) -> None:
        self.events = dict(events)
        self.source_sha256 = source_sha256
        self._captured: dict[tuple[str, int], int] = {}
        self._converted: set[tuple[str, int]] = set()
        self._receivables: list[CashReceipt] = []
        self._paid: set[tuple[str, int, str]] = set()

    @classmethod
    def from_v4(cls, path: Path, expected_sha256: str) -> RightsLedger:
        return cls(load_v4_terms(path, expected_sha256), source_sha256=expected_sha256)

    def capture(
        self, event_code: str, slot_id: int, shares: int, *, record_date: object
    ) -> None:
        """Caller confirms these shares qualify at the official rights date."""
        event = self.events[event_code]
        key = (event_code, slot_id)
        if _date(record_date) != event.record_date:
            raise ValueError("WRONG_RIGHTS_RECORD_DATE")
        if (
            type(slot_id) is not int
            or not 0 <= slot_id < 20
            or type(shares) is not int
            or shares <= 0
        ):
            raise ValueError("INVALID_RIGHTS_HOLDING")
        if key in self._captured:
            raise ValueError("DUPLICATE_RIGHTS_CAPTURE")
        self._captured[key] = shares
        for leg in event.legs:
            raw_shares = shares * leg.ratio
            fractional = raw_shares - raw_shares.numerator // raw_shares.denominator
            amount = fractional * leg.cash_price
            if leg.cash_rounding == "FLOOR_TO_WHOLE_KRW":
                amount = Fraction(amount.numerator // amount.denominator)
            if amount and leg.payment_date is not None:
                self._receivables.append(
                    CashReceipt(event_code, slot_id, leg.code, amount, leg.payment_date)
                )

    def convert(
        self, event_code: str, slot_id: int, *, available_on: object
    ) -> Conversion:
        """Return all replacement legs; caller replaces the original position."""
        event = self.events[event_code]
        key = (event_code, slot_id)
        if key not in self._captured or key in self._converted:
            raise ValueError("RIGHTS_NOT_CAPTURED_OR_ALREADY_CONVERTED")
        day = _date(available_on)
        if day < event.record_date:
            raise ValueError("RIGHTS_AVAILABLE_BEFORE_RECORD_DATE")
        shares = self._captured[key]
        allocations = []
        for leg in event.legs:
            result = shares * leg.ratio
            whole = result.numerator // result.denominator
            fraction = result - whole
            allocations.append(ShareAllocation(leg.code, whole, fraction))
        self._converted.add(key)
        return Conversion(event_code, slot_id, shares, day, tuple(allocations))

    def due_cash(self, day: object) -> list[CashReceipt]:
        """Release unpaid proceeds no earlier than the published payment date."""
        current = _date(day)
        result = []
        for item in self._receivables:
            key = (item.event_code, item.slot_id, item.leg_code)
            if item.due_date <= current and key not in self._paid:
                self._paid.add(key)
                result.append(item)
        return result

    def pending_cash(self) -> list[CashReceipt]:
        return [
            item
            for item in self._receivables
            if (item.event_code, item.slot_id, item.leg_code) not in self._paid
        ]
