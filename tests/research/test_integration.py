"""Offline integration of delivery inspection, event execution, and artifact replay."""

from pathlib import Path
import shutil

import pytest

from research.krx_lab.io import read_json, write_json
from research.krx_lab.runner import run_delivery, verify_artifacts
from research.krx_lab.vectorbt_check import reconcile_ledger


FIXTURES = Path(__file__).parent / "fixtures/contracts_v1"


def test_synthetic_delivery_runs_through_inspection_execution_and_persistence(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(FIXTURES, source)
    signals = [{"date": "2023-01-02", "instrument_id": "SYN-ID-001", "atr14": 1,
                "avg_volume20": 1_000_000, "entry": True}]
    write_json(source / "signals.json", signals)
    summary = run_delivery(source / "delivery.json", source / "signals.json", tmp_path / "run",
                           entry_id="entry", exit_id="PCT_5_10", start="2023-01-02", end="2023-01-05",
                           initial_cash=25_000)
    assert summary["status"] == "SUCCEEDED"
    assert summary["source_kind"] == "SYNTHETIC"
    assert summary["reconciliation"]["ok"]
    verify_artifacts(tmp_path / "run/result")
    ledger = read_json(tmp_path / "run/result/contract_ledger.json")
    assert reconcile_ledger(ledger)["ok"]
    assert ledger["source_kind"] == "SYNTHETIC"
    with pytest.raises(FileExistsError):
        run_delivery(source / "delivery.json", source / "signals.json", tmp_path / "run",
                     entry_id="entry", exit_id="PCT_5_10", start="2023-01-02", end="2023-01-05")


def test_real_delivery_cannot_reach_signal_loader_or_execution(tmp_path):
    delivery = read_json(FIXTURES / "delivery.json")
    delivery["source_kind"] = "REAL"
    delivery["sources"][0]["historical_capture"] = "original"
    write_json(tmp_path / "delivery.json", delivery)
    with pytest.raises(ValueError, match="REAL_EXECUTION_NOT_ADMITTED"):
        run_delivery(tmp_path / "delivery.json", tmp_path / "nonexistent-signals.json", tmp_path / "run",
                     entry_id="entry", exit_id="PCT_5_10", start="2023-01-02", end="2023-01-05")
    assert not (tmp_path / "run").exists()


def test_cli_freeze_finalize_uses_persisted_synthetic_evidence(tmp_path, capsys):
    from research.krx_lab.cli import main
    from research.krx_lab.io import digest, source_hash
    from research.krx_lab.lifecycle import read_lifecycle
    from tests.research.test_runner import _experiment
    from tests.research.test_lifecycle import _setup, _result
    out = _experiment(tmp_path)
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    _, root, evidence, bindings = _setup(evidence_dir)
    write_json(root / "code.json", {"source_kind": "SYNTHETIC", "source_hash": source_hash()})
    evidence["code_hash"] = digest(root / "code.json")
    evidence["experiment_id"] = read_json(out / "experiment.json")["experiment_id"]
    write_json(evidence_dir / "evidence.json", evidence)
    write_json(evidence_dir / "bindings.json", bindings)
    main(["freeze", "--experiment", str(out), "--evidence", str(evidence_dir / "evidence.json"),
          "--bindings", str(evidence_dir / "bindings.json"), "--artifact-root", str(root)])
    assert read_lifecycle(out / "lifecycle")["state"] == "FROZEN"
    result_path, _ = _result(out / "lifecycle", root)
    main(["finalize", "--experiment", str(out), "--result", str(result_path)])
    assert read_lifecycle(out / "lifecycle")["state"] == "FINALIZED"
    assert read_json(out / "experiment.json")["holdout_opened"] is False
    assert '"FINALIZED"' in capsys.readouterr().out


def test_resource_limit_stops_batch_before_loading_prices(tmp_path, monkeypatch):
    from tests.research.test_runner import _experiment
    import research.krx_lab.runner as runner
    _experiment(tmp_path)
    # Set limits before creating a new planned experiment, preserving the original hashes.
    config_path = tmp_path / "config.json"
    config = read_json(config_path)
    config["resource_limits"]["max_rss_bytes"] = 1
    write_json(config_path, config)
    constrained = tmp_path / "constrained"
    runner.plan(config_path, constrained)
    monkeypatch.setattr(runner, "load_prices", lambda *a, **k: pytest.fail("resource-limited batch loaded prices"))
    summary = runner.run(constrained, limit=1)
    assert summary["stop_reason"] == "RSS_LIMIT"
    assert summary["statuses"]["PLANNED"] == 816
    assert summary["resources"]["sample_count"] >= 1
