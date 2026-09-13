"""SSH/psql 읽기 전용 추출. 시세는 청크로 저장하고 잠금 구간은 기본 제외한다."""

from datetime import date, datetime, timezone
from pathlib import Path
import subprocess

import pandas as pd

from .io import digest, read_json, write_json
from .quality import audit


def export_sql(start, end):
    start, end = date.fromisoformat(start), date.fromisoformat(end)
    if start > end:
        raise ValueError("날짜 범위 역전")
    return f"""\\set ON_ERROR_STOP on
BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout='300s';
SET LOCAL lock_timeout='3s';
COPY (
 SELECT p.trading_date AS date, s.stock_code AS code, p.stock_id,
 p.open_price AS open, p.high_price AS high, p.low_price AS low,
 p.close_price AS close, p.trade_volume AS volume,
 p.adjusted, p.data_vendor, s.market_code AS current_market_code,
 s.is_active AS current_is_active
 FROM kiwoom.stock_price_krx p JOIN kiwoom.stock s ON s.id=p.stock_id
 WHERE p.adjusted AND p.trading_date BETWEEN '{start}' AND '{end}'
 ORDER BY s.stock_code,p.trading_date,p.stock_id
) TO STDOUT WITH (FORMAT CSV, HEADER TRUE, ENCODING 'UTF8');
COMMIT;
"""


def extract(out, start="2015-01-02", end="2023-12-31"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    sql = export_sql(start, end)
    (out / "extract.sql").write_text(sql, encoding="utf-8")
    manifest = {"schema_version": "snapshot-v1", "source": "PostgreSQL:ssh-home/kiwoom_db",
                "created_at": datetime.now(timezone.utc).isoformat(), "start": start, "end": end,
                "read_only": True, "price_basis": "adjusted", "price_semantics_evidence": None,
                "mixed_vendors": True, "status": "EXTRACTING", "parts": [], "rows": 0,
                "sql_sha256": digest(out / "extract.sql"), "holdout_prices_included": end >= "2024-01-01"}
    write_json(out / "manifest.json", manifest)
    command = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "home",
               "docker exec -i -e PGCLIENTENCODING=UTF8 kiwoom-db psql -X -q -U kiwoom -d kiwoom_db"]
    codes, invalid_codes, vendors = set(), set(), {}
    counts = {"rows": 0, "duplicate_keys": 0, "invalid_date_rows": 0,
              "invalid_ohlcv_rows": 0, "zero_volume_rows": 0}
    reasons = set()
    previous_key = None
    observed_first, observed_last = None, None
    try:
        with (out / "extract.stderr.txt").open("wb") as stderr:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
            try:
                process.stdin.write(sql.encode("utf-8"))
                process.stdin.close()
                for index, frame in enumerate(pd.read_csv(process.stdout, chunksize=100000,
                                                          dtype={"code": "string", "current_market_code": "string"})):
                    check = audit(frame, manifest)
                    observed_first = min(observed_first or check["first_date"], check["first_date"])
                    observed_last = max(observed_last or check["last_date"], check["last_date"])
                    for key in counts:
                        counts[key] += check[key]
                    first_key = tuple(frame.iloc[0][["code", "date"]])
                    if previous_key == first_key:
                        counts["duplicate_keys"] += 1
                        reasons.add("INVALID_KEYS")
                    previous_key = tuple(frame.iloc[-1][["code", "date"]])
                    codes.update(frame["code"].unique())
                    # This diagnostic does not remove any rows.
                    for code, group in frame.groupby("code", observed=True):
                        if audit(group, manifest)["invalid_ohlcv_rows"]:
                            invalid_codes.add(code)
                    for vendor, count in frame["data_vendor"].value_counts(dropna=False).items():
                        vendors[str(vendor)] = vendors.get(str(vendor), 0) + int(count)
                    reasons.update(check["reasons"])
                    part = out / f"prices-{index:04d}.parquet"
                    frame.to_parquet(part, index=False)
                    manifest["parts"].append({"file": part.name, "rows": len(frame), "sha256": digest(part)})
                    manifest["rows"] += len(frame)
                    print(f"snapshot: {manifest['rows']:,} rows", flush=True)
                if process.wait(timeout=30) != 0:
                    raise RuntimeError("SSH/psql 추출 실패: extract.stderr.txt 참조")
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait()
        if not manifest["rows"]:
            reasons.add("EMPTY_SNAPSHOT")
        result = {**counts, "grade": "BLOCKED", "reasons": sorted(reasons), "symbols": len(codes),
                  "invalid_ohlcv_symbols": len(invalid_codes), "vendor_rows": vendors,
                  "limitations": audit(pd.DataFrame(columns=["date", "code", "open", "high", "low", "close", "volume"]),
                                       manifest)["limitations"], "first_date": observed_first,
                  "last_date": observed_last, "requested_start": start, "requested_end": end}
        write_json(out / "quality.json", result)
        manifest.update(status="COMPLETE", quality_sha256=digest(out / "quality.json"))
        write_json(out / "manifest.json", manifest)
        return manifest
    except Exception as exc:
        manifest.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        write_json(out / "manifest.json", manifest)
        raise


