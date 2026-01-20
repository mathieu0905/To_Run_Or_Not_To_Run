#!/usr/bin/env python3
"""
RQ1: Effectiveness - Impact of Execution Permissions on Fix Success Rate

Research Question: What is the impact of three execution permissions (Run-Free, Run-Less, Run-Full) on agent fix success rate?
Is there a monotonic relationship of "more execution leads to better performance"?
"""

import sys
from pathlib import Path

# Add common module path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, load_pass_rates, get_aggregated_stats, sort_modes
)


def generate_pass_rate_table(pass_rates: dict) -> str:
    """Generate Pass Rate table"""
    lines = []
    lines.append("## Pass Rate Comparison Table")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Resolved | Total | Pass Rate |")
        lines.append("|-------|------|----------|-------|-----------|")

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                resolved = data["resolved"]
                total = data["total"]
                rate = f"{resolved * 100 / total:.1f}%" if total > 0 else "N/A"
                lines.append(f"| {agent} | {mode} | {resolved} | {total} | {rate} |")

        lines.append("")

    return "\n".join(lines)


def generate_comparison_table(pass_rates: dict) -> str:
    """Generate difference comparison table (ΔPass)"""
    lines = []
    lines.append("## Difference Analysis Table (ΔPass)")
    lines.append("")
    lines.append("Using run_full as baseline, calculate Pass Rate differences for each mode.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Pass Rate | vs run_full | ΔPass |")
        lines.append("|-------|------|-----------|-------------|-------|")

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]

            # Get run_full pass rate as baseline
            run_full_data = modes.get("run_full", {})
            run_full_rate = run_full_data.get("resolved", 0) / run_full_data.get("total", 1) * 100 if run_full_data.get("total", 0) > 0 else 0

            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                resolved = data["resolved"]
                total = data["total"]
                rate = resolved * 100 / total if total > 0 else 0
                delta = rate - run_full_rate
                delta_str = f"+{delta:.1f}%" if delta >= 0 else f"{delta:.1f}%"

                if mode == "run_full":
                    delta_str = "-"

                lines.append(f"| {agent} | {mode} | {rate:.1f}% | {run_full_rate:.1f}% | {delta_str} |")

        lines.append("")

    return "\n".join(lines)


def generate_monotonicity_analysis(pass_rates: dict) -> str:
    """Generate monotonicity analysis"""
    lines = []
    lines.append("## Monotonicity Analysis")
    lines.append("")
    lines.append("Test whether there exists a monotonic relationship of 'more execution leads to better performance'.")
    lines.append("")
    lines.append("Execution permission ordering (from less to more): run_free < run_less_k1 < run_less_k3 < run_cost ≈ run_full")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]
            lines.append(f"**{agent}:**")

            # Get pass rates sorted by execution permission
            rates = []
            for mode in MODE_ORDER:
                if mode in modes:
                    data = modes[mode]
                    rate = data["resolved"] / data["total"] * 100 if data["total"] > 0 else 0
                    rates.append((mode, rate))

            # Check monotonicity
            is_monotonic = True
            for i in range(1, len(rates)):
                if rates[i][1] < rates[i-1][1]:
                    is_monotonic = False
                    break

            rate_str = " → ".join([f"{m}: {r:.1f}%" for m, r in rates])
            lines.append(f"- {rate_str}")

            if is_monotonic:
                lines.append(f"- Conclusion: ✓ Monotonic increasing relationship exists")
            else:
                lines.append(f"- Conclusion: ✗ No monotonic increasing relationship")

            lines.append("")

    return "\n".join(lines)


def generate_key_findings(pass_rates: dict) -> str:
    """Generate key findings"""
    lines = []
    lines.append("## Key Findings")
    lines.append("")

    findings = []

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]

            run_free = modes.get("run_free", {})
            run_full = modes.get("run_full", {})

            if run_free.get("total", 0) > 0 and run_full.get("total", 0) > 0:
                free_rate = run_free["resolved"] / run_free["total"] * 100
                full_rate = run_full["resolved"] / run_full["total"] * 100
                diff = full_rate - free_rate

                findings.append({
                    "dataset": dataset_name,
                    "agent": agent,
                    "free_rate": free_rate,
                    "full_rate": full_rate,
                    "diff": diff
                })

    # Summarize findings
    lines.append("### 1. Run-Free vs Run-Full Comparison")
    lines.append("")
    for f in findings:
        diff_str = f"+{f['diff']:.1f}%" if f['diff'] >= 0 else f"{f['diff']:.1f}%"
        lines.append(f"- **{f['agent']}** ({f['dataset']}): Run-Free {f['free_rate']:.1f}% vs Run-Full {f['full_rate']:.1f}% (Δ = {diff_str})")
    lines.append("")

    # Calculate average difference
    avg_diff = sum(f['diff'] for f in findings) / len(findings) if findings else 0
    lines.append(f"### 2. Average Difference")
    lines.append("")
    lines.append(f"- Average improvement of Run-Full compared to Run-Free: **{avg_diff:.1f}%**")
    lines.append("")

    # Determine if execution is necessary
    lines.append("### 3. Conclusion")
    lines.append("")
    if abs(avg_diff) < 5:
        lines.append("- Execution permission has **minor impact** on fix success rate (< 5%)")
        lines.append("- Run-Free mode already achieves near-optimal performance")
        lines.append("- Execution environment may **not be a necessary condition**, but rather an 'engineering shortcut'")
    else:
        lines.append("- Execution permission has **significant impact** on fix success rate (≥ 5%)")
        lines.append("- Execution feedback makes important contributions to Agent fix capability")

    return "\n".join(lines)


def main():
    print("Loading data...")

    # Load pass rate data
    pass_rates = load_pass_rates()

    if not pass_rates:
        print("Error: Unable to load pass rate data, please ensure sb-cli-reports directory exists")
        return

    # Generate data file
    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq1.md"

    content = []
    content.append("# RQ1: Effectiveness - Data Tables")
    content.append("")
    content.append("Analysis data on the impact of execution permissions on fix success rate.")
    content.append("")
    content.append(generate_pass_rate_table(pass_rates))
    content.append(generate_comparison_table(pass_rates))
    content.append(generate_monotonicity_analysis(pass_rates))
    content.append(generate_key_findings(pass_rates))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"Data saved to: {data_file}")


if __name__ == "__main__":
    main()
