from __future__ import annotations

import json
from decimal import Decimal

import pandas as pd
import pytest

from research.krx_lab.io import canonical_hash, digest, read_json, write_json
from research.krx_lab.metrics import calculate_metrics
from scripts.research import merge_v3_batches as merger


def _result(parent, run_id, *, status="SUCCEEDED"):
    path = parent / "runs" / run_id
    path.mkdir(parents=True)
    row = {"run_id": run_id, "family": "basic", "entry_id": "A", "exit_id": "PCT_3_6", "strategy_id": "A__PCT_3_6", "policy": "fixed20", "sector_cap": None,
           "phase": "development", "year": None, "start": "2015-06-15", "end": "2019-12-31", "cost_bps": 30,
           "delay": 1, "cost_model": "FLAT_BPS_STRESS_ONLY", "status": status, "issues": [], "files": {}}
    if status == "SUCCEEDED":
        row.update(ledger_check={"status": "PASS"}, metrics={"total_return": 0.0})
    (path / "result.json").write_text(json.dumps(row), encoding="utf-8")
    (path / "artifact.bin").write_bytes(b"verified")
    artifacts = {"status": status, "issues": [], "files": {"artifact.bin": digest(path / "artifact.bin")}}
    (path / "artifacts.json").write_text(json.dumps(artifacts), encoding="utf-8")
    return row


def test_result_validation_rejects_missing_artifacts_and_blocked_metrics(tmp_path):
    row = _result(tmp_path, "r")
    with pytest.raises(ValueError, match="ARTIFACT_SET"):
        merger._validate_result(tmp_path, row)
    blocked = _result(tmp_path, "b", status="BLOCKED")
    blocked["metrics"] = {}
    (tmp_path / "runs" / "b" / "result.json").write_text(json.dumps(blocked), encoding="utf-8")
    with pytest.raises(ValueError, match="BLOCKED_RESULT_HAS_METRICS"):
        merger._validate_result(tmp_path, blocked)


def test_merge_assigns_unique_global_ids_with_stubbed_verified_parents(tmp_path, monkeypatch):
    basic, wide = tmp_path / "basic", tmp_path / "wide"
    basic.mkdir()
    wide.mkdir()
    basic_row, wide_row = _result(basic, "0000-basic"), _result(wide, "0000-wide")
    basic_row["family"] = "basic"
    wide_row["family"] = "wide"
    for parent, row in ((basic, basic_row), (wide, wide_row)):
        (parent / "summary.json").write_text("{}", encoding="utf-8")
        (parent / "runs" / row["run_id"] / "result.json").write_text(json.dumps(row), encoding="utf-8")
        (parent / "smoke").mkdir()
        (parent / "smoke" / "artifacts.json").write_text('{"status":"SUCCEEDED","files":{}}', encoding="utf-8")
        for name in ("smoke-oracle.json", "execution-admission.json", "basic-config.json", "wide-config.json"):
            (parent / name).write_text("{}", encoding="utf-8")
    spec = {name: basic_row[name] for name in merger._SPEC}
    monkeypatch.setattr(merger, "expected_plan", lambda: ([spec], [{**spec, "family": "wide"}]))
    def parent_summary(parent, family, plan):
        row = basic_row if family == "basic" else wide_row
        return ({"code_hash": "x", "prepared_manifest_hash": "p", "cohort": {}, "results": [row]}, {"receipt_hash": family}, {"snapshot": "same"})
    monkeypatch.setattr(merger, "_validate_parent", parent_summary)
    merged = tmp_path / "merged"
    output = merger.merge(basic, wide, merged)
    assert [row["run_id"] for row in output["results"]] == ["0000-basic", "0000-wide"]
    assert json.loads((merged / "merge-manifest.json").read_text(encoding="utf-8"))["status"] == "COMPLETE"
    copied = next((merged / "runs").iterdir())
    assert json.loads((copied / "result.json").read_text(encoding="utf-8")) in (basic_row, wide_row)
    with pytest.raises(FileExistsError):
        merger.merge(basic, wide, merged)


