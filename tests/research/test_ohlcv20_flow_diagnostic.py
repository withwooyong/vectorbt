"""The annual flow report must never invent counts from unadmitted bars."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = (
    Path(__file__).resolve().parents[2] / "scripts/research/ohlcv20_flow_diagnostic.py"
)
SPEC = importlib.util.spec_from_file_location("ohlcv20_flow_diagnostic", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def ready():
    return dict(
        status="READY",
        reason_codes=[],
        executed_configurations=0,
        factors=dict(candidate_keys=733, price_admitted=733, volume_admitted=733),
    )


def write_csv(path, rows):
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_blocked_preflight_has_null_counts_and_does_not_open_ledgers(tmp_path):
    source = tmp_path / "preflight.json"
    source.write_text(
        json.dumps(
            dict(
                status="BLOCKED",
                reason_codes=["PRICE_FACTORS_NOT_ADMITTED"],
                executed_configurations=0,
                factors=dict(candidate_keys=733, price_admitted=0, volume_admitted=0),
            )
        )
    )
    result = module.diagnose(source, tmp_path / "missing-ledger-manifest.json")
    assert result["status"] == "BLOCKED"
    assert all(
        all(value is None for value in year.values())
        for year in result["years"].values()
    )
    assert "PRICE_FACTORS_NOT_ADMITTED" in result["reason_codes"]


def test_ready_without_bound_ledgers_remains_blocked():
    result = module.summarize(ready())
    assert result["status"] == "BLOCKED"
    assert result["years"]["2015"]["signals"] is None


def test_admitted_ledgers_count_orders_fills_and_capacity_by_year_and_size(tmp_path):
    source = tmp_path / "preflight.json"
    source.write_text(json.dumps(ready()))
    signal_sha = write_csv(
        tmp_path / "signals.csv",
        [
            dict(signal_date="2015-12-30", code="000001", eligible="true"),
            dict(signal_date="2016-01-04", code="000002", eligible="true"),
        ],
    )
    order_sha = write_csv(
        tmp_path / "orders.csv",
        [
            dict(
                date="2015-12-31",
                signal_date="2015-12-30",
                code="000001",
                slot_id="0",
                status="BUY_LIQUIDITY_LIMIT_EXCEEDED",
                slot_cash_krw="5000000",
            ),
            dict(
                date="2016-01-05",
                signal_date="2016-01-04",
                code="000002",
                slot_id="1",
                status="FILLED",
                slot_cash_krw="5100000",
            ),
        ],
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            dict(
                schema="ohlcv20-diagnostic-ledgers-v1",
                status="ADMITTED",
                source_kind="REAL",
                preflight_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                signals=dict(file="signals.csv", sha256=signal_sha),
                orders=dict(file="orders.csv", sha256=order_sha),
            )
        )
    )
    result = module.diagnose(source, manifest)
    assert result["status"] == "COUNTED"
    assert result["years"]["2015"] == dict(
        signals=1,
        orders=1,
        buy_fills=0,
        sell_fills=None,
        completed_trades=None,
        buy_capacity_skips=1,
    )
    assert result["years"]["2016"] == dict(
        signals=1,
        orders=1,
        buy_fills=1,
        sell_fills=None,
        completed_trades=None,
        buy_capacity_skips=0,
    )
    assert result["capacity_skips_by_slot_size"] == {"5m_to_lt_10m": 1}


def test_optional_sell_and_completed_trade_ledgers_are_counted_separately():
    signal = [dict(signal_date="2016-01-04", code="000002", eligible="true")]
    order = [
        dict(
            date="2016-01-05",
            signal_date="2016-01-04",
            code="000002",
            slot_id="1",
            status="FILLED",
        )
    ]
    fills = [
        dict(date="2016-01-06", code="000002", slot_id="1", side="SELL"),
        dict(date="2016-01-07", code="000002", slot_id="1", side="SELL"),
    ]
    trades = [
        dict(closed_date="2016-01-07", code="000002", slot_id="1", status="COMPLETED")
    ]
    year = module.summarize(ready(), signal, order, fills, trades)["years"]["2016"]
    assert year["sell_fills"] == 2
    assert year["completed_trades"] == 1


def test_unbound_manifest_and_changed_csv_cannot_be_counted(tmp_path):
    source = tmp_path / "preflight.json"
    source.write_text(json.dumps(ready()))
    signal_sha = write_csv(
        tmp_path / "signals.csv",
        [
            dict(signal_date="2016-01-04", code="000002", eligible="true"),
        ],
    )
    order_sha = write_csv(
        tmp_path / "orders.csv",
        [
            dict(
                date="2016-01-05",
                signal_date="2016-01-04",
                code="000002",
                slot_id="1",
                status="FILLED",
            ),
        ],
    )
    manifest = tmp_path / "manifest.json"
    record = dict(
        schema="ohlcv20-diagnostic-ledgers-v1",
        status="ADMITTED",
        source_kind="REAL",
        preflight_sha256="bad",
        signals=dict(file="signals.csv", sha256=signal_sha),
        orders=dict(file="orders.csv", sha256=order_sha),
    )
    manifest.write_text(json.dumps(record))
    assert module.diagnose(source, manifest)["status"] == "BLOCKED"
    record["preflight_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(record))
    (tmp_path / "orders.csv").write_text("modified")
    with pytest.raises(ValueError, match="LEDGER_HASH_MISMATCH"):
        module.diagnose(source, manifest)


def test_order_without_signal_and_invalid_status_are_rejected():
    signal = [dict(signal_date="2016-01-04", code="000002", eligible="true")]
    order = [
        dict(
            date="2016-01-05",
            signal_date="2016-01-04",
            code="000001",
            slot_id="0",
            status="FILLED",
        )
    ]
    with pytest.raises(ValueError, match="ORDER_WITHOUT_ADMITTED_SIGNAL"):
        module.summarize(ready(), signal, order)
    order[0]["code"] = "000002"
    order[0]["status"] = "INVENTED"
    with pytest.raises(ValueError, match="UNKNOWN_ORDER_STATUS"):
        module.summarize(ready(), signal, order)
