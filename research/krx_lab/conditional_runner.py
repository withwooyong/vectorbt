"""합성 전용 후속 33슬롯: 실제 연구의 잠금 해제를 수행하지 않는다."""

from collections import Counter
import html
from pathlib import Path
import traceback

import pandas as pd

from .admission import inspect_delivery
from .contracts import CooperativeStop, ExecutionHooks, validate_delivery
from .io import canonical_hash, digest, read_json, source_hash, write_json
from .lifecycle import read_lifecycle
from .registry import Registry, worker_lock
from .resources import ResourceLimits, ResourceMonitor


def _inputs(paths, lifecycle_path, benchmark_id):
    # Reject a real delivery before loading signals or accessing a market source.
    delivery = validate_delivery(read_json(paths["delivery"]))
    if delivery["source_kind"] != "SYNTHETIC":
        raise ValueError("REAL_EXECUTION_NOT_ADMITTED")
    admission = inspect_delivery(delivery, Path(paths["delivery"]).parent)
    if admission["grade"] != "SYNTHETIC" or admission["issues"]:
        raise ValueError("DELIVERY_INSPECTION_BLOCKED")
    evidence = read_lifecycle(lifecycle_path)
    if evidence["source_kind"] != "SYNTHETIC" or evidence["state"] != "FROZEN":
        raise ValueError("SYNTHETIC_FROZEN_CANDIDATE_REQUIRED")
    if digest(paths["delivery"]) != evidence["data_hash"]:
        raise ValueError("FROZEN_DATA_MISMATCH")
    root = Path(evidence["artifact_root"])
    code = read_json(root / evidence["artifacts"]["code"]["file"])
    if code.get("source_hash") != source_hash():
        raise ValueError("CODE_CHANGED")
    costs = read_json(root / evidence["artifacts"]["cost_profile"]["file"])
    if costs.get("market_profiles") != delivery["market_profiles"]:
        raise ValueError("FROZEN_COST_PROFILE_MISMATCH")
    if benchmark_id not in {row["instrument_id"] for row in delivery["instruments"]}:
        raise ValueError("TRADABLE_BENCHMARK_REQUIRED")
    signals = pd.DataFrame(read_json(paths["signals"]))
    if signals.empty or "date" not in signals:
        raise ValueError("SYNTHETIC_SIGNALS_REQUIRED")
    dates = pd.to_datetime(signals["date"], errors="coerce")
    if dates.isna().any() or not dates.lt("2024-01-01").all():
        raise ValueError("HOLDOUT_LOCKED")
    from .conditional_plan import build_slots
    slots = build_slots(evidence["candidate_id"], evidence["growth_policy"], read_json(paths["windows"]))
    for spec in slots:
        if not (delivery["metadata"]["start"] <= spec["start"] <= spec["end"] <= delivery["metadata"]["end"]):
            raise ValueError("DELIVERY_EXECUTION_RANGE_INVALID")
        spec.update(benchmark_id=benchmark_id, data_grade="SYNTHETIC", source_kind="SYNTHETIC")
    return delivery, signals, evidence, slots


def plan_conditional(delivery, signals, windows, lifecycle, out, *, benchmark_id, resource_limits=None):
    """Freeze the synthetic execution inputs in a new, separate experiment."""
    paths = {name: str(Path(path).resolve()) for name, path in
             (("delivery", delivery), ("signals", signals), ("windows", windows))}
    lifecycle = str(Path(lifecycle).resolve())
    checked, _, evidence, slots = _inputs(paths, lifecycle, benchmark_id)
    limits = ResourceLimits(**(resource_limits if resource_limits is not None else {
        "max_rss_bytes": 2 * 1024**3, "min_free_disk_bytes": 512 * 1024**2, "poll_interval_seconds": 0.25}))
    manifest = {"schema_version": "synthetic-conditional-v1", "source_kind": "SYNTHETIC",
                "paths": paths, "hashes": {name: digest(path) for name, path in paths.items()},
                "lifecycle": lifecycle, "frozen_hash": evidence["frozen_hash"], "code_hash": source_hash(),
                "benchmark_id": benchmark_id, "initial_cash": 100_000_000, "slots": slots,
                "dataset_id": checked["metadata"]["dataset_id"], "revision": checked["metadata"]["revision"],
                "resource_limits": limits.asdict(), "real_holdout_opened": False}
    manifest["experiment_id"] = canonical_hash(manifest)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "conditional.json", manifest)
    registry = Registry(out / "registry.sqlite")
    registry.add_many([(canonical_hash({"experiment": manifest["experiment_id"], "spec": spec})[:24], spec,
                        "BLOCKED" if spec["requires_holdout"] else "PLANNED",
                        "SYNTHETIC_PRECHECKS_PENDING" if spec["requires_holdout"] else None) for spec in slots])
    return _report(out, manifest, registry.records())


