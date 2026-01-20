#!/usr/bin/env python3
"""
RQ4: Agent Sensitivity - Sensitivity Differences Between Different Agents

Research Question: Is the impact of execution permissions consistent across different agents?
Why do some agents have large cost changes while others have small cost changes?
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, load_pass_rates, get_aggregated_stats, sort_modes
)


def generate_delta_comparison_table(stats: dict, pass_rates: dict) -> str:
    """Generate ΔCost% vs ΔPass comparison table"""
    lines = []
    lines.append("## ΔCost% vs ΔPass Comparison Table")
    lines.append("")
    lines.append("Using run_free as baseline, calculate changes for each mode relative to run_free.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Pass Rate | ΔPass | Avg Tokens | ΔTokens | Avg Time | ΔTime |")
        lines.append("|-------|------|-----------|-------|------------|---------|----------|-------|")

        for agent in sorted(stats[dataset].keys()):
            if agent not in pass_rates[dataset]:
                continue

            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            # Get run_free as baseline
            run_free_s = modes.get("run_free", {})
            run_free_pr = pr_modes.get("run_free", {})

            if not run_free_s or not run_free_pr:
                continue

            base_tokens = run_free_s.get("avg_total_tokens", 1)
            base_time = run_free_s.get("avg_time_sec", 1)
            base_rate = run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr.get("total", 0) > 0 else 0

            for mode in sort_modes(modes.keys()):
                if mode not in pr_modes:
                    continue

                s = modes[mode]
                pr = pr_modes[mode]

                rate = pr["resolved"] / pr["total"] * 100 if pr.get("total", 0) > 0 else 0
                delta_rate = rate - base_rate

                delta_tokens = (s["avg_total_tokens"] - base_tokens) / base_tokens * 100
                delta_time = (s["avg_time_sec"] - base_time) / base_time * 100

                if mode == "run_free":
                    lines.append(f"| {agent} | {mode} | {rate:.1f}% | - | {s['avg_total_tokens']:,} | - | {s['avg_time_sec']:.0f}s | - |")
                else:
                    dr = f"+{delta_rate:.1f}%" if delta_rate >= 0 else f"{delta_rate:.1f}%"
                    dt = f"+{delta_tokens:.1f}%" if delta_tokens >= 0 else f"{delta_tokens:.1f}%"
                    dti = f"+{delta_time:.1f}%" if delta_time >= 0 else f"{delta_time:.1f}%"
                    lines.append(f"| {agent} | {mode} | {rate:.1f}% | {dr} | {s['avg_total_tokens']:,} | {dt} | {s['avg_time_sec']:.0f}s | {dti} |")

        lines.append("")

    return "\n".join(lines)


def generate_agent_characteristics_table(stats: dict, pass_rates: dict) -> str:
    """Generate Agent characteristics comparison table"""
    lines = []
    lines.append("## Agent Characteristics Comparison Table")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        agent_data = []
        for agent in sorted(stats[dataset].keys()):
            if agent not in pass_rates[dataset]:
                continue

            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            run_free_s = modes.get("run_free", {})
            run_full_s = modes.get("run_full", {})
            run_free_pr = pr_modes.get("run_free", {})
            run_full_pr = pr_modes.get("run_full", {})

            if run_free_s and run_full_s and run_free_pr and run_full_pr:
                free_rate = run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr.get("total", 0) > 0 else 0
                full_rate = run_full_pr["resolved"] / run_full_pr["total"] * 100 if run_full_pr.get("total", 0) > 0 else 0

                token_change = (run_full_s["avg_total_tokens"] - run_free_s["avg_total_tokens"]) / run_free_s["avg_total_tokens"] * 100
                time_change = (run_full_s["avg_time_sec"] - run_free_s["avg_time_sec"]) / run_free_s["avg_time_sec"] * 100
                rate_change = full_rate - free_rate

                # Calculate input/output token ratio
                free_input_ratio = run_free_s["avg_input_tokens"] / run_free_s["avg_total_tokens"] * 100 if run_free_s["avg_total_tokens"] > 0 else 0
                full_input_ratio = run_full_s["avg_input_tokens"] / run_full_s["avg_total_tokens"] * 100 if run_full_s["avg_total_tokens"] > 0 else 0

                agent_data.append({
                    "agent": agent,
                    "free_rate": free_rate,
                    "full_rate": full_rate,
                    "rate_change": rate_change,
                    "free_tokens": run_free_s["avg_total_tokens"],
                    "full_tokens": run_full_s["avg_total_tokens"],
                    "token_change": token_change,
                    "free_time": run_free_s["avg_time_sec"],
                    "full_time": run_full_s["avg_time_sec"],
                    "time_change": time_change,
                    "free_input_ratio": free_input_ratio,
                    "full_input_ratio": full_input_ratio
                })

        lines.append("| Metric | " + " | ".join([d["agent"] for d in agent_data]) + " |")
        lines.append("|------|" + "|".join(["------" for _ in agent_data]) + "|")

        lines.append("| Run-Free Pass Rate | " + " | ".join([f"{d['free_rate']:.1f}%" for d in agent_data]) + " |")
        lines.append("| Run-Full Pass Rate | " + " | ".join([f"{d['full_rate']:.1f}%" for d in agent_data]) + " |")
        lines.append("| ΔPass (Full-Free) | " + " | ".join([f"{d['rate_change']:+.1f}%" for d in agent_data]) + " |")
        lines.append("| Run-Free Tokens | " + " | ".join([f"{d['free_tokens']:,}" for d in agent_data]) + " |")
        lines.append("| Run-Full Tokens | " + " | ".join([f"{d['full_tokens']:,}" for d in agent_data]) + " |")
        lines.append("| ΔTokens (Full-Free) | " + " | ".join([f"+{d['token_change']:.1f}%" for d in agent_data]) + " |")
        lines.append("| Run-Free Time | " + " | ".join([f"{d['free_time']:.0f}s" for d in agent_data]) + " |")
        lines.append("| Run-Full Time | " + " | ".join([f"{d['full_time']:.0f}s" for d in agent_data]) + " |")
        lines.append("| ΔTime (Full-Free) | " + " | ".join([f"+{d['time_change']:.1f}%" for d in agent_data]) + " |")
        lines.append("| Free Input Token % | " + " | ".join([f"{d['free_input_ratio']:.1f}%" for d in agent_data]) + " |")
        lines.append("| Full Input Token % | " + " | ".join([f"{d['full_input_ratio']:.1f}%" for d in agent_data]) + " |")

        lines.append("")

    return "\n".join(lines)


def generate_token_breakdown_table(stats: dict) -> str:
    """Generate Token consumption breakdown table"""
    lines = []
    lines.append("## Token Consumption Breakdown")
    lines.append("")
    lines.append("Analyze Input Token and Output Token distribution.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Input Tokens | Output Tokens | Total | Input % | Output % |")
        lines.append("|-------|------|--------------|---------------|-------|---------|----------|")

        for agent in sorted(stats[dataset].keys()):
            modes = stats[dataset][agent]
            for mode in sort_modes(modes.keys()):
                s = modes[mode]
                total = s["avg_total_tokens"]
                input_t = s["avg_input_tokens"]
                output_t = s["avg_output_tokens"]
                input_pct = input_t / total * 100 if total > 0 else 0
                output_pct = output_t / total * 100 if total > 0 else 0

                lines.append(f"| {agent} | {mode} | {input_t:,} | {output_t:,} | {total:,} | {input_pct:.1f}% | {output_pct:.1f}% |")

        lines.append("")

    return "\n".join(lines)


def generate_sensitivity_analysis(stats: dict, pass_rates: dict) -> str:
    """Generate sensitivity analysis"""
    lines = []
    lines.append("## Sensitivity Analysis")
    lines.append("")

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
                free_rate = run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr.get("total", 0) > 0 else 0
                full_rate = run_full_pr["resolved"] / run_full_pr["total"] * 100 if run_full_pr.get("total", 0) > 0 else 0

                token_change = (run_full_s["avg_total_tokens"] - run_free_s["avg_total_tokens"]) / run_free_s["avg_total_tokens"] * 100
                rate_change = full_rate - free_rate

                all_data.append({
                    "dataset": dataset_name,
                    "agent": agent,
                    "token_change": token_change,
                    "rate_change": rate_change,
                    "free_tokens": run_free_s["avg_total_tokens"],
                    "full_tokens": run_full_s["avg_total_tokens"]
                })

    lines.append("### Cost Sensitivity Comparison")
    lines.append("")
    lines.append("| Agent | Dataset | ΔTokens% | ΔPass% | Sensitivity (ΔTokens/ΔPass) |")
    lines.append("|-------|---------|----------|--------|------------------------------|")

    for d in all_data:
        sensitivity = d["token_change"] / abs(d["rate_change"]) if d["rate_change"] != 0 else float('inf')
        sens_str = f"{sensitivity:.1f}" if sensitivity != float('inf') else "∞"
        lines.append(f"| {d['agent']} | {d['dataset']} | +{d['token_change']:.1f}% | {d['rate_change']:+.1f}% | {sens_str} |")

    lines.append("")

    return "\n".join(lines)


def generate_key_findings(stats: dict, pass_rates: dict) -> str:
    """Generate key findings"""
    lines = []
    lines.append("## Key Findings")
    lines.append("")

    # Collect data
    claude_data = []
    codex_data = []

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
                free_rate = run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr.get("total", 0) > 0 else 0
                full_rate = run_full_pr["resolved"] / run_full_pr["total"] * 100 if run_full_pr.get("total", 0) > 0 else 0

                token_change = (run_full_s["avg_total_tokens"] - run_free_s["avg_total_tokens"]) / run_free_s["avg_total_tokens"] * 100
                rate_change = full_rate - free_rate

                data = {
                    "dataset": dataset_name,
                    "token_change": token_change,
                    "rate_change": rate_change,
                    "free_tokens": run_free_s["avg_total_tokens"],
                    "full_tokens": run_full_s["avg_total_tokens"]
                }

                if "claude" in agent:
                    claude_data.append(data)
                else:
                    codex_data.append(data)

    lines.append("### 1. Claude Code Characteristics")
    lines.append("")
    if claude_data:
        avg_token_change = sum(d["token_change"] for d in claude_data) / len(claude_data)
        avg_rate_change = sum(d["rate_change"] for d in claude_data) / len(claude_data)
        avg_free_tokens = sum(d["free_tokens"] for d in claude_data) / len(claude_data)
        lines.append(f"- Average Token increase (Free→Full): **+{avg_token_change:.1f}%**")
        lines.append(f"- Average Pass Rate change: **{avg_rate_change:+.1f}%**")
        lines.append(f"- Average Run-Free Token consumption: **{avg_free_tokens:,.0f}**")
        lines.append("- Characteristics: **Cost-sensitive** - Execution permissions significantly increase cost, but benefits are limited")
    lines.append("")

    lines.append("### 2. Codex Characteristics")
    lines.append("")
    if codex_data:
        avg_token_change = sum(d["token_change"] for d in codex_data) / len(codex_data)
        avg_rate_change = sum(d["rate_change"] for d in codex_data) / len(codex_data)
        avg_free_tokens = sum(d["free_tokens"] for d in codex_data) / len(codex_data)
        lines.append(f"- Average Token increase (Free→Full): **+{avg_token_change:.1f}%**")
        lines.append(f"- Average Pass Rate change: **{avg_rate_change:+.1f}%**")
        lines.append(f"- Average Run-Free Token consumption: **{avg_free_tokens:,.0f}**")
        lines.append("- Characteristics: **Cost-stable** - Execution permissions have minimal impact on cost")
    lines.append("")

    lines.append("### 3. Difference Analysis")
    lines.append("")
    lines.append("**Reasons for Claude Code's cost sensitivity:**")
    lines.append("- Low token consumption in Run-Free mode (~65K), indicating concise reasoning process")
    lines.append("- Execution feedback leads to more interaction rounds and context accumulation")
    lines.append("- Execution results need to be parsed and processed, increasing Input Tokens")
    lines.append("")
    lines.append("**Reasons for Codex's cost stability:**")
    lines.append("- Already high token consumption in Run-Free mode (~400-500K)")
    lines.append("- Model's reasoning process is relatively verbose")
    lines.append("- Execution feedback has minimal marginal impact on overall token consumption")
    lines.append("")

    lines.append("### 4. Conclusions")
    lines.append("")
    lines.append("- **Impact of execution permissions is inconsistent across different Agents**")
    lines.append("- Claude Code is more sensitive to execution permissions (large cost changes)")
    lines.append("- Codex is insensitive to execution permissions (small cost changes)")
    lines.append("- Cost sensitivity should be considered when selecting Agents")

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
    data_file = output_dir / "data_rq4.md"

    content = []
    content.append("# RQ4: Agent Sensitivity - Data Tables")
    content.append("")
    content.append("Analysis data on sensitivity of different Agents to execution permissions.")
    content.append("")
    content.append(generate_delta_comparison_table(stats, pass_rates))
    content.append(generate_agent_characteristics_table(stats, pass_rates))
    content.append(generate_token_breakdown_table(stats))
    content.append(generate_sensitivity_analysis(stats, pass_rates))
    content.append(generate_key_findings(stats, pass_rates))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"Data saved to: {data_file}")


if __name__ == "__main__":
    main()
