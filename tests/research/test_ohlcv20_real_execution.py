"""Rights-aware portfolio execution with a real gate and fixture ledger."""

from hashlib import sha256
import json
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab.ohlcv20_real_execution import run_ohlcv20_portfolio
from research.krx_lab.ohlcv20_rights import RightsLedger, load_v4_terms


TERMS = (
    Path(__file__).resolve().parents[1]
    / "fixtures/ohlcv20/rights-price-payment-inputs-v4.parquet"
)
SHA = "c96aa8911fb4bb46d8d198596d6b1914120d587edcd6c7b2f9fb0fa1a7d7d2d5"
DAYS = list(
    pd.to_datetime(
        [
            "2015-06-29",
            "2015-06-30",
            "2015-08-07",
            "2015-08-10",
            "2015-08-11",
            "2015-08-13",
        ]
    )
)


def bar(day, code, price, volume, *, can_sell=True, can_buy=True, sell_status=None):
    return dict(
        date=day,
        code=code,
        market="KOSPI",
        open=price,
        high=price,
        low=price,
        close=price,
        volume=volume,
        can_buy=can_buy,
        can_sell=can_sell,
        sell_status=sell_status or ("SELLABLE" if can_sell else "NO_TRADE"),
        sell_status_verified=True,
        listing_status="LISTED",
        listing_status_verified=True,
        lower_limit_price=1,
        lower_limit_price_verified=True,
        order_eligible=can_buy,
        mark_valid=True,
    )


def fixture_inputs():
    old = "036710"
    successor = "222800"
    bars = [bar(DAYS[1], old, 450_000, 10_000)]
    for day, volume, tradable in (
        (DAYS[2], 0, False),
        (DAYS[3], 200, True),
        (DAYS[4], 300, True),
    ):
        bars.extend(
            (
                bar(day, old, 3900, volume, can_buy=False, can_sell=tradable),
                bar(day, successor, 11350, volume, can_buy=False, can_sell=tradable),
            )
        )
    signal = [
        dict(
            signal_date=DAYS[0],
            code=old,
            turnover=1_000_000_000,
            mean_turnover20=1_000_000_000,
            limit_price=450_000,
            eligible=True,
        )
    ]
    schedule = [dict(event_code=old, capture_on=DAYS[1], available_on=DAYS[2])]
    return bars, signal, schedule


def run_fixture(bars, signals, schedule, *, ledger=None):
    return run_ohlcv20_portfolio(
        bars,
        signals,
        DAYS,
        start=DAYS[1],
        end=DAYS[-1],
        stop_pct="0.10",
        target_pct="0.30",
        holding_months=3,
        costs=lambda *_: 0,
        levels=lambda _side, _day, _market, price: price,
        rights_ledger=ledger or RightsLedger(load_v4_terms(TERMS, SHA)),
        event_schedule=schedule,
        source_kind="SYNTHETIC_FIXTURE",
    )


def test_real_gate_refuses_current_unadmitted_inputs():
    bars, signals, schedule = fixture_inputs()
    with pytest.raises(ValueError, match="REAL_EXECUTION_NOT_ADMITTED"):
        run_ohlcv20_portfolio(
            bars,
            signals,
            DAYS,
            start=DAYS[1],
            end=DAYS[-1],
            stop_pct="0.10",
            target_pct="0.30",
            holding_months=3,
            costs=lambda *_: 0,
            levels=lambda _side, _day, _market, price: price,
            rights_ledger=RightsLedger(load_v4_terms(TERMS, SHA)),
            event_schedule=schedule,
            source_kind="REAL",
            admission={"real_execution_admitted": False},
        )


def test_real_gate_rejects_unbound_true_flags():
    bars, signals, schedule = fixture_inputs()
    flags = {
        key: True
        for key in (
            "immutable_input_verified",
            "daily_universe_admitted",
            "adjusted_price_admitted",
            "volume_factors_admitted",
            "corporate_coverage_admitted",
            "rights_admitted",
            "market_rules_admitted",
            "real_execution_admitted",
        )
    }
    with pytest.raises(ValueError, match="REAL_ADMISSION_EVIDENCE_MISSING"):
        run_ohlcv20_portfolio(
            bars,
            signals,
            DAYS,
            start=DAYS[1],
            end=DAYS[-1],
            stop_pct="0.10",
            target_pct="0.30",
            holding_months=3,
            costs=lambda *_: 0,
            levels=lambda _side, _day, _market, price: price,
            rights_ledger=RightsLedger.from_v4(TERMS, SHA),
            event_schedule=schedule,
            source_kind="REAL",
            admission=flags,
        )


