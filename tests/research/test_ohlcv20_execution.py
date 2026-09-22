"""Synthetic boundary and independent sleeve conservation checks."""

from decimal import Decimal

import pandas as pd
import pytest

from research.krx_lab.ohlcv20_execution import simulate_ohlcv20


def bar(day, code="A", **updates):
    row = dict(
        date=day,
        code=code,
        market="KOSPI",
        open=100,
        high=101,
        low=99,
        close=100,
        volume=10_000_000,
        can_buy=True,
        can_sell=True,
        regular_session_trigger_valid=False,
        order_eligible=True,
        mark_valid=True,
    )
    return dict(row, **updates)


def signal(day, code="A", turnover=100, limit=100, mean_turnover20=1_000_000_000):
    return dict(
        signal_date=day,
        code=code,
        turnover=turnover,
        limit_price=limit,
        eligible=True,
        mean_turnover20=mean_turnover20,
    )


def run(bars, signals, days, **updates):
    options = dict(
        start=days[1],
        end=days[-1],
        stop_pct="0.05",
        target_pct="0.15",
        holding_months=1,
        costs=lambda *args: 0,
        levels=lambda side, day, market, price: price,
    )
    options.update(updates)
    return simulate_ohlcv20(bars, signals, days, **options)


def test_untradeable_high_low_do_not_create_next_open_exit():
    days = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    result = run(
        [
            bar(days[1]),
            bar(
                days[2],
                open=100,
                high=125,
                low=75,
                close=100,
                can_buy=False,
                can_sell=False,
            ),
            bar(days[3]),
        ],
        [signal(days[0])],
        days,
    )
    assert result["status"] == "SUCCEEDED"
    assert result["fills"].side.tolist() == ["BUY"]


def test_open_improvement_reserves_quantity_at_limit_and_uses_actual_fill_levels():
    days = ["2023-01-02", "2023-01-03"]
    result = run(
        [bar(days[1], open=90, low=89, high=104, close=103)], [signal(days[0])], days
    )
    assert result["status"] == "SUCCEEDED"
    buy, sell = result["fills"].to_dict("records")
    assert (buy["size"], buy["price"], sell["price"]) == (50_000, 90, Decimal("103.50"))
    assert result["equity"].iloc[-1].equity == Decimal("100675000.00")


@pytest.mark.parametrize(
    "low,close,expected",
    [
        (100, 102, []),
        (99, 105, ["BUY"]),
        (99, 116, ["BUY", "SELL"]),
        (94, 116, ["BUY", "SELL"]),
    ],
)
def test_intraday_touch_preentry_high_and_stop_order(low, close, expected):
    days = ["2023-01-02", "2023-01-03"]
    result = run(
        [bar(days[1], open=110, high=120, low=low, close=close)],
        [signal(days[0])],
        days,
    )
    assert result["fills"].get("side", pd.Series(dtype=str)).tolist() == expected
    if len(expected) == 2:
        assert result["fills"].iloc[-1].price == (95 if low == 94 else 115)
    if low == 99 and close == 105:
        diagnostic = result["diagnostics"].iloc[0]
        assert (
            diagnostic.kind,
            diagnostic.action,
            diagnostic.slot_id,
            diagnostic.code,
        ) == ("intraday_preentry_high_possible", "HOLD", 0, "A")


def test_expiry_after_weekend_and_halt_never_previous_session():
    days = ["2023-01-05", "2023-01-06", "2023-02-03", "2023-02-06", "2023-02-07"]
    bars = [bar(day) for day in days[1:]]
    bars[2].update(can_sell=False, can_buy=False, volume=0)
    result = run(bars, [signal(days[0])], days)
    assert result["fills"].iloc[-1].date == pd.Timestamp("2023-02-07")
    assert result["fills"].iloc[-1].reason == "deferred_or_expiry_open"


def test_turnover_then_code_and_no_unfilled_replacement():
    days = ["2023-01-02", "2023-01-03"]
    codes = [f"{i:06d}" for i in range(21)]
    sigs = [signal(days[0], code, turnover=100) for code in reversed(codes)]
    bars = [
        bar(days[1], code, open=110, high=120, low=105, close=110) for code in codes
    ]
    bars[-1] = bar(days[1], codes[-1])
    result = run(bars, sigs, days)
    assert result["fills"].empty
    assert result["orders"].code.tolist() == codes[:20]
    assert result["orders"].slot_id.tolist() == list(range(20))


