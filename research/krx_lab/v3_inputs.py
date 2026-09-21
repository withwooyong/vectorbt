"""Prepare v3 market inputs without granting execution permission.

The core accepts already decoded tables so its market semantics can be tested
without a PostgreSQL export.  ``load_v3_inputs`` is the separate verified I/O
boundary for a sealed snapshot and its typed cache.  Both paths only prepare
data: callers still need the execution gate and ledger checks.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strategies import V2_ENTRY_IDS, build_signals
from .v3_tables import iter_v3_tables


_OHLC = ("open_price", "high_price", "low_price", "close_price")
_REQUIRED = {
    "PRICE": {"stock_id", "stock_code", "trading_date", "market", "adjusted", *_OHLC, "trade_volume"},
    "UNIVERSE": {"stock_id", "stock_code", "market", "security_type", "valid_from", "valid_to"},
    "CALENDAR": {"market", "trading_date", "is_open"},
    "STATUS": {"stock_id", "trading_date", "daily_state"},
    "ADJUSTMENT": {"stock_id", "trading_date", "explanation_status"},
    "ADMISSION_ISSUE": {"issue_code", "severity", "affected_scope", "affected_from", "affected_to", "decision"},
    "CORPORATE_ACTION": {"stock_id", "effective_date"},
}
_SIGNAL_BLOCK_DECISIONS = {"REJECT", "QUARANTINE"}
_NON_TRADING_STATES = {"HALTED", "NO_BAR_HALTED", "PARTIAL_TRADING", "PARTIAL_TRADE"}


@dataclass(frozen=True)
class V3Inputs:
    """Prepared data frames; this object intentionally has no admission flag."""

    prices: pd.DataFrame
    signals: pd.DataFrame
    calendar: pd.DataFrame
    issues: pd.DataFrame
    events: pd.DataFrame


def _require(tables: Mapping[str, pd.DataFrame]) -> None:
    missing = sorted(set(_REQUIRED) - set(tables))
    if missing:
        raise ValueError(f"MISSING_V3_TABLES: {missing}")
    for name, fields in _REQUIRED.items():
        absent = sorted(fields - set(tables[name].columns))
        if absent:
            raise ValueError(f"MISSING_V3_COLUMNS: {name}: {absent}")


def _day(values: pd.Series, label: str) -> pd.Series:
    try:
        result = pd.to_datetime(values, errors="raise").dt.normalize()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"INVALID_V3_DATE: {label}") from exc
    if result.isna().any():
        raise ValueError(f"INVALID_V3_DATE: {label}")
    return result


def _numeric(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def _calendar(tables: Mapping[str, pd.DataFrame], start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    value = tables["CALENDAR"].copy()
    value["trading_date"] = _day(value["trading_date"], "CALENDAR.trading_date")
    value = value.loc[(value["market"] == "KRX") & value["is_open"].map(bool)]
    days = pd.DatetimeIndex(sorted(value.loc[value["trading_date"].between(start, end), "trading_date"].unique()))
    if days.empty:
        raise ValueError("KRX_OPEN_CALENDAR_EMPTY")
    return days


def _scope_issues(tables: Mapping[str, pd.DataFrame], codes: pd.DataFrame,
                  start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    value = tables["ADMISSION_ISSUE"].copy()
    if value.empty:
        return pd.DataFrame(columns=[*value.columns, "instrument_id", "code", "mapped", "signal_blocking"])
    value["affected_from"] = _day(value["affected_from"], "ADMISSION_ISSUE.affected_from")
    value["affected_to"] = _day(value["affected_to"], "ADMISSION_ISSUE.affected_to")
    if (value["affected_to"] < value["affected_from"]).any():
        raise ValueError("REVERSED_ADMISSION_ISSUE_INTERVAL")
    code_map = codes.drop_duplicates("code").set_index("code")["instrument_id"]
    scopes = value["affected_scope"].astype(str)
    stock_codes = scopes.where(scopes.str.startswith("stock:")).str.removeprefix("stock:")
    value["code"] = stock_codes
    value["instrument_id"] = stock_codes.map(code_map)
    value["mapped"] = value["instrument_id"].notna()
    value["instrument_id"] = value["instrument_id"].astype("string")
    value["signal_blocking"] = (
        value["mapped"]
        & value["decision"].astype(str).isin(_SIGNAL_BLOCK_DECISIONS)
        & ~value["issue_code"].astype(str).isin({"WARMUP_250_BARS_SHORT", "POINT_IN_TIME_SECTOR_UNAVAILABLE"})
        & value["affected_from"].le(end)
        & value["affected_to"].ge(start)
    )
    return value.sort_values(["affected_from", "issue_code"], kind="stable").reset_index(drop=True)


def prepare_v3_inputs(tables: Mapping[str, pd.DataFrame], *, start: str = "2014-01-01",
                      end: str = "2023-12-31") -> V3Inputs:
    """Build calendar-expanded v3 input frames using only bars on or before each signal day.

    Adjusted OHLC plus raw volume make entry signals.  The returned signal
    ``close`` and ``atr14`` are converted to the raw unit on that same day by
    ``raw_close / adjusted_close``.  Missing bars and scoped critical source
    issues become invalid adjusted bars, resetting the required 250 complete
    bar warmup instead of silently carrying an indicator across uncertainty.
    """
    _require(tables)
    first, last = pd.Timestamp(start), pd.Timestamp(end)
    if (first != first.normalize() or last != last.normalize() or first > last
            or first < pd.Timestamp("2014-01-01") or last > pd.Timestamp("2023-12-31")):
        raise ValueError("INVALID_V3_WINDOW")
    # ``start`` is the evaluation boundary, never an indicator-input cutoff.
    # Keep the sealed 2014 preparation interval so the first evaluation day can
    # have a complete 250-bar history.  Callers filter the returned frames at
    # their execution boundary after signal preparation.
    history_first = pd.Timestamp("2014-01-01")
    sessions = _calendar(tables, history_first, last)

    universe = tables["UNIVERSE"].copy()
    universe["valid_from"] = _day(universe["valid_from"], "UNIVERSE.valid_from")
    universe["valid_to"] = _day(universe["valid_to"], "UNIVERSE.valid_to")
    universe = universe.loc[(universe["security_type"] == "COMMON_STOCK")
                            & universe["market"].isin(["KOSPI", "KOSDAQ"])
                            & universe["valid_from"].le(last) & universe["valid_to"].ge(history_first)].copy()
    if universe.empty:
        raise ValueError("COMMON_STOCK_UNIVERSE_EMPTY")
    universe["instrument_id"] = universe["stock_id"].astype("string")
    universe["code"] = universe["stock_code"].astype(str)
    if universe.duplicated(["instrument_id", "valid_from", "valid_to"]).any():
        raise ValueError("DUPLICATE_UNIVERSE_INTERVAL")

    # An instrument's code must identify it uniquely for issue-key mapping and
    # for the strategy implementation, which partitions by display code.
    codes = universe[["instrument_id", "code"]].drop_duplicates()
    if codes.duplicated("code").any() or codes.duplicated("instrument_id").any():
        raise ValueError("AMBIGUOUS_UNIVERSE_CODE")
    issues = _scope_issues(tables, codes, history_first, last)

    # Do not cross join every membership record with every session: v3 has
    # 31k intervals, so that temporary result is tens of millions of rows.
    pieces = []
    for row in universe[["instrument_id", "code", "market", "valid_from", "valid_to"]].itertuples(index=False):
        left, right = sessions.searchsorted(row.valid_from), sessions.searchsorted(row.valid_to, side="right")
        days = sessions[left:right]
        if len(days):
            pieces.append(pd.DataFrame({"instrument_id": row.instrument_id, "code": row.code,
                                        "market": row.market, "date": days}))
    expected = pd.concat(pieces, ignore_index=True)
    if expected.duplicated(["instrument_id", "date"]).any():
        raise ValueError("OVERLAPPING_UNIVERSE_INTERVAL")
    expected = expected.sort_values(["instrument_id", "date"], kind="stable")

    price = tables["PRICE"].copy()
    price["date"] = _day(price["trading_date"], "PRICE.trading_date")
    price["instrument_id"] = price["stock_id"].astype("string")
    price["code"] = price["stock_code"].astype(str)
    price = _numeric(price, (*_OHLC, "trade_volume"))
    price = price.loc[price["date"].between(history_first, last)]
    if price.duplicated(["instrument_id", "date", "adjusted"]).any():
        raise ValueError("DUPLICATE_PRICE_KEY")
    raw_columns = ["instrument_id", "date", *_OHLC, "trade_volume", "source_record_id", "source_code", "payload_sha256",
                   "available_at", "historical_capture"]
    raw = price.loc[~price["adjusted"].map(bool), [name for name in raw_columns if name in price.columns]].copy()
    raw = raw.rename(columns={**{name: name.removesuffix('_price') for name in _OHLC},
                              "trade_volume": "volume", "source_record_id": "raw_source_record_id",
                              "source_code": "raw_source_code", "payload_sha256": "raw_payload_sha256",
                              "available_at": "raw_available_at", "historical_capture": "raw_historical_capture"})
    adjusted_columns = ["instrument_id", "date", *_OHLC, "source_record_id", "source_code", "payload_sha256",
                        "available_at", "historical_capture"]
    adjusted = price.loc[price["adjusted"].map(bool), [name for name in adjusted_columns if name in price.columns]].copy()
    adjusted = adjusted.rename(columns={**{name: f"adjusted_{name.removesuffix('_price')}" for name in _OHLC},
                                        "source_record_id": "adjusted_source_record_id",
                                        "source_code": "adjusted_source_code",
                                        "payload_sha256": "adjusted_payload_sha256",
                                        "available_at": "adjusted_available_at",
                                        "historical_capture": "adjusted_historical_capture"})
    result = expected.merge(raw, on=["instrument_id", "date"], how="left", validate="one_to_one")
    result = result.merge(adjusted, on=["instrument_id", "date"], how="left", validate="one_to_one")

    status = tables["STATUS"].copy()
    status["date"] = _day(status["trading_date"], "STATUS.trading_date")
    status["instrument_id"] = status["stock_id"].astype("string")
    if status.duplicated(["instrument_id", "date"]).any():
        raise ValueError("DUPLICATE_STATUS_KEY")
    result = result.merge(status[["instrument_id", "date", "daily_state"]], on=["instrument_id", "date"], how="left")

    blocking = issues.loc[issues["signal_blocking"], ["instrument_id", "affected_from", "affected_to"]]
    result["issue_blocked"] = False
    # Issue rows are few; interval assignment avoids a giant date/instrument key map.
    for issue in blocking.itertuples(index=False):
        result.loc[(result["instrument_id"] == issue.instrument_id)
                   & result["date"].between(issue.affected_from, issue.affected_to), "issue_blocked"] = True

    raw_ohlc = ["open", "high", "low", "close"]
    adjusted_ohlc = ["adjusted_open", "adjusted_high", "adjusted_low", "adjusted_close"]
    raw_valid = result[raw_ohlc].notna().all(axis=1) & result[raw_ohlc].gt(0).all(axis=1)
    raw_valid &= (result["high"] >= result[["open", "close"]].max(axis=1))
    raw_valid &= (result["low"] <= result[["open", "close"]].min(axis=1))
    adjusted_valid = result[adjusted_ohlc].notna().all(axis=1) & result[adjusted_ohlc].gt(0).all(axis=1)
    adjusted_valid &= (result["adjusted_high"] >= result[["adjusted_open", "adjusted_close"]].max(axis=1))
    adjusted_valid &= (result["adjusted_low"] <= result[["adjusted_open", "adjusted_close"]].min(axis=1))
    # v3 STATUS stores exception dates only.  A valid positive-volume raw bar
    # therefore supplies the observed TRADING state when no explicit status is
    # present; engine eligibility must not reject every ordinary session.
    result["status"] = result.pop("daily_state")
    result.loc[result["status"].isna() & raw_valid & result["volume"].gt(0), "status"] = "TRADING"
    result.loc[result["status"].isna() & raw_valid & result["volume"].eq(0), "status"] = "NON_TRADING_OBSERVED"
    result["status"] = result["status"].fillna("UNKNOWN").astype(str)
    partial_status = result["status"].str.contains("PARTIAL", case=False, na=False)
    result["eligible"] = (raw_valid & result["volume"].gt(0) & result["status"].eq("TRADING")
                          & ~result["status"].isin(_NON_TRADING_STATES) & ~partial_status
                          & ~result["issue_blocked"])
    result["adjusted_valid"] = adjusted_valid & ~result["issue_blocked"]
    result["input_blocked"] = ~result["eligible"]
    reasons = np.full(len(result), "", dtype=object)
    reasons[~raw_valid.to_numpy()] = "RAW_OHLC_INVALID_OR_MISSING"
    volume_unknown = result["volume"].isna().to_numpy()
    known_zero = result["volume"].eq(0).to_numpy()
    reasons[volume_unknown] = np.where(reasons[volume_unknown] == "", "VOLUME_UNKNOWN",
                                       reasons[volume_unknown] + ";VOLUME_UNKNOWN")
    reasons[known_zero] = np.where(reasons[known_zero] == "", "NO_TRADE_KNOWN_ZERO",
                                   reasons[known_zero] + ";NO_TRADE_KNOWN_ZERO")
    non_trading = result["status"].isin(_NON_TRADING_STATES).to_numpy()
    reasons[non_trading] = np.where(reasons[non_trading] == "", "STATUS_NOT_TRADING",
                                    reasons[non_trading] + ";STATUS_NOT_TRADING")
    blocked = result["issue_blocked"].to_numpy()
    reasons[blocked] = np.where(reasons[blocked] == "", "ADMISSION_ISSUE_BLOCKED",
                                reasons[blocked] + ";ADMISSION_ISSUE_BLOCKED")
    result["input_block_reasons"] = pd.Series(reasons, index=result.index).mask(lambda value: value == "")

    signal_prices = result[["date", "instrument_id", "code", *adjusted_ohlc, "volume", "adjusted_valid"]].copy()
    signal_prices = signal_prices.rename(columns={"adjusted_open": "open", "adjusted_high": "high",
                                                   "adjusted_low": "low", "adjusted_close": "close"})
    signal_prices.loc[~signal_prices.pop("adjusted_valid"), ["open", "high", "low", "close", "volume"]] = np.nan
    # Internal identity prevents a display-code reuse from joining histories.
    signal_prices["code"] = signal_prices["instrument_id"]
    signals = build_signals(signal_prices, entry_ids=V2_ENTRY_IDS)
    signals["display_code"] = result["code"].to_numpy()
    signals["instrument_id"] = result["instrument_id"].to_numpy()
    factor = result["close"] / result["adjusted_close"]
    # Preserve the raw close byte-for-value for the executor's strict signal
    # basis comparison.  Multiplying adjusted_close by its factor can drift.
    signals["close"] = result["close"].to_numpy()
    signals["atr14"] = signals["atr14"] * factor.to_numpy()
    signals["eligible"] = result["eligible"].to_numpy()
    signals["market"] = result["market"].to_numpy()
    signals["status"] = result["status"].to_numpy()
    signals["issue_blocked"] = result["issue_blocked"].to_numpy()
    signals["input_blocked"] = result["input_blocked"].to_numpy()
    signals["input_block_reasons"] = result["input_block_reasons"].to_numpy()
    signals["source_kind"] = "REAL_V3_PREPARED_NOT_EXECUTABLE"

    prices = result.drop(columns=["adjusted_valid"]).rename(columns={"code": "display_code"})
    prices["code"] = prices["instrument_id"]
    calendar = pd.DataFrame({"date": sessions, "market": "KRX"})
    events = tables["CORPORATE_ACTION"].copy()
    events["effective_date"] = _day(events["effective_date"], "CORPORATE_ACTION.effective_date")
    events["instrument_id"] = events["stock_id"].astype("string")
    events = events.loc[events["effective_date"].between(history_first, last)].copy()
    return V3Inputs(prices=prices.reset_index(drop=True), signals=signals.reset_index(drop=True),
                    calendar=calendar, issues=issues, events=events.reset_index(drop=True))


def load_v3_inputs(source, typed_tables, *, start: str = "2014-01-01", end: str = "2023-12-31") -> V3Inputs:
    """Load only required typed parts with source bindings and prepare v3 inputs.

    ``iter_v3_tables`` validates the typed-cache manifest binding and every part
    it reads.  It rejects an incomplete source snapshot through that binding.
    """
    tables = {}
    price_columns = ["stock_id", "stock_code", "trading_date", "market", "adjusted", *_OHLC,
                     "trade_volume", "source_code"]
    for kind in _REQUIRED:
        # PRICE is roughly ten million rows.  The sealed source/typed manifest
        # binds its full provenance; preparation needs only these execution and
        # source-pair fields, avoiding duplicate payload/timestamp columns.
        columns = price_columns if kind == "PRICE" else None
        frames = list(iter_v3_tables(source, typed_tables, kind, columns=columns))
        tables[kind] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return prepare_v3_inputs(tables, start=start, end=end)
