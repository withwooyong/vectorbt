"""Read-only corrected-v4 OHLCV adapter; it does not admit real execution.

The corrected package contains historical bars and a monthly candidate list,
but does not establish daily point-in-time capitalization rechecks or an
approved adjusted-price convention.  Consequently order_eligible and
adjusted_valid remain false until separately verified facts are supplied.

A caller may supply the sealed factor-admission audit through admitted_factors.
An adjusted price is built by restating the past from a later vantage point, so
a bar's adjusted series is only trustworthy when every entitlement event that
takes effect after that bar carries an approved factor, and when the provider's
own adjusted close reproduces the product of those approved factors.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd


_FIELDS = {
    "prices": {
        "stock_code",
        "trading_date",
        "adjusted",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "trade_volume",
        "trade_amount",
        "market",
    },
    "selected-months.parquet": {"stock_code", "market", "month"},
    "non-execution.parquet": {
        "stock_code",
        "trading_date",
        "regular_session_execution_allowed",
        "valuation_or_entitlements_resolved",
    },
    "factor-admission": {
        "stock_code",
        "effective_date",
        "price_factor",
        "volume_factor",
        "price_admitted",
        "volume_admitted",
    },
}

# sha256 of the factor-admission audit sealed on 2026-09-22; the admission
# report of the same date records it as output_sha256.  A caller overrides it
# only to exercise a synthetic fixture.
_ADMITTED_FACTOR_SHA256 = (
    "927fe6d9b4e197112c27a64ad330902a0b285c68d1dc3c07f6bdc2944b5eecc8"
)
# Same relative tolerance the admission policy applies to a parsed allotment
# ratio, reused here to compare a provider series with the approved factors.
_ADJUSTED_RELATIVE_TOLERANCE = 0.005


@dataclass(frozen=True)
class AdjustedAdmission:
    """Counted evidence behind adjusted_valid and volume_adjusted_valid."""

    evidence_sha256: str
    event_keys: int
    price_admitted_events: int
    volume_admitted_events: int
    codes_without_events: int
    adjusted_valid_bars: int
    volume_adjusted_valid_bars: int
    provider_mismatch_bars: int
    provider_uncomparable_bars: int


@dataclass(frozen=True)
class Ohlcv20Input:
    bars: pd.DataFrame
    selected_months: pd.DataFrame
    calendar: pd.DatetimeIndex
    issues: tuple[str, ...]
    manifest_sha256: str
    real_execution_admitted: bool = False
    adjusted_admission: AdjustedAdmission | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _date(series: pd.Series) -> pd.Series:
    value = pd.to_datetime(series, errors="raise")
    if (
        value.isna().any()
        or value.dt.tz is not None
        or not value.eq(value.dt.normalize()).all()
    ):
        raise ValueError("INVALID_DAILY_DATE")
    if not value.between(pd.Timestamp("2014-01-01"), pd.Timestamp("2023-12-31")).all():
        raise ValueError("DATE_OUTSIDE_LOCKED_HISTORY")
    return value


def _factor(value: object) -> Decimal:
    number = Decimal(str(value))
    if not number.is_finite() or number <= 0:
        raise ValueError("NON_POSITIVE_ADMITTED_FACTOR")
    return number


def _load_admitted_factors(path: Path, expected_sha256: str) -> tuple[pd.DataFrame, str]:
    """Verify the sealed audit and keep an approved factor as an exact Decimal."""
    if not path.is_file():
        raise ValueError("MISSING_ADMITTED_FACTOR_EVIDENCE")
    digest = _sha256(path)
    if digest != expected_sha256:
        raise ValueError("ADMITTED_FACTOR_EVIDENCE_HASH_MISMATCH")
    frame = pd.read_parquet(path)
    if not _FIELDS["factor-admission"].issubset(frame.columns):
        raise ValueError("MISSING_ADMITTED_FACTOR_COLUMNS")
    events = pd.DataFrame(
        {
            "code": frame["stock_code"].astype(str),
            "date": _date(frame["effective_date"]),
        }
    )
    for side in ("price", "volume"):
        admitted = frame[f"{side}_admitted"]
        if admitted.dtype != bool:
            raise ValueError("NON_BOOLEAN_FACTOR_ADMISSION_FLAG")
        column = frame[f"{side}_factor"]
        if column[admitted].isna().any():
            raise ValueError("ADMITTED_FACTOR_VALUE_MISSING")
        events[f"{side}_admitted"] = admitted.to_numpy(dtype=bool)
        events[f"{side}_factor"] = [
            _factor(value) if flag else None for value, flag in zip(column, admitted)
        ]
    if events.duplicated(["code", "date"]).any():
        raise ValueError("DUPLICATE_ADMITTED_FACTOR_KEY")
    return events.sort_values(["code", "date"], ignore_index=True), digest


def _suffix(events: pd.DataFrame, side: str) -> tuple[np.ndarray, np.ndarray]:
    """Fold one code's events backwards into per-slot blockers and products.

    Slot i answers for a bar that precedes event i: blocked[i] tells whether any
    event from i onwards lacks admission, and product[i] multiplies the approved
    factors from i onwards.  Slot len(events) covers bars after the last event.
    """
    flags = events[f"{side}_admitted"].to_numpy(dtype=bool)
    values = list(events[f"{side}_factor"])
    count = len(flags)
    blocked = np.zeros(count + 1, dtype=bool)
    product = np.ones(count + 1, dtype=float)
    running = Decimal(1)
    for index in range(count - 1, -1, -1):
        if flags[index]:
            running *= values[index]
        blocked[index] = bool(blocked[index + 1]) or not bool(flags[index])
        product[index] = float(running)
    return blocked, product


def _admit_adjusted(bars: pd.DataFrame, events: pd.DataFrame) -> dict[str, int]:
    """Decide adjusted_valid per bar from the events effective after that bar.

    A code absent from the audit is not evidence that it never had an
    entitlement event; it may simply never have reached the candidate list.  So
    its bars are not granted on the event test alone and still have to reconcile
    with the provider series, which an unaccounted factor would break.
    """
    size = len(bars)
    price_ok = np.ones(size, dtype=bool)
    volume_ok = np.ones(size, dtype=bool)
    expected = np.ones(size, dtype=float)
    grouped = dict(tuple(events.groupby("code", sort=False)))
    dates = bars["date"].to_numpy("datetime64[ns]")
    missing = 0
    for code, rows in bars.groupby("code", sort=False).indices.items():
        group = grouped.get(code)
        if group is None:
            missing += 1
            continue
        slot = np.searchsorted(
            group["date"].to_numpy("datetime64[ns]"), dates[rows], side="right"
        )
        price_blocked, price_product = _suffix(group, "price")
        volume_blocked, _ = _suffix(group, "volume")
        price_ok[rows] = ~price_blocked[slot]
        volume_ok[rows] = ~volume_blocked[slot]
        expected[rows] = price_product[slot]
    close = bars["close"].to_numpy(dtype=float)
    adjusted = bars["adjusted_close"].to_numpy(dtype=float)
    observed = np.divide(adjusted, close, out=np.full(size, np.nan), where=close > 0)
    comparable = np.isfinite(observed)
    matched = comparable & (
        np.abs(observed - expected) <= _ADJUSTED_RELATIVE_TOLERANCE * expected
    )
    bars["adjusted_valid"] = price_ok & matched
    bars["volume_adjusted_valid"] = volume_ok
    return dict(
        codes_without_events=missing,
        adjusted_valid_bars=int(bars["adjusted_valid"].sum()),
        volume_adjusted_valid_bars=int(bars["volume_adjusted_valid"].sum()),
        provider_mismatch_bars=int((price_ok & comparable & ~matched).sum()),
        provider_uncomparable_bars=int((price_ok & ~comparable).sum()),
    )


def load_corrected_v4(
    package: str | Path,
    *,
    base_snapshot: str | Path | None = None,
    admitted_factors: str | Path | None = None,
    admitted_factors_sha256: str | None = None,
) -> Ohlcv20Input:
    """Verify sealed files and prepare conservative daily input frames.

    No read from a live database, network, or data after 2023 is performed.
    Source flags are deliberately conservative: a monthly ranked candidate is
    not proof of the same day's market cap or ordinary-share eligibility.
    Without admitted_factors the adjusted series stays wholly unadmitted, which
    keeps every existing caller on its previous result.
    """
    root = Path(package)
    manifest_path = root / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("schema") != "ohlcv-corrected-candidate-input-v1":
        raise ValueError("UNEXPECTED_CORRECTED_INPUT_SCHEMA")
    if manifest.get("real_execution_admitted") is not False:
        raise ValueError("UNEXPECTED_REAL_ADMISSION_FLAG")
    parts = manifest.get("files")
    if not isinstance(parts, list) or not parts:
        raise ValueError("EMPTY_CORRECTED_INPUT_MANIFEST")
    names = [item["file"] for item in parts]
    if len(set(names)) != len(names) or not any(
        name.startswith("prices/") for name in names
    ):
        raise ValueError("DUPLICATE_OR_MISSING_PRICE_PART")
    required = {"selected-months.parquet", "non-execution.parquet"}
    if not required.issubset(names):
        raise ValueError("MISSING_CORRECTED_INPUT_PART")
    for item in parts:
        relative = Path(item["file"])
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.suffix != ".parquet"
        ):
            raise ValueError("UNSAFE_MANIFEST_PATH")
        path = root / relative
        if not path.is_file():
            raise ValueError(f"MISSING_MANIFEST_FILE:{relative}")
        if _sha256(path) != item["sha256"]:
            raise ValueError(f"MANIFEST_HASH_MISMATCH:{relative}")
    frames = [
        pd.read_parquet(root / name, columns=sorted(_FIELDS["prices"]))
        for name in names
        if name.startswith("prices/")
    ]
    price = pd.concat(frames, ignore_index=True)
    if not _FIELDS["prices"].issubset(price.columns):
        raise ValueError("MISSING_PRICE_COLUMNS")
    if len(price) != manifest["total_price_rows"] or any(
        len(frame) != item["rows"]
        for frame, item in zip(
            frames, (i for i in parts if i["file"].startswith("prices/"))
        )
    ):
        raise ValueError("PRICE_ROW_COUNT_MISMATCH")
    price["date"] = _date(price["trading_date"])
    price["code"] = price["stock_code"].astype(str)
    if price.duplicated(["date", "code", "adjusted"]).any():
        raise ValueError("DUPLICATE_PRICE_KEY")
    selected = pd.read_parquet(root / "selected-months.parquet")
    blocked = pd.read_parquet(root / "non-execution.parquet")
    if not _FIELDS["selected-months.parquet"].issubset(selected.columns) or not _FIELDS[
        "non-execution.parquet"
    ].issubset(blocked.columns):
        raise ValueError("MISSING_SUPPORTING_COLUMNS")
    for name, frame in (
        ("selected-months.parquet", selected),
        ("non-execution.parquet", blocked),
    ):
        expected = next(item["rows"] for item in parts if item["file"] == name)
        if len(frame) != expected:
            raise ValueError(f"SUPPORTING_ROW_COUNT_MISMATCH:{name}")
    selected = selected.rename(columns={"stock_code": "code"}).copy()
    if selected.duplicated(["code", "month"]).any():
        raise ValueError("DUPLICATE_MONTHLY_SELECTION")
    if (
        not selected["month"]
        .astype(str)
        .str.fullmatch(r"20(?:1[4-9]|2[0-3])-(?:0[1-9]|1[0-2])")
        .all()
    ):
        raise ValueError("INVALID_SELECTION_MONTH")
    blocked = blocked.rename(columns={"stock_code": "code"}).copy()
    blocked["date"] = _date(blocked["trading_date"])
    if blocked.duplicated(["date", "code"]).any():
        raise ValueError("DUPLICATE_NON_EXECUTION_KEY")
    if blocked["regular_session_execution_allowed"].eq(True).any():
        raise ValueError("CONTRADICTORY_NON_EXECUTION_FLAG")
    raw = price.loc[price["adjusted"].eq(False)].copy()
    adj = price.loc[
        price["adjusted"].eq(True),
        ["date", "code", "open_price", "high_price", "low_price", "close_price"],
    ].copy()
    adj = adj.rename(
        columns={
            f"{name}_price": f"adjusted_{name}"
            for name in ("open", "high", "low", "close")
        }
    )
    raw = raw.rename(
        columns={f"{name}_price": name for name in ("open", "high", "low", "close")}
    )
    raw = raw.rename(columns={"trade_volume": "volume", "trade_amount": "turnover"})
    bars = raw.merge(adj, on=["date", "code"], how="left", validate="one_to_one")
    bars = bars.merge(
        blocked[
            [
                "date",
                "code",
                "regular_session_execution_allowed",
                "valuation_or_entitlements_resolved",
            ]
        ],
        on=["date", "code"],
        how="left",
        validate="one_to_one",
    )
    selected_keys = selected[["code", "market", "month"]].assign(universe_selected=True)
    bars["month"] = bars["date"].dt.strftime("%Y-%m")
    bars = bars.merge(
        selected_keys,
        on=["code", "market", "month"],
        how="left",
        validate="many_to_one",
    )
    bars["universe_selected"] = bars["universe_selected"].fillna(False).astype(bool)
    raw_ok = bars[["open", "high", "low", "close"]].notna().all(axis=1)
    raw_ok &= bars[["open", "high", "low", "close"]].gt(0).all(axis=1)
    raw_ok &= bars["high"].ge(bars[["open", "close"]].max(axis=1)) & bars["low"].le(
        bars[["open", "close"]].min(axis=1)
    )
    non_exec = bars["regular_session_execution_allowed"].eq(False)
    bars["can_buy"] = (raw_ok & bars["volume"].gt(0) & ~non_exec).astype(bool)
    bars["can_sell"] = bars["can_buy"].copy()
    bars["mark_valid"] = (
        bars["close"].gt(0) & ~bars["valuation_or_entitlements_resolved"].eq(False)
    ).astype(bool)
    # Admission is not inferred from a provider's adjusted series or a monthly
    # universe selection. Both need separate approved daily historical facts.
    bars["adjusted_valid"] = False
    bars["volume_adjusted_valid"] = False
    bars["order_eligible"] = False
    admission = None
    if admitted_factors is not None:
        events, evidence_sha256 = _load_admitted_factors(
            Path(admitted_factors),
            admitted_factors_sha256 or _ADMITTED_FACTOR_SHA256,
        )
        admission = AdjustedAdmission(
            evidence_sha256=evidence_sha256,
            event_keys=len(events),
            price_admitted_events=int(events["price_admitted"].sum()),
            volume_admitted_events=int(events["volume_admitted"].sum()),
            **_admit_adjusted(bars, events),
        )
    observed_dates = pd.DatetimeIndex(sorted(bars["date"].unique()))
    issues = ["DAILY_POINT_IN_TIME_ELIGIBILITY_UNVERIFIED"]
    if admission is None:
        issues.append("ADJUSTED_PRICE_DEFINITION_UNADMITTED")
    if base_snapshot is None:
        calendar = observed_dates
        issues.append("EXCHANGE_CALENDAR_NOT_VERIFIED_FROM_PRICE_DATES")
    else:
        from .ohlcv20_eligibility import load_sealed_krx_calendar

        expected = manifest.get("base_manifest_sha256")
        if not isinstance(expected, str):
            raise ValueError("MISSING_BASE_MANIFEST_SHA256")
        calendar = load_sealed_krx_calendar(base_snapshot, expected)
        if len(observed_dates.difference(calendar)) or len(
            calendar.difference(observed_dates)
        ):
            raise ValueError("CORRECTED_PRICE_CALENDAR_MISMATCH")
    issues.append("REAL_EXECUTION_NOT_ADMITTED")
    columns = [
        "date",
        "code",
        "market",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "turnover",
        "adjusted_open",
        "adjusted_high",
        "adjusted_low",
        "adjusted_close",
        "universe_selected",
        "can_buy",
        "can_sell",
        "mark_valid",
        "adjusted_valid",
        "order_eligible",
        "volume_adjusted_valid",
    ]
    return Ohlcv20Input(
        bars[columns],
        selected,
        calendar,
        tuple(issues),
        hashlib.sha256(manifest_bytes).hexdigest(),
        adjusted_admission=admission,
    )
