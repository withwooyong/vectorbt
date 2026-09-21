"""Fail-closed merger for separately executed v3 basic and wide batches."""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

from research.krx_lab.config_v2 import default_config, default_wide_config, primary_runs
from research.krx_lab.io import canonical_hash, digest, read_json, write_json


_SPEC = ("entry_id", "exit_id", "strategy_id", "policy", "sector_cap", "phase", "year", "start", "end", "cost_bps", "delay", "family", "cost_model")
_TABLES = ("signals", "plans", "orders", "fills", "positions", "equity", "trades", "cashflows", "events")


def _plan(family, config):
    runs = []
    for spec in primary_runs(config):
        runs.append({**spec, "family": family, "cost_model": "FLAT_BPS_STRESS_ONLY"})
    for spec in primary_runs(config):
        if spec["cost_bps"] == 30 and spec["delay"] == 1:
            runs.append({**spec, "cost_bps": None, "family": family, "cost_model": "DATED_V3_RULES"})
    return runs


def expected_plan():
    """Return the fixed 1,232 basic then 1,232 wide run specifications."""
    basic = _plan("basic", default_config("."))
    wide = _plan("wide", default_wide_config("."))
    if len(basic) != 1232 or len(wide) != 1232:
        raise ValueError("UNEXPECTED_V3_PLAN_SIZE")
    return basic, wide


def _seal(value):
    claimed = value.get("receipt_hash")
    body = dict(value)
    body.pop("receipt_hash", None)
    if not isinstance(claimed, str) or claimed != canonical_hash(body):
        raise ValueError("RECEIPT_SELF_HASH_MISMATCH")


def _artifact_hash(receipt_dir):
    artifacts = read_json(receipt_dir / "smoke" / "artifacts.json")
    if artifacts.get("status") != "SUCCEEDED":
        raise ValueError("SMOKE_ARTIFACT_NOT_SUCCEEDED")
    if set(artifacts.get("files", {})) != {name + ".parquet" for name in _TABLES}:
        raise ValueError("SMOKE_ARTIFACT_SET_MISMATCH")
    for name, expected in artifacts["files"].items():
        if digest(receipt_dir / "smoke" / name) != expected:
            raise ValueError("SMOKE_ARTIFACT_HASH_MISMATCH")
    return canonical_hash(artifacts["files"])


def _validate_receipt(parent, summary, runplan, calendar):
    smoke = read_json(parent / "smoke-oracle.json")
    if smoke.get("status") != "PASS":
        raise ValueError("SMOKE_NOT_PASSED")
    receipt = read_json(parent / "execution-admission.json")
    _seal(receipt)
    if receipt.get("schema_version") != "krx-real-execution-admission-v1" or receipt.get("decision") != "EXECUTION_ADMITTED":
        raise ValueError("EXECUTION_RECEIPT_NOT_ADMITTED")
    if (not receipt.get("data_admission_hash") or not receipt.get("manifest_hash")
            or receipt.get("checks") != {"CURRENT_NUMERICAL_ORACLE": "PASS", "SMALL_REAL_LEDGER_REPLAY": "PASS"}):
        raise ValueError("EXECUTION_RECEIPT_BINDING_INVALID")
    bindings = receipt.get("bindings") or {}
    if bindings.get("code_hash") != summary.get("code_hash"):
        raise ValueError("RECEIPT_CODE_HASH_MISMATCH")
    if bindings.get("ledger_hash") != _artifact_hash(parent):
        raise ValueError("RECEIPT_SMOKE_ARTIFACT_MISMATCH")
    if runplan.get("execution_receipt_hash") != receipt.get("receipt_hash"):
        raise ValueError("RUNPLAN_RECEIPT_MISMATCH")
    from research.krx_lab.v3_execution import audit_execution_ledger
    from research.krx_lab.v3_run import reconcile_result
    smoke_result = {"status": "SUCCEEDED", "issues": read_json(parent / "smoke" / "artifacts.json")["issues"],
                    "performance_valid": True, "initial_cash": 100_000_000}
    for name in _TABLES:
        smoke_result[name] = pd.read_parquet(parent / "smoke" / f"{name}.parquet")
    audit_execution_ledger(smoke_result)
    dates = [day for day in calendar if pd.Timestamp("2015-06-15") <= day <= pd.Timestamp("2015-12-31")]
    if reconcile_result(smoke_result, expected_dates=dates).get("status") != "PASS":
        raise ValueError("SMOKE_LEDGER_REPLAY_FAILED")
    return receipt


