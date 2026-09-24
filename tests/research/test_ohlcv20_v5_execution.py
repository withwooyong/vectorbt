"""Settlement-v5 rights routing, coverage binding and pre-run separation."""

from dataclasses import replace
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.krx_lab.ohlcv20_market_rules import (
    MISSING_RULE,
    admission_failures,
    attach_market_rules,
    reachable_bars,
    separate_configurations,
)
from research.krx_lab import ohlcv20_real_execution as engine
from research.krx_lab.ohlcv20_real_execution import run_ohlcv20_portfolio
from research.krx_lab.ohlcv20_rights import (
    NEW_SHARE_OBLIGATION,
    RightsLedger,
    coverage_mismatches,
    event_coverage,
    load_v5_program,
)


DAYS = list(pd.bdate_range("2016-01-04", periods=30))
FLAGS = (
    "immutable_input_verified",
    "daily_universe_admitted",
    "adjusted_price_admitted",
    "volume_factors_admitted",
    "corporate_coverage_admitted",
    "rights_admitted",
    "market_rules_admitted",
    "real_execution_admitted",
)


def _iso(index):
    return DAYS[index].strftime("%Y-%m-%d")


def _ledger_rows():
    entitlement = dict(
        record_date=_iso(2),
        record_date_last_cum_rights_session_t_plus_2=_iso(2),
        ex_session=_iso(3),
        traded_sessions_from_ex_session_to_effective_date=0,
    )
    common = dict(
        row_kind="LEDGER_LEG",
        record_index=0,
        event_id="kind:listing:0:036710:1",
        treatment="RIGHTS_LEDGER",
        consumer_applies_this_row=True,
        record_stock_code="036710",
        effective_date=_iso(6),
        record_event_type="SPIN_OFF",
        execution_admitted=False,
        terms_json="null",
        record_json=json.dumps(dict(entitlement=entitlement)),
        event_stock_code="036710",
        event_type="SPIN_OFF",
        rights_record_date=_iso(2),
        official_event_payment_date=_iso(8),
        cash_rounding="UNSPECIFIED_PRESERVE_EXACT_RATIONAL",
    )
    return [
        dict(
            common,
            leg_index=0,
            stock_code="036710",
            ratio_numerator=2300699,
            ratio_denominator=5000000,
            fractional_cash_price=3900,
        ),
        dict(
            common,
            leg_index=1,
            stock_code="222800",
            ratio_numerator=2699301,
            ratio_denominator=5000000,
            fractional_cash_price=11350,
        ),
    ]


def _event(index, event_id, treatment, code, effective, terms=None, applies=True):
    return dict(
        row_kind="EVENT",
        record_index=index,
        leg_index=0,
        event_id=event_id,
        treatment=treatment,
        consumer_applies_this_row=applies,
        record_stock_code=code,
        effective_date=effective,
        record_event_type="RIGHTS_OFF",
        execution_admitted=False,
        terms_json=json.dumps(terms),
        record_json="{}",
        event_stock_code=code,
        event_type="RIGHTS_OFF",
        stock_code=code,
    )


def _rows():
    bonus = dict(
        fraction_rule="WHOLE_NEW_SHARES_ADDED_FRACTION_CASH_AT_EX_DATE_REFERENCE_PRICE",
        quantity_multiplier="201/200",
        stop_take_price_multiplier="200/201",
        fraction_cash_price="1000",
        consumer_obligation=NEW_SHARE_OBLIGATION,
    )
    split = dict(
        fraction_rule="INTEGER_RATIO_NO_FRACTION",
        quantity_multiplier="10",
        stop_take_price_multiplier="1/10",
    )
    paid = dict(
        quantity_multiplier="1",
        rights_value_per_share="30",
        stop_take_price_multiplier="969/999",
    )
    return _ledger_rows() + [
        _event(1, "e:qt:000100", "QUANTITY_TRANSFORM", "000100", _iso(3), bonus),
        _event(2, "e:split:000110", "QUANTITY_TRANSFORM", "000110", _iso(3), split),
        _event(3, "e:paid:000200", "PAID_RIGHTS_CASH", "000200", _iso(3), paid),
        _event(4, "e:boh:000300", "BLOCK_ON_HOLD", "000300", _iso(3)),
        _event(5, "e:nhe:000400", "NO_HOLDER_EFFECT", "000400", _iso(3)),
        _event(6, "e:cash:000100", "POLICY_EXCLUDED", "000100", _iso(3), applies=False),
    ]


