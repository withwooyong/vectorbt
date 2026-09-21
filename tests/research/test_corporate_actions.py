import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab.contracts import validate_ledger
from research.krx_lab.corporate_actions import split_quantities
from research.krx_lab.execution import simulate_delivery


FIXTURE = Path(__file__).parent / "fixtures" / "contracts_v1" / "delivery.json"
ID = "SYN-ID-001"


def delivery_case(values=(100, 100, 100, 100), dates=None):
    """Explicit fictional policies; 25,000 cash buys exactly ten 100-unit shares."""
    delivery = json.loads(FIXTURE.read_text(encoding="utf-8"))
    dates = dates or [f"2023-01-{day:02d}" for day in range(2, len(values) + 2)]
    delivery["metadata"].update(start=dates[0], end=dates[-1])
    template = copy.deepcopy(delivery["prices"][0])
    delivery["prices"] = []
    for day, value in zip(dates, values):
        if value is None:
            continue
        row = dict(template, date=day, price_factor=1, quantity_factor=1, volume=1_000_000)
        for column in ("open", "high", "low", "close"):
            row[column] = row[f"adjusted_{column}"] = value
        delivery["prices"].append(row)
    delivery["calendar"] = [dict(delivery["calendar"][0], date=day,
                                 opens_at=day + "T09:00:00+09:00", closes_at=day + "T15:30:00+09:00")
                            for day in dates]
    delivery["statuses"][0].update(effective_from=dates[0], effective_to=None)
    delivery["market_profiles"][0].update(effective_from=dates[0], effective_to=None, buy_fee_rate=0)
    delivery["events"] = []
    return delivery


def action(kind, date="2023-01-04", **kwargs):
    event = dict(event_id="event-1", event_type=kind, instrument_id=ID, source_id="synthetic-notice",
                 effective_date=date, announced_at="2023-01-01T00:00:00+09:00", record_date=date,
                 pay_date="2023-01-05", correction_of=None, cancelled=False)
    if kind in {"SPLIT", "REVERSE_SPLIT"}:
        event.update(quantity_ratio=2, fractional_policy="REJECT")
    else:
        event.update(cash_per_share=2, withholding_rate=0, entitlement_policy="PRE_EVENT_HOLDINGS")
    return dict(event, **kwargs)


def run_case(delivery, **kwargs):
    signals = pd.DataFrame([dict(date=delivery["metadata"]["start"], instrument_id=ID,
                                 atr14=4, avg_volume20=1_000_000, entry=True)])
    return simulate_delivery(delivery, signals, entry_id="entry", exit_id="PCT_5_10",
                             start=delivery["metadata"]["start"], end=delivery["metadata"]["end"],
                             initial_cash=25_000, **kwargs)


def test_forward_split_conserves_basis_quantity_and_equity():
    delivery = delivery_case((100, 100, 50, 50))
    delivery["events"] = [action("SPLIT")]
    result = run_case(delivery)
    position = result["positions"].iloc[-1]
    assert position["quantity"] == 20
    assert position["entry_price"] == 50
    assert position["cost_basis"] == 1000
    assert result["equity"].iloc[-1]["equity"] == 25_000
    assert result["events"].iloc[0]["quantity_delta"] == 10
    assert len(result["fills"]) == 1
    validate_ledger(result["contract_ledger"])


def test_reverse_split_cash_in_lieu_preserves_basis_and_pays_once():
    delivery = delivery_case((100, 100, 300, 300))
    delivery["events"] = [action("REVERSE_SPLIT", quantity_ratio=1 / 3,
                                  fractional_policy="CASH_IN_LIEU", fractional_cash_price=300)]
    result = run_case(delivery)
    ex, paid = result["equity"].iloc[-2: ].to_dict("records")
    assert ex["cash"] == 24_000
    assert ex["receivables"] == pytest.approx(100)
    assert paid["cash"] == pytest.approx(24_100)
    assert paid["receivables"] == pytest.approx(0)
    assert paid["equity"] == pytest.approx(25_000)
    position = result["positions"].iloc[-1]
    assert position["quantity"] == 3
    assert position["cost_basis"] == pytest.approx(900)
    assert result["events"].iloc[0]["cost_basis_delta"] == pytest.approx(-100)
    assert result["cashflows"]["kind"].tolist() == ["BUY", "REVERSE_SPLIT", "PAYMENT"]


def test_fractional_reject_policy_never_discards_shares():
    delivery = delivery_case((100, 100, 300, 300))
    delivery["events"] = [action("REVERSE_SPLIT", quantity_ratio=1 / 3)]
    with pytest.raises(ValueError, match="FRACTIONAL_SHARES_UNSUPPORTED"):
        run_case(delivery)
    assert split_quantities(10, 0.5, "REJECT") == (5, 0.0)


def test_dividend_net_receivable_survives_sale_and_does_not_double_count_tax():
    delivery = delivery_case((100, 100, 110, 110))
    delivery["events"] = [action("CASH_DIVIDEND", withholding_rate=0.1)]
    result = run_case(delivery)
    ex, paid = result["equity"].iloc[-2:].to_dict("records")
    assert ex["receivables"] == 18
    assert ex["cash"] == 25_100
    assert paid["cash"] == 25_118
    assert paid["receivables"] == 0
    assert paid["equity"] == 25_118
    assert result["trades"].iloc[0]["pnl"] == 118
    assert result["events"].iloc[0]["tax"] == 2


def test_ex_date_new_buyer_has_no_dividend_entitlement():
    delivery = delivery_case()
    delivery["events"] = [action("CASH_DIVIDEND", date="2023-01-03")]
    result = run_case(delivery)
    assert result["events"].iloc[0]["receivable_delta"] == 0
    assert result["equity"].iloc[-1]["equity"] == 25_000


