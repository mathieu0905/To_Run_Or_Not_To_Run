#!/usr/bin/env python3
"""
RQ2 In-depth Analysis: Why doesn't Codex significantly reduce token consumption in run_free mode?

Core Issues:
- Codex run_free vs run_full token savings only 0.8-13.4%
- Claude Code savings as high as 56-62%
- This indicates fundamental differences in behavior patterns between Codex and Claude Code

Analysis Goals:
1. Compare command execution patterns of both agents in different modes
2. Analyze token consumption composition (reasoning vs command output)
3. Identify root causes of Codex's high token consumption
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import re

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def parse_trace_file(trace_path: Path) -> dict:
    """Parse trace.jsonl file and extract key metrics. Supports both Codex and Claude Code formats."""
    result = {
        "reasoning_count": 0,
        "command_count": 0,
        "file_change_count": 0,
        "commands": [],
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
    }

    if not trace_path.exists():
        return result

    # Detect format type
    is_claude_code = False
    with open(trace_path, 'r') as f:
        first_line = f.readline()
        try:
            d = json.loads(first_line)
            if d.get('type') == 'system' and d.get('subtype') == 'init':
                is_claude_code = True
        except:
            pass

    with open(trace_path, 'r') as f:
        for line in f:
            try:
                d = json.loads(line.strip())

                if is_claude_code:
                    # Claude Code format
                    if d.get('type') == 'assistant':
                        message = d.get('message', {})
                        content = message.get('content', [])
                        usage = message.get('usage', {})

                        # Accumulate tokens
                        result['input_tokens'] += usage.get('input_tokens', 0)
                        result['output_tokens'] += usage.get('output_tokens', 0)
                        result['cached_tokens'] += usage.get('cache_read_input_tokens', 0)

                        for item in content:
                            if item.get('type') == 'tool_use':
                                tool_name = item.get('name', '')
                                if tool_name == 'Bash':
                                    result['command_count'] += 1
                                    cmd = item.get('input', {}).get('command', '')
                                    result['commands'].append(cmd)
                                elif tool_name == 'Edit' or tool_name == 'Write':
                                    result['file_change_count'] += 1
                            elif item.get('type') == 'text':
                                # Claude Code doesn't have a separate reasoning type, text output can be considered reasoning
                                if item.get('text', '').strip():
                                    result['reasoning_count'] += 1
                else:
                    # Codex format
                    if d.get('type') == 'item.completed':
                        item = d.get('item', {})
                        item_type = item.get('type')

                        if item_type == 'reasoning':
                            result['reasoning_count'] += 1
                        elif item_type == 'command_execution':
                            result['command_count'] += 1
                            cmd = item.get('command', '')
                            result['commands'].append(cmd)
                        elif item_type == 'file_change':
                            result['file_change_count'] += 1

                    # Extract token usage
                    if d.get('type') == 'turn.completed':
                        usage = d.get('usage', {})
                        result['input_tokens'] = usage.get('input_tokens', 0)
                        result['output_tokens'] = usage.get('output_tokens', 0)
                        result['cached_tokens'] = usage.get('cached_input_tokens', 0)

            except json.JSONDecodeError:
                continue

    return result


def classify_command(cmd: str) -> str:
    """Classify commands"""
    cmd_lower = cmd.lower()

    # Test execution
    if any(x in cmd_lower for x in ['pytest', 'python -m pytest', 'python -m unittest', 'manage.py test', 'tox', 'nose']):
        return 'test_execution'

    # Python code execution (non-test)
    if 'python' in cmd_lower and ('python -c' in cmd_lower or 'python -' in cmd_lower or 'python <<' in cmd_lower):
        return 'python_snippet'

    # File viewing
    if any(x in cmd_lower for x in ['cat ', 'head ', 'tail ', 'sed -n', 'less ', 'more ']):
        return 'file_view'

    # Search
    if any(x in cmd_lower for x in ['grep', 'rg ', 'find ', 'ag ']):
        return 'search'

    # Directory browsing
    if cmd_lower.strip().startswith('ls') or 'ls ' in cmd_lower:
        return 'directory_browse'

    # Git operations
    if 'git ' in cmd_lower:
        return 'git'

    return 'other'


def analyze_agent_behavior(agent: str, dataset: str) -> dict:
    """Analyze behavior of specific agent on specific dataset"""
    base_path = OUTPUT_DIR / dataset / agent

    results = {}
    for mode in ['run_free', 'run_less_k1', 'run_less_k3', 'run_cost', 'run_full']:
        mode_path = base_path / mode
        if not mode_path.exists():
            continue

        mode_results = {
            'instances': [],
            'total_reasoning': 0,
            'total_commands': 0,
            'total_file_changes': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'command_types': defaultdict(int),
        }

        for instance_dir in mode_path.iterdir():
            if not instance_dir.is_dir():
                continue

            trace_path = instance_dir / 'trace.jsonl'
            trace_data = parse_trace_file(trace_path)

            mode_results['instances'].append({
                'name': instance_dir.name,
                **trace_data
            })

            mode_results['total_reasoning'] += trace_data['reasoning_count']
            mode_results['total_commands'] += trace_data['command_count']
            mode_results['total_file_changes'] += trace_data['file_change_count']
            mode_results['total_input_tokens'] += trace_data['input_tokens']
            mode_results['total_output_tokens'] += trace_data['output_tokens']

            # 分类命令
            for cmd in trace_data['commands']:
                cmd_type = classify_command(cmd)
                mode_results['command_types'][cmd_type] += 1

        n = len(mode_results['instances'])
        if n > 0:
            mode_results['avg_reasoning'] = mode_results['total_reasoning'] / n
            mode_results['avg_commands'] = mode_results['total_commands'] / n
            mode_results['avg_file_changes'] = mode_results['total_file_changes'] / n
            mode_results['avg_input_tokens'] = mode_results['total_input_tokens'] / n
            mode_results['avg_output_tokens'] = mode_results['total_output_tokens'] / n

        results[mode] = mode_results

    return results


def generate_report(results: dict, agent: str, dataset: str) -> str:
    """Generate analysis report"""
    report = []
    report.append(f"# {agent} Behavior Analysis on {dataset}\n")

    # Overview table
    report.append("## Overview\n")
    report.append("| Mode | Instances | Avg Reasoning | Avg Commands | Avg File Changes | Avg Input Tokens | Avg Output Tokens |")
    report.append("|------|-----------|---------------|--------------|------------------|------------------|-------------------|")

    for mode in ['run_free', 'run_less_k1', 'run_less_k3', 'run_cost', 'run_full']:
        if mode not in results:
            continue
        r = results[mode]
        n = len(r['instances'])
        report.append(f"| {mode} | {n} | {r.get('avg_reasoning', 0):.1f} | {r.get('avg_commands', 0):.1f} | {r.get('avg_file_changes', 0):.1f} | {r.get('avg_input_tokens', 0):,.0f} | {r.get('avg_output_tokens', 0):,.0f} |")

    # Command type distribution
    report.append("\n## Command Type Distribution\n")
    report.append("| Mode | Test Exec | Python Snippet | File View | Search | Dir Browse | Git | Other |")
    report.append("|------|-----------|----------------|-----------|--------|------------|-----|-------|")

    for mode in ['run_free', 'run_less_k1', 'run_less_k3', 'run_cost', 'run_full']:
        if mode not in results:
            continue
        ct = results[mode]['command_types']
        report.append(f"| {mode} | {ct.get('test_execution', 0)} | {ct.get('python_snippet', 0)} | {ct.get('file_view', 0)} | {ct.get('search', 0)} | {ct.get('directory_browse', 0)} | {ct.get('git', 0)} | {ct.get('other', 0)} |")

    # Key findings
    report.append("\n## Key Findings\n")

    if 'run_free' in results and 'run_full' in results:
        rf = results['run_free']
        rfu = results['run_full']

        rfu_tokens = rfu.get('avg_input_tokens', 0)
        rfu_cmds = rfu.get('avg_commands', 0)

        if rfu_tokens > 0:
            token_diff = (rf.get('avg_input_tokens', 0) - rfu_tokens) / rfu_tokens * 100
        else:
            token_diff = 0

        if rfu_cmds > 0:
            cmd_diff = (rf.get('avg_commands', 0) - rfu_cmds) / rfu_cmds * 100
        else:
            cmd_diff = 0

        report.append(f"- **Token change**: run_free vs run_full = {token_diff:+.1f}%")
        report.append(f"- **Command count change**: run_free vs run_full = {cmd_diff:+.1f}%")

        # Analyze command type differences
        rf_tests = rf['command_types'].get('test_execution', 0)
        rfu_tests = rfu['command_types'].get('test_execution', 0)
        rf_explore = rf['command_types'].get('file_view', 0) + rf['command_types'].get('search', 0) + rf['command_types'].get('directory_browse', 0)
        rfu_explore = rfu['command_types'].get('file_view', 0) + rfu['command_types'].get('search', 0) + rfu['command_types'].get('directory_browse', 0)

        report.append(f"- **Test execution count**: run_free={rf_tests}, run_full={rfu_tests}")
        report.append(f"- **Code exploration commands**: run_free={rf_explore}, run_full={rfu_explore}")

    return '\n'.join(report)


def main():
    """Main function"""
    print("=" * 60)
    print("RQ2 In-depth Analysis: Codex Behavior Patterns")
    print("=" * 60)

    all_reports = []

    for dataset in ['swebenchlite', 'swebenchverified']:
        for agent in ['codex', 'claude_code']:
            print(f"\nAnalyzing {agent} behavior on {dataset}...")

            results = analyze_agent_behavior(agent, dataset)
            if not results:
                print(f"  No data found")
                continue

            report = generate_report(results, agent, dataset)
            all_reports.append(report)
            print(report)

    # Save complete report
    output_path = Path(__file__).parent / "codex_behavior_analysis.md"
    with open(output_path, 'w') as f:
        f.write("# RQ2 In-depth Analysis: Why doesn't Codex significantly reduce token consumption in run_free mode?\n\n")
        f.write("## Core Issues\n\n")
        f.write("- Codex run_free vs run_full token savings only 0.8-13.4%\n")
        f.write("- Claude Code savings as high as 56-62%\n")
        f.write("- This indicates fundamental differences in behavior patterns between Codex and Claude Code\n\n")
        f.write('\n\n---\n\n'.join(all_reports))

    print(f"\nReport saved to: {output_path}")


if __name__ == '__main__':
    main()
