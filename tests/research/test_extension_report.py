"""Saved-report verification against a real synthetic execution ledger.

These tests never claim that synthetic prices or a synthetic receipt admit real
returns. They check that the report reconstructs persisted fills and balances.
"""
from decimal import Decimal

import pandas as pd
import pytest

from research.krx_lab.extension_run import trade_statistics
from research.krx_lab.io import canonical_hash, digest, read_json, write_json
from research.krx_lab.metrics import calculate_metrics
from research.krx_lab.v3_execution import PreparedExecution, audit_execution_ledger, simulate_real_slot
from research.krx_lab.v3_run import _save_result, reconcile_result
from scripts.research import report_extension_experiments as report


def test_overlapping_statistics_metrics_are_checked():
    assert report.merge_statistics_metrics({"open_positions": 20, "buy_count": 25},
                                          {"open_positions": 20.0, "total_return": 0.1}) == {
        "open_positions": 20, "buy_count": 25, "total_return": 0.1}
    with pytest.raises(ValueError, match="STATISTICS_METRICS_MISMATCH:open_positions"):
        report.merge_statistics_metrics({"open_positions": 20}, {"open_positions": 19})


class _Rules:
    def tick(self, day, market, price):
        return Decimal(1)

    def price_limit(self, day, market):
        return Decimal("0.30")

    def settlement_sessions(self, day, market):
        return 2

    def fees(self, day, market, side, amount):
        return {"fee": Decimal(0), "tax": Decimal(0), "total": Decimal(0)}


@pytest.fixture
def saved_batch(tmp_path, monkeypatch):
    days = pd.to_datetime(["2023-01-25", "2023-01-26", "2023-01-27",
                           "2023-01-30", "2023-01-31"])
    prices = pd.DataFrame(
        dict(date=day, code="A", market="KOSPI", raw_open=100,
             raw_high=107 if day == pd.Timestamp("2023-01-26") else 101,
             raw_low=99, raw_close=100, volume=100_000,
             status="TRADING", eligible=True)
        for day in days
    )
    signals = pd.DataFrame([dict(date=days[0], code="A", close=100, atr14=2,
                                 avg_volume20=1_000_000, ENTRY=True)])
    prepared = PreparedExecution(prices, signals, days)
    result = simulate_real_slot(prepared, _Rules(), entry_id="ENTRY", exit_id="PCT_3_6",
                                start=days[1], end=days[-1])
    assert result["status"] == "SUCCEEDED"
    assert result["fills"].side.tolist() == ["buy", "sell"]
    audit_execution_ledger(result)
    assert reconcile_result(result, expected_dates=days[1:])["status"] == "PASS"

    spec = dict(run_id="synthetic-oracle", family="basic", entry_id="ENTRY",
                exit_id="PCT_3_6", start="2023-01-26", end="2023-01-31",
                max_holding_months=1, window="year_2023", cost_bps=None, delay=1)
    monkeypatch.setattr(report, "experiment_plan", lambda group: [spec] if group == "basic" else [])
    batch = tmp_path / "batch"
    run_root = batch / "runs" / spec["run_id"]
    files = _save_result(run_root, result)
    metrics = calculate_metrics(result)
    metrics["total_taxes"] = float(result["fills"].tax.sum())
    statistics = trade_statistics(result)
    row = dict(**spec, status="SUCCEEDED", issues=[], files=files,
               statistics=statistics, metrics=metrics)
    write_json(run_root / "result.json", row)
    write_json(batch / "plan.json", dict(runs=[spec], plan_hash=canonical_hash([spec])))
    code_hash = "synthetic-report-check"
    summary = dict(status="COMPLETE", group="basic", code_hash=code_hash,
                   signal_manifest_hash=None, results=[row])
    write_json(batch / "summary.json", summary)
    receipt = dict(decision="EXECUTION_ADMITTED", bindings=dict(
        code_hash=code_hash,
        strategy_hash=canonical_hash({"plan": canonical_hash([spec]), "signals": None})))
    receipt["receipt_hash"] = canonical_hash(receipt)
    write_json(batch / "execution-admission.json", receipt)
    return batch, days[1:], row


def test_saved_ledger_reproduces_counts_cash_and_metrics(saved_batch):
    batch, calendar, row = saved_batch
    checked = report.verify_batch(batch, calendar)
    assert checked["results"][0]["statistics"] == row["statistics"]
    assert checked["results"][0]["statistics"]["buy_count"] == 1
    assert checked["results"][0]["statistics"]["sell_count"] == 1
    assert checked["results"][0]["statistics"]["completed_trades"] == 1


def test_changed_saved_ledger_is_rejected(saved_batch):
    batch, calendar, row = saved_batch
    path = batch / "runs" / row["run_id"] / "fills.parquet"
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="SAVED_LEDGER_CHANGED"):
        report.verify_batch(batch, calendar)


