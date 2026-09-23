"""NOT-ADMITTED exploratory run of the 52 confirmed OHLCV20 configurations.

This path exists only to see whether the confirmed rules can make money at all
before the formal admission route is finished. It never admits anything:

* It is reached only through an explicit flag (``--exploratory`` on the CLI,
  ``exploratory=True`` in Python) and runs the portfolio engine with
  ``source_kind=EXPLORATORY_NOT_ADMITTED``; the REAL gate is untouched.
* Input loading and hash verification are the preflight's own. The run refuses
  to start unless the preflight blocks for exactly the three bypassed codes.
* Every output carries ``admission_status=NOT_ADMITTED_EXPLORATORY``.

A held trade is voided at the first session it meets an event the unadmitted
ledgers cannot settle (see ``VoidRule``). Nothing is adjusted, interpolated or
priced by assumption; the trade simply leaves the ledger and its slot gets the
pre-entry cash back. Entry decisions never look at future events.

The engine requires listing and sell-status columns that the corrected input
does not verify. They are derived here from ``can_sell``; because any held bar
with ``can_sell=False``, an invalid mark or no bar voids the trade, the derived
status never decides a fill.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import time

import numpy as np
import pandas as pd

from .ohlcv20_policy import Cost2026, experiments
from .ohlcv20_preflight import load_preflight_inputs
from .ohlcv20_real_execution import EXPLORATORY_SOURCE_KIND, run_ohlcv20_portfolio
from .ohlcv20_rights import RightsLedger
from .ohlcv20_signal import build_ohlcv20_signals


ADMISSION_STATUS = "NOT_ADMITTED_EXPLORATORY"
BYPASSED_REASON_CODES = (
    "CORRECTED_INPUT_NOT_EXECUTION_ADMITTED",
    "REAL_EXECUTION_NOT_ADMITTED",
    "RIGHTS_CONTRACT_NOT_EXECUTION_ADMITTED",
)
EVALUATION_START, EVALUATION_END = "2015-06-15", "2023-12-31"
INITIAL_CASH = 100_000_000
FRICTIONS = ("0.001", "0.002")
YEARS = (2020, 2021, 2022, 2023)
INTERPRETATION = (
    "EXPLORATORY_NOT_ADMITTED: 실행 승인 차단 3건을 우회한 탐색 결과다. "
    "실거래 · 전략 선정 · 승인 판단의 근거로 쓰지 않는다."
)
EXPLORATORY_ASSUMPTIONS = (
    "CORPORATE_EVENT_COVERAGE_ASSERTED_FOR_SIGNAL_BUILDER_NOT_CERTIFIED",
    "LISTING_AND_SELL_STATUS_DERIVED_FROM_CAN_SELL_NOT_VERIFIED",
    "EXIT_LEVELS_NOT_TICK_ROUNDED",
    "LOWER_LIMIT_LOCK_NOT_MODELLED",
    "COST2026_DOMESTIC_ORDINARY_SHARE_TAX_APPLIED_TO_EVERY_INSTRUMENT",
)
LIMITATIONS = (
    "제외 거래는 성과에서 빠진다. 권리 사건 · 거래정지 · 상장폐지 · 미확정 기업행사를 만난 "
    "거래가 빠지므로, 손실이 몰리기 쉬운 사건 보유분이 사라지는 생존 편향 방향으로 성과가 "
    "부풀 수 있다.",
    "제외 거래의 슬롯은 진입일부터 무효화일까지 진입 직전 현금으로 평가한다(자산 곡선 소급). "
    "그 기간 슬롯은 점유 상태였으므로 다른 후보를 받지 못했다. 배정 · 주문 판단은 소급하지 않는다.",
    "2020~2023 연도 수익률은 2015-06-15 부터의 연속 실행 곡선에서 잘라 쓴 것이다(전년 말 자산 → "
    "당해 말 자산). 해마다 1억 원 현금으로 새로 시작한 v3 독립 실행과 달리 연초 보유 포지션 · "
    "슬롯 배정 경로 · 자본 규모를 전년에서 이어받는다.",
    "정책의 선정 절차(2021~2023 결과를 키 하나를 잠글 때까지 숨긴다)와 달리 2021~2023 결과를 "
    "모든 설정에 대해 공개한다. 이 결과를 본 뒤의 선정은 내부 검증 구간을 이미 소비한 것이다.",
    "adjusted_valid 는 이후 사건의 승인 여부로 과거 바를 거르므로, 신호 가능 종목 집합이 "
    "이후 사건 정보에 의존한다(기존 승인 설계 그대로).",
    "현금배당은 정책대로 제외하며 배당락은 무효화 사건으로 보지 않는다.",
    "제공자 수정주가 비율(adjusted_close/close)의 0.5% 초과 변화 중 감사 사건이 없는 날은 "
    "미확정 기업행사로 본다. 제공자 반올림 잡음이 소수의 불필요한 제외를 낳을 수 있다.",
)
CATEGORY_LEGEND = {
    "a": "RIGHTS_EVENT: 유상증자 · 유무상 혼합 권리락, 분할(정산 계약 v4)",
    "b": "TRADE_STATUS_UNCONFIRMED: 바 없음 · 비체결 바 · can_sell=False 바",
    "c": "CORPORATE_ACTION_UNCONFIRMED: 무상증자 · 주식배당 · 미정 사건, 감자(정산 계약 v4), "
    "감사 없는 제공자 수정 비율 변화",
}
_PRIORITY = {"a": 0, "c": 1, "b": 2}
_AUDIT_CATEGORY = {
    "PAID_RIGHTS": "a",
    "MIXED_RIGHTS_DIVIDEND": "a",
    "BONUS_ISSUE": "c",
    "STOCK_DIVIDEND": "c",
    "UNDETERMINED": "c",
}
_NOT_VOIDING_AUDIT_KINDS = {"CASH_DIVIDEND"}
_SETTLEMENT_CATEGORY = {"SPIN_OFF": "a", "CAPITAL_REDUCTION": "c"}
_PROVIDER_STEP_TOLERANCE = 0.005
_PACKAGE = "data/sources/ohlcv-admission-20260922/corrected-input-v4"
_AUDIT = "data/sources/ohlcv-admission-20260922/factor-admission-v2/factor-admission-audit.parquet"
_CODE_FILES = (
    "ohlcv20_exploratory.py",
    "ohlcv20_real_execution.py",
    "ohlcv20_preflight.py",
    "ohlcv20_signal.py",
    "ohlcv20_input.py",
    "ohlcv20_eligibility.py",
    "ohlcv20_rights.py",
    "ohlcv20_policy.py",
    "ohlcv20_execution.py",
)
_OUTPUT_FILES = (
    "exploratory-summary.json",
    "equity-curves.csv",
    "exclusions.csv",
    "fills.csv",
    "signals.csv",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def identity_level(_side, _day, _market, value):
    """No tick table is confirmed in the policy, so levels stay unrounded."""
    return value


@dataclass(frozen=True)
class VoidRule:
    """Decide, from facts known at a session, whether a held trade is voided.

    ``events`` maps (session, code) to (category, detail) pairs for dated
    corporate or rights events. ``non_execution`` maps (session, code) to the
    sealed non-execution classification. The first match by priority a > c > b
    is the counted reason; every match is kept in ``all_reasons``.
    """

    events: dict
    non_execution: dict

    def __call__(self, day, code, row):
        found = list(self.events.get((day, code), ()))
        if row is None:
            found.append(("b", "HELD_BAR_MISSING"))
        elif not row["mark_valid"] or not row["can_sell"]:
            label = self.non_execution.get((day, code))
            if label is not None:
                found.append(("b", "NON_EXECUTION_" + str(label)))
            elif row["mark_valid"]:
                found.append(("b", "NO_TRADE_BAR_STATUS_UNVERIFIED"))
            else:
                found.append(("b", "MARK_INVALID_UNCLASSIFIED"))
        if not found:
            return None
        found.sort(key=lambda item: (_PRIORITY[item[0]], item[1]))
        return dict(
            category=found[0][0],
            detail=found[0][1],
            all_reasons="|".join(f"{c}:{d}" for c, d in found),
        )


def _session_on_or_after(calendar: pd.DatetimeIndex, value) -> pd.Timestamp | None:
    position = calendar.searchsorted(pd.Timestamp(value), side="left")
    return calendar[position] if position < len(calendar) else None


def _ex_session(calendar: pd.DatetimeIndex, record) -> pd.Timestamp | None:
    """T+2: the first session whose buyer is not on the register at ``record``."""
    last = calendar.searchsorted(pd.Timestamp(record), side="right") - 1
    return calendar[last - 1] if last >= 1 else None


def void_events(
    bars: pd.DataFrame,
    calendar: pd.DatetimeIndex,
    audit: pd.DataFrame,
    rights: dict,
) -> dict:
    """Date every event a holder can meet; only sessions, never later facts."""
    events: dict[tuple[pd.Timestamp, str], list[tuple[str, str]]] = {}

    def add(day, code, category, detail):
        if day is not None:
            events.setdefault((pd.Timestamp(day), str(code)), []).append((category, detail))

    audit_keys = set()
    for row in audit.itertuples(index=False):
        kind = str(row.official_event_kind)
        day = _session_on_or_after(calendar, row.effective_date)
        if day is not None:
            audit_keys.add((day, str(row.stock_code)))
        if kind in _NOT_VOIDING_AUDIT_KINDS:
            continue
        if kind not in _AUDIT_CATEGORY:
            raise ValueError("UNMAPPED_AUDIT_EVENT_KIND:" + kind)
        admitted = bool(row.price_admitted) and bool(row.volume_admitted)
        detail = f"AUDIT_{kind}_{'FACTOR_ADMITTED' if admitted else 'FACTOR_UNADMITTED'}"
        add(day, row.stock_code, _AUDIT_CATEGORY[kind], detail)
    for code, event in rights.items():
        if event.event_type not in _SETTLEMENT_CATEGORY:
            raise ValueError("UNMAPPED_SETTLEMENT_EVENT_TYPE:" + str(event.event_type))
        add(
            _ex_session(calendar, event.record_date),
            code,
            _SETTLEMENT_CATEGORY[event.event_type],
            "SETTLEMENT_" + event.event_type,
        )
    frame = bars[["date", "code", "close", "adjusted_close"]].sort_values(["code", "date"])
    close = frame["close"].to_numpy(dtype=float)
    adjusted = frame["adjusted_close"].to_numpy(dtype=float)
    ratio = pd.Series(
        np.divide(adjusted, close, out=np.full(len(frame), np.nan), where=close > 0),
        index=frame.index,
    )
    previous = ratio.groupby(frame["code"]).transform(lambda s: s.ffill().shift(1))
    step = (ratio / previous - 1).abs() > _PROVIDER_STEP_TOLERANCE
    for day, code in zip(frame.loc[step, "date"], frame.loc[step, "code"]):
        if (pd.Timestamp(day), str(code)) not in audit_keys:
            add(day, code, "c", "PROVIDER_ADJUSTMENT_STEP_NOT_IN_AUDIT")
    return {key: tuple(value) for key, value in events.items()}


def signal_inputs(bars: pd.DataFrame, audit: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Map the verified bars and factor audit onto the signal builder's contract.

    ``can_signal`` is the bar-level factor admission. Only raw-valid bars are
    passed, so a window crossing any other bar is skipped as incomplete. An
    unadmitted factor keeps value 1 only to satisfy the parser; the builder
    skips any window containing an unadmitted event before it reads a factor.
    """
    frame = bars.copy()
    ohlc = frame[["open", "high", "low", "close"]]
    raw_ok = (
        ohlc.notna().all(axis=1)
        & ohlc.gt(0).all(axis=1)
        & frame["high"].ge(frame[["open", "close"]].max(axis=1))
        & frame["low"].le(frame[["open", "close"]].min(axis=1))
        & frame["volume"].notna()
        & frame["turnover"].notna()
    )
    frame["eligible"] = frame["signal_eligible"].eq(True)
    frame["can_signal"] = frame["adjusted_valid"].eq(True) & frame["volume_adjusted_valid"].eq(True)
    codes = set(frame.loc[frame["eligible"] & frame["can_signal"], "code"])
    prices = frame.loc[
        raw_ok & frame["code"].isin(codes),
        [
            "date",
            "code",
            "market",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover",
            "eligible",
            "can_signal",
        ],
    ].reset_index(drop=True)
    effective = pd.to_datetime(audit["effective_date"])
    known = pd.to_datetime(audit["known_at_close_date"])
    factors = pd.DataFrame(
        dict(
            code=audit["stock_code"].astype(str),
            effective_date=effective,
            price_factor=[
                value if flag else "1"
                for value, flag in zip(audit["price_factor"], audit["price_admitted"])
            ],
            volume_factor=[
                value if flag else "1"
                for value, flag in zip(audit["volume_factor"], audit["volume_admitted"])
            ],
            known_at=known.fillna(effective),
            price_admitted=[bool(v) for v in audit["price_admitted"]],
            volume_admitted=[bool(v) for v in audit["volume_admitted"]],
        )
    )
    # known_at_close_date precedes every effective date in the sealed audit, so
    # this flag never decides a relevant event; False is the conservative value.
    factors["known_before_close"] = False
    return prices, factors


