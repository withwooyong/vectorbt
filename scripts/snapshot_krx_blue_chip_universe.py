"""Snapshot the current KRX Korea Value-up constituent universe.

This script uses KRX's own index and listed-company pages.  It deliberately
labels the result as an official quality proxy rather than the output of the
repository's proposed fundamental and governance score.
"""

from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT / "docs/strategy-research/backtest-lab/assets"
INDEX_BASE = "https://index.krx.co.kr"
GLOBAL_BASE = "https://global.krx.co.kr"
USER_AGENT = "Mozilla/5.0 (compatible; vectorbt KRX research snapshot)"


def _number(value: str) -> int:
    return int((value or "0").replace(",", ""))


def _post_krx(session: requests.Session, base: str, page: str, bld: str, otp_name: str, payload: dict) -> dict:
    headers = {"User-Agent": USER_AGENT, "Referer": page, "X-Requested-With": "XMLHttpRequest"}
    response = session.get(page, headers=headers, timeout=30)
    response.raise_for_status()
    otp = session.get(
        f"{base}/contents/COM/GenerateOTP.jspx",
        params={"name": otp_name, "bld": bld},
        headers=headers,
        timeout=30,
    )
    otp.raise_for_status()
    response = session.post(
        f"{base}/contents/{'IDX' if base == INDEX_BASE else 'GLB'}/99/"
        f"{'IDX' if base == INDEX_BASE else 'GLB'}99000001.jspx",
        data={**payload, "code": otp.text},
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    return json.loads(response.content.decode("utf-8"))


def fetch_listed_companies(market_code: str) -> list[dict]:
    page = f"{GLOBAL_BASE}/contents/GLB/03/0308/0308010000/GLB0308010000.jsp"
    payload = {
        "market_gubun": market_code,
        "isu_cdnm": "",
        "isu_cd": "",
        "isu_nm": "",
        "isu_srt_cd": "",
        "sort": "A",
        "pagePath": "/contents/GLB/03/0308/0308010000/GLB0308010000.jsp",
    }
    data = _post_krx(
        requests.Session(),
        GLOBAL_BASE,
        page,
        "GLB/03/0308/0308010000/glb0308010000",
        "form",
        payload,
    )
    return next(iter(data.values()))


def fetch_value_up_constituents(trade_date: str) -> list[dict]:
    page = (
        f"{INDEX_BASE}/contents/MKD/03/0304/03040101/MKD03040101T3.jsp"
        "?idxCd=5302&idxId=XGG05P&upmidCd=0101"
    )
    payload = {
        "ind_tp_cd": "5",
        "idx_ind_cd": "302",
        "idx_id": "XGG05P",
        "lang": "ko",
        "compst_isu_tp": "1",
        "schdate": trade_date,
        "fromdate": trade_date,
        "todate": trade_date,
        "pagePath": "/contents/MKD/03/0304/03040101/MKD03040101T3.jsp",
    }
    data = _post_krx(
        requests.Session(),
        INDEX_BASE,
        page,
        "/IDX/03/0304/03040101/mkd03040101T3_02",
        "form",
        payload,
    )
    return next(iter(data.values()))


def build_snapshot(trade_date: str) -> dict:
    companies_by_market = {
        "KOSPI": fetch_listed_companies("1"),
        "KOSDAQ": fetch_listed_companies("2"),
    }
    company_lookup = {
        row["isu_cd"]: (market, row)
        for market, rows in companies_by_market.items()
        for row in rows
    }
    selected = []
    for row in fetch_value_up_constituents(trade_date):
        code = row["isu_cd"]
        if code not in company_lookup:
            raise RuntimeError(f"Value-up constituent is absent from the listed-company snapshot: {code}")
        market, company = company_lookup[code]
        close = _number(row["tdd_clsprc"])
        listed_shares = _number(company["lst_stk_vl"])
        selected.append(
            {
                "market": market,
                "code": code,
                "name": row["isu_nm"],
                "english_company_name": html.unescape(company["eng_cor_nm"]),
                "close_krw": close,
                "listed_shares": listed_shares,
                "market_cap_krw": close * listed_shares,
                "trading_value_krw": _number(row["acc_trdval"]),
                "official_proxy": "Korea Value-up index constituent",
            }
        )
    selected.sort(key=lambda item: (item["market"], -item["market_cap_krw"], item["code"]))
    counts = {market: len(rows) for market, rows in companies_by_market.items()}
    selected_counts = {market: sum(item["market"] == market for item in selected) for market in counts}
    return {
        "schema_version": 1,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "trade_date": f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}",
        "definition": (
            "Current members of the KRX Korea Value-up Index; an official quality proxy, "
            "not the result of the proposed repository-specific financial/governance score"
        ),
        "listed_company_counts": counts,
        "selected_counts": selected_counts,
        "sources": {
            "listed_companies": (
                f"{GLOBAL_BASE}/contents/GLB/03/0308/0308010000/GLB0308010000.jsp"
            ),
            "index_constituents": (
                f"{INDEX_BASE}/contents/MKD/03/0304/03040101/"
                "MKD03040101T3.jsp?idxCd=5302&idxId=XGG05P&upmidCd=0101"
            ),
            "index_factsheet": (
                "https://pdf.krx.co.kr/contents/comm/file/factsheet.jspx?"
                "ind_tp_cd=5&idx_ind_cd=302&yyyymm=202608&lang=ko&idx_id=XGG05P"
            ),
        },
        "calculation_notes": {
            "market_cap_krw": "trade-date close multiplied by current listed shares",
            "trading_value_krw": "single-day accumulated trading value on the trade date",
            "governance_score": "not calculated; KRX/KIND report normalization is not present in this repository",
        },
        "constituents": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trade-date", default="20260918", help="Last completed KRX trading day, YYYYMMDD")
    parser.add_argument("--output", type=Path, help="Output JSON path; defaults to a trade-date-specific filename")
    args = parser.parse_args()
    snapshot = build_snapshot(args.trade_date)
    output = args.output or DEFAULT_OUTPUT_DIR / (
        f"krx-blue-chip-universe-{args.trade_date[:4]}-{args.trade_date[4:6]}-{args.trade_date[6:]}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(output),
                "listed_company_counts": snapshot["listed_company_counts"],
                "selected_counts": snapshot["selected_counts"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
