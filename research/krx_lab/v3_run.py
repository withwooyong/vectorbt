"""Reproducible v3 clean-cohort research runs, with explicit data/model receipts.

This separate path never weakens the legacy synthetic runner's REAL guard.
Reports are price-trading experiments in an ex-post clean cohort, not total
returns, full-market selection or approval for live trading.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

import pandas as pd

from .io import canonical_hash, digest, read_json, write_json, source_hash
from .real_receipts import create_data_admission_receipt, create_execution_admission_receipt
from .v3_scope import clean_cohort


_TABLES = ("prices", "signals", "calendar", "events", "rules", "issues")
_ORACLE_TESTS = ["tests/research/test_v3_market.py", "tests/research/test_v3_inputs.py",
                 "tests/research/test_v3_scope.py", "tests/research/test_v3_execution.py",
                 "tests/research/test_v3_execution_oracle.py", "tests/research/test_v3_run.py"]


def _builder_hash():
    root = Path(__file__).parent
    return canonical_hash({name: digest(root / name) for name in (
        "v3_inputs.py", "v3_scope.py", "strategies.py", "indicators.py", "v3_tables.py", "v3_snapshot.py")})


def prepare_run(source, typed, out):
    """Fully verify source/cache, build one shared cohort, and bind prepared files."""
    from .v3_tables import verify_v3_tables, iter_v3_tables
    from .v3_inputs import load_v3_inputs

    source, typed, out = Path(source).resolve(), Path(typed).resolve(), Path(out).resolve()
    builder_hash = _builder_hash()
    out.mkdir(parents=True, exist_ok=False)
    state = {"status": "PREPARING", "source": str(source), "typed": str(typed)}
    write_json(out / "manifest.json", state)
    try:
        print("VERIFY_SOURCE_AND_TYPED_VALUES", flush=True)
        verify_v3_tables(source, typed)
        print("PREPARE_SIGNALS", flush=True)
        inputs = load_v3_inputs(source, typed)
        adjustment = pd.concat(list(iter_v3_tables(source, typed, "ADJUSTMENT")), ignore_index=True)
        cohort = clean_cohort(inputs, adjustment)
        write_json(out / "cohort.json", cohort)
        if cohort["decision"] != "PASS":
            raise ValueError("DATA_COHORT_BLOCKED: " + json.dumps(cohort["unresolved_issues"], ensure_ascii=False))
        included = set(cohort["instrument_ids"])
        frames = {"prices": inputs.prices.loc[inputs.prices.instrument_id.astype(str).isin(included)].copy(),
                  "signals": inputs.signals.loc[inputs.signals.instrument_id.astype(str).isin(included)].copy(),
                  "events": inputs.events.loc[inputs.events.instrument_id.astype(str).isin(included)].copy(),
                  "calendar": inputs.calendar, "issues": inputs.issues,
                  "rules": pd.concat(list(iter_v3_tables(source, typed, "EXECUTION_RULE")), ignore_index=True)}
        # source snapshots retain every provenance field. Runtime frames need
        # only execution columns and the shared, previously validated signals.
        keep_prices = [name for name in ("date", "code", "instrument_id", "display_code", "market",
                       "open", "high", "low", "close", "volume", "status", "eligible") if name in frames["prices"]]
        frames["prices"] = frames["prices"][keep_prices]
        files = {}
        for name, frame in frames.items():
            target = out / f"{name}.parquet"
            # Object columns can contain dicts in the issue/evidence transport;
            # Parquet must not invent a field-dependent struct schema.
            for column in frame.select_dtypes(include="object"):
                if frame[column].map(lambda value: isinstance(value, (dict, list))).any():
                    frame[column] = frame[column].map(lambda value: json.dumps(value, ensure_ascii=False, default=str)
                                                       if isinstance(value, (dict, list)) else value)
            frame.to_parquet(target, index=False)
            files[name] = {"file": target.name, "rows": len(frame), "sha256": digest(target)}
        manifest = {"schema_version": "v3-run-input-v1", "status": "PREPARED", "source_kind": "REAL",
                    "dataset_id": "krx-backtest-source", "revision": "2014-2023-v3",
                    "source": str(source), "typed": str(typed),
                    "source_manifest_hash": digest(source / "manifest.json"),
                    "typed_manifest_hash": digest(typed / "manifest.json"),
                    "cohort_hash": digest(out / "cohort.json"), "files": files,
                    "record_granularity": "PREPARED_PARQUET_PARTITION",
                    "created_at": datetime.now(timezone.utc).isoformat(), "builder_code_hash": builder_hash,
                    "limitations": cohort["limitations"]}
        if builder_hash != _builder_hash():
            raise ValueError("INPUT_BUILDER_CHANGED_DURING_PREPARATION")
        write_json(out / "manifest.json", manifest)
        checks = {name: "PASS" for name in ("PINNED_SOURCE_SEAL", "TYPED_VALUE_CORRESPONDENCE",
                   "CURRENT_RAW_ADJUSTED_PRICE_CONTENT", "SOURCE_ISSUE_DISPOSITION", "COMMON_COHORT",
                   "250_BAR_READINESS", "PRE_2024_PRICE_SCOPE")}
        bindings = admission_bindings(out, manifest, cohort)
        receipt = create_data_admission_receipt(manifest, checks=checks, **bindings)
        write_json(out / "data-admission.json", receipt)
        print(f"PREPARED {len(included)} instruments; {len(frames['prices'])} price rows", flush=True)
        return manifest
    except Exception as exc:
        state.update(status="BLOCKED", error=str(exc))
        write_json(out / "manifest.json", state)
        raise


def admission_bindings(out, manifest, cohort):
    return {"scope": {"start": "2015-06-15", "end": "2023-12-31", "markets": ["KOSPI", "KOSDAQ"],
                       "instrument_ids": cohort["instrument_ids"]},
            "included_record_ids": [f"partition:{name}:{value['sha256']}" for name, value in sorted(manifest["files"].items())],
            "excluded_issue_ids": [canonical_hash(item) for item in cohort["exclusions"]],
            "evaluator_code_hash": manifest["builder_code_hash"]}


def verify_prepared(out):
    out = Path(out)
    manifest, cohort = read_json(out / "manifest.json"), read_json(out / "cohort.json")
    if manifest.get("status") != "PREPARED" or manifest.get("schema_version") != "v3-run-input-v1":
        raise ValueError("PREPARED_INPUT_NOT_READY")
    if manifest["builder_code_hash"] != _builder_hash():
        raise ValueError("INPUT_BUILDER_CHANGED")
    if cohort["decision"] != "PASS" or digest(out / "cohort.json") != manifest["cohort_hash"]:
        raise ValueError("COHORT_CHANGED")
    for key in ("source", "typed"):
        if digest(Path(manifest[key]) / "manifest.json") != manifest[key + "_manifest_hash"]:
            raise ValueError("UPSTREAM_MANIFEST_CHANGED")
        upstream = Path(manifest[key]).resolve()
        for part in read_json(upstream / "manifest.json")["parts"]:
            target = upstream / part["file"]
            if target.resolve().parent != upstream or digest(target) != part["sha256"]:
                raise ValueError("UPSTREAM_PART_CHANGED")
    for value in manifest["files"].values():
        target = out / value["file"]
        if target.resolve().parent != out.resolve() or digest(target) != value["sha256"]:
            raise ValueError("PREPARED_FILE_CHANGED")
    from .real_receipts import verify_data_admission_receipt
    verify_data_admission_receipt(read_json(out / "data-admission.json"), manifest=manifest,
                                  **admission_bindings(out, manifest, cohort))
    return manifest, cohort


def certify_execution(out):
    """Record current independent numerical test evidence, never infer it from old runs."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    code_hash = source_hash()
    test_hashes = {name: digest(name) for name in _ORACLE_TESTS}
    command = [sys.executable, "-X", "utf8", "-m", "pytest", *_ORACLE_TESTS, "-q"]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
    (out / "pytest.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    passed = (completed.returncode == 0 and code_hash == source_hash()
              and test_hashes == {name: digest(name) for name in _ORACLE_TESTS})
    evidence = {"status": "PASS" if passed else "FAIL",
                "returncode": completed.returncode, "command": command, "code_hash": code_hash,
                "test_hashes": test_hashes,
                "log_hash": digest(out / "pytest.txt"), "created_at": datetime.now(timezone.utc).isoformat()}
    write_json(out / "evidence.json", evidence)
    if evidence["status"] != "PASS":
        raise ValueError("EXECUTION_ORACLE_FAILED: " + str(out / "pytest.txt"))
    return evidence


