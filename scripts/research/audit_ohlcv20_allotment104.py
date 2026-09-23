"""Audit the 104 v2 allotment-ratio volume blockers from sealed local evidence.

This script is read-only with respect to ``ted-startup``.  It verifies the v2
hash chain, identifies the exact 104 price-approved/volume-blocked keys, checks
stored DART originals when available, and writes a deterministic JSON audit and
Korean review.  It does not change admission, repair source data, call a
network/API/DB, or run a backtest.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import re
import zipfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd


VECTORBT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TED_ROOT = Path(r"C:\Users\aeby\vscode\ted-startup")
DEFAULT_OUTPUT_DIR = (
    VECTORBT_ROOT / "docs/strategy-research/backtest-lab/ohlcv20-factor-v2-intake-2026-09-23"
)
EVIDENCE_REL = Path("docs/research/evidence/ohlcv-admission-2026-09-22")
DATA_REL = Path("data/sources/ohlcv-admission-20260922")
DART_REL = Path("data/sources/dart/allotment-ratio-2015-2023")
TOLERANCE = Decimal("0.005")
TARGET_BLOCKERS = {"ALLOTMENT_RATIO_MISMATCH", "ALLOTMENT_RATIO_NOT_PARSED"}


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value):
    if value is None or (not isinstance(value, (list, dict)) and pd.isna(value)):
        return None
    return value


def decimal_or_none(value) -> Decimal | None:
    value = clean(value)
    if value in (None, "", "-"):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except InvalidOperation:
        return None


def rel_ted(path: Path, ted_root: Path) -> str:
    return str(path.relative_to(ted_root)).replace("\\", "/")


def resolve_ted_path(ted_root: Path, raw: str) -> Path:
    return ted_root / Path(raw.replace("\\", "/"))


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def flatten_zip(path: Path) -> str:
    """Mirror the delivery parser's lenient, in-memory XML text flattening."""
    texts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(path.read_bytes())) as zf:
        for info in zf.infolist():
            if not info.filename.lower().endswith(".xml"):
                continue
            raw = zf.read(info)
            for encoding in ("utf-8", "cp949", "euc-kr"):
                try:
                    text = raw.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                text = raw.decode("utf-8", errors="replace")
            texts.append(html.unescape(_TAG_RE.sub(" ", text)))
    return _WS_RE.sub(" ", " ".join(texts)).strip()


def nospace(text: str) -> str:
    return _WS_RE.sub("", text)


def extract_common_value(text_no_space: str, label: str) -> str | None:
    index = text_no_space.find(label)
    if index < 0:
        return None
    window = text_no_space[index + len(label) : index + len(label) + 220]
    match = re.search(r"(?:보통주식|보통주)(?:\(주\))?([0-9][0-9,.]*|-)", window)
    return match.group(1) if match else None


def extract_record_date(text_no_space: str) -> str | None:
    for label in ("신주배정기준일", "주주확정일", "신주배정일", "배당기준일", "기준일"):
        index = text_no_space.find(label)
        if index < 0:
            continue
        window = text_no_space[index + len(label) : index + len(label) + 45]
        match = re.search(r"(\d{4})[년.-](\d{1,2})[월.-](\d{1,2})일?", window)
        if match:
            year, month, day = map(int, match.groups())
            return f"{year:04d}-{month:02d}-{day:02d}"
    return None


def first_prose_ratio(text_no_space: str) -> str | None:
    patterns = (
        r"(?:소유주식|보유주식|보통주)1주당([0-9][0-9,.]*)주의?비율",
        r"(?:소유주식|보유주식|보통주)1주당([0-9][0-9,.]*)주를?배정",
    )
    for pattern in patterns:
        match = re.search(pattern, text_no_space)
        if match:
            return match.group(1)
    return None


def evidence_snippet(text: str, labels: tuple[str, ...], width: int = 300) -> str | None:
    for label in labels:
        match = re.search(r"\s*".join(re.escape(char) for char in label), text)
        if match:
            return text[max(0, match.start() - 40) : match.end() + width].strip()
    return None


