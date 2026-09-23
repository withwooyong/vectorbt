from decimal import Decimal

import pandas as pd

from research.krx_lab.extension_signals import (
    apply_breakout_market_filter,
    benchmark_above_sma200,
    monthly_relative_momentum,
    prior_20_low_exit,
)


def _calendar():
    return pd.DataFrame({"date": pd.bdate_range("2020-01-01", "2021-03-31")})


def _prices():
    dates = _calendar().date
    rows = []
    for code, multiplier in (("a", 2.0), ("b", 2.0), ("c", 1.5)):
        for number, date in enumerate(dates):
            rows.append({"date": date, "instrument_id": code, "adjusted_close": 100 + multiplier * number,
                         "eligible": True, "input_blocked": False, "issue_blocked": False})
    return pd.DataFrame(rows)


def test_monthly_momentum_combines_markets_is_deterministic_and_avoids_final_month():
    value = _prices()
    result = monthly_relative_momentum(value, _calendar(), top_n=2)
    final = pd.Timestamp("2021-03-31")
    assert result.loc[result.date.eq(final), "MOMENTUM_ENTRY"].any()
    # February is a completed rebalance; equal returns select a before b.
    feb = result.loc[result.date.eq("2021-02-26")].set_index("instrument_id")
    assert feb.loc["a", "MOMENTUM_ENTRY"]
    assert feb.loc["b", "MOMENTUM_ENTRY"]
    assert feb.loc["c", "MOMENTUM_EXIT"]
    assert result.loc[(result.instrument_id.eq("a")) & (result.date > pd.Timestamp("2021-02-26")), "target"].all()


def test_monthly_momentum_is_future_invariant_and_invalidates_gapped_history():
    value = _prices()
    baseline = monthly_relative_momentum(value, _calendar(), top_n=2)
    changed = value.copy()
    changed.loc[changed.date.ge("2021-03-01"), "adjusted_close"] *= 100
    assert baseline.loc[baseline.date.le("2021-02-26")].equals(
        monthly_relative_momentum(changed, _calendar(), top_n=2).loc[lambda x: x.date.le("2021-02-26")]
    )
    gap = value.loc[~((value.instrument_id == "a") & (value.date == pd.Timestamp("2020-06-01")))]
    gapped = monthly_relative_momentum(gap, _calendar(), top_n=3)
    assert not gapped.loc[(gapped.instrument_id == "a") & (gapped.date == pd.Timestamp("2021-02-26")), "MOMENTUM_ENTRY"].item()
    ineligible = value.copy()
    ineligible.loc[(ineligible.instrument_id == "a") & ineligible.date.eq("2021-02-26"), "eligible"] = False
    assert not monthly_relative_momentum(ineligible, _calendar(), top_n=3).loc[
        lambda x: x.instrument_id.eq("a") & x.date.eq("2021-02-26"), "MOMENTUM_ENTRY"
    ].item()
    for bad in (float("nan"), float("inf")):
        invalid = value.copy()
        invalid.loc[(invalid.instrument_id == "a") & invalid.date.eq("2020-06-01"), "adjusted_close"] = bad
        assert not monthly_relative_momentum(invalid, _calendar(), top_n=3).loc[
            lambda x: x.instrument_id.eq("a") & x.date.eq("2021-02-26"), "MOMENTUM_ENTRY"
        ].item()


def test_momentum_uses_t_minus_1_over_t_minus_12_not_thirteen_months():
    value = _prices()
    # On 2021-02-26, the endpoints are 2021-01-29 and 2020-02-28.
    values = {("a", "2020-01-31"): 100, ("a", "2020-02-28"): 50, ("a", "2021-01-29"): 100,
              ("b", "2020-01-31"): 50, ("b", "2020-02-28"): 100, ("b", "2021-01-29"): 150,
              ("c", "2020-02-28"): 100, ("c", "2021-01-29"): 101}
    for (code, date), close in values.items():
        value.loc[(value.instrument_id == code) & value.date.eq(date), "adjusted_close"] = close
    selected = monthly_relative_momentum(value, _calendar(), top_n=1).loc[
        lambda x: x.date.eq("2021-02-26"), ["instrument_id", "MOMENTUM_ENTRY"]
    ].set_index("instrument_id").MOMENTUM_ENTRY
    assert selected.to_dict() == {"a": True, "b": False, "c": False}


def test_prior_low20_exit_is_causal():
    dates = pd.bdate_range("2021-01-01", periods=22)
    prices = pd.DataFrame({"date": dates, "instrument_id": "a", "adjusted_low": [10] * 21 + [9], "adjusted_close": [11] * 20 + [9, 20]})
    result = prior_20_low_exit(prices, calendar=pd.DataFrame({"date": dates}))
    assert result.LOW20_VALID.tolist() == [False] * 20 + [True, True]
    assert result.LOW20_EXIT.tolist() == [False] * 20 + [True, False]
    gapped = prices.drop(index=10)
    assert not prior_20_low_exit(gapped, calendar=pd.DataFrame({"date": dates})).loc[
        lambda x: x.date.eq(dates[21]), "LOW20_VALID"
    ].item()
    nonpositive = prices.copy()
    nonpositive.loc[10, "adjusted_low"] = 0
    assert not prior_20_low_exit(nonpositive, calendar=pd.DataFrame({"date": dates})).loc[
        lambda x: x.date.eq(dates[21]), "LOW20_VALID"
    ].item()


def test_market_filter_requires_200_bars_and_gates_each_market():
    dates = pd.bdate_range("2020-01-01", periods=201)
    benchmark = pd.concat([
        pd.DataFrame({"date": dates, "market": "KOSPI", "close": [Decimal(value) for value in range(100, 301)]}),
        pd.DataFrame({"date": dates, "market": "KOSDAQ", "close": [Decimal(value) for value in range(300, 99, -1)]}),
    ], ignore_index=True)
    filter_ = benchmark_above_sma200(benchmark)
    assert not filter_.loc[filter_.date.eq(dates[198]), "MARKET_ABOVE_SMA200"].any()
    last = filter_.loc[filter_.date.eq(dates[-1])].set_index("market").MARKET_ABOVE_SMA200
    assert last.to_dict() == {"KOSDAQ": False, "KOSPI": True}
    signals = pd.DataFrame({"date": [dates[-1], dates[-1]], "instrument_id": ["a", "b"],
                            "market": ["KOSPI", "KOSDAQ"], "BREAKOUT_20": [True, True], "BREAKOUT_60": [True, True]})
    gated = apply_breakout_market_filter(signals, filter_)
    assert gated.BREAKOUT_20_MARKET200.tolist() == [True, False]
    assert gated.BREAKOUT_60_MARKET200.tolist() == [True, False]
