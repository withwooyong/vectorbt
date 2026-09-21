"""원본을 고치지 않는 데이터 인수 검사."""

import numpy as np
import pandas as pd


def delivery_grade(source_kind, issues):
    """Grade a delivery inspection without ever promoting real data to execution."""
    if issues:
        return "BLOCKED"
    return "SYNTHETIC" if source_kind == "SYNTHETIC" else "BLOCKED"


def audit(prices, manifest):
    required = {"date", "code", "open", "high", "low", "close", "volume"}
    missing = sorted(required - set(prices))
    if missing:
        return {"grade": "BLOCKED", "reasons": ["MISSING_COLUMNS"], "missing_columns": missing}
    numeric = prices[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric, errors="coerce").astype(float)
    open_price, high, low, close, volume = (numeric[k] for k in numeric)
    invalid = (~np.isfinite(numeric).all(axis=1) | (numeric.iloc[:, :4] <= 0).any(axis=1) |
               (volume < 0) | (high < pd.concat([open_price, close, low], axis=1).max(axis=1)) |
               (low > pd.concat([open_price, close, high], axis=1).min(axis=1)))
    duplicates = int(prices.duplicated(["date", "code"]).sum())
    invalid_date = int(pd.to_datetime(prices["date"], errors="coerce").isna().sum())
    reasons = []
    if prices.empty:
        reasons.append("EMPTY_SNAPSHOT")
    if duplicates or invalid_date or prices["code"].isna().any() or prices["code"].astype(str).str.strip().eq("").any():
        reasons.append("INVALID_KEYS")
    if invalid.any():
        reasons.append("INVALID_OHLCV")
    synthetic = manifest.get("source") == "SYNTHETIC"
    if not synthetic:
        if not manifest.get("price_semantics_evidence"):
            reasons.append("PRICE_SEMANTICS_UNVERIFIED")
        if manifest.get("mixed_vendors", True):
            reasons.append("MIXED_VENDOR_ADJUSTMENT_UNVERIFIED")
    grade = "SYNTHETIC" if synthetic and not reasons else "BLOCKED"
    # v1의 원가격 기업행사/실제 비용 인수 모듈은 아직 지원하지 않는다.
    # Boolean 한 개로 실제 운용 등급을 만들어 내지 않는다.
    if not synthetic and not reasons:
        grade = "EXPLORATORY_ADJUSTED"
    limitations = [] if synthetic else ["RAW_PRICE_AND_ACTIONS_UNVERIFIED", "HISTORICAL_UNIVERSE_UNVERIFIED",
                                        "OFFICIAL_CALENDAR_UNVERIFIED", "HISTORICAL_STATUS_UNVERIFIED",
                                        "HISTORICAL_TICKS_UNVERIFIED", "COST_MODEL_UNVERIFIED"]
    return {"grade": grade, "reasons": reasons, "limitations": limitations,
            "rows": len(prices), "symbols": int(prices["code"].nunique()),
            "duplicate_keys": duplicates, "invalid_date_rows": invalid_date,
            "invalid_ohlcv_rows": int(invalid.sum()), "zero_volume_rows": int((volume == 0).sum()),
            "invalid_ohlcv_symbols": int(prices.loc[invalid, "code"].nunique()),
            "first_date": str(prices["date"].min()), "last_date": str(prices["date"].max()),
            "invalid_reason_counts_overlap": True}
