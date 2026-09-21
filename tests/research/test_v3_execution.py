"""Independent cash, settlement, and blocked-path oracles for v3 execution."""
import json
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab import v3_execution as engine
from research.krx_lab.v3_execution import PreparedExecution, audit_execution_ledger, simulate_real_slot
from research.krx_lab.v3_market import V3MarketRules
from research.krx_lab.metrics import calculate_metrics


_EVIDENCE = (Path(__file__).parents[2] / "docs" / "strategy-research" / "backtest-lab"
             / "postgresql-readiness-2026-09-21" / "data" / "results.json")
_DAYS = ["2023-01-25", "2023-01-26", "2023-01-27", "2023-01-30", "2023-01-31"]


@pytest.fixture
def rules():
    report = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
    return V3MarketRules(next(item["data"] for item in report if item["check"] == "rules"))


def prepared(*, entry_open=100, entry_high=107, entry_low=99, next_volume=1000,
             atr=2, avg_volume=10_000_000, events=None):
    prices = pd.DataFrame([dict(date=day, instrument_id="1", code="000001", market="KOSPI",
                                raw_open=entry_open if day == _DAYS[1] else 100,
                                raw_high=entry_high if day == _DAYS[1] else 102,
                                raw_low=entry_low if day == _DAYS[1] else 98,
                                raw_close=100, volume=next_volume if day == _DAYS[2] else 1000,
                                status="TRADING", eligible=True) for day in _DAYS])
    signals = pd.DataFrame([dict(date=_DAYS[0], instrument_id="1", code="000001", close=100,
                                 atr14=atr, avg_volume20=avg_volume, ENTRY=True)])
    return PreparedExecution(prices, signals, _DAYS, events=events)


def run(data, rules, *, exit_id="PCT_3_6", cost_bps=None):
    return simulate_real_slot(data, rules, entry_id="ENTRY", exit_id=exit_id,
                              start=_DAYS[1], end=_DAYS[-1], cost_bps=cost_bps)


def test_fee_tax_and_t2_ledger_hand_oracle(rules):
    result = run(prepared(), rules)
    assert result["status"] == "SUCCEEDED"
    assert result["source_kind"] == "REAL"
    assert list(result["fills"]["code"]) == ["1", "1"]
    buy, sell = result["fills"].to_dict("records")
    assert (buy["size"], buy["price"], buy["fee"], buy["tax"]) == (10000, Decimal(100), Decimal(150), Decimal(0))
    assert (sell["price"], sell["fee"], sell["tax"]) == (Decimal(106), Decimal(150), Decimal(2120))
    assert result["trades"].iloc[0]["pnl"] == Decimal(57580)
    first = result["equity"].iloc[0]
    assert first["settled_cash"] == Decimal(100_000_000)
    assert first["receivables"] == Decimal(1_057_730)
    assert first["payables"] == Decimal(1_000_150)
    assert first["cash"] == first["equity"] == Decimal(100_057_580)
    settled = result["equity"].loc[result["equity"]["date"] == pd.Timestamp(_DAYS[3])].iloc[0]
    assert (settled["settled_cash"], settled["receivables"], settled["payables"]) == (
        Decimal(100_057_580), Decimal(0), Decimal(0))
    assert result["cashflows"]["kind"].tolist().count("SETTLEMENT") == 2
    audit_execution_ledger(result)
    metrics = calculate_metrics(result)
    assert metrics["trade_count"] == 1
    assert metrics["total_fees"] == 300


def test_ledger_audit_detects_report_value_rewrite(rules):
    result = run(prepared(), rules)
    result["equity"].loc[0, "equity"] += Decimal(1)
    with pytest.raises(ValueError, match="Ledger identity mismatch"):
        audit_execution_ledger(result)


