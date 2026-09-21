"""Persist versioned pre-holdout plans without granting REAL execution."""

from pathlib import Path

from . import config_v2
from .io import canonical_hash, read_json, write_json


def prepare_plan(config_path, out):
    """Freeze a separate candidate plan. Snapshot existence is not admission.

    This command deliberately never loads prices or calls the legacy runner.
    Realistic fees, the ledger and Gate A/B remain explicit pending work.
    """
    schema = read_json(config_path).get("schema_version")
    loaders = {config_v2.SCHEMA_VERSION: config_v2.load_config,
               config_v2.WIDE_EXIT_SCHEMA_VERSION: config_v2.load_wide_config}
    if schema not in loaders:
        raise ValueError("UNSUPPORTED_PREPARATION_SCHEMA")
    config = loaders[schema](config_path)
    runs = config_v2.primary_runs(config)
    identity = canonical_hash(config)
    result = {
        "schema_version": "krx-preparation-plan-v1", "experiment_schema": schema,
        "experiment_id": f"{schema}-{identity[:16]}", "config_hash": identity,
        "execution_allowed": False, "status": "PREPARED_NOT_EXECUTABLE",
        "candidate_count": len(config["entries"]) * len(config["exits"]),
        "logical_slots": len(runs), "config": config,
        "pending": ["VERIFIED_V3_SNAPSHOT", "DATA_SCOPE_GATE_A", "REAL_COST_AND_LEDGER_GATE_B",
                    "REAL_RUNNER", "SMALL_REAL_LEDGER_CHECK"],
        "runs": [{**run, "status": "PLANNED"} for run in runs],
    }
    result["plan_hash"] = canonical_hash(result)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "preparation.json", result)
    return result