def _write(tmp_path, rows, name="rights-terms.parquet"):
    frame = pd.DataFrame(rows)
    for column in ("ratio_numerator", "ratio_denominator", "fractional_cash_price"):
        frame[column] = frame.get(column, pd.Series(dtype="Int64")).astype("Int64")
    for column in ("rights_record_date", "official_event_payment_date", "cash_rounding"):
        frame[column] = frame.get(column, pd.Series(dtype=object)).astype("string")
    path = tmp_path / name
    frame.to_parquet(path, index=False)
    return path, sha256(path.read_bytes()).hexdigest(), frame


def _receipt_coverage(frame):
    """Independent restatement of the receipt's key and serialization rules."""
    first = frame.sort_values(["record_index", "leg_index"]).drop_duplicates("record_index")

    def digest(ids):
        payload = "\n".join(sorted(ids)).encode("utf-8")
        return {"count": len(ids), "sha256": sha256(payload).hexdigest()}

    def split(rows):
        return dict(
            applied=digest(list(rows.loc[rows.consumer_applies_this_row, "event_id"])),
            not_applied=digest(list(rows.loc[~rows.consumer_applies_this_row, "event_id"])),
        )

    return dict(
        all=digest(list(first.event_id)),
        **split(first),
        by_treatment={
            name: dict(digest(list(rows.event_id)), **split(rows))
            for name, rows in first.groupby("treatment")
        },
    )


@pytest.fixture
def program(tmp_path):
    path, digest, frame = _write(tmp_path, _rows())
    return load_v5_program(path, digest), frame


def bar(day, code, price=999, *, high=None, low=None, can_sell=True):
    return dict(
        date=day,
        code=code,
        market="KOSPI",
        open=price,
        high=high or price,
        low=low or price,
        close=price,
        volume=1_000_000 if can_sell else 0,
        can_buy=can_sell,
        can_sell=can_sell,
        sell_status="SELLABLE" if can_sell else "NO_TRADE",
        sell_status_verified=True,
        listing_status="LISTED",
        listing_status_verified=True,
        lower_limit_price=1,
        lower_limit_price_verified=True,
        order_eligible=can_sell,
        mark_valid=True,
    )


def _series(code, overrides=None):
    overrides = overrides or {}
    return [bar(day, code, **overrides.get(index, {})) for index, day in enumerate(DAYS)]


def _signal(code, index=0):
    return dict(
        signal_date=DAYS[index],
        code=code,
        turnover=1_000_000_000,
        mean_turnover20=1_000_000_000,
        limit_price=1001,
        eligible=True,
    )


def _run(bars, signals, program, **extra):
    kwargs = dict(
        start=DAYS[1],
        end=DAYS[-1],
        stop_pct="0.10",
        target_pct="0.30",
        holding_months=1,
        costs=lambda *_: 0,
        levels=lambda _side, _day, _market, price: price,
        rights_ledger=program.ledger(),
        event_schedule=program.event_schedule(),
        source_kind="SYNTHETIC_FIXTURE",
        rights_program=program,
    )
    kwargs.update(extra)
    return run_ohlcv20_portfolio(bars, signals, DAYS, **kwargs)


def test_v5_program_routes_every_event_and_matches_receipt_coverage(program):
    loaded, frame = program
    routed = loaded.assignment()
    assert {name: len(items) for name, items in routed.items()} == {
        "RIGHTS_LEDGER": 1,
        "QUANTITY_TRANSFORM": 2,
        "PAID_RIGHTS_CASH": 1,
        "NO_HOLDER_EFFECT": 1,
        "POLICY_EXCLUDED": 1,
        "BLOCK_ON_HOLD": 1,
    }
    assert event_coverage(loaded) == _receipt_coverage(frame)
    assert coverage_mismatches(loaded, _receipt_coverage(frame)) == []
    assert loaded.event_schedule() == [
        dict(event_code="036710", capture_on=DAYS[2].date(), available_on=DAYS[6].date())
    ]


