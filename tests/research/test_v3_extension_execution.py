"""Causal duration, signal exits, and monthly portfolio execution oracles."""
from decimal import Decimal

import pandas as pd
import pytest

from research.krx_lab.v3_execution import PreparedExecution, audit_execution_ledger, simulate_real_slot


class _Rules:
    def tick(self, day, market, price):
        return Decimal(1)

    def price_limit(self, day, market):
        return Decimal("0.30")

    def settlement_sessions(self, day, market):
        return 2

    def fees(self, day, market, side, amount):
        return {"fee": Decimal(0), "tax": Decimal(0), "total": Decimal(0)}


def _prepared(*, last="2023-08-10", codes=("A",), signal_days=None, high=101, low=99):
    days = pd.bdate_range("2023-01-27", last)
    prices = pd.DataFrame(
        dict(date=day, code=code, market="KOSPI", raw_open=100, raw_high=high,
             raw_low=low, raw_close=100, volume=100_000, status="TRADING", eligible=True)
        for day in days for code in codes
    )
    if signal_days is None:
        signal_days = {"2023-01-30": {"A"}}
    signals = pd.DataFrame(
        dict(date=day, code=code, close=100, atr14=2, avg_volume20=100_000_000,
             ENTRY=code in selected, EXIT=day == "2023-02-02" and code == "A")
        for day, selected in signal_days.items() for code in codes
    )
    return PreparedExecution(prices, signals, days)


def _run(prepared, **options):
    return simulate_real_slot(prepared, _Rules(), entry_id="ENTRY", exit_id="PCT_3_6",
                              start="2023-01-31", end=prepared.calendar[-1], **options)


def test_default_duration_matches_explicit_one_month_and_calendar_month_end():
    data = _prepared()
    default = _run(data)
    explicit = _run(data, max_holding_months=1)
    assert default["status"] == explicit["status"] == "SUCCEEDED"
    for name, frame in default.items():
        if isinstance(frame, pd.DataFrame):
            pd.testing.assert_frame_equal(frame, explicit[name])
    assert default["fills"].iloc[1]["date"] == pd.Timestamp("2023-02-28")
    for months, expected in ((3, "2023-04-28"), (6, "2023-07-31")):
        result = _run(data, max_holding_months=months)
        assert result["status"] == "SUCCEEDED"
        assert result["fills"].side.tolist() == ["buy", "sell"]
        assert result["fills"].iloc[1]["date"] == pd.Timestamp(expected)
        assert result["fills"].iloc[1]["phase"] == "time_open"
        audit_execution_ledger(result)


def test_close_signal_exits_next_open_and_fixed_target_can_be_suppressed():
    data = _prepared(last="2023-02-10", high=107,
                     signal_days={"2023-01-30": {"A"}, "2023-02-02": set()})
    result = _run(data, exit_signal_id="EXIT", suppress_target=True)
    assert result["status"] == "SUCCEEDED"
    assert result["fills"].side.tolist() == ["buy", "sell"]
    assert result["fills"].iloc[1]["date"] == pd.Timestamp("2023-02-03")
    assert result["fills"].iloc[1]["phase"] == "signal_open"
    assert result["fills"].iloc[1]["price"] == Decimal(100)
    audit_execution_ledger(result)


def test_exit_signal_survives_halt_and_does_not_attach_to_a_later_buy():
    data = _prepared(last="2023-02-10",
                     signal_days={"2023-01-30": {"A"}, "2023-02-02": set()})
    halted = data.prices_by_day[pd.Timestamp("2023-02-03")]
    halted.loc["A", "status"] = "HALTED"
    halted.loc["A", "eligible"] = False
    halted.loc["A", "volume"] = 0
    result = _run(data, exit_signal_id="EXIT")
    assert result["status"] == "SUCCEEDED"
    assert result["fills"].iloc[1]["date"] == pd.Timestamp("2023-02-06")
    assert result["fills"].iloc[1]["phase"] == "signal_open"
    audit_execution_ledger(result)

    # The Jan 30 signal occurred before the Jan 31 entry. It cannot exit
    # the position that was opened after that signal's close.
    before_buy = _prepared(last="2023-02-10")
    before_buy.signals["EXIT"] = True
    later = _run(before_buy, exit_signal_id="EXIT", max_holding_months=None)
    assert later["fills"].side.tolist() == ["buy"]


