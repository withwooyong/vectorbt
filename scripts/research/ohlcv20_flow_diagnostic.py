"""Summarize admitted OHLCV20 signal and order ledgers without running a strategy.

Usage: python scripts/research/ohlcv20_flow_diagnostic.py --preflight PATH --output PATH
When the preflight is READY, also pass --ledger-manifest PATH. That manifest
must bind admitted REAL signal and order CSVs to the exact preflight SHA-256:
{"schema":"ohlcv20-diagnostic-ledgers-v1","status":"ADMITTED",
 "source_kind":"REAL","preflight_sha256":"...",
 "signals":{"file":"signals.csv","sha256":"..."},
 "orders":{"file":"orders.csv","sha256":"..."}}

Signals need signal_date,code,eligible. Orders need date,signal_date,code,
slot_id,status; optional slot_cash_krw enables slot-size buckets. The order
ledger must contain the outcome of an admitted diagnostic pass. Optional
hash-bound fills.csv (date,code,slot_id,side) provides sell fills; optional
trades.csv (closed_date,code,slot_id,status=COMPLETED) provides completed trades.
Absent optional ledgers yield null counts. This script does not infer fills
from OHLCV or independently certify ledger provenance.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path


START_YEAR, END_YEAR = 2015, 2023
CAP_STATUS = "BUY_LIQUIDITY_LIMIT_EXCEEDED"
ORDER_STATUSES = {
    "UNFILLED",
    "INELIGIBLE_OR_UNTRADEABLE",
    "ALREADY_HELD",
    "POSITION_LIMIT_EXCESS",
    "INSUFFICIENT_CASH",
    CAP_STATUS,
    "FILLED",
}
SIZE_BUCKETS = (
    (Decimal("5000000"), "lt_5m"),
    (Decimal("10000000"), "5m_to_lt_10m"),
    (Decimal("25000000"), "10m_to_lt_25m"),
    (Decimal("50000000"), "25m_to_lt_50m"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _year(value: str) -> int:
    from datetime import date

    day = date.fromisoformat(value)
    if not START_YEAR <= day.year <= END_YEAR:
        raise ValueError("DATE_OUTSIDE_EVALUATION_WINDOW")
    return day.year


def _bucket(value: str | None) -> str:
    if value in (None, ""):
        return "unknown"
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("INVALID_SLOT_CASH") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("INVALID_SLOT_CASH")
    for ceiling, name in SIZE_BUCKETS:
        if amount < ceiling:
            return name
    return "gte_50m"


def _read_bound_csv(manifest_path: Path, entry: dict) -> list[dict[str, str]]:
    relative = Path(entry["file"])
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".csv":
        raise ValueError("UNSAFE_LEDGER_PATH")
    source = manifest_path.parent / relative
    if _sha256(source) != entry["sha256"]:
        raise ValueError("LEDGER_HASH_MISMATCH")
    with source.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _blocked(reason_codes: list[str]) -> dict:
    blank = dict(
        signals=None,
        orders=None,
        buy_fills=None,
        sell_fills=None,
        completed_trades=None,
        buy_capacity_skips=None,
    )
    return {
        "schema": "ohlcv20-flow-diagnostic-v1",
        "status": "BLOCKED",
        "reason_codes": sorted(set(reason_codes)),
        "interpretation": "NO_ADMITTED_SIGNAL_OR_ORDER_COUNTS",
        "years": {str(year): blank.copy() for year in range(START_YEAR, END_YEAR + 1)},
        "capacity_skips_by_slot_size": None,
    }


def summarize(
    preflight: dict,
    signals: list[dict] | None = None,
    orders: list[dict] | None = None,
    fills: list[dict] | None = None,
    trades: list[dict] | None = None,
) -> dict:
    """Count admitted ledgers; fail closed before looking at their rows."""
    factors = preflight.get("factors", {})
    candidate = factors.get("candidate_keys")
    admitted = (
        preflight.get("status") == "READY"
        and preflight.get("reason_codes") == []
        and preflight.get("executed_configurations") == 0
        and type(candidate) is int
        and candidate > 0
        and factors.get("price_admitted") == candidate
        and factors.get("volume_admitted") == candidate
    )
    if not admitted:
        reasons = list(preflight.get("reason_codes") or [])
        if (
            factors.get("price_admitted") != candidate
            or factors.get("volume_admitted") != candidate
        ):
            reasons.append("SIGNAL_FACTORS_NOT_FULLY_ADMITTED")
        if preflight.get("status") != "READY":
            reasons.append("PREFLIGHT_NOT_READY")
        if preflight.get("executed_configurations") != 0:
            reasons.append("NOT_A_PRE_EXECUTION_PREFLIGHT")
        return _blocked(reasons)
    if signals is None or orders is None:
        return _blocked(["ADMITTED_DIAGNOSTIC_LEDGERS_MISSING"])

    signal_keys: set[tuple[str, str]] = set()
    signal_count: Counter[int] = Counter()
    for row in signals:
        if not {"signal_date", "code", "eligible"} <= row.keys():
            raise ValueError("MISSING_SIGNAL_LEDGER_FIELDS")
        if str(row["eligible"]).lower() != "true":
            raise ValueError("NON_ELIGIBLE_ROW_IN_SIGNAL_LEDGER")
        key = row["signal_date"], row["code"]
        if key in signal_keys:
            raise ValueError("DUPLICATE_SIGNAL_KEY")
        signal_keys.add(key)
        signal_count[_year(key[0])] += 1

    order_count: Counter[int] = Counter()
    fill_count: Counter[int] = Counter()
    sell_count: Counter[int] = Counter()
    trade_count: Counter[int] = Counter()
    cap_count: Counter[int] = Counter()
    bucket_count: Counter[str] = Counter()
    order_keys: set[tuple[str, str, str]] = set()
    for row in orders:
        if not {"date", "signal_date", "code", "slot_id", "status"} <= row.keys():
            raise ValueError("MISSING_ORDER_LEDGER_FIELDS")
        if (row["signal_date"], row["code"]) not in signal_keys:
            raise ValueError("ORDER_WITHOUT_ADMITTED_SIGNAL")
        if row["status"] not in ORDER_STATUSES:
            raise ValueError("UNKNOWN_ORDER_STATUS")
        try:
            slot = int(row["slot_id"])
        except (ValueError, TypeError) as exc:
            raise ValueError("INVALID_SLOT_ID") from exc
        if not 0 <= slot < 20 or str(slot) != str(row["slot_id"]):
            raise ValueError("INVALID_SLOT_ID")
        key = row["date"], row["code"], row["slot_id"]
        if key in order_keys:
            raise ValueError("DUPLICATE_ORDER_KEY")
        order_keys.add(key)
        year = _year(row["date"])
        if row["date"] <= row["signal_date"]:
            raise ValueError("ORDER_NOT_AFTER_SIGNAL")
        order_count[year] += 1
        if row["status"] == "FILLED":
            fill_count[year] += 1
        if row["status"] == CAP_STATUS:
            cap_count[year] += 1
            bucket_count[_bucket(row.get("slot_cash_krw"))] += 1

    for row in fills or []:
        if not {"date", "code", "slot_id", "side"} <= row.keys():
            raise ValueError("MISSING_FILL_LEDGER_FIELDS")
        year = _year(row["date"])
        if row["side"] not in {"BUY", "SELL"}:
            raise ValueError("UNKNOWN_FILL_SIDE")
        if row["side"] == "SELL":
            sell_count[year] += 1
    for row in trades or []:
        if not {"closed_date", "code", "slot_id", "status"} <= row.keys():
            raise ValueError("MISSING_TRADE_LEDGER_FIELDS")
        if row["status"] != "COMPLETED":
            raise ValueError("NON_COMPLETED_ROW_IN_TRADE_LEDGER")
        trade_count[_year(row["closed_date"])] += 1

    return {
        "schema": "ohlcv20-flow-diagnostic-v1",
        "status": "COUNTED",
        "reason_codes": [],
        "interpretation": "ADMITTED_LEDGER_COUNTS_ONLY_NO_PERFORMANCE_RESULT",
        "years": {
            str(year): dict(
                signals=signal_count[year],
                orders=order_count[year],
                buy_fills=fill_count[year],
                sell_fills=sell_count[year] if fills is not None else None,
                completed_trades=trade_count[year] if trades is not None else None,
                buy_capacity_skips=cap_count[year],
            )
            for year in range(START_YEAR, END_YEAR + 1)
        },
        "capacity_skips_by_slot_size": dict(sorted(bucket_count.items())),
    }


def diagnose(preflight_path: Path, ledger_manifest_path: Path | None = None) -> dict:
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    result = summarize(preflight)
    result["preflight_sha256"] = _sha256(preflight_path)
    if result["reason_codes"] != ["ADMITTED_DIAGNOSTIC_LEDGERS_MISSING"]:
        return result
    if ledger_manifest_path is None:
        return result
    manifest = json.loads(ledger_manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("schema") != "ohlcv20-diagnostic-ledgers-v1"
        or manifest.get("status") != "ADMITTED"
        or manifest.get("source_kind") != "REAL"
        or manifest.get("preflight_sha256") != result["preflight_sha256"]
    ):
        return _blocked(["DIAGNOSTIC_LEDGER_MANIFEST_NOT_ADMITTED_OR_UNBOUND"]) | {
            "preflight_sha256": result["preflight_sha256"]
        }
    signals = _read_bound_csv(ledger_manifest_path, manifest["signals"])
    orders = _read_bound_csv(ledger_manifest_path, manifest["orders"])
    fills = (
        _read_bound_csv(ledger_manifest_path, manifest["fills"])
        if "fills" in manifest
        else None
    )
    trades = (
        _read_bound_csv(ledger_manifest_path, manifest["trades"])
        if "trades" in manifest
        else None
    )
    return summarize(preflight, signals, orders, fills, trades) | {
        "preflight_sha256": result["preflight_sha256"],
        "ledger_manifest_sha256": _sha256(ledger_manifest_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--ledger-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite an earlier diagnostic")
    result = diagnose(args.preflight, args.ledger_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps({"status": result["status"], "reason_codes": result["reason_codes"]})
    )


if __name__ == "__main__":
    main()
