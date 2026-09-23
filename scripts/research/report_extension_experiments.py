"""Verify saved ledgers and publish duration/new-hypothesis tables with fill counts."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path
import time

import pandas as pd

from research.krx_lab.extension_run import experiment_plan, trade_statistics
from research.krx_lab.io import canonical_hash, digest, read_json, write_json
from research.krx_lab.metrics import calculate_metrics
from research.krx_lab.v3_execution import audit_execution_ledger
from research.krx_lab.v3_run import reconcile_result


def close(a, b):
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a)), abs(float(b)))


def verify_batch(batch, calendar):
    batch = Path(batch)
    summary, plan = read_json(batch / "summary.json"), read_json(batch / "plan.json")
    if (summary["status"] != "COMPLETE" or plan["plan_hash"] != canonical_hash(plan["runs"])
            or plan["runs"] != experiment_plan(summary["group"])):
        raise ValueError("INCOMPLETE_OR_CHANGED_PLAN")
    receipt = read_json(batch / "execution-admission.json")
    receipt_body = {k: v for k, v in receipt.items() if k != "receipt_hash"}
    if (receipt.get("receipt_hash") != canonical_hash(receipt_body)
            or receipt.get("decision") != "EXECUTION_ADMITTED"
            or receipt.get("bindings", {}).get("code_hash") != summary["code_hash"]
            or receipt["bindings"]["strategy_hash"] != canonical_hash(
                {"plan": canonical_hash(plan["runs"]), "signals": summary["signal_manifest_hash"]})):
        raise ValueError("EXECUTION_RECEIPT_CHANGED")
    rows = summary["results"]
    if len(rows) != len(plan["runs"]) or len({x["run_id"] for x in rows}) != len(rows):
        raise ValueError("RUN_COUNT_MISMATCH")
    specs = {x["run_id"]: x for x in plan["runs"]}
    for row_index, row in enumerate(rows, start=1):
        spec = specs[row["run_id"]]
        if any(row.get(k) != v for k, v in spec.items()):
            raise ValueError("RUN_SPEC_CHANGED")
        root = batch / "runs" / row["run_id"]
        if row != read_json(root / "result.json"):
            raise ValueError("RESULT_SUMMARY_MISMATCH")
        if row["status"] == "BLOCKED" and "metrics" in row:
            raise ValueError("BLOCKED_HAS_PERFORMANCE")
        frames = {}
        for name, expected in row["files"].items():
            path = root / name
            if path.resolve().parent != root.resolve() or digest(path) != expected:
                raise ValueError("SAVED_LEDGER_CHANGED")
            frames[Path(name).stem] = pd.read_parquet(path)
        if not frames:
            if row["status"] != "BLOCKED" or row["issues"] != ["OFFICIAL_MARKET_INDEX_NOT_ADMITTED"]:
                raise ValueError("MISSING_LEDGER")
            continue
        result = dict(status=row["status"], issues=row["issues"], performance_valid=row["status"] == "SUCCEEDED",
                      initial_cash=100_000_000, **frames)
        if trade_statistics(result) != row["statistics"]:
            raise ValueError("TRADE_COUNTS_CHANGED")
        if row["status"] == "SUCCEEDED":
            audit_execution_ledger(result)
            days = calendar[(calendar >= pd.Timestamp(row["start"])) & (calendar <= pd.Timestamp(row["end"]))]
            reconcile_result(result, expected_dates=days)
            metrics = calculate_metrics(result)
            for name in ("total_return", "max_drawdown", "trade_count", "total_fees"):
                if not close(metrics.get(name), row["metrics"].get(name)):
                    raise ValueError(f"METRICS_CHANGED:{name}")
            if not close(float(frames["fills"].tax.sum()), row["metrics"]["total_taxes"]):
                raise ValueError("TAXES_CHANGED")
        if row_index % 100 == 0:
            print(f"VERIFY {summary['group']} {row_index}/{len(rows)}", flush=True)
    print(f"VERIFIED {summary['group']} {len(rows)}/{len(rows)}", flush=True)
    return summary


def wait_and_verify_batch(batch, calendar):
    """Allow finished independent batches to be verified while a sibling still runs."""
    batch = Path(batch)
    while True:
        if (batch / "failure.json").exists():
            raise ValueError(f"BATCH_FAILED:{batch}")
        status = read_json(batch / "summary.json")["status"]
        if status == "COMPLETE":
            return verify_batch(batch, calendar)
        if status != "RUNNING":
            raise ValueError(f"BATCH_NOT_COMPLETING:{batch}:{status}")
        time.sleep(10)


def legacy_parity(rows, legacy):
    source = read_json(Path(legacy) / "summary.json")
    old = {(r["family"], r["entry_id"], r["exit_id"], r["start"], r["end"]): r
           for r in source["results"] if r["cost_bps"] is None and r["delay"] == 1}
    matched = 0
    for row in rows:
        if row["family"] not in ("basic", "wide") or row["max_holding_months"] != 1:
            continue
        if row["window"] == "continuous_2020_2023":
            continue
        key = tuple(row[k] for k in ("family", "entry_id", "exit_id", "start", "end"))
        prior = old[key]
        if row["status"] != prior["status"]:
            raise ValueError("ONE_MONTH_STATUS_DRIFT")
        if row["status"] == "SUCCEEDED":
            for name in ("total_return", "max_drawdown", "trade_count", "total_fees", "total_taxes"):
                if not close(row["metrics"].get(name), prior["metrics"].get(name)):
                    raise ValueError(f"ONE_MONTH_METRIC_DRIFT:{key}:{name}")
            # Counts are checked from the original saved ledger, not inferred from trade_count.
            original = Path(legacy) / "runs" / prior["run_id"] / "fills.parquet"
            if digest(original) != prior["files"]["fills.parquet"]:
                raise ValueError("LEGACY_FILLS_CHANGED")
            fills = pd.read_parquet(original)
            if (int(fills.side.eq("buy").sum()) != row["statistics"]["buy_count"]
                    or int(fills.side.eq("sell").sum()) != row["statistics"]["sell_count"]):
                raise ValueError("ONE_MONTH_FILL_COUNT_DRIFT")
        matched += 1
    if matched != 560:
        raise ValueError(f"LEGACY_PARITY_COVERAGE:{matched}")
    return dict(status="PASS", matched=matched, legacy_summary_hash=digest(Path(legacy) / "summary.json"))


def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                     + ["| " + " | ".join("—" if v is None else str(v).replace("|", "/") for v in row)
                        + " |" for row in rows])


def pct(v):
    return "—" if v is None else f"{v:.2%}"


def exit_label(family, exit_id):
    if family == "momentum":
        return "월간 탈락(고정 손절·익절 없음)"
    if family == "trend_exit":
        stops = {"PCT_3_6": "3%", "PCT_5_10": "5%", "PCT_8_16": "8%", "PCT_10_20": "10%",
                 "ATR_1_5_3": "1.5 ATR", "ATR_2_4": "2 ATR", "ATR_3_6": "3 ATR", "ATR_4_8": "4 ATR"}
        return f"손절 {stops[exit_id]} + LOW20(고정 익절 없음)"
    return exit_id


def duration_pairs(rows):
    groups = {}
    for row in rows:
        if row["family"] not in ("basic", "wide"):
            continue
        groups.setdefault((row["family"], row["entry_id"], row["exit_id"], row["window"]), {})[
            row["max_holding_months"]] = row
    paired = []
    for window in [*(f"year_{y}" for y in range(2020, 2024)), "continuous_2020_2023"]:
        for family in ("basic", "wide"):
            complete = [v for k, v in groups.items() if k[0] == family and k[3] == window
                        and set(v) == {1, 3, 6} and all(r["status"] == "SUCCEEDED" for r in v.values())]
            for months in (1, 3, 6):
                selected = [v[months] for v in complete]
                n = len(selected)
                completed = sum(r["statistics"]["completed_trades"] for r in selected)
                days = sum(r["statistics"]["holding_days_sum"] for r in selected)
                paired.append(dict(family=family, window=window, months=months, matched=n,
                    mean_return=sum(r["metrics"]["total_return"] for r in selected) / n if n else None,
                    mean_mdd=sum(r["metrics"]["max_drawdown"] for r in selected) / n if n else None,
                    buys=sum(r["statistics"]["buy_count"] for r in selected),
                    sells=sum(r["statistics"]["sell_count"] for r in selected),
                    mean_holding=days / completed if completed else None))
    return paired


def hypothesis_pairs(rows):
    controls = {(r["entry_id"], r["exit_id"], r["max_holding_months"], r["window"]): r for r in rows
                if r["family"] in ("basic", "wide") and r["status"] == "SUCCEEDED"}
    groups = {}
    for row in rows:
        if row["family"] not in ("trend_exit", "market_filter") or row["status"] != "SUCCEEDED":
            continue
        key = (row["entry_id"].removesuffix("_MARKET200"), row["exit_id"], row["max_holding_months"], row["window"])
        if key in controls:
            groups.setdefault((row["family"], row["max_holding_months"], row["window"]), []).append((controls[key], row))
    output = []
    for (family, months, window), pairs in sorted(groups.items()):
        item = dict(family=family, months=months, window=window, matched=len(pairs))
        for side, column in (("control", 0), ("treatment", 1)):
            selected = [p[column] for p in pairs]
            n = len(selected)
            for metric in ("total_return", "max_drawdown", "average_exposure_fraction"):
                item[f"{side}_{metric}"] = sum(r["metrics"][metric] for r in selected) / n
            for count in ("buy_count", "sell_count", "completed_trades", "holding_days_sum"):
                item[f"{side}_{count}"] = sum(r["statistics"][count] for r in selected)
            count = item[f"{side}_completed_trades"]
            item[f"{side}_mean_holding_days"] = item[f"{side}_holding_days_sum"] / count if count else None
        output.append(item)
    return output


def annual_strategy_totals(rows):
    """Aggregate four independent annual accounts only when all four are verified."""
    groups = {}
    years = {f"year_{year}" for year in range(2020, 2024)}
    for row in rows:
        if row["window"] in years:
            key = (row["family"], row["entry_id"], row["exit_id"], row["max_holding_months"])
            groups.setdefault(key, []).append(row)
    output = []
    for key, values in sorted(groups.items()):
        verified = [r for r in values if r["status"] == "SUCCEEDED"]
        full = len(values) == 4 and len(verified) == 4 and {r["window"] for r in values} == years
        item = dict(family=key[0], entry=key[1], exit=key[2], months=key[3], successful_years=len(verified),
                    status="COMPLETE_4_YEARS" if full else "INCOMPLETE", mean_annual_return=None,
                    worst_annual_mdd=None, buy_count=None, sell_count=None, completed_trades=None,
                    mean_holding_days=None, year_end_open_positions_sum=None)
        item["exit_rule"] = exit_label(key[0], key[2])
        if full:
            item["mean_annual_return"] = sum(r["metrics"]["total_return"] for r in values) / 4
            item["worst_annual_mdd"] = max(r["metrics"]["max_drawdown"] for r in values)
            for count in ("buy_count", "sell_count", "completed_trades"):
                item[count] = sum(r["statistics"][count] for r in values)
            days = sum(r["statistics"]["holding_days_sum"] for r in values)
            item["mean_holding_days"] = days / item["completed_trades"] if item["completed_trades"] else None
            item["year_end_open_positions_sum"] = sum(r["statistics"]["open_positions"] for r in values)
        output.append(item)
    return output


def complete_duration_annual(annual):
    groups = {}
    for row in annual:
        if row["family"] in ("basic", "wide"):
            groups.setdefault((row["family"], row["entry"], row["exit"]), {})[row["months"]] = row
    output = []
    for family in ("basic", "wide"):
        complete = [v for k, v in groups.items() if k[0] == family and set(v) == {1, 3, 6}
                    and all(r["status"] == "COMPLETE_4_YEARS" for r in v.values())]
        for months in (1, 3, 6):
            selected = [v[months] for v in complete]
            n = len(selected)
            closed = sum(r["completed_trades"] for r in selected)
            days = sum((r["mean_holding_days"] or 0) * r["completed_trades"] for r in selected)
            output.append(dict(family=family, months=months, matched_strategies=n,
                mean_annual_return=sum(r["mean_annual_return"] for r in selected) / n if n else None,
                mean_worst_annual_mdd=sum(r["worst_annual_mdd"] for r in selected) / n if n else None,
                buy_count=sum(r["buy_count"] for r in selected), sell_count=sum(r["sell_count"] for r in selected),
                mean_holding_days=days / closed if closed else None))
    return output


def build_report(batches, prepared, legacy, out, *, wait=False, render_verified=False):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=render_verified)
    prepared_manifest = read_json(Path(prepared) / "manifest.json")
    if digest(Path(prepared) / "calendar.parquet") != prepared_manifest["files"]["calendar"]["sha256"]:
        raise ValueError("REPORT_CALENDAR_CHANGED")
    calendar = pd.to_datetime(pd.read_parquet(Path(prepared) / "calendar.parquet").date)
    # Independent batches have disjoint ledgers; verify each in its own process.
    if render_verified:
        verification = read_json(out / "verification.json")
        current = {str(p): digest(Path(p) / "summary.json") for p in batches}
        if verification.get("status") != "PASS" or verification.get("summaries") != current:
            raise ValueError("VERIFIED_SUMMARY_CHANGED")
        summaries = [read_json(Path(p) / "summary.json") for p in batches]
    else:
        with ProcessPoolExecutor(max_workers=min(3, len(batches))) as pool:
            summaries = list(pool.map(wait_and_verify_batch if wait else verify_batch, batches, repeat(calendar)))
    if {s["group"] for s in summaries} != {"basic", "wide", "new"} or len(summaries) != 3:
        raise ValueError("THREE_GROUPS_REQUIRED")
    if len({s["code_hash"] for s in summaries}) != 1 or len({s["prepared_manifest_hash"] for s in summaries}) != 1:
        raise ValueError("INCOMPARABLE_BATCH_BINDINGS")
    if summaries[0]["prepared_manifest_hash"] != digest(Path(prepared) / "manifest.json"):
        raise ValueError("REPORT_CALENDAR_INPUT_CHANGED")
    rows = [r for s in summaries for r in s["results"]]
    parity = legacy_parity(rows, legacy)
    pairs = duration_pairs(rows)
    hypotheses = hypothesis_pairs(rows)
    write_json(out / "verification.json", dict(status="PASS", runs=len(rows), legacy_parity=parity,
        summaries={str(p): digest(Path(p) / "summary.json") for p in batches}))
    write_json(out / "duration-comparison.json", pairs)
    write_json(out / "hypothesis-comparison.json", hypotheses)
    annual = annual_strategy_totals(rows)
    complete_annual = complete_duration_annual(annual)
    write_json(out / "duration-four-year-matched.json", complete_annual)
    write_json(out / "strategy-annual-totals.json", annual)
    (out / "strategy-annual-totals.md").write_text("# 전략별 2020~2023 매수·매도 횟수와 성과\n\n"
        "네 개의 독립 연도 실행이 모두 성공한 전략만 연평균 수익률과 4개년 체결 합계를 표시한다. "
        "4년 연속 복리수익률이 아니며, 미완료 연도를 빼서 전체처럼 집계하지 않는다. "
        "보유기간은 종료된 거래의 달력일 평균이다. 연말 미청산 합계는 네 계좌의 합계로, "
        "한 계좌의 동시 보유 종목 수가 아니다.\n\n"
        + table(["전략군", "매수조건", "청산기준", "최대개월", "성공연도/4", "평균연수익", "최악연도낙폭",
                 "매수체결합계", "매도체결합계", "종료거래", "평균보유일", "연말미청산합계"],
                [[r["family"], r["entry"], r["exit_rule"], r["months"] or "월간교체", r["successful_years"],
                  pct(r["mean_annual_return"]), pct(r["worst_annual_mdd"]),
                  *[r[k] if r[k] is not None else "—" for k in ("buy_count", "sell_count", "completed_trades")],
                  round(r["mean_holding_days"], 2) if r["mean_holding_days"] is not None else "—",
                  r["year_end_open_positions_sum"] if r["year_end_open_positions_sum"] is not None else "—"] for r in annual])
        + "\n", encoding="utf-8")
    flat = []
    for row in rows:
        stats, metrics = row.get("statistics", {}), row.get("metrics", {})
        flat.append(dict(family=row["family"], entry=row["entry_id"], exit=row["exit_id"],
                         exit_rule=exit_label(row["family"], row["exit_id"]),
                         months=row["max_holding_months"], window=row["window"], status=row["status"],
                         **merge_statistics_metrics(stats, {k: v for k, v in metrics.items() if k != "issues"}),
                         issues="; ".join(row["issues"]), run_id=row["run_id"]))
    write_json(out / "all-strategies.json", flat)
    pd.DataFrame(flat).to_parquet(out / "all-strategies.parquet", index=False)
    header = ["전략군", "매수 조건", "청산 기준", "최대개월", "기간", "상태", "수익률", "최대낙폭",
              "매수체결", "매도체결", "종료거래", "평균보유일", "미청산종목", "횟수범위"]
    detail = []
    for r in flat:
        detail.append([r["family"], r["entry"], r["exit_rule"], r["months"] or "월간교체", r["window"], r["status"],
                       pct(r.get("total_return")), pct(r.get("max_drawdown")), r.get("buy_count", "—"),
                       r.get("sell_count", "—"), r.get("completed_trades", "—"),
                       round(r["mean_holding_days"], 2) if r.get("mean_holding_days") is not None else "—",
                       r.get("open_positions", "—"), r.get("count_scope", "미실행")])
    (out / "all-strategies.md").write_text("# 전략별 성과와 실제 매수·매도 횟수\n\n"
        "매수·매도는 주문 제출이 아닌 실제 체결 건수다. 미청산 보유 때문에 두 수가 다를 수 있다. "
        "BLOCKED 행의 횟수는 중단 전 부분 기록이며 완결 성과와 비교하지 않는다. 수익률은 비용 차감·현금배당 제외다. "
        "연도별 계좌는 독립이고 continuous는 4년 연속 누적수익률이다. 개발기간은 별도다.\n\n"
        + table(header, detail) + "\n", encoding="utf-8")
    success = sum(r["status"] == "SUCCEEDED" for r in rows)
    no_trade = sum(r["status"] == "SUCCEEDED" and r["statistics"]["buy_count"] == 0 for r in rows)
    blocked_reasons = Counter((r["issues"][-1].split(":")[0] if r["issues"] else "UNSPECIFIED")
                              for r in rows if r["status"] == "BLOCKED")
    write_json(out / "blocked-reasons.json", dict(blocked_reasons))
    lines = ["# 신규 전략과 최대 보유기간 1·3·6개월 비교 결과", "",
        f"전체 {len(rows):,}개 계획 중 성공 {success:,}개, 차단 {len(rows)-success:,}개다. "
        "검증된 v3의 동일 1,076종목에서 날짜별 수수료·매도세와 다음 거래일 체결을 사용했다. "
        "사후 종목 제외·현금배당 제외의 한계가 있으며, 이미 본 2020~2023년은 새 독립 검증이 아니다.", "",
        "핵심 판단과 후속 후보는 [결과 해석](interpretation.md)에 정리했다. "
        "먼저 보유기간 비교에서 같은 전략의 변화를 보고, 신규 가설을 별도로 읽는다. "
        "전략별 매수·매도 횟수는 [4개년 집계표](strategy-annual-totals.md), "
        "개별 연도·연속 계좌·개발기간 결과는 [상세표](all-strategies.md)에 있다.", "",
        "## 최대 보유기간 비교", "",
        "먼저 네 연도와 세 보유기간이 모두 성공한 동일 전략들만 고정해서 비교한다. "
        "평균 연수익은 각 독립 연도 수익률의 단순 평균이며 복리수익률이 아니다. "
        "낙폭은 각 전략의 최악 연도 낙폭을 평균했다. 매수·매도는 네 해·해당 전략들의 체결 합계다.", "",
        table(["전략군", "최대개월", "동일전략수", "평균연수익", "최악연도낙폭평균", "매수합계", "매도합계", "평균보유일"],
              [[p["family"], p["months"], p["matched_strategies"], pct(p["mean_annual_return"]),
                pct(p["mean_worst_annual_mdd"]), p["buy_count"], p["sell_count"],
                round(p["mean_holding_days"], 2) if p["mean_holding_days"] is not None else "—"]
               for p in complete_annual]), "",
        "### 개별 연도와 연속 계좌", "",
        "각 행 묶음은 1·3·6개월 모두 성공한 동일 조합만 비교한다. 기간별 대응 조합이 달라 "
        "행 간 평균을 종합 순위로 읽지 않는다. continuous는 연평균이 아닌 2020~2023 누적수익률이다. "
        "손절·익절이 먼저 발생하면 만기 전에 팔린다. 매수·매도 수는 해당 조합들의 합계다.", "",
        table(["전략군", "기간", "최대개월", "대응조합", "평균수익률", "평균최대낙폭", "매수", "매도", "평균보유일"],
              [[p["family"], p["window"], p["months"], p["matched"], pct(p["mean_return"]), pct(p["mean_mdd"]),
                p["buys"], p["sells"], round(p["mean_holding"], 2) if p["mean_holding"] is not None else "—"] for p in pairs]),
        "", "## 신규 가설", "",
        "월간 모멘텀은 두 시장 통합 상위 20개를 월말 선정하고 다음 시가에 교체한다. "
        "새 보유에 계좌의 최대 4%를 배분하고 총 신규 투자 상한 80%를 적용하며, 기존 보유 수량은 유지한다. "
        "매월 전체 동일가중 재조정은 아니다. 고정 손절·익절·개월 만기는 없고 월간 탈락 신호로 청산한다. "
        "같은 유니버스의 동일가중 전체시장 기준선은 이번 실행에 없어 상대강도 자체의 초과수익을 확정하지 않는다.", "",
        "시장 필터는 공식 KOSPI/KOSDAQ의 200일 이동평균 위에서만 돌파 진입을 허용한다. "
        "추세청산은 기존 돌파·최초손절·수량을 유지하되 고정 익절을 없애고 수정종가가 직전20거래일 "
        "수정저가 최저치를 하회하면 다음 시가에 매도한다. 둘 다 기존 대응 전략과 별도 비교한다.", "",
        table(header, [v for r, v in zip(flat, detail) if r["family"] == "momentum"]), "",
        "다음 표는 4년 연속 실행에서 기존 대조군과 신규 조건이 모두 성공한 동일 조합만 비교한다. "
        "투자비중 감소 자체가 낙폭을 줄였는지도 함께 본다. 다른 기간은 [전체 대응 집계](hypothesis-comparison.json)에 있다.", "",
        table(["가설", "최대개월", "대응조합", "기존누적수익", "신규누적수익", "기존낙폭", "신규낙폭",
               "기존투자비중", "신규투자비중", "기존매수/매도", "신규매수/매도"],
              [[p["family"], p["months"], p["matched"], pct(p["control_total_return"]), pct(p["treatment_total_return"]),
                pct(p["control_max_drawdown"]), pct(p["treatment_max_drawdown"]),
                pct(p["control_average_exposure_fraction"]), pct(p["treatment_average_exposure_fraction"]),
                f"{p['control_buy_count']}/{p['control_sell_count']}",
                f"{p['treatment_buy_count']}/{p['treatment_sell_count']}"]
               for p in hypotheses if p["window"] == "continuous_2020_2023"]), "",
        "신규 돌파 변형의 전체 조건·기간과 차단 사유는 상세표와 [기계 판독 결과](all-strategies.json)에 있다.", "",
        "## 차단된 실행", "",
        "다음은 각 차단 실행의 마지막 차단 사유를 한 번씩 집계한 값이다. "
        "이 실행들은 전체 기간 성과를 확정하지 않았고, 거래횟수도 차단 전 부분 기록으로만 남겼다.", "",
        table(["사유 코드", "실행 수"], sorted(blocked_reasons.items())), "",
        "## 해석과 재현 한계", "",
        "- 각 독립 연도는 1억 원으로 다시 시작한다. 연말 강제청산은 없으며 미청산 종목은 종가 평가 후 "
        "다음 연도로 이어지지 않는다. 4년 연속 실행은 이 단절 없이 계산했다.",
        "- 1개월 대조군 560개는 이전 저장 결과의 상태·성과·매수매도 체결수를 대조했다.",
        "- 성공 장부는 파일 해시, 현금·주식 원장 재생, 성과와 거래횟수 재계산을 통과했다. "
        "차단 실행에 수익률을 부여하지 않았다.",
        f"- 성공 실행 중 매수가 한 번도 없는 실행은 {no_trade}개다. 무거래 0%는 전략의 수익성 근거가 아니다.",
        "- 2024년 이후 가격을 열지 않았다. 수익성이 있더라도 전략 선정·실거래 승인을 뜻하지 않는다.", "",
        "- 시장 지수는 KRX 공식 원천과 대조했으나 2026년에 재수집한 과거 자료다. 당시 보관한 원본 응답과 "
        "역사적 수정 이력까지 입증한 것은 아니며, 회고적 가격 연구 범위에서 사용했다.", "",
        "[검증 기록](verification.json) · [상세표](all-strategies.md) · [Parquet](all-strategies.parquet)", ""]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return {"runs": len(rows), "succeeded": success, "blocked": len(rows) - success}


def merge_statistics_metrics(statistics, metrics):
    for key in statistics.keys() & metrics.keys():
        if not close(statistics[key], metrics[key]):
            raise ValueError(f"STATISTICS_METRICS_MISMATCH:{key}")
    return {**metrics, **statistics}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", nargs=3, required=True)
    parser.add_argument("--prepared", required=True)
    parser.add_argument("--legacy", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--wait", action="store_true", help="Verify completed siblings while waiting for RUNNING batches")
    parser.add_argument("--render-verified", action="store_true",
                        help="Re-render previously verified, hash-unchanged summaries without replaying ledgers")
    args = parser.parse_args()
    print(build_report(args.batches, args.prepared, args.legacy, args.out, wait=args.wait,
                       render_verified=args.render_verified))