def execution_bars(
    bars: pd.DataFrame, signals: pd.DataFrame, calendar, *, start=EVALUATION_START
) -> pd.DataFrame:
    """Keep every bar the engine can read: signal codes from the later of their
    first signal and the session before the evaluation start. No code can be
    ordered or held before its first signal."""
    days = pd.DatetimeIndex(calendar)
    floor = days[max(days.searchsorted(pd.Timestamp(start)) - 1, 0)]
    if signals.empty:
        frame = bars.iloc[0:0].copy()
    else:
        first = signals.groupby("code")["signal_date"].min().clip(lower=floor)
        frame = bars.loc[bars["code"].isin(first.index)].copy()
        frame = frame.loc[frame["date"] >= frame["code"].map(first)]
    for column in ("open", "high", "low", "close", "volume"):
        if frame[column].isna().any():
            raise ValueError("MISSING_EXECUTION_BAR_VALUE:" + column)
    frame["listing_status"] = "LISTED"
    frame["listing_status_verified"] = True
    frame["sell_status"] = np.where(frame["can_sell"], "SELLABLE", "NO_TRADE")
    frame["sell_status_verified"] = True
    return frame[
        [
            "date",
            "code",
            "market",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "can_buy",
            "can_sell",
            "order_eligible",
            "mark_valid",
            "listing_status",
            "listing_status_verified",
            "sell_status",
            "sell_status_verified",
        ]
    ].reset_index(drop=True)