def _validate_result(parent, row, calendar=None):
    path = parent / "runs" / row["run_id"]
    actual = read_json(path / "result.json")
    if actual != row:
        raise ValueError("RESULT_SUMMARY_MISMATCH:" + row["run_id"])
    if row.get("status") == "BLOCKED" and "metrics" in row:
        raise ValueError("BLOCKED_RESULT_HAS_METRICS:" + row["run_id"])
    artifacts = read_json(path / "artifacts.json")
    if artifacts.get("status") != row.get("status") or artifacts.get("issues") != row.get("issues"):
        raise ValueError("RESULT_ARTIFACT_STATUS_MISMATCH:" + row["run_id"])
    if set(artifacts.get("files", {})) != {name + ".parquet" for name in _TABLES} or row.get("files") != artifacts["files"]:
        raise ValueError("RESULT_ARTIFACT_SET_MISMATCH:" + row["run_id"])
    for name, expected in artifacts["files"].items():
        if digest(path / name) != expected:
            raise ValueError("RESULT_ARTIFACT_HASH_MISMATCH:" + row["run_id"])
    if row.get("status") == "SUCCEEDED":
        if (row.get("ledger_check") or {}).get("status") != "PASS" or not row.get("metrics"):
            raise ValueError("SUCCEEDED_RESULT_UNVERIFIED:" + row["run_id"])
        from research.krx_lab.metrics import calculate_metrics
        from research.krx_lab.v3_execution import audit_execution_ledger
        from research.krx_lab.v3_run import reconcile_result
        result = {"status": row["status"], "issues": row["issues"], "performance_valid": True,
                  "initial_cash": 100_000_000}
        for name in _TABLES:
            result[name] = pd.read_parquet(path / f"{name}.parquet")
        audit_execution_ledger(result)
        if calendar is not None:
            expected_dates = [day for day in calendar if pd.Timestamp(row["start"]) <= day <= pd.Timestamp(row["end"])]
            if reconcile_result(result, expected_dates=expected_dates).get("status") != "PASS":
                raise ValueError("RESULT_LEDGER_REPLAY_FAILED:" + row["run_id"])
        metrics = calculate_metrics(result)
        metrics["total_taxes"] = float(result["fills"]["tax"].sum())
        equity = result["equity"]
        metrics["average_exposure_fraction"] = float((equity["exposure"].astype(float) / equity["equity"].astype(float)).mean())
        if set(row["metrics"]) != set(metrics):
            raise ValueError("RESULT_METRICS_FIELDS_MISMATCH:" + row["run_id"])
        for name, value in metrics.items():
            actual = row["metrics"][name]
            if isinstance(value, float) and isinstance(actual, (float, int)):
                equal = abs(value - actual) <= 1e-12
            else:
                equal = actual == value
            if not equal:
                raise ValueError("RESULT_METRICS_MISMATCH:" + row["run_id"] + ":" + name)
    elif row.get("status") == "BLOCKED":
        pass
    else:
        raise ValueError("UNSUPPORTED_RESULT_STATUS:" + row["run_id"])


