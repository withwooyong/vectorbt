"""User-fixed OHLCV20 experiments and explicit 2026 modeled costs.

These values are a research policy, not real-data admission or a broker ledger.
The 2026 ordinary domestic-share tax scope must be verified by the caller;
foreign shares, depositary receipts and other instruments cannot inherit it.
Exact Decimal accrual avoids an invented broker rounding convention.
"""

from dataclasses import dataclass
from decimal import Decimal
from itertools import product


@dataclass(frozen=True)
class Experiment:
    key: str
    stop_pct: Decimal
    target_pct: Decimal
    holding_months: int
    baseline: bool = False


def experiments() -> tuple[Experiment, ...]:
    rows = [
        Experiment(f"SL{s}_TP{t}_M{months}", Decimal(s) / 100, Decimal(t) / 100, months)
        for s, t, months in product((10, 15, 20), (20, 30, 40, 50), (1, 3))
    ]
    rows.extend(
        Experiment(
            f"BASE_SL5_TP15_M{months}", Decimal("0.05"), Decimal("0.15"), months, True
        )
        for months in (1, 3)
    )
    return tuple(rows)


def _amount(value) -> Decimal:
    if isinstance(value, bool):
        raise ValueError("INVALID_MONETARY_AMOUNT")
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError("INVALID_MONETARY_AMOUNT")
    return result


@dataclass(frozen=True)
class Cost2026:
    """Ordinary-share KRX policy, applied uniformly over historical dates.

    Friction is a separate modeled cash charge; it must not change the fill
    price beyond a limit order or get reported as a Kiwoom commission.
    ``tax_scope`` asserts an already validated instrument class, not a guess.
    """

    tax_scope: str
    friction_rate: Decimal = Decimal("0.001")

    def __post_init__(self):
        if self.tax_scope != "DOMESTIC_ORDINARY_SHARE":
            raise ValueError("INSTRUMENT_TAX_SCOPE_NOT_SUPPORTED")
        value = _amount(self.friction_rate)
        if value not in (Decimal("0.001"), Decimal("0.002")):
            raise ValueError("FRICTION_SCENARIO_NOT_REGISTERED")
        object.__setattr__(self, "friction_rate", value)

    def breakdown(self, side, market, notional) -> dict[str, Decimal]:
        if side not in ("BUY", "SELL") or market not in ("KOSPI", "KOSDAQ"):
            raise ValueError("UNSUPPORTED_ORDER_COST_SCOPE")
        amount = _amount(notional)
        commission = amount * Decimal("0.00015")
        transaction_tax = Decimal(0)
        rural_tax = Decimal(0)
        if side == "SELL":
            transaction_tax = amount * Decimal(
                "0.0005" if market == "KOSPI" else "0.002"
            )
            rural_tax = amount * Decimal("0.0015") if market == "KOSPI" else Decimal(0)
        friction = amount * self.friction_rate
        return {
            "commission": commission,
            "transaction_tax": transaction_tax,
            "rural_tax": rural_tax,
            "modeled_friction": friction,
            "total": commission + transaction_tax + rural_tax + friction,
        }

    def __call__(self, side, day, market, notional) -> Decimal:
        # day intentionally does not select a historical tax regime.
        return self.breakdown(side, market, notional)["total"]


