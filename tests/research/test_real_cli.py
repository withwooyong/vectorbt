"""The REAL inspection command records gaps without opening execution."""

import json

import pytest

from research.krx_lab.cli import main
from research.krx_lab.io import digest, read_json
from tests.research.real_fixtures import create_real_shaped_input


def test_inspect_real_cli_preserves_inputs_and_blocks_execution(tmp_path, capsys):
    delivery_path = create_real_shaped_input(tmp_path / "input")
    before = digest(delivery_path)
    source_before = digest(delivery_path.parent / "source.json")
    out = tmp_path / "inspection.json"

    main(["inspect-real", "--delivery", str(delivery_path), "--out", str(out)])

    report = read_json(out)
    assert report["grade"] == "BLOCKED"
    assert report["admission"] == "INSPECTION_ONLY"
    assert report["dataset_id"] == "offline-real-shape-fixture-not-market-data"
    assert any(gap["code"] == "HISTORICAL_CAPTURE_UNAVAILABLE" for gap in report["evidence_gaps"])
    assert report == json.loads(capsys.readouterr().out)
    assert digest(delivery_path) == before
    assert digest(delivery_path.parent / "source.json") == source_before
    assert not (tmp_path / "run").exists()

    report_before = digest(out)
    with pytest.raises(SystemExit):
        main(["inspect-real", "--delivery", str(delivery_path), "--out", str(out)])
    assert digest(out) == report_before

    with pytest.raises(SystemExit):
        main(["inspect-real", "--delivery", str(delivery_path),
              "--out", str(delivery_path.parent / "report.json")])
    assert not (delivery_path.parent / "report.json").exists()
