#!/usr/bin/env python3
"""
RQ3 Comprehensive Analysis: Why Does Execution Have Limited Impact on Outcomes?

Collect all relevant statistics and output to a markdown file
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


# ============================================================================
# Helper Functions
# ============================================================================

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
    """Check if it's a test file"""
    path_lower = path.lower()
    if '/test_' in path_lower or '/tests/' in path_lower:
        return True
    if path_lower.endswith('_test.py'):
        return True
    if 'test' in path_lower.split('/')[-1]:
        return True
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return True
    if path_lower.endswith('/script.py') or path_lower == 'script.py':
        return True
    return False


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


def classify_test_result(content: str) -> str:
    """Classify test result: success, test_fail, env_error"""
    content_lower = content.lower()

    # Environment errors
    env_errors = ['No module named', 'ModuleNotFoundError', 'command not found',
                  'FileNotFoundError', 'No such file or directory',
                  'Permission denied', 'UnicodeDecodeError', 'encoding']
    for err in env_errors:
        if err in content or err.lower() in content_lower:
            return "env_error"

    # Clear test failure
    if 'FAILED' in content:
        return "test_fail"
    if 'AssertionError' in content:
        return "test_fail"
    if 'Traceback (most recent call last)' in content:
        return "test_fail"

    # Success
    if 'passed' in content_lower and 'failed' not in content_lower:
        return "success"
    if content.strip().endswith('OK') or '\nOK' in content:
        return "success"

    # Default to failure
    return "test_fail"


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


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class InstanceAnalysis:
    """Analysis result for a single instance"""
    instance_id: str
    dataset: str
    agent: str
    mode: str

    # Edit information
    first_edit_file: str = ""
    first_edit_is_test: bool = False
    all_edited_files: Set[str] = field(default_factory=set)

    # Ground Truth
    gt_files: Set[str] = field(default_factory=set)

    # Localization metrics
    first_edit_hit: bool = False  # First edit hits GT
    any_edit_hit: bool = False    # Any edit hits GT
    recall: float = 0.0           # GT file recall rate

    # Verification analysis
    has_verification: bool = False
    first_verif_result: str = ""  # success, test_fail, env_error
    total_verifications: int = 0
    any_verif_success: bool = False

    # Reproduction analysis
    has_reproduction: bool = False
    reproduction_count: int = 0

    # Conversation statistics
    total_turns: int = 0
    total_edits: int = 0
    total_test_runs: int = 0


# ============================================================================
# Trace Analyzers
# ============================================================================

def analyze_claude_trace(traces: list, instance_id: str, dataset: str, mode: str) -> InstanceAnalysis:
    """Analyze Claude Code trace"""
    analysis = InstanceAnalysis(
        instance_id=instance_id,
        dataset=dataset,
        agent="claude_code",
        mode=mode
    )

    first_edit_found = False
    first_verif_recorded = False
    pending_exec = None

    for entry in traces:
        entry_type = entry.get("type", "")
        analysis.total_turns += 1

        if entry_type == "assistant":
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")

                    # File edit
                    if tool_name in ["Edit", "Write"]:
                        file_path = item.get("input", {}).get("file_path", "")
                        if file_path:
                            norm_path = normalize_path(file_path)
                            analysis.all_edited_files.add(norm_path)
                            analysis.total_edits += 1

                            if not first_edit_found:
                                first_edit_found = True
                                analysis.first_edit_file = norm_path
                                analysis.first_edit_is_test = is_test_file(norm_path)

                    # Test execution
                    if tool_name == "Bash":
                        cmd = item.get("input", {}).get("command", "")
                        if is_test_execution(cmd):
                            pending_exec = {"is_after_edit": first_edit_found}
                            analysis.total_test_runs += 1

        elif entry_type == "user" and pending_exec:
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    result = item.get("content", "")
                    if isinstance(result, str):
                        result_type = classify_test_result(result)

                        if pending_exec["is_after_edit"]:
                            # Verification
                            analysis.has_verification = True
                            analysis.total_verifications += 1

                            if result_type == "success":
                                analysis.any_verif_success = True

                            if not first_verif_recorded:
                                analysis.first_verif_result = result_type
                                first_verif_recorded = True
                        else:
                            # Reproduction
                            analysis.has_reproduction = True
                            analysis.reproduction_count += 1

            pending_exec = None

    return analysis