def trade_counts(fills: pd.DataFrame) -> dict:
    """Entries, fully sold trades and trades still open, from voided-free fills."""
    remaining: dict[int, int] = {}
    entries = completed = 0
    for row in fills.to_dict("records") if len(fills) else []:
        slot = row["slot_id"]
        if row["side"] == "BUY":
            entries += 1
            remaining[slot] = int(row["size"])
        else:
            remaining[slot] -= int(row["size"])
            if remaining[slot] == 0:
                completed += 1
                del remaining[slot]
    return dict(entries=entries, completed_trades=completed, open_trades_at_end=len(remaining))


def _drawdown(values: list[float]) -> float:
    peak, worst = values[0], 0.0
    for value in values:
        peak = max(peak, value)
        worst = min(worst, value / peak - 1)
    return worst


def performance(equity: pd.DataFrame, *, start=EVALUATION_START, initial_cash=INITIAL_CASH) -> dict:
    """Continuous-curve metrics plus calendar-year cuts of the same curve."""
    dates = pd.to_datetime(equity["date"])
    values = [float(v) for v in equity["equity"]]
    final = values[-1]
    years = (dates.iloc[-1] - pd.Timestamp(start)).days / 365.25
    cagr = (final / initial_cash) ** (1 / years) - 1 if final > 0 else -1.0
    yearly_return, yearly_mdd = {}, {}
    for year in YEARS:
        before = [v for d, v in zip(dates, values) if d.year < year]
        inside = [v for d, v in zip(dates, values) if d.year == year]
        if not before or not inside:
            continue
        yearly_return[str(year)] = inside[-1] / before[-1] - 1
        yearly_mdd[str(year)] = _drawdown([before[-1], *inside])
    return dict(
        final_equity_krw=float(final),
        total_return=final / initial_cash - 1,
        cagr=cagr,
        max_drawdown=_drawdown([float(initial_cash), *values]),
        yearly_return=yearly_return,
        mean_yearly_return_2020_2023=(
            sum(yearly_return.values()) / len(YEARS) if len(yearly_return) == len(YEARS) else None
        ),
        yearly_max_drawdown=yearly_mdd,
        worst_yearly_max_drawdown_2020_2023=min(yearly_mdd.values()) if yearly_mdd else None,
    )