def verify_snapshot(path):
    path = Path(path)
    manifest = read_json(path / "manifest.json")
    if manifest["status"] != "COMPLETE":
        raise ValueError("스냅샷 미완료")
    for part in manifest["parts"]:
        target = path / part["file"]
        if target.parent.resolve() != path.resolve() or digest(target) != part["sha256"]:
            raise ValueError("스냅샷 손상 또는 경로 이탈")
    if digest(path / "quality.json") != manifest["quality_sha256"]:
        raise ValueError("품질 검사 손상")
    return manifest, read_json(path / "quality.json")


def load_prices(path, end=None):
    path = Path(path)
    manifest, _ = verify_snapshot(path)
    frames = []
    for part in manifest["parts"]:
        frame = pd.read_parquet(path / part["file"])
        frame["date"] = pd.to_datetime(frame["date"])
        if end is not None:
            frame = frame[frame["date"] <= pd.Timestamp(end)]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def synthetic_snapshot(out):
    """난수 seed를 고정한 엔진 검증 자료. 시장 성과로 해석하지 않는다."""
    import numpy as np
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    rng = np.random.default_rng(20260913)
    days = pd.bdate_range("2015-01-02", "2023-12-29")
    frames = []
    for j in range(8):
        close = 10000 * np.exp(np.cumsum(rng.normal(0.0003, 0.018, len(days))))
        open_price = np.r_[close[0], close[:-1]] * np.exp(rng.normal(0, 0.004, len(days)))
        frames.append(pd.DataFrame({"date": days, "code": f"SYN{j:03d}", "open": open_price,
                                    "high": np.maximum(open_price, close) * 1.012,
                                    "low": np.minimum(open_price, close) * .988, "close": close,
                                    "volume": 2000000, "sector": f"sector{j % 4}",
                                    "tick_size": 1.0, "eligible": True}))
    prices = pd.concat(frames, ignore_index=True)
    prices.to_parquet(out / "prices-0000.parquet", index=False)
    manifest = {"schema_version": "snapshot-v1", "source": "SYNTHETIC", "status": "COMPLETE",
                "created_at": datetime.now(timezone.utc).isoformat(), "rows": len(prices),
                "parts": [{"file": "prices-0000.parquet", "rows": len(prices),
                           "sha256": digest(out / "prices-0000.parquet")}],
                "calendar": [str(x.date()) for x in days], "holdout_prices_included": False}
    write_json(out / "quality.json", audit(prices, manifest))
    manifest["quality_sha256"] = digest(out / "quality.json")
    write_json(out / "manifest.json", manifest)
    return manifest
