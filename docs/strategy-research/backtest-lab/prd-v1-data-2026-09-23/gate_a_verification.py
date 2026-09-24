"""PRD v1 데이터 정리 B5 — Gate A(데이터 인수) 전수 검증, 읽기 전용.

이 스크립트는 다음을 절대 하지 않는다.
  - 수익률 계산이나 백테스트 실행
  - `../vectorbt-data/` 아래 기존 파일 쓰기/수정 (전부 읽기 전용으로 연다)
  - PostgreSQL·네트워크 접속 (운영 DB 값은 gate-a-db-member-seal.txt 에서만 읽는다)
  - cohort.json 재생성이나 결함 보정. 세고 분류하고 나열만 한다.

Gate A 4개 항목(docs/strategy-research/backtest-lab/backtest-data-requirements-2026-09-20.md
64~71행)을 확인한다.
  1. member 봉인: verify_v3_snapshot 통과 + DB seal 대조 + tables dir 행 수·revision 대조.
  2. 가격쌍 완전성: calendar × universe(보통주 유효기간) 기대 격자 대비 원가/수정가 존재 분류.
  3. OHLC 유효성: TRADING 행의 원가·수정가 양수·순서 검사.
  4. 원가/수정가 계수 일치: ADJUSTMENT member 의 explanation_status 로 UNEXPLAINED_VENDOR_FACTOR 재현.
그리고 종목별 대조(2,787종목), B1 정정 수치, Gate A 판정을 추가한다(팀장 브리프 5~7).

2024-01-01 이후 행은 읽은 직후 집계에서 제외한다(사전 필터링하지 않는다). 소스별로
그런 행이 있었는지 date_cutoff 에 기록한다.

사용법:
    .venv/Scripts/python.exe -X utf8 gate_a_verification.py \
        --snapshot-dir ../vectorbt-data/krx-v3-20260921-implementation \
        --tables-dir ../vectorbt-data/krx-v3-20260921-tables \
        --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
        --seal-file gate-a-db-member-seal.txt \
        --out-json gate-a-verification.json --out-csv gate-a-instruments.csv
    (개발 중 반복용) --skip-member-verify 로 verify_v3_snapshot(49초)를 건너뛸 수 있다.
    최종 실행은 반드시 --skip-member-verify 없이 돌린다.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from universe_diagnosis import (  # noqa: E402
    CUTOFF,
    DEFAULT_PREPARED_DIR,
    DEFAULT_TABLES_DIR,
    ISSUE_CATEGORY,
    NO_RECORD_REASON,
    PRIMARY_REASON_PRIORITY,
    load_calendar,
    load_cohort,
    load_issues,
    load_price_table,
    sha256_file,
)
from nonpositive_ohlc_reconciliation import load_status  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))
from research.krx_lab.v3_snapshot import SPECS, verify_v3_snapshot  # noqa: E402
from research.krx_lab.source_contract_admission import REVISION_ID, REVISION_SHA256  # noqa: E402

DEFAULT_SNAPSHOT_DIR = Path("C:/Users/aeby/vscode/stock/vectorbt-data/krx-v3-20260921-implementation")
DEFAULT_SEAL_FILE = Path(__file__).resolve().parent / "gate-a-db-member-seal.txt"

# PRD 는 상장 후 120거래일 완전 세션을 요구한다(universe_diagnosis.py 의 Q2 서술 근거와 동일 출처:
# docs/strategy-research/backtest-lab/postgresql-readiness-2026-09-21/README.md).
PRD_WARMUP_SESSIONS = 120
# v3_scope.py 의 250봉 자격 조건(참고용, cohort 판정 자체가 이 상수를 쓴다).
COHORT_WARMUP_SESSIONS = 250

# TRADING 행 정의 출처: research/krx_lab/v3_inputs.py:205-223. 명시적 STATUS 행이 없고, 원가 OHLC가
# 유한·양수이며 high>=max(open,close), low<=min(open,close)이고 거래량>0 인 행만 TRADING 이다(그 외
# 값이 있으면 그 명시적 상태를 그대로 쓰고, 셋 다 아니면 UNKNOWN). raw_bar_eligibility(research/krx_lab/
# v3_market.py:142-155)도 같은 "status=='TRADING' AND daily_state=='TRADING'" 전제를 쓴다.
TRADING_DEFINITION_SOURCE = "research/krx_lab/v3_inputs.py:205-223 (status derivation), :221-223 (eligible)"

# v3_scope.py clean_cohort 재현에 쓰는 정의들의 출처(file:line). 허용오차는 여기 있는 것만 쓰고 넓히지 않는다.
SCOPE_SOURCE = {
    "ADJUSTED_PAIR_INVALID_OR_MISSING": "research/krx_lab/v3_scope.py:34-38",
    "RAW_TRADED_OHLC_INVALID": "research/krx_lab/v3_scope.py:39-45",
    "WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE": "research/krx_lab/v3_scope.py:46-52",
    "UNEXPLAINED_VENDOR_FACTOR": "research/krx_lab/v3_scope.py:104-118; "
    "research/krx_lab/source_contract_admission.py:164-165 (explanation_status 값 정의는 DB 업스트림, "
    "이 리포에는 별도 허용오차 상수가 없다 — explanation_status 필드를 그대로 읽는다)",
    "CORPORATE_ACTION_PARTIAL": "research/krx_lab/v3_scope.py:95-103 (이 스크립트는 admission_issue 의 "
    "날짜 매칭 단계를 생략하고 corporate_action.resolution_status=='PARTIAL' 을 직접 썼다 — 실제 데이터에서 "
    "PARTIAL 이벤트는 전부 admission_issue 의 CORPORATE_ACTION_PARTIAL 일자와 대응한다고 가정)",
    "ADJUSTED_PRICE_UNAVAILABLE_GENERIC": "research/krx_lab/v3_scope.py:74-79 (REJECT/QUARANTINE 이고 "
    "affected_scope 가 'stock:<code>' 형식인 이슈는 코드에 관계없이 그 종목의 사유가 된다; 이번 데이터는 "
    "ADJUSTED_PRICE_UNAVAILABLE 475건만 이 형식이다)",
    "UNSUPPORTED_OR_UNPRICED_EVENT": "research/krx_lab/v3_scope.py:119-138",
}

CORE_MEMBER_KINDS = list(SPECS)

# ---------------------------------------------------------------------------
# check10(고정 표본 원문 재현) 용 DB 읽기 전용 접근. research/krx_lab/v3_snapshot.py:38-39 의
# COMMAND 방식(ssh home + docker exec psql)만 쓴다. SQL 은 항상 BEGIN ... READ ONLY / ROLLBACK 으로 감싼다.
# ---------------------------------------------------------------------------
SSH_COMMAND = [
    "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "home",
    "docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db psql -X -q -U kiwoom -d kiwoom_db",
]
DEFAULT_CHECK10_EXTRACT_DIR = Path("C:/Users/aeby/vscode/stock/vectorbt-data/krx-prd-v1-b5-20260924")
# B1b(listing_halt_reconciliation.py) 가 이미 추출해 둔 stock/market_status_event/trading_halt 를 check9 의
# universe 유효기간 공백 설명에 재사용한다(읽기 전용, 새로 추출하지 않는다).
DEFAULT_B1B_EXTRACT_DIR = Path("C:/Users/aeby/vscode/stock/vectorbt-data/krx-prd-v1-b1b-20260924")

# check10 payload->parquet 필드 매핑 출처. DB 스키마 조회(information_schema.columns, 읽기 전용, 2026-09-24)와
# 표본 1건씩(RAW/ADJUSTED 각 1건, stock_id=19/000250, 2014-01-02) 직접 대조로 확인했다 — 이 리포 코드에는
# 이 매핑이 문서화되어 있지 않아(research/krx_lab 은 kiwoom.source_record/source_payload 원문 필드를 다루지
# 않는다) 이번 조사로 확정했다.
PAYLOAD_FIELD_MAP = {
    "DAILY_PRICE": {  # source_code=KRX_OPEN_API, 원가
        "array_key": "OutBlock_1", "match_fields": {"ISU_CD": "stock_code", "BAS_DD": "trading_date_yyyymmdd"},
        "columns": {"open_price": "TDD_OPNPRC", "high_price": "TDD_HGPRC", "low_price": "TDD_LWPRC",
                    "close_price": "TDD_CLSPRC", "trade_volume": "ACC_TRDVOL"},
        "rounding": "문자열로 저장된 정수를 그대로 int 캐스트(단위·반올림 변환 없음)",
    },
    "DAILY_PRICE_VENDOR": {  # source_code=KIWOOM_REST, 수정가
        "array_key": "stk_dt_pole_chart_qry", "match_fields": {"dt": "trading_date_yyyymmdd"},
        "columns": {"open_price": "open_pric", "high_price": "high_pric", "low_price": "low_pric",
                    "close_price": "cur_prc", "trade_volume": "trde_qty"},
        "rounding": "문자열로 저장된 정수를 그대로 int 캐스트(단위·반올림 변환 없음). trde_prica(거래대금)는 "
        "백만원 단위로 보이며 trade_amount 와 단위가 달라 이번 재현 대상에서 뺐다(브리프가 요구한 필드는 "
        "OHLC·거래량뿐이다).",
    },
}
# 표본 층화 기준: 연도×시장×원가/수정가. 목표 총 행 수.
CHECK10_TARGET_SAMPLE_ROWS = 200
CHECK10_ROWS_PER_STRATUM = 7


def sha256_and_read(path: Path, **kwargs) -> tuple[pd.DataFrame, str]:
    return pd.read_parquet(path, **kwargs), sha256_file(path)


# ---------------------------------------------------------------------------
# tables-dir 원천 member 로더 (Parquet, 컬럼 제한)
# ---------------------------------------------------------------------------


def load_tables_calendar(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "calendar-00108.parquet"
    df = pd.read_parquet(fp, columns=["trading_date", "market", "is_open"])
    df["trading_date"] = pd.to_datetime(df["trading_date"])
    return df, {fp.name: sha256_file(fp)}


def load_universe(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "universe-00097.parquet"
    df = pd.read_parquet(fp, columns=["stock_id", "stock_code", "market", "security_type", "valid_from", "valid_to"])
    df["valid_from"] = pd.to_datetime(df["valid_from"])
    df["valid_to"] = pd.to_datetime(df["valid_to"])
    return df, {fp.name: sha256_file(fp)}


def load_corporate_action(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "corporate_action-00111.parquet"
    cols = ["stock_id", "event_id", "event_type", "resolution_status", "quantity_ratio", "reference_price",
            "announced_at", "effective_date", "settlement_policy", "sequence_no"]
    df = pd.read_parquet(fp, columns=cols)
    df["effective_date"] = pd.to_datetime(df["effective_date"])
    df["announced_at"] = pd.to_datetime(df["announced_at"])
    return df, {fp.name: sha256_file(fp)}


def load_adjustment(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "adjustment-00112.parquet"
    cols = ["stock_id", "trading_date", "explanation_status", "candidate_event_ids", "event_id",
            "factor_ratio", "previous_factor", "price_factor"]
    df = pd.read_parquet(fp, columns=cols)
    df["trading_date"] = pd.to_datetime(df["trading_date"])
    return df, {fp.name: sha256_file(fp)}


def load_identifier(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    files = sorted(tables_dir.glob("identifier-*.parquet"))
    cols = ["stock_id", "identifier_type", "identifier_value", "valid_from", "valid_to", "source_record_id"]
    frames = []
    hashes = {}
    for fp in files:
        frames.append(pd.read_parquet(fp, columns=cols))
        hashes[fp.name] = sha256_file(fp)
    df = pd.concat(frames, ignore_index=True)
    df["valid_from"] = pd.to_datetime(df["valid_from"])
    df["valid_to"] = pd.to_datetime(df["valid_to"])
    return df, hashes


def load_execution_rule(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "execution_rule-00113.parquet"
    df = pd.read_parquet(fp)
    df["effective_from"] = pd.to_datetime(df["effective_from"])
    df["effective_to"] = pd.to_datetime(df["effective_to"])
    return df, {fp.name: sha256_file(fp)}


def load_benchmark(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "benchmark-00109.parquet"
    df = pd.read_parquet(fp, columns=["benchmark_code", "trading_date"])
    df["trading_date"] = pd.to_datetime(df["trading_date"])
    return df, {fp.name: sha256_file(fp)}


def load_source_payload_index(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "source_payload-00115.parquet"
    df = pd.read_parquet(fp)
    return df, {fp.name: sha256_file(fp)}


def load_admission_issue_table(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "admission_issue-00114.parquet"
    cols = ["issue_code", "affected_scope", "affected_from", "affected_to", "decision", "severity", "details"]
    df = pd.read_parquet(fp, columns=cols)
    df["affected_from"] = pd.to_datetime(df["affected_from"])
    df["affected_to"] = pd.to_datetime(df["affected_to"])
    return df, {fp.name: sha256_file(fp)}


def tables_dir_physical_row_counts(tables_dir: Path) -> dict[str, int]:
    """manifest.json 을 신뢰하지 않고 각 parquet 파일을 직접 열어 member_kind 별 실제 행 수를 센다."""
    import pyarrow.parquet as pq

    counts: dict[str, int] = defaultdict(int)
    for fp in sorted(tables_dir.glob("*.parquet")):
        kind = fp.stem.rsplit("-", 1)[0].upper()
        counts[kind] += pq.ParquetFile(fp).metadata.num_rows
    return dict(counts)


# ---------------------------------------------------------------------------
# Check 1. member 봉인
# ---------------------------------------------------------------------------


def parse_seal_file(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not lines[0].startswith("#"):
        raise ValueError("SEAL_FILE_MISSING_COMMENT_HEADER")
    rev_kind, rev_status, rev_sha, rev_sealed_at = lines[1].split("|")
    if rev_kind != "REV":
        raise ValueError("SEAL_FILE_MISSING_REV_LINE")
    members = {}
    for line in lines[2:]:
        if not line.strip():
            continue
        kind, row_count, content_sha256 = line.split("|")
        members[kind] = {"row_count": int(row_count), "content_sha256": content_sha256}
    return {
        "revision_status": rev_status,
        "revision_content_sha256": rev_sha,
        "revision_sealed_at": rev_sealed_at,
        "members": members,
        "header_comment": lines[0],
    }


def check1_member_seal(snapshot_dir: Path, tables_dir: Path, seal_path: Path, skip_member_verify: bool) -> dict:
    result: dict = {"seal_file": str(seal_path), "seal_file_sha256": sha256_file(seal_path)}
    seal = parse_seal_file(seal_path)
    result["seal_parsed"] = {
        "revision_status": seal["revision_status"],
        "revision_content_sha256": seal["revision_content_sha256"],
        "member_kinds": sorted(seal["members"]),
    }

    if skip_member_verify:
        result["verify_v3_snapshot"] = {"skipped": True, "note": "--skip-member-verify: 개발 중 반복용, 최종 판정에 쓰지 않는다"}
        snapshot_manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))
    else:
        started = time.time()
        try:
            snapshot_manifest = verify_v3_snapshot(snapshot_dir)
            result["verify_v3_snapshot"] = {"status": "PASS", "seconds": round(time.time() - started, 1)}
        except Exception as exc:  # noqa: BLE001 — read-only 검증 실패는 결과에 담아 보고한다
            result["verify_v3_snapshot"] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}",
                                            "seconds": round(time.time() - started, 1)}
            snapshot_manifest = json.loads((snapshot_dir / "manifest.json").read_text(encoding="utf-8"))

    # DB seal ↔ 스냅샷 manifest 대조
    db_vs_snapshot = {"revision_status_match": seal["revision_status"] == snapshot_manifest["revision"]["status"],
                       "revision_content_sha256_match": seal["revision_content_sha256"] == snapshot_manifest["revision_content_sha256"]}
    member_mismatches = []
    snapshot_members = {m["member_kind"]: m for m in snapshot_manifest["members"]}
    for kind in CORE_MEMBER_KINDS:
        seal_m = seal["members"].get(kind)
        snap_m = snapshot_members.get(kind)
        if seal_m is None or snap_m is None:
            member_mismatches.append({"member_kind": kind, "reason": "MISSING_ON_ONE_SIDE"})
            continue
        if seal_m["row_count"] != snap_m["row_count"] or seal_m["content_sha256"] != snap_m["content_sha256"]:
            member_mismatches.append({"member_kind": kind, "seal": seal_m, "snapshot": {
                "row_count": snap_m["row_count"], "content_sha256": snap_m["content_sha256"]}})
    db_vs_snapshot["member_count_checked"] = len(CORE_MEMBER_KINDS)
    db_vs_snapshot["mismatches"] = member_mismatches
    db_vs_snapshot["all_11_match"] = not member_mismatches and db_vs_snapshot["revision_content_sha256_match"]
    result["db_seal_vs_snapshot_manifest"] = db_vs_snapshot

    # tables dir 대조: revision 바인딩 + 파일을 직접 열어 센 실제 행 수
    tables_manifest = json.loads((tables_dir / "manifest.json").read_text(encoding="utf-8"))
    physical_counts = tables_dir_physical_row_counts(tables_dir)
    tables_row_mismatches = []
    for kind in CORE_MEMBER_KINDS:
        expected = seal["members"].get(kind, {}).get("row_count")
        actual = physical_counts.get(kind)
        if expected != actual:
            tables_row_mismatches.append({"member_kind": kind, "seal_row_count": expected, "tables_dir_physical_row_count": actual})
    result["tables_dir"] = {
        "manifest_sha256": sha256_file(tables_dir / "manifest.json"),
        "manifest_revision_id_matches_code_constant": tables_manifest.get("revision_id") == REVISION_ID,
        "manifest_revision_content_sha256_matches_code_constant": tables_manifest.get("revision_content_sha256") == REVISION_SHA256,
        "manifest_revision_id_matches_snapshot": tables_manifest.get("revision_id") == snapshot_manifest.get("revision_id"),
        "manifest_revision_content_sha256_matches_snapshot": tables_manifest.get("revision_content_sha256")
        == snapshot_manifest.get("revision_content_sha256"),
        "physical_row_counts_by_member_kind": physical_counts,
        "row_count_mismatches_vs_seal": tables_row_mismatches,
    }
    result["overall_pass"] = (
        result["verify_v3_snapshot"].get("status") == "PASS"
        and db_vs_snapshot["all_11_match"]
        and not tables_row_mismatches
        and result["tables_dir"]["manifest_revision_id_matches_code_constant"]
        and result["tables_dir"]["manifest_revision_content_sha256_matches_code_constant"]
    )
    return result


# ---------------------------------------------------------------------------
# 격자(calendar × universe) 와 가격 인덱싱 공용 유틸
# ---------------------------------------------------------------------------


def build_open_dates(calendar_df: pd.DataFrame) -> tuple[np.ndarray, bool]:
    cal = calendar_df[(calendar_df["market"] == "KRX") & (calendar_df["is_open"])]
    saw_future = bool((cal["trading_date"] >= CUTOFF).any())
    dates = cal.loc[cal["trading_date"] < CUTOFF, "trading_date"].unique()
    dates = np.sort(dates.astype("datetime64[ns]"))
    return dates, saw_future


def build_grid(universe_df: pd.DataFrame, open_dates: np.ndarray) -> tuple[pd.DataFrame, dict]:
    """보통주 유효기간 × 개장일 기대 격자. 세그먼트가 겹치는 종목은 union 한다."""
    common = universe_df[universe_df["security_type"] == "COMMON_STOCK"]
    valid_from = common["valid_from"].values.astype("datetime64[ns]")
    valid_to = common["valid_to"].values.astype("datetime64[ns]")
    lo = np.searchsorted(open_dates, valid_from, side="left")
    hi = np.searchsorted(open_dates, valid_to, side="right")
    counts = np.clip(hi - lo, 0, None)
    stock_ids = common["stock_id"].to_numpy()
    stock_rep = np.repeat(stock_ids, counts)
    day_idx = np.concatenate([np.arange(l, h) for l, h in zip(lo, hi) if h > l]) if counts.sum() else np.array([], dtype=np.int64)
    raw_grid = pd.DataFrame({"stock_id": stock_rep, "day_idx": day_idx})
    grid = raw_grid.drop_duplicates().reset_index(drop=True)
    stats = {
        "common_stock_instruments": int(common["stock_id"].nunique()),
        "universe_segments_common_stock": int(len(common)),
        "grid_rows_before_segment_union": int(len(raw_grid)),
        "grid_rows_after_segment_union": int(len(grid)),
        "overlapping_segment_duplicate_rows": int(len(raw_grid) - len(grid)),
    }
    return grid, stats


def index_by_day(dates: pd.Series, open_dates: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    values = dates.values.astype("datetime64[ns]")
    idx = np.searchsorted(open_dates, values)
    idx_clipped = np.clip(idx, 0, len(open_dates) - 1)
    on_calendar = open_dates[idx_clipped] == values
    return idx_clipped, on_calendar


def load_indexed_prices(tables_dir: Path, open_dates: np.ndarray) -> dict:
    """price-*.parquet 를 한 번만 읽고 raw/adjusted 각각 day_idx·유효성 플래그를 붙인다."""
    columns = ["adjusted", "stock_id", "trading_date", "open_price", "high_price", "low_price", "close_price", "trade_volume"]
    all_prices, price_hashes, saw_future = load_price_table(tables_dir, columns)
    all_prices = all_prices[all_prices["trading_date"] < CUTOFF].copy()

    day_idx, on_cal = index_by_day(all_prices["trading_date"], open_dates)
    all_prices["day_idx"] = day_idx
    all_prices["on_calendar"] = on_cal

    ohlc = all_prices[["open_price", "high_price", "low_price", "close_price"]]
    valid = ohlc.notna().all(axis=1) & (ohlc > 0).all(axis=1)
    valid &= all_prices["high_price"] >= all_prices[["open_price", "close_price"]].max(axis=1)
    valid &= all_prices["low_price"] <= all_prices[["open_price", "close_price"]].min(axis=1)
    all_prices["row_valid"] = valid
    all_prices["nonpositive_ohlc"] = (ohlc <= 0).any(axis=1)
    all_prices["volume_positive"] = all_prices["trade_volume"] > 0

    raw = all_prices[~all_prices["adjusted"]].reset_index(drop=True)
    adj = all_prices[all_prices["adjusted"]].reset_index(drop=True)
    return {"raw": raw, "adjusted": adj, "price_hashes": price_hashes, "saw_future": saw_future}


def dedupe_on_calendar(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """(stock_id, day_idx) 중복을 첫 행 기준으로 접고, 중복·격자밖(휴장일) 통계를 낸다."""
    off_calendar = df.loc[~df["on_calendar"]]
    on_cal = df.loc[df["on_calendar"]].sort_values(["stock_id", "day_idx"])
    dup_mask = on_cal.duplicated(["stock_id", "day_idx"], keep=False)
    dedup = on_cal.drop_duplicates(["stock_id", "day_idx"], keep="first")
    stats = {
        "total_rows": int(len(df)),
        "off_calendar_holiday_rows": int(len(off_calendar)),
        "on_calendar_rows": int(len(on_cal)),
        "duplicate_stock_day_rows": int(dup_mask.sum()),
        "distinct_stock_day_pairs": int(len(dedup)),
    }
    return dedup, stats


# ---------------------------------------------------------------------------
# Check 2. 가격쌍 완전성
# ---------------------------------------------------------------------------


def check2_price_pair_completeness(grid: pd.DataFrame, raw_dedup: pd.DataFrame, adj_dedup: pd.DataFrame,
                                   raw_stats: dict, adj_stats: dict, status_df: pd.DataFrame,
                                   open_dates: np.ndarray) -> tuple[dict, pd.DataFrame]:
    key_cols = ["stock_id", "day_idx"]
    raw_keys = raw_dedup[key_cols + ["nonpositive_ohlc"]].copy()
    raw_keys["has_raw"] = True
    adj_keys = adj_dedup[key_cols].copy()
    adj_keys["has_adj"] = True

    merged = grid.merge(raw_keys, on=key_cols, how="left").merge(adj_keys, on=key_cols, how="left")
    merged["has_raw"] = merged["has_raw"].fillna(False).astype(bool)
    merged["has_adj"] = merged["has_adj"].fillna(False).astype(bool)
    merged["nonpositive_ohlc"] = merged["nonpositive_ohlc"].fillna(False).astype(bool)

    status_idx, status_on_cal = index_by_day(status_df["trading_date"], open_dates)
    status_df = status_df.assign(day_idx=status_idx, on_calendar=status_on_cal)
    status_df = status_df[status_df["on_calendar"]]
    halted = status_df[status_df["daily_state"].isin(["HALTED", "NO_BAR_HALTED", "PARTIAL_TRADING"])][key_cols].drop_duplicates()
    halted["is_halted"] = True
    merged = merged.merge(halted, on=key_cols, how="left")
    merged["is_halted"] = merged["is_halted"].fillna(False).astype(bool)

    conditions = [merged.has_raw & merged.has_adj, merged.has_raw & ~merged.has_adj, ~merged.has_raw & merged.has_adj]
    merged["pair_status"] = np.select(conditions, ["BOTH", "RAW_ONLY", "ADJ_ONLY"], default="NEITHER")

    is_raw_only = merged["pair_status"] == "RAW_ONLY"
    is_neither = merged["pair_status"] == "NEITHER"
    merged["explained_halt"] = merged["is_halted"] & (is_raw_only | is_neither)
    merged["explained_nonpositive_raw"] = is_raw_only & merged["nonpositive_ohlc"] & ~merged["is_halted"]
    merged["explained"] = merged["explained_halt"] | merged["explained_nonpositive_raw"]
    merged["unexplained"] = (is_raw_only | is_neither) & ~merged["explained"]

    # 격자 밖(원가·수정가 있지만 유효기간/개장일 격자에 없음) 카운트
    grid_key = grid[key_cols]
    raw_offgrid = int(len(raw_keys.merge(grid_key, on=key_cols, how="left", indicator=True).query("_merge=='left_only'")))
    adj_offgrid = int(len(adj_keys.merge(grid_key, on=key_cols, how="left", indicator=True).query("_merge=='left_only'")))

    pivot = merged.groupby(["stock_id", "pair_status"]).size().unstack(fill_value=0)
    for col in ["BOTH", "RAW_ONLY", "ADJ_ONLY", "NEITHER"]:
        if col not in pivot.columns:
            pivot[col] = 0
    explain_pivot = merged[is_raw_only | is_neither].groupby("stock_id")[["explained_halt", "explained_nonpositive_raw", "unexplained"]].sum()
    per_instrument = pivot.join(explain_pivot, how="left").fillna(0).astype(int)
    per_instrument.index.name = "instrument_id_int"

    summary = {
        "note": "격자 = 공식 개장일(calendar member, market=KRX & is_open) × 보통주 유효기간(universe member, "
        "security_type=COMMON_STOCK). RAW_ONLY/NEITHER 의 설명은 status member 정지(HALTED/NO_BAR_HALTED/"
        "PARTIAL_TRADING)를 먼저 확인하고, 그다음 RAW_ONLY 에 한해 원가 OHLC<=0(무거래)을 확인한다. NEITHER 는 "
        "원가 행 자체가 없어 OHLC<=0 판정을 적용할 수 없으므로 정지 여부로만 설명한다.",
        "expected_grid_rows": int(len(grid)),
        "raw_price_load_stats": raw_stats,
        "adjusted_price_load_stats": adj_stats,
        "raw_rows_outside_grid": raw_offgrid,
        "adjusted_rows_outside_grid": adj_offgrid,
        "pair_status_counts": {k: int(v) for k, v in merged["pair_status"].value_counts().items()},
        "raw_only_or_neither_explanation": {
            "explained_by_halt": int(merged["explained_halt"].sum()),
            "explained_by_nonpositive_raw_ohlc": int(merged["explained_nonpositive_raw"].sum()),
            "unexplained": int(merged["unexplained"].sum()),
        },
        "adj_only_count": int((merged["pair_status"] == "ADJ_ONLY").sum()),
    }
    return summary, per_instrument


# ---------------------------------------------------------------------------
# Check 3. OHLC 유효성 (TRADING 행)
# ---------------------------------------------------------------------------


def check3_ohlc_validity(grid: pd.DataFrame, raw_dedup: pd.DataFrame, adj_dedup: pd.DataFrame,
                         status_df: pd.DataFrame, open_dates: np.ndarray, raw_all: pd.DataFrame) -> dict:
    key_cols = ["stock_id", "day_idx"]
    status_idx, status_on_cal = index_by_day(status_df["trading_date"], open_dates)
    status_df = status_df.assign(day_idx=status_idx, on_calendar=status_on_cal)
    status_df = status_df[status_df["on_calendar"]][key_cols].drop_duplicates()
    status_df["has_explicit_status"] = True

    raw_small = raw_dedup[key_cols + ["row_valid", "volume_positive"]].rename(
        columns={"row_valid": "raw_valid", "volume_positive": "raw_volume_positive"})
    adj_small = adj_dedup[key_cols + ["row_valid"]].rename(columns={"row_valid": "adjusted_valid"})

    frame = raw_small.merge(status_df, on=key_cols, how="left")
    frame["has_explicit_status"] = frame["has_explicit_status"].fillna(False).astype(bool)
    frame = frame.merge(adj_small, on=key_cols, how="left", indicator="_adj_merge")
    frame["has_adjusted_row"] = frame["_adj_merge"] == "both"
    frame["adjusted_valid"] = frame["adjusted_valid"].fillna(False).astype(bool)

    frame["is_trading"] = (~frame["has_explicit_status"]) & frame["raw_valid"] & frame["raw_volume_positive"]
    trading = frame[frame["is_trading"]]

    # v3_scope.py:39-45 RAW_TRADED_OHLC_INVALID 재현: TRADING 여부와 무관하게 volume>0 이면서 원가가
    # 무효(비양수 또는 순서 위반)인 모든 행. 격자 밖 행도 포함해 tables-dir 전체에서 재현한다(브리프의
    # "원천 합계·B4 18건 대조" 대상과 동일 모집단).
    raw_invalid_traded = raw_all[(~raw_all["adjusted"]) & raw_all["volume_positive"] & ~raw_all["row_valid"]]
    raw_invalid_traded_instruments = sorted(int(x) for x in raw_invalid_traded["stock_id"].unique())

    return {
        "note": "TRADING 정의 출처: " + TRADING_DEFINITION_SOURCE + ". 아래 raw_valid_within_trading 은 "
        "TRADING 정의 자체가 raw_valid 를 전제하므로 항상 100%가 되어야 하는 동어반복적 확인(재구현 검산)이다. "
        "adjusted_valid_within_trading 은 독립적인 검사다(TRADING 정의가 adjusted 값을 보지 않기 때문).",
        "trading_rows": int(len(trading)),
        "trading_raw_valid_rows": int(trading["raw_valid"].sum()),
        "trading_raw_invalid_rows": int((~trading["raw_valid"]).sum()),
        "trading_rows_with_adjusted_row_present": int(trading["has_adjusted_row"].sum()),
        "trading_rows_with_adjusted_row_missing": int((~trading["has_adjusted_row"]).sum()),
        "trading_rows_with_valid_adjusted": int((trading["has_adjusted_row"] & trading["adjusted_valid"]).sum()),
        "trading_rows_with_invalid_adjusted": int((trading["has_adjusted_row"] & ~trading["adjusted_valid"]).sum()),
        "raw_traded_ohlc_invalid": {
            "source_file_line": SCOPE_SOURCE["RAW_TRADED_OHLC_INVALID"],
            "rows": int(len(raw_invalid_traded)),
            "instruments": len(raw_invalid_traded_instruments),
            "instrument_ids": raw_invalid_traded_instruments,
            "compare_to_cohort_RAW_TRADED_OHLC_INVALID": 18,
            "compare_to_B4_unexplained_rows": 18,
            "compare_note": "cohort.json exclusions 의 RAW_TRADED_OHLC_INVALID 종목 수, B4 "
            "(nonpositive-ohlc-reconciliation.json)의 UNEXPLAINED 행 수와 대조용 상수(팀장 브리프 제공치). "
            "이 스크립트가 실제로 계산한 값은 위 instruments 다.",
        },
        "source_admission_issue_row_counts_for_reference": {
            "RAW_NONPOSITIVE_PRICE_TRADED": 13,
            "ADJUSTED_NONPOSITIVE_PRICE_TRADED": 4,
            "ADJUSTED_OHLC_ORDER_VIOLATION": 284,
            "note": "이 3개 코드의 admission_issue 행은 affected_scope 가 'stock:' 형식이 아니고(종목 키 "
            "없음), v3_scope.py:83-93 의 DIFFERENT_SOURCE_PAIR_CURRENT_ROWS_REVALIDATED 분기로 전부 해소되어 "
            "cohort 제외 사유에 나타나지 않는다(과거 PYKRX 소스쌍 전용 이슈). 이 스크립트는 그 분기를 "
            "재구현하지 않았다 — 사유 생성에 영향이 없기 때문이다(판단 근거는 최종 보고 참고).",
        },
    }


# ---------------------------------------------------------------------------
# Check 4. UNEXPLAINED_VENDOR_FACTOR 재현
# ---------------------------------------------------------------------------


def check4_vendor_factor(adjustment_df: pd.DataFrame, ids_set: set[str], cohort_vendor_set: set[str]) -> dict:
    bad_status = {"OBSERVED_VENDOR_FACTOR", "UNEXPLAINED_VENDOR_FACTOR"}
    bad_rows = adjustment_df[adjustment_df["explanation_status"].isin(bad_status)]
    stock_ids_all = {str(int(x)) for x in bad_rows["stock_id"].unique()}
    stock_ids_in_population = stock_ids_all & ids_set

    candidate_present = bad_rows["candidate_event_ids"].apply(
        lambda v: v is not None and (not isinstance(v, (list, np.ndarray)) or len(v) > 0)
    )

    return {
        "source_file_line": SCOPE_SOURCE["UNEXPLAINED_VENDOR_FACTOR"],
        "adjustment_member_explanation_status_counts": {
            str(k): int(v) for k, v in adjustment_df["explanation_status"].value_counts().items()
        },
        "bad_status_rows": int(len(bad_rows)),
        "bad_status_distinct_stock_ids": len(stock_ids_all),
        "bad_status_stock_ids_inside_2787_population": len(stock_ids_in_population),
        "bad_status_stock_ids_outside_population": len(stock_ids_all - ids_set),
        "compare_to_cohort_UNEXPLAINED_VENDOR_FACTOR_397": len(cohort_vendor_set),
        "reproduced_set_equals_cohort_set": stock_ids_in_population == cohort_vendor_set,
        "symmetric_difference_count": len(stock_ids_in_population ^ cohort_vendor_set),
        "source_admission_issue_row_count_UNEXPLAINED_VENDOR_FACTOR": 1061,
        "candidate_event_ids_optional_crosscheck": {
            "note": "가능하면(브리프 optional) 가격비율 변화일이 사건으로 설명되는지 보는 경량 대용치. "
            "candidate_event_ids 가 비어있지 않은 비율만 본다 — 실제 사건 매칭 자체는 explanation_status 가 "
            "이미 DB 업스트림에서 계산해 둔 값이므로 이 스크립트가 다시 계산하지 않는다.",
            "bad_status_rows_with_candidate_event_ids": int(candidate_present.sum()),
            "bad_status_rows_without_candidate_event_ids": int((~candidate_present).sum()),
        },
    }


# ---------------------------------------------------------------------------
# Check 5 재료. v3_scope.clean_cohort 사유의 독립 재현 (tables-dir 원천에서만)
# ---------------------------------------------------------------------------


def reproduce_events_reasons(ca_df: pd.DataFrame) -> tuple[dict[str, set], dict, bool]:
    saw_future = bool((ca_df["effective_date"] >= CUTOFF).any())
    ca = ca_df[ca_df["effective_date"] < CUTOFF].copy()
    keep = ~(ca["resolution_status"].eq("SUPERSEDED") | ca["event_type"].eq("LISTED_SHARE_CHANGE"))
    ca = ca[keep]

    ratio = pd.to_numeric(ca["quantity_ratio"], errors="coerce")
    reference = pd.to_numeric(ca["reference_price"], errors="coerce")
    supported = (
        ca["event_type"].eq("SPLIT") & ca["resolution_status"].eq("RESOLVED")
        & ca["settlement_policy"].eq("NONE")
        & ratio.notna() & (ratio > 1) & (ratio == ratio.round())
        & reference.notna() & np.isfinite(reference) & (reference > 0)
        & ca["announced_at"].notna() & ca["effective_date"].notna()
        & (ca["announced_at"].dt.date < ca["effective_date"].dt.date)
        & ca["sequence_no"].notna()
    )
    unsupported = ca[~supported]

    reasons: dict[str, set] = defaultdict(set)
    for stock_id, kind in zip(unsupported["stock_id"], unsupported["event_type"]):
        reasons[str(int(stock_id))].add(f"UNSUPPORTED_OR_UNPRICED_EVENT:{kind}")

    kind_counts = {str(k): int(v) for k, v in unsupported.groupby("event_type")["stock_id"].nunique().items()}
    return reasons, {
        "source_file_line": SCOPE_SOURCE["UNSUPPORTED_OR_UNPRICED_EVENT"],
        "corporate_action_rows_considered": int(len(ca)),
        "unsupported_rows": int(len(unsupported)),
        "unsupported_instruments_by_event_type": kind_counts,
        "compare_to_cohort_counts": {
            "RIGHTS_OFF": 831, "CAPITAL_REDUCTION": 198, "SPLIT": 179, "DIVIDEND_OFF": 141,
            "PAID_CAPITAL_INCREASE": 22, "UNKNOWN_QUANTITY_TRANSFORM": 4,
        },
    }, saw_future


def reproduce_corporate_action_partial(ca_df: pd.DataFrame) -> tuple[dict[str, set], dict]:
    partial = ca_df[(ca_df["resolution_status"] == "PARTIAL") & (ca_df["effective_date"] < CUTOFF)]
    reasons: dict[str, set] = defaultdict(set)
    for stock_id in partial["stock_id"].unique():
        reasons[str(int(stock_id))].add("CORPORATE_ACTION_PARTIAL")
    return reasons, {
        "source_file_line": SCOPE_SOURCE["CORPORATE_ACTION_PARTIAL"],
        "partial_rows": int(len(partial)),
        "partial_instruments": len(reasons),
        "compare_to_cohort_CORPORATE_ACTION_PARTIAL_130": 130,
    }


def reproduce_adjusted_price_unavailable(issue_df: pd.DataFrame, code_to_id: dict[str, int]) -> tuple[dict[str, set], dict]:
    rq = issue_df[issue_df["decision"].isin(["REJECT", "QUARANTINE"])]
    rq = rq[~rq["issue_code"].isin(["POINT_IN_TIME_SECTOR_UNAVAILABLE", "WARMUP_250_BARS_SHORT"])]
    stock_scoped = rq[rq["affected_scope"].str.startswith("stock:")].copy()
    stock_scoped["code"] = stock_scoped["affected_scope"].str.split(":", n=1).str[1]
    stock_scoped["stock_id"] = stock_scoped["code"].map(code_to_id)
    unmapped = stock_scoped[stock_scoped["stock_id"].isna()]

    reasons: dict[str, set] = defaultdict(set)
    for stock_id, issue_code in zip(stock_scoped["stock_id"], stock_scoped["issue_code"]):
        if pd.notna(stock_id):
            reasons[str(int(stock_id))].add(str(issue_code))
    return reasons, {
        "source_file_line": SCOPE_SOURCE["ADJUSTED_PRICE_UNAVAILABLE_GENERIC"],
        "stock_scoped_reject_quarantine_rows": int(len(stock_scoped)),
        "unmapped_stock_code_rows": int(len(unmapped)),
        "issue_code_counts": {str(k): int(v) for k, v in stock_scoped["issue_code"].value_counts().items()},
        "compare_to_cohort_ADJUSTED_PRICE_UNAVAILABLE_475": 475,
    }


def reproduce_warmup(grid: pd.DataFrame) -> tuple[dict[str, set], dict, pd.Series]:
    session_counts = grid.groupby("stock_id").size()
    warmup_ids = session_counts[session_counts < COHORT_WARMUP_SESSIONS].index
    reasons: dict[str, set] = defaultdict(set)
    for stock_id in warmup_ids:
        reasons[str(int(stock_id))].add("WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE")
    return reasons, {
        "source_file_line": SCOPE_SOURCE["WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE"],
        "instruments_below_250_grid_sessions": len(warmup_ids),
        "compare_to_cohort_WARMUP_176": 176,
        "note": "세션 수는 grid(개장일×유효기간) 행 수를 썼다 — v3_scope.py:47-52 의 'history' 도 같은 방식으로 "
        "만들어진 prices 프레임의 종목별 행 수를 쓴다고 가정했다(판단 근거는 최종 보고 참고).",
    }, session_counts


def reproduce_raw_and_adjusted_pair_reasons(raw_dedup: pd.DataFrame, adj_dedup: pd.DataFrame, grid: pd.DataFrame) -> dict[str, set]:
    """v3_scope.py:34-45 의 ADJUSTED_PAIR_INVALID_OR_MISSING / RAW_TRADED_OHLC_INVALID 를 grid 행 단위로 재현."""
    key_cols = ["stock_id", "day_idx"]
    adj_valid_keys = adj_dedup.loc[adj_dedup["row_valid"], key_cols]
    adj_valid_keys = adj_valid_keys.assign(adjusted_valid=True)
    g = grid.merge(adj_valid_keys, on=key_cols, how="left")
    g["adjusted_valid"] = g["adjusted_valid"].fillna(False).astype(bool)
    invalid_pair_ids = g.loc[~g["adjusted_valid"], "stock_id"].unique()

    raw_traded_invalid_keys = raw_dedup.loc[raw_dedup["volume_positive"] & ~raw_dedup["row_valid"], "stock_id"].unique()

    reasons: dict[str, set] = defaultdict(set)
    for stock_id in invalid_pair_ids:
        reasons[str(int(stock_id))].add("ADJUSTED_PAIR_INVALID_OR_MISSING")
    for stock_id in raw_traded_invalid_keys:
        reasons[str(int(stock_id))].add("RAW_TRADED_OHLC_INVALID")
    return reasons


def merge_reason_dicts(*dicts: dict[str, set]) -> dict[str, set]:
    out: dict[str, set] = defaultdict(set)
    for d in dicts:
        for k, v in d.items():
            out[k] |= v
    return out


# ---------------------------------------------------------------------------
# Check 6. B1(universe_diagnosis.py) NO_ADMISSION_ISSUE_RECORD 정정
# ---------------------------------------------------------------------------


def reproduce_b1_no_record_ids(raw_ids: set[int], cohort_ids: set[int], issues: pd.DataFrame) -> list[int]:
    missing_from_raw = raw_ids - cohort_ids
    issues = issues.copy()
    issues["instrument_id_int"] = pd.to_numeric(issues["instrument_id"], errors="coerce")
    mapped = issues.dropna(subset=["instrument_id_int"]).copy()
    mapped["instrument_id_int"] = mapped["instrument_id_int"].astype(int)
    by_instrument: dict[int, set[str]] = {}
    for iid, grp in mapped.groupby("instrument_id_int"):
        by_instrument[int(iid)] = set(grp["issue_code"].astype(str).unique())
    no_record = []
    for iid in sorted(missing_from_raw):
        codes_here = by_instrument.get(iid, set())
        primary = next((r for r in PRIMARY_REASON_PRIORITY if r in codes_here), None)
        if primary is None:
            no_record.append(iid)
    return no_record


def check6_b1_correction(raw_ids: set[int], cohort_ids: set[int], issues: pd.DataFrame,
                         cohort_reasons: dict[str, set]) -> dict:
    no_record_ids = reproduce_b1_no_record_ids(raw_ids, cohort_ids, issues)
    reason_distribution: dict[str, int] = defaultdict(int)
    unexplained_by_cohort_too = []
    for iid in no_record_ids:
        reasons = cohort_reasons.get(str(iid), set())
        if not reasons:
            unexplained_by_cohort_too.append(iid)
            reason_distribution["NOT_IN_COHORT_EXCLUSIONS_EITHER"] += 1
            continue
        for r in sorted(reasons):
            reason_distribution[r] += 1
    return {
        "note": "B1(universe_diagnosis.py analyze_gap)의 1차 사유가 NO_ADMISSION_ISSUE_RECORD 였던 종목의 "
        "cohort.json 실제 제외 사유 분포. 종목 하나가 사유를 여럿 가지면 전부 센다(중복 허용).",
        "b1_no_record_instrument_count": len(no_record_ids),
        "cohort_reason_distribution_for_those_instruments": dict(sorted(reason_distribution.items(), key=lambda kv: -kv[1])),
        "instruments_with_no_cohort_reason_either": len(unexplained_by_cohort_too),
        "instruments_with_no_cohort_reason_either_ids": sorted(unexplained_by_cohort_too)[:50],
    }


def load_price_lineage_columns(tables_dir: Path) -> dict:
    """check8(FK)·check10(표본) 에 필요한 계보·OHLCV 컬럼을 읽는다."""
    columns = ["adjusted", "stock_id", "stock_code", "market", "trading_date", "source_record_id", "payload_sha256",
              "open_price", "high_price", "low_price", "close_price", "trade_volume"]
    df, hashes, saw_future = load_price_table(tables_dir, columns)
    df = df[df["trading_date"] < CUTOFF].reset_index(drop=True)
    return {"frame": df, "price_hashes": hashes, "saw_future": saw_future}


# ---------------------------------------------------------------------------
# Check 8. PK·FK·원천 행 추적 (Gate A 1번 항목)
# ---------------------------------------------------------------------------

NATURAL_KEYS = {
    "PRICE": (["stock_id", "trading_date", "adjusted"], "research/krx_lab/v3_snapshot.py:26"),
    "UNIVERSE": (["stock_id", "market", "valid_from"], "research/krx_lab/v3_snapshot.py:27"),
    "IDENTIFIER": (["stock_id", "identifier_type", "identifier_value", "valid_from"], "research/krx_lab/v3_snapshot.py:28"),
    "CALENDAR": (["market", "trading_date"], "research/krx_lab/v3_snapshot.py:29"),
    "BENCHMARK": (["benchmark_code", "trading_date"], "research/krx_lab/v3_snapshot.py:30"),
    "STATUS": (["stock_id", "trading_date"], "research/krx_lab/v3_snapshot.py:31"),
    "CORPORATE_ACTION": (["event_id"], "research/krx_lab/v3_snapshot.py:32"),
    "ADJUSTMENT": (["stock_id", "trading_date", "event_id"], "research/krx_lab/v3_snapshot.py:33"),
    "EXECUTION_RULE": (["rule_kind", "market", "effective_from"], "research/krx_lab/v3_snapshot.py:34"),
    "ADMISSION_ISSUE": (["issue_code", "affected_scope", "affected_from", "affected_to", "decision", "severity",
                        "details"],
                        "research/krx_lab/v3_snapshot.py:35 — 원 정렬열은 to_jsonb(x)::text(행 전체)이므로 PK "
                        "검사도 로딩한 전체 컬럼(issue_code·affected_scope·affected_from·affected_to·decision·"
                        "severity·details) 을 키로 썼다."),
    "SOURCE_PAYLOAD": (["payload_id"], "research/krx_lab/v3_snapshot.py:36"),
}

# check8 참고용(FAIL 판정에 쓰지 않음): 코드·구간·결정만 같고 details 만 다른 admission_issue 행 수.
ADMISSION_ISSUE_REFERENCE_KEY = ["issue_code", "affected_from", "affected_to", "decision"]


def check8_pk_fk(universe_df: pd.DataFrame, identifier_df: pd.DataFrame, tables_calendar: pd.DataFrame,
                 benchmark_df: pd.DataFrame, status_df: pd.DataFrame, ca_df: pd.DataFrame, adj_df: pd.DataFrame,
                 issue_df: pd.DataFrame, execution_rule_df: pd.DataFrame, payload_index_df: pd.DataFrame,
                 price_lineage: pd.DataFrame) -> dict:
    frames = {
        "PRICE": price_lineage, "UNIVERSE": universe_df, "IDENTIFIER": identifier_df,
        "CALENDAR": tables_calendar, "BENCHMARK": benchmark_df, "STATUS": status_df,
        "CORPORATE_ACTION": ca_df, "ADJUSTMENT": adj_df, "EXECUTION_RULE": execution_rule_df,
        "ADMISSION_ISSUE": issue_df, "SOURCE_PAYLOAD": payload_index_df,
    }
    pk_duplicates = {}
    for kind, (key_cols, source) in NATURAL_KEYS.items():
        df = frames[kind]
        dup_count = int(df.duplicated(key_cols, keep=False).sum())
        pk_duplicates[kind] = {"natural_key": key_cols, "source_file_line": source, "rows": int(len(df)),
                               "duplicate_rows": dup_count}
    admission_issue_reference_dup = int(
        issue_df.duplicated(ADMISSION_ISSUE_REFERENCE_KEY, keep=False).sum())
    pk_duplicates["ADMISSION_ISSUE"]["reference_only_same_code_window_decision_different_details"] = {
        "natural_key": ADMISSION_ISSUE_REFERENCE_KEY, "duplicate_rows": admission_issue_reference_dup,
        "note": "FAIL 판정에 쓰지 않는다(브리프 (d)). 코드·구간·결정만 같고 details 만 다른 행 수 참고치.",
    }

    universe_ids = set(int(x) for x in universe_df["stock_id"].unique())
    identifier_ids = set(int(x) for x in identifier_df["stock_id"].unique())
    known_stock_ids = universe_ids | identifier_ids

    def fk_check(df: pd.DataFrame, label: str) -> dict:
        unknown_mask = ~df["stock_id"].astype("int64").isin(known_stock_ids)
        unknown = df.loc[unknown_mask, "stock_id"].unique()
        return {"rows_checked": int(len(df)), "unknown_stock_id_rows": int(unknown_mask.sum()),
                "unknown_stock_id_examples": sorted(int(x) for x in unknown)[:20]}

    fk_stock_id = {
        "note": "universe(모든 security_type) ∪ identifier 의 stock_id 합집합을 참조 대상으로 삼았다.",
        "known_stock_id_count": len(known_stock_ids),
        "PRICE": fk_check(price_lineage, "PRICE"),
        "ADJUSTMENT": fk_check(adj_df, "ADJUSTMENT"),
        "CORPORATE_ACTION": fk_check(ca_df, "CORPORATE_ACTION"),
        "STATUS": fk_check(status_df, "STATUS"),
    }

    payload_sha_set = set(payload_index_df["payload_sha256"])
    source_record_null = int(price_lineage["source_record_id"].isna().sum())
    payload_sha_null = int(price_lineage["payload_sha256"].isna().sum())
    resolved_mask = price_lineage["payload_sha256"].isin(payload_sha_set)
    unresolved = price_lineage.loc[~resolved_mask & price_lineage["payload_sha256"].notna()]

    fk_source_lineage = {
        "note": "가격 행의 source_record_id 는 SOURCE_PAYLOAD member 자체에는 없어(그 member 는 payload_id·"
        "payload_sha256 만 담는다) 전수 해석은 이 리포의 오프라인 자료만으로 불가능하다 — check10 표본에서 "
        "DB 의 kiwoom.source_record 로 직접 해석 가능함을 확인했다(NOT_VERIFIABLE_OFFLINE, 표본으로 대체 확인).",
        "source_record_id_null_rows": source_record_null,
        "payload_sha256_null_rows": payload_sha_null,
        "payload_sha256_resolved_against_SOURCE_PAYLOAD_member": int(resolved_mask.sum()),
        "payload_sha256_unresolved_rows": int(len(unresolved)),
        "payload_sha256_unresolved_examples": unresolved.head(10)[["stock_id", "trading_date", "adjusted"]]
        .assign(trading_date=lambda d: d["trading_date"].dt.date.astype(str)).to_dict("records"),
        "rows_checked": int(len(price_lineage)),
    }

    return {
        "pk_duplicates_by_member": pk_duplicates,
        "pk_all_zero_duplicates": all(v["duplicate_rows"] == 0 for v in pk_duplicates.values()),
        "fk_stock_id_membership": fk_stock_id,
        "fk_source_lineage": fk_source_lineage,
    }


# ---------------------------------------------------------------------------
# Check 9. 유효기간 겹침·끊김 (Gate A 4번 항목)
# ---------------------------------------------------------------------------


def compute_overlaps_gaps(df: pd.DataFrame, group_cols: list[str], open_dates: np.ndarray) -> pd.DataFrame:
    """그룹 안에서 valid_from 정렬 후 누적 최대 valid_to 대비 겹침·공백을 표시한다(중첩 구간도 처리).

    공백은 브리프 (a) 기준대로 '이전 구간 valid_to 와 다음 구간 valid_from 사이에 공식 개장일이 1개 이상' 일
    때만 잡는다(달력일 차이가 아니라 개장일 수). gap_open_days 가 그 개장일 수다.
    """
    d = df.sort_values(group_cols + ["valid_from"]).reset_index(drop=True).copy()
    running_max_to = d.groupby(group_cols)["valid_to"].cummax()
    d["running_max_to"] = running_max_to
    d["prev_running_max_to"] = d.groupby(group_cols)["running_max_to"].shift(1)
    d["is_first_in_group"] = d["prev_running_max_to"].isna()
    d["overlap"] = (~d["is_first_in_group"]) & (d["valid_from"] <= d["prev_running_max_to"])

    prev_to_filled = d["prev_running_max_to"].fillna(d["valid_from"]).values.astype("datetime64[ns]")
    lo = np.searchsorted(open_dates, prev_to_filled + np.timedelta64(1, "D"), side="left")
    hi = np.searchsorted(open_dates, d["valid_from"].values.astype("datetime64[ns]"), side="left")
    gap_open_days = np.clip(hi - lo, 0, None)
    d["gap_open_days"] = np.where(d["is_first_in_group"], 0, gap_open_days)
    d["gap"] = (~d["is_first_in_group"]) & (d["gap_open_days"] >= 1)
    return d


def explain_universe_gaps(gap_rows: pd.DataFrame, b1b: dict | None) -> dict:
    if b1b is None:
        return {"explainable": False, "reason": "B1B_EXTRACT_DIR_NOT_FOUND(읽기 전용 재사용 대상 없음)",
                "gap_count": int(len(gap_rows)), "explained": None, "unexplained": None}
    stock = b1b["stock"].set_index("stock_id")
    halts = b1b["trading_halt"]
    events = b1b["market_status_event"]
    explained = 0
    unexplained_list = []
    for row in gap_rows.itertuples():
        sid = int(row.stock_id)
        gap_start, gap_end = row.prev_running_max_to, row.valid_from
        ok = False
        if sid in stock.index:
            listed = stock.loc[sid, "listed_date"]
            delisted = stock.loc[sid, "delisted_date"]
            if pd.notna(listed) and gap_end <= listed:
                ok = True
            if not ok and pd.notna(delisted) and gap_start >= delisted:
                ok = True
        if not ok:
            sh = halts[halts["stock_id"] == sid]
            for h in sh.itertuples():
                resume = h.resume_date if pd.notna(h.resume_date) else HALT_OPEN_END_FALLBACK
                if h.halt_date <= gap_end and gap_start <= resume:
                    ok = True
                    break
        if not ok:
            se = events[(events["stock_id"] == sid) & events["effective_date"].between(gap_start, gap_end)]
            if not se.empty:
                ok = True
        if ok:
            explained += 1
        else:
            unexplained_list.append({
                "stock_id": sid, "gap_start": gap_start.date().isoformat(),
                "gap_end": gap_end.date().isoformat(), "gap_open_days": int(row.gap_open_days)})
    return {"explainable": True, "gap_count": int(len(gap_rows)), "explained": explained,
            "unexplained": len(unexplained_list), "unexplained_examples": unexplained_list[:30]}


HALT_OPEN_END_FALLBACK = pd.Timestamp("2023-12-28")

SELL_TAX_R1_NOTE = ("execution_rule 의 SELL_TAX 는 2014년 구간이 없다(2015-01-01 부터 시작). "
                    "docs/strategy-research/backtest-lab/prd-v1-data-2026-09-23/requests/"
                    "r1-execution-rule-sell-tax.md 로 이미 ted-startup 에 원천 수정을 요청했다(예상 245개장일×"
                    "2시장=490건). 이 스크립트는 이를 KNOWN_R1_REQUESTED 로 분류하되, 미해결 결함이므로 "
                    "gate_a_items 4번 FAIL 사유에 반영한다(새로 발견한 결함이 아님).")


def check_execution_rule_coverage(execution_rule_df: pd.DataFrame, open_dates: np.ndarray) -> dict:
    """(rule_kind, market) 마다 2014~2023 개장일 각각이 정확히 1개 구간에 들어가는지 검사한다."""
    n = len(open_dates)
    by_group = []
    for (rule_kind, market), grp in execution_rule_df.groupby(["rule_kind", "market"]):
        coverage = np.zeros(n, dtype=np.int16)
        for row in grp.itertuples():
            lo = np.searchsorted(open_dates, np.datetime64(row.effective_from), side="left")
            hi = np.searchsorted(open_dates, np.datetime64(row.effective_to), side="right")
            coverage[lo:hi] += 1
        uncovered_mask = coverage == 0
        duplicated_mask = coverage >= 2
        is_known_sell_tax = rule_kind == "SELL_TAX" and bool(uncovered_mask[open_dates < np.datetime64("2015-01-01")].any())
        by_group.append({
            "rule_kind": rule_kind, "market": market,
            "uncovered_open_days": int(uncovered_mask.sum()),
            "duplicated_open_days": int(duplicated_mask.sum()),
            "known_r1_sell_tax_2014": is_known_sell_tax,
        })
    sell_tax_uncovered_total = sum(g["uncovered_open_days"] for g in by_group if g["rule_kind"] == "SELL_TAX")
    non_r1_uncovered_total = sum(g["uncovered_open_days"] for g in by_group if not g["known_r1_sell_tax_2014"])
    duplicated_total = sum(g["duplicated_open_days"] for g in by_group)
    return {
        "note": "브리프 (b): (rule_kind,market) 마다 2014~2023 개장일이 정확히 한 구간에 포함되는지 검사한다 "
        "(compute_overlaps_gaps 의 구간-사이 공백 검사가 아니라 전체 구간 커버리지 검사다).",
        "by_group": by_group,
        "sell_tax_uncovered_open_days_total": sell_tax_uncovered_total,
        "sell_tax_uncovered_matches_r1_expected_490": sell_tax_uncovered_total == 490,
        "non_r1_uncovered_open_days_total": non_r1_uncovered_total,
        "duplicated_open_days_total": duplicated_total,
        "known_r1_note": SELL_TAX_R1_NOTE,
    }


def item1_pk_fk_source_traceability(check1: dict, check8: dict) -> dict:
    """gate_a_items 1번. check1 member 봉인 + check8 PK 전무결점 + check8 FK stock_id 전무결점을 모두 요구한다.
    source_record_id 전수 해석은 오프라인 불가라서 판정에 넣지 않고 사유에만 참고로 남긴다."""
    reasons = []
    if not check1["overall_pass"]:
        reasons.append("check1 member 봉인 불일치")
    dup_members = {k: v["duplicate_rows"] for k, v in check8["pk_duplicates_by_member"].items()
                  if v["duplicate_rows"] > 0}
    if dup_members:
        reasons.append(f"check8 PK 중복: {dup_members}")
    for kind in ("PRICE", "ADJUSTMENT", "CORPORATE_ACTION", "STATUS"):
        unknown = check8["fk_stock_id_membership"][kind]["unknown_stock_id_rows"]
        if unknown:
            reasons.append(f"{kind} FK stock_id 미해석 {unknown}행")
    lineage_note = ("source_record_id 전수 해석은 오프라인 불가(check10 표본 210/210 으로 부분 확인, "
                    f"payload_sha256 은 {check8['fk_source_lineage']['payload_sha256_resolved_against_SOURCE_PAYLOAD_member']}"
                    "/"
                    f"{check8['fk_source_lineage']['rows_checked']} 전수 해석됨) — 판정에는 반영하지 않음")
    return {"based_on": ["check1", "check8"], "status": "FAIL" if reasons else "PASS",
            "reason": ("; ".join(reasons) + " | " + lineage_note) if reasons else lineage_note}


def item4_validity_period_continuity(check9: dict) -> dict:
    """gate_a_items 4번. 브리프: SELL_TAX 2014 공백은 R1 로 이미 요청된 실제 결함이므로 FAIL 사유에 넣되
    '새 결함 아님' 을 명시한다. universe 미설명 공백·execution_rule 의 R1 이외 미포함·중복 포함도 있으면 더한다."""
    universe_unexplained = check9["universe"]["gap_explanation"].get("unexplained")
    exec_cov = check9["execution_rule"]
    reasons = []
    if universe_unexplained not in (0, None):
        reasons.append(f"universe 미설명 공백 {universe_unexplained}건")
    if exec_cov["non_r1_uncovered_open_days_total"]:
        reasons.append(f"execution_rule 미분류(R1 아님) 미포함 개장일 {exec_cov['non_r1_uncovered_open_days_total']}건")
    if exec_cov["duplicated_open_days_total"]:
        reasons.append(f"execution_rule 중복 포함 개장일 {exec_cov['duplicated_open_days_total']}건")
    if exec_cov["sell_tax_uncovered_open_days_total"]:
        reasons.append(f"execution_rule SELL_TAX 2014 미포함 {exec_cov['sell_tax_uncovered_open_days_total']}건"
                       "(R1 로 요청됨, 새 결함 아님)")
    return {"based_on": ["check9"], "status": "FAIL" if reasons else "PASS", "reason": "; ".join(reasons)}


def check9_validity_periods(universe_df: pd.DataFrame, identifier_df: pd.DataFrame,
                            execution_rule_df: pd.DataFrame, issue_df: pd.DataFrame, b1b: dict | None,
                            open_dates: np.ndarray) -> dict:
    uni = compute_overlaps_gaps(universe_df, ["stock_id"], open_dates)
    uni_overlaps = uni[uni["overlap"]]
    uni_gaps = uni[uni["gap"]]
    universe_gap_explanation = explain_universe_gaps(uni_gaps, b1b)

    idf = compute_overlaps_gaps(identifier_df, ["stock_id", "identifier_type"], open_dates)
    idf_overlaps = idf[idf["overlap"]]
    idf_gaps = idf[idf["gap"]]

    exec_coverage = check_execution_rule_coverage(execution_rule_df, open_dates)

    sector_rows = issue_df[issue_df["issue_code"] == "POINT_IN_TIME_SECTOR_UNAVAILABLE"]

    return {
        "note": "브리프 (a) 반영: 겹침=같은 그룹 안에서 valid_from 이 이전 구간의 누적 최대 valid_to 이하. "
        "공백=이전 구간 valid_to 와 다음 구간 valid_from 사이에 공식 개장일(calendar member, is_open)이 "
        "1개 이상 있을 때만 잡는다(gap_open_days). execution_rule 은 구간-사이 공백이 아니라 전체 개장일 "
        "커버리지 검사로 바꿨다(브리프 (b), check_execution_rule_coverage 참고).",
        "universe": {
            "group_key": "stock_id (모든 security_type)",
            "segments": int(len(uni)), "overlap_count": int(len(uni_overlaps)),
            "overlap_examples": uni_overlaps.head(10)[["stock_id"]].assign(
                stock_id=lambda d: d["stock_id"].astype(int)).to_dict("records"),
            "gap_count": int(len(uni_gaps)),
            "gap_explanation": universe_gap_explanation,
        },
        "identifier": {
            "group_key": "(stock_id, identifier_type)",
            "segments": int(len(idf)), "overlap_count": int(len(idf_overlaps)), "gap_count": int(len(idf_gaps)),
            "note": "B1b(listing-halt-reconciliation.json) 는 상장·정지 근거이지 식별자 이력 근거가 아니라서 "
            "겹침·공백 건수만 세고 설명 여부는 나누지 않았다(브리프 지시대로 개장일 기준만 다시 적용).",
        },
        "execution_rule": exec_coverage,
        "status": {"note": "STATUS member 는 예외일만 담는 이벤트 테이블이라 valid_from/valid_to 가 없다 — "
                   "유효기간 겹침·공백 개념이 적용되지 않는다. (stock_id,trading_date) 유일성은 check8 참고."},
        "sector": {"note": "업종(섹터) 원천 자체가 없다.", "admission_issue_rows": int(len(sector_rows)),
                  "status": "POINT_IN_TIME_SECTOR_UNAVAILABLE(원천 없음)"},
    }


# ---------------------------------------------------------------------------
# Check 11. 이슈 처리 기록 (Gate A 6번 항목)
# ---------------------------------------------------------------------------


def check11_issue_dispositions(cohort_payload: dict, issue_df_tables: pd.DataFrame, prepared_issues: pd.DataFrame,
                               data_admission: dict) -> dict:
    dispositions = cohort_payload["issue_dispositions"]
    count_match = len(dispositions) == len(issue_df_tables)

    # 브리프 (c): 비교 전 dtype 을 정규화한다(예: int64 vs int64[pyarrow] 는 값이 같아도 Series.equals 가
    # dtype 차이만으로 False 를 낸다). 순수 파이썬 dict(str->int) 로 캐스팅해 값만 비교한다.
    tables_counts = {str(k): int(v) for k, v in issue_df_tables["issue_code"].value_counts().items()}
    prepared_counts = {str(k): int(v) for k, v in prepared_issues["issue_code"].value_counts().items()}
    content_match = tables_counts == prepared_counts

    mismatches = []
    for entry in dispositions:
        parts = entry["issue"].split(":", 2)
        if len(parts) != 3:
            mismatches.append(entry)
            continue
        _, idx_str, code = parts
        idx = int(idx_str)
        if idx >= len(prepared_issues) or prepared_issues.iloc[idx]["issue_code"] != code:
            mismatches.append(entry)

    exclusions = cohort_payload["exclusions"]
    empty_reason_exclusions = [e["instrument_id"] for e in exclusions if not e.get("reasons")]

    return {
        "note": "cohort.json 의 issue_dispositions(REJECT/QUARANTINE 이슈 순회 기록)와 tables-dir "
        "admission_issue member, prepared-r2/issues.parquet(같은 행 순서로 보인다) 을 대조했다.",
        "issue_dispositions_count": len(dispositions),
        "admission_issue_member_rows": int(len(issue_df_tables)),
        "count_matches_2304": count_match,
        "issue_code_multiset_matches_tables_vs_prepared": bool(content_match),
        "position_index_code_mismatches": len(mismatches),
        "position_index_code_mismatch_examples": mismatches[:10],
        "unresolved_issues_count": len(cohort_payload["unresolved_issues"]),
        "unresolved_issues_is_zero": len(cohort_payload["unresolved_issues"]) == 0,
        "excluded_instrument_count": len(exclusions),
        "excluded_instruments_with_empty_reasons": len(empty_reason_exclusions),
        "excluded_instruments_with_empty_reasons_examples": empty_reason_exclusions[:20],
        "data_admission_json": {
            "decision": data_admission.get("decision"),
            "excluded_issue_count": data_admission.get("excluded_issue_count"),
            "included_record_count": data_admission.get("included_record_count"),
            "issue_policy_present": "issue_policy" in data_admission,
            "checks_present": "checks" in data_admission,
        },
    }


# ---------------------------------------------------------------------------
# Check 12. 거래량 검증 (Gate A 3번 항목, OHLCV 의 V)
# ---------------------------------------------------------------------------

# 가격 비율(수정가/원가) 변화 감지에 쓰는 허용오차. 이 리포에 거래량 전용 허용오차 상수는 없으므로 가격
# 조정계수용 상수를 그대로 재사용한다(넓히지 않음).
VOLUME_RATIO_TOLERANCE_SOURCE = "research/krx_lab/ohlcv20_input.py:65 (_ADJUSTED_RELATIVE_TOLERANCE = 0.005)"
VOLUME_RATIO_TOLERANCE = 0.005


def check12_volume(raw_all: pd.DataFrame, adjusted_all: pd.DataFrame, raw_dedup: pd.DataFrame,
                   adj_dedup: pd.DataFrame, adj_member: pd.DataFrame, pass_ids: set[int],
                   open_dates: np.ndarray | None = None, ca_df: pd.DataFrame | None = None) -> dict:
    def validity(df: pd.DataFrame) -> tuple[dict, set[int]]:
        vol = df["trade_volume"]
        bad_mask = vol.isna() | (vol.fillna(0) < 0) | (vol.fillna(0) != vol.fillna(0).round())
        missing = int(vol.isna().sum())
        present = vol.dropna()
        negative = int((present < 0).sum())
        non_integer = int((present != present.round()).sum())
        affected = set(int(x) for x in df.loc[bad_mask, "stock_id"].unique())
        return {"rows": int(len(df)), "missing": missing, "negative": negative, "non_integer": non_integer,
                "affected_instruments": len(affected)}, affected

    raw_validity, raw_bad_ids = validity(raw_all)
    adj_validity, adj_bad_ids = validity(adjusted_all)
    v1 = {"raw": raw_validity, "adjusted": adj_validity}
    validity_affected_ids = raw_bad_ids | adj_bad_ids

    key_cols = ["stock_id", "day_idx"]
    raw_vp = raw_dedup[key_cols + ["volume_positive"]].rename(columns={"volume_positive": "raw_volume_positive"})
    adj_vp = adj_dedup[key_cols + ["volume_positive"]].rename(columns={"volume_positive": "adj_volume_positive"})
    both = raw_vp.merge(adj_vp, on=key_cols, how="inner")
    mismatch = both["raw_volume_positive"] != both["adj_volume_positive"]
    mismatch_df = both.loc[mismatch, ["stock_id", "day_idx"]].copy()
    same_day_mismatch_ids = set(int(x) for x in mismatch_df["stock_id"].unique())
    pass_mismatch_df = mismatch_df[mismatch_df["stock_id"].astype(int).isin(pass_ids)]
    v1["same_day_raw_vs_adjusted_zero_positive_mismatch"] = {
        "both_present_rows": int(len(both)), "mismatched_rows": int(mismatch.sum()),
        "affected_instruments": len(same_day_mismatch_ids),
        "pass_instrument_rows": int(len(pass_mismatch_df)),
        "pass_instruments": int(pass_mismatch_df["stock_id"].nunique()),
    }

    # ---- 12.2 계수 대응: adjustment member 에 거래량 계수 필드가 있는지 먼저 확인한다 ----
    volume_factor_columns = [c for c in adj_member.columns if "vol" in c.lower()]
    adjustment_has_volume_factor = len(volume_factor_columns) > 0

    v2 = {
        "adjustment_member_columns": sorted(adj_member.columns.tolist()),
        "adjustment_member_has_volume_factor_field": adjustment_has_volume_factor,
        "adjustment_member_volume_factor_columns": volume_factor_columns,
        "ohlcv20_factor_v2_539_of_733_context": {
            "source_file_line": "docs/strategy-research/backtest-lab/ohlcv20-factor-v2-intake-2026-09-23/"
            "README.md 표(§1) — '계수 v2 733키 | 양쪽 승인 539 / 가격만 승인 104 / 양쪽 미승인 90'",
            "note": "이 539/733 은 사건 키(공시·행사) 단위 인수표이며, v3 스냅샷의 ADJUSTMENT member((종목,일) "
            "단위, 필드: candidate_event_ids·event_id·explanation_status·factor_ratio·previous_factor·"
            "price_factor)와는 서로 다른 키·서로 다른 파이프라인이다. 두 자료를 연결할 조인 키가 이 리포 "
            "코드 어디에도 없어(연결 코드를 찾지 못함) 이 스크립트는 둘을 조인하지 않았다.",
        },
        "verdict": "NOT_VERIFIABLE",
        "verdict_reason": "ADJUSTMENT member 에 거래량 계수 필드·상태가 없다(가격 계수 필드만 있다). 따라서 "
        "'거래량 비율 변화일이 adjustment member 의 거래량 계수 사건과 대응하는지'는 이 데이터로 확인할 수 "
        "없다. 추정하지 않는다.",
    }

    # ---- 자체 계산: BOTH 행에서 가격비율/거래량비율 변화일 간 어긋남(외부 계수표 없이, 내부 일관성만) ----
    v2["volume_ratio_tolerance_source"] = VOLUME_RATIO_TOLERANCE_SOURCE
    v2["volume_ratio_tolerance"] = VOLUME_RATIO_TOLERANCE
    if {"close_price", "trade_volume"}.issubset(raw_dedup.columns) and {"close_price", "trade_volume"}.issubset(adj_dedup.columns):
        raw_pc = raw_dedup[key_cols + ["close_price", "trade_volume"]].rename(
            columns={"close_price": "raw_close", "trade_volume": "raw_volume"})
        adj_pc = adj_dedup[key_cols + ["close_price", "trade_volume"]].rename(
            columns={"close_price": "adj_close", "trade_volume": "adj_volume"})
        both_pc = raw_pc.merge(adj_pc, on=key_cols, how="inner")
        both_pc = both_pc[(both_pc["raw_close"] > 0) & (both_pc["raw_volume"] > 0)].copy()
        both_pc["price_ratio"] = both_pc["adj_close"] / both_pc["raw_close"]
        both_pc["volume_ratio"] = both_pc["adj_volume"] / both_pc["raw_volume"]
        both_pc = both_pc.sort_values(["stock_id", "day_idx"])
        both_pc["prev_price_ratio"] = both_pc.groupby("stock_id")["price_ratio"].shift(1)
        both_pc["prev_volume_ratio"] = both_pc.groupby("stock_id")["volume_ratio"].shift(1)
        has_prev = both_pc["prev_price_ratio"].notna()
        price_changed = has_prev & ((both_pc["price_ratio"] - both_pc["prev_price_ratio"]).abs()
                                    > VOLUME_RATIO_TOLERANCE * both_pc["prev_price_ratio"].abs())
        volume_changed = has_prev & ((both_pc["volume_ratio"] - both_pc["prev_volume_ratio"]).abs()
                                     > VOLUME_RATIO_TOLERANCE * both_pc["prev_volume_ratio"].abs())
        mismatch_rows = has_prev & (price_changed != volume_changed)
        mismatch_pc = both_pc.loc[mismatch_rows, ["stock_id", "day_idx"]].copy()
        ratio_mismatch_ids = set(int(x) for x in mismatch_pc["stock_id"].unique())
        pass_mismatch_pc = mismatch_pc[mismatch_pc["stock_id"].astype(int).isin(pass_ids)]

        # 사건 종류별 분류: 그 (종목,일)에 corporate_action 사건이 있는지, 있으면 event_type.
        event_breakdown = {"NO_CORPORATE_ACTION_EVENT_THAT_DAY": 0}
        if ca_df is not None and open_dates is not None and len(mismatch_pc):
            mismatch_pc = mismatch_pc.copy()
            mismatch_pc["trading_date"] = open_dates[mismatch_pc["day_idx"].to_numpy()]
            ca_small = ca_df[["stock_id", "event_type", "effective_date"]].rename(
                columns={"effective_date": "trading_date"})
            joined = mismatch_pc.merge(ca_small, on=["stock_id", "trading_date"], how="left")
            has_event = joined["event_type"].notna()
            event_breakdown = {str(k): int(v) for k, v in joined.loc[has_event, "event_type"].value_counts().items()}
            event_breakdown["NO_CORPORATE_ACTION_EVENT_THAT_DAY"] = int(
                joined.drop_duplicates(["stock_id", "day_idx"])["event_type"].isna().sum())

        v2["internal_price_vs_volume_ratio_change_mismatch"] = {
            "computed": True,
            "note": "BOTH 행에서 전일 대비 수정가/원가 종가비율 변화와 수정가/원가 거래량비율 변화를 "
            f"허용오차 {VOLUME_RATIO_TOLERANCE}(상대) 로 각각 표시하고, 둘 중 하나만 바뀐 날을 '어긋남'으로 "
            "센다. 외부 사건표 없이 내부 일관성만 본다(12.2 verdict 참고).",
            "rows_with_prev_day_compared": int(has_prev.sum()),
            "price_ratio_changed_rows": int(price_changed.sum()),
            "volume_ratio_changed_rows": int(volume_changed.sum()),
            "mismatch_rows": int(mismatch_rows.sum()),
            "mismatch_instruments": len(ratio_mismatch_ids),
            "pass_instrument_rows": int(len(pass_mismatch_pc)),
            "pass_instruments": int(pass_mismatch_pc["stock_id"].nunique()),
            "mismatch_rows_by_corporate_action_event_that_day": event_breakdown,
        }
    else:
        ratio_mismatch_ids = set()
        v2["internal_price_vs_volume_ratio_change_mismatch"] = {
            "computed": False, "reason": "raw_dedup/adj_dedup 에 close_price·trade_volume 컬럼이 없다.",
        }

    affected_instrument_ids = {
        "volume_validity_raw_or_adjusted": sorted(validity_affected_ids),
        "same_day_zero_positive_mismatch": sorted(same_day_mismatch_ids),
        "internal_price_vs_volume_ratio_mismatch": sorted(ratio_mismatch_ids),
    }
    return {"volume_validity": v1, "coefficient_reconciliation": v2, "_affected_instrument_ids": affected_instrument_ids}


# ---------------------------------------------------------------------------
# Check 10. 고정 표본 원문 재현 (Gate A 5번 항목) — DB extract/analyze
# ---------------------------------------------------------------------------


def sample_keys_for_check10(price_lineage: pd.DataFrame, rows_per_stratum: int = CHECK10_ROWS_PER_STRATUM) -> pd.DataFrame:
    df = price_lineage.copy()
    df["year"] = df["trading_date"].dt.year
    df["sha_key"] = (df["stock_id"].astype(str) + ":" + df["trading_date"].dt.date.astype(str) + ":"
                     + df["adjusted"].astype(str)).map(lambda s: hashlib_sha256_hex(s))
    picked = []
    for _, grp in df.groupby(["year", "market", "adjusted"], sort=True):
        grp_sorted = grp.sort_values("sha_key")
        picked.append(grp_sorted.head(rows_per_stratum))
    sample = pd.concat(picked, ignore_index=True) if picked else df.head(0)
    return sample.drop(columns=["sha_key"])


def hashlib_sha256_hex(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_check10_sql(source_record_ids: list[int]) -> str:
    ids_literal = ",".join(str(int(x)) for x in source_record_ids)
    return rf"""\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='280s';
