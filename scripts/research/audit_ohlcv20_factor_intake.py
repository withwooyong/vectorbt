"""Audit local factor-v2 dependencies without generating signals or running a portfolio.

Run from the repository root with --ted-root and a new --out directory. Inputs
are read only; outputs are a key-level intake table, dependency edges, and a
hash-bound summary. Missing evidence or changed inputs fail closed. Existing
outputs are never overwritten. No network or database access is used.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.krx_lab.ohlcv20_eligibility import attach_daily_eligibility, load_candidate_metadata
from research.krx_lab.ohlcv20_input import load_corrected_v4

START = pd.Timestamp("2015-06-15")
END = pd.Timestamp("2023-12-31")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def event_window(calendar: pd.DatetimeIndex, event: pd.Timestamp) -> np.ndarray:
    """t-60 < event <= t: exactly the signal core's factor dependency test."""
    positions = np.arange(60, len(calendar))
    return positions[(calendar[positions - 60] < event) & (event <= calendar[positions])]


def prior_opportunities(dates: pd.DatetimeIndex, event: pd.Timestamp) -> dict:
    """Entry eligibility is a possibility, never evidence of an actual holding."""
    past = dates[dates < event]
    return {
        "prior_order_eligible_days_all": len(past),
        "prior_order_eligible_days_1_calendar_month": int((past >= event - pd.DateOffset(months=1)).sum()),
        "prior_order_eligible_days_3_calendar_months": int((past >= event - pd.DateOffset(months=3)).sum()),
        "actual_held_at_event": None,
        "actual_holdings_assessment": "NOT_EXECUTED_UNKNOWN",
        "delayed_exit_tail": "NOT_BOUNDED_BY_THREE_MONTHS" if len(past) else "NO_PRIOR_ELIGIBLE_ENTRY_OBSERVED",
    }


