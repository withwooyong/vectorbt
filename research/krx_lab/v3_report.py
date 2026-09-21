"""Render bounded, descriptive reports for v3 batch output."""
from __future__ import annotations

import html
import json
from pathlib import Path

from .io import read_json


_PAIRS = {"PCT_3_6": "PCT_8_16", "PCT_5_10": "PCT_10_20", "ATR_1_5_3": "ATR_3_6", "ATR_2_4": "ATR_4_8"}


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _md(value):
    return html.escape(str("-" if value is None else value), quote=True).replace("|", "\\|")


def _pct(value):
    return "-" if value is None else f"{value:.2%}"


def _table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    lines.extend("| " + " | ".join(_md(item) for item in row) + " |" for row in rows)
    return lines if rows else lines + ["| " + " | ".join(["-"] * len(headers)) + " |"]


def _full_validation(rows):
    groups = {}
    for row in rows:
        if (row.get("phase") != "validation" or row.get("cost_bps") is not None or row.get("delay") != 1
                or row.get("cost_model") != "DATED_V3_RULES" or (row.get("ledger_check") or {}).get("status") != "PASS"):
            continue
        groups.setdefault((row.get("family"), row.get("entry_id"), row.get("exit_id")), []).append(row)
    output = []
    for key, values in groups.items():
        if len(values) != 4 or {item.get("year") for item in values} != {2020, 2021, 2022, 2023}:
            continue
        if any(item.get("status") != "SUCCEEDED" or not item.get("metrics") for item in values):
            continue
        metrics = [item["metrics"] for item in values if item.get("status") == "SUCCEEDED" and item.get("metrics")]
        returns, mdds = [_num(item.get("total_return")) for item in metrics], [_num(item.get("max_drawdown")) for item in metrics]
        if None in returns or None in mdds:
            continue
        output.append({"family": key[0], "entry_id": key[1], "exit_id": key[2],
                       "avg_return": sum(returns) / 4, "worst_mdd": max(mdds),
                       "trade_count": sum(int(item.get("trade_count") or 0) for item in metrics)})
    return output


def _family_top(rows, family):
    candidates = [item for item in _full_validation(rows) if item["family"] == family]
    return sorted(candidates, key=lambda item: item["avg_return"], reverse=True)[:10]


def _sensitivity(rows):
    groups = {}
    for row in rows:
        if row.get("cost_model") != "FLAT_BPS_STRESS_ONLY" or row.get("phase") != "validation" or row.get("status") != "SUCCEEDED":
            continue
        value = _num((row.get("metrics") or {}).get("total_return"))
        if value is not None:
            groups.setdefault((row.get("cost_bps"), row.get("delay")), []).append(value)
    return [[cost, delay, len(values), _pct(sum(values) / len(values))] for (cost, delay), values in sorted(groups.items())]


def _dated_cost_totals(rows):
    values = [row.get("metrics") or {} for row in rows if row.get("status") == "SUCCEEDED"
              and row.get("cost_model") == "DATED_V3_RULES" and (row.get("ledger_check") or {}).get("status") == "PASS"]
    return sum(_num(item.get("total_fees")) or 0.0 for item in values), sum(_num(item.get("total_taxes")) or 0.0 for item in values)


def _paired(rows):
    complete = {(item["family"], item["entry_id"], item["exit_id"]): item for item in _full_validation(rows)}
    output = []
    for entry in sorted({item["entry_id"] for item in _full_validation(rows)}):
        for basic_exit, wide_exit in _PAIRS.items():
            basic, wide = complete.get(("basic", entry, basic_exit)), complete.get(("wide", entry, wide_exit))
            if basic and wide:
                output.append([entry, basic_exit, wide_exit, _pct(basic["avg_return"]), _pct(wide["avg_return"]),
                               _pct(wide["avg_return"] - basic["avg_return"])])
    return output


