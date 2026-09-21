"""후속 슬롯의 구성과 잠금 경계를 실자료 없이 독립적으로 검사한다."""

from collections import Counter
from copy import deepcopy
from datetime import date
import json
from types import MappingProxyType

import pytest

from research.krx_lab.conditional_plan import build_slots
from research.krx_lab.config import ENTRIES, EXITS


CANDIDATE = "CROSS_5_20__PCT_3_6"
PERIODS = ("development", "validation_2020", "validation_2021", "validation_2022",
           "validation_2023", "holdout")


@pytest.fixture
def windows():
    # All roles intentionally occupy 2023, including the synthetic holdout.
    return {period: [f"2023-01-{2 * i + 1:02d}", f"2023-01-{2 * i + 2:02d}"]
            for i, period in enumerate(PERIODS)}


@pytest.mark.parametrize("policy", ["fixed20", "staged10_15_20"])
def test_exact_phase_matrix_and_seven_holdout_requirements(windows, policy):
    slots = build_slots(CANDIDATE, policy, windows)
    assert len(slots) == 33
    assert Counter(row["phase"] for row in slots) == {
        "allocation": 8, "holdout": 4, "controls": 12, "realistic-costs": 5, "ambiguity": 4,
    }
    assert list(dict.fromkeys(row["phase"] for row in slots)) == [
        "allocation", "holdout", "controls", "realistic-costs", "ambiguity",
    ]
    by_phase = {phase: [row for row in slots if row["phase"] == phase]
                for phase in ("allocation", "holdout", "controls", "realistic-costs", "ambiguity")}
    for rows in by_phase.values():
        assert [row["conditional_slot"] for row in rows] == list(range(len(rows)))
    assert [(row["policy"], row["period"], row["cost_bps"], row["delay"])
            for row in by_phase["allocation"]] == [
        (allocation, period, 30, 1)
        for allocation in ("fixed20", "staged10_15_20") for period in PERIODS[1:5]
    ]
    assert [(row["cost_bps"], row["delay"]) for row in by_phase["holdout"]] == [
        (10, 1), (30, 1), (50, 1), (30, 2),
    ]
    assert [(row["control"], row["period"]) for row in by_phase["controls"]] == [
        (control, period) for control in ("cash", "buy_hold") for period in PERIODS
    ]
    assert [(row["period"], row["cost_bps"], row["delay"])
            for row in by_phase["realistic-costs"]] == [(period, None, 1) for period in PERIODS[1:]]
    assert [(row["period"], row["cost_bps"], row["delay"])
            for row in by_phase["ambiguity"]] == [(period, 30, 1) for period in PERIODS[1:5]]
    assert Counter(row["phase"] for row in slots if row["requires_holdout"]) == {
        "holdout": 4, "controls": 2, "realistic-costs": 1,
    }
    fields = {"phase", "conditional_slot", "strategy_id", "entry_id", "exit_id", "policy", "period",
              "start", "end", "cost_bps", "delay", "optimistic", "control", "requires_holdout"}
    for row in slots:
        assert set(row) == fields
        assert [row["start"], row["end"]] == windows[row["period"]]
        assert row["requires_holdout"] is (row["period"] == "holdout")
        assert row["optimistic"] is (row["phase"] == "ambiguity")
        if row["control"] is None:
            assert row["strategy_id"] == CANDIDATE
            assert (row["entry_id"], row["exit_id"]) == ("CROSS_5_20", "PCT_3_6")
            if row["phase"] != "allocation":
                assert row["policy"] == policy
        else:
            assert row["strategy_id"] == row["control"]
            assert row["entry_id"] is row["exit_id"] is row["policy"] is None
            assert row["cost_bps"] == (0 if row["control"] == "cash" else 30)
            assert row["delay"] == 1


def test_deterministic_mapping_order_independent_and_no_mutation(windows):
    before = deepcopy(windows)
    first = build_slots(CANDIDATE, "fixed20", windows)
    second = build_slots(CANDIDATE, "fixed20", MappingProxyType(dict(reversed(list(windows.items())))))
    assert json.dumps(first) == json.dumps(second)
    assert len({(row["phase"], row["conditional_slot"]) for row in first}) == 33
    first[0]["start"] = "changed"
    assert second[0]["start"] == "2023-01-03"
    assert first[1]["start"] == "2023-01-05"
    assert windows == before
    assert build_slots(CANDIDATE, "fixed20", windows) == second


