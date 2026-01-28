#!/usr/bin/env python3
"""
Parse and analyze SWE-bench experiment traces

This script parses traces from different agent frameworks and extracts:
1. Execution frequency (test runs vs exploration commands)
2. Token consumption
3. Action patterns
"""

import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from collections import defaultdict
import statistics
import csv
import yaml


@dataclass
class TraceStats:
    """Statistics for a single trace/instance"""
    instance_id: str
    submission: str  # agent+model combination
    agent_type: str  # extracted agent name
    model: str  # extracted model name

    # Execution counts
    total_actions: int = 0
    bash_commands: int = 0
    test_executions: int = 0
    file_reads: int = 0
    file_edits: int = 0
    searches: int = 0

    # Token usage (if available)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Other metrics
    num_turns: int = 0
    resolved: bool = False

    # Raw data for debugging
    action_types: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)


def extract_agent_model(submission_name: str) -> tuple:
    """Extract agent type and model from submission name"""
    # Format: YYYYMMDD_agent_model or YYYYMMDD_agent-version_model
    # May also have prefix like lite_ or verified_

    # Remove split prefix if present
    name = submission_name
    for prefix in ["lite_", "verified_"]:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    parts = name.split("_", 1)
    if len(parts) < 2:
        return "unknown", "unknown"

    rest = parts[1]

    # Known agent patterns
    agent_patterns = [
        (r"^sweagent[_-]?", "sweagent"),
        (r"^moatless[_-]?", "moatless"),
        (r"^agentless[_-]?[\d.]*[_-]?", "agentless"),
        (r"^OpenHands[_-]?", "openhands"),
        (r"^autocoderover[_-]?", "autocoderover"),
        (r"^aider", "aider"),
        (r"^MASAI", "masai"),
        (r"^amazon-q", "amazon-q"),
        (r"^CodeR", "coder"),
        (r"^SuperCoder", "supercoder"),
        (r"^IBM", "ibm"),
        (r"^rag[_-]", "rag"),
    ]

    agent_type = "other"
    model = rest

    for pattern, agent_name in agent_patterns:
        match = re.match(pattern, rest, re.IGNORECASE)
        if match:
            agent_type = agent_name
            model = rest[match.end():].strip("_-")
            break

    # Clean up model name
    model = model.replace("_", "-") if model else "unknown"

    return agent_type, model


def is_test_command(command: str) -> bool:
    """Determine if a command is a test/script execution

    Counts as test execution:
    - pytest / py.test / unittest
    - python xxx.py (any Python script, including reproduce scripts)
    - runtests.py / manage.py test
    - tox / nose

    Does NOT count:
    - ls, cat, grep, find, etc. (viewing commands)
    - search_dir, find_file, etc. (SWE-agent search commands)
    """
    if not command:
        return False

    cmd_lower = command.lower().strip()

    # Test framework patterns
    test_patterns = [
        r'\bpytest\b',
        r'\bpy\.test\b',
        r'python[3]?\s+-m\s+pytest',
        r'python[3]?\s+-m\s+unittest',
        r'runtests\.py\b',
        r'manage\.py\s+test',
        r'\btox\b',
        r'\bnose\b',
        r'\bnosetests\b',
    ]

    for pattern in test_patterns:
        if re.search(pattern, cmd_lower):
            return True

    # Python script execution (python xxx.py) - counts as test
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        # Exclude python -c (inline code)
        if not re.search(r'python[3]?\s+-c\s', cmd_lower):
            return True

    return False