def run_configuration(
    experiment,
    friction: str,
    *,
    bars,
    signals,
    calendar,
    rights_ledger,
    void_rule,
    start=EVALUATION_START,
    end=EVALUATION_END,
    initial_cash=INITIAL_CASH,
) -> dict:
    """Run one configuration on the exploratory path and return a marked row."""
    row = dict(
        admission_status=ADMISSION_STATUS,
        strategy=experiment.key,
        baseline=experiment.baseline,
        stop_pct=str(experiment.stop_pct),
        target_pct=str(experiment.target_pct),
        holding_months=experiment.holding_months,
        friction_rate=friction,
    )
    try:
        result = run_ohlcv20_portfolio(
            bars,
            signals,
            calendar,
            start=start,
            end=min(pd.Timestamp(end), pd.DatetimeIndex(calendar)[-1]),
            stop_pct=experiment.stop_pct,
            target_pct=experiment.target_pct,
            holding_months=experiment.holding_months,
            costs=Cost2026("DOMESTIC_ORDINARY_SHARE", Decimal(friction)),
            levels=identity_level,
            rights_ledger=rights_ledger,
            source_kind=EXPLORATORY_SOURCE_KIND,
            initial_cash=initial_cash,
            exploratory_void=void_rule,
        )
    except Exception as exc:  # recorded as a failed configuration, never relaxed
        row.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        return dict(row=row, equity=None, fills=None, exclusions=None)
    exclusions = result["exclusions"]
    row.update(status=result["status"], issues=list(result["issues"]))
    if result["status"] != "SUCCEEDED":
        return dict(row=row, equity=None, fills=result["fills"], exclusions=exclusions)
    by_category = {key: 0 for key in ("a", "b", "c")}
    by_detail: dict[str, int] = {}
    for item in exclusions.to_dict("records") if len(exclusions) else []:
        by_category[item["category"]] += 1
        by_detail[item["detail"]] = by_detail.get(item["detail"], 0) + 1
    row.update(performance(result["equity"], start=start, initial_cash=initial_cash))
    row.update(trade_counts(result["fills"]))
    row.update(
        excluded_trades=len(exclusions),
        excluded_by_category=by_category,
        excluded_by_detail=dict(sorted(by_detail.items())),
    )
    return dict(row=row, equity=result["equity"], fills=result["fills"], exclusions=exclusions)


