"""PostgreSQL 상장·폐지·거래정지 원천을 읽기 전용으로 추출해 로컬 자료와 대조하는 B1b 스크립트.

두 단계로 나뉜다.
  - extract: `kiwoom.stock`·`kiwoom.instrument_history`·`kiwoom.market_status_event`·
    `kiwoom.trading_halt` 를 `kiwoom.universe_membership_history` 의 distinct stock_id
    (2,787개) 범위로, 단일 `BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY ... ROLLBACK`
    트랜잭션 안에서 COPY 로 추출해 `--extract-dir` 에 Parquet + manifest.json 을 쓴다.
    커밋은 한 번도 실행하지 않는다. 쿼리는 고정 문자열이며 외부 입력을 끼워 넣지 않는다.
  - analyze: extract 결과와 `universe_diagnosis.py`/`nonpositive_ohlc_reconciliation.py` 가
    쓰는 로컬 자료(prepared-dir·tables-dir)를 대조해 `listing-halt-reconciliation.json` 을 쓴다.

이 스크립트는 다음을 절대 하지 않는다.
  - PostgreSQL 에 쓰기(모든 SQL 은 SELECT/COPY 뿐이고 트랜잭션은 항상 ROLLBACK 으로 끝난다)
  - `../vectorbt-data/` 아래 기존 파일 쓰기/수정(새 디렉터리에만 쓴다)
  - 이상값 삭제·보정(분류하고 센다)

2024-01-01 잠금: 모든 추출 쿼리는 행 기준으로 2023-12-31 이하로 제한한다(`effective_date`·
`halt_date` 등). 개별 컬럼이 이 범위를 벗어나면(`delisted_date`·`last_trade_date`·`resume_date`·
`official_delist_date`·`announced_at`·`disclosed_at`) SQL CASE 로 NULL 처리하고 `<컬럼>_after_cutoff`
불리언으로만 표시한다. 로컬 가격 Parquet 는 기존 스크립트와 같이 사전 필터링 없이 전부 읽고
`date_cutoff.saw_rows_on_or_after_cutoff` 로 표시한다.

사용법(리포 루트 기준):
    .venv/Scripts/python.exe -X utf8 docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/listing_halt_reconciliation.py \
        --extract-dir ../vectorbt-data/krx-prd-v1-b1b-20260924 \
        --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
        --tables-dir ../vectorbt-data/krx-v3-20260921-tables \
        --out docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/listing-halt-reconciliation.json

`--mode extract`·`--mode analyze` 로 단계를 나눌 수 있다. 인자 없이 실행하면 `--mode both`(기본값)로
두 단계를 순서대로 한다.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

# 같은 디렉터리의 기존 진단 스크립트를 재사용한다(로더·CUTOFF·해시 유틸·B4 분류 로직을 중복 구현하지 않는다).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from universe_diagnosis import (  # noqa: E402
    CUTOFF,
    DEFAULT_PREPARED_DIR,
    DEFAULT_TABLES_DIR,
    PRIMARY_REASON_PRIORITY,
    load_calendar,
    load_cohort,
    load_issues,
    load_price_table,
    sha256_file,
)
from nonpositive_ohlc_reconciliation import (  # noqa: E402
    OHLC_COLS,
    UNEXPLAINED,
    ZERO_VOLUME_NO_STATUS,
    build_ohlc_pattern,
    classify_rows,
    load_status,
)

DEFAULT_EXTRACT_DIR = Path("C:/Users/aeby/vscode/stock/vectorbt-data/krx-prd-v1-b1b-20260924")

# 마지막으로 잠금 없이 다룰 수 있는 날짜. 이 이후 값은 SQL CASE 로 가리고 *_after_cutoff 로만 표시한다.
CUTOFF_DATE_LITERAL = "2023-12-31"
# MSE 정지 구간의 끝을 못 찾을 때(다음 TRADING/DELISTED 가 없을 때) 열어 두는 경계일.
HALT_OPEN_END = pd.Timestamp("2023-12-28")

SSH_COMMAND = [
    "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "home",
    "docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db psql -X -q -U kiwoom -d kiwoom_db",
]

# 대상 종목 범위. 고정 서브쿼리이며 외부 입력을 받지 않는다.
TARGET_SCOPE_SQL = "SELECT DISTINCT stock_id FROM kiwoom.universe_membership_history"

# ---------------------------------------------------------------------------
# 추출 스키마
# ---------------------------------------------------------------------------

KIND_COLUMNS = {
    "STOCK": [
        "stock_id", "stock_code", "market_code", "state", "is_active",
        "listed_date", "listed_date_after_cutoff", "delisted_date", "delisted_date_after_cutoff",
    ],
    "INSTRUMENT_HISTORY": [
        "stock_id", "min_listed_date", "max_listed_date", "distinct_listed_date_count",
        "first_effective_from", "row_count",
    ],
    "INSTRUMENT_HISTORY_EXCLUDED": ["excluded_row_count"],
    "MARKET_STATUS_EVENT": [
        "event_id", "stock_id", "effective_date", "status", "reason",
        "announced_at", "announced_at_after_cutoff", "source_id", "source_url",
        "raw_file_sha256", "capture_kind",
        "last_trade_date", "last_trade_date_after_cutoff",
        "official_delist_date", "official_delist_date_after_cutoff",
    ],
    "TRADING_HALT": [
        "id", "stock_id", "notice_type", "halt_date",
        "resume_date", "resume_date_after_cutoff", "period_text",
        "disclosed_at", "disclosed_at_after_cutoff", "reason", "rule_basis", "source_url",
    ],
}

INT64_COLS = {
    "STOCK": ["stock_id"],
    "INSTRUMENT_HISTORY": ["stock_id"],
    "MARKET_STATUS_EVENT": ["stock_id"],
    "TRADING_HALT": ["id", "stock_id"],
}
NULLABLE_INT_COLS = {
    "INSTRUMENT_HISTORY": ["distinct_listed_date_count", "row_count"],
    "INSTRUMENT_HISTORY_EXCLUDED": ["excluded_row_count"],
    "MARKET_STATUS_EVENT": ["source_id"],
}
DATE_COLS = {
    "STOCK": ["listed_date", "delisted_date"],
    "INSTRUMENT_HISTORY": ["min_listed_date", "max_listed_date", "first_effective_from"],
    "MARKET_STATUS_EVENT": ["effective_date", "last_trade_date", "official_delist_date"],
    "TRADING_HALT": ["halt_date", "resume_date"],
}
TIMESTAMP_COLS = {
    "MARKET_STATUS_EVENT": ["announced_at"],
    "TRADING_HALT": ["disclosed_at"],
}
BOOL_COLS = {
    "STOCK": ["is_active", "listed_date_after_cutoff", "delisted_date_after_cutoff"],
    "MARKET_STATUS_EVENT": [
        "announced_at_after_cutoff", "last_trade_date_after_cutoff", "official_delist_date_after_cutoff",
    ],
    "TRADING_HALT": ["resume_date_after_cutoff", "disclosed_at_after_cutoff"],
}


def build_extract_sql() -> str:
    """고정 SQL 문자열. 서브쿼리(TARGET_SCOPE_SQL)와 날짜 리터럴 외에는 변수를 끼워 넣지 않는다."""
    return rf"""\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='480s';
