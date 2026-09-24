"""Rights-aware 20-slot portfolio execution on explicitly admitted daily facts.

The fixture and real paths share calculations. Real execution requires every
input-admission flag to be positively set by an external verified adapter;
the currently delivered corrected-v4 package does not meet that gate. A
position is marked every session or the result is blocked without performance.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_FLOOR, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable

import pandas as pd

from .ohlcv20_execution import _d, _day
from .ohlcv20_rights import (
    RightsLedger,
    RightsProgram,
    coverage_mismatches,
    load_v5_program,
)


_ADMISSION_FLAGS = (
    "immutable_input_verified",
    "daily_universe_admitted",
    "adjusted_price_admitted",
    "volume_factors_admitted",
    "corporate_coverage_admitted",
    "rights_admitted",
    "market_rules_admitted",
    "real_execution_admitted",
)
# Treatments that change a held position; the other three leave it unchanged.
_HOLDER_TREATMENTS = {"QUANTITY_TRANSFORM", "PAID_RIGHTS_CASH", "BLOCK_ON_HOLD"}
# Settlement v5 bounds the optimistic new-share listing assumption this way.
_NEW_SHARE_REPORT_DAYS = 30
# sha256 of the on-disk bytes of ohlcv20-real-admission-v1.json (LF, stored
# as -text in ted-startup). Real execution accepts no other receipt.
_ADMISSION_RECEIPT_SHA256 = (
    "67c6fbceeb84323834008022873717ef10c1da188a869594ebd614674f3600a8"
)
_BOUND_BAR_COLUMNS = (
    "market",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "can_buy",
    "can_sell",
    "mark_valid",
)
_BOUND_RULE_COLUMNS = (
    "listing_status",
    "listing_status_verified",
    "sell_status",
    "sell_status_verified",
    "lower_limit_price",
    "lower_limit_price_verified",
)
_BOUND_INPUTS: dict[tuple, object] = {}
_ELIGIBILITY_EVIDENCE = "docs/research/evidence/ohlcv-admission-2026-09-22/ohlcv20-eligibility-v2.json"
_ELIGIBILITY_METADATA = (
    "data/sources/krx_open_api/instrument-history-2015-2023/instrument-snapshots.parquet"
)
# Signal membership and limit prices have no bound generator yet (stage B),
# so a real run keeps its result but withholds performance for this reason.
_UNBOUND_SIGNAL_GENERATOR = "SIGNALS_NOT_BOUND_TO_GENERATOR"


def _verify_real_admission(admission: dict | None, rights_ledger: RightsLedger) -> dict:
    if not isinstance(admission, dict) or any(
        admission.get(key) is not True for key in _ADMISSION_FLAGS
    ):
        raise ValueError("REAL_EXECUTION_NOT_ADMITTED")
    try:
        source_path = Path(admission["source_manifest_path"])
        receipt_path = Path(admission["admission_evidence_path"])
        expected_receipt_sha = admission["admission_evidence_sha256"]
        source_bytes, receipt_bytes = (
            source_path.read_bytes(),
            receipt_path.read_bytes(),
        )
    except (KeyError, TypeError, OSError) as exc:
        raise ValueError("REAL_ADMISSION_EVIDENCE_MISSING") from exc
    if sha256(receipt_bytes).hexdigest() != expected_receipt_sha:
        raise ValueError("REAL_ADMISSION_EVIDENCE_HASH_MISMATCH")
    source, receipt = json.loads(source_bytes), json.loads(receipt_bytes)
    if (
        receipt.get("schema") != "ohlcv20-real-admission-v1"
        or receipt.get("status") != "ADMITTED"
        or any(receipt.get(key) is not True for key in _ADMISSION_FLAGS)
        or source.get("real_execution_admitted") is not True
        or receipt.get("source_manifest_sha256") != sha256(source_bytes).hexdigest()
        or not rights_ledger.source_sha256
        or receipt.get("rights_terms_sha256") != rights_ledger.source_sha256
    ):
        raise ValueError("REAL_ADMISSION_EVIDENCE_NOT_BOUND")
    return receipt


def _bound_rights_program(
    admission: dict,
    receipt: dict,
    rights_ledger: RightsLedger,
    rights_program: RightsProgram | None,
    schedule: dict,
) -> RightsProgram:
    """Rebuild the rights program from the receipt-bound file bytes.

    A hash label or an event-key digest says nothing about legs or ratios, so
    caller objects are accepted only when they equal the rebuilt program.
    """
    receipt_path = Path(admission["admission_evidence_path"])
    if sha256(receipt_path.read_bytes()).hexdigest() != _ADMISSION_RECEIPT_SHA256:
        raise ValueError("ADMISSION_RECEIPT_NOT_PINNED")
    package = Path(admission["source_manifest_path"]).parent
    bound = load_v5_program(
        package / "rights-terms.parquet", receipt.get("rights_terms_sha256")
    )
    if coverage_mismatches(bound, receipt.get("rights_event_coverage")):
        raise ValueError("RIGHTS_EVENT_COVERAGE_MISMATCH")
    if (
        rights_program != bound
        or rights_ledger.events != bound.ledger_events
        or rights_ledger.source_sha256 != bound.source_sha256
    ):
        raise ValueError("RIGHTS_PROGRAM_NOT_BOUND")
    expected = {
        item["event_code"]: (_day(item["capture_on"]), _day(item["available_on"]))
        for item in bound.event_schedule()
    }
    if {code: (item["capture"], item["available"]) for code, item in schedule.items()} != expected:
        raise ValueError("RIGHTS_SCHEDULE_NOT_BOUND")
    return bound


def _bound_input(admission: dict):
    """Load the manifest's own input once per process, never from the caller."""
    from .ohlcv20_input import load_corrected_v4

    manifest_path = Path(admission["source_manifest_path"])
    receipt_path = Path(admission["admission_evidence_path"])
    manifest_bytes = manifest_path.read_bytes()
    key = (
        str(manifest_path.resolve()),
        sha256(manifest_bytes).hexdigest(),
        sha256(receipt_path.read_bytes()).hexdigest(),
    )
    if key not in _BOUND_INPUTS:
        source = load_corrected_v4(
            manifest_path.parent,
            base_snapshot=json.loads(manifest_bytes).get("base_snapshot"),
            admission_receipt=receipt_path,
        )
        rules = pd.read_parquet(manifest_path.parent / "market-rules.parquet")
        rules = rules.rename(columns={"stock_code": "code", "trading_date": "date"})
        rules = rules.assign(code=rules.code.astype(str), date=pd.to_datetime(rules.date))
        # The signal rule averages the 20 bars ending on the signal day; a
        # window that skips a sealed session cannot produce a signal at all.
        bars = source.bars[["date", "code", "turnover"]].sort_values(["code", "date"])
        position = pd.Series(
            pd.DatetimeIndex(source.calendar).get_indexer(bars.date), index=bars.index
        )
        grouped = bars.groupby("code", sort=False)
        total = grouped.turnover.transform(lambda values: values.rolling(20).sum())
        span = position - position.groupby(bars.code).shift(19)
        turnover20 = bars.assign(
            mean_turnover20=(total / 20).where(span.eq(19))
        )[["date", "code", "turnover", "mean_turnover20"]]
        _BOUND_INPUTS[key] = (source, rules, turnover20)
    return _BOUND_INPUTS[key]


