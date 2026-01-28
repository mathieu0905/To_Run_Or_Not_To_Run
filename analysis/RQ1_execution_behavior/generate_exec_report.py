#!/usr/bin/env python3
"""
Generate RQ1 Execution Frequency Report
Only includes execution-based agents (SWE-agent, OpenHands)
Excludes pure-reasoning agents (Moatless, SuperCoder, etc.)
"""

import json
import os
import csv
import re
from pathlib import Path
from collections import defaultdict
import statistics

# Only analyze executive agent
EXEC_AGENTS = ['sweagent', 'openhands']

def is_test_command(cmd):
    """Determine if a command is a test execution"""
    if not cmd:
        return False
    cmd_lower = cmd.lower()
    patterns = ['pytest', 'py.test', 'python -m pytest', 'python -m unittest',
                'manage.py test', 'runtests.py', 'tox', 'nose']
    for p in patterns:
        if p in cmd_lower:
            return True
    # python xxx.py
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        if 'python -c' not in cmd_lower and 'python3 -c' not in cmd_lower:
            return True
    return False

def is_bash_command(action):
    """Determine if an action is a bash command"""
    if not action:
        return False
    action_lower = action.lower().strip()
    patterns = [r'^python', r'^ls\b', r'^cat\b', r'^grep\b', r'^find\b', r'^head\b', r'^tail\b',
                r'^pwd\b', r'^cd\b', r'^echo\b', r'^pip', r'^search_dir\b', r'^search_file\b',
                r'^find_file\b', r'^git\b', r'^mkdir\b', r'^rm\b', r'^mv\b', r'^cp\b', r'^curl\b', r'^wget\b']
    for p in patterns:
        if re.match(p, action_lower):
            return True
    return False

def parse_sweagent(path):
    """Parse SWE-agent format trace"""
    with open(path) as f:
        data = json.load(f)

    trajectory = data.get('trajectory', data.get('history', []))
    bash_cmds = 0
    test_execs = 0
    file_edits = 0
    file_reads = 0
    commands = []

    for item in trajectory:
        if not isinstance(item, dict):
            continue
        action = item.get('action', '')
        if not isinstance(action, str):
            continue

        action_lower = action.lower().strip()

        if is_bash_command(action):
            bash_cmds += 1
            commands.append(action[:200])
            if is_test_command(action):
                test_execs += 1
        elif action_lower.startswith('search_') or action_lower.startswith('find_'):
            bash_cmds += 1
        elif action_lower.startswith('edit ') or action_lower.startswith('create '):
            file_edits += 1
        elif action_lower.startswith('open ') or action_lower.startswith('scroll_') or action_lower.startswith('goto '):
            file_reads += 1

    return {
        'total_actions': len(trajectory),
        'bash_commands': bash_cmds,
        'test_executions': test_execs,
        'file_edits': file_edits,
        'file_reads': file_reads,
        'commands': commands
    }

def parse_openhands(path):
    """Parse OpenHands format trace"""
    with open(path) as f:
        data = json.load(f)

    if not isinstance(data, list):
        return None

    bash_cmds = 0
    test_execs = 0
    file_edits = 0
    commands = []
    total_actions = 0

    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get('role') != 'assistant':
            continue

        tool_calls = item.get('tool_calls', [])
        for tc in tool_calls:
            func = tc.get('function', {})
            func_name = func.get('name', '')
            args_str = func.get('arguments', '')

            cmd = ''
            if args_str:
                try:
                    args = json.loads(args_str)
                    cmd = args.get('command', '')
                except:
                    pass

            if func_name == 'execute_bash':
                bash_cmds += 1
                total_actions += 1
                if cmd:
                    commands.append(cmd[:200])
                    if is_test_command(cmd):
                        test_execs += 1
            elif func_name == 'str_replace_editor':
                file_edits += 1
                total_actions += 1

    return {
        'total_actions': total_actions,
        'bash_commands': bash_cmds,
        'test_executions': test_execs,
        'file_edits': file_edits,
        'file_reads': 0,
        'commands': commands
    }

