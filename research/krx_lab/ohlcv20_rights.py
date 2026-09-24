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
import json
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
    return _events_from_frame(pd.read_parquet(path))


def _events_from_frame(frame: pd.DataFrame) -> dict[str, RightsEvent]:
    """Apply the sealed-leg rules to a table already bound by its caller."""
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


# The six consumer paths of settlement v5. Every event of the sealed table is
# routed to exactly one of them; the receipt hashes the routed event keys.
TREATMENTS = (
    "RIGHTS_LEDGER",
    "QUANTITY_TRANSFORM",
    "PAID_RIGHTS_CASH",
    "NO_HOLDER_EFFECT",
    "POLICY_EXCLUDED",
    "BLOCK_ON_HOLD",
)
NEW_SHARE_OBLIGATION = (
    "REPORT_EXITS_WITHIN_30_CALENDAR_DAYS_AFTER_EFFECTIVE_DATE_AS_OPTIMISTIC_NEW_SHARE_LISTING_BOUND"
)
_FRACTION_CASH_RULE = "WHOLE_NEW_SHARES_ADDED_FRACTION_CASH_AT_EX_DATE_REFERENCE_PRICE"
_INTEGER_RULE = "INTEGER_RATIO_NO_FRACTION"


@dataclass(frozen=True)
class CorporateEvent:
    """A non-ledger event applied to a position held at the prior close."""

    event_id: str
    treatment: str
    applies: bool
    code: str
    effective_date: date
    event_type: str
    quantity_multiplier: Fraction | None = None
    price_multiplier: Fraction | None = None
    fraction_cash_price: Fraction | None = None
    rights_value_per_share: Fraction | None = None
    new_share_bound: bool = False


@dataclass(frozen=True)
class LedgerSchedule:
    """Capture on the last cum-rights session; no trade until available_on."""

    event_code: str
    event_id: str
    capture_on: date
    suspended_from: date
    available_on: date


@dataclass(frozen=True)
class RightsProgram:
    """Every settlement-v5 event routed to the path the engine applies."""

    source_sha256: str
    ledger_events: dict[str, RightsEvent]
    ledger_schedule: tuple[LedgerSchedule, ...]
    events: tuple[CorporateEvent, ...]

    def ledger(self) -> RightsLedger:
        return RightsLedger(self.ledger_events, source_sha256=self.source_sha256)

    def event_schedule(self) -> list[dict]:
        return [
            dict(
                event_code=item.event_code,
                capture_on=item.capture_on,
                available_on=item.available_on,
            )
            for item in self.ledger_schedule
        ]

    def assignment(self) -> dict[str, list[tuple[str, bool]]]:
        """Event keys per path, read back from the containers the engine uses."""
        routed: dict[str, list[tuple[str, bool]]] = {name: [] for name in TREATMENTS}
        for item in self.ledger_schedule:
            if item.event_code in self.ledger_events:
                routed["RIGHTS_LEDGER"].append((item.event_id, True))
        for event in self.events:
            routed[event.treatment].append((event.event_id, event.applies))
        return routed


def _digest(ids: list[str]) -> dict:
    payload = "\n".join(sorted(ids)).encode("utf-8")
    return {"count": len(ids), "sha256": sha256(payload).hexdigest()}


def event_coverage(program: RightsProgram) -> dict:
    """Hash routed event keys exactly as the admission receipt defines them."""
    routed = program.assignment()
    every = [key for items in routed.values() for key, _ in items]
    applied = [key for items in routed.values() for key, flag in items if flag]
    skipped = [key for items in routed.values() for key, flag in items if not flag]
    by_treatment = {
        name: dict(
            _digest([key for key, _ in items]),
            applied=_digest([key for key, flag in items if flag]),
            not_applied=_digest([key for key, flag in items if not flag]),
        )
        for name, items in routed.items()
        if items
    }
    return dict(
        all=_digest(every),
        applied=_digest(applied),
        not_applied=_digest(skipped),
        by_treatment=by_treatment,
    )


def coverage_mismatches(program: RightsProgram, receipt_coverage: object) -> list[str]:
    """Name every coverage part that differs from the receipt; empty means bound."""
    if not isinstance(receipt_coverage, dict):
        return ["rights_event_coverage"]
    actual = event_coverage(program)
    return [
        key
        for key in ("all", "applied", "not_applied", "by_treatment")
        if actual[key] != receipt_coverage.get(key)
    ]


def _ratio(terms: dict, key: str) -> Fraction:
    value = Fraction(str(terms[key]))
    if value <= 0:
        raise ValueError("INVALID_CORPORATE_TERMS:" + key)
    return value


