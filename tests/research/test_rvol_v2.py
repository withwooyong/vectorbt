import numpy as np
import pandas as pd
import pytest

from research.krx_lab.config import ENTRIES as V1_ENTRIES
from research.krx_lab.config_v2 import (
    ENTRIES,
    WIDE_EXITS,
    default_config,
    default_wide_config,
    load_config,
    load_wide_config,
    primary_runs,
)
from research.krx_lab.io import write_json
from research.krx_lab.strategies import ENTRY_IDS, RVOL_ENTRY_IDS, V2_ENTRY_IDS, build_signals


def _prices(n=301):
    dates = pd.bdate_range("2024-01-02", periods=n)
    close = np.arange(100.0, 100.0 + n)
    return pd.DataFrame({
        "date": dates, "code": "A", "open": close - 0.5, "high": close + 1,
        "low": close - 1, "close": close, "volume": 200_000.0,
    })


def test_v1_default_output_and_catalog_are_unchanged():
    prices = _prices()
    baseline = build_signals(prices)
    explicit = build_signals(prices, entry_ids=ENTRY_IDS)
    pd.testing.assert_frame_equal(baseline, explicit)
    assert ENTRY_IDS == V1_ENTRIES
    assert len(ENTRY_IDS) == 12
    assert list(baseline.columns[-14:]) == ["atr14", "avg_volume20", *ENTRY_IDS]


@pytest.mark.parametrize("entry_id", RVOL_ENTRY_IDS)
def test_rvol_uses_twenty_prior_volumes_and_excludes_current_day(entry_id):
    prices = _prices()
    prices.loc[prices.index[-1], "volume"] = 300_000.0
    result = build_signals(prices, entry_ids=V2_ENTRY_IDS)
    assert result.loc[result.index[-1], entry_id]

    # If the current 300k volume were included, the denominator would be 205k
    # and RVOL would fall below 1.5.  A lower current volume must fail instead.
    low_current = prices.copy()
    low_current.loc[low_current.index[-1], "volume"] = 299_999.0
    low_result = build_signals(low_current, entry_ids=V2_ENTRY_IDS)
    assert not low_result.loc[low_result.index[-1], entry_id]


def test_rvol_missing_prior_volume_blocks_the_candidate_and_future_data_is_irrelevant():
    prices = _prices()
    prices.loc[prices.index[-1], "volume"] = 300_000.0
    prices.loc[prices.index[-2], "volume"] = np.nan
    blocked = build_signals(prices, entry_ids=V2_ENTRY_IDS)
    assert not blocked.loc[blocked.index[-1], list(RVOL_ENTRY_IDS)].any()

    clean = _prices()
    clean.loc[clean.index[-1], "volume"] = 300_000.0
    prefix = build_signals(clean, entry_ids=V2_ENTRY_IDS)
    future = _prices(20).assign(date=lambda frame: frame.date + pd.offsets.BDay(500), volume=9_999_999.0)
    extended = build_signals(pd.concat([clean, future], ignore_index=True), entry_ids=V2_ENTRY_IDS)
    pd.testing.assert_frame_equal(prefix, extended.iloc[: len(prefix)].reset_index(drop=True))


def test_v2_config_has_56_fixed_candidates_and_952_primary_comparisons(tmp_path):
    config_path = tmp_path / "config-v2.json"
    write_json(config_path, default_config(tmp_path / "snapshot"))
    config = load_config(config_path)
    runs = primary_runs(config)
    assert len(ENTRIES) == 14
    assert len(ENTRIES) * 4 == 56
    assert len(runs) == 952
    assert sum(run["phase"] == "development" for run in runs) == 56
    assert sum(run["phase"] == "validation" for run in runs) == 896
    assert config["sector_cap"] is None
    assert config["execution_admitted"] is False
    assert config["development"][0] == "2015-06-15"


def test_v2_config_rejects_candidate_or_execution_changes(tmp_path):
    config_path = tmp_path / "config-v2.json"
    config = default_config(tmp_path / "snapshot")
    config["entries"] = config["entries"][:-1]
    write_json(config_path, config)
    with pytest.raises(ValueError, match="48개 기준선"):
        load_config(config_path)

    config = default_config(tmp_path / "snapshot")
    config["execution_admitted"] = True
    write_json(config_path, config)
    with pytest.raises(ValueError, match="REAL execution"):
        load_config(config_path)


def test_v2_config_immutable_execution_policy_and_primary_runs_revalidate(tmp_path):
    config_path = tmp_path / "config-v2.json"
    config = default_config(tmp_path / "snapshot")
    config["holdout"]["unused_confirmed"] = True
    write_json(config_path, config)
    with pytest.raises(ValueError, match="holdout"):
        load_config(config_path)

    config = default_config(tmp_path / "snapshot")
    config["worker_count"] = True
    write_json(config_path, config)
    with pytest.raises(ValueError, match="boolean이 아닌 정수"):
        load_config(config_path)

    config = default_config(tmp_path / "snapshot")
    config["cost_model"] = "REALISTIC"
    with pytest.raises(ValueError, match="cost_model"):
        primary_runs(config)


def test_wide_exit_config_is_a_separate_56_candidate_952_comparison_experiment(tmp_path):
    config_path = tmp_path / "wide-config.json"
    write_json(config_path, default_wide_config(tmp_path / "snapshot"))
    config = load_wide_config(config_path)
    runs = primary_runs(config)
    assert config["schema_version"] != default_config(tmp_path / "snapshot")["schema_version"]
    assert config["selection_policy"] == "selection_policy_wide_exits_v1"
    assert tuple(config["exits"]) == WIDE_EXITS
    assert len(ENTRIES) * len(WIDE_EXITS) == 56
    assert len(runs) == 952
    with pytest.raises(ValueError, match="krx-breakout-rvol-v2"):
        load_config(config_path)
