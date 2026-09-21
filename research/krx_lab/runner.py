"""실험 계획·실행·검증·선정. 기본 경로는 데이터 인수 실패 시 성과를 만들지 않는다."""

from collections import Counter
from importlib.metadata import version
from pathlib import Path
import time
import traceback

import pandas as pd
import psutil

from .config import load_config, primary_runs
from .contracts import CooperativeStop, ExecutionHooks
from .io import canonical_hash, digest, read_json, source_hash, write_json
from .registry import Registry, now, worker_lock
from .resources import ResourceLimits, ResourceMonitor
from .snapshot import load_prices, verify_snapshot


def plan(config_path, out):
    config = load_config(config_path)
    manifest, quality = verify_snapshot(config["snapshot"])
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    experiment = {"created_at": now(), "config": config, "config_hash": canonical_hash(config),
                  "code_hash": source_hash(), "snapshot_hash": digest(Path(config["snapshot"]) / "manifest.json"),
                  "quality": quality, "versions": {k: version(k) for k in
                                                    ("vectorbt", "numpy", "pandas", "numba", "pyarrow")},
                  "holdout_opened": False, "implementation_stage": "RESEARCH_CORE_V1",
                  "limitations": ["EXECUTION_ELIGIBLE_ADMISSION_NOT_IMPLEMENTED",
                                   "REALISTIC_COST_AND_CORPORATE_ACTION_ENGINE_PENDING"],
                  "primary_slots": 816, "conditional_slots": 33, "logical_slots": 849}
    experiment["experiment_id"] = canonical_hash(experiment)[:20]
    write_json(out / "experiment.json", experiment)
    registry = Registry(out / "registry.sqlite")
    planned_rows = []
    for spec in primary_runs(config):
        spec["data_grade"] = quality["grade"]
        run_id = canonical_hash({"experiment": experiment["experiment_id"], "spec": spec})[:24]
        planned_rows.append((run_id, spec, "PLANNED", None))
    # Conditional slots stay explicit even when no primary candidate is eligible.
    conditional = []
    for phase, count in (("allocation", 8), ("holdout", 4), ("controls", 12),
                         ("realistic-costs", 5), ("ambiguity", 4)):
        for i in range(count):
            conditional.append({"phase": phase, "conditional_slot": i, "strategy_id": "UNASSIGNED",
                                "data_grade": quality["grade"]})
    for spec in conditional:
        run_id = canonical_hash({"experiment": experiment["experiment_id"], "spec": spec})[:24]
        reason = "HOLDOUT_LOCKED" if spec["phase"] == "holdout" else "REQUIRES_ELIGIBLE_FROZEN_CANDIDATE"
        if spec["phase"] == "controls":
            reason = "TRADABLE_BENCHMARK_AND_CORPORATE_ACTION_PROFILE_REQUIRED"
        planned_rows.append((run_id, spec, "BLOCKED", reason))
    registry.add_many(planned_rows)
    update_report(out)
    return experiment


def verify_experiment(out):
    out = Path(out)
    experiment = read_json(out / "experiment.json")
    if experiment["code_hash"] != source_hash():
        raise ValueError("CODE_CHANGED: 코드를 바꾼 뒤에는 새 실험을 생성하십시오")
    if experiment["config_hash"] != canonical_hash(experiment["config"]):
        raise ValueError("CONFIG_CHANGED: 기존 실험 설정을 고칠 수 없습니다")
    if digest(Path(experiment["config"]["snapshot"]) / "manifest.json") != experiment["snapshot_hash"]:
        raise ValueError("DATA_CHANGED: 새 실험을 생성하십시오")
    for name, saved in experiment["versions"].items():
        if version(name) != saved:
            raise ValueError(f"ENVIRONMENT_CHANGED: {name}")
    verify_snapshot(experiment["config"]["snapshot"])
    return experiment