def is_bash_command(action: str) -> bool:
    """Determine if an action is a bash/shell command execution

    Counts as bash command:
    - python xxx.py
    - ls, cat, grep, find, head, tail, etc.
    - search_dir, find_file (SWE-agent commands)
    - Any shell-like command

    Does NOT count:
    - edit, create (file modifications)
    - open, scroll (file viewing in editor)
    - submit (end command)
    """
    if not action:
        return False

    action_lower = action.lower().strip()

    # Shell command patterns
    bash_patterns = [
        r'^python[3]?\s+',
        r'^ls\b',
        r'^cat\b',
        r'^grep\b',
        r'^find\b',
        r'^head\b',
        r'^tail\b',
        r'^pwd\b',
        r'^cd\b',
        r'^echo\b',
        r'^pip[3]?\b',
        r'^search_dir\b',
        r'^search_file\b',
        r'^find_file\b',
        r'^git\b',
        r'^mkdir\b',
        r'^rm\b',
        r'^mv\b',
        r'^cp\b',
        r'^curl\b',
        r'^wget\b',
    ]

    for pattern in bash_patterns:
        if re.search(pattern, action_lower):
            return True

    return False


def parse_sweagent_trace(trace_path: Path) -> Optional[TraceStats]:
    """Parse SWE-agent format trace (JSON or YAML)

    SWE-agent format:
    {
        "environment": "...",
        "trajectory": [
            {"action": "...", "observation": "...", "thought": "...", "state": "..."},
            ...
        ],
        "info": {"exit_status": "submitted", ...}
    }
    """
    instance_id = trace_path.stem.replace(".traj", "").replace(".json", "").replace(".yaml", "")

    # Determine submission from path
    submission = trace_path.parent.parent.name
    agent_type, model = extract_agent_model(submission)

    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model
    )

    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try JSON first
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            # Try YAML
            try:
                data = yaml.safe_load(content)
            except:
                return None

        if not data:
            return None

        # SWE-agent format: {"trajectory": [...], "info": {...}}
        trajectory = data.get("trajectory", data.get("history", []))

        for item in trajectory:
            if not isinstance(item, dict):
                continue

            stats.num_turns += 1
            action = item.get("action", "")

            if not isinstance(action, str):
                continue

            # SWE-agent uses specific action commands
            action_lower = action.lower().strip()

            # Count ALL bash/shell commands (including search, grep, ls, python, etc.)
            if is_bash_command(action):
                stats.bash_commands += 1
                stats.commands.append(action[:200])
                if is_test_command(action):
                    stats.test_executions += 1

            # Also count SWE-agent specific commands as bash
            elif action_lower.startswith("search_") or action_lower.startswith("find_"):
                stats.bash_commands += 1
                stats.searches += 1
                stats.commands.append(action[:200])

            # edit command
            elif action_lower.startswith("edit "):
                stats.file_edits += 1
            # create command
            elif action_lower.startswith("create "):
                stats.file_edits += 1
            # open command
            elif action_lower.startswith("open "):
                stats.file_reads += 1
            # scroll commands (file reading)
            elif action_lower.startswith("scroll_") or action_lower.startswith("goto "):
                stats.file_reads += 1
            # submit command
            elif action_lower.startswith("submit"):
                pass  # end of trajectory

        stats.total_actions = len(trajectory)

        # Check if resolved - look for exit_status in info
        info = data.get("info", {})
        if isinstance(info, dict):
            exit_status = info.get("exit_status", "")
            stats.resolved = "submitted" in str(exit_status).lower() or info.get("resolved", False)

    except Exception as e:
        print(f"Error parsing {trace_path}: {e}")
        return None

    return stats


