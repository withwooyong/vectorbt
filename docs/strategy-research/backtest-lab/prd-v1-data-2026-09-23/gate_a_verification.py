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
import json
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
    cols = ["stock_id", "trading_date", "explanation_status", "candidate_event_ids"]
    df = pd.read_parquet(fp, columns=cols)
    df["trading_date"] = pd.to_datetime(df["trading_date"])
    return df, {fp.name: sha256_file(fp)}


def load_admission_issue_table(tables_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = tables_dir / "admission_issue-00114.parquet"
    cols = ["issue_code", "affected_scope", "affected_from", "affected_to", "decision"]
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


if __name__ == "__main__":
    main()