def reconcile_result(result, *, expected_dates, initial_cash=100_000_000):
    """Replay cash claims and daily holdings independently of the simulator."""
    from decimal import Decimal
    if result["status"] != "SUCCEEDED":
        return {"status": "BLOCKED", "issues": result["issues"]}
    def D(value):
        return Decimal(str(value))
    equity = result["equity"]
    if len(expected_dates) == 0 or pd.to_datetime(equity["date"]).tolist() != list(pd.to_datetime(expected_dates)):
        raise ValueError("EQUITY_CALENDAR_INCOMPLETE")
    flows = result["cashflows"]
    cash, recv, payable = D(initial_cash), D(0), D(0)
    def records_by_day(frame):
        grouped = {}
        for item in frame.to_dict("records"):
            grouped.setdefault(pd.Timestamp(item["date"]), []).append(item)
        return grouped

    by_day = records_by_day(flows)
    holdings = records_by_day(result["positions"])
    quantities = {}
    fills = records_by_day(result["fills"])
    events = records_by_day(result["events"])
    for row in equity.to_dict("records"):
        day = pd.Timestamp(row["date"])
        for item in events.get(day, ()):
            code = str(item["code"])
            quantities[code] = quantities.get(code, 0) + int(item["quantity_delta"])
        for item in fills.get(day, ()):
            code, size = str(item["code"]), int(item["size"])
            if size <= 0 or D(item["size"]) != size:
                raise ValueError("NON_INTEGER_FILL")
            quantities[code] = quantities.get(code, 0) + (size if item["side"] == "buy" else -size)
            if quantities[code] < 0:
                raise ValueError("NEGATIVE_POSITION")
        for flow in by_day.get(day, ()):
            cash += D(flow["cash_delta"])
            recv += D(flow["receivable_delta"])
            payable += D(flow["payable_delta"])
        positions = holdings.get(day, ())
        position_map = {str(item["code"]): int(item["size"]) for item in positions}
        if position_map != {key: value for key, value in quantities.items() if value}:
            raise ValueError("POSITION_REPLAY_MISMATCH")
        exposure = sum((D(item["size"]) * D(item["mark_price"]) for item in positions), D(0))
        expected = {"settled_cash": cash, "receivables": recv, "payables": payable,
                    "cash": cash + recv - payable, "exposure": exposure,
                    "equity": cash + recv - payable + exposure}
        for name, value in expected.items():
            if abs(D(row[name]) - value) > D("0.00001"):
                raise ValueError("LEDGER_REPLAY_MISMATCH:" + name)
        if row["positions_count"] != len(position_map) or len(position_map) > 20:
            raise ValueError("POSITION_LIMIT_MISMATCH")
        if expected["cash"] < D("-0.00001"):
            raise ValueError("NEGATIVE_ECONOMIC_CASH")
    return {"status": "PASS", "days": len(equity), "fills": len(result["fills"])}