def inspect_raw(path: Path, kind: str, back_computed: Decimal | None) -> dict:
    text = flatten_zip(path)
    compact = nospace(text)
    if kind == "BONUS_ISSUE":
        ratio_label = "1주당신주배정주식수"
        new_label = "신주의종류와수"
        issued_label = "증자전발행주식총수"
        snippet_labels = ("1주당 신주배정 주식수", "1주당신주배정주식수")
    else:
        ratio_label = "1주당배당주식수"
        new_label = "배당주식총수"
        issued_label = "발행주식총수"
        snippet_labels = ("1주당 배당주식수", "1주당배당주식수")

    direct_ratio = extract_common_value(compact, ratio_label)
    new_shares = extract_common_value(compact, new_label)
    issued_shares = extract_common_value(compact, issued_label)
    direct_decimal = decimal_or_none(direct_ratio)
    new_decimal = decimal_or_none(new_shares)
    issued_decimal = decimal_or_none(issued_shares)
    effective_factor = None
    effective_gap = None
    if new_decimal is not None and issued_decimal not in (None, Decimal(0)):
        effective_factor = Decimal(1) + new_decimal / issued_decimal
        if back_computed not in (None, Decimal(0)):
            effective_gap = abs(effective_factor - back_computed) / back_computed

    return {
        "record_date": extract_record_date(compact),
        "labeled_common_share_allotment_ratio_raw": direct_ratio,
        "labeled_common_share_allotment_ratio_numeric": str(direct_decimal) if direct_decimal is not None else None,
        "new_or_dividend_common_shares": new_shares,
        "pre_event_issued_common_shares": issued_shares,
        "effective_total_share_factor_candidate": str(effective_factor) if effective_factor is not None else None,
        "effective_factor_vs_price_back_relative_gap": str(effective_gap) if effective_gap is not None else None,
        "effective_factor_matches_0_5pct": effective_gap is not None and effective_gap <= TOLERANCE,
        "prose_allotment_ratio_candidate": first_prose_ratio(compact),
        "mentions_treasury_shares": "자기주식" in compact,
        "mentions_fractional_shares": "단수주" in compact,
        "field_snippet": evidence_snippet(text, snippet_labels),
    }


def verify_hash(checks: list[dict], name: str, path: Path, expected: str) -> str:
    actual = sha256_path(path) if path.exists() else None
    checks.append(
        {
            "name": name,
            "path": str(path),
            "expected_sha256": expected,
            "actual_sha256": actual,
            "ok": actual == expected,
        }
    )
    return actual or ""


