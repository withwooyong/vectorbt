"""Backtest result metrics with JSON-safe outputs."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

import numpy as np
import pandas as pd


def _finite(value: Any) -> Any:
    """Convert pandas/numpy values into finite, JSON-serializable values."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, Mapping):
        return {str(key): _finite(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, np.ndarray, pd.Series)):
        return [_finite(item) for item in list(value)]
    if isinstance(value, (pd.Timestamp, np.datetime64, datetime, date)):
        timestamp = pd.Timestamp(value)
        return None if pd.isna(timestamp) else timestamp.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def _frame(result: dict[str, Any], name: str, columns: list[str]) -> pd.DataFrame:
    value = result.get(name)
    if value is None:
        return pd.DataFrame(columns=columns)
    frame = value.copy() if isinstance(value, pd.DataFrame) else pd.DataFrame(value)
    for column in columns:
        if column not in frame:
            frame[column] = pd.Series(dtype="object")
    return frame


def _equity_frame(result: dict[str, Any]) -> pd.DataFrame:
    frame = _frame(result, "equity", ["date", "cash", "equity", "exposure", "positions_count"])
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame["equity"] = pd.to_numeric(frame["equity"], errors="coerce")
    invalid = frame["date"].isna() | frame["equity"].isna() | ~np.isfinite(frame["equity"])
    if invalid.any():
        raise ValueError(f"INVALID_EQUITY_LEDGER: {int(invalid.sum())}개 날짜/자산 행이 유효하지 않습니다")
    return frame.sort_values("date", kind="stable").reset_index(drop=True)


def monthly_stats(result: dict[str, Any], initial_cash: float = 100_000_000) -> pd.DataFrame:
    """Return one row per calendar month from daily account equity.

    Each month starts at the preceding month's last equity (or ``initial_cash``
    for the first observed month), so monthly P&L is not distorted by grouping.
    """
    equity = _equity_frame(result)
    columns = ["month", "start_equity", "end_equity", "pnl", "return", "is_loss"]
    if equity.empty:
        return pd.DataFrame(columns=columns)

    month_end = equity.set_index("date")["equity"].resample("ME").last().dropna()
    starts = month_end.shift(1)
    starts.iloc[0] = float(initial_cash)
    monthly = pd.DataFrame(
        {
            "month": month_end.index.to_period("M").astype(str),
            "start_equity": starts.to_numpy(dtype=float),
            "end_equity": month_end.to_numpy(dtype=float),
        }
    )
    monthly["pnl"] = monthly["end_equity"] - monthly["start_equity"]
    monthly["return"] = np.where(
        monthly["start_equity"] != 0,
        monthly["pnl"] / monthly["start_equity"],
        np.nan,
    )
    monthly["is_loss"] = monthly["pnl"] < 0
    return monthly[columns]