SET LOCAL lock_timeout='5s';
COPY (
  SELECT 'STOCK', s.id, s.stock_code, s.market_code, s.state, s.is_active,
    CASE WHEN s.listed_date > DATE '{CUTOFF_DATE_LITERAL}' THEN NULL ELSE s.listed_date END,
    COALESCE(s.listed_date > DATE '{CUTOFF_DATE_LITERAL}', FALSE),
    CASE WHEN s.delisted_date > DATE '{CUTOFF_DATE_LITERAL}' THEN NULL ELSE s.delisted_date END,
    COALESCE(s.delisted_date > DATE '{CUTOFF_DATE_LITERAL}', FALSE)
  FROM kiwoom.stock s
  WHERE s.id IN ({TARGET_SCOPE_SQL})
  ORDER BY s.id
) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8', NULL '\N');
COPY (
  SELECT 'INSTRUMENT_HISTORY', stock_id, MIN(listed_date), MAX(listed_date),
    COUNT(DISTINCT listed_date), MIN(effective_from), COUNT(*)
  FROM kiwoom.instrument_history
  WHERE stock_id IN ({TARGET_SCOPE_SQL})
    AND effective_from <= DATE '{CUTOFF_DATE_LITERAL}'
  GROUP BY stock_id ORDER BY stock_id
) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8', NULL '\N');
COPY (
  SELECT 'INSTRUMENT_HISTORY_EXCLUDED', COUNT(*)
  FROM kiwoom.instrument_history
  WHERE stock_id IN ({TARGET_SCOPE_SQL})
    AND effective_from > DATE '{CUTOFF_DATE_LITERAL}'
) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8', NULL '\N');
COPY (
  SELECT 'MARKET_STATUS_EVENT', event_id, stock_id, effective_date, status, reason,
    CASE WHEN announced_at::date > DATE '{CUTOFF_DATE_LITERAL}' THEN NULL ELSE announced_at END,
    COALESCE(announced_at::date > DATE '{CUTOFF_DATE_LITERAL}', FALSE),
    source_id, source_url, raw_file_sha256, capture_kind,
    CASE WHEN last_trade_date > DATE '{CUTOFF_DATE_LITERAL}' THEN NULL ELSE last_trade_date END,
    COALESCE(last_trade_date > DATE '{CUTOFF_DATE_LITERAL}', FALSE),
    CASE WHEN official_delist_date > DATE '{CUTOFF_DATE_LITERAL}' THEN NULL ELSE official_delist_date END,
    COALESCE(official_delist_date > DATE '{CUTOFF_DATE_LITERAL}', FALSE)
  FROM kiwoom.market_status_event
  WHERE stock_id IN ({TARGET_SCOPE_SQL})
    AND effective_date <= DATE '{CUTOFF_DATE_LITERAL}'
  ORDER BY stock_id, effective_date, event_id
) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8', NULL '\N');
COPY (
  SELECT 'TRADING_HALT', id, stock_id, notice_type, halt_date,
    CASE WHEN resume_date > DATE '{CUTOFF_DATE_LITERAL}' THEN NULL ELSE resume_date END,
    COALESCE(resume_date > DATE '{CUTOFF_DATE_LITERAL}', FALSE),
    period_text,
    CASE WHEN disclosed_at::date > DATE '{CUTOFF_DATE_LITERAL}' THEN NULL ELSE disclosed_at END,
    COALESCE(disclosed_at::date > DATE '{CUTOFF_DATE_LITERAL}', FALSE),
    reason, rule_basis, source_url
  FROM kiwoom.trading_halt
  WHERE stock_id IN ({TARGET_SCOPE_SQL})
    AND halt_date <= DATE '{CUTOFF_DATE_LITERAL}'
  ORDER BY stock_id, halt_date, id
) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8', NULL '\N');
COPY (SELECT 'END', 'true') TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8');
ROLLBACK;
"""


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------


def run_extract_sql(sql: str, command=None, timeout: int = 580) -> str:
    """SQL 을 표준입력으로 넘겨 읽기 전용 SSH 세션에서 실행하고 stdout 텍스트를 반환한다."""
    result = subprocess.run(
        command or SSH_COMMAND, input=sql.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"SSH/psql extraction failed (code={result.returncode}): "
            f"{result.stderr.decode('utf-8', errors='replace')[:4000]}"
        )
    return result.stdout.decode("utf-8")


def parse_extract_stream(text: str) -> dict:
    rows_by_kind: dict = {kind: [] for kind in KIND_COLUMNS}
    ended = False
    for row in csv.reader(io.StringIO(text)):
        if not row:
            continue
        if ended:
            raise ValueError("END 마커 이후에 행이 있다")
        kind, rest = row[0], row[1:]
        if kind == "END":
            if rest != ["true"]:
                raise ValueError("잘못된 END 마커")
            ended = True
            continue
        if kind not in KIND_COLUMNS:
            raise ValueError(f"알 수 없는 종류: {kind}")
        rows_by_kind[kind].append(rest)
    if not ended:
        raise ValueError("END 마커가 없다(추출이 중간에 끊겼을 수 있다)")
    return rows_by_kind


def _to_bool(series: pd.Series) -> pd.Series:
    return series.map({"t": True, "f": False}).fillna(False).astype(bool)


def build_frame(kind: str, rows: list) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=KIND_COLUMNS[kind])
    for col in INT64_COLS.get(kind, []):
        df[col] = pd.to_numeric(df[col], errors="raise").astype("int64")
    for col in NULLABLE_INT_COLS.get(kind, []):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in DATE_COLS.get(kind, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in TIMESTAMP_COLS.get(kind, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in BOOL_COLS.get(kind, []):
        df[col] = _to_bool(df[col])
    return df


def extract(out_dir: Path, command=None, timeout: int = 580) -> dict:
    """네 원천을 단일 읽기 전용 트랜잭션으로 추출해 out_dir 에 쓴다. 기존 디렉터리는 덮어쓰지 않는다."""
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"디렉터리가 이미 있고 비어 있지 않다: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    sql = build_extract_sql()
    (out_dir / "extract.sql").write_text(sql, encoding="utf-8")
    generated_at = pd.Timestamp.now().isoformat()

    try:
        stdout_text = run_extract_sql(sql, command=command, timeout=timeout)
        rows_by_kind = parse_extract_stream(stdout_text)

        files = []
        row_counts = {}
        for kind in KIND_COLUMNS:
            frame = build_frame(kind, rows_by_kind[kind])
            filename = f"{kind.lower()}.parquet"
            frame.to_parquet(out_dir / filename, index=False)
            files.append({
                "file": filename, "kind": kind, "rows": len(frame),
                "sha256": sha256_file(out_dir / filename),
            })
            row_counts[kind] = len(frame)

        excluded_rows = rows_by_kind["INSTRUMENT_HISTORY_EXCLUDED"]
        excluded_count = int(excluded_rows[0][0]) if excluded_rows else 0

        manifest = {
            "schema_version": "b1b-extract-1",
            "status": "COMPLETE",
            "source": "REAL",
            "generated_at": generated_at,
            "read_only": True,
            "isolation_level": "REPEATABLE READ READ ONLY",
            "note": "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY 로 시작해 COPY 로만 읽고 ROLLBACK 으로 "
                    "끝난다. COMMIT 은 한 번도 실행하지 않는다.",
            "target_stock_id_source": f"kiwoom.universe_membership_history distinct stock_id ({TARGET_SCOPE_SQL})",
            "date_cutoff": CUTOFF_DATE_LITERAL,
            "sql_file": "extract.sql",
            "sql_sha256": sha256_file(out_dir / "extract.sql"),
            "files": files,
            "row_counts": row_counts,
            "instrument_history_excluded_after_cutoff_row_count": excluded_count,
        }
        (out_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return manifest
    except Exception as exc:
        error_manifest = {
            "schema_version": "b1b-extract-1", "status": "FAILED",
            "generated_at": generated_at, "error": f"{type(exc).__name__}: {exc}",
        }
        (out_dir / "manifest.json").write_text(
            json.dumps(error_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        raise


def load_extracted(extract_dir: Path):
    extract_dir = Path(extract_dir)
    manifest = json.loads((extract_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPLETE":
        raise ValueError(f"추출이 완료되지 않았다: {manifest.get('status')}")
    frames = {}
    hashes = {}
    for entry in manifest["files"]:
        fp = extract_dir / entry["file"]
        actual_hash = sha256_file(fp)
        if actual_hash != entry["sha256"]:
            raise ValueError(f"파일 해시 불일치: {entry['file']}")
        frames[entry["kind"]] = pd.read_parquet(fp)
        hashes[entry["file"]] = actual_hash
    return frames, manifest, hashes


# ---------------------------------------------------------------------------
# 정지 구간 구성 · 대조
# ---------------------------------------------------------------------------


def build_mse_halt_intervals(mse_df: pd.DataFrame, open_dates: np.ndarray) -> pd.DataFrame:
    """HALTED 다음 TRADING/DELISTED 전날(개장일 기준)까지를 정지 구간으로 만든다.

    끝을 못 찾으면(그 뒤로 TRADING/DELISTED 가 없으면) HALT_OPEN_END 까지 열어 둔다.
    """
    df = mse_df.sort_values(["stock_id", "effective_date"]).reset_index(drop=True)
    intervals = []
    for stock_id, grp in df.groupby("stock_id"):
        grp = grp.reset_index(drop=True)
        for i in grp.index[grp["status"] == "HALTED"]:
            row = grp.loc[i]
            tail = grp.loc[i + 1:]
            resolving = tail[tail["status"].isin(["TRADING", "DELISTED"])]
            if len(resolving):
                boundary = resolving.iloc[0]["effective_date"]
                pos = int(np.searchsorted(open_dates, np.datetime64(boundary), side="left")) - 1
                day_before = pd.Timestamp(open_dates[pos]) if pos >= 0 else row["effective_date"]
                # KIND 공시는 같은 날 HALTED·TRADING 을 함께 내는 경우가 흔하다(당일 정지 후 재개).
                # 그런 경우 "전날"이 시작일보다 앞서 구간이 비므로, 시작일 자체는 항상 포함시킨다.
                end_date = max(day_before, row["effective_date"])
                open_ended = False
            else:
                end_date = HALT_OPEN_END
                open_ended = True
            intervals.append({
                "stock_id": stock_id, "start_date": row["effective_date"],
                "end_date": end_date, "open_ended": open_ended, "reason": row["reason"],
            })
    return pd.DataFrame(intervals, columns=["stock_id", "start_date", "end_date", "open_ended", "reason"])


def build_trading_halt_intervals(th_df: pd.DataFrame) -> pd.DataFrame:
    """halt_date~resume_date 전날(달력일)을 구간으로 만든다. resume_date 가 없으면 halt_date 하루만 쓴다."""
    halt_rows = th_df[th_df["notice_type"] == "HALT"].copy()
    resume_known = halt_rows["resume_date"].notna()
    halt_rows["end_date"] = halt_rows["halt_date"]
    halt_rows.loc[resume_known, "end_date"] = halt_rows.loc[resume_known, "resume_date"] - pd.Timedelta(days=1)
    halt_rows = halt_rows.rename(columns={"halt_date": "start_date"})
    halt_rows["confirmed_range"] = resume_known
    return halt_rows[["stock_id", "start_date", "end_date", "confirmed_range"]]


def match_intervals(rows: pd.DataFrame, intervals: pd.DataFrame, date_col: str = "trading_date",
                     extra_cols: list | None = None) -> pd.DataFrame:
    """rows 의 (stock_id, date_col) 이 종목별 구간(start_date~end_date) 안에 있는지와, 맞은 구간의
    extra_cols(예: open_ended)를 함께 반환한다. 맞지 않으면 extra_cols 는 NaN."""
    extra_cols = extra_cols or []
    if intervals.empty or rows.empty:
        out = pd.DataFrame(index=rows.index)
        out["hit"] = False
        for col in extra_cols:
            out[col] = pd.NA
        return out
    # merge_asof 는 by 와 무관하게 on 컬럼 자체가 전역적으로 정렬돼 있어야 한다.
    left = rows[["stock_id", date_col]].reset_index().rename(columns={"index": "_orig_index"})
    left = left.sort_values(date_col)
    right = intervals[["stock_id", "start_date", "end_date"] + extra_cols].sort_values("start_date")
    merged = pd.merge_asof(left, right, left_on=date_col, right_on="start_date", by="stock_id", direction="backward")
    hit = merged["end_date"].notna() & (merged[date_col] <= merged["end_date"])
    merged["hit"] = hit
    for col in extra_cols:
        merged.loc[~hit, col] = pd.NA
    merged = merged.set_index("_orig_index")
    out = merged[["hit"] + extra_cols].reindex(rows.index)
    out["hit"] = out["hit"].fillna(False)
    return out


def flag_in_intervals(rows: pd.DataFrame, intervals: pd.DataFrame, date_col: str = "trading_date") -> pd.Series:
    """rows 의 (stock_id, date_col) 이 종목별 구간(start_date~end_date) 안에 있는지 표시한다."""
    return match_intervals(rows, intervals, date_col=date_col)["hit"]


def compute_interval_truncation(intervals: pd.DataFrame, raw_window: pd.DataFrame,
                                 open_dates: np.ndarray) -> pd.DataFrame:
    """구간마다(닫힌·열린 구분 없이) 시작일 이후 첫 '원가 거래량>0' 날짜와, 그 전날(트렁케이션 후보
    end_date)을 계산한다. 시작일 당일에 이미 거래량이 양수면 '전날' 이 시작일보다 앞서 구간이 자연히
    비게 된다(거래가 있었던 날은 정지일이 아니라는 규칙을 그대로 만족한다). 구간 끝까지 양수 거래량이
    한 번도 없으면 원래 end_date 를 그대로 쓴다(트렁케이션 근거가 없다)."""
    work = intervals.copy()
    if work.empty:
        work["first_positive_volume_date"] = pd.NaT
        work["truncated_end_date"] = pd.NaT
        return work

    pos_vol = raw_window.loc[raw_window["trade_volume"] > 0, ["stock_id", "trading_date"]] \
        .rename(columns={"trading_date": "first_positive_volume_date"}) \
        .sort_values("first_positive_volume_date")
    left = work[["stock_id", "start_date"]].reset_index().rename(columns={"index": "_orig_index"})
    left = left.sort_values("start_date")
    merged = pd.merge_asof(left, pos_vol, left_on="start_date", right_on="first_positive_volume_date",
                            by="stock_id", direction="forward")
    merged = merged.set_index("_orig_index")
    work["first_positive_volume_date"] = merged["first_positive_volume_date"].reindex(work.index)

    def _day_before(d):
        if pd.isna(d):
            return pd.NaT
        pos = int(np.searchsorted(open_dates, np.datetime64(d), side="left")) - 1
        return pd.Timestamp(open_dates[pos]) if pos >= 0 else pd.NaT

    work["truncated_end_date"] = work["first_positive_volume_date"].map(_day_before)
    return work


def build_truncated_mse_intervals(mse_intervals: pd.DataFrame, truncation: pd.DataFrame) -> pd.DataFrame:
    """트렁케이션 후보가 있는 구간만 end_date 를 대체한 구간 표를 만든다(근거 없는 구간은 원래 end_date)."""
    truncated = mse_intervals.copy()
    trunc_map = truncation["truncated_end_date"].dropna()
    truncated.loc[trunc_map.index, "end_date"] = trunc_map
    return truncated


def reconstruct_b4_bad_rows(raw_window: pd.DataFrame, status_df: pd.DataFrame) -> pd.DataFrame:
    """B4(nonpositive_ohlc_reconciliation.main())와 같은 분류를 재현한다."""
    nonpositive_mask = (raw_window[OHLC_COLS] <= 0).any(axis=1)
    bad = raw_window[nonpositive_mask].copy()
    bad["ohlc_pattern"] = build_ohlc_pattern(bad)
    halted_pairs = set(zip(
        status_df.loc[status_df["daily_state"].isin(["HALTED", "NO_BAR_HALTED"]), "stock_id"],
        status_df.loc[status_df["daily_state"].isin(["HALTED", "NO_BAR_HALTED"]), "trading_date"],
    ))
    partial_pairs = set(zip(
        status_df.loc[status_df["daily_state"] == "PARTIAL_TRADING", "stock_id"],
        status_df.loc[status_df["daily_state"] == "PARTIAL_TRADING", "trading_date"],
    ))
    bad["classification"] = classify_rows(bad, halted_pairs, partial_pairs)
    return bad


def compute_no_record_stock_ids(raw_ids: set, cohort_ids: set, issues: pd.DataFrame) -> list:
    """universe_diagnosis.analyze_gap 의 1차 사유 NO_ADMISSION_ISSUE_RECORD 전체 목록을 재계산한다."""
    missing_from_raw = raw_ids - cohort_ids
    issues = issues.copy()
    issues["instrument_id_int"] = pd.to_numeric(issues["instrument_id"], errors="coerce")
    mapped = issues.dropna(subset=["instrument_id_int"]).copy()
    mapped["instrument_id_int"] = mapped["instrument_id_int"].astype(int)
    issues_by_instrument = {
        int(iid): set(g["issue_code"].astype(str).unique()) for iid, g in mapped.groupby("instrument_id_int")
    }
    no_record = []
    for iid in sorted(missing_from_raw):
        codes_here = issues_by_instrument.get(iid, set())
        primary = next((r for r in PRIMARY_REASON_PRIORITY if r in codes_here), None)
        if primary is None:
            no_record.append(iid)
    return no_record


# ---------------------------------------------------------------------------
# A. 상장일
# ---------------------------------------------------------------------------


def analyze_a_listing(stock_df: pd.DataFrame, ih_df: pd.DataFrame, raw_window: pd.DataFrame) -> dict:
    stock_has = stock_df.loc[stock_df["listed_date"].notna(), ["stock_id", "listed_date"]].rename(
        columns={"listed_date": "stock_listed_date"}
    )
    ih_has = ih_df.loc[ih_df["min_listed_date"].notna(), [
        "stock_id", "min_listed_date", "max_listed_date", "distinct_listed_date_count", "first_effective_from",
    ]]

    stock_has_ids = set(stock_has["stock_id"])
    ih_has_ids = set(ih_has["stock_id"])
    both_ids = stock_has_ids & ih_has_ids

    merged = stock_has.merge(ih_has, on="stock_id", how="inner")
    mismatch = merged[merged["stock_listed_date"] != merged["min_listed_date"]]
    inconsistent_ih = ih_df[ih_df["distinct_listed_date_count"] > 1]

    stock_codes = stock_df.set_index("stock_id")["stock_code"]
    mismatch_examples = [
        {
            "stock_id": int(r.stock_id),
            "stock_code": stock_codes.get(r.stock_id),
            "stock_listed_date": r.stock_listed_date.date().isoformat(),
            "instrument_history_min_listed_date": r.min_listed_date.date().isoformat(),
        }
        for r in mismatch.head(10).itertuples()
    ]

    effective = stock_df[["stock_id", "stock_code", "listed_date"]].merge(
        ih_df[["stock_id", "min_listed_date"]], on="stock_id", how="left"
    )
    effective["effective_listed_date"] = effective["listed_date"].fillna(effective["min_listed_date"])

    first_raw_trade = raw_window.groupby("stock_id")["trading_date"].min().rename("first_raw_trade_date")
    joined = effective.merge(first_raw_trade, on="stock_id", how="left")
    has_both = joined.dropna(subset=["effective_listed_date", "first_raw_trade_date"])
    contradiction = has_both[has_both["effective_listed_date"] > has_both["first_raw_trade_date"]]

    after_20140102 = joined[joined["effective_listed_date"] >= pd.Timestamp("2014-01-02")]
    h2_2013 = joined[
        (joined["effective_listed_date"] >= pd.Timestamp("2013-07-01"))
        & (joined["effective_listed_date"] <= pd.Timestamp("2013-12-31"))
    ]

    return {
        "note": "상장일은 stock.listed_date 를 우선하고 없으면 instrument_history 의 최소 listed_date "
                "(effective_listed_date)를 쓴다. 2013년 하반기 상장 건은 2014-01-02 이전 개장일 캘린더가 "
                "없어 '120거래일 ≈ 6개월' 로 근사했으며 실제 거래일 수가 아니다.",
        "target_stock_count": int(stock_df["stock_id"].nunique()),
        "has_listed_date_in_stock": len(stock_has_ids),
        "has_listed_date_in_instrument_history": len(ih_has_ids),
        "has_listed_date_in_both": len(both_ids),
        "mismatch_count": int(len(mismatch)),
        "mismatch_examples": mismatch_examples,
        "instrument_history_internally_inconsistent_count": int(len(inconsistent_ih)),
        "contradiction_listed_after_first_raw_trade_count": int(len(contradiction)),
        "listed_on_or_after_2014_01_02_count": int(len(after_20140102)),
        "listed_2013_h2_approx_120td_boundary_count": int(len(h2_2013)),
    }


# ---------------------------------------------------------------------------
# B. 상장폐지
# ---------------------------------------------------------------------------


def analyze_b_delisting(stock_df: pd.DataFrame, mse_df: pd.DataFrame, th_df: pd.DataFrame,
                         raw_window: pd.DataFrame) -> dict:
    stock_delisted_ids = {int(x) for x in stock_df.loc[stock_df["delisted_date"].notna(), "stock_id"]}
    mse_delisted_ids = {int(x) for x in mse_df.loc[mse_df["status"] == "DELISTED", "stock_id"]}
    th_delist_ids = {int(x) for x in th_df.loc[th_df["notice_type"] == "DELIST", "stock_id"]}
    union_ids = stock_delisted_ids | mse_delisted_ids | th_delist_ids

    last_seen = raw_window.groupby("stock_id")["trading_date"].max()
    calendar_end = raw_window["trading_date"].max()
    threshold = calendar_end - pd.Timedelta(days=90)
    proxy_delisted = last_seen[last_seen < threshold]
    proxy_ids = {int(x) for x in proxy_delisted.index}
    proxy_with_evidence = proxy_ids & union_ids
    proxy_without_evidence = proxy_ids - union_ids

    mse_last_trade = mse_df.loc[mse_df["last_trade_date"].notna(), ["stock_id", "last_trade_date"]] \
        .drop_duplicates("stock_id")
    lt_join = mse_last_trade.merge(last_seen.rename("last_raw_trade_date"), on="stock_id", how="inner")
    lt_join["diff_days"] = (lt_join["last_trade_date"] - lt_join["last_raw_trade_date"]).dt.days

    mse_delist_dates = mse_df.loc[mse_df["status"] == "DELISTED", ["stock_id", "effective_date"]] \
        .rename(columns={"effective_date": "ref_date"})
    th_delist_dates = th_df.loc[th_df["notice_type"] == "DELIST", ["stock_id", "halt_date"]] \
        .rename(columns={"halt_date": "ref_date"})
    stock_delist_dates = stock_df.loc[stock_df["delisted_date"].notna(), ["stock_id", "delisted_date"]] \
        .rename(columns={"delisted_date": "ref_date"})
    all_ref_dates = pd.concat([mse_delist_dates, th_delist_dates, stock_delist_dates], ignore_index=True)
    first_ref_date = all_ref_dates.groupby("stock_id")["ref_date"].min().rename("delisting_reference_date")
    ref_join = first_ref_date.reset_index().merge(last_seen.rename("last_raw_trade_date"), on="stock_id", how="inner")
    ref_join["diff_days"] = (ref_join["delisting_reference_date"] - ref_join["last_raw_trade_date"]).dt.days

    def _describe(series: pd.Series) -> dict:
        if series.empty:
            return {"count": 0}
        d = series.describe()
        return {
            "count": int(d["count"]), "mean": round(float(d["mean"]), 1),
            "std": round(float(d["std"]), 1) if pd.notna(d.get("std")) else None,
            "min": float(d["min"]), "p25": float(d["25%"]), "median": float(d["50%"]),
            "p75": float(d["75%"]), "max": float(d["max"]),
        }

    return {
        "note": "B1(universe_diagnosis.py 의 analyze_delisting_proxy)의 '데이터 종료일보다 90일 이상 앞서 "
                "원가가 끊긴 종목' 정의(임계값 90일)를 그대로 재현했고, 폐지 근거는 stock.delisted_date / "
                "MSE status=DELISTED / trading_halt notice_type=DELIST 의 합집합이다(전부 2023-12-31 이하).",
        "evidence_by_source": {
            "stock_delisted_date": len(stock_delisted_ids),
            "market_status_event_delisted": len(mse_delisted_ids),
            "trading_halt_delist": len(th_delist_ids),
            "union": len(union_ids),
        },
        "stock_delisted_date_masked_after_cutoff_count": int(stock_df["delisted_date_after_cutoff"].sum()),
        "proxy_last_print_gt_90d_count": len(proxy_ids),
        "proxy_with_delisting_evidence_count": len(proxy_with_evidence),
        "proxy_without_evidence_collection_cutoff_candidate_count": len(proxy_without_evidence),
        "mse_last_trade_date_vs_last_raw_trade_date_diff_days": _describe(lt_join["diff_days"]),
        "delisting_reference_date_vs_last_raw_trade_date_diff_days": _describe(ref_join["diff_days"]),
    }


# ---------------------------------------------------------------------------
# C. 거래정지
# ---------------------------------------------------------------------------


def analyze_c_halt(bad: pd.DataFrame, status_df: pd.DataFrame, mse_df: pd.DataFrame, th_df: pd.DataFrame,
                    open_dates: np.ndarray, raw_window: pd.DataFrame, stock_df: pd.DataFrame) -> dict:
    mse_intervals = build_mse_halt_intervals(mse_df, open_dates)
    th_intervals = build_trading_halt_intervals(th_df)

    zero_rows = bad[bad["classification"] == ZERO_VOLUME_NO_STATUS].copy()
    mse_match = match_intervals(zero_rows, mse_intervals, extra_cols=["open_ended"])
    in_mse = mse_match["hit"]
    in_th = flag_in_intervals(zero_rows, th_intervals)
    category = pd.Series("NEITHER", index=zero_rows.index)
    category[in_th] = "TH_START_ONLY"
    category[in_mse] = "MSE_INTERVAL"
    zero_rows["halt_source_category"] = category

    category_counts = {k: int(v) for k, v in zero_rows["halt_source_category"].value_counts().items()}
    category_by_market: dict = {}
    for (mkt, cat), v in zero_rows.groupby(["market", "halt_source_category"]).size().items():
        category_by_market.setdefault(str(mkt), {})[str(cat)] = int(v)

    # 검증 1: MSE_INTERVAL 을 '닫힌 구간'과 '열린 구간(끝을 못 찾음)'으로 나눈다.
    mse_hit_mask = category == "MSE_INTERVAL"
    mse_open_ended_bool = mse_match["open_ended"].astype("boolean")
    mse_interval_closed_rows = int((mse_hit_mask & (mse_open_ended_bool == False)).sum())  # noqa: E712
    mse_interval_open_rows = int((mse_hit_mask & (mse_open_ended_bool == True)).sum())  # noqa: E712

    # 검증 2: MSE 정지 구간(닫힌·열린 따로) 안에 있는데 원가 거래량이 양수인 종목·일 수(모순).
    raw_match = match_intervals(raw_window, mse_intervals, extra_cols=["open_ended"])
    raw_in_mse = raw_match["hit"]
    raw_open_ended_bool = raw_match["open_ended"].astype("boolean")
    positive_volume = raw_window["trade_volume"] > 0
    contradiction_closed = int((raw_in_mse & (raw_open_ended_bool == False) & positive_volume).sum())  # noqa: E712
    contradiction_open = int((raw_in_mse & (raw_open_ended_bool == True) & positive_volume).sum())  # noqa: E712

    # 검증 2b(열린 구간 한정, 참고용): 정지 해제 공시 누락을 가정하고 열린 구간만 잘랐을 때의 추정치.
    full_truncation = compute_interval_truncation(mse_intervals, raw_window, open_dates)
    open_truncation = full_truncation[mse_intervals["open_ended"]]
    open_intervals_with_truncation_point = int(open_truncation["truncated_end_date"].notna().sum())

    # MSE_INTERVAL_TRUNCATED(보수 추정치): 닫힌·열린 구간 모두, 시작일 이후 첫 원가 거래량>0 날짜의
    # 전날에서 자른다. 시작일 당일에 이미 거래량이 양수면 그 구간은 빈 구간이 된다. 트렁케이션 근거가
    # 없는 구간(끝까지 거래량이 한 번도 양수가 아님)은 원래 end_date 를 그대로 쓴다. 기존
    # halt_source_category(상한값)는 바꾸지 않고 별도 필드로만 보고한다.
    truncated_mse_intervals = build_truncated_mse_intervals(mse_intervals, full_truncation)
    mse_trunc_match = match_intervals(zero_rows, truncated_mse_intervals, extra_cols=["reason"])
    in_mse_truncated = mse_trunc_match["hit"]
    category_truncated = pd.Series("NEITHER", index=zero_rows.index)
    category_truncated[in_th] = "TH_START_ONLY"
    category_truncated[in_mse_truncated] = "MSE_INTERVAL_TRUNCATED"
    zero_rows["halt_source_category_truncated"] = category_truncated

    category_truncated_counts = {k: int(v) for k, v in zero_rows["halt_source_category_truncated"].value_counts().items()}
    category_truncated_by_market: dict = {}
    for (mkt, cat), v in zero_rows.groupby(["market", "halt_source_category_truncated"]).size().items():
        category_truncated_by_market.setdefault(str(mkt), {})[str(cat)] = int(v)

    # STATUS_HALTED 280행이 절단 구간에도 모두 들어가는지 다시 확인한다.
    halted_status_rows = status_df.loc[
        status_df["daily_state"].isin(["HALTED", "NO_BAR_HALTED"]), ["stock_id", "trading_date"]
    ]
    status_in_mse = flag_in_intervals(halted_status_rows, mse_intervals)
    status_in_mse_truncated = flag_in_intervals(halted_status_rows, truncated_mse_intervals)

    # 정지 사유(reason) 상위 10개별로 절단 구간(MSE_INTERVAL_TRUNCATED) 행 수를 센다.
    top10_reasons = mse_df.loc[mse_df["status"] == "HALTED", "reason"].value_counts().head(10)
    matched_reason = mse_trunc_match.loc[in_mse_truncated, "reason"]
    reason_truncated_counts = {
        str(reason): int((matched_reason == reason).sum()) for reason in top10_reasons.index
    }

    # 검증 3: 원천(MSE HALTED·trading_halt HALT)의 시장 편중을 stock.market_code 기준으로 센다.
    market_label_map = stock_df.set_index("stock_id")["market_code"].map(
        lambda c: {"0": "KOSPI", "10": "KOSDAQ"}.get(c, f"OTHER({c})")
    )
    mse_halted_by_market = {
        str(k): int(v) for k, v in
        mse_df.loc[mse_df["status"] == "HALTED", "stock_id"].map(market_label_map).value_counts().items()
    }
    th_halt_by_market = {
        str(k): int(v) for k, v in
        th_df.loc[th_df["notice_type"] == "HALT", "stock_id"].map(market_label_map).value_counts().items()
    }

    halt_event_pairs = set(zip(
        mse_df.loc[mse_df["status"] == "HALTED", "stock_id"], mse_df.loc[mse_df["status"] == "HALTED", "effective_date"],
    )) | set(zip(
        th_df.loc[th_df["notice_type"] == "HALT", "stock_id"], th_df.loc[th_df["notice_type"] == "HALT", "halt_date"],
    ))

    def _next_open_date(date: pd.Timestamp):
        pos = int(np.searchsorted(open_dates, np.datetime64(date), side="right"))
        return pd.Timestamp(open_dates[pos]) if pos < len(open_dates) else None

    unexplained = bad[bad["classification"] == UNEXPLAINED]
    unexplained_table = []
    for row in unexplained.itertuples():
        next_open = _next_open_date(row.trading_date)
        unexplained_table.append({
            "stock_id": int(row.stock_id),
            "stock_code": row.stock_code,
            "trading_date": row.trading_date.date().isoformat(),
            "same_day_halt_event": (row.stock_id, row.trading_date) in halt_event_pairs,
            "next_trading_date": next_open.date().isoformat() if next_open is not None else None,
            "next_trading_day_halt_event": bool(
                next_open is not None and (row.stock_id, next_open) in halt_event_pairs
            ),
        })

    return {
        "note": "MSE 정지 구간은 HALTED 다음 TRADING/DELISTED 전날(개장일 기준)까지, 끝을 못 찾으면 "
                f"{HALT_OPEN_END.date().isoformat()} 까지 열어 둔다. trading_halt 구간은 halt_date~"
                "resume_date 전날(달력일)이며 resume_date 가 없으면 halt_date 하루만 확정 구간으로 쓴다. "
                "우선순위는 MSE_INTERVAL > TH_START_ONLY > NEITHER. 분류 기준(halt_source_category) 자체는 "
                "아래 검증 지표를 위해 바꾸지 않았다 — 검증 지표는 별도 필드로만 보고한다.",
        "mse_interval_count": int(len(mse_intervals)),
        "mse_interval_open_ended_count": int(mse_intervals["open_ended"].sum()) if len(mse_intervals) else 0,
        "trading_halt_interval_count": int(len(th_intervals)),
        "trading_halt_interval_confirmed_range_count":
            int(th_intervals["confirmed_range"].sum()) if len(th_intervals) else 0,
        "zero_volume_no_status_total": int(len(zero_rows)),
        "zero_volume_no_status_by_category": category_counts,
        "zero_volume_no_status_by_market_x_category": category_by_market,
        "validation": {
            "note": "MSE_INTERVAL(상한값) 104,067행이 전부 KOSDAQ 이고, MSE 구간 3,849개 중 1,030개가 끝을 "
                    "못 찾아 2023-12-28 까지 열려 있어 과대 집계 가능성을 점검했다. 닫힌 구간의 모순도 "
                    "적지 않은데(80,488건), 원인은 HALTED 의 의미(무상증자·개선기간 부여·상장폐지 사유 "
                    "발생 등 실제 매매정지 공시) 자체가 아니라 해제 이벤트(TRADING 1,205건)가 정지 이벤트"
                    "(HALTED 3,849건)보다 훨씬 적어 '다음 TRADING/DELISTED 전날' 규칙이 다른 정지의 해제일"
                    "까지 구간을 이어 붙이기 때문으로 본다.",
            "mse_interval_rows_in_closed_intervals": mse_interval_closed_rows,
            "mse_interval_rows_in_open_intervals": mse_interval_open_rows,
            "contradiction_positive_volume_in_mse_closed_interval_rows": contradiction_closed,
            "contradiction_positive_volume_in_mse_open_interval_rows": contradiction_open,
            "open_intervals_with_positive_volume_after_start_count": open_intervals_with_truncation_point,
            "open_intervals_total_count": int(len(open_truncation)),
            "mse_interval_truncated": {
                "note": "보수 추정치. 닫힌·열린 구간 모두 시작일 이후 첫 원가 거래량>0 날짜의 전날에서 "
                        "자른다(시작일 당일 거래량이 양수면 그 구간은 빈 구간이 된다). 트렁케이션 근거가 "
                        "없는(끝까지 양수 거래량이 없는) 구간은 원래 end_date 를 그대로 쓴다. 기존 "
                        "halt_source_category(상한값 104,067)는 바꾸지 않고 halt_source_category_truncated "
                        "로 별도 집계했다.",
                "zero_volume_no_status_by_category_truncated": category_truncated_counts,
                "zero_volume_no_status_by_market_x_category_truncated": category_truncated_by_market,
                "status_halted_280_in_truncated_mse_interval": int(status_in_mse_truncated.sum()),
                "status_halted_280_not_in_truncated_mse_interval": int((~status_in_mse_truncated).sum()),
                "top10_halted_reasons_row_count_in_truncated_interval": reason_truncated_counts,
            },
            "source_market_bias": {
                "note": "정지 원천(MSE HALTED·trading_halt HALT)의 시장 분포. stock.market_code 기준"
                        "(종목의 현재 시장, 사건 발생 시점 시장과 다를 수 있다). KOSPI 는 두 원천 모두 "
                        "표본이 극히 적어 KOSPI 무거래일의 정지 여부는 이번 원천으로도 판별되지 않는다.",
                "market_status_event_halted_by_market": mse_halted_by_market,
                "trading_halt_halt_by_market": th_halt_by_market,
            },
        },
        "status_halted_280_reverse_check": {
            "total": int(len(halted_status_rows)),
            "in_mse_interval": int(status_in_mse.sum()),
            "not_in_mse_interval": int((~status_in_mse).sum()),
        },
        "unexplained_18_halt_event_adjacency": unexplained_table,
    }


# ---------------------------------------------------------------------------
# D. 원인 미확인 누락 1,184종목 교차 집계
# ---------------------------------------------------------------------------


def analyze_d_no_record(no_record_ids: list, stock_df: pd.DataFrame, mse_df: pd.DataFrame,
                         th_df: pd.DataFrame, delisting_union_ids: set) -> dict:
    halt_history_ids = {int(x) for x in mse_df.loc[mse_df["status"] == "HALTED", "stock_id"]} | \
                        {int(x) for x in th_df.loc[th_df["notice_type"] == "HALT", "stock_id"]}
    listed_map = stock_df.set_index("stock_id")["listed_date"]

    def _listing_bucket(sid: int) -> str:
        ld = listed_map.get(sid)
        if ld is None or pd.isna(ld):
            return "NO_LISTED_DATE"
        return "2014_01_02_이후" if ld >= pd.Timestamp("2014-01-02") else "2014_01_02_이전"

    records = [
        {
            "stock_id": sid,
            "has_delisting_evidence": sid in delisting_union_ids,
            "listing_bucket": _listing_bucket(sid),
            "has_halt_history": sid in halt_history_ids,
        }
        for sid in no_record_ids
    ]
    crosstab: dict = {}
    if records:
        cross = pd.DataFrame(records)
        counts = cross.groupby(["has_delisting_evidence", "listing_bucket", "has_halt_history"]).size()
        for (delist, bucket, halt), v in counts.items():
            crosstab[f"delisting={delist}|listing={bucket}|halt={halt}"] = int(v)

    return {
        "note": "universe_diagnosis.py 의 gap 로직(원가 population - cohort, 1차 사유가 이슈 기록 전혀 없는 "
                "NO_ADMISSION_ISSUE_RECORD 인 종목)을 그대로 재계산했다(top20 예시가 아니라 전체 목록).",
        "no_record_stock_count": len(no_record_ids),
        "crosstab_delisting_x_listing_x_halt": crosstab,
    }


# ---------------------------------------------------------------------------
# analyze 메인
# ---------------------------------------------------------------------------


def analyze(extract_dir: Path, prepared_dir: Path, tables_dir: Path, out_path: Path) -> dict:
    started = time.time()

    frames, extract_manifest, extract_hashes = load_extracted(extract_dir)
    stock_df = frames["STOCK"]
    ih_df = frames["INSTRUMENT_HISTORY"]
    mse_df = frames["MARKET_STATUS_EVENT"]
    th_df = frames["TRADING_HALT"]

    cohort_ids, cohort_hash = load_cohort(prepared_dir)
    issues, issues_hash = load_issues(prepared_dir)
    calendar, calendar_hash = load_calendar(prepared_dir)
    status_df, status_hash = load_status(tables_dir)

    price_columns = ["adjusted", "stock_id", "stock_code", "market", "trading_date",
                      "open_price", "high_price", "low_price", "close_price", "trade_volume"]
    all_prices, price_hashes, saw_future = load_price_table(tables_dir, price_columns)
    raw_prices = all_prices[~all_prices["adjusted"]].reset_index(drop=True)
    raw_window = raw_prices[raw_prices["trading_date"] < CUTOFF].copy()
    raw_ids = {int(x) for x in raw_window["stock_id"].unique().tolist()}

    open_dates = np.sort(calendar["date"].values)

    bad = reconstruct_b4_bad_rows(raw_window, status_df)

    a_result = analyze_a_listing(stock_df, ih_df, raw_window)
    b_result = analyze_b_delisting(stock_df, mse_df, th_df, raw_window)
    c_result = analyze_c_halt(bad, status_df, mse_df, th_df, open_dates, raw_window, stock_df)

    no_record_ids = compute_no_record_stock_ids(raw_ids, cohort_ids, issues)
    delisting_union_ids = (
        {int(x) for x in stock_df.loc[stock_df["delisted_date"].notna(), "stock_id"]}
        | {int(x) for x in mse_df.loc[mse_df["status"] == "DELISTED", "stock_id"]}
        | {int(x) for x in th_df.loc[th_df["notice_type"] == "DELIST", "stock_id"]}
    )
    d_result = analyze_d_no_record(no_record_ids, stock_df, mse_df, th_df, delisting_union_ids)

    result = {
        "admission_status": "READ_ONLY_DIAGNOSTIC_NOT_ADMITTED",
        "note": "이 결과는 백테스트 실행이나 전략 승인의 근거가 아니다. B1b(상장·폐지·거래정지 PostgreSQL "
                "대조) 결과다.",
        "generated_at": pd.Timestamp.now().isoformat(),
        "runtime_seconds": None,
        "date_cutoff": {
            "cutoff": CUTOFF.date().isoformat(),
            "saw_rows_on_or_after_cutoff": bool(saw_future),
            "note": "로컬 가격 Parquet 는 날짜로 사전 필터링하지 않고 전부 읽은 뒤 컷오프 이후 행을 "
                    "집계에서 제외했다(saw_rows_on_or_after_cutoff 로 존재 여부만 표시). DB 추출은 SQL "
                    "WHERE 절과 CASE 마스킹으로 2023-12-31 이하만 값으로 내보냈다.",
        },
        "extract_manifest_summary": {
            "extract_dir": str(extract_dir),
            "row_counts": extract_manifest.get("row_counts"),
            "instrument_history_excluded_after_cutoff_row_count":
                extract_manifest.get("instrument_history_excluded_after_cutoff_row_count"),
            "sql_sha256": extract_manifest.get("sql_sha256"),
        },
        "input_sha256": {
            **cohort_hash, **issues_hash, **calendar_hash, **status_hash,
            "price_parquet_files": price_hashes,
            "extract_parquet_files": extract_hashes,
        },
        "a_listing": a_result,
        "b_delisting": b_result,
        "c_halt": c_result,
        "d_no_record_crosstab": d_result,
    }
    result["runtime_seconds"] = round(time.time() - started, 1)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_path} in {result['runtime_seconds']}s")
    return result


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prepared-dir", type=Path, default=DEFAULT_PREPARED_DIR)
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    parser.add_argument("--extract-dir", type=Path, default=DEFAULT_EXTRACT_DIR)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--mode", choices=["extract", "analyze", "both"], default="both")
    parser.add_argument("--timeout", type=int, default=580, help="DB 추출 subprocess 타임아웃(초)")
    args = parser.parse_args(argv)

    out_path = args.out or (Path(__file__).resolve().parent / "listing-halt-reconciliation.json")

    if args.mode in ("extract", "both"):
        manifest = extract(args.extract_dir, timeout=args.timeout)
        print(f"extracted to {args.extract_dir}: {manifest['row_counts']}")

    if args.mode in ("analyze", "both"):
        analyze(args.extract_dir, args.prepared_dir, args.tables_dir, out_path)


if __name__ == "__main__":
    main()