def parse_openhands_trace(trace_path: Path) -> Optional[TraceStats]:
    """Parse OpenHands format trace (JSON array of messages)

    OpenHands format:
    [
        {"role": "system", "content": [...]},
        {"role": "user", "content": [...]},
        {"role": "assistant", "content": [...], "tool_calls": [{"function": {"name": "execute_bash", "arguments": "{\"command\": \"...\"}"}}]},
        {"role": "tool", "content": "...", "name": "execute_bash"},
        ...
    ]
    """
    instance_id = trace_path.stem.replace(".json", "")

    submission = trace_path.parent.parent.name
    agent_type, model = extract_agent_model(submission)

    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model
    )

    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            return None

        for item in data:
            if not isinstance(item, dict):
                continue

            role = item.get("role", "")
            stats.num_turns += 1

            # Check tool calls in assistant messages
            if role == "assistant":
                tool_calls = item.get("tool_calls", [])
                if not isinstance(tool_calls, list):
                    continue

                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    func = tc.get("function", {})
                    if not isinstance(func, dict):
                        continue

                    func_name = func.get("name", "")
                    args_str = func.get("arguments", "")

                    # Parse arguments JSON string
                    cmd = ""
                    if isinstance(args_str, str) and args_str:
                        try:
                            args_dict = json.loads(args_str)
                            cmd = args_dict.get("command", "")
                        except json.JSONDecodeError:
                            cmd = args_str

                    if func_name == "execute_bash":
                        stats.bash_commands += 1
                        if cmd:
                            stats.commands.append(cmd[:200])
                            if is_test_command(cmd):
                                stats.test_executions += 1

                    elif func_name == "str_replace_editor":
                        stats.file_edits += 1

        stats.total_actions = stats.num_turns
        # Assume resolved if we have bash commands
        stats.resolved = stats.bash_commands > 0

    except Exception as e:
        print(f"Error parsing OpenHands {trace_path.name}: {e}")
        return None

    return stats


def parse_moatless_trace(trace_path: Path) -> Optional[TraceStats]:
    """Parse Moatless format trace (JSON with transitions)

    Moatless format:
    {
        "name": "AgenticLoop",
        "initial_message": "...",
        "transitions": [
            {
                "name": "SearchCode",
                "state": {...},
                "actions": [{"action": {...}, "output": {...}, "completion_cost": 0.005}]
            },
            ...
        ]
    }

    Note: Moatless is a PURE REASONING agent - it doesn't execute bash commands.
    It uses high-level API actions like SearchCode, IdentifyCode, PlanToCode, EditCode.
    We count these high-level actions as "total_actions" but bash_commands stays 0.
    """
    instance_id = trace_path.stem.replace(".json", "")

    submission = trace_path.parent.parent.name
    agent_type, model = extract_agent_model(submission)

    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model
    )

    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return None

        # Check for Moatless format
        transitions = data.get("transitions", [])
        if not transitions:
            return None

        for transition in transitions:
            if not isinstance(transition, dict):
                continue

            transition_name = transition.get("name", "")
            stats.num_turns += 1
            stats.action_types.append(transition_name)

            # Count action types (Moatless uses high-level API, not bash)
            if transition_name in ["SearchCode", "FindCode"]:
                stats.searches += 1
            elif transition_name in ["IdentifyCode", "ViewCode"]:
                stats.file_reads += 1
            elif transition_name in ["PlanToCode", "EditCode", "ApplyChange"]:
                stats.file_edits += 1
            elif transition_name in ["RunTests", "Verify"]:
                # Moatless doesn't actually run tests via bash - it's API-based
                stats.test_executions += 1

            # Count actions within transitions
            actions = transition.get("actions", [])
            for action in actions:
                if isinstance(action, dict):
                    stats.total_actions += 1

        if stats.total_actions == 0:
            stats.total_actions = len(transitions)

        # Check if resolved - look for Finished state or info.submission
        if transitions:
            last_transition = transitions[-1]
            if isinstance(last_transition, dict):
                name = last_transition.get("name", "")
                stats.resolved = name in ["Finished", "Rejected", "PlanToCode"]

        # Also check info for submission (indicates successful completion)
        info = data.get("info", {})
        if isinstance(info, dict) and info.get("submission"):
            stats.resolved = True

    except Exception as e:
        print(f"Error parsing Moatless {trace_path.name}: {e}")
        return None

    return stats


def parse_generic_trace(trace_path: Path) -> Optional[TraceStats]:
    """Parse generic trace format (try multiple parsers)"""

    # Detect format by reading first bytes
    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
    except:
        return None

    # If starts with '[', it's likely OpenHands format (array)
    if first_char == '[':
        stats = parse_openhands_trace(trace_path)
        if stats and stats.total_actions > 0:
            return stats

    # Try to detect format by reading the file
    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict):
            # Check for Moatless format (has "transitions" key)
            if "transitions" in data:
                stats = parse_moatless_trace(trace_path)
                if stats and stats.total_actions > 0:
                    return stats

            # Otherwise try SWE-agent format (object with trajectory)
            if "trajectory" in data or "history" in data:
                stats = parse_sweagent_trace(trace_path)
                if stats and stats.total_actions > 0:
                    return stats

    except:
        pass

    # Fallback: try SWE-agent format
    stats = parse_sweagent_trace(trace_path)
    if stats and stats.total_actions > 0:
        return stats

    return None