def _save_result(out, result):
    out.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, value in result.items():
        if isinstance(value, pd.DataFrame):
            target = out / f"{name}.parquet"
            value.to_parquet(target, index=False)
            files[target.name] = digest(target)
    write_json(out / "artifacts.json", {"files": files, "status": result["status"], "issues": result["issues"]})
    return files


def _select_runs(runs, family=None):
    if family not in (None, "basic", "wide"):
        raise ValueError("UNKNOWN_EXPERIMENT_FAMILY")
    return [(index, spec) for index, spec in enumerate(runs) if family is None or spec["family"] == family]


def run_batch(prepared_path, evidence_path, out, *, limit=None, family=None):
    """Monitor one worker and preserve failures without overwriting past runs."""
    from .resources import ResourceLimits, ResourceMonitor
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    limits = ResourceLimits(max_rss_bytes=2 * 1024**3, min_free_disk_bytes=512 * 1024**2,
                            poll_interval_seconds=0.25)
    with ResourceMonitor(out, limits) as monitor:
        try:
            return _run_batch(prepared_path, evidence_path, out, limit=limit, monitor=monitor, family=family)
        except Exception as exc:
            write_json(out / "failure.json", {"status": "FAILED", "error": f"{type(exc).__name__}: {exc}",
                                              "resources": monitor.telemetry})
            raise
        finally:
            write_json(out / "resources.json", monitor.telemetry)


