"""Read-only delivery inspection for the C1 contract.

This module deliberately reports an inspection result, rather than admitting
real data for execution.  It has no database or network dependencies.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import pandas as pd

from .contracts import ContractError, validate_delivery
from .io import canonical_hash, digest
from .quality import delivery_grade


_ROW_KEYS = {
    "sources": ("source_id",),
    "prices": ("instrument_id", "date"),
    "events": ("event_id",),
    "instruments": ("instrument_id", "effective_from"),
    "statuses": ("status_id",),
    "calendar": ("market", "date"),
    "market_profiles": ("profile_id",),
}
_SUPPORTED_FILE_SCHEMAS = {"synthetic-source-v1": ".json"}


def _issue(issues: list[dict], code: str, detail: str = "") -> None:
    issues.append({"code": code, "detail": detail})


def _day(value: str) -> pd.Timestamp:
    return pd.Timestamp(value).normalize()


def _active(rows: list[Mapping], when: pd.Timestamp) -> list[Mapping]:
    return [row for row in rows if _day(row["effective_from"]) <= when
            and (row["effective_to"] is None or when <= _day(row["effective_to"]))]


def _row_count(path: Path) -> int | None:
    """Return an inexpensive row count for supported local formats."""
    if path.suffix.lower() == ".parquet":
        return len(pd.read_parquet(path))
    if path.suffix.lower() == ".json":
        import json

        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return len(value) if isinstance(value, list) else 1 if isinstance(value, Mapping) else None
    return None


def _check_files(value: Mapping, root: Path, issues: list[dict]) -> dict[str, str]:
    hashes = {}
    resolved_root = root.resolve()
    for item in value["metadata"]["files"]:
        relative = PurePosixPath(item["file"])
        path = root.joinpath(*relative.parts)
        try:
            resolved = path.resolve()
            contained = resolved.is_relative_to(resolved_root)
        except (OSError, ValueError):
            contained = False
        if not contained:
            _issue(issues, "ARTIFACT_PATH_ESCAPE", item["file"])
            continue
        expected_suffix = _SUPPORTED_FILE_SCHEMAS.get(item["schema"])
        if expected_suffix is None:
            _issue(issues, "ARTIFACT_SCHEMA_UNVERIFIED", item["schema"])
        elif path.suffix.lower() != expected_suffix:
            _issue(issues, "ARTIFACT_SCHEMA_MISMATCH", item["file"])
        if not resolved.is_file():
            _issue(issues, "MISSING_ARTIFACT", item["file"])
            continue
        actual_hash = digest(resolved)
        hashes[item["file"]] = actual_hash
        if actual_hash != item["sha256"]:
            _issue(issues, "ARTIFACT_HASH_MISMATCH", item["file"])
        try:
            rows = _row_count(resolved)
        except Exception as exc:
            _issue(issues, "ARTIFACT_UNREADABLE", f"{item['file']}: {type(exc).__name__}")
            continue
        if rows is not None and rows != item["rows"]:
            _issue(issues, "ARTIFACT_ROW_COUNT_MISMATCH", f"{item['file']}: {rows} != {item['rows']}")
    return hashes


def _intervals(rows: list[Mapping], group_key: str, label: str, issues: list[dict]) -> None:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row[group_key]].append(row)
    for key, entries in grouped.items():
        ordered = sorted(entries, key=lambda row: _day(row["effective_from"]))
        last_end = None
        for row in ordered:
            start = _day(row["effective_from"])
            if last_end is not None and start <= last_end:
                _issue(issues, "OVERLAPPING_EFFECTIVE_INTERVAL", f"{label}: {key}")
            end = _day(row["effective_to"]) if row["effective_to"] is not None else pd.Timestamp.max
            last_end = max(last_end, end) if last_end is not None else end


def _check_market_data(value: Mapping, issues: list[dict]) -> None:
    instruments = defaultdict(list)
    for row in value["instruments"]:
        instruments[row["instrument_id"]].append(row)
    statuses = defaultdict(list)
    for row in value["statuses"]:
        statuses[row["instrument_id"]].append(row)
    sessions = {(row["market"], row["date"]): row for row in value["calendar"]}
    markets = {row["market"] for row in value["instruments"]}
    for day in pd.date_range(value["metadata"]["start"], value["metadata"]["end"], freq="D"):
        for market in markets:
            if (market, day.date().isoformat()) not in sessions:
                _issue(issues, "CALENDAR_DATE_MISSING", f"{market}: {day.date()}")
    _intervals(value["instruments"], "instrument_id", "instrument", issues)
    _intervals(value["instruments"], "code", "code", issues)
    _intervals(value["statuses"], "instrument_id", "status", issues)
    _intervals(value["market_profiles"], "market", "market profile", issues)
    if not value["prices"]:
        _issue(issues, "EMPTY_PRICES")
    price_rows = defaultdict(list)
    for price in value["prices"]:
        price_rows[(price["instrument_id"], price["date"])].append(price)

    for price in value["prices"]:
        when = _day(price["date"])
        matches = _active(instruments[price["instrument_id"]], when)
        if len(matches) != 1 or (matches and matches[0]["code"] != price["code"]):
            _issue(issues, "INVALID_EFFECTIVE_CODE", f"{price['instrument_id']}: {price['date']}")
            continue
        session = sessions.get((matches[0]["market"], price["date"]))
        if session is None or not session["is_open"]:
            _issue(issues, "PRICE_OUTSIDE_OPEN_SESSION", f"{price['instrument_id']}: {price['date']}")
        raw = np.asarray([price[name] for name in ("open", "high", "low", "close")], dtype=float)
        adjusted = np.asarray([price[f"adjusted_{name}"] for name in ("open", "high", "low", "close")], dtype=float)
        if not np.allclose(adjusted, raw * float(price["price_factor"]), rtol=1e-12, atol=1e-12):
            _issue(issues, "ADJUSTED_PRICE_FACTOR_MISMATCH", f"{price['instrument_id']}: {price['date']}")
        state = _active(statuses[price["instrument_id"]], when)
        if len(state) != 1:
            _issue(issues, "PRICE_OUTSIDE_TRADING_STATUS", f"{price['instrument_id']}: {price['date']}")
            continue
        if state[0]["status"] == "DELISTED":
            _issue(issues, "HALTED_OR_DELISTED_PRICE", state[0]["status_id"])
            continue
        if state[0]["status"] == "HALTED":
            if float(price["volume"]) != 0:
                _issue(issues, "HALTED_NONZERO_VOLUME", state[0]["status_id"])
            continue
        if (not np.isfinite(raw).all() or (raw <= 0).any() or raw[1] < raw.max() or raw[2] > raw.min()):
            _issue(issues, "INVALID_TRADING_OHLC", f"{price['instrument_id']}: {price['date']}")

    for (market, day), session in sessions.items():
        when = _day(day)
        if not session["is_open"]:
            continue
        profiles = _active([row for row in value["market_profiles"] if row["market"] == market], when)
        if len(profiles) != 1:
            _issue(issues, "MARKET_PROFILE_COVERAGE_INVALID", f"{market}: {day}")
        for instrument_id, entries in instruments.items():
            active_instruments = [row for row in _active(entries, when) if row["market"] == market]
            if not active_instruments:
                continue
            current_status = _active(statuses[instrument_id], when)
            if len(current_status) != 1:
                _issue(issues, "STATUS_COVERAGE_INVALID", f"{instrument_id}: {day}")
            elif current_status[0]["status"] == "TRADING" and not price_rows[(instrument_id, day)]:
                _issue(issues, "MISSING_TRADING_PRICE", f"{instrument_id}: {day}")


def _check_sources_and_events(value: Mapping, hashes: dict[str, str], issues: list[dict]) -> None:
    declared_hashes = set(hashes.values())
    sources = {row["source_id"]: row for row in value["sources"]}
    for source in sources.values():
        if source["raw_file_sha256"] not in declared_hashes:
            _issue(issues, "SOURCE_RAW_HASH_UNLINKED", source["source_id"])
        if source["time_precision"] != "timestamp" or source["historical_capture"] == "unavailable":
            _issue(issues, "SOURCE_TIME_UNRESOLVED", source["source_id"])
    instruments = defaultdict(list)
    for row in value["instruments"]:
        instruments[row["instrument_id"]].append(row)
    sessions = {(row["market"], row["date"]): row for row in value["calendar"]}
    for event in value["events"]:
        matching = _active(instruments[event["instrument_id"]], _day(event["effective_date"]))
        session = sessions.get((matching[0]["market"], event["effective_date"])) if len(matching) == 1 else None
        if session is None or not session["is_open"]:
            _issue(issues, "EVENT_EFFECTIVE_SESSION_UNKNOWN", event["event_id"])
            continue
        announced = pd.Timestamp(event["announced_at"])
        opens = pd.Timestamp(session["opens_at"])
        if announced >= opens:
            _issue(issues, "EVENT_ANNOUNCED_AFTER_EFFECTIVE_OPEN", event["event_id"])
        source = sources[event["source_id"]]
        if source["time_precision"] == "timestamp" and announced < pd.Timestamp(source["published_at"]):
            _issue(issues, "EVENT_ANNOUNCEMENT_BEFORE_SOURCE", event["event_id"])


def _revision_summary(value: Mapping, previous: Mapping | None, issues: list[dict]) -> dict[str, Any]:
    if previous is None:
        if value["metadata"]["previous_revision"] is not None:
            _issue(issues, "PREVIOUS_REVISION_REQUIRED", str(value["metadata"]["previous_revision"]))
        return {"previous_revision": None, "changed_keys": {}}
    try:
        prior = validate_delivery(previous)
    except ContractError as exc:
        _issue(issues, "PREVIOUS_SCHEMA_INVALID", exc.code)
        return {"previous_revision": None, "changed_keys": {}}
    metadata, old_metadata = value["metadata"], prior["metadata"]
    if metadata["revision"] == old_metadata["revision"]:
        _issue(issues, "REVISION_NOT_ADVANCED", metadata["revision"])
    if metadata["previous_revision"] != old_metadata["revision"] or metadata["dataset_id"] != old_metadata["dataset_id"]:
        _issue(issues, "INVALID_PREVIOUS_REVISION_LINK", metadata["revision"])
    changed = {}
    for section, fields in _ROW_KEYS.items():
        before = {tuple(row[field] for field in fields): canonical_hash(row) for row in prior[section]}
        after = {tuple(row[field] for field in fields): canonical_hash(row) for row in value[section]}
        changed[section] = sorted(repr(key) for key in set(before) ^ set(after) | {key for key in set(before) & set(after) if before[key] != after[key]})
    return {"previous_revision": old_metadata["revision"], "changed_keys": changed}


def inspect_delivery(delivery: Mapping, root: Path, previous: Mapping | None = None) -> dict[str, Any]:
    """Inspect a delivery without changing it or granting real-data admission."""
    issues: list[dict] = []
    try:
        value = validate_delivery(delivery)
    except ContractError as exc:
        _issue(issues, "SCHEMA_INVALID", exc.code)
        return {"grade": "BLOCKED", "admission": "INSPECTION_ONLY", "issues": issues,
                "limitations": ["SCHEMA_VALIDATION_REQUIRED", "REAL_EXECUTION_NOT_ADMITTED"]}
    hashes = _check_files(value, Path(root), issues)
    _check_market_data(value, issues)
    _check_sources_and_events(value, hashes, issues)
    revision = _revision_summary(value, previous, issues)
    grade = delivery_grade(value["source_kind"], issues)
    return {"grade": grade, "admission": "INSPECTION_ONLY", "issues": issues,
            "limitations": (["SYNTHETIC_DATA_ONLY"] if grade == "SYNTHETIC" else ["REAL_EXECUTION_NOT_ADMITTED"]),
            "dataset_id": value["metadata"]["dataset_id"], "revision": value["metadata"]["revision"],
            "file_hashes": hashes, "revision_summary": revision}
