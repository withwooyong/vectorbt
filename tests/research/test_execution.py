import pandas as pd
import hashlib
import pytest

from research.krx_lab.execution import simulate


def test_simulation_hook_propagates_cooperative_stop_before_day_execution():
    from research.krx_lab.contracts import CooperativeStop, ExecutionHooks

    visited = []
    def checkpoint(stage, context):
        visited.append((stage, context["date"]))
        raise CooperativeStop("TEST_STOP")

    with pytest.raises(CooperativeStop, match="TEST_STOP"):
        simulate(_prices(_base_rows()), _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6",
                 start="2026-01-02", end="2026-01-06", hooks=ExecutionHooks(checkpoint=checkpoint))
    assert visited == [("simulation_day", "2026-01-02")]


def _prices(rows):
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def _signals(rows):
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame


def _base_rows():
    return [
        {"date": "2026-01-02", "code": "A", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1_000_000, "sector": "S1", "tick_size": 1, "eligible": True},
        {"date": "2026-01-05", "code": "A", "open": 100, "high": 108, "low": 99, "close": 105, "volume": 1_000_000, "sector": "S1", "tick_size": 1, "eligible": True},
        {"date": "2026-01-06", "code": "A", "open": 105, "high": 106, "low": 104, "close": 105, "volume": 1_000_000, "sector": "S1", "tick_size": 1, "eligible": True},
    ]


def _base_signals():
    return [{"date": "2026-01-02", "code": "A", "atr14": 4, "avg_volume20": 1_000_000, "entry": True}]


