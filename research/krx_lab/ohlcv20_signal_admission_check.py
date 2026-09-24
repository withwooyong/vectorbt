"""Independent consumer-side reproduction of the OHLCV signal admission rules.

This module does not import the producer's calculation scripts. It rebuilds
R1 (future-event admission), R2 (event-list completeness) and R3 (provider
reconciliation) from this repository's own input path
(``ohlcv20_input.load_corrected_v4``) and reconciles the resulting bar counts
against the provider evidence file ``signal-admission-v1.json``.

R1 and R3 mirror the algorithm already used by
``ohlcv20_input._admit_adjusted`` (suffix-blocked / suffix-product over
per-code events sorted by date), because that algorithm is the consumer's
existing, already-shipped interpretation of R1/R3 and 2026-09-23 design notes
record that it matches the provider's interpretation on those two rules. R2 is
new: this repository has no prior implementation of it, so it is written from
the rule text alone (see ``docs/research/signal-admission-design-2026-09-23.md``
line 58 in the ted-startup repository).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

from .ohlcv20_input import load_corrected_v4

_ADJUSTED_RELATIVE_TOLERANCE = 0.005  # must match ohlcv20_input._ADJUSTED_RELATIVE_TOLERANCE
_NON_PRICE_EVENT_TYPE = "LISTED_SHARE_CHANGE"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.normalize()


def _factor(value: object) -> Decimal:
    number = Decimal(str(value))
    if not number.is_finite() or number <= 0:
        raise ValueError("NON_POSITIVE_ADMITTED_FACTOR")
    return number


@dataclass(frozen=True)
class Candidates:
    """The 733-key candidate set (factor-admission-v3 audit)."""

    events: pd.DataFrame  # code, date, price_admitted, volume_admitted, price_factor
    sha256: str


def load_candidates(path: Path, expected_sha256: str | None = None) -> Candidates:
    digest = _sha256(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError(f"CANDIDATE_AUDIT_HASH_MISMATCH:{digest}")
    frame = pd.read_parquet(path)
    events = pd.DataFrame(
        {
            "code": frame["stock_code"].astype(str),
            "date": _date(frame["effective_date"]),
        }
    )
    for side in ("price", "volume"):
        admitted = frame[f"{side}_admitted"].to_numpy(dtype=bool)
        column = frame[f"{side}_factor"]
        events[f"{side}_admitted"] = admitted
        events[f"{side}_factor"] = [
            _factor(value) if flag else None for value, flag in zip(column, admitted)
        ]
    if events.duplicated(["code", "date"]).any():
        raise ValueError("DUPLICATE_CANDIDATE_KEY")
    return Candidates(events.sort_values(["code", "date"], ignore_index=True), digest)


def load_uncovered_events(path: Path, candidates: Candidates) -> pd.DataFrame:
    """Price-affecting corporate actions absent from the 733-key candidate set (R2)."""
    actions = pd.read_parquet(path, columns=["stock_code", "effective_date", "event_type", "apply_event"])
    price_affecting = actions.loc[
        actions["apply_event"].eq(True) & actions["event_type"].ne(_NON_PRICE_EVENT_TYPE)
    ].copy()
    price_affecting["code"] = price_affecting["stock_code"].astype(str)
    price_affecting["date"] = _date(price_affecting["effective_date"])
    candidate_keys = set(zip(candidates.events["code"], candidates.events["date"]))
    covered = [
        (code, date) in candidate_keys
        for code, date in zip(price_affecting["code"], price_affecting["date"])
    ]
    uncovered = price_affecting.loc[~np.asarray(covered), ["code", "date"]]
    return uncovered.drop_duplicates().sort_values(["code", "date"], ignore_index=True)


def _suffix(events: pd.DataFrame, side: str) -> tuple[np.ndarray, np.ndarray]:
    """Fold one code's events backwards into per-slot blockers and products.

    Reimplements, without importing, the same suffix-scan used by
    ``ohlcv20_input._suffix``: slot i answers for a bar preceding event i
    whether any event from i onwards is unadmitted, and the running product of
    admitted factors from i onwards.
    """
    flags = events[f"{side}_admitted"].to_numpy(dtype=bool)
    values = list(events[f"{side}_factor"])
    count = len(flags)
    blocked = np.zeros(count + 1, dtype=bool)
    product = np.ones(count + 1, dtype=float)
    running = Decimal(1)
    for index in range(count - 1, -1, -1):
        if flags[index]:
            running *= values[index]
        blocked[index] = bool(blocked[index + 1]) or not bool(flags[index])
        product[index] = float(running)
    return blocked, product


def _uncovered_blocked(dates_sorted: np.ndarray, bar_dates: np.ndarray) -> np.ndarray:
    """True where at least one uncovered event lies strictly after the bar."""
    slot = np.searchsorted(dates_sorted, bar_dates, side="right")
    return slot < len(dates_sorted)


@dataclass(frozen=True)
class AdmissionCounts:
    raw_bars_total: int
    r1_pass_price: int
    r1_pass_volume: int
    r2_additional_excluded_price: int
    r1_r2_pass_price: int
    r3_no_match_price: int
    r3_mismatch_price: int
    final_valid_bars_price: int


def compute_admission(
    bars: pd.DataFrame, candidates: Candidates, uncovered: pd.DataFrame
) -> tuple[AdmissionCounts, pd.DataFrame]:
    size = len(bars)
    price_ok = np.ones(size, dtype=bool)
    volume_ok = np.ones(size, dtype=bool)
    r2_blocked = np.zeros(size, dtype=bool)
    expected = np.ones(size, dtype=float)

    candidate_groups = dict(tuple(candidates.events.groupby("code", sort=False)))
    uncovered_groups = dict(tuple(uncovered.groupby("code", sort=False)))
    dates = bars["date"].to_numpy("datetime64[ns]")

    for code, rows in bars.groupby("code", sort=False).indices.items():
        group = candidate_groups.get(code)
        if group is not None:
            slot = np.searchsorted(
                group["date"].to_numpy("datetime64[ns]"), dates[rows], side="right"
            )
            price_blocked, price_product = _suffix(group, "price")
            volume_blocked, _ = _suffix(group, "volume")
            price_ok[rows] = ~price_blocked[slot]
            volume_ok[rows] = ~volume_blocked[slot]
            expected[rows] = price_product[slot]
        uncovered_group = uncovered_groups.get(code)
        if uncovered_group is not None:
            r2_blocked[rows] = _uncovered_blocked(
                uncovered_group["date"].to_numpy("datetime64[ns]"), dates[rows]
            )

    close = bars["close"].to_numpy(dtype=float)
    adjusted = bars["adjusted_close"].to_numpy(dtype=float)
    observed = np.divide(adjusted, close, out=np.full(size, np.nan), where=close > 0)
    comparable = np.isfinite(observed)
    matched = comparable & (np.abs(observed - expected) <= _ADJUSTED_RELATIVE_TOLERANCE * expected)

    r1_r2_price = price_ok & ~r2_blocked
    final_valid = r1_r2_price & matched
    no_match = r1_r2_price & ~comparable
    mismatch = r1_r2_price & comparable & ~matched

    bars = bars.copy()
    bars["r1_price_ok"] = price_ok
    bars["r1_volume_ok"] = volume_ok
    bars["r2_blocked"] = r2_blocked
    bars["r3_comparable"] = comparable
    bars["r3_matched"] = matched
    bars["signal_admitted_bar"] = final_valid

    counts = AdmissionCounts(
        raw_bars_total=size,
        r1_pass_price=int(price_ok.sum()),
        r1_pass_volume=int(volume_ok.sum()),
        r2_additional_excluded_price=int((price_ok & r2_blocked).sum()),
        r1_r2_pass_price=int(r1_r2_price.sum()),
        r3_no_match_price=int(no_match.sum()),
        r3_mismatch_price=int(mismatch.sum()),
        final_valid_bars_price=int(final_valid.sum()),
    )
    return counts, bars


def build_reconciliation(
    *,
    corrected_input_package: Path,
    candidate_audit_path: Path,
    corporate_actions_path: Path,
    provider_evidence_path: Path,
) -> dict[str, object]:
    """Reconcile consumer-side R1/R2/R3 bar counts against provider evidence.

    Candidate audit selection is fail-closed: the sha256 the provider declared
    in ``factor_admission_audit_sha256`` is the only accepted candidate audit.
    A ``candidate_audit_path`` whose bytes hash to anything else (e.g. the
    since-superseded v3 draft) is rejected before any bar is read, so the
    comparison never silently runs against the wrong candidate set.
    """
    provider = json.loads(provider_evidence_path.read_text(encoding="utf-8"))
    declared_audit_sha256 = provider.get("factor_admission_audit_sha256")
    if not isinstance(declared_audit_sha256, str):
        raise ValueError("MISSING_DECLARED_CANDIDATE_AUDIT_SHA256")

    candidates = load_candidates(candidate_audit_path, declared_audit_sha256)
    consumer_input = load_corrected_v4(corrected_input_package, admitted_factors=None)
    uncovered = load_uncovered_events(corporate_actions_path, candidates)
    counts, _ = compute_admission(consumer_input.bars, candidates, uncovered)

    provider_counts = provider["bar_counts"]

    fields = [
        "raw_bars_total",
        "r1_pass_price",
        "r1_pass_volume",
        "r2_additional_excluded_price",
        "r1_r2_pass_price",
        "r3_no_match_price",
        "r3_mismatch_price",
        "final_valid_bars_price",
    ]
    per_field = {}
    all_match = True
    for field in fields:
        consumer_value = getattr(counts, field)
        provider_value = provider_counts[field]
        match = consumer_value == provider_value
        all_match &= match
        per_field[field] = {
            "consumer": consumer_value,
            "provider": provider_value,
            "diff": consumer_value - provider_value,
            "match": match,
        }

    return {
        "schema": "ohlcv20-signal-admission-consumer-check-v1",
        "verdict": "MATCH" if all_match else "MISMATCH",
        "fields": per_field,
        "input_sha256": {
            "provider_evidence": _sha256(provider_evidence_path),
            "candidate_audit_used": candidates.sha256,
            "candidate_audit_declared_in_provider": provider.get("factor_admission_audit_sha256"),
            "corporate_actions": _sha256(corporate_actions_path),
        },
        "notes": [
            "R1/R3 재구현은 ohlcv20_input._admit_adjusted 의 suffix 스캔 알고리즘을 참고했다"
            "(코드 복사 없이 이 모듈에서 새로 작성).",
            "R2 는 이 저장소에 기존 구현이 없어 규칙 문장만으로 새로 작성했다.",
            "provider_evidence 의 factor_admission_audit_sha256 값은 factor-admission-v2 감사 parquet 의 "
            "해시와 일치한다. 팀장 확인 결과 공급자가 실제로 결합한 audit 은 v2 이며, "
            "factor-admission-v3.json(과 v3 audit)은 폐기 예정이라 커밋되지 않은 구판이므로 결합 대상이 "
            "아니다. 이 스크립트는 candidate_audit_path 를 열기 전에 provider 가 선언한 해시와 실제 파일의 "
            "sha256 을 대조해 다르면 대조를 시작하지 않고 실패한다(fail closed) — v3 파일을 지정하면 거부된다.",
        ],
    }


# v2 is the audit the provider actually admitted against (its parquet hash
# matches signal-admission-v1.json's factor_admission_audit_sha256). v3 is a
# since-superseded, uncommitted draft and must never be combined here; the
# fail-closed hash check in build_reconciliation() rejects it even if a
# caller overrides --candidate-audit to point at it.
_DEFAULT_CANDIDATE_AUDIT = Path(
    "C:/Users/aeby/vscode/ted-startup/data/sources/ohlcv-admission-20260922"
    "/factor-admission-v2/factor-admission-audit.parquet"
)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corrected-input", type=Path, required=True)
    parser.add_argument("--candidate-audit", type=Path, default=_DEFAULT_CANDIDATE_AUDIT)
    parser.add_argument("--corporate-actions", type=Path, required=True)
    parser.add_argument("--provider-evidence", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    result = build_reconciliation(
        corrected_input_package=args.corrected_input,
        candidate_audit_path=args.candidate_audit,
        corporate_actions_path=args.corporate_actions,
        provider_evidence_path=args.provider_evidence,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], "fields": result["fields"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
