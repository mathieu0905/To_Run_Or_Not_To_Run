#!/usr/bin/env python3
"""
RQ1 Analysis: Execution Frequency and Token Consumption in Baseline (run_full) Mode

This script analyzes:
1. Test execution frequency (pytest, unittest, etc.) vs total Bash calls
2. Token consumption statistics
3. Ratio of test executions to total executions

Outputs:
- CSV files with detailed statistics
- Markdown report with summary tables
"""

import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics


@dataclass
class ExecutionStats:
    """Statistics for a single instance"""
    instance_id: str
    agent_type: str
    dataset: str

    # Execution counts
    total_bash_calls: int = 0
    test_executions: int = 0  # pytest, unittest, etc.

    # Token usage
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0

    # Token usage for test executions (tokens in turns that contain test commands)
    test_input_tokens: int = 0
    test_output_tokens: int = 0
    test_tokens: int = 0

    # Cost
    total_cost_usd: float = 0.0

    # Duration
    duration_sec: float = 0.0

    # Bash commands breakdown
    bash_commands: List[str] = field(default_factory=list)
    test_commands: List[str] = field(default_factory=list)


def is_test_execution(command: str) -> bool:
    """
    Determine if a command is a test execution (pytest, unittest, etc.)

    Counts as test execution:
    - pytest / py.test
    - unittest
    - Django tests (python manage.py test, runtests.py)
    - tox
    - nose / nosetests
    - python xxx.py (running test scripts)

    Does NOT count:
    - ls, cat, grep, find, rg, sed, etc. (viewing commands)
    - git commands
    - cd, pwd (navigation)
    - python -c (simple commands)
    - python --version (info queries)
    """
    if not command:
        return False

    # Normalize: Codex wraps commands in /bin/bash -lc 'bash -lc "..."'
    # Extract the innermost command for analysis
    command_normalized = command

    # Remove outer bash wrapper patterns
    bash_wrapper_patterns = [
        r"^/bin/bash\s+-lc\s+['\"]bash\s+-lc\s+['\\\"](.+)['\\\"]['\"]$",
        r"^/bin/bash\s+-lc\s+['\"](.+)['\"]$",
        r"^bash\s+-lc\s+['\"](.+)['\"]$",
    ]
    for pattern in bash_wrapper_patterns:
        match = re.match(pattern, command, re.DOTALL)
        if match:
            command_normalized = match.group(1)
            # Unescape
            command_normalized = command_normalized.replace('\\"', '"').replace("\\'", "'")
            break

    command_lower = command_normalized.lower()

    # Exclude common viewing/exploration commands first
    viewing_patterns = [
        r'^\s*(ls|cat|head|tail|grep|rg|find|sed|awk|nl|wc)\s',
        r'^\s*(cd|pwd|echo|printf|export)\s',
        r'^\s*(git)\s',
        r'^\s*(pip|pip3)\s',
    ]
    for pattern in viewing_patterns:
        if re.search(pattern, command_lower):
            return False

    # Test framework patterns
    test_patterns = [
        r'\bpytest\b',
        r'\bpy\.test\b',
        r'python[3]?\s+(-m\s+)?pytest',
        r'python[3]?\s+-m\s+unittest',
        r'runtests\.py\b',  # Django's test runner
        r'manage\.py\s+test',
        r'python[3]?\s+manage\.py\s+test',
        r'\btox\b',
        r'\bnose\b',
        r'\bnosetests\b',
        r'python[3]?\s+-m\s+nose',
    ]

    for pattern in test_patterns:
        if re.search(pattern, command_lower):
            return True

    # Python script execution (but exclude special cases)
    if re.search(r'python[3]?\s+', command_lower):
        # Exclude python -c (simple commands)
        if re.search(r'python[3]?\s+-c\s', command_lower):
            return False
        # Exclude info queries
        if '--version' in command_lower or '--help' in command_lower:
            return False
        # Exclude module info
        if re.search(r'-m\s+pip', command_lower):
            return False
        # If running a .py file, count it
        if re.search(r'python[3]?\s+\S+\.py', command_lower):
            return True

    return False