def test_delisting_removes_stock_and_keeps_settlement_receivable_until_payment():
    delivery = delivery_case((100, 100, None, None))
    delivery["events"] = [action("DELIST_CASH", cash_per_share=40)]
    first = delivery["statuses"][0]
    first["effective_to"] = "2023-01-03"
    delivery["statuses"].append(dict(first, status_id="delisted", effective_from="2023-01-04",
                                     effective_to=None, status="DELISTED", official_delist_date="2023-01-04"))
    result = run_case(delivery)
    ex, paid = result["equity"].iloc[-2:].to_dict("records")
    assert ex["exposure"] == 0
    assert ex["receivables"] == 400
    assert paid["cash"] == 24_400
    assert paid["receivables"] == 0
    assert result["trades"].iloc[0]["pnl"] == -600
    assert len(result["fills"]) == 1  # settlement is not a fabricated market sale


def test_suspension_past_expiry_preserves_position_until_first_resumed_open():
    days = ["2023-01-02", "2023-01-03", "2023-02-03", "2023-02-04", "2023-02-06"]
    delivery = delivery_case((100, 100, None, None, 99), days)
    template = delivery["statuses"][0]
    delivery["statuses"] = [dict(template, effective_to="2023-02-02"),
        dict(template, status_id="halted", effective_from="2023-02-03", effective_to="2023-02-05", status="HALTED"),
        dict(template, status_id="resumed", effective_from="2023-02-06", effective_to=None)]
    result = run_case(delivery)
    overdue = result["positions"].loc[result["positions"]["date"].eq(pd.Timestamp("2023-02-04"))].iloc[0]
    assert overdue["quantity"] == 10
    assert overdue["overdue"]
    assert result["fills"].iloc[-1]["phase"] == "time_open"
    assert result["fills"].iloc[-1]["price"] == 99
    assert result["equity"].iloc[-1]["cash"] == 24_990


def test_pending_pre_split_entry_plan_is_converted_at_effective_date():
    delivery = delivery_case((100, 100, 50, 50))
    delivery["events"] = [action("SPLIT")]
    result = run_case(delivery, delay=2)
    assert result["fills"].iloc[0]["quantity"] == 20
    assert result["fills"].iloc[0]["price"] == 50
    assert result["plans"].iloc[0]["entry_cap"] == 50
    assert result["equity"].iloc[-1]["equity"] == 25_000


def test_payment_on_closed_date_is_recorded_on_exact_date_without_marking_stale():
    delivery = delivery_case((100, 100, 100, None, 100))
    delivery["events"] = [action("CASH_DIVIDEND")]
    delivery["calendar"][3].update(is_open=False, opens_at=None, closes_at=None)
    result = run_case(delivery)
    paid = result["equity"].set_index("date").loc[pd.Timestamp("2023-01-05")]
    assert paid["cash"] == 24_020
    assert paid["receivables"] == 0
    marked = result["positions"].set_index("date").loc[pd.Timestamp("2023-01-05")]
    assert not marked["stale"]
    assert len(result["fills"]) == 1
    assert result["cashflows"].iloc[-1]["date"] == pd.Timestamp("2023-01-05")


def test_reverse_split_eliminating_last_share_realizes_basis_without_fabricated_fill():
    delivery = delivery_case((100, 100, 2000, 2000))
    delivery["events"] = [action("REVERSE_SPLIT", quantity_ratio=0.05,
                                  fractional_policy="CASH_IN_LIEU", fractional_cash_price=1800)]
    result = run_case(delivery)
    assert result["positions"].iloc[-1]["date"] == pd.Timestamp("2023-01-03")
    assert result["equity"].iloc[-1]["cash"] == 24_900
    assert result["trades"].iloc[0]["pnl"] == -100
    assert len(result["fills"]) == 1


def test_full_loss_delisting_and_unsupported_same_day_order_fail_closed():
    delivery = delivery_case()
    delivery["events"] = [action("DELIST_CASH", cash_per_share=0)]
    result = run_case(delivery)
    assert result["equity"].iloc[-1]["cash"] == 24_000
    assert result["trades"].iloc[0]["pnl"] == -1000
    delivery["events"].append(action("CASH_DIVIDEND", event_id="event-2"))
    with pytest.raises(ValueError, match="SAME_DAY_EVENT_ORDER_UNSUPPORTED"):
        run_case(delivery)


def test_split_before_simulation_start_still_converts_delayed_plan():
    delivery = delivery_case((100, 100, 50, 50))
    delivery["events"] = [action("SPLIT")]
    signals = pd.DataFrame([dict(date="2023-01-02", instrument_id=ID, atr14=4, avg_volume20=1_000_000, entry=True)])
    result = simulate_delivery(delivery, signals, entry_id="entry", exit_id="PCT_5_10",
                               start="2023-01-05", end="2023-01-05", delay=3, initial_cash=25_000)
    assert result["fills"].iloc[0]["quantity"] == 20
    assert result["fills"].iloc[0]["price"] == 50


@pytest.mark.parametrize("change,match", [
    ({"announced_at": "2023-01-04T10:00:00+09:00"}, "EVENT_NOT_KNOWN_AT_OPEN"),
    ({"announced_at": "2023-01-04T09:00:00+09:00"}, "EVENT_NOT_KNOWN_AT_OPEN"),
    ({"event_type": "MERGER"}, "UNSUPPORTED_EVENT"),
    ({"pay_date": "2023-01-03"}, "PAYMENT_BEFORE_ENTITLEMENT"),
])
def test_unresolved_or_future_event_input_fails_closed(change, match):
    delivery = delivery_case()
    delivery["events"] = [action("CASH_DIVIDEND", **change)]
    with pytest.raises(ValueError, match=match):
        run_case(delivery)
