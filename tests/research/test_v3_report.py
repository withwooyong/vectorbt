from __future__ import annotations

import json

import pytest

from research.krx_lab.v3_report import generate_report


def _row(entry, exit_id, year, value, *, family="basic", status="SUCCEEDED"):
    return {"run_id": f"{entry}-{exit_id}-{year}", "entry_id": entry, "exit_id": exit_id,
            "strategy_id": f"{entry}__{exit_id}", "family": family, "phase": "validation", "year": year,
            "cost_bps": None, "delay": 1, "cost_model": "DATED_V3_RULES", "ledger_check": {"status": "PASS"}, "status": status,
            "metrics": {"total_return": value, "max_drawdown": .1, "trade_count": 2} if status == "SUCCEEDED" else {},
            "issues": ["<unsafe>&"] if status != "SUCCEEDED" else []}


def test_report_separates_complete_years_escapes_html_and_never_overwrites(tmp_path):
    rows = [_row("CROSS<5", "PCT_3_6", year, .01) for year in range(2020, 2024)]
    rows += [_row("CROSS<5", "PCT_8_16", year, .02, family="wide") for year in range(2020, 2024)]
    rows.append(_row("partial", "PCT_3_6", 2020, .9))
    rows.append(_row("blocked", "PCT_3_6", 2020, None, status="BLOCKED"))
    batch = tmp_path / "batch"
    batch.mkdir()
    (batch / "summary.json").write_text(json.dumps({"status": "PARTIAL", "results": rows, "cohort": {"result_label": "CLEAN", "instrument_ids": ["1"], "exclusions": [], "limitations": ["LIMIT"]}}), encoding="utf-8")
    (batch / "smoke-oracle.json").write_text('{"status":"PASS"}', encoding="utf-8")
    (batch / "execution-admission.json").write_text('{}', encoding="utf-8")
    out = tmp_path / "report"
    result = generate_report(batch, out)
    assert result["attempted"] == 10 and result["blocked"] == 1
    markdown, page = (out / "report.md").read_text(encoding="utf-8"), (out / "report.html").read_text(encoding="utf-8")
    assert "CROSS&lt;5" in markdown and "<table>" in page and "&lt;unsafe&gt;&amp;" in page
    assert "1.00%" in markdown and "2.00%" in markdown
    with pytest.raises(FileExistsError):
        generate_report(batch, out)


def test_report_handles_no_results_and_blocked_smoke(tmp_path):
    batch = tmp_path / "batch"
    batch.mkdir()
    (batch / "summary.json").write_text('{"status":"BLOCKED","results":[]}', encoding="utf-8")
    out = tmp_path / "out"
    result = generate_report(batch, out)
    assert result["attempted"] == 0
    assert "실행 기록" in (out / "report.md").read_text(encoding="utf-8")
