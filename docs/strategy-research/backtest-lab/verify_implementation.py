"""저장한 실행물의 검증 기록을 갱신한다. DB·가격·실험에는 쓰지 않는다."""

import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from research.krx_lab.io import digest, read_json, source_hash, write_json
from research.krx_lab.registry import Registry
from research.krx_lab.runner import status, verify_artifacts, verify_experiment


def main():
    root = Path(os.environ["LOCALAPPDATA"]) / "vectorbt-research"
    real = root / "krx-lab-real-20260913-final"
    synthetic = root / "krx-lab-synthetic-20260913-final"
    previous = root / "krx-lab-synthetic-20260913"
    diagnostic = root / "krx-lab-diagnostic-20260913-v2"
    snapshot = root / "krx-lab-db-20260913-1542"
    verify_experiment(real)
    verify_experiment(synthetic)
    real_status, synthetic_status = status(real), status(synthetic)
    assert real_status["statuses"] == {"BLOCKED": 849}
    assert synthetic_status["statuses"] == {"SUCCEEDED": 64, "PLANNED": 752, "BLOCKED": 33}
    results = Registry(synthetic / "registry.sqlite").records()
    successful = [r for r in results if r["status"] == "SUCCEEDED"]
    old = Registry(previous / "registry.sqlite").records()
    def key(record):
        return (record["strategy_id"], record["phase"], record["year"], record["cost_bps"], record["delay"])
    old_by_key = {key(r): r for r in old if r["status"] == "SUCCEEDED"}
    def performance(metrics):
        return {k: v for k, v in metrics.items() if k not in {"elapsed_seconds", "rss_bytes"}}
    orders, days = 0, 0
    for record in successful:
        directory = synthetic / record["artifacts"]
        verify_artifacts(directory)
        check = read_json(directory / "reconciliation.json")
        assert check["ok"]
        assert performance(record["metrics"]) == performance(old_by_key[key(record)]["metrics"])
        orders += check["orders_checked"]
        days += check["eod_checked"]
    receipt = read_json(diagnostic / "diagnostic.json")
    for name, sha in receipt["files"].items():
        assert digest(diagnostic / name) == sha
    assert receipt["symbols"] == 4025 and not receipt["returns_computed"]
    result = {
        "status": "VERIFIED_CORE_WITH_DATA_BLOCKERS", "current_source_sha256": source_hash(),
        "real": {**real_status, "selection": read_json(real / "selection.json")["status"],
                 "quality": read_json(snapshot / "quality.json"),
                 "observed_price_range_independently_checked": ["2015-01-02", "2023-12-28"],
                 "returns_computed": False},
        "synthetic": {**synthetic_status, "market_performance": False,
                      "orders_reconciled": orders, "eod_rows_reconciled": days,
                      "fresh_run_metric_matches": len(successful),
                      "development_strategies": len({r["strategy_id"] for r in successful if r["phase"] == "development"}),
                      "validation_slots": sum(r["phase"] == "validation" for r in successful),
                      "sum_run_elapsed_seconds": sum(r["metrics"]["elapsed_seconds"] for r in successful),
                      "max_recorded_rss_bytes": max(r["metrics"]["rss_bytes"] for r in successful)},
        "diagnostic": receipt,
        "checks": {
            "pytest_command": ".venv/Scripts/python.exe -X utf8 -m pytest tests/research docs/strategy-research/test_research_backtest.py -q",
            "pytest_passed": 64, "pytest_seconds": 19.05,
            "ruff_command": "uv run --no-sync ruff check research/krx_lab tests/research",
            "ruff": "PASS", "compileall": "PASS", "git_diff_check": "PASS",
            "test_result_provenance": "이번 세션의 실제 실행 결과 기록; 이 검산기는 pytest 자체를 재실행하지 않음",
        },
        "artifacts": {"real_report": str(real / "report.html"),
                      "synthetic_report": str(synthetic / "report.html"),
                      "snapshot": str(snapshot), "diagnostic": str(diagnostic)},
        "not_implemented_or_not_verified": ["EXECUTION_ELIGIBLE admission", "historical corporate-action settlement",
                                            "realistic cost adapter", "conditional phase execution", "freeze/finalize",
                                            "actual strategy returns", "final strategy selection", "paper/live orders"],
        "old_example_sha256": digest(REPO / "docs/strategy-research/research_backtest.py"),
    }
    write_json(Path(__file__).with_name("implementation-validation-2026-09-13.json"), result)
    print(json.dumps({"status": result["status"], "synthetic_runs_verified": len(successful),
                      "orders_reconciled": orders, "real_statuses": real_status["statuses"]}, indent=2))


if __name__ == "__main__":
    main()