def test_suppressed_target_does_not_label_stop_as_ambiguous():
    data = _prepared(last="2023-02-10", high=107, low=95)
    result = _run(data, suppress_target=True)
    assert result["fills"].iloc[1]["phase"] == "stop_intraday"


@pytest.mark.parametrize("missing", [False, True])
def test_missing_or_invalid_prior_exit_evaluation_blocks_held_return(missing):
    data = _prepared(last="2023-02-10",
                     signal_days={"2023-01-30": {"A"}, "2023-01-31": set()})
    data.signals["LOW20_VALID"] = True
    if missing:
        data.signals = data.signals.loc[data.signals.date.ne(pd.Timestamp("2023-01-31"))].copy()
    else:
        data.signals.loc[data.signals.date.eq(pd.Timestamp("2023-01-31")), "LOW20_VALID"] = False
    result = _run(data, exit_signal_id="EXIT", exit_signal_valid_id="LOW20_VALID",
                  suppress_target=True)
    assert result["status"] == "BLOCKED"
    assert result["equity"].empty
    assert result["trades"].empty
    assert "INVALID_EXIT_SIGNAL_INPUT:2023-02-01:A" in result["issues"]


def test_exit_validity_is_ignored_before_first_position():
    data = _prepared(last="2023-02-10")
    data.signals["LOW20_VALID"] = False
    result = _run(data, exit_signal_id="EXIT", exit_signal_valid_id="LOW20_VALID",
                  suppress_target=True)
    assert result["fills"].side.tolist()[0] == "buy"
    assert "INVALID_EXIT_SIGNAL_INPUT:2023-01-31:A" not in result["issues"]


def test_monthly_selection_keeps_selected_holdings_and_counts_actual_fills():
    signals = {"2023-01-30": {"A", "B"}, "2023-02-27": {"B", "C"}}
    data = _prepared(last="2023-03-03", codes=("A", "B", "C"), signal_days=signals,
                     high=107, low=94)
    data.signals.loc[data.signals.date.eq(pd.Timestamp("2023-02-27")), "EXIT"] = (
        data.signals.code.eq("A")
    )
    result = _run(data, max_holding_months=None, exit_signal_id="EXIT",
                  suppress_stop=True, suppress_target=True,
                  position_sizing="equal_weight", entry_order="market_open")
    assert result["status"] == "SUCCEEDED"
    fills = result["fills"]
    assert fills.side.tolist().count("buy") == 3
    assert fills.side.tolist().count("sell") == 1
    assert fills.loc[fills.side.eq("sell"), "code"].tolist() == ["A"]
    assert set(fills.loc[fills.side.eq("buy"), "code"]) == {"A", "B", "C"}
    assert result["plans"].loc[(result["plans"].code.eq("B"))
                               & (result["plans"].signal_date.eq(pd.Timestamp("2023-02-27"))),
                               "reason"].iloc[0] == "ALREADY_HELD_OR_EXITED"
    for fill in fills.loc[fills.side.eq("buy")].itertuples(index=False):
        assert fill.size == 40_000  # 4% of the original account at 100/share.
    audit_execution_ledger(result)


@pytest.mark.parametrize("options", [dict(max_holding_months=2), dict(max_holding_months=True),
                                      dict(position_sizing="unknown"), dict(entry_order="unknown"),
                                      dict(exit_signal_id="ABSENT")])
def test_invalid_extension_contracts_fail_closed(options):
    with pytest.raises(ValueError):
        _run(_prepared(last="2023-02-10"), **options)
