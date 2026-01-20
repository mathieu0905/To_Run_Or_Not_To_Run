#!/usr/bin/env python3
"""Figure 1: Pass rate comparison with 95% Wilson confidence intervals.

Data source:
- sb-cli-reports/*.json
- pass_rate = resolved_instances / completed_instances

Output:
- figures/fig1_passrate_ci.png (default; also writes figures/fig1_passrate_ci.pdf)

Run:
  python figures/fig1_passrate_ci.py

Notes:
- By default, the y-axis range is auto-zoomed (shared across subplots) to avoid
  the bars looking completely flat. Use `--ylim 0 100` to force the full range.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


MODE_ORDER = ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"]
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


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if total <= 0:
        return (0.0, 0.0)

    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    margin = (z * ((p * (1.0 - p) + (z * z) / (4.0 * total)) / total) ** 0.5) / denom

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (lower, upper)


def _detect_dataset(filename_lower: str) -> str | None:
    if "swe-bench_lite" in filename_lower:
        return "swebenchlite"
    if "swe-bench_verified" in filename_lower:
        return "swebenchverified"
    return None


def load_pass_rates(reports_dir: Path) -> dict:
    """Load resolved/completed from sb-cli report files."""
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
        resolved = int(report.get("resolved_instances", 0))
        completed = int(report.get("completed_instances", 0))

        if mode in data[dataset][agent]:
            raise ValueError(f"Duplicate report for {dataset}/{agent}/{mode}: {path}")

        data[dataset][agent][mode] = {
            "resolved": resolved,
            "total": completed,
            "path": str(path),
        }

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


def _round_down(x: float, step: float) -> float:
    return step * (x // step)


def _round_up(x: float, step: float) -> float:
    return step * ((x + step - 1e-9) // step)


def compute_auto_ylim(pass_rate_data: dict, pad_pct: float = 1.0) -> tuple[float, float]:
    """Compute a shared y-lim based on Wilson CI bounds (in percent)."""
    lows: list[float] = []
    highs: list[float] = []

    for dataset in DATASET_ORDER:
        for agent in AGENT_ORDER:
            for mode in MODE_ORDER:
                cell = pass_rate_data[dataset][agent][mode]
                k = int(cell["resolved"])
                n = int(cell["total"])
                lo, hi = wilson_ci(k, n)
                lows.append(100.0 * lo)
                highs.append(100.0 * hi)

    ymin = max(0.0, min(lows) - pad_pct)
    ymax = min(100.0, max(highs) + pad_pct)

    # Use nice round ticks.
    ymin = _round_down(ymin, 5.0)
    ymax = _round_up(ymax, 5.0)

    # Ensure a reasonable window; fall back to full range if something goes wrong.
    if ymax - ymin < 10.0:
        return (0.0, 100.0)

    return (ymin, ymax)


def plot_fig1(
    reports_dir: Path,
    out_path: Path,
    dpi: int,
    palette: str,
    alpha: float,
    bar_width: float,
    ylim: tuple[float, float] | None,
) -> None:
    data = load_pass_rates(reports_dir)

    # Softer palette by default; keep colors consistent across modes.
    cmap = plt.get_cmap(palette)
    mode_colors = {mode: cmap(i) for i, mode in enumerate(MODE_ORDER)}

    if ylim is None:
        ylim = compute_auto_ylim(data)

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 7), sharey=True)

    x = list(range(len(MODE_ORDER)))

    for r, dataset in enumerate(DATASET_ORDER):
        for c, agent in enumerate(AGENT_ORDER):
            ax = axes[r][c]

            rates_pct: list[float] = []
            err_low: list[float] = []
            err_high: list[float] = []
            totals: list[int] = []

            for mode in MODE_ORDER:
                cell = data[dataset][agent][mode]
                k = int(cell["resolved"])
                n = int(cell["total"])
                totals.append(n)

                rate = 100.0 * k / n if n > 0 else 0.0
                lo, hi = wilson_ci(k, n)
                lo_pct, hi_pct = 100.0 * lo, 100.0 * hi

                rates_pct.append(rate)
                err_low.append(rate - lo_pct)
                err_high.append(hi_pct - rate)

            bars = ax.bar(
                x,
                rates_pct,
                width=bar_width,
                color=[mode_colors[m] for m in MODE_ORDER],
                alpha=alpha,
                yerr=[err_low, err_high],
                capsize=3,
                ecolor="black",
                linewidth=0,
            )

            ax.set_xticks(x)
            ax.set_xticklabels([MODE_LABEL[m] for m in MODE_ORDER])
            ax.set_ylim(ylim)
            ax.grid(axis="y", alpha=0.25)

            if c == 0:
                ax.set_ylabel("Pass Rate (%)")

            ax.set_title(f"{DATASET_LABEL[dataset]} — {AGENT_LABEL[agent]}")

            # Percent labels on top of the CI error bars.
            for i, rect in enumerate(bars):
                height = float(rect.get_height())
                label = f"{height:.0f}%" if totals[i] == 100 else f"{height:.1f}%"

                y_text = height + err_high[i] + 0.6
                y_text = min(y_text, float(ylim[1]) - 0.5)

                ax.text(
                    rect.get_x() + rect.get_width() / 2.0,
                    y_text,
                    label,
                    ha="center",
                    va="bottom",
                    fontsize=9,
                )

    # If we are not using the full y-range, add a clear note.
    note = None
    if float(ylim[0]) > 0.0 or float(ylim[1]) < 100.0:
        note = f"Note: y-axis is truncated to [{ylim[0]:.0f}, {ylim[1]:.0f}] for readability."

    if note:
        fig.tight_layout(rect=(0, 0.04, 1, 1))
        fig.text(0.5, 0.01, note, ha="center", va="bottom", fontsize=9)
    else:
        fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = out_path.with_suffix(".png")
    pdf_path = out_path.with_suffix(".pdf")
    fig.savefig(png_path, dpi=dpi, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", type=Path, default=Path("sb-cli-reports"))
    parser.add_argument("--out", type=Path, default=Path("figures/fig1_passrate_ci.png"))
    parser.add_argument("--dpi", type=int, default=200)

    parser.add_argument(
        "--palette",
        type=str,
        default="Set2",
        help="Matplotlib colormap name (e.g., Set2, tab10, Pastel1).",
    )
    parser.add_argument("--alpha", type=float, default=0.9, help="Bar fill alpha (0..1).")
    parser.add_argument("--bar-width", type=float, default=0.65, help="Bar width (default: 0.65).")
    parser.add_argument(
        "--ylim",
        type=float,
        nargs=2,
        default=None,
        metavar=("YMIN", "YMAX"),
        help="Force shared y-limits. Example: --ylim 0 100",
    )

    args = parser.parse_args()

    ylim = tuple(args.ylim) if args.ylim is not None else None

    plot_fig1(
        args.reports_dir,
        args.out,
        dpi=args.dpi,
        palette=args.palette,
        alpha=args.alpha,
        bar_width=args.bar_width,
        ylim=ylim,
    )


if __name__ == "__main__":
    main()
