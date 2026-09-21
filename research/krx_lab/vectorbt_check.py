"""실행 장부를 vectorbt 주문 엔진으로 독립 재생하는 연구용 검산기."""
from __future__ import annotations

import numpy as np
import pandas as pd
import vectorbt as vbt


FILL_COLUMNS = ("date", "code", "side", "size", "price", "fees", "phase")
EQUITY_COLUMNS = ("date", "cash", "equity", "exposure", "positions_count")


def reconcile(result: dict, initial_cash: float = 100_000_000) -> dict:
    """Replay fills using shared cash and return independent order/EOD comparisons.

    ``fees`` are absolute currency fees and ``fill_seq`` is the mandatory,
    chronological replay order.
    Positions must be EOD rows with ``size`` (or ``qty``) and ``mark_price``.
    Contract errors raise ``ValueError``; a ledger disagreement returns ``ok=False``.
    """
    if not np.isfinite(initial_cash) or initial_cash <= 0:
        raise ValueError("initial_cash must be a positive finite number")
    fills = _frame(result, "fills", FILL_COLUMNS)
    equity = _frame(result, "equity", EQUITY_COLUMNS)
    positions = _frame(result, "positions", ("date", "code", "mark_price"))
    quantity_column = "size" if "size" in positions.columns else "qty" if "qty" in positions.columns else None
    if quantity_column is None and not positions.empty:
        raise ValueError("positions requires size or qty")
    if equity.empty:
        if not fills.empty or not positions.empty:
            raise ValueError("fills/positions require EOD equity rows")
        return {"ok": True, "engine": "numba", "order_source": "none", "mismatches": []}

    fills = _normalise_fills(fills)
    equity = _normalise_equity(equity)
    positions = _normalise_positions(positions, quantity_column)
    eod_dates = set(equity["date"])
    if not set(fills["date"]).issubset(eod_dates) or not set(positions["date"]).issubset(eod_dates):
        raise ValueError("fills and positions dates must have matching EOD equity rows")
    codes = sorted(set(fills.code) | set(positions.code))
    if not codes and (equity.positions_count != 0).any():
        raise ValueError("positive positions_count requires EOD position rows")
    replay_codes = codes or ["__ZERO_TRADE_CASH__"]
    matrices, eod_rows, fill_rows = _build_matrices(fills, equity, positions, replay_codes)
    portfolio = vbt.Portfolio.from_orders(
        matrices["close"],
        size=matrices["size"],
        price=matrices["price"],
        fixed_fees=matrices["fees"],
        init_cash=float(initial_cash),
        cash_sharing=True,
        group_by=True,
        engine="numba",
        freq="1D",
    )
    mismatches = []
    if (equity["cash"] < -1e-6).any():
        mismatches.append("negative_cash_longonly_contract")
    mismatches.extend(_compare(portfolio, fills, equity, positions, replay_codes, eod_rows, fill_rows))
    return {
        "ok": not mismatches,
        "engine": "numba",
        "order_source": "fill_seq",
        "mismatches": mismatches,
        "orders_checked": len(fills),
        "eod_checked": len(equity),
    }


def _frame(result: dict, key: str, columns: tuple[str, ...]) -> pd.DataFrame:
    if key not in result or not isinstance(result[key], pd.DataFrame):
        raise ValueError(f"result[{key!r}] must be a DataFrame")
    frame = result[key].copy()
    missing = set(columns).difference(frame.columns)
    if missing:
        raise ValueError(f"{key} missing columns: {sorted(missing)}")
    return frame


def _normalise_fills(fills: pd.DataFrame) -> pd.DataFrame:
    fills["date"] = pd.to_datetime(fills.date, errors="raise").dt.normalize()
    for column in ("size", "price", "fees"):
        fills[column] = pd.to_numeric(fills[column], errors="raise")
    numeric_fills = fills[["size", "price", "fees"]]
    if numeric_fills.isna().any().any() or not np.isfinite(numeric_fills.to_numpy()).all():
        raise ValueError("fills must be finite")
    if (fills["size"] <= 0).any() or (fills["price"] <= 0).any() or (fills["fees"] < 0).any():
        raise ValueError("fills require positive size/price and nonnegative fees")
    if not np.equal(fills["size"], np.floor(fills["size"])).all():
        raise ValueError("fills size must be a positive integer")
    if not fills["side"].isin(["buy", "sell"]).all() or fills["code"].isna().any():
        raise ValueError("fills require buy/sell side and code")
    if "fill_seq" not in fills:
        raise ValueError("fills requires fill_seq")
    fills["_seq"] = pd.to_numeric(fills.fill_seq, errors="raise")
    valid_seq = (
        np.isfinite(fills["_seq"]).all()
        and (fills["_seq"] >= 0).all()
        and np.equal(fills["_seq"], np.floor(fills["_seq"])).all()
    )
    if not valid_seq or fills["_seq"].duplicated().any():
        raise ValueError("fill_seq must be unique, finite, nonnegative integers")
    fills = fills.sort_values("_seq", kind="stable").reset_index(drop=True)
    if not fills["date"].is_monotonic_increasing:
        raise ValueError("fill_seq must be chronological by date")
    return fills


