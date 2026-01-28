#!/usr/bin/env python3
"""
RQ3 Analysis: Identify Hurt and Helped cases between Offline and Unbounded modes

Hurt cases: Offline succeeds but Unbounded fails (execution led agent astray)
Helped cases: Offline fails but Unbounded succeeds (execution provided value)

This script identifies these cases and analyzes their characteristics.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SB_CLI_REPORTS = PROJECT_ROOT / "sb-cli-reports"
OUTPUT_DIR = PROJECT_ROOT / "output"

DATASETS = {
    "swebenchlite": "SWE-bench Lite",
    "swebenchverified": "SWE-bench Verified"
}

AGENTS = ["claude_code", "codex"]


def load_resolved_ids(dataset: str, agent: str, mode: str) -> set:
    """Load resolved instance IDs from sb-cli-reports"""
    # Map mode names
    mode_map = {
        "offline": "run_free",
        "unbounded": "run_full",
        "run_free": "run_free",
        "run_full": "run_full"
    }
    mode_key = mode_map.get(mode, mode)

    # Find the report file
    patterns = [
        f"swe-bench_lite__test__{dataset}_{agent}_{mode_key}.json",
        f"swe-bench_verified__test__{dataset}_{agent}_{mode_key}.json",
        f"swe-bench_lite__test__lite__{agent}__{mode_key}.json",
        f"swe-bench_verified__test__verified__{agent}__{mode_key}.json",
    ]

    for pattern in patterns:
        report_file = SB_CLI_REPORTS / pattern
        if report_file.exists():
            with open(report_file) as f:
                data = json.load(f)
                return set(data.get("resolved_ids", []))

    # Try alternative naming
    for f in SB_CLI_REPORTS.glob(f"*{dataset}*{agent}*{mode_key}*.json"):
        with open(f) as fp:
            data = json.load(fp)
            return set(data.get("resolved_ids", []))

    return set()


def analyze_hurt_helped():
    """Analyze Hurt and Helped cases across all agent-dataset combinations"""
    results = {
        "summary": defaultdict(lambda: {"hurt": [], "helped": [], "both_pass": [], "both_fail": []}),
        "all_hurt": [],
        "all_helped": []
    }

    for dataset in DATASETS:
        for agent in AGENTS:
            offline_resolved = load_resolved_ids(dataset, agent, "offline")
            unbounded_resolved = load_resolved_ids(dataset, agent, "unbounded")

            if not offline_resolved and not unbounded_resolved:
                print(f"Warning: No data for {dataset}/{agent}")
                continue

            # Get all instances (union of both)
            all_instances = offline_resolved | unbounded_resolved

            # Also need to get the full instance list from checkpoint
            checkpoint_file = OUTPUT_DIR / dataset / agent / "run_free" / "checkpoint.json"
            if checkpoint_file.exists():
                with open(checkpoint_file) as f:
                    checkpoint = json.load(f)
                    all_instances = all_instances | set(checkpoint.get("completed", []))

            key = f"{agent}_{dataset}"

            for instance in all_instances:
                offline_pass = instance in offline_resolved
                unbounded_pass = instance in unbounded_resolved

                if offline_pass and not unbounded_pass:
                    # Hurt: Offline succeeds, Unbounded fails
                    results["summary"][key]["hurt"].append(instance)
                    results["all_hurt"].append({
                        "instance": instance,
                        "agent": agent,
                        "dataset": dataset
                    })
                elif not offline_pass and unbounded_pass:
                    # Helped: Offline fails, Unbounded succeeds
                    results["summary"][key]["helped"].append(instance)
                    results["all_helped"].append({
                        "instance": instance,
                        "agent": agent,
                        "dataset": dataset
                    })
                elif offline_pass and unbounded_pass:
                    results["summary"][key]["both_pass"].append(instance)
                else:
                    results["summary"][key]["both_fail"].append(instance)

    return results


def print_summary(results: dict):
    """Print summary of Hurt/Helped analysis"""
    print("=" * 80)
    print("RQ3 Analysis: Hurt vs Helped Cases")
    print("=" * 80)
    print()
    print("Hurt = Offline succeeds, Unbounded fails (execution led agent astray)")
    print("Helped = Offline fails, Unbounded succeeds (execution provided value)")
    print()

    total_hurt = 0
    total_helped = 0
    total_both_pass = 0
    total_both_fail = 0

    print("-" * 80)
    print(f"{'Agent':<15} {'Dataset':<20} {'Hurt':<8} {'Helped':<8} {'Both Pass':<10} {'Both Fail':<10}")
    print("-" * 80)

    for key, data in sorted(results["summary"].items()):
        parts = key.split("_", 1)
        agent = parts[0]
        dataset = parts[1] if len(parts) > 1 else ""

        hurt = len(data["hurt"])
        helped = len(data["helped"])
        both_pass = len(data["both_pass"])
        both_fail = len(data["both_fail"])

        total_hurt += hurt
        total_helped += helped
        total_both_pass += both_pass
        total_both_fail += both_fail

        print(f"{agent:<15} {dataset:<20} {hurt:<8} {helped:<8} {both_pass:<10} {both_fail:<10}")

    print("-" * 80)
    print(f"{'TOTAL':<15} {'':<20} {total_hurt:<8} {total_helped:<8} {total_both_pass:<10} {total_both_fail:<10}")
    print("-" * 80)

    print()
    print("Key Insights:")
    print(f"  - Net benefit from execution: {total_helped - total_hurt} instances")
    print(f"  - Hurt ratio: {total_hurt}/{total_hurt + total_helped} = {total_hurt/(total_hurt+total_helped)*100:.1f}%" if total_hurt + total_helped > 0 else "  - No discordant pairs")
    print(f"  - Identical outcomes: {total_both_pass + total_both_fail} instances ({(total_both_pass + total_both_fail)/(total_hurt + total_helped + total_both_pass + total_both_fail)*100:.1f}%)" if total_hurt + total_helped + total_both_pass + total_both_fail > 0 else "")
    print()

    return {
        "total_hurt": total_hurt,
        "total_helped": total_helped,
        "total_both_pass": total_both_pass,
        "total_both_fail": total_both_fail
    }


def save_instance_lists(results: dict, output_dir: Path):
    """Save lists of hurt and helped instances for further analysis"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save hurt cases
    hurt_file = output_dir / "hurt_cases.json"
    with open(hurt_file, "w") as f:
        json.dump(results["all_hurt"], f, indent=2)
    print(f"Saved hurt cases to: {hurt_file}")

    # Save helped cases
    helped_file = output_dir / "helped_cases.json"
    with open(helped_file, "w") as f:
        json.dump(results["all_helped"], f, indent=2)
    print(f"Saved helped cases to: {helped_file}")

    # Save summary by agent-dataset
    summary_file = output_dir / "summary.json"
    summary_data = {}
    for key, data in results["summary"].items():
        summary_data[key] = {
            "hurt": data["hurt"],
            "helped": data["helped"],
            "hurt_count": len(data["hurt"]),
            "helped_count": len(data["helped"]),
            "both_pass_count": len(data["both_pass"]),
            "both_fail_count": len(data["both_fail"])
        }
    with open(summary_file, "w") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Saved summary to: {summary_file}")


def main():
    print("Analyzing Hurt/Helped cases...")
    print()

    results = analyze_hurt_helped()
    totals = print_summary(results)

    # Save results
    output_dir = Path(__file__).parent
    save_instance_lists(results, output_dir)

    print()
    print("Analysis complete!")


if __name__ == "__main__":
    main()