def main():
    # Collect all data
    all_data = []

    for split in ['lite', 'verified']:
        split_dir = Path(f'data/traces/{split}')
        if not split_dir.exists():
            continue

        for submission_dir in sorted(split_dir.iterdir()):
            if not submission_dir.is_dir():
                continue

            name = submission_dir.name

            # Determine agent type
            agent_type = 'unknown'
            model = 'unknown'
            if 'sweagent' in name.lower():
                agent_type = 'sweagent'
                if 'gpt4o' in name.lower():
                    model = 'gpt-4o'
                elif 'gpt4' in name.lower():
                    model = 'gpt-4'
                elif 'claude3.5' in name.lower() or 'claude-3.5' in name.lower():
                    model = 'claude-3.5-sonnet'
                elif 'claude-3-7' in name.lower():
                    model = 'claude-3.7-sonnet'
            elif 'openhands' in name.lower():
                agent_type = 'openhands'
                model = 'claude-3.5-sonnet'

            # Only process execution-based agents
            if agent_type not in EXEC_AGENTS:
                continue

            trajs_dir = submission_dir / 'trajs'
            if not trajs_dir.exists():
                continue

            for trace_file in list(trajs_dir.glob('*.json')) + list(trajs_dir.glob('*.traj')):
                try:
                    # Detect format
                    with open(trace_file) as f:
                        first_char = f.read(1)

                    if first_char == '[':
                        stats = parse_openhands(trace_file)
                    else:
                        stats = parse_sweagent(trace_file)

                    if stats and stats['total_actions'] > 0:
                        all_data.append({
                            'split': split,
                            'submission': name,
                            'agent': agent_type,
                            'model': model,
                            'instance_id': trace_file.stem,
                            **stats
                        })
                except Exception as e:
                    pass

    print(f'Parsed {len(all_data)} traces from execution-based agents')
    print()

    # Aggregate by submission
    by_submission = defaultdict(list)
    for d in all_data:
        key = (d['split'], d['submission'], d['agent'], d['model'])
        by_submission[key].append(d)

    # Generate reports
    report_lines = []
    report_lines.append('# RQ1: Execution Frequency Analysis on SWE-bench')
    report_lines.append('')
    report_lines.append('## Overview')
    report_lines.append('')
    report_lines.append('This report analyzes **execution patterns** of execution-based agents on SWE-bench.')
    report_lines.append('Pure-reasoning agents (Moatless, SuperCoder, etc.) are excluded.')
    report_lines.append('')
    report_lines.append(f'**Total traces analyzed:** {len(all_data)}')
    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')

    # Summary table
    report_lines.append('## Summary by Submission')
    report_lines.append('')
    report_lines.append('| Split | Agent | Model | Instances | Avg Bash | Avg Test | Test Ratio |')
    report_lines.append('|-------|-------|-------|-----------|----------|----------|------------|')

    for key in sorted(by_submission.keys()):
        split, submission, agent, model = key
        traces = by_submission[key]

        n = len(traces)
        avg_bash = sum(t['bash_commands'] for t in traces) / n
        avg_test = sum(t['test_executions'] for t in traces) / n
        total_bash = sum(t['bash_commands'] for t in traces)
        total_test = sum(t['test_executions'] for t in traces)
        test_ratio = total_test / total_bash if total_bash > 0 else 0

        report_lines.append(f'| {split} | {agent} | {model} | {n} | {avg_bash:.1f} | {avg_test:.1f} | {test_ratio:.1%} |')

    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')

    # By agent type
    report_lines.append('## Summary by Agent Type')
    report_lines.append('')

    by_agent = defaultdict(list)
    for d in all_data:
        by_agent[d['agent']].append(d)

    report_lines.append('| Agent | Total Instances | Avg Bash/Instance | Avg Test/Instance | Test Ratio |')
    report_lines.append('|-------|-----------------|-------------------|-------------------|------------|')

    for agent in sorted(by_agent.keys()):
        traces = by_agent[agent]
        n = len(traces)
        avg_bash = sum(t['bash_commands'] for t in traces) / n
        avg_test = sum(t['test_executions'] for t in traces) / n
        total_bash = sum(t['bash_commands'] for t in traces)
        total_test = sum(t['test_executions'] for t in traces)
        test_ratio = total_test / total_bash if total_bash > 0 else 0

        report_lines.append(f'| {agent} | {n} | {avg_bash:.1f} | {avg_test:.1f} | {test_ratio:.1%} |')

    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')

    # By model
    report_lines.append('## Summary by Model')
    report_lines.append('')

    by_model = defaultdict(list)
    for d in all_data:
        by_model[d['model']].append(d)

    report_lines.append('| Model | Total Instances | Avg Bash/Instance | Avg Test/Instance | Test Ratio |')
    report_lines.append('|-------|-----------------|-------------------|-------------------|------------|')

    for model in sorted(by_model.keys()):
        traces = by_model[model]
        n = len(traces)
        avg_bash = sum(t['bash_commands'] for t in traces) / n
        avg_test = sum(t['test_executions'] for t in traces) / n
        total_bash = sum(t['bash_commands'] for t in traces)
        total_test = sum(t['test_executions'] for t in traces)
        test_ratio = total_test / total_bash if total_bash > 0 else 0

        report_lines.append(f'| {model} | {n} | {avg_bash:.1f} | {avg_test:.1f} | {test_ratio:.1%} |')

    report_lines.append('')
    report_lines.append('---')
    report_lines.append('')

    # Distribution stats
    report_lines.append('## Distribution Statistics')
    report_lines.append('')

    bash_counts = [d['bash_commands'] for d in all_data]
    test_counts = [d['test_executions'] for d in all_data]

    report_lines.append('### Bash Commands per Instance')
    report_lines.append('')
    report_lines.append(f'- **Min:** {min(bash_counts)}')
    report_lines.append(f'- **Max:** {max(bash_counts)}')
    report_lines.append(f'- **Mean:** {statistics.mean(bash_counts):.1f}')
    report_lines.append(f'- **Median:** {statistics.median(bash_counts):.1f}')
    report_lines.append(f'- **Std Dev:** {statistics.stdev(bash_counts):.1f}')
    report_lines.append('')

    report_lines.append('### Test Executions per Instance')
    report_lines.append('')
    report_lines.append(f'- **Min:** {min(test_counts)}')
    report_lines.append(f'- **Max:** {max(test_counts)}')
    report_lines.append(f'- **Mean:** {statistics.mean(test_counts):.1f}')
    report_lines.append(f'- **Median:** {statistics.median(test_counts):.1f}')
    report_lines.append(f'- **Std Dev:** {statistics.stdev(test_counts):.1f}')
    report_lines.append('')

    # Key findings
    report_lines.append('---')
    report_lines.append('')
    report_lines.append('## Key Findings')
    report_lines.append('')

    # Calculate overall stats
    total_bash = sum(d['bash_commands'] for d in all_data)
    total_test = sum(d['test_executions'] for d in all_data)
    overall_ratio = total_test / total_bash if total_bash > 0 else 0

    report_lines.append(f'1. **Overall Test Execution Ratio:** {overall_ratio:.1%} of bash commands are test executions')
    report_lines.append('')
    report_lines.append(f'2. **Average Bash Commands:** {statistics.mean(bash_counts):.1f} per instance')
    report_lines.append('')
    report_lines.append(f'3. **Average Test Executions:** {statistics.mean(test_counts):.1f} per instance')
    report_lines.append('')

    # Agent comparison
    sweagent_data = by_agent.get('sweagent', [])
    openhands_data = by_agent.get('openhands', [])

    if sweagent_data:
        sw_bash = sum(d['bash_commands'] for d in sweagent_data)
        sw_test = sum(d['test_executions'] for d in sweagent_data)
        sw_ratio = sw_test / sw_bash if sw_bash > 0 else 0
        report_lines.append(f'4. **SWE-agent:** {sw_ratio:.1%} test ratio ({len(sweagent_data)} instances)')

    if openhands_data:
        oh_bash = sum(d['bash_commands'] for d in openhands_data)
        oh_test = sum(d['test_executions'] for d in openhands_data)
        oh_ratio = oh_test / oh_bash if oh_bash > 0 else 0
        report_lines.append(f'5. **OpenHands:** {oh_ratio:.1%} test ratio ({len(openhands_data)} instances)')

    report_lines.append('')

    # Save report
    output_dir = Path('results_all')
    output_dir.mkdir(exist_ok=True)

    report_path = output_dir / 'rq1_execution_analysis.md'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    print(f'Report saved to: {report_path}')

    # Save CSV
    csv_path = output_dir / 'rq1_execution_stats.csv'
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['split', 'submission', 'agent', 'model', 'instance_id',
                                                'total_actions', 'bash_commands', 'test_executions',
                                                'file_edits', 'file_reads'])
        writer.writeheader()
        for d in all_data:
            row = {k: v for k, v in d.items() if k != 'commands'}
            writer.writerow(row)
    print(f'CSV saved to: {csv_path}')

    # Print report to console
    print()
    print('\n'.join(report_lines))

if __name__ == '__main__':
    main()
