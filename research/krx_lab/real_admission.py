"""Read-only REAL C1 evidence inventory; this module never admits execution.

The C1 contract validates shape and local consistency. It cannot establish that
the collector supplied complete, historically available market evidence. Keep
those requirements visible even when the C1 inspection has no issues.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .admission import inspect_delivery


_OUTSIDE_C1 = (
    "FIXED_34_SOURCE_RECONCILIATION_UNVERIFIED",
    "UPSTREAM_REQUEST_AND_TRANSFORM_LINEAGE_UNVERIFIED",
    "RAW_ADJUSTED_DEFINITION_INDEPENDENTLY_UNVERIFIED",
    "CORPORATE_ACTION_COMPLETENESS_UNVERIFIED",
    "HISTORICAL_UNIVERSE_AND_STATUS_COMPLETENESS_UNVERIFIED",
    "OFFICIAL_CALENDAR_PROVENANCE_UNVERIFIED",
    "REAL_COST_AND_FILL_MODEL_UNVERIFIED",
    "REAL_EXECUTION_LEDGER_UNVERIFIED",
)


def inspect_real_readiness(delivery: Mapping, root: Path, previous: Mapping | None = None) -> dict[str, Any]:
    """Inventory REAL evidence in a C1 delivery without changing input or files.

    ``root`` is passed to :func:`inspect_delivery` for its local file checks.
    The result is always ``BLOCKED`` and ``INSPECTION_ONLY``. ``evidence_gaps``
    names missing C1 evidence and requirements that C1 cannot prove. A clean
    inventory is not an execution grant; callers must preserve existing REAL
    execution gates. No database or network access is performed.
    """
    inspection = inspect_delivery(delivery, root, previous)
    gaps: list[dict[str, str]] = []

    def gap(code: str, detail: str = "") -> None:
        gaps.append({"code": code, "detail": detail})

    if not isinstance(delivery, Mapping) or delivery.get("source_kind") != "REAL":
        gap("REAL_SOURCE_REQUIRED")

    if "SCHEMA_INVALID" in {issue["code"] for issue in inspection["issues"]}:
        gap("C1_SCHEMA_INVALID")
        metadata = delivery.get("metadata", {}) if isinstance(delivery, Mapping) else {}
        metadata = metadata if isinstance(metadata, Mapping) else {}
        return {"grade": "BLOCKED", "admission": "INSPECTION_ONLY", "schema_valid": False,
                "dataset_id": metadata.get("dataset_id"), "revision": metadata.get("revision"),
                "inspection": inspection, "section_counts": {}, "historical_capture_counts": {},
                "evidence_gaps": gaps, "limitations": ["REAL_EXECUTION_NOT_ADMITTED"]}

    for issue in inspection["issues"]:
        gap("C1_INSPECTION_ISSUE", issue["code"] + (": " + issue["detail"] if issue["detail"] else ""))

    sources = delivery["sources"]
    capture_counts = Counter(row["historical_capture"] for row in sources)
    if not sources:
        gap("SOURCE_EVIDENCE_EMPTY")
    if capture_counts["unavailable"]:
        gap("HISTORICAL_CAPTURE_UNAVAILABLE", str(capture_counts["unavailable"]))
    if capture_counts["new_observation"]:
        gap("NEW_OBSERVATION_NOT_HISTORICAL_CAPTURE", str(capture_counts["new_observation"]))
    if capture_counts["synthetic"]:
        gap("SYNTHETIC_SOURCE_IN_REAL", str(capture_counts["synthetic"]))
    if not capture_counts["original"]:
        gap("ORIGINAL_SOURCE_CAPTURE_ABSENT")

    section_counts = {name: len(delivery[name]) for name in
                      ("sources", "prices", "events", "instruments", "statuses", "calendar", "market_profiles")}
    for name in ("prices", "instruments", "statuses", "calendar", "market_profiles"):
        if not section_counts[name]:
            gap("C1_SECTION_EMPTY", name)

    for code in _OUTSIDE_C1:
        gap(code)

    return {
        "grade": "BLOCKED",
        "admission": "INSPECTION_ONLY",
        "schema_valid": True,
        "dataset_id": inspection["dataset_id"],
        "revision": inspection["revision"],
        "inspection": inspection,
        "section_counts": section_counts,
        "historical_capture_counts": dict(sorted(capture_counts.items())),
        "evidence_gaps": gaps,
        "limitations": ["REAL_EXECUTION_NOT_ADMITTED"],
    }
