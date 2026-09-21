import json
from pathlib import Path

from research.krx_lab.report import write_detail_report


FIXTURE = Path(__file__).parent / "fixtures" / "contracts_v1" / "expected-ledger.json"


def _result():
    return {"contract_ledger": json.loads(FIXTURE.read_text(encoding="utf-8"))}


def test_detail_report_is_self_contained_safe_and_traces_synthetic_ledger(tmp_path):
    result = _result()
    result["contract_ledger"]["fills"][0]["fill_id"] = "<long-id-" + "x" * 400 + ">"
    result["contract_ledger"]["cashflows"][0]["fill_id"] = result["contract_ledger"]["fills"][0]["fill_id"]
    rendered = write_detail_report(tmp_path, result, initial_cash=1000, manifest={"source": "synthetic <input>"})
    page = (tmp_path / "detail-report.html").read_text(encoding="utf-8")
    assert rendered["summary"]["source_kind"] == "SYNTHETIC"
    assert rendered["summary"]["total_fees"] == 1.0
    assert "합성 자료" in page
    assert "&lt;long-id-" in page
    assert "<long-id-" not in page
    assert "<svg" in page
    assert "cash-0" in page and "fill" in page and "event" in page
    assert "synthetic &lt;input&gt;" in page


def test_detail_report_handles_zero_trade_and_missing_optional_ledgers(tmp_path):
    result = {"contract_ledger": {"source_kind": "SYNTHETIC", "equity": [], "positions": [], "fills": [],
                                  "events": [], "cashflows": []}}
    output = write_detail_report(tmp_path, result, initial_cash=0, manifest=None)
    page = Path(output["paths"]["detail_report"]).read_text(encoding="utf-8")
    assert output["summary"]["open_positions"] == 0
    assert "NAV·낙폭 그래프를 만들지 않았습니다" in page
    assert "전달된 manifest 없음" in page
