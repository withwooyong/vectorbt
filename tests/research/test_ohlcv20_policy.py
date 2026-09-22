from decimal import Decimal
import json
import os
from pathlib import Path

import pytest

from research.krx_lab.ohlcv20_policy import Cost2026, experiments, policy_manifest
from research.krx_lab.ohlcv20_execution import simulate_ohlcv20


def test_registered_comparison_has_both_baselines_and_no_narrow_stop_grid():
    rows = experiments()
    assert len(rows) == len({row.key for row in rows}) == 26
    assert {row.holding_months for row in rows if row.baseline} == {1, 3}
    assert {row.stop_pct for row in rows if not row.baseline} == {
        Decimal("0.10"),
        Decimal("0.15"),
        Decimal("0.20"),
    }
    assert policy_manifest()["real_execution_admitted"] is False


def test_policy_manifest_matches_delivered_machine_readable_contract():
    contract = (
        Path(__file__).resolve().parents[1]
        / "fixtures/ohlcv20/confirmed-strategy-policy-v1.json"
    )
    assert json.loads(contract.read_text(encoding="utf-8")) == policy_manifest()
    delivery_path = os.environ.get("OHLCV20_POLICY_DELIVERY")
    if delivery_path:
        delivered = Path(delivery_path)
        assert json.loads(delivered.read_text(encoding="utf-8")) == policy_manifest()
    assert policy_manifest()["capacity_failed_candidate_assignment"] == (
        "RETAIN_ORIGINAL_SLOT_NO_TRANSFER_TO_LATER_SLOT"
    )
    assert policy_manifest()["delisting_valuation"][
        "unresolved_held_mark_or_rights"
    ] == ("BLOCK_PERFORMANCE_NO_INVENTED_ZERO_OR_LAST_CLOSE")


@pytest.mark.parametrize(
    "market,tax,rural", [("KOSPI", 2500, 7500), ("KOSDAQ", 10000, 0)]
)
def test_5million_round_trip_separates_2026_broker_tax_from_friction(
    market, tax, rural
):
    cost = Cost2026("DOMESTIC_ORDINARY_SHARE")
    buy = cost.breakdown("BUY", market, 5_000_000)
    sell = cost.breakdown("SELL", market, 5_000_000)
    assert buy["commission"] == sell["commission"] == 750
    assert buy["transaction_tax"] == buy["rural_tax"] == 0
    assert (sell["transaction_tax"], sell["rural_tax"]) == (tax, rural)
    assert buy["total"] + sell["total"] == 21_500
    assert buy["modeled_friction"] + sell["modeled_friction"] == 10_000


def test_current_cost_regime_does_not_accidentally_follow_historical_day():
    base = Cost2026("DOMESTIC_ORDINARY_SHARE")
    stress = Cost2026("DOMESTIC_ORDINARY_SHARE", Decimal("0.002"))
    assert base("SELL", "2015-06-15", "KOSPI", 12345) == base(
        "SELL", "2023-12-28", "KOSPI", 12345
    )
    assert stress("BUY", "2015-06-15", "KOSDAQ", 5_000_000) == 10_750
    assert base("SELL", "2023-01-03", "KOSPI", 12345) == (
        base("SELL", "2023-01-03", "KOSPI", 12000)
        + base("SELL", "2023-01-03", "KOSPI", 345)
    )


@pytest.mark.parametrize("scope", ["DR", "FOREIGN_SHARE", "UNKNOWN"])
def test_unverified_instrument_scope_cannot_inherit_domestic_share_tax(scope):
    with pytest.raises(ValueError, match="TAX_SCOPE"):
        Cost2026(scope)


@pytest.mark.parametrize("value", [-1, "NaN", "Infinity", True])
def test_invalid_notional_rejected(value):
    with pytest.raises(ValueError, match="MONETARY"):
        Cost2026("DOMESTIC_ORDINARY_SHARE").breakdown("SELL", "KOSPI", value)


def test_cost_reservation_partial_sales_and_halt_preserve_one_slot_wealth():
    days = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05", "2023-01-06"]
    bars = [
        dict(
            date=day,
            code="A",
            market="KOSPI",
            open=opened,
            high=high,
            low=low,
            close=close,
            volume=volume,
            can_buy=can_trade,
            can_sell=can_trade,
            order_eligible=can_trade,
            mark_valid=True,
        )
        for day, opened, high, low, close, volume, can_trade in [
            (days[1], 100000, 101000, 99000, 100000, 10000, True),
            (days[2], 95000, 96000, 89000, 90000, 2000, True),
            (days[3], 0, 0, 0, 85000, 0, False),
            (days[4], 80000, 82000, 79000, 81000, 2900, True),
        ]
    ]
    result = simulate_ohlcv20(
        bars,
        [
            dict(
                signal_date=days[0],
                code="A",
                turnover=1_000_000_000,
                mean_turnover20=500_000_000,
                limit_price=100000,
                eligible=True,
            )
        ],
        days,
        start=days[1],
        end=days[-1],
        stop_pct="0.10",
        target_pct="0.30",
        holding_months=1,
        costs=Cost2026("DOMESTIC_ORDINARY_SHARE"),
        levels=lambda side, day, market, price: price,
    )
    assert result["status"] == "SUCCEEDED"
    assert result["performance_valid"] is False
    fills = result["fills"]
    assert fills["size"].tolist() == [49, 20, 29]
    assert fills["cost"].tolist() == [Decimal(5635), Decimal(5670), Decimal(7308)]
    slot = result["positions"].query("slot_id == 0")
    assert slot["size"].tolist() == [49, 29, 29, 0]
    assert slot.iloc[1].cash == slot.iloc[2].cash == Decimal(1888695)
    assert slot.iloc[-1].cash == Decimal(4201387)
    assert result["equity"].iloc[-1].equity == Decimal(99201387)