def analyze_codex_trace(traces: list, instance_id: str, dataset: str, mode: str) -> InstanceAnalysis:
    """Analyze Codex trace"""
    analysis = InstanceAnalysis(
        instance_id=instance_id,
        dataset=dataset,
        agent="codex",
        mode=mode
    )

    first_edit_found = False
    first_verif_recorded = False

    for entry in traces:
        entry_type = entry.get("type", "")
        analysis.total_turns += 1

        if entry_type == "item.completed":
            item = entry.get("item", {})
            item_type = item.get("type", "")

            # 文件编辑
            if item_type in ["file_edit", "file_change"]:
                # Get file path from changes or file_path
                changes = item.get("changes", [])
                for change in changes:
                    path = change.get("path", "")
                    if path:
                        norm_path = normalize_path(path)
                        analysis.all_edited_files.add(norm_path)
                        analysis.total_edits += 1

                        if not first_edit_found:
                            first_edit_found = True
                            analysis.first_edit_file = norm_path
                            analysis.first_edit_is_test = is_test_file(norm_path)

                file_path = item.get("file_path", "")
                if file_path:
                    norm_path = normalize_path(file_path)
                    analysis.all_edited_files.add(norm_path)
                    if not first_edit_found:
                        first_edit_found = True
                        analysis.first_edit_file = norm_path
                        analysis.first_edit_is_test = is_test_file(norm_path)

            # Test execution
            if item_type == "command_execution":
                cmd = item.get("command", "")
                if "bash -lc" in cmd:
                    match = re.search(r"'([^']+)'[^']*$", cmd)
                    if match:
                        cmd = match.group(1)

                if is_test_execution(cmd):
                    analysis.total_test_runs += 1
                    result = item.get("aggregated_output", "")
                    exit_code = item.get("exit_code")

                    if exit_code is not None:
                        result_type = "success" if exit_code == 0 else "test_fail"
                    else:
                        result_type = classify_test_result(result)

                    if first_edit_found:
                        # Verification
                        analysis.has_verification = True
                        analysis.total_verifications += 1

                        if result_type == "success":
                            analysis.any_verif_success = True

                        if not first_verif_recorded:
                            analysis.first_verif_result = result_type
                            first_verif_recorded = True
                    else:
                        # Reproduction
                        analysis.has_reproduction = True
                        analysis.reproduction_count += 1

    return analysis


def compute_localization_metrics(analysis: InstanceAnalysis):
    """Compute file localization metrics"""
    if not analysis.gt_files:
        return

    # First edit hit
    if analysis.first_edit_file and analysis.first_edit_file in analysis.gt_files:
        analysis.first_edit_hit = True

    # Any edit hit
    if analysis.all_edited_files & analysis.gt_files:
        analysis.any_edit_hit = True

    # Recall rate
    if analysis.gt_files:
        intersection = analysis.all_edited_files & analysis.gt_files
        analysis.recall = len(intersection) / len(analysis.gt_files)


# ============================================================================
# Data Loading
# ============================================================================

def load_outcome_cases() -> Dict:
    """Load P→P and F→F cases"""
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

            dataset = "swebenchlite" if "Lite" in group else "swebenchverified"
            cases[agent]["pp"].append((dataset, instance))

    # Find F→F cases
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


# ============================================================================
# Main Analysis Logic
# ============================================================================

def run_analysis() -> Dict:
    """Run all analyses"""
    cases = load_outcome_cases()

    results = {}

    for agent in ["claude_code", "codex"]:
        results[agent] = {}

        for outcome in ["pp", "ff"]:
            results[agent][outcome] = {}

            for mode in ["run_full", "run_free"]:
                mode_label = "unrestricted" if mode == "run_full" else "prohibited"

                analyses = []

                for dataset, instance in cases[agent][outcome]:
                    traces = load_trace(dataset, agent, mode, instance)
                    if not traces:
                        continue

                    # Analyze trace
                    if agent == "claude_code":
                        analysis = analyze_claude_trace(traces, instance, dataset, mode)
                    else:
                        analysis = analyze_codex_trace(traces, instance, dataset, mode)

                    # Load GT
                    analysis.gt_files = load_ground_truth_files(dataset, instance)

                    # Compute metrics
                    compute_localization_metrics(analysis)

                    analyses.append(analysis)

                # Aggregate statistics
                results[agent][outcome][mode_label] = aggregate_stats(analyses)

    return results