def find_trace_files(submission_dir: Path) -> List[Path]:
    """Find all trace files in a submission directory"""
    trace_files = []

    # Check trajs/ folder
    trajs_dir = submission_dir / "trajs"
    if trajs_dir.exists():
        for ext in ["*.json", "*.jsonl", "*.yaml", "*.md", "*.traj"]:
            trace_files.extend(trajs_dir.glob(ext))

    # Check logs/ folder as fallback
    if not trace_files:
        logs_dir = submission_dir / "logs"
        if logs_dir.exists():
            for ext in ["*.json", "*.jsonl", "*.yaml", "*.log"]:
                trace_files.extend(logs_dir.glob(f"**/{ext}"))

    return trace_files


def analyze_submission(submission_dir: Path) -> List[TraceStats]:
    """Analyze all traces in a submission"""
    trace_files = find_trace_files(submission_dir)

    if not trace_files:
        print(f"  No trace files found in {submission_dir.name}")
        return []

    stats_list = []
    for trace_path in trace_files:
        stats = parse_generic_trace(trace_path)
        if stats:
            stats_list.append(stats)

    return stats_list


def compute_aggregate(stats_list: List[TraceStats]) -> Dict[str, Any]:
    """Compute aggregate statistics"""
    if not stats_list:
        return {}

    total_bash = sum(s.bash_commands for s in stats_list)
    total_test = sum(s.test_executions for s in stats_list)
    total_actions = sum(s.total_actions for s in stats_list)
    resolved_count = sum(1 for s in stats_list if s.resolved)

    bash_counts = [s.bash_commands for s in stats_list]
    test_counts = [s.test_executions for s in stats_list]
    action_counts = [s.total_actions for s in stats_list]

    test_ratios = []
    for s in stats_list:
        if s.bash_commands > 0:
            test_ratios.append(s.test_executions / s.bash_commands)
        else:
            test_ratios.append(0.0)

    return {
        "num_instances": len(stats_list),
        "resolved": resolved_count,
        "resolve_rate": resolved_count / len(stats_list) if stats_list else 0,

        "total_actions": total_actions,
        "total_bash_commands": total_bash,
        "total_test_executions": total_test,
        "test_execution_ratio": total_test / total_bash if total_bash > 0 else 0,

        "avg_actions_per_instance": statistics.mean(action_counts) if action_counts else 0,
        "avg_bash_per_instance": statistics.mean(bash_counts) if bash_counts else 0,
        "avg_test_per_instance": statistics.mean(test_counts) if test_counts else 0,
        "avg_test_ratio": statistics.mean(test_ratios) if test_ratios else 0,

        "median_bash_per_instance": statistics.median(bash_counts) if bash_counts else 0,
        "median_test_per_instance": statistics.median(test_counts) if test_counts else 0,
    }