def test_real_gate_requires_full_rights_event_schedule_even_with_positive_flags(
    tmp_path,
):
    bars, signals, schedule = fixture_inputs()
    flags = {
        name: True
        for name in (
            "immutable_input_verified",
            "daily_universe_admitted",
            "adjusted_price_admitted",
            "volume_factors_admitted",
            "corporate_coverage_admitted",
            "rights_admitted",
            "market_rules_admitted",
            "real_execution_admitted",
        )
    }
    source = tmp_path / "manifest.json"
    source.write_text(json.dumps({"real_execution_admitted": True}))
    receipt = tmp_path / "admission.json"
    receipt.write_text(
        json.dumps(
            dict(
                schema="ohlcv20-real-admission-v1",
                status="ADMITTED",
                **flags,
                source_manifest_sha256=sha256(source.read_bytes()).hexdigest(),
                rights_terms_sha256=SHA,
            )
        )
    )
    flags.update(
        source_manifest_path=str(source),
        admission_evidence_path=str(receipt),
        admission_evidence_sha256=sha256(receipt.read_bytes()).hexdigest(),
    )
    with pytest.raises(ValueError, match="INCOMPLETE_RIGHTS_EVENT_SCHEDULE"):
        run_ohlcv20_portfolio(
            bars,
            signals,
            DAYS,
            start=DAYS[1],
            end=DAYS[-1],
            stop_pct="0.10",
            target_pct="0.30",
            holding_months=3,
            costs=lambda *_: 0,
            levels=lambda _side, _day, _market, price: price,
            rights_ledger=RightsLedger.from_v4(TERMS, SHA),
            event_schedule=schedule,
            source_kind="REAL",
            admission=flags,
        )


def test_spinoff_two_legs_halt_partial_sales_and_later_cash_same_slot():
    bars, signals, schedule = fixture_inputs()
    result = run_fixture(bars, signals, schedule)
    assert result["status"] == "SUCCEEDED"
    assert not result["performance_valid"]
    fills = result["fills"]
    assert fills.side.tolist() == ["BUY", "SELL", "SELL", "SELL", "SELL"]
    assert fills.loc[fills.side.eq("BUY"), "size"].tolist() == [11]
    sold = fills.loc[fills.side.eq("SELL")]
    assert sorted(sold.groupby(["date", "code"])["size"].sum().tolist()) == [2, 2, 3, 3]
    assert set(sold.slot_id) == {0}
    assert not sold.date.eq(DAYS[2]).any()  # Conversion-day halt.
    converted = result["rights_events"]
    assert set(converted.code) == {"036710", "222800"}
    assert converted.new_shares.tolist() == [5, 5]
    assert (
        result["equity"]
        .loc[result["equity"].date.eq(DAYS[2]), "positions_count"]
        .iloc[0]
        == 2
    )
    receipts = result["cash_receipts"]
    assert len(receipts) == 2
    assert set(receipts.slot_id) == {0}
    assert set(receipts.date) == {DAYS[-1]}
    assert all(receipts.exact_denominator > 0)
    assert (
        result["equity"].loc[result["equity"].date.eq(DAYS[2]), "receivables"].iloc[0]
        > 0
    )
    assert (
        result["equity"].loc[result["equity"].date.eq(DAYS[-1]), "receivables"].iloc[0]
        == 0
    )


def test_captured_old_shares_cannot_trade_before_conversion():
    bars, signals, schedule = fixture_inputs()
    schedule[0]["available_on"] = DAYS[3]
    intermediate = next(
        row for row in bars if row["date"] == DAYS[2] and row["code"] == "036710"
    )
    intermediate["can_sell"] = True
    intermediate["sell_status"] = "SELLABLE"
    intermediate["volume"] = 100
    result = run_fixture(bars, signals, schedule)
    assert result["status"] == "BLOCKED"
    assert any("CAPTURED_RIGHTS_SUSPENSION_NOT_VERIFIED" in x for x in result["issues"])
    assert result["equity"].empty


def test_captured_old_shares_require_positive_suspension_evidence():
    bars, signals, schedule = fixture_inputs()
    schedule[0]["available_on"] = DAYS[3]
    intermediate = next(
        row for row in bars if row["date"] == DAYS[2] and row["code"] == "036710"
    )
    assert (
        "CAPTURED_RIGHTS_SUSPENSION_NOT_VERIFIED"
        in run_fixture(bars, signals, schedule)["issues"][0]
    )
    intermediate["rights_suspension_verified"] = True
    assert run_fixture(bars, signals, schedule)["status"] == "SUCCEEDED"


