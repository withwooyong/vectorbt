"""Corporate rights ledger behavior against the sealed v4 terms."""

from fractions import Fraction
from pathlib import Path

import pytest

from research.krx_lab.ohlcv20_rights import RightsLedger, load_v4_terms


INPUT = (
    Path(__file__).resolve().parents[1]
    / "fixtures/ohlcv20/rights-price-payment-inputs-v4.parquet"
)
SHA = "c96aa8911fb4bb46d8d198596d6b1914120d587edcd6c7b2f9fb0fa1a7d7d2d5"


def ledger() -> RightsLedger:
    return RightsLedger(load_v4_terms(INPUT, SHA))


def test_sealed_v4_loads_exact_19_events_31_legs() -> None:
    events = load_v4_terms(INPUT, SHA)
    assert len(events) == 19
    assert sum(len(event.legs) for event in events.values()) == 31
    with pytest.raises(ValueError, match="RIGHTS_INPUT_HASH_MISMATCH"):
        load_v4_terms(INPUT, "0" * 64)


def test_spinoff_keeps_both_shares_in_original_slot_and_pays_later() -> None:
    book = ledger()
    book.capture("036710", 3, 11, record_date="2015-06-30")
    converted = book.convert("036710", 3, available_on="2015-08-07")
    assert converted.old_shares_removed == 11
    assert [(leg.code, leg.shares) for leg in converted.allocations] == [
        ("036710", 5),
        ("222800", 5),
    ]
    assert converted.allocations[0].fractional_shares == Fraction(307689, 5000000)
    assert book.due_cash("2015-08-12") == []
    receipts = book.due_cash("2015-08-13")
    assert len(receipts) == 2
    assert {r.slot_id for r in receipts} == {3}
    assert {r.leg_code for r in receipts} == {"036710", "222800"}
    assert sum((r.amount for r in receipts), Fraction()) == (
        converted.allocations[0].fractional_shares * 3900
        + converted.allocations[1].fractional_shares * 11350
    )
    assert book.due_cash("2015-08-14") == []


def test_explicit_rounding_only_on_named_successor_leg() -> None:
    book = ledger()
    book.capture("054620", 0, 7, record_date="2017-02-27")
    conversion = book.convert("054620", 0, available_on="2017-04-07")
    due = {r.leg_code: r.amount for r in book.due_cash("2017-04-13")}
    fractions = {leg.code: leg.fractional_shares for leg in conversion.allocations}
    assert due["054620"] == fractions["054620"] * 16400
    raw_successor = fractions["265520"] * 41700
    assert due["265520"] == raw_successor.numerator // raw_successor.denominator


def test_reduction_explicit_fraction_cancellation_has_no_receivable() -> None:
    book = ledger()
    book.capture("028670", 19, 3, record_date="2015-06-18")
    result = book.convert("028670", 19, available_on="2015-07-01")
    assert [(x.code, x.shares, x.fractional_shares) for x in result.allocations] == [
        ("028670", 2, Fraction(2, 5))
    ]
    assert book.pending_cash() == []


def test_conversion_and_capture_cannot_double_count() -> None:
    book = ledger()
    book.capture("003580", 2, 6, record_date="2016-09-30")
    with pytest.raises(ValueError, match="DUPLICATE_RIGHTS_CAPTURE"):
        book.capture("003580", 2, 6, record_date="2016-09-30")
    result = book.convert("003580", 2, available_on="2016-10-19")
    assert result.allocations[0].shares == 1
    assert result.allocations[0].fractional_shares == Fraction(1, 5)
    assert book.due_cash("2016-10-23") == []
    assert book.due_cash("2016-10-24")[0].amount == 9400
    with pytest.raises(ValueError, match="RIGHTS_NOT_CAPTURED_OR_ALREADY_CONVERTED"):
        book.convert("003580", 2, available_on="2016-10-19")


def test_invalid_dates_do_not_mutate_conversion() -> None:
    book = ledger()
    with pytest.raises(ValueError, match="WRONG_RIGHTS_RECORD_DATE"):
        book.capture("011200", 1, 10, record_date="2016-04-20")
    book.capture("011200", 1, 10, record_date="2016-04-21")
    with pytest.raises(ValueError, match="RIGHTS_AVAILABLE_BEFORE_RECORD_DATE"):
        book.convert("011200", 1, available_on="2016-04-20")
    assert (
        book.convert("011200", 1, available_on="2016-05-09").allocations[0].shares == 1
    )


def test_cash_receipt_does_not_wait_for_share_availability() -> None:
    book = ledger()
    book.capture("003580", 4, 6, record_date="2016-09-30")
    assert book.due_cash("2016-10-24")[0].amount == 9400
    assert book.convert("003580", 4, available_on="2016-10-25").old_shares_removed == 6
    assert book.due_cash("2016-10-25") == []
