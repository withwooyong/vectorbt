"""Independent, tiny contract examples; no external data or engine-derived truth."""

from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import pytest

from research.krx_lab.contracts import (
    ContractError, CooperativeStop, ExecutionHooks, ResourceSample, StopToken,
    validate_delivery, validate_files, validate_ledger, validate_lifecycle_evidence,
)


FIXTURES = Path(__file__).parent / "fixtures" / "contracts_v1"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_delivery_fixture_and_source_hash_are_independent_and_immutable():
    value = fixture("delivery.json")
    before = deepcopy(value)
    result = validate_delivery(value)
    assert value == before and result == before and result is not value
    result["metadata"]["revision"] = "changed"
    assert value == before
    assert hashlib.sha256((FIXTURES / "source.json").read_bytes()).hexdigest() == value["sources"][0]["raw_file_sha256"]


@pytest.mark.parametrize("mutate,code", [
    (lambda d: d.update(schema_version="v-next"), "UNSUPPORTED_VERSION"),
    (lambda d: d.pop("events"), "MISSING_FIELDS"),
    (lambda d: d["prices"][0].update(close=float("nan")), "INVALID_NUMBER"),
    (lambda d: d["prices"].append(deepcopy(d["prices"][0])), "DUPLICATE_KEY"),
    (lambda d: d["events"][0].update(event_type="RIGHTS"), "UNSUPPORTED_EVENT"),
    (lambda d: d["events"][0].update(quantity_ratio=0), "INVALID_FACTOR"),
    (lambda d: d["events"][0].update(cancelled=True), "EVENT_REVISION_REQUIRES_RESOLUTION"),
    (lambda d: d["events"][1].update(pay_date="2023-01-01"), "PAYMENT_BEFORE_ENTITLEMENT"),
    (lambda d: d["market_profiles"][0].update(model="KRX_ASSUMED"), "UNSUPPORTED_MARKET_PROFILE"),
    (lambda d: d["metadata"].update(real_data_admitted=True), "REAL_ADMISSION_NOT_GRANTED"),
    (lambda d: d["metadata"].update(end="2024-01-01"), "HOLDOUT_LOCKED"),
    (lambda d: d["sources"][0].update(published_at="2023-01-01"), "INVALID_TIMESTAMP"),
    (lambda d: d["prices"][0].update(source_id="missing"), "UNKNOWN_SOURCE"),
    (lambda d: d["prices"][0].update(instrument_id="missing"), "UNKNOWN_INSTRUMENT"),
    (lambda d: d.update(source_kind="REAL"), "SYNTHETIC_SOURCE_MISLABELED"),
])
def test_delivery_fails_closed(mutate, code):
    value = fixture("delivery.json")
    mutate(value)
    with pytest.raises(ContractError) as exc:
        validate_delivery(value)
    assert exc.value.code == code


def test_fractional_payment_and_source_date_precision_remain_explicit():
    value = fixture("delivery.json")
    value["sources"][0].update(time_precision="date", published_at="2023-01-01")
    validate_delivery(value)
    value["events"][0].update(fractional_policy="CASH_IN_LIEU", fractional_cash_price=25,
                               pay_date="2023-01-02")
    with pytest.raises(ContractError, match="PAYMENT_BEFORE_ENTITLEMENT"):
        validate_delivery(value)


@pytest.mark.parametrize("path", ["../source.json", "/source.json", "C:/source.json", "a\\source.json", "./source.json"])
def test_manifest_path_cannot_escape(path):
    item = fixture("delivery.json")["metadata"]["files"][0]
    item["file"] = path
    with pytest.raises(ContractError, match="UNSAFE_ARTIFACT_PATH"):
        validate_files([item])


def test_hand_calculated_ledger_conservation_without_engine():
    ledger = validate_ledger(fixture("expected-ledger.json"))
    cash, receivable, payable, quantity = 1000, 0, 0, 0
    for day in ledger["equity"]:
        when = day["date"]
        for flow in ledger["cashflows"]:
            if flow["date"] == when:
                cash += flow["cash_delta"]
                receivable += flow["receivable_delta"]
                payable += flow["payable_delta"]
        for fill in ledger["fills"]:
            if fill["date"] == when:
                quantity += fill["quantity"] * (1 if fill["side"] == "buy" else -1)
        for event in ledger["events"]:
            if event["date"] == when:
                quantity += event["quantity_delta"]
        position = next(row for row in ledger["positions"] if row["date"] == when)
        assert (cash, receivable, payable) == (day["cash"], day["receivables"], day["payables"])
        assert quantity == position["quantity"]
        assert day["exposure"] == quantity * position["mark_price"]
    assert (cash, receivable, quantity) == (517, 0, 20)
    assert ledger["equity"][-1]["equity"] == 997
    assert sum(row["fee"] for row in ledger["cashflows"]) == 1
    assert sum(row["tax"] for row in ledger["cashflows"]) == 2