def test_untradeable_intraday_quote_requires_explicit_regular_session_proof():
    code = "777777"
    quote = bar(DAYS[2], code, 100, 100, can_buy=False, can_sell=False)
    quote["high"] = 200  # Vendor high alone must not set a pending target.
    bars = [bar(DAYS[1], code, 100, 100_000), quote, bar(DAYS[3], code, 100, 6_000_000)]
    signal = [
        dict(
            signal_date=DAYS[0],
            code=code,
            turnover=1_000_000_000,
            mean_turnover20=1_000_000_000,
            limit_price=100,
            eligible=True,
        )
    ]

    def execute():
        return run_ohlcv20_portfolio(
            bars,
            signal,
            DAYS,
            start=DAYS[1],
            end=DAYS[3],
            stop_pct="0.10",
            target_pct="0.30",
            holding_months=3,
            costs=lambda *_: 0,
            levels=lambda _side, _day, _market, price: price,
            rights_ledger=RightsLedger({}),
            source_kind="SYNTHETIC_FIXTURE",
        )

    assert execute()["fills"].side.tolist() == ["BUY"]
    quote["regular_session_trigger_valid"] = True
    assert execute()["fills"].side.tolist() == ["BUY", "SELL"]


def test_unvalued_delisted_holding_blocks_performance_even_with_stale_positive_close():
    code = "777777"
    first = bar(DAYS[1], code, 100, 100_000)
    stale = bar(DAYS[2], code, 100, 0, can_buy=False, can_sell=False)
    stale["listing_status"] = "DELISTED"
    signal = [
        dict(
            signal_date=DAYS[0],
            code=code,
            turnover=1_000_000_000,
            mean_turnover20=1_000_000_000,
            limit_price=100,
            eligible=True,
        )
    ]
    result = run_fixture([first, stale], signal, [])
    assert result["status"] == "BLOCKED"
    assert result["issues"] == [f"UNVALUED_DELISTED_HOLDING:{DAYS[2]}:{code}"]
    assert result["equity"].empty
    assert result["positions"].empty


def test_positive_volume_lower_limit_lock_cannot_fill_stop_sale():
    code = "777777"
    locked = bar(
        DAYS[2],
        code,
        70,
        100_000,
        can_buy=False,
        can_sell=False,
        sell_status="LOWER_LIMIT_LOCKED",
    )
    locked["lower_limit_price"] = 70
    locked["regular_session_trigger_valid"] = True
    signal = [
        dict(
            signal_date=DAYS[0],
            code=code,
            turnover=1_000_000_000,
            mean_turnover20=1_000_000_000,
            limit_price=100,
            eligible=True,
        )
    ]
    result = run_fixture(
        [bar(DAYS[1], code, 100, 100_000), locked, bar(DAYS[3], code, 70, 6_000_000)],
        signal,
        [],
    )
    assert result["status"] == "SUCCEEDED"
    assert result["fills"].side.tolist() == ["BUY", "SELL"]
    assert result["fills"].loc[result["fills"].side.eq("SELL"), "date"].tolist() == [
        DAYS[3]
    ]


def test_sellable_lower_limit_locked_bar_is_rejected_even_with_positive_volume():
    quote = bar(DAYS[1], "777777", 70, 100_000)
    quote["lower_limit_price"] = 70
    with pytest.raises(ValueError, match="LOWER_LIMIT_LOCKED_SELL_STATUS_CONFLICT"):
        run_fixture([quote], [], [])


@pytest.mark.parametrize(
    ("flag", "error"),
    [
        ("sell_status_verified", "VERIFIED_SELL_STATUS_REQUIRED"),
        ("listing_status_verified", "VERIFIED_LISTING_STATUS_REQUIRED"),
        ("lower_limit_price_verified", "VERIFIED_LOWER_LIMIT_PRICE_REQUIRED"),
    ],
)
def test_execution_refuses_unverified_daily_status(flag, error):
    quote = bar(DAYS[1], "777777", 100, 100_000)
    quote[flag] = False
    with pytest.raises(ValueError, match=error):
        run_fixture([quote], [], [])