def _normalise_equity(equity: pd.DataFrame) -> pd.DataFrame:
    equity["date"] = pd.to_datetime(equity.date, errors="raise").dt.normalize()
    if equity.date.duplicated().any():
        raise ValueError("equity requires one EOD row per date")
    for column in EQUITY_COLUMNS[1:]:
        equity[column] = pd.to_numeric(equity[column], errors="raise")
    if not np.isfinite(equity[list(EQUITY_COLUMNS[1:])].to_numpy()).all() or (equity.positions_count < 0).any():
        raise ValueError("equity values must be finite and positions_count nonnegative")
    return equity.sort_values("date", kind="stable").reset_index(drop=True)


def _normalise_positions(positions: pd.DataFrame, quantity_column: str | None) -> pd.DataFrame:
    if positions.empty:
        return positions.assign(_qty=pd.Series(dtype=float))
    positions["date"] = pd.to_datetime(positions.date, errors="raise").dt.normalize()
    if positions.duplicated(["date", "code"]).any():
        raise ValueError("positions requires one EOD row per date/code")
    positions["_qty"] = pd.to_numeric(positions[quantity_column], errors="raise")
    positions["mark_price"] = pd.to_numeric(positions.mark_price, errors="raise")
    valid_position_values = np.isfinite(positions[["_qty", "mark_price"]].to_numpy()).all()
    if not valid_position_values or (positions["_qty"] <= 0).any() or (positions["mark_price"] <= 0).any():
        raise ValueError("positions require positive finite qty and mark_price")
    return positions.sort_values(["date", "code"], kind="stable").reset_index(drop=True)


def _build_matrices(fills: pd.DataFrame, equity: pd.DataFrame, positions: pd.DataFrame, codes: list[str]):
    position_by_date = {day: frame.set_index("code") for day, frame in positions.groupby("date", sort=False)}
    fills_by_date = {day: frame for day, frame in fills.groupby("date", sort=False)}
    marks = {code: 1.0 for code in codes}
    rows, sizes, prices, fees, index, fill_rows, eod_rows = [], [], [], [], [], [], []
    for day in equity.date:
        positions_today = position_by_date.get(day, pd.DataFrame())
        if not positions_today.empty:
            marks.update(positions_today.mark_price.to_dict())
        for fill_index, fill in fills_by_date.get(day, pd.DataFrame()).iterrows():
            index.append((day, f"fill_{int(fill._seq):09d}"))
            rows.append([marks[code] for code in codes])
            size_row, price_row, fee_row = [np.nan] * len(codes), [np.nan] * len(codes), [np.nan] * len(codes)
            column = codes.index(fill["code"])
            size_row[column] = float(fill["size"] if fill["side"] == "buy" else -fill["size"])
            price_row[column], fee_row[column] = float(fill["price"]), float(fill["fees"])
            sizes.append(size_row)
            prices.append(price_row)
            fees.append(fee_row)
            fill_rows.append(len(index) - 1)
        index.append((day, "eod"))
        rows.append([marks[code] for code in codes])
        sizes.append([np.nan] * len(codes))
        prices.append([np.nan] * len(codes))
        fees.append([np.nan] * len(codes))
        eod_rows.append(len(index) - 1)
    multi_index = pd.MultiIndex.from_tuples(index, names=["date", "event"])
    def build(values):
        return pd.DataFrame(values, index=multi_index, columns=codes, dtype=float)
    matrices = {"close": build(rows), "size": build(sizes), "price": build(prices), "fees": build(fees)}
    return matrices, eod_rows, fill_rows


