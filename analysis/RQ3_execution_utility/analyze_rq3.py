#!/usr/bin/env python3
"""
RQ3: Execution Utility - Analysis of Execution Behavior Purpose

Research Question: What are the main purposes of execution behavior under different regimes?
Which types of execution bring actual benefits, and which are low-value overhead?
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, sort_modes, HIGH_COST_PATTERNS, PYTHON_SCRIPT_PATTERN
)

# Execution purpose classification rules
EXECUTION_CATEGORIES = {
    "verification": {
        "name": "Verification",
        "description": "Run test frameworks to verify fixes",
        "patterns": ["pytest", "python -m pytest", "python -m unittest",
                    "manage.py test", "python manage.py test",
                    "tox", "nose", "nosetests", "python -m django test",
                    "python tests/runtests.py"]
    },
    "localization": {
        "name": "Localization",
        "description": "Run scripts to locate problems",
        "patterns": []  # Use PYTHON_SCRIPT_PATTERN
    },
    "environment": {
        "name": "Environment",
        "description": "Confirm environment configuration",
        "patterns": ["python --version", "pip list", "pip show", "pip freeze",
                    "which python", "python -c", "pwd", "whoami"]
    },
    "exploration": {
        "name": "Exploration",
        "description": "Explore filesystem and code",
        "patterns": ["ls", "find", "cat", "head", "tail", "grep", "tree", "wc"]
    }
}


def classify_command(cmd: str) -> str:
    """Classify execution commands according to rules"""
    cmd_lower = cmd.lower().strip()

    # Verification
    for pattern in EXECUTION_CATEGORIES["verification"]["patterns"]:
        if pattern in cmd_lower:
            return "verification"

    # Environment confirmation
    for pattern in EXECUTION_CATEGORIES["environment"]["patterns"]:
        if pattern in cmd_lower:
            return "environment"

    # Exploration
    for pattern in EXECUTION_CATEGORIES["exploration"]["patterns"]:
        if cmd_lower.startswith(pattern) or f" {pattern}" in cmd_lower:
            return "exploration"

    # Localization (running Python scripts)
    if PYTHON_SCRIPT_PATTERN.search(cmd):
        return "localization"

    return "other"


def extract_commands_from_trace(trace_path: Path) -> list:
    """Extract all executed commands from trace file"""
    commands = []

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)

                # Codex format
                if item.get("type") in ["item.started", "item.completed"]:
                    inner = item.get("item", {})
                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        if cmd:
                            commands.append(cmd)

                # Claude Code format
                if item.get("type") == "assistant":
                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            if cmd:
                                commands.append(cmd)
            except:
                continue

    return commands


def analyze_execution_purposes(results: dict) -> dict:
    """Analyze execution purpose distribution across modes"""
    analysis = {}

    for dataset in results:
        analysis[dataset] = {}
        for agent in results[dataset]:
            analysis[dataset][agent] = {}
            for mode in results[dataset][agent]:
                category_counts = defaultdict(int)
                total_commands = 0
                repeated_commands = defaultdict(int)

                for instance_id, data in results[dataset][agent][mode].items():
                    commands = data.get("commands", [])

                    # Count command classifications
                    for cmd in commands:
                        category = classify_command(cmd)
                        category_counts[category] += 1
                        total_commands += 1

                    # Count repeated commands (trial-error loops)
                    cmd_counter = defaultdict(int)
                    for cmd in commands:
                        # Simplify command for comparison
                        simplified = re.sub(r'\s+', ' ', cmd.strip())
                        cmd_counter[simplified] += 1

                    for cmd, count in cmd_counter.items():
                        if count > 1:
                            repeated_commands[cmd] = max(repeated_commands[cmd], count)

                # Calculate trial-error loops (same command executed > 1 time)
                trial_error_count = sum(1 for count in repeated_commands.values() if count > 1)

                analysis[dataset][agent][mode] = {
                    "total_commands": total_commands,
                    "categories": dict(category_counts),
                    "trial_error_instances": trial_error_count,
                    "repeated_commands": len(repeated_commands)
                }

    return analysis


def generate_category_distribution_table(analysis: dict) -> str:
    """Generate execution purpose classification distribution table"""
    lines = []
    lines.append("## Execution Purpose Classification Distribution")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in analysis:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Total | Verification | Localization | Environment | Exploration | Other |")
        lines.append("|-------|------|-------|--------------|--------------|-------------|-------------|-------|")

        for agent in sorted(analysis[dataset].keys()):
            modes = analysis[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                total = data["total_commands"]
                cats = data["categories"]

                v = cats.get("verification", 0)
                l = cats.get("localization", 0)
                e = cats.get("environment", 0)
                x = cats.get("exploration", 0)
                o = cats.get("other", 0)

                # Calculate percentages
                v_pct = f"{v} ({v*100/total:.1f}%)" if total > 0 else "0"
                l_pct = f"{l} ({l*100/total:.1f}%)" if total > 0 else "0"
                e_pct = f"{e} ({e*100/total:.1f}%)" if total > 0 else "0"
                x_pct = f"{x} ({x*100/total:.1f}%)" if total > 0 else "0"
                o_pct = f"{o} ({o*100/total:.1f}%)" if total > 0 else "0"

                lines.append(f"| {agent} | {mode} | {total} | {v_pct} | {l_pct} | {e_pct} | {x_pct} | {o_pct} |")

        lines.append("")

    return "\n".join(lines)


def generate_mode_comparison_table(analysis: dict) -> str:
    """Generate execution purpose comparison table across modes"""
    lines = []
    lines.append("## Execution Purpose Comparison Across Modes")
    lines.append("")
    lines.append("Compare execution behavior differences under different execution modes.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in analysis:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(analysis[dataset].keys()):
            modes = analysis[dataset][agent]
            lines.append(f"**{agent}:**")
            lines.append("")

            # Get run_free and run_full data
            run_free = modes.get("run_free", {})
            run_full = modes.get("run_full", {})

            if run_free and run_full:
                free_total = run_free.get("total_commands", 0)
                full_total = run_full.get("total_commands", 0)

                free_verify = run_free.get("categories", {}).get("verification", 0)
                full_verify = run_full.get("categories", {}).get("verification", 0)

                lines.append(f"- Run-Free total executions: {free_total}")
                lines.append(f"- Run-Full total executions: {full_total}")
                lines.append(f"- Run-Free verification executions: {free_verify}")
                lines.append(f"- Run-Full verification executions: {full_verify}")

                if full_total > 0:
                    diff = full_total - free_total
                    lines.append(f"- Execution count difference: +{diff} ({diff*100/free_total:.1f}% increase)" if free_total > 0 else f"- Execution count difference: +{diff}")

            lines.append("")

    return "\n".join(lines)


def generate_trial_error_analysis(analysis: dict) -> str:
    """Generate trial-error loop analysis"""
    lines = []
    lines.append("## Trial-Error Loop Analysis")
    lines.append("")
    lines.append("Count repeated executions of the same command, reflecting trial-error behavior.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in analysis:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Repeated Commands | Trial-Error Instances |")
        lines.append("|-------|------|-------------------|----------------------|")

        for agent in sorted(analysis[dataset].keys()):
            modes = analysis[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                repeated = data.get("repeated_commands", 0)
                trial_error = data.get("trial_error_instances", 0)
                lines.append(f"| {agent} | {mode} | {repeated} | {trial_error} |")

        lines.append("")

    return "\n".join(lines)


def generate_key_findings(analysis: dict) -> str:
    """Generate key findings"""
    lines = []
    lines.append("## Key Findings")
    lines.append("")

    lines.append("### 1. Execution Purpose Classification")
    lines.append("")
    lines.append("| Category | Description | Typical Commands |")
    lines.append("|----------|-------------|------------------|")
    for cat_id, cat_info in EXECUTION_CATEGORIES.items():
        patterns = ", ".join(cat_info["patterns"][:3]) if cat_info["patterns"] else "python script.py"
        lines.append(f"| {cat_info['name']} | {cat_info['description']} | {patterns} |")
    lines.append("")

    lines.append("### 2. Main Findings")
    lines.append("")

    # Collect statistics
    all_data = []
    for dataset in analysis:
        for agent in analysis[dataset]:
            for mode in analysis[dataset][agent]:
                data = analysis[dataset][agent][mode]
                total = data["total_commands"]
                verify = data["categories"].get("verification", 0)
                if total > 0:
                    all_data.append({
                        "dataset": dataset,
                        "agent": agent,
                        "mode": mode,
                        "total": total,
                        "verify": verify,
                        "verify_pct": verify * 100 / total
                    })

    # Group statistics by mode
    mode_stats = defaultdict(lambda: {"total": 0, "verify": 0, "count": 0})
    for d in all_data:
        mode_stats[d["mode"]]["total"] += d["total"]
        mode_stats[d["mode"]]["verify"] += d["verify"]
        mode_stats[d["mode"]]["count"] += 1

    lines.append("**Average execution count per mode:**")
    lines.append("")
    for mode in sort_modes(mode_stats.keys()):
        stats = mode_stats[mode]
        avg_total = stats["total"] / stats["count"] if stats["count"] > 0 else 0
        avg_verify = stats["verify"] / stats["count"] if stats["count"] > 0 else 0
        lines.append(f"- {mode}: average {avg_total:.0f} executions, including {avg_verify:.0f} verifications")
    lines.append("")

    lines.append("### 3. Conclusions")
    lines.append("")
    lines.append("- **Run-Free mode executes almost no commands**: verification execution count close to 0")
    lines.append("- **Run-Full mode executes the most**: heavily used for verification and exploration")
    lines.append("- **Verification is the main execution purpose**: in modes with execution permissions, verification has the highest proportion")
    lines.append("- **Trial-error loops are common**: Run-Full mode has more cases of repeatedly executing the same command")

    return "\n".join(lines)


def main():
    print("Loading data...")

    results = load_all_results()

    if not results:
        print("Error: Unable to load experimental results data")
        return

    print("Analyzing execution purposes...")
    analysis = analyze_execution_purposes(results)

    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq3.md"

    content = []
    content.append("# RQ3: Execution Utility - Data Tables")
    content.append("")
    content.append("Analysis data on execution behavior purposes.")
    content.append("")
    content.append(generate_category_distribution_table(analysis))
    content.append(generate_mode_comparison_table(analysis))
    content.append(generate_trial_error_analysis(analysis))
    content.append(generate_key_findings(analysis))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"Data saved to: {data_file}")


if __name__ == "__main__":
    main()
