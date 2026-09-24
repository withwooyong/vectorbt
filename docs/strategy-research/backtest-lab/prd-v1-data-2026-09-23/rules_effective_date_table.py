"""PRD v1 트랙 B2b: 증권거래세 SELL_TAX 규칙을 법령 원문으로 재확인해 새 효력일별 rules.parquet 를 만드는 스크립트.

발견한 두 문제를 고친다.
  1. 기존 표는 SELL_TAX 가 2015-01-01 부터 시작해 2014-01-01~2014-12-31 이 비어 있다(소비자가 2014년
     매도에서 예외를 던짐).
  2. 법령 효력일은 「양도분」 기준이고, 거래소 매매의 양도는 결제일(T+2 거래소 영업일)이다. 소비자
     (`research/krx_lab/v3_execution.py:369`, `v3_market.py:73-83,102`)는 체결일(trade date)로
     `SELL_TAX` 를 조회하므로(결제일이 아니라), 경계를 체결일 기준으로 다시 계산해야 한다.

이 스크립트는 다음을 절대 하지 않는다.
  - 수익률 계산이나 백테스트 실행
  - `../vectorbt-data/krx-v3-20260921-prepared-r2/` 등 기존 파일 쓰기/수정 (읽기 전용으로 연다)
  - `research/krx_lab/` 아래 코드 수정
  - PostgreSQL·네트워크 접속

세율 상수의 출처는 팀장이 law.go.kr 에서 확인한 원문(2026-09-24)이다. 농어촌특별세율은 원문 표가 텍스트로
추출되지 않아 2차 확인이며, 기존 표의 값을 그대로 유지한다(KOSPI 매도분 0.15%, KOSDAQ 없음).

사용법:
    .venv/Scripts/python.exe -X utf8 rules_effective_date_table.py \
        --prepared-dir ../vectorbt-data/krx-v3-20260921-prepared-r2 \
        --out-data-dir ../vectorbt-data/krx-prd-v1-b2b-20260924 \
        --out rules-effective-date-table.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from decimal import Decimal
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from universe_diagnosis import sha256_file  # noqa: E402  (같은 디렉터리 유틸 재사용)

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))
from research.krx_lab.v3_market import V3MarketRules  # noqa: E402

DEFAULT_PREPARED_DIR = _REPO_ROOT.parent / "vectorbt-data" / "krx-v3-20260921-prepared-r2"
DEFAULT_OUT_DATA_DIR = _REPO_ROOT.parent / "vectorbt-data" / "krx-prd-v1-b2b-20260924"

WINDOW_START = pd.Timestamp("2014-01-01")
WINDOW_END = pd.Timestamp("2023-12-31")
MARKETS = ["KOSDAQ", "KOSPI"]

# 소비자(v3_execution.py:369 -> costs(day, ...) -> rules.fees(day, ...))가 매도 세율을 조회할 때 넘기는
# `day` 는 체결(fill) 당일이다(정산일이 아니다). record_fill 은 정산일을 `day + settlement_sessions(day)` 로
# 별도 계산한다(v3_execution.py:375). 따라서 이 표의 effective_from/to 경계는 체결일 기준이다.
EFFECTIVE_BASIS = "TRADE_DATE"

# 법령 원문 세율(팀장 확인, 2026-09-24). 농어촌특별세율은 기존 표 값 유지(2차 확인, 원문 표 텍스트 미추출).
LAW_PERIODS = [
    {
        "law_reference": "대통령령 제24697호(2013-08-29 시행)",
        "source_url": "https://www.law.go.kr/법령/증권거래세법시행령/(24697,20130827)",
        "settlement_effective_from": "2013-08-29",
        "rates": {
            "KOSPI": {"securities_transaction_rate": Decimal("0.0015"), "rural_special_tax_rate": Decimal("0.0015")},
            "KOSDAQ": {"securities_transaction_rate": Decimal("0.003"), "rural_special_tax_rate": Decimal("0")},
        },
    },
    {
        "law_reference": "대통령령 제29788호(2019-06-03 시행)",
        "source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=208731",
        "settlement_effective_from": "2019-06-03",
        "rates": {
            "KOSPI": {"securities_transaction_rate": Decimal("0.001"), "rural_special_tax_rate": Decimal("0.0015")},
            "KOSDAQ": {"securities_transaction_rate": Decimal("0.0025"), "rural_special_tax_rate": Decimal("0")},
        },
    },
    {
        "law_reference": "대통령령 제31290호(2021-01-01 시행)",
        "source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=225167",
        "settlement_effective_from": "2021-01-01",
        "rates": {
            "KOSPI": {"securities_transaction_rate": Decimal("0.0008"), "rural_special_tax_rate": Decimal("0.0015")},
            "KOSDAQ": {"securities_transaction_rate": Decimal("0.0023"), "rural_special_tax_rate": Decimal("0")},
        },
    },
    {
        "law_reference": "대통령령 제33209호(2023-01-01 시행)",
        "source_url": "https://www.law.go.kr/LSW/lsInfoP.do?lsiSeq=269487",
        "settlement_effective_from": "2023-01-01",
        "rates": {
            "KOSPI": {"securities_transaction_rate": Decimal("0.0005"), "rural_special_tax_rate": Decimal("0.0015")},
            "KOSDAQ": {"securities_transaction_rate": Decimal("0.002"), "rural_special_tax_rate": Decimal("0")},
        },
    },
]

RULE_COLUMNS = ["effective_from", "effective_to", "evidence_status", "market", "rule_kind", "rule_value", "source_url"]


# ---------------------------------------------------------------------------
# 입력 로딩
# ---------------------------------------------------------------------------


def load_rules(prepared_dir: Path) -> tuple[pd.DataFrame, dict]:
    fp = prepared_dir / "rules.parquet"
    return pd.read_parquet(fp), {fp.name: sha256_file(fp)}


def load_calendar(prepared_dir: Path) -> tuple[pd.DatetimeIndex, dict]:
    fp = prepared_dir / "calendar.parquet"
    df = pd.read_parquet(fp)
    dates = pd.DatetimeIndex(sorted(pd.to_datetime(df["date"])))
    return dates, {fp.name: sha256_file(fp)}


# ---------------------------------------------------------------------------
# 체결일 경계 계산 (T+2 결제일이 시행일 이상이 되는 첫 개장일)
# ---------------------------------------------------------------------------


def first_trade_date_for_settlement(dates: pd.DatetimeIndex, law_effective: pd.Timestamp) -> pd.Timestamp:
    """정산(T+2 개장일)이 `law_effective` 이상이 되는 첫 체결(개장)일을 반환한다."""
    n = len(dates)
    for i in range(n - 2):
        if dates[i + 2] >= law_effective:
            return dates[i]
    raise ValueError("Calendar too short to resolve T+2 settlement boundary")


# ---------------------------------------------------------------------------
# SELL_TAX rule_value 직렬화 (기존 표와 같은 8자리 소수·무공백·알파벳순 키 형식 유지)
# ---------------------------------------------------------------------------


def _fmt_rate(value: Decimal) -> str:
    if value == 0:
        return "0E-8"
    return format(value, ".8f")


def build_sell_tax_value(rates: dict, settlement_effective_from: str, law_reference: str) -> str:
    total = rates["securities_transaction_rate"] + rates["rural_special_tax_rate"]
    fields = {
        "effective_basis": json.dumps(EFFECTIVE_BASIS, ensure_ascii=False),
        "law_reference": json.dumps(law_reference, ensure_ascii=False),
        "rural_special_tax_rate": _fmt_rate(rates["rural_special_tax_rate"]),
        "securities_transaction_rate": _fmt_rate(rates["securities_transaction_rate"]),
        "settlement_effective_from": json.dumps(settlement_effective_from, ensure_ascii=False),
        "total_sell_tax_rate": _fmt_rate(total),
    }
    return "{" + ",".join(f'"{k}":{fields[k]}' for k in sorted(fields)) + "}"


def build_new_sell_tax_rows(dates: pd.DatetimeIndex) -> tuple[list[dict], dict]:
    """네 법령 구간의 체결일 경계를 계산하고 시장별 SELL_TAX 행을 만든다."""
    boundaries = [WINDOW_START]
    boundary_notes = {}
    for period in LAW_PERIODS[1:]:
        law_effective = pd.Timestamp(period["settlement_effective_from"])
        trade_boundary = first_trade_date_for_settlement(dates, law_effective)
        boundaries.append(trade_boundary)
        boundary_notes[period["law_reference"]] = {
            "settlement_effective_from": period["settlement_effective_from"],
            "trade_date_boundary": trade_boundary.date().isoformat(),
        }
    boundaries.append(WINDOW_END + pd.Timedelta(days=1))  # sentinel for end-of-window arithmetic

    rows = []
    for idx, period in enumerate(LAW_PERIODS):
        effective_from = boundaries[idx]
        effective_to = boundaries[idx + 1] - pd.Timedelta(days=1)
        if effective_to > WINDOW_END:
            effective_to = WINDOW_END
        for market in MARKETS:
            rows.append(
                {
                    "effective_from": effective_from.date().isoformat(),
                    "effective_to": effective_to.date().isoformat(),
                    "evidence_status": "OFFICIAL",
                    "market": market,
                    "rule_kind": "SELL_TAX",
                    "rule_value": build_sell_tax_value(
                        period["rates"][market], period["settlement_effective_from"], period["law_reference"]
                    ),
                    "source_url": period["source_url"],
                }
            )
    return rows, boundary_notes


# ---------------------------------------------------------------------------
# 검증
# ---------------------------------------------------------------------------


def probe_all(rules: V3MarketRules, dates: pd.DatetimeIndex) -> dict:
    """2014-01-01~2023-12-31 개장일 x 시장 x rule_kind 전수 조회. 실패 건을 모두 기록한다."""
    window = dates[(dates >= WINDOW_START) & (dates <= WINDOW_END)]
    failures = []
    checked = 0
    for day in window:
        for market in MARKETS:
            for kind, fn in (
                ("COMMISSION", lambda d, m: rules._rule("COMMISSION", d, m)),
                ("SELL_TAX", lambda d, m: rules._rule("SELL_TAX", d, m)),
                ("SETTLEMENT", lambda d, m: rules._rule("SETTLEMENT", d, m)),
                ("TICK_SIZE", lambda d, m: rules._rule("TICK_SIZE", d, m)),
            ):
                checked += 1
                try:
                    fn(day, market)
                except Exception as exc:
                    failures.append(
                        {"date": day.date().isoformat(), "market": market, "rule_kind": kind, "error": str(exc)}
                    )
    return {"checked": checked, "failure_count": len(failures), "failures": failures}


def diff_sell_tax(old_rules: V3MarketRules, new_rules: V3MarketRules, dates: pd.DatetimeIndex) -> list[dict]:
    """구·신 표의 SELL_TAX total_sell_tax_rate 가 달라지는 개장일을 시장별로 나열한다."""
    window = dates[(dates >= WINDOW_START) & (dates <= WINDOW_END)]
    diffs = []
    for day in window:
        for market in MARKETS:
            old_rate = None
            new_rate = None
            try:
                old_rate = str(old_rules._rule("SELL_TAX", day, market)["total_sell_tax_rate"])
            except Exception as exc:
                old_rate = f"ERROR:{exc}"
            try:
                new_rate = str(new_rules._rule("SELL_TAX", day, market)["total_sell_tax_rate"])
            except Exception as exc:
                new_rate = f"ERROR:{exc}"
            if old_rate != new_rate:
                diffs.append(
                    {"date": day.date().isoformat(), "market": market, "old_rate": old_rate, "new_rate": new_rate}
                )
    return diffs


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prepared-dir", type=Path, default=DEFAULT_PREPARED_DIR)
    parser.add_argument("--out-data-dir", type=Path, default=DEFAULT_OUT_DATA_DIR)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    out_path = args.out or (Path(__file__).resolve().parent / "rules-effective-date-table.json")

    started = time.time()

    old_df, rules_hash = load_rules(args.prepared_dir)
    dates, calendar_hash = load_calendar(args.prepared_dir)

    new_sell_tax_rows, boundary_notes = build_new_sell_tax_rows(dates)
    kept_rows = old_df.loc[old_df["rule_kind"] != "SELL_TAX", RULE_COLUMNS].to_dict("records")
    all_rows = kept_rows + new_sell_tax_rows

    new_df = pd.DataFrame(all_rows, columns=RULE_COLUMNS).sort_values(
        ["rule_kind", "market", "effective_from"]
    ).reset_index(drop=True)
    for col in RULE_COLUMNS:
        new_df[col] = new_df[col].astype("string")

    max_effective_to = max(new_df["effective_to"])
    effective_to_ok = bool(max_effective_to <= "2023-12-31")

    args.out_data_dir.mkdir(parents=True, exist_ok=False)
    out_parquet = args.out_data_dir / "rules.parquet"
    new_df.to_parquet(out_parquet, index=False)
    new_sha256 = sha256_file(out_parquet)
    manifest = {
        "schema_version": "krx-prd-v1-b2b-sell-tax-v1",
        "source_prepared_manifest_hash": sha256_file(args.prepared_dir / "manifest.json"),
        "generated_at": pd.Timestamp.now().isoformat(),
        "files": {"rules.parquet": {"rows": int(len(new_df)), "sha256": new_sha256}},
    }
    (args.out_data_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    old_rules = V3MarketRules(old_df)
    new_rules = V3MarketRules(new_df)

    old_probe = probe_all(old_rules, dates)
    new_probe = probe_all(new_rules, dates)
    sell_tax_diffs = diff_sell_tax(old_rules, new_rules, dates)

    result = {
        "admission_status": "READ_ONLY_DIAGNOSTIC_NOT_ADMITTED",
        "note": "새 rules.parquet 후보를 만들고 기존 소비자(V3MarketRules)로 전수 조회 검증한 결과다. "
        "PRD 승인·admission 판단은 이 스크립트의 몫이 아니다.",
        "generated_at": pd.Timestamp.now().isoformat(),
        "runtime_seconds": None,
        "step1_effective_basis": {
            "conclusion": EFFECTIVE_BASIS,
            "evidence": [
                "research/krx_lab/v3_execution.py:369 costs(day,...) -> rules.fees(day,...)",
                "research/krx_lab/v3_execution.py:375 정산일은 day + settlement_sessions(day) 로 별도 계산",
                "research/krx_lab/v3_market.py:102 fees() 가 SELL_TAX 를 인자로 받은 day(체결일)로 조회",
            ],
        },
        "law_periods": [
            {
                "law_reference": p["law_reference"],
                "source_url": p["source_url"],
                "settlement_effective_from": p["settlement_effective_from"],
                "rates": {m: {k: str(v) for k, v in r.items()} for m, r in p["rates"].items()},
            }
            for p in LAW_PERIODS
        ],
        "trade_date_boundaries": boundary_notes,
        "new_sell_tax_rows": new_sell_tax_rows,
        "input_sha256": {**rules_hash, **calendar_hash},
        "output": {
            "data_dir": str(args.out_data_dir),
            "rules_parquet_sha256": new_sha256,
            "rows": int(len(new_df)),
        },
        "validation": {
            "effective_to_within_window": {"max_effective_to": max_effective_to, "ok": effective_to_ok},
            "old_table_probe": {"checked": old_probe["checked"], "failure_count": old_probe["failure_count"],
                                 "failures_sample": old_probe["failures"][:20]},
            "new_table_probe": {"checked": new_probe["checked"], "failure_count": new_probe["failure_count"],
                                 "failures_sample": new_probe["failures"][:20]},
            "sell_tax_rate_diffs": {"count": len(sell_tax_diffs), "rows": sell_tax_diffs},
        },
    }
    result["runtime_seconds"] = round(time.time() - started, 1)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} in {result['runtime_seconds']}s")
    print(f"wrote {out_parquet} sha256={new_sha256}")


if __name__ == "__main__":
    main()
