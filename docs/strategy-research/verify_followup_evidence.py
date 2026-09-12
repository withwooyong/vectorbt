"""Independently recalculate the saved September 12 follow-up; no DB access."""

import json
from decimal import Decimal
from pathlib import Path

from verify_evidence import table

ROOT = Path(__file__).resolve().parent
BASE = "20260912-222200/"


def main():
    evidence = ROOT / "evidence" / BASE
    for name in ("06-price-provenance.txt", "07-hts-comparison-inputs.txt"):
        text = (evidence / name).read_text(encoding="utf-8-sig")
        assert text.rstrip().endswith("COMMIT") and "ERROR:" not in text
    annual = table(BASE + "06-price-provenance.txt", "year")
    assert sum(int(r["rows"]) for r in annual) == 2870
    assert sum(int(r["zero_close"]) for r in annual) == 1201
    assert sum(int(r["zero_close_positive_volume"]) for r in annual) == 695
    snapshot = json.loads((evidence / "hts-sample-bars.json").read_text(encoding="utf-8"))
    assert snapshot["read_only"] == "on" and len(snapshot["rows"]) == 180
    computed = table(BASE + "07-hts-comparison-inputs.txt", "stock_code")
    assert {r["stock_code"] for r in computed} == {"000660", "005930", "069500"}
    for result in computed:
        bars = sorted(
            [r for r in snapshot["rows"] if r["stock_code"] == result["stock_code"]],
            key=lambda r: r["trading_date"],
        )
        assert len(bars) == len({r["trading_date"] for r in bars}) == 60
        assert bars[-1]["trading_date"] == result["trading_date"] == "2026-09-10"
        assert bars[-2]["trading_date"] == result["previous_date"] == "2026-09-09"
        closes = [r["close_price"] for r in bars]
        assert all(c > 0 for c in closes)
        assert int(result["close_price"]) == closes[-1]
        assert int(result["previous_volume"]) == bars[-2]["trade_volume"]
        assert int(result["count60"]) == 60 and int(result["count20"]) == 20
        assert abs(Decimal(result["sma60"]) - Decimal(sum(closes)) / 60) <= Decimal("0.0000005")
        prior_max = max(closes[-21:-1])
        assert prior_max == int(result["prior20_max"])
        values = (bars[-2]["trade_volume"] >= 100000, closes[-1] * 60 > sum(closes), closes[-1] > prior_max)
        for field, value in zip(("volume_condition", "sma_condition", "high_condition"), values):
            assert result[field] == ("t" if value else "f")
    print("PASS: 1,201 zero closes / 695 positive-volume rows; 180 bars; 3 SQL/Python condition comparisons")


if __name__ == "__main__":
    main()