def _verify(out):
    manifest = read_json(out / "conditional.json")
    identity = {key: value for key, value in manifest.items() if key != "experiment_id"}
    if (manifest.get("schema_version") != "synthetic-conditional-v1"
            or manifest.get("source_kind") != "SYNTHETIC" or manifest.get("real_holdout_opened") is not False
            or canonical_hash(identity) != manifest.get("experiment_id")):
        raise ValueError("CONDITIONAL_MANIFEST_CHANGED")
    if manifest["code_hash"] != source_hash():
        raise ValueError("CODE_CHANGED")
    for name, path in manifest["paths"].items():
        if digest(path) != manifest["hashes"][name]:
            raise ValueError("INPUT_CHANGED: " + name)
    delivery, signals, evidence, slots = _inputs(manifest["paths"], manifest["lifecycle"], manifest["benchmark_id"])
    if evidence["frozen_hash"] != manifest["frozen_hash"] or slots != manifest["slots"]:
        raise ValueError("FROZEN_BINDING_CHANGED")
    if any(manifest[key] != delivery["metadata"][key] for key in ("dataset_id", "revision")):
        raise ValueError("FROZEN_DATA_MISMATCH")
    records = Registry(out / "registry.sqlite").records()
    expected = {canonical_hash({"experiment": manifest["experiment_id"], "spec": spec})[:24]: spec for spec in slots}
    if len(records) != 33 or {r["run_id"] for r in records} != set(expected):
        raise ValueError("CONDITIONAL_REGISTRY_CHANGED")
    for record in records:
        if any(record.get(k) != v for k, v in expected[record["run_id"]].items()):
            raise ValueError("CONDITIONAL_REGISTRY_CHANGED")
    return manifest, delivery, signals


def _check_result(out, record, manifest):
    from .runner import verify_artifacts
    from .vectorbt_check import reconcile_ledger
    directory = (out / record["artifacts"]).resolve()
    if not directory.is_relative_to(out.resolve()):
        raise ValueError("ARTIFACT_PATH_INVALID")
    verify_artifacts(directory)
    if "contract_ledger.json" not in {item["file"] for item in read_json(directory / "artifacts.json")["files"]}:
        raise ValueError("UNHASHED_CONTRACT_LEDGER")
    ledger = read_json(directory / "contract_ledger.json")
    if ledger["run_id"] != record["run_id"] or ledger["source_kind"] != "SYNTHETIC":
        raise ValueError("LEDGER_BINDING_MISMATCH")
    fields = ("phase", "conditional_slot", "strategy_id", "entry_id", "exit_id", "policy", "period",
              "start", "end", "cost_bps", "delay", "optimistic", "control", "requires_holdout", "benchmark_id")
    expected = {key: record[key] for key in fields}
    expected.update(growth_policy=record["policy"], dataset_id=manifest["dataset_id"], revision=manifest["revision"],
                    initial_cash=manifest["initial_cash"],
                    cost_model="delivery_profiles" if record["phase"] == "realistic-costs" else "aggregate_bps_per_side")
    if (any(ledger.get(key) != value for key, value in expected.items()) or not ledger["equity"]
            or any(not record["start"] <= row["date"] <= record["end"] for section in
                   ("orders", "fills", "events", "cashflows", "positions", "equity") for row in ledger[section])):
        raise ValueError("LEDGER_SLOT_MISMATCH")
    if read_json(directory / "metrics.json") != record["metrics"]:
        raise ValueError("REGISTRY_METRICS_MISMATCH")
    if ledger["issues"] or not reconcile_ledger(ledger)["ok"]:
        raise ValueError("UNRESOLVED_LEDGER_ISSUES")