def _run_batch(prepared_path, evidence_path, out, *, limit, monitor, family=None):
    """Smoke-check the admitted cohort, then run both preregistered experiment plans."""
    from .config_v2 import default_config, default_wide_config, primary_runs
    from .metrics import calculate_metrics
    from .v3_execution import PreparedExecution, simulate_real_slot, audit_execution_ledger
    from .v3_market import V3MarketRules

    prepared_path, evidence_path, out = Path(prepared_path), Path(evidence_path), Path(out)
    manifest, cohort = verify_prepared(prepared_path)
    evidence = read_json(evidence_path / "evidence.json")
    if (evidence.get("status") != "PASS" or evidence["code_hash"] != source_hash()
            or evidence["log_hash"] != digest(evidence_path / "pytest.txt")
            or any(digest(name) != value for name, value in evidence["test_hashes"].items())):
        raise ValueError("EXECUTION_EVIDENCE_STALE")
    frames = {name: pd.read_parquet(prepared_path / value["file"]) for name, value in manifest["files"].items()}
    rules = V3MarketRules(frames["rules"])
    prepared = PreparedExecution(frames["prices"], frames["signals"], frames["calendar"].date, frames["events"],
                                  period_start="2014-01-01", period_end="2023-12-31")
    del frames
    summary = {"status": "RUNNING", "created_at": datetime.now(timezone.utc).isoformat(),
               "prepared_manifest_hash": digest(prepared_path / "manifest.json"), "cohort": cohort,
               "code_hash": source_hash(), "results": [], "limitations": cohort["limitations"],
               "rule_assumptions": rules.assumptions}
    write_json(out / "summary.json", summary)
    # Model smoke uses the admitted cohort and one year, and is reported only
    # after independent ledger replay. Failure does not authorize the batch.
    smoke = simulate_real_slot(prepared, rules, entry_id="CROSS_5_20", exit_id="PCT_3_6",
                               start="2015-06-15", end="2015-12-31", cost_bps=None, hooks=monitor.checkpoint)
    if smoke["status"] == "SUCCEEDED":
        audit_execution_ledger(smoke)
    oracle = reconcile_result(smoke, expected_dates=[day for day in prepared.calendar
                                                     if pd.Timestamp("2015-06-15") <= day <= pd.Timestamp("2015-12-31")])
    smoke_files = _save_result(out / "smoke", smoke)
    if oracle["status"] == "PASS" and (
        not {"buy", "sell"}.issubset(set(smoke["fills"].side))
        or not smoke["cashflows"].kind.eq("SETTLEMENT").any()
    ):
        oracle = {"status": "BLOCKED", "issues": ["SMOKE_HAS_NO_ROUND_TRIP_AND_SETTLEMENT"]}
    write_json(out / "smoke-oracle.json", oracle)
    if oracle["status"] != "PASS":
        summary.update(status="BLOCKED", smoke_issues=smoke["issues"])
        write_json(out / "summary.json", summary)
        return summary
    bindings = {"model_hash": digest(Path(__file__).with_name("v3_execution.py")),
                "cost_hash": digest(Path(__file__).with_name("v3_market.py")),
                "strategy_hash": digest(Path(__file__).with_name("strategies.py")),
                "code_hash": source_hash(), "oracle_hash": canonical_hash(evidence),
                "ledger_hash": canonical_hash(smoke_files)}
    receipt = create_execution_admission_receipt(read_json(prepared_path / "data-admission.json"),
                manifest=manifest, **admission_bindings(prepared_path, manifest, cohort), bindings=bindings,
                checks={"CURRENT_NUMERICAL_ORACLE": "PASS", "SMALL_REAL_LEDGER_REPLAY": "PASS"})
    write_json(out / "execution-admission.json", receipt)
    runs = []
    for run_family, factory in (("basic", default_config), ("wide", default_wide_config)):
        config = factory(prepared_path)
        write_json(out / f"{run_family}-config.json", config)
        for spec in primary_runs(config):
            runs.append({**spec, "family": run_family, "cost_model": "FLAT_BPS_STRESS_ONLY"})
        # Actual dated costs are additional controls, distinct from stress runs.
        for spec in primary_runs(config):
            if spec["cost_bps"] == 30 and spec["delay"] == 1:
                runs.append({**spec, "cost_bps": None, "family": run_family, "cost_model": "DATED_V3_RULES"})
    selected = _select_runs(runs, family)
    summary["planned_runs"] = len(selected)
    summary["experiment_family"] = family or "both"
    write_json(out / "run-plan.json", {"runs": [spec for _, spec in selected],
                                      "execution_receipt_hash": receipt["receipt_hash"]})
    for completed_index, (index, spec) in enumerate(selected[:limit] if limit else selected):
        if summary["code_hash"] != source_hash():
            summary["status"] = "INTERRUPTED_CODE_CHANGED"
            write_json(out / "summary.json", summary)
            raise ValueError("CODE_CHANGED_DURING_BATCH")
        started = time.monotonic()
        run_id = f"{index:04d}-{canonical_hash(spec)[:12]}"
        result = simulate_real_slot(prepared, rules, entry_id=spec["entry_id"], exit_id=spec["exit_id"],
                                    start=spec["start"], end=spec["end"], cost_bps=spec["cost_bps"], delay=spec["delay"],
                                    hooks=monitor.checkpoint)
        if result["status"] == "SUCCEEDED":
            audit_execution_ledger(result)
        checked = reconcile_result(result, expected_dates=[day for day in prepared.calendar
                                    if pd.Timestamp(spec["start"]) <= day <= pd.Timestamp(spec["end"])])
        files = _save_result(out / "runs" / run_id, result)
        item = {"run_id": run_id, **spec, "status": result["status"], "ledger_check": checked,
                "result_label": cohort["result_label"],
                "issues": result["issues"], "seconds": round(time.monotonic() - started, 3), "files": files}
        if checked["status"] == "PASS":
            item["metrics"] = calculate_metrics(result)
            item["metrics"]["total_taxes"] = float(result["fills"]["tax"].sum())
            account = result["equity"]
            item["metrics"]["average_exposure_fraction"] = float(
                (account["exposure"].astype(float) / account["equity"].astype(float)).mean())
        if summary["code_hash"] != source_hash():
            summary["status"] = "INTERRUPTED_CODE_CHANGED"
            write_json(out / "summary.json", summary)
            raise ValueError("CODE_CHANGED_DURING_SLOT")
        write_json(out / "runs" / run_id / "result.json", item)
        summary["results"].append(item)
        write_json(out / "progress.json", {"attempted": completed_index + 1, "planned": len(selected), "latest": run_id})
        if (completed_index + 1) % 25 == 0:
            write_json(out / "summary.json", summary)
        print(f"{completed_index+1}/{len(selected)} {spec['family']} {spec['strategy_id']} {spec['phase']} {item['status']} {item['seconds']}s", flush=True)
    summary["status"] = "COMPLETE" if len(summary["results"]) == len(selected) else "PARTIAL"
    summary["attempted_runs"] = len(summary["results"])
    summary["succeeded_runs"] = sum(row["status"] == "SUCCEEDED" for row in summary["results"])
    summary["blocked_runs"] = sum(row["status"] == "BLOCKED" for row in summary["results"])
    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    write_json(out / "summary.json", summary)
    return summary
