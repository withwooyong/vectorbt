"""실험 계획·실행·검증·선정. 기본 경로는 데이터 인수 실패 시 성과를 만들지 않는다."""

from collections import Counter
from importlib.metadata import version
from pathlib import Path
import time
import traceback

import pandas as pd
import psutil

from .config import load_config, primary_runs
from .io import canonical_hash, digest, read_json, source_hash, write_json
from .registry import Registry, now, worker_lock
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
    directory = Path(directory)
    artifacts = read_json(directory / "artifacts.json")
    for item in artifacts["files"]:
        path = directory / item["file"]
        if path.parent.resolve() != directory.resolve() or digest(path) != item["sha256"]:
            raise ValueError("CORRUPT_ARTIFACT")


def save_result(directory, result, metrics, reconciliation):
    from .metrics import monthly_stats
    directory = Path(directory)
    temp = directory.with_name(directory.name + ".partial")
    temp.mkdir(parents=True, exist_ok=False)
    files = []
    for name, value in {**result, "monthly": monthly_stats(result)}.items():
        if isinstance(value, pd.DataFrame):
            path = temp / f"{name}.parquet"
            value.to_parquet(path, index=False)
            files.append({"file": path.name, "rows": len(value), "sha256": digest(path)})
    for name, value in (("metrics", metrics), ("issues", result["issues"]), ("reconciliation", reconciliation)):
        path = temp / f"{name}.json"
        write_json(path, value)
        files.append({"file": path.name, "sha256": digest(path)})
    write_json(temp / "artifacts.json", {"complete": True, "files": files})
    verify_artifacts(temp)
    temp.rename(directory)


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


def run(out, phases=("development", "validation"), limit=None):
    out = Path(out).resolve()
    if set(phases) - {"development", "validation"}:
        raise ValueError("후속 단계는 적격 후보 및 원가격·기업행사·현실 비용 인수 후 활성화됩니다")
    with worker_lock(out):
        experiment = verify_experiment(out)
        config, quality = experiment["config"], experiment["quality"]
        registry = Registry(out / "registry.sqlite")
        registry.recover()
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
            update_report(out)
            return status(out)
        if quality["grade"] != "SYNTHETIC":
            # Adjusted whole-share quantities cannot be passed off as raw-price quantities.
            registry.block_many(pending, "ADJUSTED_SHARE_MODEL_NOT_VALIDATED")
            update_report(out)
            return status(out)
        if limit is not None:
            pending = pending[:limit]
        if not pending:
            update_report(out)
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
            try:
                start = max(spec["start"], str(sorted(prices["date"].unique())[250])[:10])
                # Signals remain available before the fold for first-session entries.
                result = simulate(prices, signals, entry_id=spec["entry_id"], exit_id=spec["exit_id"],
                                  start=start, end=spec["end"], cost_bps=spec["cost_bps"], delay=spec["delay"],
                                  initial_cash=config["initial_cash_krw"], policy=spec["policy"],
                                  calendar=snapshot.get("calendar"))
                reconciliation = reconcile(result, config["initial_cash_krw"])
                if not reconciliation.get("ok"):
                    raise ValueError("VECTORBT_LEDGER_MISMATCH: " + str(reconciliation.get("mismatches")))
                metrics = calculate_metrics(result, config["initial_cash_krw"])
                metrics.update(elapsed_seconds=time.perf_counter() - started,
                               rss_bytes=psutil.Process().memory_info().rss)
                save_result(out / relative, result, metrics, reconciliation)
                registry.finish(spec["run_id"], "SUCCEEDED", metrics=metrics, artifacts=relative)
            except Exception as exc:
                error_dir = out / relative.parent / f"attempt-{attempt:03d}-failure"
                error_dir.mkdir(exist_ok=False)
                (error_dir / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
                registry.finish(spec["run_id"], "FAILED", reason=f"{type(exc).__name__}: {exc}",
                                artifacts=error_dir.relative_to(out))
            print(f"{index + 1}/{len(pending)} {spec['strategy_id']} {spec['phase']} {spec.get('year')}", flush=True)
        update_report(out)
        return status(out)


def status(out):
    records = Registry(Path(out) / "registry.sqlite").records()
    return {"experiment": str(Path(out).resolve()), "total": len(records),
            "statuses": dict(Counter(row["status"] for row in records))}


def update_report(out):
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