_SHARED: dict = {}


def _init_worker(shared: dict) -> None:
    _SHARED.update(shared)


def _run_job(job: tuple[int, str]) -> dict:
    index, friction = job
    return run_configuration(experiments()[index], friction, **_SHARED)


def _stats(values: list[float]) -> dict:
    if not values:
        return dict(count=0)
    return dict(
        count=len(values),
        mean=statistics.fmean(values),
        median=statistics.median(values),
        max=max(values),
        min=min(values),
        positive=sum(1 for v in values if v > 0),
    )


def aggregate(rows: list[dict]) -> dict:
    ok = [row for row in rows if row["status"] == "SUCCEEDED"]

    def four_year(baseline=None) -> list[float]:
        return [
            row["mean_yearly_return_2020_2023"]
            for row in ok
            if row["mean_yearly_return_2020_2023"] is not None
            and (baseline is None or row["baseline"] is baseline)
        ]

    totals = {key: sum(row["excluded_by_category"][key] for row in ok) for key in ("a", "b", "c")}
    details: dict[str, int] = {}
    for row in ok:
        for key, value in row["excluded_by_detail"].items():
            details[key] = details.get(key, 0) + value
    completed = sum(row["completed_trades"] for row in ok)
    excluded = sum(row["excluded_trades"] for row in ok)
    top = sorted(ok, key=lambda row: (-row["cagr"], row["strategy"], row["friction_rate"]))[:5]
    return dict(
        admission_status=ADMISSION_STATUS,
        configurations=len(rows),
        succeeded=len(ok),
        failed=[
            dict(strategy=row["strategy"], friction_rate=row["friction_rate"], status=row["status"],
                 error=row.get("error"), issues=row.get("issues"))
            for row in rows
            if row["status"] != "SUCCEEDED"
        ],
        cagr=_stats([row["cagr"] for row in ok]),
        cagr_by_friction={
            friction: _stats([row["cagr"] for row in ok if row["friction_rate"] == friction])
            for friction in FRICTIONS
        },
        mean_yearly_return_2020_2023=_stats(four_year()),
        mean_yearly_return_2020_2023_baseline=_stats(four_year(True)),
        mean_yearly_return_2020_2023_non_baseline=_stats(four_year(False)),
        top5_by_cagr=[
            dict(
                strategy=row["strategy"],
                friction_rate=row["friction_rate"],
                cagr=row["cagr"],
                max_drawdown=row["max_drawdown"],
                completed_trades=row["completed_trades"],
                mean_yearly_return_2020_2023=row["mean_yearly_return_2020_2023"],
            )
            for row in top
        ],
        completed_trades=completed,
        excluded_trades=excluded,
        excluded_by_category=totals,
        excluded_by_detail=dict(sorted(details.items())),
        excluded_to_completed_ratio=excluded / completed if completed else None,
    )


