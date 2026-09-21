from __future__ import annotations

import json

import pytest

from scripts.research.chart_v3_comparison import chart_data, generate_chart


def _row(entry, exit_id, year, value, family):
    return {
        "entry_id": entry, "exit_id": exit_id, "year": year, "family": family,
        "phase": "validation", "cost_bps": None, "delay": 1,
        "cost_model": "DATED_V3_RULES", "ledger_check": {"status": "PASS"},
        "status": "SUCCEEDED", "metrics": {"total_return": value, "max_drawdown": .1, "trade_count": 1},
    }


def _batch(tmp_path, rows, smoke="PASS", receipt=True):
    batch = tmp_path / "batch"
    batch.mkdir(parents=True)
    (batch / "summary.json").write_text(json.dumps({"results": rows, "fixture_label": "SYNTHETIC"}), encoding="utf-8")
    (batch / "smoke-oracle.json").write_text(json.dumps({"status": smoke}), encoding="utf-8")
    if receipt:
        (batch / "execution-admission.json").write_text("{}", encoding="utf-8")
    return batch


def test_chart_data_keeps_missing_pairs_missing_and_uses_percentage_points(tmp_path):
    rows = []
    for year in range(2020, 2024):
        rows.extend([_row("CROSS_5_20", "PCT_3_6", year, .01, "basic"),
                     _row("CROSS_5_20", "PCT_8_16", year, .02, "wide")])
    data = chart_data(_batch(tmp_path, rows))
    assert data["values_percentage_points"][0][0] == pytest.approx(1.0)
    assert data["values_percentage_points"][0][1:] == [None, None, None]
    assert data["complete_pair_count"] == 1


def test_chart_requires_admission_and_refuses_overwrite(tmp_path):
    batch = _batch(tmp_path, [], smoke="FAIL", receipt=False)
    with pytest.raises(ValueError):
        chart_data(batch)
    batch = _batch(tmp_path / "admitted", [], smoke="PASS", receipt=True)
    out = tmp_path / "out"
    result = generate_chart(batch, out)
    assert all((out / name).is_file() for name in ("v3-comparison-heatmap.png", "v3-comparison-heatmap.svg", "v3-comparison-data.json"))
    assert set(result) == {"png", "svg", "data"}
    with pytest.raises(FileExistsError):
        generate_chart(batch, out)