def test_v5_program_rejects_unknown_treatment_and_self_admitted_rows(tmp_path):
    rows = _rows()
    rows[3]["treatment"] = "SILENTLY_IGNORED"
    path, digest, _ = _write(tmp_path, rows)
    with pytest.raises(ValueError, match="UNKNOWN_RIGHTS_TREATMENT"):
        load_v5_program(path, digest)
    rows = _rows()
    rows[2]["execution_admitted"] = True
    path, digest, _ = _write(tmp_path, rows, "admitted.parquet")
    with pytest.raises(ValueError, match="RIGHTS_TABLE_ADMISSION_FLAG_INVALID"):
        load_v5_program(path, digest)
    with pytest.raises(ValueError, match="RIGHTS_INPUT_HASH_MISMATCH"):
        load_v5_program(path, "0" * 64)


def test_ledger_legs_only_table_fails_coverage(tmp_path, program):
    _, frame = program
    path, digest, _ = _write(tmp_path, _ledger_rows(), "ledger-only.parquet")
    ledger_only = load_v5_program(path, digest)
    assert coverage_mismatches(ledger_only, _receipt_coverage(frame)) == [
        "all",
        "applied",
        "not_applied",
        "by_treatment",
    ]


CODES = ("000100", "000200", "000300", "000400", "000500")


def _real_package(
    tmp_path,
    monkeypatch=None,
    *,
    development_end="2023-12-31",
    unverified=(),
    ineligible=(),
):
    """Seal a v5-shaped package, a bound receipt and the engine admission."""
    folder = tmp_path / "corrected-input-v5"
    (folder / "prices").mkdir(parents=True)
    frames = {
        "prices/price-00000.parquet": pd.DataFrame(
            [
                dict(
                    stock_code=code,
                    trading_date=_iso(index),
                    adjusted=False,
                    market="KOSPI",
                    open_price=999,
                    high_price=999,
                    low_price=999,
                    close_price=999,
                    trade_volume=1_000_000,
                    trade_amount=1_000_000_000,
                )
                for code in CODES
                for index in range(len(DAYS))
            ]
        ),
        "selected-months.parquet": pd.DataFrame(
            [
                dict(stock_code=code, market="KOSPI", month=month)
                for code in CODES
                for month in ("2016-01", "2016-02")
            ]
        ),
        "non-execution.parquet": pd.DataFrame(
            columns=[
                "stock_code",
                "trading_date",
                "regular_session_execution_allowed",
                "valuation_or_entitlements_resolved",
            ]
        ),
        "market-rules.parquet": pd.DataFrame(
            [
                _rule(day, code, sell_status_verified=(day, code) not in unverified)
                for code in CODES
                for day in DAYS
            ]
        ),
    }
    for name, frame in frames.items():
        frame.to_parquet(folder / name, index=False)
    _, _, table = _write(folder, _rows())
    entries = []
    for name in [*frames, "rights-terms.parquet"]:
        data = (folder / name).read_bytes()
        rows = len(pd.read_parquet(folder / name))
        entries.append(dict(file=name, rows=rows, sha256=sha256(data).hexdigest()))
    manifest = folder / "manifest.json"
    manifest.write_text(
        json.dumps(
            dict(
                schema="ohlcv-corrected-candidate-input-v1",
                real_execution_admitted=True,
                admission_receipt_schema="ohlcv20-real-admission-v1",
                total_price_rows=len(frames["prices/price-00000.parquet"]),
                files=entries,
            )
        )
    )
    rights_sha = sha256((folder / "rights-terms.parquet").read_bytes()).hexdigest()
    receipt = tmp_path / "admission.json"
    receipt.write_text(
        json.dumps(
            dict(
                schema="ohlcv20-real-admission-v1",
                status="ADMITTED",
                blocked_reasons=[],
                **{name: True for name in FLAGS},
                source_manifest_sha256=sha256(manifest.read_bytes()).hexdigest(),
                rights_terms_sha256=rights_sha,
                rights_event_coverage=_receipt_coverage(table),
                admission_scope=dict(
                    development_period=dict(start="2015-06-15", end=development_end)
                ),
            )
        )
    )
    digest = sha256(receipt.read_bytes()).hexdigest()
    if monkeypatch is not None:
        monkeypatch.setattr(engine, "_ADMISSION_RECEIPT_SHA256", digest)
        # Stand-in for the sealed metadata chain, which a fixture cannot
        # carry; the real recomputation is exercised on the sealed data.
        eligibility = pd.DataFrame(
            [
                dict(date=day, code=code, order_eligible=(day, code) not in ineligible)
                for code in CODES
                for day in DAYS
            ]
        )
        monkeypatch.setattr(engine, "_bound_eligibility", lambda _admission: eligibility)
    admission = dict(
        {name: True for name in FLAGS},
        source_manifest_path=str(manifest),
        admission_evidence_path=str(receipt),
        admission_evidence_sha256=digest,
    )
    return admission, load_v5_program(folder / "rights-terms.parquet", rights_sha)


