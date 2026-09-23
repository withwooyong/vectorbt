"""Versioned, JSON-native interfaces for synthetic backtest-lab development.

These shape checks are not data admission or evidence of real market rules.
Existing snapshot-v1 and simulator outputs remain independent interfaces.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime
import math
from pathlib import PurePosixPath
import re
from typing import Any


CONTRACT_VERSION = "krx-lab-contracts-v1"
SUPPORTED_EVENT_TYPES = frozenset({"SPLIT", "REVERSE_SPLIT", "CASH_DIVIDEND", "DELIST_CASH",
                                    "BONUS_ISSUE", "STOCK_DIVIDEND"})
HOOK_STAGES = frozenset({
    "run_start", "simulation_day", "resource_exceeded", "stop_requested", "before_artifacts",
    "after_artifacts", "before_rename", "after_rename", "before_registry_commit",
    "after_registry_commit", "resume",
})
LIFECYCLE_TRANSITIONS = {
    "DRAFT": frozenset({"FROZEN", "NO_SELECTION", "FAILED"}),
    "FROZEN": frozenset({"FINALIZED", "FAILED"}),
    "FAILED": frozenset({"FAILED"}),
    "NO_SELECTION": frozenset(),
    "FINALIZED": frozenset(),
}
PREREQUISITES = (
    "data_verified", "candidate_policy_frozen", "realistic_costs_verified", "holdout_implementation_verified",
)


class ContractError(ValueError):
    """Stable machine-readable code with a human-readable field location."""

    def __init__(self, code: str, detail: str = ""):
        self.code = code
        super().__init__(f"{code}: {detail}" if detail else code)


def _require(value: Mapping, fields: tuple | list, location: str) -> None:
    if not isinstance(value, Mapping):
        raise ContractError("INVALID_OBJECT", location)
    missing = set(fields) - value.keys()
    if missing:
        raise ContractError("MISSING_FIELDS", f"{location}: {sorted(missing)}")


def _text(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("INVALID_TEXT", location)
    return value


def _number(value: Any, location: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError("INVALID_NUMBER", location)
    if minimum is not None and value < minimum:
        raise ContractError("INVALID_NUMBER", location)
    return value


def _day(value: Any, location: str) -> date:
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError()
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ContractError("INVALID_DATE", location) from None


def _instant(value: Any, location: str) -> datetime:
    try:
        if not isinstance(value, str):
            raise ValueError()
        result = datetime.fromisoformat(value)
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError()
        return result
    except (TypeError, ValueError):
        raise ContractError("INVALID_TIMESTAMP", location) from None


def _sha(value: Any, location: str) -> None:
    if not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None:
        raise ContractError("INVALID_SHA256", location)


def _rows(value: Any, location: str) -> list:
    if not isinstance(value, list) or any(not isinstance(row, Mapping) for row in value):
        raise ContractError("INVALID_ROWS", location)
    return value


def _unique(rows: list, keys: tuple, location: str) -> None:
    found = set()
    for row in rows:
        _require(row, keys, location)
        key = tuple(row[name] for name in keys)
        try:
            if key in found:
                raise ContractError("DUPLICATE_KEY", f"{location}: {key}")
            found.add(key)
        except TypeError:
            raise ContractError("INVALID_KEY", location) from None


def _header(value: Mapping, fields: tuple) -> dict:
    _require(value, ("schema_version", "source_kind", *fields), "root")
    if value["schema_version"] != CONTRACT_VERSION:
        raise ContractError("UNSUPPORTED_VERSION", str(value["schema_version"]))
    if value["source_kind"] not in {"SYNTHETIC", "REAL"}:
        raise ContractError("INVALID_SOURCE_KIND")
    return deepcopy(dict(value))


def _interval(row: Mapping, location: str) -> None:
    _require(row, ("effective_from", "effective_to"), location)
    first = _day(row["effective_from"], location)
    last = _day(row["effective_to"], location) if row["effective_to"] is not None else None
    if last is not None and first > last:
        raise ContractError("REVERSED_INTERVAL", location)


def validate_delivery(delivery: Mapping) -> dict:
    """Check C1 shape and supported policy; D2 owns lineage/coverage/admission checks.

    Dates use inclusive effective intervals. All prices are raw execution prices;
    adjusted prices equal raw prices times price_factor with exact/no rounding in
    this synthetic profile. Real deliveries may be inspected but are not admitted.
    """
    result = _header(delivery, (
        "metadata", "sources", "prices", "events", "instruments", "statuses", "calendar", "market_profiles",
    ))
    metadata = result["metadata"]
    _require(metadata, ("dataset_id", "revision", "previous_revision", "extracted_at", "start", "end",
                        "currency", "price_basis", "adjustment_definition", "files", "real_data_admitted",
                        "holdout_prices_included"), "metadata")
    for name in ("dataset_id", "revision", "currency", "adjustment_definition"):
        _text(metadata[name], f"metadata.{name}")
    _instant(metadata["extracted_at"], "metadata.extracted_at")
    start, end = _day(metadata["start"], "start"), _day(metadata["end"], "end")
    if start > end:
        raise ContractError("REVERSED_INTERVAL", "metadata")
    if metadata["real_data_admitted"] is not False:
        raise ContractError("REAL_ADMISSION_NOT_GRANTED")
    if metadata["holdout_prices_included"] is not False or end >= date(2024, 1, 1):
        raise ContractError("HOLDOUT_LOCKED")
    if metadata["price_basis"] != "raw":
        raise ContractError("RAW_PRICES_REQUIRED")
    validate_files(metadata["files"])
    for section in ("sources", "prices", "events", "instruments", "statuses", "calendar", "market_profiles"):
        _rows(result[section], section)
    for section, keys in (("sources", ("source_id",)), ("prices", ("instrument_id", "date")),
                          ("events", ("event_id",)), ("instruments", ("instrument_id", "effective_from")),
                          ("statuses", ("status_id",)), ("calendar", ("market", "date")),
                          ("market_profiles", ("profile_id",))):
        _unique(result[section], keys, section)
    source_ids = set()
    for row in result["sources"]:
        _require(row, ("source_id", "source_url_or_document_id", "published_at", "time_precision", "captured_at",
                       "raw_file_sha256", "historical_capture"), "sources")
        source_ids.add(_text(row["source_id"], "source_id"))
        _text(row["source_url_or_document_id"], "source_url_or_document_id")
        _instant(row["captured_at"], "captured_at")
        _sha(row["raw_file_sha256"], "raw_file_sha256")
        precision = row["time_precision"]
        if precision == "timestamp":
            published = _instant(row["published_at"], "published_at")
            captured = _instant(row["captured_at"], "captured_at")
            if published > captured or captured > _instant(metadata["extracted_at"], "extracted_at"):
                raise ContractError("INVALID_SOURCE_CHRONOLOGY", row["source_id"])
        elif precision == "date":
            _day(row["published_at"], "published_at")
        elif precision != "unknown" or row["published_at"] is not None or not row.get("unavailable_reason"):
            raise ContractError("INVALID_TIME_PRECISION")
        if row["historical_capture"] not in {"synthetic", "original", "new_observation", "unavailable"}:
            raise ContractError("INVALID_CAPTURE_KIND")
        if result["source_kind"] == "REAL" and row["historical_capture"] == "synthetic":
            raise ContractError("SYNTHETIC_SOURCE_MISLABELED")
    for section in ("prices", "events", "instruments", "statuses", "calendar", "market_profiles"):
        for row in result[section]:
            _require(row, ("source_id",), section)
            if row["source_id"] not in source_ids:
                raise ContractError("UNKNOWN_SOURCE", section)
    instrument_ids = set()
    for row in result["instruments"]:
        _require(row, ("instrument_id", "code", "market", "product_type", "sector"), "instruments")
        for name in ("instrument_id", "code", "market", "product_type", "sector"):
            _text(row[name], name)
        instrument_ids.add(row["instrument_id"])
        _interval(row, "instruments")
    for section in ("prices", "events", "statuses"):
        for row in result[section]:
            _require(row, ("instrument_id",), section)
            if row["instrument_id"] not in instrument_ids:
                raise ContractError("UNKNOWN_INSTRUMENT", section)
    for row in result["prices"]:
        _require(row, ("date", "code", "open", "high", "low", "close", "volume", "turnover", "price_factor",
                       "quantity_factor", "adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close"), "prices")
        day = _day(row["date"], "prices.date")
        if not start <= day <= end:
            raise ContractError("PRICE_OUTSIDE_RANGE")
        for name in ("open", "high", "low", "close", "volume", "turnover"):
            _number(row[name], name, minimum=0)
        for name in ("price_factor", "quantity_factor"):
            if _number(row[name], name, minimum=0) == 0:
                raise ContractError("INVALID_FACTOR", name)
        for name in ("open", "high", "low", "close"):
            _number(row[f"adjusted_{name}"], f"adjusted_{name}", minimum=0)
    for row in result["events"]:
        _require(row, ("event_id", "event_type", "effective_date", "announced_at", "record_date", "pay_date",
                       "correction_of", "cancelled"), "events")
        _text(row["event_id"], "event_id")
        _day(row["effective_date"], "effective_date")
        _instant(row["announced_at"], "announced_at")
        if row["event_type"] not in SUPPORTED_EVENT_TYPES:
            raise ContractError("UNSUPPORTED_EVENT", str(row["event_type"]))
        if row["cancelled"] is not False or row["correction_of"] is not None:
            raise ContractError("EVENT_REVISION_REQUIRES_RESOLUTION", row["event_id"])
        if row["event_type"] in {"SPLIT", "REVERSE_SPLIT"}:
            _require(row, ("quantity_ratio", "fractional_policy"), "events")
            if _number(row["quantity_ratio"], "quantity_ratio", minimum=0) == 0:
                raise ContractError("INVALID_FACTOR", "quantity_ratio")
            if row["fractional_policy"] not in {"REJECT", "CASH_IN_LIEU"}:
                raise ContractError("UNSUPPORTED_FRACTIONAL_POLICY")
            if row["fractional_policy"] == "CASH_IN_LIEU":
                _require(row, ("fractional_cash_price", "pay_date"), "events")
                _number(row["fractional_cash_price"], "fractional_cash_price", minimum=0)
                if _day(row["pay_date"], "pay_date") < _day(row["effective_date"], "effective_date"):
                    raise ContractError("PAYMENT_BEFORE_ENTITLEMENT")
        elif row["event_type"] in {"BONUS_ISSUE", "STOCK_DIVIDEND"}:
            if row.get("allotment_ratio_admitted") is not True:
                raise ContractError("UNADMITTED_ALLOTMENT_RATIO", row["event_id"])
            _require(row, ("allotment_ratio", "fractional_policy"), "events")
            if _number(row["allotment_ratio"], "allotment_ratio", minimum=0) == 0:
                raise ContractError("INVALID_FACTOR", "allotment_ratio")
            if row["fractional_policy"] not in {"REJECT", "CASH_IN_LIEU"}:
                raise ContractError("UNSUPPORTED_FRACTIONAL_POLICY")
            if row["fractional_policy"] == "CASH_IN_LIEU":
                _require(row, ("fractional_cash_price", "pay_date"), "events")
                _number(row["fractional_cash_price"], "fractional_cash_price", minimum=0)
                if _day(row["pay_date"], "pay_date") < _day(row["effective_date"], "effective_date"):
                    raise ContractError("PAYMENT_BEFORE_ENTITLEMENT")
        else:
            _require(row, ("cash_per_share", "withholding_rate", "entitlement_policy"), "events")
            _number(row["cash_per_share"], "cash_per_share", minimum=0)
            if not 0 <= _number(row["withholding_rate"], "withholding_rate") <= 1:
                raise ContractError("INVALID_RATE", "withholding_rate")
            if row["entitlement_policy"] != "PRE_EVENT_HOLDINGS":
                raise ContractError("UNSUPPORTED_ENTITLEMENT_POLICY")
            if _day(row["pay_date"], "pay_date") < _day(row["effective_date"], "effective_date"):
                raise ContractError("PAYMENT_BEFORE_ENTITLEMENT")
            _day(row["record_date"], "record_date")
    for row in result["statuses"]:
        _interval(row, "statuses")
        _require(row, ("status", "reason", "last_trade_date", "official_delist_date"), "statuses")
        if row["status"] not in {"TRADING", "HALTED", "DELISTED"}:
            raise ContractError("UNSUPPORTED_TRADING_STATUS")
        for name in ("last_trade_date", "official_delist_date"):
            if row[name] is not None:
                _day(row[name], name)
    for row in result["calendar"]:
        _require(row, ("date", "market", "is_open", "opens_at", "closes_at", "reason"), "calendar")
        _day(row["date"], "calendar.date")
        if type(row["is_open"]) is not bool:
            raise ContractError("INVALID_BOOLEAN", "calendar.is_open")
        if row["is_open"]:
            session_day = _day(row["date"], "calendar.date")
            if (_instant(row["opens_at"], "opens_at").date() != session_day
                    or _instant(row["closes_at"], "closes_at").date() != session_day):
                raise ContractError("SESSION_DATE_MISMATCH", row["date"])
            if _instant(row["opens_at"], "opens_at") >= _instant(row["closes_at"], "closes_at"):
                raise ContractError("REVERSED_SESSION")
        elif row["opens_at"] is not None or row["closes_at"] is not None:
            raise ContractError("CLOSED_SESSION_HAS_HOURS")
    for row in result["market_profiles"]:
        _require(row, ("profile_id", "market", "model", "tick_size", "lot_size", "buy_fee_rate", "sell_fee_rate",
                       "sell_tax_rate", "slippage_bps", "settlement_delay_days", "rounding"), "market_profiles")
        _interval(row, "market_profiles")
        if row["model"] != "SYNTHETIC_FIXED" or row["rounding"] != "NONE":
            raise ContractError("UNSUPPORTED_MARKET_PROFILE")
        if _number(row["tick_size"], "tick_size", minimum=0) == 0:
            raise ContractError("INVALID_TICK")
        for name in ("lot_size", "settlement_delay_days"):
            if type(row[name]) is not int or row[name] < (1 if name == "lot_size" else 0):
                raise ContractError("INVALID_INTEGER", name)
        for name in ("buy_fee_rate", "sell_fee_rate", "sell_tax_rate"):
            if not 0 <= _number(row[name], name) <= 1:
                raise ContractError("INVALID_RATE", name)
        _number(row["slippage_bps"], "slippage_bps", minimum=0)
    return result


def validate_files(files: list) -> list:
    """Validate relative artifact names and hashes; caller verifies actual bytes."""
    _rows(files, "files")
    _unique(files, ("file",), "files")
    for item in files:
        _require(item, ("file", "sha256", "rows", "schema"), "files")
        name = _text(item["file"], "files.file")
        path = PurePosixPath(name)
        if path.is_absolute() or any(p in {".", ".."} for p in name.split("/")) or "\\" in name or ":" in name:
            raise ContractError("UNSAFE_ARTIFACT_PATH", name)
        _sha(item["sha256"], "files.sha256")
        if type(item["rows"]) is not int or item["rows"] < 0:
            raise ContractError("INVALID_INTEGER", "files.rows")
        _text(item["schema"], "files.schema")
    return deepcopy(files)


def validate_ledger(ledger: Mapping) -> dict:
    """Check C2 transport and per-snapshot equity conservation, not economic truth."""
    result = _header(ledger, ("run_id", "dataset_id", "revision", "currency", "initial_cash", "orders", "fills",
                              "events", "cashflows", "positions", "equity", "issues", "files"))
    for name in ("run_id", "dataset_id", "revision", "currency"):
        _text(result[name], name)
    _number(result["initial_cash"], "initial_cash", minimum=0)
    validate_files(result["files"])
    if not isinstance(result["issues"], list) or any(not isinstance(x, str) for x in result["issues"]):
        raise ContractError("INVALID_ISSUES")
    fields = {
        "orders": ("order_id", "date", "instrument_id", "side", "quantity", "status"),
        "fills": ("ledger_seq", "fill_id", "order_id", "date", "instrument_id", "side", "quantity", "price", "fee", "tax"),
        "events": ("ledger_seq", "event_id", "date", "instrument_id", "event_type", "quantity_delta",
                   "cost_basis_delta", "cash_delta", "receivable_delta", "payable_delta", "fee", "tax"),
        "cashflows": ("ledger_seq", "cashflow_id", "date", "instrument_id", "event_id", "fill_id", "kind", "cash_delta",
                      "receivable_delta", "payable_delta", "fee", "tax"),
        "positions": ("date", "instrument_id", "quantity", "mark_price", "cost_basis", "stale"),
        "equity": ("date", "cash", "receivables", "payables", "exposure", "equity"),
    }
    for section, required in fields.items():
        for row in _rows(result[section], section):
            _require(row, required, section)
            _day(row["date"], f"{section}.date")
            if "instrument_id" in row:
                _text(row["instrument_id"], f"{section}.instrument_id")
            if "ledger_seq" in row and (type(row["ledger_seq"]) is not int or row["ledger_seq"] < 0):
                raise ContractError("INVALID_INTEGER", "ledger_seq")
    for section in ("orders", "fills", "positions"):
        for row in result[section]:
            if type(row["quantity"]) is not int or row["quantity"] < (0 if section == "positions" else 1):
                raise ContractError("INVALID_INTEGER", "quantity")
            if section != "positions" and row["side"] not in {"buy", "sell"}:
                raise ContractError("INVALID_SIDE")
    for row in result["orders"]:
        if row["status"] not in {"PLANNED", "FILLED", "REJECTED", "CANCELLED", "PARTIALLY_FILLED"}:
            raise ContractError("INVALID_ORDER_STATUS")
    for row in result["events"]:
        _text(row["event_id"], "event_id")
        if row["event_type"] not in SUPPORTED_EVENT_TYPES:
            raise ContractError("UNSUPPORTED_EVENT")
        if type(row["quantity_delta"]) is not int:
            raise ContractError("INVALID_INTEGER", "quantity_delta")
        for name in ("cost_basis_delta", "cash_delta", "receivable_delta", "payable_delta", "fee", "tax"):
            _number(row[name], name)
    for section, key in (("orders", "order_id"), ("fills", "fill_id"), ("cashflows", "cashflow_id")):
        _unique(result[section], (key,), section)
        for row in result[section]:
            _text(row[key], key)
    _unique(result["positions"], ("date", "instrument_id"), "positions")
    _unique(result["equity"], ("date",), "equity")
    order_ids = {row["order_id"] for row in result["orders"]}
    fill_ids = {row["fill_id"] for row in result["fills"]}
    for row in result["fills"]:
        if row["order_id"] not in order_ids:
            raise ContractError("UNKNOWN_ORDER")
        for name in ("quantity", "price", "fee", "tax"):
            _number(row[name], name, minimum=0)
    for row in result["cashflows"]:
        if row["fill_id"] is not None and row["fill_id"] not in fill_ids:
            raise ContractError("UNKNOWN_FILL")
        for name in ("cash_delta", "receivable_delta", "payable_delta", "fee", "tax"):
            _number(row[name], name)
    for row in result["positions"]:
        for name in ("quantity", "mark_price", "cost_basis"):
            _number(row[name], name, minimum=0)
        if type(row["stale"]) is not bool:
            raise ContractError("INVALID_BOOLEAN", "stale")
    for row in result["equity"]:
        for name in fields["equity"][1:]:
            _number(row[name], name)
        expected = row["cash"] + row["receivables"] - row["payables"] + row["exposure"]
        if not math.isclose(row["equity"], expected, rel_tol=1e-12, abs_tol=1e-8):
            raise ContractError("EQUITY_NOT_CONSERVED", row["date"])
    return result


def validate_lifecycle_evidence(evidence: Mapping) -> dict:
    """Check C3 evidence shape. D3 verifies hashes, prerequisites, and transitions."""
    result = _header(evidence, ("experiment_id", "state", "candidate_id", "growth_policy", "selection_policy",
                                "code_hash", "data_hash", "cost_profile_hash", "validation_hash", "prerequisites",
                                "holdout_access", "attempts"))
    if result["state"] not in LIFECYCLE_TRANSITIONS:
        raise ContractError("INVALID_LIFECYCLE_STATE")
    for name in ("experiment_id", "growth_policy", "selection_policy"):
        _text(result[name], name)
    for name in ("code_hash", "data_hash", "cost_profile_hash", "validation_hash"):
        _sha(result[name], name)
    _require(result["prerequisites"], PREREQUISITES, "prerequisites")
    if any(type(result["prerequisites"][name]) is not bool for name in PREREQUISITES):
        raise ContractError("INVALID_BOOLEAN", "prerequisites")
    if result["state"] in {"FROZEN", "FINALIZED"}:
        _text(result["candidate_id"], "candidate_id")
    elif result["state"] == "NO_SELECTION" and result["candidate_id"] is not None:
        raise ContractError("NO_SELECTION_HAS_CANDIDATE")
    for row in _rows(result["holdout_access"], "holdout_access"):
        _require(row, ("at", "action", "allowed", "reason"), "holdout_access")
        _instant(row["at"], "holdout_access.at")
        if type(row["allowed"]) is not bool:
            raise ContractError("INVALID_BOOLEAN", "holdout_access.allowed")
        if row["allowed"] and (result["source_kind"] == "SYNTHETIC"
                               or result["state"] not in {"FROZEN", "FINALIZED"}
                               or not all(result["prerequisites"].values())):
            raise ContractError("HOLDOUT_LOCKED")
    for row in _rows(result["attempts"], "attempts"):
        _require(row, ("attempt_id", "at", "action", "status", "reason"), "attempts")
        _instant(row["at"], "attempts.at")
    _unique(result["attempts"], ("attempt_id",), "attempts")
    return result


@dataclass(frozen=True)
class ResourceSample:
    elapsed_seconds: float
    rss_bytes: int
    peak_rss_bytes: int
    disk_free_bytes: int

    def __post_init__(self):
        _number(self.elapsed_seconds, "elapsed_seconds", minimum=0)
        for name in ("rss_bytes", "peak_rss_bytes", "disk_free_bytes"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ContractError("INVALID_RESOURCE_SAMPLE", name)
        if self.peak_rss_bytes < self.rss_bytes:
            raise ContractError("INVALID_RESOURCE_SAMPLE", "peak_rss_bytes < rss_bytes")


class CooperativeStop(RuntimeError):
    def __init__(self, reason: str):
        self.reason = _text(reason, "stop.reason")
        super().__init__(reason)


@dataclass
class StopToken:
    """First stop reason is retained; cooperative checkpoints do not impose OS limits."""

    reason: str | None = None

    def request_stop(self, reason: str = "STOP_REQUESTED") -> None:
        _text(reason, "stop.reason")
        if self.reason is None:
            self.reason = reason

    def raise_if_requested(self) -> None:
        if self.reason is not None:
            raise CooperativeStop(self.reason)


@dataclass
class ExecutionHooks:
    """Synchronous callback; all exceptions propagate, including fault injection."""

    checkpoint: Callable[[str, Mapping[str, Any]], None] | None = None
    stop_token: StopToken = field(default_factory=StopToken)

    def __call__(self, stage: str, context: Mapping[str, Any] | None = None) -> None:
        if stage not in HOOK_STAGES:
            raise ContractError("UNKNOWN_HOOK_STAGE", stage)
        self.stop_token.raise_if_requested()
        if self.checkpoint is not None:
            self.checkpoint(stage, {} if context is None else context)
        self.stop_token.raise_if_requested()
