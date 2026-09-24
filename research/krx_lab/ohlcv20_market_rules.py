"""Attach sealed daily market rules and separate blocked configurations pre-run.

The execution engine refuses a whole run when one loaded bar lacks a verified
listing, sell or lower-limit status. Which bars a configuration may consult is
bounded without trading: a signal-eligible bar on T can lead to an order on the
next session B, an expiry E at the first session on or after B plus the holding
months, and a carry-over of margin sessions after E. Every bar inside that
bound must load, or the configuration is blocked before it runs; it is never
converted to a zero return.
"""

from __future__ import annotations

from bisect import bisect_left
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .ohlcv20_real_execution import _admit_bar
from .ohlcv20_rights import RightsProgram


# Carry-over adopted by execution-touch-set-v1 (p99 of non-execution runs).
MARGIN_SESSIONS = 252
MISSING_RULE = "MARKET_RULE_ROW_MISSING"
_RULE_COLUMNS = {
    "stock_code",
    "trading_date",
    "listing_status",
    "listing_status_verified",
    "sell_status",
    "sell_status_verified",
    "lower_limit_price",
    "lower_limit_price_verified",
}
ENGINE_COLUMNS = [
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
    "lower_limit_price",
    "lower_limit_price_verified",
    "rights_suspension_verified",
]


def attach_market_rules(
    bars: pd.DataFrame, rules: pd.DataFrame, program: RightsProgram | None = None
) -> pd.DataFrame:
    """Join rules by (date, code); a bar without a rule row keeps nulls.

    A ledger event's no-trade span, confirmed by settlement v5, is the only
    source of rights_suspension_verified, and only on non-sellable bars.
    """
    if not _RULE_COLUMNS <= set(rules.columns):
        raise ValueError("INVALID_MARKET_RULES_SCHEMA")
    rules = rules.rename(columns={"stock_code": "code", "trading_date": "date"})
    rules = rules.assign(code=rules.code.astype(str), date=pd.to_datetime(rules.date))
    if rules.duplicated(["date", "code"]).any():
        raise ValueError("DUPLICATE_MARKET_RULE_KEY")
    columns = [name for name in bars.columns if name not in _RULE_COLUMNS]
    frame = bars[columns].merge(
        rules[["date", "code", *sorted(_RULE_COLUMNS - {"stock_code", "trading_date"})]],
        on=["date", "code"],
        how="left",
        validate="one_to_one",
        indicator="_rule",
    )
    frame["market_rule_present"] = frame.pop("_rule").eq("both")
    suspended = pd.Series(False, index=frame.index)
    for item in program.ledger_schedule if program is not None else ():
        suspended |= (
            frame.code.eq(item.event_code)
            & frame.date.ge(pd.Timestamp(item.suspended_from))
            & frame.date.lt(pd.Timestamp(item.available_on))
        )
    frame["rights_suspension_verified"] = (suspended & frame.can_sell.eq(False)).astype(bool)
    return frame


def admission_failures(frame: pd.DataFrame) -> pd.Series:
    """Reason the engine would refuse each bar; None where it loads."""
    reasons = []
    for present, row in zip(
        frame.market_rule_present, frame[ENGINE_COLUMNS].to_dict("records")
    ):
        if not present:
            reasons.append(MISSING_RULE)
            continue
        try:
            _admit_bar(row, "REAL")
        except ValueError as exc:
            reasons.append(str(exc))
        else:
            reasons.append(None)
    return pd.Series(reasons, index=frame.index, dtype=object)


