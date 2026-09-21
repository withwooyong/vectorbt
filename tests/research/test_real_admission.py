"""REAL evidence inventory remains blocked even with a clean C1 inspection."""

from copy import deepcopy
import json
from pathlib import Path

from research.krx_lab.real_admission import inspect_real_readiness


FIXTURES = Path(__file__).parent / "fixtures" / "contracts_v1"


def real_delivery():
    value = json.loads((FIXTURES / "delivery.json").read_text(encoding="utf-8"))
    value["source_kind"] = "REAL"
    value["sources"][0]["historical_capture"] = "original"
    return value


def codes(result):
    return {item["code"] for item in result["evidence_gaps"]}


def test_clean_c1_real_inventory_never_grants_execution():
    value = real_delivery()
    original = deepcopy(value)
    result = inspect_real_readiness(value, FIXTURES)
    assert value == original
    assert result["grade"] == "BLOCKED"
    assert result["admission"] == "INSPECTION_ONLY"
    assert result["inspection"]["issues"] == []
    assert result["historical_capture_counts"] == {"original": 1}
    assert result["section_counts"]["prices"] == len(value["prices"])
    assert {"FIXED_34_SOURCE_RECONCILIATION_UNVERIFIED", "REAL_EXECUTION_LEDGER_UNVERIFIED"} <= codes(result)
    assert result["limitations"] == ["REAL_EXECUTION_NOT_ADMITTED"]


def test_new_observation_and_unavailable_sources_are_not_historical_originals():
    for capture, expected in (("new_observation", "NEW_OBSERVATION_NOT_HISTORICAL_CAPTURE"),
                              ("unavailable", "HISTORICAL_CAPTURE_UNAVAILABLE")):
        value = real_delivery()
        value["sources"][0]["historical_capture"] = capture
        result = inspect_real_readiness(value, FIXTURES)
        assert expected in codes(result)
        assert "ORIGINAL_SOURCE_CAPTURE_ABSENT" in codes(result)
        assert result["grade"] == "BLOCKED"


def test_existing_c1_inspection_issues_are_retained(tmp_path):
    value = real_delivery()
    (tmp_path / "source.json").write_text('{"different": true}', encoding="utf-8")
    result = inspect_real_readiness(value, tmp_path)
    assert "ARTIFACT_HASH_MISMATCH" in {item["code"] for item in result["inspection"]["issues"]}
    assert "C1_INSPECTION_ISSUE" in codes(result)
    assert result["grade"] == "BLOCKED"


def test_invalid_c1_and_synthetic_inputs_do_not_raise_or_get_promoted():
    invalid = real_delivery()
    invalid["metadata"]["real_data_admitted"] = True
    result = inspect_real_readiness(invalid, FIXTURES)
    assert {"C1_SCHEMA_INVALID"} <= codes(result)
    assert result["inspection"]["issues"][0]["code"] == "SCHEMA_INVALID"
    assert result["grade"] == "BLOCKED"
    assert result["schema_valid"] is False
    assert result["dataset_id"] == invalid["metadata"]["dataset_id"]
    assert result["section_counts"] == {}
    assert result["historical_capture_counts"] == {}

    synthetic = json.loads((FIXTURES / "delivery.json").read_text(encoding="utf-8"))
    result = inspect_real_readiness(synthetic, FIXTURES)
    assert "REAL_SOURCE_REQUIRED" in codes(result)
    assert result["grade"] == "BLOCKED"
    assert result["schema_valid"] is True
