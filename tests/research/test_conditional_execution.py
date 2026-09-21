"""Hand expectations for synthetic conditional execution; no real-market evidence."""

import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab.conditional_execution import simulate_slot
from research.krx_lab.contracts import ExecutionHooks, StopToken, CooperativeStop, validate_ledger
from research.krx_lab.metrics import calculate_metrics
from research.krx_lab.runner import save_result, verify_artifacts
from research.krx_lab.vectorbt_check import reconcile_ledger


FIXTURE = Path(__file__).parent / "fixtures" / "contracts_v1" / "delivery.json"
ID = "SYN-ID-001"


def delivery_case(values=(100, 100, 100, 100), dates=None):
    delivery = json.loads(FIXTURE.read_text(encoding="utf-8"))
    dates = dates or [f"2023-01-{day:02d}" for day in range(2, len(values) + 2)]
    delivery["metadata"].update(start=dates[0], end=dates[-1])
    template = delivery["prices"][0]
    delivery["prices"] = []
    for day, value in zip(dates, values):
        row = dict(template, date=day, price_factor=1, quantity_factor=1, volume=1_000_000)
        for column in ("open", "high", "low", "close"):
            row[column] = row[f"adjusted_{column}"] = value
        delivery["prices"].append(row)
    delivery["calendar"] = [dict(delivery["calendar"][0], date=day,
                                 opens_at=day + "T09:00:00+09:00", closes_at=day + "T15:30:00+09:00")
                            for day in dates]
    delivery["statuses"][0].update(effective_from=dates[0], effective_to=None)
    delivery["market_profiles"][0].update(effective_from=dates[0], effective_to=None, buy_fee_rate=0.02,
                                          sell_fee_rate=0.03, sell_tax_rate=0.04)
    delivery["events"] = []
    return delivery


def slot(delivery, **updates):
    return dict(dict(phase="allocation", conditional_slot=0, strategy_id="entry__PCT_5_10",
                     entry_id="entry", exit_id="PCT_5_10", policy="fixed20", period="validation",
                     start=delivery["metadata"]["start"], end=delivery["metadata"]["end"], cost_bps=0,
                     delay=1, optimistic=False, control=None, requires_holdout=False), **updates)


def signals(delivery):
    return pd.DataFrame([dict(date=delivery["metadata"]["start"], instrument_id=ID,
                              atr14=4, avg_volume20=1_000_000, entry=True)])


def run(delivery, initial_cash=25_000, **updates):
    return simulate_slot(delivery, signals(delivery), slot(delivery, **updates),
                         initial_cash=initial_cash, run_id="synthetic-slot")


def test_synthetic_costs_change_fills_without_mutation_or_double_charge():
    delivery = delivery_case((100, 100, 110, 110))
    before = copy.deepcopy(delivery)
    signal = signals(delivery)
    signal_before = signal.copy(deep=True)
    free = run(delivery)
    spec = slot(delivery, cost_bps=100)
    spec_before = copy.deepcopy(spec)
    paid = simulate_slot(delivery, signal, spec, initial_cash=25_000, run_id="cost-test")
    assert free["fills"]["quantity"].tolist() == [10, 10]
    assert free["equity"].iloc[-1]["cash"] == 25_100
    quantities = paid["fills"]["quantity"].tolist()
    assert quantities == [9, 9]
    assert paid["fills"]["fee"].tolist() == pytest.approx([9, 9.9])
    assert paid["fills"]["tax"].tolist() == [0, 0]
    assert paid["equity"].iloc[-1]["cash"] == pytest.approx(25_071.1)
    assert paid["reconciliation"]["ok"]
    assert delivery == before and spec == spec_before
    pd.testing.assert_frame_equal(signal, signal_before)


def test_realistic_profiles_preserve_fee_and_tax_rates():
    delivery = delivery_case((100, 100, 110, 110))
    result = run(delivery, phase="realistic-costs", cost_bps=None)
    for fill in result["fills"].to_dict("records"):
        notional = fill["quantity"] * fill["price"]
        assert fill["fee"] == pytest.approx(notional * (0.02 if fill["side"] == "buy" else 0.03))
        assert fill["tax"] == pytest.approx(notional * (0 if fill["side"] == "buy" else 0.04))
    assert result["reconciliation"]["ok"]
    with pytest.raises(ValueError, match="null cost_bps"):
        run(delivery, phase="realistic-costs", cost_bps=30)


