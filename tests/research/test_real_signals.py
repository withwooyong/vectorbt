"""Offline checks for REAL C1 signal preparation; no market observation or P&L."""

from __future__ import annotations

from copy import deepcopy

import pandas as pd
import pytest

from research.krx_lab.io import read_json
from research.krx_lab.real_signals import prepare_real_signals
from research.krx_lab.strategies import ENTRY_IDS
from tests.research.real_fixtures import create_real_shaped_input


def _delivery(tmp_path):
    return read_json(create_real_shaped_input(tmp_path / "input"))


def test_adjusted_prices_and_twelve_warmup_signals(tmp_path):
    delivery = _delivery(tmp_path)
    result = prepare_real_signals(delivery)
    first = result.iloc[0]
    assert first["source_kind"] == "REAL"
    assert first["close"] == delivery["prices"][0]["adjusted_close"]
    assert first["close"] != delivery["prices"][0]["close"]
    assert len(result) == 4
    assert len(ENTRY_IDS) == 12
    assert not result[list(ENTRY_IDS)].to_numpy().any()


def test_missing_open_session_remains_blank_and_breaks_history(tmp_path):
    delivery = _delivery(tmp_path)
    delivery["prices"] = [p for p in delivery["prices"] if p["date"] != "2023-01-03"]
    result = prepare_real_signals(delivery)
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2023-01-02", "2023-01-03", "2023-01-04", "2023-01-05"]
    missing = result.loc[result["date"] == pd.Timestamp("2023-01-03")].iloc[0]
    assert pd.isna(missing["close"])
    assert pd.isna(missing["volume"])
    assert not missing[list(ENTRY_IDS)].any()


def test_end_cutoff_precedes_signal_calculation_and_start_keeps_warmup(tmp_path, monkeypatch):
    delivery = _delivery(tmp_path)
    seen = {}

    def capture(prices):
        seen["dates"] = prices["date"].dt.strftime("%Y-%m-%d").tolist()
        return prices.assign(atr14=float("nan"), avg_volume20=float("nan"),
                             **{entry: False for entry in ENTRY_IDS})

    monkeypatch.setattr("research.krx_lab.real_signals.build_signals", capture)
    result = prepare_real_signals(delivery, start="2023-01-03", end="2023-01-04")
    assert seen["dates"] == ["2023-01-02", "2023-01-03", "2023-01-04"]
    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == ["2023-01-03", "2023-01-04"]


def test_wrong_source_and_unsupported_status_fail_closed(tmp_path):
    delivery = _delivery(tmp_path)
    delivery["source_kind"] = "SYNTHETIC"
    with pytest.raises(ValueError, match="REAL_SOURCE_REQUIRED"):
        prepare_real_signals(delivery)
    delivery["source_kind"] = "REAL"
    delivery["statuses"][0]["status"] = "HALTED"
    with pytest.raises(ValueError, match="UNSUPPORTED_STATUS_FOR_SIGNALS"):
        prepare_real_signals(delivery)


def test_repeated_instrument_intervals_are_processed_once_or_rejected(tmp_path):
    delivery = _delivery(tmp_path)
    initial = delivery["instruments"][0]
    initial["effective_to"] = "2023-01-03"
    resumed = deepcopy(initial)
    resumed["effective_from"] = "2023-01-04"
    resumed["effective_to"] = None
    delivery["instruments"].append(resumed)
    assert len(prepare_real_signals(delivery)) == 4

    resumed["effective_from"] = "2023-01-03"
    with pytest.raises(ValueError, match="INSTRUMENT_INTERVAL_OVERLAP"):
        prepare_real_signals(delivery)


@pytest.mark.parametrize("reuse_code", [False, True])
def test_indicator_warmup_resets_after_inactive_gap_or_code_reuse(tmp_path, reuse_code):
    delivery = _delivery(tmp_path)
    days = pd.bdate_range("2022-01-03", periods=252).strftime("%Y-%m-%d").tolist()
    delivery["metadata"].update(start=days[0], end=days[-1])
    calendar_template = delivery["calendar"][0]
    delivery["calendar"] = []
    for day in days:
        item = deepcopy(calendar_template)
        item.update(date=day, opens_at=f"{day}T09:00:00+09:00", closes_at=f"{day}T15:30:00+09:00")
        delivery["calendar"].append(item)

    first_id = delivery["instruments"][0]["instrument_id"]
    last_id = "OFFLINE-SPECIMEN-002" if reuse_code else first_id
    delivery["instruments"][0].update(effective_from=days[0], effective_to=days[249])
    last_instrument = deepcopy(delivery["instruments"][0])
    last_instrument.update(instrument_id=last_id, effective_from=days[251], effective_to=None)
    delivery["instruments"].append(last_instrument)
    delivery["statuses"][0].update(effective_from=days[0], effective_to=days[249])
    last_status = deepcopy(delivery["statuses"][0])
    last_status.update(status_id="trading-2", instrument_id=last_id,
                       effective_from=days[251], effective_to=days[251])
    delivery["statuses"].append(last_status)

    template = delivery["prices"][1]
    delivery["prices"] = []
    for day, identity, close in [(day, first_id, 10) for day in days[:250]] + [(days[251], last_id, 20)]:
        price = deepcopy(template)
        price.update(date=day, instrument_id=identity, open=close, high=close, low=close, close=close,
                     adjusted_open=close, adjusted_high=close, adjusted_low=close, adjusted_close=close,
                     price_factor=1, quantity_factor=1, volume=200_000, turnover=close * 200_000)
        delivery["prices"].append(price)

    signals = prepare_real_signals(delivery)
    final = signals.loc[signals["date"] == pd.Timestamp(days[251])].iloc[0]
    assert final["code"] == "OFFLINE001"
    assert final["instrument_id"] == last_id
    assert not final[list(ENTRY_IDS)].any()
    assert pd.isna(final["atr14"])
