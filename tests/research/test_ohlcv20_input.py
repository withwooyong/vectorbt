import hashlib
import json

import pandas as pd
import pytest

from research.krx_lab.ohlcv20_input import load_corrected_v4


def _prices(rows):
    """Build flat daily bars whose adjusted close is stated per trading date."""
    frame = []
    for date, close, adjusted in rows:
        frame.append(
            dict(
                stock_code="005930",
                trading_date=date,
                adjusted=False,
                market="KOSPI",
                open_price=close,
                high_price=close,
                low_price=close,
                close_price=close,
                trade_volume=1000,
                trade_amount=close * 1000,
            )
        )
        frame.append(
            dict(
                stock_code="005930",
                trading_date=date,
                adjusted=True,
                market="KRX",
                open_price=adjusted,
                high_price=adjusted,
                low_price=adjusted,
                close_price=adjusted,
                trade_volume=1000,
                trade_amount=adjusted * 1000,
            )
        )
    return pd.DataFrame(frame)


def _audit(tmp_path, rows):
    """Write a synthetic factor-admission audit and report its own digest."""
    frame = pd.DataFrame(
        [
            dict(
                stock_code="005930",
                effective_date=date,
                price_factor=price_factor,
                volume_factor=volume_factor,
                price_admitted=price_admitted,
                volume_admitted=volume_admitted,
            )
            for date, price_factor, price_admitted, volume_factor, volume_admitted
            in rows
        ]
    )
    path = tmp_path / "factor-admission-audit.parquet"
    frame.to_parquet(path, index=False)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _package(tmp_path, price=None):
    folder = tmp_path / "corrected-input-v4"
    (folder / "prices").mkdir(parents=True)
    if price is None:
        price = pd.DataFrame(
            [
                dict(
                    stock_code="005930",
                    trading_date="2015-06-15",
                    adjusted=False,
                    market="KOSPI",
                    open_price=100,
                    high_price=110,
                    low_price=90,
                    close_price=105,
                    trade_volume=1000,
                    trade_amount=103000,
                ),
                dict(
                    stock_code="005930",
                    trading_date="2015-06-15",
                    adjusted=True,
                    market="KRX",
                    open_price=100,
                    high_price=110,
                    low_price=90,
                    close_price=105,
                    trade_volume=1000,
                    trade_amount=103,
                ),
            ]
        )
    selected = pd.DataFrame(
        [dict(stock_code="005930", market="KOSPI", month="2015-06")]
    )
    blocked = pd.DataFrame(
        columns=[
            "stock_code",
            "trading_date",
            "regular_session_execution_allowed",
            "valuation_or_entitlements_resolved",
        ]
    )
    files = [
        ("prices/price-00000.parquet", price),
        ("selected-months.parquet", selected),
        ("non-execution.parquet", blocked),
    ]
    entries = []
    for name, frame in files:
        path = folder / name
        frame.to_parquet(path, index=False)
        entries.append(
            dict(
                file=name,
                rows=len(frame),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    manifest = dict(
        schema="ohlcv-corrected-candidate-input-v1",
        real_execution_admitted=False,
        total_price_rows=len(price),
        files=entries,
    )
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return folder


def test_loads_verified_bars_without_granting_real_eligibility(tmp_path):
    value = load_corrected_v4(_package(tmp_path))
    bar = value.bars.iloc[0]
    assert len(value.bars) == 1
    assert bar["close"] == 105 and bar["turnover"] == 103000
    assert bool(bar["universe_selected"])
    assert bool(bar["can_buy"]) and bool(bar["mark_valid"])
    assert not bool(bar["adjusted_valid"]) and not bool(bar["order_eligible"])
    assert value.real_execution_admitted is False
    assert "DAILY_POINT_IN_TIME_ELIGIBILITY_UNVERIFIED" in value.issues


def test_rejects_tampered_source_part(tmp_path):
    folder = _package(tmp_path)
    path = folder / "selected-months.parquet"
    path.write_bytes(path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="MANIFEST_HASH_MISMATCH"):
        load_corrected_v4(folder)


def test_overlay_blocks_regular_session_and_unresolved_mark(tmp_path):
    folder = _package(tmp_path)
    path = folder / "non-execution.parquet"
    pd.DataFrame(
        [
            dict(
                stock_code="005930",
                trading_date="2015-06-15",
                regular_session_execution_allowed=False,
                valuation_or_entitlements_resolved=False,
            )
        ]
    ).to_parquet(path, index=False)
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entry = next(row for row in manifest["files"] if row["file"] == path.name)
    entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    entry["rows"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    bar = load_corrected_v4(folder).bars.iloc[0]
    assert not bool(bar["can_buy"]) and not bool(bar["can_sell"])
    assert not bool(bar["mark_valid"])


def test_without_admitted_factors_the_adjusted_series_stays_unadmitted(tmp_path):
    value = load_corrected_v4(_package(tmp_path))
    assert not value.bars["adjusted_valid"].any()
    assert not value.bars["volume_adjusted_valid"].any()
    assert value.adjusted_admission is None
    assert "ADJUSTED_PRICE_DEFINITION_UNADMITTED" in value.issues


def test_admitted_factors_split_bars_at_the_unadmitted_event(tmp_path):
    folder = _package(
        tmp_path,
        _prices(
            [
                ("2015-06-15", 200, 50.0),
                ("2015-06-16", 200, 100.0),
                ("2015-06-17", 100, 100.0),
            ]
        ),
    )
    path, digest = _audit(
        tmp_path,
        [
            ("2015-06-16", None, False, None, False),
            ("2015-06-17", "0.5", True, "1", True),
        ],
    )
    value = load_corrected_v4(
        folder, admitted_factors=path, admitted_factors_sha256=digest
    )
    bars = value.bars.sort_values("date").reset_index(drop=True)
    assert list(bars["adjusted_valid"]) == [False, True, True]
    assert list(bars["volume_adjusted_valid"]) == [False, True, True]
    assert "ADJUSTED_PRICE_DEFINITION_UNADMITTED" not in value.issues
    assert "REAL_EXECUTION_NOT_ADMITTED" in value.issues
    assert "DAILY_POINT_IN_TIME_ELIGIBILITY_UNVERIFIED" in value.issues
    admission = value.adjusted_admission
    assert admission.evidence_sha256 == digest
    assert admission.event_keys == 2
    assert admission.price_admitted_events == 1
    assert admission.adjusted_valid_bars == 2
    assert admission.provider_mismatch_bars == 0


def test_provider_series_disagreeing_with_admitted_factors_is_rejected(tmp_path):
    folder = _package(
        tmp_path,
        _prices(
            [
                ("2015-06-15", 200, 120.0),
                ("2015-06-16", 200, 100.4),
                ("2015-06-17", 100, 100.0),
            ]
        ),
    )
    path, digest = _audit(tmp_path, [("2015-06-17", "0.5", True, "1", True)])
    value = load_corrected_v4(
        folder, admitted_factors=path, admitted_factors_sha256=digest
    )
    bars = value.bars.sort_values("date").reset_index(drop=True)
    assert list(bars["adjusted_valid"]) == [False, True, True]
    assert value.adjusted_admission.provider_mismatch_bars == 1


def test_rejects_admitted_factor_evidence_with_unexpected_hash(tmp_path):
    folder = _package(tmp_path)
    path, _ = _audit(tmp_path, [("2015-06-17", "0.5", True, "1", True)])
    with pytest.raises(ValueError, match="ADMITTED_FACTOR_EVIDENCE_HASH_MISMATCH"):
        load_corrected_v4(folder, admitted_factors=path)