@pytest.mark.parametrize("mutate,code", [
    (lambda d: d["equity"][-1].update(equity=999), "EQUITY_NOT_CONSERVED"),
    (lambda d: d["fills"][0].update(order_id="missing"), "UNKNOWN_ORDER"),
    (lambda d: d["orders"][0].update(side="unknown"), "INVALID_SIDE"),
    (lambda d: d["orders"][0].update(quantity=True), "INVALID_INTEGER"),
    (lambda d: d["orders"][0].update(status="unknown"), "INVALID_ORDER_STATUS"),
    (lambda d: d["fills"][0].update(quantity=0.5), "INVALID_INTEGER"),
    (lambda d: d["events"][0].update(ledger_seq=-1), "INVALID_INTEGER"),
])
def test_ledger_rejects_corrupt_transport(mutate, code):
    value = fixture("expected-ledger.json")
    mutate(value)
    with pytest.raises(ContractError) as exc:
        validate_ledger(value)
    assert exc.value.code == code


def test_lifecycle_fixture_cannot_grant_holdout_even_with_green_synthetic_flags():
    value = fixture("lifecycle.json")
    validate_lifecycle_evidence(value)
    value.update(state="FROZEN", candidate_id="synthetic-candidate")
    value["prerequisites"] = dict.fromkeys(value["prerequisites"], True)
    value["holdout_access"].append({"at":"2023-01-06T00:00:00+09:00", "action":"open", "allowed":True,
                                     "reason":"synthetic test"})
    with pytest.raises(ContractError, match="HOLDOUT_LOCKED"):
        validate_lifecycle_evidence(value)
    value.update(source_kind="REAL", state="DRAFT")
    with pytest.raises(ContractError, match="HOLDOUT_LOCKED"):
        validate_lifecycle_evidence(value)


def test_resource_peak_is_observed_and_stop_reason_is_retained():
    samples = [ResourceSample(**row) for row in fixture("resource-samples.json")]
    assert asdict(samples[-1])["peak_rss_bytes"] == 200
    with pytest.raises(ContractError, match="INVALID_RESOURCE_SAMPLE"):
        ResourceSample(1, 200, 100, 1000)
    token = StopToken()
    token.request_stop("RSS_LIMIT")
    token.request_stop("LATER_REASON")
    with pytest.raises(CooperativeStop) as exc:
        token.raise_if_requested()
    assert exc.value.reason == "RSS_LIMIT"


def test_hooks_propagate_callback_fault_and_callback_stop_request():
    observed = []
    token = StopToken()

    def checkpoint(stage, context):
        observed.append((stage, context["run_id"]))
        token.request_stop("CANCELLED")

    hooks = ExecutionHooks(checkpoint, token)
    with pytest.raises(CooperativeStop, match="CANCELLED"):
        hooks("before_rename", {"run_id": "run-1"})
    assert observed == [("before_rename", "run-1")]

    def fault(stage, context):
        raise OSError("injected rename boundary failure")

    with pytest.raises(OSError, match="injected"):
        ExecutionHooks(fault)("after_artifacts")
    with pytest.raises(ContractError, match="UNKNOWN_HOOK_STAGE"):
        ExecutionHooks()("typo")


@pytest.mark.parametrize("case", ["session_date", "source_before_publish"])
def test_temporal_contract_cannot_relabel_future_evidence(case):
    from pathlib import Path
    from research.krx_lab.io import read_json
    delivery = read_json(Path(__file__).parent / "fixtures/contracts_v1/delivery.json")
    if case == "session_date":
        delivery["calendar"][0]["opens_at"] = "2023-01-10T09:00:00+09:00"
        delivery["calendar"][0]["closes_at"] = "2023-01-10T15:30:00+09:00"
    else:
        delivery["sources"][0]["captured_at"] = "2022-01-01T01:00:00+09:00"
    with pytest.raises(ContractError):
        validate_delivery(delivery)