def classify(row: dict, raw: dict | None, manifest_result: dict) -> tuple[str, dict, list[str]]:
    blocker = row["current_blocker"]
    unresolved: list[str] = []
    if blocker == "ALLOTMENT_RATIO_MISMATCH":
        parsed = decimal_or_none(row["dart_parse"]["allotment_ratio"])
        direct = decimal_or_none(raw.get("labeled_common_share_allotment_ratio_numeric") if raw else None)
        prose = decimal_or_none(raw.get("prose_allotment_ratio_candidate") if raw else None)
        effective_matches = bool(raw and raw.get("effective_factor_matches_0_5pct"))
        if direct is not None and parsed is not None and direct != parsed:
            cause = "RAW_TABLE_RATIO_FIELD_INCONSISTENT_AND_PARSER_COMMA_TRUNCATION"
            recovery = {
                "possible": effective_matches and prose is not None,
                "candidate": "원문 서술 배정비율과 신주수/발행주식수 파생계수를 별도 심사",
                "automatic_promotion_allowed": False,
                "required_review": "원공시 표 내부 모순 확인, 파서 수정, 정책상 허용 근거의 별도 승인",
            }
            unresolved.append("현재 원문 표의 1주당 필드와 원문 서술·주식수 합계가 서로 다름")
        elif effective_matches:
            cause = "ELIGIBLE_SHARE_RATIO_DIFFERS_FROM_TOTAL_ISSUED_EFFECTIVE_RATIO"
            recovery = {
                "possible": True,
                "candidate": "원문 신주/배당주식수 ÷ 증자전/발행주식총수로 구한 실효 총주식 계수",
                "automatic_promotion_allowed": False,
                "required_review": "현행 직접 배정비율 정책과 다른 산식이므로 정책 판단 및 독립 검증",
            }
            unresolved.append("현행 정책은 적격주주 1주당 배정비율을 직접 비교하므로 현재 차단은 유지")
        else:
            cause = "DIRECT_AND_EFFECTIVE_RATIOS_BOTH_MISMATCH_PRICE_BACKCOMPUTATION"
            recovery = {
                "possible": False,
                "candidate": None,
                "automatic_promotion_allowed": False,
                "required_review": "KRX 기준가격 산식, anchor close, 복합행사 여부의 별도 원문 감사",
            }
            unresolved.append("저장 원문 주식수로 만든 실효계수도 0.5% 안에서 기준가격 역산값과 맞지 않음")
        return cause, recovery, unresolved

    failure = row["dart_parse"]["failure_reason"]
    match_count = len(manifest_result.get("matches", []))
    if failure == "DISCLOSURE_NO_UNIQUE_DISCLOSURE" and match_count == 0:
        cause = "SEARCH_RESULT_NO_POLICY_TITLE_CANDIDATE"
        recovery = {
            "possible": True,
            "candidate": "검색기간·명칭·기업코드 연결을 재감사하고 정책에 맞는 원공시를 새로 특정",
            "automatic_promotion_allowed": False,
            "required_review": "현재 저장 검색결과에는 정책 제목 후보가 없고 원문 ZIP도 없어 외부 재수집 전 확정 불가",
        }
        unresolved.append("후보 0건은 공시 자체의 부재나 데이터 누락을 뜻하지 않음")
    elif failure == "DISCLOSURE_NO_UNIQUE_DISCLOSURE":
        cause = "SEARCH_RESULT_MULTIPLE_POLICY_TITLE_CANDIDATES"
        recovery = {
            "possible": True,
            "candidate": "모든 원공시의 기준일·주식종류를 대조하여 한 건을 특정",
            "automatic_promotion_allowed": False,
            "required_review": "현재 수집본은 후보가 복수라 선택하지 않았고 일부/전부 원문이 저장되지 않음",
        }
        unresolved.append("제목 후보만으로 원공시를 임의 선택할 수 없음")
    elif failure == "RECORD_DATE_MISMATCH":
        cause = "MATCHED_DISCLOSURE_RECORD_DATE_MISMATCH"
        recovery = {
            "possible": True,
            "candidate": "해당 effective date와 0~14일 차이의 기준일을 가진 별도 원공시를 특정",
            "automatic_promotion_allowed": False,
            "required_review": "현재 ZIP은 다른 사건 공시로 판정되어 비율을 재사용할 수 없음",
        }
        unresolved.append("저장된 유일 제목 후보가 목표 사건과 시간상 연결되지 않음")
    elif failure == "ALLOTMENT_LABEL_NOT_FOUND" and raw and raw.get(
        "labeled_common_share_allotment_ratio_raw"
    ) in (None, "-"):
        cause = "ORDINARY_SHARE_RATIO_ABSENT_PREFERRED_ONLY"
        recovery = {
            "possible": False,
            "candidate": None,
            "automatic_promotion_allowed": False,
            "required_review": "보통주 대상 사건/종목종류 연결을 재검토; 종류주식 비율로 대체 금지",
        }
        unresolved.append("원공시의 보통주 배정 칸은 비어 있고 종류주식 비율만 존재")
    else:
        cause = "PARSE_FAILURE_OTHER"
        recovery = {
            "possible": True,
            "candidate": "원문 라벨과 사건 연결을 수동 재감사",
            "automatic_promotion_allowed": False,
            "required_review": "현재 파싱 실패 사유만으로 비율을 추정하지 않음",
        }
        unresolved.append("현재 저장 근거로 배정비율을 확정하지 못함")
    return cause, recovery, unresolved


