#!/usr/bin/env python3
"""
Analyze advantage scenarios of Run-Less mode
Find cases where moderate execution is better than no execution
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


def find_run_less_advantages(resolved, results):
    """Find advantage scenarios of Run-Less mode"""
    lines = []
    lines.append("# Analysis of Run-Less Mode Advantage Scenarios")
    lines.append("")
    lines.append("Although overall data shows Run-Less is not as good as Run-Free, moderate execution does help in certain specific scenarios.")
    lines.append("")

    # 1. Find cases where only Run-Less succeeded
    lines.append("## 1. Cases Where Only Run-Less Succeeded")
    lines.append("")
    lines.append("In these cases, both Run-Free and Run-Full failed, but Run-Less succeeded.")
    lines.append("")

    run_less_unique = []

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            if not all(m in modes for m in ["run_free", "run_less_k1", "run_less_k3", "run_full"]):
                continue

            free = modes["run_free"]
            k1 = modes["run_less_k1"]
            k3 = modes["run_less_k3"]
            full = modes["run_full"]

            # Run-Less-K1 unique success (both Free and Full failed)
            k1_unique = k1 - free - full
            # Run-Less-K3 unique success
            k3_unique = k3 - free - full
            # Any Run-Less unique success
            any_less_unique = (k1 | k3) - free - full

            lines.append(f"**{agent}:**")
            lines.append("")
            lines.append(f"- Run-Less-K1 unique success: {len(k1_unique)} cases")
            lines.append(f"- Run-Less-K3 unique success: {len(k3_unique)} cases")
            lines.append(f"- Any Run-Less unique success: {len(any_less_unique)} cases")
            lines.append("")

            if any_less_unique:
                lines.append("**Case list:**")
                for inst in sorted(any_less_unique):
                    in_k1 = "K1" if inst in k1 else ""
                    in_k3 = "K3" if inst in k3 else ""
                    modes_str = ", ".join(filter(None, [in_k1, in_k3]))
                    lines.append(f"- `{inst}` ({modes_str})")
                    run_less_unique.append((dataset, agent, inst))
                lines.append("")

    # 2. Analyze characteristics of Run-Less unique success cases
    lines.append("## 2. Detailed Analysis of Run-Less Unique Success Cases")
    lines.append("")

    for dataset, agent, inst in run_less_unique[:10]:
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
        lines.append("**Analysis**: Moderate execution (1-3 times) helps verify fixes, but excessive execution is harmful.")
        lines.append("")

    # 3. Find cases where Run-Less is better than Run-Free
    lines.append("## 3. Cases Where Run-Less is Better Than Run-Free")
    lines.append("")
    lines.append("In these cases, Run-Free failed but Run-Less succeeded.")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            if "run_free" not in modes:
                continue

            free = modes["run_free"]
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())

            # Run-Less succeeded but Run-Free failed
            k1_better = k1 - free
            k3_better = k3 - free

            lines.append(f"**{agent}:**")
            lines.append("")
            lines.append(f"- Run-Less-K1 succeeded but Run-Free failed: {len(k1_better)} cases")
            lines.append(f"- Run-Less-K3 succeeded but Run-Free failed: {len(k3_better)} cases")
            lines.append("")

            if k1_better or k3_better:
                lines.append("**Cases:**")
                for inst in sorted(k1_better)[:5]:
                    lines.append(f"- `{inst}` (K1 succeeded)")
                for inst in sorted(k3_better - k1_better)[:5]:
                    lines.append(f"- `{inst}` (K3 succeeded)")
                lines.append("")

    # 4. Analyze the value of moderate execution
    lines.append("## 4. Value Analysis of Moderate Execution")
    lines.append("")

    # Count unique successes for each mode
    stats = defaultdict(lambda: {"unique": 0, "better_than_free": 0, "better_than_full": 0})

    for dataset in resolved:
        for agent in resolved[dataset]:
            modes = resolved[dataset][agent]
            if len(modes) < 4:
                continue

            free = modes.get("run_free", set())
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())
            cost = modes.get("run_cost", set())
            full = modes.get("run_full", set())

            # Unique success
            stats["run_less_k1"]["unique"] += len(k1 - free - k3 - cost - full)
            stats["run_less_k3"]["unique"] += len(k3 - free - k1 - cost - full)
            stats["run_cost"]["unique"] += len(cost - free - k1 - k3 - full)

            # Better than Run-Free
            stats["run_less_k1"]["better_than_free"] += len(k1 - free)
            stats["run_less_k3"]["better_than_free"] += len(k3 - free)
            stats["run_cost"]["better_than_free"] += len(cost - free)

            # Better than Run-Full
            stats["run_less_k1"]["better_than_full"] += len(k1 - full)
            stats["run_less_k3"]["better_than_full"] += len(k3 - full)
            stats["run_cost"]["better_than_full"] += len(cost - full)

    lines.append("| Mode | Unique Success | Better than Run-Free | Better than Run-Full |")
    lines.append("|------|----------------|----------------------|----------------------|")
    for mode in ["run_less_k1", "run_less_k3", "run_cost"]:
        s = stats[mode]
        lines.append(f"| {mode} | {s['unique']} | {s['better_than_free']} | {s['better_than_full']} |")
    lines.append("")

    # 5. Summary
    lines.append("## 5. Key Findings: The Value of Moderate Execution")
    lines.append("")
    lines.append("### Scenarios Where Moderate Execution Helps")
    lines.append("")
    lines.append("1. **Problems that need verification but not iteration**")
    lines.append("   - 1-3 executions are sufficient to verify if the fix is correct")
    lines.append("   - More executions introduce noise and interference")
    lines.append("")
    lines.append("2. **Problems where Run-Free reasoning is insufficient**")
    lines.append("   - Pure reasoning cannot determine the correct answer")
    lines.append("   - But a small amount of execution feedback can point the way")
    lines.append("")
    lines.append("3. **Problems where Run-Full over-execution is harmful**")
    lines.append("   - Excessive execution leads to trial-and-error loops")
    lines.append("   - Moderate execution avoids this problem")
    lines.append("")
    lines.append("### Practical Recommendations")
    lines.append("")
    lines.append("1. **Run-Free is still the default choice** - Lowest cost, near-optimal effectiveness")
    lines.append("2. **Run-Less-K1 can be an alternative** - When Run-Free fails, try 1 execution")
    lines.append("3. **Avoid Run-Full** - Unless extensive iterative debugging is truly needed")
    lines.append("4. **The value of moderate execution is in verification** - Not exploration, but confirmation")
    lines.append("")

    return "\n".join(lines)


def main():
    print("Loading data...")

    results = load_all_results()
    resolved = load_resolved_ids()

    analysis = find_run_less_advantages(resolved, results)

    output_path = Path(__file__).parent / "run_less_advantages.md"
    output_path.write_text(analysis, encoding="utf-8")
    print(f"Analysis saved to: {output_path}")


if __name__ == "__main__":
    main()