def test_receipt_rejects_resealed_nonadmission_and_missing_oracle_check(tmp_path):
    write_json(tmp_path / "smoke-oracle.json", {"status": "PASS"})
    body = {"schema_version": "krx-real-execution-admission-v1", "decision": "EXECUTION_ADMITTED",
            "data_admission_hash": "data", "manifest_hash": "manifest",
            "checks": {"CURRENT_NUMERICAL_ORACLE": "PASS", "SMALL_REAL_LEDGER_REPLAY": "PASS"},
            "bindings": {"code_hash": "code", "ledger_hash": "ledger"}}
    for changed, error in (({"decision": "NOT_ADMITTED"}, "EXECUTION_RECEIPT_NOT_ADMITTED"),
                           ({"checks": {}}, "EXECUTION_RECEIPT_BINDING_INVALID")):
        receipt = {**body, **changed}
        receipt["receipt_hash"] = canonical_hash(receipt)
        write_json(tmp_path / "execution-admission.json", receipt)
        with pytest.raises(ValueError, match=error):
            merger._validate_receipt(tmp_path, {"code_hash": "code"},
                                     {"execution_receipt_hash": receipt["receipt_hash"]}, [])


def test_parent_rejects_changed_cohort_policy_and_global_id(tmp_path, monkeypatch):
    from research.krx_lab import v3_run

    plan, _ = merger.expected_plan()
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    pd.DataFrame({"date": pd.to_datetime(["2023-01-02"])}).to_parquet(prepared / "calendar.parquet")
    manifest = {"files": {"calendar": {"file": "calendar.parquet", "sha256": digest(prepared / "calendar.parquet")}}}
    write_json(prepared / "manifest.json", manifest)
    cohort = {"decision": "PASS", "instrument_ids": ["1"]}
    monkeypatch.setattr(v3_run, "verify_prepared", lambda path: (manifest, cohort))
    monkeypatch.setattr(merger, "primary_runs", lambda config: [{k: v for k, v in spec.items()
                                                                 if k not in {"family", "cost_model"}}
                                                                for spec in plan[:952]])
    monkeypatch.setattr(merger, "_validate_receipt", lambda *args: {"receipt_hash": "ok",
                                                                "data_admission_hash": "data"})
    monkeypatch.setattr(merger, "_validate_result", lambda *args: None)
    rows = [{**spec, "run_id": f"{index:04d}-{canonical_hash(spec)[:12]}"}
            for index, spec in enumerate(plan)]
    summary = {"status": "COMPLETE", "planned_runs": 1232, "attempted_runs": 1232,
               "prepared_manifest_hash": digest(prepared / "manifest.json"), "cohort": cohort, "results": rows}
    parent = tmp_path / "basic"
    parent.mkdir()
    write_json(parent / "basic-config.json", {"snapshot": str(prepared)})
    write_json(parent / "run-plan.json", {"runs": plan})
    write_json(prepared / "data-admission.json", {"receipt_hash": "data"})
    monkeypatch.setattr(merger, "_seal", lambda value: None)
    for change, error in (({"cohort": {"decision": "PASS", "instrument_ids": ["2"]}},
                           "PREPARED_COHORT_MISMATCH"),
                          ({"results": [{**rows[0], "policy": "altered"}, *rows[1:]]},
                           "SUMMARY_SPEC_MISMATCH"),
                          ({"results": [{**rows[0], "run_id": "../wrong"}, *rows[1:]]},
                           "GLOBAL_RUN_ID_MISMATCH")):
        write_json(parent / "summary.json", {**summary, **change})
        with pytest.raises(ValueError, match=error):
            merger._validate_parent(parent, "basic", plan)


