"""실자료 접근 없이 합성 기간으로 후속 33슬롯의 구조만 계획한다."""

from collections.abc import Mapping
from datetime import date

from .config import ENTRIES, EXITS


_PERIODS = ("development", "validation_2020", "validation_2021", "validation_2022",
            "validation_2023", "holdout")
_POLICIES = ("fixed20", "staged10_15_20")


def _validate_windows(windows):
    if not isinstance(windows, Mapping) or set(windows) != set(_PERIODS):
        raise ValueError("windows must contain exactly the six synthetic periods")
    previous_end = None
    normalized = {}
    for period in _PERIODS:
        bounds = windows[period]
        if not isinstance(bounds, (list, tuple)) or len(bounds) != 2:
            raise ValueError(f"{period}: expected [start, end] ISO dates")
        parsed = []
        for value in bounds:
            if not isinstance(value, str):
                raise ValueError(f"{period}: dates must be YYYY-MM-DD strings")
            try:
                day = date.fromisoformat(value)
            except ValueError as exc:
                raise ValueError(f"{period}: invalid ISO date") from exc
            if day.isoformat() != value:
                raise ValueError(f"{period}: dates must be YYYY-MM-DD strings")
            if day >= date(2024, 1, 1):
                raise ValueError(f"{period}: synthetic dates must be before 2024")
            parsed.append(day)
        start, end = parsed
        if start > end:
            raise ValueError(f"{period}: window must be nonempty (start <= end)")
        if previous_end is not None and start <= previous_end:
            raise ValueError(f"{period}: windows must be strictly ordered and nonoverlapping")
        normalized[period] = (start.isoformat(), end.isoformat())
        previous_end = end
    return normalized


def build_slots(candidate_id, growth_policy, windows) -> list[dict]:
    """Return 33 deterministic specs without reading data or granting holdout access.

    ``candidate_id`` must be an ENTRIES/EXITS pair joined by ``__`` and
    ``growth_policy`` must be fixed20 or staged10_15_20. ``windows`` maps exactly
    development, validation_2020 through validation_2023, and holdout to inclusive
    [start, end] YYYY-MM-DD bounds, chronologically ordered without overlap and
    entirely before 2024. Labels describe synthetic roles, not calendar years.
    Invalid inputs raise ValueError; inputs are never mutated.

    Phase order is allocation (8), holdout (4), controls (12), realistic-costs
    (5), ambiguity (4); conditional_slot starts at zero within each phase.
    Allocation compares both policies; other candidate slots use growth_policy.
    Controls use their control name as strategy_id, with entry_id, exit_id and
    policy set to None, cost 0 for cash and 30 for buy_hold, and delay 1.
    Profile-cost slots have cost_bps=None. Every holdout-period slot carries
    requires_holdout=True (7 total), which is a requirement, never permission.
    """
    if not isinstance(candidate_id, str):
        raise ValueError("candidate_id must be an entry__exit string")
    parts = candidate_id.split("__")
    if len(parts) != 2 or parts[0] not in ENTRIES or parts[1] not in EXITS:
        raise ValueError("candidate_id must pair an existing ENTRIES and EXITS identifier")
    if growth_policy not in _POLICIES:
        raise ValueError("growth_policy must be fixed20 or staged10_15_20")
    periods = _validate_windows(windows)
    entry_id, exit_id = parts
    slots = []
    phase_counts = {}

    def append(phase, period, cost_bps=30, delay=1, policy=growth_policy, optimistic=False, control=None):
        ordinal = phase_counts.get(phase, 0)
        start, end = periods[period]
        slots.append({
            "phase": phase, "conditional_slot": ordinal,
            "strategy_id": candidate_id if control is None else control,
            "entry_id": entry_id if control is None else None,
            "exit_id": exit_id if control is None else None,
            "policy": policy if control is None else None,
            "period": period, "start": start, "end": end,
            "cost_bps": cost_bps, "delay": delay, "optimistic": optimistic,
            "control": control, "requires_holdout": period == "holdout",
        })
        phase_counts[phase] = ordinal + 1

    for policy in _POLICIES:
        for period in _PERIODS[1:5]:
            append("allocation", period, policy=policy)
    for cost, delay in ((10, 1), (30, 1), (50, 1), (30, 2)):
        append("holdout", "holdout", cost_bps=cost, delay=delay)
    for control in ("cash", "buy_hold"):
        for period in _PERIODS:
            append("controls", period, cost_bps=0 if control == "cash" else 30, control=control)
    for period in _PERIODS[1:]:
        append("realistic-costs", period, cost_bps=None)
    for period in _PERIODS[1:5]:
        append("ambiguity", period, optimistic=True)
    return slots
