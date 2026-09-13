"""2015~2023 KRX 스냅샷의 OHLCV 품질을 청크별로 집계한다.

수익률이나 신호를 계산하지 않으며 원본 Parquet 파일을 수정하지 않는다.
각 Parquet 파트(현재 최대 10만 행) 하나만 메모리에 올린다.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PRICE_COLUMNS = ["open", "high", "low", "close"]
NUMERIC_COLUMNS = [*PRICE_COLUMNS, "volume"]
CORE_REASONS = [
    "nonfinite_numeric",
    "nonpositive_price",
    "negative_volume",
    "high_relationship",
    "low_relationship",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add(counter: dict[str, int], key: str, value: int) -> None:
    counter[key] = counter.get(key, 0) + int(value)


def new_bucket() -> dict[str, Any]:
    return {"counts": Counter(), "symbols": set(), "invalid_symbols": set(), "zero_volume_symbols": set()}


def flags_for(frame: pd.DataFrame) -> dict[str, np.ndarray]:
    numeric = frame[NUMERIC_COLUMNS].apply(pd.to_numeric, errors="coerce").astype(float)
    values = {column: numeric[column].to_numpy() for column in NUMERIC_COLUMNS}
    finite = np.isfinite(numeric.to_numpy())
    nonfinite_numeric = ~finite.all(axis=1)
    nonpositive_fields = {column: ~(values[column] > 0) & np.isfinite(values[column]) for column in PRICE_COLUMNS}
    nonpositive_price = np.logical_or.reduce(list(nonpositive_fields.values()))
    negative_volume = (values["volume"] < 0) & np.isfinite(values["volume"])
    zero_volume = (values["volume"] == 0) & np.isfinite(values["volume"])

    # research/krx_lab/quality.py의 관계 판정식을 그대로 분해한다.
    high_relationship = values["high"] < np.maximum.reduce(
        [values["open"], values["close"], values["low"]]
    )
    low_relationship = values["low"] > np.minimum.reduce(
        [values["open"], values["close"], values["high"]]
    )
    invalid_ohlcv = (
        nonfinite_numeric
        | nonpositive_price
        | negative_volume
        | high_relationship
        | low_relationship
    )
    return {
        "nonfinite_numeric": nonfinite_numeric,
        "nonpositive_price": nonpositive_price,
        "negative_volume": negative_volume,
        "high_relationship": high_relationship,
        "low_relationship": low_relationship,
        "zero_volume": zero_volume,
        "invalid_ohlcv": invalid_ohlcv,
        **{f"{column}_nonpositive": flag for column, flag in nonpositive_fields.items()},
        **{f"{column}_zero": (values[column] == 0) & np.isfinite(values[column]) for column in PRICE_COLUMNS},
        **{f"{column}_negative": (values[column] < 0) & np.isfinite(values[column]) for column in PRICE_COLUMNS},
        "high_below_open": values["high"] < values["open"],
        "high_below_close": values["high"] < values["close"],
        "high_below_low": values["high"] < values["low"],
        "low_above_open": values["low"] > values["open"],
        "low_above_close": values["low"] > values["close"],
        "low_above_high": values["low"] > values["high"],
    }


def reason_signature(flags: dict[str, np.ndarray], index: int) -> str:
    reasons = [reason for reason in CORE_REASONS if flags[reason][index]]
    if flags["zero_volume"][index]:
        reasons.append("zero_volume")
    return "+".join(reasons) or "none"


def accumulate_bucket(bucket: dict[str, Any], frame: pd.DataFrame, flags: dict[str, np.ndarray]) -> None:
    counts = bucket["counts"]
    counts["rows"] += len(frame)
    for name, mask in flags.items():
        counts[name] += int(mask.sum())
    counts["invalid_with_zero_volume"] += int((flags["invalid_ohlcv"] & flags["zero_volume"]).sum())
    counts["invalid_with_nonzero_volume"] += int((flags["invalid_ohlcv"] & ~flags["zero_volume"]).sum())
    counts["invalid_with_positive_volume"] += int((flags["invalid_ohlcv"] & ~flags["zero_volume"] & ~flags["negative_volume"]).sum())
    codes = frame["code"].astype(str)
    bucket["symbols"].update(codes.unique())
    bucket["invalid_symbols"].update(codes[flags["invalid_ohlcv"]].unique())
    bucket["zero_volume_symbols"].update(codes[flags["zero_volume"]].unique())


def serialise_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    result = dict(sorted(bucket["counts"].items()))
    result["symbols"] = len(bucket["symbols"])
    result["invalid_symbols"] = len(bucket["invalid_symbols"])
    result["zero_volume_symbols"] = len(bucket["zero_volume_symbols"])
    return result


def audit(snapshot: Path) -> dict[str, Any]:
    manifest_path = snapshot / "manifest.json"
    quality_path = snapshot / "quality.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior_quality = json.loads(quality_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPLETE":
        raise ValueError("완료된 스냅샷이 아닙니다")
    if manifest.get("holdout_prices_included"):
        raise ValueError("2024년 이후 잠금 구간이 포함된 스냅샷은 감사하지 않습니다")
    if sha256(quality_path) != manifest.get("quality_sha256"):
        raise ValueError("quality.json 해시가 manifest와 다릅니다")

    overall = new_bucket()
    by_vendor: dict[str, dict[str, Any]] = defaultdict(new_bucket)
    by_year: dict[str, dict[str, Any]] = defaultdict(new_bucket)
    by_vendor_year: dict[str, dict[str, Any]] = defaultdict(new_bucket)
    exact_combinations: Counter[str] = Counter()
    exact_combinations_by_vendor: dict[str, Counter[str]] = defaultdict(Counter)
    nonpositive_field_combinations: Counter[str] = Counter()
    zero_price_field_combinations: Counter[str] = Counter()
    negative_price_field_combinations: Counter[str] = Counter()
    invalid_codes: dict[str, dict[str, Any]] = {}
    zero_volume_by_code: Counter[str] = Counter()
    observed_first: str | None = None
    observed_last: str | None = None
    maximum_part_rows = 0
    total_part_rows = 0

    required = {"date", "code", *NUMERIC_COLUMNS, "data_vendor"}
    for part in manifest["parts"]:
        part_path = snapshot / part["file"]
        if part_path.parent.resolve() != snapshot.resolve():
            raise ValueError(f"스냅샷 밖의 파트 경로: {part['file']}")
        if sha256(part_path) != part["sha256"]:
            raise ValueError(f"파트 해시 불일치: {part['file']}")
        frame = pd.read_parquet(part_path, columns=sorted(required))
        if set(frame.columns) != required:
            raise ValueError(f"필수 열 불일치: {part['file']}")
        if len(frame) != part["rows"]:
            raise ValueError(f"파트 행 수 불일치: {part['file']}")
        maximum_part_rows = max(maximum_part_rows, len(frame))
        total_part_rows += len(frame)

        dates = pd.to_datetime(frame["date"], errors="coerce")
        if dates.isna().any():
            raise ValueError(f"날짜 변환 실패: {part['file']}")
        if (dates >= pd.Timestamp("2024-01-01")).any():
            raise ValueError(f"2024년 이후 잠금 구간 발견: {part['file']}")
        date_text = dates.dt.strftime("%Y-%m-%d")
        observed_first = min(observed_first or date_text.min(), date_text.min())
        observed_last = max(observed_last or date_text.max(), date_text.max())
        years = dates.dt.year.astype(str)
        vendors = frame["data_vendor"].fillna("<NULL>").astype(str)
        codes = frame["code"].astype(str)
        flags = flags_for(frame)

        accumulate_bucket(overall, frame, flags)
        grouping = pd.DataFrame({"vendor": vendors, "year": years})
        for vendor, index in grouping.groupby("vendor", sort=True).groups.items():
            positions = np.asarray(index, dtype=int)
            accumulate_bucket(by_vendor[vendor], frame.iloc[positions], {k: v[positions] for k, v in flags.items()})
        for year, index in grouping.groupby("year", sort=True).groups.items():
            positions = np.asarray(index, dtype=int)
            accumulate_bucket(by_year[year], frame.iloc[positions], {k: v[positions] for k, v in flags.items()})
        for (vendor, year), index in grouping.groupby(["vendor", "year"], sort=True).groups.items():
            positions = np.asarray(index, dtype=int)
            accumulate_bucket(
                by_vendor_year[f"{vendor}|{year}"],
                frame.iloc[positions],
                {k: v[positions] for k, v in flags.items()},
            )

        invalid_positions = np.flatnonzero(flags["invalid_ohlcv"])
        for position in invalid_positions:
            position = int(position)
            signature = reason_signature(flags, position)
            exact_combinations[signature] += 1
            exact_combinations_by_vendor[vendors.iloc[position]][signature] += 1
            fields = [column for column in PRICE_COLUMNS if flags[f"{column}_nonpositive"][position]]
            if fields:
                nonpositive_field_combinations["+".join(fields)] += 1
            zero_fields = [column for column in PRICE_COLUMNS if flags[f"{column}_zero"][position]]
            if zero_fields:
                zero_price_field_combinations["+".join(zero_fields)] += 1
            negative_fields = [column for column in PRICE_COLUMNS if flags[f"{column}_negative"][position]]
            if negative_fields:
                negative_price_field_combinations["+".join(negative_fields)] += 1
        zero_volume_by_code.update(codes[flags["zero_volume"]].tolist())

        invalid_frame = pd.DataFrame(
            {
                "code": codes[flags["invalid_ohlcv"]],
                "date": date_text[flags["invalid_ohlcv"]],
                "vendor": vendors[flags["invalid_ohlcv"]],
                **{name: mask[flags["invalid_ohlcv"]] for name, mask in flags.items()},
            }
        )
        for code, group in invalid_frame.groupby("code", sort=False):
            record = invalid_codes.setdefault(
                code,
                {
                    "code": code,
                    "invalid_ohlcv_rows": 0,
                    "first_invalid_date": None,
                    "last_invalid_date": None,
                    "vendors": set(),
                    "counts": Counter(),
                    "exact_combinations": Counter(),
                },
            )
            record["invalid_ohlcv_rows"] += len(group)
            first_date, last_date = group["date"].min(), group["date"].max()
            record["first_invalid_date"] = min(record["first_invalid_date"] or first_date, first_date)
            record["last_invalid_date"] = max(record["last_invalid_date"] or last_date, last_date)
            record["vendors"].update(group["vendor"].unique())
            for name in flags:
                record["counts"][name] += int(group[name].sum())
            for row in group.itertuples(index=False):
                active = [reason for reason in CORE_REASONS if getattr(row, reason)]
                if row.zero_volume:
                    active.append("zero_volume")
                record["exact_combinations"]["+".join(active)] += 1

    if total_part_rows != manifest["rows"]:
        raise ValueError("전체 파트 행 수가 manifest와 다릅니다")

    invalid_code_rows = []
    for record in invalid_codes.values():
        invalid_code_rows.append(
            {
                "code": record["code"],
                "invalid_ohlcv_rows": record["invalid_ohlcv_rows"],
                "first_invalid_date": record["first_invalid_date"],
                "last_invalid_date": record["last_invalid_date"],
                "vendors": sorted(record["vendors"]),
                "counts": dict(sorted(record["counts"].items())),
                "exact_combinations": dict(record["exact_combinations"].most_common()),
            }
        )
    invalid_code_rows.sort(key=lambda row: (-row["invalid_ohlcv_rows"], row["code"]))

    invariant_values = {
        "manifest_rows_equal_scanned_rows": manifest["rows"] == overall["counts"]["rows"],
        "prior_rows_equal_scanned_rows": prior_quality["rows"] == overall["counts"]["rows"],
        "prior_invalid_rows_reproduced": prior_quality["invalid_ohlcv_rows"] == overall["counts"]["invalid_ohlcv"],
        "prior_zero_volume_rows_reproduced": prior_quality["zero_volume_rows"] == overall["counts"]["zero_volume"],
        "prior_invalid_symbols_reproduced": prior_quality["invalid_ohlcv_symbols"] == len(invalid_code_rows),
        "invalid_code_detail_matches_bucket": len(invalid_code_rows) == len(overall["invalid_symbols"]),
        "exact_reason_combinations_sum_to_invalid_rows": sum(exact_combinations.values()) == overall["counts"]["invalid_ohlcv"],
        "vendor_rows_sum_to_total": sum(v["counts"]["rows"] for v in by_vendor.values()) == overall["counts"]["rows"],
        "vendor_invalid_rows_sum_to_total": sum(v["counts"]["invalid_ohlcv"] for v in by_vendor.values()) == overall["counts"]["invalid_ohlcv"],
        "year_rows_sum_to_total": sum(v["counts"]["rows"] for v in by_year.values()) == overall["counts"]["rows"],
        "year_invalid_rows_sum_to_total": sum(v["counts"]["invalid_ohlcv"] for v in by_year.values()) == overall["counts"]["invalid_ohlcv"],
        "invalid_zero_and_nonzero_partition": (
            overall["counts"]["invalid_with_zero_volume"] + overall["counts"]["invalid_with_nonzero_volume"]
            == overall["counts"]["invalid_ohlcv"]
        ),
        "no_holdout_rows_observed": observed_last is not None and observed_last < "2024-01-01",
    }
    if not all(invariant_values.values()):
        failures = sorted(name for name, passed in invariant_values.items() if not passed)
        raise ValueError(f"감사 내부 불변식 실패: {failures}")

    result = {
        "schema_version": "krx-snapshot-quality-audit-v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "date_range": [observed_first, observed_last],
            "holdout_2024_plus_locked": True,
            "returns_computed": False,
            "signals_computed": False,
            "raw_data_modified": False,
            "read_pattern": "one manifest part at a time",
            "maximum_rows_loaded_per_part": maximum_part_rows,
        },
        "source_evidence": {
            "snapshot": str(snapshot.resolve()),
            "manifest_sha256": sha256(manifest_path),
            "quality_sha256": sha256(quality_path),
            "parts_verified_by_sha256": len(manifest["parts"]),
            "manifest_rows": manifest["rows"],
            "prior_quality": prior_quality,
        },
        "rule_definition": {
            "reference": "research/krx_lab/quality.py:audit",
            "invalid_ohlcv": "nonfinite_numeric OR nonpositive_price OR negative_volume OR high_relationship OR low_relationship",
            "high_relationship": "high < max(open, close, low)",
            "low_relationship": "low > min(open, close, high)",
            "zero_volume": "diagnostic only; it does not independently make INVALID_OHLCV",
            "reason_counts_overlap": True,
        },
        "decision": {
            "grade": "BLOCKED",
            "reason": "INVALID_OHLCV remains present; source lineage and adjustment semantics are also unverified",
            "causal_classification": "UNPROVEN",
        },
        "invariants": {**invariant_values, "all_passed": True},
        "overall": serialise_bucket(overall),
        "exact_reason_combinations": dict(exact_combinations.most_common()),
        "exact_reason_combinations_by_vendor": {
            key: dict(value.most_common()) for key, value in sorted(exact_combinations_by_vendor.items())
        },
        "nonpositive_price_field_combinations": dict(nonpositive_field_combinations.most_common()),
        "zero_price_field_combinations": dict(zero_price_field_combinations.most_common()),
        "negative_price_field_combinations": dict(negative_price_field_combinations.most_common()),
        "by_vendor": {key: serialise_bucket(value) for key, value in sorted(by_vendor.items())},
        "by_year": {key: serialise_bucket(value) for key, value in sorted(by_year.items())},
        "by_vendor_year": {key: serialise_bucket(value) for key, value in sorted(by_vendor_year.items())},
        "invalid_by_code": invalid_code_rows,
        "zero_volume": {
            "symbols": len(zero_volume_by_code),
            "top_codes": [
                {"code": code, "rows": count} for code, count in zero_volume_by_code.most_common(50)
            ],
        },
        "interpretation_boundaries": [
            "공급자 라벨은 저장 필드이며 행별 원천 계보를 입증하지 않는다.",
            "0 가격이나 OHLC 관계 위반만으로 거래정지, 정상 비거래 봉, 조정 정밀도, 적재 오류를 구분할 수 없다.",
            "거래량 0은 현재 품질 규칙상 독립적인 오류가 아니며 INVALID_OHLCV와의 중복을 별도로 센다.",
            "원천 응답, 당시 수집 코드와 플래그, 기업행사 및 거래 상태 자료 없이는 원인을 확정하지 않는다.",
        ],
    }
    return result


def main() -> None:
    default_snapshot = Path(os.environ.get("LOCALAPPDATA", "")) / "vectorbt-research" / "krx-lab-db-20260913-1542"
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, default=default_snapshot)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("quality-audit.json"))
    args = parser.parse_args()
    result = audit(args.snapshot)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "rows": result["overall"]["rows"],
                "invalid_ohlcv_rows": result["overall"]["invalid_ohlcv"],
                "invalid_ohlcv_symbols": len(result["invalid_by_code"]),
                "returns_computed": False,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