def _compare(portfolio, fills, equity, positions, codes, eod_rows, fill_rows) -> list[str]:
    mismatches: list[str] = []
    records = portfolio.orders.records.reset_index(drop=True)
    if len(records) != len(fills):
        mismatches.append(f"order_count:{len(records)}!={len(fills)}")
    for number, (_, fill) in enumerate(fills.iterrows()):
        if number >= len(records):
            break
        record = records.iloc[number]
        expected_side = 0 if fill["side"] == "buy" else 1
        expected_column = codes.index(fill["code"])
        if record.idx != fill_rows[number] or record.col != expected_column or record.side != expected_side:
            mismatches.append(f"order_identity:{number}")
        if not np.allclose(
            [record["size"], record.price, record.fees],
            [fill["size"], fill["price"], fill["fees"]],
            rtol=1e-10,
            atol=1e-6,
        ):
            mismatches.append(f"order_amount:{number}")
    cash = np.asarray(portfolio.cash())
    value = np.asarray(portfolio.value())
    assets = portfolio.assets().to_numpy()
    asset_value = np.asarray(portfolio.asset_value())
    for number, (_, expected) in enumerate(equity.iterrows()):
        idx = eod_rows[number]
        if not np.allclose(
            [cash[idx], value[idx], asset_value[idx]],
            [expected.cash, expected.equity, expected.exposure],
            rtol=1e-10,
            atol=1e-5,
        ):
            mismatches.append(f"eod_value:{expected.date.date()}")
        actual_qty = assets[idx]
        expected_positions = positions[positions.date == expected.date].set_index("code")
        expected_qty = np.array([expected_positions._qty.get(code, 0.0) for code in codes])
        if not np.allclose(actual_qty, expected_qty, rtol=0, atol=1e-12):
            mismatches.append(f"eod_qty:{expected.date.date()}")
        if len(expected_positions) != int(expected.positions_count):
            mismatches.append(f"positions_count_contract:{expected.date.date()}")
    return mismatches