def generate_report(all_stats: Dict[str, List[TraceStats]], output_dir: Path):
    """Generate analysis report"""

    report_lines = [
        "# RQ1: Cross-Agent Execution Analysis on SWE-bench",
        "",
        "## Overview",
        "",
        "This report analyzes execution patterns across different agent+model combinations",
        "on SWE-bench Lite/Verified.",
        "",
        "---",
        "",
        "## Summary Table",
        "",
        "| Submission | Agent | Model | Instances | Resolved | Resolve Rate | Avg Actions | Avg Bash | Avg Test | Test Ratio |",
        "|------------|-------|-------|-----------|----------|--------------|-------------|----------|----------|------------|",
    ]

    aggregates = {}
    for submission, stats_list in sorted(all_stats.items()):
        if not stats_list:
            continue

        agg = compute_aggregate(stats_list)
        aggregates[submission] = agg

        agent_type, model = extract_agent_model(submission)

        report_lines.append(
            f"| {submission[:40]} | {agent_type} | {model[:20]} | "
            f"{agg['num_instances']} | {agg['resolved']} | {agg['resolve_rate']:.1%} | "
            f"{agg['avg_actions_per_instance']:.1f} | {agg['avg_bash_per_instance']:.1f} | "
            f"{agg['avg_test_per_instance']:.1f} | {agg['test_execution_ratio']:.1%} |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## By Agent Type",
        "",
    ])

    # Group by agent type
    by_agent = defaultdict(list)
    for submission, stats_list in all_stats.items():
        agent_type, _ = extract_agent_model(submission)
        by_agent[agent_type].extend(stats_list)

    report_lines.append("| Agent Type | Instances | Avg Bash | Avg Test | Test Ratio |")
    report_lines.append("|------------|-----------|----------|----------|------------|")

    for agent_type, stats_list in sorted(by_agent.items()):
        if not stats_list:
            continue
        agg = compute_aggregate(stats_list)
        report_lines.append(
            f"| {agent_type} | {agg['num_instances']} | "
            f"{agg['avg_bash_per_instance']:.1f} | {agg['avg_test_per_instance']:.1f} | "
            f"{agg['test_execution_ratio']:.1%} |"
        )

    # Save report
    report_path = output_dir / "rq1_cross_agent_analysis.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"Report saved to: {report_path}")

    # Save CSV
    csv_path = output_dir / "rq1_cross_agent_stats.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'submission', 'agent_type', 'model', 'instance_id',
            'total_actions', 'bash_commands', 'test_executions',
            'file_edits', 'file_reads', 'resolved'
        ])
        for submission, stats_list in all_stats.items():
            agent_type, model = extract_agent_model(submission)
            for s in stats_list:
                writer.writerow([
                    submission, agent_type, model, s.instance_id,
                    s.total_actions, s.bash_commands, s.test_executions,
                    s.file_edits, s.file_reads, s.resolved
                ])
    print(f"CSV saved to: {csv_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze SWE-bench experiment traces")
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Directory containing downloaded experiments")
    parser.add_argument("--output-dir", type=str, default="./results",
                        help="Output directory for analysis results")
    parser.add_argument("--split", type=str, default="all",
                        help="Which split to analyze (lite/verified/all)")

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SWE-bench Cross-Agent Trace Analysis")
    print("=" * 60)
    print()

    # Determine which splits to analyze
    if args.split == "all":
        splits = ["lite", "verified"]
    else:
        splits = [args.split]

    all_stats = {}

    for split in splits:
        print(f"\n{'='*60}")
        print(f"Analyzing {split.upper()} dataset...")
        print("=" * 60)

        # Find submissions - try multiple path patterns
        eval_dir = None
        for pattern in [
            data_dir / split,  # data/traces/lite
            data_dir / "swe-bench-experiments" / "evaluation" / split,
            data_dir / "evaluation" / split,
        ]:
            if pattern.exists():
                eval_dir = pattern
                break

        if not eval_dir or not eval_dir.exists():
            print(f"  Evaluation directory not found for {split}. Skipping.")
            continue

        submissions = [d for d in eval_dir.iterdir() if d.is_dir()]
        print(f"Found {len(submissions)} submissions in {split}")
        print()

        # Analyze each submission
        for submission_dir in sorted(submissions):
            print(f"  Analyzing {submission_dir.name}...")
            stats_list = analyze_submission(submission_dir)
            if stats_list:
                # Use split prefix to distinguish same submission in different splits
                key = f"{split}_{submission_dir.name}"
                all_stats[key] = stats_list
                print(f"    Parsed {len(stats_list)} traces")

    print()
    print("=" * 60)
    print("Generating report...")
    print("=" * 60)

    generate_report(all_stats, output_dir)

    print()
    print("Analysis complete!")


if __name__ == "__main__":
    main()
