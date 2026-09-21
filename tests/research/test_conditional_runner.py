from pathlib import Path
import sqlite3

import pytest

from research.krx_lab.conditional_runner import plan_conditional, run_conditional, conditional_status
from research.krx_lab.contracts import CooperativeStop, ExecutionHooks
from research.krx_lab.io import digest, read_json, write_json
from research.krx_lab.registry import Registry
from tests.research.conditional_fixtures import create_inputs


def _plan(tmp_path):
    inputs = create_inputs(tmp_path / "inputs")
    out = tmp_path / "experiment"
    plan_conditional(inputs["delivery"], inputs["signals"], inputs["windows"], inputs["lifecycle"],
                     out, benchmark_id=inputs["benchmark_id"], resource_limits={})
    return inputs, out


def test_all_33_with_separate_hidden_wave_and_idempotent_resume(tmp_path):
    inputs, out = _plan(tmp_path)
    first = run_conditional(out)
    assert first["statuses"] == {"SUCCEEDED": 26, "BLOCKED": 7}
    assert first["status"] == "INCOMPLETE"
    second = run_conditional(out, include_synthetic_holdout=True)
    assert second["statuses"] == {"SUCCEEDED": 33}
    assert second["status"] == "SYNTHETIC_VERIFIED"
    assert second["selection"] == "NOT_A_REAL_SELECTION"
    assert second["real_holdout_opened"] is False
    assert all(r["attempt"] == 1 for r in Registry(out / "registry.sqlite").records())
    assert run_conditional(out, include_synthetic_holdout=True) == second
    assert conditional_status(out) == second
    assert '상세 장부' in (out / "conditional-report.html").read_text(encoding="utf-8")
    from research.krx_lab.lifecycle import read_lifecycle
    assert read_lifecycle(inputs["lifecycle"])["holdout_access"] == []


def test_prerequisite_failure_keeps_all_seven_hidden_slots_blocked(tmp_path, monkeypatch):
    _, out = _plan(tmp_path)
    import research.krx_lab.conditional_execution as execution
    original = execution.simulate_slot

    def fail_one(delivery, signals, spec, **kwargs):
        assert not spec["requires_holdout"]
        if spec["phase"] == "allocation" and spec["conditional_slot"] == 0:
            raise ValueError("EXPECTED_FAULT")
        return original(delivery, signals, spec, **kwargs)

    monkeypatch.setattr(execution, "simulate_slot", fail_one)
    result = run_conditional(out, include_synthetic_holdout=True)
    assert result["statuses"] == {"FAILED": 1, "SUCCEEDED": 25, "BLOCKED": 7}
    failed = Registry(out / "registry.sqlite").records()[0]
    failure_path = out / failed["artifacts"]
    failure = read_json(failure_path / "failure.json")
    assert failure["attempt"] == 1 and failure["run_id"] == failed["run_id"]
    assert "EXPECTED_FAULT" in (failure_path / "traceback.txt").read_text(encoding="utf-8")
    assert digest(failure_path / "traceback.txt") == failure["traceback_sha256"]
    monkeypatch.setattr(execution, "simulate_slot", original)
    result = run_conditional(out, include_synthetic_holdout=True)
    assert result["statuses"] == {"SUCCEEDED": 33}
    assert read_json(failure_path / "failure.json") == failure
    with sqlite3.connect(out / "registry.sqlite") as db:
        assert db.execute("SELECT status FROM attempts WHERE run_id=? ORDER BY attempt",
                          (failed["run_id"],)).fetchall() == [("FAILED",), ("SUCCEEDED",)]


@pytest.mark.parametrize("stage", ["before_artifacts", "after_artifacts", "before_rename", "after_rename",
                                   "before_registry_commit", "after_registry_commit"])
def test_checkpoint_interruption_resume_preserves_attempts(tmp_path, stage):
    _, out = _plan(tmp_path)

    def stop(current, context):
        if current == stage:
            raise CooperativeStop("EXPECTED_STOP")

    stopped = run_conditional(out, limit=1, hooks=ExecutionHooks(checkpoint=stop))
    assert stopped["stop_reason"] == "EXPECTED_STOP"
    row = Registry(out / "registry.sqlite").records()[0]
    assert row["status"] == ("SUCCEEDED" if stage == "after_registry_commit" else "INTERRUPTED")
    run_conditional(out, limit=1)
    updated = Registry(out / "registry.sqlite").records()[0]
    assert updated["status"] == "SUCCEEDED"
    assert updated["attempt"] == (1 if stage == "after_registry_commit" else 2)