def build_audit(ted_root: Path) -> dict:
    evidence = ted_root / EVIDENCE_REL
    data = ted_root / DATA_REL
    dart = ted_root / DART_REL
    paths = {
        "policy": evidence / "factor-admission-policy-v1.json",
        "factor_report": evidence / "factor-admission-v2.json",
        "candidate_report": evidence / "reference-factor-candidates-v2.json",
        "parse_report": evidence / "allotment-ratio-parse-v1.json",
        "factor_audit": data / "factor-admission-v2/factor-admission-audit.parquet",
        "candidates": data / "reference-factor-candidates-v2/candidates.parquet",
        "allotment": data / "allotment-ratios-v1/allotment-ratios.parquet",
        "manifest": dart / "manifest.json",
    }
    reports = {name: load_json(paths[name]) for name in ("factor_report", "candidate_report", "parse_report")}
    factor_report = reports["factor_report"]
    candidate_report = reports["candidate_report"]
    parse_report = reports["parse_report"]

    checks: list[dict] = []
    verify_hash(checks, "policy<-factor_report", paths["policy"], factor_report["policy_sha256"])
    verify_hash(checks, "policy<-candidate_report", paths["policy"], candidate_report["policy_sha256"])
    verify_hash(
        checks, "candidate_report<-factor_report", paths["candidate_report"], factor_report["candidate_report_sha256"]
    )
    verify_hash(checks, "candidates<-factor_report", paths["candidates"], factor_report["candidates_sha256"])
    verify_hash(checks, "factor_audit<-factor_report", paths["factor_audit"], factor_report["output_sha256"])
    verify_hash(
        checks,
        "factor_builder<-factor_report",
        ted_root / "scripts/data_delivery/build_ohlcv_admitted_factors.py",
        factor_report["builder_sha256"],
    )
    verify_hash(checks, "manifest<-parse_report", paths["manifest"], parse_report["input_manifest_sha256"])
    verify_hash(
        checks,
        "parser_builder<-parse_report",
        ted_root / "scripts/data_delivery/parse_ohlcv_allotment_ratios.py",
        parse_report["builder_sha256"],
    )
    verify_hash(checks, "allotment<-parse_report", paths["allotment"], parse_report["output_sha256"])
    verify_hash(
        checks,
        "allotment<-candidate_report",
        paths["allotment"],
        candidate_report["allotment_ratio_data_sha256"],
    )
    verify_hash(
        checks,
        "parse_report<-candidate_report",
        paths["parse_report"],
        candidate_report["allotment_ratio_report_sha256"],
    )
    verify_hash(
        checks,
        "candidate_builder<-candidate_report",
        ted_root / "scripts/data_delivery/build_ohlcv_reference_factor_candidates.py",
        candidate_report["builder_sha256"],
    )
    for owner, report in (("parse_report", parse_report), ("candidate_report", candidate_report)):
        for artifact in report["artifacts"]:
            verify_hash(
                checks,
                f"{owner}_artifact:{artifact['path']}",
                resolve_ted_path(ted_root, artifact["path"]),
                artifact["sha256"],
            )

    audit = pd.read_parquet(paths["factor_audit"])
    candidates = pd.read_parquet(paths["candidates"])
    allotment = pd.read_parquet(paths["allotment"])
    audit["blockers"] = audit.blocker_codes_json.map(json.loads)
    target_mask = audit.apply(
        lambda row: bool(row.price_admitted)
        and not bool(row.volume_admitted)
        and bool(set(row.blockers) & TARGET_BLOCKERS),
        axis=1,
    )
    targets = audit[target_mask].copy()
    if len(targets) != 104 or targets.duplicated(["stock_code", "effective_date"]).any():
        raise ValueError("EXPECTED_104_UNIQUE_TARGETS")

    combined = targets.merge(
        candidates,
        on=["stock_code", "effective_date", "official_event_kind"],
        validate="one_to_one",
        suffixes=("_audit", "_candidate"),
    ).merge(
        allotment,
        on=["stock_code", "effective_date", "official_event_kind"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_parse"),
    )
    manifest = load_json(paths["manifest"])
    manifest_results = {
        (item["stock_code"], item["effective_date"], item["official_event_kind"]): item
        for item in manifest["key_results"]
    }
    manifest_files = {item["rcept_no"]: item for item in manifest["files"]}

    key_results: list[dict] = []
    source_hash_failures: list[dict] = []
    dart_hash_failures: list[dict] = []
    for record in combined.sort_values(["stock_code", "effective_date"]).to_dict("records"):
        key = (record["stock_code"], record["effective_date"], record["official_event_kind"])
        manifest_result = manifest_results[key]
        blocker_list = json.loads(record["blocker_codes_json_audit"])
        blocker = next(code for code in blocker_list if code in TARGET_BLOCKERS)
        crosscheck = json.loads(record["allotment_ratio_crosscheck_json"])
        back = decimal_or_none(crosscheck.get("back_computed"))

        krx_sources = []
        for source in json.loads(record["sources_json"]):
            source_path = resolve_ted_path(ted_root, source["path"])
            actual = sha256_path(source_path) if source_path.exists() else None
            verified = actual == source["sha256"]
            item = {
                "path": source["path"].replace("\\", "/"),
                "sha256": source["sha256"],
                "hash_verified": verified,
                "origin": source.get("origin"),
                "official_reason": source.get("official_reason"),
                "event_kind": source.get("event_kind"),
            }
            krx_sources.append(item)
            if not verified:
                source_hash_failures.append({"key": key[:2], **item, "actual_sha256": actual})

        selected_rcept = clean(record.get("rcept_no"))
        raw_inspection = None
        raw_path = None
        raw_verified = None
        if selected_rcept:
            raw_path = dart / "raw/documents" / f"{selected_rcept}.zip"
            expected = clean(record.get("raw_sha256"))
            actual = sha256_path(raw_path) if raw_path.exists() else None
            manifest_expected = manifest_files.get(selected_rcept, {}).get("sha256")
            raw_verified = actual == expected == manifest_expected
            if not raw_verified:
                dart_hash_failures.append(
                    {
                        "key": key[:2],
                        "rcept_no": selected_rcept,
                        "parse_sha256": expected,
                        "manifest_sha256": manifest_expected,
                        "actual_sha256": actual,
                    }
                )
            if raw_path.exists():
                raw_inspection = inspect_raw(raw_path, record["official_event_kind"], back)

        match_details = []
        available_count = 0
        for match in manifest_result.get("matches", []):
            rcept_no = match["rcept_no"]
            candidate_path = dart / "raw/documents" / f"{rcept_no}.zip"
            candidate_manifest = manifest_files.get(rcept_no)
            available = candidate_path.exists() and candidate_manifest is not None
            detail = {**match, "stored_original_available": available}
            if available:
                available_count += 1
                actual = sha256_path(candidate_path)
                detail["stored_original_path"] = rel_ted(candidate_path, ted_root)
                detail["sha256"] = candidate_manifest["sha256"]
                detail["hash_verified"] = actual == candidate_manifest["sha256"]
                detail["raw_fields"] = inspect_raw(candidate_path, record["official_event_kind"], back)
                if not detail["hash_verified"]:
                    dart_hash_failures.append({"key": key[:2], "rcept_no": rcept_no, "actual_sha256": actual})
            match_details.append(detail)

        if manifest_result["status"] == "MATCHED" and raw_inspection is not None:
            raw_scope = "COMPLETE_STORED_MATCHED_ORIGINAL"
        elif available_count:
            raw_scope = "PARTIAL_STORED_CANDIDATE_ORIGINALS"
        else:
            raw_scope = "NO_STORED_ORIGINAL_FOR_TARGET"

        parse_data = {
            "status": clean(record.get("status_parse")),
            "failure_reason": clean(record.get("failure_reason")),
            "extraction_method": clean(record.get("extraction_method")),
            "allotment_ratio": clean(record.get("allotment_ratio")),
            "quantity_ratio": clean(record.get("quantity_ratio")),
            "evidence_snippet": clean(record.get("evidence_snippet")),
        }
        item = {
            "stock_code": record["stock_code"],
            "effective_date": record["effective_date"],
            "official_event_kind": record["official_event_kind"],
            "current_blocker": blocker,
            "admission": {
                "price_admitted": bool(record["price_admitted"]),
                "volume_admitted": bool(record["volume_admitted"]),
                "signal_admitted": bool(record["signal_admitted"]),
                "all_blockers": blocker_list,
            },
            "formula": {
                "anchor_close": clean(record.get("anchor_close")),
                "official_reference_price": clean(record.get("reference_price")),
                "price_back_computed_factor": crosscheck.get("back_computed"),
                "parsed_expected_factor": crosscheck.get("expected_from_allotment"),
                "relative_gap": crosscheck.get("relative_gap"),
                "tolerance": str(TOLERANCE),
            },
            "krx_reference_sources": krx_sources,
            "dart_manifest_match": {
                "status": manifest_result["status"],
                "search_window": manifest_result.get("search_window"),
                "searched_disclosures": manifest_result.get("searched_disclosures"),
                "matches": match_details,
            },
            "dart_selected_original": {
                "rcept_no": selected_rcept,
                "path": rel_ted(raw_path, ted_root) if raw_path else None,
                "sha256": clean(record.get("raw_sha256")),
                "hash_verified": raw_verified,
                "review_scope": raw_scope,
                "raw_fields": raw_inspection,
            },
            "dart_parse": parse_data,
        }
        cause, recovery, unresolved = classify(item, raw_inspection, manifest_result)
        item["cause"] = cause
        item["recovery_candidate"] = recovery
        item["unresolved"] = unresolved
        key_results.append(item)

    critical_failures = [check for check in checks if not check["ok"]]
    if critical_failures or source_hash_failures or dart_hash_failures:
        raise ValueError(
            f"HASH_VERIFICATION_FAILED: critical={len(critical_failures)}, "
            f"krx={len(source_hash_failures)}, dart={len(dart_hash_failures)}"
        )

    actual_counts = {
        "candidate_keys": len(audit),
        "price_admitted": int(audit.price_admitted.sum()),
        "volume_admitted": int(audit.volume_admitted.sum()),
        "both_admitted": int((audit.price_admitted & audit.volume_admitted).sum()),
    }
    expected_counts = {
        "candidate_keys": factor_report["candidate_keys"],
        "price_admitted": factor_report["price_factors_admitted"],
        "volume_admitted": factor_report["volume_factors_admitted"],
        "both_admitted": factor_report["both_factors_admitted"],
    }
    if actual_counts != expected_counts:
        raise ValueError(f"FACTOR_REPORT_COUNT_MISMATCH: {actual_counts} != {expected_counts}")

    cause_counts = dict(sorted(Counter(row["cause"] for row in key_results).items()))
    blocker_counts = dict(sorted(Counter(row["current_blocker"] for row in key_results).items()))
    raw_scope_counts = dict(
        sorted(Counter(row["dart_selected_original"]["review_scope"] for row in key_results).items())
    )
    return {
        "schema": "ohlcv20-allotment-104-audit-v1",
        "purpose": "현재 v2 정책에서 가격은 승인됐지만 배정비율 사유로 거래량이 미승인인 104키의 원문·매칭·산식 감사",
        "conclusion": "104키 모두 현행 거래량 미승인을 유지한다. 복구 후보는 다음 검토 입력일 뿐 자동 승인이나 정책 변경이 아니다.",
        "scope": {
            "ted_root": str(ted_root),
            "network_api_db_used": False,
            "backtest_run": False,
            "source_or_policy_modified": False,
            "independent_admission": False,
            "excluded": "factor-admission-v3 및 미추적 잔여",
        },
        "policy_rule": {
            "source": rel_ted(paths["policy"], ted_root),
            "rule": "DART 원공시의 배정비율 직접 파싱; expected=1+ratio와 back=anchor_close/reference_price의 상대차가 0.005 이하여야 승인",
            "formula": "relative_gap = abs(expected - back) / back",
            "corrections_excluded": True,
        },
        "hash_verification": {
            "all_passed": True,
            "critical_chain_checks": checks,
            "krx_source_files_checked": sum(len(row["krx_reference_sources"]) for row in key_results),
            "krx_source_hash_failures": [],
            "dart_raw_hash_failures": [],
            "generator_sha256": sha256_path(Path(__file__)),
        },
        "factor_counts_reproduced": actual_counts,
        "target_counts": {
            "total": len(key_results),
            "unique_stock_date": len({(row["stock_code"], row["effective_date"]) for row in key_results}),
            "blocker_counts": blocker_counts,
            "cause_counts": cause_counts,
            "raw_review_scope_counts": raw_scope_counts,
        },
        "interpretation_limits": [
            "NO_STORED_ORIGINAL_FOR_TARGET은 원공시 부재나 누락을 뜻하지 않는다.",
            "실효 총주식 계수 후보는 현행 직접 배정비율 정책과 다른 산식이므로 자동 승격하지 않는다.",
            "가격·거래량 계수 승인과 신호·실행 승인은 별개이며 signal_admitted와 real_execution_admitted는 false다.",
        ],
        "keys": key_results,
    }


def render_review(result: dict) -> str:
    counts = result["target_counts"]
    cause_korean = {
        "SEARCH_RESULT_NO_POLICY_TITLE_CANDIDATE": "저장 검색결과에 정책 제목 후보 없음",
        "SEARCH_RESULT_MULTIPLE_POLICY_TITLE_CANDIDATES": "정책 제목 후보 복수",
        "MATCHED_DISCLOSURE_RECORD_DATE_MISMATCH": "유일 후보의 기준일 불일치",
        "ORDINARY_SHARE_RATIO_ABSENT_PREFERRED_ONLY": "보통주 비율 없음·종류주식만 존재",
        "RAW_TABLE_RATIO_FIELD_INCONSISTENT_AND_PARSER_COMMA_TRUNCATION": "원문 표 모순과 콤마 숫자 파서 절단",
        "ELIGIBLE_SHARE_RATIO_DIFFERS_FROM_TOTAL_ISSUED_EFFECTIVE_RATIO": "적격주주 배정비율과 실효 총주식 비율 차이",
        "DIRECT_AND_EFFECTIVE_RATIOS_BOTH_MISMATCH_PRICE_BACKCOMPUTATION": "직접·실효 비율 모두 가격 역산값과 불일치",
        "PARSE_FAILURE_OTHER": "그 밖의 파싱 실패",
    }
    lines = [
        "# 배정비율 104키 원문·매칭·산식 감사",
        "",
        "이 문서는 현재 해시와 일치하는 계수 v2에서 **가격은 승인됐지만 배정비율 때문에 거래량은 미승인인 104키**를 저장 원문으로 전수 감사한다. 결론은 104키 모두 현행 미승인을 유지한다는 것이다. 46건은 원문 주식수로 계산한 실효 총주식 계수가 가격 역산값과 0.5% 안에서 맞지만 현행 직접 배정비율 정책과 다른 산식이고, 나머지도 원문 부족·후보 모호성·기준일 불일치·미해결 산식이 남는다. 아래 복구 후보는 다음 조사 입력이며 승인·원자료 정정·정책 변경이 아니다.",
        "",
        "범위는 로컬에 보존된 DART 원공시 ZIP, 수집 manifest, 파싱 결과, KRX 기준가격 원문, v2 후보·감사 Parquet다. 네트워크/API/DB·백테스트는 사용하지 않았고 ted-startup은 수정하지 않았다. `factor-admission-v3` 잔여는 제외했다.",
        "",
        "## 핵심 결과",
        "",
        f"- 전수성: **{counts['total']} / 104**, 고유 `(stock_code, effective_date)` **{counts['unique_stock_date']} / 104**.",
        f"- 현재 차단: `ALLOTMENT_RATIO_MISMATCH` {counts['blocker_counts'].get('ALLOTMENT_RATIO_MISMATCH', 0)}건, `ALLOTMENT_RATIO_NOT_PARSED` {counts['blocker_counts'].get('ALLOTMENT_RATIO_NOT_PARSED', 0)}건.",
        "- 해시: 정책→파서→수집 manifest/원문→후보→v2 감사 체인과 104키 KRX 원문·저장 DART ZIP의 SHA-256 대조를 모두 통과했다.",
        f"- 원문 대조 범위: 완전 저장 원공시 {counts['raw_review_scope_counts'].get('COMPLETE_STORED_MATCHED_ORIGINAL', 0)}키, 복수 후보 중 일부 원문만 저장 {counts['raw_review_scope_counts'].get('PARTIAL_STORED_CANDIDATE_ORIGINALS', 0)}키, 해당 키 원문 미저장 {counts['raw_review_scope_counts'].get('NO_STORED_ORIGINAL_FOR_TARGET', 0)}키.",
        "- 실행 상태: 거래량 미승인 유지, `signal_admitted=false`, `real_execution_admitted=false`; 실행·성과 수치는 만들지 않았다.",
        "",
        "원문 미저장은 공시가 없었다거나 수집에서 누락됐다는 뜻이 아니다. 저장된 120일 검색 결과와 정책 제목 필터만으로는 원인을 확정할 수 없다는 뜻이다.",
        "",
        "## 원인 분류",
        "",
        "| 원인 | 건수 | 판단과 다음 확인 |",
        "| --- | ---: | --- |",
    ]
    for cause, count in counts["cause_counts"].items():
        descriptions = {
            "ELIGIBLE_SHARE_RATIO_DIFFERS_FROM_TOTAL_ISSUED_EFFECTIVE_RATIO": "원공시의 신주/배당주식수 ÷ 전체 발행주식수 계수는 가격 역산값과 0.5% 안에서 맞는다. 자기주식 제외·단수주 절사와 정합적이지만 현행 정책 산식이 아니므로 차단 유지.",
            "RAW_TABLE_RATIO_FIELD_INCONSISTENT_AND_PARSER_COMMA_TRUNCATION": "208340/2020-06-30은 1주당 표 칸이 신주 총수와 같은 6,910,809이고 서술은 1주당 1주다. 파서는 콤마 앞 6만 읽었다. 원문 내부 모순과 파서 문제를 함께 해결해야 함.",
            "DIRECT_AND_EFFECTIVE_RATIOS_BOTH_MISMATCH_PRICE_BACKCOMPUTATION": "직접 비율뿐 아니라 원문 총주식수 기반 계수도 0.5%를 넘는다. 기준가격 산식·anchor·복합행사를 별도 감사해야 함.",
            "SEARCH_RESULT_NO_POLICY_TITLE_CANDIDATE": "저장 검색 결과에서 비정정 정책 제목 후보가 0건이다. 원공시 부재/누락으로 단정하지 않고 검색·기업코드·명칭 범위를 재감사해야 함.",
            "SEARCH_RESULT_MULTIPLE_POLICY_TITLE_CANDIDATES": "원공시 제목 후보가 2건이라 수집기가 선택하지 않았다. 모든 후보 원문과 기준일을 확보하기 전 선택 금지.",
            "MATCHED_DISCLOSURE_RECORD_DATE_MISMATCH": "유일 제목 후보의 원문 기준일이 목표 effective date 허용 범위와 맞지 않아 다른 사건으로 판정됨.",
            "ORDINARY_SHARE_RATIO_ABSENT_PREFERRED_ONLY": "원문 보통주 칸은 '-'이고 종류주식 0.15만 있다. 종류주식 값을 보통주에 대입하지 않음.",
            "PARSE_FAILURE_OTHER": "현재 저장 원문과 파싱 근거로 확정할 수 없음.",
        }
        lines.append(f"| {cause_korean.get(cause, cause)} (`{cause}`) | {count} | {descriptions[cause]} |")

    lines.extend(
        [
            "",
            "## 산식 감사",
            "",
            "현행 정책 비교는 `expected = 1 + DART 1주당 배정비율`, `back = anchor_close / KRX 공식 기준가격`, `gap = abs(expected - back) / back`이며 `gap <= 0.005`만 승인한다. 이 기준으로 50건이 불일치했다.",
            "",
            "50건 중 일반형 45건은 공시의 1주당 배정비율이 배정 대상 주식에 적용된 값인 반면, `1 + 신주(또는 배당주식) 총수 / 행사 전 발행주식총수`는 가격 역산값과 0.5% 안에서 맞았다. 구형 서식인 060720/2015-03-12도 이 45건에 포함된다. 이는 자기주식 제외나 단수주 처리로 설명 가능한 복구 후보지만 현행 정책이 요구하는 직접 비교를 바꾸므로 자동 승격할 수 없다.",
            "",
            "`208340/2020-06-30`은 별도 원인 1건이다. 원공시 표의 '1주당 신주배정 주식수'에 `6,910,809`가 들어가 신주 총수와 같고, 본문 서술은 1주당 1주다. 기존 파서는 콤마 숫자의 앞부분 `6`을 배정비율로 기록했다. 본문 1과 총주식 계수 2는 가격 역산 2와 맞지만 원문 표 자체가 모순이어서 원자료를 고쳐 덮어쓰지 않고 차단을 유지한다. 따라서 실효 총주식 계수가 0.5% 안에서 맞는 건수는 일반형 45건과 이 특이 1건을 합친 46건이며, 208340을 다시 더하지 않는다.",
            "",
            "나머지 4건(`089030/2022-08-01`, `097780/2017-05-30`, `131970/2020-09-15`, `137400/2019-05-07`)은 원문 총주식수 계수도 0.5%를 넘었다. 저장 자료만으로 기준가격 차이를 확정 설명할 수 없어 KRX 산식·anchor·동시 기업행사 감사를 남긴다.",
            "",
            "## 키별 판정",
            "",
            "상세 수치·공시번호·원문 경로·SHA-256·필드·snippet은 `allotment-104-audit.json`에 있다.",
            "",
            "| 키 | 종류 | 현재 차단 | 원인 | 원문 범위 | 복구 후보 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in result["keys"]:
        recovery = "있음(재심사 필요)" if row["recovery_candidate"]["possible"] else "확정 후보 없음"
        lines.append(
            f"| {row['stock_code']}/{row['effective_date']} | {row['official_event_kind']} | "
            f"{row['current_blocker']} | {cause_korean.get(row['cause'], row['cause'])} | "
            f"{row['dart_selected_original']['review_scope']} | {recovery} |"
        )

    lines.extend(
        [
            "",
            "## 재실행과 한계",
            "",
            "저장 원문이 그대로인 환경에서 새 출력 디렉터리에 JSON과 이 문서를 다시 만든다. 기존 출력이 있으면 기본적으로 거절한다.",
            "",
            "```powershell",
            ".venv\\Scripts\\python.exe -B scripts\\research\\audit_ohlcv20_allotment104.py --ted-root C:\\Users\\aeby\\vscode\\ted-startup --output-dir docs/strategy-research/backtest-lab/ohlcv20-factor-v2-intake-2026-09-23/allotment-new",
            "```",
            "",
            "스크립트는 104 고유키, v2의 733/643/539/539 집계, 모든 핵심·원문 해시를 검증하고 불일치하면 산출 전에 실패한다. 결과는 독립 승인 영수증이 아니며, 복구 후보를 적용하려면 ted-startup에서 원문 연결·정책·파서를 별도 검토하고 새 불변 revision으로 전달해야 한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ted-root", type=Path, default=DEFAULT_TED_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--overwrite", action="store_true", help="Explicitly replace this audit's two generated files")
    args = parser.parse_args()
    names = ("allotment-104-audit.json", "allotment-104-review.md")
    if not args.overwrite and any((args.output_dir / name).exists() for name in names):
        raise FileExistsError("Refusing to overwrite an earlier allotment audit; use a new --output-dir")
    result = build_audit(args.ted_root.resolve())
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "allotment-104-audit.json"
    review_path = args.output_dir / "allotment-104-review.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    review_path.write_text(render_review(result), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "targets": result["target_counts"]["total"],
                "blockers": result["target_counts"]["blocker_counts"],
                "causes": result["target_counts"]["cause_counts"],
                "json": str(json_path),
                "review": str(review_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
