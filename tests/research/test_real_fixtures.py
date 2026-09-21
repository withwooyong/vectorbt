"""The REAL-shaped specimen verifies inspection boundaries, not market returns."""

import pytest

from research.krx_lab.admission import inspect_delivery
from research.krx_lab.contracts import validate_delivery
from research.krx_lab.io import digest, read_json
from tests.research.real_fixtures import create_real_shaped_input


def test_real_shaped_fixture_is_deterministic_and_blocked(tmp_path):
    first = create_real_shaped_input(tmp_path / "first")
    second = create_real_shaped_input(tmp_path / "second")
    assert digest(first) == digest(second)
    assert digest(first.parent / "source.json") == digest(second.parent / "source.json")

    delivery = read_json(first)
    validated = validate_delivery(delivery)
    assert validated["source_kind"] == "REAL"
    assert validated["metadata"]["real_data_admitted"] is False
    assert validated["metadata"]["end"] < "2024-01-01"
    assert all(row["historical_capture"] == "unavailable" for row in validated["sources"])
    assert all(row["adjusted_close"] == row["close"] * row["price_factor"]
               for row in validated["prices"])

    inspection = inspect_delivery(delivery, first.parent)
    assert inspection["grade"] == "BLOCKED"
    assert inspection["admission"] == "INSPECTION_ONLY"
    assert "REAL_EXECUTION_NOT_ADMITTED" in inspection["limitations"]
    assert "SOURCE_TIME_UNRESOLVED" in {issue["code"] for issue in inspection["issues"]}

    with pytest.raises(FileExistsError):
        create_real_shaped_input(first.parent)
