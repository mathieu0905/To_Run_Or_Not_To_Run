#!/usr/bin/env python3
"""Figure 2: Cost-effectiveness tradeoff (Pareto front).

Facets:
- Rows: dataset (SWE-bench Lite / Verified)
- Cols: agent (Claude Code / Codex)

Encodings:
- X: Avg Total Tokens (computed from output/ traces)
- Y: Pass Rate (%) (from sb-cli-reports)
- Bubble area: Avg High-Cost Exec (computed from output/ traces)
- Color: Mode (kept consistent across figures)
- Pareto-optimal points are highlighted with a black ring (within each subplot)

Run:
  python figures/fig2_pareto_front.py

Output:
  figures/fig2_pareto_front.png
  figures/fig2_pareto_front.pdf
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.transforms import Bbox
from matplotlib.ticker import FuncFormatter, MaxNLocator


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.common.data_loader import (  # noqa: E402
    MODE_ORDER,
    get_aggregated_stats,
    load_all_results,
    load_pass_rates,
)


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
class Point:
    dataset: str
    agent: str
    mode: str
    tokens: float
    pass_rate: float
    high_cost_exec: float


def _comma_int(x: float, _pos: int) -> str:
    return f"{int(x):,}"


def _round_down(x: float, step: float) -> float:
    return step * (x // step)


def _round_up(x: float, step: float) -> float:
    return step * ((x + step - 1e-9) // step)


def compute_auto_ylim(points: list[Point], pad_pct: float = 1.5) -> tuple[float, float]:
    """Compute a shared y-lim (in percent) for readability."""
    rates = [p.pass_rate for p in points]
    if not rates:
        return (0.0, 100.0)

    ymin = max(0.0, min(rates) - pad_pct)
    ymax = min(100.0, max(rates) + pad_pct)

    ymin = _round_down(ymin, 5.0)
    ymax = _round_up(ymax, 5.0)

    if ymax - ymin < 10.0:
        return (0.0, 100.0)

    return (ymin, ymax)


def scale_sizes(values: list[float], s_min: float, s_max: float, gamma: float) -> list[float]:
    """Map values to scatter area sizes with a contrast parameter (gamma)."""
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if vmax <= vmin:
        return [(s_min + s_max) / 2.0 for _ in values]

    out: list[float] = []
    for v in values:
        t = (v - vmin) / (vmax - vmin)
        t = max(0.0, min(1.0, t))
        t = t**gamma
        out.append(s_min + t * (s_max - s_min))
    return out


def pareto_optimal(points: list[Point]) -> dict[str, bool]:
    """Return {mode: is_pareto} within a single facet.

    Objective: maximize pass_rate, minimize tokens.
    """
    is_pareto: dict[str, bool] = {p.mode: True for p in points}

    for i, p in enumerate(points):
        for j, q in enumerate(points):
            if i == j:
                continue
            dominates = (
                q.pass_rate >= p.pass_rate
                and q.tokens <= p.tokens
                and (q.pass_rate > p.pass_rate or q.tokens < p.tokens)
            )
            if dominates:
                is_pareto[p.mode] = False
                break

    return is_pareto


def load_points(reports_dir: Path, output_dir: Path) -> list[Point]:
    pass_rates = load_pass_rates(reports_dir)
    results = load_all_results(output_dir=output_dir, exclude_glm=True)
    stats = get_aggregated_stats(results)

    missing: list[str] = []
    pts: list[Point] = []

    for dataset in DATASET_ORDER:
        for agent in AGENT_ORDER:
            for mode in MODE_ORDER:
                pr = pass_rates.get(dataset, {}).get(agent, {}).get(mode)
                st = stats.get(dataset, {}).get(agent, {}).get(mode)
                if not pr:
                    missing.append(f"pass_rate:{dataset}/{agent}/{mode}")
                    continue
                if not st:
                    missing.append(f"cost_stats:{dataset}/{agent}/{mode}")
                    continue

                total = pr.get("total", 0)
                resolved = pr.get("resolved", 0)
                rate = (resolved / total * 100.0) if total else 0.0

                pts.append(
                    Point(
                        dataset=dataset,
                        agent=agent,
                        mode=mode,
                        tokens=float(st["avg_total_tokens"]),
                        pass_rate=float(rate),
                        high_cost_exec=float(st["avg_high_cost_exec"]),
                    )
                )

    if missing:
        raise FileNotFoundError(
            "Missing required data for: " + ", ".join(missing) + f". reports_dir={reports_dir}, output_dir={output_dir}"
        )

    return pts


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


def place_labels(
    ax,
    fig,
    renderer,
    facet_points: list[Point],
    size_by_key: dict[tuple[str, str, str], float],
    fontsize: int,
) -> None:
    """Place point labels with simple collision avoidance (no extra deps)."""

    # Candidate offsets in points.
    candidates = [
        (8, 8),
        (8, 14),
        (14, 8),
        (-8, 8),
        (-8, 14),
        (-14, 8),
        (8, -8),
        (8, -14),
        (14, -8),
        (-8, -8),
        (-8, -14),
        (-14, -8),
        (0, 14),
        (0, -14),
        (14, 0),
        (-14, 0),
        (20, 10),
        (-20, 10),
        (20, -10),
        (-20, -10),
    ]

    ax_bbox = ax.get_window_extent(renderer)

    marker_bboxes = []
    for p in facet_points:
        s = size_by_key[(p.dataset, p.agent, p.mode)]
        marker_bboxes.append(_marker_bbox(ax, fig, p.tokens, p.pass_rate, s))

    placed: list[Bbox] = []

    # Stable ordering helps reproducibility.
    for p in sorted(facet_points, key=lambda q: (q.tokens, -q.pass_rate)):
        label = f"{MODE_LABEL.get(p.mode, p.mode)}\n({p.high_cost_exec:.1f})"

        best = None
        best_score = None
        best_text = None

        for dx, dy in candidates:
            ha = "left" if dx >= 0 else "right"
            va = "bottom" if dy >= 0 else "top"

            txt = ax.annotate(
                label,
                (p.tokens, p.pass_rate),
                textcoords="offset points",
                xytext=(dx, dy),
                ha=ha,
                va=va,
                fontsize=fontsize,
                color="black",
                zorder=6,
                clip_on=True,
            )

            bb = txt.get_window_extent(renderer)

            # Score: overlap with existing labels + overlap with markers + penalty for leaving axes.
            score = 0.0

            # Keep labels inside axes bbox (penalize leaving).
            if not (ax_bbox.contains(bb.x0, bb.y0) and ax_bbox.contains(bb.x1, bb.y1)):
                score += 1e9

            for other_bb in placed:
                score += 1000.0 * _bbox_overlap_area(bb, other_bb)

            for mb in marker_bboxes:
                score += 10.0 * _bbox_overlap_area(bb, mb)

            if best_score is None or score < best_score:
                # Remove the previous best candidate, otherwise we will leave duplicate labels.
                if best_text is not None:
                    best_text.remove()
                best_score = score
                best = (dx, dy, ha, va)
                best_text = txt
            else:
                txt.remove()

            # Early exit if perfect placement.
            if best_score == 0.0:
                break

        # If we never created anything (shouldn't happen), skip.
        if best_text is None:
            continue

        # If best_text isn't the last created, ensure only best_text remains.
        # (Other candidates were already removed in the loop.)
        placed.append(best_text.get_window_extent(renderer))


def plot_fig2(
    reports_dir: Path,
    output_dir: Path,
    out_path: Path,
    dpi: int,
    palette: str,
    alpha: float,
    s_min: float,
    s_max: float,
    size_gamma: float,
    ylim: tuple[float, float] | None,
    label_fontsize: int,
    x_nbins: int,
) -> None:
    pts = load_points(reports_dir, output_dir)

    exec_values = [p.high_cost_exec for p in pts]
    exec_sizes = scale_sizes(exec_values, s_min=s_min, s_max=s_max, gamma=size_gamma)
    size_by_key = {(p.dataset, p.agent, p.mode): s for p, s in zip(pts, exec_sizes)}

    cmap = plt.get_cmap(palette)
    mode_colors = {mode: cmap(i) for i, mode in enumerate(MODE_ORDER)}

    if ylim is None:
        ylim = compute_auto_ylim(pts)

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 7), sharey=True)

    facets: dict[tuple[str, str], list[Point]] = {}

    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            ax = axes[r][c]
            facet = [p for p in pts if p.dataset == dataset and p.agent == agent]
            facets[(dataset, agent)] = facet
            facet_by_mode = {p.mode: p for p in facet}

            pareto = pareto_optimal(facet)

            # Set x-limits with padding for readability.
            xs = [p.tokens for p in facet]
            x_min, x_max = min(xs), max(xs)
            x_pad = (x_max - x_min) * 0.10 if x_max > x_min else max(1.0, x_max * 0.08)
            ax.set_xlim(x_min - x_pad, x_max + x_pad)

            for mode in MODE_ORDER:
                p = facet_by_mode[mode]
                s = size_by_key[(dataset, agent, mode)]

                ax.scatter(
                    p.tokens,
                    p.pass_rate,
                    s=s,
                    color=mode_colors[mode],
                    alpha=alpha,
                    edgecolors="white",
                    linewidths=0.8,
                    zorder=3,
                )

            # Highlight Pareto-optimal points.
            for mode in MODE_ORDER:
                if not pareto.get(mode, False):
                    continue
                p = facet_by_mode[mode]
                s = size_by_key[(dataset, agent, mode)]
                ax.scatter(
                    p.tokens,
                    p.pass_rate,
                    s=s + 80.0,
                    facecolors="none",
                    edgecolors="black",
                    linewidths=2.0,
                    zorder=4,
                )

            ax.set_ylim(ylim)
            ax.grid(axis="y", alpha=0.25)
            ax.set_title(f"{DATASET_LABEL[dataset]} — {AGENT_LABEL[agent]}")

            ax.xaxis.set_major_formatter(FuncFormatter(_comma_int))
            ax.xaxis.set_major_locator(MaxNLocator(nbins=x_nbins))
            ax.tick_params(axis="x", labelrotation=0)

            if r == 1:
                ax.set_xlabel("Avg Total Tokens")
            if c == 0:
                ax.set_ylabel("Pass Rate (%)")

    # Draw once to get a renderer, then place labels to avoid overlaps.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            ax = axes[r][c]
            place_labels(
                ax=ax,
                fig=fig,
                renderer=renderer,
                facet_points=facets[(dataset, agent)],
                size_by_key=size_by_key,
                fontsize=label_fontsize,
            )

    # Figure footnote (caption-like).
    notes = []
    if float(ylim[0]) > 0.0 or float(ylim[1]) < 100.0:
        notes.append(f"Note: y-axis is truncated to [{ylim[0]:.0f}, {ylim[1]:.0f}] for readability.\n")
    notes.append("Bubble area encodes Avg High-Cost Exec (numbers in parentheses show the exact value).\n")
    notes.append("Black ring marks Pareto-optimal points within each subplot (higher pass rate, lower tokens).")

    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.text(0.5, 0.01, " ".join(notes), ha="center", va="bottom", fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = out_path.with_suffix(".png")
    pdf_path = out_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", type=Path, default=PROJECT_ROOT / "sb-cli-reports")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output")
    parser.add_argument("--out", type=Path, default=PROJECT_ROOT / "figures/fig2_pareto_front.png")
    parser.add_argument("--dpi", type=int, default=200)

    parser.add_argument("--palette", type=str, default="Set2")
    parser.add_argument("--alpha", type=float, default=0.9)

    parser.add_argument("--size-min", type=float, default=120.0, help="Min bubble area (points^2).")
    parser.add_argument("--size-max", type=float, default=1400.0, help="Max bubble area (points^2).")
    parser.add_argument("--size-gamma", type=float, default=1.6, help="Contrast for bubble sizes (>1 increases contrast).")

    parser.add_argument(
        "--ylim",
        type=float,
        nargs=2,
        default=None,
        metavar=("YMIN", "YMAX"),
        help="Force shared y-limits. Example: --ylim 0 100",
    )

    parser.add_argument("--label-fontsize", type=int, default=9)
    parser.add_argument("--x-nbins", type=int, default=4, help="Max number of x ticks per subplot.")

    args = parser.parse_args()

    ylim = tuple(args.ylim) if args.ylim is not None else None

    plot_fig2(
        reports_dir=args.reports_dir,
        output_dir=args.output_dir,
        out_path=args.out,
        dpi=args.dpi,
        palette=args.palette,
        alpha=args.alpha,
        s_min=args.size_min,
        s_max=args.size_max,
        size_gamma=args.size_gamma,
        ylim=ylim,
        label_fontsize=args.label_fontsize,
        x_nbins=args.x_nbins,
    )


if __name__ == "__main__":
    main()