def extract_bash_commands(entry: Dict[str, Any]) -> List[str]:
    """Extract bash commands from a trace entry

    Supports multiple formats:
    1. Claude Code: entry.message.content[] contains tool_use items with name="Bash"
    2. Codex: entry.type="item.completed" with item.type="command_execution"
    """
    commands = []

    # Format 1: Direct tool_use entry (some formats)
    if entry.get("type") == "tool_use" and str(entry.get("name", "")).lower() == "bash":
        input_data = entry.get("input", {})
        if isinstance(input_data, dict) and input_data.get("command"):
            commands.append(input_data.get("command"))
        return commands

    # Format 2: Claude Code format - nested in message.content[]
    message = entry.get("message", {})
    if isinstance(message, dict):
        content = message.get("content", [])
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "tool_use" and str(item.get("name", "")).lower() == "bash":
                    input_data = item.get("input", {})
                    if isinstance(input_data, dict) and input_data.get("command"):
                        commands.append(input_data.get("command"))

    # Format 3: Codex format - item.completed with command_execution
    if entry.get("type") == "item.completed":
        item = entry.get("item", {})
        if isinstance(item, dict) and item.get("type") == "command_execution":
            cmd = item.get("command", "")
            if cmd:
                # Codex wraps commands in /bin/bash -lc "bash -lc \"...\""
                # Extract the actual command
                commands.append(cmd)

    return commands


def parse_trace_file(trace_path: Path) -> ExecutionStats:
    """Parse a trace.jsonl file and extract statistics"""
    instance_id = trace_path.parent.name

    # Determine agent type and dataset from path
    # Path format: output/{dataset}/{agent}/{mode}/{instance_id}/trace.jsonl
    path_parts = trace_path.parts
    try:
        output_idx = path_parts.index("output")
        dataset = path_parts[output_idx + 1]
        agent_type = path_parts[output_idx + 2]
    except (ValueError, IndexError):
        dataset = "unknown"
        agent_type = "unknown"

    stats = ExecutionStats(
        instance_id=instance_id,
        agent_type=agent_type,
        dataset=dataset
    )

    traces = []
    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        traces.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"Warning: Failed to read {trace_path}: {e}")
        return stats

    # Detect agent format based on trace content
    is_codex_format = any(e.get("type") == "turn.started" for e in traces)

    if is_codex_format:
        # Codex format: process by turns
        # turn.started -> item.completed (commands) -> turn.completed (usage)
        current_turn_commands = []
        current_turn_has_test = False

        for entry in traces:
            entry_type = entry.get("type")

            if entry_type == "turn.started":
                # Reset for new turn
                current_turn_commands = []
                current_turn_has_test = False

            elif entry_type == "item.completed":
                item = entry.get("item", {})
                if isinstance(item, dict) and item.get("type") == "command_execution":
                    cmd = item.get("command", "")
                    if cmd:
                        stats.total_bash_calls += 1
                        stats.bash_commands.append(cmd)
                        if is_test_execution(cmd):
                            stats.test_executions += 1
                            stats.test_commands.append(cmd)
                            current_turn_has_test = True

            elif entry_type == "turn.completed":
                # Turn completed, get usage for this turn
                usage = entry.get("usage", {})
                if isinstance(usage, dict):
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)

                    stats.total_input_tokens += input_tokens
                    stats.total_output_tokens += output_tokens

                    # If this turn had test commands, count tokens as test tokens
                    if current_turn_has_test:
                        stats.test_input_tokens += input_tokens
                        stats.test_output_tokens += output_tokens

                # Reset for next turn
                current_turn_commands = []
                current_turn_has_test = False

            # Extract final stats from thread completion if available
            elif entry_type == "thread.completed":
                if entry.get("total_cost_usd"):
                    stats.total_cost_usd = entry.get("total_cost_usd", 0.0) or 0.0
                if entry.get("duration_ms"):
                    stats.duration_sec = entry.get("duration_ms", 0) / 1000.0

    else:
        # Claude Code format: process each entry individually
        for entry in traces:
            # Extract bash commands (may return multiple per entry)
            cmds = extract_bash_commands(entry)
            has_test_cmd = False
            for cmd in cmds:
                stats.total_bash_calls += 1
                stats.bash_commands.append(cmd)
                if is_test_execution(cmd):
                    stats.test_executions += 1
                    stats.test_commands.append(cmd)
                    has_test_cmd = True

            # Extract token usage
            entry_input_tokens = 0
            entry_output_tokens = 0

            # Format: entry.message.usage (Claude Code)
            message = entry.get("message")
            if isinstance(message, dict):
                msg_usage = message.get("usage")
                if isinstance(msg_usage, dict):
                    entry_input_tokens += msg_usage.get("input_tokens", 0)
                    entry_output_tokens += msg_usage.get("output_tokens", 0)

            # Add to totals
            stats.total_input_tokens += entry_input_tokens
            stats.total_output_tokens += entry_output_tokens

            # If this entry contains a test command, count its tokens as test tokens
            if has_test_cmd:
                stats.test_input_tokens += entry_input_tokens
                stats.test_output_tokens += entry_output_tokens

            # Extract final result stats
            if entry.get("type") == "result":
                stats.total_cost_usd = entry.get("total_cost_usd", 0.0) or 0.0
                stats.duration_sec = entry.get("duration_ms", 0) / 1000.0

                # modelUsage provides aggregated stats if we haven't collected any
                model_usage = entry.get("modelUsage", {})
                if model_usage and stats.total_input_tokens == 0:
                    for model_name, model_stats in model_usage.items():
                        if isinstance(model_stats, dict):
                            stats.total_input_tokens += model_stats.get("inputTokens", 0)
                            stats.total_output_tokens += model_stats.get("outputTokens", 0)

    stats.total_tokens = stats.total_input_tokens + stats.total_output_tokens
    stats.test_tokens = stats.test_input_tokens + stats.test_output_tokens

    return stats


