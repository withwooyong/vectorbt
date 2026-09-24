"""Attempt the confirmed 52 real-data configurations only after input admission.

The preflight writes a reproducible blocked ledger when any indispensable fact
is absent. A blocked configuration has no return, trade count or equity curve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .ohlcv20_eligibility import attach_daily_eligibility, load_candidate_metadata
from .ohlcv20_input import load_corrected_v4
from .ohlcv20_market_rules import (
    ENGINE_COLUMNS,
    MARGIN_SESSIONS,
    admission_failures,
    attach_market_rules,
    load_touch_set,
    out_of_touch_set_events,
    separate_configurations,
)
from .ohlcv20_policy import experiments
from .ohlcv20_real_execution import run_ohlcv20_portfolio
from .ohlcv20_rights import coverage_mismatches, event_coverage, load_v4_terms, load_v5_program


def _read(path: Path) -> tuple[dict, str]:
    data = path.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def _coverage(evaluated) -> dict:
    """Fold the evaluation-window bars into a per-year admission scorecard."""
    coverage: dict[str, dict] = {}
    years = evaluated["date"].dt.year
    for year, rows in evaluated.groupby(years, sort=True):
        total = len(rows)
        adjusted = int(rows["adjusted_valid"].sum())
        volume_adjusted = int(rows["volume_adjusted_valid"].sum())
        coverage[str(int(year))] = dict(
            total_bars=total,
            adjusted_valid_bars=adjusted,
            adjusted_valid_ratio=f"{(adjusted / total if total else 0):.4f}",
            volume_adjusted_valid_bars=volume_adjusted,
            volume_adjusted_valid_ratio=f"{(volume_adjusted / total if total else 0):.4f}",
            signal_eligible_bars=int(rows["signal_eligible"].sum()),
            order_eligible_bars=int(rows["order_eligible"].sum()),
            codes=int(rows["code"].nunique()),
        )
    return coverage


@dataclass(frozen=True)
class PreflightInputs:
    """Hash-verified inputs and the blocking decision derived from them."""

    prepared: object
    eligibility: object
    evaluated: object
    factor: dict
    factor_sha256: str
    settlement: dict
    settlement_sha256: str
    eligibility_sha256: str
    metadata_sha256: str
    rights: dict
    reasons: list[str]


def load_preflight_inputs(root: Path) -> PreflightInputs:
    """Load and verify the sealed inputs exactly as the preflight judges them."""
    package = root / "data/sources/ohlcv-admission-20260922/corrected-input-v4"
    evidence = root / "docs/research/evidence/ohlcv-admission-2026-09-22"
    factor, factor_sha = _read(evidence / "factor-admission-v2.json")
    settlement, settlement_sha = _read(evidence / "settlement-compilation-v4.json")
    eligibility_record, eligibility_sha = _read(
        evidence / "ohlcv20-eligibility-v2.json"
    )
    package_manifest, _ = _read(package / "manifest.json")
    admitted_factors_path = (
        root
        / "data/sources/ohlcv-admission-20260922/factor-admission-v2"
        / "factor-admission-audit.parquet"
    )
    prepared = load_corrected_v4(
        package,
        base_snapshot=Path(package_manifest["base_snapshot"]),
        admitted_factors=admitted_factors_path,
        admitted_factors_sha256=factor["output_sha256"],
    )
    if factor["source_manifest_sha256"] != prepared.manifest_sha256:
        raise ValueError("FACTOR_AND_INPUT_MANIFEST_MISMATCH")
    metadata_path = (
        root
        / "data/sources/krx_open_api/instrument-history-2015-2023/instrument-snapshots.parquet"
    )
    metadata, metadata_sha = load_candidate_metadata(
        metadata_path, set(prepared.bars.code)
    )
    eligibility = attach_daily_eligibility(
        prepared.bars,
        prepared.selected_months,
        prepared.calendar,
        metadata,
        metadata_sha256=metadata_sha,
    )
    evaluated = eligibility.bars.loc[
        eligibility.bars.date.between("2015-06-15", "2023-12-31")
    ]
    if (
        eligibility_record["corrected_manifest_sha256"] != prepared.manifest_sha256
        or eligibility_record["metadata_sha256"] != metadata_sha
        or eligibility_record["evaluation_raw_bars"] != len(evaluated)
        or eligibility_record["evaluation_signal_daily_cap_class_eligible"]
        != int(evaluated.signal_eligible.sum())
        or eligibility_record["evaluation_order_prior_session_cap_class_eligible"]
        != int(evaluated.order_eligible.sum())
        or eligibility_record["evaluation_missing_daily_metadata"]
        != int(evaluated.listed_shares.isna().sum())
    ):
        raise ValueError("ELIGIBILITY_EVIDENCE_MISMATCH")
    rights_path = (
        root
        / "data/sources/ohlcv-admission-20260922/settlement-contract-v4/rights-price-payment-inputs.parquet"
    )
    rights = load_v4_terms(rights_path, settlement["output_sha256"])
    reasons = [
        issue
        for issue in prepared.issues
        if issue != "DAILY_POINT_IN_TIME_ELIGIBILITY_UNVERIFIED"
    ]
    if factor["price_factors_admitted"] == 0:
        reasons.append("PRICE_FACTORS_NOT_ADMITTED")
    if factor["volume_factors_admitted"] == 0:
        reasons.append("VOLUME_FACTORS_NOT_ADMITTED")
    if not settlement["execution_admitted"]:
        reasons.append("RIGHTS_CONTRACT_NOT_EXECUTION_ADMITTED")
    if not prepared.real_execution_admitted:
        reasons.append("CORRECTED_INPUT_NOT_EXECUTION_ADMITTED")
    # A partial factor admission does not by itself grant a signal; the audit
    # tracks that separately from per-key price/volume admission.
    if not factor.get("signal_admitted"):
        reasons.append("SIGNAL_ADMISSION_NOT_GRANTED")
    # The adjusted series is only wired for order/signal use once the input
    # adapter received the sealed admitted-factor evidence and it actually
    # admitted at least one bar.
    admission = prepared.adjusted_admission
    if admission is None or admission.adjusted_valid_bars == 0:
        reasons.append("ADJUSTED_INPUT_NOT_WIRED")
    return PreflightInputs(
        prepared=prepared,
        eligibility=eligibility,
        evaluated=evaluated,
        factor=factor,
        factor_sha256=factor_sha,
        settlement=settlement,
        settlement_sha256=settlement_sha,
        eligibility_sha256=eligibility_sha,
        metadata_sha256=metadata_sha,
        rights=rights,
        reasons=sorted(set(reasons)),
    )


def preflight(root: Path) -> dict:
    """Verify actual cached data and list every blocked requested execution."""
    loaded = load_preflight_inputs(root)
    prepared, evaluated, factor = loaded.prepared, loaded.evaluated, loaded.factor
    settlement, rights, reasons = loaded.settlement, loaded.rights, loaded.reasons
    factor_sha, settlement_sha = loaded.factor_sha256, loaded.settlement_sha256
    eligibility_sha = loaded.eligibility_sha256
    admission = prepared.adjusted_admission
    configurations = [
        dict(
            strategy=e.key,
            stop_pct=str(e.stop_pct),
            target_pct=str(e.target_pct),
            holding_months=e.holding_months,
            friction_rate=friction,
            status="BLOCKED" if reasons else "READY",
            equity_krw=None,
            total_return=None,
            completed_trades=None,
            reason_codes=reasons,
        )
        for e in experiments()
        for friction in ("0.001", "0.002")
    ]
    assert len(configurations) == 52
    return dict(
        status="BLOCKED" if reasons else "READY",
        interpretation="REAL_BACKTEST_NOT_EXECUTED_NO_PERFORMANCE_OUTPUT"
        if reasons
        else "INPUT_READY_FOR_EXECUTION",
        evaluation_start="2015-06-15",
        evaluation_end="2023-12-31",
        initial_cash_krw=100_000_000,
        requested_configurations=52,
        executed_configurations=0,
        input=dict(
            manifest_sha256=prepared.manifest_sha256,
            raw_bars=len(prepared.bars),
            monthly_selected=len(prepared.selected_months),
            observed_price_dates=len(prepared.calendar),
            eligibility_evidence_sha256=eligibility_sha,
            evaluation_signal_eligible_rows=int(evaluated.signal_eligible.sum()),
            order_eligible_rows=int(evaluated.order_eligible.sum()),
            adjusted_valid_rows=int(prepared.bars.adjusted_valid.sum()),
            admitted_factor_evidence_sha256=admission.evidence_sha256
            if admission
            else None,
            provider_mismatch_bars=admission.provider_mismatch_bars
            if admission
            else None,
        ),
        factors=dict(
            evidence_sha256=factor_sha,
            candidate_keys=factor["candidate_keys"],
            price_admitted=factor["price_factors_admitted"],
            volume_admitted=factor["volume_factors_admitted"],
            both_factors_admitted=factor["both_factors_admitted"],
            signal_admitted=factor["signal_admitted"],
        ),
        rights=dict(
            evidence_sha256=settlement_sha,
            event_count=len(rights),
            leg_count=sum(len(event.legs) for event in rights.values()),
            source_sha256=settlement["output_sha256"],
        ),
        reason_codes=reasons,
        coverage=_coverage(evaluated),
        configurations=configurations,
    )


_V4_MANIFEST = "data/sources/ohlcv-admission-20260922/corrected-input-v4/manifest.json"
_TOUCH_SET = "docs/research/evidence/ohlcv-admission-2026-09-22/execution-touch-set-v1.json"
_RECEIPT_REQUIRED_INPUTS = (
    "docs/research/evidence/ohlcv-admission-2026-09-22/factor-admission-v2.json",
    "docs/research/evidence/ohlcv-admission-2026-09-22/ohlcv20-eligibility-v2.json",
    "data/sources/ohlcv-admission-20260922/factor-admission-v2/factor-admission-audit.parquet",
    "docs/research/evidence/ohlcv-admission-2026-09-22/settlement-compilation-v5.json",
    "docs/research/evidence/ohlcv-admission-2026-09-22/signal-admission-v1.json",
    _V4_MANIFEST,
    _TOUCH_SET,
)


def _engine_dry_pass(frame, failures, calendar, program, prepared, outside) -> dict:
    """Load every admissible bar through the real gate with no signal at all.

    No order can be placed, so this checks the gate, the rights coverage, the
    ledger schedule and bar admission on actual data without any return.
    """
    loadable = frame.loc[failures.isna(), ENGINE_COLUMNS]
    result = run_ohlcv20_portfolio(
        loadable,
        [],
        calendar,
        start=calendar[0],
        end=calendar[-1],
        stop_pct="0.10",
        target_pct="0.20",
        holding_months=1,
        costs=lambda *_: 0,
        levels=lambda _side, _day, _market, price: price,
        rights_ledger=program.ledger(),
        event_schedule=program.event_schedule(),
        admission=prepared.engine_admission(),
        source_kind="REAL",
        rights_program=program,
        out_of_set_events=outside,
    )
    return dict(
        status=result["status"],
        loaded_bars=len(loadable),
        issues=result["issues"],
        fills=len(result["fills"]),
    )


def preflight_v5(root: Path) -> dict:
    """Rerun the preflight on corrected-input-v5 opened only by its receipt.

    Configurations are separated before any run: a coverage mismatch blocks
    all of them, and refused market-rule bars block the holding horizon that
    can reach them. No configuration is executed here.
    """
    package = root / "data/sources/ohlcv-admission-20260922/corrected-input-v5"
    evidence = root / "docs/research/evidence/ohlcv-admission-2026-09-22"
    receipt_path = evidence / "ohlcv20-real-admission-v1.json"
    factor, factor_sha = _read(evidence / "factor-admission-v2.json")
    eligibility_record, eligibility_sha = _read(evidence / "ohlcv20-eligibility-v2.json")
    package_manifest, _ = _read(package / "manifest.json")
    prepared = load_corrected_v4(
        package,
        base_snapshot=Path(package_manifest["base_snapshot"]),
        admitted_factors=root
        / "data/sources/ohlcv-admission-20260922/factor-admission-v2"
        / "factor-admission-audit.parquet",
        admission_receipt=receipt_path,
    )
    receipt = prepared.admission_receipt
    # Every evidence file the receipt was built from must still hash the same,
    # the ones this preflight reads above all.
    hashes = receipt.get("input_hashes") or {}
    if not set(_RECEIPT_REQUIRED_INPUTS) <= set(hashes):
        raise ValueError("RECEIPT_INPUT_HASHES_INCOMPLETE")
    for name, expected in hashes.items():
        path = Path(name) if Path(name).is_absolute() else root / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("RECEIPT_INPUT_HASH_MISMATCH:" + name)
    # Factor and eligibility evidence were sealed on v4; v5 must carry every
    # v4 file byte for byte for that evidence to describe the same bars.
    v4_manifest, v4_sha = _read(root / _V4_MANIFEST)
    v5_files = {item["file"]: item["sha256"] for item in package_manifest["files"]}
    if receipt["input_hashes"].get(_V4_MANIFEST) != v4_sha or any(
        v5_files.get(item["file"]) != item["sha256"] for item in v4_manifest["files"]
    ):
        raise ValueError("V5_DOES_NOT_CARRY_BOUND_V4_FILES")
    if factor["source_manifest_sha256"] != v4_sha:
        raise ValueError("FACTOR_AND_INPUT_MANIFEST_MISMATCH")
    metadata, metadata_sha = load_candidate_metadata(
        root
        / "data/sources/krx_open_api/instrument-history-2015-2023/instrument-snapshots.parquet",
        set(prepared.bars.code),
    )
    eligibility = attach_daily_eligibility(
        prepared.bars,
        prepared.selected_months,
        prepared.calendar,
        metadata,
        metadata_sha256=metadata_sha,
    )
    evaluated = eligibility.bars.loc[
        eligibility.bars.date.between("2015-06-15", "2023-12-31")
    ]
    if (
        eligibility_record["corrected_manifest_sha256"] != v4_sha
        or eligibility_record["metadata_sha256"] != metadata_sha
        or eligibility_record["evaluation_raw_bars"] != len(evaluated)
        or eligibility_record["evaluation_signal_daily_cap_class_eligible"]
        != int(evaluated.signal_eligible.sum())
        or eligibility_record["evaluation_order_prior_session_cap_class_eligible"]
        != int(evaluated.order_eligible.sum())
    ):
        raise ValueError("ELIGIBILITY_EVIDENCE_MISMATCH")

    program = load_v5_program(package / "rights-terms.parquet", receipt["rights_terms_sha256"])
    mismatches = coverage_mismatches(program, receipt["rights_event_coverage"])
    touch_set = load_touch_set(root / _TOUCH_SET, receipt["input_hashes"].get(_TOUCH_SET))
    calendar = [
        day for day in prepared.calendar if pd.Timestamp("2015-06-15") <= day <= pd.Timestamp("2023-12-31")
    ]
    outside = out_of_touch_set_events(
        pd.read_parquet(package / "corporate-actions.parquet"), touch_set, calendar
    )
    frame = attach_market_rules(
        evaluated, pd.read_parquet(package / "market-rules.parquet"), program
    )
    failures = admission_failures(frame)
    # Blocking uses the full reach bound; the entry-feasible bound is reported
    # beside it so the two judgment units can be compared.
    horizons = separate_configurations(frame, failures, calendar, program=program)
    entry_horizons = separate_configurations(
        frame, failures, calendar, program=program, entry_feasible_only=True
    )

    reasons = [
        issue
        for issue in prepared.issues
        if issue != "DAILY_POINT_IN_TIME_ELIGIBILITY_UNVERIFIED"
    ]
    if mismatches:
        reasons.append("RIGHTS_EVENT_COVERAGE_MISMATCH")
    admission = prepared.adjusted_admission
    if admission is None or admission.adjusted_valid_bars == 0:
        reasons.append("ADJUSTED_INPUT_NOT_WIRED")
    reasons = sorted(set(reasons))
    dry_pass = (
        None
        if reasons
        else _engine_dry_pass(frame, failures, calendar, program, prepared, outside)
    )
    if dry_pass is not None and dry_pass["status"] != "SUCCEEDED":
        reasons.append("ENGINE_DRY_PASS_BLOCKED")
    configurations = []
    for e in experiments():
        for friction in ("0.001", "0.002"):
            codes = sorted(set(reasons) | set(horizons[e.holding_months]["reason_codes"]))
            configurations.append(
                dict(
                    strategy=e.key,
                    stop_pct=str(e.stop_pct),
                    target_pct=str(e.target_pct),
                    holding_months=e.holding_months,
                    friction_rate=friction,
                    status="BLOCKED" if codes else "READY",
                    equity_krw=None,
                    total_return=None,
                    completed_trades=None,
                    reason_codes=codes,
                )
            )
    assert len(configurations) == 52
    ready = sum(item["status"] == "READY" for item in configurations)
    blocked_by_reason: dict[str, int] = {}
    for item in configurations:
        for code in item["reason_codes"]:
            blocked_by_reason[code] = blocked_by_reason.get(code, 0) + 1
    coverage = event_coverage(program)
    return dict(
        schema="ohlcv20-preflight-v5",
        status="READY" if ready == 52 else ("PARTIAL" if ready else "BLOCKED"),
        interpretation="PREFLIGHT_ONLY_NO_CONFIGURATION_EXECUTED",
        evaluation_start="2015-06-15",
        evaluation_end="2023-12-31",
        requested_configurations=52,
        executed_configurations=0,
        ready_configurations=ready,
        blocked_configurations=52 - ready,
        blocked_by_reason=dict(sorted(blocked_by_reason.items())),
        blocking_basis="REACH_UPPER_BOUND",
        blocked_if_entry_feasible_basis=sum(
            bool(set(reasons) | set(entry_horizons[e.holding_months]["reason_codes"]))
            for e in experiments()
            for _ in ("0.001", "0.002")
        ),
        input=dict(
            manifest_sha256=prepared.manifest_sha256,
            admission_receipt_sha256=prepared.admission_receipt_sha256,
            real_execution_admitted=prepared.real_execution_admitted,
            v4_manifest_sha256=v4_sha,
            eligibility_evidence_sha256=eligibility_sha,
            factor_evidence_sha256=factor_sha,
            evaluation_bars=len(evaluated),
            evaluation_signal_eligible_rows=int(evaluated.signal_eligible.sum()),
        ),
        rights=dict(
            source_sha256=program.source_sha256,
            coverage_mismatches=mismatches,
            events=coverage["all"]["count"],
            applied=coverage["applied"]["count"],
            applied_by_treatment={
                name: part["applied"]["count"]
                for name, part in coverage["by_treatment"].items()
            },
            ledger_events=len(program.ledger_events),
        ),
        market_rules=dict(
            evaluation_bars=len(frame),
            bars_without_rule_row=int((~frame.market_rule_present).sum()),
            codes_without_rule_row=int(frame.loc[~frame.market_rule_present, "code"].nunique()),
            refused_bars=int(failures.notna().sum()),
            refused_rule_present_bars=int((failures.notna() & frame.market_rule_present).sum()),
            margin_sessions=MARGIN_SESSIONS,
            by_holding_months={str(key): value for key, value in horizons.items()},
            entry_feasible_by_holding_months={
                str(key): value for key, value in entry_horizons.items()
            },
        ),
        touch_set=dict(
            reached_events=len(touch_set),
            out_of_set_event_sessions=len(outside),
        ),
        deferred_blocker_revalidation=dict(
            blocker="NEW_STRATEGY_EXECUTION_MODEL_NOT_VALIDATED",
            checks=dict(
                receipt_bound_input_loader=prepared.real_execution_admitted,
                rights_event_coverage_matches_receipt=not mismatches,
                engine_dry_pass=dry_pass,
            ),
            # Wiring on real data plus synthetic path tests; real trading paths
            # remain unchecked while no configuration can run.
            resolved=bool(dry_pass and dry_pass["status"] == "SUCCEEDED")
            and not mismatches
            and ready > 0,
        ),
        reason_codes=reasons,
        configurations=configurations,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ted-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--v5", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite a prior preflight")
    result = (preflight_v5 if args.v5 else preflight)(args.ted_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "requested_configurations",
                    "executed_configurations",
                    "reason_codes",
                )
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