def test_optimistic_path_changes_ambiguous_exit():
    delivery = delivery_case()
    delivery["prices"][1].update(high=110, adjusted_high=110, low=95, adjusted_low=95)
    pessimistic = run(delivery, phase="ambiguity")
    optimistic = run(delivery, phase="ambiguity", optimistic=True)
    assert pessimistic["fills"].iloc[-1]["price"] == 95
    assert optimistic["fills"].iloc[-1]["price"] == 110
    assert pessimistic["equity"].iloc[-1]["cash"] == 24_950
    assert optimistic["equity"].iloc[-1]["cash"] == 25_100


def test_cash_has_constant_equity_and_no_ledger_transitions():
    delivery = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = run(delivery, control="cash", cost_bps=50)
    for key in ("orders", "fills", "positions", "trades", "events", "cashflows"):
        assert result[key].empty
    assert result["equity"]["equity"].tolist() == [25_000] * 4
    assert result["equity"]["exposure"].eq(0).all()
    assert result["reconciliation"]["transitions_checked"] == 0


def test_buy_hold_split_dividend_and_no_monthly_or_technical_sale():
    delivery = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # 1,000 cash buys 20 x 50; split gives 40, dividend pays net 36.
    day = "2023-03-06"
    delivery["metadata"]["end"] = day
    delivery["market_profiles"][0]["effective_to"] = day
    delivery["statuses"][0]["effective_to"] = day
    delivery["calendar"].append(dict(delivery["calendar"][-1], date=day,
                                     opens_at=day + "T09:00:00+09:00", closes_at=day + "T15:30:00+09:00"))
    delivery["prices"].append(dict(delivery["prices"][-1], date=day, open=100, high=100, low=100,
                                   close=100, adjusted_open=100, adjusted_high=100, adjusted_low=100,
                                   adjusted_close=100))
    result = run(delivery, initial_cash=1000, control="buy_hold", benchmark_id=ID)
    assert result["fills"]["quantity"].tolist() == [20]
    assert result["fills"].iloc[0]["date"] == pd.Timestamp("2023-01-02")
    assert result["positions"].iloc[-1]["quantity"] == 40
    assert result["positions"].iloc[-1]["cost_basis"] == 1000
    assert result["equity"].iloc[-1]["cash"] == 36
    assert result["equity"].iloc[-1]["equity"] == 4036
    assert result["trades"].empty
    assert result["reconciliation"]["ok"]


def test_buy_hold_waits_for_first_tradable_open_and_includes_fee_in_affordability():
    delivery = delivery_case()
    status = delivery["statuses"][0]
    delivery["statuses"] = [dict(status, status="HALTED", effective_to="2023-01-02"),
                            dict(status, status_id="resumed", effective_from="2023-01-03")]
    result = run(delivery, initial_cash=1000, control="buy_hold", benchmark_id=ID, cost_bps=100)
    assert result["fills"].iloc[0]["date"] == pd.Timestamp("2023-01-03")
    assert result["fills"].iloc[0]["quantity"] == 9
    assert result["fills"].iloc[0]["fee"] == 9
    assert result["equity"].iloc[-1]["cash"] == 91
    assert result["equity"].iloc[-1]["equity"] == 991


@pytest.mark.parametrize("control", [None, "cash", "buy_hold"])
def test_controls_and_strategy_persist_with_trace(tmp_path, control):
    delivery = delivery_case()
    result = run(delivery, control=control, benchmark_id=ID)
    ledger = result["contract_ledger"]
    assert ledger["source_kind"] == "SYNTHETIC"
    assert ledger["strategy_id"] == "entry__PCT_5_10"
    assert ledger["growth_policy"] == ledger["policy"] == "fixed20"
    assert ledger["control"] == control
    validate_ledger(ledger)
    save_result(tmp_path / "result", result, calculate_metrics(result, 25_000), result["reconciliation"], initial_cash=25_000)
    verify_artifacts(tmp_path / "result")
    saved = json.loads((tmp_path / "result/contract_ledger.json").read_text(encoding="utf-8"))
    assert saved == ledger


