"""Fixed configuration for the opt-in 56-strategy relative-volume experiment.

This module intentionally does not alter ``config.py`` or its 48-candidate v1
contract.  It plans comparisons only; REAL execution remains unadmitted.
"""

from pathlib import Path

from .config import ENTRIES as V1_ENTRIES
from .config import EXITS
from .io import read_json
from .resources import ResourceLimits
from .strategies import RVOL_ENTRY_IDS


ENTRIES = (*V1_ENTRIES, *RVOL_ENTRY_IDS)
SCHEMA_VERSION = "krx-breakout-rvol-v2"
WIDE_EXIT_SCHEMA_VERSION = "krx-breakout-rvol-wide-exits-v3"
WIDE_EXITS = ("PCT_8_16", "PCT_10_20", "ATR_3_6", "ATR_4_8")
_FIXED_POLICY_KEYS = (
    "development", "validation_years", "warmup_sessions", "fees_bps", "base_cost_bps",
    "delay_stress", "selection_policy", "research_mdd_limit", "sector_cap", "holdout",
    "exit_reference", "holding_period", "max_positions", "portfolio_exposure_cap",
    "per_trade_risk_fraction", "execution_model", "cost_model", "exit_reward_risk_ratio",
)


def default_config(snapshot):
    """Return the preregistered v2 experiment configuration without opening data."""
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot": str(Path(snapshot).resolve()),
        "initial_cash_krw": 100000000,
        "warmup_sessions": 250,
        "development": ["2015-06-15", "2019-12-31"],
        "validation_years": [2020, 2021, 2022, 2023],
        "holdout": {"start": "2024-01-01", "end": "2026-09-10", "unused_confirmed": False},
        "entries": list(ENTRIES),
        "exits": list(EXITS),
        "fees_bps": [10, 30, 50],
        "base_cost_bps": 30,
        "delay_stress": 2,
        "worker_count": 1,
        "selection_policy": "selection_policy_v1",
        "research_mdd_limit": 0.2,
        "sector_cap": None,
        "exit_reference": "SIGNAL_CLOSE",
        "holding_period": "ONE_CALENDAR_MONTH",
        "max_positions": 20,
        "portfolio_exposure_cap": 0.8,
        "per_trade_risk_fraction": 0.005,
        "execution_model": "PENDING_REAL_VALIDATION",
        "cost_model": "FLAT_BPS_STRESS_ONLY",
        "exit_reward_risk_ratio": "NOMINAL_1_TO_2",
        "execution_admitted": False,
        "allow_unverified_proxy": False,
        "resource_limits": {
            "max_rss_bytes": 2 * 1024**3,
            "min_free_disk_bytes": 512 * 1024**2,
            "poll_interval_seconds": 0.25,
        },
    }


def load_config(path):
    """Load only the frozen v2 candidate set and execution policy."""
    return _load_config(path, default_config, SCHEMA_VERSION, ENTRIES, EXITS,
                        "selection_policy_v1", "v2")


def default_wide_config(snapshot):
    """Return the separate wide-exit experiment, without mutating the RVOL v2 plan.

    The same fourteen entry hypotheses are combined with four preregistered
    one-to-two-risk exits.  It is a distinct, unadmitted experiment and cannot
    be loaded through :func:`load_config`.
    """
    config = default_config(snapshot)
    config.update(
        schema_version=WIDE_EXIT_SCHEMA_VERSION,
        exits=list(WIDE_EXITS),
        selection_policy="selection_policy_wide_exits_v1",
    )
    return config


def load_wide_config(path):
    """Load only the separately versioned wide-exit candidate set."""
    return _load_config(path, default_wide_config, WIDE_EXIT_SCHEMA_VERSION, ENTRIES, WIDE_EXITS,
                        "selection_policy_wide_exits_v1", "wide-exit v3")