def find_trace_files(output_dir: Path, agent_types: List[str], mode: str = "run_full") -> List[Path]:
    """Find all trace.jsonl files for specified agents and mode"""
    trace_files = []

    for dataset in ["swebenchlite", "swebenchverified"]:
        dataset_dir = output_dir / dataset
        if not dataset_dir.exists():
            continue

        for agent in agent_types:
            agent_mode_dir = dataset_dir / agent / mode
            if not agent_mode_dir.exists():
                continue

            for instance_dir in agent_mode_dir.iterdir():
                if instance_dir.is_dir():
                    trace_file = instance_dir / "trace.jsonl"
                    if trace_file.exists():
                        trace_files.append(trace_file)

    return trace_files


def compute_aggregate_stats(all_stats: List[ExecutionStats]) -> Dict[str, Any]:
    """Compute aggregate statistics across all instances"""
    if not all_stats:
        return {}

    total_bash = sum(s.total_bash_calls for s in all_stats)
    total_test = sum(s.test_executions for s in all_stats)
    total_tokens = sum(s.total_tokens for s in all_stats)
    total_test_tokens = sum(s.test_tokens for s in all_stats)
    total_cost = sum(s.total_cost_usd for s in all_stats)

    bash_counts = [s.total_bash_calls for s in all_stats]
    test_counts = [s.test_executions for s in all_stats]
    token_counts = [s.total_tokens for s in all_stats]
    test_token_counts = [s.test_tokens for s in all_stats]

    # Calculate test execution ratio per instance
    test_ratios = []
    test_token_ratios = []
    for s in all_stats:
        if s.total_bash_calls > 0:
            test_ratios.append(s.test_executions / s.total_bash_calls)
        else:
            test_ratios.append(0.0)
        if s.total_tokens > 0:
            test_token_ratios.append(s.test_tokens / s.total_tokens)
        else:
            test_token_ratios.append(0.0)

    return {
        "num_instances": len(all_stats),
        "total_bash_calls": total_bash,
        "total_test_executions": total_test,
        "test_execution_ratio": total_test / total_bash if total_bash > 0 else 0.0,
        "total_tokens": total_tokens,
        "total_test_tokens": total_test_tokens,
        "test_token_ratio": total_test_tokens / total_tokens if total_tokens > 0 else 0.0,
        "total_cost_usd": total_cost,

        # Per-instance stats
        "avg_bash_per_instance": statistics.mean(bash_counts) if bash_counts else 0,
        "median_bash_per_instance": statistics.median(bash_counts) if bash_counts else 0,
        "std_bash_per_instance": statistics.stdev(bash_counts) if len(bash_counts) > 1 else 0,
        "min_bash_per_instance": min(bash_counts) if bash_counts else 0,
        "max_bash_per_instance": max(bash_counts) if bash_counts else 0,

        "avg_test_per_instance": statistics.mean(test_counts) if test_counts else 0,
        "median_test_per_instance": statistics.median(test_counts) if test_counts else 0,
        "std_test_per_instance": statistics.stdev(test_counts) if len(test_counts) > 1 else 0,

        "avg_tokens_per_instance": statistics.mean(token_counts) if token_counts else 0,
        "median_tokens_per_instance": statistics.median(token_counts) if token_counts else 0,

        "avg_test_tokens_per_instance": statistics.mean(test_token_counts) if test_token_counts else 0,
        "median_test_tokens_per_instance": statistics.median(test_token_counts) if test_token_counts else 0,

        "avg_test_ratio_per_instance": statistics.mean(test_ratios) if test_ratios else 0,
        "median_test_ratio_per_instance": statistics.median(test_ratios) if test_ratios else 0,

        "avg_test_token_ratio_per_instance": statistics.mean(test_token_ratios) if test_token_ratios else 0,
        "median_test_token_ratio_per_instance": statistics.median(test_token_ratios) if test_token_ratios else 0,
    }