def test_changed_reported_fill_count_is_rejected_even_when_jsons_agree(saved_batch):
    batch, calendar, row = saved_batch
    row["statistics"]["buy_count"] += 1
    write_json(batch / "summary.json", dict(status="COMPLETE", group="basic",
               code_hash="synthetic-report-check", signal_manifest_hash=None, results=[row]))
    write_json(batch / "runs" / row["run_id"] / "result.json", row)
    with pytest.raises(ValueError, match="TRADE_COUNTS_CHANGED"):
        report.verify_batch(batch, calendar)


def test_rehashed_false_equity_is_caught_by_ledger_replay(saved_batch):
    batch, calendar, row = saved_batch
    path = batch / "runs" / row["run_id"] / "equity.parquet"
    equity = pd.read_parquet(path)
    equity.loc[0, "equity"] += Decimal(1)
    equity.to_parquet(path, index=False)
    row["files"]["equity.parquet"] = digest(path)
    write_json(batch / "summary.json", dict(status="COMPLETE", group="basic",
               code_hash="synthetic-report-check", signal_manifest_hash=None, results=[row]))
    write_json(batch / "runs" / row["run_id"] / "result.json", row)
    with pytest.raises(ValueError, match="Ledger identity mismatch"):
        report.verify_batch(batch, calendar)


@pytest.mark.parametrize("change", ["receipt_hash", "strategy_hash"])
def test_changed_execution_receipt_is_rejected(saved_batch, change):
    batch, calendar, _ = saved_batch
    path = batch / "execution-admission.json"
    receipt = read_json(path)
    if change == "receipt_hash":
        receipt["receipt_hash"] = "0" * 64
    else:
        receipt["bindings"]["strategy_hash"] = "0" * 64
        receipt["receipt_hash"] = canonical_hash({k: v for k, v in receipt.items() if k != "receipt_hash"})
    write_json(path, receipt)
    with pytest.raises(ValueError, match="EXECUTION_RECEIPT_CHANGED"):
        report.verify_batch(batch, calendar)


def test_changed_plan_is_rejected(saved_batch):
    batch, calendar, _ = saved_batch
    write_json(batch / "plan.json", dict(runs=[], plan_hash=canonical_hash([])))
    with pytest.raises(ValueError, match="INCOMPLETE_OR_CHANGED_PLAN"):
        report.verify_batch(batch, calendar)


def _four_annual_rows():
    returns = (0.10, -0.10, 0.20, -0.05)
    mdds = (0.10, 0.20, 0.15, 0.30)
    buys, sells, days, opens = (2, 3, 4, 5), (1, 2, 4, 3), (3, 8, 20, 9), (1, 1, 0, 2)
    return [dict(family="basic", entry_id="BREAKOUT_20", exit_id="PCT_3_6",
                 max_holding_months=3, window=f"year_{year}", status="SUCCEEDED",
                 metrics=dict(total_return=returns[index], max_drawdown=mdds[index]),
                 statistics=dict(buy_count=buys[index], sell_count=sells[index],
                                 completed_trades=sells[index], holding_days_sum=days[index],
                                 open_positions=opens[index]))
            for index, year in enumerate(range(2020, 2024))]


def test_annual_strategy_totals_sum_fills_but_average_independent_year_returns():
    annual = report.annual_strategy_totals(_four_annual_rows())
    assert len(annual) == 1
    value = annual[0]
    assert value["status"] == "COMPLETE_4_YEARS"
    assert value["successful_years"] == 4
    assert value["mean_annual_return"] == pytest.approx(0.0375)
    assert value["mean_annual_return"] != pytest.approx(1.10 * 0.90 * 1.20 * 0.95 - 1)
    assert value["worst_annual_mdd"] == pytest.approx(0.30)
    assert (value["buy_count"], value["sell_count"], value["completed_trades"]) == (14, 10, 10)
    assert value["mean_holding_days"] == pytest.approx(4.0)
    assert value["year_end_open_positions_sum"] == 4


@pytest.mark.parametrize("incomplete", ["missing", "blocked", "duplicate"])
def test_annual_strategy_totals_withhold_four_year_totals(incomplete):
    rows = _four_annual_rows()
    if incomplete == "missing":
        rows.pop()
    elif incomplete == "blocked":
        rows[-1]["status"] = "BLOCKED"
        rows[-1].pop("metrics")
        rows[-1].pop("statistics")
    else:
        rows[-1]["window"] = "year_2022"
    value = report.annual_strategy_totals(rows)[0]
    assert value["status"] == "INCOMPLETE"
    assert value["successful_years"] == (3 if incomplete == "blocked" else len(rows))
    assert all(value[name] is None for name in ("mean_annual_return", "worst_annual_mdd",
                                                "buy_count", "sell_count", "completed_trades",
                                                "mean_holding_days", "year_end_open_positions_sum"))