def verify_eligibility_receipt(receipt: dict, corrected_sha: str, base_sha: str) -> None:
    expected = {
        "corrected_manifest_sha256": corrected_sha,
        "base_manifest_sha256": base_sha,
        "evaluation_start": str(START.date()),
        "evaluation_end": str(END.date()),
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            raise ValueError(f"ELIGIBILITY_RECEIPT_BINDING_MISMATCH:{field}")


def audit(ted: Path, out: Path) -> dict:
    if out.exists():
        raise FileExistsError("Refusing to overwrite an earlier intake audit")
    evidence = ted / "docs/research/evidence/ohlcv-admission-2026-09-22"
    package = ted / "data/sources/ohlcv-admission-20260922/corrected-input-v4"
    inputs: dict[str, str] = {}

    def bind(path: Path, expected: str | None = None) -> dict | None:
        observed = digest(path)
        if expected is not None and observed != expected:
            raise ValueError(f"INPUT_HASH_MISMATCH:{path}")
        inputs[str(path.resolve())] = observed
        return json.loads(path.read_bytes()) if path.suffix == ".json" else None

    factor = bind(evidence / "factor-admission-v2.json")
    candidate = bind(evidence / "reference-factor-candidates-v2.json", factor["candidate_report_sha256"])
    bind(evidence / "factor-admission-policy-v1.json", factor["policy_sha256"])
    manifest = bind(package / "manifest.json", factor["source_manifest_sha256"])
    bind(ted / "scripts/data_delivery/build_ohlcv_admitted_factors.py", factor["builder_sha256"])
    bind(ted / "scripts/data_delivery/build_ohlcv_reference_factor_candidates.py", candidate["builder_sha256"])
    for artifact in candidate["artifacts"]:
        bind(ted / artifact["path"], artifact["sha256"])
    factor_path = ted / "data/sources/ohlcv-admission-20260922/factor-admission-v2/factor-admission-audit.parquet"
    bind(factor_path, factor["output_sha256"])
    for part in manifest["files"]:
        bind(package / part["file"], part["sha256"])
    base = Path(manifest["base_snapshot"])
    base_manifest = bind(base / "manifest.json", manifest["base_manifest_sha256"])
    for part in base_manifest["parts"]:
        if part["member_kind"] == "CALENDAR":
            bind(base / part["file"], part["sha256"])
    for filename in ("ohlcv20_input.py", "ohlcv20_eligibility.py", "ohlcv20_signal.py", "ohlcv20_real_execution.py"):
        bind(REPO / "research/krx_lab" / filename)
    bind(Path(__file__))
    source = pd.read_parquet(factor_path)
    if len(source) != factor["candidate_keys"] or source.duplicated(["stock_code", "effective_date"]).any():
        raise ValueError("FACTOR_KEY_COUNT_OR_IDENTITY_MISMATCH")
    if factor["signal_admitted"] or factor["real_execution_admitted"]:
        raise ValueError("ADMISSION_CONTRACT_CHANGED_REVIEW_REQUIRED")
    for side in ("price", "volume"):
        if int(source[f"{side}_admitted"].sum()) != factor[f"{side}_factors_admitted"]:
            raise ValueError("FACTOR_REPORT_COUNT_MISMATCH")
    prepared = load_corrected_v4(
        package, base_snapshot=base, admitted_factors=factor_path,
        admitted_factors_sha256=factor["output_sha256"],
    )
    eligibility_record = bind(evidence / "ohlcv20-eligibility-v2.json")
    verify_eligibility_receipt(
        eligibility_record, factor["source_manifest_sha256"], manifest["base_manifest_sha256"],
    )
    metadata_path = ted / "data/sources/krx_open_api/instrument-history-2015-2023/instrument-snapshots.parquet"
    bind(metadata_path, eligibility_record["metadata_sha256"])
    metadata, metadata_sha = load_candidate_metadata(metadata_path, set(prepared.bars.code))
    eligible = attach_daily_eligibility(
        prepared.bars, prepared.selected_months, prepared.calendar, metadata, metadata_sha256=metadata_sha,
    )
    bars = eligible.bars.reset_index(drop=True)
    calendar = prepared.calendar
    evaluation = bars.date.between(START, END).to_numpy()
    if int(evaluation.sum()) != eligibility_record["evaluation_raw_bars"]:
        raise ValueError("ELIGIBILITY_EVALUATION_ROWS_CHANGED")
    for column, field in (("signal_eligible", "evaluation_signal_daily_cap_class_eligible"),
                          ("order_eligible", "evaluation_order_prior_session_cap_class_eligible")):
        if int(bars.loc[evaluation, column].sum()) != eligibility_record[field]:
            raise ValueError(f"ELIGIBILITY_COUNT_CHANGED:{column}")
    context = {}
    for code, indexes in bars.groupby("code", sort=False).indices.items():
        frame = bars.iloc[indexes].set_index("date").sort_index()
        presence = np.asarray(calendar.isin(frame.index), dtype=int)
        complete = np.convolve(presence, np.ones(61, dtype=int))[:len(calendar)] == 61
        context[code] = (frame, indexes, complete)
    price_suffix = np.zeros(len(bars), dtype=bool)
    volume_suffix = np.zeros(len(bars), dtype=bool)
    edges, rows = [], []
    selected = prepared.selected_months
    for record in source.sort_values(["stock_code", "effective_date"]).to_dict("records"):
        code, event = record["stock_code"], pd.Timestamp(record["effective_date"])
        blockers = json.loads(record["blocker_codes_json"])
        blocked = not (record["price_admitted"] and record["volume_admitted"])
        is104 = bool(set(blockers) & {"ALLOTMENT_RATIO_MISMATCH", "ALLOTMENT_RATIO_NOT_PARSED"})
        item = dict(record)
        item.update(
            key=f"{code}:{event.date()}", group="ALLOTMENT_104" if is104 else "OTHER_BLOCKED" if blocked else "BOTH_ADMITTED",
            data_owner="ted-startup", consumer_owner="vectorbt", actual_signal_count=None,
            actual_order_count=None, actual_trade_count=None,
            monthly_selected_at_event=bool(((selected.code == code) & (selected.month == event.strftime("%Y-%m"))).any()),
            event_is_exchange_session=bool(event in calendar),
        )
        dates = calendar[event_window(calendar, event)]
        dates = dates[(dates >= START) & (dates <= END)]
        frame, indexes, complete = context[code]
        observed = dates.intersection(frame.index)
        signal_days = observed[frame.loc[observed, "signal_eligible"].to_numpy(bool)]
        complete_days = signal_days[complete[calendar.get_indexer(signal_days)]]
        order_days = []
        for day in signal_days:
            pos = calendar.get_loc(day)
            next_day = calendar[pos + 1] if pos + 1 < len(calendar) else None
            order_possible = bool(next_day is not None and next_day <= END and next_day in frame.index
                                  and frame.loc[next_day, "order_eligible"])
            if order_possible:
                order_days.append(next_day)
            edges.append(dict(
                key=item["key"], code=code, effective_date=str(event.date()),
                signal_dependency_date=str(day.date()), next_session=str(next_day.date()) if next_day is not None else None,
                complete_61_raw_sessions=bool(complete[pos]), next_session_order_eligible=order_possible,
                factor_blocked=blocked, allotment_104=is104,
            ))
        local_past = (bars.iloc[indexes].date < event).to_numpy() & evaluation[indexes]
        if not record["price_admitted"]:
            price_suffix[indexes] |= local_past
        if not record["volume_admitted"]:
            volume_suffix[indexes] |= local_past
        entry_dates = pd.DatetimeIndex(frame.index[frame.order_eligible & frame.index.to_series().between(START, END)])
        item.update(prior_opportunities(entry_dates, event))
        item.update(
            signal_dependency_calendar_days=len(dates), signal_dependency_observed_days=len(observed),
            signal_eligible_dependency_days=len(signal_days), complete_61_raw_signal_eligible_dependency_days=len(complete_days),
            potential_next_order_eligible_days=len(order_days),
            first_signal_dependency_date=str(signal_days.min().date()) if len(signal_days) else None,
            last_signal_dependency_date=str(signal_days.max().date()) if len(signal_days) else None,
            current_adapter_price_block_dependency_rows=int(local_past.sum()) if not record["price_admitted"] else 0,
            current_adapter_volume_block_dependency_rows=int(local_past.sum()) if not record["volume_admitted"] else 0,
        )
        rows.append(item)
    table = pd.DataFrame(rows)
    edge_table = pd.DataFrame(edges)
    groups = {}
    for name, subset in table.groupby("group"):
        selected_edges = edge_table[edge_table.key.isin(subset.key)]
        groups[name] = dict(
            keys=len(subset), codes=int(subset.stock_code.nunique()),
            keys_with_signal_eligible_dependency=int(subset.signal_eligible_dependency_days.gt(0).sum()),
            signal_dependency_key_day_sum=int(subset.signal_eligible_dependency_days.sum()),
            unique_signal_dependency_code_days=len(selected_edges.drop_duplicates(["code", "signal_dependency_date"])),
            unique_complete_61_raw_signal_dependency_code_days=len(selected_edges[selected_edges.complete_61_raw_sessions].drop_duplicates(["code", "signal_dependency_date"])),
            unique_potential_next_order_code_days=len(selected_edges[selected_edges.next_session_order_eligible].drop_duplicates(["code", "next_session"])),
            keys_with_prior_eligible_entry=int(subset.prior_order_eligible_days_all.gt(0).sum()),
        )
    blocked_edges = edge_table[edge_table.factor_blocked]
    summary = dict(
        schema="ohlcv20-factor-v2-intake-audit-v1", status="ANALYSIS_COMPLETE_EXECUTION_NOT_ADMITTED",
        evaluation_start=str(START.date()), evaluation_end=str(END.date()),
        input_files=inputs, factor_keys=len(table), price_admitted=int(table.price_admitted.sum()),
        volume_admitted=int(table.volume_admitted.sum()), both_admitted=int((table.price_admitted & table.volume_admitted).sum()),
        blocker_counts=dict(sorted(Counter(b for values in table.blocker_codes_json for b in json.loads(values)).items())),
        groups=groups,
        union_blocked_signal_eligible_dependency_code_days=len(blocked_edges.drop_duplicates(["code", "signal_dependency_date"])),
        current_adapter_price_unadmitted_suffix_rows=int(price_suffix.sum()),
        current_adapter_volume_unadmitted_suffix_rows=int(volume_suffix.sum()),
        current_adapter_any_unadmitted_suffix_rows=int((price_suffix | volume_suffix).sum()),
        adapter_adjusted_admission=vars(prepared.adjusted_admission),
        actual_signals=None, actual_orders=None, actual_held_exposures=None, actual_returns=None,
        limitations=[
            "Dependency windows are not generated signals; no signal thresholds or portfolio was run.",
            "Daily eligibility and raw-window presence do not prove can_signal or complete event coverage.",
            "Next-session order eligibility is a potential downstream dependency, not an order or fill.",
            "Prior entry eligibility is not actual ownership or a corporate-action record-date entitlement.",
            "One/three-month entry windows are descriptive; suspended or partial exits can extend holdings beyond three months.",
            "Current adapter suffix blocking uses all later events through 2023 and differs from causal 60-session signal dependencies.",
            "Source evidence after a signal date cannot silently be treated as known at that date.",
            "No data, policy, factor, signal, or REAL admission was changed.",
        ],
    )
    for path, expected in inputs.items():
        if digest(Path(path)) != expected:
            raise ValueError(f"INPUT_CHANGED_DURING_AUDIT:{path}")
    out.mkdir(parents=True)
    table.to_parquet(out / "intake-733.parquet", index=False)
    (out / "intake-733.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    edge_table.to_parquet(out / "dependency-edges.parquet", index=False)
    summary["outputs"] = {name: digest(out / name) for name in ("intake-733.parquet", "intake-733.json", "dependency-edges.parquet")}
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("input_files", "blocker_counts", "limitations")}, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ted-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    audit(args.ted_root.resolve(), args.out.resolve())