def generate_markdown_report(
    stats_by_agent: Dict[str, List[ExecutionStats]],
    aggregate_by_agent: Dict[str, Dict[str, Any]],
    output_path: Path
):
    """Generate a markdown report with analysis results"""

    lines = [
        "# RQ1: Execution Frequency and Token Consumption Analysis",
        "",
        "## Overview",
        "",
        "This report analyzes the **run_full** (unrestricted execution) mode to understand:",
        "1. How frequently agents execute tests vs. other commands",
        "2. Token consumption patterns",
        "3. The ratio of test executions to total Bash calls",
        "",
        "---",
        "",
        "## Summary Statistics",
        "",
    ]

    # Summary table
    lines.append("| Agent | Dataset | Instances | Total Bash | Total Test Exec | Test Ratio | Total Tokens | Test Tokens | Test Token Ratio |")
    lines.append("|-------|---------|-----------|------------|-----------------|------------|--------------|-------------|------------------|")

    for agent, stats_list in stats_by_agent.items():
        # Group by dataset
        by_dataset = defaultdict(list)
        for s in stats_list:
            by_dataset[s.dataset].append(s)

        for dataset, ds_stats in by_dataset.items():
            agg = compute_aggregate_stats(ds_stats)
            lines.append(
                f"| {agent} | {dataset} | {agg['num_instances']} | "
                f"{agg['total_bash_calls']} | {agg['total_test_executions']} | "
                f"{agg['test_execution_ratio']:.2%} | {agg['total_tokens']:,} | "
                f"{agg['total_test_tokens']:,} | {agg['test_token_ratio']:.2%} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Statistics by Agent",
        "",
    ])

    for agent, agg in aggregate_by_agent.items():
        lines.extend([
            f"### {agent}",
            "",
            f"- **Total Instances**: {agg['num_instances']}",
            f"- **Total Bash Calls**: {agg['total_bash_calls']}",
            f"- **Total Test Executions**: {agg['total_test_executions']}",
            f"- **Overall Test Execution Ratio**: {agg['test_execution_ratio']:.2%}",
            "",
            "#### Bash Calls per Instance",
            f"- Mean: {agg['avg_bash_per_instance']:.2f}",
            f"- Median: {agg['median_bash_per_instance']:.1f}",
            f"- Std Dev: {agg['std_bash_per_instance']:.2f}",
            f"- Range: [{agg['min_bash_per_instance']}, {agg['max_bash_per_instance']}]",
            "",
            "#### Test Executions per Instance",
            f"- Mean: {agg['avg_test_per_instance']:.2f}",
            f"- Median: {agg['median_test_per_instance']:.1f}",
            f"- Std Dev: {agg['std_test_per_instance']:.2f}",
            "",
            "#### Test Ratio per Instance",
            f"- Mean: {agg['avg_test_ratio_per_instance']:.2%}",
            f"- Median: {agg['median_test_ratio_per_instance']:.2%}",
            "",
            "#### Token Usage",
            f"- Total Tokens: {agg['total_tokens']:,}",
            f"- Mean per Instance: {agg['avg_tokens_per_instance']:,.0f}",
            f"- Median per Instance: {agg['median_tokens_per_instance']:,.0f}",
            f"- Total Cost (USD): ${agg['total_cost_usd']:.2f}",
            "",
            "---",
            "",
        ])

    # Key findings
    lines.extend([
        "## Key Findings",
        "",
    ])

    # Compare agents if we have multiple
    agents = list(aggregate_by_agent.keys())
    if len(agents) >= 2:
        a1, a2 = agents[0], agents[1]
        agg1, agg2 = aggregate_by_agent[a1], aggregate_by_agent[a2]

        lines.extend([
            f"### Comparison: {a1} vs {a2}",
            "",
            f"| Metric | {a1} | {a2} |",
            "|--------|------|------|",
            f"| Avg Bash Calls/Instance | {agg1['avg_bash_per_instance']:.2f} | {agg2['avg_bash_per_instance']:.2f} |",
            f"| Avg Test Executions/Instance | {agg1['avg_test_per_instance']:.2f} | {agg2['avg_test_per_instance']:.2f} |",
            f"| Test Execution Ratio | {agg1['test_execution_ratio']:.2%} | {agg2['test_execution_ratio']:.2%} |",
            f"| Avg Tokens/Instance | {agg1['avg_tokens_per_instance']:,.0f} | {agg2['avg_tokens_per_instance']:,.0f} |",
            "",
        ])

    lines.extend([
        "### Observations",
        "",
        "1. **Test Execution Ratio**: The ratio of test executions to total Bash calls indicates how much of the agent's execution effort is dedicated to running tests.",
        "",
        "2. **Token Consumption**: Higher token usage may correlate with more complex problem-solving or more verbose agent interactions.",
        "",
        "3. **Execution Frequency**: The number of Bash calls reflects the agent's debugging strategy - more calls suggest a trial-and-error approach.",
        "",
    ])

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Markdown report saved to: {output_path}")