def _bound_eligibility(admission: dict) -> pd.DataFrame:
    """Recompute order_eligible from the metadata the receipt's evidence pins.

    The eligibility evidence is bound by the receipt's input_hashes and names
    the metadata digest, so the flag is rebuilt rather than taken on trust.
    """
    from .ohlcv20_eligibility import attach_daily_eligibility, load_candidate_metadata

    source, _, _ = _bound_input(admission)
    manifest_path = Path(admission["source_manifest_path"]).resolve()
    receipt = json.loads(Path(admission["admission_evidence_path"]).read_bytes())
    relative = Path(receipt["source_manifest_path"])
    root = manifest_path.parents[len(relative.parts) - 1]
    key = (str(manifest_path), "eligibility")
    if key in _BOUND_INPUTS:
        return _BOUND_INPUTS[key]
    record_path = root / _ELIGIBILITY_EVIDENCE
    if (root / relative).resolve() != manifest_path or not record_path.is_file():
        raise ValueError("ELIGIBILITY_EVIDENCE_NOT_BOUND")
    record_bytes = record_path.read_bytes()
    expected = (receipt.get("input_hashes") or {}).get(_ELIGIBILITY_EVIDENCE)
    if sha256(record_bytes).hexdigest() != expected:
        raise ValueError("ELIGIBILITY_EVIDENCE_NOT_BOUND")
    record = json.loads(record_bytes)
    metadata, digest = load_candidate_metadata(root / _ELIGIBILITY_METADATA, set(source.bars.code))
    if digest != record["metadata_sha256"]:
        raise ValueError("ELIGIBILITY_EVIDENCE_NOT_BOUND")
    bars = attach_daily_eligibility(
        source.bars,
        source.selected_months,
        source.calendar,
        metadata,
        metadata_sha256=digest,
    ).bars
    window = bars.date.between(record["evaluation_start"], record["evaluation_end"])
    if int(bars.loc[window, "order_eligible"].sum()) != record[
        "evaluation_order_prior_session_cap_class_eligible"
    ]:
        raise ValueError("ELIGIBILITY_EVIDENCE_MISMATCH")
    _BOUND_INPUTS[key] = bars[["date", "code", "order_eligible"]].copy()
    return _BOUND_INPUTS[key]