def build_report(rows: list[dict], *, provenance: dict) -> dict:
    """Wrap configuration rows with the non-admission marks at the top level."""
    if any(row.get("admission_status") != ADMISSION_STATUS for row in rows):
        raise ValueError("UNMARKED_EXPLORATORY_ROW")
    return dict(
        schema="ohlcv20-exploratory-run-v1",
        admission_status=ADMISSION_STATUS,
        source_kind=EXPLORATORY_SOURCE_KIND,
        performance_valid=False,
        bypassed_reason_codes=list(BYPASSED_REASON_CODES),
        exploratory_assumptions=list(EXPLORATORY_ASSUMPTIONS),
        interpretation=INTERPRETATION,
        limitations=list(LIMITATIONS),
        exclusion_rule=dict(
            method="VOID_AT_FIRST_SESSION_HELD_INTO_EVENT_RESTORE_PRE_ENTRY_CASH",
            priority="a > c > b",
            categories=CATEGORY_LEGEND,
        ),
        evaluation_start=EVALUATION_START,
        evaluation_end=EVALUATION_END,
        initial_cash_krw=INITIAL_CASH,
        friction_rates=list(FRICTIONS),
        **provenance,
        summary=aggregate(rows),
        configurations=rows,
    )


def _git_head(repo: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _json_default(value):
    if isinstance(value, (pd.Timestamp,)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    raise TypeError(type(value).__name__)


def run_exploratory(
    root: Path,
    output_dir: Path,
    *,
    exploratory: bool = False,
    workers: int = 8,
    log=print,
) -> dict:
    """Load through the preflight, run all 52 configurations and write outputs."""
    if exploratory is not True:
        raise ValueError("EXPLORATORY_FLAG_REQUIRED")
    targets = [output_dir / name for name in _OUTPUT_FILES]
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise FileExistsError("Refusing to overwrite: " + ", ".join(existing))
    started = time.time()
    loaded = load_preflight_inputs(root)
    if loaded.reasons != sorted(BYPASSED_REASON_CODES):
        raise ValueError("UNEXPECTED_PREFLIGHT_BLOCKERS:" + ",".join(loaded.reasons))
    log(f"preflight verified in {time.time() - started:.0f}s; bypassing {loaded.reasons}")
    package = root / _PACKAGE
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    entry = next(item for item in manifest["files"] if item["file"] == "non-execution.parquet")
    if _sha256(package / "non-execution.parquet") != entry["sha256"]:
        raise ValueError("NON_EXECUTION_HASH_MISMATCH")
    audit_path = root / _AUDIT
    if _sha256(audit_path) != loaded.factor["output_sha256"]:
        raise ValueError("ADMITTED_FACTOR_EVIDENCE_HASH_MISMATCH")
    audit = pd.read_parquet(audit_path)
    blocked = pd.read_parquet(package / "non-execution.parquet")
    non_execution = {
        (pd.Timestamp(day), str(code)): str(label)
        for day, code, label in zip(
            pd.to_datetime(blocked["trading_date"]), blocked["stock_code"], blocked["classification"]
        )
    }
    bars = loaded.eligibility.bars
    calendar = pd.DatetimeIndex(loaded.prepared.calendar)
    events = void_events(bars, calendar, audit, loaded.rights)
    void_rule = VoidRule(events, non_execution)
    prices, factors = signal_inputs(bars, audit)
    log(f"signal inputs: {len(prices)} bars, {prices['code'].nunique()} codes")
    built = build_ohlcv20_signals(
        prices,
        factors,
        {"KOSPI": list(calendar), "KOSDAQ": list(calendar)},
        corporate_coverage_certified=True,
    )
    signals, skipped = built["signals"], built["skipped"]
    log(f"signals built in {time.time() - started:.0f}s: {len(signals)}")
    engine_bars = execution_bars(bars, signals, calendar, start=EVALUATION_START)
    log(f"execution bars: {len(engine_bars)}")
    rights_ledger = RightsLedger(loaded.rights, source_sha256=loaded.settlement["output_sha256"])
    shared = dict(
        bars=engine_bars,
        signals=signals,
        calendar=list(calendar),
        rights_ledger=rights_ledger,
        void_rule=void_rule,
    )
    jobs = [(index, friction) for index in range(len(experiments())) for friction in FRICTIONS]
    outcomes = []
    with ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(shared,)) as pool:
        for job, outcome in zip(jobs, pool.map(_run_job, jobs)):
            outcomes.append(outcome)
            row = outcome["row"]
            log(
                f"[{len(outcomes)}/{len(jobs)}] {row['strategy']} {row['friction_rate']} "
                f"{row['status']} cagr={row.get('cagr')} excluded={row.get('excluded_trades')} "
                f"{time.time() - started:.0f}s"
            )
    assert len(outcomes) == 52
    rows = [outcome["row"] for outcome in outcomes]
    here = Path(__file__).resolve().parent
    detail_counts: dict[str, int] = {}
    for reasons in events.values():
        for category, detail in reasons:
            key = f"{category}:{detail}"
            detail_counts[key] = detail_counts.get(key, 0) + 1
    provenance = dict(
        code=dict(
            git_head=_git_head(here),
            sha256={name: _sha256(here / name) for name in _CODE_FILES},
        ),
        input=dict(
            corrected_manifest_sha256=loaded.prepared.manifest_sha256,
            base_manifest_sha256=manifest.get("base_manifest_sha256"),
            non_execution_sha256=entry["sha256"],
            factor_evidence_sha256=loaded.factor_sha256,
            factor_audit_sha256=loaded.factor["output_sha256"],
            settlement_evidence_sha256=loaded.settlement_sha256,
            rights_terms_sha256=loaded.settlement["output_sha256"],
            eligibility_evidence_sha256=loaded.eligibility_sha256,
            metadata_sha256=loaded.metadata_sha256,
            raw_bars=len(bars),
            calendar_first=calendar[0],
            calendar_last=calendar[-1],
        ),
        preflight_reason_codes=list(loaded.reasons),
        signals=dict(
            signal_input_bars=len(prices),
            signal_input_codes=int(prices["code"].nunique()),
            signals=len(signals),
            signal_codes=int(signals["code"].nunique()) if len(signals) else 0,
            skipped=skipped["reason"].value_counts().to_dict() if len(skipped) else {},
            execution_bars=len(engine_bars),
        ),
        void_event_keys=dict(sorted(detail_counts.items())),
    )
    report = build_report(rows, provenance=provenance)
    output_dir.mkdir(parents=True, exist_ok=True)
    targets[0].write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=_json_default) + "\n",
        encoding="utf-8",
    )
    frames = {"equity": [], "fills": [], "exclusions": []}
    for outcome in outcomes:
        tags = dict(
            admission_status=ADMISSION_STATUS,
            strategy=outcome["row"]["strategy"],
            friction_rate=outcome["row"]["friction_rate"],
        )
        for key in frames:
            frame = outcome[key]
            if frame is not None and len(frame):
                frames[key].append(frame.assign(**tags))
    for key, path in zip(("equity", "exclusions", "fills"), targets[1:4]):
        data = pd.concat(frames[key], ignore_index=True) if frames[key] else pd.DataFrame()
        data.to_csv(path, index=False, encoding="utf-8")
    signals.assign(admission_status=ADMISSION_STATUS).to_csv(targets[4], index=False, encoding="utf-8")
    log(f"done in {time.time() - started:.0f}s")
    return report


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ted-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--exploratory",
        action="store_true",
        help="Run NOT_ADMITTED exploration; without it nothing runs.",
    )
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args(argv)
    if not args.exploratory:
        parser.exit(
            2,
            "EXPLORATORY_FLAG_REQUIRED: real execution stays blocked; "
            "pass --exploratory to run the NOT_ADMITTED exploration.\n",
        )
    report = run_exploratory(
        args.ted_root, args.output_dir, exploratory=True, workers=args.workers,
        log=lambda message: print(message, flush=True),
    )
    print(json.dumps(report["summary"], ensure_ascii=False, default=_json_default)[:4000], flush=True)


if __name__ == "__main__":
    main()
