"""Dependency audits must not turn possible input exposure into executed trades."""

import importlib.util
from pathlib import Path

import pandas as pd
import pytest


def _module():
    path = Path(__file__).resolve().parents[2] / "scripts/research/audit_ohlcv20_factor_intake.py"
    spec = importlib.util.spec_from_file_location("factor_intake_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_effective_day_and_strict_sixty_session_boundary():
    calendar = pd.bdate_range("2020-01-01", periods=180)
    result = _module().event_window(calendar, calendar[70])
    assert result.tolist() == list(range(70, 130))
    assert 130 not in result  # event == the oldest observation is not adjusted


def test_non_session_event_uses_next_exchange_day():
    calendar = pd.bdate_range("2020-01-01", periods=180)
    saturday = pd.Timestamp("2020-04-11")
    result = _module().event_window(calendar, saturday)
    assert calendar[result[0]] == pd.Timestamp("2020-04-13")
    assert len(result) == 60


def test_warmup_and_future_event_do_not_invent_windows():
    calendar = pd.bdate_range("2020-01-01", periods=80)
    audit = _module()
    assert audit.event_window(calendar, calendar[0]).size == 0
    assert audit.event_window(calendar, calendar[-1] + pd.Timedelta(days=7)).size == 0
    assert audit.event_window(calendar, calendar[10]).tolist() == list(range(60, 70))


def test_holding_opportunities_exclude_event_day_and_keep_delayed_tail_unknown():
    result = _module().prior_opportunities(
        pd.DatetimeIndex(["2019-01-02", "2020-02-01", "2020-03-01", "2020-04-01", "2020-04-02"]),
        pd.Timestamp("2020-04-01"),
    )
    assert result["prior_order_eligible_days_all"] == 3
    assert result["prior_order_eligible_days_1_calendar_month"] == 1
    assert result["prior_order_eligible_days_3_calendar_months"] == 2
    assert result["actual_held_at_event"] is None
    assert result["delayed_exit_tail"] == "NOT_BOUNDED_BY_THREE_MONTHS"


def test_existing_outputs_are_preserved(tmp_path):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        _module().audit(tmp_path / "missing-input", tmp_path)
    assert marker.read_text(encoding="utf-8") == "keep"


@pytest.mark.parametrize("field", ["corrected_manifest_sha256", "base_manifest_sha256", "evaluation_start", "evaluation_end"])
def test_equal_counts_cannot_hide_changed_input_identity_or_period(field):
    receipt = {
        "corrected_manifest_sha256": "a" * 64,
        "base_manifest_sha256": "b" * 64,
        "evaluation_start": "2015-06-15",
        "evaluation_end": "2023-12-31",
    }
    module = _module()
    module.verify_eligibility_receipt(receipt, "a" * 64, "b" * 64)
    receipt[field] = "changed"
    with pytest.raises(ValueError, match="ELIGIBILITY_RECEIPT_BINDING_MISMATCH"):
        module.verify_eligibility_receipt(receipt, "a" * 64, "b" * 64)
