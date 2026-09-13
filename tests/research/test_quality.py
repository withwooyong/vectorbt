from __future__ import annotations

import json

import pandas as pd
import pytest

from research.krx_lab.io import digest, write_json
from research.krx_lab.quality import audit
from research.krx_lab.snapshot import verify_snapshot


def _prices() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": ["2023-01-02", "2023-01-03"],
            "code": ["005930", "005930"],
            "open": [100.0, 101.0],
            "high": [105.0, 104.0],
            "low": [99.0, 100.0],
            "close": [103.0, 102.0],
            "volume": [1000, 0],
        }
    )


def test_valid_synthetic_data_has_synthetic_grade():
    result = audit(_prices(), {"source": "SYNTHETIC"})
    assert result["grade"] == "SYNTHETIC"
    assert result["reasons"] == []
    assert result["zero_volume_rows"] == 1


@pytest.mark.parametrize(
    ("column", "value"),
    [("open", 0.0), ("close", float("nan")), ("high", 98.0), ("low", 106.0), ("volume", -1.0)],
)
def test_standard_invalid_price_cases_are_blocked(column, value):
    prices = _prices()
    prices.loc[0, column] = value
    result = audit(prices, {"source": "SYNTHETIC"})
    assert result["grade"] == "BLOCKED"
    assert result["reasons"] == ["INVALID_OHLCV"]
    assert result["invalid_ohlcv_rows"] == 1


def test_invalid_keys_cover_duplicate_bad_date_and_missing_code():
    prices = pd.concat([_prices(), _prices().iloc[[0]], _prices().iloc[[0]]], ignore_index=True)
    prices.loc[3, "date"] = "not-a-date"
    prices.loc[1, "code"] = None
    result = audit(prices, {"source": "SYNTHETIC"})
    assert result["grade"] == "BLOCKED"
    assert "INVALID_KEYS" in result["reasons"]
    assert result["duplicate_keys"] == 1
    assert result["invalid_date_rows"] == 1


def test_real_data_cannot_be_promoted_to_execution_eligible_by_manifest_flags():
    result = audit(
        _prices(),
        {"source": "PostgreSQL", "price_semantics_evidence": "reviewed", "mixed_vendors": False},
    )
    assert result["grade"] == "EXPLORATORY_ADJUSTED"
    assert result["grade"] != "EXECUTION_ELIGIBLE"
    assert "RAW_PRICE_AND_ACTIONS_UNVERIFIED" in result["limitations"]


def test_quality_hash_corruption_blocks_snapshot(tmp_path):
    part = tmp_path / "prices.parquet"
    _prices().to_parquet(part, index=False)
    quality = audit(_prices(), {"source": "SYNTHETIC"})
    write_json(tmp_path / "quality.json", quality)
    manifest = {
        "status": "COMPLETE",
        "parts": [{"file": part.name, "sha256": digest(part), "rows": 2}],
        "quality_sha256": digest(tmp_path / "quality.json"),
    }
    write_json(tmp_path / "manifest.json", manifest)
    (tmp_path / "quality.json").write_text(json.dumps({"grade": "EXECUTION_ELIGIBLE"}), encoding="utf-8")
    with pytest.raises(ValueError, match="품질 검사 손상"):
        verify_snapshot(tmp_path)
