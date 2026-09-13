"""연구 전용 단일 종목 일봉 백테스트 예제. 실제 주문·HTS 일치·실적 검증 도구가 아니다."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import vectorbt as vbt


INIT_CASH = 1.0
REQUIRED = ["date", "open", "high", "low", "close", "volume"]
ORDER_COLUMNS = ["strategy", "signal_date", "date", "side", "status", "price", "quantity", "fee"]
VARIANTS = {
    "T1": [("T1_SMA5_20", 5), ("T1_SMA10_20", 10)],
    "T2": [("T2_PREV20_HIGH", 20), ("T2_PREV60_HIGH", 60)],
    "T3": [("T3_PULLBACK_3", -3), ("T3_PULLBACK_5", -5)],
}


@dataclass
class Result:
    name: str
    equity: pd.DataFrame
    orders: list[dict]
    metrics: dict


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(message: str) -> None:
    raise ValueError(f"지원하지 않는 입력: {message}")


def load_csv(path: Path) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        fail(f"CSV를 읽을 수 없음 ({exc})")
    if list(frame.columns) != REQUIRED:
        fail("열은 정확히 date,open,high,low,close,volume 이어야 함")
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    for column in REQUIRED[1:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame.isna().any().any() or not np.isfinite(frame[REQUIRED[1:]].to_numpy()).all():
        fail("NaN 또는 날짜/숫자 변환 불가 값")
    if (frame["date"].dt.normalize() != frame["date"]).any():
        fail("date는 시간 정보 없는 일자여야 함")
    if frame["date"].duplicated().any():
        fail("중복 date")
    if not frame["date"].is_monotonic_increasing:
        fail("date 오름차순 정렬 필요")
    if (frame[REQUIRED[1:]] <= 0).any().any():
        fail("OHLC 또는 volume이 0 이하")
    if ((frame.high < frame[["open", "close"]].max(axis=1)) | (frame.low > frame[["open", "close"]].min(axis=1)) | (frame.high < frame.low)).any():
        fail("OHLC 고가/저가 관계 위반")
    if len(frame) < 61:
        fail("최소 61개 관측봉 필요")
    return frame.reset_index(drop=True)


def demo_data() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=130)
    trend = np.linspace(100, 140, len(dates))
    wave = 5 * np.sin(np.arange(len(dates)) * 0.31)
    close = trend + wave
    return pd.DataFrame({
        "date": dates,
        "open": close * (1 + 0.002 * np.cos(np.arange(len(dates)))),
        "high": close * 1.01,
        "low": close * 0.99,
        "close": close,
        "volume": np.full(len(dates), 200_000),
    })


def rolling_mean(close: pd.Series, window: int) -> pd.Series:
    # 지표 계산 경로를 명시적으로 Numba에 고정한다.
    return pd.Series(close.vbt.rolling_mean(window, engine="numba"), index=close.index)


def rolling_max(close: pd.Series, window: int) -> pd.Series:
    return pd.Series(close.vbt.rolling_max(window, engine="numba"), index=close.index)


def signals(frame: pd.DataFrame, family: str, value: int) -> pd.Series:
    close, volume = frame.close, frame.volume
    if family == "T1":
        fast, slow = rolling_mean(close, value), rolling_mean(close, 20)
        raw = (fast.shift(1) < slow.shift(1)) & (fast > slow)
    elif family == "T2":
        raw = close > rolling_max(close.shift(1), value)
    else:
        raw = (close > rolling_mean(close, 60)) & ((close / close.shift(3) - 1) * 100 <= value)
    return raw.fillna(False) & (volume.shift(1) >= 100_000)


def metric_values(dates: pd.Series, values: pd.Series) -> dict:
    values = pd.Series(values, dtype=float).reset_index(drop=True)
    with_initial = pd.concat([pd.Series([INIT_CASH]), values], ignore_index=True)
    daily = with_initial.pct_change().dropna()
    peak = with_initial.cummax()
    mdd = float((with_initial / peak - 1).min())
    elapsed = (pd.Timestamp(dates.iloc[-1]) - pd.Timestamp(dates.iloc[0])).days
    total = float(values.iloc[-1] / INIT_CASH - 1)
    cagr = float((values.iloc[-1] / INIT_CASH) ** (365.25 / elapsed) - 1) if elapsed else np.nan
    sharpe = float(daily.mean() / daily.std(ddof=1) * np.sqrt(252)) if len(daily) > 1 and daily.std(ddof=1) else np.nan
    return {"total_return": total, "calendar_elapsed_days": elapsed, "cagr": cagr, "sharpe_252_rf0_ddof1": sharpe, "max_drawdown": mdd}


def performance_bounds(dates: pd.Series, start: str | None, end: str | None) -> tuple[int, int]:
    start_i = int(np.searchsorted(dates.to_numpy(), np.datetime64(start))) if start else 61
    end_i = int(np.searchsorted(dates.to_numpy(), np.datetime64(end), side="right") - 1) if end else len(dates) - 1
    if start_i >= len(dates) or end_i < start_i:
        fail("start/end가 데이터 기간과 겹치지 않음")
    return start_i, end_i


def run_one(frame: pd.DataFrame, name: str, family: str, value: int, start: str | None, end: str | None, delay: int, fee: float) -> Result:
    dates = frame.date
    start_i, end_i = performance_bounds(dates, start, end)
    sig = signals(frame, family, value)
    scheduled = {}
    for t in np.flatnonzero(sig.to_numpy()):
        entry_i = t + delay
        if start_i <= entry_i <= end_i:
            scheduled.setdefault(entry_i, []).append(t)
    entries, exits = np.zeros(end_i - start_i + 1, dtype=bool), np.zeros(end_i - start_i + 1, dtype=bool)
    cash, qty, exit_i, entry_i, entry_signal_i = INIT_CASH, 0.0, None, None, None
    orders, rows = [], []
    for i in range(start_i, end_i + 1):
        exit_today = exit_i == i
        if exit_today:
            exits[i - start_i] = True
            gross = qty * frame.open.iloc[i]
            cost = gross * fee
            cash += gross - cost
            orders.append({"strategy": name, "signal_date": str(dates.iloc[entry_signal_i].date()), "date": str(dates.iloc[i].date()), "side": "sell", "status": "closed", "price": frame.open.iloc[i], "quantity": qty, "fee": cost})
            qty, exit_i, entry_i, entry_signal_i = 0.0, None, None, None
        for signal_i in scheduled.get(i, []):
            if exit_today:
                status = "rejected_same_day_exit"
            elif qty:
                status = "rejected_already_open"
            else:
                gross = cash / (1 + fee)
                qty = gross / frame.open.iloc[i]
                cost = gross * fee
                cash -= gross + cost
                entry_i = i
                entry_signal_i = signal_i
                exit_i = i + 10 if i + 10 <= end_i else None
                entries[i - start_i] = True
                status = "opened"
                orders.append({"strategy": name, "signal_date": str(dates.iloc[signal_i].date()), "date": str(dates.iloc[i].date()), "side": "buy", "status": status, "price": frame.open.iloc[i], "quantity": qty, "fee": cost})
                continue
            orders.append({"strategy": name, "signal_date": str(dates.iloc[signal_i].date()), "date": str(dates.iloc[i].date()), "side": "buy", "status": status, "price": np.nan, "quantity": 0.0, "fee": 0.0})
        rows.append({"date": dates.iloc[i], "strategy": name, "equity": cash + qty * frame.close.iloc[i], "cash": cash, "position_quantity": qty, "close": frame.close.iloc[i], "open_position": bool(qty)})
    equity = pd.DataFrame(rows)
    portfolio = vbt.Portfolio.from_signals(
        frame.close.iloc[start_i : end_i + 1].set_axis(equity.date),
        entries=entries,
        exits=exits,
        price=frame.open.iloc[start_i : end_i + 1].set_axis(equity.date),
        size=np.inf,
        fees=fee,
        slippage=0.0,
        init_cash=INIT_CASH,
        engine="numba",
        freq="1D",
    )
    portfolio_value = pd.Series(np.asarray(portfolio.value()), index=equity.index)
    expected = [o for o in orders if o["status"] in {"opened", "closed"}]
    records = portfolio.orders.records
    if not np.allclose(portfolio_value.to_numpy(), equity.equity.to_numpy(), rtol=1e-10, atol=1e-12) or len(records) != len(expected):
        raise AssertionError("감사용 원장과 vectorbt 체결/자산 값이 일치하지 않음")
    for record, order in zip(records.itertuples(index=False), expected):
        expected_index = int(np.searchsorted(equity.date.to_numpy(), np.datetime64(order["date"])))
        expected_side = 0 if order["side"] == "buy" else 1
        if record.idx != expected_index or record.side != expected_side or not np.allclose(
            [record.size, record.price, record.fees], [order["quantity"], order["price"], order["fee"]], rtol=1e-10, atol=1e-12
        ):
            raise AssertionError("감사용 원장과 vectorbt 주문 세부값이 일치하지 않음")
    equity["equity"] = portfolio_value
    opened = sum(o["status"] == "opened" for o in orders)
    closed = sum(o["status"] == "closed" for o in orders)
    metrics = metric_values(equity.date, equity.equity) | {"strategy": name, "init_cash": INIT_CASH, "opened_trades": opened, "closed_trades": closed, "unclosed_trades": opened - closed, "total_cost": sum(o["fee"] for o in orders), "terminal_position_unclosed": bool(qty)}
    return Result(name, equity, orders, metrics)


def buyhold(frame: pd.DataFrame, start: str | None, end: str | None, fee: float) -> dict:
    dates = frame.date
    start_i, end_i = performance_bounds(dates, start, end)
    gross = INIT_CASH / (1 + fee)
    qty = gross / frame.open.iloc[start_i]
    values = qty * frame.close.iloc[start_i : end_i + 1].reset_index(drop=True)
    return metric_values(dates.iloc[start_i : end_i + 1].reset_index(drop=True), values) | {"entry_fee": gross * fee, "terminal_position_unclosed": True}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--demo", action="store_true", help="합성 데이터로 실행")
    source.add_argument("--input", type=Path, help="단일 종목 OHLCV CSV")
    parser.add_argument("--price-semantics-reviewed", action="store_true", help="가격 의미를 별도 검토했다는 사용자 확인 (공식 검증 아님)")
    parser.add_argument("--strategy", choices=["T1", "T2", "T3", "all"], default="all")
    parser.add_argument("--cost-bps", type=float, default=30)
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--start", type=lambda value: str(pd.Timestamp(value).date()))
    parser.add_argument("--end", type=lambda value: str(pd.Timestamp(value).date()))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.input and not args.price_semantics_reviewed:
        parser.error("--input에는 --price-semantics-reviewed가 필수입니다. 이는 공식 검증을 뜻하지 않습니다.")
    if not np.isfinite(args.cost_bps) or args.cost_bps < 0 or args.delay < 1:
        parser.error("cost-bps는 유한한 0 이상 값, delay는 1 이상이어야 합니다.")
    if args.out.exists():
        parser.error("--out은 존재하지 않는 새 폴더여야 합니다.")
    return args


def main() -> None:
    args = parse_args()
    frame = demo_data() if args.demo else load_csv(args.input)
    if args.demo:
        frame = load_csv_data(frame)
    families = VARIANTS if args.strategy == "all" else {args.strategy: VARIANTS[args.strategy]}
    fee = args.cost_bps / 10_000
    results = [run_one(frame, name, family, value, args.start, args.end, args.delay, fee) for family, pairs in families.items() for name, value in pairs]
    args.out.mkdir(parents=True)
    benchmark = {f"buyhold_{key}": value for key, value in buyhold(frame, args.start, args.end, fee).items()}
    pd.DataFrame([r.metrics | benchmark for r in results]).to_csv(args.out / "summary.csv", index=False)
    pd.concat([r.equity for r in results]).to_csv(args.out / "equity.csv", index=False)
    pd.DataFrame([o for r in results for o in r.orders], columns=ORDER_COLUMNS).to_csv(args.out / "orders.csv", index=False)
    source_hash = hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest() if args.demo else sha256_path(args.input)
    manifest = {"research_only": True, "source": "synthetic_demo" if args.demo else str(args.input), "data_sha256": source_hash, "code_sha256": sha256_path(Path(__file__)), "parameters": vars(args) | {"input": str(args.input) if args.input else None, "out": str(args.out)}, "engine": {"portfolio": "numba", "indicators": "numba", "slippage": 0.0}, "vectorbt_version": vbt.__version__, "python_version": sys.version, "price_semantics_reviewed": bool(args.price_semantics_reviewed), "official_trading_calendar_verified": False, "default_common_warmup_bars": 61, "pre_start_signal_may_enter_on_first_performance_day": True, "limitations": ["공식 거래일 일치와 가격 조정 의미는 미검증", "분수 수량·init_cash=1 단일 종목 연구", "실제 주수, 공동계좌, HTS 일치, 실적 및 실주문 검증 아님", "기말 보유 포지션은 종가 평가이며 미청산으로 표시", "비용은 편도 fees만 적용하고 slippage=0"]}
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if args.self_check:
        assert all(r.metrics["init_cash"] == 1 and r.metrics["opened_trades"] >= r.metrics["closed_trades"] for r in results)
    print(f"wrote {len(results)} strategy results to {args.out}")


def load_csv_data(frame: pd.DataFrame) -> pd.DataFrame:
    """데모도 실제 입력과 동일한 fail-closed 검사를 적용한다."""
    if len(frame) < 61 or frame.isna().any().any() or (frame[REQUIRED[1:]] <= 0).any().any():
        fail("합성 데이터 생성 실패")
    return frame.sort_values("date").reset_index(drop=True)


if __name__ == "__main__":
    main()