def _real(bars, signals, program, admission, **extra):
    extra.setdefault("out_of_set_events", {})
    return _run(bars, signals, program, source_kind="REAL", admission=admission, **extra)


def _forgeries(program):
    """The two reviewer probes (legs cut, ratios doubled) and a dropped table."""
    cut = {
        code: replace(event, legs=event.legs[:1])
        for code, event in program.ledger_events.items()
    }
    doubled = tuple(
        replace(event, quantity_multiplier=event.quantity_multiplier * 2)
        if event.quantity_multiplier
        else event
        for event in program.events
    )
    return [
        replace(program, ledger_events=cut),
        replace(program, events=doubled),
        replace(program, events=()),
    ]


def test_real_run_accepts_only_the_program_rebuilt_from_bound_bytes(tmp_path, monkeypatch):
    admission, program = _real_package(tmp_path, monkeypatch)
    result = _real(_series("000400"), [_signal("000400", 20)], program, admission)
    assert result["status"] == "SUCCEEDED"
    assert result["fills"].side.tolist() == ["BUY"]
    # Signal membership and limit prices are not bound to a generator yet.
    assert not result["performance_valid"]
    assert result["performance_withheld"] == ["SIGNALS_NOT_BOUND_TO_GENERATOR"]
    for forged in _forgeries(program)[:2]:
        # Event keys are untouched, so the coverage digest alone would pass.
        assert coverage_mismatches(forged, event_coverage(program)) == []
    for forged in _forgeries(program):
        with pytest.raises(ValueError, match="RIGHTS_PROGRAM_NOT_BOUND"):
            _real(
                [],
                [],
                forged,
                admission,
                rights_ledger=forged.ledger(),
                event_schedule=forged.event_schedule(),
            )
    # Reviewer reproduction: only the ledger legs, labelled with the table hash.
    labelled = RightsLedger(program.ledger_events, source_sha256=program.source_sha256)
    with pytest.raises(ValueError, match="RIGHTS_PROGRAM_NOT_BOUND"):
        _real([], [], program, admission, rights_ledger=labelled, rights_program=None)


def test_real_run_refuses_an_unpinned_receipt(tmp_path):
    admission, program = _real_package(tmp_path)
    with pytest.raises(ValueError, match="ADMISSION_RECEIPT_NOT_PINNED"):
        _real([], [], program, admission)


def _tampered_rights(folder):
    path = folder / "rights-terms.parquet"
    frame = pd.read_parquet(path)
    frame["terms_json"] = frame.terms_json.str.replace("201/200", "101/100", regex=False)
    frame.to_parquet(path, index=False)


