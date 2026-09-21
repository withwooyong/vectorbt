"""Render the descriptive v3 basic-versus-wide exit comparison heatmap.

The chart is intentionally a small standalone consumer of a completed batch.
It admits metrics only after the batch smoke oracle passes and the execution
admission receipt is present; incomplete entry/exit pairs remain missing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

# Keep the documented direct-file CLI usable from any working directory.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from research.krx_lab.v3_report import _PAIRS, _full_validation


ENTRY_IDS = (
    "CROSS_5_20", "CROSS_10_20", "BREAKOUT_20", "BREAKOUT_60",
    "TREND_PULLBACK_3", "TREND_PULLBACK_5", "RSI_REENTRY_30", "RSI_REENTRY_40",
    "BOLLINGER_REENTRY_1_5", "BOLLINGER_REENTRY_2", "MACD_CROSS_SMA60",
    "MACD_CROSS_SMA120", "BREAKOUT_20_RVOL_1_5", "BREAKOUT_60_RVOL_1_5",
)
ENTRY_LABELS = {
    "CROSS_5_20": "이평 교차 5/20", "CROSS_10_20": "이평 교차 10/20",
    "BREAKOUT_20": "돌파 20일", "BREAKOUT_60": "돌파 60일",
    "TREND_PULLBACK_3": "추세 눌림 3", "TREND_PULLBACK_5": "추세 눌림 5",
    "RSI_REENTRY_30": "RSI 재진입 30", "RSI_REENTRY_40": "RSI 재진입 40",
    "BOLLINGER_REENTRY_1_5": "볼린저 재진입 1.5", "BOLLINGER_REENTRY_2": "볼린저 재진입 2",
    "MACD_CROSS_SMA60": "MACD 교차 SMA60", "MACD_CROSS_SMA120": "MACD 교차 SMA120",
    "BREAKOUT_20_RVOL_1_5": "돌파 20일 RVOL 1.5", "BREAKOUT_60_RVOL_1_5": "돌파 60일 RVOL 1.5",
}
EXIT_LABELS = ("3/6→8/16", "5/10→10/20", "ATR1.5/3→3/6", "ATR2/4→4/8")
LIMITATION_TEXT = "독립 연도별 1억원 창, 현금배당 제외, 소급 1,076종목 코호트, 색상은 서술적 비교만 표시"
SUBTITLE = "2020~2023 매년 1억 원 별도 실행 · 배당 제외 · 사후 선정 1,076종목"
ENTRY_LABELS_ASCII = {entry: entry.replace("_", " ") for entry in ENTRY_IDS}


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _font_name() -> str:
    names = {font_manager.FontProperties(fname=p).get_name() for p in font_manager.findSystemFonts()}
    return "Malgun Gothic" if "Malgun Gothic" in names else "DejaVu Sans"


def _admit_rows(batch: Path) -> list[dict]:
    smoke_path = batch / "smoke-oracle.json"
    receipt_path = batch / "execution-admission.json"
    if not smoke_path.is_file() or _read_json(smoke_path).get("status") != "PASS":
        raise ValueError("chart metrics require smoke-oracle.json status PASS")
    if not receipt_path.is_file():
        raise ValueError("chart metrics require execution-admission.json")
    summary_path = batch / "summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(summary_path)
    return list((_read_json(summary_path).get("results") or []))


def _fixture_label(batch: Path) -> str | None:
    summary = _read_json(batch / "summary.json")
    return summary.get("fixture_label")


def chart_data(batch_dir: str | Path) -> dict:
    """Return the exact 14-by-4 percentage-point matrix used by the chart."""
    batch = Path(batch_dir)
    complete = {(item["family"], item["entry_id"], item["exit_id"]): item
                for item in _full_validation(_admit_rows(batch))}
    cells: list[list[float | None]] = []
    pair_counts: list[list[int]] = []
    for entry in ENTRY_IDS:
        row, counts = [], []
        for basic_exit, wide_exit in _PAIRS.items():
            basic = complete.get(("basic", entry, basic_exit))
            wide = complete.get(("wide", entry, wide_exit))
            if basic is None or wide is None:
                row.append(None)
                counts.append(0)
            else:
                row.append((wide["avg_return"] - basic["avg_return"]) * 100.0)
                counts.append(4)
        cells.append(row)
        pair_counts.append(counts)
    return {
        "entry_ids": list(ENTRY_IDS), "entry_labels": [ENTRY_LABELS[x] for x in ENTRY_IDS],
        "exit_labels": list(EXIT_LABELS), "values_percentage_points": cells,
        "year_counts": pair_counts, "complete_pair_count": sum(x == 4 for row in pair_counts for x in row),
        "limitations": LIMITATION_TEXT, "color_meaning": "wide 평균 연도별 수익률 - basic 평균 연도별 수익률 (percentage points)",
        "fixture_label": _fixture_label(batch),
    }


def generate_chart(batch_dir: str | Path, out_dir: str | Path) -> dict[str, str]:
    """Create PNG, SVG, and exact plotted-data JSON without overwriting."""
    out = Path(out_dir)
    if out.exists():
        raise FileExistsError(out)
    data = chart_data(batch_dir)
    out.mkdir(parents=True, exist_ok=False)
    (out / "v3-comparison-data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    values = np.asarray(data["values_percentage_points"], dtype=float)
    masked = np.ma.masked_invalid(values)
    cmap = matplotlib.colormaps["RdBu_r"].copy()
    cmap = cmap.with_extremes(bad="#b7b7b7") if hasattr(cmap, "with_extremes") else cmap
    if not hasattr(cmap, "with_extremes"):
        cmap.set_bad("#b7b7b7")
    vmax = max(float(np.nanmax(np.abs(values))) if np.isfinite(values).any() else 1.0, 1.0)
    font = _font_name()
    plt.rcParams["font.family"] = font
    plt.rcParams["axes.unicode_minus"] = False
    labels = data["entry_labels"] if font == "Malgun Gothic" else [ENTRY_LABELS_ASCII[x] for x in data["entry_ids"]]
    fixture_suffix = " · SYNTHETIC" if data.get("fixture_label") == "SYNTHETIC" else ""
    fig, ax = plt.subplots(figsize=(12.5, 8.5), constrained_layout=True)
    image = ax.imshow(masked, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")
    ax.set_xticks(range(4), data["exit_labels"])
    ax.set_yticks(range(14), labels)
    ax.set_xlabel("기본 청산 → 넓은 청산 대응")
    ax.set_title("청산 폭을 넓혔을 때 수익률 차이" + fixture_suffix, fontsize=15, pad=18)
    ax.text(0.5, 1.01, SUBTITLE, transform=ax.transAxes,
            ha="center", va="bottom", fontsize=9)
    for i in range(14):
        for j in range(4):
            value = values[i, j]
            if np.isfinite(value):
                ax.text(j, i, f"{value:+.2f}", ha="center", va="center", fontsize=8,
                        color="black" if abs(value) < vmax * .55 else "white")
    colorbar = fig.colorbar(image, ax=ax, shrink=0.82, pad=0.02)
    colorbar.set_label("차이 (percentage points)")
    ax.text(0, -0.12, "양수: 넓은 청산 우세 / 음수: 기본 청산 우세 / 회색: 4개 연도 비교 불가",
            transform=ax.transAxes, ha="left", va="top", fontsize=7, wrap=True)
    png, svg = out / "v3-comparison-heatmap.png", out / "v3-comparison-heatmap.svg"
    fig.savefig(png, dpi=180)
    fig.savefig(svg)
    plt.close(fig)
    return {"png": str(png), "svg": str(svg), "data": str(out / "v3-comparison-data.json")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Render v3 basic-versus-wide exit comparison heatmap")
    parser.add_argument("--batch", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    print(json.dumps(generate_chart(args.batch, args.out), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
