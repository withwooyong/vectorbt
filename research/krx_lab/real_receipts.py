"""Fail-closed receipts for REAL data and execution admission.

The receipts in this module are integrity bindings, not signatures or market
evidence.  Gate A binds a conditionally admitted dataset scope to one immutable
manifest and an explicit exclusion set.  Gate B additionally binds an execution
model and its independently checked evidence to that exact Gate A receipt.

Creating or validating a receipt never reads a database and never executes a
backtest.  Callers must supply the current bindings again when validating so a
self-consistent but stale receipt cannot authorize execution.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any

from .io import canonical_hash


DATA_RECEIPT_VERSION = "krx-real-data-admission-v1"
EXECUTION_RECEIPT_VERSION = "krx-real-execution-admission-v1"
DATA_DECISION = "CONDITIONALLY_ADMITTED"
EXECUTION_DECISION = "EXECUTION_ADMITTED"
EXCLUSION_POLICY = {"REJECT": "EXCLUDE", "QUARANTINE": "EXCLUDE"}
EXECUTION_HASH_FIELDS = (
    "model_hash",
    "cost_hash",
    "strategy_hash",
    "code_hash",
    "oracle_hash",
    "ledger_hash",
)


class ReceiptError(ValueError):
    """A stable fail-closed receipt validation error."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(code + (f": {detail}" if detail else ""))


