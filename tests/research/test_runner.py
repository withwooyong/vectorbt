"""The batch boundary must preserve failed reconciliation and immutable inputs."""

import pandas as pd
import pytest

from research.krx_lab.config import default_config
from research.krx_lab.io import digest, write_json
from research.krx_lab.quality import audit
from research.krx_lab.registry import Registry
from research.krx_lab.runner import plan, run, update_report, verify_experiment


def _experiment(tmp_path, source="SYNTHETIC"):
    snapshot = tmp_path / "snapshot"
    snapshot.mkdir()
    dates = pd.bdate_range("2015-01-02", periods=300)
    prices = pd.DataFrame({"date": dates, "code": "A", "open": 100., "high": 101., "low": 99.,
                           "close": 100., "volume": 1000000, "sector": "S", "tick_size": 1.,
                           "eligible": True})
    prices.to_parquet(snapshot / "prices.parquet", index=False)
    manifest = {"source": source, "status": "COMPLETE", "parts": [
        {"file": "prices.parquet", "rows": len(prices), "sha256": digest(snapshot / "prices.parquet")}],
        "calendar": [str(x.date()) for x in dates]}
    write_json(snapshot / "quality.json", audit(prices, manifest))
    manifest["quality_sha256"] = digest(snapshot / "quality.json")
    write_json(snapshot / "manifest.json", manifest)
    write_json(tmp_path / "config.json", default_config(snapshot))
    out = tmp_path / "experiment"
    plan(tmp_path / "config.json", out)
    return out


def test_real_unverified_data_blocks_all_primary_runs_without_simulating(tmp_path, monkeypatch):
    out = _experiment(tmp_path, "PostgreSQL")
    import research.krx_lab.runner as runner
    monkeypatch.setattr(runner, "load_prices", lambda *a, **kw: pytest.fail("blocked data was loaded for returns"))
    summary = run(out)
    assert summary["statuses"] == {"BLOCKED": 849}
    assert all(r["attempt"] == 1 for r in Registry(out / "registry.sqlite").records()
               if r["phase"] in {"development", "validation"})
    assert update_report(out)["status"] == "NO_SELECTION"


def test_zero_trade_run_resume_and_corrupt_artifact(tmp_path):
    out = _experiment(tmp_path)
    summary = run(out, phases=("development",), limit=1)
    assert summary["statuses"]["SUCCEEDED"] == 1
    registry = Registry(out / "registry.sqlite")
    completed = next(r for r in registry.records() if r["status"] == "SUCCEEDED")
    assert completed["metrics"]["trade_count"] == 0
    assert completed["metrics"]["total_return"] == 0
    run(out, phases=("development",), limit=1)
    assert next(r for r in registry.records() if r["run_id"] == completed["run_id"])["attempt"] == 1
    (out / completed["artifacts"] / "metrics.json").write_text("{}", encoding="utf-8")
    update_report(out)
    assert next(r for r in registry.records() if r["run_id"] == completed["run_id"])["status"] == "CORRUPT"


def test_changed_config_and_holdout_phase_are_rejected(tmp_path):
    out = _experiment(tmp_path)
    with pytest.raises(ValueError, match="후속 단계"):
        run(out, phases=("holdout",))
    from research.krx_lab.io import read_json
    experiment = read_json(out / "experiment.json")
    experiment["config"]["initial_cash_krw"] = 1
    write_json(out / "experiment.json", experiment)
    with pytest.raises(ValueError, match="CONFIG_CHANGED"):
        verify_experiment(out)


def test_reconciliation_failure_is_not_success(tmp_path, monkeypatch):
    out = _experiment(tmp_path)
    import research.krx_lab.vectorbt_check as checker
    monkeypatch.setattr(checker, "reconcile", lambda *a, **kw: {"ok": False, "mismatches": ["cash"]})
    summary = run(out, phases=("development",), limit=1)
    assert summary["statuses"]["FAILED"] == 1
    failed = next(r for r in Registry(out / "registry.sqlite").records() if r["status"] == "FAILED")
    assert "VECTORBT_LEDGER_MISMATCH" in failed["reason"]