def _report(out, manifest, records):
    complete = len(records) == 33 and all(r["status"] == "SUCCEEDED" for r in records)
    report = {"source_kind": "SYNTHETIC", "status": "SYNTHETIC_VERIFIED" if complete else "INCOMPLETE",
              "experiment_id": manifest["experiment_id"], "total": 33,
              "statuses": dict(Counter(r["status"] for r in records)), "real_holdout_opened": False,
              "frozen_candidate": manifest["slots"][0]["strategy_id"],
              "selection": "NOT_A_REAL_SELECTION", "runs": records,
              "limitations": ["SYNTHETIC_WINDOWS_ONLY", "SYNTHETIC_COST_PROFILE_ONLY",
                              "FROZEN_POLICY_NOT_RESELECTED", "NO_PRIMARY_RUN_REUSE"]}
    write_json(out / "conditional-report.json", report)
    rows = []
    for r in records:
        artifact = r.get("artifacts")
        link = "-"
        if artifact and r["status"] == "SUCCEEDED":
            href = str(Path(artifact) / "detail-report.html").replace("\\", "/")
            link = f'<a href="{html.escape(href, quote=True)}">상세 장부</a>'
        metrics = r.get("metrics") or {}
        def percentage(key):
            value = metrics.get(key)
            return "-" if value is None else f"{value:.2%}"
        cells = [r["phase"], r["period"], f'{r["start"]}~{r["end"]}', r["policy"] or "-",
                 r.get("control") or "strategy", "합성 프로필" if r["cost_bps"] is None else f'{r["cost_bps"]}bp',
                 r["delay"], percentage("total_return"), percentage("max_drawdown"),
                 r["status"], r.get("reason") or "-"]
        rows.append("<tr>" + "".join(f"<td>{html.escape(str(x))}</td>" for x in cells) + f"<td>{link}</td></tr>")
    page = ('<!doctype html><html lang="ko"><meta charset="utf-8"><title>합성 후속 실행</title>'
            '<style>body{font-family:sans-serif;margin:2rem}td,th{padding:.5rem;border:1px solid #ddd}'
            'table{border-collapse:collapse}td{overflow-wrap:anywhere}</style><h1>합성 후속 33슬롯</h1>'
            '<p>실제 전략 선정·수익성 검증 결과가 아닙니다. 실제 잠금 자료는 열지 않았습니다.</p>'
            f'<p>{html.escape(report["status"])} · {report["statuses"].get("SUCCEEDED", 0)}/33 실행 성공</p>'
            '<table><tr><th>단계</th><th>합성 구간</th><th>합성 날짜</th><th>정책</th><th>비교</th>'
            '<th>편도 비용</th><th>지연</th><th>합성 수익률</th><th>최대낙폭</th><th>상태</th>'
            '<th>사유</th><th>장부</th></tr>' + "".join(rows) + '</table></html>')
    (out / "conditional-report.html").write_text(page, encoding="utf-8")
    return {key: value for key, value in report.items() if key != "runs"}


