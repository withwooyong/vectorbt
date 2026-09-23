"""Render read-only comparison charts from a final extension experiment report.

The input is the directory created by ``report_extension_experiments.py``.
It never calculates performance or fills missing values: incomplete comparison
sets simply produce no chart for that section.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


MONTHS = (1, 3, 6)
FAMILIES = ("basic", "wide")
CONTINUOUS = "continuous_2020_2023"


def _read(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"EXPECTED_JSON_LIST: {path}")
    return value


def _continuous_duration_cells(rows: list[dict]) -> dict[tuple[str, int], dict]:
    cells = {}
    for family in FAMILIES:
        for months in MONTHS:
            values = [row for row in rows if row.get("family") == family and row.get("months") == months
                      and row.get("window") == CONTINUOUS and isinstance(row.get("matched"), int)
                      and row["matched"] > 0 and row.get("mean_return") is not None]
            if len(values) != 1:
                continue
            row = values[0]
            cells[family, months] = {
                "value": float(row["mean_return"]),
                "denominator": row["matched"],
            }
    return cells


def _four_year_duration_cells(rows: list[dict]) -> dict[tuple[str, int], dict]:
    """Use only the report's fixed cohorts with all 1/3/6-month four-year runs."""
    cells = {}
    for row in rows:
        key = row.get("family"), row.get("months")
        if key[0] not in FAMILIES or key[1] not in MONTHS:
            continue
        if not isinstance(row.get("matched_strategies"), int) or row["matched_strategies"] < 1:
            continue
        if row.get("mean_annual_return") is None or row.get("mean_worst_annual_mdd") is None:
            continue
        if key in cells:
            raise ValueError(f"DUPLICATE_FOUR_YEAR_DURATION_CELL: {key}")
        cells[key] = {"value": float(row["mean_annual_return"]), "denominator": row["matched_strategies"],
                      "mdd": float(row["mean_worst_annual_mdd"])}
    return cells


def _draw_duration(duration_rows: list[dict], four_year_rows: list[dict], out: Path,
                   formats: tuple[str, ...]) -> list[Path]:
    continuous = _continuous_duration_cells(duration_rows)
    annual = _four_year_duration_cells(four_year_rows)
    if not continuous and not annual:
        return []
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True, constrained_layout=True)
    panels = (
        (axes[0], continuous, "Cumulative return: continuous 2020–2023", "matched strategy combinations"),
        (axes[1], annual, "Mean annual return: fixed 2020–2023 cohorts", "matched strategies; all four years"),
    )
    colors = {1: "#4C78A8", 3: "#F58518", 6: "#54A24B"}
    for axis, cells, title, denominator_label in panels:
        positions = np.arange(len(FAMILIES))
        width = 0.22
        for offset, months in zip((-width, 0, width), MONTHS, strict=True):
            values, labels = [], []
            for family in FAMILIES:
                cell = cells.get((family, months))
                values.append(np.nan if cell is None else cell["value"])
                labels.append("" if cell is None else f"n={cell['denominator']}")
            bars = axis.bar(positions + offset, values, width, label=f"{months} months", color=colors[months])
            for bar, label in zip(bars, labels, strict=True):
                if label:
                    axis.annotate(label, (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                                  xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8)
        axis.axhline(0, color="#555555", linewidth=0.8)
        axis.set_xticks(positions, [name.title() for name in FAMILIES])
        axis.set_title(title)
        axis.set_ylabel("Mean total return" if axis is axes[0] else "")
        axis.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
        axis.text(0.5, -0.19, f"Denominator: {denominator_label}", transform=axis.transAxes,
                  ha="center", fontsize=8)
    axes[0].legend(title="Maximum holding")
    figure.suptitle("Matched-cohort holding-duration comparison", fontsize=14)
    return _save(figure, out / "duration-comparison", formats)


def _draw_hypotheses(rows: list[dict], out: Path, formats: tuple[str, ...]) -> list[Path]:
    rows = [row for row in rows if row.get("window") == CONTINUOUS and row.get("matched", 0) > 0
            and row.get("control_total_return") is not None and row.get("treatment_total_return") is not None]
    if not rows:
        return []
    labels = [f"{row['family']}\n{row['months']}m\nn={row['matched']}" for row in rows]
    positions = np.arange(len(rows))
    figure, axis = plt.subplots(figsize=(max(8, len(rows) * 1.25), 5), constrained_layout=True)
    width = 0.36
    control = [float(row["control_total_return"]) for row in rows]
    treatment = [float(row["treatment_total_return"]) for row in rows]
    axis.bar(positions - width / 2, control, width, label="Matched control", color="#9D755D")
    axis.bar(positions + width / 2, treatment, width, label="New hypothesis", color="#59A14F")
    axis.axhline(0, color="#555555", linewidth=0.8)
    axis.set_xticks(positions, labels)
    axis.set_ylabel("Mean cumulative total return")
    axis.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    axis.set_title("Continuous 2020–2023 matched control versus hypothesis")
    axis.legend()
    axis.text(0.5, -0.2, "Each label reports its matched comparison denominator; blocked runs are excluded.",
              transform=axis.transAxes, ha="center", fontsize=8)
    return _save(figure, out / "hypothesis-comparison", formats)


def _save(figure, stem: Path, formats: tuple[str, ...]) -> list[Path]:
    paths = []
    for extension in formats:
        path = stem.with_suffix("." + extension)
        figure.savefig(path, dpi=180 if extension == "png" else None, bbox_inches="tight")
        paths.append(path)
    plt.close(figure)
    return paths


def build_charts(report_dir, out=None, *, svg: bool = False) -> dict:
    """Build available charts and return their paths; an empty report is valid input."""
    report_dir = Path(report_dir)
    out = Path(out) if out is not None else report_dir / "charts"
    out.mkdir(parents=True, exist_ok=True)
    duration = _read(report_dir / "duration-comparison.json")
    four_year_duration = _read(report_dir / "duration-four-year-matched.json")
    hypotheses = _read(report_dir / "hypothesis-comparison.json")
    # Read the flat artifact too: its presence catches accidental use against a partial report.
    strategies = _read(report_dir / "all-strategies.json")
    if not strategies and (duration or hypotheses):
        raise ValueError("MISSING_ALL_STRATEGIES_FOR_COMPARISON")
    formats = ("png", "svg") if svg else ("png",)
    paths = [*_draw_duration(duration, four_year_duration, out, formats), *_draw_hypotheses(hypotheses, out, formats)]
    return {"status": "EMPTY" if not paths else "CREATED", "charts": [str(path) for path in paths]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_dir")
    parser.add_argument("--out")
    parser.add_argument("--svg", action="store_true")
    args = parser.parse_args()
    print(build_charts(args.report_dir, args.out, svg=args.svg))