@pytest.mark.parametrize(
    "case, error",
    [
        ("price", "BARS_NOT_FROM_BOUND_INPUT"),
        ("unknown_code", "BARS_NOT_FROM_BOUND_INPUT"),
        ("rule", "MARKET_RULES_NOT_FROM_BOUND_INPUT"),
        ("trigger", "UNBOUND_EXECUTION_FLAG:regular_session_trigger_valid"),
        ("calendar", "CALENDAR_NOT_FROM_BOUND_INPUT"),
        ("signal", "SIGNALS_NOT_FROM_BOUND_INPUT"),
        ("mean", "SIGNALS_NOT_FROM_BOUND_INPUT"),
        ("eligibility", "ELIGIBILITY_NOT_FROM_BOUND_INPUT"),
        ("rights_bytes", "RIGHTS_INPUT_HASH_MISMATCH"),
    ],
)
def test_real_run_refuses_frames_not_from_the_manifest(tmp_path, monkeypatch, case, error):
    admission, program = _real_package(
        tmp_path,
        monkeypatch,
        unverified={(DAYS[5], "000400")},
        ineligible={(DAYS[7], "000400")} if case == "eligibility" else (),
    )
    bars = [row for row in _series("000400") if row["date"] != DAYS[5]]
    signals, calendar = [_signal("000400", 20)], DAYS
    if case == "price":
        bars[3].update(open=1000, high=1000, low=1000, close=1000)
    elif case == "unknown_code":
        bars.append(bar(DAYS[5], "999999"))
    elif case == "rule":
        bars.append(bar(DAYS[5], "000400"))  # The file leaves this status unverified.
    elif case == "trigger":
        bars[3]["regular_session_trigger_valid"] = True
    elif case == "calendar":
        bars, signals, calendar = [], [], [day for day in DAYS if day != DAYS[5]]
    elif case == "signal":
        signals[0]["turnover"] = 2_000_000_000
    elif case == "mean":
        signals[0]["mean_turnover20"] = 2_000_000_000  # Loosens the buy limit.
    elif case == "eligibility":
        pass  # The bar is ineligible in the bound chain but passed as True.
    else:
        _tampered_rights(Path(admission["source_manifest_path"]).parent)
    with pytest.raises(ValueError, match=error):
        run_ohlcv20_portfolio(
            bars,
            signals,
            calendar,
            start=calendar[1],
            end=calendar[-1],
            stop_pct="0.10",
            target_pct="0.30",
            holding_months=1,
            costs=lambda *_: 0,
            levels=lambda _side, _day, _market, price: price,
            rights_ledger=program.ledger(),
            event_schedule=program.event_schedule(),
            source_kind="REAL",
            admission=admission,
            rights_program=program,
            out_of_set_events={},
        )


def test_real_gate_requires_touch_set_and_respects_validation_lock(tmp_path, monkeypatch):
    admission, program = _real_package(tmp_path / "open", monkeypatch)
    with pytest.raises(ValueError, match="OUT_OF_TOUCH_SET_EVENTS_REQUIRED"):
        _run([], [], program, source_kind="REAL", admission=admission)
    locked, program = _real_package(
        tmp_path / "locked", monkeypatch, development_end="2015-12-31"
    )
    with pytest.raises(ValueError, match="VALIDATION_PERIOD_LOCKED"):
        _real([], [], program, locked)


def test_bonus_shares_transform_quantity_prices_and_report_early_exit(program):
    loaded, _ = program
    bars = _series("000100", {3: dict(price=994), 5: dict(price=994, high=1300)})
    result = _run(bars, [_signal("000100")], loaded)
    assert result["status"] == "SUCCEEDED"
    event = result["corporate_events"].iloc[0]
    assert (event.old_shares, event.new_shares) == (4995, 5019)
    assert event.cash == Decimal(975)  # 0.975 fractional share at the reference price.
    sold = result["fills"].loc[result["fills"].side.eq("SELL")].iloc[0]
    assert sold.date == DAYS[5] and sold.reason == "target_intraday"
    assert sold.price < Decimal("1298.7")  # Target scaled by 200/201.
    exits = result["new_share_exits"]
    assert exits.event_id.tolist() == ["e:qt:000100"]
    summary = result["new_share_exit_summary"]
    assert summary["exits"] == 1 and summary["pnl"] == exits.pnl.iloc[0] > 0


