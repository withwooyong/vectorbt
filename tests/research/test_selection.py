from __future__ import annotations

import json

import pandas as pd
import pytest

from research.krx_lab.metrics import calculate_metrics
from research.krx_lab.report import write_report
from research.krx_lab.selection import select_candidate


def _records(strategy_id: str, *, cagr: float = 0.10, turnover: float = 2.0, grade: str = "EXECUTION_ELIGIBLE"):
    records = []
    for year in range(2020, 2024):
        for cost, delay, total_return in [(10, 1, 0.09), (30, 1, 0.08), (50, 1, 0.04), (30, 2, 0.03)]:
            records.append(
                {
                    "run_id": f"{strategy_id}-{year}-{cost}-{delay}",
                    "strategy_id": strategy_id,
                    "phase": "validation",
                    "year": year,
                    "cost_bps": cost,
                    "delay": delay,
                    "status": "SUCCEEDED",
                    "data_grade": grade,
                    "metrics": {
                        "total_return": total_return,
                        "cagr": cagr,
                        "max_drawdown": 0.12,
                        "annual_turnover": turnover,
                        "trade_count": 30,
                        "positive_pnl_by_code": {"005930": 20.0, "000660": 20.0, "035420": 20.0, "035720": 20.0, "051910": 20.0},
                        "issue_count": 0,
                        "issues": [],
                    },
                }
            )
    return records


def test_safe_candidate_is_selected_and_json_finite():
    result = select_candidate(_records("safe"))
    assert result["status"] == "FROZEN_CANDIDATE"
    assert result["selected_strategy_id"] == "safe"
    assert result["candidates"][0]["slot_count"] == 16
    json.dumps(result, allow_nan=False)


def test_ranking_ties_end_with_strategy_id():
    result = select_candidate(_records("zeta") + _records("alpha"))
    assert result["selected_strategy_id"] == "alpha"
    assert [row["strategy_id"] for row in result["candidates"][:2]] == ["alpha", "zeta"]


def test_failed_gate_returns_no_selection():
    records = _records("risky")
    for record in records:
        if record["cost_bps"] == 30 and record["delay"] == 1:
            record["metrics"]["max_drawdown"] = 0.21
    result = select_candidate(records)
    assert result["status"] == "NO_SELECTION"
    assert "MAX_DRAWDOWN_EXCEEDED" in result["candidates"][0]["reason_codes"]


def test_fractional_cost_does_not_fill_a_required_slot():
    records = _records("bad-slot")
    records[0]["cost_bps"] = 10.5
    result = select_candidate(records)
    assert result["status"] == "NO_SELECTION"
    assert "VALIDATION_SLOTS_INCOMPLETE" in result["candidates"][0]["reason_codes"]


def test_partial_positive_contribution_detail_is_not_accepted():
    records = _records("partial")
    base = [record for record in records if record["cost_bps"] == 30 and record["delay"] == 1]
    del base[0]["metrics"]["positive_pnl_by_code"]
    result = select_candidate(records)
    assert result["status"] == "NO_SELECTION"
    assert "PROFIT_CONCENTRATION_EXCEEDED" in result["candidates"][0]["reason_codes"]


def test_data_profile_blocks_otherwise_safe_candidate(tmp_path):
    records = _records("adjusted", grade="EXPLORATORY_ADJUSTED")
    result = select_candidate(records)
    assert result["selected_strategy_id"] is None
    assert "DATA_NOT_EXECUTION_ELIGIBLE" in result["candidates"][0]["reason_codes"]

    records[0]["run_id"] = "<script>alert(1)</script>"
    write_report(tmp_path, records, result)
    report_html = (tmp_path / "report.html").read_text(encoding="utf-8")
    leaderboard = (tmp_path / "leaderboard.csv").read_text(encoding="utf-8-sig")
    assert "<script>alert(1)</script>" not in report_html
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in report_html
    assert "EXECUTION_ELIGIBLE" in report_html
    assert "<svg" in report_html
    assert "strategy_id,eligible,rank" in leaderboard
    assert "adjusted,False" in leaderboard


def test_calculate_metrics_emits_finite_json_and_combined_concentration():
    result = {
        "equity": pd.DataFrame(
            {
                "date": pd.to_datetime(["2023-01-02", "2023-01-31", "2023-02-28"]),
                "cash": [50.0, 55.0, 60.0],
                "equity": [100.0, 110.0, 90.0],
                "exposure": [0.5, 0.5, float("inf")],
                "positions_count": [1, 2, 1],
            }
        ),
        "trades": pd.DataFrame({"code": ["A", "B", "A"], "pnl": [30.0, 20.0, -10.0]}),
        "fills": pd.DataFrame({"size": [1, -1], "price": [10.0, 12.0], "fees": [0.1, 0.2]}),
        "issues": [],
    }
    metrics = calculate_metrics(result, initial_cash=100.0)
    assert metrics["trade_count"] == 3
    assert metrics["positive_profit_concentration"] == 0.6
    assert metrics["max_drawdown"] == 1 - 90 / 110
    json.dumps(metrics, allow_nan=False)


def test_initial_cash_anchors_first_day_drawdown_and_invalid_ledger_is_not_dropped():
    result = {
        "equity": pd.DataFrame(
            {"date": pd.to_datetime(["2023-01-02"]), "cash": [90.0], "equity": [90.0], "exposure": [0.0], "positions_count": [0]}
        )
    }
    metrics = calculate_metrics(result, initial_cash=100.0)
    assert metrics["max_drawdown"] == pytest.approx(0.1)
    assert metrics["total_return"] == pytest.approx(-0.1)

    result["equity"].loc[0, "equity"] = float("nan")
    with pytest.raises(ValueError, match="INVALID_EQUITY_LEDGER"):
        calculate_metrics(result, initial_cash=100.0)
