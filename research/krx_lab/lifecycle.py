"""Append-only synthetic lifecycle evidence; real transitions and holdout stay locked.

The caller must hold the experiment lock across each mutation. Numbered snapshots
are atomically published without replacement and hash chained. This detects
accidental corruption, not an attacker rewriting the entire local history.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from typing import Any, Mapping
from uuid import uuid4

from .contracts import ContractError, validate_lifecycle_evidence, validate_ledger
from .selection import select_candidate


_ROLES = ("code", "data", "cost_profile", "validation", "growth_policy", "selection_policy")


def _bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _hash(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _json(path: Path) -> dict:
    try:
        result = json.loads(path.read_bytes())
        if not isinstance(result, dict):
            raise ValueError()
        _bytes(result)
        return result
    except (ValueError, UnicodeError, OSError):
        raise ContractError("INVALID_ARTIFACT_JSON", str(path)) from None


def _path(root: Path, name: str) -> Path:
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or PurePosixPath(name).is_absolute() or any(p in {"", ".", ".."} for p in name.split("/"))):
        raise ContractError("UNSAFE_ARTIFACT_PATH", str(name))
    result = (root / name).resolve()
    if not result.is_relative_to(root.resolve()) or not result.is_file():
        raise ContractError("ARTIFACT_MISSING_OR_UNSAFE", name)
    return result


def _file_hash(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        raise ContractError("ARTIFACT_MISSING_OR_UNSAFE", str(path)) from None


def _verify(evidence: dict) -> None:
    root = Path(evidence["artifact_root"])
    for role, artifact in evidence["artifacts"].items():
        path = _path(root, artifact["file"])
        if _file_hash(path) != artifact["sha256"]:
            raise ContractError("ARTIFACT_HASH_MISMATCH", role)
    if evidence.get("final_result"):
        item = evidence["final_result"]
        if _file_hash(Path(item["file"])) != item["sha256"]:
            raise ContractError("ARTIFACT_HASH_MISMATCH", "final_result")
        final = _json(Path(item["file"]))
        for artifact in final["ledger"]["files"]:
            if _file_hash(_path(Path(item["file"]).parent, artifact["file"])) != artifact["sha256"]:
                raise ContractError("ARTIFACT_HASH_MISMATCH", artifact["file"])


def _load(directory: str | Path) -> tuple[dict, list[dict]]:
    files = sorted(Path(directory).glob("[0-9]*.json"))
    if not files:
        raise ContractError("LIFECYCLE_NOT_INITIALIZED")
    previous = None
    events = []
    for number, path in enumerate(files):
        event = _json(path)
        digest = event.pop("sha256", None)
        if (path.name != f"{number:08d}.json" or event.get("sequence") != number
                or event.get("previous_sha256") != previous or _hash(event) != digest):
            raise ContractError("LIFECYCLE_HISTORY_CORRUPT", path.name)
        event["sha256"] = digest
        validate_lifecycle_evidence(event["evidence"])
        previous = digest
        events.append(event)
    return deepcopy(events[-1]["evidence"]), events


def read_lifecycle(directory: str | Path, *, verify_artifacts: bool = True) -> dict:
    """Inspect persisted evidence; disabling byte checks never grants execution."""
    evidence, _ = _load(directory)
    if verify_artifacts:
        _verify(evidence)
    return evidence


def _append(directory: str | Path, evidence: dict, events: list[dict], request: dict) -> dict:
    validate_lifecycle_evidence(evidence)
    event = {"sequence": len(events), "previous_sha256": events[-1]["sha256"] if events else None,
             "request": request, "evidence": evidence}
    event["sha256"] = _hash(event)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / f".{uuid4().hex}.tmp"
    target = directory / f"{len(events):08d}.json"
    try:
        with temporary.open("xb") as handle:
            handle.write(_bytes(event))
            handle.flush()
            os.fsync(handle.fileno())
        # Hard-link publication fails if another writer already published this seq.
        os.link(temporary, target)
    except FileExistsError:
        raise ContractError("LIFECYCLE_CONCURRENT_WRITE") from None
    finally:
        temporary.unlink(missing_ok=True)
    return deepcopy(evidence)


def _attempt(evidence: dict, request: dict, status: str, reason: str, *, conflict: bool = False) -> None:
    evidence["attempts"].append({"attempt_id": uuid4().hex if conflict else request["attempt_id"],
                                 "request_attempt_id": request["attempt_id"],
                                 "at": datetime.now(timezone.utc).isoformat(), "action": request["action"],
                                 "status": status, "reason": reason})


def _request(action: str, attempt_id: str, **parameters) -> dict:
    if not isinstance(attempt_id, str) or not attempt_id.strip():
        raise ContractError("INVALID_ATTEMPT_ID")
    return deepcopy({"action": action, "attempt_id": attempt_id, **parameters})


def _retry(directory, evidence, events, request) -> bool:
    for event in events:
        prior = event["request"]
        if prior["attempt_id"] != request["attempt_id"]:
            continue
        if prior != request:
            _attempt(evidence, request, "DENIED", "ATTEMPT_ID_CONFLICT", conflict=True)
            _append(directory, evidence, events, request)
            raise ContractError("ATTEMPT_ID_CONFLICT")
        attempt = event["evidence"]["attempts"][-1]
        if attempt["status"] == "DENIED" and request["action"] != "holdout_access":
            raise ContractError(attempt["reason"])
        if request["action"] != "holdout_access":
            _verify(evidence)
        return True
    return False


def initialize_lifecycle(directory: str | Path, evidence: Mapping, *, artifact_root: str | Path,
                         artifacts: Mapping[str, str], attempt_id: str = "initialize") -> dict:
    """Bind six actual artifact files to a clean C3 synthetic DRAFT evidence."""
    checked = validate_lifecycle_evidence(evidence)
    if checked["source_kind"] != "SYNTHETIC":
        raise ContractError("REAL_LIFECYCLE_DISABLED")
    if checked["state"] != "DRAFT" or checked["candidate_id"] is not None or checked["attempts"] or checked["holdout_access"]:
        raise ContractError("CLEAN_DRAFT_REQUIRED")
    root = Path(artifact_root).resolve()
    request = _request("initialize", attempt_id, evidence=checked, artifact_root=str(root), artifacts=dict(artifacts))
    if list(Path(directory).glob("[0-9]*.json")):
        current, events = _load(directory)
        if _retry(directory, current, events, request):
            return current
        _attempt(current, request, "DENIED", "LIFECYCLE_ALREADY_INITIALIZED")
        _append(directory, current, events, request)
        raise ContractError("LIFECYCLE_ALREADY_INITIALIZED")
    if set(artifacts) != set(_ROLES):
        raise ContractError("REQUIRED_ARTIFACTS_MISSING", ",".join(_ROLES))
    bindings = {}
    for role in _ROLES:
        path = _path(root, artifacts[role])
        digest = _file_hash(path)
        if role in _ROLES[:4] and checked[f"{role}_hash"] != digest:
            raise ContractError("ARTIFACT_HASH_MISMATCH", role)
        if role != "code":
            payload = _json(path)
            if payload.get("source_kind") != "SYNTHETIC":
                raise ContractError("SYNTHETIC_ARTIFACT_REQUIRED", role)
            if role in ("growth_policy", "selection_policy") and payload.get("policy") != checked[role]:
                raise ContractError("POLICY_MISMATCH", role)
        bindings[role] = {"file": artifacts[role], "sha256": digest}
    checked.update(artifact_root=str(root), artifacts=bindings)
    checked["prerequisites"]["candidate_policy_frozen"] = False
    _attempt(checked, request, "SUCCEEDED", "SYNTHETIC_DRAFT_CREATED")
    return _append(directory, checked, [], request)


def _mutate(directory, request, operation) -> dict:
    evidence, events = _load(directory)
    if _retry(directory, evidence, events, request):
        return evidence
    original = deepcopy(evidence)
    try:
        if evidence["source_kind"] != "SYNTHETIC":
            raise ContractError("REAL_LIFECYCLE_DISABLED")
        if request["action"] != "holdout_access":
            _verify(evidence)
        operation(evidence)
        if request["action"] != "holdout_access":
            _verify(evidence)
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        reason = exc.code if isinstance(exc, ContractError) else "INVALID_LIFECYCLE_INPUT"
        _attempt(original, request, "DENIED", reason)
        _append(directory, original, events, request)
        raise ContractError(reason, str(exc)) from exc
    if request["action"] == "holdout_access":
        _attempt(evidence, request, "DENIED", "HOLDOUT_LOCKED")
    else:
        _attempt(evidence, request, "SUCCEEDED", "SYNTHETIC_ONLY")
    return _append(directory, evidence, events, request)


def freeze_lifecycle(directory: str | Path, *, attempt_id: str) -> dict:
    """Recompute selection from bound bytes and persist FROZEN or NO_SELECTION."""
    def operation(evidence):
        if evidence["state"] != "DRAFT":
            raise ContractError("INVALID_LIFECYCLE_TRANSITION")
        if evidence["selection_policy"] != "selection_policy_v1":
            raise ContractError("UNSUPPORTED_SELECTION_POLICY")
        validation = _json(_path(Path(evidence["artifact_root"]), evidence["artifacts"]["validation"]["file"]))
        records = validation.get("records")
        if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
            raise ContractError("INVALID_VALIDATION_RECORDS")
        if any(row.get("source_kind", "SYNTHETIC") != "SYNTHETIC" for row in records):
            raise ContractError("SYNTHETIC_ARTIFACT_REQUIRED")
        selection = select_candidate(records)
        evidence["selection"] = selection
        evidence["candidate_id"] = selection["selected_strategy_id"]
        evidence["state"] = "FROZEN" if evidence["candidate_id"] else "NO_SELECTION"
        evidence["prerequisites"]["candidate_policy_frozen"] = evidence["state"] == "FROZEN"
        evidence["frozen_hash"] = _hash({key: evidence[key] for key in
                                        ("experiment_id", "candidate_id", "growth_policy", "selection_policy",
                                         "artifacts", "selection")})
    return _mutate(directory, _request("freeze", attempt_id), operation)


def finalize_lifecycle(directory: str | Path, result_file: str | Path, *, attempt_id: str) -> dict:
    """Finalize only bound, explicitly verified synthetic C2 evidence after replay.

    Result JSON requires source_kind, status=SUCCEEDED, verified=true, frozen_hash,
    candidate_id, growth_policy_hash, selection_policy_hash, and a C2 ledger.
    Verification is recomputed from the ledger, not inferred from status or flags.
    """
    path = Path(result_file).resolve()
    request = _request("finalize", attempt_id, result_file=str(path),
                       result_sha256=_file_hash(path) if path.is_file() else None)
    def operation(evidence):
        if evidence["state"] != "FROZEN":
            raise ContractError("INVALID_LIFECYCLE_TRANSITION")
        result = _json(path)
        if result.get("source_kind") != "SYNTHETIC" or result.get("verified") is not True or result.get("status") != "SUCCEEDED":
            raise ContractError("VERIFIED_SYNTHETIC_RESULT_REQUIRED")
        for field in ("frozen_hash", "candidate_id"):
            if result.get(field) != evidence[field]:
                raise ContractError("FROZEN_BINDING_MISMATCH", field)
        for role in ("growth_policy", "selection_policy"):
            if result.get(f"{role}_hash") != evidence["artifacts"][role]["sha256"]:
                raise ContractError("FROZEN_BINDING_MISMATCH", role)
        ledger = validate_ledger(result["ledger"])
        data = _json(_path(Path(evidence["artifact_root"]), evidence["artifacts"]["data"]["file"]))
        for key in ("dataset_id", "revision"):
            if not isinstance(data.get(key), str) or not data[key] or ledger[key] != data[key]:
                raise ContractError("LEDGER_DATA_BINDING_MISMATCH", key)
        if ledger.get("strategy_id") != evidence["candidate_id"] or ledger.get("growth_policy") != evidence["growth_policy"]:
            raise ContractError("LEDGER_STRATEGY_BINDING_MISMATCH")
        execution = result.get("execution_manifest", {})
        if execution.get("run_id") != ledger["run_id"] or execution.get("ledger_hash") != _hash(ledger):
            raise ContractError("LEDGER_EXECUTION_BINDING_MISMATCH")
        for key in ("code_hash", "data_hash", "cost_profile_hash"):
            if execution.get(key) != evidence[key]:
                raise ContractError("LEDGER_EXECUTION_BINDING_MISMATCH", key)
        if ledger["source_kind"] != "SYNTHETIC" or ledger["issues"] or not ledger["equity"]:
            raise ContractError("VERIFIED_SYNTHETIC_RESULT_REQUIRED")
        if any(row["date"] >= "2024-01-01" for section in ("orders", "fills", "events", "cashflows", "positions", "equity")
               for row in ledger[section]):
            raise ContractError("HOLDOUT_LOCKED")
        for artifact in ledger["files"]:
            if _file_hash(_path(path.parent, artifact["file"])) != artifact["sha256"]:
                raise ContractError("ARTIFACT_HASH_MISMATCH", artifact["file"])
        from .vectorbt_check import reconcile_ledger
        verification = reconcile_ledger(ledger)
        if not verification["ok"]:
            raise ContractError("SYNTHETIC_REPLAY_FAILED", str(verification["mismatches"]))
        if _file_hash(path) != request["result_sha256"]:
            raise ContractError("ARTIFACT_HASH_MISMATCH", "final_result")
        evidence["state"] = "FINALIZED"
        evidence["final_result"] = {"file": str(path), "sha256": request["result_sha256"], "verification": verification}
    return _mutate(directory, request, operation)


def fail_lifecycle(directory: str | Path, *, attempt_id: str, reason: str) -> dict:
    """Record failure without clearing or replacing the frozen candidate."""
    def operation(evidence):
        if not isinstance(reason, str) or not reason.strip():
            raise ContractError("INVALID_FAILURE_REASON")
        if evidence["state"] not in {"DRAFT", "FROZEN", "FAILED"}:
            raise ContractError("INVALID_LIFECYCLE_TRANSITION")
        evidence["state"] = "FAILED"
        evidence["failure_reason"] = reason
    return _mutate(directory, _request("fail", attempt_id, reason=reason), operation)


def record_holdout_access(directory: str | Path, *, attempt_id: str, action: str = "holdout") -> dict:
    """Append a denial; this API never opens or returns any holdout price data."""
    def operation(evidence):
        if not isinstance(action, str) or not action.strip():
            raise ContractError("INVALID_ACCESS_ACTION")
        evidence["holdout_access"].append({"at": datetime.now(timezone.utc).isoformat(), "action": action,
                                            "allowed": False, "reason": "HOLDOUT_LOCKED"})
    return _mutate(directory, _request("holdout_access", attempt_id, access_action=action), operation)
