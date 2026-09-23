"""Frozen, dated-cost experiments for duration and separately registered hypotheses."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pandas as pd

from .config_v2 import ENTRIES, EXITS, WIDE_EXITS
from .io import canonical_hash, digest, read_json, source_hash, write_json
from .metrics import calculate_metrics
from .v3_run import _ORACLE_TESTS, _save_result, admission_bindings, reconcile_result, verify_prepared


EXTRA_TESTS = ["tests/research/test_v3_extension_execution.py",
               "tests/research/test_extension_signals.py", "tests/research/test_extension_run.py"]


def prepare_signals(prepared_path, benchmark_evidence, out):
    """Bind new causal signals to unchanged admitted inputs and official index evidence."""
    from .extension_signals import (load_adjusted_prices, load_v3_benchmarks, monthly_relative_momentum,
                                    prior_20_low_exit, benchmark_above_sma200, apply_breakout_market_filter)
    prepared_path, benchmark_evidence, out = Path(prepared_path), Path(benchmark_evidence), Path(out)
    out.mkdir(parents=True, exist_ok=False)
    code_hash = source_hash()
    manifest, cohort = verify_prepared(prepared_path)
    evidence = read_json(benchmark_evidence)
    if (evidence.get("status") != "PASS_RETROSPECTIVE"
            or evidence["source_manifest_hash"] != manifest["source_manifest_hash"]
            or evidence["typed_manifest_hash"] != manifest["typed_manifest_hash"]):
        raise ValueError("BENCHMARK_NOT_VERIFIED_FOR_SOURCE")
    base = pd.read_parquet(prepared_path / "signals.parquet")
    calendar = pd.read_parquet(prepared_path / "calendar.parquet")
    keys = ["date", "instrument_id"]
    base["date"] = pd.to_datetime(base.date)
    base["instrument_id"] = base.instrument_id.astype(str)
    print("LOAD_ADJUSTED_EXTENSION_INPUTS", flush=True)
    adjusted = load_adjusted_prices(manifest["source"], manifest["typed"], instrument_ids=cohort["instrument_ids"])
    adjusted["instrument_id"] = adjusted.instrument_id.astype(str)
    working = base[keys + ["eligible", "input_blocked", "issue_blocked"]].merge(
        adjusted[keys + ["adjusted_close", "adjusted_low"]], on=keys, how="left", validate="one_to_one")
    del adjusted
    working["eligible"] = (working.eligible.fillna(False).astype(bool)
                           & ~working.input_blocked.fillna(True).astype(bool)
                           & ~working.issue_blocked.fillna(True).astype(bool))
    print("BUILD_MONTHLY_MOMENTUM", flush=True)
    momentum = monthly_relative_momentum(working, calendar)
    print("BUILD_LOW20_AND_MARKET_FILTER", flush=True)
    lows = prior_20_low_exit(working, calendar=calendar)
    del working
    benchmarks = load_v3_benchmarks(manifest["source"], manifest["typed"])
    sessions = set(pd.to_datetime(calendar.date))
    if set(benchmarks.market) != {"KOSPI", "KOSDAQ"}:
        raise ValueError("BENCHMARK_MARKETS_INCOMPLETE")
    for _, part in benchmarks.groupby("market"):
        values = pd.to_numeric(part.close).to_numpy(dtype=float)
        if (set(part.date) != sessions or part.date.duplicated().any()
                or not np.isfinite(values).all() or (values <= 0).any()):
            raise ValueError("BENCHMARK_CALENDAR_OR_VALUE_INVALID")
    market = apply_breakout_market_filter(base, benchmark_above_sma200(benchmarks))
    derived = base
    for extra in (momentum.drop(columns=["target"]), lows, market):
        derived = derived.merge(extra, on=keys, how="left", validate="one_to_one")
    names = ["MOMENTUM_ENTRY", "MOMENTUM_EXIT", "LOW20_EXIT", "LOW20_VALID",
             "BREAKOUT_20_MARKET200", "BREAKOUT_60_MARKET200"]
    if len(derived) != len(base) or derived[names].isna().any().any():
        raise ValueError("DERIVED_SIGNAL_ALIGNMENT_INCOMPLETE")
    for name in names:
        derived[name] = derived[name].astype(bool)
    derived.to_parquet(out / "signals.parquet", index=False)
    if source_hash() != code_hash:
        raise ValueError("CODE_CHANGED_DURING_SIGNAL_PREPARATION")
    binding = dict(status="PREPARED", code_hash=code_hash,
                   prepared_manifest_hash=digest(prepared_path / "manifest.json"),
                   benchmark_evidence_path=str(benchmark_evidence.resolve()),
                   benchmark_evidence_hash=digest(benchmark_evidence), sha256=digest(out / "signals.parquet"),
                   rows=len(derived), signal_counts={name: int(derived[name].sum()) for name in names},
                   definitions={"momentum": "C(month-1)/C(month-12)-1; combined top20; completed month-end; next open",
                                "low20": "adjusted close < minimum of previous20 session adjusted lows; next open",
                                "market": "respective official KOSPI/KOSDAQ close > inclusive trailing200 mean"},
                   limitations=["RETROSPECTIVE_INDEX_CAPTURE_NOT_HISTORICAL_VINTAGE",
                                "EX_POST_CLEAN_COHORT", "CASH_DIVIDENDS_EXCLUDED", "2024_PLUS_LOCKED"])
    write_json(out / "manifest.json", binding)
    return binding


def experiment_plan(group="all"):
    """Keep legacy annual controls and add a separately labeled continuous window."""
    windows = [("development", "2015-06-15", "2019-12-31")]
    windows += [(f"year_{year}", f"{year}-01-01", f"{year}-12-31") for year in range(2020, 2024)]
    windows += [("continuous_2020_2023", "2020-01-01", "2023-12-31")]
    runs = []

    def add(family, entry, exit_id, months, **kwargs):
        for window, start, end in windows:
            spec = dict(family=family, entry_id=entry, exit_id=exit_id, max_holding_months=months,
                        window=window, start=start, end=end, cost_bps=None, delay=1, **kwargs)
            spec["run_id"] = canonical_hash(spec)[:20]
            runs.append(spec)

    for family, exits in (("basic", EXITS), ("wide", WIDE_EXITS)):
        if group in ("all", family):
            for entry in ENTRIES:
                for exit_id in exits:
                    for months in (1, 3, 6):
                        add(family, entry, exit_id, months)
    if group in ("all", "new"):
        for entry in ("BREAKOUT_20", "BREAKOUT_60"):
            for exit_id in (*EXITS, *WIDE_EXITS):
                for months in (1, 3, 6):
                    add("trend_exit", entry, exit_id, months,
                        exit_signal_id="LOW20_EXIT", exit_signal_valid_id="LOW20_VALID", suppress_target=True)
                    add("market_filter", entry + "_MARKET200", exit_id, months)
        add("momentum", "MOMENTUM_ENTRY", "PCT_3_6", None,
            exit_signal_id="MOMENTUM_EXIT", suppress_target=True, suppress_stop=True,
            position_sizing="equal_weight", entry_order="market_open")
    if group not in ("all", "basic", "wide", "new"):
        raise ValueError("UNKNOWN_GROUP")
    return runs


def trade_statistics(result):
    """Filled orders, completed round trips and open holdings are different counts."""
    fills, trades, equity = result["fills"], result["trades"], result["equity"]
    if result["status"] != "SUCCEEDED":
        return dict(buy_count=int(fills.side.eq("buy").sum()), sell_count=int(fills.side.eq("sell").sum()),
                    completed_trades=None, holding_days_sum=None, mean_holding_days=None,
                    median_holding_days=None, open_positions=None, count_scope="PARTIAL_BEFORE_BLOCK")
    holding = (pd.to_datetime(trades.exit_date) - pd.to_datetime(trades.entry_date)).dt.days
    return dict(buy_count=int(fills.side.eq("buy").sum()), sell_count=int(fills.side.eq("sell").sum()),
                completed_trades=len(trades), holding_days_sum=int(holding.sum()),
                mean_holding_days=float(holding.mean()) if len(holding) else None,
                median_holding_days=float(holding.median()) if len(holding) else None,
                open_positions=int(equity.iloc[-1].positions_count) if len(equity) else 0,
                count_scope="FULL_WINDOW" if result["status"] == "SUCCEEDED" else "PARTIAL_BEFORE_BLOCK")


def certify(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    code_hash = source_hash()
    tests = list(dict.fromkeys([*_ORACLE_TESTS, *EXTRA_TESTS]))
    test_hashes = {name: digest(name) for name in tests}
    command = [sys.executable, "-X", "utf8", "-m", "pytest", *tests, "-q"]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    (out / "pytest.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    passed = completed.returncode == 0 and code_hash == source_hash()
    passed &= test_hashes == {name: digest(name) for name in tests}
    evidence = dict(status="PASS" if passed else "FAIL", code_hash=code_hash, test_hashes=test_hashes,
                    command=command, log_hash=digest(out / "pytest.txt"), returncode=completed.returncode)
    write_json(out / "evidence.json", evidence)
    if not passed:
        raise ValueError(f"EXTENSION_ORACLE_FAILED: {out / 'pytest.txt'}")
    return evidence


def verify_evidence(path):
    path = Path(path)
    evidence = read_json(path / "evidence.json")
    if (evidence.get("status") != "PASS" or evidence.get("code_hash") != source_hash()
            or evidence.get("log_hash") != digest(path / "pytest.txt")
            or not set([*_ORACLE_TESTS, *EXTRA_TESTS]).issubset(evidence.get("test_hashes", {}))
            or any(digest(name) != value for name, value in evidence["test_hashes"].items())):
        raise ValueError("EXECUTION_EVIDENCE_STALE")
    return evidence


def run(prepared_path, evidence_path, signal_path, out, *, group, limit=None):
    """All source/signal checks and current numerical evidence precede real execution."""
    from .real_receipts import create_execution_admission_receipt
    from .resources import ResourceLimits, ResourceMonitor
    from .v3_execution import PreparedExecution, audit_execution_ledger, simulate_real_slot
    from .v3_market import V3MarketRules

    if group not in ("basic", "wide", "new"):
        raise ValueError("RUN_REQUIRES_SINGLE_GROUP")
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("LIMIT_MUST_BE_POSITIVE")
    prepared_path, signal_path, out = Path(prepared_path), Path(signal_path), Path(out)
    out.mkdir(parents=True, exist_ok=False)
    with ResourceMonitor(out, ResourceLimits(max_rss_bytes=3 * 1024**3,
                         min_free_disk_bytes=1024**3, poll_interval_seconds=0.5)) as monitor:
        try:
            manifest, cohort = verify_prepared(prepared_path)
            evidence = verify_evidence(evidence_path)
            plan = experiment_plan(group)
            frames = {name: pd.read_parquet(prepared_path / info["file"])
                      for name, info in manifest["files"].items()}
            signals = frames["signals"]
            signal_binding = None
            if group == "new":
                extra = read_json(signal_path / "manifest.json")
                if (extra["prepared_manifest_hash"] != digest(prepared_path / "manifest.json")
                        or extra["code_hash"] != source_hash()
                        or extra["sha256"] != digest(signal_path / "signals.parquet")
                        or extra["benchmark_evidence_hash"] != digest(extra["benchmark_evidence_path"])):
                    raise ValueError("EXTENSION_SIGNALS_CHANGED")
                signals = pd.read_parquet(signal_path / "signals.parquet")
                signal_binding = digest(signal_path / "manifest.json")
            rules = V3MarketRules(frames["rules"])
            prepared = PreparedExecution(frames["prices"], signals, frames["calendar"].date, frames["events"],
                                         period_start="2014-01-01", period_end="2023-12-31")
            del frames, signals
            summary = dict(schema_version="krx-extension-v1", status="RUNNING", group=group,
                           created_at=datetime.now(timezone.utc).isoformat(), code_hash=source_hash(),
                           prepared_manifest_hash=digest(prepared_path / "manifest.json"),
                           signal_manifest_hash=signal_binding, planned_runs=len(plan), results=[],
                           limitations=cohort["limitations"], rule_assumptions=rules.assumptions)
            write_json(out / "plan.json", {"runs": plan, "plan_hash": canonical_hash(plan)})
            write_json(out / "summary.json", summary)
            smoke = simulate_real_slot(prepared, rules, entry_id="CROSS_5_20", exit_id="PCT_3_6",
                                       start="2015-06-15", end="2015-12-31", hooks=monitor.checkpoint)
            if smoke["status"] == "SUCCEEDED":
                audit_execution_ledger(smoke)
            checked = reconcile_result(smoke, expected_dates=[d for d in prepared.calendar
                                       if pd.Timestamp("2015-06-15") <= d <= pd.Timestamp("2015-12-31")])
            smoke_files = _save_result(out / "smoke", smoke)
            if (checked["status"] != "PASS" or not {"buy", "sell"}.issubset(set(smoke["fills"].side))
                    or not smoke["cashflows"].kind.eq("SETTLEMENT").any()):
                raise ValueError("SMALL_REAL_LEDGER_REPLAY_FAILED")
            bindings = dict(model_hash=digest(Path(__file__).with_name("v3_execution.py")),
                            cost_hash=digest(Path(__file__).with_name("v3_market.py")),
                            strategy_hash=canonical_hash({"plan": canonical_hash(plan), "signals": signal_binding}),
                            code_hash=source_hash(), oracle_hash=canonical_hash(evidence),
                            ledger_hash=canonical_hash(smoke_files))
            receipt = create_execution_admission_receipt(read_json(prepared_path / "data-admission.json"),
                manifest=manifest, **admission_bindings(prepared_path, manifest, cohort), bindings=bindings,
                checks={"CURRENT_NUMERICAL_ORACLE": "PASS", "SMALL_REAL_LEDGER_REPLAY": "PASS"})
            write_json(out / "execution-admission.json", receipt)
            for index, spec in enumerate(plan[:limit] if limit else plan):
                if source_hash() != summary["code_hash"]:
                    raise ValueError("CODE_CHANGED_DURING_BATCH")
                started = time.monotonic()
                missing = spec["entry_id"] not in prepared.signals
                if missing and spec["family"] != "market_filter":
                    raise ValueError("MISSING_REQUIRED_STRATEGY_SIGNAL")
                if missing:
                    item = {**spec, "status": "BLOCKED", "issues": ["OFFICIAL_MARKET_INDEX_NOT_ADMITTED"],
                            "ledger_check": {"status": "BLOCKED"}, "files": {}}
                    target = out / "runs" / spec["run_id"]
                    target.mkdir(parents=True, exist_ok=False)
                else:
                    args = {k: v for k, v in spec.items() if k not in ("run_id", "family", "window")}
                    result = simulate_real_slot(prepared, rules, **args, hooks=monitor.checkpoint)
                    if result["status"] == "SUCCEEDED":
                        audit_execution_ledger(result)
                    checked = reconcile_result(result, expected_dates=[d for d in prepared.calendar
                                                if pd.Timestamp(spec["start"]) <= d <= pd.Timestamp(spec["end"])])
                    if result["status"] == "SUCCEEDED" and checked["status"] != "PASS":
                        raise ValueError("SUCCESSFUL_RESULT_LEDGER_NOT_VERIFIED")
                    target = out / "runs" / spec["run_id"]
                    files = _save_result(target, result)
                    item = {**spec, "status": result["status"], "issues": result["issues"],
                            "ledger_check": checked, "files": files, "statistics": trade_statistics(result)}
                    if checked["status"] == "PASS":
                        item["metrics"] = calculate_metrics(result)
                        item["metrics"]["total_taxes"] = float(result["fills"].tax.sum())
                        account = result["equity"]
                        item["metrics"]["average_exposure_fraction"] = float(
                            (account.exposure.astype(float) / account.equity.astype(float)).mean())
                    del result
                item["seconds"] = round(time.monotonic() - started, 3)
                if source_hash() != summary["code_hash"]:
                    raise ValueError("CODE_CHANGED_DURING_SLOT")
                write_json(target / "result.json", item)
                summary["results"].append(item)
                write_json(out / "progress.json", {"attempted": index + 1, "planned": len(plan),
                                                   "latest": spec["run_id"]})
                if (index + 1) % 20 == 0:
                    write_json(out / "summary.json", summary)
                print(f"{index+1}/{len(plan)} {spec['family']} {spec['entry_id']} {spec['exit_id']} "
                      f"M{spec['max_holding_months']} {spec['window']} {item['status']} {item['seconds']}s", flush=True)
            summary.update(status="COMPLETE" if len(summary["results"]) == len(plan) else "PARTIAL",
                           attempted_runs=len(summary["results"]),
                           succeeded_runs=sum(x["status"] == "SUCCEEDED" for x in summary["results"]),
                           blocked_runs=sum(x["status"] == "BLOCKED" for x in summary["results"]),
                           completed_at=datetime.now(timezone.utc).isoformat())
            write_json(out / "summary.json", summary)
            return summary
        except Exception as exc:
            write_json(out / "failure.json", {"error": f"{type(exc).__name__}: {exc}"})
            raise
        finally:
            write_json(out / "resources.json", monitor.telemetry)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "certify", "run"])
    parser.add_argument("--out", required=True)
    parser.add_argument("--prepared")
    parser.add_argument("--evidence")
    parser.add_argument("--signals")
    parser.add_argument("--benchmark-evidence")
    parser.add_argument("--group", choices=["basic", "wide", "new"], default="new")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare_signals(args.prepared, args.benchmark_evidence, args.out)
    elif args.action == "certify":
        certify(args.out)
    else:
        run(args.prepared, args.evidence, args.signals or args.prepared, args.out,
            group=args.group, limit=args.limit)


if __name__ == "__main__":
    main()