def test_result_replay_rejects_self_consistently_rehashed_bad_ledger(tmp_path):
    D = Decimal
    days = pd.to_datetime(["2023-01-25", "2023-01-26", "2023-01-27", "2023-01-30"])
    cash = D(100_000_000)
    result = {"status": "SUCCEEDED", "issues": [], "performance_valid": True, "initial_cash": cash,
              "equity": pd.DataFrame([
                  dict(date=days[0], settled_cash=cash, receivables=D(0), payables=D(1010),
                       cash=cash-D(1010), exposure=D(1000), equity=cash-D(10), positions_count=1),
                  dict(date=days[1], settled_cash=cash, receivables=D(1088), payables=D(1010),
                       cash=cash+D(78), exposure=D(0), equity=cash+D(78), positions_count=0),
                  dict(date=days[2], settled_cash=cash-D(1010), receivables=D(1088), payables=D(0),
                       cash=cash+D(78), exposure=D(0), equity=cash+D(78), positions_count=0),
                  dict(date=days[3], settled_cash=cash+D(78), receivables=D(0), payables=D(0),
                       cash=cash+D(78), exposure=D(0), equity=cash+D(78), positions_count=0)]),
              "cashflows": pd.DataFrame([
                  dict(date=days[0], kind="BUY", cash_delta=D(0), receivable_delta=D(0),
                       payable_delta=D(1010), fee=D(10), tax=D(0), fill_seq=0),
                  dict(date=days[1], kind="SELL", cash_delta=D(0), receivable_delta=D(1088),
                       payable_delta=D(0), fee=D(10), tax=D(2), fill_seq=1),
                  dict(date=days[2], kind="SETTLEMENT", cash_delta=D(-1010), receivable_delta=D(0),
                       payable_delta=D(-1010), fee=D(0), tax=D(0), fill_seq=0),
                  dict(date=days[3], kind="SETTLEMENT", cash_delta=D(1088), receivable_delta=D(-1088),
                       payable_delta=D(0), fee=D(0), tax=D(0), fill_seq=1)]),
              "fills": pd.DataFrame([dict(date=days[0], code="1", side="buy", size=10, price=D(100),
                                          fee=D(10), fees=D(10), tax=D(0), fill_seq=0),
                                     dict(date=days[1], code="1", side="sell", size=10, price=D(110),
                                          fee=D(10), fees=D(10), tax=D(2), fill_seq=1)]),
              "positions": pd.DataFrame([dict(date=days[0], code="1", size=10, mark_price=D(100))]),
              "trades": pd.DataFrame([dict(code="1", pnl=D(78), entry_date=days[0], exit_date=days[1])]),
              "events": pd.DataFrame(columns=["date", "code", "quantity_delta"])}
    for name in ("signals", "plans", "orders"):
        result[name] = pd.DataFrame({"date": pd.to_datetime([])})
    row = {"run_id": "hand-ledger", "status": "SUCCEEDED", "issues": [],
           "start": str(days[0].date()), "end": str(days[-1].date()), "ledger_check": {"status": "PASS"}}
    metrics = calculate_metrics(result)
    metrics["total_taxes"] = float(result["fills"]["tax"].sum())
    metrics["average_exposure_fraction"] = float((result["equity"]["exposure"].astype(float)
                                                  / result["equity"]["equity"].astype(float)).mean())
    row["metrics"] = metrics
    path = tmp_path / "runs" / row["run_id"]
    path.mkdir(parents=True)
    files = {}
    for name in merger._TABLES:
        target = path / f"{name}.parquet"
        result[name].to_parquet(target, index=False)
        files[target.name] = digest(target)
    row["files"] = files
    write_json(path / "result.json", row)
    write_json(path / "artifacts.json", {"status": "SUCCEEDED", "issues": [], "files": files})
    merger._validate_result(tmp_path, row, days)

    equity = pd.read_parquet(path / "equity.parquet")
    equity.loc[3, "equity"] += D(1)
    equity.to_parquet(path / "equity.parquet", index=False)
    files["equity.parquet"] = digest(path / "equity.parquet")
    write_json(path / "result.json", row)
    write_json(path / "artifacts.json", {"status": "SUCCEEDED", "issues": [], "files": files})
    with pytest.raises(ValueError, match="Ledger identity mismatch"):
        merger._validate_result(tmp_path, read_json(path / "result.json"), days)
