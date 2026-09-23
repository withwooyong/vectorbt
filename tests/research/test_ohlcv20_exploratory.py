"""Exploratory OHLCV20 path: explicit flag, marked output, voided event trades."""

from decimal import Decimal
from types import SimpleNamespace

import pandas as pd
import pytest

from research.krx_lab import ohlcv20_exploratory as module
from research.krx_lab.ohlcv20_policy import Experiment
from research.krx_lab.ohlcv20_real_execution import (
    EXPLORATORY_SOURCE_KIND,
    run_ohlcv20_portfolio,
)
from research.krx_lab.ohlcv20_rights import RightsLedger


DAYS = list(pd.bdate_range("2020-03-02", periods=8))
CODES = [f"C{i:02d}" for i in range(20)]
PRICE = 10_000


def raw_bar(day, code, *, price=PRICE, tradable=True, mark_valid=True):
    halted = not mark_valid
    return dict(
        date=day,
        code=code,
        market="KOSPI",
        open=0 if halted else price,
        high=0 if halted else price,
        low=0 if halted else price,
        close=price,
        volume=1_000_000 if tradable else 0,
        can_buy=tradable,
        can_sell=tradable,
        order_eligible=tradable,
        mark_valid=mark_valid,
    )


def signal(day, code, turnover):
    return dict(
        signal_date=day,
        code=code,
        turnover=turnover,
        mean_turnover20=10**12,
        limit_price=PRICE,
        eligible=True,
    )


def scenario():
    """20 codes fill every slot on DAYS[1]; five of them meet voiding events.

    C00 meets a rights event (a) on DAYS[3]; C01 a sealed non-execution bar,
    C03 an unconfirmed corporate action on a non-sellable bar and C04 an
    unverified no-trade bar on DAYS[4]; C02 has no bar on DAYS[5]. NEW is
    signalled on DAYS[3] and can only get the slot C00 released.
    """
    rows = []
    for day in DAYS:
        for code in CODES + ["NEW"]:
            if code == "C02" and day == DAYS[5]:
                continue
            if code == "C01" and day == DAYS[4]:
                rows.append(raw_bar(day, code, tradable=False, mark_valid=False))
            elif code in ("C03", "C04") and day == DAYS[4]:
                rows.append(raw_bar(day, code, tradable=False))
            elif code == "C00" and day == DAYS[2]:
                rows.append(raw_bar(day, code, price=11_000))
            else:
                rows.append(raw_bar(day, code))
    bars = pd.DataFrame(rows)
    signals = pd.DataFrame(
        [signal(DAYS[0], code, 10**9 - i) for i, code in enumerate(CODES)]
        + [signal(DAYS[3], "NEW", 10**9)]
    )
    rule = module.VoidRule(
        events={
            (DAYS[3], "C00"): (("a", "AUDIT_PAID_RIGHTS_FACTOR_ADMITTED"),),
            (DAYS[4], "C03"): (("c", "AUDIT_BONUS_ISSUE_FACTOR_UNADMITTED"),),
        },
        non_execution={(DAYS[4], "C01"): "ZERO_VOLUME_WITH_OFFICIAL_HALT_INTERVAL"},
    )
    engine_bars = module.execution_bars(bars, signals, DAYS, start=DAYS[1])
    return engine_bars, signals, rule


def run(source_kind, **kwargs):
    bars, signals, rule = scenario()
    params = dict(
        start=DAYS[1],
        end=DAYS[-1],
        stop_pct="0.10",
        target_pct="0.30",
        holding_months=1,
        costs=lambda *_: 0,
        levels=module.identity_level,
        rights_ledger=RightsLedger({}),
        source_kind=source_kind,
    )
    params.update(kwargs)
    if "exploratory_void" not in params and source_kind == EXPLORATORY_SOURCE_KIND:
        params["exploratory_void"] = rule
    return run_ohlcv20_portfolio(bars, signals, DAYS, **params)


# (i) The REAL gate is unchanged, with or without the exploratory rule.


def test_real_path_without_flag_stays_blocked():
    with pytest.raises(ValueError, match="REAL_EXECUTION_NOT_ADMITTED"):
        run("REAL")
    _, _, rule = scenario()
    with pytest.raises(ValueError, match="REAL_EXECUTION_NOT_ADMITTED"):
        run("REAL", exploratory_void=rule, admission={"real_execution_admitted": True})


def test_void_rule_requires_the_explicit_exploratory_source():
    _, _, rule = scenario()
    with pytest.raises(ValueError, match="EXPLORATORY_VOID_RULE_ONLY"):
        run("SYNTHETIC_FIXTURE", exploratory_void=rule)
    with pytest.raises(ValueError, match="EXPLORATORY_VOID_RULE_ONLY"):
        run(EXPLORATORY_SOURCE_KIND, exploratory_void=None)
    with pytest.raises(ValueError, match="EXPLORATORY_RUN_VOIDS_INSTEAD"):
        run(EXPLORATORY_SOURCE_KIND, event_schedule=[])