def verify_artifacts(directory):
    directory = Path(directory).resolve()
    artifacts = read_json(directory / "artifacts.json")
    if artifacts.get("complete") is not True or not isinstance(artifacts.get("files"), list):
        raise ValueError("CORRUPT_ARTIFACT_MANIFEST")
    seen = set()
    for item in artifacts["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("file"), str):
            raise ValueError("CORRUPT_ARTIFACT_MANIFEST")
        name = item["file"]
        path = directory / name
        if (name in seen or Path(name).name != name or path.resolve().parent != directory
                or not path.is_file() or digest(path) != item.get("sha256")):
            raise ValueError("CORRUPT_ARTIFACT")
        seen.add(name)
    required = {"fills.parquet", "positions.parquet", "equity.parquet", "metrics.json",
                "issues.json", "reconciliation.json"}
    if not required.issubset(seen):
        raise ValueError("CORRUPT_ARTIFACT_MISSING_FILES")


def save_result(directory, result, metrics, reconciliation, *, hooks=None, initial_cash=100_000_000, manifest=None):
    from .metrics import monthly_stats
    hooks = hooks or ExecutionHooks()
    hooks("before_artifacts", {"directory": str(directory)})
    directory = Path(directory)
    temp = directory.with_name(directory.name + ".partial")
    temp.mkdir(parents=True, exist_ok=False)
    files = []
    for name, value in {**result, "monthly": monthly_stats(result, initial_cash)}.items():
        if isinstance(value, pd.DataFrame):
            path = temp / f"{name}.parquet"
            value.to_parquet(path, index=False)
            files.append({"file": path.name, "rows": len(value), "sha256": digest(path)})
    json_results = {"metrics": metrics, "issues": result["issues"], "reconciliation": reconciliation}
    if "contract_ledger" in result:
        json_results["contract_ledger"] = result["contract_ledger"]
    for name, value in json_results.items():
        path = temp / f"{name}.json"
        write_json(path, value)
        files.append({"file": path.name, "sha256": digest(path)})
    from .report import write_detail_report
    report_result = dict(result)
    report_result.setdefault("source_kind", (manifest or {}).get("source_kind", "UNKNOWN"))
    write_detail_report(temp, report_result, initial_cash=initial_cash,
                        manifest={**(manifest or {}), "artifacts": list(files)})
    files.append({"file": "detail-report.html", "sha256": digest(temp / "detail-report.html")})
    write_json(temp / "artifacts.json", {"complete": True, "files": files})
    verify_artifacts(temp)
    hooks("after_artifacts", {"directory": str(temp)})
    hooks("before_rename", {"directory": str(temp)})
    temp.rename(directory)
    hooks("after_rename", {"directory": str(directory)})


def _prepare_signals(prices):
    from .strategies import build_signals
    # Preserve the observed session axis; missing rows remain NaN, never compressed into adjacent days.
    sessions = sorted(prices["date"].unique())
    frames = []
    for code, group in prices.groupby("code", observed=True, sort=True):
        aligned = group.set_index("date").reindex(sessions)
        aligned["code"] = code
        aligned.index.name = "date"
        frames.append(build_signals(aligned.reset_index()))
    return pd.concat(frames, ignore_index=True)


def run(out, phases=("development", "validation"), limit=None, *, hooks=None):
    out = Path(out).resolve()
    hooks = hooks or ExecutionHooks()
    if set(phases) - {"development", "validation"}:
        raise ValueError("후속 단계는 적격 후보 및 원가격·기업행사·현실 비용 인수 후 활성화됩니다")
    with worker_lock(out):
        experiment = verify_experiment(out)
        config, quality = experiment["config"], experiment["quality"]
        with ResourceMonitor(out, ResourceLimits(**config.get("resource_limits", {}))) as monitor:
            user_hooks = hooks
            def checkpoint(stage, context):
                monitor.checkpoint(stage, context)
                user_hooks(stage, context)
            hooks = ExecutionHooks(checkpoint=checkpoint)
            registry = Registry(out / "registry.sqlite")
            registry.recover()
            try:
                hooks("resume", {"experiment": str(out)})
            except CooperativeStop as exc:
                return {**status(out), "stop_reason": exc.reason, "resources": monitor.telemetry}
            for record in registry.records():
                if record["status"] == "SUCCEEDED":
                    try:
                        verify_artifacts(out / record["artifacts"])
                    except (ValueError, OSError) as exc:
                        registry.finish(record["run_id"], "CORRUPT", reason=str(exc))
            pending = [r for r in registry.records() if r["phase"] in phases and
                       r["status"] in {"PLANNED", "FAILED", "INTERRUPTED"}]
            if quality["grade"] == "BLOCKED":
                reason = ",".join(quality["reasons"])
                registry.block_many(pending, reason)
                _update_report(out)
                return status(out)
            if quality["grade"] != "SYNTHETIC":
                # Adjusted whole-share quantities cannot be passed off as raw-price quantities.
                registry.block_many(pending, "ADJUSTED_SHARE_MODEL_NOT_VALIDATED")
                _update_report(out)
                return status(out)
            if limit is not None:
                pending = pending[:limit]
            if not pending:
                _update_report(out)
                return status(out)
            from .execution import simulate
            from .metrics import calculate_metrics
            from .vectorbt_check import reconcile
            prices = load_prices(config["snapshot"], end="2023-12-31")
            cache = out / "signals-cache.parquet"
            receipt = out / "signals-cache.json"
            if cache.exists() and receipt.exists():
                if digest(cache) != read_json(receipt)["sha256"]:
                    raise ValueError("SIGNAL_CACHE_CORRUPT")
                signals = pd.read_parquet(cache)
            else:
                signals = _prepare_signals(prices)
                signals.to_parquet(cache, index=False)
                write_json(receipt, {"sha256": digest(cache), "rows": len(signals)})
            snapshot = read_json(Path(config["snapshot"]) / "manifest.json")
            for index, spec in enumerate(pending):
                attempt = registry.begin(spec["run_id"])
                started = time.perf_counter()
                relative = Path("runs") / spec["run_id"] / f"attempt-{attempt:03d}"
                (out / relative).parent.mkdir(parents=True, exist_ok=True)
                committed = False
                try:
                    hooks("run_start", {"run_id": spec["run_id"], "attempt": attempt})
                    start = max(spec["start"], str(sorted(prices["date"].unique())[250])[:10])
                    # Signals remain available before the fold for first-session entries.
                    result = simulate(prices, signals, entry_id=spec["entry_id"], exit_id=spec["exit_id"],
                                      start=start, end=spec["end"], cost_bps=spec["cost_bps"], delay=spec["delay"],
                                      initial_cash=config["initial_cash_krw"], policy=spec["policy"],
                                      calendar=snapshot.get("calendar"), hooks=hooks)
                    reconciliation = reconcile(result, config["initial_cash_krw"])
                    if not reconciliation.get("ok"):
                        raise ValueError("VECTORBT_LEDGER_MISMATCH: " + str(reconciliation.get("mismatches")))
                    metrics = calculate_metrics(result, config["initial_cash_krw"])
                    metrics.update(elapsed_seconds=time.perf_counter() - started,
                                   rss_bytes=psutil.Process().memory_info().rss)
                    metrics["resources"] = monitor.telemetry
                    save_result(out / relative, result, metrics, reconciliation, hooks=hooks,
                                manifest={"source_kind": "SYNTHETIC", "source": "../../../experiment.json",
                                          "experiment_id": experiment["experiment_id"], "run_id": spec["run_id"],
                                          "snapshot_hash": experiment["snapshot_hash"], "code_hash": experiment["code_hash"]})
                    hooks("before_registry_commit", {"run_id": spec["run_id"]})
                    registry.finish(spec["run_id"], "SUCCEEDED", metrics=metrics, artifacts=relative)
                    committed = True
                    hooks("after_registry_commit", {"run_id": spec["run_id"]})
                except CooperativeStop as exc:
                    if committed:
                        break
                    registry.finish(spec["run_id"], "INTERRUPTED", reason=exc.reason, artifacts=relative)
                    break
                except Exception as exc:
                    if committed:
                        raise
                    error_dir = out / relative.parent / f"attempt-{attempt:03d}-failure"
                    error_dir.mkdir(exist_ok=False)
                    (error_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
                    registry.finish(spec["run_id"], "FAILED", reason=f"{type(exc).__name__}: {exc}",
                                    artifacts=error_dir.relative_to(out))
                print(f"{index + 1}/{len(pending)} {spec['strategy_id']} {spec['phase']} {spec.get('year')}", flush=True)
            _update_report(out)
            return status(out)


def status(out):
    records = Registry(Path(out) / "registry.sqlite").records()
    return {"experiment": str(Path(out).resolve()), "total": len(records),
            "statuses": dict(Counter(row["status"] for row in records))}


def update_report(out):
    """Verify and render under the same lock used by execution and recovery."""
    with worker_lock(out):
        verify_experiment(out)
        return _update_report(out)


def _update_report(out):
    """Caller owns the experiment lock; artifact corruption may update registry."""
    from .selection import select_candidate
    from .report import write_report
    out = Path(out)
    registry = Registry(out / "registry.sqlite")
    for record in registry.records():
        if record["status"] == "SUCCEEDED":
            try:
                directory = out / record["artifacts"]
                verify_artifacts(directory)
                if read_json(directory / "metrics.json") != record["metrics"]:
                    raise ValueError("REGISTRY_METRICS_MISMATCH")
            except (TypeError, OSError, ValueError) as exc:
                registry.finish(record["run_id"], "CORRUPT", reason=str(exc))
    records = registry.records()
    selection = select_candidate(records)
    write_json(out / "selection.json", selection)
    write_report(out, records, selection)
    return selection


def freeze(out, *, evidence_path=None, bindings_path=None, artifact_root=None, attempt_id="freeze"):
    """Exercise persisted lifecycle with synthetic evidence; never open holdout."""
    from .lifecycle import initialize_lifecycle, freeze_lifecycle
    out = Path(out).resolve()
    with worker_lock(out):
        experiment = verify_experiment(out)
        if experiment["quality"]["grade"] != "SYNTHETIC":
            raise ValueError("REAL_LIFECYCLE_DISABLED")
        directory = out / "lifecycle"
        if evidence_path is not None:
            if bindings_path is None or artifact_root is None:
                raise ValueError("LIFECYCLE_BINDINGS_REQUIRED")
            evidence = read_json(evidence_path)
            if evidence["experiment_id"] != experiment["experiment_id"]:
                raise ValueError("LIFECYCLE_EXPERIMENT_MISMATCH")
            bindings = read_json(bindings_path)
            root = Path(artifact_root).resolve()
            code_path = (root / bindings["code"]).resolve()
            if not code_path.is_relative_to(root):
                raise ValueError("UNSAFE_ARTIFACT_PATH")
            if read_json(code_path).get("source_hash") != experiment["code_hash"]:
                raise ValueError("CODE_CHANGED")
            initialize_lifecycle(directory, evidence, artifact_root=root, artifacts=bindings,
                                 attempt_id=f"{attempt_id}:initialize")
        return freeze_lifecycle(directory, attempt_id=attempt_id)


def finalize(out, result_path, *, attempt_id="finalize"):
    from .lifecycle import finalize_lifecycle
    out = Path(out).resolve()
    with worker_lock(out):
        experiment = verify_experiment(out)
        if experiment["quality"]["grade"] != "SYNTHETIC":
            raise ValueError("REAL_LIFECYCLE_DISABLED")
        return finalize_lifecycle(out / "lifecycle", result_path, attempt_id=attempt_id)


def inspect_delivery_file(delivery_path, *, root=None, previous_path=None):
    from .admission import inspect_delivery
    delivery_path = Path(delivery_path).resolve()
    return inspect_delivery(read_json(delivery_path), Path(root).resolve() if root else delivery_path.parent,
                            read_json(previous_path) if previous_path else None)


def run_delivery(delivery_path, signals_path, out, *, entry_id, exit_id, start, end,
                 initial_cash=100_000_000, root=None, previous_path=None, hooks=None, resource_limits=None):
    """Run an explicitly synthetic C1 delivery with read-only source inspection."""
    from .execution import simulate_delivery
    from .metrics import calculate_metrics
    from .vectorbt_check import reconcile_ledger
    from .contracts import validate_delivery
    delivery_path, signals_path = Path(delivery_path).resolve(), Path(signals_path).resolve()
    delivery = validate_delivery(read_json(delivery_path))
    if delivery["source_kind"] != "SYNTHETIC":
        raise ValueError("REAL_EXECUTION_NOT_ADMITTED")
    if not (delivery["metadata"]["start"] <= start <= end <= delivery["metadata"]["end"] < "2024-01-01"):
        raise ValueError("DELIVERY_EXECUTION_RANGE_INVALID")
    admission = inspect_delivery_file(delivery_path, root=root, previous_path=previous_path)
    if admission["grade"] != "SYNTHETIC":
        raise ValueError("DELIVERY_INSPECTION_BLOCKED: " + str(admission["issues"]))
    signals = pd.DataFrame(read_json(signals_path))
    if signals.empty or "date" not in signals or not pd.to_datetime(signals["date"]).lt("2024-01-01").all():
        raise ValueError("SYNTHETIC_SIGNAL_RANGE_INVALID")
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    hooks = hooks or ExecutionHooks()
    inputs = {"delivery_sha256": digest(delivery_path), "signals_sha256": digest(signals_path),
              "code_hash": source_hash(), "source_kind": "SYNTHETIC", "start": start, "end": end,
              "entry_id": entry_id, "exit_id": exit_id, "initial_cash": initial_cash,
              "dataset_id": delivery["metadata"]["dataset_id"], "revision": delivery["metadata"]["revision"]}
    run_id = canonical_hash(inputs)[:24]
    write_json(out / "input-manifest.json", inputs)
    write_json(out / "delivery.json", delivery)
    write_json(out / "signals.json", read_json(signals_path))
    write_json(out / "admission.json", admission)
    registry = Registry(out / "registry.sqlite")
    registry.add(run_id, {"phase": "synthetic-contract", "data_grade": "SYNTHETIC", **inputs})
    limits = ResourceLimits(**(resource_limits if resource_limits is not None else {
        "max_rss_bytes": 2 * 1024**3, "min_free_disk_bytes": 512 * 1024**2, "poll_interval_seconds": 0.25}))
    with worker_lock(out), ResourceMonitor(out, limits) as monitor:
        user_hooks = hooks
        def checkpoint(stage, context):
            monitor.checkpoint(stage, context)
            user_hooks(stage, context)
        hooks = ExecutionHooks(checkpoint=checkpoint)
        registry.begin(run_id)
        try:
            hooks("run_start", {"run_id": run_id})
            result = simulate_delivery(delivery, signals, entry_id=entry_id, exit_id=exit_id, start=start, end=end,
                                       initial_cash=initial_cash, hooks=hooks, run_id=run_id)
            reconciliation = reconcile_ledger(result["contract_ledger"])
            if not reconciliation["ok"]:
                raise ValueError("CONTRACT_LEDGER_MISMATCH: " + str(reconciliation["mismatches"]))
            metrics = calculate_metrics(result, initial_cash)
            metrics["resources"] = monitor.telemetry
            save_result(out / "result", result, metrics, reconciliation, hooks=hooks, initial_cash=initial_cash,
                        manifest={**inputs, "source": "../input-manifest.json", "sources": delivery["sources"],
                                  "events": delivery["events"], "prices": [{"instrument_id": row["instrument_id"],
                                  "date": row["date"], "source_id": row["source_id"]} for row in delivery["prices"]]})
            hooks("before_registry_commit", {"run_id": run_id})
            registry.finish(run_id, "SUCCEEDED", metrics=metrics, artifacts="result")
        except CooperativeStop as exc:
            registry.finish(run_id, "INTERRUPTED", reason=exc.reason)
            raise
        except Exception as exc:
            registry.finish(run_id, "FAILED", reason=f"{type(exc).__name__}: {exc}")
            raise
    return {"run_id": run_id, "status": "SUCCEEDED", "source_kind": "SYNTHETIC",
            "output": str(out), "reconciliation": reconciliation, "issues": result["issues"]}