def _load_config(path, factory, schema_version, entries, exits, selection_policy, label):
    config = read_json(path)
    allowed = set(factory("."))
    if set(config) - allowed:
        raise ValueError(f"알 수 없는 설정 키: {sorted(set(config) - allowed)}")
    result = factory(config["snapshot"])
    result.update(config)
    _validate_config(result, factory, schema_version, entries, exits, selection_policy, label)
    result["resource_limits"] = ResourceLimits(**result["resource_limits"]).asdict()
    result["snapshot"] = str(Path(result["snapshot"]).resolve())
    return result


def primary_runs(config):
    """Return the configured experiment's 56 development and 896 validation comparisons."""
    _validate_primary_config(config)
    runs = []
    for entry in config["entries"]:
        for exit_id in config["exits"]:
            common = {"entry_id": entry, "exit_id": exit_id, "strategy_id": f"{entry}__{exit_id}",
                      "policy": "fixed20", "sector_cap": config["sector_cap"]}
            runs.append({**common, "phase": "development", "year": None,
                         "start": config["development"][0], "end": config["development"][1],
                         "cost_bps": 30, "delay": 1})
            for year in config["validation_years"]:
                for cost, delay in ((10, 1), (30, 1), (50, 1), (30, 2)):
                    runs.append({**common, "phase": "validation", "year": year,
                                 "start": f"{year}-01-01", "end": f"{year}-12-31",
                                 "cost_bps": cost, "delay": delay})
    return runs


def _validate_primary_config(config):
    if not isinstance(config, dict):
        raise ValueError("config는 object여야 합니다")
    schema_version = config.get("schema_version")
    if schema_version == SCHEMA_VERSION:
        _validate_config(config, default_config, SCHEMA_VERSION, ENTRIES, EXITS, "selection_policy_v1", "v2")
    elif schema_version == WIDE_EXIT_SCHEMA_VERSION:
        _validate_config(config, default_wide_config, WIDE_EXIT_SCHEMA_VERSION, ENTRIES, WIDE_EXITS,
                         "selection_policy_wide_exits_v1", "wide-exit v3")
    else:
        raise ValueError("알 수 없는 v2 실험 스키마입니다")


def _validate_config(result, factory, schema_version, entries, exits, selection_policy, label):
    if result.get("schema_version") != schema_version:
        raise ValueError(f"실행용 {schema_version} 설정이 필요합니다")
    if type(result.get("initial_cash_krw")) is not int or type(result.get("worker_count")) is not int:
        raise ValueError("initial_cash_krw와 worker_count는 boolean이 아닌 정수여야 합니다")
    if result["initial_cash_krw"] != 100000000 or result["worker_count"] != 1:
        raise ValueError(f"{label}은 초기 1억 원, worker=1을 지원합니다")
    if result.get("entries") != list(entries) or result.get("exits") != list(exits):
        raise ValueError(f"{label}은 고정된 48개 기준선과 8개 RVOL 후보만 지원합니다")
    if result.get("selection_policy") != selection_policy:
        raise ValueError("selection_policy: 다른 연구 정책은 새 스키마 버전이 필요합니다")
    if type(result.get("max_positions")) is not int:
        raise ValueError("max_positions는 boolean이 아닌 정수여야 합니다")
    for key in ("portfolio_exposure_cap", "per_trade_risk_fraction"):
        if isinstance(result.get(key), bool) or not isinstance(result.get(key), (int, float)):
            raise ValueError(f"{key}는 boolean이 아닌 숫자여야 합니다")
    fixed = factory(".")
    for key in _FIXED_POLICY_KEYS:
        if result.get(key) != fixed[key]:
            raise ValueError(f"{key}: 다른 연구 정책은 새 스키마 버전이 필요합니다")
    if result.get("execution_admitted") is not False:
        raise ValueError("v2의 REAL execution은 아직 인수되지 않았습니다")
    if not isinstance(result.get("allow_unverified_proxy"), bool):
        raise ValueError("allow_unverified_proxy는 boolean이어야 합니다")
    if result["allow_unverified_proxy"]:
        raise ValueError("미검증 조정가격의 수익률 우회 실행은 v2에서 지원하지 않습니다")
    if not isinstance(result.get("resource_limits"), dict):
        raise ValueError("resource_limits must be an object")
