"""Offline C1 REAL-shaped input for inspection tests only.

Every price and event comes from the existing synthetic C1 fixture.  The REAL
label exercises the delivery boundary; it never represents observed KRX data.
The source is explicitly unavailable, so inspection must remain blocked.
"""

from __future__ import annotations

from pathlib import Path

from research.krx_lab.io import digest, read_json, write_json


_FIXTURES = Path(__file__).parent / "fixtures" / "contracts_v1"


def create_real_shaped_input(root: Path) -> Path:
    """Write a deterministic, pre-2024 C1 inspection specimen and return its path.

    This helper must never be used as a market observation or admitted input.
    It writes only below ``root`` and does not connect to a database or network.
    """
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    delivery = read_json(_FIXTURES / "delivery.json")
    source_path = root / "source.json"
    write_json(source_path, {
        "fixture_kind": "fabricated-offline-contract-specimen",
        "notice": "No historical raw observation is available; all values are synthetic.",
        "date_range": ["2023-01-02", "2023-01-05"],
    })
    raw_hash = digest(source_path)

    delivery["source_kind"] = "REAL"
    delivery["metadata"].update(
        dataset_id="offline-real-shape-fixture-not-market-data",
        currency="KRW",
        files=[{"file": "source.json", "rows": 1, "schema": "synthetic-source-v1", "sha256": raw_hash}],
        real_data_admitted=False,
        holdout_prices_included=False,
    )
    source = delivery["sources"][0]
    source.update(
        source_id="unavailable-original-offline-fixture",
        source_url_or_document_id="fixture:source.json",
        published_at=None,
        time_precision="unknown",
        captured_at="2023-01-06T00:00:00+09:00",
        raw_file_sha256=raw_hash,
        historical_capture="unavailable",
        unavailable_reason="Fabricated contract specimen; no historical observation exists.",
    )
    for section in ("prices", "events", "instruments", "statuses", "calendar", "market_profiles"):
        for row in delivery[section]:
            row["source_id"] = source["source_id"]
            if row.get("market") == "SYNTHETIC":
                row["market"] = "KRX"
    for price in delivery["prices"]:
        price["instrument_id"] = "OFFLINE-SPECIMEN-001"
        price["code"] = "OFFLINE001"
    for section in ("events", "statuses", "instruments"):
        for row in delivery[section]:
            row["instrument_id"] = "OFFLINE-SPECIMEN-001"
            if "code" in row:
                row["code"] = "OFFLINE001"
    delivery_path = root / "delivery.json"
    write_json(delivery_path, delivery)
    return delivery_path