def test_oldest_idle_first_no_same_day_reuse_and_no_duplicate_held():
    days = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    sigs = [
        signal(days[0], "A", turnover=200),
        signal(days[0], "B"),
        signal(days[1], "A"),
        signal(days[1], "B"),
        signal(days[2], "C"),
    ]
    bars = [bar(day, code) for day in days[1:] for code in ("A", "B", "C")]
    for row in bars:
        if row["date"] == days[2] and row["code"] == "A":
            row.update(open=120, high=121, low=119, close=120)
    result = run(bars, sigs, days)
    buys = result["fills"].query("side == 'BUY'")
    assert buys.code.tolist() == ["A", "B", "C"]
    assert buys.slot_id.tolist() == [0, 1, 2]
    assert result["orders"].date.eq(pd.Timestamp("2023-01-04")).sum() == 0
    assert result["equity"].iloc[-1].equity == 101_000_000


def test_slot_proceeds_stay_local_and_reinvest_next_session():
    days = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    codes = [str(i) for i in range(20)]
    sigs = [signal(days[0], c, turnover=1000 - int(c)) for c in codes] + [
        signal(days[2], "X")
    ]
    bars = [bar(day, c) for day in days[1:] for c in codes + ["X"]]
    for row in bars:
        if row["code"] == "0" and row["date"] == days[2]:
            row.update(open=120, high=120, low=120, close=120)
    result = run(bars, sigs, days)
    last = result["fills"].iloc[-1]
    assert (last.code, last.slot_id, last["size"]) == ("X", 0, 60_000)
    final = result["positions"].loc[
        result["positions"].date.eq(pd.Timestamp("2023-01-05"))
    ]
    assert final.equity.sum() == 101_000_000


def test_fees_and_sell_tax_preserve_slot_cash_independently():
    days = ["2023-01-02", "2023-01-03"]

    def costs(side, day, market, value):
        return value * Decimal("0.001" if side == "BUY" else "0.003")

    result = run(
        [bar(days[1], high=120, close=116)], [signal(days[0])], days, costs=costs
    )
    buy, sell = result["fills"].to_dict("records")
    quantity = 49_950
    remaining = Decimal(5_000_000) - quantity * Decimal("100.1")
    expected = remaining + quantity * Decimal("115") * Decimal("0.997")
    assert buy["size"] == quantity
    assert sell["size"] == quantity
    assert result["equity"].iloc[-1].equity == Decimal(95_000_000) + expected


@pytest.mark.parametrize("reason", ["event", "missing", "unknownmark"])
def test_unknown_exposure_blocks_and_withholds_equity(reason):
    days = ["2023-01-02", "2023-01-03", "2023-01-04"]
    bars = [bar(day) for day in days[1:]]
    kwargs = {}
    if reason == "event":
        kwargs["events"] = [
            dict(effective_date=days[2], code="A", event_type="SPINOFF")
        ]
    elif reason == "missing":
        bars.pop()
    else:
        bars[-1]["mark_valid"] = False
    result = run(bars, [signal(days[0])], days, **kwargs)
    assert result["status"] == "BLOCKED"
    assert result["equity"].empty and result["positions"].empty
    assert len(result["fills"]) == 1


def test_real_input_cannot_be_promoted_by_caller():
    with pytest.raises(ValueError, match="REAL_EXECUTION_NOT_ADMITTED"):
        run([], [], ["2023-01-02", "2023-01-03"], source_kind="REAL")


def test_optimistic_sensitivity_only_changes_ambiguous_open_positions():
    days = ["2023-01-02", "2023-01-03"]
    bars = [bar(days[1], high=120, low=94)]
    pessimistic = run(bars, [signal(days[0])], days)
    optimistic = run(bars, [signal(days[0])], days, optimistic=True)
    assert pessimistic["fills"].iloc[-1].price == 95
    assert optimistic["fills"].iloc[-1].price == 115
    assert pessimistic["diagnostics"].iloc[0].kind == "simultaneous_stop_target"
    assert pessimistic["diagnostics"].iloc[0].action == "STOP"
    assert optimistic["diagnostics"].iloc[0].action == "TARGET"


