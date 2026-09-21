"""KRX v3 execution-rule regressions using the sealed read-only rule evidence."""
from decimal import Decimal
import json
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab.v3_market import V3MarketRules, raw_bar_eligibility


_EVIDENCE = (Path(__file__).parents[2] / "docs" / "strategy-research" / "backtest-lab"
             / "postgresql-readiness-2026-09-21" / "data" / "results.json")


@pytest.fixture
def rows():
    report = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
    return next(section["data"] for section in report if section["check"] == "rules")


@pytest.fixture
def rules(rows):
    return V3MarketRules(pd.DataFrame(rows))


@pytest.mark.parametrize("day,market,expected", [
    ("2015-06-14", "KOSPI", "0.15"),
    ("2015-06-15", "KOSDAQ", "0.30"),
    ("2023-12-31", "KOSPI", "0.30"),
])
def test_price_limit_boundary(rules, day, market, expected):
    assert rules.price_limit(day, market) == Decimal(expected)
    assert rules.settlement_sessions(day, market) == 2


@pytest.mark.parametrize("day,market,price,expected", [
    ("2023-01-24", "KOSPI", 2000, "5"),
    ("2023-01-24", "KOSDAQ", 100000, "100"),
    ("2023-01-24", "KOSPI", 100000, "500"),
    ("2023-01-25", "KOSDAQ", 100000, "100"),
    ("2023-01-25", "KOSPI", 100000, "100"),
    ("2023-01-25", "KOSPI", 200000, "500"),
    ("2023-01-25", "KOSDAQ", 500000, "1000"),
])
def test_tick_market_and_reform_boundaries(rules, day, market, price, expected):
    assert rules.tick(day, market, price) == Decimal(expected)


@pytest.mark.parametrize("day,market,expected", [
    ("2019-06-02", "KOSPI", "3000"),
    ("2019-06-03", "KOSPI", "2500"),
    ("2021-01-01", "KOSDAQ", "2300"),
    ("2023-01-01", "KOSDAQ", "2000"),
])
def test_sell_tax_by_market_and_day(rules, day, market, expected):
    # 1m KRW * .00015 = 150 KRW, then truncated to 150 KRW.
    amounts = rules.fees(day, market, "SELL", Decimal("1000000"))
    assert amounts == {"fee": Decimal("150"), "tax": Decimal(expected),
                       "total": Decimal("150") + Decimal(expected)}


def test_commission_truncation_and_unrounded_tax(rules):
    value = Decimal("123456")
    assert rules.fees("2023-12-29", "KOSPI", "BUY", value) == {
        "fee": Decimal("10"), "tax": Decimal("0"), "total": Decimal("10")}
    assert rules.fees("2023-12-29", "KOSPI", "SELL", value) == {
        "fee": Decimal("10"), "tax": Decimal("246.912"), "total": Decimal("256.912")}


def test_rule_gap_overlap_and_lock_are_errors(rows):
    rules = V3MarketRules(rows)
    with pytest.raises(ValueError, match="outside sealed"):
        rules.fees("2024-01-02", "KOSPI", "BUY", 1000000)
    with pytest.raises(ValueError, match="found 0"):
        rules.fees("2014-06-01", "KOSPI", "SELL", 1000000)
    with pytest.raises(ValueError, match="Unsupported v3 market"):
        rules.tick("2023-01-25", "NXT", 1000)
    duplicate = next(row for row in rows if row["rule_kind"] == "TICK_SIZE"
                     and row["market"] == "ALL").copy()
    duplicate["market"] = "KOSPI"
    with pytest.raises(ValueError, match="found 2"):
        V3MarketRules([*rows, duplicate]).tick("2023-01-25", "KOSPI", 1000)


def test_json_rule_values_and_bad_inputs(rows):
    encoded = [{**row, "rule_value": json.dumps(row["rule_value"])} for row in rows]
    rules = V3MarketRules(encoded)
    assert rules.tick("2023-01-25", "KOSDAQ", 2000) == Decimal("5")
    with pytest.raises(ValueError, match="Trade value"):
        rules.fees("2023-01-25", "KOSPI", "BUY", -1)
    with pytest.raises(ValueError, match="Price must be positive"):
        rules.tick("2023-01-25", "KOSPI", 0)


def test_raw_bar_orderability():
    valid = dict(open_price=100, high_price=110, low_price=90, close_price=105, trade_volume=1200)
    assert raw_bar_eligibility(valid)
    assert raw_bar_eligibility(dict(open=100, high=110, low=90, close=105, volume=1200))
    assert not raw_bar_eligibility({**valid, "trade_volume": 0})
    assert not raw_bar_eligibility({**valid, "open_price": 0, "trade_volume": 10})
    assert not raw_bar_eligibility({**valid, "high_price": 99})
    assert not raw_bar_eligibility({**valid, "close_price": float("nan")})
    assert not raw_bar_eligibility({**valid, "daily_state": "HALTED"})
    assert not raw_bar_eligibility(valid, status="PARTIAL_TRADING")
