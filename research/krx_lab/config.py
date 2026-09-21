"""성과 확인 전에 고정하는 실험 구성."""

from pathlib import Path

from .io import read_json

ENTRIES = ("CROSS_5_20", "CROSS_10_20", "BREAKOUT_20", "BREAKOUT_60", "TREND_PULLBACK_3",
           "TREND_PULLBACK_5", "RSI_REENTRY_30", "RSI_REENTRY_40", "BOLLINGER_REENTRY_1_5",
           "BOLLINGER_REENTRY_2", "MACD_CROSS_SMA60", "MACD_CROSS_SMA120")
EXITS = ("PCT_3_6", "PCT_5_10", "ATR_1_5_3", "ATR_2_4")


def default_config(snapshot):
    return {
        "schema_version": "krx-lab-v1", "snapshot": str(Path(snapshot).resolve()),
        "initial_cash_krw": 100000000, "warmup_sessions": 250,
        "development": ["2015-01-02", "2019-12-31"], "validation_years": [2020, 2021, 2022, 2023],
        "holdout": {"start": "2024-01-01", "end": "2026-09-10", "unused_confirmed": False},
        "entries": list(ENTRIES), "exits": list(EXITS), "fees_bps": [10, 30, 50],
        "base_cost_bps": 30, "delay_stress": 2, "worker_count": 1,
        "selection_policy": "selection_policy_v1", "research_mdd_limit": 0.2,
        "allow_unverified_proxy": False,
        "resource_limits": {"max_rss_bytes": 2 * 1024**3, "min_free_disk_bytes": 512 * 1024**2,
                            "poll_interval_seconds": 0.25},
    }


def load_config(path):
    config = read_json(path)
    allowed = set(default_config("."))
    if set(config) - allowed:
        raise ValueError(f"알 수 없는 설정 키: {sorted(set(config) - allowed)}")
    result = default_config(config["snapshot"])
    result.update(config)
    if result["schema_version"] != "krx-lab-v1":
        raise ValueError("실행용 krx-lab-v1 설정이 필요합니다")
    if result["initial_cash_krw"] != 100000000 or result["worker_count"] != 1:
        raise ValueError("v1은 초기 1억 원, worker=1을 지원합니다")
    if result["entries"] != list(ENTRIES) or result["exits"] != list(EXITS):
        raise ValueError("선정 시도 수 보존을 위해 v1의 48개 후보를 변경할 수 없습니다")
    fixed = default_config(".")
    for key in ("development", "validation_years", "warmup_sessions", "fees_bps", "base_cost_bps",
                "delay_stress", "selection_policy", "research_mdd_limit"):
        if result[key] != fixed[key]:
            raise ValueError(f"{key}: 다른 연구 정책은 새 스키마 버전이 필요합니다")
    if not isinstance(result["allow_unverified_proxy"], bool):
        raise ValueError("allow_unverified_proxy는 boolean이어야 합니다")
    if result["allow_unverified_proxy"]:
        raise ValueError("미검증 조정가격의 수익률 우회 실행은 v1에서 지원하지 않습니다")
    from .resources import ResourceLimits
    if not isinstance(result["resource_limits"], dict):
        raise ValueError("resource_limits must be an object")
    result["resource_limits"] = ResourceLimits(**result["resource_limits"]).asdict()
    result["snapshot"] = str(Path(result["snapshot"]).resolve())
    return result


def primary_runs(config):
    runs = []
    for entry in config["entries"]:
        for exit_id in config["exits"]:
            common = {"entry_id": entry, "exit_id": exit_id, "strategy_id": f"{entry}__{exit_id}",
                      "policy": "fixed20"}
            runs.append({**common, "phase": "development", "year": None,
                         "start": config["development"][0], "end": config["development"][1],
                         "cost_bps": 30, "delay": 1})
            for year in config["validation_years"]:
                for cost, delay in ((10, 1), (30, 1), (50, 1), (30, 2)):
                    runs.append({**common, "phase": "validation", "year": year,
                                 "start": f"{year}-01-01", "end": f"{year}-12-31",
                                 "cost_bps": cost, "delay": delay})
    return runs