def save_csv(all_stats: List[ExecutionStats], output_path: Path):
    """Save detailed statistics to CSV"""
    import csv

    fieldnames = [
        'instance_id', 'agent_type', 'dataset',
        'total_bash_calls', 'test_executions', 'test_ratio',
        'total_input_tokens', 'total_output_tokens', 'total_tokens',
        'total_cost_usd', 'duration_sec'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for s in all_stats:
            test_ratio = s.test_executions / s.total_bash_calls if s.total_bash_calls > 0 else 0.0
            writer.writerow({
                'instance_id': s.instance_id,
                'agent_type': s.agent_type,
                'dataset': s.dataset,
                'total_bash_calls': s.total_bash_calls,
                'test_executions': s.test_executions,
                'test_ratio': f"{test_ratio:.4f}",
                'total_input_tokens': s.total_input_tokens,
                'total_output_tokens': s.total_output_tokens,
                'total_tokens': s.total_tokens,
                'total_cost_usd': f"{s.total_cost_usd:.4f}",
                'duration_sec': f"{s.duration_sec:.2f}"
            })

    print(f"CSV saved to: {output_path}")


def save_commands_sample(all_stats: List[ExecutionStats], output_path: Path, sample_size: int = 100):
    """Save a sample of bash commands for manual inspection"""

    all_commands = []
    for s in all_stats:
        for cmd in s.bash_commands:
            is_test = is_test_execution(cmd)
            all_commands.append({
                'instance_id': s.instance_id,
                'agent_type': s.agent_type,
                'command': cmd[:200],  # Truncate long commands
                'is_test_execution': is_test
            })

    # Sample
    import random
    if len(all_commands) > sample_size:
        sampled = random.sample(all_commands, sample_size)
    else:
        sampled = all_commands

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sampled, f, indent=2, ensure_ascii=False)

    print(f"Commands sample saved to: {output_path}")


