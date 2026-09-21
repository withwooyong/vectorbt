"""Complete synthetic inputs for conditional-run integration tests.

Period labels represent test roles, not real validation or holdout years. All
market dates precede 2024; fabricated selection evidence proves only mechanics.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from pathlib import Path

from research.krx_lab.admission import inspect_delivery
from research.krx_lab.io import digest, read_json, source_hash, write_json
from research.krx_lab.lifecycle import freeze_lifecycle, initialize_lifecycle, read_lifecycle
from tests.research.test_selection import _records


_FIXTURES = Path(__file__).parent / "fixtures" / "contracts_v1"
_CANDIDATE = "CROSS_5_20__PCT_3_6"
_PERIODS = (
    "development", "validation_2020", "validation_2021", "validation_2022", "validation_2023", "holdout",
)


def create_inputs(root: Path) -> dict:
    """Write C1 delivery, signals, six disjoint windows, and bound FROZEN evidence.

    Use a fresh test directory. Data and policy bytes are deterministic; lifecycle
    audit timestamps are supplied by the existing lifecycle implementation.
    ``artifact_root`` contains the exact delivery bound as the data artifact.
    """
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    delivery = read_json(_FIXTURES / "delivery.json")
    first, last = date(2017, 12, 1), date(2018, 8, 31)
    start, end = first.isoformat(), last.isoformat()
    source = root / "source.json"
    write_json(source, {
        "source_kind": "SYNTHETIC",
        "notice": "Original synthetic fixture specification; no real market observations.",
        "instrument_id": "TEST", "start": start, "end": end,
        "calendar": "Every civil day; Monday through Friday open, no holidays",
        "ohlc": 100, "volume": 10_000_000,
    })
    raw_hash = digest(source)
    delivery["metadata"].update(
        dataset_id="synthetic-conditional-fixture", start=start, end=end,
        extracted_at="2018-09-01T00:00:00+09:00",
        files=[{"file": source.name, "rows": 1, "schema": "synthetic-source-v1", "sha256": raw_hash}],
    )
    delivery["sources"][0].update(
        published_at="2017-11-30T00:00:00+09:00", captured_at="2017-11-30T01:00:00+09:00",
        raw_file_sha256=raw_hash,
    )
    delivery["events"] = []
    delivery["instruments"][0].update(instrument_id="TEST", code="TEST", effective_from=start)
    delivery["statuses"][0].update(instrument_id="TEST", effective_from=start, effective_to=end)
    delivery["market_profiles"][0].update(effective_from=start, effective_to=end, buy_fee_rate=0)
    delivery["prices"], delivery["calendar"] = [], []
    signals = []
    for offset in range((last - first).days + 1):
        day = first + timedelta(days=offset)
        day_text = day.isoformat()
        is_open = day.weekday() < 5
        delivery["calendar"].append({
            "market": "SYNTHETIC", "date": day_text, "is_open": is_open,
            "opens_at": f"{day_text}T09:00:00+09:00" if is_open else None,
            "closes_at": f"{day_text}T15:30:00+09:00" if is_open else None,
            "reason": "synthetic weekday" if is_open else "synthetic weekend",
            "source_id": "synthetic-notice",
        })
        if not is_open:
            continue
        price = {
            "instrument_id": "TEST", "code": "TEST", "date": day_text,
            "volume": 10_000_000, "turnover": 1_000_000_000,
            "price_factor": 1, "quantity_factor": 1, "source_id": "synthetic-notice",
        }
        for field in ("open", "high", "low", "close"):
            price[field] = price[f"adjusted_{field}"] = 100
        delivery["prices"].append(price)
        # Warmup signals include the prior open session at each window boundary;
        # July/August calendar rows provide future entry and expiry coverage.
        if day < date(2018, 7, 1):
            signals.append({
                "date": day_text, "instrument_id": "TEST", "code": "TEST", "close": 100,
                "atr14": 2, "avg_volume20": 10_000_000, "CROSS_5_20": True,
            })
    windows = {
        period: [date(2018, month, 1).isoformat(), date(2018, month, calendar.monthrange(2018, month)[1]).isoformat()]
        for month, period in enumerate(_PERIODS, start=1)
    }
    for name, payload in (("delivery", delivery), ("signals", signals), ("windows", windows)):
        write_json(root / f"{name}.json", payload)

    evidence = read_json(_FIXTURES / "lifecycle.json")
    evidence["experiment_id"] = "synthetic-conditional-fixture"
    artifacts = {"data": "delivery.json"}
    payloads = {
        "code": {"source_hash": source_hash()},
        "cost_profile": {"market_profiles": delivery["market_profiles"]},
        "validation": {"records": _records(_CANDIDATE)},
        "growth_policy": {"policy": evidence["growth_policy"]},
        "selection_policy": {"policy": evidence["selection_policy"]},
    }
    for role, payload in payloads.items():
        artifacts[role] = f"{role}.json"
        write_json(root / artifacts[role], {"source_kind": "SYNTHETIC", **payload})
    for role in ("code", "data", "cost_profile", "validation"):
        evidence[f"{role}_hash"] = digest(root / artifacts[role])
    lifecycle = root / "lifecycle"
    initialize_lifecycle(lifecycle, evidence, artifact_root=root, artifacts=artifacts)
    freeze_lifecycle(lifecycle, attempt_id="freeze")

    inspection = inspect_delivery(read_json(root / "delivery.json"), root)
    assert inspection["issues"] == [], inspection
    frozen = read_lifecycle(lifecycle)
    assert frozen["state"] == "FROZEN" and frozen["candidate_id"] == _CANDIDATE
    return {
        "delivery": root / "delivery.json", "signals": root / "signals.json", "windows": root / "windows.json",
        "lifecycle": lifecycle, "benchmark_id": "TEST", "artifact_root": root,
    }
