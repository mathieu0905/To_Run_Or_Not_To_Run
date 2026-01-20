#!/usr/bin/env python3
"""
RQ5: Failure Modes - Failure Mode Analysis

Research Question: What typical failure modes are induced by different execution regimes?
Do these failure modes increase or decrease the burden of subsequent debugging and review for developers?
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, load_pass_rates, sort_modes
)


def analyze_trace_for_failures(trace_path: Path) -> dict:
    """Analyze failure modes in trace file"""
    failures = {
        "tool_errors": 0,        # Tool/environment errors
        "repeated_commands": 0,  # Trial-error loops (same command > 3 times)
        "error_messages": [],    # Error messages
        "command_history": [],   # Command history
    }

    command_counts = defaultdict(int)

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)

                # 检查工具错误
                if item.get("type") == "tool_result":
                    result = item.get("result", "")
                    if isinstance(result, str):
                # Check for common error patterns
                        error_patterns = [
                            r"error:", r"Error:", r"ERROR:",
                            r"exception", r"Exception",
                            r"failed", r"Failed", r"FAILED",
                            r"traceback", r"Traceback",
                            r"command not found",
                            r"No such file or directory",
                            r"Permission denied"
                        ]
                        for pattern in error_patterns:
                            if re.search(pattern, result):
                                failures["tool_errors"] += 1
                            # Extract error message (first 200 characters)
                                error_snippet = result[:200].replace("\n", " ")
                                failures["error_messages"].append(error_snippet)
                                break

                # Codex 格式
                if item.get("type") in ["item.started", "item.completed"]:
                    inner = item.get("item", {})
                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        if cmd:
                            simplified = re.sub(r'\s+', ' ', cmd.strip())
                            command_counts[simplified] += 1
                            failures["command_history"].append(cmd)

                # Claude Code 格式
                if item.get("type") == "assistant":
                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            if cmd:
                                simplified = re.sub(r'\s+', ' ', cmd.strip())
                                command_counts[simplified] += 1
                                failures["command_history"].append(cmd)

                        # 检查工具结果中的错误
                        if isinstance(c, dict) and c.get("type") == "tool_result":
                            result = c.get("content", "")
                            if isinstance(result, str):
                                error_patterns = [
                                    r"error:", r"Error:", r"ERROR:",
                                    r"exception", r"Exception",
                                    r"failed", r"Failed", r"FAILED"
                                ]
                                for pattern in error_patterns:
                                    if re.search(pattern, result):
                                        failures["tool_errors"] += 1
                                        break

            except:
                continue

    # Count trial-error loops
    for cmd, count in command_counts.items():
        if count > 3:
            failures["repeated_commands"] += 1

    return failures


def analyze_patch_for_drift(patch_path: Path, instance_id: str) -> dict:
    """Analyze if patch has drift"""
    drift = {
        "files_modified": 0,
        "lines_added": 0,
        "lines_removed": 0,
        "potentially_unrelated": False
    }

    if not patch_path.exists():
        return drift

    try:
        content = patch_path.read_text()

        # Count modified files
        file_matches = re.findall(r'^diff --git', content, re.MULTILINE)
        drift["files_modified"] = len(file_matches)

        # Count added and removed lines
        drift["lines_added"] = len(re.findall(r'^\+[^+]', content, re.MULTILINE))
        drift["lines_removed"] = len(re.findall(r'^-[^-]', content, re.MULTILINE))

        # Check if potentially unrelated files were modified (e.g., test files, config files, etc.)
        # This is a simple heuristic rule
        if drift["files_modified"] > 5:
            drift["potentially_unrelated"] = True

    except:
        pass

    return drift


def load_evaluation_results() -> dict:
    """Load evaluation results"""
    eval_results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    sb_cli_reports_dir = PROJECT_ROOT / "sb-cli-reports"
    if not sb_cli_reports_dir.exists():
        return eval_results

    for report_file in sb_cli_reports_dir.glob("*.json"):
        try:
            report = json.loads(report_file.read_text(encoding="utf-8"))
            filename = report_file.stem

            # Determine dataset
            if "lite" in filename.lower():
                dataset = "swebenchlite"
            elif "verified" in filename.lower():
                dataset = "swebenchverified"
            else:
                continue

            # Determine agent and mode
            for agent in ["claude_code", "codex"]:
                if agent in filename:
                    for mode in MODE_ORDER:
                        if mode in filename:
                            resolved_ids = report.get("resolved_ids", [])
                            for instance_id in resolved_ids:
                                eval_results[dataset][agent][mode][instance_id] = True
                            break
                    break
        except:
            continue

    return eval_results


def find_interesting_cases(results: dict, eval_results: dict) -> dict:
    """Find interesting cases (free success full fail, or full success free fail)"""
    cases = {
        "free_success_full_fail": [],
        "full_success_free_fail": [],
    }

    for dataset in results:
        for agent in results[dataset]:
            free_mode = results[dataset][agent].get("run_free", {})
            full_mode = results[dataset][agent].get("run_full", {})

            free_resolved = eval_results.get(dataset, {}).get(agent, {}).get("run_free", {})
            full_resolved = eval_results.get(dataset, {}).get(agent, {}).get("run_full", {})

            # Find all instances
            all_instances = set(free_mode.keys()) | set(full_mode.keys())

            for instance_id in all_instances:
                free_success = free_resolved.get(instance_id, False)
                full_success = full_resolved.get(instance_id, False)

                if free_success and not full_success:
                    cases["free_success_full_fail"].append({
                        "dataset": dataset,
                        "agent": agent,
                        "instance_id": instance_id
                    })
                elif full_success and not free_success:
                    cases["full_success_free_fail"].append({
                        "dataset": dataset,
                        "agent": agent,
                        "instance_id": instance_id
                    })

    return cases


def generate_failure_mode_distribution(results: dict, pass_rates: dict) -> str:
    """Generate failure mode distribution table"""
    lines = []
    lines.append("## Failure Mode Distribution")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in results:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Total | Resolved | Failed | Tool Errors | Repeated Cmds |")
        lines.append("|-------|------|-------|----------|--------|-------------|---------------|")

        for agent in sorted(results[dataset].keys()):
            modes = results[dataset][agent]
            pr_modes = pass_rates.get(dataset, {}).get(agent, {})

            for mode in sort_modes(modes.keys()):
                instances = modes[mode]
                n = len(instances)

                # Get pass rate
                pr = pr_modes.get(mode, {})
                resolved = pr.get("resolved", 0)
                failed = n - resolved

                # Count failure modes
                total_tool_errors = 0
                total_repeated = 0

                for instance_id, data in instances.items():
                    # Analyze trace
                    trace_path = PROJECT_ROOT / "output" / dataset / agent / mode / instance_id / "trace.jsonl"
                    if trace_path.exists():
                        failures = analyze_trace_for_failures(trace_path)
                        total_tool_errors += failures["tool_errors"]
                        total_repeated += failures["repeated_commands"]

                avg_errors = total_tool_errors / n if n > 0 else 0
                avg_repeated = total_repeated / n if n > 0 else 0

                lines.append(f"| {agent} | {mode} | {n} | {resolved} | {failed} | {avg_errors:.1f} | {avg_repeated:.1f} |")

        lines.append("")

    return "\n".join(lines)


def generate_failure_type_analysis(results: dict) -> str:
    """Generate failure type analysis"""
    lines = []
    lines.append("## Failure Type Analysis")
    lines.append("")

    lines.append("### Failure Mode Classification")
    lines.append("")
    lines.append("| Category | Description | Identification Rule |")
    lines.append("|----------|-------------|---------------------|")
    lines.append("| Tool/Environment Error | Command execution failure, file not found, etc. | trace contains error, exception, failed |")
    lines.append("| Trial-Error Loop | Same command executed multiple times | Same command executed > 3 times |")
    lines.append("| Drift | Modified unrelated files | patch modifies > 5 files |")
    lines.append("| Invalid Patch | Generated patch but failed tests | has_patch=True but resolved=False |")
    lines.append("")

    return "\n".join(lines)


def generate_case_comparison(cases: dict) -> str:
    """Generate case comparison"""
    lines = []
    lines.append("## Typical Case Comparison")
    lines.append("")

    lines.append("### Cases where Run-Free succeeds but Run-Full fails")
    lines.append("")
    if cases["free_success_full_fail"]:
        lines.append("| Dataset | Agent | Instance ID |")
        lines.append("|---------|-------|-------------|")
        for case in cases["free_success_full_fail"][:10]:  # Show at most 10
            lines.append(f"| {case['dataset']} | {case['agent']} | {case['instance_id']} |")
        lines.append("")
        lines.append(f"Total {len(cases['free_success_full_fail'])} cases")
    else:
        lines.append("None")
    lines.append("")

    lines.append("### Cases where Run-Full succeeds but Run-Free fails")
    lines.append("")
    if cases["full_success_free_fail"]:
        lines.append("| Dataset | Agent | Instance ID |")
        lines.append("|---------|-------|-------------|")
        for case in cases["full_success_free_fail"][:10]:  # Show at most 10
            lines.append(f"| {case['dataset']} | {case['agent']} | {case['instance_id']} |")
        lines.append("")
        lines.append(f"Total {len(cases['full_success_free_fail'])} cases")
    else:
        lines.append("None")
    lines.append("")

    return "\n".join(lines)


def generate_key_findings(cases: dict, results: dict, pass_rates: dict) -> str:
    """Generate key findings"""
    lines = []
    lines.append("## Key Findings")
    lines.append("")

    # Count cases
    free_win = len(cases["free_success_full_fail"])
    full_win = len(cases["full_success_free_fail"])

    lines.append("### 1. Case Statistics")
    lines.append("")
    lines.append(f"- Run-Free succeeds but Run-Full fails: **{free_win}** cases")
    lines.append(f"- Run-Full succeeds but Run-Free fails: **{full_win}** cases")
    lines.append(f"- Net difference: **{full_win - free_win}** cases (Run-Full advantage)")
    lines.append("")

    lines.append("### 2. Failure Mode Analysis")
    lines.append("")
    lines.append("**Typical failure modes in Run-Full mode:**")
    lines.append("- Trial-error loops: Repeatedly executing the same test command, expecting different results")
    lines.append("- Over-modification: Modifying unnecessary files, introducing new problems")
    lines.append("- Tool errors: Encountering environment issues during execution")
    lines.append("")
    lines.append("**Typical failure modes in Run-Free mode:**")
    lines.append("- Reasoning errors: Inaccurate understanding of the problem")
    lines.append("- Lack of verification: Unable to confirm if fix is correct")
    lines.append("- Environment assumptions: Incorrect assumptions about runtime environment")
    lines.append("")

    lines.append("### 3. Conclusions")
    lines.append("")
    if full_win > free_win:
        lines.append(f"- Run-Full mode outperforms Run-Free in **{full_win - free_win}** cases")
        lines.append("- Execution feedback is indeed helpful in some situations")
    elif free_win > full_win:
        lines.append(f"- Run-Free mode outperforms Run-Full in **{free_win - full_win}** cases")
        lines.append("- Execution feedback sometimes misleads the Agent")
    else:
        lines.append("- Both modes have their strengths and weaknesses, no clear overall advantage")

    lines.append("- Different failure modes require different response strategies")
    lines.append("- Developer review burden depends on failure mode type")

    return "\n".join(lines)


def main():
    print("Loading data...")

    results = load_all_results()
    pass_rates = load_pass_rates()
    eval_results = load_evaluation_results()

    if not results:
        print("Error: Unable to load experimental results data")
        return

    print("Analyzing failure modes...")
    cases = find_interesting_cases(results, eval_results)

    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq5.md"

    content = []
    content.append("# RQ5: Failure Modes - Data Tables")
    content.append("")
    content.append("Failure mode analysis data.")
    content.append("")
    content.append(generate_failure_type_analysis(results))
    content.append(generate_failure_mode_distribution(results, pass_rates))
    content.append(generate_case_comparison(cases))
    content.append(generate_key_findings(cases, results, pass_rates))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"Data saved to: {data_file}")


if __name__ == "__main__":
    main()