def main():
    # Determine paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / "output"
    results_dir = project_root / "analysis_results" / "rq1"
    results_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("RQ1: Execution Frequency and Token Consumption Analysis")
    print("=" * 60)
    print()

    # Find trace files
    # Only analyze claude_code (Codex doesn't have per-turn token breakdown)
    agent_types = ["claude_code"]
    mode = "run_full"

    print(f"Scanning for {mode} trace files...")
    print(f"Agents: {agent_types}")
    print(f"Output directory: {output_dir}")
    print()

    trace_files = find_trace_files(output_dir, agent_types, mode)
    print(f"Found {len(trace_files)} trace files")
    print()

    if not trace_files:
        print("No trace files found. Exiting.")
        return

    # Parse all traces
    print("Parsing trace files...")
    all_stats = []
    for i, trace_file in enumerate(trace_files):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(trace_files)} files...")
        stats = parse_trace_file(trace_file)
        all_stats.append(stats)

    print(f"Parsed {len(all_stats)} instances")
    print()

    # Group by agent
    stats_by_agent = defaultdict(list)
    for s in all_stats:
        stats_by_agent[s.agent_type].append(s)

    # Compute aggregate stats
    aggregate_by_agent = {}
    for agent, stats_list in stats_by_agent.items():
        aggregate_by_agent[agent] = compute_aggregate_stats(stats_list)

    # Print summary to console
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print()

    for agent, agg in aggregate_by_agent.items():
        print(f"Agent: {agent}")
        print(f"  Instances: {agg['num_instances']}")
        print(f"  Total Bash Calls: {agg['total_bash_calls']}")
        print(f"  Total Test Executions: {agg['total_test_executions']}")
        print(f"  Test Execution Ratio: {agg['test_execution_ratio']:.2%}")
        print(f"  Avg Bash/Instance: {agg['avg_bash_per_instance']:.2f}")
        print(f"  Avg Test/Instance: {agg['avg_test_per_instance']:.2f}")
        print(f"  Total Tokens: {agg['total_tokens']:,}")
        print(f"  Total Cost: ${agg['total_cost_usd']:.2f}")
        print()

    # Save outputs
    print("Saving results...")

    # CSV with all instance details
    save_csv(all_stats, results_dir / "rq1_execution_stats.csv")

    # Markdown report
    generate_markdown_report(stats_by_agent, aggregate_by_agent, results_dir / "rq1_report.md")

    # Sample commands for inspection
    save_commands_sample(all_stats, results_dir / "rq1_commands_sample.json")

    print()
    print("=" * 60)
    print(f"Results saved to: {results_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