def test_paid_rights_are_sold_with_selling_cost_and_levels_rescaled(program):
    loaded, _ = program
    bars = _series("000200", {3: dict(price=970), 4: dict(price=970, low=880)})
    result = _run(
        bars,
        [_signal("000200")],
        loaded,
        costs=lambda side, _day, _market, amount: amount * Decimal("0.001")
        if side == "SELL"
        else 0,
    )
    assert result["status"] == "SUCCEEDED"
    event = result["corporate_events"].iloc[0]
    assert event.cash == Decimal("149700.15")  # 4995 x 30 less 0.1% selling cost.
    # The unadjusted stop 899.1 would fire at 880; the rescaled 872.1 does not,
    # so the position leaves only at its expiry session.
    sold = result["fills"].loc[result["fills"].side.eq("SELL")]
    assert sold.date.tolist() == [DAYS[24]]
    assert result["new_share_exits"].empty


def test_block_on_hold_event_blocks_with_event_list_not_zero_return(program):
    loaded, _ = program
    result = _run(_series("000300"), [_signal("000300")], loaded)
    assert result["status"] == "BLOCKED" and not result["performance_valid"]
    assert result["issues"][0].startswith("BLOCK_ON_HOLD_EVENT:")
    assert result["blocked_events"].event_id.tolist() == ["e:boh:000300"]
    assert result["equity"].empty and result["new_share_exit_summary"] is None


def test_unapplied_and_no_effect_events_leave_position_unchanged(program):
    loaded, _ = program
    result = _run(_series("000400"), [_signal("000400")], loaded)
    assert result["status"] == "SUCCEEDED"
    assert result["corporate_events"].empty


@pytest.mark.parametrize("session, where", [(28, "BEYOND"), (25, "WITHIN")])
def test_out_of_touch_set_event_on_held_position_blocks(program, session, where):
    loaded, _ = program
    halted = {index: dict(can_sell=False) for index in range(20, 30)}
    result = _run(
        _series("000500", halted),
        [_signal("000500")],
        loaded,
        out_of_set_events={(DAYS[session], "000500"): ["kind:outside:1"]},
        margin_sessions=2,  # Expiry 2016-02-05 is session 24.
    )
    assert result["status"] == "BLOCKED"
    assert result["issues"] == [
        f"OUT_OF_TOUCH_SET_EVENT_{where}_MARGIN:{DAYS[session]}:000500:kind:outside:1"
    ]


def _rule(day, code, **changes):
    row = dict(
        stock_code=code,
        trading_date=day,
        listing_status="LISTED",
        listing_status_verified=True,
        sell_status="SELLABLE",
        sell_status_verified=True,
        lower_limit_price=1.0,
        lower_limit_price_verified=True,
    )
    row.update(changes)
    return row


def test_market_rules_refuse_missing_and_unverified_rows_like_the_engine():
    rule_columns = {
        "listing_status",
        "listing_status_verified",
        "sell_status",
        "sell_status_verified",
        "lower_limit_price",
        "lower_limit_price_verified",
    }
    bars = pd.DataFrame(
        [
            {k: v for k, v in bar(DAYS[i], "000600").items() if k not in rule_columns}
            for i in range(3)
        ]
    )
    rules = pd.DataFrame(
        [
            _rule(DAYS[0], "000600"),
            _rule(DAYS[1], "000600", sell_status_verified=False),
        ]
    )
    frame = attach_market_rules(bars, rules)
    assert frame.market_rule_present.tolist() == [True, True, False]
    assert admission_failures(frame).tolist() == [
        None,
        "VERIFIED_SELL_STATUS_REQUIRED",
        MISSING_RULE,
    ]


def test_reach_starts_after_signal_and_ends_margin_sessions_after_expiry():
    frame = pd.DataFrame(
        dict(
            date=DAYS,
            code="000700",
            signal_eligible=[index == 2 for index in range(30)],
        )
    )
    # Order on session 3 (2016-01-07); expiry 2016-02-08 is session 25.
    reach = reachable_bars(frame, DAYS, 1, margin=2)
    assert np.flatnonzero(reach).tolist() == list(range(3, 28))
    failures = pd.Series([None] * 30, dtype=object)
    failures[27], failures[29] = "VERIFIED_LISTING_STATUS_REQUIRED", MISSING_RULE
    horizons = separate_configurations(
        frame, failures, DAYS, holding_months_values=(1,), margin=2
    )
    assert horizons[1]["reason_codes"] == ["UNVERIFIED_MARKET_RULE_ROW_IN_REACH"]
    assert horizons[1]["refused_by_reason"] == {"VERIFIED_LISTING_STATUS_REQUIRED": 1}