def test_exploratory_entry_points_refuse_without_flag(tmp_path, capsys):
    with pytest.raises(ValueError, match="EXPLORATORY_FLAG_REQUIRED"):
        module.run_exploratory(tmp_path, tmp_path / "out")
    with pytest.raises(SystemExit) as stopped:
        module.main(["--ted-root", str(tmp_path), "--output-dir", str(tmp_path / "out")])
    assert stopped.value.code == 2
    assert "EXPLORATORY_FLAG_REQUIRED" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_run_refuses_unexpected_preflight_blockers(tmp_path, monkeypatch):
    monkeypatch.setattr(
        module,
        "load_preflight_inputs",
        lambda root: SimpleNamespace(
            reasons=sorted(module.BYPASSED_REASON_CODES + ("SIGNAL_ADMISSION_NOT_GRANTED",))
        ),
    )
    with pytest.raises(ValueError, match="UNEXPECTED_PREFLIGHT_BLOCKERS"):
        module.run_exploratory(tmp_path, tmp_path / "out", exploratory=True)


# (iii) Trades that meet an event are voided at that session.


def test_event_trades_are_voided_and_slot_cash_restored():
    result = run(EXPLORATORY_SOURCE_KIND)
    assert result["status"] == "SUCCEEDED" and not result["issues"]
    assert result["performance_valid"] is False
    exclusions = result["exclusions"].set_index("code")
    assert exclusions["category"].to_dict() == {
        "C00": "a",
        "C01": "b",
        "C03": "c",
        "C04": "b",
        "C02": "b",
    }
    assert exclusions.loc["C00", "date"] == DAYS[3]
    assert exclusions.loc["C01", "detail"] == "NON_EXECUTION_ZERO_VOLUME_WITH_OFFICIAL_HALT_INTERVAL"
    assert exclusions.loc["C02", "detail"] == "HELD_BAR_MISSING"
    assert exclusions.loc["C04", "detail"] == "NO_TRADE_BAR_STATUS_UNVERIFIED"
    assert exclusions.loc["C03", "detail"] == "AUDIT_BONUS_ISSUE_FACTOR_UNADMITTED"
    assert exclusions.loc["C03", "all_reasons"] == (
        "c:AUDIT_BONUS_ISSUE_FACTOR_UNADMITTED|b:NO_TRADE_BAR_STATUS_UNVERIFIED"
    )
    assert (exclusions["restored_cash"] == Decimal(5_000_000)).all()
    fills = result["fills"]
    assert not fills["code"].isin(["C00", "C01", "C02", "C03", "C04"]).any()
    # The released slot (not an untouched one) takes NEW with the restored cash.
    new = fills.loc[fills["code"] == "NEW"].iloc[0]
    released = int(exclusions.loc["C00", "slot_id"])
    assert (new["date"], new["slot_id"], new["size"]) == (DAYS[4], released, 500)
    # C00 rose to 11,000 on DAYS[2]; the curve carries its slot at entry cash.
    equity = result["equity"].set_index("date")["equity"]
    assert (equity == Decimal(100_000_000)).all()
    positions = result["positions"]
    assert not positions["code"].isin(["C00", "C01", "C02", "C03", "C04"]).any()


def test_exclusion_counts_by_reason_in_configuration_row():
    bars, signals, rule = scenario()
    experiment = Experiment("T", Decimal("0.10"), Decimal("0.30"), 1)
    outcome = module.run_configuration(
        experiment,
        "0.001",
        bars=bars,
        signals=signals,
        calendar=DAYS,
        rights_ledger=RightsLedger({}),
        void_rule=rule,
        start=DAYS[1],
        end=DAYS[-1],
    )
    row = outcome["row"]
    assert row["status"] == "SUCCEEDED"
    assert row["excluded_trades"] == 5
    assert row["excluded_by_category"] == {"a": 1, "b": 3, "c": 1}
    assert row["excluded_by_detail"] == {
        "AUDIT_BONUS_ISSUE_FACTOR_UNADMITTED": 1,
        "AUDIT_PAID_RIGHTS_FACTOR_ADMITTED": 1,
        "HELD_BAR_MISSING": 1,
        "NON_EXECUTION_ZERO_VOLUME_WITH_OFFICIAL_HALT_INTERVAL": 1,
        "NO_TRADE_BAR_STATUS_UNVERIFIED": 1,
    }
    # 15 untouched entries plus NEW remain open: holding months have not elapsed.
    assert (row["entries"], row["completed_trades"], row["open_trades_at_end"]) == (16, 0, 16)


# (ii) Every result carries the non-admission marks.


