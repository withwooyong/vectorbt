"""Attempt the confirmed 52 real-data configurations only after input admission.

The preflight writes a reproducible blocked ledger when any indispensable fact
is absent. A blocked configuration has no return, trade count or equity curve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from .ohlcv20_eligibility import attach_daily_eligibility, load_candidate_metadata
from .ohlcv20_input import load_corrected_v4
from .ohlcv20_policy import experiments
from .ohlcv20_rights import load_v4_terms


def _read(path: Path) -> tuple[dict, str]:
    data = path.read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def preflight(root: Path) -> dict:
    """Verify actual cached data and list every blocked requested execution."""
    package = root / "data/sources/ohlcv-admission-20260922/corrected-input-v4"
    evidence = root / "docs/research/evidence/ohlcv-admission-2026-09-22"
    factor, factor_sha = _read(evidence / "factor-admission-v1.json")
    settlement, settlement_sha = _read(evidence / "settlement-compilation-v4.json")
    eligibility_record, eligibility_sha = _read(
        evidence / "ohlcv20-eligibility-v2.json"
    )
    package_manifest, _ = _read(package / "manifest.json")
    prepared = load_corrected_v4(
        package, base_snapshot=Path(package_manifest["base_snapshot"])
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
    if factor["price_factors_admitted"] != factor["candidate_keys"]:
        reasons.append("PRICE_FACTORS_NOT_ADMITTED")
    if factor["volume_factors_admitted"] != factor["candidate_keys"]:
        reasons.append("VOLUME_FACTORS_NOT_ADMITTED")
    if not settlement["execution_admitted"]:
        reasons.append("RIGHTS_CONTRACT_NOT_EXECUTION_ADMITTED")
    if not prepared.real_execution_admitted:
        reasons.append("CORRECTED_INPUT_NOT_EXECUTION_ADMITTED")
    # A rights-aware REAL core exists, but the admitted factor/signal and
    # official event schedule have not been delivered to its inputs.
    reasons.append("SIGNAL_AND_RIGHTS_INPUT_PIPELINE_NOT_WIRED")
    reasons = sorted(set(reasons))
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
        ),
        factors=dict(
            evidence_sha256=factor_sha,
            candidate_keys=factor["candidate_keys"],
            price_admitted=factor["price_factors_admitted"],
            volume_admitted=factor["volume_factors_admitted"],
        ),
        rights=dict(
            evidence_sha256=settlement_sha,
            event_count=len(rights),
            leg_count=sum(len(event.legs) for event in rights.values()),
            source_sha256=settlement["output_sha256"],
        ),
        reason_codes=reasons,
        configurations=configurations,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ted-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Refusing to overwrite a prior preflight")
    result = preflight(args.ted_root)
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
