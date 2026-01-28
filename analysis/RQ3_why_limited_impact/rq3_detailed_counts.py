#!/usr/bin/env python3
"""
RQ3 Supplementary Analysis: Complete Verification/Reproduction Statistics

Complete two metrics:
1. Reproduction success/fail (count) - Whether reproduction execution provides effective localization signals
2. Verification total attempt count statistics - Not just first/any
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Set
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


def normalize_path(path: str) -> str:
    if path.startswith('./'):
        path = path[2:]
    if path.startswith('/'):
        path = path.lstrip('/')
    if path.startswith('testbed/'):
        path = path[8:]
    return path


def is_test_execution(cmd: str) -> bool:
    cmd_lower = cmd.lower().strip()
    test_patterns = [
        r'\bpytest\b', r'\bpy\.test\b', r'python[3]?\s+-m\s+pytest',
        r'python[3]?\s+-m\s+unittest', r'manage\.py\s+test',
        r'\btox\b', r'\bnosetests?\b',
    ]
    for pattern in test_patterns:
        if re.search(pattern, cmd_lower):
            return True
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        if not re.search(r'python[3]?\s+-c\s', cmd_lower):
            return True
    return False


def is_test_file(path: str) -> bool:
    """Check if it's a test file (not a source code file)"""
    path_lower = path.lower()
    # Test file characteristics
    if '/test_' in path_lower or '/tests/' in path_lower:
        return True
    if path_lower.endswith('_test.py'):
        return True
    if 'test' in path_lower.split('/')[-1]:  # Filename contains test
        return True
    # Temporary scripts (for reproduction)
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return True
    if 'script' in path_lower.split('/')[-1]:
        return True
    # Check if it's a temporary file in project root
    if path_lower.count('/') == 0:  # No directory, may be a temporary script
        if path_lower.endswith('.py'):
            return True
    return False


def classify_execution_result(content: str) -> str:
    """
    Classify execution result:
    - actionable: Contains useful information (stacktrace, file path, test name)
    - env_error: Environment errors (pytest not installed, path errors, etc.)
    - success: Tests passed
    - test_fail: Test failure (but contains useful information)
    """
    content_lower = content.lower()

    # Environment errors
    env_errors = ['No module named', 'ModuleNotFoundError', 'command not found',
                  'FileNotFoundError', 'No such file or directory',
                  'Permission denied', 'UnicodeDecodeError', 'encoding']
    for err in env_errors:
        if err in content or err.lower() in content_lower:
            return "env_error"

    # Success
    if 'passed' in content_lower and 'failed' not in content_lower:
        return "success"
    if content.strip().endswith('OK') or '\nOK' in content:
        return "success"

    # Test failure (but contains useful information)
    if 'FAILED' in content or 'AssertionError' in content:
        return "test_fail"
    if 'Traceback (most recent call last)' in content:
        return "test_fail"

    # Default: may have information but uncertain
    return "unknown"


def is_actionable(content: str, result_type: str) -> bool:
    """
    Check if execution result is actionable (provides information useful for localization)
    - Contains file path
    - Contains stacktrace
    - Contains specific test name/error message
    """
    if result_type == "env_error":
        return False
    if result_type == "success":
        return True  # Successful reproduction = confirms bug location

    # Check if it contains useful information
    has_filepath = bool(re.search(r'[a-zA-Z_][a-zA-Z0-9_/]*\.py', content))
    has_traceback = 'Traceback' in content or 'File "' in content
    has_line_number = bool(re.search(r'line \d+', content.lower()))

    return has_filepath or has_traceback or has_line_number


@dataclass
class InstanceStats:
    instance_id: str
    agent: str
    outcome: str  # pp or ff

    # Reproduction stats
    reproduction_count: int = 0
    reproduction_actionable: int = 0
    reproduction_non_actionable: int = 0

    # Verification stats
    verification_count: int = 0
    verification_success: int = 0
    verification_test_fail: int = 0
    verification_env_error: int = 0
    verification_unknown: int = 0


