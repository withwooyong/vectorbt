import json
from pathlib import Path

from research.krx_lab.metrics import ledger_summary, monthly_stats


FIXTURE = Path(__file__).parent / "fixtures" / "contracts_v1" / "expected-ledger.json"


def _ledger():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_ledger_summary_uses_cashflows_once_and_reports_settlement_state():
    ledger = _ledger()
    ledger["fills"][0]["fee"] = 999  # A cashflow already records the same fill fee.
    summary = ledger_summary({"contract_ledger": ledger})
    assert summary == {
        "date": "2023-01-05T00:00:00", "cash": 517, "receivables": 0, "payables": 0,
        "exposure": 480, "equity": 997, "open_positions": 1, "stale_positions": 0,
        "overdue_positions": 0, "total_fees": 1.0, "total_taxes": 2.0, "cost_source": "cashflows",
    }


def test_monthly_stats_handles_empty_and_uses_initial_cash_for_first_month():
    assert monthly_stats({"equity": []}, 1000).empty
    ledger = _ledger()
    monthly = monthly_stats({"equity": ledger["equity"]}, 1000)
    assert monthly.to_dict("records") == [{
        "month": "2023-01", "start_equity": 1000.0, "end_equity": 997.0,
        "pnl": -3.0, "return": -0.003, "is_loss": True,
    }]


def test_liquidated_positions_do_not_reappear_in_latest_summary():
    ledger = _ledger()
    ledger["equity"].append({"date": "2023-01-06", "cash": 997, "receivables": 0,
                             "payables": 0, "exposure": 0, "equity": 997})
    summary = ledger_summary({"contract_ledger": ledger})
    assert summary["open_positions"] == 0
    assert summary["stale_positions"] == 0


def test_legacy_position_size_alias_is_counted_only_when_positive():
    summary = ledger_summary({"equity": [{"date": "2023-01-02", "cash": 90, "equity": 100, "exposure": 10}],
                              "positions": [{"date": "2023-01-02", "code": "A", "size": 1, "mark_price": 10},
                                            {"date": "2023-01-02", "code": "B", "size": 0, "mark_price": 10}]})
    assert summary["open_positions"] == 1
