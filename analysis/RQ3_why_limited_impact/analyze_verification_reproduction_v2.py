#!/usr/bin/env python3
"""
RQ3 Analysis v2: Why Does Execution Have Limited Impact?

Two angles:
1. Verification: Is the first verification after edit successful?
   - If success → Agent got it right first time, verification is redundant
   - If fail → Needs iteration

2. Reproduction: Does reproduction help locate the correct files?
   - Compare file localization accuracy with/without reproduction
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


@dataclass
class InstanceAnalysis:
    """Analysis result for a single instance"""
    instance_id: str
    agent: str
    dataset: str = ""

    # Outcome category
    outcome: str = ""  # "pp" or "ff"

    # File edit info
    first_edit_position: Optional[int] = None
    edited_files: Set[str] = field(default_factory=set)

    # Ground truth files
    gt_files: Set[str] = field(default_factory=set)

    # Verification analysis
    has_verification: bool = False
    first_verification_success: Optional[bool] = None
    total_verifications: int = 0
    successful_verifications: int = 0

    # Reproduction analysis
    has_reproduction: bool = False
    reproduction_count: int = 0

    # File localization metrics
    hit: bool = False  # At least one correct file
    precision: float = 0.0  # Correct files / Agent files
    recall: float = 0.0  # Correct files / GT files


def is_test_execution(cmd: str) -> bool:
    """Check if command is a test execution"""
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


def classify_test_result(content: str) -> bool:
    """Returns True if success, False if failure"""
    content_lower = content.lower()

    # 明确的失败标志
    if 'FAILED' in content or ('failed' in content_lower and 'passed' not in content_lower):
        return False

    if ' error ' in content_lower or 'ERROR' in content:
        if not ('0 error' in content_lower or 'no error' in content_lower):
            return False

    # Python 异常
    exception_types = ['ModuleNotFoundError', 'ImportError', 'SyntaxError', 'FileNotFoundError',
                       'NameError', 'AttributeError', 'TypeError', 'ValueError', 'KeyError',
                       'IndexError', 'AssertionError', 'No module named']
    for exc in exception_types:
        if exc in content:
            return False

    if 'Traceback (most recent call last)' in content:
        return False

    # Exit code 检查
    if 'exit code 1' in content_lower or 'exit code: 1' in content_lower:
        return False

    # 明确的成功标志
    if 'passed' in content_lower and 'failed' not in content_lower:
        return True

    if content.strip().endswith('OK') or '\nOK' in content:
        return True

    # 如果没有明确标志，检查是否有任何错误迹象
    error_indicators = ['error', 'exception', 'fail', 'traceback', 'assert']
    for indicator in error_indicators:
        if indicator in content_lower:
            return False

    # 默认：如果没有明确的成功标志，视为失败（保守判断）
    return False


def normalize_path(path: str) -> str:
    """Normalize file path for comparison"""
    # Remove leading ./
    if path.startswith('./'):
        path = path[2:]
    # Remove leading /
    if path.startswith('/'):
        path = path.lstrip('/')
    # Remove testbed/ prefix (Docker container path)
    if path.startswith('testbed/'):
        path = path[8:]
    return path


def extract_files_from_patch(patch_content: str) -> Set[str]:
    """Extract file paths from a git diff patch"""
    files = set()
    for line in patch_content.split('\n'):
        # Match "diff --git a/path/to/file b/path/to/file"
        if line.startswith('diff --git'):
            match = re.search(r'diff --git a/(.+?) b/', line)
            if match:
                files.add(normalize_path(match.group(1)))
        # Match "+++ b/path/to/file"
        elif line.startswith('+++ b/'):
            path = line[6:].strip()
            if path and path != '/dev/null':
                files.add(normalize_path(path))
        # Match "--- a/path/to/file"
        elif line.startswith('--- a/'):
            path = line[6:].strip()
            if path and path != '/dev/null':
                files.add(normalize_path(path))
    return files


def load_ground_truth_files(dataset: str, instance_id: str) -> Set[str]:
    """Load ground truth files from SWE-bench dataset"""
    # Map dataset name to file name
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


def analyze_claude_code_trace(traces: List[dict], instance_id: str) -> InstanceAnalysis:
    """Analyze Claude Code format trace"""
    analysis = InstanceAnalysis(instance_id=instance_id, agent="claude_code", dataset="")

    first_edit_found = False
    pending_exec = None
    position = 0
    first_verification_recorded = False

    for entry in traces:
        entry_type = entry.get("type", "")
        position += 1

        if entry_type == "assistant":
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")

                    # Track file edits
                    if tool_name in ["Edit", "Write"]:
                        file_path = item.get("input", {}).get("file_path", "")
                        if file_path:
                            analysis.edited_files.add(normalize_path(file_path))
                        if not first_edit_found:
                            first_edit_found = True
                            analysis.first_edit_position = position

                    # Track test executions
                    if tool_name == "Bash":
                        cmd = item.get("input", {}).get("command", "")
                        if is_test_execution(cmd):
                            pending_exec = {
                                "position": position,
                                "is_after_edit": first_edit_found
                            }

        elif entry_type == "user" and pending_exec:
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    result = item.get("content", "")
                    if isinstance(result, str):
                        success = classify_test_result(result)

                        if pending_exec["is_after_edit"]:
                            # Verification
                            analysis.has_verification = True
                            analysis.total_verifications += 1
                            if success:
                                analysis.successful_verifications += 1

                            # Record first verification result
                            if not first_verification_recorded:
                                analysis.first_verification_success = success
                                first_verification_recorded = True
                        else:
                            # Reproduction
                            analysis.has_reproduction = True
                            analysis.reproduction_count += 1

            pending_exec = None

    return analysis


def analyze_codex_trace(traces: List[dict], instance_id: str) -> InstanceAnalysis:
    """Analyze Codex format trace"""
    analysis = InstanceAnalysis(instance_id=instance_id, agent="codex", dataset="")

    first_edit_found = False
    position = 0
    first_verification_recorded = False

    for entry in traces:
        entry_type = entry.get("type", "")
        position += 1

        if entry_type == "item.completed":
            item = entry.get("item", {})
            item_type = item.get("type", "")

            # Track file edits
            if item_type in ["file_edit", "file_change"]:
                # Try to get file path from changes
                changes = item.get("changes", [])
                for change in changes:
                    path = change.get("path", "")
                    if path:
                        analysis.edited_files.add(normalize_path(path))

                file_path = item.get("file_path", "")
                if file_path:
                    analysis.edited_files.add(normalize_path(file_path))

                if not first_edit_found:
                    first_edit_found = True
                    analysis.first_edit_position = position

            # Track test executions
            if item_type == "command_execution":
                cmd = item.get("command", "")
                if "bash -lc" in cmd:
                    match = re.search(r"'([^']+)'[^']*$", cmd)
                    if match:
                        cmd = match.group(1)

                if is_test_execution(cmd):
                    exit_code = item.get("exit_code")
                    result = item.get("aggregated_output", "")

                    if exit_code is not None:
                        success = (exit_code == 0)
                    else:
                        success = classify_test_result(result)

                    if first_edit_found:
                        # Verification
                        analysis.has_verification = True
                        analysis.total_verifications += 1
                        if success:
                            analysis.successful_verifications += 1

                        if not first_verification_recorded:
                            analysis.first_verification_success = success
                            first_verification_recorded = True
                    else:
                        # Reproduction
                        analysis.has_reproduction = True
                        analysis.reproduction_count += 1

    return analysis


def load_trace(dataset: str, agent: str, mode: str, instance: str) -> List[dict]:
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


def load_outcome_cases() -> Dict[str, List[Tuple[str, str]]]:
    """Load P→P and F→F cases"""
    # Load from existing analysis
    pp_file = PROJECT_ROOT / "analysis" / "pp_why_no_execution_needed.json"

    cases = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    # Load P→P cases
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

            cases[agent]["pp"].append((dataset, instance))

    # Find F→F cases (instances that are not P→P)
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


def calculate_localization_metrics(analysis: InstanceAnalysis):
    """Calculate file localization metrics"""
    if not analysis.gt_files or not analysis.edited_files:
        return

    intersection = analysis.gt_files & analysis.edited_files

    # Hit: at least one correct file
    analysis.hit = len(intersection) > 0

    # Precision: correct files / agent files
    if analysis.edited_files:
        analysis.precision = len(intersection) / len(analysis.edited_files)

    # Recall: correct files / GT files
    if analysis.gt_files:
        analysis.recall = len(intersection) / len(analysis.gt_files)


def generate_markdown_report(results: Dict) -> str:
    """Generate markdown report"""
    lines = []
    lines.append("# RQ3: Why Does Execution Have Limited Impact?")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("This analysis examines two aspects of execution:")
    lines.append("1. **Verification**: Is the first test after editing successful? (If yes → verification is redundant)")
    lines.append("2. **Reproduction**: Does running tests before editing help locate correct files?")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Verification Analysis
    lines.append("## 1. Verification Analysis")
    lines.append("")
    lines.append("**Question**: When agents edit files and then run tests, do they get it right the first time?")
    lines.append("")
    lines.append("### Summary Table")
    lines.append("")
    lines.append("| Agent | Outcome | Has Verification | First Verif Success | First Verif Fail |")
    lines.append("|-------|---------|-----------------|--------------------|--------------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        for outcome in ["pp", "ff"]:
            outcome_label = "P→P" if outcome == "pp" else "F→F"
            data = results[agent][outcome]

            has_verif = data["has_verification"]
            first_success = data["first_verification_success"]
            first_fail = data["first_verification_fail"]
            total = has_verif

            if total > 0:
                success_pct = f"{first_success/total*100:.1f}%"
                fail_pct = f"{first_fail/total*100:.1f}%"
            else:
                success_pct = "N/A"
                fail_pct = "N/A"

            lines.append(f"| {agent_label} | {outcome_label} | {has_verif} | {first_success} ({success_pct}) | {first_fail} ({fail_pct}) |")

    lines.append("")

    # Detailed verification analysis
    lines.append("### Interpretation")
    lines.append("")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp_data = results[agent]["pp"]
        ff_data = results[agent]["ff"]

        lines.append(f"**{agent_label}:**")

        if pp_data["has_verification"] > 0:
            pp_success_rate = pp_data["first_verification_success"] / pp_data["has_verification"] * 100
            lines.append(f"- P→P: {pp_success_rate:.1f}% first verification success → Verification is mostly redundant")

        if ff_data["has_verification"] > 0:
            ff_fail_rate = ff_data["first_verification_fail"] / ff_data["has_verification"] * 100
            lines.append(f"- F→F: {ff_fail_rate:.1f}% first verification fail → Iteration didn't help")

        lines.append("")

    lines.append("---")
    lines.append("")

    # Reproduction Analysis
    lines.append("## 2. Reproduction Analysis")
    lines.append("")
    lines.append("**Question**: Does running tests before editing help locate the correct files?")
    lines.append("")
    lines.append("### File Localization Accuracy")
    lines.append("")
    lines.append("| Agent | Outcome | Has Repro | Count | Avg Hit | Avg Recall | No Repro | Count | Avg Hit | Avg Recall |")
    lines.append("|-------|---------|-----------|-------|---------|------------|----------|-------|---------|------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        for outcome in ["pp", "ff"]:
            outcome_label = "P→P" if outcome == "pp" else "F→F"
            data = results[agent][outcome]

            # With reproduction
            with_repro = data["with_reproduction"]
            with_count = with_repro["count"]
            with_hit = f"{with_repro['avg_hit']*100:.1f}%" if with_count > 0 else "N/A"
            with_recall = f"{with_repro['avg_recall']*100:.1f}%" if with_count > 0 else "N/A"

            # Without reproduction
            no_repro = data["without_reproduction"]
            no_count = no_repro["count"]
            no_hit = f"{no_repro['avg_hit']*100:.1f}%" if no_count > 0 else "N/A"
            no_recall = f"{no_repro['avg_recall']*100:.1f}%" if no_count > 0 else "N/A"

            lines.append(f"| {agent_label} | {outcome_label} | Yes | {with_count} | {with_hit} | {with_recall} | No | {no_count} | {no_hit} | {no_recall} |")

    lines.append("")
    lines.append("### Interpretation")
    lines.append("")
    lines.append("- **Hit**: At least one edited file matches ground truth")
    lines.append("- **Recall**: Proportion of ground truth files that were edited")
    lines.append("")
    lines.append("If 'No Reproduction' cases have similar or better Hit/Recall than 'Has Reproduction' cases,")
    lines.append("it suggests that reproduction execution doesn't significantly help with file localization.")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Key Findings
    lines.append("## Key Findings")
    lines.append("")

    # Calculate overall stats
    total_pp_verif = sum(results[a]["pp"]["has_verification"] for a in ["claude_code", "codex"])
    total_pp_first_success = sum(results[a]["pp"]["first_verification_success"] for a in ["claude_code", "codex"])

    if total_pp_verif > 0:
        overall_pp_success = total_pp_first_success / total_pp_verif * 100
        lines.append(f"1. **Verification is largely redundant**: {overall_pp_success:.1f}% of P→P cases succeed on first verification")
        lines.append("   - Agents get it right the first time; verification just confirms")
        lines.append("")

    # Compare reproduction vs no reproduction
    lines.append("2. **Reproduction has limited impact on file localization**:")
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp_with = results[agent]["pp"]["with_reproduction"]
        pp_without = results[agent]["pp"]["without_reproduction"]

        if pp_with["count"] > 0 and pp_without["count"] > 0:
            lines.append(f"   - {agent_label} P→P: With repro Hit={pp_with['avg_hit']*100:.1f}%, Without repro Hit={pp_without['avg_hit']*100:.1f}%")

    lines.append("")
    lines.append("3. **Implications**:")
    lines.append("   - Problem descriptions are clear enough for static reasoning")
    lines.append("   - Execution overhead doesn't proportionally improve outcomes")
    lines.append("")

    return "\n".join(lines)


def main():
    """Main analysis function"""
    print("=" * 80)
    print("RQ3 Analysis v2: Verification and Reproduction")
    print("=" * 80)

    # Load outcome cases
    cases = load_outcome_cases()

    print("\nLoaded cases:")
    for agent in ["claude_code", "codex"]:
        print(f"  {agent}: {len(cases[agent]['pp'])} P→P, {len(cases[agent]['ff'])} F→F")

    # Analyze each group
    results = {}

    for agent in ["claude_code", "codex"]:
        results[agent] = {}

        for outcome in ["pp", "ff"]:
            print(f"\nAnalyzing {agent} {outcome.upper()}...")

            group_results = {
                "total": 0,
                "has_verification": 0,
                "first_verification_success": 0,
                "first_verification_fail": 0,
                "with_reproduction": {"count": 0, "total_hit": 0, "total_recall": 0, "avg_hit": 0, "avg_recall": 0},
                "without_reproduction": {"count": 0, "total_hit": 0, "total_recall": 0, "avg_hit": 0, "avg_recall": 0},
            }

            for dataset, instance in cases[agent][outcome]:
                # Load trace (Unrestricted mode)
                traces = load_trace(dataset, agent, "run_full", instance)
                if not traces:
                    continue

                # Analyze trace
                if agent == "claude_code":
                    analysis = analyze_claude_code_trace(traces, instance)
                else:
                    analysis = analyze_codex_trace(traces, instance)

                analysis.dataset = dataset
                analysis.outcome = outcome

                # Load ground truth files
                analysis.gt_files = load_ground_truth_files(dataset, instance)

                # Calculate localization metrics
                calculate_localization_metrics(analysis)

                # Aggregate results
                group_results["total"] += 1

                # Verification stats
                if analysis.has_verification:
                    group_results["has_verification"] += 1
                    if analysis.first_verification_success:
                        group_results["first_verification_success"] += 1
                    else:
                        group_results["first_verification_fail"] += 1

                # Reproduction stats
                if analysis.has_reproduction:
                    bucket = group_results["with_reproduction"]
                else:
                    bucket = group_results["without_reproduction"]

                bucket["count"] += 1
                bucket["total_hit"] += (1 if analysis.hit else 0)
                bucket["total_recall"] += analysis.recall

            # Calculate averages
            for key in ["with_reproduction", "without_reproduction"]:
                bucket = group_results[key]
                if bucket["count"] > 0:
                    bucket["avg_hit"] = bucket["total_hit"] / bucket["count"]
                    bucket["avg_recall"] = bucket["total_recall"] / bucket["count"]

            results[agent][outcome] = group_results

            print(f"  Total: {group_results['total']}")
            print(f"  Has verification: {group_results['has_verification']}")
            print(f"  First verif success: {group_results['first_verification_success']}")
            print(f"  With reproduction: {group_results['with_reproduction']['count']}")
            print(f"  Without reproduction: {group_results['without_reproduction']['count']}")

    # Generate markdown report
    md_content = generate_markdown_report(results)

    # Save markdown report
    md_file = ANALYSIS_DIR / "rq3_verification_reproduction_v2.md"
    with open(md_file, "w") as f:
        f.write(md_content)
    print(f"\nMarkdown report saved to: {md_file}")

    # Save JSON for reference
    json_file = ANALYSIS_DIR / "rq3_verification_reproduction_v2.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"JSON data saved to: {json_file}")


if __name__ == "__main__":
    main()