def test_all_result_tables_can_be_persisted(tmp_path, rules):
    result = run(prepared(), rules)
    for name, value in result.items():
        if isinstance(value, pd.DataFrame):
            value.to_parquet(tmp_path / f"{name}.parquet", index=False)
    assert pd.read_parquet(tmp_path / "fills.parquet").iloc[1]["tax"] == Decimal(2120)


def test_daily_hook_propagates_resource_stop(rules):
    observed = []

    def stop_on_second_day(event, payload):
        observed.append((event, payload["date"]))
        if payload["date"] == _DAYS[2]:
            raise RuntimeError("RESOURCE_STOP")

    with pytest.raises(RuntimeError, match="RESOURCE_STOP"):
        simulate_real_slot(prepared(), rules, entry_id="ENTRY", exit_id="PCT_3_6",
                           start=_DAYS[1], end=_DAYS[-1], hooks=stop_on_second_day)
    assert observed == [("simulation_day", _DAYS[1]), ("simulation_day", _DAYS[2])]


def test_ambiguous_candle_stops_first_and_gap_target_capped(rules):
    ambiguous = run(prepared(entry_high=107, entry_low=95), rules)
    assert ambiguous["fills"].iloc[1]["phase"] == "stop_intraday_ambiguous"
    assert ambiguous["fills"].iloc[1]["price"] == Decimal(97)
    assert ambiguous["trades"].iloc[0]["pnl"] == Decimal(-32230)
    gap = run(prepared(entry_open=100, entry_high=107), rules)
    assert gap["fills"].iloc[1]["price"] == Decimal(106)


def test_next_open_cap_and_invalid_entry_do_not_fill(rules):
    cap = run(prepared(entry_open=102), rules)
    assert cap["fills"].empty
    assert cap["plans"].iloc[0]["reason"] == "ENTRY_RANGE_OR_PRICE_RELATION"
    data = prepared()
    data.prices_by_day[pd.Timestamp(_DAYS[1])].loc["1", "volume"] = 0
    invalid = run(data, rules)
    assert invalid["fills"].empty
    assert invalid["plans"].iloc[0]["reason"] == "INVALID_ENTRY_RAW_BAR"


def test_price_limit_cache_does_not_cross_rule_sets(rules):
    data = prepared()
    normal = run(data, rules)
    altered = [{**row, "rule_value": {"percent": 5} if row["rule_kind"] == "PRICE_LIMIT"
                and row["effective_from"].year == 2015 else row["rule_value"]} for row in rules.rows]
    strict = V3MarketRules(altered)
    restricted = run(data, strict)
    assert len(normal["fills"]) == 2
    assert restricted["fills"].empty
    assert restricted["plans"].iloc[0]["reason"] == "OUT_OF_LIMIT"


def test_price_cache_is_bounded_and_eviction_keeps_values(monkeypatch):
    monkeypatch.setattr(engine, "_BAR_CACHE_LIMIT", 2)
    monkeypatch.setattr(engine, "_DAY_ARRAY_LIMIT", 1)
    data = prepared()
    first = data.price(pd.Timestamp(_DAYS[0]), "1")
    with pytest.raises(TypeError):
        first["close"] = 999
    for day in _DAYS[1:]:
        assert data.price(pd.Timestamp(day), "1")["close"] == 100
        assert len(data._price_cache) <= 2
        assert len(data._price_arrays) <= 1
    assert data.price(pd.Timestamp(_DAYS[0]), "1")["close"] == first["close"]


def test_wide_exit_changes_risk_size(rules):
    data = prepared(entry_high=102, entry_low=99, atr=4, avg_volume=100_000_000)
    narrow = run(data, rules, exit_id="PCT_3_6")
    wide = run(data, rules, exit_id="ATR_4_8")
    assert narrow["fills"].iloc[0]["size"] > wide["fills"].iloc[0]["size"]
    assert wide["plans"].iloc[0]["stop_price"] == Decimal(84)
    assert wide["plans"].iloc[0]["target_price"] == Decimal(132)


