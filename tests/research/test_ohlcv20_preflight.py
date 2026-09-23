"""A blocked real-data attempt must not emit returns or trade counts."""

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from research.krx_lab import ohlcv20_preflight as module


# v2 승인 표본: 후보 733건 중 가격 643건·거래량 539건 승인(부분 승인), signal 미승인.
_FACTOR_V2_BASE = dict(
    source_manifest_sha256="manifest",
    candidate_keys=733,
    price_factors_admitted=643,
    volume_factors_admitted=539,
    both_factors_admitted=539,
    signal_admitted=False,
    output_sha256="admitted-factor-sha",
)


def _write_evidence(tmp_path, factor_overrides=None):
    evidence = tmp_path / "docs/research/evidence/ohlcv-admission-2026-09-22"
    evidence.mkdir(parents=True)
    package = tmp_path / "data/sources/ohlcv-admission-20260922/corrected-input-v4"
    package.mkdir(parents=True)
    (package / "manifest.json").write_text(json.dumps(dict(base_snapshot="base")))
    (evidence / "ohlcv20-eligibility-v2.json").write_text(
        json.dumps(
            dict(
                corrected_manifest_sha256="manifest",
                metadata_sha256="a" * 64,
                evaluation_raw_bars=1,
                evaluation_signal_daily_cap_class_eligible=1,
                evaluation_order_prior_session_cap_class_eligible=1,
                evaluation_missing_daily_metadata=0,
            )
        )
    )
    factor = dict(_FACTOR_V2_BASE)
    factor.update(factor_overrides or {})
    (evidence / "factor-admission-v2.json").write_text(json.dumps(factor))
    (evidence / "settlement-compilation-v4.json").write_text(
        json.dumps(dict(output_sha256="rights-sha", execution_admitted=False))
    )
    return evidence


def _admission(evidence_sha="audit-sha", adjusted_valid_bars=1, provider_mismatch_bars=0):
    return SimpleNamespace(
        evidence_sha256=evidence_sha,
        adjusted_valid_bars=adjusted_valid_bars,
        provider_mismatch_bars=provider_mismatch_bars,
    )


def _single_row_bars():
    return pd.DataFrame(
        [
            dict(
                date=pd.Timestamp("2015-06-15"),
                code="000001",
                signal_eligible=True,
                order_eligible=True,
                listed_shares=1,
                adjusted_valid=True,
                volume_adjusted_valid=True,
            )
        ]
    )


def _patch_common(monkeypatch, *, admission, eligibility_bars, issues=("REAL_EXECUTION_NOT_ADMITTED",)):
    monkeypatch.setattr(
        module,
        "load_corrected_v4",
        lambda path, base_snapshot, admitted_factors, admitted_factors_sha256: SimpleNamespace(
            manifest_sha256="manifest",
            bars=pd.DataFrame(
                [
                    dict(
                        date=pd.Timestamp("2015-06-15"),
                        code="000001",
                        order_eligible=False,
                        adjusted_valid=False,
                    )
                ]
            ),
            selected_months=pd.DataFrame([dict(code="000001")]),
            calendar=[pd.Timestamp("2023-01-02")],
            issues=issues,
            real_execution_admitted=False,
            adjusted_admission=admission,
        ),
    )
    monkeypatch.setattr(
        module,
        "load_candidate_metadata",
        lambda path, codes: (pd.DataFrame(), "a" * 64),
    )
    monkeypatch.setattr(
        module,
        "attach_daily_eligibility",
        lambda *args, **kwargs: SimpleNamespace(bars=eligibility_bars, missing_daily_metadata=0),
    )
    monkeypatch.setattr(
        module,
        "load_v4_terms",
        lambda path, sha: {"000001": SimpleNamespace(legs=[object(), object()])},
    )


def test_all_requested_configurations_block_without_real_execution_admission(
    tmp_path, monkeypatch
):
    _write_evidence(tmp_path)
    _patch_common(monkeypatch, admission=_admission(), eligibility_bars=_single_row_bars())
    result = module.preflight(tmp_path)
    assert result["requested_configurations"] == 52
    assert result["executed_configurations"] == 0
    assert all(
        row["status"] == "BLOCKED"
        and row["total_return"] is None
        and row["equity_krw"] is None
        and row["completed_trades"] is None
        for row in result["configurations"]
    )
    # 체결 축 증거(rights·real_execution)가 여전히 미승인이므로 부분 계수 승인만으로는
    # 차단이 풀리지 않는다.
    assert "CORRECTED_INPUT_NOT_EXECUTION_ADMITTED" in result["reason_codes"]
    assert "RIGHTS_CONTRACT_NOT_EXECUTION_ADMITTED" in result["reason_codes"]


