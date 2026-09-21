"""Offline Gate A/B receipt checks; no database or market-return execution."""

from copy import deepcopy

import pytest

from research.krx_lab.io import canonical_hash
from research.krx_lab.real_receipts import (
    DATA_DECISION,
    EXECUTION_DECISION,
    ReceiptError,
    create_data_admission_receipt,
    create_execution_admission_receipt,
    verify_data_admission_receipt,
    verify_execution_admission_receipt,
)


H = canonical_hash
CREATED = "2026-09-21T12:00:00+09:00"


def inputs():
    manifest = {
        "schema_version": "ted-krx-snapshot-v3",
        "dataset_id": "ted-krx-daily-2014-2023",
        "revision": "2014-2023-v3",
        "members": [
            {"name": "prices", "sha256": H("prices")},
            {"name": "issues", "sha256": H("issues")},
        ],
    }
    scope = {
        "start": "2015-01-02",
        "end": "2023-12-31",
        "markets": ["KRX"],
        "instrument_ids": ["instrument-2", "instrument-1"],
    }
    included = ["record-2", "record-1"]
    excluded = ["issue-quarantine", "issue-reject"]
    return manifest, scope, included, excluded


def gate_a(manifest=None, scope=None, included=None, excluded=None):
    defaults = inputs()
    return create_data_admission_receipt(
        manifest or defaults[0],
        scope=scope or defaults[1],
        included_record_ids=included or defaults[2],
        excluded_issue_ids=defaults[3] if excluded is None else excluded,
        checks={"lineage": "PASS", "quality": "PASS"},
        evaluator_code_hash=H("gate-a-code"),
        created_at=CREATED,
    )


def execution_bindings():
    return {
        "model_hash": H("model"),
        "cost_hash": H("cost"),
        "strategy_hash": H("strategy"),
        "code_hash": H("runner-code"),
        "oracle_hash": H("hand-oracle"),
        "ledger_hash": H("independent-ledger"),
    }


def verify_a(receipt, manifest=None, scope=None, included=None, excluded=None, code_hash=None):
    defaults = inputs()
    return verify_data_admission_receipt(
        receipt,
        manifest=manifest or defaults[0],
        scope=scope or defaults[1],
        included_record_ids=included or defaults[2],
        excluded_issue_ids=defaults[3] if excluded is None else excluded,
        evaluator_code_hash=code_hash or H("gate-a-code"),
    )


def gate_b(data_receipt, *, bindings=None):
    manifest, scope, included, excluded = inputs()
    return create_execution_admission_receipt(
        data_receipt,
        manifest=manifest,
        scope=scope,
        included_record_ids=included,
        excluded_issue_ids=excluded,
        evaluator_code_hash=H("gate-a-code"),
        bindings=bindings or execution_bindings(),
        checks={"corporate_action_oracle": "PASS", "independent_ledger": "PASS"},
        created_at=CREATED,
    )


def verify_b(receipt, data_receipt, *, manifest=None, scope=None, included=None, excluded=None, bindings=None):
    defaults = inputs()
    return verify_execution_admission_receipt(
        receipt,
        data_receipt=data_receipt,
        manifest=manifest or defaults[0],
        scope=scope or defaults[1],
        included_record_ids=included or defaults[2],
        excluded_issue_ids=defaults[3] if excluded is None else excluded,
        evaluator_code_hash=H("gate-a-code"),
        bindings=bindings or execution_bindings(),
    )


def test_gate_a_binds_manifest_revision_exact_scope_and_exclusions():
    manifest, scope, included, excluded = inputs()
    receipt = gate_a(manifest, scope, included, excluded)

    checked = verify_a(receipt, manifest, scope, reversed(included), reversed(excluded))

    assert checked["decision"] == DATA_DECISION
    assert checked["dataset_id"] == manifest["dataset_id"]
    assert checked["revision"] == manifest["revision"]
    assert checked["manifest_hash"] == H(manifest)
    assert checked["scope_hash"] == H({**scope, "instrument_ids": sorted(scope["instrument_ids"])})
    assert checked["issue_policy"] == {"REJECT": "EXCLUDE", "QUARANTINE": "EXCLUDE"}
    assert checked["included_record_ids_hash"] == H(sorted(included))
    assert checked["excluded_issue_ids_hash"] == H(sorted(excluded))


