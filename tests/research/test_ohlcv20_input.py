import hashlib
import json

import pandas as pd
import pytest

from research.krx_lab.ohlcv20_input import load_corrected_v4


def _package(tmp_path):
    folder = tmp_path / "corrected-input-v4"
    (folder / "prices").mkdir(parents=True)
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
        total_price_rows=2,
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
