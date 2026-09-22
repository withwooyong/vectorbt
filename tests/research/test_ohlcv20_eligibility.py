import hashlib
import json

import pandas as pd
import pytest

from research.krx_lab.ohlcv20_eligibility import (
    attach_daily_eligibility,
    load_sealed_krx_calendar,
)


SHA = "a" * 64


def _inputs():
    days = pd.DatetimeIndex(["2015-06-30", "2015-07-01", "2015-07-02"])
    bars = pd.DataFrame(
        [
            dict(date=day, code="005930", market="KOSPI", close=1000, can_buy=True)
            for day in days
        ]
    )
    selected = pd.DataFrame([dict(code="005930", market="KOSPI", month="2015-07")])
    meta = pd.DataFrame(
        [
            dict(
                observed_date=day,
                short_code="005930",
                market="KOSPI",
                share_class="보통주",
                security_group="주권",
                listed_shares=100_000_000,
            )
            for day in days
        ]
    )
    return bars, selected, days, meta


def test_month_boundary_uses_current_rank_and_previous_session_facts():
    bars, selected, days, meta = _inputs()
    result = attach_daily_eligibility(bars, selected, days, meta, metadata_sha256=SHA)
    assert result.bars["signal_eligible"].tolist() == [False, True, True]
    assert result.bars["order_eligible"].tolist() == [False, True, True]
    assert result.missing_daily_metadata == 0


def test_order_never_uses_its_own_fresh_share_count():
    bars, selected, days, meta = _inputs()
    meta.loc[0, "listed_shares"] = 99_999_999
    result = attach_daily_eligibility(bars, selected, days, meta, metadata_sha256=SHA)
    assert result.bars["signal_eligible"].tolist() == [False, True, True]
    assert result.bars["order_eligible"].tolist() == [False, False, True]


def test_missing_daily_metadata_fails_closed():
    bars, selected, days, meta = _inputs()
    meta = meta.iloc[[0, 2]]
    result = attach_daily_eligibility(bars, selected, days, meta, metadata_sha256=SHA)
    assert result.bars["signal_eligible"].tolist() == [False, False, True]
    assert result.bars["order_eligible"].tolist() == [False, True, False]
    assert result.missing_daily_metadata == 1


def test_rejects_duplicate_daily_metadata():
    bars, selected, days, meta = _inputs()
    meta = pd.concat([meta, meta.iloc[[0]]], ignore_index=True)
    with pytest.raises(ValueError, match="DUPLICATE_DAILY_INSTRUMENT_FACT"):
        attach_daily_eligibility(bars, selected, days, meta, metadata_sha256=SHA)


def test_market_transfer_cannot_inherit_other_markets_monthly_selection():
    bars, selected, days, meta = _inputs()
    bars.loc[2, "market"] = "KOSDAQ"
    meta.loc[2, "market"] = "KOSDAQ"
    result = attach_daily_eligibility(bars, selected, days, meta, metadata_sha256=SHA)
    assert result.bars["signal_eligible"].tolist() == [False, True, False]
    assert result.bars["order_eligible"].tolist() == [False, True, False]


def test_sealed_calendar_checks_manifest_and_part(tmp_path):
    part = tmp_path / "calendar.parquet"
    pd.DataFrame(
        [
            dict(trading_date="2015-06-15", market="KRX", is_open=True),
            dict(trading_date="2015-06-16", market="KRX", is_open=False),
        ]
    ).to_parquet(part)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            dict(
                parts=[
                    dict(
                        file=part.name,
                        member_kind="CALENDAR",
                        rows=2,
                        sha256=hashlib.sha256(part.read_bytes()).hexdigest(),
                    )
                ]
            )
        )
    )
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert load_sealed_krx_calendar(tmp_path, digest).tolist() == [
        pd.Timestamp("2015-06-15")
    ]
    part.write_bytes(part.read_bytes() + b"tamper")
    with pytest.raises(ValueError, match="CALENDAR_PART_HASH_MISMATCH"):
        load_sealed_krx_calendar(tmp_path, digest)
