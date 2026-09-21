"""Independent account identities and adverse daily-bar cases for v3 execution."""
from decimal import Decimal
import json
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab.v3_execution import PreparedExecution, simulate_real_slot
from research.krx_lab.v3_market import V3MarketRules


EVIDENCE = (Path(__file__).parents[2] / "docs/strategy-research/backtest-lab"
            / "postgresql-readiness-2026-09-21/data/results.json")
DAYS = pd.to_datetime(["2023-01-25", "2023-01-26", "2023-01-27", "2023-01-30",
                       "2023-01-31", "2023-02-01", "2023-02-02"])


def _rules():
    report = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    return V3MarketRules(next(item["data"] for item in report if item["check"] == "rules"))


def _prepared(*, day_changes=None, events=()):
    day_changes = day_changes or {}
    prices = []
    for day in DAYS:
        values = dict(date=day, instrument_id="1", code="000001", market="KOSPI",
                      raw_open=100, raw_high=102, raw_low=98, raw_close=100,
                      volume=1000, status="TRADING", eligible=True)
        values.update(day_changes.get(day.strftime("%Y-%m-%d"), {}))
        prices.append(values)
    signals = pd.DataFrame([dict(date=DAYS[0], instrument_id="1", code="000001",
                                 close=100, atr14=2, avg_volume20=10_000_000, ENTRY=True)])
    return PreparedExecution(pd.DataFrame(prices), signals, DAYS, events=events)


def _run(prepared):
    return simulate_real_slot(prepared, _rules(), entry_id="ENTRY", exit_id="PCT_3_6",
                              start=DAYS[1], end=DAYS[-1])


def test_cash_claims_and_equity_reconcile_to_hand_ledger_on_every_session():
    data = _prepared(day_changes={"2023-01-30": dict(raw_high=107, raw_low=99)})
    result = _run(data)
    assert result["status"] == "SUCCEEDED"
    assert [(row.side, row.size, row.price) for row in result["fills"].itertuples()] == [
        ("buy", 10000, Decimal(100)), ("sell", 10000, Decimal(106))]
    assert result["trades"].iloc[0].pnl == Decimal(57_580)

    flows = result["cashflows"]
    for row in result["equity"].itertuples():
        through_day = flows.loc[flows.date.le(row.date)]
        bank = Decimal(100_000_000) + sum(through_day.cash_delta, Decimal(0))
        receivable = sum(through_day.receivable_delta, Decimal(0))
        payable = sum(through_day.payable_delta, Decimal(0))
        assert (row.settled_cash, row.receivables, row.payables) == (bank, receivable, payable)
        assert row.cash == bank + receivable - payable
        assert row.equity == row.cash + row.exposure
    assert result["equity"].iloc[-1].settled_cash == Decimal(100_057_580)
    assert result["equity"].iloc[-1].receivables == result["equity"].iloc[-1].payables == 0


def test_future_bar_mutation_cannot_change_prior_fills_or_equity():
    baseline = _run(_prepared(day_changes={"2023-01-30": dict(raw_high=107, raw_low=99)}))
    changed = _run(_prepared(day_changes={"2023-01-30": dict(raw_high=107, raw_low=99),
                                         "2023-02-02": dict(raw_open=150, raw_high=155,
                                                              raw_low=145, raw_close=151)}))
    pd.testing.assert_frame_equal(baseline["fills"], changed["fills"])
    pd.testing.assert_frame_equal(baseline["equity"].iloc[:-1].reset_index(drop=True),
                                  changed["equity"].iloc[:-1].reset_index(drop=True))


def test_gap_stop_uses_observed_open_and_same_bar_ambiguity_uses_stop():
    gap = _run(_prepared(day_changes={"2023-01-27": dict(raw_open=90, raw_high=92,
                                                          raw_low=89, raw_close=90)}))
    assert gap["status"] == "SUCCEEDED"
    assert gap["fills"].iloc[1]["phase"] == "stop_gap_open"
    assert gap["fills"].iloc[1]["price"] == Decimal(90)
    assert gap["trades"].iloc[0].pnl == Decimal(-102_080)

    both = _run(_prepared(day_changes={"2023-01-26": dict(raw_high=107, raw_low=95)}))
    assert both["status"] == "SUCCEEDED"
    assert both["fills"].iloc[1]["phase"] == "stop_intraday_ambiguous"
    assert both["fills"].iloc[1]["price"] == Decimal(97)


def test_held_reference_dividend_blocks_return_release():
    event = dict(instrument_id="1", effective_date=DAYS[2], event_id="reference-dividend",
                 event_type="DIVIDEND_OFF", resolution_status="REFERENCE_FACT", sequence_no=None,
                 quantity_ratio=None, announced_at=None)
    result = _run(_prepared(events=[event]))
    assert result["status"] == "BLOCKED"
    assert not result["performance_valid"]
    assert result["equity"].empty and result["trades"].empty


def test_legal_fill_tick_and_no_volume_mark_are_distinct():
    illegal = _run(_prepared(day_changes={"2023-01-26": dict(raw_open=100.5)}))
    assert illegal["fills"].empty or illegal["status"] == "BLOCKED"

    no_volume = _run(_prepared(day_changes={"2023-01-27": dict(volume=0, eligible=False),
                                            "2023-01-30": dict(raw_high=107, raw_low=99)}))
    assert no_volume["status"] == "SUCCEEDED"
    held = no_volume["positions"].loc[no_volume["positions"].date.eq(DAYS[2])]
    assert len(held) == 1 and held.iloc[0].mark_price == Decimal(100)
    assert not no_volume["fills"].date.eq(DAYS[2]).any()


def test_impossible_unadjusted_gap_cannot_release_a_return():
    # Jan 2023's 30% limit cannot produce a 150 KRW open after a 100 KRW close.
    source = _prepared(day_changes={"2023-01-27": dict(raw_open=150, raw_high=151,
                                                        raw_low=149, raw_close=150)})
    result = _run(source)
    assert result["status"] == "BLOCKED"
    assert result["equity"].empty


def test_requested_window_cannot_be_silently_truncated_to_prepared_calendar():
    data = _prepared()
    for start, end in (("2023-01-01", "2023-02-02"),
                       ("2023-01-26", "2023-12-31")):
        with pytest.raises(ValueError, match="calendar|window|Slot"):
            simulate_real_slot(data, _rules(), entry_id="ENTRY", exit_id="PCT_3_6",
                               start=start, end=end)
