import hashlib
import json

import pandas as pd
import pytest

from research.krx_lab import ohlcv20_real_execution as engine
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


_FLAGS = (
    "immutable_input_verified",
    "daily_universe_admitted",
    "adjusted_price_admitted",
    "volume_factors_admitted",
    "corporate_coverage_admitted",
    "rights_admitted",
    "market_rules_admitted",
    "real_execution_admitted",
)


def _admitted_package(tmp_path, price=None, pin=None, **receipt_changes):
    """Seal a v5-shaped package and a receipt bound to its manifest bytes."""
    folder = _package(tmp_path, price)
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for name, frame in (
        ("rights-terms.parquet", pd.DataFrame(dict(event_id=["e:1"]))),
        ("market-rules.parquet", pd.DataFrame(dict(stock_code=["005930"]))),
    ):
        frame.to_parquet(folder / name, index=False)
        manifest["files"].append(
            dict(
                file=name,
                rows=len(frame),
                sha256=hashlib.sha256((folder / name).read_bytes()).hexdigest(),
            )
        )
    manifest.update(
        real_execution_admitted=True,
        admission_receipt_schema="ohlcv20-real-admission-v1",
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    receipt = dict(
        schema="ohlcv20-real-admission-v1",
        status="ADMITTED",
        blocked_reasons=[],
        **{name: True for name in _FLAGS},
        source_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        rights_terms_sha256=hashlib.sha256(
            (folder / "rights-terms.parquet").read_bytes()
        ).hexdigest(),
        admission_scope=dict(
            development_period=dict(start="2015-06-15", end="2023-12-31")
        ),
    )
    receipt.update(receipt_changes)
    receipt_path = tmp_path / "admission.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    if pin is not None:
        # The engine pins the sealed receipt; a fixture pins its own digest.
        pin.setattr(
            engine,
            "_ADMISSION_RECEIPT_SHA256",
            hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        )
    return folder, receipt_path


def test_receipt_bound_package_opens_real_execution(tmp_path, monkeypatch):
    folder, receipt = _admitted_package(tmp_path, pin=monkeypatch)
    value = load_corrected_v4(folder, admission_receipt=receipt)
    assert value.real_execution_admitted is True
    assert "REAL_EXECUTION_NOT_ADMITTED" not in value.issues
    admission = value.engine_admission()
    assert all(admission[name] is True for name in _FLAGS)
    assert admission["admission_evidence_sha256"] == hashlib.sha256(
        receipt.read_bytes()
    ).hexdigest()


def test_admitted_manifest_without_receipt_does_not_open(tmp_path):
    folder, _ = _admitted_package(tmp_path)
    with pytest.raises(ValueError, match="REAL_ADMISSION_RECEIPT_REQUIRED"):
        load_corrected_v4(folder)


def test_receipt_cannot_open_an_unadmitted_v4_package(tmp_path):
    _, receipt = _admitted_package(tmp_path / "v5")
    value = load_corrected_v4(_package(tmp_path))
    with pytest.raises(ValueError, match="REAL_EXECUTION_NOT_ADMITTED"):
        value.engine_admission()
    with pytest.raises(ValueError, match="RECEIPT_CANNOT_ADMIT_UNADMITTED_INPUT"):
        load_corrected_v4(_package(tmp_path / "again"), admission_receipt=receipt)


@pytest.mark.parametrize(
    "changes, error",
    [
        (dict(status="BLOCKED"), "REAL_ADMISSION_RECEIPT_NOT_ADMITTED"),
        (dict(rights_admitted=False), "REAL_ADMISSION_RECEIPT_NOT_ADMITTED"),
        (dict(source_manifest_sha256="0" * 64), "REAL_ADMISSION_RECEIPT_MANIFEST_MISMATCH"),
        (dict(rights_terms_sha256="0" * 64), "REAL_ADMISSION_RECEIPT_RIGHTS_MISMATCH"),
    ],
)
def test_receipt_must_be_admitted_and_bound_to_file_bytes(
    tmp_path, monkeypatch, changes, error
):
    folder, receipt = _admitted_package(tmp_path, pin=monkeypatch, **changes)
    with pytest.raises(ValueError, match=error):
        load_corrected_v4(folder, admission_receipt=receipt)


def test_receipt_keeps_validation_years_locked(tmp_path, monkeypatch):
    price = _prices([("2015-06-15", 100, 100), ("2024-01-02", 100, 100)])
    folder, receipt = _admitted_package(tmp_path, price, pin=monkeypatch)
    with pytest.raises(ValueError, match="DATE_OUTSIDE_LOCKED_HISTORY"):
        load_corrected_v4(folder, admission_receipt=receipt)


def test_only_the_pinned_receipt_opens_real_execution(tmp_path):
    folder, receipt = _admitted_package(tmp_path)
    with pytest.raises(ValueError, match="ADMISSION_RECEIPT_NOT_PINNED"):
        load_corrected_v4(folder, admission_receipt=receipt)
