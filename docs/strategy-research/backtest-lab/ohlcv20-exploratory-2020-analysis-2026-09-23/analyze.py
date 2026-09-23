"""OHLCV20 탐색 백테스트(NOT_ADMITTED_EXPLORATORY) 52개의 2020년 수익이 신호 효과(alpha)인지
2020년 시장 반등(beta)인지를 판별하는 읽기 전용 분석 스크립트.

이 스크립트는 다음을 절대 하지 않는다.
  - 백테스트 재실행 (research/krx_lab/ohlcv20_exploratory.py 의 시뮬레이션 경로를 호출하지 않는다)
  - 입력 파일 쓰기/수정 (전부 읽기 전용으로 연다)
  - 2024-01-01 이후 가격 조회 (아래 CUTOFF 로 명시적으로 자른다)

사용법:
    .venv/Scripts/python.exe -X utf8 analyze.py [--data-dir ...] [--ted-root ...] [--out results.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_DATA_DIR = Path(
    "C:/Users/aeby/vscode/stock/vectorbt-data/krx-ohlcv20-exploratory-20260923"
)
DEFAULT_TED_ROOT = Path("C:/Users/aeby/vscode/ted-startup")
PRICE_PKG_REL = "data/sources/ohlcv-admission-20260922/corrected-input-v4/prices"
IDX_RAW_DIRS_REL = [
    "data/sources/krx_open_api/warmup-2014/raw",
    "data/sources/krx_open_api/source-complement-2015-2023/raw",
]

# 2024-01-01 이후 가격은 절대 읽지도 계산하지도 않는다 (브리프 제약).
CUTOFF = pd.Timestamp("2024-01-01")
YEARS = [2020, 2021, 2022, 2023]

STOP_REASONS = {"stop_intraday", "stop_gap_open", "ambiguous_stop_first"}
TARGET_REASONS = {"target_intraday", "target_gap_open"}
TIME_OR_EVENT_REASONS = {"rights_or_deferred_or_expiry_open"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_strategy(name: str) -> dict:
    m = re.match(r"SL(\d+)_TP(\d+)_M(\d+)", name)
    if not m:
        return {"sl": None, "tp": None, "m": None}
    return {"sl": int(m.group(1)), "tp": int(m.group(2)), "m": int(m.group(3))}


def exit_category(reason: str) -> str:
    if reason in STOP_REASONS:
        return "STOP"
    if reason in TARGET_REASONS:
        return "TARGET"
    if reason in TIME_OR_EVENT_REASONS:
        return "TIME_OR_EVENT"
    return "OTHER"


# ---------------------------------------------------------------------------
# 입력 로딩
# ---------------------------------------------------------------------------


def load_inputs(data_dir: Path):
    summary = json.loads((data_dir / "exploratory-summary.json").read_text(encoding="utf-8"))
    equity = pd.read_csv(data_dir / "equity-curves.csv", parse_dates=["date"])
    fills = pd.read_csv(data_dir / "fills.csv", parse_dates=["date"])
    signals = pd.read_csv(data_dir / "signals.csv", parse_dates=["signal_date"])
    exclusions = pd.read_csv(data_dir / "exclusions.csv", parse_dates=["date", "entry_date"])
    return summary, equity, fills, signals, exclusions


def input_hashes(data_dir: Path) -> dict:
    names = ["exploratory-summary.json", "equity-curves.csv", "fills.csv", "signals.csv", "exclusions.csv"]
    return {name: sha256_file(data_dir / name) for name in names}


# ---------------------------------------------------------------------------
# Q1. 신호
# ---------------------------------------------------------------------------


def analyze_signals(signals: pd.DataFrame, summary: dict) -> dict:
    s = signals.copy()
    s["year"] = s["signal_date"].dt.year
    by_year_market = (
        s.groupby(["year", "market"]).size().unstack(fill_value=0).to_dict(orient="index")
    )
    by_year = s.groupby("year").size().to_dict()
    total_input_codes = summary["signals"]["signal_input_codes"]  # 740, 평가 전체 기간 고정 모집단
    codes_per_year = s.groupby("year")["code"].nunique().to_dict()
    return {
        "note": (
            "signal_input_codes(740)는 2015-06-15~2023-12-31 전체 기간의 고정 모집단이며 연도별 "
            "분모가 아니다. density_vs_total_universe 는 그 고정 모집단 대비 연도별 신호 종목 비율이다."
        ),
        "signals_by_year": {int(k): int(v) for k, v in by_year.items()},
        "signals_by_year_market": {
            int(k): {mk: int(v) for mk, v in row.items()} for k, row in by_year_market.items()
        },
        "signal_codes_by_year": {int(k): int(v) for k, v in codes_per_year.items()},
        "signal_input_codes_total_universe": int(total_input_codes),
        "density_vs_total_universe_by_year": {
            int(k): round(v / total_input_codes, 6) for k, v in codes_per_year.items()
        },
    }


# ---------------------------------------------------------------------------
# Q2. 거래
# ---------------------------------------------------------------------------


def build_trades(fills: pd.DataFrame) -> pd.DataFrame:
    trades = []
    key_cols = ["strategy", "friction_rate", "slot_id"]
    for key, grp in fills.sort_values("date").groupby(key_cols, sort=False):
        grp = grp.sort_values("date").reset_index(drop=True)
        pending = None
        for _, row in grp.iterrows():
            if row["side"] == "BUY":
                pending = row
            elif row["side"] == "SELL" and pending is not None:
                buy_notional = pending["price"] * pending["size"] + pending["cost"]
                sell_notional = row["price"] * row["size"] - row["cost"]
                pnl = sell_notional - buy_notional
                ret = pnl / buy_notional if buy_notional else np.nan
                trades.append(
                    dict(
                        strategy=key[0],
                        friction_rate=key[1],
                        slot_id=key[2],
                        code=pending["code"],
                        entry_date=pending["date"],
                        exit_date=row["date"],
                        entry_price=pending["price"],
                        exit_price=row["price"],
                        size=row["size"],
                        pnl=pnl,
                        ret=ret,
                        reason=row["reason"],
                        exit_category=exit_category(row["reason"]),
                        holding_days=(row["date"] - pending["date"]).days,
                    )
                )
                pending = None
    return pd.DataFrame(trades)


def analyze_trades(trades: pd.DataFrame) -> dict:
    t = trades.copy()
    t["exit_year"] = t["exit_date"].dt.year
    t = t[t["exit_year"].isin(YEARS)]
    axes = t["strategy"].apply(parse_strategy).apply(pd.Series)
    t = pd.concat([t, axes], axis=1)

    by_year = {}
    for year, g in t.groupby("exit_year"):
        by_year[int(year)] = {
            "completed_trades": int(len(g)),
            "win_rate": round(float((g["ret"] > 0).mean()), 6),
            "mean_return": round(float(g["ret"].mean()), 6),
            "median_return": round(float(g["ret"].median()), 6),
            "mean_holding_days": round(float(g["holding_days"].mean()), 2),
            "exit_reason_composition": {
                k: int(v) for k, v in g["exit_category"].value_counts().to_dict().items()
            },
        }

    def axis_2020_vs_rest(col: str) -> dict:
        out = {}
        for val, g in t.groupby(col):
            g2020 = g[g["exit_year"] == 2020]
            grest = g[g["exit_year"] != 2020]
            out[str(val)] = {
                "n_2020": int(len(g2020)),
                "mean_return_2020": round(float(g2020["ret"].mean()), 6) if len(g2020) else None,
                "n_rest": int(len(grest)),
                "mean_return_rest": round(float(grest["ret"].mean()), 6) if len(grest) else None,
            }
        return out

    return {
        "by_year": by_year,
        "by_sl_axis_2020_vs_rest": axis_2020_vs_rest("sl"),
        "by_tp_axis_2020_vs_rest": axis_2020_vs_rest("tp"),
        "by_m_axis_2020_vs_rest": axis_2020_vs_rest("m"),
    }


# ---------------------------------------------------------------------------
# Q3. 투자 비중
# ---------------------------------------------------------------------------


def analyze_exposure(equity: pd.DataFrame) -> dict:
    e = equity.copy()
    e = e[e["date"] < CUTOFF]
    e["year"] = e["date"].dt.year
    e["invested_frac"] = 1 - (e["cash"] / e["equity"])
    out = {}
    for year, g in e.groupby("year"):
        if year not in YEARS:
            continue
        out[int(year)] = {
            "mean_invested_fraction": round(float(g["invested_frac"].mean()), 6),
            "mean_positions_count": round(float(g["positions_count"].mean()), 3),
        }
    return out


# ---------------------------------------------------------------------------
# Q4. 시장 비교
# ---------------------------------------------------------------------------


def load_equal_weight_returns(ted_root: Path, codes: set[str] | None) -> pd.Series:
    """동일가중 일간 수익률(수정주가 기준)을 만든다.

    codes=None 이면 원시 가격 Parquet(raw bars)에 있는 **전체 종목**을 쓴다(신호 발생 여부로
    사후에 고르지 않은, look-ahead 없는 벤치마크). codes 를 주면 그 부분집합만 쓴다(선택 편향이
    있는 참고값 계산용).

    당일 관측이 없는 종목(거래정지·상장폐지 등)은 그 날의 평균 계산에서 그냥 빠진다
    (그 날 값이 있는 종목만으로 단순 평균) — 명시적 보간·전진채움을 하지 않는다.
    """
    pkg = ted_root / PRICE_PKG_REL
    frames = []
    for fp in sorted(pkg.glob("price-*.parquet")):
        df = pd.read_parquet(
            fp,
            columns=["adjusted", "close_price", "stock_code", "trading_date"],
        )
        df = df[df["adjusted"]]
        if codes is not None:
            df = df[df["stock_code"].isin(codes)]
        if len(df):
            frames.append(df)
    if not frames:
        return pd.Series(dtype=float)
    prices = pd.concat(frames, ignore_index=True)
    prices["trading_date"] = pd.to_datetime(prices["trading_date"])
    prices = prices[prices["trading_date"] < CUTOFF]
    prices = prices.drop_duplicates(["stock_code", "trading_date"])
    wide = prices.pivot(index="trading_date", columns="stock_code", values="close_price").sort_index()
    rets = wide.pct_change()
    eq_weight = rets.mean(axis=1, skipna=True)
    return eq_weight


def load_index_series(ted_root: Path, idx_name: str) -> pd.Series:
    """로컬 KRX 지수 raw JSON(일별)에서 종가 지수를 뽑는다. 참고용이며 회귀에는 쓰지 않는다."""
    rows = {}
    for rel in IDX_RAW_DIRS_REL:
        d = ted_root / rel
        subdir = "idx_kospi_dd_trd" if idx_name == "코스피" else "idx_kosdaq_dd_trd"
        p = d / subdir
        if not p.exists():
            continue
        for fp in sorted(p.glob("*.json")):
            date_str = fp.stem
            date = pd.Timestamp(date_str)
            if date >= CUTOFF:
                continue
            try:
                payload = json.loads(fp.read_text(encoding="utf-8"))
            except Exception:
                continue
            for item in payload.get("OutBlock_1", []):
                if item.get("IDX_NM") == idx_name:
                    val = item.get("CLSPRC_IDX")
                    if val:
                        try:
                            rows[date] = float(val)
                        except ValueError:
                            pass
                    break
    return pd.Series(rows).sort_index()


def annual_returns_from_daily(daily: pd.Series) -> dict:
    d = daily.dropna()
    d = d[d.index < CUTOFF]
    d = d[d.index.year.isin(YEARS)]
    out = {}
    for year, g in d.groupby(d.index.year):
        out[int(year)] = round(float((1 + g).prod() - 1), 6)
    return out


def strategy_daily_returns(equity: pd.DataFrame) -> pd.Series:
    """52개 조합의 일간 수익률을 날짜별로 동일가중 평균한 '평균 전략' 일간 수익률."""
    e = equity.copy()
    e = e[e["date"] < CUTOFF]
    e["config"] = e["strategy"] + "|" + e["friction_rate"].astype(str)
    wide = e.pivot(index="date", columns="config", values="equity").sort_index()
    rets = wide.pct_change()
    return rets.mean(axis=1, skipna=True)


def ols_full(y: pd.Series, x: pd.Series) -> dict:
    """alpha, beta, R^2, alpha/beta 의 표준오차와 t값을 계산한다 (단순 OLS, HAC 보정 없음)."""
    df = pd.concat([y, x], axis=1, join="inner").dropna()
    n = len(df)
    if n < 5:
        return dict(alpha=float("nan"), beta=float("nan"), r_squared=float("nan"), n=n,
                    alpha_se=float("nan"), alpha_t=float("nan"), beta_se=float("nan"), beta_t=float("nan"))
    yv = df.iloc[:, 0].to_numpy()
    xv = df.iloc[:, 1].to_numpy()
    X = np.column_stack([np.ones(n), xv])
    coef, *_ = np.linalg.lstsq(X, yv, rcond=None)
    alpha, beta = coef
    fitted = X @ coef
    resid = yv - fitted
    dof = n - 2
    sigma2 = float(np.sum(resid**2) / dof) if dof > 0 else float("nan")
    xtx_inv = np.linalg.inv(X.T @ X)
    cov = sigma2 * xtx_inv
    alpha_se = float(np.sqrt(cov[0, 0]))
    beta_se = float(np.sqrt(cov[1, 1]))
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((yv - yv.mean()) ** 2))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return dict(
        alpha=float(alpha),
        beta=float(beta),
        r_squared=r_squared,
        n=n,
        alpha_se=alpha_se,
        alpha_t=float(alpha / alpha_se) if alpha_se else float("nan"),
        beta_se=beta_se,
        beta_t=float(beta / beta_se) if beta_se else float("nan"),
    )


def analyze_market(
    ted_root: Path,
    signals: pd.DataFrame,
    equity: pd.DataFrame,
    summary: dict,
    exposure: dict,
) -> dict:
    # 1) 신호 발생 종목(283개)만의 동일가중 수익률 — 사후 선택 편향이 있는 참고값.
    signal_codes = set(signals["code"].astype(str).unique())
    eq_weight_signal_universe = load_equal_weight_returns(ted_root, signal_codes)
    signal_universe_annual = annual_returns_from_daily(eq_weight_signal_universe)

    # 2) 원시 가격 Parquet(raw bars)에 있는 전체 종목의 동일가중 수익률 — look-ahead 없는 주 벤치마크.
    eq_weight_full = load_equal_weight_returns(ted_root, None)
    full_universe_annual = annual_returns_from_daily(eq_weight_full)

    # 로컬 raw JSON(KRX 공개 API 원본, source-complement-2015-2023 · warmup-2014)에서 직접 계산.
    # 외부 공개 수치를 그대로 가져온 것이 아니다.
    kospi_daily = load_index_series(ted_root, "코스피").pct_change()
    kosdaq_daily = load_index_series(ted_root, "코스닥").pct_change()
    kospi_annual = annual_returns_from_daily(kospi_daily)
    kosdaq_annual = annual_returns_from_daily(kosdaq_daily)

    strat_daily = strategy_daily_returns(equity)

    cfg_yearly = [c["yearly_return"] for c in summary["configurations"]]
    mean_strategy_annual = {
        y: round(float(np.mean([c.get(str(y)) for c in cfg_yearly])), 6) for y in YEARS
    }

    regression = {}
    predicted_vs_actual = {}
    for year in YEARS:
        y_daily = strat_daily[strat_daily.index.year == year]
        x_daily = eq_weight_full[eq_weight_full.index.year == year]
        fit = ols_full(y_daily, x_daily)
        alpha_daily = fit["alpha"]
        alpha_annual = (1 + alpha_daily) ** 252 - 1 if not np.isnan(alpha_daily) else float("nan")
        regression[year] = {
            "beta": round(fit["beta"], 4) if not np.isnan(fit["beta"]) else None,
            "beta_se": round(fit["beta_se"], 4) if not np.isnan(fit["beta_se"]) else None,
            "beta_t": round(fit["beta_t"], 3) if not np.isnan(fit["beta_t"]) else None,
            "alpha_daily": round(alpha_daily, 8) if not np.isnan(alpha_daily) else None,
            "alpha_annualized": round(alpha_annual, 6) if not np.isnan(alpha_annual) else None,
            "alpha_se_daily": round(fit["alpha_se"], 8) if not np.isnan(fit["alpha_se"]) else None,
            "alpha_t": round(fit["alpha_t"], 3) if not np.isnan(fit["alpha_t"]) else None,
            "r_squared": round(fit["r_squared"], 4) if not np.isnan(fit["r_squared"]) else None,
            "n_days": fit["n"],
        }
        market_ret = full_universe_annual.get(year)
        invested = exposure.get(year, {}).get("mean_invested_fraction")
        actual = mean_strategy_annual.get(year)
        if market_ret is not None and invested is not None and actual is not None:
            predicted = market_ret * invested
            predicted_vs_actual[year] = {
                "market_return": round(market_ret, 6),
                "mean_invested_fraction": round(invested, 6),
                "predicted_return_market_x_exposure": round(predicted, 6),
                "actual_mean_strategy_return": round(actual, 6),
                "actual_minus_predicted": round(actual - predicted, 6),
            }

    return {
        "full_universe": {
            "definition": "원시 가격 Parquet(raw bars, corrected-input-v4/prices, 총 1,829,295행)의 조정주가 "
            "행을 신호 발생 여부와 무관하게 전부 써서 만든 동일가중 벤치마크. signal_inputs() 를 호출하지 "
            "않으므로 신호 사후 선택에 따른 look-ahead 편향이 없다. 회귀·베타*노출 예측치는 이 벤치마크를 쓴다.",
            "annual_return": full_universe_annual,
        },
        "signal_universe_biased_reference": {
            "definition": "signals.csv 에 나타난 신호 발생 종목 코드 집합(283개)의 동일가중 수정주가 수익률. "
            "거래대금 급증으로 사후에 걸러진 하위집합이라 선택 편향(look-ahead)이 있다 — 참고용일 뿐 회귀·"
            "베타*노출 계산에는 쓰지 않는다.",
            "n_codes": len(signal_codes),
            "annual_return": signal_universe_annual,
        },
        "kospi_index_annual_return_reference": kospi_annual,
        "kosdaq_index_annual_return_reference": kosdaq_annual,
        "index_source_note": "로컬 raw JSON(KRX 공개 API 원본: "
        "data/sources/krx_open_api/{warmup-2014,source-complement-2015-2023}/raw/idx_{kospi,kosdaq}_dd_trd)"
        "에서 직접 계산. 외부 공개값을 그대로 옮긴 것이 아니다.",
        "mean_strategy_annual_return": mean_strategy_annual,
        "regression_strategy_on_full_universe": regression,
        "predicted_market_x_exposure_vs_actual": predicted_vs_actual,
    }


# ---------------------------------------------------------------------------
# Q5. 집중도
# ---------------------------------------------------------------------------


def analyze_concentration(trades: pd.DataFrame) -> dict:
    t = trades.copy()
    t["exit_year"] = t["exit_date"].dt.year
    t2020 = t[t["exit_year"] == 2020]
    total_pnl_2020 = float(t2020["pnl"].sum())

    top10 = t2020.nlargest(10, "pnl")
    top10_sum = float(top10["pnl"].sum())

    by_code = t2020.groupby("code")["pnl"].sum().sort_values(ascending=False)
    top5_codes = by_code.head(5)
    top5_sum = float(top5_codes.sum())

    remainder_sum = total_pnl_2020 - top10_sum

    t2020 = t2020.copy()
    t2020["exit_month"] = t2020["exit_date"].dt.month
    by_month = t2020.groupby("exit_month")["pnl"].sum()

    return {
        "total_pnl_2020_krw": round(total_pnl_2020, 2),
        "top10_trades_pnl_krw": round(top10_sum, 2),
        "top10_trades_share_of_total": round(top10_sum / total_pnl_2020, 6) if total_pnl_2020 else None,
        "pnl_2020_excluding_top10_krw": round(remainder_sum, 2),
        "top5_codes_pnl_krw": round(top5_sum, 2),
        "top5_codes_share_of_total": round(top5_sum / total_pnl_2020, 6) if total_pnl_2020 else None,
        "top5_codes": {str(k): round(float(v), 2) for k, v in top5_codes.items()},
        "monthly_pnl_2020_krw": {int(k): round(float(v), 2) for k, v in by_month.items()},
        "monthly_pnl_2020_share": {
            int(k): round(float(v) / total_pnl_2020, 6) if total_pnl_2020 else None
            for k, v in by_month.items()
        },
    }


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--ted-root", type=Path, default=DEFAULT_TED_ROOT)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    out_path = args.out or (Path(__file__).resolve().parent / "results.json")

    started = time.time()
    summary, equity, fills, signals, exclusions = load_inputs(args.data_dir)

    trades = build_trades(fills)

    signals_result = analyze_signals(signals, summary)
    trades_result = analyze_trades(trades)
    exposure_result = analyze_exposure(equity)
    market_result = analyze_market(args.ted_root, signals, equity, summary, exposure_result)
    concentration_result = analyze_concentration(trades)

    result = {
        "admission_status": "NOT_ADMITTED_EXPLORATORY",
        "note": "이 결과는 전략 선정이나 실거래 판단의 근거가 아니다. 원본 52개 탐색 결과와 동일한 미승인 딱지를 물려받는다.",
        "generated_at": pd.Timestamp.now().isoformat(),
        "runtime_seconds": None,  # 아래에서 채운다
        "input_sha256": input_hashes(args.data_dir),
        "signals": signals_result,
        "trades": trades_result,
        "exposure": exposure_result,
        "market": market_result,
        "concentration_2020": concentration_result,
        "exclusions_count": int(len(exclusions)),
    }
    result["runtime_seconds"] = round(time.time() - started, 1)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out_path} in {result['runtime_seconds']}s")


if __name__ == "__main__":
    main()