def _validate_parent(parent, family, plan):
    summary, runplan = read_json(parent / "summary.json"), read_json(parent / "run-plan.json")
    config = read_json(parent / f"{family}-config.json")
    prepared = Path(config["snapshot"])
    from research.krx_lab.v3_run import verify_prepared
    prepared_manifest, prepared_cohort = verify_prepared(prepared)
    if digest(prepared / "manifest.json") != summary.get("prepared_manifest_hash"):
        raise ValueError("PREPARED_MANIFEST_MISMATCH:" + family)
    if summary.get("cohort") != prepared_cohort:
        raise ValueError("PREPARED_COHORT_MISMATCH:" + family)
    calendar_file = prepared_manifest.get("files", {}).get("calendar") or {}
    if digest(prepared / calendar_file.get("file", "")) != calendar_file.get("sha256"):
        raise ValueError("PREPARED_CALENDAR_HASH_MISMATCH:" + family)
    calendar = pd.to_datetime(pd.read_parquet(prepared / "calendar.parquet")["date"]).tolist()
    if summary.get("status") != "COMPLETE" or summary.get("planned_runs") != 1232 or len(summary.get("results") or []) != 1232:
        raise ValueError("PARENT_NOT_COMPLETE:" + family)
    if summary.get("attempted_runs") != 1232:
        raise ValueError("PARENT_ATTEMPT_COUNT_MISMATCH:" + family)
    if len(runplan.get("runs") or []) != 1232:
        raise ValueError("PARENT_RUNPLAN_COUNT_MISMATCH:" + family)
    configured = primary_runs(config)
    if len(configured) != 952 or any(any(item.get(name) != expected.get(name) for name in _SPEC if name not in {"family", "cost_model"})
                                     for item, expected in zip(configured, plan[:952], strict=True)):
        raise ValueError("CONFIG_PLAN_MISMATCH:" + family)
    receipt = _validate_receipt(parent, summary, runplan, calendar)
    data = read_json(prepared / "data-admission.json")
    _seal(data)
    for field in ("dataset_id", "revision", "manifest_hash", "scope_hash"):
        if receipt.get(field) != data.get(field):
            raise ValueError("RECEIPT_DATA_BINDING_MISMATCH:" + family + ":" + field)
    if receipt.get("data_admission_hash") != data.get("receipt_hash"):
        raise ValueError("RECEIPT_DATA_ADMISSION_MISMATCH:" + family)
    rows = summary["results"]
    for index, (row, expected, planned) in enumerate(zip(rows, plan, runplan["runs"], strict=True)):
        if row.get("family") != family or any(row.get(name) != expected.get(name) for name in _SPEC):
            raise ValueError(f"SUMMARY_SPEC_MISMATCH:{family}:{index}")
        if any(planned.get(name) != expected.get(name) for name in _SPEC):
            raise ValueError(f"RUNPLAN_SPEC_MISMATCH:{family}:{index}")
        global_id = f"{index + (0 if family == 'basic' else 1232):04d}-{canonical_hash(expected)[:12]}"
        if row.get("run_id") != global_id:
            raise ValueError(f"GLOBAL_RUN_ID_MISMATCH:{family}:{index}")
        _validate_result(parent, row, calendar)
        if (index + 1) % 100 == 0:
            print(f"VALIDATED {family} {index + 1}/1232", flush=True)
    if summary.get("prepared_manifest_hash") is None or summary.get("cohort") is None:
        raise ValueError("PARENT_BINDING_MISSING:" + family)
    return summary, receipt, config


