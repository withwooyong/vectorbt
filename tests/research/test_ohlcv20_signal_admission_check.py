from __future__ import annotations

import json
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from research.krx_lab.ohlcv20_signal_admission_check import (
    Candidates,
    _suffix,
    _uncovered_blocked,
    build_reconciliation,
    compute_admission,
    load_uncovered_events,
)


def _candidates(rows: list[dict]) -> Candidates:
    frame = pd.DataFrame(rows)
    frame["date"] = pd.to_datetime(frame["date"])
    return Candidates(frame.sort_values(["code", "date"], ignore_index=True), sha256="test")


def test_suffix_blocks_everything_before_an_unadmitted_event() -> None:
    events = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-10", "2020-02-10"]),
            "price_admitted": [True, False],
            "price_factor": [Decimal("2"), None],
        }
    )
    blocked, product = _suffix(events, "price")
    # slot 0 covers bars before the first event: both events are ahead, one is
    # unadmitted, so slot 0 must be blocked.
    assert blocked[0] is np.True_
    # slot 1 covers bars between the two events: only the unadmitted event is
    # ahead, so slot 1 must be blocked too.
    assert blocked[1] is np.True_
    # slot 2 covers bars after the last event: nothing is ahead, so it is open.
    assert blocked[2] is np.False_
    assert product[2] == pytest.approx(1.0)


def test_suffix_open_when_all_admitted() -> None:
    events = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-10", "2020-02-10"]),
            "price_admitted": [True, True],
            "price_factor": [Decimal("2"), Decimal("3")],
        }
    )
    blocked, product = _suffix(events, "price")
    assert not blocked[0]
    assert product[0] == pytest.approx(6.0)
    assert product[1] == pytest.approx(3.0)


def test_uncovered_blocked_true_only_when_event_is_strictly_after_bar() -> None:
    dates = np.array(["2020-02-10"], dtype="datetime64[ns]")
    bar_dates = np.array(["2020-01-01", "2020-02-10", "2020-03-01"], dtype="datetime64[ns]")
    blocked = _uncovered_blocked(dates, bar_dates)
    # 2020-01-01 precedes the event -> blocked; 2020-02-10 (effective date
    # itself) is not strictly after -> not blocked; 2020-03-01 follows -> open.
    assert list(blocked) == [True, False, False]


def test_compute_admission_matches_rule_definitions() -> None:
    # One code with one candidate event (admitted for price, not for volume),
    # and one uncovered price-affecting event further in the future.
    bars = pd.DataFrame(
        {
            "code": ["A", "A", "A"],
            "date": pd.to_datetime(["2020-01-01", "2020-02-15", "2020-04-01"]),
            "close": [100.0, 100.0, 100.0],
            "adjusted_close": [200.0, 200.0, 100.0],
        }
    )
    candidates = _candidates(
        [
            {
                "code": "A",
                "date": "2020-02-01",
                "price_admitted": True,
                "volume_admitted": False,
                "price_factor": Decimal("2"),
                "volume_factor": None,
            }
        ]
    )
    uncovered = pd.DataFrame({"code": ["A"], "date": pd.to_datetime(["2020-03-01"])})

    counts, out = compute_admission(bars, candidates, uncovered)

    assert counts.raw_bars_total == 3
    # Bar 0 (2020-01-01) precedes the candidate event -> R1 price passes
    # (admitted) but R1 volume fails (not admitted). The uncovered event
    # (2020-03-01) is also still ahead, so R2 blocks it.
    assert bool(out.loc[0, "r1_price_ok"]) is True
    assert bool(out.loc[0, "r1_volume_ok"]) is False
    assert bool(out.loc[0, "r2_blocked"]) is True
    # Bar 1 (2020-02-15) is after the candidate event but still before the
    # uncovered event -> R1 passes, R2 blocks it too.
    assert bool(out.loc[1, "r1_price_ok"]) is True
    assert bool(out.loc[1, "r2_blocked"]) is True
    # Bar 2 (2020-04-01) is after both events -> R1 open, R2 open, R3 expects
    # factor 1 (no admitted event ahead) and observed 100/100=1 -> matched.
    assert bool(out.loc[2, "signal_admitted_bar"]) is True
    assert counts.r1_pass_price == 3
    assert counts.r2_additional_excluded_price == 2  # bars 0 and 1
    assert counts.final_valid_bars_price == 1  # only bar 2


def test_load_uncovered_events_excludes_listed_share_change_and_covered_keys(tmp_path) -> None:
    actions = pd.DataFrame(
        {
            "stock_code": ["A", "A", "B"],
            "effective_date": ["2020-01-01", "2020-02-01", "2020-01-01"],
            "event_type": ["SPLIT", "LISTED_SHARE_CHANGE", "SPLIT"],
            "apply_event": [True, True, True],
        }
    )
    path = tmp_path / "corporate-actions.parquet"
    actions.to_parquet(path)

    candidates = _candidates(
        [
            {
                "code": "A",
                "date": "2020-01-01",
                "price_admitted": True,
                "volume_admitted": True,
                "price_factor": Decimal("1"),
                "volume_factor": Decimal("1"),
            }
        ]
    )
    uncovered = load_uncovered_events(path, candidates)
    # A/2020-01-01 is covered by the candidate set; A/2020-02-01 is
    # LISTED_SHARE_CHANGE and excluded regardless; B/2020-01-01 is a
    # price-affecting event absent from the candidate set -> uncovered.
    assert list(zip(uncovered["code"], uncovered["date"].dt.strftime("%Y-%m-%d"))) == [
        ("B", "2020-01-01")
    ]


def test_build_reconciliation_rejects_a_candidate_audit_the_provider_did_not_declare(
    tmp_path,
) -> None:
    """A stale/superseded audit (e.g. a v3 draft) must be rejected before any
    bar is read, even if a caller points --candidate-audit at it."""
    declared = pd.DataFrame(
        {
            "stock_code": ["A"],
            "effective_date": ["2020-01-01"],
            "price_admitted": [True],
            "volume_admitted": [True],
            "price_factor": [1.0],
            "volume_factor": [1.0],
        }
    )
    declared_path = tmp_path / "declared-audit.parquet"
    declared.to_parquet(declared_path)

    stale = declared.copy()
    stale.loc[0, "price_admitted"] = False
    stale_path = tmp_path / "stale-v3-audit.parquet"
    stale.to_parquet(stale_path)

    import hashlib

    provider_path = tmp_path / "signal-admission-v1.json"
    provider_path.write_text(
        json.dumps(
            {
                "factor_admission_audit_sha256": hashlib.sha256(declared_path.read_bytes()).hexdigest(),
                "bar_counts": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CANDIDATE_AUDIT_HASH_MISMATCH"):
        build_reconciliation(
            corrected_input_package=tmp_path / "does-not-need-to-exist",
            candidate_audit_path=stale_path,
            corporate_actions_path=tmp_path / "does-not-need-to-exist-either",
            provider_evidence_path=provider_path,
        )
