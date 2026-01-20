#!/usr/bin/env python3
"""Figure 4: Paired analysis (b/c scatter) vs Run-Full.

Facets:
- Rows: dataset (SWE-bench Lite / Verified)
- Cols: agent (Claude Code / Codex)

Points:
- Modes compared against run_full: run_free, run_less_k1, run_less_k3, run_cost

Definitions (instance-level, from sb-cli-reports resolved_ids):
- b = #instances solved by mode but not by full
- c = #instances solved by full but not by mode

Plot:
- X=b, Y=c
- Diagonal y=x indicates symmetry.

Run:
  python figures/fig4_paired_bc_scatter.py

Output:
  figures/fig4_paired_bc_scatter.png
  figures/fig4_paired_bc_scatter.pdf
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox


MODE_ORDER = ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"]
COMPARE_MODES = ["run_free", "run_less_k1", "run_less_k3", "run_cost"]

MODE_LABEL = {
    "run_free": "Free",
    "run_less_k1": "Less-K1",
    "run_less_k3": "Less-K3",
    "run_cost": "Cost",
    "run_full": "Full",
}

AGENT_ORDER = ["claude_code", "codex"]
AGENT_LABEL = {"claude_code": "Claude Code", "codex": "Codex"}

DATASET_ORDER = ["swebenchlite", "swebenchverified"]
DATASET_LABEL = {"swebenchlite": "SWE-bench Lite", "swebenchverified": "SWE-bench Verified"}


@dataclass(frozen=True)
class Report:
    completed_ids: list[str]
    completed_set: set[str]
    resolved_set: set[str]


@dataclass(frozen=True)
class BCPoint:
    mode: str
    b: int
    c: int


def _detect_dataset(filename_lower: str) -> str | None:
    if "swe-bench_lite" in filename_lower:
        return "swebenchlite"
    if "swe-bench_verified" in filename_lower:
        return "swebenchverified"
    return None


def load_reports(reports_dir: Path) -> dict:
    data: dict = {d: {a: {} for a in AGENT_ORDER} for d in DATASET_ORDER}

    for path in sorted(reports_dir.glob("*.json")):
        name = path.name.lower()
        dataset = _detect_dataset(name)
        if dataset is None:
            continue

        agent = next((a for a in AGENT_ORDER if a in name), None)
        if agent is None:
            continue

        mode = next((m for m in MODE_ORDER if m in name), None)
        if mode is None:
            continue

        report = json.loads(path.read_text(encoding="utf-8"))

        completed_ids = report.get("completed_ids")
        resolved_ids = report.get("resolved_ids")

        if not isinstance(completed_ids, list):
            raise KeyError(f"Missing or invalid 'completed_ids' in {path}")
        if not isinstance(resolved_ids, list):
            raise KeyError(f"Missing or invalid 'resolved_ids' in {path}")

        if mode in data[dataset][agent]:
            raise ValueError(f"Duplicate report for {dataset}/{agent}/{mode}: {path}")

        data[dataset][agent][mode] = Report(
            completed_ids=list(completed_ids),
            completed_set=set(completed_ids),
            resolved_set=set(resolved_ids),
        )

    missing = []
    for dataset in DATASET_ORDER:
        for agent in AGENT_ORDER:
            for mode in MODE_ORDER:
                if mode not in data[dataset][agent]:
                    missing.append(f"{dataset}/{agent}/{mode}")
    if missing:
        raise FileNotFoundError(
            "Missing sb-cli report(s) for: " + ", ".join(missing) + f". reports_dir={reports_dir}"
        )

    return data


def compute_bc(mode_rep: Report, full_rep: Report) -> tuple[int, int]:
    # Pairing reference: run_full completed_ids.
    # If an id is missing in mode completed_ids, treat it as failure (not resolved).
    ids = list(full_rep.completed_ids)

    mode_resolved = set(i for i in ids if i in mode_rep.completed_set and i in mode_rep.resolved_set)
    full_resolved = set(i for i in ids if i in full_rep.resolved_set)

    b = len(mode_resolved - full_resolved)
    c = len(full_resolved - mode_resolved)
    return b, c


def _bbox_overlap_area(a: Bbox, b: Bbox) -> float:
    x0 = max(a.x0, b.x0)
    x1 = min(a.x1, b.x1)
    y0 = max(a.y0, b.y0)
    y1 = min(a.y1, b.y1)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    return float((x1 - x0) * (y1 - y0))


def _marker_bbox(ax, fig, x: float, y: float, s: float) -> Bbox:
    # Matplotlib scatter size `s` is area in points^2.
    r_points = math.sqrt(max(s, 1.0) / math.pi)
    r_px = r_points * fig.dpi / 72.0
    cx, cy = ax.transData.transform((x, y))
    return Bbox.from_bounds(cx - r_px, cy - r_px, 2 * r_px, 2 * r_px)


def place_labels(ax, fig, renderer, points: list[BCPoint], point_size: float, fontsize: int) -> None:
    """Place labels with simple collision avoidance (no extra deps).

    We brute-force all candidate offset combinations (only 4 labels per subplot).
    """

    if not points:
        return

    # Candidate offsets in points.
    candidates = [
        (8, 8),
        (8, 16),
        (16, 8),
        (16, 16),
        (-8, 8),
        (-8, 16),
        (-16, 8),
        (-16, 16),
        (8, -8),
        (8, -16),
        (16, -8),
        (16, -16),
        (-8, -8),
        (-8, -16),
        (-16, -8),
        (-16, -16),
        (0, 22),
        (0, -22),
        (22, 0),
        (-22, 0),
        (28, 14),
        (-28, 14),
        (28, -14),
        (-28, -14),
    ]

    ax_bbox = ax.get_window_extent(renderer)

    marker_bboxes = [
        _marker_bbox(ax, fig, float(p.b), float(p.c), float(point_size)) for p in points
    ]

    labels = [f"{MODE_LABEL.get(p.mode, p.mode)} ({p.b},{p.c})" for p in points]

    # Precompute bboxes for every (point, candidate).
    cand_bboxes: list[list[tuple[int, int, str, str, Bbox]]] = []
    for p, label in zip(points, labels):
        per_point: list[tuple[int, int, str, str, Bbox]] = []
        for dx, dy in candidates:
            ha = "left" if dx >= 0 else "right"
            va = "bottom" if dy >= 0 else "top"
            txt = ax.annotate(
                label,
                (p.b, p.c),
                textcoords="offset points",
                xytext=(dx, dy),
                ha=ha,
                va=va,
                fontsize=fontsize,
                color="black",
                zorder=4,
                clip_on=True,
            )
            bb = txt.get_window_extent(renderer)
            txt.remove()
            per_point.append((dx, dy, ha, va, bb))
        cand_bboxes.append(per_point)

    best_score: float | None = None
    best_choice: list[tuple[int, int, str, str]] | None = None

    def score_choice(choice: list[tuple[int, int, str, str]], bboxes: list[Bbox]) -> float:
        score = 0.0

        # Penalize leaving the axes.
        for bb in bboxes:
            if not (ax_bbox.contains(bb.x0, bb.y0) and ax_bbox.contains(bb.x1, bb.y1)):
                score += 1e9

        # Label-label overlaps.
        for i in range(len(bboxes)):
            for j in range(i + 1, len(bboxes)):
                score += 1000.0 * _bbox_overlap_area(bboxes[i], bboxes[j])

        # Label-marker overlaps.
        for bb in bboxes:
            for mb in marker_bboxes:
                score += 10.0 * _bbox_overlap_area(bb, mb)

        # Prefer closer labels (small tie-breaker).
        for dx, dy, _ha, _va in choice:
            score += 0.2 * (abs(dx) + abs(dy))

        return score

    # Brute-force all combinations (<= 24^4 = 331k).
    n = len(points)

    # Nested loops are fine since n is fixed and small.
    for c0 in range(len(cand_bboxes[0])):
        for c1 in range(len(cand_bboxes[1])):
            for c2 in range(len(cand_bboxes[2])):
                for c3 in range(len(cand_bboxes[3])):
                    idxs = [c0, c1, c2, c3]
                    choice = []
                    bbs = []
                    for i, ci in enumerate(idxs):
                        dx, dy, ha, va, bb = cand_bboxes[i][ci]
                        choice.append((dx, dy, ha, va))
                        bbs.append(bb)

                    s = score_choice(choice, bbs)
                    if best_score is None or s < best_score:
                        best_score = s
                        best_choice = choice

    if best_choice is None:
        return

    # Apply the best choice.
    for p, label, (dx, dy, ha, va) in zip(points, labels, best_choice):
        ax.annotate(
            label,
            (p.b, p.c),
            textcoords="offset points",
            xytext=(dx, dy),
            ha=ha,
            va=va,
            fontsize=fontsize,
            color="black",
            zorder=4,
            clip_on=True,
        )


def plot_fig4(
    reports_dir: Path,
    out_path: Path,
    dpi: int,
    palette: str,
    alpha: float,
    point_size: float,
    label_fontsize: int,
) -> None:
    reports = load_reports(reports_dir)

    cmap = plt.get_cmap(palette)
    mode_colors = {mode: cmap(i) for i, mode in enumerate(MODE_ORDER)}

    # Precompute all b/c to set a shared axis range.
    all_bc = []
    bc_map: dict[tuple[str, str, str], tuple[int, int]] = {}
    for dataset in DATASET_ORDER:
        for agent in AGENT_ORDER:
            full_rep = reports[dataset][agent]["run_full"]
            for mode in COMPARE_MODES:
                b, c = compute_bc(reports[dataset][agent][mode], full_rep)
                bc_map[(dataset, agent, mode)] = (b, c)
                all_bc.append((b, c))

    max_bc = max(max(b, c) for b, c in all_bc) if all_bc else 0
    lim = max_bc + 1

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 7), sharex=True, sharey=True)

    facet_points: dict[tuple[str, str], list[BCPoint]] = {}

    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            ax = axes[r][c]

            # Diagonal y=x
            ax.plot([0, lim], [0, lim], color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)

            pts = []
            for mode in COMPARE_MODES:
                b, cc = bc_map[(dataset, agent, mode)]
                pts.append(BCPoint(mode=mode, b=b, c=cc))

                ax.scatter(
                    [b],
                    [cc],
                    s=point_size,
                    color=mode_colors[mode],
                    alpha=alpha,
                    edgecolors="white",
                    linewidths=0.8,
                    zorder=3,
                )

            facet_points[(dataset, agent)] = pts

            ax.set_xlim(0, lim)
            ax.set_ylim(0, lim)
            ax.set_aspect("equal", adjustable="box")

            ax.grid(alpha=0.25)
            ax.set_title(f"{DATASET_LABEL[dataset]} — {AGENT_LABEL[agent]}")

            if r == 1:
                ax.set_xlabel("b = Mode-only successes")
            if c == 0:
                ax.set_ylabel("c = Full-only successes")

    # Place labels after a draw so we can measure text extents.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            ax = axes[r][c]
            place_labels(
                ax=ax,
                fig=fig,
                renderer=renderer,
                points=facet_points[(dataset, agent)],
                point_size=point_size,
                fontsize=label_fontsize,
            )

    note = (
        "Note: Each point compares a mode against Run-Full using instance-level resolved_ids.\n"
        "Diagonal y=x indicates symmetry; points above it mean Run-Full has more unique wins (c>b),\n"
        "below it mean the mode has more unique wins (b>c). Colors denote modes."
    )

    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = out_path.with_suffix(".png")
    pdf_path = out_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", type=Path, default=Path("sb-cli-reports"))
    parser.add_argument("--out", type=Path, default=Path("figures/fig4_paired_bc_scatter.png"))
    parser.add_argument("--dpi", type=int, default=200)

    parser.add_argument("--palette", type=str, default="Set2")
    parser.add_argument("--alpha", type=float, default=0.9)

    parser.add_argument("--point-size", type=float, default=120.0)
    parser.add_argument("--label-fontsize", type=int, default=9)

    args = parser.parse_args()

    plot_fig4(
        reports_dir=args.reports_dir,
        out_path=args.out,
        dpi=args.dpi,
        palette=args.palette,
        alpha=args.alpha,
        point_size=float(args.point_size),
        label_fontsize=int(args.label_fontsize),
    )


if __name__ == "__main__":
    main()