def test_three_month_monthend_uses_first_session_after_sunday():
    days = ["2023-01-30", "2023-01-31", "2023-04-28", "2023-05-02"]
    result = run(
        [bar(day) for day in days[1:]], [signal(days[0])], days, holding_months=3
    )
    assert result["fills"].iloc[-1].date == pd.Timestamp("2023-05-02")


def test_unfilled_slot_retains_oldest_idle_priority():
    days = ["2023-01-02", "2023-01-03", "2023-01-04"]
    bars = [
        bar(days[1], "A", open=110, low=105, high=111, close=110),
        bar(days[2], "B"),
    ]
    result = run(bars, [signal(days[0], "A"), signal(days[1], "B")], days)
    assert result["orders"].slot_id.tolist() == [0, 0]


def test_zero_volume_halt_preserves_mark_without_executable_zeros():
    days = ["2023-01-02", "2023-01-03", "2023-01-04"]
    bars = [
        bar(days[1]),
        bar(days[2], open=0, high=0, low=0, volume=0, can_buy=False, can_sell=False),
    ]
    result = run(bars, [signal(days[0])], days)
    assert result["status"] == "SUCCEEDED"
    assert len(result["fills"]) == 1
    assert result["equity"].iloc[-1].equity == 100_000_000


def test_triggered_stop_waits_until_sellable_open():
    days = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    bars = [
        bar(days[1]),
        bar(
            days[2],
            open=90,
            high=90,
            low=90,
            close=90,
            can_sell=False,
            regular_session_trigger_valid=True,
        ),
        bar(days[3], open=97, high=100, low=97, close=100),
    ]
    result = run(bars, [signal(days[0])], days)
    assert result["fills"].iloc[-1].price == 97
    assert result["fills"].iloc[-1].date == pd.Timestamp(days[-1])


def test_ambiguous_intraday_entry_remains_stop_first_in_sensitivity():
    days = ["2023-01-02", "2023-01-03"]
    result = run(
        [bar(days[1], open=110, high=120, low=94, close=116)],
        [signal(days[0])],
        days,
        optimistic=True,
    )
    assert result["fills"].iloc[-1].price == 95


def test_open_exit_does_not_create_later_intraday_ambiguity():
    days = ["2023-01-02", "2023-01-03", "2023-01-04"]
    bars = [bar(days[1]), bar(days[2], open=120, high=121, low=90, close=100)]
    result = run(bars, [signal(days[0])], days)
    assert result["fills"].iloc[-1].reason == "target_gap_open"
    assert result["diagnostics"].empty


def test_sell_cost_cannot_overdraw_independent_slot():
    days = ["2023-01-02", "2023-01-03"]

    def costs(side, day, market, amount):
        return amount + 1 if side == "SELL" else 0

    with pytest.raises(ValueError, match="SELL_COST_EXCEEDS_SLOT_ASSETS"):
        run([bar(days[1], high=120, close=116)], [signal(days[0])], days, costs=costs)


def test_partial_open_exit_latches_and_never_sells_twice_same_day():
    days = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05", "2023-01-06"]
    bars = [
        bar(days[1]),
        bar(days[2], open=120, high=125, low=90, close=100, volume=550),
        bar(days[3], open=101, high=102, low=99, close=100, volume=299),
        bar(days[4], open=102, high=103, low=99, close=100, volume=300),
    ]
    result = run(
        bars,
        [signal(days[0]), signal(days[2]), signal(days[3])],
        days,
        initial_cash=20_000,
    )
    sells = result["fills"].query("side == 'SELL'")
    assert sells["size"].tolist() == [5, 2, 3]
    assert sells.price.tolist() == [120, 101, 102]
    assert result["orders"].shape[0] == 1
    slot = result["positions"].query("slot_id == 0")
    assert slot["size"].tolist() == [10, 5, 3, 0]
    assert slot.cash.tolist() == [0, 600, 802, 1108]
    assert "simultaneous_stop_target" not in result["diagnostics"].kind.tolist()
    assert result["performance_valid"] is False