def test_stress_cost_is_separate_from_dated_tax(rules):
    result = run(prepared(), rules, cost_bps=30)
    assert result["cost_model"] == "FLAT_BPS_STRESS_ONLY"
    assert set(result["fills"]["tax"]) == {Decimal(0)}
    assert result["fills"].iloc[0]["fee"] == Decimal(3000)


def test_unknown_held_mark_blocks_all_performance(rules):
    data = prepared(entry_high=103, entry_low=98, next_volume=0)
    data.prices_by_day[pd.Timestamp(_DAYS[2])].loc["1", "close"] = 0
    result = run(data, rules)
    assert result["status"] == "BLOCKED"
    assert not result["performance_valid"]
    assert result["equity"].empty and result["trades"].empty
    assert any("UNKNOWN_HELD_MARK:2023-01-27:1" in issue for issue in result["issues"])


def test_zero_volume_holds_with_raw_close_but_cannot_fill(rules):
    result = run(prepared(entry_high=103, entry_low=98, next_volume=0), rules)
    assert result["status"] == "SUCCEEDED"
    assert result["fills"]["side"].tolist() == ["buy"]
    assert any(issue.startswith("UNTRADEABLE_HELD_MARK") for issue in result["issues"])


def test_unresolved_held_event_blocks_performance(rules):
    events = [dict(instrument_id="1", effective_date=_DAYS[2], event_id="e1",
                   event_type="SPLIT", resolution_status="PARTIAL", quantity_ratio=2, sequence_no=1)]
    result = run(prepared(entry_high=103, entry_low=98, events=events), rules)
    assert result["status"] == "BLOCKED"
    assert result["equity"].empty
    assert any(issue.startswith("UNRESOLVED_HELD_EVENT") for issue in result["issues"])


def test_resolved_split_transforms_whole_position_before_new_session(rules):
    events = [dict(instrument_id="1", effective_date=_DAYS[2], announced_at="2023-01-24",
                   event_id="e2", event_type="SPLIT", resolution_status="RESOLVED",
                   quantity_ratio=2, reference_price=50, sequence_no=1)]
    data = prepared(entry_high=103, entry_low=98, events=events)
    row = data.prices_by_day[pd.Timestamp(_DAYS[2])]
    for name, value in (("open", 50), ("high", 51), ("low", 49), ("close", 50)):
        row.loc["1", name] = value
    result = simulate_real_slot(data, rules, entry_id="ENTRY", exit_id="PCT_3_6",
                                start=_DAYS[1], end=_DAYS[2])
    assert result["status"] == "SUCCEEDED"
    assert result["events"].iloc[0]["quantity_delta"] == 10000
    assert result["positions"].iloc[-1]["size"] == 20000
    assert result["positions"].iloc[-1]["stop_price"] == Decimal("48")
    assert result["equity"].iloc[-1]["equity"] == Decimal("99999850")


def test_resolved_label_without_announced_timing_blocks(rules):
    events = [dict(instrument_id="1", effective_date=_DAYS[2], event_id="e3",
                   event_type="REVERSE_SPLIT", resolution_status="RESOLVED",
                   quantity_ratio=Decimal("0.5"), sequence_no=1)]
    result = run(prepared(entry_high=103, entry_low=98, events=events), rules)
    assert result["status"] == "BLOCKED"
    assert any(issue.startswith("UNRESOLVED_HELD_EVENT") for issue in result["issues"])


def test_reference_share_fact_does_not_transform_owned_shares(rules):
    event = dict(instrument_id="1", effective_date=_DAYS[2], event_id="shares",
                 event_type="LISTED_SHARE_CHANGE", resolution_status="REFERENCE_FACT",
                 quantity_ratio=None, sequence_no=None)
    result = run(prepared(entry_high=103, entry_low=98, events=[event]), rules)
    assert result["status"] == "SUCCEEDED"
    assert result["positions"].iloc[-1]["size"] == 10000
    assert result["events"].empty