def analyze_claude_trace(traces: list, instance_id: str, outcome: str) -> InstanceStats:
    stats = InstanceStats(instance_id=instance_id, agent="claude_code", outcome=outcome)

    first_source_edit_found = False  # Changed to: first source code file edit
    pending_exec = None

    for entry in traces:
        entry_type = entry.get("type", "")

        if entry_type == "assistant":
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")

                    if tool_name in ["Edit", "Write"]:
                        file_path = item.get("input", {}).get("file_path", "")
                        # Only editing source code files counts as "first edit"
                        if file_path and not is_test_file(file_path):
                            first_source_edit_found = True

                    if tool_name == "Bash":
                        cmd = item.get("input", {}).get("command", "")
                        if is_test_execution(cmd):
                            pending_exec = {"is_after_source_edit": first_source_edit_found}

        elif entry_type == "user" and pending_exec:
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    result = item.get("content", "")
                    if isinstance(result, str):
                        result_type = classify_execution_result(result)
                        actionable = is_actionable(result, result_type)

                        if pending_exec["is_after_source_edit"]:
                            # Verification: test execution after editing source code
                            stats.verification_count += 1
                            if result_type == "success":
                                stats.verification_success += 1
                            elif result_type == "test_fail":
                                stats.verification_test_fail += 1
                            elif result_type == "env_error":
                                stats.verification_env_error += 1
                            else:
                                stats.verification_unknown += 1
                        else:
                            # Reproduction: test execution before editing source code (including writing tests first then running)
                            stats.reproduction_count += 1
                            if actionable:
                                stats.reproduction_actionable += 1
                            else:
                                stats.reproduction_non_actionable += 1

            pending_exec = None

    return stats


def analyze_codex_trace(traces: list, instance_id: str, outcome: str) -> InstanceStats:
    stats = InstanceStats(instance_id=instance_id, agent="codex", outcome=outcome)

    first_source_edit_found = False  # Changed to: first source code file edit

    for entry in traces:
        entry_type = entry.get("type", "")

        if entry_type == "item.completed":
            item = entry.get("item", {})
            item_type = item.get("type", "")

            if item_type in ["file_edit", "file_change"]:
                # Get file path
                file_path = ""
                changes = item.get("changes", [])
                for change in changes:
                    path = change.get("path", "")
                    if path:
                        file_path = path
                        break
                if not file_path:
                    file_path = item.get("file_path", "")

                # Only editing source code files counts as "first edit"
                if file_path and not is_test_file(file_path):
                    first_source_edit_found = True

            if item_type == "command_execution":
                cmd = item.get("command", "")
                if "bash -lc" in cmd:
                    match = re.search(r"'([^']+)'[^']*$", cmd)
                    if match:
                        cmd = match.group(1)

                if is_test_execution(cmd):
                    result = item.get("aggregated_output", "")
                    exit_code = item.get("exit_code")

                    if exit_code is not None:
                        if exit_code == 0:
                            result_type = "success"
                        else:
                            result_type = classify_execution_result(result)
                    else:
                        result_type = classify_execution_result(result)

                    actionable = is_actionable(result, result_type)

                    if first_source_edit_found:
                        # Verification: test execution after editing source code
                        stats.verification_count += 1
                        if result_type == "success":
                            stats.verification_success += 1
                        elif result_type == "test_fail":
                            stats.verification_test_fail += 1
                        elif result_type == "env_error":
                            stats.verification_env_error += 1
                        else:
                            stats.verification_unknown += 1
                    else:
                        # Reproduction: test execution before editing source code
                        stats.reproduction_count += 1
                        if actionable:
                            stats.reproduction_actionable += 1
                        else:
                            stats.reproduction_non_actionable += 1

    return stats


def load_trace(dataset: str, agent: str, mode: str, instance: str) -> list:
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


def load_outcome_cases() -> dict:
    pp_file = PROJECT_ROOT / "analysis" / "pp_why_no_execution_needed.json"

    cases = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    if pp_file.exists():
        with open(pp_file) as f:
            data = json.load(f)

        for item in data.get("results", []):
            instance = item["instance"]
            agent = item["agent"]
            group = item["group"]
            dataset = "swebenchlite" if "Lite" in group else "swebenchverified"
            cases[agent]["pp"].append((dataset, instance))

    pp_sets = {
        "claude_code": set(inst for _, inst in cases["claude_code"]["pp"]),
        "codex": set(inst for _, inst in cases["codex"]["pp"])
    }

    for dataset in ["swebenchlite", "swebenchverified"]:
        for agent in ["claude_code", "codex"]:
            free_dir = OUTPUT_DIR / dataset / agent / "run_free"
            full_dir = OUTPUT_DIR / dataset / agent / "run_full"

            if not free_dir.exists() or not full_dir.exists():
                continue

            free_instances = set(d.name for d in free_dir.iterdir() if d.is_dir())
            full_instances = set(d.name for d in full_dir.iterdir() if d.is_dir())
            common = free_instances & full_instances

            for instance in common:
                if instance not in pp_sets[agent]:
                    cases[agent]["ff"].append((dataset, instance))

    return cases