def ledger_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Summarize the latest C2 account state without changing its ledger.

    Fees and taxes are deliberately read from cashflows when they are present.
    A fill can also be represented by a cashflow, so adding both would report
    the same charge twice.
    """
    ledger = result.get("contract_ledger") if isinstance(result.get("contract_ledger"), Mapping) else result
    equity = _frame(ledger, "equity", ["date", "cash", "receivables", "payables", "exposure", "equity"])
    positions = _frame(ledger, "positions", ["date", "instrument_id", "quantity", "mark_price", "stale", "overdue"])
    cashflows = _frame(ledger, "cashflows", ["fee", "tax"])
    fills = _frame(ledger, "fills", ["fee", "fees", "tax"])

    latest: dict[str, Any] = {"date": None, "cash": None, "receivables": None, "payables": None,
                              "exposure": None, "equity": None}
    if not equity.empty:
        equity["date"] = pd.to_datetime(equity["date"], errors="coerce")
        equity = equity.sort_values("date", kind="stable")
        row = equity.iloc[-1]
        latest = {name: row.get(name) for name in latest}

    if "size" in positions:
        positions["quantity"] = positions["quantity"].fillna(positions["size"])
    latest_positions = positions.iloc[0:0]
    if not positions.empty and "date" in positions:
        dates = pd.to_datetime(positions["date"], errors="coerce")
        if latest["date"] is not None:
            latest_positions = positions.loc[dates.eq(pd.Timestamp(latest["date"]))]
    stale_values = latest_positions.get("stale", pd.Series(dtype=bool)).fillna(False)
    overdue_values = latest_positions.get("overdue", pd.Series(dtype=bool)).fillna(False)
    stale = int(stale_values.map(lambda value: value is True or value == 1).sum())
    overdue = int(overdue_values.map(lambda value: value is True or value == 1).sum())
    open_positions = int((pd.to_numeric(latest_positions.get("quantity", pd.Series(dtype=float)), errors="coerce").fillna(0) > 0).sum())

    if not cashflows.empty:
        fee = pd.to_numeric(cashflows["fee"], errors="coerce").fillna(0.0).sum()
        tax = pd.to_numeric(cashflows["tax"], errors="coerce").fillna(0.0).sum()
        cost_source = "cashflows"
    else:
        fee_column = "fee" if "fee" in fills and fills["fee"].notna().any() else "fees"
        fee = pd.to_numeric(fills.get(fee_column, pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
        tax = pd.to_numeric(fills.get("tax", pd.Series(dtype=float)), errors="coerce").fillna(0.0).sum()
        cost_source = "fills"
    latest.update(open_positions=open_positions, stale_positions=stale, overdue_positions=overdue,
                  total_fees=float(fee), total_taxes=float(tax), cost_source=cost_source)
    return _finite(latest)


def calculate_metrics(result: dict[str, Any], initial_cash: float = 100_000_000) -> dict[str, Any]:
    """Calculate comparable account metrics without emitting NaN or infinity."""
    equity = _equity_frame(result)
    trades = _frame(result, "trades", ["code", "pnl", "entry_date", "exit_date"])
    fills = _frame(result, "fills", ["date", "code", "side", "size", "price", "fees", "phase"])
    issues = _finite(result.get("issues", []))
    if not isinstance(issues, list):
        issues = [issues]

    start_equity = float(initial_cash)
    end_equity: float | None = None
    total_return: float | None = None
    cagr: float | None = None
    max_drawdown: float | None = None
    sharpe: float | None = None
    average_exposure: float | None = None
    average_cash_ratio: float | None = None
    max_positions = 0
    annual_turnover: float | None = None

    if not equity.empty:
        values = equity["equity"].astype(float)
        end_equity = float(values.iloc[-1])
        if start_equity > 0:
            total_return = end_equity / start_equity - 1.0
        days = max((equity["date"].iloc[-1] - equity["date"].iloc[0]).days + 1, 1)
        if days > 0 and start_equity > 0 and end_equity > 0:
            cagr = (end_equity / start_equity) ** (365.25 / days) - 1.0
        running_peak = values.cummax().clip(lower=start_equity)
        drawdown = values / running_peak - 1.0
        if len(drawdown):
            max_drawdown = float(-drawdown.min())
        anchored = pd.concat([pd.Series([start_equity]), values.reset_index(drop=True)], ignore_index=True)
        returns = anchored.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        if len(returns) >= 2 and float(returns.std(ddof=1)) > 0:
            sharpe = float(np.sqrt(252.0) * returns.mean() / returns.std(ddof=1))
        if "exposure" in equity:
            exposure = pd.to_numeric(equity["exposure"], errors="coerce").dropna()
            if not exposure.empty:
                average_exposure = float(exposure.mean())
        if "cash" in equity:
            cash = pd.to_numeric(equity["cash"], errors="coerce")
            valid = values.ne(0) & cash.notna()
            if valid.any():
                average_cash_ratio = float((cash[valid] / values[valid]).mean())
        if "positions_count" in equity:
            counts = pd.to_numeric(equity["positions_count"], errors="coerce").dropna()
            if not counts.empty:
                max_positions = int(counts.max())

    pnl = pd.to_numeric(trades["pnl"], errors="coerce") if not trades.empty else pd.Series(dtype=float)
    completed = pnl.notna()
    trade_count = int(completed.sum())
    wins = int((pnl[completed] > 0).sum())
    win_rate = wins / trade_count if trade_count else None
    gross_profit = float(pnl[pnl > 0].sum()) if trade_count else 0.0
    gross_loss = float(pnl[pnl < 0].sum()) if trade_count else 0.0
    net_pnl = float(pnl[completed].sum()) if trade_count else 0.0

    positive_by_code: dict[str, float] = {}
    if trade_count and "code" in trades:
        positive_rows = trades.loc[pnl > 0, ["code"]].copy()
        positive_rows["pnl"] = pnl[pnl > 0]
        grouped = positive_rows.groupby(positive_rows["code"].astype(str), sort=True)["pnl"].sum()
        positive_by_code = {str(code): float(value) for code, value in grouped.items()}
    concentration = max(positive_by_code.values()) / gross_profit if gross_profit > 0 else None

    total_fees = 0.0
    traded_notional = 0.0
    if not fills.empty:
        fees = pd.to_numeric(fills["fees"], errors="coerce").fillna(0.0)
        sizes = pd.to_numeric(fills["size"], errors="coerce").fillna(0.0)
        prices = pd.to_numeric(fills["price"], errors="coerce").fillna(0.0)
        total_fees = float(fees.sum())
        traded_notional = float((sizes.abs() * prices.abs()).sum())
    if not equity.empty and float(equity["equity"].mean()) > 0:
        annual_turnover = traded_notional / float(equity["equity"].mean()) * (365.25 / days)

    months = monthly_stats(result, initial_cash)
    metrics = {
        "initial_cash": start_equity,
        "ending_equity": end_equity,
        "total_return": total_return,
        "cagr": cagr,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown,
        "trade_count": trade_count,
        "win_rate": win_rate,
        "gross_profit": gross_profit,
        "gross_loss": gross_loss,
        "net_pnl": net_pnl,
        "total_fees": total_fees,
        "traded_notional": traded_notional,
        "annual_turnover": annual_turnover,
        "average_exposure": average_exposure,
        "average_cash_ratio": average_cash_ratio,
        "max_positions": max_positions,
        "positive_profit_concentration": concentration,
        "positive_pnl_by_code": positive_by_code,
        "loss_months": int(months["is_loss"].sum()) if not months.empty else 0,
        "open_positions": int(equity["positions_count"].iloc[-1]) if not equity.empty else 0,
        "issue_count": len(issues),
        "issues": issues,
    }
    return _finite(metrics)
