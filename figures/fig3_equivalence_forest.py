#!/usr/bin/env python3
"""Figure 3: Equivalence-style forest plot (ΔPass vs Run-Full).

Facets:
- Rows: dataset (SWE-bench Lite / Verified)
- Cols: agent (Claude Code / Codex)

Comparisons (all vs run_full):
- run_free, run_less_k1, run_less_k3, run_cost

Effect size:
- Delta Pass Rate (pp) = PassRate(mode) - PassRate(run_full)

Uncertainty:
- 90% CI via paired bootstrap on instance IDs from sb-cli-reports
  (default: n_boot=10000, seed=0).

Run:
  python figures/fig3_equivalence_forest.py

Output:
  figures/fig3_equivalence_forest.png
  figures/fig3_equivalence_forest.pdf
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory


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
    resolved_instances: int
    completed_instances: int


def _detect_dataset(filename_lower: str) -> str | None:
    if "swe-bench_lite" in filename_lower:
        return "swebenchlite"
    if "swe-bench_verified" in filename_lower:
        return "swebenchverified"
    return None


def load_reports(reports_dir: Path) -> dict:
    """Load instance-level ids from sb-cli-reports."""
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

        resolved_instances = int(report.get("resolved_instances", len(resolved_ids)))
        completed_instances = int(report.get("completed_instances", len(completed_ids)))

        if mode in data[dataset][agent]:
            raise ValueError(f"Duplicate report for {dataset}/{agent}/{mode}: {path}")

        data[dataset][agent][mode] = Report(
            completed_ids=list(completed_ids),
            completed_set=set(completed_ids),
            resolved_set=set(resolved_ids),
            resolved_instances=resolved_instances,
            completed_instances=completed_instances,
        )

    # Sanity check: ensure all expected cells exist.
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

    full_success = [1 if inst_id in full_rep.resolved_set else 0 for inst_id in ids]
    mode_success = [
        1 if (inst_id in mode_rep.completed_set and inst_id in mode_rep.resolved_set) else 0 for inst_id in ids
    ]

    delta = (sum(mode_success) / n - sum(full_success) / n) * 100.0 if n else 0.0

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


def plot_fig3(
    reports_dir: Path,
    out_path: Path,
    dpi: int,
    palette: str,
    alpha: float,
    xlim: tuple[float, float],
    n_boot: int,
    seed: int,
    equivalence_margin_pp: float,
    annotate: bool,
) -> None:
    reports = load_reports(reports_dir)

    cmap = plt.get_cmap(palette)
    mode_colors = {mode: cmap(i) for i, mode in enumerate(MODE_ORDER)}

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 7), sharey=True)

    y_pos = list(range(len(COMPARE_MODES)))

    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            ax = axes[r][c]

            full_rep = reports[dataset][agent]["run_full"]

            # Equivalence band and reference lines.
            ax.axvspan(
                -equivalence_margin_pp,
                equivalence_margin_pp,
                color="gray",
                alpha=0.15,
                zorder=0,
            )
            ax.axvline(0.0, color="black", linewidth=1.0, alpha=0.6, zorder=1)
            ax.axvline(-equivalence_margin_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)
            ax.axvline(equivalence_margin_pp, color="gray", linestyle="--", linewidth=1.0, alpha=0.7, zorder=1)

            # Plot rows.
            for i, mode in enumerate(COMPARE_MODES):
                rep = reports[dataset][agent][mode]
                delta, lo, hi, n_ids = paired_bootstrap_delta_pp(rep, full_rep, n_boot=n_boot, seed=seed)

                # CI line.
                ax.hlines(i, lo, hi, color="black", linewidth=2.0, zorder=2)

                # Point estimate.
                ax.scatter(
                    [delta],
                    [i],
                    s=70,
                    color=mode_colors[mode],
                    alpha=alpha,
                    edgecolors="white",
                    linewidths=0.8,
                    zorder=3,
                )

                if annotate:
                    txt = f"Delta={delta:+.1f}pp [{lo:+.1f}, {hi:+.1f}]"
                    trans = blended_transform_factory(ax.transAxes, ax.transData)
                    ax.text(
                        0.98,
                        i,
                        txt,
                        transform=trans,
                        ha="right",
                        va="center",
                        fontsize=8,
                        color="black",
                    )

            ax.set_xlim(xlim)
            ax.set_xticks([xlim[0], -equivalence_margin_pp, 0.0, equivalence_margin_pp, xlim[1]])
            ax.grid(axis="x", alpha=0.2)

            ax.set_yticks(y_pos)
            ax.set_yticklabels([MODE_LABEL[m] for m in COMPARE_MODES])
            ax.invert_yaxis()

            ax.set_title(f"{DATASET_LABEL[dataset]} — {AGENT_LABEL[agent]}")

            if r == 1:
                ax.set_xlabel("Delta Pass Rate (pp) vs Full")
            if c == 0:
                ax.set_ylabel("Mode (vs Full)")

    note = (
        f"Note: 90% CI via paired bootstrap (n_boot={n_boot}, seed={seed}) on completed_ids; "
        f"gray band denotes equivalence margin ±{equivalence_margin_pp:.0f}pp."
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
    parser.add_argument("--out", type=Path, default=Path("figures/fig3_equivalence_forest.png"))
    parser.add_argument("--dpi", type=int, default=200)

    parser.add_argument("--palette", type=str, default="Set2")
    parser.add_argument("--alpha", type=float, default=0.9)

    parser.add_argument("--xlim", type=float, nargs=2, default=(-10.0, 10.0), metavar=("XMIN", "XMAX"))
    parser.add_argument("--n-boot", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--equiv", type=float, default=5.0, help="Equivalence margin in percentage points (pp).")

    parser.add_argument("--no-annotate", dest="annotate", action="store_false")
    parser.set_defaults(annotate=True)

    args = parser.parse_args()

    plot_fig3(
        reports_dir=args.reports_dir,
        out_path=args.out,
        dpi=args.dpi,
        palette=args.palette,
        alpha=args.alpha,
        xlim=(float(args.xlim[0]), float(args.xlim[1])),
        n_boot=int(args.n_boot),
        seed=int(args.seed),
        equivalence_margin_pp=float(args.equiv),
        annotate=bool(args.annotate),
    )


if __name__ == "__main__":
    main()
