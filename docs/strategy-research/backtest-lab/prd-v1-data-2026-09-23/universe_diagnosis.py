"""PRD §5.3 Universe 정책과 준비된 v3 입력(cohort) 사이의 공백을 읽기 전용으로 진단하는 스크립트.

이 스크립트는 다음을 절대 하지 않는다.
  - 수익률 계산이나 백테스트 실행 (research/krx_lab 의 시뮬레이션 경로를 호출하지 않는다)
  - `../vectorbt-data/` 아래 기존 파일 쓰기/수정 (전부 읽기 전용으로 연다)
  - PostgreSQL·네트워크 접속

2024-01-01 이후 가격 행은 파일에서 걸러 읽지 않는다(날짜로 사전 필터링하지 않는다). 대신 읽은 뒤
집계 직전에 제외하고, 그런 행이 있었는지를 결과 JSON의 `date_cutoff` 에 기록한다.

사용법:
    .venv/Scripts/python.exe -X utf8 universe_diagnosis.py \
        --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
        --tables-dir ../vectorbt-data/krx-v3-20260921-tables \
        --out universe-diagnosis.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import pandas as pd

DEFAULT_PREPARED_DIR = Path(
    "C:/Users/aeby/vscode/stock/vectorbt-data/krx-v3-20260921-prepared-r2"
)
DEFAULT_TABLES_DIR = Path(
    "C:/Users/aeby/vscode/stock/vectorbt-data/krx-v3-20260921-tables"
)

# 이 컷오프 이후 가격은 집계에 쓰지 않는다. 파일 자체는 걸러 읽지 않고 전체를 읽은 뒤 잘라낸다.
CUTOFF = pd.Timestamp("2024-01-01")

# issue_code -> (분류, 설명). 분류는 데이터 결함 / 이전 전략 자격 / 정책 제외 중 하나다.
# 근거: docs/strategy-research/backtest-lab/postgresql-readiness-2026-09-21/README.md 의 인수 이슈
# 서술과 research/krx_lab/v3_inputs.py 의 _SIGNAL_BLOCK_DECISIONS / signal_blocking 예외 목록
# (WARMUP_250_BARS_SHORT, POINT_IN_TIME_SECTOR_UNAVAILABLE 는 신호 차단에서 명시적으로 제외됨).
ISSUE_CATEGORY = {
    "ADJUSTED_PRICE_UNAVAILABLE": "데이터_결함",
    "CORPORATE_ACTION_PARTIAL": "데이터_결함",
    "UNEXPLAINED_VENDOR_FACTOR": "데이터_결함",
    "ADJUSTED_OHLC_ORDER_VIOLATION": "데이터_결함",
    "RAW_NONPOSITIVE_PRICE_TRADED": "데이터_결함",
    "ADJUSTED_NONPOSITIVE_PRICE_TRADED": "데이터_결함",
    "WARMUP_250_BARS_SHORT": "이전_전략_자격",
    "POINT_IN_TIME_SECTOR_UNAVAILABLE": "정책_제외",
}
# 사유가 여럿인 종목의 1차 사유를 고를 때 쓰는 우선순위(엄격한 REJECT 계열을 먼저, 그다음 WARNING 계열).
PRIMARY_REASON_PRIORITY = [
    "ADJUSTED_PRICE_UNAVAILABLE",
    "CORPORATE_ACTION_PARTIAL",
    "ADJUSTED_OHLC_ORDER_VIOLATION",
    "RAW_NONPOSITIVE_PRICE_TRADED",
    "ADJUSTED_NONPOSITIVE_PRICE_TRADED",
    "UNEXPLAINED_VENDOR_FACTOR",
    "WARMUP_250_BARS_SHORT",
    "POINT_IN_TIME_SECTOR_UNAVAILABLE",
]
NO_RECORD_REASON = "NO_ADMISSION_ISSUE_RECORD"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# 입력 로딩
# ---------------------------------------------------------------------------


def load_price_table(tables_dir: Path, columns: list[str]) -> tuple[pd.DataFrame, dict, bool]:
    """모든 price-*.parquet 를 지정한 컬럼만 이어붙여 읽는다.

    날짜로 사전 필터링하지 않는다(브리프 제약). 컷오프 이후 행이 있었는지만 반환한다.
    """
    files = sorted(tables_dir.glob("price-*.parquet"))
    if not files:
        raise FileNotFoundError(f"NO_PRICE_FILES: {tables_dir}")
    frames = []
    hashes = {}
    saw_future = False
    for fp in files:
        df = pd.read_parquet(fp, columns=columns)
        hashes[fp.name] = sha256_file(fp)
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    raw["trading_date"] = pd.to_datetime(raw["trading_date"])
    if (raw["trading_date"] >= CUTOFF).any():
        saw_future = True
    return raw, hashes, saw_future


def load_cohort(prepared_dir: Path) -> tuple[set[int], dict]:
    fp = prepared_dir / "cohort.json"
    payload = json.loads(fp.read_text(encoding="utf-8"))
    ids = {int(x) for x in payload["instrument_ids"]}
    return ids, {"cohort.json": sha256_file(fp)}


def load_issues(prepared_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = prepared_dir / "issues.parquet"
    df = pd.read_parquet(fp)
    return df, {"issues.parquet": sha256_file(fp)}


def load_calendar(prepared_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = prepared_dir / "calendar.parquet"
    df = pd.read_parquet(fp)
    df["date"] = pd.to_datetime(df["date"])
    return df, {"calendar.parquet": sha256_file(fp)}


# ---------------------------------------------------------------------------
# Q1. cohort 에서 빠진 종목의 사유 분해
# ---------------------------------------------------------------------------


def analyze_gap(raw_ids: set[int], adjusted_ids: set[int], cohort_ids: set[int], issues: pd.DataFrame) -> dict:
    missing_from_raw = raw_ids - cohort_ids
    missing_from_adjusted = adjusted_ids - cohort_ids

    issues = issues.copy()
    issues["instrument_id_int"] = pd.to_numeric(issues["instrument_id"], errors="coerce")
    mapped_issues = issues.dropna(subset=["instrument_id_int"]).copy()
    mapped_issues["instrument_id_int"] = mapped_issues["instrument_id_int"].astype(int)

    missing_issues = mapped_issues[mapped_issues["instrument_id_int"].isin(missing_from_raw)]

    # 이슈 테이블 전체의 issue_code 중 instrument_id 로 매핑되지 않는 것들(affected_scope 가
    # "stock:<code>" 형식이 아닌 것). 이런 사유는 특정 종목에 귀속시킬 수 없으므로
    # reason_counts_all_occurrences/primary_reason_counts 에 나타나지 않는다 — 과소집계 경고.
    unmapped = issues[issues["instrument_id_int"].isna()]
    unmapped_reason_counts = {
        str(k): int(v) for k, v in unmapped["issue_code"].value_counts().to_dict().items()
    }
    unmapped_scope_examples = {
        str(code): sorted(grp["affected_scope"].astype(str).unique().tolist())[:3]
        for code, grp in unmapped.groupby("issue_code")
    }

    # 중복 허용 집계 (한 종목의 사유가 여럿이면 전부 센다)
    reason_counts_all_occurrences = {
        str(k): int(v) for k, v in missing_issues["issue_code"].value_counts().to_dict().items()
    }
    # 종목 단위(사유 유무와 무관하게, 이슈가 있는 종목이 그 사유를 "가진다"는 의미의 중복 허용)
    codes_per_reason = {
        str(k): int(v)
        for k, v in missing_issues.groupby("issue_code")["instrument_id_int"].nunique().to_dict().items()
    }

    # 1차 사유: 종목별로 PRIMARY_REASON_PRIORITY 순서에서 가장 먼저 걸리는 사유. 이슈 기록이 전혀
    # 없는 종목은 NO_ADMISSION_ISSUE_RECORD 로 분류한다(비보통주 등 정책 필터로 추정되나 오프라인
    # 테이블에는 security_type 이 없어 직접 확인할 수 없다 — Q3 참고).
    issues_by_instrument: dict[int, set[str]] = {}
    for iid, grp in missing_issues.groupby("instrument_id_int"):
        issues_by_instrument[int(iid)] = set(grp["issue_code"].astype(str).unique())

    primary_reason_counts: dict[str, int] = {}
    primary_category_counts: dict[str, int] = {}
    unrecorded_examples = []
    for iid in sorted(missing_from_raw):
        codes_here = issues_by_instrument.get(iid, set())
        primary = next((r for r in PRIMARY_REASON_PRIORITY if r in codes_here), None)
        if primary is None:
            primary = NO_RECORD_REASON
            if len(unrecorded_examples) < 20:
                unrecorded_examples.append(iid)
        primary_reason_counts[primary] = primary_reason_counts.get(primary, 0) + 1
        category = ISSUE_CATEGORY.get(primary, "정책_제외_추정_미확인")
        primary_category_counts[category] = primary_category_counts.get(category, 0) + 1

    return {
        "note": (
            "denominator 는 원가 기준 전체 종목(raw_population, 2,787종목 근방)이며, cohort 에 없는 "
            "종목을 '빠진 종목' 으로 본다. missing_from_adjusted_population 은 수정가 기준 전체 종목을 "
            "분모로 한 참고치다. reason_counts_all_occurrences 는 종목 1개가 사유를 여러 개 가지면 "
            "모두 센 중복 허용 집계이고, primary_reason_counts 는 종목당 하나의 1차 사유만 센 집계다. "
            "⚠ issues.parquet 2,304행 중 instrument_id 로 매핑된 것은 781행(ADJUSTED_PRICE_UNAVAILABLE "
            "475 + WARMUP_250_BARS_SHORT 306)뿐이다. 나머지 1,523행(UNEXPLAINED_VENDOR_FACTOR 1,061 · "
            "ADJUSTED_OHLC_ORDER_VIOLATION 284 · CORPORATE_ACTION_PARTIAL 160 · "
            "RAW_NONPOSITIVE_PRICE_TRADED 13 · ADJUSTED_NONPOSITIVE_PRICE_TRADED 4 · "
            "POINT_IN_TIME_SECTOR_UNAVAILABLE 1)은 affected_scope 가 'stock:<code>' 형식이 아니어서 "
            "(예: PRICE_SERIES_AT_DATE, DAILY_PRICE_ROW, POSITION_ON_EVENT_DATE) 특정 종목에 귀속시킬 수 "
            "없다. 즉 이 5~6개 사유는 실제로 특정 종목의 cohort 제외에 기여했을 수 있지만 이 데이터로는 "
            "어느 종목인지 확인할 수 없고, 아래 NO_ADMISSION_ISSUE_RECORD 1차 사유(1,184종목)에 그런 "
            "진짜 원인이 섞여 들어가 있을 가능성이 있다. unmapped_reason_counts 를 참고하라."
        ),
        "unmapped_reason_counts_system_wide": unmapped_reason_counts,
        "unmapped_affected_scope_examples": unmapped_scope_examples,
        "raw_population_stock_count": len(raw_ids),
        "adjusted_population_stock_count": len(adjusted_ids),
        "cohort_stock_count": len(cohort_ids),
        "missing_from_raw_population_count": len(missing_from_raw),
        "missing_from_adjusted_population_count": len(missing_from_adjusted),
        "reason_counts_all_occurrences": reason_counts_all_occurrences,
        "codes_per_reason_dedup": codes_per_reason,
        "primary_reason_counts": primary_reason_counts,
        "primary_category_counts": primary_category_counts,
        "category_definition": {
            "데이터_결함": "ADJUSTED_PRICE_UNAVAILABLE, CORPORATE_ACTION_PARTIAL, UNEXPLAINED_VENDOR_FACTOR, "
            "ADJUSTED_OHLC_ORDER_VIOLATION, RAW_NONPOSITIVE_PRICE_TRADED, ADJUSTED_NONPOSITIVE_PRICE_TRADED",
            "이전_전략_자격": "WARMUP_250_BARS_SHORT — PRD 는 상장 후 120거래일만 요구하므로 이 사유의 "
            "종목은 데이터 결함이 아니라 이전(구) 전략의 250봉 자격 조건 때문에 빠졌을 수 있다.",
            "정책_제외": "POINT_IN_TIME_SECTOR_UNAVAILABLE",
            "정책_제외_추정_미확인": "이슈 기록이 전혀 없는 종목(NO_ADMISSION_ISSUE_RECORD). 비보통주 "
            "필터(ETF/우선주 등) 또는 평가 구간 밖 상장/상장폐지 때문으로 추정되나, security_type 필드가 "
            "오프라인 테이블에 없어 확인할 수 없다.",
        },
        "no_record_example_instrument_ids_top20": unrecorded_examples,
    }


# ---------------------------------------------------------------------------
# Q2. PRD 기준 일별 Universe 크기 — 실현 가능성 진단 + 한계가 명시된 근사치
# ---------------------------------------------------------------------------


def analyze_universe_feasibility(raw_prices: pd.DataFrame, cohort_ids: set[int], calendar: pd.DataFrame) -> dict:
    feasible = {
        "prd_required_fields": [
            "security_type (보통주 여부)",
            "listing_date (상장 후 120거래일 계산용, 2014년 이전 상장 이력 포함)",
            "delisting_flag_or_date (상장폐지 종목을 사후 제거하지 않기 위한 식별)",
            "daily_trading_status (거래정지 등, 가격 전진 채움 방지)",
        ],
        "available_offline": {
            "security_type": False,
            "listing_date": False,
            "delisting_flag_or_date": False,
            "daily_trading_status": False,
        },
        "evidence": (
            "research/krx_lab/v3_inputs.py 의 _REQUIRED['UNIVERSE'] 는 security_type·valid_from·valid_to 를 "
            "요구하고, v3_snapshot.py 는 이를 PostgreSQL 뷰 backtest_universe_v2 에서 가져온다(security_type="
            "'COMMON_STOCK' AND valid_from<=... AND valid_to>=...). 이번 진단은 PostgreSQL 접속이 금지되어 "
            "있고, ../vectorbt-data/ 아래 오프라인 parquet 테이블(identifier/price/adjustment/corporate_action/"
            "admission_issue/execution_rule/benchmark/calendar)에는 UNIVERSE·STATUS 테이블이 없다. 상장일도 "
            "2014-01-01 이전 이력이 없어 이 창에서의 '첫 관측일'을 상장일로 쓰면 2014년 이전 상장 종목의 "
            "120거래일 조건이 왜곡된다."
        ),
        "conclusion": "PRD 기준(보통주·상장120거래일·상폐 포함) Universe 크기는 오프라인 데이터만으로 계산할 "
        "수 없다. 아래 proxy_daily_universe 는 그 한계를 명시한 근사치이며 PRD 준수 수치가 아니다.",
    }

    raw = raw_prices.copy()
    raw = raw[raw["trading_date"] < CUTOFF]
    raw = raw.drop_duplicates(["stock_id", "trading_date"])
    raw["in_cohort"] = raw["stock_id"].isin(cohort_ids)
    raw["year"] = raw["trading_date"].dt.year

    daily_total = raw.groupby("trading_date")["stock_id"].nunique()
    daily_cohort = raw[raw["in_cohort"]].groupby("trading_date")["stock_id"].nunique()
    daily_excluded = (daily_total - daily_cohort.reindex(daily_total.index, fill_value=0)).rename("excluded")

    by_year_total = daily_total.groupby(daily_total.index.year).mean()
    by_year_cohort = daily_cohort.reindex(daily_total.index, fill_value=0).groupby(daily_total.index.year).mean()
    by_year_excluded = daily_excluded.groupby(daily_excluded.index.year).mean()

    proxy = {
        "definition": "각 거래일에 원가(unadjusted) 가격 행이 있는 distinct stock_id 수를 '그날 관측된 종목' "
        "으로 삼은 근사치. security_type 필터(비보통주 포함) 와 120거래일 신규상장 자격을 적용하지 못했고, "
        "상장폐지 종목은 자연히 마지막 거래일 이후 사라지므로 '사후 제거 금지' 요건은 이 근사치에서 우연히 "
        "충족된다.",
        "mean_stock_count_by_year_total_proxy": {int(k): round(float(v), 1) for k, v in by_year_total.items()},
        "mean_stock_count_by_year_in_cohort": {int(k): round(float(v), 1) for k, v in by_year_cohort.items()},
        "mean_stock_count_by_year_excluded_from_cohort": {
            int(k): round(float(v), 1) for k, v in by_year_excluded.items()
        },
        "calendar_days_used": int(len(calendar)),
        "calendar_date_range": [
            calendar["date"].min().date().isoformat(),
            calendar["date"].max().date().isoformat(),
        ],
    }

    return {"feasibility": feasible, "proxy_daily_universe": proxy}


# ---------------------------------------------------------------------------
# Q3. 증권 종류 구분 필드
# ---------------------------------------------------------------------------


def analyze_security_type_field(tables_dir: Path) -> dict:
    return {
        "field_found_in_offline_tables": False,
        "checked_tables": sorted(
            {fp.name.rsplit("-", 1)[0] for fp in tables_dir.glob("*.parquet")}
        ),
        "note": "identifier/price/adjustment/corporate_action/admission_issue/execution_rule/benchmark/"
        "calendar 8종 오프라인 parquet 테이블 어디에도 ETF·ETN·우선주·스팩·리츠를 구분하는 필드가 없다. "
        "research/krx_lab/v3_inputs.py:23,133 과 v3_snapshot.py:27 은 'security_type' 필드(값 예: "
        "COMMON_STOCK)를 PostgreSQL 뷰 backtest_universe_v2 에서만 읽으며, 그 값 분포는 이번 진단(PG 접속 "
        "금지)에서 확인할 수 없다.",
        "field_name_if_available_online": "security_type (PostgreSQL backtest_universe_v2 뷰, 예: "
        "'COMMON_STOCK'; 다른 값의 존재·분포는 미확인)",
    }


# ---------------------------------------------------------------------------
# Q4. 상장폐지 종목 수 (직접 플래그 없음 — 근사치)
# ---------------------------------------------------------------------------


def analyze_delisting_proxy(raw_prices: pd.DataFrame) -> dict:
    raw = raw_prices[raw_prices["trading_date"] < CUTOFF]
    last_seen = raw.groupby("stock_id")["trading_date"].max()
    calendar_end = raw["trading_date"].max()
    # 계산 기간 마지막 거래일 이전 60거래일(대략 3개월)보다 먼저 마지막 인쇄가 끊긴 종목을 근사 상장폐지로 본다.
    threshold = calendar_end - pd.Timedelta(days=90)
    proxy_delisted = last_seen[last_seen < threshold]
    return {
        "field_found": False,
        "note": "오프라인 테이블(price/identifier/corporate_action 등)에 상장폐지 플래그나 사유 코드가 "
        "없다. corporate_action.event_type 값도 LISTED_SHARE_CHANGE/RIGHTS_OFF/DIVIDEND_OFF/"
        "CAPITAL_REDUCTION/SPLIT/PAID_CAPITAL_INCREASE/UNKNOWN_QUANTITY_TRANSFORM/REVERSE_SPLIT 뿐이고 "
        "상장폐지 이벤트 타입이 없다. 아래는 '계산기간 마지막 거래일에서 90일 이상 앞서 마지막 원가 가격 "
        "행이 끊긴 종목 수'를 상장폐지의 근사치로 쓴 것이며, 데이터 수집 절단과 실제 상장폐지를 구분하지 "
        "못한다.",
        "proxy_last_print_gt_90d_before_dataset_end_count": int(len(proxy_delisted)),
        "dataset_end_date": calendar_end.date().isoformat(),
    }


# ---------------------------------------------------------------------------
# Q5. 원가 OHLC<=0 135,717행의 설명 가능/불가능 분해
# ---------------------------------------------------------------------------


def analyze_nonpositive_ohlc(raw_prices: pd.DataFrame) -> dict:
    raw = raw_prices[raw_prices["trading_date"] < CUTOFF].copy()
    ohlc = ["open_price", "high_price", "low_price", "close_price"]
    nonpositive_mask = (raw[ohlc] <= 0).any(axis=1)
    bad = raw[nonpositive_mask]
    explained_by_zero_volume = bad[bad["trade_volume"] == 0]
    unexplained = bad[bad["trade_volume"] > 0]
    return {
        "note": "거래상태(정지 등) 필드가 오프라인 price 테이블에 없으므로 '거래상태로 설명됨' 은 거래량 "
        "0 인 행만으로 판정했다(정지일이 거래량>0 을 남길 가능성은 배제하지 않았다). "
        "docs/strategy-research/backtest-lab/postgresql-readiness-2026-09-21/README.md 는 PostgreSQL 소비 "
        "view 에서 같은 방식으로 원가 OHLC<=0 135,717건, 거래량0 135,699건, 거래량>0 인데 OHLC<=0 18건을 "
        "보고했다(이번 진단은 오프라인 parquet 로 독립 재현).",
        "total_rows_examined": int(len(raw)),
        "nonpositive_ohlc_rows": int(nonpositive_mask.sum()),
        "explained_by_zero_trade_volume": int(len(explained_by_zero_volume)),
        "unexplained_positive_volume": int(len(unexplained)),
        "unexplained_example_stock_ids_top20": sorted(unexplained["stock_id"].unique().tolist())[:20],
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

    out_path = args.out or (Path(__file__).resolve().parent / "universe-diagnosis.json")

    started = time.time()

    cohort_ids, cohort_hash = load_cohort(args.prepared_dir)
    issues, issues_hash = load_issues(args.prepared_dir)
    calendar, calendar_hash = load_calendar(args.prepared_dir)

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
    ]
    all_prices, price_hashes, saw_future = load_price_table(args.tables_dir, price_columns)

    raw_prices = all_prices[~all_prices["adjusted"]].reset_index(drop=True)
    adjusted_prices = all_prices[all_prices["adjusted"]].reset_index(drop=True)
    raw_prices_in_window = raw_prices[raw_prices["trading_date"] < CUTOFF]
    adjusted_prices_in_window = adjusted_prices[adjusted_prices["trading_date"] < CUTOFF]

    raw_ids = set(raw_prices_in_window["stock_id"].unique().tolist())
    adjusted_ids = set(adjusted_prices_in_window["stock_id"].unique().tolist())

    gap_result = analyze_gap(raw_ids, adjusted_ids, cohort_ids, issues)
    universe_result = analyze_universe_feasibility(raw_prices_in_window, cohort_ids, calendar)
    security_type_result = analyze_security_type_field(args.tables_dir)
    delisting_result = analyze_delisting_proxy(raw_prices)
    nonpositive_result = analyze_nonpositive_ohlc(raw_prices)

    result = {
        "admission_status": "READ_ONLY_DIAGNOSTIC_NOT_ADMITTED",
        "note": "이 결과는 백테스트 실행이나 전략 승인의 근거가 아니다. Universe 정책 공백을 진단한 것이다.",
        "generated_at": pd.Timestamp.now().isoformat(),
        "runtime_seconds": None,
        "date_cutoff": {
            "cutoff": CUTOFF.date().isoformat(),
            "saw_rows_on_or_after_cutoff": bool(saw_future),
            "note": "파일 자체는 날짜로 사전 필터링하지 않고 전부 읽었다. 컷오프 이후 행이 있었다면 "
            "saw_rows_on_or_after_cutoff 가 true 이며, 모든 집계는 그런 행을 제외했다.",
        },
        "input_sha256": {
            **cohort_hash,
            **issues_hash,
            **calendar_hash,
            "price_parquet_files": price_hashes,
        },
        "q1_cohort_gap_by_reason": gap_result,
        "q2_prd_universe_size": universe_result,
        "q3_security_type_field": security_type_result,
        "q4_delisted_count_proxy": delisting_result,
        "q5_nonpositive_ohlc_breakdown": nonpositive_result,
    }
    result["runtime_seconds"] = round(time.time() - started, 1)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} in {result['runtime_seconds']}s")


if __name__ == "__main__":
    main()
