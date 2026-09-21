"""Explicit conservative v3 cohort, independent of strategy outcomes.

The cohort is selected retrospectively for source/model completeness. Its price
trading returns cannot establish full-market performance or dividend-inclusive
account returns. Exclusion reasons are retained, never hidden as zero signals.
"""

from collections import defaultdict
import json

import numpy as np
import pandas as pd

from .io import canonical_hash


def clean_cohort(inputs, adjustments):
    """Return one common instrument set and all exclusions before any returns.

    Known zero-volume days with a valid closing mark remain in the calendar and
    cannot fill. Unsupported entitlements are excluded for the entire study;
    this deliberate hindsight bias is part of the reported estimand.
    """
    prices = inputs.prices
    ids = prices["instrument_id"].astype(str)
    reasons = defaultdict(set)

    def exclude(mask, reason):
        for identity in ids.loc[mask].unique():
            reasons[identity].add(reason)

    raw = {name: prices["raw_" + name] if "raw_" + name in prices else prices[name]
           for name in ("open", "high", "low", "close")}
    adjusted = prices[["adjusted_" + name for name in ("open", "high", "low", "close")]].astype(float)
    adj_valid = np.isfinite(adjusted).all(axis=1) & adjusted.gt(0).all(axis=1)
    adj_valid &= adjusted["adjusted_high"].ge(adjusted.max(axis=1))
    adj_valid &= adjusted["adjusted_low"].le(adjusted.min(axis=1))
    exclude(~adj_valid, "ADJUSTED_PAIR_INVALID_OR_MISSING")
    raw_frame = pd.DataFrame(raw).astype(float)
    volume = pd.to_numeric(prices["volume"], errors="coerce").astype(float)
    valid_ohlc = np.isfinite(raw_frame).all(axis=1) & raw_frame.gt(0).all(axis=1)
    valid_ohlc &= raw_frame.high.ge(raw_frame.max(axis=1)) & raw_frame.low.le(raw_frame.min(axis=1))
    exclude(~np.isfinite(volume) | volume.lt(0), "RAW_VOLUME_UNKNOWN")
    exclude(~np.isfinite(raw_frame.close) | raw_frame.close.le(0), "RAW_CLOSING_MARK_UNKNOWN")
    exclude(volume.gt(0) & ~valid_ohlc, "RAW_TRADED_OHLC_INVALID")
    ready_dates = {}
    for identity, history in prices.assign(_id=ids).groupby("_id", sort=False):
        days = pd.to_datetime(history["date"]).sort_values()
        if len(days) < 250:
            reasons[identity].add("WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE")
        else:
            ready_dates[identity] = days.iloc[249].date().isoformat()

    proof = []
    unresolved = []
    ids_set = set(ids)
    source_rows = prices.loc[~ids.isin(reasons)]
    current_source_pair = ("raw_source_code" in prices and "adjusted_source_code" in prices
                           and source_rows.raw_source_code.notna().all()
                           and source_rows.adjusted_source_code.notna().all()
                           and set(source_rows.raw_source_code) == {"KRX_OPEN_API"}
                           and set(source_rows.adjusted_source_code) == {"KIWOOM_REST"})
    for index, row in inputs.issues.iterrows():
        code = str(row["issue_code"])
        decision = str(row["decision"])
        if decision not in {"REJECT", "QUARANTINE"}:
            continue
        issue_key = f"issue:{index}:{code}"
        if code == "POINT_IN_TIME_SECTOR_UNAVAILABLE":
            proof.append({"issue": issue_key, "disposition": "NOT_USED_NO_SECTOR_POLICY"})
            continue
        if code == "WARMUP_250_BARS_SHORT":
            proof.append({"issue": issue_key, "disposition": "ENFORCED_BY_250_COMPLETE_BAR_READINESS"})
            continue
        identity = row.get("instrument_id")
        if pd.notna(identity) and str(identity) in ids_set:
            reasons[str(identity)].add(code)
            proof.append({"issue": issue_key, "disposition": "INSTRUMENT_EXCLUDED", "instrument_id": str(identity)})
            continue
        if str(row["affected_scope"]).startswith("stock:") and pd.isna(identity):
            proof.append({"issue": issue_key, "disposition": "OUTSIDE_COMMON_STOCK_COHORT"})
            continue
        if code in {"ADJUSTED_NONPOSITIVE_PRICE_TRADED", "ADJUSTED_OHLC_ORDER_VIOLATION", "RAW_NONPOSITIVE_PRICE_TRADED"}:
            details = row.get("details", {})
            if isinstance(details, str):
                details = json.loads(details)
            # These historical PYKRX issues concern a different source pair.
            # Current consumed rows are independently checked above. Do not
            # generalize this exception to unknown source or issue kinds.
            if (details.get("source_id") == "PYKRX_KRX_UNADJUSTED"
                    and details.get("adjusted_source_id") == "PYKRX_NAVER_ADJUSTED"
                    and current_source_pair):
                proof.append({"issue": issue_key, "disposition": "DIFFERENT_SOURCE_PAIR_CURRENT_ROWS_REVALIDATED"})
                continue
        if code == "CORPORATE_ACTION_PARTIAL":
            day = pd.Timestamp(row["affected_from"])
            matched = inputs.events.loc[(pd.to_datetime(inputs.events.effective_date) == day)
                                        & inputs.events.resolution_status.eq("PARTIAL")]
            if not matched.empty:
                for identity in matched.instrument_id.astype(str):
                    reasons[identity].add(code)
                proof.append({"issue": issue_key, "disposition": "MATCHED_ALL_PARTIAL_EVENTS_ON_DATE"})
                continue
        if code == "UNEXPLAINED_VENDOR_FACTOR":
            day = pd.Timestamp(row["affected_from"])
            matched = adjustments.loc[(pd.to_datetime(adjustments.trading_date) == day)
                                      & adjustments.explanation_status.isin(["OBSERVED_VENDOR_FACTOR", "UNEXPLAINED_VENDOR_FACTOR"])]
            if not matched.empty:
                for identity in matched.stock_id.astype(str):
                    reasons[identity].add(code)
                proof.append({"issue": issue_key, "disposition": "MATCHED_ALL_UNEXPLAINED_FACTORS_ON_DATE"})
                continue
        unresolved.append({"issue": issue_key, "scope": str(row["affected_scope"])})

    if not adjustments.empty:
        bad = adjustments.explanation_status.isin(["OBSERVED_VENDOR_FACTOR", "UNEXPLAINED_VENDOR_FACTOR"])
        for identity in adjustments.loc[bad, "stock_id"].astype(str):
            reasons[identity].add("UNEXPLAINED_VENDOR_FACTOR")
    for event in inputs.events.to_dict("records"):
        identity = str(event["instrument_id"])
        kind, resolution = event.get("event_type"), event.get("resolution_status")
        if resolution == "SUPERSEDED" or kind == "LISTED_SHARE_CHANGE":
            continue
        # Keep only integer splits with explicit source evidence and timing.
        # More complex entitlements require a separate model/data admission.
        ratio = event.get("quantity_ratio")
        reference = event.get("reference_price")
        announcement = event.get("announced_at")
        effective = event.get("effective_date")
        supported = (kind == "SPLIT" and resolution == "RESOLVED"
                     and event.get("settlement_policy") == "NONE"
                     and pd.notna(ratio) and float(ratio) > 1 and float(ratio).is_integer()
                     and pd.notna(reference) and np.isfinite(float(reference)) and float(reference) > 0
                     and pd.notna(announcement) and pd.notna(effective)
                     and pd.Timestamp(announcement).date() < pd.Timestamp(effective).date()
                     and pd.notna(event.get("sequence_no")))
        if not supported:
            reasons[identity].add("UNSUPPORTED_OR_UNPRICED_EVENT:" + str(kind))

    included = sorted(ids_set - set(reasons))
    exclusions = [{"instrument_id": identity, "reasons": sorted(reasons[identity])}
                  for identity in sorted(ids_set & set(reasons))]
    result = {"schema_version": "v3-clean-cohort-v1", "decision": "PASS" if included and not unresolved else "BLOCKED",
              "instrument_ids": included, "exclusions": exclusions, "issue_dispositions": proof,
              "unresolved_issues": unresolved, "source_instruments": len(ids_set),
              "included_instruments": len(included), "excluded_instruments": len(exclusions),
              "allowed_signal_from": {identity: ready_dates[identity] for identity in included},
              "result_label": "CLEAN_COHORT_RAW_PRICE_TRADING_RETURN_CASH_DIVIDENDS_EXCLUDED",
              "limitations": ["RETROSPECTIVE_WHOLE_INSTRUMENT_EXCLUSION_BIAS", "NOT_FULL_MARKET",
                              "CASH_DIVIDENDS_EXCLUDED", "HISTORICAL_DATA_OBSERVED_IN_2026",
                              "STRATEGY_SELECTION_NOT_ADMITTED"]}
    result["scope_hash"] = canonical_hash(result)
    return result