def test_capacity_overflow_candidate_does_not_move_to_smaller_slot():
    old, overflow, next_candidate = "777777", "888888", "999999"
    bars = [
        bar(DAYS[1], old, 100, 100_000),
        bar(DAYS[2], old, 50, 5_000_000),
        bar(DAYS[3], overflow, 100, 100_000),
        bar(DAYS[3], next_candidate, 100, 100_000),
    ]
    signals = [
        dict(
            signal_date=DAYS[0],
            code=old,
            turnover=2_000_000_000,
            mean_turnover20=1_000_000_000,
            limit_price=100,
            eligible=True,
        ),
        dict(
            signal_date=DAYS[2],
            code=overflow,
            turnover=2_000_000_000,
            mean_turnover20=300_000_000,
            limit_price=100,
            eligible=True,
        ),
        dict(
            signal_date=DAYS[2],
            code=next_candidate,
            turnover=1_000_000_000,
            mean_turnover20=1_000_000_000,
            limit_price=100,
            eligible=True,
        ),
    ]
    # Occupy slots 1..18 so the larger untouched slot 19 is first in idle order,
    # followed by slot 0 after its loss and sale on DAYS[2].
    for number in range(18):
        code = str(100001 + number)
        signals.append(
            dict(
                signal_date=DAYS[0],
                code=code,
                turnover=1_900_000_000 - number,
                mean_turnover20=1_000_000_000,
                limit_price=100,
                eligible=True,
            )
        )
        bars.extend(bar(day, code, 100, 100_000) for day in DAYS[1:4])
    result = run_ohlcv20_portfolio(
        bars,
        signals,
        DAYS,
        start=DAYS[1],
        end=DAYS[3],
        stop_pct="0.10",
        target_pct="0.30",
        holding_months=3,
        costs=lambda *_: 0,
        levels=lambda _side, _day, _market, price: price,
        rights_ledger=RightsLedger({}),
        source_kind="SYNTHETIC_FIXTURE",
    )
    assert result["status"] == "SUCCEEDED"
    orders = result["orders"].set_index("code")
    assert orders.loc[overflow, "slot_id"] == 19
    assert orders.loc[overflow, "status"] == "BUY_LIQUIDITY_LIMIT_EXCEEDED"
    assert orders.loc[next_candidate, "slot_id"] == 0
    assert orders.loc[next_candidate, "status"] == "FILLED"


def test_slot_reuse_waits_until_both_legs_are_fully_sold():
    bars, signals, schedule = fixture_inputs()
    # Fill the other 19 slots so the old event slot is the only possible
    # destination after both successor legs have been fully sold.
    for number in range(19):
        code = str(100001 + number)
        signals.append(
            dict(
                signal_date=DAYS[0],
                code=code,
                turnover=900_000_000,
                mean_turnover20=1_000_000_000,
                limit_price=10_000,
                eligible=True,
            )
        )
        bars.extend(bar(day, code, 10_000, 100_000) for day in DAYS[1:])
    bars.append(bar(DAYS[5], "999999", 10_000, 100_000))
    signals.extend(
        (
            dict(
                signal_date=DAYS[3],
                code="888888",
                turnover=1_000_000_000,
                mean_turnover20=1_000_000_000,
                limit_price=10_000,
                eligible=True,
            ),
            dict(
                signal_date=DAYS[4],
                code="999999",
                turnover=1_000_000_000,
                mean_turnover20=1_000_000_000,
                limit_price=10_000,
                eligible=True,
            ),
        )
    )
    result = run_fixture(bars, signals, schedule)
    assert result["status"] == "SUCCEEDED"
    orders = result["orders"]
    # No new order can take the event slot on the session with residual shares.
    assert orders.loc[orders.code.eq("888888")].empty
    assert orders.loc[orders.code.eq("999999"), "slot_id"].tolist() == [0]


def test_each_configuration_gets_fresh_rights_state():
    bars, signals, schedule = fixture_inputs()
    ledger = RightsLedger(load_v4_terms(TERMS, SHA))
    first = run_fixture(bars, signals, schedule, ledger=ledger)
    second = run_fixture(bars, signals, schedule, ledger=ledger)
    assert first["cash_receipts"].to_dict("records") == second["cash_receipts"].to_dict(
        "records"
    )


def test_unconverted_rights_at_end_withhold_performance():
    bars, signals, schedule = fixture_inputs()
    result = run_ohlcv20_portfolio(
        bars,
        signals,
        DAYS,
        start=DAYS[1],
        end=DAYS[1],
        stop_pct="0.10",
        target_pct="0.30",
        holding_months=3,
        costs=lambda *_: 0,
        levels=lambda _side, _day, _market, price: price,
        rights_ledger=RightsLedger(load_v4_terms(TERMS, SHA)),
        event_schedule=schedule,
        source_kind="SYNTHETIC_FIXTURE",
    )
    assert result["status"] == "BLOCKED"
    assert "UNCONVERTED_RIGHTS_AT_EVALUATION_END" in result["issues"]
    assert result["equity"].empty
