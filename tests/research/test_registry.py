from __future__ import annotations

import os
from pathlib import Path
import socket

import psutil
import pandas as pd
import pytest

from research.krx_lab.config import default_config
from research.krx_lab.io import digest, write_json
from research.krx_lab.registry import Registry, worker_lock
from research.krx_lab.runner import plan, status


def test_registry_interrupted_run_resumes_as_new_attempt_and_rejects_duplicates(tmp_path):
    registry = Registry(tmp_path / "registry.sqlite")
    registry.add("run-1", {"phase": "validation"})
    with pytest.raises(Exception):
        registry.add("run-1", {"phase": "validation"})

    assert registry.begin("run-1") == 1
    with pytest.raises(ValueError, match="실행 중/완료"):
        registry.begin("run-1")
    registry.recover()
    interrupted = registry.records()[0]
    assert interrupted["status"] == "INTERRUPTED"
    assert interrupted["attempt"] == 1

    assert registry.begin("run-1") == 2
    registry.finish("run-1", "SUCCEEDED", metrics={"total_return": 0.1})
    completed = registry.records()[0]
    assert completed["status"] == "SUCCEEDED"
    assert completed["attempt"] == 2
    with registry.connect() as db:
        attempts = [tuple(row) for row in db.execute("SELECT attempt,status FROM attempts ORDER BY attempt")]
    assert attempts == [(1, "INTERRUPTED"), (2, "SUCCEEDED")]
    with pytest.raises(ValueError, match="실행 중/완료"):
        registry.begin("run-1")


def test_worker_lock_rejects_live_existing_pid(tmp_path):
    payload = {
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "create_time": psutil.Process().create_time(),
    }
    write_json(tmp_path / "worker.lock", payload)
    with pytest.raises(RuntimeError, match="실행 중인 worker"):
        with worker_lock(tmp_path):
            pass
    assert (tmp_path / "worker.lock").exists()


def _tiny_synthetic_snapshot(path: Path) -> None:
    path.mkdir()
    prices = pd.DataFrame(
        {
            "date": pd.to_datetime(["2015-01-02", "2015-01-05"]),
            "code": ["SYN000", "SYN000"],
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000, 1000],
        }
    )
    part = path / "prices.parquet"
    prices.to_parquet(part, index=False)
    quality = {
        "grade": "SYNTHETIC",
        "reasons": [],
        "limitations": [],
        "rows": 2,
        "symbols": 1,
    }
    write_json(path / "quality.json", quality)
    manifest = {
        "status": "COMPLETE",
        "source": "SYNTHETIC",
        "parts": [{"file": part.name, "rows": 2, "sha256": digest(part)}],
        "quality_sha256": digest(path / "quality.json"),
    }
    write_json(path / "manifest.json", manifest)


def test_plan_materializes_816_primary_and_33_conditional_slots(tmp_path):
    snapshot = tmp_path / "snapshot"
    _tiny_synthetic_snapshot(snapshot)
    config_path = tmp_path / "config.json"
    write_json(config_path, default_config(snapshot))
    out = tmp_path / "experiment"

    experiment = plan(config_path, out)
    summary = status(out)
    records = Registry(out / "registry.sqlite").records()

    assert experiment["primary_slots"] == 816
    assert experiment["conditional_slots"] == 33
    assert experiment["logical_slots"] == 849
    assert summary["total"] == 849
    assert sum(row["phase"] in {"development", "validation"} for row in records) == 816
    assert sum(row["phase"] not in {"development", "validation"} for row in records) == 33
    assert summary["statuses"] == {"PLANNED": 816, "BLOCKED": 33}
    assert (out / "leaderboard.csv").exists()
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "실제 시장 성과" in report
