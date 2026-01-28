#!/usr/bin/env python3
"""
Parse and analyze SWE-bench experiment traces - V2
Supports multiple agent formats: SWE-agent, OpenHands, Moatless, Honeycomb, GRU, IBM-SWE

This script parses traces from different agent frameworks and extracts:
1. Execution frequency (test runs vs exploration commands)
2. Action patterns
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
    submission: str
    agent_type: str
    model: str
    dataset: str  # lite or verified

    # Execution counts
    total_actions: int = 0
    bash_commands: int = 0
    test_executions: int = 0
    file_edits: int = 0

    # Other metrics
    num_turns: int = 0
    resolved: bool = False

    # Raw commands for debugging
    commands: List[str] = field(default_factory=list)


def extract_agent_model(submission_name: str) -> tuple:
    """Extract agent type and model from submission name"""
    name = submission_name
    for prefix in ["lite_", "verified_"]:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break

    parts = name.split("_", 1)
    if len(parts) < 2:
        return "unknown", "unknown"

    rest = parts[1]

    agent_patterns = [
        (r"^sweagent[_-]?", "SWE-agent"),
        (r"^moatless[_-]?", "Moatless"),
        (r"^agentless[_-]?[\d.]*[_-]?", "Agentless"),
        (r"^OpenHands[_-]?", "OpenHands"),
        (r"^autocoderover[_-]?", "AutoCodeRover"),
        (r"^aider", "Aider"),
        (r"^MASAI", "MASAI"),
        (r"^amazon-q", "Amazon-Q"),
        (r"^CodeR", "CodeR"),
        (r"^SuperCoder", "SuperCoder"),
        (r"^IBM", "IBM-SWE"),
        (r"^honeycomb", "Honeycomb"),
        (r"^gru", "GRU"),
        (r"^factory", "Factory"),
    ]

    agent_type = "Other"
    model = rest

    for pattern, agent_name in agent_patterns:
        match = re.match(pattern, rest, re.IGNORECASE)
        if match:
            agent_type = agent_name
            model = rest[match.end():].strip("_-")
            break

    # Clean up model name
    model = model.replace("_", "-") if model else "unknown"

    # Normalize model names
    model_mapping = {
        "gpt4": "GPT-4",
        "gpt-4": "GPT-4",
        "gpt4o": "GPT-4o",
        "gpt-4o": "GPT-4o",
        "claude3opus": "Claude-3-Opus",
        "claude3.5sonnet": "Claude-3.5-Sonnet",
        "claude-3.5-sonnet": "Claude-3.5-Sonnet",
        "claude-3-5-sonnet": "Claude-3.5-Sonnet",
        "claude-3-7-sonnet": "Claude-3.7-Sonnet",
    }

    for key, val in model_mapping.items():
        if key in model.lower():
            model = val
            break

    return agent_type, model


def is_test_command(command: str) -> bool:
    """Determine if a command is a test/script execution"""
    if not command:
        return False

    cmd_lower = command.lower().strip()

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

    # Python script execution (python xxx.py)
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        if not re.search(r'python[3]?\s+-c\s', cmd_lower):
            return True

    return False


def is_bash_command(action: str) -> bool:
    """Determine if an action is a bash/shell command execution"""
    if not action:
        return False

    action_lower = action.lower().strip()

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
        r'^pytest\b',
        r'^bash\b',
        r'^sh\b',
    ]

    for pattern in bash_patterns:
        if re.search(pattern, action_lower):
            return True

    return False


def parse_sweagent_trace(data: dict, instance_id: str, submission: str, dataset: str) -> Optional[TraceStats]:
    """Parse SWE-agent format trace"""
    agent_type, model = extract_agent_model(submission)
    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model,
        dataset=dataset
    )

    trajectory = data.get("trajectory", data.get("history", []))

    for item in trajectory:
        if not isinstance(item, dict):
            continue

        stats.num_turns += 1
        action = item.get("action", "")

        if not isinstance(action, str):
            continue

        if is_bash_command(action):
            stats.bash_commands += 1
            stats.commands.append(action[:200])
            if is_test_command(action):
                stats.test_executions += 1
        elif action.lower().startswith("search_") or action.lower().startswith("find_"):
            stats.bash_commands += 1
            stats.commands.append(action[:200])
        elif action.lower().startswith("edit ") or action.lower().startswith("create "):
            stats.file_edits += 1

    stats.total_actions = len(trajectory)

    info = data.get("info", {})
    if isinstance(info, dict):
        exit_status = info.get("exit_status", "")
        stats.resolved = "submitted" in str(exit_status).lower() or info.get("resolved", False)

    return stats


def parse_openhands_trace(data: list, instance_id: str, submission: str, dataset: str) -> Optional[TraceStats]:
    """Parse OpenHands format trace (JSON array)

    Supports two formats:
    1. Old format: role=assistant with tool_calls[].function.name/arguments
    2. New format (Qwen3, etc.): source=agent with action=run and args.command
    """
    agent_type, model = extract_agent_model(submission)
    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model,
        dataset=dataset
    )

    for item in data:
        if not isinstance(item, dict):
            continue

        stats.num_turns += 1

        # Format 1: Old OpenHands format (role=assistant, tool_calls)
        role = item.get("role", "")
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

        # Format 2: New OpenHands format (source=agent, action=run)
        source = item.get("source", "")
        action = item.get("action", "")
        if source == "agent" and action == "run":
            args = item.get("args", {})
            if isinstance(args, dict):
                cmd = args.get("command", "")
                if cmd:
                    stats.bash_commands += 1
                    stats.commands.append(cmd[:200])
                    if is_test_command(cmd):
                        stats.test_executions += 1
        elif source == "agent" and action in ["edit", "write"]:
            stats.file_edits += 1

    stats.total_actions = stats.num_turns
    stats.resolved = stats.bash_commands > 0

    return stats


def parse_honeycomb_trace(data: list, instance_id: str, submission: str, dataset: str) -> Optional[TraceStats]:
    """Parse Honeycomb format trace (conversation array)"""
    agent_type, model = extract_agent_model(submission)
    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model,
        dataset=dataset
    )

    # Honeycomb uses conversation format where commands appear in user messages
    # after being executed (showing terminal output)
    for item in data:
        if not isinstance(item, dict):
            continue

        role = item.get("role", "")
        content = item.get("content", "")
        stats.num_turns += 1

        if role == "user" and isinstance(content, str):
            # Look for terminal prompts indicating command execution
            # Pattern: ubuntu@xxx:~/workdir$ command
            cmd_matches = re.findall(r'\$\s*(.+?)(?:\n|$)', content)
            for cmd in cmd_matches:
                cmd = cmd.strip()
                if cmd and is_bash_command(cmd):
                    stats.bash_commands += 1
                    stats.commands.append(cmd[:200])
                    if is_test_command(cmd):
                        stats.test_executions += 1

    stats.total_actions = stats.num_turns
    stats.resolved = stats.bash_commands > 0

    return stats


def parse_moatless_trace(data: dict, instance_id: str, submission: str, dataset: str) -> Optional[TraceStats]:
    """Parse Moatless format trace (pure reasoning agent)"""
    agent_type, model = extract_agent_model(submission)
    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model,
        dataset=dataset
    )

    transitions = data.get("transitions", [])

    for transition in transitions:
        if not isinstance(transition, dict):
            continue

        transition_name = transition.get("name", "")
        stats.num_turns += 1

        # Moatless uses high-level API, not bash
        if transition_name in ["SearchCode", "FindCode"]:
            pass  # Search action
        elif transition_name in ["IdentifyCode", "ViewCode"]:
            pass  # Read action
        elif transition_name in ["PlanToCode", "EditCode", "ApplyChange"]:
            stats.file_edits += 1
        elif transition_name in ["RunTests", "Verify"]:
            # Moatless doesn't actually run tests via bash
            stats.test_executions += 1

        actions = transition.get("actions", [])
        stats.total_actions += len(actions) if actions else 1

    if stats.total_actions == 0:
        stats.total_actions = len(transitions)

    # Moatless is pure reasoning - bash_commands stays 0
    return stats


def parse_gru_trace(data: dict, instance_id: str, submission: str, dataset: str) -> Optional[TraceStats]:
    """Parse GRU format trace"""
    agent_type, model = extract_agent_model(submission)
    stats = TraceStats(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model,
        dataset=dataset
    )

    traj = data.get("trajectory", {})
    details = traj.get("details", []) if isinstance(traj, dict) else []

    for detail in details:
        if not isinstance(detail, dict):
            continue

        conv = detail.get("exportedConversation", {})
        if not isinstance(conv, dict):
            continue

        # Check messages
        messages = conv.get("messages", [])
        for msg in messages:
            if isinstance(msg, dict):
                stats.num_turns += 1
                content = msg.get("content", "")
                if isinstance(content, str):
                    # Look for bash commands in content
                    cmd_matches = re.findall(r'```(?:bash|shell|sh)?\n(.+?)\n```', content, re.DOTALL)
                    for cmd_block in cmd_matches:
                        for cmd in cmd_block.split('\n'):
                            cmd = cmd.strip()
                            if cmd and is_bash_command(cmd):
                                stats.bash_commands += 1
                                stats.commands.append(cmd[:200])
                                if is_test_command(cmd):
                                    stats.test_executions += 1

    stats.total_actions = max(stats.num_turns, 1)
    return stats


def parse_trace_file(trace_path: Path, submission: str, dataset: str) -> Optional[TraceStats]:
    """Parse a trace file, auto-detecting format"""
    instance_id = trace_path.stem.replace(".traj", "").replace(".json", "").replace(".yaml", "")

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

        if data is None:
            return None

        # Detect format and parse
        if isinstance(data, list):
            # OpenHands or Honeycomb format
            if data and isinstance(data[0], dict):
                first_item = data[0]
                # OpenHands old format: has role=system or tool_calls
                # OpenHands new format (Qwen3, etc.): has source=agent and action
                if ("tool_calls" in str(first_item) or
                    first_item.get("role") == "system" or
                    first_item.get("source") == "agent"):
                    return parse_openhands_trace(data, instance_id, submission, dataset)
                else:
                    return parse_honeycomb_trace(data, instance_id, submission, dataset)

        elif isinstance(data, dict):
            # Check for Moatless format
            if "transitions" in data:
                return parse_moatless_trace(data, instance_id, submission, dataset)
            # Check for GRU format
            elif "trajectory" in data and isinstance(data.get("trajectory"), dict):
                if "details" in data.get("trajectory", {}):
                    return parse_gru_trace(data, instance_id, submission, dataset)
            # Check for SWE-agent format
            if "trajectory" in data or "history" in data:
                return parse_sweagent_trace(data, instance_id, submission, dataset)

        return None

    except Exception as e:
        return None


def find_trace_files(submission_dir: Path) -> List[Path]:
    """Find all trace files in a submission directory"""
    trace_files = []

    # Check trajs/ folder
    trajs_dir = submission_dir / "trajs"
    if trajs_dir.exists():
        # Pattern 1: trajs/*.json (flat structure)
        for ext in ["*.json", "*.traj", "*.yaml"]:
            trace_files.extend(trajs_dir.glob(ext))

        # Pattern 2: trajs/instance_id/trajectory.json (nested structure, e.g., Qwen)
        if not trace_files:
            trace_files.extend(trajs_dir.glob("*/trajectory.json"))

    return trace_files


def analyze_submission(submission_dir: Path, dataset: str) -> List[TraceStats]:
    """Analyze all traces in a submission"""
    trace_files = find_trace_files(submission_dir)
    submission_name = submission_dir.name

    if not trace_files:
        return []

    stats_list = []
    for trace_path in trace_files:
        stats = parse_trace_file(trace_path, submission_name, dataset)
        if stats:
            stats_list.append(stats)

    return stats_list


def compute_aggregate(stats_list: List[TraceStats]) -> Dict[str, Any]:
    """Compute aggregate statistics"""
    if not stats_list:
        return {}

    total_bash = sum(s.bash_commands for s in stats_list)
    total_test = sum(s.test_executions for s in stats_list)

    bash_counts = [s.bash_commands for s in stats_list]
    test_counts = [s.test_executions for s in stats_list]

    return {
        "num_instances": len(stats_list),
        "total_bash_commands": total_bash,
        "total_test_executions": total_test,
        "test_execution_ratio": total_test / total_bash if total_bash > 0 else 0,
        "avg_bash_per_instance": statistics.mean(bash_counts) if bash_counts else 0,
        "avg_test_per_instance": statistics.mean(test_counts) if test_counts else 0,
    }


def generate_report(all_stats: Dict[str, List[TraceStats]], output_dir: Path):
    """Generate analysis report"""

    # Group by agent-model-dataset
    grouped = defaultdict(list)
    for submission, stats_list in all_stats.items():
        for s in stats_list:
            key = (s.agent_type, s.model, s.dataset)
            grouped[key].append(s)

    report_lines = [
        "# Cross-Agent Execution Analysis on SWE-bench",
        "",
        "## Summary Table",
        "",
        "| Agent | Model | Dataset | Instances | Avg Bash | Avg Test | Test Ratio |",
        "|-------|-------|---------|-----------|----------|----------|------------|",
    ]

    # Sort by agent, model, dataset
    for key in sorted(grouped.keys()):
        agent_type, model, dataset = key
        stats_list = grouped[key]
        agg = compute_aggregate(stats_list)

        if agg["num_instances"] > 0:
            report_lines.append(
                f"| {agent_type} | {model[:20]} | {dataset} | "
                f"{agg['num_instances']} | {agg['avg_bash_per_instance']:.1f} | "
                f"{agg['avg_test_per_instance']:.1f} | {agg['test_execution_ratio']:.1%} |"
            )

    report_lines.extend([
        "",
        "## By Agent Type (Aggregated)",
        "",
        "| Agent Type | Total Instances | Avg Bash | Avg Test | Test Ratio |",
        "|------------|-----------------|----------|----------|------------|",
    ])

    # Group by agent type only
    by_agent = defaultdict(list)
    for key, stats_list in grouped.items():
        agent_type = key[0]
        by_agent[agent_type].extend(stats_list)

    for agent_type in sorted(by_agent.keys()):
        stats_list = by_agent[agent_type]
        agg = compute_aggregate(stats_list)
        if agg["num_instances"] > 0:
            report_lines.append(
                f"| {agent_type} | {agg['num_instances']} | "
                f"{agg['avg_bash_per_instance']:.1f} | {agg['avg_test_per_instance']:.1f} | "
                f"{agg['test_execution_ratio']:.1%} |"
            )

    # Save report
    report_path = output_dir / "cross_agent_analysis_v2.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print(f"Report saved to: {report_path}")

    # Save CSV
    csv_path = output_dir / "cross_agent_stats_v2.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'agent_type', 'model', 'dataset', 'instance_id',
            'bash_commands', 'test_executions', 'file_edits', 'num_turns'
        ])
        for submission, stats_list in all_stats.items():
            for s in stats_list:
                writer.writerow([
                    s.agent_type, s.model, s.dataset, s.instance_id,
                    s.bash_commands, s.test_executions, s.file_edits, s.num_turns
                ])
    print(f"CSV saved to: {csv_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Analyze SWE-bench experiment traces V2")
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Directory containing traces")
    parser.add_argument("--output-dir", type=str, default="./results_v2",
                        help="Output directory")

    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SWE-bench Cross-Agent Trace Analysis V2")
    print("=" * 60)
    print()

    all_stats = {}

    for dataset in ["lite", "verified"]:
        dataset_dir = data_dir / dataset
        if not dataset_dir.exists():
            continue

        print(f"\n{'='*60}")
        print(f"Analyzing {dataset.upper()} dataset...")
        print("=" * 60)

        submissions = [d for d in dataset_dir.iterdir() if d.is_dir()]
        print(f"Found {len(submissions)} submissions")

        for submission_dir in sorted(submissions):
            print(f"  Analyzing {submission_dir.name}...")
            stats_list = analyze_submission(submission_dir, dataset)
            if stats_list:
                key = f"{dataset}_{submission_dir.name}"
                all_stats[key] = stats_list

                # Quick summary
                agg = compute_aggregate(stats_list)
                print(f"    Parsed {len(stats_list)} traces, "
                      f"avg bash={agg['avg_bash_per_instance']:.1f}, "
                      f"avg test={agg['avg_test_per_instance']:.1f}, "
                      f"ratio={agg['test_execution_ratio']:.1%}")
            else:
                print(f"    No traces found")

    print()
    print("=" * 60)
    print("Generating report...")
    print("=" * 60)

    generate_report(all_stats, output_dir)

    print()
    print("Analysis complete!")


if __name__ == "__main__":
    main()
