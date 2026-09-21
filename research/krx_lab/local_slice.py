"""Bounded, read-only access to an existing verified local snapshot.

This is an inspection/data-preparation path. It does not change the snapshot's
quality grade or permit real-data P&L execution.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

from .snapshot import verify_snapshot


DEFAULT_COLUMNS = ("date", "code", "open", "high", "low", "close", "volume")


def load_snapshot_window(path: str | Path, *, start: str, end: str,
                         codes: Iterable[str] | None = None,
                         columns: Iterable[str] = DEFAULT_COLUMNS) -> pd.DataFrame:
    """Read only selected rows/columns after validating all snapshot hashes.

    The requested window must end before the locked 2024+ period. Parts are
    read one at a time so full chunks are not concatenated before filtering.
    This function does not perform data admission or calculate returns.
    """
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if first > last:
        raise ValueError("START_AFTER_END")
    if last >= date(2024, 1, 1):
        raise ValueError("HOLDOUT_LOCKED")
    if isinstance(columns, str):
        raise ValueError("INVALID_COLUMNS")
    selected = tuple(columns)
    if not selected or len(set(selected)) != len(selected) or any(not isinstance(name, str) or not name for name in selected):
        raise ValueError("INVALID_COLUMNS")
    if isinstance(codes, str):
        raise ValueError("INVALID_CODES")
    code_set = None if codes is None else frozenset(codes)
    if code_set is not None and (not code_set or any(not isinstance(code, str) or not code for code in code_set)):
        raise ValueError("INVALID_CODES")

    root = Path(path)
    manifest, _ = verify_snapshot(root)
    required = tuple(dict.fromkeys((*selected, "date", "code")))
    start_time, end_time = pd.Timestamp(first), pd.Timestamp(last)
    frames = []
    for part in manifest["parts"]:
        frame = pd.read_parquet(root / part["file"], columns=list(required))
        dates = pd.to_datetime(frame["date"], errors="raise")
        mask = dates.between(start_time, end_time)
        if code_set is not None:
            mask &= frame["code"].isin(code_set)
        if mask.any():
            frame = frame.loc[mask, list(selected)].copy()
            if "date" in frame:
                frame["date"] = dates.loc[mask].to_numpy()
            frames.append(frame)
    if not frames:
        return pd.DataFrame(columns=selected)
    return pd.concat(frames, ignore_index=True)
