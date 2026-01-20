#!/usr/bin/env python3
"""Figure 5: Token-savings vs Run-Full and ΔPass (pp) with 90% CI.

This script can generate:
- ONE figure for a specified dataset (Lite or Verified), with two panels (agents), OR
- ONE combined figure overlaying Lite+Verified in the same two panels, OR
- ONE combined 2×2 grid figure: rows=datasets (Lite/Verified), cols=agents (Claude/Codex).

Encodings (all relative to Run-Full within each agent+dataset):
- X: Token savings (k tokens) = AvgTokens(full) - AvgTokens(mode)
- Y: ΔPass (pp) = PassRate(mode) - PassRate(full)
- Uncertainty: 90% CI via paired bootstrap on instance IDs (completed_ids of run_full)
- Gray band: equivalence margin ±5pp (configurable)

Data sources:
- Pass/fail IDs from sb-cli-reports/*.json (completed_ids, resolved_ids)
- Token counts from output/{dataset}/{agent}/{mode}/{instance_id}/trace.jsonl

Run:
  python figures/fig5_delta_plane.py --dataset swebenchlite
  python figures/fig5_delta_plane.py --dataset swebenchverified
  python figures/fig5_delta_plane.py --dataset both --layout grid
  python figures/fig5_delta_plane.py --dataset both --layout overlay

Output:
  figures/fig5_delta_plane_{dataset}.png (+ .pdf), or
  figures/fig5_delta_plane_grid.png (+ .pdf) when --dataset=both --layout=grid, or
  figures/fig5_delta_plane_overlay.png (+ .pdf) when --dataset=both --layout=overlay
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from matplotlib.transforms import Bbox


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analysis.common.data_loader import count_tokens_and_execs  # noqa: E402


MODE_ORDER = ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"]
COMPARE_MODES = ["run_free", "run_less_k1", "run_less_k3", "run_cost"]

MODE_LABEL = {
    "run_free": "Free",
    "run_less_k1": "Less-K1",
    "run_less_k3": "Less-K3",
    "run_cost": "Cost",
    "run_full": "Full",
}

MODE_MARKER = {
    "run_free": "o",
    "run_less_k1": "s",
    "run_less_k3": "^",
    "run_cost": "D",
    "run_full": "*",
}

AGENT_ORDER = ["claude_code", "codex"]
AGENT_LABEL = {"claude_code": "Claude Code", "codex": "Codex"}

DATASET_ORDER = ["swebenchlite", "swebenchverified"]
DATASET_LABEL = {"swebenchlite": "SWE-bench Lite", "swebenchverified": "SWE-bench Verified"}
DATASET_SUFFIX = {"swebenchlite": "L", "swebenchverified": "V"}


@dataclass(frozen=True)
class Report:
    completed_ids: list[str]
    completed_set: set[str]
    resolved_set: set[str]
    resolved_instances: int
    completed_instances: int


@dataclass(frozen=True)
class DeltaPoint:
    dataset: str
    mode: str
    x_savings_k: float
    y_delta_pp: float
    ci_lo_pp: float
    ci_hi_pp: float


def _detect_dataset(filename_lower: str) -> str | None:
    if "swe-bench_lite" in filename_lower:
        return "swebenchlite"
    if "swe-bench_verified" in filename_lower:
        return "swebenchverified"
    return None


def load_reports_for_dataset(reports_dir: Path, dataset: str) -> dict[str, dict[str, Report]]:
    """Return {agent: {mode: Report}} for a single dataset."""
    data: dict[str, dict[str, Report]] = {a: {} for a in AGENT_ORDER}

    for path in sorted(reports_dir.glob("*.json")):
        name = path.name.lower()
        detected = _detect_dataset(name)
        if detected != dataset:
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

        resolved_instances = int(report.get("resolved_instances", len(resolved_ids)))
        completed_instances = int(report.get("completed_instances", len(completed_ids)))

        if mode in data[agent]:
            raise ValueError(f"Duplicate report for {dataset}/{agent}/{mode}: {path}")

        data[agent][mode] = Report(
            completed_ids=list(completed_ids),
            completed_set=set(completed_ids),
            resolved_set=set(resolved_ids),
            resolved_instances=resolved_instances,
            completed_instances=completed_instances,
        )

    missing = []
    for agent in AGENT_ORDER:
        for mode in MODE_ORDER:
            if mode not in data[agent]:
                missing.append(f"{dataset}/{agent}/{mode}")
    if missing:
        raise FileNotFoundError(
            "Missing sb-cli report(s) for: " + ", ".join(missing) + f". reports_dir={reports_dir}"
        )

    return data


def _percentile(sorted_vals: list[float], q: float) -> float:
    """q in [0,1]. Linear interpolation between closest ranks."""
    if not sorted_vals:
        return 0.0
    if q <= 0.0:
        return sorted_vals[0]
    if q >= 1.0:
        return sorted_vals[-1]

    n = len(sorted_vals)
    pos = (n - 1) * q
    lo = int(pos)
    hi = min(lo + 1, n - 1)
    w = pos - lo
    return (1.0 - w) * sorted_vals[lo] + w * sorted_vals[hi]


def paired_bootstrap_delta_pp(
    mode_rep: Report,
    full_rep: Report,
    n_boot: int,
    seed: int,
) -> tuple[float, float, float, int]:
    """Return (delta_pp, ci_lo_pp, ci_hi_pp, n_ids).

    Pairing reference: run_full completed_ids.
    If a full_id is missing from mode completed_ids, treat it as a failure (0).
    """
    ids = list(full_rep.completed_ids)
    n = len(ids)
    if n == 0:
        return (0.0, 0.0, 0.0, 0)

    full_success = [1 if inst_id in full_rep.resolved_set else 0 for inst_id in ids]
    mode_success = [
        1 if (inst_id in mode_rep.completed_set and inst_id in mode_rep.resolved_set) else 0
        for inst_id in ids
    ]

    delta = (sum(mode_success) / n - sum(full_success) / n) * 100.0

    rng = random.Random(seed)
    deltas: list[float] = []
    for _ in range(n_boot):
        s_m = 0
        s_f = 0
        for _i in range(n):
            j = rng.randrange(n)
            s_m += mode_success[j]
            s_f += full_success[j]
        deltas.append((s_m / n - s_f / n) * 100.0)

    deltas.sort()
    ci_lo = _percentile(deltas, 0.05)
    ci_hi = _percentile(deltas, 0.95)

    return (delta, ci_lo, ci_hi, n)


def avg_total_tokens_for_ids(
    output_dir: Path,
    dataset: str,
    agent: str,
    mode: str,
    ids: list[str],
) -> tuple[float, int]:
    """Average (input+output) tokens over the given ids. Raises on missing traces."""
    totals: list[int] = []
    missing: list[str] = []

    for inst_id in ids:
        trace_path = output_dir / dataset / agent / mode / inst_id / "trace.jsonl"
        if not trace_path.exists():
            missing.append(inst_id)
            continue

        data = count_tokens_and_execs(trace_path)
        tok = int(data["tokens"]["input"]) + int(data["tokens"]["output"])
        totals.append(tok)

    if missing:
        sample = ", ".join(missing[:8])
        more = "" if len(missing) <= 8 else f" (+{len(missing) - 8} more)"
        raise FileNotFoundError(
            f"Missing trace.jsonl for {dataset}/{agent}/{mode}: {sample}{more}. output_dir={output_dir}"
        )

    if not totals:
        return (0.0, 0)

    return (sum(totals) / len(totals), len(totals))


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


def place_mode_labels(
    ax,
    fig,
    renderer,
    points: list[DeltaPoint],
    point_size: float,
    fontsize: int,
    *,
    labels: list[str] | None = None,
) -> None:
    """Place labels with simple collision avoidance (no extra deps)."""
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
    marker_bboxes = [_marker_bbox(ax, fig, float(p.x_savings_k), float(p.y_delta_pp), float(point_size)) for p in points]
    if labels is None:
        labels = [MODE_LABEL.get(p.mode, p.mode) for p in points]

    # Precompute bboxes for every (point, candidate).
    cand_bboxes: list[list[tuple[int, int, str, str, Bbox]]] = []
    for p, label in zip(points, labels):
        per_point: list[tuple[int, int, str, str, Bbox]] = []
        for dx, dy in candidates:
            ha = "left" if dx >= 0 else "right"
            va = "bottom" if dy >= 0 else "top"
            txt = ax.annotate(
                label,
                (p.x_savings_k, p.y_delta_pp),
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

    if len(points) != 4:
        # Greedy placement for N != 4 (brute-force would explode).
        n = len(points)
        px = [ax.transData.transform((float(p.x_savings_k), float(p.y_delta_pp))) for p in points]
        min_dist = []
        for i in range(n):
            d = min(
                math.hypot(px[i][0] - px[j][0], px[i][1] - px[j][1]) for j in range(n) if j != i
            )
            min_dist.append(d)
        order = sorted(range(n), key=lambda i: min_dist[i])  # most crowded first

        chosen: list[tuple[int, int, str, str] | None] = [None] * n
        chosen_bboxes: list[Bbox] = []

        def score_single(dx: int, dy: int, bb: Bbox) -> float:
            score = 0.0

            if not (ax_bbox.contains(bb.x0, bb.y0) and ax_bbox.contains(bb.x1, bb.y1)):
                score += 1e9

            for other_bb in chosen_bboxes:
                score += 1000.0 * _bbox_overlap_area(bb, other_bb)

            for mb in marker_bboxes:
                score += 10.0 * _bbox_overlap_area(bb, mb)

            score += 0.2 * (abs(dx) + abs(dy))
            return score

        for idx in order:
            best: tuple[int, int, str, str, Bbox] | None = None
            best_score: float | None = None

            for dx, dy, ha, va, bb in cand_bboxes[idx]:
                s = score_single(dx, dy, bb)
                if best_score is None or s < best_score:
                    best_score = s
                    best = (dx, dy, ha, va, bb)

            if best is None:
                continue
            dx, dy, ha, va, bb = best
            chosen[idx] = (dx, dy, ha, va)
            chosen_bboxes.append(bb)

        for p, label, ch in zip(points, labels, chosen):
            if ch is None:
                dx, dy, ha, va = (8, 8, "left", "bottom")
            else:
                dx, dy, ha, va = ch
            ax.annotate(
                label,
                (p.x_savings_k, p.y_delta_pp),
                textcoords="offset points",
                xytext=(dx, dy),
                ha=ha,
                va=va,
                fontsize=fontsize,
                color="black",
                zorder=6,
                clip_on=True,
            )
        return

    # Brute-force all combinations (<= 24^4 = 331k).
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
            (p.x_savings_k, p.y_delta_pp),
            textcoords="offset points",
            xytext=(dx, dy),
            ha=ha,
            va=va,
            fontsize=fontsize,
            color="black",
            zorder=6,
            clip_on=True,
        )


def compute_auto_ylim(points_by_agent: dict[str, list[DeltaPoint]], equiv_pp: float) -> tuple[float, float]:
    vals: list[float] = [-equiv_pp, 0.0, equiv_pp]
    for pts in points_by_agent.values():
        for p in pts:
            vals.extend([p.ci_lo_pp, p.ci_hi_pp])

    ymin = min(vals)
    ymax = max(vals)
    span = max(1e-6, ymax - ymin)
    pad = max(0.6, 0.12 * span)

    ymin -= pad
    ymax += pad

    # Round to nice bounds (integer pp).
    ymin = math.floor(ymin)
    ymax = math.ceil(ymax)

    # Ensure the equivalence band is fully visible.
    ymin = min(ymin, -equiv_pp - 1.0)
    ymax = max(ymax, equiv_pp + 1.0)

    return (float(ymin), float(ymax))


def compute_auto_xlim(points_by_agent: dict[str, list[DeltaPoint]]) -> tuple[float, float]:
    xs: list[float] = [0.0]
    for pts in points_by_agent.values():
        xs.extend([p.x_savings_k for p in pts])

    xmin = min(xs)
    xmax = max(xs)
    span = max(1e-6, xmax - xmin)
    pad = max(6.0, 0.10 * span)

    xmin -= pad
    xmax += pad

    # Round to nice bounds (10k tokens).
    xmin = 10.0 * math.floor(xmin / 10.0)
    xmax = 10.0 * math.ceil(xmax / 10.0)

    return (float(xmin), float(xmax))


def _int_tick(x: float, _pos: int) -> str:
    # x is in k tokens
    if abs(x) < 1e-6:
        return "0"
    if abs(x) >= 1000:
        return f"{int(x):,}"
    return f"{int(x)}"


def plot_dataset(
    *,
    reports_dir: Path,
    output_dir: Path,
    dataset: str,
    out_path: Path,
    dpi: int,
    palette: str,
    alpha: float,
    point_size: float,
    label_fontsize: int,
    n_boot: int,
    seed: int,
    equiv_pp: float,
    show_k_trend: bool,
) -> None:
    reports = load_reports_for_dataset(reports_dir, dataset)

    cmap = plt.get_cmap(palette)
    mode_colors = {mode: cmap(i) for i, mode in enumerate(MODE_ORDER)}

    points_by_agent: dict[str, list[DeltaPoint]] = {}
    full_meta: dict[str, tuple[float, float, int]] = {}
    # agent -> (full_pass_rate_pct, full_avg_tokens, n_ids)

    for agent in AGENT_ORDER:
        full_rep = reports[agent]["run_full"]
        ids = list(full_rep.completed_ids)

        full_avg_tokens, n_tokens = avg_total_tokens_for_ids(output_dir, dataset, agent, "run_full", ids)
        full_pass = (full_rep.resolved_instances / full_rep.completed_instances * 100.0) if full_rep.completed_instances else 0.0
        full_meta[agent] = (full_pass, full_avg_tokens, n_tokens)

        pts: list[DeltaPoint] = []
        for mode in COMPARE_MODES:
            rep = reports[agent][mode]
            delta, lo, hi, _n = paired_bootstrap_delta_pp(rep, full_rep, n_boot=n_boot, seed=seed)

            mode_avg_tokens, _n2 = avg_total_tokens_for_ids(output_dir, dataset, agent, mode, ids)
            savings_k = (full_avg_tokens - mode_avg_tokens) / 1000.0

            pts.append(
                DeltaPoint(
                    dataset=dataset,
                    mode=mode,
                    x_savings_k=float(savings_k),
                    y_delta_pp=float(delta),
                    ci_lo_pp=float(lo),
                    ci_hi_pp=float(hi),
                )
            )

        points_by_agent[agent] = pts

    xlim = compute_auto_xlim(points_by_agent)
    ylim = compute_auto_ylim(points_by_agent, equiv_pp=equiv_pp)

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 4.4), sharex=True, sharey=True)
    fig.suptitle(DATASET_LABEL.get(dataset, dataset), fontsize=13)

    for i, agent in enumerate(AGENT_ORDER):
        ax = axes[i]

        # Equivalence band and reference lines.
        ax.axhspan(-equiv_pp, equiv_pp, color="gray", alpha=0.15, zorder=0)
        ax.axhline(0.0, color="black", linewidth=1.0, alpha=0.55, zorder=1)
        ax.axvline(0.0, color="black", linewidth=1.0, alpha=0.55, zorder=1)
        ax.axhline(-equiv_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)
        ax.axhline(equiv_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)

        pts = points_by_agent[agent]
        pts_by_mode = {p.mode: p for p in pts}

        # Plot CI + point marker.
        for p in pts:
            ax.vlines(p.x_savings_k, p.ci_lo_pp, p.ci_hi_pp, color="black", linewidth=2.0, zorder=2)
            ax.scatter(
                [p.x_savings_k],
                [p.y_delta_pp],
                s=point_size,
                marker=MODE_MARKER[p.mode],
                color=mode_colors[p.mode],
                alpha=alpha,
                edgecolors="white",
                linewidths=0.8,
                zorder=4,
            )

        # Optional: connect K=1 -> K=3 for Run-Less to show K trend.
        if show_k_trend and "run_less_k1" in pts_by_mode and "run_less_k3" in pts_by_mode:
            p1 = pts_by_mode["run_less_k1"]
            p3 = pts_by_mode["run_less_k3"]
            ax.plot(
                [p1.x_savings_k, p3.x_savings_k],
                [p1.y_delta_pp, p3.y_delta_pp],
                color="gray",
                linestyle="--",
                linewidth=1.1,
                alpha=0.75,
                zorder=1,
            )
            mx = (p1.x_savings_k + p3.x_savings_k) / 2.0
            my = (p1.y_delta_pp + p3.y_delta_pp) / 2.0
            ax.annotate(
                "K↑",
                (mx, my),
                textcoords="offset points",
                xytext=(6, 6),
                fontsize=8,
                color="gray",
                zorder=5,
                clip_on=True,
            )

        ax.set_title(AGENT_LABEL[agent])
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.grid(alpha=0.22)

        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.xaxis.set_major_formatter(FuncFormatter(_int_tick))

        if i == 0:
            ax.set_ylabel("ΔPass (pp) vs Full (90% CI)")
        ax.set_xlabel("Token savings vs Full (k tokens)")

        # Baseline annotation (Full).
        full_pass, full_tokens, n_ids = full_meta[agent]
        txt = f"Full pass={full_pass:.0f}%\nFull tokens={full_tokens/1000.0:.0f}k\nn={n_ids}"
        ax.text(
            0.02,
            0.98,
            txt,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
            zorder=10,
        )

    # Place labels after a draw so we can measure text extents.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for i, agent in enumerate(AGENT_ORDER):
        place_mode_labels(
            ax=axes[i],
            fig=fig,
            renderer=renderer,
            points=points_by_agent[agent],
            point_size=point_size,
            fontsize=label_fontsize,
        )

    note = (
        f"Note: X is AvgTokens(full)−AvgTokens(mode) over run_full completed_ids; "
        f"Y is ΔPass(pp) vs Full with 90% CI via paired bootstrap (n_boot={n_boot}, seed={seed}); "
        f"gray band denotes equivalence margin ±{equiv_pp:.0f}pp."
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = out_path.with_suffix(".png")
    pdf_path = out_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def plot_both_datasets_overlay(
    *,
    reports_dir: Path,
    output_dir: Path,
    out_path: Path,
    dpi: int,
    palette: str,
    alpha: float,
    point_size: float,
    label_fontsize: int,
    n_boot: int,
    seed: int,
    equiv_pp: float,
    show_k_trend: bool,
) -> None:
    reports_by_dataset = {d: load_reports_for_dataset(reports_dir, d) for d in DATASET_ORDER}

    cmap = plt.get_cmap(palette)
    mode_colors = {mode: cmap(i) for i, mode in enumerate(MODE_ORDER)}

    points_by_agent_dataset: dict[str, dict[str, list[DeltaPoint]]] = {
        a: {d: [] for d in DATASET_ORDER} for a in AGENT_ORDER
    }
    full_meta: dict[str, dict[str, tuple[float, float, int]]] = {
        a: {} for a in AGENT_ORDER
    }
    # full_meta[agent][dataset] = (full_pass_rate_pct, full_avg_tokens, n_ids)

    for dataset in DATASET_ORDER:
        reports = reports_by_dataset[dataset]
        for agent in AGENT_ORDER:
            full_rep = reports[agent]["run_full"]
            ids = list(full_rep.completed_ids)

            full_avg_tokens, n_tokens = avg_total_tokens_for_ids(output_dir, dataset, agent, "run_full", ids)
            full_pass = (
                full_rep.resolved_instances / full_rep.completed_instances * 100.0
                if full_rep.completed_instances
                else 0.0
            )
            full_meta[agent][dataset] = (full_pass, full_avg_tokens, n_tokens)

            pts: list[DeltaPoint] = []
            for mode in COMPARE_MODES:
                rep = reports[agent][mode]
                delta, lo, hi, _n = paired_bootstrap_delta_pp(rep, full_rep, n_boot=n_boot, seed=seed)

                mode_avg_tokens, _n2 = avg_total_tokens_for_ids(output_dir, dataset, agent, mode, ids)
                savings_k = (full_avg_tokens - mode_avg_tokens) / 1000.0

                pts.append(
                    DeltaPoint(
                        dataset=dataset,
                        mode=mode,
                        x_savings_k=float(savings_k),
                        y_delta_pp=float(delta),
                        ci_lo_pp=float(lo),
                        ci_hi_pp=float(hi),
                    )
                )

            points_by_agent_dataset[agent][dataset] = pts

    points_by_agent_union: dict[str, list[DeltaPoint]] = {
        agent: points_by_agent_dataset[agent]["swebenchlite"] + points_by_agent_dataset[agent]["swebenchverified"]
        for agent in AGENT_ORDER
    }
    xlim = compute_auto_xlim(points_by_agent_union)
    ylim = compute_auto_ylim(points_by_agent_union, equiv_pp=equiv_pp)

    fig, axes = plt.subplots(nrows=1, ncols=2, figsize=(12, 5.0), sharex=True, sharey=True)
    fig.suptitle("SWE-bench Lite & Verified", fontsize=13)

    for i, agent in enumerate(AGENT_ORDER):
        ax = axes[i]

        # Equivalence band and reference lines.
        ax.axhspan(-equiv_pp, equiv_pp, color="gray", alpha=0.15, zorder=0)
        ax.axhline(0.0, color="black", linewidth=1.0, alpha=0.55, zorder=1)
        ax.axvline(0.0, color="black", linewidth=1.0, alpha=0.55, zorder=1)
        ax.axhline(-equiv_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)
        ax.axhline(equiv_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)

        # Plot both datasets (filled vs hollow).
        for dataset in DATASET_ORDER:
            pts = points_by_agent_dataset[agent][dataset]
            pts_by_mode = {p.mode: p for p in pts}

            is_lite = dataset == "swebenchlite"
            ci_ls = "-" if is_lite else "--"
            ci_alpha = 0.85 if is_lite else 0.75
            z_scatter = 4 if is_lite else 5

            for p in pts:
                ax.vlines(
                    p.x_savings_k,
                    p.ci_lo_pp,
                    p.ci_hi_pp,
                    color="black",
                    linestyle=ci_ls,
                    linewidth=2.0,
                    alpha=ci_alpha,
                    zorder=2,
                )

                if is_lite:
                    ax.scatter(
                        [p.x_savings_k],
                        [p.y_delta_pp],
                        s=point_size,
                        marker=MODE_MARKER[p.mode],
                        color=mode_colors[p.mode],
                        alpha=alpha,
                        edgecolors="white",
                        linewidths=0.9,
                        zorder=z_scatter,
                    )
                else:
                    ax.scatter(
                        [p.x_savings_k],
                        [p.y_delta_pp],
                        s=point_size,
                        marker=MODE_MARKER[p.mode],
                        facecolors="none",
                        edgecolors=mode_colors[p.mode],
                        linewidths=1.8,
                        alpha=1.0,
                        zorder=z_scatter,
                    )

            # Optional: connect K=1 -> K=3 for Run-Less (without extra text to reduce clutter).
            if show_k_trend and "run_less_k1" in pts_by_mode and "run_less_k3" in pts_by_mode:
                p1 = pts_by_mode["run_less_k1"]
                p3 = pts_by_mode["run_less_k3"]
                ax.plot(
                    [p1.x_savings_k, p3.x_savings_k],
                    [p1.y_delta_pp, p3.y_delta_pp],
                    color="gray",
                    linestyle="--" if is_lite else ":",
                    linewidth=1.0,
                    alpha=0.55,
                    zorder=1,
                )

        ax.set_title(AGENT_LABEL[agent])
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.grid(alpha=0.22)

        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.xaxis.set_major_formatter(FuncFormatter(_int_tick))

        if i == 0:
            ax.set_ylabel("ΔPass (pp) vs Full (90% CI)")
        ax.set_xlabel("Token savings vs Full (k tokens)")

        # Baseline annotation (Full) for both datasets.
        lines = []
        for dataset in DATASET_ORDER:
            full_pass, full_tokens, n_ids = full_meta[agent][dataset]
            ds_name = "Lite" if dataset == "swebenchlite" else "Verified"
            lines.append(f"{ds_name} Full: pass={full_pass:.0f}%, tok={full_tokens/1000.0:.0f}k, n={n_ids}")
        txt = "\n".join(lines)
        ax.text(
            0.02,
            0.98,
            txt,
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
            zorder=10,
        )

    # Place labels after a draw so we can measure text extents.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for i, agent in enumerate(AGENT_ORDER):
        pts = points_by_agent_union[agent]
        labels = [f"{MODE_LABEL.get(p.mode, p.mode)}$^{{{DATASET_SUFFIX.get(p.dataset, '?')}}}$" for p in pts]
        place_mode_labels(
            ax=axes[i],
            fig=fig,
            renderer=renderer,
            points=pts,
            point_size=point_size,
            fontsize=label_fontsize,
            labels=labels,
        )

    note = (
        f"Note: Superscript L/V denotes dataset (Lite/Verified). Filled markers are Lite; hollow markers are Verified.\n"
        f"X is AvgTokens(full)−AvgTokens(mode) over run_full completed_ids (per dataset); "
        f"Y is ΔPass(pp) vs Full with 90% CI via paired bootstrap (n_boot={n_boot}, seed={seed});\n"
        f"gray band denotes equivalence margin ±{equiv_pp:.0f}pp."
    )
    fig.tight_layout(rect=(0, 0.08, 1, 0.95))
    fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = out_path.with_suffix(".png")
    pdf_path = out_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def plot_both_datasets_grid(
    *,
    reports_dir: Path,
    output_dir: Path,
    out_path: Path,
    dpi: int,
    palette: str,
    alpha: float,
    point_size: float,
    label_fontsize: int,
    n_boot: int,
    seed: int,
    equiv_pp: float,
    show_k_trend: bool,
) -> None:
    """2×2 grid: rows=datasets (Lite/Verified), cols=agents (Claude/Codex)."""
    reports_by_dataset = {d: load_reports_for_dataset(reports_dir, d) for d in DATASET_ORDER}

    cmap = plt.get_cmap(palette)
    mode_colors = {mode: cmap(i) for i, mode in enumerate(MODE_ORDER)}

    points_by_cell: dict[tuple[str, str], list[DeltaPoint]] = {}
    full_meta: dict[tuple[str, str], tuple[float, float, int]] = {}
    # (dataset, agent) -> (full_pass_rate_pct, full_avg_tokens, n_ids)

    all_points_by_agent: dict[str, list[DeltaPoint]] = {a: [] for a in AGENT_ORDER}

    for dataset in DATASET_ORDER:
        reports = reports_by_dataset[dataset]
        for agent in AGENT_ORDER:
            full_rep = reports[agent]["run_full"]
            ids = list(full_rep.completed_ids)

            full_avg_tokens, n_tokens = avg_total_tokens_for_ids(output_dir, dataset, agent, "run_full", ids)
            full_pass = (
                full_rep.resolved_instances / full_rep.completed_instances * 100.0
                if full_rep.completed_instances
                else 0.0
            )
            full_meta[(dataset, agent)] = (full_pass, full_avg_tokens, n_tokens)

            pts: list[DeltaPoint] = []
            for mode in COMPARE_MODES:
                rep = reports[agent][mode]
                delta, lo, hi, _n = paired_bootstrap_delta_pp(rep, full_rep, n_boot=n_boot, seed=seed)

                mode_avg_tokens, _n2 = avg_total_tokens_for_ids(output_dir, dataset, agent, mode, ids)
                savings_k = (full_avg_tokens - mode_avg_tokens) / 1000.0

                pts.append(
                    DeltaPoint(
                        dataset=dataset,
                        mode=mode,
                        x_savings_k=float(savings_k),
                        y_delta_pp=float(delta),
                        ci_lo_pp=float(lo),
                        ci_hi_pp=float(hi),
                    )
                )

            points_by_cell[(dataset, agent)] = pts
            all_points_by_agent[agent].extend(pts)

    # Shared limits across all 4 facets (to make Lite/Verified directly comparable).
    points_union: dict[str, list[DeltaPoint]] = {
        agent: all_points_by_agent[agent] for agent in AGENT_ORDER
    }
    xlim = compute_auto_xlim(points_union)
    ylim = compute_auto_ylim(points_union, equiv_pp=equiv_pp)

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 7.2), sharex=True, sharey=True)

    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            ax = axes[r][c]

            # Equivalence band and reference lines.
            ax.axhspan(-equiv_pp, equiv_pp, color="gray", alpha=0.15, zorder=0)
            ax.axhline(0.0, color="black", linewidth=1.0, alpha=0.55, zorder=1)
            ax.axvline(0.0, color="black", linewidth=1.0, alpha=0.55, zorder=1)
            ax.axhline(-equiv_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)
            ax.axhline(equiv_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)

            pts = points_by_cell[(dataset, agent)]
            pts_by_mode = {p.mode: p for p in pts}

            for p in pts:
                ax.vlines(p.x_savings_k, p.ci_lo_pp, p.ci_hi_pp, color="black", linewidth=2.0, zorder=2)
                ax.scatter(
                    [p.x_savings_k],
                    [p.y_delta_pp],
                    s=point_size,
                    marker=MODE_MARKER[p.mode],
                    color=mode_colors[p.mode],
                    alpha=alpha,
                    edgecolors="white",
                    linewidths=0.8,
                    zorder=4,
                )

            if show_k_trend and "run_less_k1" in pts_by_mode and "run_less_k3" in pts_by_mode:
                p1 = pts_by_mode["run_less_k1"]
                p3 = pts_by_mode["run_less_k3"]
                ax.plot(
                    [p1.x_savings_k, p3.x_savings_k],
                    [p1.y_delta_pp, p3.y_delta_pp],
                    color="gray",
                    linestyle="--",
                    linewidth=1.0,
                    alpha=0.65,
                    zorder=1,
                )
                mx = (p1.x_savings_k + p3.x_savings_k) / 2.0
                my = (p1.y_delta_pp + p3.y_delta_pp) / 2.0
                ax.annotate(
                    "K↑",
                    (mx, my),
                    textcoords="offset points",
                    xytext=(6, 6),
                    fontsize=8,
                    color="gray",
                    zorder=5,
                    clip_on=True,
                )

            ax.set_xlim(xlim)
            ax.set_ylim(ylim)
            ax.grid(alpha=0.22)

            if r == 1:
                ax.set_xlabel("Token savings vs Full (k tokens)")
            if c == 0:
                ax.set_ylabel("ΔPass (pp) vs Full (90% CI)")

            # Titles: always show full dataset+agent for clarity.
            ax.set_title(f"{DATASET_LABEL[dataset]} — {AGENT_LABEL[agent]}")

            # Baseline annotation per subplot.
            full_pass, full_tokens, n_ids = full_meta[(dataset, agent)]
            txt = f"Full pass={full_pass:.0f}%\nFull tokens={full_tokens/1000.0:.0f}k\nn={n_ids}"
            ax.text(
                0.02,
                0.98,
                txt,
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=9,
                bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "none", "alpha": 0.85},
                zorder=10,
            )

    for ax in axes.ravel():
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=6))
        ax.xaxis.set_major_formatter(FuncFormatter(_int_tick))

    # Place labels after a draw so we can measure text extents.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            place_mode_labels(
                ax=axes[r][c],
                fig=fig,
                renderer=renderer,
                points=points_by_cell[(dataset, agent)],
                point_size=point_size,
                fontsize=label_fontsize,
            )

    note = (
        f"Note: X is AvgTokens(full)−AvgTokens(mode) over run_full completed_ids (per dataset);\n"
        f"Y is ΔPass(pp) vs Full with 90% CI via paired bootstrap (n_boot={n_boot}, seed={seed});\n"
        f"gray band denotes equivalence margin ±{equiv_pp:.0f}pp. Axes are shared across all panels."
    )
    fig.tight_layout(rect=(0, 0.06, 1, 0.98))
    # fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=9)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = out_path.with_suffix(".png")
    pdf_path = out_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        choices=["swebenchlite", "swebenchverified", "both"],
        help="Which dataset to plot (produces ONE figure). Use 'both' to overlay Lite+Verified.",
    )
    parser.add_argument("--reports-dir", type=Path, default=PROJECT_ROOT / "sb-cli-reports")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dpi", type=int, default=200)

    parser.add_argument("--palette", type=str, default="Set2")
    parser.add_argument("--alpha", type=float, default=0.92)
    parser.add_argument("--point-size", type=float, default=130.0)
    parser.add_argument("--label-fontsize", type=int, default=10)

    parser.add_argument("--n-boot", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--equiv", type=float, default=5.0, help="Equivalence margin in percentage points (pp).")

    parser.add_argument("--no-k-trend", dest="show_k_trend", action="store_false")
    parser.set_defaults(show_k_trend=True)

    parser.add_argument(
        "--layout",
        type=str,
        default="grid",
        choices=["grid", "overlay"],
        help="Only used when --dataset=both: 'grid' (2x2 facets) or 'overlay' (two datasets in one panel).",
    )

    args = parser.parse_args()

    out_path = args.out
    if out_path is None:
        if args.dataset == "both":
            out_path = PROJECT_ROOT / ("figures/fig5_delta_plane_grid.png" if args.layout == "grid" else "figures/fig5_delta_plane_overlay.png")
        else:
            out_path = PROJECT_ROOT / f"figures/fig5_delta_plane_{args.dataset}.png"

    if args.dataset == "both":
        if args.layout == "grid":
            plot_both_datasets_grid(
                reports_dir=args.reports_dir,
                output_dir=args.output_dir,
                out_path=Path(out_path),
                dpi=int(args.dpi),
                palette=str(args.palette),
                alpha=float(args.alpha),
                point_size=float(args.point_size),
                label_fontsize=int(args.label_fontsize),
                n_boot=int(args.n_boot),
                seed=int(args.seed),
                equiv_pp=float(args.equiv),
                show_k_trend=bool(args.show_k_trend),
            )
        else:
            plot_both_datasets_overlay(
                reports_dir=args.reports_dir,
                output_dir=args.output_dir,
                out_path=Path(out_path),
                dpi=int(args.dpi),
                palette=str(args.palette),
                alpha=float(args.alpha),
                point_size=float(args.point_size),
                label_fontsize=int(args.label_fontsize),
                n_boot=int(args.n_boot),
                seed=int(args.seed),
                equiv_pp=float(args.equiv),
                show_k_trend=bool(args.show_k_trend),
            )
    else:
        plot_dataset(
            reports_dir=args.reports_dir,
            output_dir=args.output_dir,
            dataset=str(args.dataset),
            out_path=Path(out_path),
            dpi=int(args.dpi),
            palette=str(args.palette),
            alpha=float(args.alpha),
            point_size=float(args.point_size),
            label_fontsize=int(args.label_fontsize),
            n_boot=int(args.n_boot),
            seed=int(args.seed),
            equiv_pp=float(args.equiv),
            show_k_trend=bool(args.show_k_trend),
        )


if __name__ == "__main__":
    main()
