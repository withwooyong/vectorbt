"""Human-readable Markdown and self-contained HTML reports."""

from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def _md(value: Any) -> str:
    return html.escape(_text(value), quote=True).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _run_rows(records: list[dict[str, Any]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for record in records:
        metrics = record.get("metrics") or {}
        rows.append(
            [
                _text(record.get("run_id")),
                _text(record.get("strategy_id")),
                _text(record.get("phase")),
                _text(record.get("year")),
                _text(record.get("cost_bps")),
                _text(record.get("delay")),
                _text(record.get("status")),
                _text(record.get("data_grade")),
                _text(metrics.get("total_return")),
                _text(metrics.get("max_drawdown")),
                _text(metrics.get("trade_count")),
                _text(record.get("reason")),
            ]
        )
    return rows


def _write_leaderboard(path: Path, candidates: list[dict[str, Any]]) -> None:
    fields = [
        "strategy_id", "eligible", "rank", "slot_count", "trade_count", "positive_years",
        "validation_growth_score", "cost_50_growth_score", "delay_2_growth_score",
        "median_cagr", "worst_max_drawdown", "average_annual_turnover",
        "positive_profit_concentration", "reason_codes", "reasons_ko",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for candidate in candidates:
            row = dict(candidate)
            row["reason_codes"] = ";".join(candidate.get("reason_codes") or [])
            row["reasons_ko"] = ";".join(candidate.get("reasons_ko") or [])
            writer.writerow(row)


def _cost_svg(records: list[dict[str, Any]]) -> str:
    """Build a small inline comparison using only succeeded finite run metrics."""
    groups: dict[int, list[float]] = {}
    used_grades: set[str] = set()
    for record in records:
        value = (record.get("metrics") or {}).get("total_return")
        try:
            value = float(value)
            cost = int(float(record["cost_bps"]))
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if record.get("status") == "SUCCEEDED" and math.isfinite(value):
            groups.setdefault(cost, []).append(value)
            used_grades.add(str(record.get("data_grade", "UNKNOWN")))
    averages = [(cost, sum(values) / len(values)) for cost, values in sorted(groups.items()) if values]
    if not averages:
        return "<p>성공한 실행의 유한 수익률이 없어 비용별 그래프를 만들지 않았습니다.</p>"
    scale = max(abs(value) for _, value in averages) or 1.0
    height = 38 * len(averages) + 35
    data_label = "합성 데이터 실행 비교" if "SYNTHETIC" in used_grades else "실행 기록 비교"
    elements = [
        f'<p><strong>데이터 구분: {html.escape(data_label)}</strong></p>',
        f'<svg viewBox="0 0 520 {height}" role="img" aria-label="비용별 성공 실행 평균 총수익률">',
        '<line x1="250" y1="8" x2="250" y2="100%" stroke="#667085" stroke-width="1"/>',
    ]
    for index, (cost, value) in enumerate(averages):
        y = 18 + index * 38
        width = abs(value) / scale * 210
        x = 250 if value >= 0 else 250 - width
        color = "#287a52" if value >= 0 else "#b5473c"
        elements.extend(
            [
                f'<text x="0" y="{y + 14}" font-size="13">{cost} bp</text>',
                f'<rect x="{x:.2f}" y="{y}" width="{width:.2f}" height="20" fill="{color}"/>',
                f'<text x="470" y="{y + 14}" text-anchor="end" font-size="13">{value:.2%}</text>',
            ]
        )
    elements.append("</svg>")
    return "".join(elements)


def write_report(out: Path, records: list[dict[str, Any]], selection: dict[str, Any]) -> None:
    """Write ``report.md`` and ``report.html`` beneath *out*."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    headers = ["run ID", "전략", "단계", "연도", "비용(bp)", "지연", "상태", "데이터 등급", "총수익률", "MDD", "거래 수", "상태 사유"]
    rows = _run_rows(records)
    selected = selection.get("selected_strategy_id")
    status = selection.get("status", "NO_SELECTION")
    candidates = selection.get("candidates") or []
    _write_leaderboard(out / "leaderboard.csv", candidates)
    grades = {str(record.get("data_grade", "UNKNOWN")) for record in records}
    market_warning = (
        "현재 기록에는 EXECUTION_ELIGIBLE이 아닌 데이터 등급이 포함되어 있으므로 실제 시장 성과로 해석할 수 없다."
        if grades - {"EXECUTION_ELIGIBLE"}
        else "이 결과는 실행 가능 데이터 게이트를 통과했더라도 과거 연구 결과이며 실전 성과를 보장하지 않는다."
    )

    md_lines = [
        "# 백테스트 후보 비교 보고서",
        "",
        "이 보고서는 모든 실행 상태를 함께 보여 주고, 사전 고정한 `selection_policy_v1`에 따라 모의 검토 후보를 선정하거나 보류한 이유를 기록한다. 선정 결과는 실전 주문 승인이 아니다.",
        "",
        "## 핵심 판단",
        "",
        f"- 선정 상태: **{_md(status)}**",
        f"- 선정 전략: **{_md(selected)}**",
        f"- 전체 후보 / 게이트 통과: {_md(selection.get('candidate_count', len(candidates)))} / {_md(selection.get('eligible_count', 0))}",
        f"- 데이터 주의: {_md(market_warning)}",
        "",
        "## 후보 게이트와 선정 차단 원인",
        "",
        "| 전략 | 통과 | 순위 | 거래 수 | 양수 연도 | 성장점수 | 최악 MDD | 집중도 | 차단 원인 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for candidate in candidates:
        reasons = "; ".join(candidate.get("reasons_ko") or []) or "없음"
        md_lines.append(
            "| " + " | ".join(
                _md(value)
                for value in [
                    candidate.get("strategy_id"),
                    "예" if candidate.get("eligible") else "아니오",
                    candidate.get("rank"),
                    candidate.get("trade_count"),
                    candidate.get("positive_years"),
                    candidate.get("validation_growth_score"),
                    candidate.get("worst_max_drawdown"),
                    candidate.get("positive_profit_concentration"),
                    reasons,
                ]
            ) + " |"
        )
    if not candidates:
        md_lines.append("| - | 아니오 | - | - | - | - | - | - | 검증 후보 없음 |")

    md_lines.extend(["", "## 전체 실행 비교", "", "| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]) 
    for row in rows:
        md_lines.append("| " + " | ".join(_md(value) for value in row) + " |")
    if not rows:
        md_lines.append("| " + " | ".join(["-"] * len(headers)) + " |")
    md_lines.extend(
        [
            "",
            "## 판정 범위와 한계",
            "",
            "검증 16슬롯의 완전성, 거래 수, 연도별 수익, 비용·지연 스트레스, 최대낙폭, 종목 집중도를 검사한다. 과거 검증 통과는 미래 수익을 보장하지 않으며, `EXECUTION_ELIGIBLE` 이외의 데이터는 선정할 수 없다. 비용별 수치 비교는 HTML의 성공 실행 그래프에서만 제공하며 성공하지 않은 실행을 0으로 바꾸지 않는다.",
            "",
        ]
    )
    (out / "report.md").write_text("\n".join(md_lines), encoding="utf-8")

    def td(value: Any) -> str:
        return f"<td>{html.escape(_text(value), quote=True)}</td>"

    candidate_html = []
    for candidate in candidates:
        reasons = "; ".join(candidate.get("reasons_ko") or []) or "없음"
        candidate_html.append(
            "<tr>" + "".join(td(value) for value in [candidate.get("strategy_id"), "예" if candidate.get("eligible") else "아니오", candidate.get("rank"), candidate.get("trade_count"), candidate.get("positive_years"), candidate.get("validation_growth_score"), candidate.get("worst_max_drawdown"), candidate.get("positive_profit_concentration"), reasons]) + "</tr>"
        )
    if not candidate_html:
        candidate_html.append("<tr><td colspan=\"9\">검증 후보 없음</td></tr>")
    run_html = ["<tr>" + "".join(td(value) for value in row) + "</tr>" for row in rows]
    if not run_html:
        run_html.append(f"<tr><td colspan=\"{len(headers)}\">실행 기록 없음</td></tr>")
    safe_status = html.escape(_text(status), quote=True)
    safe_selected = html.escape(_text(selected), quote=True)
    safe_warning = html.escape(market_warning, quote=True)
    cost_svg = _cost_svg(records)
    html_doc = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>백테스트 후보 비교 보고서</title><style>body{{font-family:system-ui,sans-serif;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#172033}}table{{border-collapse:collapse;width:100%;font-size:.9rem;margin:1rem 0 2rem}}th,td{{border:1px solid #ccd3dc;padding:.45rem;text-align:right}}th:first-child,td:first-child,th:nth-child(2),td:nth-child(2),th:last-child,td:last-child{{text-align:left}}th{{background:#eef2f6}}.summary{{padding:1rem;background:#f4f7fa;border-left:4px solid #315a8a}}code{{background:#eef2f6;padding:.1rem .25rem}}</style></head>
<body><h1>백테스트 후보 비교 보고서</h1><p>모든 실행 상태와 사전 고정 게이트의 판정을 기록한다. 선정 결과는 실전 주문 승인이 아니다.</p>
<div class="summary"><strong>선정 상태:</strong> {safe_status}<br><strong>선정 전략:</strong> {safe_selected}<br><strong>데이터 주의:</strong> {safe_warning}</div>
<h2>후보 게이트와 선정 차단 원인</h2><table><thead><tr>{''.join(f'<th>{html.escape(h)}</th>' for h in ['전략','통과','순위','거래 수','양수 연도','성장점수','최악 MDD','집중도','차단 원인'])}</tr></thead><tbody>{''.join(candidate_html)}</tbody></table>
<h2>비용별 성공 실행 평균 총수익률</h2>{cost_svg}<p>이 그래프는 실행 기록의 단순 비교이며 실제 시장 성과나 후보 선정 결과가 아니다.</p>
<h2>전체 실행 비교</h2><table><thead><tr>{''.join(f'<th>{html.escape(h)}</th>' for h in headers)}</tr></thead><tbody>{''.join(run_html)}</tbody></table>
<h2>판정 범위와 한계</h2><p>검증 16슬롯의 완전성, 거래 수, 연도별 수익, 비용·지연 스트레스, 최대낙폭, 종목 집중도를 검사한다. 과거 검증 통과는 미래 수익을 보장하지 않으며, <code>EXECUTION_ELIGIBLE</code> 이외의 데이터는 선정할 수 없다.</p>
<script type="application/json" id="selection-data">{html.escape(json.dumps(selection, ensure_ascii=False, allow_nan=False), quote=False)}</script></body></html>"""
    (out / "report.html").write_text(html_doc, encoding="utf-8")
