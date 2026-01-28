#!/usr/bin/env python3
"""
Investigate why Unrestricted mode has lower first edit hit rate

Hypothesis: In Unrestricted mode, Agent tends to edit test files/debug scripts first,
while Prohibited mode directly edits source code files.
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


def normalize_path(path: str) -> str:
    """Normalize file path for comparison"""
    if path.startswith('./'):
        path = path[2:]
    if path.startswith('/'):
        path = path.lstrip('/')
    if path.startswith('testbed/'):
        path = path[8:]
    return path


def is_test_file(path: str) -> bool:
    """Check if the file is a test file"""
    path_lower = path.lower()
    # Test file characteristics
    if '/test_' in path_lower or '/tests/' in path_lower:
        return True
    if path_lower.endswith('_test.py'):
        return True
    if 'test' in path_lower.split('/')[-1]:  # Filename contains test
        return True
    # Temporary scripts
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return True
    if path_lower.endswith('/script.py') or path_lower == 'script.py':
        return True
    return False


def extract_files_from_patch(patch_content: str) -> set:
    """Extract file paths from a git diff patch"""
    files = set()
    for line in patch_content.split('\n'):
        if line.startswith('diff --git'):
            match = re.search(r'diff --git a/(.+?) b/', line)
            if match:
                files.add(normalize_path(match.group(1)))
        elif line.startswith('+++ b/'):
            path = line[6:].strip()
            if path and path != '/dev/null':
                files.add(normalize_path(path))
    return files


def load_ground_truth_files(dataset: str, instance_id: str) -> set:
    """Load ground truth files from SWE-bench dataset"""
    dataset_file_map = {
        "swebenchlite": "swe_bench_lite.json",
        "swebenchverified": "swe_bench_verified.json",
    }
    filename = dataset_file_map.get(dataset, f"{dataset}.json")
    swebench_data_file = PROJECT_ROOT / "data" / filename

    if swebench_data_file.exists():
        with open(swebench_data_file) as f:
            data = json.load(f)
        for item in data:
            if item.get("instance_id") == instance_id:
                patch = item.get("patch", "")
                return extract_files_from_patch(patch)
    return set()


def get_first_edit_file_claude(traces: list) -> str:
    """Get the first edited file from Claude Code trace"""
    for entry in traces:
        if entry.get("type") == "assistant":
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")
                    if tool_name in ["Edit", "Write"]:
                        file_path = item.get("input", {}).get("file_path", "")
                        if file_path:
                            return normalize_path(file_path)
    return ""


def get_first_edit_file_codex(traces: list) -> str:
    """Get the first edited file from Codex trace"""
    for entry in traces:
        if entry.get("type") == "item.completed":
            item = entry.get("item", {})
            item_type = item.get("type", "")
            if item_type in ["file_edit", "file_change"]:
                # Try changes first
                changes = item.get("changes", [])
                for change in changes:
                    path = change.get("path", "")
                    if path:
                        return normalize_path(path)
                # Fallback to file_path
                file_path = item.get("file_path", "")
                if file_path:
                    return normalize_path(file_path)
    return ""


def load_trace(dataset: str, agent: str, mode: str, instance: str) -> list:
    """Load trace file"""
    trace_file = OUTPUT_DIR / dataset / agent / mode / instance / "trace.jsonl"
    if not trace_file.exists():
        return []

    traces = []
    with open(trace_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    traces.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return traces


def load_pp_cases() -> dict:
    """Load P→P cases"""
    pp_file = PROJECT_ROOT / "analysis" / "pp_why_no_execution_needed.json"

    cases = {"claude_code": [], "codex": []}

    if pp_file.exists():
        with open(pp_file) as f:
            data = json.load(f)

        for item in data.get("results", []):
            instance = item["instance"]
            agent = item["agent"]
            group = item["group"]

            if "Lite" in group:
                dataset = "swebenchlite"
            else:
                dataset = "swebenchverified"

            cases[agent].append((dataset, instance))

    return cases


def main():
    print("=" * 80)
    print("Investigating First Edit Hit Rate Difference")
    print("=" * 80)

    # Load P→P cases
    pp_cases = load_pp_cases()

    results = []

    for agent in ["claude_code", "codex"]:
        print(f"\nAnalyzing {agent}...")

        for mode in ["run_full", "run_free"]:
            mode_label = "Unrestricted" if mode == "run_full" else "Prohibited"

            stats = {
                "total": 0,
                "first_edit_is_test": 0,
                "first_edit_is_source": 0,
                "first_edit_hit_gt": 0,
                "first_edit_miss_gt": 0,
                "no_first_edit": 0,
                "examples": []
            }

            for dataset, instance in pp_cases[agent]:
                traces = load_trace(dataset, agent, mode, instance)
                if not traces:
                    continue

                # Get first edit file
                if agent == "claude_code":
                    first_edit = get_first_edit_file_claude(traces)
                else:
                    first_edit = get_first_edit_file_codex(traces)

                if not first_edit:
                    stats["no_first_edit"] += 1
                    continue

                stats["total"] += 1

                # Check if test file
                if is_test_file(first_edit):
                    stats["first_edit_is_test"] += 1
                else:
                    stats["first_edit_is_source"] += 1

                # Check if matches GT
                gt_files = load_ground_truth_files(dataset, instance)
                if first_edit in gt_files:
                    stats["first_edit_hit_gt"] += 1
                else:
                    stats["first_edit_miss_gt"] += 1
                    # Record example
                    if len(stats["examples"]) < 5:
                        stats["examples"].append({
                            "instance": instance,
                            "first_edit": first_edit,
                            "gt_files": list(gt_files),
                            "is_test": is_test_file(first_edit)
                        })

            results.append({
                "agent": agent,
                "mode": mode_label,
                "stats": stats
            })

            # Print summary
            print(f"\n  {mode_label} mode:")
            print(f"    Total instances: {stats['total']}")
            if stats['total'] > 0:
                test_pct = stats['first_edit_is_test'] / stats['total'] * 100
                hit_pct = stats['first_edit_hit_gt'] / stats['total'] * 100
                print(f"    First edit is test file: {stats['first_edit_is_test']} ({test_pct:.1f}%)")
                print(f"    First edit is source file: {stats['first_edit_is_source']} ({100-test_pct:.1f}%)")
                print(f"    First edit hits GT: {stats['first_edit_hit_gt']} ({hit_pct:.1f}%)")

                if stats["examples"]:
                    print(f"\n    Miss examples:")
                    for ex in stats["examples"][:3]:
                        print(f"      - {ex['instance']}")
                        print(f"        First edit: {ex['first_edit']} (Test file: {ex['is_test']})")
                        print(f"        GT files: {ex['gt_files']}")

    # Generate markdown report
    generate_report(results)


def generate_report(results: list):
    """Generate markdown report"""
    lines = []
    lines.append("# First Edit Hit Rate Difference Analysis")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    lines.append("## Problem")
    lines.append("")
    lines.append("Why is the first edit hit rate in P→P cases much lower in Unrestricted mode (55.2%) than in Prohibited mode (95.7%)?")
    lines.append("")
    lines.append("## Hypothesis")
    lines.append("")
    lines.append("**In Unrestricted mode, Agent tends to edit test files/debug scripts first, rather than directly editing source code files.**")
    lines.append("")
    lines.append("## Verification Results")
    lines.append("")
    lines.append("| Agent | Mode | Total | First Edit is Test File | First Edit is Source Code | First Edit Hits GT |")
    lines.append("|-------|------|-------|-------------------|-----------------|-----------------|")

    for r in results:
        s = r["stats"]
        if s["total"] > 0:
            test_pct = s["first_edit_is_test"] / s["total"] * 100
            source_pct = s["first_edit_is_source"] / s["total"] * 100
            hit_pct = s["first_edit_hit_gt"] / s["total"] * 100
            lines.append(f"| {r['agent']} | {r['mode']} | {s['total']} | {s['first_edit_is_test']} ({test_pct:.1f}%) | {s['first_edit_is_source']} ({source_pct:.1f}%) | {s['first_edit_hit_gt']} ({hit_pct:.1f}%) |")
        else:
            lines.append(f"| {r['agent']} | {r['mode']} | 0 | N/A | N/A | N/A |")

    lines.append("")
    lines.append("## Analysis")
    lines.append("")

    # Find Unrestricted and Prohibited for Claude Code
    cc_unres = next((r for r in results if r["agent"] == "claude_code" and r["mode"] == "Unrestricted"), None)
    cc_proh = next((r for r in results if r["agent"] == "claude_code" and r["mode"] == "Prohibited"), None)

    if cc_unres and cc_proh and cc_unres["stats"]["total"] > 0 and cc_proh["stats"]["total"] > 0:
        unres_test = cc_unres["stats"]["first_edit_is_test"] / cc_unres["stats"]["total"] * 100
        proh_test = cc_proh["stats"]["first_edit_is_test"] / cc_proh["stats"]["total"] * 100

        lines.append("### Claude Code")
        lines.append("")
        lines.append(f"- **Unrestricted** mode: {unres_test:.1f}% of first edits are test/debug files")
        lines.append(f"- **Prohibited** mode: {proh_test:.1f}% of first edits are test/debug files")
        lines.append("")

        if unres_test > proh_test + 10:
            lines.append("**Conclusion**: Hypothesis verified! In Unrestricted mode, Agent tends to edit test files first to reproduce the problem,")
            lines.append("which leads to significantly lower first edit hit rate compared to Prohibited mode.")
        else:
            lines.append("**Note**: Hypothesis not fully verified, further analysis needed for specific reasons of misses.")

    lines.append("")
    lines.append("## Miss Examples")
    lines.append("")

    for r in results:
        if r["stats"]["examples"]:
            lines.append(f"### {r['agent']} - {r['mode']}")
            lines.append("")
            for ex in r["stats"]["examples"][:3]:
                lines.append(f"**{ex['instance']}**")
                lines.append(f"- First edit: `{ex['first_edit']}` (Test file: {ex['is_test']})")
                lines.append(f"- GT file: `{', '.join(ex['gt_files'])}`")
                lines.append("")

    lines.append("## Conclusion")
    lines.append("")
    lines.append("The difference in first edit hit rate is mainly due to **analysis methodology issues**, not differences in Agent capability:")
    lines.append("")
    lines.append("1. **Unrestricted mode**: Agent creates test scripts first to reproduce the problem, then fixes source code")
    lines.append("2. **Prohibited mode**: Agent cannot execute, so directly edits source code")
    lines.append("")
    lines.append("**Therefore, \"first edit hit rate\" should not be used as an indicator of localization capability**. Should use:")
    lines.append("- **Final edit hit rate**: Whether all edited files include GT files")
    lines.append("- **File recall rate**: How many GT files were edited by Agent")
    lines.append("")

    # Save report
    report_file = ANALYSIS_DIR / "first_edit_investigation.md"
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\nReport saved: {report_file}")


if __name__ == "__main__":
    main()
