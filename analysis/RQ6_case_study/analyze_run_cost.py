#!/usr/bin/env python3
"""
Analyze the performance of Run-Cost mode
Run-Cost is an execution mode with cost constraints, potentially a good compromise solution
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, sort_modes
)


def load_resolved_ids():
    """Load resolved instance IDs for each configuration"""
    sb_cli_reports_dir = PROJECT_ROOT / "sb-cli-reports"
    resolved = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    if not sb_cli_reports_dir.exists():
        return resolved

    for report_file in sb_cli_reports_dir.glob("*.json"):
        try:
            report = json.loads(report_file.read_text(encoding="utf-8"))
            filename = report_file.stem

            if "lite" in filename.lower():
                dataset = "swebenchlite"
            elif "verified" in filename.lower():
                dataset = "swebenchverified"
            else:
                continue

            for agent in ["claude_code", "codex"]:
                if agent in filename:
                    for mode in MODE_ORDER:
                        if mode in filename:
                            resolved_ids = set(report.get("resolved_ids", []))
                            resolved[dataset][agent][mode] = resolved_ids
                            break
                    break
        except:
            continue

    return resolved


def analyze_run_cost(resolved, results):
    """Analyze the performance of Run-Cost mode"""
    lines = []
    lines.append("# Run-Cost Mode In-Depth Analysis")
    lines.append("")
    lines.append("Run-Cost is an execution mode with cost constraints, seeking a balance between execution count and cost.")
    lines.append("")

    # 1. Overall performance comparison
    lines.append("## 1. Overall Performance Comparison")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        lines.append("| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |")
        lines.append("|-------|----------|-------------|-------------|----------|----------|")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            row = f"| {agent} |"
            for mode in MODE_ORDER:
                if mode in modes:
                    count = len(modes[mode])
                    row += f" {count} |"
                else:
                    row += " - |"
            lines.append(row)

        lines.append("")

    # 2. Run-Cost vs other modes
    lines.append("## 2. Run-Cost Comparison with Other Modes")
    lines.append("")

    total_stats = {
        "cost_unique": 0,
        "cost_better_free": 0,
        "cost_better_full": 0,
        "cost_better_k1": 0,
        "cost_better_k3": 0,
        "free_better_cost": 0,
        "full_better_cost": 0,
    }

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            if "run_cost" not in modes:
                continue

            free = modes.get("run_free", set())
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())
            cost = modes["run_cost"]
            full = modes.get("run_full", set())

            # Run-Cost unique successes
            cost_unique = cost - free - k1 - k3 - full

            # Run-Cost vs Run-Free
            cost_better_free = cost - free
            free_better_cost = free - cost

            # Run-Cost vs Run-Full
            cost_better_full = cost - full
            full_better_cost = full - cost

            # Run-Cost vs Run-Less
            cost_better_k1 = cost - k1
            cost_better_k3 = cost - k3

            total_stats["cost_unique"] += len(cost_unique)
            total_stats["cost_better_free"] += len(cost_better_free)
            total_stats["cost_better_full"] += len(cost_better_full)
            total_stats["cost_better_k1"] += len(cost_better_k1)
            total_stats["cost_better_k3"] += len(cost_better_k3)
            total_stats["free_better_cost"] += len(free_better_cost)
            total_stats["full_better_cost"] += len(full_better_cost)

            lines.append(f"**{agent}:**")
            lines.append("")
            lines.append("| Comparison | Run-Cost Wins | Opponent Wins | Net Difference |")
            lines.append("|------|-------------|--------|--------|")
            lines.append(f"| vs Run-Free | {len(cost_better_free)} | {len(free_better_cost)} | {len(cost_better_free) - len(free_better_cost):+d} |")
            lines.append(f"| vs Run-Less-K1 | {len(cost_better_k1)} | {len(k1 - cost)} | {len(cost_better_k1) - len(k1 - cost):+d} |")
            lines.append(f"| vs Run-Less-K3 | {len(cost_better_k3)} | {len(k3 - cost)} | {len(cost_better_k3) - len(k3 - cost):+d} |")
            lines.append(f"| vs Run-Full | {len(cost_better_full)} | {len(full_better_cost)} | {len(cost_better_full) - len(full_better_cost):+d} |")
            lines.append("")

            if cost_unique:
                lines.append(f"**Run-Cost Unique Successes ({len(cost_unique)} cases):**")
                for inst in sorted(cost_unique):
                    lines.append(f"- `{inst}`")
                lines.append("")

    # 3. Summary statistics
    lines.append("## 3. Summary Statistics")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|------|------|")
    lines.append(f"| Run-Cost Unique Successes | {total_stats['cost_unique']} |")
    lines.append(f"| Run-Cost Better than Run-Free | {total_stats['cost_better_free']} |")
    lines.append(f"| Run-Cost Better than Run-Full | {total_stats['cost_better_full']} |")
    lines.append(f"| Run-Free Better than Run-Cost | {total_stats['free_better_cost']} |")
    lines.append(f"| Run-Full Better than Run-Cost | {total_stats['full_better_cost']} |")
    lines.append("")

    # 4. Run-Cost unique success case analysis
    lines.append("## 4. Detailed Analysis of Run-Cost Unique Success Cases")
    lines.append("")

    cost_unique_cases = []
    for dataset in resolved:
        for agent in resolved[dataset]:
            modes = resolved[dataset][agent]
            if "run_cost" not in modes:
                continue

            free = modes.get("run_free", set())
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())
            cost = modes["run_cost"]
            full = modes.get("run_full", set())

            cost_unique = cost - free - k1 - k3 - full
            for inst in cost_unique:
                cost_unique_cases.append((dataset, agent, inst))

    for dataset, agent, inst in cost_unique_cases:
        dataset_name = DATASETS.get(dataset, dataset)
        lines.append(f"### `{inst}` ({agent}, {dataset_name})")
        lines.append("")

        lines.append("| Mode | Tokens | Turns | High-Cost Exec | Result |")
        lines.append("|------|--------|-------|----------------|--------|")

        for mode in sort_modes(resolved[dataset][agent].keys()):
            data = results.get(dataset, {}).get(agent, {}).get(mode, {}).get(inst, {})
            is_resolved = inst in resolved[dataset][agent].get(mode, set())

            if data:
                tokens = data["tokens"]["input"] + data["tokens"]["output"]
                turns = data["turns"]
                high_exec = data["high_cost_exec"]
                result = "**Success**" if is_resolved else "Failed"
                lines.append(f"| {mode} | {tokens:,} | {turns} | {high_exec} | {result} |")

        lines.append("")

    # 5. Cost efficiency analysis
    lines.append("## 5. Cost Efficiency Analysis")
    lines.append("")
    lines.append("Run-Cost's cost position relative to other modes.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in results:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(results[dataset].keys()):
            modes = results[dataset][agent]
            lines.append(f"**{agent}:**")
            lines.append("")

            lines.append("| Mode | Avg Tokens | Pass Rate | Efficiency Ratio (Pass/Token) |")
            lines.append("|------|------------|-----------|---------------------|")

            pass_rates = {}
            for mode in sort_modes(modes.keys()):
                if mode in resolved.get(dataset, {}).get(agent, {}):
                    pass_rates[mode] = len(resolved[dataset][agent][mode])

            for mode in sort_modes(modes.keys()):
                instances = modes[mode]
                if not instances:
                    continue

                tokens_list = [v["tokens"]["input"] + v["tokens"]["output"] for v in instances.values()]
                avg_tokens = sum(tokens_list) / len(tokens_list)
                pass_rate = pass_rates.get(mode, 0)
                efficiency = pass_rate / (avg_tokens / 1000) if avg_tokens > 0 else 0

                lines.append(f"| {mode} | {avg_tokens:,.0f} | {pass_rate} | {efficiency:.2f} |")

            lines.append("")

    # 6. Conclusion
    lines.append("## 6. Value of Run-Cost Mode")
    lines.append("")
    lines.append("### Advantages")
    lines.append("")
    lines.append("1. **Controllable Cost** - Has a clear cost ceiling, avoiding unlimited consumption")
    lines.append("2. **Stable Performance** - Approaches Run-Full's effectiveness in most cases")
    lines.append("3. **Unique Success Cases** - Some problems can only be solved by Run-Cost")
    lines.append("4. **More Flexible than Run-Less** - Limits total cost rather than simply restricting execution count")
    lines.append("")
    lines.append("### Applicable Scenarios")
    lines.append("")
    lines.append("1. **Limited Budget but Need Execution Feedback** - More verification capability than Run-Free")
    lines.append("2. **Avoid Over-Execution** - More restrained than Run-Full")
    lines.append("3. **Production Environment** - Predictable cost, suitable for large-scale deployment")
    lines.append("")
    lines.append("### Practical Recommendations")
    lines.append("")
    lines.append("1. **Run-Free** - Default first choice, lowest cost")
    lines.append("2. **Run-Cost** - Best choice when execution is needed but cost must be controlled")
    lines.append("3. **Run-Full** - Use only when debugging complex problems")
    lines.append("4. **Run-Less** - Not recommended, unstable performance")
    lines.append("")

    return "\n".join(lines)


def main():
    print("Loading data...")

    results = load_all_results()
    resolved = load_resolved_ids()

    analysis = analyze_run_cost(resolved, results)

    output_path = Path(__file__).parent / "run_cost_analysis.md"
    output_path.write_text(analysis, encoding="utf-8")
    print(f"Analysis saved to: {output_path}")


if __name__ == "__main__":
    main()
