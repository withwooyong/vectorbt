"""A blocked real-data attempt must not emit returns or trade counts."""

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from research.krx_lab import ohlcv20_preflight as module


def test_all_requested_configurations_block_without_admitted_inputs(
    tmp_path, monkeypatch
):
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
    (evidence / "factor-admission-v1.json").write_text(
        json.dumps(
            dict(
                source_manifest_sha256="manifest",
                candidate_keys=733,
                price_factors_admitted=0,
                volume_factors_admitted=0,
            )
        )
    )
    (evidence / "settlement-compilation-v4.json").write_text(
        json.dumps(
            dict(
                output_sha256="rights-sha",
                execution_admitted=False,
            )
        )
    )
    monkeypatch.setattr(
        module,
        "load_corrected_v4",
        lambda path, base_snapshot: SimpleNamespace(
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
            issues=("ADJUSTED_PRICE_DEFINITION_UNADMITTED",),
            real_execution_admitted=False,
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
        lambda *args, **kwargs: SimpleNamespace(
            bars=pd.DataFrame(
                [
                    dict(
                        date=pd.Timestamp("2015-06-15"),
                        signal_eligible=True,
                        order_eligible=True,
                        listed_shares=1,
                    )
                ]
            ),
            missing_daily_metadata=0,
        ),
    )
    monkeypatch.setattr(
        module,
        "load_v4_terms",
        lambda path, sha: {
            "000001": SimpleNamespace(legs=[object(), object()]),
        },
    )
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
    assert "PRICE_FACTORS_NOT_ADMITTED" in result["reason_codes"]


def test_factor_manifest_mismatch_stops_before_reporting(tmp_path, monkeypatch):
    evidence = tmp_path / "docs/research/evidence/ohlcv-admission-2026-09-22"
    evidence.mkdir(parents=True)
    package = tmp_path / "data/sources/ohlcv-admission-20260922/corrected-input-v4"
    package.mkdir(parents=True)
    (package / "manifest.json").write_text(json.dumps(dict(base_snapshot="base")))
    (evidence / "ohlcv20-eligibility-v2.json").write_text("{}")
    (evidence / "factor-admission-v1.json").write_text(
        json.dumps(
            dict(
                source_manifest_sha256="wrong",
                candidate_keys=1,
                price_factors_admitted=0,
                volume_factors_admitted=0,
            )
        )
    )
    (evidence / "settlement-compilation-v4.json").write_text(
        json.dumps(
            dict(
                output_sha256="rights",
                execution_admitted=False,
            )
        )
    )
    monkeypatch.setattr(
        module,
        "load_corrected_v4",
        lambda path, base_snapshot: SimpleNamespace(
            manifest_sha256="correct",
        ),
    )
    monkeypatch.setattr(module, "load_v4_terms", lambda path, sha: {})
    with pytest.raises(ValueError, match="FACTOR_AND_INPUT_MANIFEST_MISMATCH"):
        module.preflight(tmp_path)