def test_rows_and_report_carry_non_admission_marks():
    bars, signals, rule = scenario()
    rows = [
        module.run_configuration(
            Experiment("T", Decimal("0.10"), Decimal("0.30"), 1),
            friction,
            bars=bars,
            signals=signals,
            calendar=DAYS,
            rights_ledger=RightsLedger({}),
            void_rule=rule,
            start=DAYS[1],
            end=DAYS[-1],
        )["row"]
        for friction in module.FRICTIONS
    ]
    report = module.build_report(rows, provenance={})
    assert report["admission_status"] == "NOT_ADMITTED_EXPLORATORY"
    assert report["performance_valid"] is False
    assert report["bypassed_reason_codes"] == [
        "CORRECTED_INPUT_NOT_EXECUTION_ADMITTED",
        "REAL_EXECUTION_NOT_ADMITTED",
        "RIGHTS_CONTRACT_NOT_EXECUTION_ADMITTED",
    ]
    assert "실거래" in report["interpretation"] and "선정" in report["interpretation"]
    assert any("생존 편향" in item for item in report["limitations"])
    assert any("연속 실행" in item for item in report["limitations"])
    assert all(row["admission_status"] == "NOT_ADMITTED_EXPLORATORY" for row in report["configurations"])
    assert report["summary"]["admission_status"] == "NOT_ADMITTED_EXPLORATORY"
    assert report["summary"]["excluded_by_category"] == {"a": 2, "b": 6, "c": 2}
    with pytest.raises(ValueError, match="UNMARKED_EXPLORATORY_ROW"):
        module.build_report([dict(rows[0], admission_status=None)], provenance={})


# Event dating and metrics.


def test_void_events_dates_audit_settlement_and_provider_steps():
    calendar = pd.DatetimeIndex(DAYS)
    bars = pd.DataFrame(
        [
            dict(date=day, code="X", close=100.0, adjusted_close=50.0 if day < DAYS[3] else 100.0)
            for day in DAYS
        ]
        + [
            dict(date=day, code="Y", close=100.0, adjusted_close=80.0 if day < DAYS[2] else 100.0)
            for day in DAYS
        ]
    )
    audit = pd.DataFrame(
        [
            dict(
                stock_code="Y",
                effective_date=str(DAYS[2].date()),
                official_event_kind="PAID_RIGHTS",
                price_admitted=True,
                volume_admitted=False,
            ),
            dict(
                stock_code="Y",
                effective_date=str(DAYS[5].date()),
                official_event_kind="CASH_DIVIDEND",
                price_admitted=True,
                volume_admitted=True,
            ),
        ]
    )
    rights = {
        "Z": SimpleNamespace(event_type="SPIN_OFF", record_date=DAYS[6].date()),
        "W": SimpleNamespace(event_type="CAPITAL_REDUCTION", record_date=DAYS[6].date()),
    }
    events = module.void_events(bars, calendar, audit, rights)
    assert events == {
        (DAYS[2], "Y"): (("a", "AUDIT_PAID_RIGHTS_FACTOR_UNADMITTED"),),
        (DAYS[5], "Z"): (("a", "SETTLEMENT_SPIN_OFF"),),
        (DAYS[5], "W"): (("c", "SETTLEMENT_CAPITAL_REDUCTION"),),
        (DAYS[3], "X"): (("c", "PROVIDER_ADJUSTMENT_STEP_NOT_IN_AUDIT"),),
    }
    unknown = audit.assign(official_event_kind="NEW_KIND")
    with pytest.raises(ValueError, match="UNMAPPED_AUDIT_EVENT_KIND"):
        module.void_events(bars, calendar, unknown, {})


def test_performance_cuts_calendar_years_from_one_curve():
    equity = pd.DataFrame(
        dict(
            date=pd.to_datetime(
                [
                    "2019-12-30",
                    "2020-06-30",
                    "2020-12-30",
                    "2021-06-30",
                    "2021-12-30",
                    "2022-12-29",
                    "2023-12-28",
                ]
            ),
            equity=[100.0, 80.0, 120.0, 150.0, 90.0, 90.0, 99.0],
        )
    )
    result = module.performance(equity, start="2019-12-30", initial_cash=100)
    assert result["yearly_return"] == pytest.approx(
        {"2020": 0.2, "2021": -0.25, "2022": 0.0, "2023": 0.1}
    )
    assert result["mean_yearly_return_2020_2023"] == pytest.approx(0.0125)
    assert result["yearly_max_drawdown"] == pytest.approx(
        {"2020": -0.2, "2021": -0.4, "2022": 0.0, "2023": 0.0}
    )
    assert result["worst_yearly_max_drawdown_2020_2023"] == pytest.approx(-0.4)
    assert result["max_drawdown"] == pytest.approx(-0.4)
    assert result["total_return"] == pytest.approx(-0.01)