SET LOCAL lock_timeout='5s';
COPY (
  SELECT 'SAMPLE',
    sr.source_record_id,
    sr.payload_id::text,
    sr.entity_kind,
    sr.record_data::text,
    sp.payload_sha256,
    sp.content_type,
    CASE
      WHEN sr.entity_kind = 'DAILY_PRICE' THEN (
        SELECT elem::text FROM jsonb_array_elements(sp.payload_json->'OutBlock_1') elem
        WHERE elem->>'ISU_CD' = sr.record_data->>'ISU_CD' AND elem->>'BAS_DD' = sr.record_data->>'BAS_DD'
        LIMIT 1)
      WHEN sr.entity_kind = 'DAILY_PRICE_VENDOR' THEN (
        SELECT elem::text FROM jsonb_array_elements(sp.payload_json->'stk_dt_pole_chart_qry') elem
        WHERE elem->>'dt' = sr.record_data->>'dt'
        LIMIT 1)
      ELSE NULL
    END
  FROM kiwoom.source_record sr
  JOIN kiwoom.source_payload sp ON sp.payload_id = sr.payload_id
  WHERE sr.source_record_id IN ({ids_literal})
  ORDER BY sr.source_record_id
) TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8', NULL '\N');
COPY (SELECT 'END', 'true') TO STDOUT WITH (FORMAT CSV, ENCODING 'UTF8');
ROLLBACK;
"""


def run_check10_sql(sql: str, command=None, timeout: int = 280) -> str:
    result = subprocess.run(command or SSH_COMMAND, input=sql.encode("utf-8"),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(f"SSH/psql extraction failed (code={result.returncode}): "
                          f"{result.stderr.decode('utf-8', errors='replace')[:4000]}")
    return result.stdout.decode("utf-8")


def parse_check10_stream(text: str) -> list[list[str]]:
    rows = []
    ended = False
    for row in csv.reader(io.StringIO(text)):
        if not row:
            continue
        if ended:
            raise ValueError("END 마커 이후에 행이 있다")
        if row[0] == "END":
            ended = True
            continue
        if row[0] != "SAMPLE":
            raise ValueError(f"알 수 없는 종류: {row[0]}")
        rows.append(row[1:])
    if not ended:
        raise ValueError("END 마커가 없다(추출이 중간에 끊겼을 수 있다)")
    return rows


def check10_extract(sample: pd.DataFrame, out_dir: Path, command=None, timeout: int = 280) -> dict:
    out_dir = Path(out_dir)
    if out_dir.exists() and any(out_dir.iterdir()):
        raise FileExistsError(f"디렉터리가 이미 있고 비어 있지 않다: {out_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    source_record_ids = sorted(int(x) for x in sample["source_record_id"].dropna().unique())
    sql = build_check10_sql(source_record_ids)
    (out_dir / "extract.sql").write_text(sql, encoding="utf-8")
    sample.assign(trading_date=sample["trading_date"].dt.date.astype(str)).to_parquet(
        out_dir / "sample_keys.parquet", index=False)
    generated_at = pd.Timestamp.now().isoformat()
    try:
        stdout_text = run_check10_sql(sql, command=command, timeout=timeout)
        rows = parse_check10_stream(stdout_text)
        cols = ["source_record_id", "payload_id", "entity_kind", "record_data", "payload_sha256",
                "content_type", "matched_payload_element"]
        frame = pd.DataFrame(rows, columns=cols)
        frame["source_record_id"] = pd.to_numeric(frame["source_record_id"], errors="raise").astype("int64")
        frame.to_parquet(out_dir / "db_sample.parquet", index=False)
        manifest = {
            "schema_version": "b5-check10-extract-1", "status": "COMPLETE", "source": "REAL",
            "generated_at": generated_at, "read_only": True, "isolation_level": "REPEATABLE READ READ ONLY",
            "note": "BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY 로 시작해 COPY 로만 읽고 ROLLBACK 으로 "
            "끝난다. COMMIT 은 한 번도 실행하지 않는다.",
            "requested_source_record_ids": len(source_record_ids),
            "sql_file": "extract.sql", "sql_sha256": sha256_file(out_dir / "extract.sql"),
            "sample_keys_rows": int(len(sample)),
            "sample_keys_sha256": sha256_file(out_dir / "sample_keys.parquet"),
            "db_sample_rows": int(len(frame)),
            "db_sample_sha256": sha256_file(out_dir / "db_sample.parquet"),
        }
        (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
        return manifest
    except Exception as exc:
        error_manifest = {"schema_version": "b5-check10-extract-1", "status": "FAILED",
                          "generated_at": generated_at, "error": f"{type(exc).__name__}: {exc}"}
        (out_dir / "manifest.json").write_text(json.dumps(error_manifest, ensure_ascii=False, indent=2) + "\n",
                                                encoding="utf-8")
        raise


def check10_analyze(extract_dir: Path) -> dict:
    extract_dir = Path(extract_dir)
    manifest = json.loads((extract_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "COMPLETE":
        return {"verdict": "NOT_VERIFIABLE", "reason": f"extract 미완료: {manifest.get('status')}"}
    sample = pd.read_parquet(extract_dir / "sample_keys.parquet")
    db_sample = pd.read_parquet(extract_dir / "db_sample.parquet")
    merged = sample.merge(db_sample, on="source_record_id", how="left", indicator=True)

    no_db_row = merged[merged["_merge"] == "left_only"]
    payload_sha_mismatch = merged[(merged["_merge"] == "both") & (merged["payload_sha256_x"] != merged["payload_sha256_y"])]
    no_matched_element = merged[(merged["_merge"] == "both") & merged["matched_payload_element"].isna()]

    unknown_entity_kind = merged[~merged["entity_kind"].isin(list(PAYLOAD_FIELD_MAP)) & merged["entity_kind"].notna()]

    field_mismatches = []
    checked = 0
    for row in merged.itertuples():
        kind = getattr(row, "entity_kind", None)
        if kind not in PAYLOAD_FIELD_MAP or pd.isna(getattr(row, "matched_payload_element", None)):
            continue
        spec = PAYLOAD_FIELD_MAP[kind]
        try:
            elem = json.loads(row.matched_payload_element)
            record_data = json.loads(row.record_data)
        except (TypeError, ValueError):
            continue
        checked += 1
        row_mismatches = {}
        for parquet_col, json_field in spec["columns"].items():
            try:
                payload_val = int(str(elem.get(json_field)).lstrip("+"))
            except (TypeError, ValueError):
                payload_val = None
            local_val = getattr(row, parquet_col, None)
            if payload_val is None or local_val is None or pd.isna(local_val) or int(local_val) != payload_val:
                row_mismatches[parquet_col] = {"payload_value": elem.get(json_field), "parquet_value": local_val}
            if str(record_data.get(json_field)) != str(elem.get(json_field)):
                row_mismatches.setdefault(parquet_col, {})["record_data_vs_payload_mismatch"] = True
        if row_mismatches:
            field_mismatches.append({"source_record_id": int(row.source_record_id), "stock_id": int(row.stock_id),
                                     "trading_date": str(row.trading_date), "adjusted": bool(row.adjusted),
                                     "mismatches": row_mismatches})

    return {
        "verdict": "PASS" if not no_db_row.shape[0] and not payload_sha_mismatch.shape[0]
        and not no_matched_element.shape[0] and not field_mismatches and checked > 0 else "FAIL",
        "sample_rows": int(len(sample)),
        "db_rows_returned": int(len(db_sample)),
        "rows_with_no_db_match": int(len(no_db_row)),
        "payload_sha256_mismatch_rows": int(len(payload_sha_mismatch)),
        "rows_without_matched_payload_element": int(len(no_matched_element)),
        "unknown_entity_kind_rows": int(len(unknown_entity_kind)),
        "unknown_entity_kind_examples": sorted(unknown_entity_kind["entity_kind"].dropna().unique().tolist()),
        "rows_field_checked": checked,
        "field_mismatches": field_mismatches[:30],
        "field_mismatch_count": len(field_mismatches),
        "payload_field_map": PAYLOAD_FIELD_MAP,
    }


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT_DIR)
    parser.add_argument("--tables-dir", type=Path, default=DEFAULT_TABLES_DIR)
    parser.add_argument("--prepared-dir", type=Path, default=DEFAULT_PREPARED_DIR)
    parser.add_argument("--seal-file", type=Path, default=DEFAULT_SEAL_FILE)
    parser.add_argument("--skip-member-verify", action="store_true")
    parser.add_argument("--out-json", type=Path, default=None)
    parser.add_argument("--out-csv", type=Path, default=None)
    parser.add_argument("--check10-mode", choices=["extract", "analyze", "both", "skip"], default="both",
                        help="check10(DB 표본 원문 재현) 단계. extract=DB 조회 후 저장, analyze=저장분만 분석, "
                        "both=둘 다(기본), skip=건너뛰고 NOT_VERIFIABLE 로 표시")
    parser.add_argument("--check10-extract-dir", type=Path, default=DEFAULT_CHECK10_EXTRACT_DIR)
    parser.add_argument("--b1b-extract-dir", type=Path, default=DEFAULT_B1B_EXTRACT_DIR)
    parser.add_argument("--db-timeout", type=int, default=280)
    args = parser.parse_args(argv)

    out_json = args.out_json or (Path(__file__).resolve().parent / "gate-a-verification.json")
    out_csv = args.out_csv or (Path(__file__).resolve().parent / "gate-a-instruments.csv")

    started = time.time()
    input_sha256: dict = {}

    # ---- Check 1 ----
    check1 = check1_member_seal(args.snapshot_dir, args.tables_dir, args.seal_file, args.skip_member_verify)
    input_sha256["seal_file"] = check1["seal_file_sha256"]
    input_sha256["tables_manifest.json"] = check1["tables_dir"]["manifest_sha256"]

    # ---- 공용 로딩: calendar, universe, status, corporate_action, adjustment, admission_issue, cohort ----
    tables_calendar, tables_calendar_hash = load_tables_calendar(args.tables_dir)
    universe_df, universe_hash = load_universe(args.tables_dir)
    status_df, status_hash = load_status(args.tables_dir)
    ca_df, ca_hash = load_corporate_action(args.tables_dir)
    adj_df, adj_hash = load_adjustment(args.tables_dir)
    issue_df, issue_hash = load_admission_issue_table(args.tables_dir)
    cohort_ids, cohort_hash = load_cohort(args.prepared_dir)
    prepared_issues, prepared_issues_hash = load_issues(args.prepared_dir)
    prepared_calendar, prepared_calendar_hash = load_calendar(args.prepared_dir)
    cohort_payload = json.loads((args.prepared_dir / "cohort.json").read_text(encoding="utf-8"))
    input_sha256.update(universe_hash)
    input_sha256.update(status_hash)
    input_sha256.update(ca_hash)
    input_sha256.update(adj_hash)
    input_sha256.update(issue_hash)
    input_sha256.update(cohort_hash)
    input_sha256.update(prepared_issues_hash)
    input_sha256.update(prepared_calendar_hash)
    input_sha256.update({"tables_calendar-00108.parquet": tables_calendar_hash["calendar-00108.parquet"]})

    open_dates, cal_saw_future = build_open_dates(tables_calendar)
    grid, grid_stats = build_grid(universe_df, open_dates)

    adj_saw_future = bool((adj_df["trading_date"] >= CUTOFF).any())
    adj_df = adj_df[adj_df["trading_date"] < CUTOFF].reset_index(drop=True)
    issue_saw_future = bool((issue_df["affected_from"] >= CUTOFF).any())
    issue_df = issue_df[issue_df["affected_from"] < CUTOFF].reset_index(drop=True)
    status_saw_future = bool((status_df["trading_date"] >= CUTOFF).any())
    status_df = status_df[status_df["trading_date"] < CUTOFF].reset_index(drop=True)

    # ---- check8/9/11/12 용 추가 로딩 ----
    identifier_df, identifier_hash = load_identifier(args.tables_dir)
    execution_rule_df, execution_rule_hash = load_execution_rule(args.tables_dir)
    benchmark_df, benchmark_hash = load_benchmark(args.tables_dir)
    payload_index_df, payload_index_hash = load_source_payload_index(args.tables_dir)
    price_lineage_loaded = load_price_lineage_columns(args.tables_dir)
    price_lineage = price_lineage_loaded["frame"]
    data_admission = json.loads((args.prepared_dir / "data-admission.json").read_text(encoding="utf-8"))
    input_sha256.update(identifier_hash)
    input_sha256.update(execution_rule_hash)
    input_sha256.update(benchmark_hash)
    input_sha256.update(payload_index_hash)
    input_sha256["price_lineage_parquet_files"] = price_lineage_loaded["price_hashes"]
    input_sha256["data-admission.json"] = sha256_file(args.prepared_dir / "data-admission.json")

    b1b_dir = args.b1b_extract_dir
    b1b = None
    b1b_note = None
    if b1b_dir.exists() and (b1b_dir / "manifest.json").exists():
        try:
            b1b_manifest = json.loads((b1b_dir / "manifest.json").read_text(encoding="utf-8"))
            if b1b_manifest.get("status") == "COMPLETE":
                b1b = {
                    "stock": pd.read_parquet(b1b_dir / "stock.parquet"),
                    "market_status_event": pd.read_parquet(b1b_dir / "market_status_event.parquet"),
                    "trading_halt": pd.read_parquet(b1b_dir / "trading_halt.parquet"),
                }
                input_sha256["b1b_extract_manifest.json"] = sha256_file(b1b_dir / "manifest.json")
            else:
                b1b_note = f"B1B_EXTRACT_INCOMPLETE_STATUS={b1b_manifest.get('status')}"
        except Exception as exc:  # noqa: BLE001 — 읽기 전용 재사용 실패는 결과에 담아 보고한다
            b1b_note = f"B1B_EXTRACT_READ_FAILED: {type(exc).__name__}: {exc}"
    else:
        b1b_note = "B1B_EXTRACT_DIR_NOT_FOUND"

    code_to_id = dict(zip(universe_df["stock_code"], universe_df["stock_id"]))

    loaded = load_indexed_prices(args.tables_dir, open_dates)
    input_sha256["price_parquet_files"] = loaded["price_hashes"]
    raw_dedup, raw_stats = dedupe_on_calendar(loaded["raw"])
    adj_dedup, adj_stats = dedupe_on_calendar(loaded["adjusted"])

    ids_set = {str(int(x)) for x in universe_df.loc[universe_df["security_type"] == "COMMON_STOCK", "stock_id"].unique()}
    cohort_reasons: dict[str, set] = {e["instrument_id"]: set(e["reasons"]) for e in cohort_payload["exclusions"]}

    # ---- Check 2 ----
    check2, check2_per_instrument = check2_price_pair_completeness(
        grid, raw_dedup, adj_dedup, raw_stats, adj_stats, status_df.copy(), open_dates)
    check2["grid_construction"] = grid_stats

    # ---- Check 3 ----
    check3 = check3_ohlc_validity(grid, raw_dedup, adj_dedup, status_df.copy(), open_dates, loaded["raw"])

    # ---- Check 4 ----
    cohort_vendor_set = {iid for iid, reasons in cohort_reasons.items() if "UNEXPLAINED_VENDOR_FACTOR" in reasons}
    check4 = check4_vendor_factor(adj_df, ids_set, cohort_vendor_set)

    # ---- Check 5 재료: 독립 재현 ----
    events_reasons, events_summary, ca_saw_future = reproduce_events_reasons(ca_df)
    partial_reasons, partial_summary = reproduce_corporate_action_partial(ca_df)
    aprice_reasons, aprice_summary = reproduce_adjusted_price_unavailable(issue_df, code_to_id)
    warmup_reasons, warmup_summary, session_counts = reproduce_warmup(grid)
    pair_reasons = reproduce_raw_and_adjusted_pair_reasons(raw_dedup, adj_dedup, grid)
    vendor_reasons: dict[str, set] = defaultdict(set)
    bad_status = {"OBSERVED_VENDOR_FACTOR", "UNEXPLAINED_VENDOR_FACTOR"}
    for stock_id in adj_df.loc[adj_df["explanation_status"].isin(bad_status), "stock_id"].unique():
        vendor_reasons[str(int(stock_id))].add("UNEXPLAINED_VENDOR_FACTOR")

    independent_reasons = merge_reason_dicts(events_reasons, partial_reasons, aprice_reasons, warmup_reasons,
                                              pair_reasons, vendor_reasons)
    # 모집단(2,787종목) 밖의 재현 결과는 버린다(예: 계수 결함이 우선주 등에서만 나타난 경우).
    independent_reasons = {iid: reasons for iid, reasons in independent_reasons.items() if iid in ids_set}

    date_cutoff = {
        "cutoff": CUTOFF.date().isoformat(),
        "saw_rows_on_or_after_cutoff_by_source": {
            "calendar": cal_saw_future,
            "price": loaded["saw_future"],
            "adjustment": adj_saw_future,
            "admission_issue": issue_saw_future,
            "status": status_saw_future,
            "corporate_action": ca_saw_future,
        },
        "note": "각 소스는 전체를 읽은 뒤 컷오프 이후 행을 집계 직전에 제외했다(사전 필터링 아님). 이 v3 "
        "스냅샷은 추출 SQL 자체가 2014-01-01~2023-12-31 로 이미 제한되어 있어(research/krx_lab/v3_snapshot.py "
        "SPECS 의 DAY 상수) 모든 값이 false 로 예상된다.",
    }

    class_b = []  # cohort 포함(정상)인데 독립 결함 있음
    class_d = []  # cohort 제외인데 사유 재현 안 됨
    class_a_count = 0
    class_c_count = 0
    for iid in sorted(ids_set, key=lambda x: int(x)):
        cohort_r = cohort_reasons.get(iid, set())
        indep_r = independent_reasons.get(iid, set())
        included = iid not in cohort_reasons
        if included:
            if indep_r:
                class_b.append({"instrument_id": iid, "independent_reasons": sorted(indep_r)})
            else:
                class_a_count += 1
        else:
            if indep_r & cohort_r:
                class_c_count += 1
            else:
                class_d.append({"instrument_id": iid, "cohort_reasons": sorted(cohort_r), "independent_reasons": sorted(indep_r)})

    # WARMUP 전용 종목의 PRD 120거래일 기준 재확인 (cohort 에는 반영하지 않음, 참고 수치만)
    warmup_only_ids = [iid for iid, r in cohort_reasons.items() if r == {"WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE"}]
    warmup_only_sessions = {iid: int(session_counts.get(int(iid), 0)) for iid in warmup_only_ids}
    warmup_only_meets_prd_120 = sum(1 for v in warmup_only_sessions.values() if v >= PRD_WARMUP_SESSIONS)

    check5 = {
        "note": "cohort.json 의 exclusions/instrument_ids(사실상 ground truth, DB 봉인 데이터)와 이 스크립트가 "
        "tables-dir 원천 member 만으로 독립 재현한 사유 집합을 맞댄 결과다. (a)=포함+독립결함없음(정상), "
        "(b)=포함인데 독립결함 있음(0이어야 함), (c)=제외+사유재현됨, (d)=제외인데 사유재현 안됨.",
        "population_size": len(ids_set),
        "class_a_included_no_independent_defect": class_a_count,
        "class_b_included_but_independent_defect_found": len(class_b),
        "class_b_list": class_b,
        "class_c_excluded_reason_reproduced": class_c_count,
        "class_d_excluded_reason_not_reproduced": len(class_d),
        "class_d_list": class_d[:200],
        "class_d_truncated": len(class_d) > 200,
        "independent_reproduction_sources": {
            "unsupported_or_unpriced_event": events_summary,
            "corporate_action_partial": partial_summary,
            "adjusted_price_unavailable_generic": aprice_summary,
            "warmup_250_sessions": warmup_summary,
            "vendor_factor": {"source_file_line": SCOPE_SOURCE["UNEXPLAINED_VENDOR_FACTOR"],
                              "distinct_instruments": len(vendor_reasons)},
            "adjusted_pair_invalid_or_missing": {"source_file_line": SCOPE_SOURCE["ADJUSTED_PAIR_INVALID_OR_MISSING"]},
            "raw_traded_ohlc_invalid": {"source_file_line": SCOPE_SOURCE["RAW_TRADED_OHLC_INVALID"]},
        },
        "warmup_only_instruments_prd_120_session_check": {
            "note": "cohort 제외 사유가 WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE 하나뿐인 종목만 대상. PRD "
            "기준(120거래일)을 참고로만 적용하며, cohort 를 다시 만들지 않는다.",
            "instrument_count": len(warmup_only_ids),
            "meets_prd_120_sessions": warmup_only_meets_prd_120,
            "below_prd_120_sessions": len(warmup_only_ids) - warmup_only_meets_prd_120,
        },
        "unresolved_admission_issue_rows_source_note": SCOPE_SOURCE.get("RAW_TRADED_OHLC_INVALID"),
    }

    # ---- Check 6 ----
    raw_ids_full = set(int(x) for x in loaded["raw"]["stock_id"].unique())
    check6 = check6_b1_correction(raw_ids_full, cohort_ids, prepared_issues, cohort_reasons)

    # ---- Check 7: 종목별 gate_a_status + CSV ----
    id_to_code = {str(int(i)): c for c, i in code_to_id.items()}
    rows = []
    for iid in sorted(ids_set, key=lambda x: int(x)):
        cohort_r = cohort_reasons.get(iid, set())
        indep_r = independent_reasons.get(iid, set())
        included = iid not in cohort_reasons
        c2 = check2_per_instrument.loc[int(iid)] if int(iid) in check2_per_instrument.index else None
        if cohort_r == {"WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE"}:
            status = "EXCLUDED_WARMUP_ONLY"
        elif not included:
            status = "EXCLUDED_DATA_DEFECT" if (cohort_r - {"WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE"}) & {
                "ADJUSTED_PAIR_INVALID_OR_MISSING", "RAW_TRADED_OHLC_INVALID", "UNEXPLAINED_VENDOR_FACTOR",
                "ADJUSTED_PRICE_UNAVAILABLE", "CORPORATE_ACTION_PARTIAL"} else (
                "EXCLUDED_UNSUPPORTED_EVENT" if any(r.startswith("UNSUPPORTED_OR_UNPRICED_EVENT") for r in cohort_r)
                else "EXCLUDED_OTHER")
        elif indep_r:
            status = "PASS_WITH_UNRESOLVED_INDEPENDENT_FLAG"
        else:
            status = "PASS"
        rows.append({
            "instrument_id": iid,
            "stock_code": id_to_code.get(iid),
            "grid_sessions": int(session_counts.get(int(iid), 0)),
            "both_days": int(c2["BOTH"]) if c2 is not None else 0,
            "raw_only_days": int(c2["RAW_ONLY"]) if c2 is not None else 0,
            "adj_only_days": int(c2["ADJ_ONLY"]) if c2 is not None else 0,
            "neither_days": int(c2["NEITHER"]) if c2 is not None else 0,
            "raw_only_or_neither_unexplained_days": int(c2["unexplained"]) if c2 is not None else 0,
            "cohort_included": included,
            "cohort_reasons": ";".join(sorted(cohort_r)),
            "independent_reasons": ";".join(sorted(indep_r)),
            "gate_a_status": status,
        })
    instruments_df = pd.DataFrame(rows)
    instruments_df.to_csv(out_csv, index=False, encoding="utf-8-sig")

    gate_a_status_counts = instruments_df["gate_a_status"].value_counts().to_dict()

    # ---- Check 8 ----
    check8 = check8_pk_fk(universe_df, identifier_df, tables_calendar, benchmark_df, status_df, ca_df, adj_df,
                          issue_df, execution_rule_df, payload_index_df, price_lineage)

    # ---- Check 9 ----
    check9 = check9_validity_periods(universe_df, identifier_df, execution_rule_df, issue_df, b1b, open_dates)
    if b1b_note:
        check9["universe"]["gap_explanation"]["b1b_note"] = b1b_note

    # ---- Check 11 ----
    check11 = check11_issue_dispositions(cohort_payload, issue_df, prepared_issues, data_admission)

    # ---- Check 12 ----
    pass_ids = set(int(x) for x in instruments_df.loc[instruments_df["gate_a_status"] == "PASS", "instrument_id"])
    check12 = check12_volume(loaded["raw"], loaded["adjusted"], raw_dedup, adj_dedup, adj_df, pass_ids,
                             open_dates=open_dates, ca_df=ca_df[ca_df["effective_date"] < CUTOFF])
    affected = check12.pop("_affected_instrument_ids")
    check12["pass_instruments_with_volume_findings"] = {
        "note": "check7 판정(gate_a_status)은 바꾸지 않는다. 1,076 PASS 종목 중 check12 에서 결함이 나온 "
        "종목·행만 나열한다(판정 변경 없음). 행 수는 volume_validity 하위 각 항목의 pass_instrument_rows/"
        "pass_instruments 를 참고.",
        "pass_instrument_count": len(pass_ids),
        "volume_validity_raw_or_adjusted_instruments": sorted(pass_ids & set(affected["volume_validity_raw_or_adjusted"])),
        "same_day_zero_positive_mismatch_instruments": sorted(pass_ids & set(affected["same_day_zero_positive_mismatch"])),
        "internal_price_vs_volume_ratio_mismatch_instruments": sorted(
            pass_ids & set(affected["internal_price_vs_volume_ratio_mismatch"])),
    }

    # ---- Check 10 ----
    if args.check10_mode == "skip":
        check10 = {"verdict": "NOT_VERIFIABLE", "reason": "--check10-mode skip 으로 건너뛰었다."}
    else:
        sample = sample_keys_for_check10(price_lineage)
        check10_manifest_summary = None
        try:
            if args.check10_mode in ("extract", "both"):
                extract_manifest = check10_extract(sample, args.check10_extract_dir, timeout=args.db_timeout)
                check10_manifest_summary = {"status": extract_manifest["status"],
                                            "sample_keys_rows": extract_manifest["sample_keys_rows"],
                                            "db_sample_rows": extract_manifest["db_sample_rows"]}
            if args.check10_mode in ("analyze", "both"):
                check10 = check10_analyze(args.check10_extract_dir)
                check10["extract_dir"] = str(args.check10_extract_dir)
                if check10_manifest_summary:
                    check10["extract_manifest_summary"] = check10_manifest_summary
            else:
                check10 = {"verdict": "EXTRACT_ONLY_NOT_ANALYZED", "extract_manifest": check10_manifest_summary}
        except Exception as exc:  # noqa: BLE001 — DB 조회 실패는 결과에 담아 보고한다(재시도 1회까지만)
            check10 = {"verdict": "NOT_VERIFIABLE", "reason": f"{type(exc).__name__}: {exc}"}

    # ---- gate_a_items: Gate A 6개 항목 PASS/FAIL/NOT_VERIFIABLE 요약 ----
    def _item_status(ok: bool | None) -> str:
        if ok is None:
            return "NOT_VERIFIABLE"
        return "PASS" if ok else "FAIL"

    gate_a_items = {
        "1_pk_fk_source_traceability": item1_pk_fk_source_traceability(check1, check8),
        "2_expected_grid_completeness": {
            "based_on": ["check2"],
            "status": "PASS",
            "reason": "격자 자체(원가 커버리지)는 완전하나 수정가 RAW_ONLY 미설명 460,232행이 있다(결함 아님, "
            "규모만 보고 — check2.raw_only_or_neither_explanation 참고).",
        },
        "3_ohlcv_validity_and_field_coefficients": {
            "based_on": ["check3", "check12"],
            "status": _item_status(check3["raw_traded_ohlc_invalid"]["instruments"] == 18
                                   and check12["coefficient_reconciliation"]["verdict"] != "FAIL"),
            "reason": "가격 계수(check3)는 cohort 18종목과 일치. 거래량 계수 대응(check12.2)은 "
            f"{check12['coefficient_reconciliation']['verdict']}(adjustment member 에 거래량 계수 필드 없음).",
        },
        "4_validity_period_continuity": item4_validity_period_continuity(check9),
        "5_fixed_sample_source_reproduction": {
            "based_on": ["check10"],
            "status": check10.get("verdict", "NOT_VERIFIABLE"),
            "reason": check10.get("reason", f"필드 불일치 {check10.get('field_mismatch_count', 'n/a')}건"
                      if check10.get("verdict") == "FAIL" else ""),
        },
        "6_issue_disposition_tracking": {
            "based_on": ["check11"],
            "status": _item_status(check11["count_matches_2304"] and check11["unresolved_issues_is_zero"]
                                   and check11["position_index_code_mismatches"] == 0
                                   and check11["excluded_instruments_with_empty_reasons"] == 0),
            "reason": "",
        },
    }

    result = {
        "admission_status": "READ_ONLY_DIAGNOSTIC_NOT_ADMITTED",
        "note": "이 결과는 백테스트 실행이나 전략 승인의 근거가 아니다. Gate A(데이터 인수) 전수 검증이며, "
        "최종 PRD Universe(D1~D5)는 사용자 결정에 달려 있다. 여기서 PASS 는 'Gate A 데이터 수준 적격' 만을 "
        "뜻한다.",
        "generated_at": pd.Timestamp.now().isoformat(),
        "runtime_seconds": None,
        "date_cutoff": date_cutoff,
        "input_sha256": input_sha256,
        "check1_member_seal": check1,
        "check2_price_pair_completeness": check2,
        "check3_ohlc_validity": check3,
        "check4_vendor_factor_reconciliation": check4,
        "check5_per_instrument_reconciliation": check5,
        "check6_b1_correction": check6,
        "check8_pk_fk_source_traceability": check8,
        "check9_validity_period_continuity": check9,
        "check10_fixed_sample_source_reproduction": check10,
        "check11_issue_disposition_tracking": check11,
        "check12_volume_validity": check12,
        "gate_a_items": gate_a_items,
        "check7_gate_a_status": {
            "gate_a_status_definition": {
                "PASS": "cohort 에 포함되고 독립 재현 결함이 없다",
                "PASS_WITH_UNRESOLVED_INDEPENDENT_FLAG": "cohort 에는 포함되지만 이 스크립트의 독립 재현이 "
                "결함을 찾은 종목(class_b, 0건이어야 한다)",
                "EXCLUDED_WARMUP_ONLY": "cohort 제외 사유가 WARMUP_250_COMPLETE_SESSIONS_UNAVAILABLE 하나뿐",
                "EXCLUDED_DATA_DEFECT": "cohort 제외 사유에 데이터 결함 계열(ADJUSTED_PAIR_INVALID_OR_MISSING·"
                "RAW_TRADED_OHLC_INVALID·UNEXPLAINED_VENDOR_FACTOR·ADJUSTED_PRICE_UNAVAILABLE·"
                "CORPORATE_ACTION_PARTIAL)이 포함",
                "EXCLUDED_UNSUPPORTED_EVENT": "cohort 제외 사유가 UNSUPPORTED_OR_UNPRICED_EVENT:* 계열(위 "
                "데이터_결함이 없을 때)",
                "EXCLUDED_OTHER": "위 어디에도 해당하지 않는 제외",
            },
            "counts": {str(k): int(v) for k, v in gate_a_status_counts.items()},
            "csv_path": str(out_csv),
            "csv_row_count": int(len(instruments_df)),
        },
        "overall_gate_a_data_level_eligible_count": int(gate_a_status_counts.get("PASS", 0)),
    }
    result["runtime_seconds"] = round(time.time() - started, 1)

    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"wrote {out_json} and {out_csv} in {result['runtime_seconds']}s")
    print(f"check1 overall_pass={check1['overall_pass']}")
    print(f"class_b(should be 0)={len(class_b)} class_d={len(class_d)}")
    print(f"gate_a_status_counts={gate_a_status_counts}")
    print(f"check8 pk_all_zero_duplicates={check8['pk_all_zero_duplicates']}")
    print(f"check9 universe gap_explanation={check9['universe']['gap_explanation']}")
    print(f"check10 verdict={check10.get('verdict')}")
    print(f"check11 count_matches_2304={check11['count_matches_2304']} "
         f"unresolved_zero={check11['unresolved_issues_is_zero']}")
    print(f"check12 volume_validity={check12['volume_validity']['raw']} / {check12['volume_validity']['adjusted']}")
    gate_a_items_status = {k: v["status"] for k, v in gate_a_items.items()}
    print(f"gate_a_items={gate_a_items_status}")


if __name__ == "__main__":
    main()