@pytest.mark.parametrize("volume,can_sell", [(99, True), (1000, False)])
def test_zero_fill_target_exit_persists_to_next_sellable_open(volume, can_sell):
    days = ["2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    bars = [
        bar(days[1]),
        bar(
            days[2],
            high=116,
            close=110,
            volume=volume,
            can_sell=can_sell,
            regular_session_trigger_valid=not can_sell,
        ),
        bar(days[3], open=102, high=103, low=100, close=102),
    ]
    result = run(bars, [signal(days[0])], days, initial_cash=20_000)
    sells = result["fills"].query("side == 'SELL'")
    assert len(sells) == 1
    assert (sells.iloc[0].date, sells.iloc[0].price, sells.iloc[0]["size"]) == (
        pd.Timestamp(days[3]),
        102,
        10,
    )


def test_new_intraday_position_target_latches_while_unsellable():
    days = ["2023-01-02", "2023-01-03", "2023-01-04"]
    bars = [
        bar(
            days[1],
            open=110,
            high=116,
            low=99,
            close=116,
            can_sell=False,
            regular_session_trigger_valid=True,
        ),
        bar(days[2], open=102, high=103, low=100, close=102),
    ]
    result = run(bars, [signal(days[0])], days, initial_cash=20_000)
    assert result["fills"].iloc[-1].reason == "deferred_or_expiry_open"
    assert result["fills"].iloc[-1].price == 102


def test_partial_exit_halt_and_full_exit_next_session_reuse():
    days = [
        "2023-01-02",
        "2023-01-03",
        "2023-01-04",
        "2023-01-05",
        "2023-01-06",
        "2023-01-09",
    ]
    codes = [f"{i:02d}" for i in range(20)]
    bars = [bar(day, code) for day in days[1:] for code in codes + ["X"]]
    for row in bars:
        if row["code"] == "00" and row["date"] == days[2]:
            row.update(open=90, high=100, low=89, volume=500)
        if row["code"] == "00" and row["date"] == days[3]:
            row.update(volume=0, can_buy=False, can_sell=False)
    signals = [signal(days[0], code) for code in codes]
    signals += [signal(day, "X") for day in days[1:-1]]
    result = run(bars, signals, days, initial_cash=20_000)
    replacement = result["fills"].query("side == 'BUY' and code == 'X'")
    assert len(replacement) == 1
    assert (
        replacement.iloc[0].date,
        replacement.iloc[0].slot_id,
        replacement.iloc[0]["size"],
    ) == (pd.Timestamp(days[5]), 0, 9)


@pytest.mark.parametrize(
    "mean,expected", [(100_000, "FILLED"), (99_999, "BUY_LIQUIDITY_LIMIT_EXCEEDED")]
)
def test_buy_capacity_checks_full_reserved_notional_before_open_improvement(
    mean, expected
):
    days = ["2023-01-02", "2023-01-03"]
    result = run(
        [bar(days[1], open=90, high=91, low=89, close=90)],
        [signal(days[0], mean_turnover20=mean)],
        days,
        initial_cash=20_000,
    )
    assert result["orders"].iloc[0].status == expected
    if expected != "FILLED":
        assert result["fills"].empty


def test_buy_capacity_uses_cost_affordable_integer_order_and_no_replacement():
    days = ["2023-01-02", "2023-01-03"]
    result = run(
        [bar(days[1])],
        [signal(days[0], mean_turnover20=90_000)],
        days,
        initial_cash=20_000,
        costs=lambda side, day, market, amount: amount * Decimal("0.01"),
    )
    assert result["fills"].iloc[0]["size"] == 9
    codes = [f"{i:02d}" for i in range(21)]
    result = run(
        [bar(days[1], code) for code in codes],
        [
            signal(days[0], code, mean_turnover20=1 if code == "00" else 1_000_000)
            for code in codes
        ],
        days,
        initial_cash=20_000,
    )
    assert result["orders"].code.tolist() == codes[:20]
    assert result["fills"].code.tolist() == codes[1:20]
    assert result["orders"].iloc[0].status == "BUY_LIQUIDITY_LIMIT_EXCEEDED"


@pytest.mark.parametrize("mean", [None, 0, -1, "NaN", "Infinity"])
def test_missing_or_invalid_prior_mean_turnover_fails_closed(mean):
    days = ["2023-01-02", "2023-01-03"]
    row = signal(days[0], mean_turnover20=mean)
    if mean is None:
        row.pop("mean_turnover20")
    with pytest.raises(ValueError):
        run([bar(days[1])], [row], days)