def merge(basic, wide, out):
    """Verify two immutable complete parents, then create a fresh merged batch."""
    basic, wide, out = Path(basic).resolve(), Path(wide).resolve(), Path(out).resolve()
    if out.exists():
        raise FileExistsError(out)
    basic_plan, wide_plan = expected_plan()
    basic_summary, basic_receipt, basic_config = _validate_parent(basic, "basic", basic_plan)
    wide_summary, wide_receipt, wide_config = _validate_parent(wide, "wide", wide_plan)
    for field in ("code_hash", "prepared_manifest_hash", "cohort"):
        if basic_summary.get(field) != wide_summary.get(field):
            raise ValueError("PARENT_BINDING_MISMATCH:" + field)
    for field in ("manifest_hash", "scope_hash", "data_admission_hash"):
        if basic_receipt.get(field) != wide_receipt.get(field):
            raise ValueError("PARENT_RECEIPT_BINDING_MISMATCH:" + field)
    if basic_config.get("snapshot") != wide_config.get("snapshot"):
        raise ValueError("PARENT_CONFIG_SNAPSHOT_MISMATCH")
    out.mkdir(parents=True, exist_ok=False)
    try:
        write_json(out / "merge-manifest.json", {"schema_version": "v3-merge-v1", "status": "MERGING",
                                                   "basic": str(basic), "wide": str(wide), "merge_code_hash": digest(__file__)})
        rows, global_plan = [], []
        for offset, (parent, summary, plan) in enumerate(((basic, basic_summary, basic_plan), (wide, wide_summary, wide_plan))):
            base = offset * 1232
            for index, (row, spec) in enumerate(zip(summary["results"], plan, strict=True)):
                global_id = f"{base + index:04d}-{canonical_hash(spec)[:12]}"
                source, target = parent / "runs" / row["run_id"], out / "runs" / global_id
                shutil.copytree(source, target)
                rows.append(row)
                global_plan.append({**spec, "run_id": global_id})
                if (index + 1) % 100 == 0:
                    print(f"COPIED {spec['family']} {index + 1}/1232", flush=True)
        for name in ("smoke",):
            shutil.copytree(basic / name, out / name)
        for name in ("smoke-oracle.json", "execution-admission.json", "basic-config.json"):
            shutil.copy2(basic / name, out / name)
        for name in ("execution-admission.json", "wide-config.json"):
            shutil.copy2(wide / name, out / ("wide-execution-admission.json" if name == "execution-admission.json" else name))
        summary = {"schema_version": "v3-merged-batch-v1", "status": "COMPLETE", "planned_runs": 2464,
                   "attempted_runs": 2464, "succeeded_runs": sum(row["status"] == "SUCCEEDED" for row in rows),
                   "blocked_runs": sum(row["status"] == "BLOCKED" for row in rows), "results": rows,
                   "code_hash": basic_summary["code_hash"], "prepared_manifest_hash": basic_summary["prepared_manifest_hash"],
                   "cohort": basic_summary["cohort"], "parent_manifest_hashes": {"basic": digest(basic / "summary.json"), "wide": digest(wide / "summary.json")},
                   "parent_receipt_hashes": {"basic": basic_receipt["receipt_hash"], "wide": wide_receipt["receipt_hash"]},
                   "limitations": basic_summary.get("limitations"), "rule_assumptions": basic_summary.get("rule_assumptions"),
                   "parent_sources": {"basic": str(basic), "wide": str(wide)}, "merge_code_hash": digest(__file__)}
        write_json(out / "run-plan.json", {"runs": global_plan, "basic_execution_receipt_hash": basic_receipt["receipt_hash"], "wide_execution_receipt_hash": wide_receipt["receipt_hash"]})
        write_json(out / "merge-manifest.json", {"schema_version": "v3-merge-v1", "status": "COMPLETE", "merge_code_hash": digest(__file__)})
        # Publish the complete summary last: a reader must never see COMPLETE
        # summary state before the merge manifest has sealed successfully.
        write_json(out / "summary.json", summary)
        return summary
    except Exception as exc:
        write_json(out / "merge-manifest.json", {"schema_version": "v3-merge-v1", "status": "BLOCKED",
                                                   "error": f"{type(exc).__name__}: {exc}", "merge_code_hash": digest(__file__)})
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--basic", required=True)
    parser.add_argument("--wide", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    merge(args.basic, args.wide, args.out)


if __name__ == "__main__":
    main()