def test_pending_plan_adjusts_for_split_before_delayed_entry(rules):
    event = dict(instrument_id="1", effective_date=_DAYS[1], announced_at="2023-01-24",
                 event_id="split-before-entry", event_type="SPLIT", resolution_status="RESOLVED",
                 quantity_ratio=2, reference_price=50, sequence_no=1)
    data = prepared(events=[event])
    split_day = data.prices_by_day[pd.Timestamp(_DAYS[1])]
    for name, value in (("open", 50), ("high", 51), ("low", 49), ("close", 50)):
        split_day.loc["1", name] = value
    day = data.prices_by_day[pd.Timestamp(_DAYS[2])]
    for name, value in (("open", 50), ("high", 51), ("low", 49), ("close", 50)):
        day.loc["1", name] = value
    result = simulate_real_slot(data, rules, entry_id="ENTRY", exit_id="PCT_3_6",
                                start=_DAYS[1], end=_DAYS[2], delay=2)
    assert result["status"] == "SUCCEEDED"
    assert result["fills"].iloc[0]["price"] == Decimal(50)
    assert result["plans"].iloc[0]["entry_cap"] == Decimal("50.5")


def test_non_session_event_blocks_held_exposure(rules):
    event = dict(instrument_id="1", effective_date="2023-01-28", announced_at="2023-01-24",
                 event_id="weekend", event_type="SPLIT", resolution_status="RESOLVED",
                 quantity_ratio=2, sequence_no=1)
    result = run(prepared(entry_high=103, entry_low=98, events=[event]), rules)
    assert result["status"] == "BLOCKED"
    assert any(issue.startswith("NONSESSION_HELD_EVENT") for issue in result["issues"])


def test_each_threshold_uses_its_own_tick_band(rules):
    data = prepared(entry_high=2000, entry_low=1990, atr=100)
    data.signals.loc[0, "close"] = 1995
    signal_day = data.prices_by_day[pd.Timestamp(_DAYS[0])]
    for name, value in (("open", 1995), ("high", 2000), ("low", 1990), ("close", 1995)):
        signal_day.loc["1", name] = value
    entry = data.prices_by_day[pd.Timestamp(_DAYS[1])]
    for name, value in (("open", 1995), ("high", 2000), ("low", 1990), ("close", 1995)):
        entry.loc["1", name] = value
    result = run(data, rules)
    plan = result["plans"].iloc[0]
    assert plan["entry_cap"] == Decimal(2010)
    assert plan["stop_price"] == Decimal(1935)
    assert plan["target_price"] == Decimal(2115)


def test_requested_window_must_be_covered_by_prepared_calendar(rules):
    data = prepared()
    with pytest.raises(ValueError, match="prepared calendar coverage"):
        simulate_real_slot(data, rules, entry_id="ENTRY", exit_id="PCT_3_6",
                           start="2023-01-24", end="2023-01-31")
    with pytest.raises(ValueError, match="prepared calendar coverage"):
        simulate_real_slot(data, rules, entry_id="ENTRY", exit_id="PCT_3_6",
                           start="2023-01-25", end="2023-12-31")


def test_verified_source_bounds_allow_non_session_end(rules):
    data = prepared()
    prices = pd.concat(data.prices_by_day.values(), ignore_index=True)
    calendar = pd.DataFrame({"date": _DAYS, "market": "KRX"})
    bounded = PreparedExecution(prices, data.signals, calendar,
                                period_start="2023-01-24", period_end="2023-12-31")
    result = simulate_real_slot(bounded, rules, entry_id="ENTRY", exit_id="PCT_3_6",
                                start="2023-01-24", end="2023-12-31")
    assert result["status"] == "SUCCEEDED"


def test_rejects_locked_calendar(rules):
    data = prepared()
    with pytest.raises(ValueError, match="Post-2023"):
        PreparedExecution(data.signals, data.signals, [*_DAYS, "2024-01-02"])