def test_entry_feasible_reach_consults_only_the_order_bar_without_entry():
    frame = pd.DataFrame(
        dict(
            date=DAYS,
            code="000700",
            signal_eligible=[index == 2 for index in range(30)],
            order_eligible=[index != 3 for index in range(30)],
            can_buy=True,
        )
    )
    failures = pd.Series([None] * 30, dtype=object)
    failures[3], failures[10] = MISSING_RULE, "VERIFIED_SELL_STATUS_REQUIRED"
    reach = reachable_bars(frame, DAYS, 1, margin=2, entry_feasible_only=True)
    assert np.flatnonzero(reach).tolist() == [3]
    horizons = separate_configurations(
        frame, failures, DAYS, holding_months_values=(1,), margin=2, entry_feasible_only=True
    )
    assert horizons[1]["missing_rule_bars"] == 1 and horizons[1]["refused_rule_bars"] == 0
    assert horizons[1]["reason_codes"] == ["MARKET_RULE_ROW_MISSING_IN_REACH"]


TED_ROOT = os.environ.get("OHLCV20_TED_ROOT")
V5 = "data/sources/ohlcv-admission-20260922/corrected-input-v5/rights-terms.parquet"
RECEIPT = "docs/research/evidence/ohlcv-admission-2026-09-22/ohlcv20-real-admission-v1.json"


@pytest.mark.skipif(not TED_ROOT, reason="OHLCV20_TED_ROOT points at the sealed data")
def test_real_v5_table_rebuilds_and_reviewer_forgeries_are_refused():
    root = Path(TED_ROOT)
    receipt_path = root / RECEIPT
    receipt = json.loads(receipt_path.read_bytes())
    assert sha256(receipt_path.read_bytes()).hexdigest() == engine._ADMISSION_RECEIPT_SHA256
    admission = dict(
        source_manifest_path=str((root / V5).parent / "manifest.json"),
        admission_evidence_path=str(receipt_path),
    )
    full = load_v5_program(root / V5, receipt["rights_terms_sha256"])
    applied = {
        name: part["applied"]["count"]
        for name, part in event_coverage(full)["by_treatment"].items()
    }
    assert applied == receipt["applied_treatment_counts"]
    assert len(pd.read_parquet(root / V5).query("row_kind == 'LEDGER_LEG'")) == 27

    def schedule(program):
        return {
            item["event_code"]: dict(
                capture=pd.Timestamp(item["capture_on"]),
                available=pd.Timestamp(item["available_on"]),
            )
            for item in program.event_schedule()
        }

    bound = engine._bound_rights_program(admission, receipt, full.ledger(), full, schedule(full))
    assert bound == full
    for forged in _forgeries(full):
        with pytest.raises(ValueError, match="RIGHTS_PROGRAM_NOT_BOUND"):
            engine._bound_rights_program(
                admission, receipt, forged.ledger(), forged, schedule(forged)
            )

    # order_eligible is recomputed from the pinned metadata chain; an
    # ineligible bar passed as eligible is refused.
    source, rules, _ = engine._bound_input(admission)
    eligibility = engine._bound_eligibility(admission)
    frame = source.bars.drop(columns="order_eligible").merge(rules, on=["date", "code"]).merge(
        eligibility, on=["date", "code"]
    )
    row = frame.loc[
        frame.date.between("2015-06-15", "2023-12-31") & frame.order_eligible.eq(False)
    ].iloc[[0]]
    engine._verify_bound_frames(admission, full, row, pd.DataFrame(), [row.date.iloc[0]])
    with pytest.raises(ValueError, match="ELIGIBILITY_NOT_FROM_BOUND_INPUT"):
        engine._verify_bound_frames(
            admission, full, row.assign(order_eligible=True), pd.DataFrame(), [row.date.iloc[0]]
        )