def reachable_bars(
    frame: pd.DataFrame,
    calendar,
    holding_months: int,
    *,
    program: RightsProgram | None = None,
    margin: int = MARGIN_SESSIONS,
    entry_feasible_only: bool = False,
) -> np.ndarray:
    """Mark bars inside (T, E + margin] of any signal-eligible bar of the code.

    Successor legs of a ledger event whose old code is reachable on the
    conversion session are reachable for margin sessions from that session.
    With entry_feasible_only a holding window opens only when the order bar
    B is order-eligible and buyable; otherwise only B itself is consulted.
    """
    days = pd.DatetimeIndex(sorted(pd.to_datetime(calendar)))
    codes, code_ids = np.unique(frame.code.to_numpy(dtype=str), return_inverse=True)
    rows = days.get_indexer(frame.date)
    if (rows < 0).any():
        raise ValueError("OFF_CALENDAR_BAR")
    starts = frame.signal_eligible.eq(True).to_numpy()
    start_ids, start_rows = code_ids[starts], rows[starts]
    ordered = start_rows + 1 < len(days)
    start_ids, start_rows = start_ids[ordered], start_rows[ordered]
    anniversary = days[start_rows + 1] + pd.DateOffset(months=holding_months)
    ends = np.minimum(days.searchsorted(anniversary, side="left") + margin, len(days) - 1)
    if entry_feasible_only:
        buyable = np.zeros((len(codes), len(days)), dtype=bool)
        enterable = (frame.order_eligible.eq(True) & frame.can_buy.eq(True)).to_numpy()
        buyable[code_ids[enterable], rows[enterable]] = True
        ends = np.where(buyable[start_ids, start_rows + 1], ends, start_rows + 1)
    cover = np.zeros((len(codes), len(days) + 1), dtype=np.int32)
    np.add.at(cover, (start_ids, start_rows + 1), 1)
    np.add.at(cover, (start_ids, ends + 1), -1)
    covered = np.cumsum(cover, axis=1)[:, : len(days)] > 0
    position = {code: index for index, code in enumerate(codes)}
    extra = np.zeros_like(covered)
    for item in program.ledger_schedule if program is not None else ():
        start = days.searchsorted(pd.Timestamp(item.available_on))
        old = position.get(item.event_code)
        if old is None or start >= len(days) or not covered[old, start]:
            continue
        for leg in program.ledger_events[item.event_code].legs:
            if leg.code in position:
                extra[position[leg.code], start : start + margin + 1] = True
    return (covered | extra)[code_ids, rows]


def load_touch_set(path: Path, expected_sha256: str) -> frozenset[str]:
    """Reached event keys of execution-touch-set-v1, bound by the receipt."""
    data = path.read_bytes()
    if not expected_sha256 or sha256(data).hexdigest() != expected_sha256:
        raise ValueError("TOUCH_SET_HASH_MISMATCH")
    record = json.loads(data)
    ids = record["classification"]["reached_event_ids_sorted"]
    payload = "\n".join(sorted(ids)).encode("utf-8")
    if (
        record.get("schema") != "ohlcv20-execution-touch-set-v1"
        or len(set(ids)) != len(ids)
        or sha256(payload).hexdigest()
        != record["classification"]["reached_event_ids_sha256"]
    ):
        raise ValueError("TOUCH_SET_EVENT_IDS_MISMATCH")
    return frozenset(ids)


def out_of_touch_set_events(
    corporate_actions: pd.DataFrame, touch_set: frozenset[str], calendar
) -> dict[tuple[pd.Timestamp, str], list[str]]:
    """Key each event outside the touch set by the session it first binds."""
    days = sorted(pd.to_datetime(calendar))
    result: dict[tuple[pd.Timestamp, str], list[str]] = {}
    for row in corporate_actions[["event_id", "stock_code", "effective_date"]].itertuples(
        index=False
    ):
        if row.event_id in touch_set:
            continue
        index = bisect_left(days, pd.Timestamp(row.effective_date))
        if index < len(days):
            result.setdefault((days[index], str(row.stock_code)), []).append(
                str(row.event_id)
            )
    return result


def separate_configurations(
    frame: pd.DataFrame,
    failures: pd.Series,
    calendar,
    *,
    program: RightsProgram | None = None,
    holding_months_values=(1, 3),
    margin: int = MARGIN_SESSIONS,
    entry_feasible_only: bool = False,
) -> dict[int, dict]:
    """Per holding horizon, count reachable bars the engine would refuse.

    A missing rule row and a present row the engine refuses are counted apart;
    neither is filled with a default status.
    """
    result = {}
    for months in holding_months_values:
        reach = reachable_bars(
            frame,
            calendar,
            months,
            program=program,
            margin=margin,
            entry_feasible_only=entry_feasible_only,
        )
        refused = failures[reach].dropna()
        missing = refused.eq(MISSING_RULE)
        reasons = []
        if missing.any():
            reasons.append("MARKET_RULE_ROW_MISSING_IN_REACH")
        if (~missing).any():
            reasons.append("UNVERIFIED_MARKET_RULE_ROW_IN_REACH")
        result[months] = dict(
            reachable_bars=int(reach.sum()),
            refused_bars=len(refused),
            refused_codes=int(frame.loc[refused.index, "code"].nunique()),
            missing_rule_bars=int(missing.sum()),
            missing_rule_codes=int(frame.loc[refused.index[missing], "code"].nunique()),
            refused_rule_bars=int((~missing).sum()),
            refused_rule_codes=int(frame.loc[refused.index[~missing], "code"].nunique()),
            refused_by_reason={
                str(key): int(value) for key, value in refused.value_counts().items()
            },
            reason_codes=reasons,
        )
    return result
