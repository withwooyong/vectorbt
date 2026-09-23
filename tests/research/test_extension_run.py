"""Experiment coverage and count semantics, including incomplete/blocked runs."""
import pandas as pd
import pytest

from research.krx_lab.extension_run import experiment_plan, trade_statistics, verify_evidence
from research.krx_lab.io import write_json


def test_plan_covers_all_horizons_and_preserves_independent_windows():
    plan = experiment_plan()
    assert len(plan) == 2598
    assert len({row["run_id"] for row in plan}) == len(plan)
    for group in ("basic", "wide"):
        rows = experiment_plan(group)
        assert len(rows) == 1008
        assert {r["max_holding_months"] for r in rows} == {1, 3, 6}
        assert sum(r["window"] == "continuous_2020_2023" for r in rows) == 168
        assert all(r["cost_bps"] is None and r["delay"] == 1 for r in rows)
    assert all(row["end"] < "2024-01-01" for row in plan)
    momentum = [r for r in plan if r["family"] == "momentum"]
    assert len(momentum) == 6
    assert all(r["max_holding_months"] is None and r["suppress_stop"] for r in momentum)


def test_filled_sides_are_not_round_trips_or_submitted_orders():
    result = dict(status="BLOCKED", fills=pd.DataFrame({"side": ["buy", "buy", "sell"]}),
                  trades=pd.DataFrame({"entry_date": ["2020-01-01"], "exit_date": ["2020-01-11"]}),
                  equity=pd.DataFrame({"positions_count": [1]}))
    stats = trade_statistics(result)
    assert stats == dict(buy_count=2, sell_count=1, completed_trades=None, holding_days_sum=None,
                         mean_holding_days=None, median_holding_days=None, open_positions=None,
                         count_scope="PARTIAL_BEFORE_BLOCK")
    result["status"] = "SUCCEEDED"
    assert trade_statistics(result)["count_scope"] == "FULL_WINDOW"


def test_empty_trade_counts_have_no_invented_holding_period():
    result = dict(status="SUCCEEDED", fills=pd.DataFrame(columns=["side"]),
                  trades=pd.DataFrame(columns=["entry_date", "exit_date"]),
                  equity=pd.DataFrame({"positions_count": [0]}))
    stats = trade_statistics(result)
    assert stats["buy_count"] == stats["sell_count"] == stats["completed_trades"] == 0
    assert stats["mean_holding_days"] is None


def test_failed_or_stale_evidence_never_opens_run(tmp_path):
    write_json(tmp_path / "evidence.json", {"status": "FAIL"})
    with pytest.raises(ValueError, match="STALE"):
        verify_evidence(tmp_path)


def test_duration_comparison_uses_same_successful_candidates():
    from scripts.research.report_extension_experiments import duration_pairs
    rows = []
    for entry in ("A", "B"):
        for month in (1, 3, 6):
            rows.append(dict(family="basic", entry_id=entry, exit_id="PCT_3_6", window="year_2020",
                max_holding_months=month, status="BLOCKED" if entry == "B" and month == 6 else "SUCCEEDED",
                metrics={"total_return": 100 if entry == "B" else month / 100, "max_drawdown": .1},
                statistics={"completed_trades": 2, "holding_days_sum": 20, "buy_count": 3, "sell_count": 2}))
    pairs = [r for r in duration_pairs(rows) if r["family"] == "basic" and r["window"] == "year_2020"]
    assert [r["matched"] for r in pairs] == [1, 1, 1]
    assert [r["mean_return"] for r in pairs] == [.01, .03, .06]
    assert [r["buys"] for r in pairs] == [3, 3, 3]