def _html_table(headers, rows):
    head = "".join(f"<th>{html.escape(str(item), quote=True)}</th>" for item in headers)
    if not rows:
        body = f'<tr><td colspan="{len(headers)}">기록 없음</td></tr>'
    else:
        body = "".join("<tr>" + "".join(f"<td>{html.escape(str('-' if item is None else item), quote=True)}</td>" for item in row) + "</tr>" for row in rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def generate_report(batch_dir, out_dir):
    """Create non-overwriting Korean Markdown and standalone HTML from ``summary.json``.

    A result is eligible for a descriptive annual comparison only if all four
    independent validation years succeeded under dated v3 costs and delay one.
    This deliberately does not rank partial records or select a strategy.
    """
    batch, out = Path(batch_dir), Path(out_dir)
    if out.exists():
        raise FileExistsError(out)
    summary = read_json(batch / "summary.json")
    rows = list(summary.get("results") or [])
    out.mkdir(parents=True, exist_ok=False)
    planned, attempted = int(summary.get("planned_runs", 2464)), len(rows)
    succeeded = sum(row.get("status") == "SUCCEEDED" for row in rows)
    blocked = sum(row.get("status") == "BLOCKED" for row in rows)
    no_trade = sum(row.get("status") == "SUCCEEDED" and int((row.get("metrics") or {}).get("trade_count") or 0) == 0 for row in rows)
    smoke = read_json(batch / "smoke-oracle.json") if (batch / "smoke-oracle.json").is_file() else {}
    cohort = summary.get("cohort") or {}
    smoke_passed = smoke.get("status") == "PASS" and (batch / "execution-admission.json").is_file()
    pair_rows, basic_top, wide_top = (_paired(rows), _family_top(rows, "basic"), _family_top(rows, "wide")) if smoke_passed else ([], [], [])
    sensitivity = _sensitivity(rows) if smoke_passed else []
    dated_fees, dated_taxes = _dated_cost_totals(rows) if smoke_passed else (0.0, 0.0)
    exclusions = cohort.get("exclusions") or []
    (out / "excluded-symbols.json").write_text(json.dumps(exclusions, ensure_ascii=False, indent=2), encoding="utf-8")
    limits = "이 결과는 확인 가능한 종목만 모은 과거 가격 실험이며 배당금은 넣지 않았다. 제외된 종목 때문에 전체 시장 성과와 다를 수 있고, 전략 선택이나 실제 매매 허가가 아니다."
    md = ["# v3 56개 전략 실행 보고서", "", f"이 보고서는 기본 청산과 넓은 청산을 따로 비교한다. {limits}",
          "", "## 핵심 판단", "", f"- 실행 상태: **{_md(summary.get('status'))}**; 시도/계획 **{attempted}/{planned}** (기준 계획: flat stress 1,904 + 날짜별 실제비용 control 560 = 2,464, smoke 1개 별도).",
          f"- 성공/차단/무거래: **{succeeded}/{blocked}/{no_trade}**; 작은 사전 점검: **{_md(smoke.get('status', '없음'))}**.",
          "- 검증 연도는 2020~2023의 독립적인 1억 원 창이다. 아래 평균은 하나의 연속 4년 백테스트가 아니다.",
          "- 일부 또는 차단된 실행은 순위와 섞지 않았다. 상위 10개는 결과를 설명하기 위한 표이며 선택 결과가 아니다.", "", "## 범위·입력·미해결", "",
          f"- 확인 가능한 종목 묶음: {_md(cohort.get('result_label'))}; 포함 종목 수: {_md(len(cohort.get('instrument_ids') or []))}; 제외: {_md(len(exclusions))} ([제외 종목 상세](excluded-symbols.json)).",
          f"- 입력·실행 확인 파일: 준비 입력 hash `{_md(summary.get('prepared_manifest_hash'))}`; 실행 확인은 batch 폴더의 `execution-admission.json`을 참조.",
          f"- 미해결 제한: {_md('; '.join(summary.get('limitations') or cohort.get('limitations') or ['기록 없음']))}.",
          f"- 날짜별 비용 가정: {_md('; '.join(str(x) for x in (summary.get('rule_assumptions') or ['매수·매도 수수료와 매도세는 입력 규칙의 가정값'])))}.", "", "## 기본·넓은 청산 대응 비교", "",
          "동일 진입, 날짜별 v3 비용, delay=1, 네 검증 연도가 모두 성공한 경우만 비교한다. 작은 사전 점검이 통과하지 않으면 성과 표를 만들지 않는다.", ""]
    if not rows:
        md.extend(["실행 기록이 없어 비교·설명표를 만들지 않았습니다.", ""])
    md += _table(["진입", "기본", "넓은", "기본 평균", "넓은 평균", "차이"], pair_rows)
    for family, top in (("basic", basic_top), ("wide", wide_top)):
        md += ["", f"## {family} 상위 10개 설명표", "", "완전한 네 독립 연도만 표시하며 선정 순위가 아니다.", ""]
        md += _table(["진입", "청산", "평균 연도 수익", "최악 MDD", "4년 거래 수"],
                     [[x["entry_id"], x["exit_id"], _pct(x["avg_return"]), _pct(x["worst_mdd"]), x["trade_count"]] for x in top])
    md += ["", "## 비용·지연 점검", "", "아래는 고정 비용·지연을 바꾼 별도 점검의 성공 실행 평균이다. 성공한 실행 집합이 조건마다 다를 수 있어, 비용의 짝지은 효과나 전략 순위로 해석하지 않는다. 날짜별 비용 결과와도 섞지 않는다.", ""]
    md += _table(["고정 비용(bp)", "지연(일)", "성공 실행", "평균 수익"], sensitivity)
    md += ["", f"날짜별 비용 실행의 검증된 수수료/세금 합계는 각각 **{dated_fees:,.0f}원 / {dated_taxes:,.0f}원**이다. 같은 기간·전략을 여러 번 실행한 합계이므로 하나의 계좌 비용으로 해석하지 않는다."]
    reason_counts = {}
    for row in rows:
        if row.get("status") != "SUCCEEDED":
            reasons = row.get("issues") or [row.get("status") or "UNKNOWN"]
            for reason in reasons:
                reason_counts[str(reason)] = reason_counts.get(str(reason), 0) + 1
    failures = [[reason, count] for reason, count in sorted(reason_counts.items(), key=lambda item: (-item[1], item[0]))]
    md += ["", "## 차단·실패 요약", "", "개별 실행 목록을 본문에 모두 넣지 않았다. 원본 실행별 사유는 batch의 `runs/<run-id>/result.json`과 `runs/<run-id>/artifacts.json`에서 확인한다.", ""] + _table(["사유", "건수"], failures)
    (out / "report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    pair_html = _html_table(["진입", "기본", "넓은", "기본 평균", "넓은 평균", "차이"], pair_rows)
    top_html = "".join(f"<h2>{html.escape(family)} 상위 10개 설명표</h2><p>완전한 네 독립 연도만 표시하며 선택 순위가 아닙니다.</p>" + _html_table(["진입", "청산", "평균 연도 수익", "최악 MDD", "4년 거래 수"], [[x["entry_id"], x["exit_id"], _pct(x["avg_return"]), _pct(x["worst_mdd"]), x["trade_count"]] for x in values]) for family, values in (("기본", basic_top), ("넓은 청산", wide_top)))
    html_doc = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>v3 실행 보고서</title><style>body{{font-family:system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#182230}}table{{border-collapse:collapse;width:100%;margin:1rem 0 2rem}}th,td{{border:1px solid #ccd3dc;padding:.45rem;text-align:left}}th{{background:#eef2f6}}.notice{{background:#fff4e5;padding:1rem;border-left:4px solid #b5473c}}</style></head><body><h1>v3 56개 전략 실행 보고서</h1><p>{html.escape(limits)}</p><div class="notice">실행 상태: {html.escape(str(summary.get("status")), quote=True)} · 성공/차단/무거래: {succeeded}/{blocked}/{no_trade} · 작은 사전 점검과 실행 확인 파일: {"통과" if smoke_passed else "미통과 또는 없음"}</div><h2>입력 범위와 한계</h2><p>포함 종목 {len(cohort.get("instrument_ids") or [])}개, 제외 {len(exclusions)}개. <a href="excluded-symbols.json">제외 종목 상세</a>을 확인할 수 있습니다. 입력 hash: <code>{html.escape(str(summary.get("prepared_manifest_hash")), quote=True)}</code>.</p><p>제한: {html.escape('; '.join(summary.get("limitations") or cohort.get("limitations") or ['기록 없음']), quote=True)}</p><p>날짜별 비용 가정: {html.escape('; '.join(str(x) for x in (summary.get("rule_assumptions") or ['매수·매도 수수료와 매도세는 입력 규칙의 가정값'])), quote=True)}</p><h2>기본·넓은 청산 대응 비교</h2><p>날짜별 비용과 하루 지연 조건에서 2020~2023 네 해가 모두 성공한 경우만 비교합니다. 네 해는 각각 1억 원으로 독립 실행했으므로 연속 4년 성과가 아닙니다.</p>{pair_html}{top_html}<h2>비용·지연 점검</h2><p>고정 비용·지연을 바꾼 별도 점검입니다. 성공한 실행 집합이 조건마다 다를 수 있어 비용의 짝지은 효과나 전략 순위가 아닙니다. 날짜별 비용 실행의 수수료/세금 합계는 {dated_fees:,.0f}원 / {dated_taxes:,.0f}원이며, 반복 실행 합계이므로 하나의 계좌 비용이 아닙니다.</p>{_html_table(["고정 비용(bp)", "지연(일)", "성공 실행", "평균 수익"], sensitivity)}<h2>차단·실패 요약</h2><p>원본 실행별 사유는 batch의 <code>runs/&lt;run-id&gt;/result.json</code>과 <code>runs/&lt;run-id&gt;/artifacts.json</code>에서 확인합니다.</p>{_html_table(["사유", "건수"], failures)}</body></html>'''
    (out / "report.html").write_text(html_doc, encoding="utf-8")
    return {"markdown": str(out / "report.md"), "html": str(out / "report.html"), "attempted": attempted,
            "succeeded": succeeded, "blocked": blocked, "no_trade": no_trade}