def test_changed_signal_bytes_rejected_before_execution(tmp_path):
    inputs, out = _plan(tmp_path)
    with Path(inputs["signals"]).open("a", encoding="utf-8") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="INPUT_CHANGED"):
        run_conditional(out)


def test_corrupt_precheck_artifact_prevents_hidden_wave(tmp_path):
    _, out = _plan(tmp_path)
    run_conditional(out)
    row = Registry(out / "registry.sqlite").records()[0]
    path = out / row["artifacts"] / "contract_ledger.json"
    path.write_text("{}", encoding="utf-8")
    result = run_conditional(out, include_synthetic_holdout=True)
    assert result["statuses"] == {"CORRUPT": 1, "SUCCEEDED": 25, "BLOCKED": 7}


def test_registry_spec_tampering_rejected(tmp_path):
    _, out = _plan(tmp_path)
    with sqlite3.connect(out / "registry.sqlite") as db:
        db.execute("UPDATE runs SET spec=json_set(spec, '$.requires_holdout', 0) WHERE json_extract(spec, '$.requires_holdout')=1")
    with pytest.raises(ValueError, match="REGISTRY_CHANGED"):
        run_conditional(out)


def test_real_delivery_rejected_before_loading_missing_signals(tmp_path):
    inputs = create_inputs(tmp_path / "inputs")
    delivery = read_json(inputs["delivery"])
    delivery["source_kind"] = "REAL"
    write_json(inputs["delivery"], delivery)
    with pytest.raises(ValueError):
        plan_conditional(inputs["delivery"], tmp_path / "absent.json", inputs["windows"], inputs["lifecycle"],
                         tmp_path / "out", benchmark_id="TEST")
    assert not (tmp_path / "out").exists()


def test_cli_plan_and_status(tmp_path, capsys):
    from research.krx_lab.cli import main
    inputs = create_inputs(tmp_path / "inputs")
    out = tmp_path / "out"
    args = ["conditional-plan"]
    for key in ("delivery", "signals", "windows", "lifecycle"):
        args.extend(["--" + key, str(inputs[key])])
    main(args + ["--out", str(out), "--benchmark-id", "TEST"])
    assert '"PLANNED": 26' in capsys.readouterr().out
    main(["conditional-status", "--experiment", str(out)])
    assert '"BLOCKED": 7' in capsys.readouterr().out


def test_registry_metrics_cannot_replace_verified_report_values(tmp_path):
    _, out = _plan(tmp_path)
    run_conditional(out, limit=1)
    with sqlite3.connect(out / "registry.sqlite") as db:
        db.execute("UPDATE runs SET metrics=json_set(metrics, '$.total_return', 999999) WHERE status='SUCCEEDED'")
    with pytest.raises(ValueError, match="REGISTRY_METRICS_MISMATCH"):
        conditional_status(out)


@pytest.mark.parametrize("field,value", [("cost_bps", 10), ("delay", 2), ("policy", "staged10_15_20"),
                                         ("period", "holdout"), ("optimistic", True), ("requires_holdout", True),
                                         ("benchmark_id", "OTHER"), ("dataset_id", "OTHER"), ("revision", "2"),
                                         ("initial_cash", 1), ("cost_model", "delivery_profiles"),
                                         ("growth_policy", "staged10_15_20"), ("phase", "holdout"),
                                         ("orders_date", "2024-01-01")])
def test_rehashed_ledger_still_requires_exact_frozen_slot(tmp_path, field, value):
    _, out = _plan(tmp_path)
    run_conditional(out, limit=1)
    row = Registry(out / "registry.sqlite").records()[0]
    directory = out / row["artifacts"]
    ledger_path = directory / "contract_ledger.json"
    ledger = read_json(ledger_path)
    if field == "orders_date":
        assert ledger["orders"]
        ledger["orders"][0]["date"] = value
    else:
        ledger[field] = value
    write_json(ledger_path, ledger)
    artifacts = read_json(directory / "artifacts.json")
    for artifact in artifacts["files"]:
        if artifact["file"] == ledger_path.name:
            artifact["sha256"] = digest(ledger_path)
    write_json(directory / "artifacts.json", artifacts)
    with pytest.raises(ValueError, match="LEDGER_SLOT_MISMATCH"):
        conditional_status(out)