@pytest.mark.parametrize("entry", ENTRIES)
@pytest.mark.parametrize("exit_id", EXITS)
def test_all_existing_candidates_are_accepted(windows, entry, exit_id):
    candidate = f"{entry}__{exit_id}"
    slots = build_slots(candidate, "fixed20", windows)
    assert all(row["strategy_id"] == candidate for row in slots if row["control"] is None)


@pytest.mark.parametrize("candidate", [None, 1, [], {}, "", "CROSS_5_20", "UNKNOWN__PCT_3_6",
                                       "CROSS_5_20__UNKNOWN", "CROSS_5_20__PCT_3_6__extra",
                                       " CROSS_5_20__PCT_3_6", "cross_5_20__PCT_3_6"])
def test_invalid_candidate(windows, candidate):
    with pytest.raises(ValueError, match="candidate_id"):
        build_slots(candidate, "fixed20", windows)


@pytest.mark.parametrize("policy", [None, 1, True, [], {}, "", "fixed10", "FIXED20"])
def test_invalid_policy(windows, policy):
    with pytest.raises(ValueError, match="growth_policy"):
        build_slots(CANDIDATE, policy, windows)


@pytest.mark.parametrize("value", [None, 20230101, True, date(2023, 1, 1), "", "2023-02-29",
                                   "2023-13-01", "2023-01-00", "0000-01-01", "20230101",
                                   "2023-W01-1", "2023-1-1", "2023-01-01T00:00:00",
                                   "2023-01-01 ", "2024-01-01", "2025-01-01"])
@pytest.mark.parametrize("bound", [0, 1])
def test_invalid_dates(windows, value, bound):
    windows["development"][bound] = value
    with pytest.raises(ValueError):
        build_slots(CANDIDATE, "fixed20", windows)


@pytest.mark.parametrize("bounds", [None, [], ["2023-01-01"], ["2023-01-01"] * 3,
                                    "2023-01-01", {"start": "2023-01-01", "end": "2023-01-02"},
                                    ["2023-01-02", "2023-01-01"]])
def test_invalid_or_empty_window(windows, bounds):
    windows["development"] = bounds
    with pytest.raises(ValueError):
        build_slots(CANDIDATE, "fixed20", windows)


@pytest.mark.parametrize("period", PERIODS[1:])
@pytest.mark.parametrize("overlap", ["equal_boundary", "earlier_window"])
def test_every_boundary_rejects_overlap_or_wrong_order(windows, period, overlap):
    previous = PERIODS[PERIODS.index(period) - 1]
    if overlap == "equal_boundary":
        windows[period][0] = windows[previous][1]
    else:
        windows[period] = ["2022-01-01", "2022-01-02"]
    with pytest.raises(ValueError, match="strictly ordered and nonoverlapping"):
        build_slots(CANDIDATE, "fixed20", windows)


@pytest.mark.parametrize("value", [None, [], {}, "windows"])
def test_invalid_windows_mapping(value):
    with pytest.raises(ValueError, match="exactly"):
        build_slots(CANDIDATE, "fixed20", value)


@pytest.mark.parametrize("period", PERIODS)
def test_all_periods_required(windows, period):
    del windows[period]
    with pytest.raises(ValueError, match="exactly"):
        build_slots(CANDIDATE, "fixed20", windows)


def test_unknown_period_rejected(windows):
    windows["unexpected"] = ["2023-02-01", "2023-02-02"]
    with pytest.raises(ValueError, match="exactly"):
        build_slots(CANDIDATE, "fixed20", windows)


def test_inclusive_single_day_leap_day_and_last_pre2024_day(windows):
    windows["development"] = ["2020-02-29", "2020-02-29"]
    windows["holdout"] = ("2023-12-31", "2023-12-31")
    slots = build_slots(CANDIDATE, "fixed20", windows)
    assert len(slots) == 33
    assert all(row["end"] == "2023-12-31" for row in slots if row["requires_holdout"])
