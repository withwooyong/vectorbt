"""Independent replay and evidence-integrity checks for v3 run orchestration."""
from decimal import Decimal
from types import SimpleNamespace

import pandas as pd
import pytest

from research.krx_lab import v3_run
from research.krx_lab.io import digest, read_json, write_json


DAYS = pd.to_datetime(["2023-01-25", "2023-01-26", "2023-01-27", "2023-01-30"])
D = Decimal


def test_family_partitions_preserve_global_run_ids_and_cover_full_plan():
    from research.krx_lab.config_v2 import default_config, default_wide_config, primary_runs
    runs = []
    for family, factory in (("basic", default_config), ("wide", default_wide_config)):
        primary = primary_runs(factory("."))
        runs.extend({**spec, "family": family} for spec in primary)
        runs.extend({**spec, "family": family, "cost_bps": None} for spec in primary
                    if spec["cost_bps"] == 30 and spec["delay"] == 1)
    basic, wide = v3_run._select_runs(runs, "basic"), v3_run._select_runs(runs, "wide")
    assert len(basic) == len(wide) == 1232
    assert basic + wide == v3_run._select_runs(runs)
    assert set(index for index, _ in basic).isdisjoint(index for index, _ in wide)
    with pytest.raises(ValueError, match="UNKNOWN_EXPERIMENT_FAMILY"):
        v3_run._select_runs(runs, "invalid")


def _completed_account():
    """Ten shares bought, sold, and settled; all amounts are hand computed."""
    equity = pd.DataFrame([
        dict(date=DAYS[0], settled_cash=D(10000), receivables=D(0), payables=D(1010),
             cash=D(8990), exposure=D(1000), equity=D(9990), positions_count=1),
        dict(date=DAYS[1], settled_cash=D(10000), receivables=D(1088), payables=D(1010),
             cash=D(10078), exposure=D(0), equity=D(10078), positions_count=0),
        dict(date=DAYS[2], settled_cash=D(8990), receivables=D(1088), payables=D(0),
             cash=D(10078), exposure=D(0), equity=D(10078), positions_count=0),
        dict(date=DAYS[3], settled_cash=D(10078), receivables=D(0), payables=D(0),
             cash=D(10078), exposure=D(0), equity=D(10078), positions_count=0),
    ])
    cashflows = pd.DataFrame([
        dict(date=DAYS[0], cash_delta=D(0), receivable_delta=D(0), payable_delta=D(1010)),
        dict(date=DAYS[1], cash_delta=D(0), receivable_delta=D(1088), payable_delta=D(0)),
        dict(date=DAYS[2], cash_delta=D(-1010), receivable_delta=D(0), payable_delta=D(-1010)),
        dict(date=DAYS[3], cash_delta=D(1088), receivable_delta=D(-1088), payable_delta=D(0)),
    ])
    fills = pd.DataFrame([dict(date=DAYS[0], code="1", side="buy", size=10),
                          dict(date=DAYS[1], code="1", side="sell", size=10)])
    positions = pd.DataFrame([dict(date=DAYS[0], code="1", size=10, mark_price=D(100))])
    return dict(status="SUCCEEDED", issues=[], equity=equity, cashflows=cashflows,
                fills=fills, positions=positions, events=pd.DataFrame())


def test_replay_complete_cash_claim_and_share_lifecycle():
    result = _completed_account()
    assert v3_run.reconcile_result(result, expected_dates=DAYS, initial_cash=10000) == {
        "status": "PASS", "days": 4, "fills": 2}


def test_replay_rejects_calendar_cash_and_quantity_corruption():
    missing = _completed_account()
    missing["equity"] = missing["equity"].drop(index=2).reset_index(drop=True)
    with pytest.raises(ValueError, match="EQUITY_CALENDAR_INCOMPLETE"):
        v3_run.reconcile_result(missing, expected_dates=DAYS, initial_cash=10000)

    cash = _completed_account()
    cash["equity"].loc[1, "receivables"] = D(1089)
    with pytest.raises(ValueError, match="LEDGER_REPLAY_MISMATCH:receivables"):
        v3_run.reconcile_result(cash, expected_dates=DAYS, initial_cash=10000)

    shares = _completed_account()
    shares["positions"].loc[0, "size"] = 11
    with pytest.raises(ValueError, match="POSITION_REPLAY_MISMATCH"):
        v3_run.reconcile_result(shares, expected_dates=DAYS, initial_cash=10000)


@pytest.mark.parametrize("changed", ["test", "code"])
def test_certification_rejects_inflight_test_or_code_change(tmp_path, monkeypatch, changed):
    monkeypatch.setattr(v3_run, "_ORACLE_TESTS", ["oracle.py"])
    monkeypatch.setattr(v3_run.subprocess, "run", lambda *args, **kwargs:
                        SimpleNamespace(returncode=0, stdout="1 passed", stderr=""))
    calls = {"test": 0, "code": 0}

    def fake_digest(path):
        if str(path) == "oracle.py":
            calls["test"] += 1
            return ("b" if changed == "test" and calls["test"] > 1 else "a") * 64
        return digest(path)

    def fake_source_hash():
        calls["code"] += 1
        return ("b" if changed == "code" and calls["code"] > 1 else "a") * 64

    monkeypatch.setattr(v3_run, "digest", fake_digest)
    monkeypatch.setattr(v3_run, "source_hash", fake_source_hash)
    with pytest.raises(ValueError, match="EXECUTION_ORACLE_FAILED"):
        v3_run.certify_execution(tmp_path / "evidence")
    evidence = read_json(tmp_path / "evidence/evidence.json")
    assert evidence["status"] == "FAIL"
    assert evidence["returncode"] == 0


@pytest.mark.parametrize("changed", ["source", "typed"])
def test_prepared_verification_rejects_tampered_upstream_part(tmp_path, monkeypatch, changed):
    monkeypatch.setattr(v3_run, "_builder_hash", lambda: "builder")
    upstream = {}
    for name in ("source", "typed"):
        path = tmp_path / name
        path.mkdir()
        (path / "part.parquet").write_bytes(b"sealed-part")
        write_json(path / "manifest.json", {"parts": [{"file": "part.parquet",
                                                       "sha256": digest(path / "part.parquet")}]})
        upstream[name] = path
    out = tmp_path / "prepared"
    out.mkdir()
    cohort = {"decision": "PASS", "instrument_ids": [], "exclusions": []}
    write_json(out / "cohort.json", cohort)
    write_json(out / "manifest.json", {
        "status": "PREPARED", "schema_version": "v3-run-input-v1", "builder_code_hash": "builder",
        "cohort_hash": digest(out / "cohort.json"), "files": {},
        **{name: str(path) for name, path in upstream.items()},
        **{name + "_manifest_hash": digest(path / "manifest.json") for name, path in upstream.items()},
    })
    (upstream[changed] / "part.parquet").write_bytes(b"changed-but-manifest-untouched")
    with pytest.raises(ValueError, match="UPSTREAM_PART_CHANGED"):
        v3_run.verify_prepared(out)
