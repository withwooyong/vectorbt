import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest


SCRIPT = Path(__file__).with_name("research_backtest.py")
SPEC = importlib.util.spec_from_file_location("research_backtest", SCRIPT)
research = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = research
SPEC.loader.exec_module(research)


def test_demo_contract_and_timing(tmp_path):
    out = tmp_path / "out"
    subprocess.run([sys.executable, str(SCRIPT), "--demo", "--strategy", "all", "--cost-bps", "30", "--delay", "1", "--out", str(out), "--self-check"], check=True)
    orders = pd.read_csv(out / "orders.csv")
    summary = pd.read_csv(out / "summary.csv")
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["engine"]["portfolio"] == "numba"
    assert manifest["official_trading_calendar_verified"] is False
    assert "buyhold_total_return" in summary and "total_return" in summary
    for _, buy in orders[orders.status == "opened"].iterrows():
        dates = research.demo_data().date.reset_index(drop=True)
        assert dates[dates == pd.Timestamp(buy.date)].index[0] - dates[dates == pd.Timestamp(buy.signal_date)].index[0] == 1
    for strategy, sells in orders[orders.status == "closed"].groupby("strategy"):
        buys = orders[(orders.strategy == strategy) & (orders.status == "opened")]
        for _, sell in sells.iterrows():
            buy = buys[buys.signal_date == sell.signal_date].iloc[0]
            dates = research.demo_data().date.reset_index(drop=True)
            assert dates[dates == pd.Timestamp(sell.date)].index[0] - dates[dates == pd.Timestamp(buy.date)].index[0] == 10
    no_trade_out = tmp_path / "no-trade"
    subprocess.run([sys.executable, str(SCRIPT), "--demo", "--strategy", "T3", "--out", str(no_trade_out)], check=True)
    assert list(pd.read_csv(no_trade_out / "orders.csv").columns) == research.ORDER_COLUMNS
    no_trade_summary = pd.read_csv(no_trade_out / "summary.csv")
    assert no_trade_summary.loc[0, "opened_trades"] == 0
    assert pd.isna(no_trade_summary.loc[0, "sharpe_252_rf0_ddof1"])


@pytest.mark.parametrize("family,name,value", [(family, name, value) for family, pairs in research.VARIANTS.items() for name, value in pairs])
def test_all_signal_formulas_match_independent_pandas(family, name, value):
    frame = research.demo_data()
    close, volume = frame.close, frame.volume
    if family == "T1":
        fast, slow = close.rolling(value).mean(), close.rolling(20).mean()
        expected = (fast.shift(1) < slow.shift(1)) & (fast > slow)
    elif family == "T2":
        expected = close > close.shift(1).rolling(value).max()
    else:
        expected = (close > close.rolling(60).mean()) & ((close / close.shift(3) - 1) * 100 <= value)
    expected = (expected.fillna(False) & (volume.shift(1) >= 100_000)).rename(None)
    pd.testing.assert_series_equal(research.signals(frame, family, value).rename(None), expected)


@pytest.mark.parametrize("fee", [0.001, 0.005])
def test_delay_two_and_cost_scenarios(fee):
    result = research.run_one(research.demo_data(), "T2_PREV20_HIGH", "T2", 20, None, None, 2, fee)
    assert result.metrics["total_cost"] >= 0
    for order in [order for order in result.orders if order["status"] == "opened"]:
        dates = research.demo_data().date.reset_index(drop=True)
        assert dates[dates == pd.Timestamp(order["date"])].index[0] - dates[dates == pd.Timestamp(order["signal_date"])].index[0] == 2


def test_prefix_invariance_and_initial_mdd():
    data = research.demo_data()
    full = research.run_one(data, "T2_PREV20_HIGH", "T2", 20, "2024-03-01", None, 1, 0.003)
    beyond_end = research.run_one(data, "T2_PREV20_HIGH", "T2", 20, None, "2099-01-01", 1, 0.003)
    extended = research.run_one(pd.concat([data, data.tail(5).assign(date=lambda x: x.date + pd.offsets.BDay(130))], ignore_index=True), "T2_PREV20_HIGH", "T2", 20, "2024-03-01", data.date.iloc[-1].strftime("%Y-%m-%d"), 1, 0.003)
    pd.testing.assert_frame_equal(full.equity.reset_index(drop=True), extended.equity.reset_index(drop=True))
    assert beyond_end.equity.date.iloc[-1] == data.date.iloc[-1]
    assert research.metric_values(pd.Series(pd.to_datetime(["2024-01-01", "2024-01-02"])), pd.Series([0.9, 1.0]))["max_drawdown"] == pytest.approx(-0.1)
    one_day = research.run_one(data, "T3_PULLBACK_5", "T3", -5, "2024-07-01", "2024-07-01", 1, 0.003)
    assert one_day.metrics["total_return"] == 0
    assert pd.isna(one_day.metrics["sharpe_252_rf0_ddof1"])


def test_invalid_csv_and_pre_start_entry_rejected(tmp_path):
    bad = research.demo_data()
    bad.loc[2, "volume"] = 0
    path = tmp_path / "bad.csv"
    bad.to_csv(path, index=False)
    with pytest.raises(ValueError, match="0 이하"):
        research.load_csv(path)
    bad = research.demo_data()
    bad.loc[3, "high"] = bad.loc[3, "low"] / 2
    bad.to_csv(path, index=False)
    with pytest.raises(ValueError, match="고가/저가"):
        research.load_csv(path)
    result = research.run_one(research.demo_data(), "T1_SMA5_20", "T1", 5, "2024-04-01", None, 1, 0.003)
    assert pd.to_datetime(result.equity.date).min() == pd.Timestamp("2024-04-01")
    assert all(pd.Timestamp(order["date"]) >= pd.Timestamp("2024-04-01") for order in result.orders)
    no_orders = research.run_one(research.demo_data(), "T3_PULLBACK_5", "T3", -5, None, None, 1, 0.003)
    assert no_orders.orders == []
    assert list(pd.DataFrame(no_orders.orders, columns=research.ORDER_COLUMNS)) == research.ORDER_COLUMNS
