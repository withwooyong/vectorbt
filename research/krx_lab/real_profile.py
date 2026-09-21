"""Fail-closed, read-only precheck for a proposed single-KRX daily REAL run.

This checks only facts expressible in a C1 delivery. It does not verify the
collector's historical completeness, market-rule provenance, or a fill ledger.
No current C1 market model can execute REAL orders.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import date
import math
from typing import Any

from .contracts import validate_delivery


FIRST_DAY = date(2015, 1, 1)
LAST_DAY = date(2023, 12, 31)


def _active(rows: list[dict], day: str) -> list[dict]:
    return [row for row in rows if row["effective_from"] <= day
            and (row["effective_to"] is None or day <= row["effective_to"])]


def precheck_real_daily_profile(delivery: Mapping) -> dict[str, Any]:
    """Report C1-level blockers, never admission or permission to execute.

    The input must be C1-valid; malformed input raises ``ContractError``.
    Findings are deliberately narrower than real-data admission. In
    particular, a complete-looking C1 file cannot prove absence of omitted
    instruments, corporate actions, closures, or historical fee changes.
    """
    value = validate_delivery(delivery)
    issues: list[dict[str, str]] = []

    def issue(code: str, detail: str = "") -> None:
        issues.append({"code": code, "detail": detail})

    if value["source_kind"] != "REAL":
        issue("REAL_SOURCE_REQUIRED")

    metadata = value["metadata"]
    start, end = date.fromisoformat(metadata["start"]), date.fromisoformat(metadata["end"])
    if start < FIRST_DAY or end > LAST_DAY:
        issue("OUTSIDE_2015_2023_DAILY_SCOPE", f"{start}/{end}")
    if metadata["currency"] != "KRW":
        issue("KRW_CURRENCY_REQUIRED", str(metadata["currency"]))

    instruments = defaultdict(list)
    for row in value["instruments"]:
        instruments[row["instrument_id"]].append(row)
        if row["market"] != "KRX":
            issue("SINGLE_KRX_MARKET_REQUIRED", row["instrument_id"])
    if not instruments:
        issue("INSTRUMENT_HISTORY_EMPTY")

    calendars = {row["date"]: row for row in value["calendar"] if row["market"] == "KRX"}
    for row in value["calendar"]:
        if row["market"] != "KRX":
            issue("NON_KRX_CALENDAR", row["date"])
        if not metadata["start"] <= row["date"] <= metadata["end"]:
            issue("CALENDAR_OUTSIDE_RUN_RANGE", row["date"])
    for boundary in (metadata["start"], metadata["end"]):
        if boundary not in calendars:
            issue("CALENDAR_BOUNDARY_MISSING", boundary)
    if not any(row["is_open"] for row in calendars.values()):
        issue("OPEN_SESSION_ABSENT")

    profiles = defaultdict(list)
    for row in value["market_profiles"]:
        profiles[row["market"]].append(row)
        if row["market"] != "KRX":
            issue("NON_KRX_PROFILE", row["profile_id"])
        if row["model"] == "SYNTHETIC_FIXED":
            issue("SYNTHETIC_PROFILE_IN_REAL", row["profile_id"])
        else:
            issue("REAL_PROFILE_MODEL_UNIMPLEMENTED", f"{row['profile_id']}: {row['model']}")
        # Numeric fields are shape-checked by C1, but C1 does not establish
        # that these values match dated KRX, broker, or tax rules.
        if row["tick_size"] == 0:
            issue("ZERO_TICK_SIZE", row["profile_id"])
    if not profiles["KRX"]:
        issue("KRX_COST_AND_MARKET_PROFILE_MISSING")

    statuses = defaultdict(list)
    for row in value["statuses"]:
        statuses[row["instrument_id"]].append(row)
    events_by_instrument = defaultdict(list)
    for event in value["events"]:
        events_by_instrument[event["instrument_id"]].append(event)
    prices = {(row["instrument_id"], row["date"]): row for row in value["prices"]}
    for day, session in calendars.items():
        if not session["is_open"]:
            continue
        for instrument_id, history in instruments.items():
            identity = _active(history, day)
            if not identity:
                continue
            if len(identity) != 1:
                issue("AMBIGUOUS_INSTRUMENT_HISTORY", f"{instrument_id}: {day}")
                continue
            state = _active(statuses[instrument_id], day)
            if len(state) != 1:
                issue("MISSING_OR_AMBIGUOUS_STATUS", f"{instrument_id}: {day}")
            market_profile = _active(profiles["KRX"], day)
            if len(market_profile) != 1:
                issue("MISSING_OR_AMBIGUOUS_MARKET_PROFILE", day)
            if len(state) == 1 and state[0]["status"] == "TRADING" and (instrument_id, day) not in prices:
                issue("TRADING_PRICE_MISSING", f"{instrument_id}: {day}")

    for row in value["prices"]:
        instrument_id, day = row["instrument_id"], row["date"]
        session = calendars.get(day)
        if session is None or not session["is_open"]:
            issue("PRICE_WITHOUT_OPEN_KRX_SESSION", f"{instrument_id}: {day}")
        if len(_active(instruments[instrument_id], day)) != 1:
            issue("PRICE_WITHOUT_UNIQUE_INSTRUMENT", f"{instrument_id}: {day}")
        if len(_active(statuses[instrument_id], day)) != 1:
            issue("PRICE_WITHOUT_UNIQUE_STATUS", f"{instrument_id}: {day}")
        for field in ("open", "high", "low", "close"):
            expected = row[field] * row["price_factor"]
            if not math.isclose(row[f"adjusted_{field}"], expected, rel_tol=1e-12, abs_tol=1e-12):
                issue("ADJUSTED_PRICE_FACTOR_MISMATCH", f"{instrument_id}: {day}: {field}")
        if row["price_factor"] != 1 or row["quantity_factor"] != 1:
            if not events_by_instrument[instrument_id]:
                issue("NONUNIT_FACTOR_WITHOUT_EVENT", f"{instrument_id}: {day}")
            # A dated event for the same instrument, including one many years
            # away, is not a demonstrated factor-to-event relationship. C1
            # carries no such link or adjustment revision chain.
            issue("NONUNIT_FACTOR_EVENT_LINKAGE_UNVERIFIED", f"{instrument_id}: {day}")

    for event in value["events"]:
        day = event["effective_date"]
        if not metadata["start"] <= day <= metadata["end"]:
            issue("EVENT_OUTSIDE_RUN_RANGE", event["event_id"])
        if len(_active(instruments[event["instrument_id"]], day)) != 1:
            issue("EVENT_WITHOUT_UNIQUE_INSTRUMENT", event["event_id"])

    # These are mandatory independent reviews, even when all C1 rows agree.
    for code in ("COST_AND_MARKET_RULE_PROVENANCE_UNVERIFIED",
                 "OFFICIAL_SESSION_COMPLETENESS_UNVERIFIED",
                 "CORPORATE_ACTION_COMPLETENESS_UNVERIFIED",
                 "HISTORICAL_UNIVERSE_AND_STATUS_COMPLETENESS_UNVERIFIED",
                 "RAW_ADJUSTED_FACTOR_PROVENANCE_UNVERIFIED",
                 "REAL_FILL_AND_LEDGER_UNVERIFIED"):
        issue(code)

    return {"grade": "BLOCKED", "admission": "PRECHECK_ONLY", "execution_allowed": False,
            "dataset_id": metadata["dataset_id"], "revision": metadata["revision"], "issues": issues,
            "limitations": ["REAL_EXECUTION_NOT_ADMITTED"]}
