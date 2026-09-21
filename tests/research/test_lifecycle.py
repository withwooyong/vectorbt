from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.krx_lab.contracts import ContractError, validate_lifecycle_evidence
from research.krx_lab.lifecycle import (fail_lifecycle, finalize_lifecycle, freeze_lifecycle, initialize_lifecycle,
                                      read_lifecycle, record_holdout_access)
from tests.research.test_selection import _records


FIXTURES = Path(__file__).parent / "fixtures" / "contracts_v1"


def _write(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _setup(tmp_path, records=None):
    root = tmp_path / "artifacts"
    root.mkdir()
    evidence = json.loads((FIXTURES / "lifecycle.json").read_text())
    artifacts = {}
    for role in ("code", "data", "cost_profile", "validation", "growth_policy", "selection_policy"):
        payload = {"source_kind": "SYNTHETIC"}
        if role == "data":
            payload.update(dataset_id="synthetic-contract-fixture", revision="1")
        if role == "validation":
            payload["records"] = _records("safe") if records is None else records
        if role in ("growth_policy", "selection_policy"):
            payload["policy"] = evidence[role]
        artifacts[role] = f"{role}.json"
        digest = _write(root / artifacts[role], payload)
        if role in ("code", "data", "cost_profile", "validation"):
            evidence[f"{role}_hash"] = digest
    directory = tmp_path / "lifecycle"
    initialize_lifecycle(directory, evidence, artifact_root=root, artifacts=artifacts)
    return directory, root, evidence, artifacts


def _result(directory, root):
    frozen = read_lifecycle(directory)
    result = {"source_kind": "SYNTHETIC", "status": "SUCCEEDED", "verified": True,
              "frozen_hash": frozen["frozen_hash"], "candidate_id": frozen["candidate_id"],
              "growth_policy_hash": frozen["artifacts"]["growth_policy"]["sha256"],
              "selection_policy_hash": frozen["artifacts"]["selection_policy"]["sha256"],
              "ledger": json.loads((FIXTURES / "expected-ledger.json").read_text())}
    result["ledger"].update(strategy_id=frozen["candidate_id"], growth_policy=frozen["growth_policy"])
    from research.krx_lab.io import canonical_hash
    result["execution_manifest"] = {"run_id": result["ledger"]["run_id"], "ledger_hash": canonical_hash(result["ledger"]),
                                    **{key: frozen[key] for key in ("code_hash", "data_hash", "cost_profile_hash")}}
    path = root / "result.json"
    _write(path, result)
    return path, result


def test_freeze_is_persisted_and_exact_retries_do_not_append(tmp_path):
    directory, root, evidence, artifacts = _setup(tmp_path)
    before = (directory / "00000000.json").read_bytes()
    initialize_lifecycle(directory, evidence, artifact_root=root, artifacts=artifacts)
    assert len(list(directory.glob("*.json"))) == 1
    frozen = freeze_lifecycle(directory, attempt_id="freeze")
    assert frozen["state"] == "FROZEN"
    assert frozen["candidate_id"] == "safe"
    assert frozen["prerequisites"]["candidate_policy_frozen"] is True
    assert frozen["prerequisites"]["data_verified"] is False
    assert freeze_lifecycle(directory, attempt_id="freeze") == frozen
    assert (directory / "00000000.json").read_bytes() == before
    assert len(list(directory.glob("*.json"))) == 2
    validate_lifecycle_evidence(frozen)


def test_verified_synthetic_finalize_replays_actual_result(tmp_path):
    directory, root, _, _ = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    path, _ = _result(directory, root)
    result = finalize_lifecycle(directory, path, attempt_id="finalize")
    assert result["state"] == "FINALIZED"
    assert result["final_result"]["verification"]["engine"] == "independent_contract_replay"
    assert result["final_result"]["verification"]["eod_checked"] > 0
    assert finalize_lifecycle(directory, path, attempt_id="finalize") == result
    with pytest.raises(ContractError, match="INVALID_LIFECYCLE_TRANSITION"):
        fail_lifecycle(directory, attempt_id="late-failure", reason="new")
    assert read_lifecycle(directory)["state"] == "FINALIZED"


@pytest.mark.parametrize("field,value", [("verified", False), ("status", "FAILED"), ("source_kind", "REAL"),
                                          ("candidate_id", "runner-up"), ("frozen_hash", "0" * 64),
                                          ("growth_policy_hash", "0" * 64), ("selection_policy_hash", "0" * 64)])
def test_finalize_rejects_missing_verification_or_changed_bindings(tmp_path, field, value):
    directory, root, _, _ = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    path, result = _result(directory, root)
    result[field] = value
    _write(path, result)
    with pytest.raises(ContractError):
        finalize_lifecycle(directory, path, attempt_id="bad")
    persisted = read_lifecycle(directory)
    assert persisted["state"] == "FROZEN"
    assert persisted["attempts"][-1]["status"] == "DENIED"


def test_verified_flag_cannot_hide_bad_ledger_or_real_holdout(tmp_path):
    directory, root, _, _ = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    path, result = _result(directory, root)
    result["ledger"]["initial_cash"] += 1
    from research.krx_lab.io import canonical_hash
    result["execution_manifest"]["ledger_hash"] = canonical_hash(result["ledger"])
    _write(path, result)
    with pytest.raises(ContractError, match="SYNTHETIC_REPLAY_FAILED"):
        finalize_lifecycle(directory, path, attempt_id="bad-ledger")
    result["ledger"]["initial_cash"] -= 1
    for section in ("orders", "fills", "events", "cashflows", "positions", "equity"):
        for row in result["ledger"][section]:
            row["date"] = "2024-01-02"
    _write(path, result)
    with pytest.raises(ContractError):
        finalize_lifecycle(directory, path, attempt_id="holdout-ledger")
    assert read_lifecycle(directory)["state"] == "FROZEN"


def test_failed_candidate_cannot_be_replaced_and_failures_remain_auditable(tmp_path):
    directory, root, evidence, artifacts = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    fail_lifecycle(directory, attempt_id="failure", reason="synthetic check failed")
    failed = fail_lifecycle(directory, attempt_id="retry-failure", reason="still failed")
    assert failed["state"] == "FAILED"
    assert failed["candidate_id"] == "safe"
    with pytest.raises(ContractError, match="INVALID_LIFECYCLE_TRANSITION"):
        freeze_lifecycle(directory, attempt_id="second-place")
    with pytest.raises(ContractError, match="LIFECYCLE_ALREADY_INITIALIZED"):
        initialize_lifecycle(directory, evidence, artifact_root=root, artifacts=artifacts, attempt_id="replace")
    path, _ = _result(directory, root)
    with pytest.raises(ContractError, match="INVALID_LIFECYCLE_TRANSITION"):
        finalize_lifecycle(directory, path, attempt_id="rescue")
    assert read_lifecycle(directory)["candidate_id"] == "safe"


def test_no_selection_is_terminal(tmp_path):
    directory, _, _, _ = _setup(tmp_path, [])
    result = freeze_lifecycle(directory, attempt_id="freeze")
    assert result["state"] == "NO_SELECTION" and result["candidate_id"] is None
    with pytest.raises(ContractError, match="INVALID_LIFECYCLE_TRANSITION"):
        freeze_lifecycle(directory, attempt_id="new-candidate")
    with pytest.raises(ContractError, match="INVALID_LIFECYCLE_TRANSITION"):
        fail_lifecycle(directory, attempt_id="fail", reason="retry")


@pytest.mark.parametrize("role", ["code", "data", "cost_profile", "validation", "growth_policy", "selection_policy"])
def test_bound_byte_change_blocks_freeze_and_appends_denial(tmp_path, role):
    directory, root, _, artifacts = _setup(tmp_path)
    with (root / artifacts[role]).open("a") as stream:
        stream.write(" ")
    with pytest.raises(ContractError, match="ARTIFACT_HASH_MISMATCH"):
        freeze_lifecycle(directory, attempt_id="freeze")
    with pytest.raises(ContractError, match="ARTIFACT_HASH_MISMATCH"):
        read_lifecycle(directory)
    inspection = read_lifecycle(directory, verify_artifacts=False)
    assert inspection["state"] == "DRAFT"
    assert inspection["attempts"][-1]["reason"] == "ARTIFACT_HASH_MISMATCH"


def test_attempt_id_reuse_rejects_changed_payload(tmp_path):
    directory, _, _, _ = _setup(tmp_path)
    fail_lifecycle(directory, attempt_id="fail", reason="original")
    with pytest.raises(ContractError, match="ATTEMPT_ID_CONFLICT"):
        fail_lifecycle(directory, attempt_id="fail", reason="changed")
    result = read_lifecycle(directory)
    assert result["failure_reason"] == "original"
    assert result["attempts"][-1]["reason"] == "ATTEMPT_ID_CONFLICT"
    assert len({row["attempt_id"] for row in result["attempts"]}) == len(result["attempts"])


def test_flags_never_authorize_real_data_or_holdout(tmp_path):
    directory, root, evidence, artifacts = _setup(tmp_path)
    evidence["source_kind"] = "REAL"
    evidence["prerequisites"] = {key: True for key in evidence["prerequisites"]}
    validate_lifecycle_evidence(evidence)  # shape inspection remains supported
    with pytest.raises(ContractError, match="REAL_LIFECYCLE_DISABLED"):
        initialize_lifecycle(tmp_path / "real", evidence, artifact_root=root, artifacts=artifacts)
    freeze_lifecycle(directory, attempt_id="freeze")
    result = record_holdout_access(directory, attempt_id="access")
    assert result["holdout_access"][-1]["allowed"] is False
    assert result["holdout_access"][-1]["reason"] == "HOLDOUT_LOCKED"
    assert record_holdout_access(directory, attempt_id="access") == result


def test_history_tampering_is_detected(tmp_path):
    directory, _, _, _ = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    path = directory / "00000001.json"
    event = json.loads(path.read_text())
    event["evidence"]["candidate_id"] = "replacement"
    _write(path, event)
    with pytest.raises(ContractError, match="LIFECYCLE_HISTORY_CORRUPT"):
        read_lifecycle(directory)


def test_final_artifact_tampering_and_changed_retry_are_rejected(tmp_path):
    directory, root, _, _ = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    path, result = _result(directory, root)
    finalize_lifecycle(directory, path, attempt_id="finalize")
    result["candidate_id"] = "replacement"
    _write(path, result)
    with pytest.raises(ContractError, match="ARTIFACT_HASH_MISMATCH"):
        read_lifecycle(directory)
    with pytest.raises(ContractError, match="ATTEMPT_ID_CONFLICT"):
        finalize_lifecycle(directory, path, attempt_id="finalize")


def test_missing_or_traversing_artifacts_rejected(tmp_path):
    _, root, evidence, artifacts = _setup(tmp_path)
    artifacts["code"] = "../elsewhere.json"
    with pytest.raises(ContractError, match="UNSAFE_ARTIFACT_PATH"):
        initialize_lifecycle(tmp_path / "other", evidence, artifact_root=root, artifacts=artifacts)


def test_holdout_denial_is_logged_even_when_bound_artifact_is_missing(tmp_path):
    directory, root, _, artifacts = _setup(tmp_path)
    (root / artifacts["data"]).unlink()
    result = record_holdout_access(directory, attempt_id="locked")
    assert result["holdout_access"][-1]["allowed"] is False
    assert result["attempts"][-1]["status"] == "DENIED"
    assert record_holdout_access(directory, attempt_id="locked") == result


def test_failed_exact_retry_does_not_append_another_failure(tmp_path):
    directory, _, _, _ = _setup(tmp_path, [])
    freeze_lifecycle(directory, attempt_id="no-selection")
    for _ in range(2):
        with pytest.raises(ContractError, match="INVALID_LIFECYCLE_TRANSITION"):
            freeze_lifecycle(directory, attempt_id="denied")
    assert len(read_lifecycle(directory)["attempts"]) == 3


@pytest.mark.parametrize("field,value", [("dataset_id", "other-data"), ("revision", "other-revision"),
                                          ("strategy_id", "runner-up"), ("growth_policy", "other-policy")])
def test_finalize_rejects_foreign_ledger_even_with_fresh_hash(tmp_path, field, value):
    from research.krx_lab.io import canonical_hash
    directory, root, _, _ = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    path, result = _result(directory, root)
    result["ledger"][field] = value
    result["execution_manifest"]["ledger_hash"] = canonical_hash(result["ledger"])
    _write(path, result)
    with pytest.raises(ContractError, match="BINDING_MISMATCH"):
        finalize_lifecycle(directory, path, attempt_id="foreign")


def test_finalized_sidecar_bytes_are_rechecked_on_read_and_exact_retry(tmp_path):
    from research.krx_lab.io import canonical_hash
    directory, root, _, _ = _setup(tmp_path)
    freeze_lifecycle(directory, attempt_id="freeze")
    path, result = _result(directory, root)
    sidecar = root / "sidecar.json"
    file_hash = _write(sidecar, {"evidence": "original"})
    result["ledger"]["files"] = [{"file": sidecar.name, "sha256": file_hash, "rows": 1, "schema": "synthetic"}]
    result["execution_manifest"]["ledger_hash"] = canonical_hash(result["ledger"])
    _write(path, result)
    finalize_lifecycle(directory, path, attempt_id="finalize")
    _write(sidecar, {"evidence": "changed"})
    with pytest.raises(ContractError, match="ARTIFACT_HASH_MISMATCH"):
        read_lifecycle(directory)
    with pytest.raises(ContractError, match="ARTIFACT_HASH_MISMATCH"):
        finalize_lifecycle(directory, path, attempt_id="finalize")