def test_causal_entry_and_target_with_shared_cash_outputs():
    result = simulate(_prices(_base_rows()), _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"])

    assert result["plans"].iloc[0]["entry_date"] == pd.Timestamp("2026-01-05")
    assert result["fills"]["side"].tolist() == ["buy", "sell"]
    assert result["fills"].iloc[0]["price"] == 100
    assert result["fills"].iloc[1]["price"] == 106  # target, not a future close
    assert result["trades"].iloc[0]["code"] == "A"
    assert set(result["equity"].columns) == {"date", "cash", "equity", "exposure", "positions_count"}


def test_same_bar_stop_wins_unless_optimistic():
    rows = _base_rows()
    rows[1].update({"high": 110, "low": 95})
    conservative = simulate(_prices(rows), _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"])
    optimistic = simulate(_prices(rows), _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"], optimistic=True)

    assert conservative["fills"].iloc[-1]["price"] == 97
    assert conservative["fills"].iloc[-1]["phase"] == "stop_intraday_ambiguous"
    assert optimistic["fills"].iloc[-1]["price"] == 106


def test_month_clamp_time_exit_and_stale_missing_row_issue():
    rows = [
        {"date": "2026-01-30", "code": "A", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1_000_000, "sector": "S1", "tick_size": 1, "eligible": True},
        {"date": "2026-02-02", "code": "A", "open": 100, "high": 101, "low": 99, "close": 100, "volume": 1_000_000, "sector": "S1", "tick_size": 1, "eligible": True},
        {"date": "2026-02-27", "code": "A", "open": 99, "high": 100, "low": 98, "close": 99, "volume": 1_000_000, "sector": "S1", "tick_size": 1, "eligible": True},
        {"date": "2026-03-02", "code": "A", "open": 99, "high": 100, "low": 98, "close": 99, "volume": 1_000_000, "sector": "S1", "tick_size": 1, "eligible": True},
    ]
    signals = [{"date": "2026-01-30", "code": "A", "atr14": 1, "avg_volume20": 1_000_000, "entry": True}]
    result = simulate(_prices(rows), _signals(signals), entry_id="entry", exit_id="PCT_5_10", start="2026-01-30", end="2026-03-02", calendar=["2026-01-30", "2026-02-02", "2026-02-27", "2026-03-02"])

    assert result["trades"].iloc[0]["exit_date"] == pd.Timestamp("2026-03-02")
    assert result["fills"].iloc[-1]["phase"] == "time_open"


def test_missing_optional_fields_and_calendar_are_explicit_issues():
    prices = _prices(_base_rows()).drop(columns=["sector", "tick_size", "eligible"])
    result = simulate(prices, _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-06")

    assert {"CALENDAR_UNVERIFIED", "MISSING_SECTOR", "MISSING_TICK_SIZE", "MISSING_ELIGIBLE"}.issubset(result["issues"])


def test_missing_holding_row_is_stale_without_forced_exit():
    rows = _base_rows()[:2]
    result = simulate(
        _prices(rows),
        _signals(_base_signals()),
        entry_id="entry",
        exit_id="PCT_5_10",
        start="2026-01-02",
        end="2026-01-06",
        calendar=["2026-01-02", "2026-01-05", "2026-01-06"],
    )

    assert "STALE_PRICE:2026-01-06:A" in result["issues"]
    stale_row = result["positions"].loc[result["positions"]["date"].eq(pd.Timestamp("2026-01-06"))].iloc[0]
    assert stale_row["stale"]


def test_shared_account_enforces_twenty_slot_limit():
    codes = [f"C{number:02d}" for number in range(21)]
    rows = []
    signal_rows = []
    for index, code in enumerate(codes):
        sector = f"S{index // 6}"
        for date in ("2026-01-02", "2026-01-05"):
            rows.append({"date": date, "code": code, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10_000_000, "sector": sector, "tick_size": 1, "eligible": True})
        signal_rows.append({"date": "2026-01-02", "code": code, "atr14": 4, "avg_volume20": 10_000_000, "entry": True})
    result = simulate(_prices(rows), _signals(signal_rows), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-05", calendar=["2026-01-02", "2026-01-05"])

    assert result["equity"].iloc[-1]["positions_count"] == 20
    assert "SLOT_LIMIT" in result["plans"]["reason"].tolist()


def test_open_entry_does_not_read_same_day_high_low_close_or_volume():
    rows = _base_rows()
    rows[1].update({"high": float("nan"), "low": float("nan"), "close": float("nan"), "volume": 0})
    result = simulate(_prices(rows), _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"])

    assert result["fills"].iloc[0]["side"] == "buy"
    assert result["fills"].iloc[0]["price"] == 100
    assert "STALE_PRICE:2026-01-05:A" in result["issues"]


def test_pre_start_signal_can_enter_on_first_evaluation_day():
    rows = _base_rows()[:2]
    result = simulate(_prices(rows), _signals(_base_signals()), entry_id="entry", exit_id="PCT_5_10", start="2026-01-05", end="2026-01-05", calendar=["2026-01-02", "2026-01-05"])

    assert result["plans"].iloc[0]["entry_date"] == pd.Timestamp("2026-01-05")
    assert result["fills"].iloc[0]["date"] == pd.Timestamp("2026-01-05")
    assert result["plans"].iloc[0]["decision_at"] == pd.Timestamp("2026-01-02")


def test_end_of_evaluation_does_not_force_early_month_exit_and_plan_is_replayable():
    rows = _base_rows()[:2]
    result = simulate(_prices(rows), _signals(_base_signals()), entry_id="entry", exit_id="PCT_5_10", start="2026-01-02", end="2026-01-05", calendar=["2026-01-02", "2026-01-05"])

    assert result["trades"].empty
    assert result["positions"].iloc[-1]["expiry"] == pd.Timestamp("2026-02-05")
    assert "EXPIRY_CALENDAR_UNAVAILABLE:2026-01-05:2026-02-05" in result["issues"]
    assert {"expiry_date", "decision_at", "data_cutoff", "fill_seq", "avg_volume20"}.issubset(result["plans"].columns)
    assert {"mark_price", "expiry", "overdue"}.issubset(result["positions"].columns)


def test_candidate_order_uses_fixed_hash_and_staged_policy_uses_ten_slots_below_threshold():
    codes = [f"C{number:02d}" for number in range(11)]
    rows, signal_rows = [], []
    for index, code in enumerate(codes):
        sector = f"S{index // 6}"
        for date in ("2026-01-02", "2026-01-05"):
            rows.append({"date": date, "code": code, "open": 100, "high": 101, "low": 99, "close": 100, "volume": 10_000_000, "sector": sector, "tick_size": 1, "eligible": True})
        signal_rows.append({"date": "2026-01-02", "code": code, "atr14": 4, "avg_volume20": 10_000_000, "entry": True})
    result = simulate(_prices(rows), _signals(signal_rows), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-05", calendar=["2026-01-02", "2026-01-05"], initial_cash=149_000_000, policy="staged10_15_20")

    expected_rejected = max(codes, key=lambda code: hashlib.sha256(f"lab-v1|20260913|2026-01-02|{code}".encode("utf-8")).hexdigest())
    rejected = result["plans"].loc[result["plans"]["reason"].eq("SLOT_LIMIT"), "code"].tolist()
    assert result["equity"].iloc[-1]["positions_count"] == 10
    assert rejected == [expected_rejected]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"cost_bps": -1}, "cost_bps"),
        ({"cost_bps": float("nan")}, "cost_bps"),
        ({"initial_cash": float("inf")}, "initial_cash"),
        ({"delay": 1.5}, "delay"),
        ({"exit_id": "UNKNOWN"}, "exit_id"),
    ],
)
def test_invalid_execution_inputs_fail_before_processing(kwargs, message):
    call = {"entry_id": "entry", "exit_id": "PCT_3_6", "start": "2026-01-02", "end": "2026-01-06", "calendar": ["2026-01-02", "2026-01-05", "2026-01-06"]}
    call.update(kwargs)
    with pytest.raises(ValueError, match=message):
        simulate(_prices(_base_rows()), _signals(_base_signals()), **call)


def test_phase_artifacts_exclude_future_signals_but_keep_terminal_no_future_plan():
    signal_rows = _base_signals() + [{"date": "2026-01-05", "code": "A", "atr14": 4, "avg_volume20": 1_000_000, "entry": True}]
    result = simulate(_prices(_base_rows()[:2]), _signals(signal_rows), entry_id="entry", exit_id="PCT_5_10", start="2026-01-02", end="2026-01-05", calendar=["2026-01-02", "2026-01-05"])

    assert result["signals"]["date"].tolist() == [pd.Timestamp("2026-01-02"), pd.Timestamp("2026-01-05")]
    assert result["plans"].iloc[-1]["reason"] == "NO_FUTURE_TRADING_DAY"
    assert result["fills"]["fill_seq"].tolist() == list(range(len(result["fills"])))
    assert result["plans"].iloc[0]["fill_seq"] == result["fills"].iloc[0]["fill_seq"]


def test_eligible_false_blocks_trading_but_keeps_valid_close_as_mark():
    rows = _base_rows()
    rows[2].update({"eligible": False, "close": 104})
    result = simulate(_prices(rows), _signals(_base_signals()), entry_id="entry", exit_id="PCT_5_10", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"])

    marked = result["positions"].loc[result["positions"]["date"].eq(pd.Timestamp("2026-01-06"))].iloc[0]
    assert marked["mark_price"] == 104
    assert not marked["stale"]
    assert "INELIGIBLE_MARK:2026-01-06:A" in result["issues"]


def test_gap_exit_prevents_same_day_reentry_and_higher_fee_is_not_better():
    rows = _base_rows()
    rows[2].update({"open": 90, "high": 92, "low": 89, "close": 90})
    signals = _base_signals() + [{"date": "2026-01-05", "code": "A", "atr14": 4, "avg_volume20": 1_000_000, "entry": True}]
    result = simulate(_prices(rows), _signals(signals), entry_id="entry", exit_id="PCT_5_10", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"])
    low_fee = simulate(_prices(_base_rows()), _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"], cost_bps=10)
    high_fee = simulate(_prices(_base_rows()), _signals(_base_signals()), entry_id="entry", exit_id="PCT_3_6", start="2026-01-02", end="2026-01-06", calendar=["2026-01-02", "2026-01-05", "2026-01-06"], cost_bps=50)

    assert result["fills"].iloc[-1]["phase"] == "stop_gap_open"
    assert "ALREADY_HELD_OR_EXITED" in result["plans"]["reason"].tolist()
    assert high_fee["equity"].iloc[-1]["equity"] <= low_fee["equity"].iloc[-1]["equity"]