def policy_manifest() -> dict:
    return {
        "schema": "ohlcv20-user-policy-v1",
        "initial_cash_krw": 100_000_000,
        "independent_slots": 20,
        "evaluation_start": "2015-06-15",
        "evaluation_end": "2023-12-31",
        "cash_dividends": "EXCLUDED",
        "price_basis": "VERIFIED_SIGNAL_ADJUSTMENT_AND_RAW_FILLS",
        "ordinary_universe_exit": "NO_FORCED_LIQUIDATION",
        "buy_capacity": "ORDER_NOTIONAL_LE_1PCT_PRIOR20_SESSION_MEAN_ACTUAL_TURNOVER",
        "buy_capacity_overflow": "SKIP_WITHOUT_RESIZING_OR_SAME_DAY_REPLACEMENT",
        "capacity_failed_candidate_assignment": "RETAIN_ORIGINAL_SLOT_NO_TRANSFER_TO_LATER_SLOT",
        "universe": {
            "markets": ["KOSPI", "KOSDAQ"],
            "preferred_history": ["KOSPI200", "KOSDAQ150"],
            "fallback_market_cap_rank_limits": {"KOSPI": 200, "KOSDAQ": 150},
            "minimum_market_cap_krw_inclusive": 100_000_000_000,
            "exclude_types": ["ETF", "ETN", "PREFERRED", "SPAC", "KONEX", "REIT"],
            "include_ordinary_shares_with_letter_codes": True,
            "management_stock_filter": False,
            "fallback_rank_rebalance": "PRIOR_MONTH_LAST_SESSION_FOR_NEXT_MONTH",
            "universe_exit": "NO_FORCED_LIQUIDATION_ON_CAP_OR_MEMBERSHIP_EXIT",
            "missing_required_metadata": "BLOCK",
        },
        "signal": {
            "basis": "POINT_IN_TIME_ADJUSTED_PRICES_AND_ADMITTED_VOLUME_FACTORS",
            "kospi_close_gain_gte": "0.10",
            "kosdaq_close_gain_gte": "0.15",
            "volume_today_gte_prior_comparable_multiple": "2",
            "prior_volume_must_be_positive": True,
            "prior_close_lte_prior_60_session_low_multiple": "1.2",
            "low_window": "T_MINUS_60_THROUGH_T_MINUS_1_INCLUSIVE",
            "signal_day": "AFTER_CLOSE",
        },
        "entry": {
            "order_day": "NEXT_MARKET_SESSION_ONLY",
            "limit_price": "SIGNAL_DAY_RAW_REGULAR_CLOSE",
            "open_lte_limit": "FILL_AT_OPEN",
            "open_gt_limit_and_low_lt_limit": "FILL_AT_LIMIT",
            "open_gt_limit_and_low_eq_limit": "NO_FILL",
            "low_gt_limit": "NO_FILL",
            "order_quantity": "MAX_INTEGER_SHARES_AFFORDABLE_AT_LIMIT_WITH_COST",
            "unfilled_order": "CANCEL_AT_DAY_END_NO_SAME_DAY_REPLACEMENT",
            "same_day_open_entry": "STOP_FIRST_IF_BOTH_LEVELS_TOUCHED",
            "same_day_intraday_entry": "STOP_IF_LOW_REACHES_STOP_ELSE_TARGET_ONLY_IF_CLOSE_REACHES_TARGET",
        },
        "assignment": {
            "candidate_order": "SIGNAL_DAY_ACTUAL_TURNOVER_DESC_THEN_CODE_ASC",
            "candidate_count": "AVAILABLE_SLOTS_ONLY",
            "slot_order": "IDLE_SINCE_ASC_THEN_SLOT_ID_ASC",
            "mapping": "ONE_TO_ONE_IN_SORTED_ORDER_NO_REASSIGNMENT_AFTER_CAPACITY_FAILURE",
            "held_or_duplicate_code": "EXCLUDE",
        },
        "exit": {
            "levels_basis": "ACTUAL_BUY_FILL_PRICE",
            "open_gap": "FILL_AT_OPEN_IF_SELLABLE",
            "intraday_level": "FILL_AT_LEVEL_IF_SELLABLE",
            "both_levels_touched": "STOP_FIRST_WITH_TARGET_FIRST_SENSITIVITY",
            "holding_months": [1, 3],
            "calendar_month_end": "USE_LAST_DAY_IF_NO_SAME_DAY_NUMBER",
            "expiry": "FIRST_SELLABLE_SESSION_OPEN_ON_OR_AFTER_CALENDAR_ANNIVERSARY",
            "pending_exit": "CONTINUE_AT_NEXT_SELLABLE_OPEN_SUBJECT_TO_VOLUME_CAP",
        },
        "sellability": {
            "source": "EXPLICIT_VERIFIED_STOCK_DATE_LISTING_AND_SELL_STATUS",
            "lower_limit_reference": "OFFICIAL_DATE_SPECIFIC_LIMIT_WHEN_TRADABLE",
            "lower_limit_locked": "NO_ASSUMED_SELL_FILL_EVEN_IF_DAILY_VOLUME_POSITIVE",
            "unknown_or_conflicting_status": "BLOCK_PERFORMANCE",
        },
        "delisting_valuation": {
            "documented_cash_or_security_rights": "BOOK_ONLY_WHEN_ADMITTED",
            "unresolved_held_mark_or_rights": "BLOCK_PERFORMANCE_NO_INVENTED_ZERO_OR_LAST_CLOSE",
        },
        "sell_capacity": "FLOOR_1PCT_CURRENT_DAY_VOLUME_AGGREGATE_BY_INSTRUMENT",
        "sell_capacity_timing": "DAILY_PROXY_NOT_OBSERVED_INTRADAY_LIQUIDITY",
        "pending_exit": "REMAINDER_AT_NEXT_SELLABLE_SESSION_OPEN",
        "slot_reuse": "SESSION_AFTER_ALL_HELD_SHARES_SOLD",
        "spin_off": "ORIGINAL_SLOT_BOTH_LEGS_LIQUIDATE_WHEN_SELLABLE_SUBJECT_TO_CAPACITY",
        "late_fractional_cash": "ORIGINAL_SLOT_NO_TOP_UP_BUYS",
        "fixed_cost_year": 2026,
        "commission_each_side": "0.00015",
        "ordinary_domestic_sell_tax_total": "0.002",
        "friction_scenarios_each_side": ["0.001", "0.002"],
        "monetary_rounding": "EXACT_DECIMAL_MODEL_NOT_BROKER_STATEMENT_REPLICATION",
        "experiments": [
            {
                "key": row.key,
                "stop_pct": str(row.stop_pct),
                "target_pct": str(row.target_pct),
                "holding_months": row.holding_months,
                "baseline": row.baseline,
            }
            for row in experiments()
        ],
        "experiment_count": 26,
        "cost_scenario_runs": 52,
        "selection_protocol": {
            "development_end": "2020-12-31",
            "internal_validation_start": "2021-01-01",
            "internal_validation_end": "2023-12-31",
            "primary_friction_each_side": "0.001",
            "development_rank": "NET_END_EQUITY_DESC_THEN_ABSOLUTE_MAX_DRAWDOWN_ASC_THEN_EXPERIMENT_KEY_ASC",
            "validation_visibility": "HIDE_2021_TO_2023_RESULTS_UNTIL_ONE_KEY_IS_LOCKED",
            "validation": "SELECT_ONE_ON_DEVELOPMENT_ONLY_THEN_REPORT_WITHOUT_RETUNING",
            "claim_limit": "INTERNAL_TEMPORAL_VALIDATION_NOT_EXTERNAL_OR_LIVE_APPROVAL",
            "post_2023_locked_period": "NOT_USED",
        },
        "real_execution_admitted": False,
    }
