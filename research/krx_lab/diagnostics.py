"""성과 차단 자료의 지표 준비율·신호 빈도 진단. 매매 수익률을 계산하지 않는다."""

from pathlib import Path
import time

import numpy as np
import pandas as pd

from .io import digest, write_json
from .snapshot import verify_snapshot
from .strategies import ENTRY_IDS, build_signals


def diagnose(snapshot, out):
    snapshot, out = Path(snapshot), Path(out)
    manifest, quality = verify_snapshot(snapshot)
    if quality.get("duplicate_keys") or quality.get("invalid_date_rows"):
        raise ValueError("키 오류는 지표 진단 전에도 해결해야 합니다")
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    sessions = set()
    for part in manifest["parts"]:
        dates = pd.read_parquet(snapshot / part["file"], columns=["date"])["date"]
        sessions.update(pd.to_datetime(dates[dates.astype(str) < "2024-01-01"]).unique())
    sessions = sorted(sessions)
    summary = []
    codes_done = 0

    def consume(group):
        nonlocal codes_done
        code = str(group["code"].iloc[0])
        group = group.copy()
        group["date"] = pd.to_datetime(group["date"])
        group = group[group["date"] < "2024-01-01"]
        if group.empty:
            return
        numeric = group[["open", "high", "low", "close", "volume"]].astype(float)
        invalid = (~np.isfinite(numeric).all(axis=1) | (numeric.iloc[:, :4] <= 0).any(axis=1) |
                   (numeric["volume"] < 0) |
                   (numeric["high"] < numeric[["open", "low", "close"]].max(axis=1)) |
                   (numeric["low"] > numeric[["open", "high", "close"]].min(axis=1)))
        group["invalid_observed_row"] = invalid
        # Only the in-memory diagnostic copy is masked. No date/position is deleted.
        group[["open", "high", "low", "close", "volume"]] = numeric
        group.loc[invalid, ["open", "high", "low", "close", "volume"]] = np.nan
        aligned = group.set_index("date").reindex(sessions)
        aligned["code"] = code
        aligned.index.name = "date"
        signals = build_signals(aligned.reset_index())
        for year, subset in signals.groupby(signals["date"].dt.year):
            for entry_id in ENTRY_IDS:
                summary.append({"code": code, "year": int(year), "entry_id": entry_id,
                                "signals": int(subset[entry_id].sum()),
                                "valid_observed_bars": int(subset["close"].notna().sum()),
                                "invalid_observed_rows": int(subset["invalid_observed_row"].fillna(False).sum())})
        codes_done += 1
        if codes_done % 250 == 0:
            print(f"diagnostic: {codes_done} symbols (no return calculation)", flush=True)

    carry = pd.DataFrame()
    # Export is ordered by code,date. A symbol crossing a file boundary is retained once.
    for part in manifest["parts"]:
        frame = pd.read_parquet(snapshot / part["file"])
        frame = pd.concat([carry, frame], ignore_index=True)
        last_code = frame["code"].iloc[-1]
        complete = frame[frame["code"] != last_code]
        carry = frame[frame["code"] == last_code].copy()
        for _, group in complete.groupby("code", sort=True, observed=True):
            consume(group)
    if not carry.empty:
        consume(carry)
    detail = pd.DataFrame(summary)
    detail.to_parquet(out / "signal-counts-by-stock-year.parquet", index=False)
    aggregate = detail.groupby(["entry_id", "year"], as_index=False).agg(
        signals=("signals", "sum"), symbols_with_signals=("signals", lambda s: int((s > 0).sum())))
    aggregate.to_csv(out / "signal-counts.csv", index=False, encoding="utf-8-sig")
    receipt = {"status": "DIAGNOSTIC_ONLY", "price_grade": quality["grade"],
               "source_manifest_sha256": digest(snapshot / "manifest.json"), "symbols": codes_done,
               "elapsed_seconds": time.perf_counter() - started, "observed_sessions": len(sessions),
               "returns_computed": False, "invalid_row_policy": "mask diagnostic OHLCV only; retain dates",
               "survivorship_filter_applied": False,
               "files": {p.name: digest(p) for p in out.iterdir() if p.is_file()}}
    write_json(out / "diagnostic.json", receipt)
    return receipt
