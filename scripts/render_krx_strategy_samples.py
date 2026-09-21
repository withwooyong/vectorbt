"""Render deterministic synthetic charts for the 48 KRX lab strategy variants.

The figures explain signal and order sequencing. They are not market data or
performance examples. Run from the repository root with the project venv.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.krx_lab.config import ENTRIES, EXITS  # noqa: E402
from research.krx_lab.execution import simulate  # noqa: E402
from research.krx_lab.indicators import ema_sma_seeded, wilder_rsi14  # noqa: E402
from research.krx_lab.strategies import ENTRY_IDS, build_signals  # noqa: E402


OUTPUT = ROOT / "docs/strategy-research/backtest-lab/assets/strategy-samples"


def _chart_font() -> font_manager.FontProperties:
    installed = {item.name: item.fname for item in font_manager.fontManager.ttflist}
    for family in ("Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR"):
        if family in installed:
            return font_manager.FontProperties(fname=installed[family])
    return font_manager.FontProperties()


FONT = _chart_font()
plt.rcParams["svg.hashsalt"] = "krx-lab-strategy-samples-v1"
ENTRY_CASES = {
    "CROSS_5_20": (0, 328),
    "CROSS_10_20": (0, 333),
    "BREAKOUT_20": (0, 336),
    "BREAKOUT_60": (0, 358),
    "TREND_PULLBACK_3": (0, 382),
    "TREND_PULLBACK_5": (144, 293),
    "RSI_REENTRY_30": (None, 296),
    "RSI_REENTRY_40": (4, 321),
    "BOLLINGER_REENTRY_1_5": (0, 270),
    "BOLLINGER_REENTRY_2": (4, 318),
    "MACD_CROSS_SMA60": (0, 379),
    "MACD_CROSS_SMA120": (0, 379),
}
FORMULAS = {
    "CROSS_5_20": "SMA5[t-1] < SMA20[t-1], SMA5[t] > SMA20[t]",
    "CROSS_10_20": "SMA10[t-1] < SMA20[t-1], SMA10[t] > SMA20[t]",
    "BREAKOUT_20": "C[t] > max(C[t-20:t-1])",
    "BREAKOUT_60": "C[t] > max(C[t-60:t-1])",
    "TREND_PULLBACK_3": "C[t] > SMA60[t], return(3 bars) <= -3%",
    "TREND_PULLBACK_5": "C[t] > SMA60[t], return(3 bars) <= -5%",
    "RSI_REENTRY_30": "C[t] > SMA60[t], RSI[t-1] < 30 <= RSI[t]",
    "RSI_REENTRY_40": "C[t] > SMA60[t], RSI[t-1] < 40 <= RSI[t]",
    "BOLLINGER_REENTRY_1_5": "C[t] > SMA60[t], C[t-1] < Lower(1.5σ)[t-1], C[t] >= Lower(1.5σ)[t]",
    "BOLLINGER_REENTRY_2": "C[t] > SMA60[t], C[t-1] < Lower(2σ)[t-1], C[t] >= Lower(2σ)[t]",
    "MACD_CROSS_SMA60": "C[t] > SMA60[t], MACD[t-1] <= Signal[t-1], MACD[t] > Signal[t]",
    "MACD_CROSS_SMA120": "C[t] > SMA120[t], MACD[t-1] <= Signal[t-1], MACD[t] > Signal[t]",
}
SLUGS = {entry: entry.lower() for entry in ENTRIES}
FUTURE_RETURNS = np.array(
    [0.004, 0.015, 0.030, 0.052, 0.066, 0.040, 0.012, -0.015, -0.036, -0.056,
     -0.030, 0.000, 0.020, 0.035, 0.015, -0.005, 0.010, 0.025, 0.018, 0.005,
     -0.010, 0.004, 0.012, 0.006, -0.004, 0.008, 0.002, 0.010]
)


def _random_case(seed: int, n: int = 420) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    returns = 0.00025 + 0.009 * rng.normal(size=n) + 0.0015 * np.sin(np.arange(n) / 17 + seed)
    close = 10_000 * np.exp(np.cumsum(returns))
    open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.002, n))
    high = np.maximum(open_, close) * (1 + rng.uniform(0.002, 0.012, n))
    low = np.minimum(open_, close) * (1 - rng.uniform(0.002, 0.012, n))
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2020-01-01", periods=n),
            "code": "SYNTH",
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": rng.integers(150_000, 600_000, n),
        }
    )


def _rsi30_case(n: int = 340) -> pd.DataFrame:
    close = np.r_[np.linspace(10_000, 12_000, 250), np.linspace(12_100, 18_000, 40), np.linspace(18_000, 14_500, 6)]
    while len(close) < n:
        close = np.r_[close, close[-1] * (1.005 if len(close) == 296 else 1.001)]
    open_ = np.r_[close[0], close[:-1]]
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2020-01-01", periods=n),
            "code": "SYNTH",
            "open": open_,
            "high": np.maximum(open_, close) * 1.005,
            "low": np.minimum(open_, close) * 0.995,
            "close": close,
            "volume": 200_000,
        }
    )


def _case(entry_id: str) -> tuple[pd.DataFrame, pd.DataFrame, int]:
    seed, signal_at = ENTRY_CASES[entry_id]
    prices = _rsi30_case() if seed is None else _random_case(seed)
    signals = build_signals(prices)
    assert bool(signals.iloc[signal_at][entry_id]), f"target signal missing: {entry_id}"
    assert prices.iloc[signal_at - 249 : signal_at + 1][["open", "high", "low", "close", "volume"]].notna().all().all()
    assert prices.iloc[signal_at - 1].volume >= 100_000
    return prices, signals, signal_at


def _append_common_future(prefix: pd.DataFrame) -> pd.DataFrame:
    signal = prefix.iloc[-1]
    c = float(signal.close)
    dates = pd.bdate_range(signal.date + pd.offsets.BDay(1), periods=len(FUTURE_RETURNS))
    closes = c * (1 + FUTURE_RETURNS)
    opens = np.r_[c, closes[:-1]]
    future = pd.DataFrame(
        {
            "date": dates,
            "code": "SYNTH",
            "open": opens,
            "high": np.maximum(opens, closes) * 1.0015,
            "low": np.minimum(opens, closes) * 0.9985,
            "close": closes,
            "volume": 250_000,
            "sector": "SYNTHETIC",
            "tick_size": 1.0,
            "eligible": True,
        }
    )
    result = prefix.copy()
    result["sector"] = "SYNTHETIC"
    result["tick_size"] = 1.0
    result["eligible"] = True
    return pd.concat([result, future], ignore_index=True)


def _candles(ax, frame: pd.DataFrame, *, alpha: float = 1.0) -> None:
    x = np.arange(len(frame))
    width = 0.55
    for pos, row in zip(x, frame.itertuples(index=False)):
        rising = row.close >= row.open
        color = "#1769aa" if rising else "#d95f02"
        ax.vlines(pos, row.low, row.high, color=color, linewidth=0.8, alpha=alpha)
        bottom = min(row.open, row.close)
        height = max(abs(row.close - row.open), max(row.close * 0.00035, 0.5))
        ax.add_patch(
            Rectangle(
                (pos - width / 2, bottom), width, height, facecolor="white" if rising else color,
                edgecolor=color, linewidth=0.8, alpha=alpha,
            )
        )
    ax.set_xlim(-1, len(frame))
    ax.grid(axis="y", color="#dddddd", linewidth=0.6)


def _entry_context(ax, prices: pd.DataFrame, signal_at: int, entry_id: str) -> None:
    start = max(0, signal_at - 54)
    frame = prices.iloc[start : signal_at + 1].reset_index(drop=True)
    _candles(ax, frame)
    close = prices.close.astype(float)
    x = np.arange(len(frame))
    absolute = np.arange(start, signal_at + 1)
    legend_axes = [ax]
    if entry_id.startswith("CROSS"):
        fast = 5 if "5_20" in entry_id else 10
        ax.plot(x, close.rolling(fast).mean().iloc[absolute], color="#6a3d9a", label=f"SMA{fast}")
        ax.plot(x, close.rolling(20).mean().iloc[absolute], color="#1b9e77", label="SMA20")
    elif entry_id.startswith("BREAKOUT"):
        window = 20 if entry_id.endswith("20") else 60
        prior_high = close.shift(1).rolling(window).max()
        ax.plot(x, prior_high.iloc[absolute], color="#6a3d9a", linestyle="--", label=f"prior {window}D max")
    elif entry_id.startswith("TREND_PULLBACK"):
        ax.plot(x, close.rolling(60).mean().iloc[absolute], color="#1b9e77", label="SMA60")
    elif entry_id.startswith("RSI_REENTRY"):
        ax.plot(x, close.rolling(60).mean().iloc[absolute], color="#1b9e77", label="SMA60")
        rsi = wilder_rsi14(close)
        twin = ax.twinx()
        legend_axes.append(twin)
        threshold = 30 if entry_id.endswith("30") else 40
        twin.plot(x, rsi.iloc[absolute], color="#6a3d9a", linewidth=1.2, label="RSI14")
        twin.axhline(threshold, color="#6a3d9a", linestyle=":", linewidth=1, label=f"RSI {threshold}")
        twin.set_ylim(0, 100)
        twin.set_ylabel("RSI", fontproperties=FONT, fontsize=8)
    elif entry_id.startswith("BOLLINGER"):
        k = 1.5 if entry_id.endswith("1_5") else 2.0
        sma20 = close.rolling(20).mean()
        lower = sma20 - k * close.rolling(20).std(ddof=0)
        ax.plot(x, close.rolling(60).mean().iloc[absolute], color="#1b9e77", label="SMA60")
        ax.plot(x, lower.iloc[absolute], color="#6a3d9a", linestyle="--", label=f"Lower {k}σ")
    elif entry_id.startswith("MACD"):
        trend = 60 if entry_id.endswith("60") else 120
        ax.plot(x, close.rolling(trend).mean().iloc[absolute], color="#1b9e77", label=f"SMA{trend}")
        macd = ema_sma_seeded(close, 12) - ema_sma_seeded(close, 26)
        macd_signal = ema_sma_seeded(macd, 9)
        twin = ax.twinx()
        legend_axes.append(twin)
        twin.plot(x, macd.iloc[absolute], color="#6a3d9a", linewidth=1.2, label="MACD")
        twin.plot(x, macd_signal.iloc[absolute], color="#e7298a", linewidth=1.0, label="Signal")
        twin.axhline(0, color="#999999", linewidth=0.6)
        twin.set_ylabel("MACD", fontproperties=FONT, fontsize=8)
    ax.axvline(len(frame) - 1, color="#222222", linestyle="--", linewidth=1.1, label="signal t")
    ax.set_title(f"진입 판정 · {entry_id}\n{FORMULAS[entry_id]}", fontproperties=FONT, fontsize=11)
    ax.set_ylabel("가격 (합성)", fontproperties=FONT, fontsize=9)
    handles, labels = [], []
    for legend_ax in legend_axes:
        axis_handles, axis_labels = legend_ax.get_legend_handles_labels()
        handles.extend(axis_handles)
        labels.extend(axis_labels)
    ax.legend(handles, labels, loc="upper left", fontsize=7, ncol=5)
    ax.set_xticks([])


def _exit_panel(ax, display: pd.DataFrame, result: dict, entry_id: str, exit_id: str) -> dict:
    plan = result["plans"].iloc[0]
    fills = result["fills"]
    buys = fills[fills.side == "buy"]
    sells = fills[fills.side == "sell"]
    assert len(buys) == 1, f"expected one entry: {entry_id} {exit_id}"
    assert len(sells) == 1, f"expected one exit: {entry_id} {exit_id}"
    buy, sell = buys.iloc[0], sells.iloc[0]
    _candles(ax, display)
    dates = list(pd.to_datetime(display.date))
    date_to_x = {day: idx for idx, day in enumerate(dates)}
    signal_date = pd.Timestamp(plan.signal_date)
    buy_date, sell_date = pd.Timestamp(buy.date), pd.Timestamp(sell.date)
    expiry = pd.Timestamp(plan.expiry_date)
    sx, bx, ex = date_to_x[signal_date], date_to_x[buy_date], date_to_x[sell_date]
    ax.axhline(plan.stop_price, color="#d95f02", linestyle="--", linewidth=1.1, label=f"S {plan.stop_price:,.0f}")
    ax.axhline(plan.target_price, color="#1769aa", linestyle="-.", linewidth=1.1, label=f"T {plan.target_price:,.0f}")
    ax.axhline(plan.entry_cap, color="#666666", linestyle=":", linewidth=1.0, label=f"B {plan.entry_cap:,.0f}")
    ax.axvline(sx, color="#222222", linestyle="--", linewidth=0.9)
    if expiry in date_to_x:
        ax.axvline(date_to_x[expiry], color="#777777", linestyle=":", linewidth=1.0, label="만기")
    ax.scatter(bx, buy.price, s=46, marker="o", facecolor="#2ca25f", edgecolor="black", zorder=5, label="매수 t+1 시가")
    ax.scatter(ex, sell.price, s=58, marker="x", color="#c51b7d", linewidth=2.0, zorder=5, label="매도")
    if ex + 1 < len(display):
        ax.axvspan(ex + 0.5, len(display) - 0.5, color="#eeeeee", alpha=0.72)
    phase_labels = {
        "target_intraday": "목표가 장중",
        "stop_intraday": "손절가 장중",
        "target_gap_open": "갭 목표(시가)",
        "stop_gap_open": "갭 손절(시가)",
        "expiry_open": "만기 시가",
        "time_open": "보유기간 만료 시가",
    }
    exit_reason = str(sell.phase)
    exit_reason_ko = phase_labels.get(exit_reason, exit_reason)
    ax.annotate(
        exit_reason_ko, (ex, sell.price), xytext=(4, 8), textcoords="offset points", fontsize=7,
        fontproperties=FONT, color="#7a0177",
    )
    strategy_id = f"{entry_id}__{exit_id}"
    ax.set_title(strategy_id, fontproperties=FONT, fontsize=9)
    ax.tick_params(axis="both", labelsize=7)
    ax.set_xticks([sx, bx, ex])
    ax.set_xticklabels(["신호 t", "매수 t+1", "매도"], fontproperties=FONT, fontsize=7, rotation=28, ha="right")
    ax.legend(loc="upper left", fontsize=6, ncol=2)
    return {
        "strategy_id": strategy_id,
        "entry_cap": float(plan.entry_cap),
        "stop": float(plan.stop_price),
        "target": float(plan.target_price),
        "expiry": expiry.date().isoformat(),
        "entry_date": buy_date.date().isoformat(),
        "entry_price": float(buy.price),
        "exit_date": sell_date.date().isoformat(),
        "exit_price": float(sell.price),
        "exit_reason": exit_reason,
        "exit_reason_ko": exit_reason_ko,
    }


def render_entry(entry_id: str) -> dict:
    source, all_signals, signal_at = _case(entry_id)
    prefix = source.iloc[: signal_at + 1].copy()
    frozen = build_signals(prefix)
    target = frozen.iloc[-1]
    assert bool(target[entry_id])
    co_signals = [candidate for candidate in ENTRY_IDS if bool(target[candidate])]
    prices = _append_common_future(prefix)
    future_check = build_signals(prices.iloc[: signal_at + 1])
    pd.testing.assert_series_equal(
        frozen.iloc[-1][list(ENTRY_IDS) + ["atr14"]],
        future_check.iloc[-1][list(ENTRY_IDS) + ["atr14"]],
        check_names=False,
    )
    signal_frame = frozen.iloc[[-1]][["date", "code", "atr14", "avg_volume20", entry_id, "close"]]
    signal_date = pd.Timestamp(target.date)
    display_start = max(0, signal_at - 8)
    display = prices.iloc[display_start:].reset_index(drop=True)

    plt.rcParams.update({"font.family": FONT.get_name(), "axes.unicode_minus": False})
    fig = plt.figure(figsize=(14, 11))
    grid = fig.add_gridspec(3, 2, height_ratios=(1.15, 1, 1))
    entry_ax = fig.add_subplot(grid[0, :])
    _entry_context(entry_ax, source, signal_at, entry_id)
    panels = []
    for position, exit_id in enumerate(EXITS):
        ax = fig.add_subplot(grid[1 + position // 2, position % 2])
        result = simulate(
            prices,
            signal_frame,
            entry_id=entry_id,
            exit_id=exit_id,
            start=str(signal_date.date()),
            end=str(pd.Timestamp(prices.iloc[-1].date).date()),
            cost_bps=0,
            delay=1,
            calendar=[str(pd.Timestamp(day).date()) for day in prices.date],
        )
        panels.append(_exit_panel(ax, display, result, entry_id, exit_id))

    fig.suptitle(
        f"{entry_id} · 4개 청산 방식\n교육용 합성 예시 — 실제 종목·실제 수익률 아님",
        y=0.965,
        fontproperties=FONT,
        fontsize=16,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.016,
        "모든 진입 예시는 신호 뒤에 동일한 합성 가격 경로를 사용합니다. 신호일 종가에는 매수하지 않고 t+1 시가에 한 번만 진입합니다.\n"
        "합성 tick=1이며 현금·슬롯·업종·비용 게이트는 이해를 돕기 위해 그림에서 생략했습니다.",
        ha="center",
        fontproperties=FONT,
        fontsize=8.5,
        color="#333333",
    )
    fig.subplots_adjust(left=0.055, right=0.98, top=0.84, bottom=0.085, hspace=0.42, wspace=0.12)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image_path = OUTPUT / f"{SLUGS[entry_id]}.svg"
    svg_metadata = {"Title": f"Synthetic illustration for {entry_id}", "Date": None}
    fig.savefig(image_path, format="svg", dpi=120, metadata=svg_metadata)
    fig.savefig(image_path.with_suffix(".png"), format="png", dpi=140)
    plt.close(fig)
    source_hash = hashlib.sha256(
        prefix[["date", "open", "high", "low", "close", "volume"]].to_csv(index=False).encode("utf-8")
    ).hexdigest()
    return {
        "entry_id": entry_id,
        "formula": FORMULAS[entry_id],
        "synthetic_only": True,
        "signal_date": signal_date.date().isoformat(),
        "signal_close": float(target.close),
        "atr14": float(target.atr14),
        "previous_volume": int(prefix.iloc[-2].volume),
        "co_signals": co_signals,
        "prefix_sha256": source_hash,
        "image": image_path.relative_to(ROOT).as_posix(),
        "panels": panels,
    }


def main() -> None:
    assert tuple(ENTRY_IDS) == tuple(ENTRIES)
    records = [render_entry(entry_id) for entry_id in ENTRIES]
    panel_ids = [panel["strategy_id"] for record in records for panel in record["panels"]]
    expected = [f"{entry}__{exit_id}" for entry in ENTRIES for exit_id in EXITS]
    assert panel_ids == expected
    metadata = {
        "schema_version": "krx-strategy-sample-charts-v1",
        "purpose": "deterministic_synthetic_strategy_explanation",
        "warning": "not real market data and not performance evidence",
        "common_future_returns": FUTURE_RETURNS.tolist(),
        "entries": records,
    }
    (OUTPUT / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"images": len(records), "panels": len(panel_ids), "output": str(OUTPUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
