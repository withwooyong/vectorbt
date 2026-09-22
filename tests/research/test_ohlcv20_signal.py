"""Checks that event dates, volume units and 60-session history cannot leak."""

import pandas as pd
import pytest

from research.krx_lab.ohlcv20_signal import build_ohlcv20_signals


def fixture_rows():
    days = list(pd.bdate_range("2023-01-02", periods=61))
    bars = [
        dict(
            date=day,
            code="000001",
            market="KOSPI",
            open=100,
            high=101,
            low=90,
            close=100,
            volume=100,
            turnover=100_000_000,
            eligible=True,
            can_signal=True,
        )
        for day in days
    ]
    bars[-1].update(open=110, high=111, low=99, close=110, volume=200)
    calendars = {"KOSPI": days, "KOSDAQ": days}
    empty_events = pd.DataFrame(
        columns=[
            "code",
            "effective_date",
            "price_factor",
            "volume_factor",
            "known_at",
            "known_before_close",
            "price_admitted",
            "volume_admitted",
        ]
    )
    return bars, days, calendars, empty_events


def test_signal_uses_complete_prior_sixty_days_and_signal_day_liquidity():
    bars, days, calendars, events = fixture_rows()
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert result["signals"].iloc[0]["signal_date"] == days[-1]
    assert len(result["signals"]) == 1
    assert result["signals"].iloc[0]["limit_price"] == 110
    assert result["signals"].iloc[0]["mean_turnover20"] == 100_000_000


def test_ex_date_price_and_volume_transforms_are_separate():
    bars, days, calendars, events = fixture_rows()
    bars[-1].update(open=60, high=61, low=59, close=60, volume=400)
    events = pd.DataFrame(
        [
            dict(
                code="000001",
                effective_date=days[-1],
                price_factor="0.5",
                volume_factor="2",
                known_at=days[-1],
                known_before_close=True,
                price_admitted=True,
                volume_admitted=True,
            )
        ]
    )
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert len(result["signals"]) == 1  # 60 vs adjusted prior close 50
    bars[-1]["volume"] = 399
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert result["signals"].empty  # prior volume 100 becomes 200


def test_unadmitted_and_future_events_block_signal():
    bars, days, calendars, events = fixture_rows()
    events = pd.DataFrame(
        [
            dict(
                code="000001",
                effective_date=days[-1],
                price_factor="1",
                volume_factor="1",
                known_at=days[-1],
                known_before_close=True,
                price_admitted=False,
                volume_admitted=True,
            )
        ]
    )
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert result["signals"].empty
    assert result["skipped"].iloc[0]["reason"] == "UNADMITTED_OR_FUTURE_FACTOR"
    events.loc[0, "price_admitted"] = True
    events.loc[0, "known_at"] = days[-1] + pd.Timedelta(days=1)
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert result["signals"].empty


def test_same_day_after_close_notice_cannot_enter_signal():
    bars, days, calendars, _ = fixture_rows()
    events = pd.DataFrame(
        [
            dict(
                code="000001",
                effective_date=days[-1],
                price_factor="1",
                volume_factor="1",
                known_at=days[-1],
                known_before_close=False,
                price_admitted=True,
                volume_admitted=True,
            )
        ]
    )
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert result["signals"].empty
    assert result["skipped"].iloc[0]["reason"] == "UNADMITTED_OR_FUTURE_FACTOR"


def test_observed_zero_turnover_stays_in_twenty_session_average():
    bars, days, calendars, events = fixture_rows()
    bars[-5]["turnover"] = 0
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert len(result["signals"]) == 1
    assert result["signals"].iloc[0]["mean_turnover20"] == 95_000_000


def test_missing_session_is_skipped_and_caller_must_certify_event_coverage():
    bars, days, calendars, events = fixture_rows()
    with pytest.raises(ValueError, match="CORPORATE_EVENT_COVERAGE_NOT_CERTIFIED"):
        build_ohlcv20_signals(
            pd.DataFrame(bars), events, calendars, corporate_coverage_certified=False
        )
    bars.pop(20)
    result = build_ohlcv20_signals(
        pd.DataFrame(bars), events, calendars, corporate_coverage_certified=True
    )
    assert result["signals"].empty
