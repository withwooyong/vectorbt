"""원가(adjusted=False) OHLC 중 하나라도 0 이하인 행을 거래정지 기록·무거래와 대조해 설명되지 않는 행을
종목·일 단위로 확정하는 읽기 전용 진단 스크립트.

이전 진단(B1, universe_diagnosis.py 의 analyze_nonpositive_ohlc)은 거래상태 필드가 오프라인 price
테이블에 없어 "거래량 0" 만으로 설명 여부를 판정했다. 이 스크립트는 별도의 거래상태 테이블
(status-00110.parquet)을 결합해 HALTED/PARTIAL_TRADING 상태까지 반영한 더 정밀한 분류를 만든다.

이 스크립트는 다음을 절대 하지 않는다.
  - 수익률 계산이나 백테스트 실행
  - `../vectorbt-data/` 아래 기존 파일 쓰기/수정 (전부 읽기 전용으로 연다)
  - 이상값 삭제·보정 (기록만 한다)
  - PostgreSQL·네트워크 접속

2024-01-01 이후 가격 행은 파일에서 걸러 읽지 않는다(날짜로 사전 필터링하지 않는다). 대신 읽은 뒤
집계 직전에 제외하고, 그런 행이 있었는지를 결과 JSON의 `date_cutoff` 에 기록한다.

사용법:
    .venv/Scripts/python.exe -X utf8 nonpositive_ohlc_reconciliation.py \
        --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
        --tables-dir ../vectorbt-data/krx-v3-20260921-tables \
        --out nonpositive-ohlc-reconciliation.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

# 같은 디렉터리의 universe_diagnosis.py 를 모듈로 재사용한다(로더·CUTOFF·해시 유틸을 중복 구현하지 않는다).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from universe_diagnosis import (  # noqa: E402
    CUTOFF,
    DEFAULT_PREPARED_DIR,
    DEFAULT_TABLES_DIR,
    load_calendar,
    load_issues,
    load_price_table,
    sha256_file,
)

OHLC_COLS = ["open_price", "high_price", "low_price", "close_price"]
OHLC_LETTERS = ["O", "H", "L", "C"]

# 상태 우선순위(위에서부터). a > b > c > d.
STATUS_HALTED = "STATUS_HALTED"
STATUS_PARTIAL_TRADING = "STATUS_PARTIAL_TRADING"
ZERO_VOLUME_NO_STATUS = "ZERO_VOLUME_NO_STATUS"
UNEXPLAINED = "UNEXPLAINED"

RAW_NONPOSITIVE_ISSUE_CODE = "RAW_NONPOSITIVE_PRICE_TRADED"


# ---------------------------------------------------------------------------
# 입력 로딩
# ---------------------------------------------------------------------------


def load_status(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    """거래상태 테이블(status-00110.parquet)을 읽는다. HALTED/PARTIAL_TRADING/NO_BAR_HALTED 상태를 담는다."""
    fp = tables_dir / "status-00110.parquet"
    if not fp.exists():
        raise FileNotFoundError(f"NO_STATUS_FILE: {fp}")
    df = pd.read_parquet(fp)
    df["trading_date"] = pd.to_datetime(df["trading_date"])
    return df, {fp.name: sha256_file(fp)}


# ---------------------------------------------------------------------------
# 분류
# ---------------------------------------------------------------------------


def build_ohlc_pattern(df: pd.DataFrame) -> pd.Series:
    """0 이하인 OHLC 필드를 O/H/L/C 순서로 이어붙인 패턴 문자열 시리즈를 만든다."""
    pattern = pd.Series("", index=df.index, dtype=object)
    for letter, col in zip(OHLC_LETTERS, OHLC_COLS):
        pattern = pattern + (df[col] <= 0).map({True: letter, False: ""})
    return pattern


def classify_rows(bad: pd.DataFrame, halted_pairs: set, partial_pairs: set) -> pd.Series:
    """우선순위 a>b>c>d 로 각 행을 분류한다. 낮은 우선순위부터 채우고 높은 우선순위로 덮어쓴다."""
    pair_index = pd.MultiIndex.from_arrays([bad["stock_id"], bad["trading_date"]])
    is_halted = pair_index.isin(pd.MultiIndex.from_tuples(halted_pairs)) if halted_pairs else pd.Series(False, index=bad.index).values
    is_partial = pair_index.isin(pd.MultiIndex.from_tuples(partial_pairs)) if partial_pairs else pd.Series(False, index=bad.index).values

    classification = pd.Series(UNEXPLAINED, index=bad.index, dtype=object)
    classification.loc[(bad["trade_volume"] == 0) & ~is_halted & ~is_partial] = ZERO_VOLUME_NO_STATUS
    classification.loc[is_partial] = STATUS_PARTIAL_TRADING
    classification.loc[is_halted] = STATUS_HALTED
    return classification


def nested_counts(df: pd.DataFrame, outer_col: str, inner_col: str) -> dict:
    """두 컬럼 조합의 건수를 {outer: {inner: count}} 형태 중첩 dict 로 만든다."""
    counts = df.groupby([outer_col, inner_col]).size()
    nested: dict = {}
    for (outer, inner), v in counts.items():
        nested.setdefault(str(outer), {})[str(inner)] = int(v)
    return nested


# ---------------------------------------------------------------------------
# UNEXPLAINED 행 상세 정보
# ---------------------------------------------------------------------------


def neighbor_rows(raw_window_sorted: pd.DataFrame, stock_id: int, date: pd.Timestamp) -> tuple[dict | None, dict | None]:
    """같은 종목의 직전·직후 원가 행(날짜·종가·거래량)을 컷오프 이전 범위 안에서 찾는다."""
    sub = raw_window_sorted[raw_window_sorted["stock_id"] == stock_id]
    matches = sub.index[sub["trading_date"] == date]
    if len(matches) == 0:
        return None, None
    pos = sub.index.get_loc(matches[0])

    def _fmt(row: pd.Series | None) -> dict | None:
        if row is None:
            return None
        return {
            "trading_date": row["trading_date"].date().isoformat(),
            "close_price": int(row["close_price"]),
            "trade_volume": int(row["trade_volume"]),
        }

    prev_row = sub.iloc[pos - 1] if pos > 0 else None
    next_row = sub.iloc[pos + 1] if pos < len(sub) - 1 else None
    return _fmt(prev_row), _fmt(next_row)


def same_day_adjusted(adjusted_window: pd.DataFrame, stock_id: int, date: pd.Timestamp) -> dict:
    """같은 날 수정가(adjusted=True) 행이 있는지와 그 OHLC 를 반환한다."""
    sub = adjusted_window[(adjusted_window["stock_id"] == stock_id) & (adjusted_window["trading_date"] == date)]
    if sub.empty:
        return {"exists": False}
    row = sub.iloc[0]
    return {
        "exists": True,
        "open_price": int(row["open_price"]),
        "high_price": int(row["high_price"]),
        "low_price": int(row["low_price"]),
        "close_price": int(row["close_price"]),
    }


def find_issue_link(raw_nonpositive_issues: pd.DataFrame, date: pd.Timestamp) -> dict:
    """issues.parquet 의 RAW_NONPOSITIVE_PRICE_TRADED 이슈와 날짜로만 연결을 시도한다.

    issues.parquet 의 instrument_id 가 이 이슈 코드에서는 전부 비어 있어(mapped=False) 종목 단위 확인이
    불가능하다. affected_scope=DAILY_PRICE_ROW, affected_from<=date<=affected_to 로만 매칭하며, 매칭되어도
    종목이 일치한다는 보장은 없다.
    """
    matches = raw_nonpositive_issues[
        (raw_nonpositive_issues["affected_from"] <= date) & (raw_nonpositive_issues["affected_to"] >= date)
    ]
    if matches.empty:
        return {"linked": False, "note": "NOT_LINKED", "matches": []}
    return {
        "linked": True,
        "note": "날짜만 일치(issues.parquet 의 instrument_id 가 비어 있어 종목 단위 확인 불가)",
        "matches": [
            {
                "affected_from": m["affected_from"].date().isoformat(),
                "affected_to": m["affected_to"].date().isoformat(),
                "decision": m["decision"],
                "details": m["details"],
            }
            for _, m in matches.iterrows()
        ],
    }


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prepared-dir", type=Path, default=DEFAULT_PREPARED_DIR)
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    out_path = args.out or (Path(__file__).resolve().parent / "nonpositive-ohlc-reconciliation.json")

    started = time.time()

    issues, issues_hash = load_issues(args.prepared_dir)
    calendar, calendar_hash = load_calendar(args.prepared_dir)
    status_df, status_hash = load_status(args.tables_dir)

    price_columns = [
        "adjusted",
        "stock_id",
        "stock_code",
        "market",
        "trading_date",
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "trade_volume",
        "trade_amount",
        "source_code",
        "source_record_id",
        "payload_sha256",
    ]
    all_prices, price_hashes, saw_future = load_price_table(args.tables_dir, price_columns)

    raw_prices = all_prices[~all_prices["adjusted"]].reset_index(drop=True)
    adjusted_prices = all_prices[all_prices["adjusted"]].reset_index(drop=True)

    raw_window = raw_prices[raw_prices["trading_date"] < CUTOFF].copy()
    adjusted_window = adjusted_prices[adjusted_prices["trading_date"] < CUTOFF].copy()

    # ---- 대상 행: 원가 OHLC 중 하나라도 <= 0 ----
    nonpositive_mask = (raw_window[OHLC_COLS] <= 0).any(axis=1)
    bad = raw_window[nonpositive_mask].copy()
    bad["ohlc_pattern"] = build_ohlc_pattern(bad)

    # ---- 거래상태와 대조해 분류 ----
    halted_pairs = set(
        zip(
            status_df.loc[status_df["daily_state"].isin(["HALTED", "NO_BAR_HALTED"]), "stock_id"],
            status_df.loc[status_df["daily_state"].isin(["HALTED", "NO_BAR_HALTED"]), "trading_date"],
        )
    )
    partial_pairs = set(
        zip(
            status_df.loc[status_df["daily_state"] == "PARTIAL_TRADING", "stock_id"],
            status_df.loc[status_df["daily_state"] == "PARTIAL_TRADING", "trading_date"],
        )
    )
    bad["classification"] = classify_rows(bad, halted_pairs, partial_pairs)
    bad["volume_bucket"] = bad["trade_volume"].map(lambda v: "ZERO" if v == 0 else "POSITIVE")
    bad["year"] = bad["trading_date"].dt.year.astype(str)

    classification_counts = {k: int(v) for k, v in bad["classification"].value_counts().items()}

    # ---- 캘린더상 휴장일에 걸린 행 ----
    open_dates = set(calendar["date"])
    bad["is_holiday"] = ~bad["trading_date"].isin(open_dates)
    holiday_total = int(bad["is_holiday"].sum())
    holiday_by_class = {k: int(v) for k, v in bad.loc[bad["is_holiday"], "classification"].value_counts().items()}

    # ---- 반대 방향: 상태 테이블 292행 중 원가 OHLC<=0 행과 짝이 맞는지 ----
    raw_pairs_all = set(zip(raw_window["stock_id"], raw_window["trading_date"]))
    raw_pairs_nonpositive = set(zip(bad["stock_id"], bad["trading_date"]))

    def _reverse_category(row: pd.Series) -> str:
        key = (row["stock_id"], row["trading_date"])
        if key in raw_pairs_nonpositive:
            return "MATCHED_NONPOSITIVE_RAW_ROW"
        if key in raw_pairs_all:
            return "RAW_ROW_EXISTS_BUT_POSITIVE"
        return "NO_RAW_ROW"

    status_df["reverse_match"] = status_df.apply(_reverse_category, axis=1)
    reverse_counts = {k: int(v) for k, v in status_df["reverse_match"].value_counts().items()}
    reverse_by_state = nested_counts(status_df, "daily_state", "reverse_match")

    # ---- UNEXPLAINED 행 상세 ----
    raw_window_sorted = raw_window.sort_values(["stock_id", "trading_date"]).reset_index(drop=True)
    raw_nonpositive_issues = issues[
        (issues["issue_code"] == RAW_NONPOSITIVE_ISSUE_CODE) & (issues["affected_scope"] == "DAILY_PRICE_ROW")
    ]

    unexplained_rows = []
    for _, row in bad.loc[bad["classification"] == UNEXPLAINED].sort_values(["trading_date", "stock_id"]).iterrows():
        prev_row, next_row = neighbor_rows(raw_window_sorted, row["stock_id"], row["trading_date"])
        unexplained_rows.append(
            {
                "stock_id": int(row["stock_id"]),
                "stock_code": row["stock_code"],
                "market": row["market"],
                "trading_date": row["trading_date"].date().isoformat(),
                "open_price": int(row["open_price"]),
                "high_price": int(row["high_price"]),
                "low_price": int(row["low_price"]),
                "close_price": int(row["close_price"]),
                "trade_volume": int(row["trade_volume"]),
                "trade_amount": int(row["trade_amount"]),
                "ohlc_pattern": row["ohlc_pattern"],
                "source_code": row["source_code"],
                "source_record_id": int(row["source_record_id"]),
                "payload_sha256": row["payload_sha256"],
                "prev_raw_row": prev_row,
                "next_raw_row": next_row,
                "same_day_adjusted_row": same_day_adjusted(adjusted_window, row["stock_id"], row["trading_date"]),
                "issue_link": find_issue_link(raw_nonpositive_issues, row["trading_date"]),
            }
        )

    result = {
        "admission_status": "READ_ONLY_DIAGNOSTIC_NOT_ADMITTED",
        "note": "이 결과는 백테스트 실행이나 전략 승인의 근거가 아니다. B1 진단(universe_diagnosis.py 의 "
        "analyze_nonpositive_ohlc, 거래량0 만으로 판정: 원가 OHLC<=0 135,717건 / 거래량0 135,699건 / "
        "거래량>0 18건)을 거래상태 테이블로 정밀화한 것이다.",
        "generated_at": pd.Timestamp.now().isoformat(),
        "runtime_seconds": None,
        "date_cutoff": {
            "cutoff": CUTOFF.date().isoformat(),
            "saw_rows_on_or_after_cutoff": bool(saw_future),
            "note": "파일 자체는 날짜로 사전 필터링하지 않고 전부 읽었다. 컷오프 이후 행이 있었다면 "
            "saw_rows_on_or_after_cutoff 가 true 이며, 모든 집계·목록은 그런 행을 제외했다.",
        },
        "input_sha256": {
            **issues_hash,
            **calendar_hash,
            **status_hash,
            "price_parquet_files": price_hashes,
        },
        "summary": {
            "total_nonpositive_rows_examined": int(len(bad)),
            "classification_counts": classification_counts,
            "classification_x_volume_bucket": nested_counts(bad, "classification", "volume_bucket"),
            "classification_x_ohlc_pattern": nested_counts(bad, "classification", "ohlc_pattern"),
            "ohlc_pattern_totals": {k: int(v) for k, v in bad["ohlc_pattern"].value_counts().items()},
            "holiday_rows": {
                "total": holiday_total,
                "by_classification": holiday_by_class,
                "note": "calendar.parquet 는 개장일만 나열하므로(is_open 컬럼 없음), 그 목록에 없는 날짜를 "
                "휴장일로 판정했다.",
            },
            "reverse_status_match": {
                "total_status_rows": int(len(status_df)),
                "counts": reverse_counts,
                "by_daily_state": reverse_by_state,
            },
            "classification_x_year": nested_counts(bad, "classification", "year"),
            "classification_x_market": nested_counts(bad, "classification", "market"),
        },
        "unexplained_rows": unexplained_rows,
    }
    result["runtime_seconds"] = round(time.time() - started, 1)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} in {result['runtime_seconds']}s")


if __name__ == "__main__":
    main()
