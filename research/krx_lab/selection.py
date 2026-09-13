"""Deterministic validation gates and candidate ranking."""

from __future__ import annotations

from collections import defaultdict
from math import prod
from statistics import mean, median
from typing import Any


_YEARS = (2020, 2021, 2022, 2023)
_EXPECTED_SLOTS = {(year, cost, 1) for year in _YEARS for cost in (10, 30, 50)} | {
    (year, 30, 2) for year in _YEARS
}

_REASON_KO = {
    "DATA_NOT_EXECUTION_ELIGIBLE": "EXECUTION_ELIGIBLE 데이터가 아닌 실행이 있습니다.",
    "VALIDATION_SLOTS_INCOMPLETE": "검증 16슬롯이 모두 유일하게 존재하지 않습니다.",
    "RUN_NOT_SUCCEEDED": "성공하지 않은 검증 실행이 있습니다.",
    "UNRESOLVED_ISSUES": "설명되지 않은 데이터·장부 문제가 남아 있습니다.",
    "INSUFFICIENT_TRADES": "기준비용·지연1의 완료 거래가 100건 미만입니다.",
    "POSITIVE_YEARS_BELOW_MINIMUM": "기준비용 수익이 양수인 연도가 3개 미만입니다.",
    "BASE_GROWTH_NON_POSITIVE": "기준비용 validation_growth_score가 양수가 아닙니다.",
    "COST_50_GROWTH_NON_POSITIVE": "50bp 스트레스 validation_growth_score가 양수가 아닙니다.",
    "DELAY_2_GROWTH_NON_POSITIVE": "지연2 스트레스 validation_growth_score가 양수가 아닙니다.",
    "MAX_DRAWDOWN_EXCEEDED": "기준비용 최악 최대낙폭이 20%를 초과합니다.",
    "PROFIT_CONCENTRATION_EXCEEDED": "기준비용 양의 거래손익 중 단일 종목 기여가 25%를 초과합니다.",
    "RANKING_METRICS_INCOMPLETE": "순위 산정에 필요한 CAGR 또는 회전율이 완전하지 않습니다.",
}


def _number(metrics: dict[str, Any], *names: str) -> float | None:
    for name in names:
        value = metrics.get(name)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = float(value)
            if value == value and abs(value) != float("inf"):
                return value
    return None


def _slot(record: dict[str, Any]) -> tuple[int, int, int] | None:
    try:
        values = [float(record[name]) for name in ("year", "cost_bps", "delay")]
        if not all(value.is_integer() for value in values):
            return None
        return tuple(int(value) for value in values)
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def _growth(rows: list[dict[str, Any]]) -> float | None:
    returns = [_number(row.get("metrics") or {}, "total_return") for row in rows]
    if len(returns) != 4 or any(value is None for value in returns):
        return None
    return float(prod(1.0 + value for value in returns if value is not None) - 1.0)