def aggregate_stats(analyses: List[InstanceAnalysis]) -> Dict:
    """Aggregate statistics"""
    if not analyses:
        return {"count": 0}

    stats = {
        "count": len(analyses),

        # First edit analysis
        "first_edit_is_test": sum(1 for a in analyses if a.first_edit_is_test),
        "first_edit_hit": sum(1 for a in analyses if a.first_edit_hit),

        # Final edit analysis
        "any_edit_hit": sum(1 for a in analyses if a.any_edit_hit),
        "avg_recall": sum(a.recall for a in analyses) / len(analyses),

        # Verification analysis
        "has_verification": sum(1 for a in analyses if a.has_verification),
        "first_verif_success": sum(1 for a in analyses if a.first_verif_result == "success"),
        "first_verif_test_fail": sum(1 for a in analyses if a.first_verif_result == "test_fail"),
        "first_verif_env_error": sum(1 for a in analyses if a.first_verif_result == "env_error"),
        "any_verif_success": sum(1 for a in analyses if a.any_verif_success),

        # Reproduction analysis
        "has_reproduction": sum(1 for a in analyses if a.has_reproduction),

        # Behavior statistics
        "avg_turns": sum(a.total_turns for a in analyses) / len(analyses),
        "avg_edits": sum(a.total_edits for a in analyses) / len(analyses),
        "avg_test_runs": sum(a.total_test_runs for a in analyses) / len(analyses),
        "total_verifications": sum(a.total_verifications for a in analyses),
    }

    return stats


# ============================================================================
# Markdown Report Generation
# ============================================================================

