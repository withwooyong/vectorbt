"""Recalculate saved read-only audit evidence; no network or DB access."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"


def read(name):
    raw = (EVIDENCE / name).read_bytes()
    return raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")


def table(name, first_column):
    lines = read(name).splitlines()
    for i, line in enumerate(lines):
        headers = [v.strip() for v in line.split("|")]
        if headers[0] != first_column:
            continue
        result = []
        for line in lines[i + 2 :]:
            if not line.strip() or line.lstrip().startswith("("):
                break
            values = [v.strip() for v in line.split("|")]
            if len(values) != len(headers):
                raise ValueError(f"Invalid table row: {name}")
            result.append(dict(zip(headers, values)))
        return result
    raise ValueError(f"Missing table: {name}: {first_column}")


def main():
    for name in ("01-schema.txt", "02-data-audit.txt", "04-coverage.txt", "05-backfill-check.txt"):
        content = read(name)
        assert "COMMIT" in content and "ERROR:" not in content, name
    quality = table("02-data-audit.txt", "adjusted")[0]
    annual = table("02-data-audit.txt", "year")
    detail = table("04-coverage.txt", "year")
    total = int(quality["rows"])
    assert sum(int(row["rows"]) for row in annual) == total
    for year in sorted({row["year"] for row in detail}):
        expected = sum(int(r["rows"]) for r in annual if r["year"] == year and r["market_code"] == "0")
        assert sum(int(r["rows"]) for r in detail if r["year"] == year) == expected
    sources = [json.loads(line) for line in read("03-api.jsonl").splitlines()]
    checks = {r["check"]: r for r in sources if "check" in r}
    assert checks["sample"]["status"] == 200
    assert checks["over_400_days"]["status"] == 400
    assert checks["unsupported_exchange"]["status"] in (400, 422)
    db_rows = table("05-backfill-check.txt", "stock_code")
    api_rows = checks["sample"]["data"]
    assert len(db_rows) == len(api_rows) == 7
    for db, api in zip(db_rows, api_rows):
        assert db["trading_date"] == api["trading_date"]
        for key in ("open_price", "high_price", "low_price", "close_price", "trade_volume", "trade_amount"):
            assert int(db[key]) == api[key], (db["trading_date"], key)
    summary = {
        "observed_date_kst": "2026-09-10",
        "annual_row_sum_verified": total,
        "market_zero_breakdown_verified": True,
        "api_db_matching_days": len(db_rows),
        "api_checks": {k: v["status"] for k, v in checks.items()},
        "quality": quality,
        "current_exchange_label_annual": [r for r in detail if r["market_name"] == "거래소"],
        "limitations": ["Current market labels are not historical membership", "Proxy calendar cannot detect dates missing for all stocks"],
    }
    (EVIDENCE / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: annual rows={total:,}; market breakdown; API/DB={len(db_rows)} days; API boundaries")


if __name__ == "__main__":
    main()