def _text(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReceiptError("INVALID_TEXT", location)
    return value


def _sha256(value: Any, location: str) -> str:
    text = _text(value, location)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ReceiptError("INVALID_SHA256", location)
    return text


def _timestamp(value: str | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc).isoformat()
    try:
        instant = datetime.fromisoformat(_text(value, "created_at").replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReceiptError("INVALID_TIMESTAMP", "created_at") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ReceiptError("TIMEZONE_REQUIRED", "created_at")
    return value


def _unique_texts(values: Iterable[str], location: str, *, allow_empty: bool = False) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise ReceiptError("INVALID_SEQUENCE", location)
    try:
        result = [_text(value, location) for value in values]
    except TypeError as exc:
        raise ReceiptError("INVALID_SEQUENCE", location) from exc
    if not result and not allow_empty:
        raise ReceiptError("EMPTY_SEQUENCE", location)
    if len(result) != len(set(result)):
        raise ReceiptError("DUPLICATE_VALUE", location)
    return sorted(result)


def _manifest_binding(manifest: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(manifest, Mapping):
        raise ReceiptError("INVALID_MANIFEST")
    dataset_id = _text(manifest.get("dataset_id"), "manifest.dataset_id")
    revision = _text(manifest.get("revision"), "manifest.revision")
    try:
        manifest_hash = canonical_hash(manifest)
    except (TypeError, ValueError) as exc:
        raise ReceiptError("NONCANONICAL_MANIFEST") from exc
    return {"dataset_id": dataset_id, "revision": revision, "manifest_hash": manifest_hash}


def _scope_binding(scope: Mapping[str, Any], included_record_ids: Iterable[str],
                   excluded_issue_ids: Iterable[str]) -> dict[str, Any]:
    if not isinstance(scope, Mapping) or set(scope) != {"start", "end", "markets", "instrument_ids"}:
        raise ReceiptError("INVALID_SCOPE_FIELDS")
    try:
        start = date.fromisoformat(_text(scope["start"], "scope.start"))
        end = date.fromisoformat(_text(scope["end"], "scope.end"))
    except ValueError as exc:
        raise ReceiptError("INVALID_SCOPE_DATE") from exc
    if start > end:
        raise ReceiptError("REVERSED_SCOPE")
    normalized_scope = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "markets": _unique_texts(scope["markets"], "scope.markets"),
        "instrument_ids": _unique_texts(scope["instrument_ids"], "scope.instrument_ids"),
    }
    included = _unique_texts(included_record_ids, "included_record_ids")
    excluded = _unique_texts(excluded_issue_ids, "excluded_issue_ids", allow_empty=True)
    return {
        "scope": normalized_scope,
        "scope_hash": canonical_hash(normalized_scope),
        "included_record_ids_hash": canonical_hash(included),
        "included_record_count": len(included),
        "excluded_issue_ids_hash": canonical_hash(excluded),
        "excluded_issue_count": len(excluded),
    }


def _passing_checks(checks: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(checks, Mapping) or not checks:
        raise ReceiptError("EMPTY_CHECKS")
    normalized = {}
    for name, result in checks.items():
        name = _text(name, "checks.name")
        if result != "PASS":
            raise ReceiptError("ADMISSION_CHECK_NOT_PASSED", name)
        normalized[name] = "PASS"
    return dict(sorted(normalized.items()))


def _seal(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = deepcopy(dict(payload))
    result["receipt_hash"] = canonical_hash(result)
    return result


def _verify_seal(receipt: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, Mapping):
        raise ReceiptError("INVALID_RECEIPT")
    value = deepcopy(dict(receipt))
    claimed = value.pop("receipt_hash", None)
    _sha256(claimed, "receipt_hash")
    if canonical_hash(value) != claimed:
        raise ReceiptError("RECEIPT_HASH_MISMATCH")
    return dict(receipt)


def create_data_admission_receipt(
    manifest: Mapping[str, Any],
    *,
    scope: Mapping[str, Any],
    included_record_ids: Iterable[str],
    excluded_issue_ids: Iterable[str],
    checks: Mapping[str, Any],
    evaluator_code_hash: str,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Create a Gate A receipt bound to one exact admitted subset.

    Both REJECT and QUARANTINE issues are excluded.  This function deliberately
    offers no waiver flag: a caller must produce a new manifest/scope when the
    issue disposition changes.
    """

    payload = {
        "schema_version": DATA_RECEIPT_VERSION,
        "decision": DATA_DECISION,
        **_manifest_binding(manifest),
        **_scope_binding(scope, included_record_ids, excluded_issue_ids),
        "issue_policy": dict(EXCLUSION_POLICY),
        "checks": _passing_checks(checks),
        "evaluator_code_hash": _sha256(evaluator_code_hash, "evaluator_code_hash"),
        "created_at": _timestamp(created_at),
    }
    return _seal(payload)


def verify_data_admission_receipt(
    receipt: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    scope: Mapping[str, Any],
    included_record_ids: Iterable[str],
    excluded_issue_ids: Iterable[str],
    evaluator_code_hash: str,
) -> dict[str, Any]:
    """Verify Gate A against current manifest, scope, issue set, and code."""

    checked = _verify_seal(receipt)
    if checked.get("schema_version") != DATA_RECEIPT_VERSION or checked.get("decision") != DATA_DECISION:
        raise ReceiptError("DATA_ADMISSION_NOT_GRANTED")
    expected = {
        **_manifest_binding(manifest),
        **_scope_binding(scope, included_record_ids, excluded_issue_ids),
        "issue_policy": dict(EXCLUSION_POLICY),
        "evaluator_code_hash": _sha256(evaluator_code_hash, "evaluator_code_hash"),
    }
    for field, value in expected.items():
        if checked.get(field) != value:
            raise ReceiptError("DATA_BINDING_MISMATCH", field)
    _timestamp(checked.get("created_at"))
    if checked.get("checks") != _passing_checks(checked.get("checks")):
        raise ReceiptError("DATA_BINDING_MISMATCH", "checks")
    return checked


def _execution_bindings(bindings: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(bindings, Mapping) or set(bindings) != set(EXECUTION_HASH_FIELDS):
        raise ReceiptError("INVALID_EXECUTION_BINDINGS")
    return {name: _sha256(bindings[name], name) for name in EXECUTION_HASH_FIELDS}


def create_execution_admission_receipt(
    data_receipt: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any],
    scope: Mapping[str, Any],
    included_record_ids: Iterable[str],
    excluded_issue_ids: Iterable[str],
    evaluator_code_hash: str,
    bindings: Mapping[str, str],
    checks: Mapping[str, Any],
    created_at: str | None = None,
) -> dict[str, Any]:
    """Create Gate B only after re-verifying the exact current Gate A inputs."""

    data = verify_data_admission_receipt(
        data_receipt,
        manifest=manifest,
        scope=scope,
        included_record_ids=included_record_ids,
        excluded_issue_ids=excluded_issue_ids,
        evaluator_code_hash=evaluator_code_hash,
    )
    payload = {
        "schema_version": EXECUTION_RECEIPT_VERSION,
        "decision": EXECUTION_DECISION,
        "dataset_id": data["dataset_id"],
        "revision": data["revision"],
        "manifest_hash": data["manifest_hash"],
        "scope_hash": data["scope_hash"],
        "data_admission_hash": data["receipt_hash"],
        "bindings": _execution_bindings(bindings),
        "checks": _passing_checks(checks),
        "created_at": _timestamp(created_at),
    }
    return _seal(payload)


def verify_execution_admission_receipt(
    receipt: Mapping[str, Any],
    *,
    data_receipt: Mapping[str, Any],
    manifest: Mapping[str, Any],
    scope: Mapping[str, Any],
    included_record_ids: Iterable[str],
    excluded_issue_ids: Iterable[str],
    evaluator_code_hash: str,
    bindings: Mapping[str, str],
) -> dict[str, Any]:
    """Verify Gate B and recursively re-verify Gate A against current inputs."""

    data = verify_data_admission_receipt(
        data_receipt,
        manifest=manifest,
        scope=scope,
        included_record_ids=included_record_ids,
        excluded_issue_ids=excluded_issue_ids,
        evaluator_code_hash=evaluator_code_hash,
    )
    checked = _verify_seal(receipt)
    if checked.get("schema_version") != EXECUTION_RECEIPT_VERSION or checked.get("decision") != EXECUTION_DECISION:
        raise ReceiptError("EXECUTION_ADMISSION_NOT_GRANTED")
    expected = {
        "dataset_id": data["dataset_id"],
        "revision": data["revision"],
        "manifest_hash": data["manifest_hash"],
        "scope_hash": data["scope_hash"],
        "data_admission_hash": data["receipt_hash"],
        "bindings": _execution_bindings(bindings),
    }
    for field, value in expected.items():
        if checked.get(field) != value:
            raise ReceiptError("EXECUTION_BINDING_MISMATCH", field)
    _timestamp(checked.get("created_at"))
    if checked.get("checks") != _passing_checks(checked.get("checks")):
        raise ReceiptError("EXECUTION_BINDING_MISMATCH", "checks")
    return checked
