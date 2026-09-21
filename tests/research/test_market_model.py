import copy
import json
from pathlib import Path

import pandas as pd
import pytest

from research.krx_lab.execution import simulate_delivery
from research.krx_lab.market_model import MarketModel


def fixture():
    delivery = json.loads((Path(__file__).parent / "fixtures/contracts_v1/delivery.json").read_text(encoding="utf-8"))
    delivery["events"] = []
    for row in delivery["prices"]:
        for name in ("open", "high", "low", "close", "adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close"):
            row[name] = 100
    return delivery


@pytest.mark.parametrize("field,value", [("settlement_delay_days", 2), ("lot_size", 10), ("slippage_bps", 1)])
def test_unsupported_profile_is_never_silently_approximated(field, value):
    delivery = fixture()
    delivery["market_profiles"][0][field] = value
    with pytest.raises(ValueError, match="UNSUPPORTED_EXECUTION_PROFILE"):
        MarketModel(delivery)


def test_dated_profiles_change_trade_costs_and_tick_quantization():
    delivery = fixture()
    first = delivery["market_profiles"][0]
    first.update(buy_fee_rate=0.01, effective_to="2023-01-03")
    delivery["market_profiles"].append(dict(first, profile_id="second", effective_from="2023-01-04",
        effective_to=None, tick_size=5, sell_fee_rate=0.02, sell_tax_rate=0.03))
    for row in delivery["prices"]:
        if row["date"] >= "2023-01-04":
            for name in ("open", "high", "low", "close", "adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close"):
                row[name] = 115
    signals = pd.DataFrame([dict(date="2023-01-02", instrument_id="SYN-ID-001", atr14=4,
                                avg_volume20=1_000_000, entry=True)])
    result = simulate_delivery(delivery, signals, entry_id="entry", exit_id="PCT_3_6",
                               start="2023-01-02", end="2023-01-05", initial_cash=25_000)
    buy, sell = result["fills"].to_dict("records")
    # 1,000 allocation / 101 total unit cost -> 9 shares, fee 9.
    # Old target 106 becomes ceil-to-5 110; sell gross 990, fee 19.8, tax 29.7.
    assert buy["quantity"] == 9
    assert buy["fee"] == 9
    assert sell["price"] == 110
    assert sell["fee"] == pytest.approx(19.8)
    assert sell["tax"] == pytest.approx(29.7)
    assert result["equity"].iloc[-1]["cash"] == pytest.approx(25_031.5)
    assert result["trades"].iloc[0]["pnl"] == pytest.approx(31.5)


def test_missing_or_overlapping_profile_and_code_mapping_fail_closed():
    delivery = fixture()
    second = copy.deepcopy(delivery["market_profiles"][0])
    second["profile_id"] = "overlap"
    delivery["market_profiles"].append(second)
    with pytest.raises(ValueError, match="MISSING_OR_AMBIGUOUS_INTERVAL"):
        MarketModel(delivery).prepare_prices()
    delivery["market_profiles"] = []
    with pytest.raises(ValueError, match="MISSING_OR_AMBIGUOUS_INTERVAL"):
        MarketModel(delivery).prepare_prices()
    delivery = fixture()
    delivery["prices"][0]["code"] = "WRONG"
    with pytest.raises(ValueError, match="CODE_MAPPING_MISMATCH"):
        MarketModel(delivery).prepare_prices()


def test_unexplained_missing_trading_row_and_off_tick_prices_fail_closed():
    delivery = fixture()
    delivery["prices"].pop()
    with pytest.raises(ValueError, match="UNEXPLAINED_MISSING_TRADING_PRICE"):
        MarketModel(delivery).prepare_prices()
    delivery = fixture()
    delivery["market_profiles"][0]["tick_size"] = 3
    with pytest.raises(ValueError, match="OFF_TICK_PRICE"):
        MarketModel(delivery).prepare_prices()
