"""Fail-closed profiling for the sealed ted-startup source contract.

The profiler never repairs source data and never grants execution permission.
It derives a conservative instrument scope from immutable snapshot relations so
that the separate Gate A receipt can bind the exact usable scope.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from typing import Any

import pandas as pd

from .io import canonical_hash


DATASET_NAME = "krx-backtest-source"
REVISION_ID = "0eeed564-0b89-587c-b8f9-d8eea981bb9e"
REVISION_LABEL = "2014-2023-v3"
REVISION_SHA256 = "e95066aa516971ff63e4d6da19a7639b0eab18783eca159a428dc268a2bd13c2"
PERIOD_START = "2014-01-01"
PERIOD_END = "2023-12-31"
EVALUATION_START = "2015-06-15"

REQUIRED_TABLES = {
    "PRICE",
    "UNIVERSE",
    "CALENDAR",
    "STATUS",
    "CORPORATE_ACTION",
    "ADJUSTMENT",
    "EXECUTION_RULE",
    "ADMISSION_ISSUE",
}
HALTED_STATES = {"HALTED", "NO_BAR_HALTED"}


class SourceContractAdmissionError(ValueError):
    """Raised when the snapshot cannot be profiled without guessing."""

    def __init__(self, code: str, detail: str = ""):
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


def _require_columns(frame: pd.DataFrame, names: set[str], label: str) -> None:
    missing = sorted(names - set(frame.columns))
    if missing:
        raise SourceContractAdmissionError("MISSING_COLUMNS", f"{label}: {missing}")


def _day_series(frame: pd.DataFrame, name: str) -> pd.Series:
    try:
        values = pd.to_datetime(frame[name], errors="raise").dt.normalize()
    except (TypeError, ValueError) as exc:
        raise SourceContractAdmissionError("INVALID_DATE", f"{name}: {exc}") from exc
    return values


def _check_manifest(manifest: Mapping[str, Any]) -> None:
    expected = {
        "dataset_name": DATASET_NAME,
        "revision_id": REVISION_ID,
        "revision_label": REVISION_LABEL,
        "revision_content_sha256": REVISION_SHA256,
        "revision_status": "SEALED",
        "period_start": PERIOD_START,
        "period_end": PERIOD_END,
    }
    for name, value in expected.items():
        if manifest.get(name) != value:
            raise SourceContractAdmissionError("REVISION_BINDING_MISMATCH", name)


def _price_profile(prices: pd.DataFrame) -> tuple[dict[int, set[pd.Timestamp]], set[int], dict[int, set[str]]]:
    required = {"stock_id", "stock_code", "trading_date", "adjusted", "open_price", "high_price",
                "low_price", "close_price"}
    _require_columns(prices, required, "PRICE")
    value = prices.copy()
    value["trading_date"] = _day_series(value, "trading_date")
    keys = ["stock_id", "trading_date", "adjusted"]
    if value.duplicated(keys).any():
        raise SourceContractAdmissionError("DUPLICATE_PRICE_KEY")
    ohlc = value[["open_price", "high_price", "low_price", "close_price"]].apply(
        pd.to_numeric, errors="coerce"
    )
    valid = ohlc.notna().all(axis=1) & ohlc.gt(0).all(axis=1)
    valid &= ohlc["high_price"].ge(ohlc.max(axis=1)) & ohlc["low_price"].le(ohlc.min(axis=1))
    value["row_valid"] = valid

    paired: dict[int, set[pd.Timestamp]] = defaultdict(set)
    reasons: dict[int, set[str]] = defaultdict(set)
    blocked: set[int] = set()
    for (stock_id, trading_day), group in value.groupby(["stock_id", "trading_date"], sort=False):
        stock_id = int(stock_id)
        if len(group) != 2 or set(group["adjusted"].map(bool)) != {False, True}:
            blocked.add(stock_id)
            reasons[stock_id].add("RAW_ADJUSTED_PAIR_MISSING")
        elif not group["row_valid"].all():
            blocked.add(stock_id)
            reasons[stock_id].add("INVALID_PRICE_ROW")
        else:
            paired[stock_id].add(pd.Timestamp(trading_day))
    return paired, blocked, reasons


def _expected_sessions(universe: pd.DataFrame, calendar: pd.DataFrame,
                       statuses: pd.DataFrame) -> tuple[dict[int, set[pd.Timestamp]], dict[int, str]]:
    _require_columns(universe, {"stock_id", "stock_code", "security_type", "valid_from", "valid_to"}, "UNIVERSE")
    _require_columns(calendar, {"market", "trading_date", "is_open"}, "CALENDAR")
    _require_columns(statuses, {"stock_id", "trading_date", "daily_state"}, "STATUS")
    days = calendar.loc[(calendar["market"] == "KRX") & calendar["is_open"].map(bool)].copy()
    days["trading_date"] = _day_series(days, "trading_date")
    open_days = pd.DatetimeIndex(sorted(days["trading_date"].unique()))
    if open_days.empty:
        raise SourceContractAdmissionError("OPEN_CALENDAR_EMPTY")
    status_value = statuses.copy()
    status_value["trading_date"] = _day_series(status_value, "trading_date")
    halted: dict[int, set[pd.Timestamp]] = defaultdict(set)
    for row in status_value.loc[status_value["daily_state"].isin(HALTED_STATES)].itertuples():
        halted[int(row.stock_id)].add(pd.Timestamp(row.trading_date))

    expected: dict[int, set[pd.Timestamp]] = defaultdict(set)
    codes: dict[int, str] = {}
    common = universe.loc[universe["security_type"] == "COMMON_STOCK"].copy()
    common["valid_from"] = _day_series(common, "valid_from")
    common["valid_to"] = _day_series(common, "valid_to")
    for row in common.itertuples():
        stock_id = int(row.stock_id)
        code = str(row.stock_code)
        previous = codes.setdefault(stock_id, code)
        if previous != code:
            raise SourceContractAdmissionError("AMBIGUOUS_STOCK_CODE", str(stock_id))
        interval = open_days[(open_days >= row.valid_from) & (open_days <= row.valid_to)]
        expected[stock_id].update(pd.Timestamp(day) for day in interval if pd.Timestamp(day) not in halted[stock_id])
    return expected, codes


def _apply_member_exclusions(tables: Mapping[str, pd.DataFrame], codes: Mapping[int, str],
                             blocked: set[int], reasons: dict[int, set[str]]) -> None:
    inverse_codes = {code: stock_id for stock_id, code in codes.items()}
    issues = tables["ADMISSION_ISSUE"]
    _require_columns(issues, {"issue_code", "affected_scope", "decision"}, "ADMISSION_ISSUE")
    for row in issues.itertuples():
        scope = str(row.affected_scope)
        if str(row.decision) not in {"REJECT", "QUARANTINE"} or not scope.startswith("stock:"):
            continue
        stock_id = inverse_codes.get(scope.split(":", 1)[1])
        if stock_id is not None and str(row.issue_code) != "WARMUP_250_BARS_SHORT":
            blocked.add(stock_id)
            reasons[stock_id].add(str(row.issue_code))

    events = tables["CORPORATE_ACTION"]
    _require_columns(events, {"stock_id", "resolution_status"}, "CORPORATE_ACTION")
    for stock_id in events.loc[events["resolution_status"] == "PARTIAL", "stock_id"].dropna().unique():
        blocked.add(int(stock_id))
        reasons[int(stock_id)].add("CORPORATE_ACTION_PARTIAL")

    adjustments = tables["ADJUSTMENT"]
    _require_columns(adjustments, {"stock_id", "explanation_status"}, "ADJUSTMENT")
    unexplained = adjustments["explanation_status"].isin({"OBSERVED_VENDOR_FACTOR", "UNEXPLAINED_VENDOR_FACTOR"})
    for stock_id in adjustments.loc[unexplained, "stock_id"].dropna().unique():
        blocked.add(int(stock_id))
        reasons[int(stock_id)].add("UNEXPLAINED_VENDOR_FACTOR")


def profile_source_contract(tables: Mapping[str, pd.DataFrame], manifest: Mapping[str, Any],
                            *, evaluation_start: str = EVALUATION_START) -> dict[str, Any]:
    """Return a conservative Gate A profile without granting execution.

    Any instrument with an unexplained missing/invalid raw-adjusted pair, a
    partial corporate action, or an unexplained vendor factor is excluded for
    the whole experiment. This deliberate over-exclusion compensates for the
    v3 issue view omitting some row identifiers.
    """
    _check_manifest(manifest)
    missing = sorted(REQUIRED_TABLES - set(tables))
    if missing:
        raise SourceContractAdmissionError("MISSING_RELATIONS", str(missing))
    first = pd.Timestamp(date.fromisoformat(evaluation_start))
    if first < pd.Timestamp(PERIOD_START) or first > pd.Timestamp(PERIOD_END):
        raise SourceContractAdmissionError("INVALID_EVALUATION_START", evaluation_start)

    paired, blocked, reasons = _price_profile(tables["PRICE"])
    expected, codes = _expected_sessions(tables["UNIVERSE"], tables["CALENDAR"], tables["STATUS"])
    for stock_id, expected_days in expected.items():
        missing_days = expected_days - paired.get(stock_id, set())
        if missing_days:
            blocked.add(stock_id)
            reasons[stock_id].add("UNEXPLAINED_TRADING_PRICE_GAP")
    _apply_member_exclusions(tables, codes, blocked, reasons)

    scopes = []
    for stock_id in sorted(set(expected) - blocked):
        history = sorted(day for day in paired.get(stock_id, set()) if day in expected[stock_id])
        if len(history) < 250:
            blocked.add(stock_id)
            reasons[stock_id].add("WARMUP_250_BARS_UNAVAILABLE")
            continue
        ready = max(first, history[249])
        allowed = [day for day in history if day >= ready]
        if not allowed:
            blocked.add(stock_id)
            reasons[stock_id].add("NO_EVALUATION_SESSIONS")
            continue
        scopes.append({"instrument_id": str(stock_id), "code": codes[stock_id],
                       "allowed_from": allowed[0].date().isoformat(), "allowed_to": allowed[-1].date().isoformat()})

    exclusions = [{"instrument_id": str(stock_id), "code": codes.get(stock_id),
                   "reasons": sorted(values)} for stock_id, values in sorted(reasons.items()) if stock_id in blocked]
    issue_counts = tables["ADMISSION_ISSUE"].groupby(["decision", "severity"], dropna=False).size()
    issue_summary = {f"{decision}:{severity}": int(count) for (decision, severity), count in issue_counts.items()}
    checks = {
        "revision_binding": "PASS",
        "required_relations": "PASS",
        "raw_adjusted_completeness": "PASS_WITH_CONSERVATIVE_INSTRUMENT_EXCLUSIONS",
        "point_in_time_sector": "NOT_AVAILABLE_NOT_APPLIED",
    }
    result = {
        "schema_version": "krx-source-admission-profile-v1",
        "decision": "CONDITIONALLY_ADMITTED" if scopes else "BLOCKED",
        "execution_allowed": False,
        "dataset_id": DATASET_NAME,
        "revision": REVISION_LABEL,
        "revision_id": REVISION_ID,
        "manifest_sha256": canonical_hash(manifest),
        "evaluation_start": evaluation_start,
        "execution_policy": {"sector_cap": None, "sector_data_used": False},
        "checks": checks,
        "scope": scopes,
        "scope_sha256": canonical_hash(scopes),
        "exclusions": exclusions,
        "exclusions_sha256": canonical_hash(exclusions),
        "issue_summary": issue_summary,
        "limitations": ["POINT_IN_TIME_SECTOR_UNAVAILABLE", "V3_PRICE_ISSUE_KEYS_INCOMPLETE",
                        "CONSERVATIVE_WHOLE_INSTRUMENT_EXCLUSION", "EXECUTION_GATE_NOT_GRANTED"],
    }
    return result