def run_conditional(out, *, include_synthetic_holdout=False, limit=None, hooks=None):
    """Resume verified synthetic attempts; real data and dates remain prohibited."""
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
        raise ValueError("LIMIT_MUST_BE_POSITIVE_INTEGER")
    out = Path(out).resolve()
    with worker_lock(out):
        manifest, delivery, signals = _verify(out)
        registry = Registry(out / "registry.sqlite")
        registry.recover()
        for row in registry.records():
            if row["status"] == "SUCCEEDED":
                try:
                    _check_result(out, row, manifest)
                except (ValueError, OSError, KeyError, TypeError) as exc:
                    registry.finish(row["run_id"], "CORRUPT", reason=str(exc), artifacts=row["artifacts"])
        from .conditional_execution import simulate_slot
        from .metrics import calculate_metrics
        from .runner import save_result
        from .vectorbt_check import reconcile_ledger
        with ResourceMonitor(out, ResourceLimits(**manifest["resource_limits"])) as monitor:
            user_hooks = hooks or ExecutionHooks()
            def checkpoint(stage, context):
                monitor.checkpoint(stage, context)
                user_hooks(stage, context)
            active_hooks = ExecutionHooks(checkpoint=checkpoint)
            try:
                active_hooks("resume", {"experiment": str(out)})
            except CooperativeStop as exc:
                return {**_report(out, manifest, registry.records()), "stop_reason": exc.reason,
                        "resources": monitor.telemetry}
            executed = 0
            # Two waves ensure holdout slots cannot slip through ahead of prechecks.
            for hidden in (False, True):
                if hidden and not include_synthetic_holdout:
                    break
                rows = registry.records()
                if hidden and any(r["status"] != "SUCCEEDED" for r in rows if not r["requires_holdout"]):
                    break
                if hidden:
                    _verify(out)
                    for row in rows:
                        if not row["requires_holdout"]:
                            _check_result(out, row, manifest)
                for row in rows:
                    if row["requires_holdout"] != hidden or row["status"] not in {"PLANNED", "FAILED", "INTERRUPTED", "BLOCKED"}:
                        continue
                    if limit is not None and executed >= limit:
                        return _report(out, manifest, registry.records())
                    attempt = registry.begin(row["run_id"])
                    relative = Path("runs") / row["run_id"] / f"attempt-{attempt:03d}"
                    committed = False
                    try:
                        active_hooks("run_start", {"run_id": row["run_id"], "attempt": attempt})
                        slot = next(s for s in manifest["slots"] if s["phase"] == row["phase"]
                                    and s["conditional_slot"] == row["conditional_slot"])
                        result = simulate_slot(delivery, signals, slot, initial_cash=manifest["initial_cash"],
                                               hooks=active_hooks, run_id=row["run_id"])
                        reconciliation = reconcile_ledger(result["contract_ledger"])
                        if result["issues"] or not reconciliation["ok"]:
                            raise ValueError("UNRESOLVED_LEDGER_ISSUES: " + str(result["issues"]))
                        metrics = calculate_metrics(result, manifest["initial_cash"])
                        metrics["resources"] = monitor.telemetry
                        save_result(out / relative, result, metrics, reconciliation, hooks=active_hooks,
                                    initial_cash=manifest["initial_cash"],
                                    manifest={"source_kind": "SYNTHETIC", "input": manifest, "slot": row})
                        active_hooks("before_registry_commit", {"run_id": row["run_id"]})
                        registry.finish(row["run_id"], "SUCCEEDED", metrics=metrics, artifacts=relative)
                        committed = True
                        active_hooks("after_registry_commit", {"run_id": row["run_id"]})
                    except CooperativeStop as exc:
                        if not committed:
                            registry.finish(row["run_id"], "INTERRUPTED", reason=exc.reason, artifacts=relative)
                        return {**_report(out, manifest, registry.records()), "stop_reason": exc.reason,
                                "resources": monitor.telemetry}
                    except Exception as exc:
                        if committed:
                            raise
                        failure = out / relative.with_name(relative.name + "-failure")
                        failure.mkdir(parents=True, exist_ok=False)
                        reason = f"{type(exc).__name__}: {exc}"
                        (failure / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
                        write_json(failure / "failure.json", {"status": "FAILED", "run_id": row["run_id"],
                                   "attempt": attempt, "reason": reason, "source_kind": "SYNTHETIC",
                                   "experiment_id": manifest["experiment_id"], "slot": row,
                                   "traceback_sha256": digest(failure / "traceback.txt")})
                        registry.finish(row["run_id"], "FAILED", reason=reason, artifacts=failure.relative_to(out))
                    executed += 1
        return _report(out, manifest, registry.records())


def conditional_status(out):
    """Verify saved input and result evidence before reporting completion."""
    out = Path(out).resolve()
    with worker_lock(out):
        manifest, _, _ = _verify(out)
        registry = Registry(out / "registry.sqlite")
        for row in registry.records():
            if row["status"] == "SUCCEEDED":
                _check_result(out, row, manifest)
        return _report(out, manifest, registry.records())