def test_partial_admission_does_not_block_on_price_or_volume_factors(tmp_path, monkeypatch):
    _write_evidence(tmp_path)  # 기본값: 가격 643건·거래량 539건(부분 승인)
    _patch_common(monkeypatch, admission=_admission(), eligibility_bars=_single_row_bars())
    result = module.preflight(tmp_path)
    assert "PRICE_FACTORS_NOT_ADMITTED" not in result["reason_codes"]
    assert "VOLUME_FACTORS_NOT_ADMITTED" not in result["reason_codes"]


def test_zero_admission_still_blocks_on_price_and_volume_factors(tmp_path, monkeypatch):
    _write_evidence(
        tmp_path,
        dict(price_factors_admitted=0, volume_factors_admitted=0, both_factors_admitted=0),
    )
    _patch_common(
        monkeypatch,
        admission=_admission(adjusted_valid_bars=0),
        eligibility_bars=_single_row_bars(),
    )
    result = module.preflight(tmp_path)
    assert "PRICE_FACTORS_NOT_ADMITTED" in result["reason_codes"]
    assert "VOLUME_FACTORS_NOT_ADMITTED" in result["reason_codes"]


@pytest.mark.parametrize("signal_admitted", [True, False])
def test_signal_admission_reason_follows_evidence(tmp_path, monkeypatch, signal_admitted):
    _write_evidence(tmp_path, dict(signal_admitted=signal_admitted))
    _patch_common(monkeypatch, admission=_admission(), eligibility_bars=_single_row_bars())
    result = module.preflight(tmp_path)
    assert ("SIGNAL_ADMISSION_NOT_GRANTED" in result["reason_codes"]) == (not signal_admitted)


def test_adjusted_input_not_wired_when_admission_missing(tmp_path, monkeypatch):
    _write_evidence(tmp_path)
    _patch_common(monkeypatch, admission=None, eligibility_bars=_single_row_bars())
    result = module.preflight(tmp_path)
    assert "ADJUSTED_INPUT_NOT_WIRED" in result["reason_codes"]


def test_coverage_reports_every_evaluation_year(tmp_path, monkeypatch):
    years = list(range(2015, 2024))
    rows = [
        dict(
            date=pd.Timestamp(f"{year}-06-15" if year == 2015 else f"{year}-01-05"),
            code="000001",
            signal_eligible=True,
            order_eligible=(year != 2016),
            listed_shares=1,
            adjusted_valid=(year >= 2018),
            volume_adjusted_valid=True,
        )
        for year in years
    ]
    bars = pd.DataFrame(rows)
    evidence = _write_evidence(tmp_path)
    (evidence / "ohlcv20-eligibility-v2.json").write_text(
        json.dumps(
            dict(
                corrected_manifest_sha256="manifest",
                metadata_sha256="a" * 64,
                evaluation_raw_bars=len(bars),
                evaluation_signal_daily_cap_class_eligible=int(bars.signal_eligible.sum()),
                evaluation_order_prior_session_cap_class_eligible=int(bars.order_eligible.sum()),
                evaluation_missing_daily_metadata=0,
            )
        )
    )
    _patch_common(monkeypatch, admission=_admission(), eligibility_bars=bars)
    result = module.preflight(tmp_path)
    assert set(result["coverage"]) == {str(year) for year in years}
    assert result["coverage"]["2016"]["order_eligible_bars"] == 0
    assert result["coverage"]["2018"]["adjusted_valid_ratio"] == "1.0000"
    assert result["coverage"]["2015"]["adjusted_valid_ratio"] == "0.0000"
    assert result["coverage"]["2023"]["codes"] == 1


def test_factor_manifest_mismatch_stops_before_reporting(tmp_path, monkeypatch):
    _write_evidence(tmp_path, dict(source_manifest_sha256="wrong"))
    monkeypatch.setattr(
        module,
        "load_corrected_v4",
        lambda path, base_snapshot, admitted_factors, admitted_factors_sha256: SimpleNamespace(
            manifest_sha256="correct",
        ),
    )
    monkeypatch.setattr(module, "load_v4_terms", lambda path, sha: {})
    with pytest.raises(ValueError, match="FACTOR_AND_INPUT_MANIFEST_MISMATCH"):
        module.preflight(tmp_path)
