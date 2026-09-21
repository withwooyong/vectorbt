"""Preparation artifacts cannot be mistaken for executable experiments."""

import json

import pytest

from research.krx_lab.cli import main
from research.krx_lab.io import canonical_hash
from research.krx_lab.preparation import prepare_plan


def test_cli_prepares_separate_default_and_wide_experiments(tmp_path, capsys):
    outputs = []
    for wide in (False, True):
        config = tmp_path / f"config-{wide}.json"
        args = ["config56", "--snapshot", str(tmp_path / "absent-snapshot"), "--out", str(config)]
        main(args + (["--wide-exits"] if wide else []))
        out = tmp_path / f"plan-{wide}"
        main(["prepare56", "--config", str(config), "--out", str(out)])
        plan = json.loads((out / "preparation.json").read_text(encoding="utf-8"))
        assert plan["status"] == "PREPARED_NOT_EXECUTABLE"
        assert plan["execution_allowed"] is False
        assert plan["candidate_count"] == 56
        assert plan["logical_slots"] == 952
        assert all(row["end"] < "2024-01-01" and row["status"] == "PLANNED" for row in plan["runs"])
        saved_hash = plan.pop("plan_hash")
        assert saved_hash == canonical_hash(plan)
        assert not (out / "experiment.json").exists()
        with pytest.raises(FileExistsError):
            prepare_plan(config, out)
        with pytest.raises(FileExistsError):
            main(args)
        outputs.append(plan)
    assert outputs[0]["experiment_id"] != outputs[1]["experiment_id"]
    assert set(outputs[0]["config"]["exits"]).isdisjoint(outputs[1]["config"]["exits"])


def test_preparation_rejects_old_or_unknown_schema(tmp_path):
    config = tmp_path / "config.json"
    config.write_text('{"schema_version": "krx-lab-v1"}', encoding="utf-8")
    with pytest.raises(ValueError, match="UNSUPPORTED_PREPARATION_SCHEMA"):
        prepare_plan(config, tmp_path / "out")
    assert not (tmp_path / "out").exists()