@pytest.mark.parametrize(
    ("change", "field"),
    [
        (lambda manifest, scope, included, excluded: manifest.update(revision="2014-2023-v4"), "revision"),
        (lambda manifest, scope, included, excluded: manifest["members"].append({"name": "new", "sha256": H("new")}), "manifest_hash"),
        (lambda manifest, scope, included, excluded: scope.update(end="2023-12-29"), "scope"),
        (lambda manifest, scope, included, excluded: included.append("record-3"), "included_record_ids"),
        (lambda manifest, scope, included, excluded: excluded.append("issue-new"), "excluded_issue_ids"),
    ],
)
def test_gate_a_rejects_stale_or_mismatched_current_inputs(change, field):
    receipt = gate_a()
    manifest, scope, included, excluded = inputs()
    change(manifest, scope, included, excluded)

    with pytest.raises(ReceiptError, match="DATA_BINDING_MISMATCH"):
        verify_a(receipt, manifest, scope, included, excluded)


def test_gate_a_rejects_forgery_code_drift_and_nonpassing_checks():
    receipt = gate_a()
    forged = deepcopy(receipt)
    forged["decision"] = "ADMITTED"
    with pytest.raises(ReceiptError, match="RECEIPT_HASH_MISMATCH"):
        verify_a(forged)
    with pytest.raises(ReceiptError, match="DATA_BINDING_MISMATCH"):
        verify_a(receipt, code_hash=H("changed-code"))
    manifest, scope, included, excluded = inputs()
    with pytest.raises(ReceiptError, match="ADMISSION_CHECK_NOT_PASSED"):
        create_data_admission_receipt(
            manifest,
            scope=scope,
            included_record_ids=included,
            excluded_issue_ids=excluded,
            checks={"quality": "BLOCKED"},
            evaluator_code_hash=H("gate-a-code"),
        )


def test_gate_b_binds_gate_a_and_all_execution_evidence():
    data = gate_a()
    receipt = gate_b(data)

    checked = verify_b(receipt, data)

    assert checked["decision"] == EXECUTION_DECISION
    assert checked["data_admission_hash"] == data["receipt_hash"]
    assert checked["scope_hash"] == data["scope_hash"]
    assert checked["bindings"] == execution_bindings()


@pytest.mark.parametrize("field", tuple(execution_bindings()))
def test_gate_b_rejects_every_execution_binding_drift(field):
    data = gate_a()
    receipt = gate_b(data)
    changed = execution_bindings()
    changed[field] = H("changed-" + field)

    with pytest.raises(ReceiptError, match="EXECUTION_BINDING_MISMATCH"):
        verify_b(receipt, data, bindings=changed)


def test_gate_b_rejects_stale_gate_a_scope_forgery_and_failed_oracle():
    data = gate_a()
    receipt = gate_b(data)
    manifest, scope, included, excluded = inputs()
    included.append("later-record")
    with pytest.raises(ReceiptError, match="DATA_BINDING_MISMATCH"):
        verify_b(receipt, data, included=included)

    replacement = gate_a(excluded=["different-issue"])
    with pytest.raises(ReceiptError, match="EXECUTION_BINDING_MISMATCH"):
        verify_b(receipt, replacement, excluded=["different-issue"])

    forged = deepcopy(receipt)
    forged["bindings"]["ledger_hash"] = H("forged")
    with pytest.raises(ReceiptError, match="RECEIPT_HASH_MISMATCH"):
        verify_b(forged, data)

    with pytest.raises(ReceiptError, match="ADMISSION_CHECK_NOT_PASSED"):
        create_execution_admission_receipt(
            data,
            manifest=manifest,
            scope=scope,
            included_record_ids=inputs()[2],
            excluded_issue_ids=excluded,
            evaluator_code_hash=H("gate-a-code"),
            bindings=execution_bindings(),
            checks={"oracle": "BLOCKED"},
        )


def test_receipts_reject_ambiguous_scope_duplicate_ids_and_missing_hashes():
    manifest, scope, included, excluded = inputs()
    with pytest.raises(ReceiptError, match="INVALID_SCOPE_FIELDS"):
        gate_a(scope={**scope, "selector": "all"})
    with pytest.raises(ReceiptError, match="DUPLICATE_VALUE"):
        gate_a(included=[included[0], included[0]])
    data = gate_a()
    incomplete = execution_bindings()
    incomplete.pop("oracle_hash")
    with pytest.raises(ReceiptError, match="INVALID_EXECUTION_BINDINGS"):
        gate_b(data, bindings=incomplete)
