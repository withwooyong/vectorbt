"""Read-only bounded access to the verified local Parquet snapshot."""

import pytest

from research.krx_lab.io import digest
from research.krx_lab.local_slice import load_snapshot_window
from research.krx_lab.snapshot import synthetic_snapshot


def test_window_filters_symbols_dates_and_columns_without_changing_snapshot(tmp_path):
    root = tmp_path / "snapshot"
    synthetic_snapshot(root)
    before = {name: digest(root / name) for name in ("manifest.json", "quality.json", "prices-0000.parquet")}

    result = load_snapshot_window(root, start="2021-01-04", end="2021-01-08",
                                  codes=["SYN001", "SYN003"], columns=["code", "date", "close"])

    assert list(result.columns) == ["code", "date", "close"]
    assert set(result.code) == {"SYN001", "SYN003"}
    assert len(result) == 10
    assert result.date.min().strftime("%Y-%m-%d") == "2021-01-04"
    assert result.date.max().strftime("%Y-%m-%d") == "2021-01-08"
    assert before == {name: digest(root / name) for name in before}


def test_window_preserves_empty_result_and_rejects_locked_or_corrupt_input(tmp_path):
    root = tmp_path / "snapshot"
    synthetic_snapshot(root)
    empty = load_snapshot_window(root, start="2021-01-04", end="2021-01-08", codes=["ABSENT"])
    assert empty.empty
    assert list(empty.columns) == ["date", "code", "open", "high", "low", "close", "volume"]

    with pytest.raises(ValueError, match="HOLDOUT_LOCKED"):
        load_snapshot_window(root, start="2023-12-29", end="2024-01-02")
    with pytest.raises(ValueError, match="START_AFTER_END"):
        load_snapshot_window(root, start="2021-01-08", end="2021-01-04")
    with pytest.raises(ValueError, match="INVALID_CODES"):
        load_snapshot_window(root, start="2021-01-04", end="2021-01-08", codes=[])
    with pytest.raises(ValueError, match="INVALID_CODES"):
        load_snapshot_window(root, start="2021-01-04", end="2021-01-08", codes="SYN001")
    with pytest.raises(ValueError, match="INVALID_COLUMNS"):
        load_snapshot_window(root, start="2021-01-04", end="2021-01-08", columns="close")

    with (root / "prices-0000.parquet").open("ab") as stream:
        stream.write(b"corrupt")
    with pytest.raises(ValueError, match="손상"):
        load_snapshot_window(root, start="2021-01-04", end="2021-01-08")
