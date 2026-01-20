#!/usr/bin/env python3
"""
RQ2: Efficiency - Cost and Efficiency Pareto Frontier

Research Question: How much impact do different execution permissions have on cost (tokens), turns, and time?
Does a Pareto frontier exist? Can Run-Less achieve success rates close to Run-Full at significantly lower cost?
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, load_pass_rates, get_aggregated_stats, sort_modes
)


def generate_cost_table(stats: dict) -> str:
    """Generate cost comparison table"""
    lines = []
    lines.append("## Cost Comparison Table")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Avg Tokens | Avg Turns | Avg Time (s) | High-Cost Exec | Low-Cost Exec |")
        lines.append("|-------|------|------------|-----------|--------------|----------------|---------------|")

        for agent in sorted(stats[dataset].keys()):
            modes = stats[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                lines.append(f"| {agent} | {mode} | {data['avg_total_tokens']:,} | {data['avg_turns']:.1f} | {data['avg_time_sec']:.1f} | {data['avg_high_cost_exec']:.1f} | {data['avg_low_cost_exec']:.1f} |")

        lines.append("")

    return "\n".join(lines)


def generate_relative_change_table(stats: dict) -> str:
    """Generate relative change percentage table (baseline: run_full)"""
    lines = []
    lines.append("## Relative Change Percentage Table (vs run_full)")
    lines.append("")
    lines.append("Using run_full as baseline, calculate cost changes for each mode. Negative values indicate cost reduction.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | ΔTokens | ΔTurns | ΔTime |")
        lines.append("|-------|------|---------|--------|-------|")

        for agent in sorted(stats[dataset].keys()):
            modes = stats[dataset][agent]

            # Get run_full as baseline
            run_full = modes.get("run_full", {})
            if not run_full:
                continue

            base_tokens = run_full.get("avg_total_tokens", 1)
            base_turns = run_full.get("avg_turns", 1)
            base_time = run_full.get("avg_time_sec", 1)

            for mode in sort_modes(modes.keys()):
                data = modes[mode]

                delta_tokens = (data["avg_total_tokens"] - base_tokens) / base_tokens * 100
                delta_turns = (data["avg_turns"] - base_turns) / base_turns * 100
                delta_time = (data["avg_time_sec"] - base_time) / base_time * 100

                if mode == "run_full":
                    lines.append(f"| {agent} | {mode} | - | - | - |")
                else:
                    dt = f"+{delta_tokens:.1f}%" if delta_tokens >= 0 else f"{delta_tokens:.1f}%"
                    dtu = f"+{delta_turns:.1f}%" if delta_turns >= 0 else f"{delta_turns:.1f}%"
                    dti = f"+{delta_time:.1f}%" if delta_time >= 0 else f"{delta_time:.1f}%"
                    lines.append(f"| {agent} | {mode} | {dt} | {dtu} | {dti} |")

        lines.append("")

    return "\n".join(lines)


def generate_pareto_data(stats: dict, pass_rates: dict) -> str:
    """Generate Pareto frontier data (Pass Rate vs Avg Total Tokens)"""
    lines = []
    lines.append("## Pareto Frontier Data")
    lines.append("")
    lines.append("Pass Rate vs Avg Total Tokens data points for plotting Pareto frontier.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Pass Rate (%) | Avg Tokens | Pareto Optimal? |")
        lines.append("|-------|------|---------------|------------|-----------------|")

        # Collect all data points
        data_points = []
        for agent in sorted(stats[dataset].keys()):
            if agent not in pass_rates[dataset]:
                continue
            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            for mode in sort_modes(modes.keys()):
                if mode not in pr_modes:
                    continue
                s = modes[mode]
                pr = pr_modes[mode]
                rate = pr["resolved"] / pr["total"] * 100 if pr["total"] > 0 else 0
                tokens = s["avg_total_tokens"]
                data_points.append({
                    "agent": agent,
                    "mode": mode,
                    "rate": rate,
                    "tokens": tokens
                })

        # Determine Pareto optimality
        for dp in data_points:
            is_pareto = True
            for other in data_points:
                # If another point exists with higher rate and lower tokens, current point is not Pareto optimal
                if other["rate"] > dp["rate"] and other["tokens"] < dp["tokens"]:
                    is_pareto = False
                    break
                # If another point exists with same rate but lower tokens
                if other["rate"] == dp["rate"] and other["tokens"] < dp["tokens"]:
                    is_pareto = False
                    break
            dp["pareto"] = is_pareto

        for dp in data_points:
            pareto_str = "✓" if dp["pareto"] else ""
            lines.append(f"| {dp['agent']} | {dp['mode']} | {dp['rate']:.1f} | {dp['tokens']:,} | {pareto_str} |")

        lines.append("")

    return "\n".join(lines)


def generate_efficiency_analysis(stats: dict, pass_rates: dict) -> str:
    """Generate efficiency analysis"""
    lines = []
    lines.append("## Efficiency Analysis")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(stats[dataset].keys()):
            if agent not in pass_rates[dataset]:
                continue
            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            lines.append(f"**{agent}:**")
            lines.append("")

            # Calculate run_free efficiency relative to run_full
            run_free_s = modes.get("run_free", {})
            run_full_s = modes.get("run_full", {})
            run_free_pr = pr_modes.get("run_free", {})
            run_full_pr = pr_modes.get("run_full", {})

            if run_free_s and run_full_s and run_free_pr and run_full_pr:
                free_rate = run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr["total"] > 0 else 0
                full_rate = run_full_pr["resolved"] / run_full_pr["total"] * 100 if run_full_pr["total"] > 0 else 0

                token_saving = (run_full_s["avg_total_tokens"] - run_free_s["avg_total_tokens"]) / run_full_s["avg_total_tokens"] * 100
                time_saving = (run_full_s["avg_time_sec"] - run_free_s["avg_time_sec"]) / run_full_s["avg_time_sec"] * 100
                rate_diff = full_rate - free_rate

                lines.append(f"- Run-Free vs Run-Full:")
                lines.append(f"  - Pass Rate 差异: {rate_diff:+.1f}%")
                lines.append(f"  - Token 节省: {token_saving:.1f}%")
                lines.append(f"  - 时间节省: {time_saving:.1f}%")

                # Calculate efficiency ratio
                if rate_diff != 0:
                    efficiency = token_saving / abs(rate_diff)
                    lines.append(f"  - Efficiency ratio (Token saving/Pass difference): {efficiency:.1f}")
                lines.append("")

    return "\n".join(lines)


def generate_key_findings(stats: dict, pass_rates: dict) -> str:
    """Generate key findings"""
    lines = []
    lines.append("## Key Findings")
    lines.append("")

    # Collect all data
    all_data = []
    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue
        for agent in stats[dataset].keys():
            if agent not in pass_rates[dataset]:
                continue
            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            run_free_s = modes.get("run_free", {})
            run_full_s = modes.get("run_full", {})
            run_free_pr = pr_modes.get("run_free", {})
            run_full_pr = pr_modes.get("run_full", {})

            if run_free_s and run_full_s:
                all_data.append({
                    "dataset": dataset_name,
                    "agent": agent,
                    "free_tokens": run_free_s["avg_total_tokens"],
                    "full_tokens": run_full_s["avg_total_tokens"],
                    "free_time": run_free_s["avg_time_sec"],
                    "full_time": run_full_s["avg_time_sec"],
                    "free_rate": run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr.get("total", 0) > 0 else 0,
                    "full_rate": run_full_pr["resolved"] / run_full_pr["total"] * 100 if run_full_pr.get("total", 0) > 0 else 0,
                })

    lines.append("### 1. Token Consumption Comparison")
    lines.append("")
    for d in all_data:
        saving = (d["full_tokens"] - d["free_tokens"]) / d["full_tokens"] * 100
        lines.append(f"- **{d['agent']}** ({d['dataset']}): Run-Free {d['free_tokens']:,} vs Run-Full {d['full_tokens']:,} (saving {saving:.1f}%)")
    lines.append("")

    lines.append("### 2. Time Consumption Comparison")
    lines.append("")
    for d in all_data:
        saving = (d["full_time"] - d["free_time"]) / d["full_time"] * 100
        lines.append(f"- **{d['agent']}** ({d['dataset']}): Run-Free {d['free_time']:.0f}s vs Run-Full {d['full_time']:.0f}s (saving {saving:.1f}%)")
    lines.append("")

    lines.append("### 3. Cost-Benefit Conclusion")
    lines.append("")

    # Calculate average savings
    avg_token_saving = sum((d["full_tokens"] - d["free_tokens"]) / d["full_tokens"] * 100 for d in all_data) / len(all_data) if all_data else 0
    avg_time_saving = sum((d["full_time"] - d["free_time"]) / d["full_time"] * 100 for d in all_data) / len(all_data) if all_data else 0
    avg_rate_diff = sum(d["full_rate"] - d["free_rate"] for d in all_data) / len(all_data) if all_data else 0

    lines.append(f"- Average Token saving: **{avg_token_saving:.1f}%**")
    lines.append(f"- Average time saving: **{avg_time_saving:.1f}%**")
    lines.append(f"- Average Pass Rate difference: **{avg_rate_diff:+.1f}%**")
    lines.append("")
    lines.append(f"**Conclusion**: Run-Free mode trades {abs(avg_rate_diff):.1f}% performance loss for {avg_token_saving:.0f}% cost savings, making it the most cost-effective choice.")

    return "\n".join(lines)


def main():
    print("Loading data...")

    results = load_all_results()
    stats = get_aggregated_stats(results)
    pass_rates = load_pass_rates()

    if not stats:
        print("Error: Unable to load experimental results data")
        return

    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq2.md"

    content = []
    content.append("# RQ2: Efficiency - Data Tables")
    content.append("")
    content.append("Cost and efficiency Pareto frontier analysis data.")
    content.append("")
    content.append(generate_cost_table(stats))
    content.append(generate_relative_change_table(stats))
    content.append(generate_pareto_data(stats, pass_rates))
    content.append(generate_efficiency_analysis(stats, pass_rates))
    content.append(generate_key_findings(stats, pass_rates))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"Data saved to: {data_file}")


if __name__ == "__main__":
    main()