def generate_markdown(results: Dict) -> str:
    """Generate markdown report"""
    lines = []

    # Title
    lines.append("# RQ3 Comprehensive Analysis: Why Does Execution Have Limited Impact on Outcomes?")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    # Table of Contents
    lines.append("## Table of Contents")
    lines.append("")
    lines.append("1. [Data Overview](#1-data-overview)")
    lines.append("2. [RQ3.1 Verification Analysis](#2-rq31-verification-analysis)")
    lines.append("3. [RQ3.2 File Localization Analysis](#3-rq32-file-localization-analysis)")
    lines.append("4. [Agent Behavior Comparison](#4-agent-behavior-comparison)")
    lines.append("5. [Key Findings and Conclusions](#5-key-findings-and-conclusions)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. Data Overview
    lines.append("## 1. Data Overview")
    lines.append("")
    lines.append("### Case Distribution")
    lines.append("")
    lines.append("| Agent | P→P (Both Succeed) | F→F (Both Fail) |")
    lines.append("|-------|-----------------|-----------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp_count = results[agent]["pp"]["unrestricted"]["count"]
        ff_count = results[agent]["ff"]["unrestricted"]["count"]
        lines.append(f"| {agent_label} | {pp_count} | {ff_count} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. Verification Analysis
    lines.append("## 2. RQ3.1 Verification Analysis")
    lines.append("")
    lines.append("**Question**: What are the results of verification execution after the first edit? Can it demonstrate that verification is redundant?")
    lines.append("")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        lines.append(f"### {agent_label}")
        lines.append("")

        # P→P Analysis
        lines.append("#### P→P Cases (Both Modes Succeed)")
        lines.append("")

        pp_unres = results[agent]["pp"]["unrestricted"]
        pp_proh = results[agent]["pp"]["prohibited"]

        lines.append("| Metric | Unrestricted | Prohibited |")
        lines.append("|------|-------------|------------|")

        if pp_unres["count"] > 0:
            # Instances with verification
            has_verif_unres = pp_unres["has_verification"]
            has_verif_proh = pp_proh["has_verification"]
            lines.append(f"| Instances with verification | {has_verif_unres} ({has_verif_unres/pp_unres['count']*100:.1f}%) | {has_verif_proh} ({has_verif_proh/pp_proh['count']*100:.1f}%) |")

            # First verification result distribution
            if has_verif_unres > 0:
                success_pct = pp_unres["first_verif_success"] / has_verif_unres * 100
                fail_pct = pp_unres["first_verif_test_fail"] / has_verif_unres * 100
                env_pct = pp_unres["first_verif_env_error"] / has_verif_unres * 100
            else:
                success_pct = fail_pct = env_pct = 0

            if has_verif_proh > 0:
                success_pct_p = pp_proh["first_verif_success"] / has_verif_proh * 100
                fail_pct_p = pp_proh["first_verif_test_fail"] / has_verif_proh * 100
                env_pct_p = pp_proh["first_verif_env_error"] / has_verif_proh * 100
            else:
                success_pct_p = fail_pct_p = env_pct_p = 0

            lines.append(f"| First verification success | {pp_unres['first_verif_success']} ({success_pct:.1f}%) | {pp_proh['first_verif_success']} ({success_pct_p:.1f}%) |")
            lines.append(f"| First verification fail (test) | {pp_unres['first_verif_test_fail']} ({fail_pct:.1f}%) | {pp_proh['first_verif_test_fail']} ({fail_pct_p:.1f}%) |")
            lines.append(f"| First verification fail (env) | {pp_unres['first_verif_env_error']} ({env_pct:.1f}%) | {pp_proh['first_verif_env_error']} ({env_pct_p:.1f}%) |")

        lines.append("")

        # F→F Analysis
        lines.append("#### F→F Cases (Both Modes Fail)")
        lines.append("")

        ff_unres = results[agent]["ff"]["unrestricted"]
        ff_proh = results[agent]["ff"]["prohibited"]

        lines.append("| Metric | Unrestricted | Prohibited |")
        lines.append("|------|-------------|------------|")

        if ff_unres["count"] > 0:
            has_verif_unres = ff_unres["has_verification"]
            has_verif_proh = ff_proh["has_verification"]
            lines.append(f"| Instances with verification | {has_verif_unres} ({has_verif_unres/ff_unres['count']*100:.1f}%) | {has_verif_proh} ({has_verif_proh/ff_proh['count']*100:.1f}%) |")

            if has_verif_unres > 0:
                any_success = ff_unres["any_verif_success"]
                lines.append(f"| Any verification succeeded | {any_success} ({any_success/has_verif_unres*100:.1f}%) | N/A |")

        lines.append("")

        # Interpretation
        lines.append("**Interpretation**:")
        lines.append("")
        if pp_unres["count"] > 0 and pp_unres["has_verification"] > 0:
            success_rate = pp_unres["first_verif_success"] / pp_unres["has_verification"] * 100
            if success_rate < 30:
                lines.append(f"- In P→P cases, first verification success rate is only {success_rate:.1f}%, indicating Agent needs multiple iterations to pass verification")
            else:
                lines.append(f"- In P→P cases, first verification success rate is {success_rate:.1f}%")

            env_rate = pp_unres["first_verif_env_error"] / pp_unres["has_verification"] * 100
            if env_rate > 20:
                lines.append(f"- {env_rate:.1f}% of first verification failures are environment errors (pytest not installed, etc.), not code issues")

        if ff_unres["count"] > 0 and ff_unres["has_verification"] > 0:
            any_success_rate = ff_unres["any_verif_success"] / ff_unres["has_verification"] * 100
            if any_success_rate > 50:
                lines.append(f"- In F→F cases, {any_success_rate:.1f}% had successful verification at some point, but still failed ultimately → Agent's tests are inconsistent with evaluation tests")

        lines.append("")

    lines.append("---")
    lines.append("")

    # 3. File Localization Analysis
    lines.append("## 3. RQ3.2 File Localization Analysis")
    lines.append("")
    lines.append("**Question**: Can Agent accurately locate the files that need modification? Does execution help with localization?")
    lines.append("")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        lines.append(f"### {agent_label}")
        lines.append("")

        # P→P Analysis
        lines.append("#### P→P Cases")
        lines.append("")

        pp_unres = results[agent]["pp"]["unrestricted"]
        pp_proh = results[agent]["pp"]["prohibited"]

        lines.append("| Metric | Unrestricted | Prohibited |")
        lines.append("|------|-------------|------------|")

        if pp_unres["count"] > 0:
            # First edit is test file
            test_pct_u = pp_unres["first_edit_is_test"] / pp_unres["count"] * 100
            test_pct_p = pp_proh["first_edit_is_test"] / pp_proh["count"] * 100
            lines.append(f"| First edit is test file | {pp_unres['first_edit_is_test']} ({test_pct_u:.1f}%) | {pp_proh['first_edit_is_test']} ({test_pct_p:.1f}%) |")

            # First edit hit
            hit_pct_u = pp_unres["first_edit_hit"] / pp_unres["count"] * 100
            hit_pct_p = pp_proh["first_edit_hit"] / pp_proh["count"] * 100
            lines.append(f"| First edit hits GT | {pp_unres['first_edit_hit']} ({hit_pct_u:.1f}%) | {pp_proh['first_edit_hit']} ({hit_pct_p:.1f}%) |")

            # Final edit hit
            any_hit_u = pp_unres["any_edit_hit"] / pp_unres["count"] * 100
            any_hit_p = pp_proh["any_edit_hit"] / pp_proh["count"] * 100
            lines.append(f"| Final edit hits GT | {pp_unres['any_edit_hit']} ({any_hit_u:.1f}%) | {pp_proh['any_edit_hit']} ({any_hit_p:.1f}%) |")

            # Average recall
            lines.append(f"| Average recall | {pp_unres['avg_recall']*100:.1f}% | {pp_proh['avg_recall']*100:.1f}% |")

            # Reproduction usage
            repro_u = pp_unres["has_reproduction"]
            repro_p = pp_proh["has_reproduction"]
            lines.append(f"| Uses Reproduction | {repro_u} ({repro_u/pp_unres['count']*100:.1f}%) | {repro_p} ({repro_p/pp_proh['count']*100:.1f}%) |")

        lines.append("")

        # Interpretation
        lines.append("**Interpretation**:")
        lines.append("")
        if pp_unres["count"] > 0:
            test_diff = test_pct_u - test_pct_p
            if test_diff > 20:
                lines.append(f"- Unrestricted mode has {test_pct_u:.1f}% first edits on test files (vs Prohibited {test_pct_p:.1f}%)")
                lines.append("  - This explains the difference in first edit hit rate: Unrestricted writes tests first to reproduce the issue")

            if any_hit_u > 95 and any_hit_p > 95:
                lines.append(f"- Final edit hit rates are both high ({any_hit_u:.1f}% vs {any_hit_p:.1f}%), indicating comparable localization ability")

            if repro_u / pp_unres["count"] < 0.2:
                lines.append(f"- Only {repro_u/pp_unres['count']*100:.1f}% use Reproduction, suggesting problem descriptions are clear enough")

        lines.append("")

    lines.append("---")
    lines.append("")

    # 4. Agent Behavior Comparison
    lines.append("## 4. Agent Behavior Comparison")
    lines.append("")
    lines.append("### P→P Case Behavior Statistics")
    lines.append("")
    lines.append("| Agent | Mode | Avg Conversation Turns | Avg Edit Count | Avg Test Count |")
    lines.append("|-------|------|------------|------------|------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        for mode_key, mode_label in [("unrestricted", "Unrestricted"), ("prohibited", "Prohibited")]:
            s = results[agent]["pp"][mode_key]
            if s["count"] > 0:
                lines.append(f"| {agent_label} | {mode_label} | {s['avg_turns']:.1f} | {s['avg_edits']:.1f} | {s['avg_test_runs']:.1f} |")

    lines.append("")

    # Comparison analysis
    lines.append("### Behavior Difference Analysis")
    lines.append("")

    cc_unres = results["claude_code"]["pp"]["unrestricted"]
    cc_proh = results["claude_code"]["pp"]["prohibited"]

    if cc_unres["count"] > 0 and cc_proh["count"] > 0:
        lines.append("**Claude Code**:")
        lines.append(f"- Unrestricted averages {cc_unres['avg_test_runs']:.1f} test executions vs Prohibited {cc_proh['avg_test_runs']:.1f}")
        lines.append(f"- Unrestricted averages {cc_unres['avg_edits']:.1f} edits vs Prohibited {cc_proh['avg_edits']:.1f}")

        if cc_unres['avg_test_runs'] > cc_proh['avg_test_runs'] * 3:
            lines.append(f"- **More iterations did not lead to better results**: Both succeed, but Unrestricted consumes more resources")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 5. Key Findings and Conclusions
    lines.append("## 5. Key Findings and Conclusions")
    lines.append("")
    lines.append("### Key Findings")
    lines.append("")
    lines.append("| # | Finding | Evidence |")
    lines.append("|---|------|------|")

    findings = []

    finding_num = 1

    # Finding: Limited value of verification feedback (both agents)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp = results[agent]["pp"]["unrestricted"]
        if pp["count"] > 0 and pp["has_verification"] > 0:
            first_success = pp["first_verif_success"] / pp["has_verification"] * 100
            findings.append(f"| {finding_num} | **{agent_label}: Limited value of verification feedback** | P→P first verification success rate only {first_success:.1f}% |")
            finding_num += 1

    # Finding: Environment errors interfere (Claude Code)
    cc_pp = results["claude_code"]["pp"]["unrestricted"]
    if cc_pp["count"] > 0 and cc_pp["has_verification"] > 0:
        env_rate = cc_pp["first_verif_env_error"] / cc_pp["has_verification"] * 100
        if env_rate > 10:
            findings.append(f"| {finding_num} | **Claude Code: Environment errors interfere with verification** | {env_rate:.1f}% of first verifications are environment errors |")
            finding_num += 1

    # Finding: Test inconsistency (both agents)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        ff = results[agent]["ff"]["unrestricted"]
        if ff["count"] > 0 and ff["has_verification"] > 0:
            any_success = ff["any_verif_success"] / ff["has_verification"] * 100
            if any_success > 50:
                findings.append(f"| {finding_num} | **{agent_label}: Verification inconsistent with evaluation** | In F→F, {any_success:.1f}% had successful verification but ultimately failed |")
                finding_num += 1

    # Finding: Localization doesn't need execution (both agents)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp = results[agent]["pp"]["unrestricted"]
        if pp["count"] > 0:
            repro_rate = pp["has_reproduction"] / pp["count"] * 100
            any_hit = pp["any_edit_hit"] / pp["count"] * 100
            if repro_rate < 30 and any_hit > 90:
                findings.append(f"| {finding_num} | **{agent_label}: Localization doesn't need execution** | Only {repro_rate:.1f}% used Reproduction, but {any_hit:.1f}% hit GT |")
                finding_num += 1

    # Finding: More iterations ≠ better results (both agents)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        unres = results[agent]["pp"]["unrestricted"]
        proh = results[agent]["pp"]["prohibited"]
        if unres["count"] > 0 and proh["count"] > 0:
            if unres["avg_test_runs"] > proh["avg_test_runs"] + 1:
                findings.append(f"| {finding_num} | **{agent_label}: More iterations ≠ better** | Unrestricted {unres['avg_test_runs']:.1f} tests vs Prohibited {proh['avg_test_runs']:.1f} |")
                finding_num += 1

    for f in findings:
        lines.append(f)

    lines.append("")
    lines.append("### Conclusions")
    lines.append("")
    lines.append("**Why does execution have limited impact on outcomes?**")
    lines.append("")
    lines.append("1. **Problem descriptions are clear enough**: Agent can locate files through static analysis without dynamic execution for reproduction")
    lines.append("2. **Verification feedback is noisy**: Environment errors and test inconsistencies reduce the value of verification")
    lines.append("3. **Iteration may lead to over-fixing**: More edits may introduce unnecessary changes")
    lines.append("4. **Core capability is understanding**: Regardless of execution, Agent's code comprehension ability is the key to success")
    lines.append("")
    lines.append("> **Execution feedback is a double-edged sword**: It can help discover problems, but may also mislead Agent into making unnecessary modifications.")
    lines.append("> When problem descriptions are clear enough, \"getting it right the first time\" is more effective than \"trial-and-error iteration\".")
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# Main Function
# ============================================================================

def main():
    print("=" * 80)
    print("RQ3 Comprehensive Analysis")
    print("=" * 80)

    print("\nAnalyzing...")
    results = run_analysis()

    print("\nGenerating report...")
    md_content = generate_markdown(results)

    # Save markdown
    md_file = ANALYSIS_DIR / "rq3_comprehensive_report.md"
    with open(md_file, "w") as f:
        f.write(md_content)
    print(f"\nReport saved: {md_file}")

    # Save JSON
    json_file = ANALYSIS_DIR / "rq3_comprehensive_data.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Data saved: {json_file}")

    print("\nDone!")


if __name__ == "__main__":
    main()
