"""Point-in-time daily eligibility from historical share snapshots and raw closes.

The signal day may use its own completed-session facts.  The following order
day may use only the previous exchange session's facts.  Missing facts fail
closed.  This does not approve the unrelated adjusted-price signal series.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds


MIN_CAP = 100_000_000_000
_META = (
    "observed_date",
    "market",
    "short_code",
    "share_class",
    "security_group",
    "listed_shares",
)


@dataclass(frozen=True)
class EligibilityResult:
    bars: pd.DataFrame
    metadata_sha256: str
    signal_eligible_count: int
    order_eligible_count: int
    missing_daily_metadata: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_candidate_metadata(
    path: str | Path, codes: set[str]
) -> tuple[pd.DataFrame, str]:
    """Read local daily instrument snapshots for the required historical codes."""
    source = Path(path)
    digest = _sha256(source)
    dataset = ds.dataset(source)
    absent = set(_META) - set(dataset.schema.names)
    if absent:
        raise ValueError(f"MISSING_DAILY_METADATA_COLUMNS:{sorted(absent)}")
    table = dataset.to_table(
        columns=list(_META), filter=ds.field("short_code").isin(sorted(codes))
    )
    return table.to_pandas(), digest


def load_sealed_krx_calendar(
    snapshot: str | Path, expected_manifest_sha256: str
) -> pd.DatetimeIndex:
    """Read the KRX session calendar only after verifying its sealed v3 part."""
    root = Path(snapshot)
    manifest_path = root / "manifest.json"
    if _sha256(manifest_path) != expected_manifest_sha256:
        raise ValueError("BASE_MANIFEST_HASH_MISMATCH")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    parts = [row for row in manifest["parts"] if row["member_kind"] == "CALENDAR"]
    if len(parts) != 1:
        raise ValueError("EXPECTED_ONE_KRX_CALENDAR_PART")
    part = parts[0]
    relative = Path(part["file"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("UNSAFE_CALENDAR_PATH")
    path = root / relative
    if _sha256(path) != part["sha256"]:
        raise ValueError("CALENDAR_PART_HASH_MISMATCH")
    frame = pd.read_parquet(path)
    if len(frame) != part["rows"] or not {"trading_date", "market", "is_open"}.issubset(
        frame.columns
    ):
        raise ValueError("INVALID_KRX_CALENDAR_PART")
    frame = frame.loc[frame["market"].eq("KRX")].copy()
    frame["date"] = pd.to_datetime(frame["trading_date"])
    if frame.duplicated("date").any() or frame["is_open"].isna().any():
        raise ValueError("DUPLICATE_OR_UNKNOWN_KRX_SESSION")
    return pd.DatetimeIndex(sorted(frame.loc[frame["is_open"].eq(True), "date"]))


def attach_daily_eligibility(
    bars: pd.DataFrame,
    selected_months: pd.DataFrame,
    calendar: pd.DatetimeIndex,
    metadata: pd.DataFrame,
    *,
    metadata_sha256: str,
) -> EligibilityResult:
    """Add signal and next-session order eligibility without future knowledge.

    The monthly list must have been computed from the preceding month-end.
    The historical instrument snapshot is treated as known only after its
    observed session closes.  No market-cap inference uses the order day's
    close or that day's share snapshot.
    """
    if len(metadata_sha256) != 64 or any(
        ch not in "0123456789abcdef" for ch in metadata_sha256
    ):
        raise ValueError("INVALID_METADATA_SHA256")
    required_bars = {"date", "code", "market", "close", "can_buy"}
    if not required_bars.issubset(bars.columns) or not {
        "code",
        "market",
        "month",
    }.issubset(selected_months.columns):
        raise ValueError("MISSING_ELIGIBILITY_INPUT_COLUMNS")
    if not set(_META).issubset(metadata.columns):
        raise ValueError("MISSING_DAILY_METADATA_COLUMNS")
    dates = pd.DatetimeIndex(calendar)
    if (
        dates.empty
        or dates.has_duplicates
        or not dates.is_monotonic_increasing
        or dates.tz is not None
    ):
        raise ValueError("INVALID_EXCHANGE_CALENDAR")
    frame = bars.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    if frame.duplicated(["date", "code"]).any() or not frame["date"].isin(dates).all():
        raise ValueError("DUPLICATE_OR_OFF_CALENDAR_BAR")
    frame["code"] = frame["code"].astype(str)
    frame["month"] = frame["date"].dt.strftime("%Y-%m")
    selected = selected_months[["code", "market", "month"]].copy()
    selected["code"] = selected["code"].astype(str)
    if selected.duplicated(["code", "month"]).any():
        raise ValueError("DUPLICATE_MONTHLY_SELECTION")
    meta = (
        metadata[list(_META)]
        .rename(columns={"observed_date": "date", "short_code": "code"})
        .copy()
    )
    meta["date"] = pd.to_datetime(meta["date"])
    meta["code"] = meta["code"].astype(str)
    if meta.duplicated(["date", "market", "code"]).any():
        raise ValueError("DUPLICATE_DAILY_INSTRUMENT_FACT")
    if not meta["date"].isin(dates).all():
        # Metadata may include non-candidate dates outside the evaluation
        # window; remove only those. Candidate date gaps still fail closed.
        meta = meta.loc[meta["date"].isin(dates)]
    frame = frame.merge(
        meta, on=["date", "market", "code"], how="left", validate="one_to_one"
    )
    frame = frame.merge(
        selected.assign(monthly_selected=True),
        on=["code", "market", "month"],
        how="left",
        validate="many_to_one",
    )
    frame["monthly_selected"] = frame["monthly_selected"].fillna(False).astype(bool)
    shares = pd.to_numeric(frame["listed_shares"], errors="coerce")
    close = pd.to_numeric(frame["close"], errors="coerce")
    frame["market_cap"] = close * shares
    fact_ready = (
        frame["share_class"].eq("보통주")
        & shares.gt(0)
        & close.gt(0)
        & frame["market_cap"].ge(MIN_CAP)
    )
    # All observed security_group classes in this KRX stock-history feed are
    # share-like, but never silently admit an unrecognized future class.
    stock_groups = {
        "주권",
        "외국주권",
        "부동산투자회사",
        "선박투자회사",
        "주식예탁증권",
        "투자회사",
        "사회간접자본투융자회사",
    }
    fact_ready &= frame["security_group"].isin(stock_groups)
    frame["signal_eligible"] = (
        frame["monthly_selected"] & fact_ready & frame["can_buy"].eq(True)
    ).astype(bool)
    successor = pd.DataFrame({"date": dates[:-1], "order_date": dates[1:]})
    prior = frame[["date", "code", "market"]].copy()
    prior["prior_fact_eligible"] = fact_ready.to_numpy()
    prior = prior.merge(successor, on="date", how="inner", validate="many_to_one")
    prior = prior[["order_date", "code", "market", "prior_fact_eligible"]].rename(
        columns={"order_date": "date"}
    )
    frame = frame.merge(
        prior, on=["date", "code", "market"], how="left", validate="one_to_one"
    )
    frame["order_eligible"] = (
        frame["monthly_selected"]
        & frame["prior_fact_eligible"].eq(True)
        & frame["can_buy"].eq(True)
    ).astype(bool)
    missing = int(frame["listed_shares"].isna().sum())
    return EligibilityResult(
        frame,
        metadata_sha256,
        int(frame["signal_eligible"].sum()),
        int(frame["order_eligible"].sum()),
        missing,
    )


def main() -> None:
    """Reproduce a non-admission coverage receipt for the locked evaluation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corrected-input", type=Path, required=True)
    parser.add_argument("--base-snapshot", type=Path, required=True)
    parser.add_argument("--daily-metadata", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    from .ohlcv20_input import load_corrected_v4

    input_value = load_corrected_v4(
        args.corrected_input, base_snapshot=args.base_snapshot
    )
    metadata, metadata_sha = load_candidate_metadata(
        args.daily_metadata, set(input_value.selected_months.code)
    )
    result = attach_daily_eligibility(
        input_value.bars,
        input_value.selected_months,
        input_value.calendar,
        metadata,
        metadata_sha256=metadata_sha,
    )
    period = result.bars["date"].between("2015-06-15", "2023-12-31")
    rows = result.bars.loc[period]
    base_manifest = args.base_snapshot / "manifest.json"
    receipt = {
        "schema": "ohlcv20-eligibility-audit-v1",
        "evaluation_start": "2015-06-15",
        "evaluation_end": "2023-12-31",
        "corrected_manifest_sha256": input_value.manifest_sha256,
        "base_manifest_sha256": _sha256(base_manifest),
        "metadata_sha256": metadata_sha,
        "metadata_candidate_rows": len(metadata),
        "sealed_krx_open_sessions_2014_2023": len(input_value.calendar),
        "observed_price_session_mismatch": 0,
        "monthly_selected_rows": len(input_value.selected_months),
        "evaluation_raw_bars": len(rows),
        "evaluation_monthly_selected_bars": int(rows["monthly_selected"].sum()),
        "evaluation_signal_daily_cap_class_eligible": int(
            rows["signal_eligible"].sum()
        ),
        "evaluation_order_prior_session_cap_class_eligible": int(
            rows["order_eligible"].sum()
        ),
        "evaluation_missing_daily_metadata": int(rows["listed_shares"].isna().sum()),
        "cap_floor_krw": MIN_CAP,
        "order_fact_timing": "previous_open_exchange_session_close",
        "price_adjustment_admitted": False,
        "real_execution_admitted": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