@pytest.mark.parametrize("changes,match", [
    ({"control": "buy_hold"}, "UNSUPPORTED_BENCHMARK"),
    ({"control": "buy_hold", "benchmark_id": "FAKE_INDEX"}, "UNSUPPORTED_BENCHMARK"),
    ({"requires_holdout": "true"}, "requires_holdout"),
    ({"end": "2024-01-01"}, "HOLDOUT_LOCKED"),
    ({"start": "2023-01-05", "end": "2023-01-02"}, "end must"),
    ({"cost_bps": None}, "cost_bps"),
    ({"cost_bps": float("nan")}, "cost_bps"),
    ({"delay": 0}, "delay"),
])
def test_invalid_slots_fail_closed(changes, match):
    with pytest.raises(ValueError, match=match):
        run(delivery_case(), **changes)


@pytest.mark.parametrize("control", [None, "cash", "buy_hold"])
def test_real_and_missing_prices_rejected(control):
    delivery = delivery_case()
    delivery["source_kind"] = "REAL"
    with pytest.raises(ValueError, match="REAL_EXECUTION_NOT_ADMITTED"):
        run(delivery, control=control, benchmark_id=ID)
    delivery["source_kind"] = "SYNTHETIC"
    delivery["prices"].pop()
    with pytest.raises(ValueError, match="MISSING_TRADING_PRICE"):
        run(delivery, control=control, benchmark_id=ID)


def test_unused_future_calendar_event_and_signal_dates_are_rejected():
    for section, key in (("calendar", "date"), ("events", "pay_date")):
        delivery = json.loads(FIXTURE.read_text(encoding="utf-8"))
        delivery[section][-1][key] = "2024-01-01"
        with pytest.raises(ValueError):
            run(delivery, control="cash")
    delivery = delivery_case()
    signal = signals(delivery)
    signal.loc[0, "date"] = "2024-01-01"
    with pytest.raises(ValueError, match="HOLDOUT_LOCKED"):
        simulate_slot(delivery, signal, slot(delivery, control="cash"), run_id="future")


def test_reconciliation_detects_corrupt_benchmark_fill():
    result = run(delivery_case(), control="buy_hold", benchmark_id=ID)
    ledger = copy.deepcopy(result["contract_ledger"])
    ledger["fills"][0]["fee"] += 1
    assert not reconcile_ledger(ledger)["ok"]


def test_cooperative_stop_runs_before_control_execution():
    delivery = delivery_case()
    token = StopToken()
    token.request_stop("test-stop")
    with pytest.raises(CooperativeStop, match="test-stop"):
        simulate_slot(delivery, signals(delivery), slot(delivery, control="cash"),
                      hooks=ExecutionHooks(stop_token=token), run_id="stopped")


def test_synthetic_holdout_trace_and_nullable_control_policy_are_accepted():
    delivery = delivery_case()
    result = run(delivery, phase="controls", requires_holdout=True, period="holdout",
                 control="cash", strategy_id="cash", entry_id=None, exit_id=None, policy=None)
    assert result["contract_ledger"]["requires_holdout"] is True
    assert result["contract_ledger"]["growth_policy"] is None
    assert result["reconciliation"]["ok"]


def test_buy_hold_no_tradable_open_and_unaffordable_benchmark_fail_closed():
    delivery = delivery_case()
    with pytest.raises(ValueError, match="BENCHMARK_UNAFFORDABLE"):
        run(delivery, initial_cash=99, control="buy_hold", benchmark_id=ID)
    delivery["statuses"][0]["status"] = "HALTED"
    with pytest.raises(ValueError, match="NO_VALID_BENCHMARK_OPEN"):
        run(delivery, control="buy_hold", benchmark_id=ID)


def test_buy_hold_closed_payment_day_keeps_valid_mark():
    delivery = json.loads(FIXTURE.read_text(encoding="utf-8"))
    delivery["calendar"][-1].update(is_open=False, opens_at=None, closes_at=None)
    delivery["prices"].pop()
    result = run(delivery, initial_cash=1000, control="buy_hold", benchmark_id=ID)
    assert result["equity"].iloc[-1]["cash"] == 36
    assert result["equity"].iloc[-1]["equity"] == 996
    assert not result["positions"].iloc[-1]["stale"]
    assert result["reconciliation"]["ok"]


def test_delay_is_passed_to_strategy_execution():
    delivery = delivery_case()
    result = run(delivery, delay=2)
    assert result["fills"].iloc[0]["date"] == pd.Timestamp("2023-01-04")