def _verify_bound_frames(
    admission: dict, program: RightsProgram, prices: pd.DataFrame, signals: pd.DataFrame, days
) -> None:
    """Every bar, rule status, session and signal key must come from the manifest."""
    source, rules, turnover20 = _bound_input(admission)
    calendar = [_day(day) for day in source.calendar]
    start = bisect_left(calendar, days[0])
    if calendar[start : start + len(days)] != days:
        raise ValueError("CALENDAR_NOT_FROM_BOUND_INPUT")
    if len(prices):
        frame = prices.assign(
            date=pd.to_datetime(prices["date"]), code=prices["code"].astype(str)
        )
        try:
            merged = frame[["date", "code", *_BOUND_BAR_COLUMNS]].merge(
                source.bars[["date", "code", *_BOUND_BAR_COLUMNS]],
                on=["date", "code"],
                how="left",
                suffixes=("", "_bound"),
                indicator=True,
            )
        except KeyError as exc:
            raise ValueError("BARS_NOT_FROM_BOUND_INPUT") from exc
        same = merged["_merge"].eq("both")
        for name in _BOUND_BAR_COLUMNS:
            left, right = merged[name], merged[name + "_bound"]
            if name in {"open", "high", "low", "close", "volume"}:
                left, right = pd.to_numeric(left).astype(float), right.astype(float)
            same &= left.eq(right)
        if not same.all():
            raise ValueError("BARS_NOT_FROM_BOUND_INPUT")
        merged = frame[["date", "code", "order_eligible"]].merge(
            _bound_eligibility(admission),
            on=["date", "code"],
            how="left",
            suffixes=("", "_bound"),
        )
        if not merged.order_eligible.eq(True).eq(merged.order_eligible_bound.eq(True)).all():
            raise ValueError("ELIGIBILITY_NOT_FROM_BOUND_INPUT")
        try:
            merged = frame[["date", "code", *_BOUND_RULE_COLUMNS]].merge(
                rules[["date", "code", *_BOUND_RULE_COLUMNS]],
                on=["date", "code"],
                how="left",
                suffixes=("", "_bound"),
                indicator=True,
            )
        except KeyError as exc:
            raise ValueError("MARKET_RULES_NOT_FROM_BOUND_INPUT") from exc
        same = merged["_merge"].eq("both")
        for name in _BOUND_RULE_COLUMNS:
            left, right = merged[name], merged[name + "_bound"]
            if name == "lower_limit_price":
                left, right = pd.to_numeric(left).astype(float), right.astype(float)
                same &= left.eq(right) | (left.isna() & right.isna())
            elif name.endswith("_verified"):
                same &= left.eq(True).eq(right.eq(True))
            else:
                same &= left.eq(right)
        if not same.all():
            raise ValueError("MARKET_RULES_NOT_FROM_BOUND_INPUT")
        # Suspension proof exists only for ledger no-trade spans in the program;
        # no bound source proves a trigger on an untradeable session.
        expected = pd.Series(False, index=frame.index)
        for item in program.ledger_schedule:
            expected |= (
                frame.code.eq(item.event_code)
                & frame.date.ge(pd.Timestamp(item.suspended_from))
                & frame.date.lt(pd.Timestamp(item.available_on))
                & frame.can_sell.eq(False)
            )
        for name, allowed in (
            ("rights_suspension_verified", expected),
            ("regular_session_trigger_valid", pd.Series(False, index=frame.index)),
        ):
            if name in frame and (frame[name].eq(True) & ~allowed).any():
                raise ValueError("UNBOUND_EXECUTION_FLAG:" + name)
    if len(signals):
        keys = signals.assign(
            date=pd.to_datetime(signals["signal_date"]), code=signals["code"].astype(str)
        )[["date", "code", "turnover", "mean_turnover20"]]
        merged = keys.merge(
            turnover20,
            on=["date", "code"],
            how="left",
            suffixes=("", "_bound"),
            indicator=True,
        )
        # An inflated 20-day mean would loosen the buy liquidity limit.
        mean = pd.to_numeric(merged.mean_turnover20).astype(float)
        bound_mean = merged.mean_turnover20_bound.astype(float)
        if not (
            merged["_merge"].eq("both")
            & pd.to_numeric(merged.turnover).astype(float).eq(
                merged.turnover_bound.astype(float)
            )
            & ((mean - bound_mean).abs() <= bound_mean.abs() * 1e-12)
        ).all():
            raise ValueError("SIGNALS_NOT_FROM_BOUND_INPUT")


def _admit_bar(row: dict, source_kind: str) -> dict:
    """Validate one daily bar exactly as execution loads it; raise on failure."""
    for flag in ("can_buy", "can_sell", "order_eligible", "mark_valid"):
        if type(row[flag]) is not bool:
            raise ValueError("EXPLICIT_BOOLEAN_REQUIRED:" + flag)
    if row.get("listing_status") not in {"LISTED", "DELISTED"}:
        raise ValueError("EXPLICIT_LISTING_STATUS_REQUIRED")
    if (
        row.get("listing_status_verified") is not True
        or type(row["listing_status_verified"]) is not bool
    ):
        raise ValueError("VERIFIED_LISTING_STATUS_REQUIRED")
    sell_status = row.get("sell_status")
    if sell_status not in {
        "SELLABLE",
        "HALTED",
        "NO_TRADE",
        "LOWER_LIMIT_LOCKED",
    }:
        raise ValueError("EXPLICIT_SELL_STATUS_REQUIRED")
    if (
        row.get("sell_status_verified") is not True
        or type(row["sell_status_verified"]) is not bool
    ):
        raise ValueError("VERIFIED_SELL_STATUS_REQUIRED")
    if row["can_sell"] != (sell_status == "SELLABLE"):
        raise ValueError("SELL_STATUS_CAN_SELL_CONFLICT")
    if row["listing_status"] == "DELISTED" and (row["can_buy"] or row["can_sell"]):
        raise ValueError("DELISTED_TRADE_STATUS_CONFLICT")
    for optional_flag in (
        "regular_session_trigger_valid",
        "rights_suspension_verified",
    ):
        value = row.get(optional_flag, False)
        if pd.isna(value):
            value = False
        if type(value) is not bool:
            raise ValueError("EXPLICIT_BOOLEAN_REQUIRED:" + optional_flag)
        row[optional_flag] = value
    for key in ("open", "high", "low", "close", "volume"):
        row[key] = _d(row[key])
    lower_limit = row.get("lower_limit_price")
    if lower_limit is None or pd.isna(lower_limit):
        if source_kind == "REAL" and (row["can_buy"] or row["can_sell"]):
            raise ValueError("VERIFIED_LOWER_LIMIT_PRICE_REQUIRED")
    else:
        if row.get("lower_limit_price_verified") is not True:
            raise ValueError("VERIFIED_LOWER_LIMIT_PRICE_REQUIRED")
        row["lower_limit_price"] = _d(lower_limit)
        if row["lower_limit_price"] <= 0:
            raise ValueError("INVALID_LOWER_LIMIT_PRICE")
        if (
            row["can_sell"]
            and row["open"]
            == row["high"]
            == row["low"]
            == row["close"]
            == row["lower_limit_price"]
        ):
            raise ValueError("LOWER_LIMIT_LOCKED_SELL_STATUS_CONFLICT")
    if row["volume"] < 0 or (row["mark_valid"] and row["close"] <= 0):
        raise ValueError("INVALID_BAR_MARK_OR_VOLUME")
    if row["can_buy"] or row["can_sell"]:
        if (
            row["volume"] <= 0
            or row["low"] <= 0
            or row["low"] > min(row["open"], row["close"])
            or row["high"] < max(row["open"], row["close"])
        ):
            raise ValueError("INVALID_EXECUTABLE_OHLCV")
    return row