def reconcile_ledger(ledger: dict) -> dict:
    """Independently replay the C2 cash/quantity transitions and EOD balances.

    This arithmetic check complements source-event/hand-calculated engine tests.
    It does not claim vectorbt supports corporate actions or certify market data.
    """
    from .contracts import validate_ledger
    checked = validate_ledger(ledger)
    quantities = {}
    bases = {}
    cash = float(checked["initial_cash"])
    receivables = payables = 0.0
    mismatches = []
    fills = checked["fills"]
    events = checked["events"]
    cashflows = checked["cashflows"]
    orders = {row["order_id"]: row for row in checked["orders"]}
    filled = {}
    for fill in fills:
        order = orders[fill["order_id"]]
        filled[fill["order_id"]] = filled.get(fill["order_id"], 0) + fill["quantity"]
        if (order["instrument_id"] != fill["instrument_id"] or order["side"] != fill["side"]
                or order["date"] > fill["date"]):
            mismatches.append(f"order_fill_link:{fill['fill_id']}")
    for order_id, order in orders.items():
        quantity = filled.get(order_id, 0)
        if (quantity > order["quantity"] or (order["status"] == "FILLED" and quantity != order["quantity"])
                or (order["status"] in {"REJECTED", "CANCELLED"} and quantity)):
            mismatches.append(f"order_fill_quantity:{order_id}")
    entitlements = {}
    transitions = sorted([(row["ledger_seq"], "fill", row) for row in fills]
                         + [(row["ledger_seq"], "event", row) for row in events])
    seqs = [seq for seq, _, _ in transitions]
    if len(seqs) != len(set(seqs)):
        mismatches.append("duplicate_transition_seq")
    by_seq = {}
    for row in cashflows:
        by_seq.setdefault(row["ledger_seq"], []).append(row)
    source_events = {row["event_id"] for row in events}
    for seq in set(by_seq) - set(seqs):
        flows = by_seq[seq]
        if (len(flows) != 1 or not flows[0]["kind"].endswith("PAYMENT")
                or flows[0]["event_id"] not in source_events or flows[0]["fill_id"] is not None):
            mismatches.append("cashflow_transition_coverage")
        transitions.append((seq, "payment", flows[0]))
    transitions.sort(key=lambda transition: transition[0])
    previous_date = ""
    for _, _, row in transitions:
        if row["date"] < previous_date:
            mismatches.append("nonchronological_transition")
        previous_date = row["date"]
    days = sorted(checked["equity"], key=lambda row: row["date"])
    cursor = 0
    for expected in days:
        day = expected["date"]
        while cursor < len(transitions) and transitions[cursor][2]["date"] <= day:
            seq, kind, row = transitions[cursor]
            instrument = row["instrument_id"]
            flows = by_seq.get(seq, [])
            dc = sum(flow["cash_delta"] for flow in flows)
            dr = sum(flow["receivable_delta"] for flow in flows)
            dp = sum(flow["payable_delta"] for flow in flows)
            if any(flow["date"] != row["date"] for flow in flows):
                mismatches.append(f"cashflow_date:{seq}")
            if kind == "payment":
                quantity = 0
                entitlement = entitlements.get(row["event_id"])
                if (entitlement is None or entitlement["instrument_id"] != instrument
                        or dc > entitlement["remaining"] + 1e-8):
                    mismatches.append(f"payment_entitlement:{seq}")
                else:
                    entitlement["remaining"] += dr
                if any(flow["fee"] != 0 or flow["tax"] != 0 for flow in flows):
                    mismatches.append(f"payment_cost:{seq}")
                if dc < 0 or dr > 0 or not np.isclose(dc + dr - dp, 0, rtol=0, atol=1e-8):
                    mismatches.append(f"payment_balance:{seq}")
            elif kind == "fill":
                sign = 1 if row["side"] == "buy" else -1
                quantity = sign * row["quantity"]
                expected_cash = -sign * row["quantity"] * row["price"] - row["fee"] - row["tax"]
                if not np.isclose(dc + dr - dp, expected_cash, rtol=1e-12, atol=1e-8):
                    mismatches.append(f"fill_cash:{row['fill_id']}")
                if any(flow["fill_id"] != row["fill_id"] or flow["instrument_id"] != instrument for flow in flows):
                    mismatches.append(f"fill_link:{row['fill_id']}")
            else:
                quantity = row["quantity_delta"]
                if row["event_id"] in entitlements:
                    mismatches.append(f"duplicate_entitlement:{row['event_id']}")
                entitlements[row["event_id"]] = {"instrument_id": instrument, "remaining": dr}
                if not np.allclose([dc, dr, dp],
                                   [row["cash_delta"], row["receivable_delta"], row["payable_delta"]],
                                   rtol=1e-12, atol=1e-8):
                    mismatches.append(f"event_cash:{row['event_id']}")
                if any(flow["event_id"] != row["event_id"] or flow["instrument_id"] != instrument for flow in flows):
                    mismatches.append(f"event_link:{row['event_id']}")
            if kind != "payment":
                if not np.allclose([sum(flow["fee"] for flow in flows), sum(flow["tax"] for flow in flows)],
                                   [row["fee"], row["tax"]], rtol=1e-12, atol=1e-8):
                    mismatches.append(f"flow_cost:{seq}")
            old_qty = quantities.get(instrument, 0.0)
            if kind == "fill":
                if row["side"] == "buy":
                    basis_delta = row["quantity"] * row["price"] + row["fee"] + row["tax"]
                else:
                    basis_delta = -bases.get(instrument, 0.0) * row["quantity"] / old_qty if old_qty else 0
            else:
                basis_delta = row["cost_basis_delta"] if kind == "event" else 0
            bases[instrument] = bases.get(instrument, 0.0) + basis_delta
            quantities[instrument] = old_qty + quantity
            cash, receivables, payables = cash + dc, receivables + dr, payables + dp
            if quantities[instrument] < -1e-10 or min(cash, receivables, payables) < -1e-7:
                mismatches.append(f"negative_balance:{seq}")
            cursor += 1
        positions = [row for row in checked["positions"] if row["date"] == day]
        expected_qty = {row["instrument_id"]: row["quantity"] for row in positions}
        for instrument in set(quantities) | set(expected_qty):
            if not np.isclose(quantities.get(instrument, 0), expected_qty.get(instrument, 0), rtol=0, atol=1e-10):
                mismatches.append(f"eod_quantity:{day}:{instrument}")
        expected_basis = {row["instrument_id"]: row["cost_basis"] for row in positions}
        for instrument in set(bases) | set(expected_basis):
            if not np.isclose(bases.get(instrument, 0), expected_basis.get(instrument, 0), rtol=1e-12, atol=1e-7):
                mismatches.append(f"eod_basis:{day}:{instrument}")
        exposure = sum(row["quantity"] * row["mark_price"] for row in positions)
        actual = [cash, receivables, payables, exposure, cash + receivables - payables + exposure]
        wanted = [expected[key] for key in ("cash", "receivables", "payables", "exposure", "equity")]
        if not np.allclose(actual, wanted, rtol=1e-12, atol=1e-7):
            mismatches.append(f"eod_balance:{day}")
    if cursor != len(transitions):
        mismatches.append("transitions_without_eod")
    if any(row["date"] not in {day["date"] for day in days} for row in checked["positions"]):
        mismatches.append("positions_without_eod")
    return {"ok": not mismatches, "engine": "independent_contract_replay",
            "mismatches": list(dict.fromkeys(mismatches)), "transitions_checked": len(transitions),
            "eod_checked": len(days)}