def main():
    print("=" * 80)
    print("RQ3 Supplementary Analysis: Complete Verification/Reproduction Statistics")
    print("=" * 80)

    cases = load_outcome_cases()

    # Only analyze Unrestricted mode
    results = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    for agent in ["claude_code", "codex"]:
        for outcome in ["pp", "ff"]:
            print(f"\nAnalyzing {agent} {outcome.upper()}...")

            for dataset, instance in cases[agent][outcome]:
                traces = load_trace(dataset, agent, "run_full", instance)
                if not traces:
                    continue

                if agent == "claude_code":
                    stats = analyze_claude_trace(traces, instance, outcome)
                else:
                    stats = analyze_codex_trace(traces, instance, outcome)

                results[agent][outcome].append(stats)

    # Generate report
    generate_report(results)


def generate_report(results: dict):
    lines = []
    lines.append("# RQ3 Supplementary Analysis: Complete Verification/Reproduction Statistics")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    # 1. Reproduction statistics
    lines.append("## 1. Reproduction Execution Statistics")
    lines.append("")
    lines.append("**Definition**: Test executions that occur before the first file edit, used for understanding/localizing bugs.")
    lines.append("")
    lines.append("- **Actionable**: Execution result contains useful information (file path, stacktrace, line number), can be used for localization")
    lines.append("- **Non-actionable**: Environment errors or no useful information")
    lines.append("")

    lines.append("### P->P Cases (Unrestricted Mode)")
    lines.append("")
    lines.append("| Agent | Has Repro. | Total Execs | Actionable | Non-actionable |")
    lines.append("|-------|-----------|-------------|------------|----------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp_stats = results[agent]["pp"]

        has_repro = sum(1 for s in pp_stats if s.reproduction_count > 0)
        total_repro = sum(s.reproduction_count for s in pp_stats)
        actionable = sum(s.reproduction_actionable for s in pp_stats)
        non_actionable = sum(s.reproduction_non_actionable for s in pp_stats)

        has_repro_pct = has_repro / len(pp_stats) * 100 if pp_stats else 0
        actionable_pct = actionable / total_repro * 100 if total_repro > 0 else 0

        lines.append(f"| {agent_label} | {has_repro} ({has_repro_pct:.1f}%) | {total_repro} | {actionable} ({actionable_pct:.1f}%) | {non_actionable} |")

    lines.append("")

    # 2. Verification statistics
    lines.append("## 2. Verification Execution Statistics")
    lines.append("")
    lines.append("**Definition**: Test executions that occur after the first file edit, used for verifying patches.")
    lines.append("")

    lines.append("### P->P Cases (Unrestricted Mode)")
    lines.append("")
    lines.append("| Agent | Has Verif. | Total Execs | Success | Test Fail | Env Error |")
    lines.append("|-------|-----------|-------------|---------|-----------|-----------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp_stats = results[agent]["pp"]

        has_verif = sum(1 for s in pp_stats if s.verification_count > 0)
        total_verif = sum(s.verification_count for s in pp_stats)
        success = sum(s.verification_success for s in pp_stats)
        test_fail = sum(s.verification_test_fail for s in pp_stats)
        env_error = sum(s.verification_env_error for s in pp_stats)

        has_verif_pct = has_verif / len(pp_stats) * 100 if pp_stats else 0
        success_pct = success / total_verif * 100 if total_verif > 0 else 0
        test_fail_pct = test_fail / total_verif * 100 if total_verif > 0 else 0
        env_error_pct = env_error / total_verif * 100 if total_verif > 0 else 0

        lines.append(f"| {agent_label} | {has_verif} ({has_verif_pct:.1f}%) | {total_verif} | {success} ({success_pct:.1f}%) | {test_fail} ({test_fail_pct:.1f}%) | {env_error} ({env_error_pct:.1f}%) |")

    lines.append("")

    lines.append("### F->F Cases (Unrestricted Mode)")
    lines.append("")
    lines.append("| Agent | Has Verif. | Total Execs | Success | Test Fail | Env Error |")
    lines.append("|-------|-----------|-------------|---------|-----------|-----------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        ff_stats = results[agent]["ff"]

        has_verif = sum(1 for s in ff_stats if s.verification_count > 0)
        total_verif = sum(s.verification_count for s in ff_stats)
        success = sum(s.verification_success for s in ff_stats)
        test_fail = sum(s.verification_test_fail for s in ff_stats)
        env_error = sum(s.verification_env_error for s in ff_stats)

        has_verif_pct = has_verif / len(ff_stats) * 100 if ff_stats else 0
        success_pct = success / total_verif * 100 if total_verif > 0 else 0
        test_fail_pct = test_fail / total_verif * 100 if total_verif > 0 else 0
        env_error_pct = env_error / total_verif * 100 if total_verif > 0 else 0

        lines.append(f"| {agent_label} | {has_verif} ({has_verif_pct:.1f}%) | {total_verif} | {success} ({success_pct:.1f}%) | {test_fail} ({test_fail_pct:.1f}%) | {env_error} ({env_error_pct:.1f}%) |")

    lines.append("")

    # 3. Average statistics
    lines.append("## 3. Average Executions Per Instance")
    lines.append("")
    lines.append("| Agent | Outcome | Avg. Repro/Instance | Avg. Verif/Instance |")
    lines.append("|-------|---------|---------------------|---------------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        for outcome in ["pp", "ff"]:
            outcome_label = "P->P" if outcome == "pp" else "F->F"
            stats_list = results[agent][outcome]

            if stats_list:
                avg_repro = sum(s.reproduction_count for s in stats_list) / len(stats_list)
                avg_verif = sum(s.verification_count for s in stats_list) / len(stats_list)
                lines.append(f"| {agent_label} | {outcome_label} | {avg_repro:.2f} | {avg_verif:.2f} |")

    lines.append("")

    # 4. Key findings
    lines.append("## 4. Key Findings")
    lines.append("")

    # Claude Code P->P
    cc_pp = results["claude_code"]["pp"]
    if cc_pp:
        total_repro = sum(s.reproduction_count for s in cc_pp)
        actionable = sum(s.reproduction_actionable for s in cc_pp)
        total_verif = sum(s.verification_count for s in cc_pp)
        success = sum(s.verification_success for s in cc_pp)
        env_error = sum(s.verification_env_error for s in cc_pp)

        lines.append("### Claude Code")
        lines.append("")
        if total_repro > 0:
            lines.append(f"- **Reproduction**: Out of {total_repro} executions, {actionable} ({actionable/total_repro*100:.1f}%) provided information useful for localization")
        lines.append(f"- **Verification**: Out of {total_verif} executions, {success} ({success/total_verif*100:.1f}%) succeeded, {env_error} ({env_error/total_verif*100:.1f}%) were environment errors")
        lines.append("")

    # Codex P->P
    cx_pp = results["codex"]["pp"]
    if cx_pp:
        total_repro = sum(s.reproduction_count for s in cx_pp)
        actionable = sum(s.reproduction_actionable for s in cx_pp)
        total_verif = sum(s.verification_count for s in cx_pp)
        success = sum(s.verification_success for s in cx_pp)
        env_error = sum(s.verification_env_error for s in cx_pp)

        lines.append("### Codex")
        lines.append("")
        if total_repro > 0:
            lines.append(f"- **Reproduction**: Out of {total_repro} executions, {actionable} ({actionable/total_repro*100:.1f}%) provided information useful for localization")
        lines.append(f"- **Verification**: Out of {total_verif} executions, {success} ({success/total_verif*100:.1f}%) succeeded, {env_error} ({env_error/total_verif*100:.1f}%) were environment errors")
        lines.append("")

    # Save
    report_file = ANALYSIS_DIR / "rq3_detailed_counts.md"
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\nReport saved: {report_file}")

    # Also save JSON
    json_file = ANALYSIS_DIR / "rq3_detailed_counts.json"

    # Convert to serializable format
    json_data = {}
    for agent in ["claude_code", "codex"]:
        json_data[agent] = {}
        for outcome in ["pp", "ff"]:
            stats_list = results[agent][outcome]
            json_data[agent][outcome] = {
                "count": len(stats_list),
                "reproduction": {
                    "total": sum(s.reproduction_count for s in stats_list),
                    "actionable": sum(s.reproduction_actionable for s in stats_list),
                    "non_actionable": sum(s.reproduction_non_actionable for s in stats_list),
                },
                "verification": {
                    "total": sum(s.verification_count for s in stats_list),
                    "success": sum(s.verification_success for s in stats_list),
                    "test_fail": sum(s.verification_test_fail for s in stats_list),
                    "env_error": sum(s.verification_env_error for s in stats_list),
                }
            }

    with open(json_file, "w") as f:
        json.dump(json_data, f, indent=2)
    print(f"JSON saved: {json_file}")


if __name__ == "__main__":
    main()