def _fraction(value: Decimal | Fraction | int) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def _money(value: Fraction) -> Decimal:
    with localcontext() as context:
        context.prec = 38
        return Decimal(value.numerator) / Decimal(value.denominator)


@dataclass
class _Sleeve:
    slot_id: int
    cash: Fraction
    idle_since: pd.Timestamp
    reusable_from: pd.Timestamp
    positions: dict[str, dict] = field(default_factory=dict)
    captured_event: str | None = None


def run_ohlcv20_portfolio(
    prices,
    signals,
    calendar,
    *,
    start,
    end,
    stop_pct,
    target_pct,
    holding_months,
    costs: Callable,
    levels: Callable,
    rights_ledger: RightsLedger,
    event_schedule=None,
    admission: dict | None = None,
    source_kind: str = "REAL",
    initial_cash=100_000_000,
    optimistic: bool = False,
    rights_program: RightsProgram | None = None,
    out_of_set_events: dict | None = None,
    margin_sessions: int = 252,
) -> dict:
    """Execute confirmed rules, including two-leg forced corporate exits.

    `event_schedule` requires event_code, capture_on and available_on. The
    external adapter must prove the capture session has qualifying settled
    ownership and that all replacement shares are available on available_on.

    `rights_program` applies the non-ledger v5 events to a position held at the
    prior close. `out_of_set_events` maps (date, code) to corporate events
    outside the execution touch set; a held position meeting one is blocked.
    """
    if source_kind not in {"REAL", "SYNTHETIC_FIXTURE"}:
        raise ValueError("UNKNOWN_EXECUTION_SOURCE_KIND")
    receipt = None
    if source_kind == "REAL":
        receipt = _verify_real_admission(admission, rights_ledger)
    if holding_months not in (1, 3) or type(holding_months) is not int:
        raise ValueError("HOLDING_MONTHS_MUST_BE_1_OR_3")
    stop, target, capital = _d(stop_pct), _d(target_pct), _d(initial_cash)
    if not 0 < stop < 1 or target <= 0 or capital <= 0:
        raise ValueError("INVALID_STRATEGY_AMOUNTS")
    first, last = _day(start), _day(end)
    days = [_day(day) for day in calendar]
    if (
        not days
        or days != sorted(set(days))
        or first > last
        or first < days[0]
        or last > days[-1]
    ):
        raise ValueError("INVALID_CALENDAR_COVERAGE")
    evaluation = [day for day in days if first <= day <= last]
    if not evaluation:
        raise ValueError("EMPTY_EVALUATION")
    next_day = dict(zip(days[:-1], days[1:]))
    rights_book = RightsLedger(
        rights_ledger.events, source_sha256=rights_ledger.source_sha256
    )

    price_frame, signal_frame = pd.DataFrame(prices), pd.DataFrame(signals)
    bars = {}
    for row in price_frame.to_dict("records"):
        day, code = _day(row["date"]), str(row["code"])
        if day not in days or (day, code) in bars:
            raise ValueError("DUPLICATE_OR_OFF_CALENDAR_BAR")
        bars[day, code] = _admit_bar(row, source_kind)

    signal_days: dict[pd.Timestamp, list[dict]] = {}
    signal_keys = set()
    for row in signal_frame.to_dict("records"):
        day, code = _day(row["signal_date"]), str(row["code"])
        if day not in days or (day, code) in signal_keys:
            raise ValueError("DUPLICATE_OR_OFF_CALENDAR_SIGNAL")
        signal_keys.add((day, code))
        if type(row["eligible"]) is not bool:
            raise ValueError("EXPLICIT_SIGNAL_ELIGIBILITY_REQUIRED")
        turnover, mean, limit = (
            _d(row["turnover"]),
            _d(row["mean_turnover20"]),
            _d(row["limit_price"]),
        )
        if turnover < 0 or mean <= 0 or limit <= 0:
            raise ValueError("INVALID_SIGNAL_AMOUNTS")
        if row["eligible"]:
            signal_days.setdefault(day, []).append(
                dict(code=code, turnover=turnover, mean=mean, limit=limit)
            )

    schedule = {}
    for row in pd.DataFrame(
        event_schedule if event_schedule is not None else []
    ).to_dict("records"):
        code = str(row["event_code"])
        capture, available = _day(row["capture_on"]), _day(row["available_on"])
        if code in schedule or code not in rights_book.events:
            raise ValueError("DUPLICATE_OR_UNKNOWN_RIGHTS_EVENT")
        record = pd.Timestamp(rights_book.events[code].record_date)
        if (
            capture not in days
            or available not in days
            or not capture <= record < available
        ):
            raise ValueError("INVALID_RIGHTS_EVENT_SCHEDULE")
        schedule[code] = dict(capture=capture, available=available, record=record)
    if source_kind == "REAL" and set(schedule) != set(rights_book.events):
        raise ValueError("INCOMPLETE_RIGHTS_EVENT_SCHEDULE")
    if source_kind == "REAL":
        rights_program = _bound_rights_program(
            admission, receipt, rights_ledger, rights_program, schedule
        )
        _verify_bound_frames(admission, rights_program, price_frame, signal_frame, days)
        try:
            locked_after = _day(receipt["admission_scope"]["development_period"]["end"])
        except (KeyError, TypeError) as exc:
            raise ValueError("VALIDATION_LOCK_UNDECLARED") from exc
        if days[-1] > locked_after:
            raise ValueError("VALIDATION_PERIOD_LOCKED")
        if out_of_set_events is None:
            raise ValueError("OUT_OF_TOUCH_SET_EVENTS_REQUIRED")
    elif rights_program is not None and rights_program.ledger_events != rights_book.events:
        raise ValueError("RIGHTS_PROGRAM_LEDGER_MISMATCH")
    if type(margin_sessions) is not int or margin_sessions < 0:
        raise ValueError("INVALID_MARGIN_SESSIONS")

    # An event applies to a position held at the close before its effective
    # date, so it is keyed by the first session on or after that date.
    corporate: dict[pd.Timestamp, list] = {}
    for event in rights_program.events if rights_program is not None else ():
        if not event.applies or event.treatment not in _HOLDER_TREATMENTS:
            continue
        position = bisect_left(days, pd.Timestamp(event.effective_date))
        if position < len(days) and first <= days[position] <= last:
            corporate.setdefault(days[position], []).append(event)
    outside = {
        (_day(day), str(code)): sorted(map(str, ids))
        for (day, code), ids in (out_of_set_events or {}).items()
        if ids
    }

    sleeves = [_Sleeve(i, _fraction(capital) / 20, first, first) for i in range(20)]
    fills, orders, equity, positions, issues, diagnostics = [], [], [], [], [], []
    rights_events, cash_receipts = [], []
    corporate_events, blocked_events, new_share_exits = [], [], []
    assignments: dict[pd.Timestamp, list[tuple[_Sleeve, dict]]] = {}
    sold_by_day_code: dict[tuple[pd.Timestamp, str], int] = {}
    attempted_exits: set[tuple[pd.Timestamp, int, str]] = set()
    converted_rights: set[tuple[str, int]] = set()

    def fee(side, day, market, amount: Decimal) -> Fraction:
        charge = _d(costs(side, day, market, amount))
        if charge < 0:
            raise ValueError("NEGATIVE_COST")
        return _fraction(charge)

    def level(side, day, market, value: Decimal) -> Decimal:
        rounded = _d(levels(side, day, market, value))
        if rounded <= 0:
            raise ValueError("NONPOSITIVE_ORDER_LEVEL")
        return rounded

    def report_new_share_exit(sleeve: _Sleeve, pos: dict, day: pd.Timestamp) -> None:
        # Positions whose new shares were assumed sellable from the effective
        # date form the optimistic bound when they close within the window.
        for event_id, effective in pos.get("new_share_events", ()):
            if day > effective + pd.Timedelta(days=_NEW_SHARE_REPORT_DAYS):
                continue
            invested = pos.get("invested")
            new_share_exits.append(
                dict(
                    event_id=event_id,
                    slot_id=sleeve.slot_id,
                    code=pos["code"],
                    effective_date=effective,
                    exit_date=day,
                    pnl=None if invested is None else _money(pos["proceeds"] - invested),
                )
            )

    def apply_corporate(sleeve: _Sleeve, pos: dict, event, day: pd.Timestamp) -> None:
        old = pos["size"]
        shares = old * event.quantity_multiplier
        whole = shares.numerator // shares.denominator
        cash = (shares - whole) * (event.fraction_cash_price or 0)
        if event.rights_value_per_share is not None:
            # Decision D6 (1): the rights are sold on the ex date and the sale
            # bears the ordinary selling cost.
            value = old * event.rights_value_per_share
            cash += value - fee("SELL", day, pos["market"], _money(value))
        sleeve.cash += cash
        if sleeve.cash < 0:
            raise ValueError("SELL_COST_EXCEEDS_SLOT_ASSETS")
        if pos.get("proceeds") is not None:
            pos["proceeds"] += cash
        pos["size"] = whole
        for key, side in (("stop", "STOP"), ("target", "TARGET")):
            if pos[key] is not None:
                pos[key] = level(
                    side,
                    day,
                    pos["market"],
                    _money(_fraction(pos[key]) * event.price_multiplier),
                )
        if event.new_share_bound and whole > old:
            pos.setdefault("new_share_events", []).append(
                (event.event_id, pd.Timestamp(event.effective_date))
            )
        corporate_events.append(
            dict(
                date=day,
                slot_id=sleeve.slot_id,
                code=pos["code"],
                event_id=event.event_id,
                treatment=event.treatment,
                old_shares=old,
                new_shares=whole,
                cash=_money(cash),
                exact_numerator=cash.numerator,
                exact_denominator=cash.denominator,
            )
        )
        if whole == 0:
            report_new_share_exit(sleeve, pos, day)
            del sleeve.positions[pos["code"]]
            finalize_slot(sleeve, day)

    def margin_end(pos: dict) -> int:
        return bisect_left(days, pos["expiry"]) + margin_sessions

    def finalize_slot(sleeve: _Sleeve, day: pd.Timestamp) -> None:
        if sleeve.positions:
            return
        sleeve.captured_event = None
        sleeve.idle_since = day
        sleeve.reusable_from = next_day.get(day, day + pd.Timedelta(days=1))

    def sell(
        sleeve: _Sleeve, pos: dict, day: pd.Timestamp, price: Decimal, reason: str
    ) -> None:
        code = pos["code"]
        pos["pending_exit"] = True
        attempted_exits.add((day, sleeve.slot_id, code))
        key = (day, code)
        capacity = int(
            (bars[key]["volume"] * Decimal("0.01")).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        remaining_capacity = max(0, capacity - sold_by_day_code.get(key, 0))
        quantity = min(pos["size"], remaining_capacity)
        if quantity < pos["size"]:
            diagnostics.append(
                dict(
                    date=day,
                    slot_id=sleeve.slot_id,
                    code=code,
                    kind="daily_sell_volume_cap",
                    action="DEFER_REMAINDER",
                )
            )
        if quantity == 0:
            return
        amount = quantity * price
        charge = fee("SELL", day, pos["market"], amount)
        sleeve.cash += _fraction(amount) - charge
        if sleeve.cash < 0:
            raise ValueError("SELL_COST_EXCEEDS_SLOT_ASSETS")
        if pos.get("proceeds") is not None:
            pos["proceeds"] += _fraction(amount) - charge
        fills.append(
            dict(
                date=day,
                slot_id=sleeve.slot_id,
                code=code,
                side="SELL",
                size=quantity,
                price=price,
                cost=_money(charge),
                reason=reason,
            )
        )
        sold_by_day_code[key] = sold_by_day_code.get(key, 0) + quantity
        pos["size"] -= quantity
        if pos["size"] == 0:
            report_new_share_exit(sleeve, pos, day)
            del sleeve.positions[code]
            finalize_slot(sleeve, day)

    def assign(signal_day: pd.Timestamp) -> None:
        order_day = next_day.get(signal_day)
        if order_day is None:
            return
        held = {code for sleeve in sleeves for code in sleeve.positions}
        candidates = sorted(
            (r for r in signal_days.get(signal_day, []) if r["code"] not in held),
            key=lambda r: (-r["turnover"], r["code"]),
        )
        idle = sorted(
            (s for s in sleeves if not s.positions and s.reusable_from <= order_day),
            key=lambda s: (s.idle_since, s.slot_id),
        )
        assignments[order_day] = [
            (s, dict(r, signal_date=signal_day)) for s, r in zip(idle, candidates)
        ]

    index = days.index(evaluation[0])
    if index:
        assign(days[index - 1])
    for day in evaluation:
        # Rights cash belongs to its original slot even if it was reused.
        for receipt in rights_book.due_cash(day):
            sleeves[receipt.slot_id].cash += receipt.amount
            cash_receipts.append(
                dict(
                    date=day,
                    due_date=receipt.due_date,
                    slot_id=receipt.slot_id,
                    event_code=receipt.event_code,
                    code=receipt.leg_code,
                    amount=_money(receipt.amount),
                    exact_numerator=receipt.amount.numerator,
                    exact_denominator=receipt.amount.denominator,
                )
            )

        for code, event in schedule.items():
            if day != event["available"]:
                continue
            for sleeve in sleeves:
                if sleeve.captured_event != code:
                    continue
                old = sleeve.positions.get(code)
                if old is None:
                    issues.append(
                        f"CAPTURED_RIGHTS_POSITION_MISSING:{day}:{code}:{sleeve.slot_id}"
                    )
                    break
                conversion = rights_book.convert(code, sleeve.slot_id, available_on=day)
                if conversion.old_shares_removed != old["size"]:
                    issues.append(
                        f"RIGHTS_QUANTITY_MISMATCH:{day}:{code}:{sleeve.slot_id}"
                    )
                    break
                converted_rights.add((code, sleeve.slot_id))
                del sleeve.positions[code]
                sleeve.captured_event = None
                for leg in conversion.allocations:
                    if leg.shares == 0:
                        continue
                    row = bars.get((day, leg.code))
                    if row is None or not row["mark_valid"]:
                        issues.append(f"UNKNOWN_RIGHTS_LEG_MARK:{day}:{leg.code}")
                        break
                    sleeve.positions[leg.code] = dict(
                        code=leg.code,
                        market=row["market"],
                        size=leg.shares,
                        entry_price=None,
                        stop=None,
                        target=None,
                        expiry=day,
                        pending_exit=True,
                        forced_event=code,
                    )
                    rights_events.append(
                        dict(
                            date=day,
                            slot_id=sleeve.slot_id,
                            event_code=code,
                            code=leg.code,
                            old_shares_removed=conversion.old_shares_removed,
                            new_shares=leg.shares,
                            fractional_numerator=leg.fractional_shares.numerator,
                            fractional_denominator=leg.fractional_shares.denominator,
                        )
                    )
                if issues:
                    break
                finalize_slot(sleeve, day)
            if issues:
                break
        if issues:
            break

        # Holdings at the prior close meet today's corporate events before any
        # order. Every blocking hit of the day is listed before stopping.
        for sleeve in sleeves:
            for pos in sleeve.positions.values():
                hits = outside.get((day, pos["code"]))
                if hits:
                    where = "BEYOND" if days.index(day) > margin_end(pos) else "WITHIN"
                    issues.append(
                        f"OUT_OF_TOUCH_SET_EVENT_{where}_MARGIN:{day}:{pos['code']}:"
                        + ",".join(hits)
                    )
        for event in corporate.get(day, []):
            for sleeve in sleeves:
                pos = sleeve.positions.get(event.code)
                if pos is None:
                    continue
                if event.treatment == "BLOCK_ON_HOLD":
                    blocked_events.append(
                        dict(
                            date=day,
                            slot_id=sleeve.slot_id,
                            code=event.code,
                            event_id=event.event_id,
                        )
                    )
                    issues.append(f"BLOCK_ON_HOLD_EVENT:{day}:{event.code}:{event.event_id}")
                elif sleeve.captured_event == event.code:
                    issues.append(
                        f"CORPORATE_EVENT_ON_CAPTURED_RIGHTS:{day}:{event.code}:{event.event_id}"
                    )
                elif not issues:
                    apply_corporate(sleeve, pos, event, day)
        if issues:
            break

        # Existing holdings and forced new legs sell before next-day entry orders.
        for sleeve in sleeves:
            for pos in list(sleeve.positions.values()):
                code = pos["code"]
                row = bars.get((day, code))
                if (
                    row is None
                    or not row["mark_valid"]
                    or row["market"] != pos["market"]
                ):
                    issues.append(f"UNKNOWN_HELD_MARK:{day}:{code}")
                    break
                if row["listing_status"] == "DELISTED":
                    issues.append(f"UNVALUED_DELISTED_HOLDING:{day}:{code}")
                    break
                if sleeve.captured_event == code:
                    if row["can_sell"] or not row["rights_suspension_verified"]:
                        issues.append(
                            f"CAPTURED_RIGHTS_SUSPENSION_NOT_VERIFIED:{day}:{code}"
                        )
                        break
                    continue  # Verified suspension until replacement shares arrive.
                if not row["can_sell"]:
                    if day >= pos["expiry"] or (
                        row["regular_session_trigger_valid"]
                        and row["volume"] > 0
                        and pos["stop"] is not None
                        and (row["low"] <= pos["stop"] or row["high"] >= pos["target"])
                    ):
                        pos["pending_exit"] = True
                    continue
                if pos["pending_exit"] or day >= pos["expiry"]:
                    sell(
                        sleeve,
                        pos,
                        day,
                        row["open"],
                        "rights_or_deferred_or_expiry_open",
                    )
                elif row["open"] <= pos["stop"]:
                    sell(sleeve, pos, day, row["open"], "stop_gap_open")
                elif row["open"] >= pos["target"]:
                    sell(sleeve, pos, day, row["open"], "target_gap_open")
            if issues:
                break
        if issues:
            break

        entered: dict[tuple[int, str], str] = {}
        for sleeve, plan in assignments.get(day, []):
            code, limit = plan["code"], plan["limit"]
            order = dict(
                date=day,
                signal_date=plan["signal_date"],
                slot_id=sleeve.slot_id,
                code=code,
                limit=limit,
                status="UNFILLED",
            )
            orders.append(order)
            row = bars.get((day, code))
            if row is None:
                issues.append(f"UNKNOWN_ORDER_BAR:{day}:{code}")
                break
            if not row["order_eligible"] or not row["can_buy"]:
                order["status"] = "INELIGIBLE_OR_UNTRADEABLE"
                continue
            if sleeve.positions or sleeve.reusable_from > day:
                raise ValueError("INVALID_SLOT_ASSIGNMENT")
            if any(code in other.positions for other in sleeves):
                order["status"] = "ALREADY_HELD"
                continue
            if sum(len(other.positions) for other in sleeves) >= 20:
                order["status"] = "POSITION_LIMIT_EXCESS"
                continue
            lo, hi = (
                0,
                int(
                    (sleeve.cash / _fraction(limit)).numerator
                    // (sleeve.cash / _fraction(limit)).denominator
                ),
            )
            while lo < hi:
                mid = (lo + hi + 1) // 2
                amount = mid * limit
                if (
                    _fraction(amount) + fee("BUY", day, row["market"], amount)
                    <= sleeve.cash
                ):
                    lo = mid
                else:
                    hi = mid - 1
            if lo == 0:
                order["status"] = "INSUFFICIENT_CASH"
                continue
            order["planned_size"] = lo
            order["liquidity_limit"] = plan["mean"] * Decimal("0.01")
            if lo * limit > order["liquidity_limit"]:
                # Assignment was fixed at signal close. Do not pass this candidate
                # to a smaller slot or replace it with another candidate today.
                order["status"] = "BUY_LIQUIDITY_LIMIT_EXCEEDED"
                continue
            if row["open"] <= limit:
                price, phase = row["open"], "OPEN"
            elif row["low"] < limit:
                price, phase = limit, "INTRADAY"
            else:
                continue
            amount = lo * price
            charge = fee("BUY", day, row["market"], amount)
            pre_entry_cash = sleeve.cash
            sleeve.cash -= _fraction(amount) + charge
            if sleeve.cash < 0:
                raise ValueError("COST_FUNCTION_NOT_MONOTONE")
            stop_level = level("STOP", day, row["market"], price * (1 - stop))
            target_level = level("TARGET", day, row["market"], price * (1 + target))
            if not stop_level < price < target_level:
                raise ValueError("INVALID_ROUNDED_EXIT_LEVELS")
            sleeve.positions[code] = dict(
                code=code,
                market=row["market"],
                size=lo,
                entry_price=price,
                stop=stop_level,
                target=target_level,
                expiry=day + pd.DateOffset(months=holding_months),
                pending_exit=False,
                forced_event=None,
                entry_day=day,
                pre_entry_cash=pre_entry_cash,
                invested=_fraction(amount) + charge,
                proceeds=Fraction(),
            )
            entered[sleeve.slot_id, code] = phase
            order["status"] = "FILLED"
            fills.append(
                dict(
                    date=day,
                    slot_id=sleeve.slot_id,
                    code=code,
                    side="BUY",
                    size=lo,
                    price=price,
                    cost=_money(charge),
                    reason=phase,
                )
            )
        if issues:
            break

        for sleeve in sleeves:
            for pos in list(sleeve.positions.values()):
                code = pos["code"]
                if (
                    sleeve.captured_event == code
                    or (day, sleeve.slot_id, code) in attempted_exits
                ):
                    continue
                row = bars[day, code]
                if pos["forced_event"] is not None:
                    continue  # Forced leg exits are always at the next sellable open.
                stop_hit = row["low"] <= pos["stop"]
                intraday_entry = entered.get((sleeve.slot_id, code)) == "INTRADAY"
                target_hit = (row["close"] if intraday_entry else row["high"]) >= pos[
                    "target"
                ]
                if not row["can_sell"]:
                    if day >= pos["expiry"] or (
                        row["regular_session_trigger_valid"]
                        and row["volume"] > 0
                        and (stop_hit or target_hit)
                    ):
                        pos["pending_exit"] = True
                    continue
                if stop_hit and target_hit and optimistic and not intraday_entry:
                    sell(sleeve, pos, day, pos["target"], "ambiguous_target_first")
                elif stop_hit:
                    sell(
                        sleeve,
                        pos,
                        day,
                        pos["stop"],
                        "ambiguous_stop_first" if target_hit else "stop_intraday",
                    )
                elif target_hit:
                    sell(sleeve, pos, day, pos["target"], "target_intraday")

        for code, event in schedule.items():
            if event["capture"] != day:
                continue
            for sleeve in sleeves:
                pos = sleeve.positions.get(code)
                if pos is None:
                    continue
                if sleeve.captured_event is not None:
                    issues.append(
                        f"OVERLAPPING_RIGHTS_EVENTS:{day}:{code}:{sleeve.slot_id}"
                    )
                    break
                rights_book.capture(
                    code, sleeve.slot_id, pos["size"], record_date=event["record"]
                )
                sleeve.captured_event = code
            if issues:
                break
        if issues:
            break

        receivables = sum(
            (
                item.amount
                for item in rights_book.pending_cash()
                if (item.event_code, item.slot_id) in converted_rights
            ),
            Fraction(),
        )
        total = receivables
        for sleeve in sleeves:
            exposure = Fraction()
            for pos in sleeve.positions.values():
                row = bars.get((day, pos["code"]))
                if row is None or not row["mark_valid"]:
                    issues.append(f"UNKNOWN_HELD_MARK:{day}:{pos['code']}")
                    break
                mark = _fraction(pos["size"] * row["close"])
                exposure += mark
                positions.append(
                    dict(
                        date=day,
                        slot_id=sleeve.slot_id,
                        code=pos["code"],
                        size=pos["size"],
                        mark_price=row["close"],
                        exposure=_money(mark),
                        pending_exit=pos["pending_exit"],
                        forced_event=pos["forced_event"],
                    )
                )
            if issues:
                break
            total += sleeve.cash + exposure
            if not sleeve.positions:
                positions.append(
                    dict(
                        date=day,
                        slot_id=sleeve.slot_id,
                        code=None,
                        size=0,
                        mark_price=None,
                        exposure=Decimal(0),
                        pending_exit=False,
                        forced_event=None,
                    )
                )
        if issues:
            break
        equity.append(
            dict(
                date=day,
                equity=_money(total),
                cash=_money(sum((s.cash for s in sleeves), Fraction())),
                receivables=_money(receivables),
                positions_count=sum(len(s.positions) for s in sleeves),
            )
        )
        assign(day)

    if not issues and any(sleeve.captured_event is not None for sleeve in sleeves):
        issues.append("UNCONVERTED_RIGHTS_AT_EVALUATION_END")
    blocked = bool(issues)
    withheld = [_UNBOUND_SIGNAL_GENERATOR] if source_kind == "REAL" else []
    result = dict(
        status="BLOCKED" if blocked else "SUCCEEDED",
        source_kind=source_kind,
        performance_valid=source_kind == "REAL" and not blocked and not withheld,
        performance_withheld=withheld,
        issues=issues,
        fills=pd.DataFrame(fills),
        orders=pd.DataFrame(orders),
        equity=pd.DataFrame([] if blocked else equity),
        positions=pd.DataFrame([] if blocked else positions),
        rights_events=pd.DataFrame(rights_events),
        cash_receipts=pd.DataFrame(cash_receipts),
        diagnostics=pd.DataFrame(diagnostics),
        corporate_events=pd.DataFrame(corporate_events),
        blocked_events=pd.DataFrame(blocked_events),
        new_share_exits=pd.DataFrame(new_share_exits),
        new_share_exit_summary=None
        if blocked
        else dict(
            window_calendar_days=_NEW_SHARE_REPORT_DAYS,
            exits=len(new_share_exits),
            pnl=_money(
                sum(
                    (_fraction(item["pnl"]) for item in new_share_exits if item["pnl"] is not None),
                    Fraction(),
                )
            ),
            exits_without_entry_cost=sum(item["pnl"] is None for item in new_share_exits),
        ),
        limitations=[
            "CASH_DIVIDENDS_EXCLUDED",
            "DAILY_VOLUME_PROXY_NOT_INTRADAY_PROOF",
            "FRACTIONAL_WON_CASH_MODELLED_AS_EXACT_RATIONAL",
            "CORPORATE_SUSPENSION_MARKS_REQUIRE_EXTERNAL_VALIDATION",
        ]
        + (
            [
                "NEW_SHARES_SELLABLE_FROM_EFFECTIVE_DATE_OPTIMISTIC",
                "PAID_RIGHTS_SOLD_AT_REFERENCE_PRICE_GAP_ON_EX_DATE",
            ]
            if rights_program is not None
            else []
        ),
    )
    return result