def _corporate_event(record, terms: object) -> CorporateEvent:
    base = dict(
        event_id=str(record.event_id),
        treatment=str(record.treatment),
        applies=bool(record.consumer_applies_this_row),
        code=str(record.record_stock_code),
        effective_date=_date(record.effective_date),
        event_type=str(record.record_event_type),
    )
    if record.treatment == "QUANTITY_TRANSFORM":
        if not isinstance(terms, dict):
            raise ValueError("MISSING_CORPORATE_TERMS")
        rule = terms.get("fraction_rule")
        multiplier = _ratio(terms, "quantity_multiplier")
        cash_price = None
        if rule == _FRACTION_CASH_RULE:
            cash_price = _ratio(terms, "fraction_cash_price")
        elif rule != _INTEGER_RULE or multiplier.denominator != 1:
            raise ValueError("INVALID_FRACTION_RULE")
        return CorporateEvent(
            **base,
            quantity_multiplier=multiplier,
            price_multiplier=_ratio(terms, "stop_take_price_multiplier"),
            fraction_cash_price=cash_price,
            new_share_bound=terms.get("consumer_obligation") == NEW_SHARE_OBLIGATION,
        )
    if record.treatment == "PAID_RIGHTS_CASH":
        if not isinstance(terms, dict) or _ratio(terms, "quantity_multiplier") != 1:
            raise ValueError("PAID_RIGHTS_MUST_KEEP_QUANTITY")
        value = Fraction(str(terms["rights_value_per_share"]))
        if value < 0:
            raise ValueError("INVALID_CORPORATE_TERMS:rights_value_per_share")
        return CorporateEvent(
            **base,
            quantity_multiplier=Fraction(1),
            price_multiplier=_ratio(terms, "stop_take_price_multiplier"),
            rights_value_per_share=value,
        )
    if terms is not None:
        raise ValueError("UNEXPECTED_CORPORATE_TERMS")
    return CorporateEvent(**base)


def load_v5_program(path: Path, expected_sha256: str) -> RightsProgram:
    """Route all events of the sealed v5 table; the file bytes must be reviewed.

    Ledger legs keep the v4 leg rules. Event rows carry quantity transforms and
    the paid-rights cash of decision D6 (1). Rows never admit themselves.
    """
    if not expected_sha256 or sha256(path.read_bytes()).hexdigest() != expected_sha256:
        raise ValueError("RIGHTS_INPUT_HASH_MISMATCH")
    frame = pd.read_parquet(path)
    required = {
        "row_kind",
        "record_index",
        "leg_index",
        "event_id",
        "treatment",
        "consumer_applies_this_row",
        "record_stock_code",
        "effective_date",
        "record_event_type",
        "execution_admitted",
        "terms_json",
        "record_json",
    }
    if not required <= set(frame.columns) or frame.empty:
        raise ValueError("INVALID_RIGHTS_SCHEMA")
    if not frame.execution_admitted.map(lambda value: value is False).all():
        raise ValueError("RIGHTS_TABLE_ADMISSION_FLAG_INVALID")
    frame = frame.sort_values(["record_index", "leg_index"], kind="stable")
    keys = ["event_id", "treatment", "consumer_applies_this_row", "row_kind"]
    if (frame.groupby("record_index")[keys].nunique(dropna=False) != 1).any().any():
        raise ValueError("INCONSISTENT_RIGHTS_RECORD")
    records = frame.drop_duplicates("record_index")
    if records.event_id.isna().any() or records.event_id.duplicated().any():
        raise ValueError("DUPLICATE_RIGHTS_EVENT_ID")
    if not records.treatment.isin(TREATMENTS).all():
        raise ValueError("UNKNOWN_RIGHTS_TREATMENT")
    ledger_rows = frame.row_kind.eq("LEDGER_LEG")
    if not frame.row_kind.isin({"LEDGER_LEG", "EVENT"}).all() or not ledger_rows.eq(
        frame.treatment.eq("RIGHTS_LEDGER")
    ).all():
        raise ValueError("RIGHTS_ROW_KIND_MISMATCH")
    if frame.loc[~ledger_rows].record_index.duplicated().any():
        raise ValueError("DUPLICATE_EVENT_ROW")

    legs = frame.loc[ledger_rows & frame.consumer_applies_this_row.eq(True)]
    ledger_events = _events_from_frame(legs) if len(legs) else {}
    schedule = []
    for code, rows in legs.groupby("event_stock_code", sort=True):
        if rows.event_id.nunique() != 1:
            raise ValueError("LEDGER_CODE_EVENT_AMBIGUOUS")
        first = rows.iloc[0]
        entitlement = json.loads(first.record_json)["entitlement"]
        if entitlement.get("traded_sessions_from_ex_session_to_effective_date") != 0:
            raise ValueError("LEDGER_SUSPENSION_NOT_CONFIRMED")
        item = LedgerSchedule(
            event_code=str(code),
            event_id=str(first.event_id),
            capture_on=_date(entitlement["record_date_last_cum_rights_session_t_plus_2"]),
            suspended_from=_date(entitlement["ex_session"]),
            available_on=_date(first.effective_date),
        )
        record = ledger_events[str(code)].record_date
        if _date(entitlement["record_date"]) != record or not (
            item.capture_on <= record < item.available_on
            and item.capture_on < item.suspended_from <= item.available_on
        ):
            raise ValueError("INVALID_LEDGER_SCHEDULE")
        schedule.append(item)
    events = tuple(
        _corporate_event(record, json.loads(record.terms_json))
        for record in records.loc[records.row_kind.eq("EVENT")].itertuples(index=False)
    )
    return RightsProgram(expected_sha256, ledger_events, tuple(schedule), events)