def _candidate(strategy_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    reasons: list[str] = []
    slots = [_slot(row) for row in rows]
    slot_set = {slot for slot in slots if slot is not None}
    if len(rows) != 16 or len(slot_set) != 16 or slot_set != _EXPECTED_SLOTS:
        reasons.append("VALIDATION_SLOTS_INCOMPLETE")
    if any(str(row.get("status", "")).upper() != "SUCCEEDED" for row in rows):
        reasons.append("RUN_NOT_SUCCEEDED")
    if any(row.get("data_grade") != "EXECUTION_ELIGIBLE" for row in rows):
        reasons.append("DATA_NOT_EXECUTION_ELIGIBLE")
    if any(
        (row.get("metrics") or {}).get("issues")
        or (_number(row.get("metrics") or {}, "issue_count") or 0) > 0
        for row in rows
    ):
        reasons.append("UNRESOLVED_ISSUES")

    base = [row for row in rows if _slot(row) in {(year, 30, 1) for year in _YEARS}]
    cost_50 = [row for row in rows if _slot(row) in {(year, 50, 1) for year in _YEARS}]
    delay_2 = [row for row in rows if _slot(row) in {(year, 30, 2) for year in _YEARS}]
    base.sort(key=lambda row: int(row.get("year", 0)))
    cost_50.sort(key=lambda row: int(row.get("year", 0)))
    delay_2.sort(key=lambda row: int(row.get("year", 0)))

    base_returns = [_number(row.get("metrics") or {}, "total_return") for row in base]
    trade_count = sum(int(_number(row.get("metrics") or {}, "trade_count", "trades") or 0) for row in base)
    positive_years = sum(value is not None and value > 0 for value in base_returns)
    base_growth = _growth(base)
    cost_50_growth = _growth(cost_50)
    delay_2_growth = _growth(delay_2)
    if trade_count < 100:
        reasons.append("INSUFFICIENT_TRADES")
    if positive_years < 3:
        reasons.append("POSITIVE_YEARS_BELOW_MINIMUM")
    if base_growth is None or base_growth <= 0:
        reasons.append("BASE_GROWTH_NON_POSITIVE")
    if cost_50_growth is None or cost_50_growth <= 0:
        reasons.append("COST_50_GROWTH_NON_POSITIVE")
    if delay_2_growth is None or delay_2_growth <= 0:
        reasons.append("DELAY_2_GROWTH_NON_POSITIVE")

    drawdowns = [_number(row.get("metrics") or {}, "max_drawdown", "mdd") for row in base]
    worst_drawdown = max((value for value in drawdowns if value is not None), default=None)
    if len(drawdowns) != 4 or any(value is None for value in drawdowns) or worst_drawdown is None or worst_drawdown > 0.20:
        reasons.append("MAX_DRAWDOWN_EXCEEDED")

    positive_by_code: defaultdict[str, float] = defaultdict(float)
    has_contribution_detail = len(base) == 4
    for row in base:
        contribution = (row.get("metrics") or {}).get("positive_pnl_by_code")
        if isinstance(contribution, dict):
            for code, value in contribution.items():
                if isinstance(value, (int, float)) and value > 0:
                    positive_by_code[str(code)] += float(value)
        else:
            has_contribution_detail = False
    if has_contribution_detail:
        positive_total = sum(positive_by_code.values())
        concentration = max(positive_by_code.values(), default=0.0) / positive_total if positive_total > 0 else None
    else:
        concentrations = [
            _number(row.get("metrics") or {}, "positive_profit_concentration", "profit_concentration") for row in base
        ]
        concentration = max((value for value in concentrations if value is not None), default=None)
    if concentration is None or concentration > 0.25:
        reasons.append("PROFIT_CONCENTRATION_EXCEEDED")

    cagrs = [_number(row.get("metrics") or {}, "cagr") for row in base]
    turnovers = [_number(row.get("metrics") or {}, "annual_turnover", "turnover") for row in base]
    median_cagr = median(cagrs) if len(cagrs) == 4 and all(value is not None for value in cagrs) else None
    average_turnover = mean(turnovers) if len(turnovers) == 4 and all(value is not None for value in turnovers) else None
    if median_cagr is None or average_turnover is None:
        reasons.append("RANKING_METRICS_INCOMPLETE")

    reasons = list(dict.fromkeys(reasons))
    return {
        "strategy_id": strategy_id,
        "eligible": not reasons,
        "reason_codes": reasons,
        "reasons_ko": [_REASON_KO[code] for code in reasons],
        "run_ids": [str(row.get("run_id", "")) for row in rows],
        "slot_count": len(rows),
        "trade_count": trade_count,
        "positive_years": positive_years,
        "validation_growth_score": base_growth,
        "cost_50_growth_score": cost_50_growth,
        "delay_2_growth_score": delay_2_growth,
        "worst_max_drawdown": worst_drawdown,
        "positive_profit_concentration": concentration,
        "median_cagr": median_cagr,
        "average_annual_turnover": average_turnover,
    }


def select_candidate(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Apply ``selection_policy_v1`` and return one frozen candidate or none."""
    grouped: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    ignored_run_ids: list[str] = []
    for record in records:
        if record.get("phase", "validation") != "validation":
            ignored_run_ids.append(str(record.get("run_id", "")))
            continue
        grouped[str(record.get("strategy_id", ""))].append(record)

    candidates = [_candidate(strategy_id, rows) for strategy_id, rows in grouped.items()]
    eligible = [candidate for candidate in candidates if candidate["eligible"]]
    eligible.sort(
        key=lambda candidate: (
            -float(candidate["median_cagr"]),
            float(candidate["worst_max_drawdown"]),
            float(candidate["average_annual_turnover"]),
            candidate["strategy_id"],
        )
    )
    rank_by_id = {candidate["strategy_id"]: rank for rank, candidate in enumerate(eligible, 1)}
    for candidate in candidates:
        candidate["rank"] = rank_by_id.get(candidate["strategy_id"])
    candidates.sort(key=lambda candidate: (candidate["rank"] is None, candidate["rank"] or 0, candidate["strategy_id"]))

    selected = eligible[0] if eligible else None
    return {
        "policy": "selection_policy_v1",
        "status": "FROZEN_CANDIDATE" if selected else "NO_SELECTION",
        "selected_strategy_id": selected["strategy_id"] if selected else None,
        "selected_run_ids": selected["run_ids"] if selected else [],
        "candidate_count": len(candidates),
        "eligible_count": len(eligible),
        "candidates": candidates,
        "blockers": [] if selected else ["NO_ELIGIBLE_CANDIDATE"],
        "ignored_run_ids": ignored_run_ids,
    }
