#!/usr/bin/env python3
"""
RQ1 Detailed Analysis: Execution Distribution, Intent, and Results
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict
import statistics

@dataclass
class ExecutionStats:
    """Statistics for a single trace"""
    instance_id: str
    total_turns: int = 0
    total_executions: int = 0
    execution_positions: List[float] = field(default_factory=list)  # Normalized 0-1

    # Intent categories
    intent_test: int = 0       # pytest, unittest, python script.py
    intent_debug: int = 0      # python -c with print, debug scripts
    intent_explore: int = 0    # ls, cat, grep, find, head, tail
    intent_env: int = 0        # pip, git, cd, pwd
    intent_other: int = 0

    # Execution results
    result_success: int = 0
    result_error: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)


def classify_intent(cmd: str) -> str:
    """Classify command intent"""
    cmd_lower = cmd.lower()

    # Test execution
    if any(x in cmd_lower for x in ['pytest', 'python -m pytest', 'unittest', 'python -m unittest',
                                      'python manage.py test', 'tox', 'nosetests']):
        return 'test'

    # Running a python script (likely test)
    if re.search(r'python\s+[\w_/]+\.py', cmd_lower):
        return 'test'

    # Debug/exploration with python -c
    if 'python -c' in cmd_lower or 'python3 -c' in cmd_lower:
        return 'debug'

    # File exploration
    if any(cmd_lower.startswith(x) or f' {x} ' in cmd_lower or cmd_lower.startswith(f'cd ') and x in cmd_lower
           for x in ['ls', 'cat', 'grep', 'find', 'head', 'tail', 'wc', 'tree']):
        return 'explore'

    # Environment commands
    if any(x in cmd_lower for x in ['pip ', 'git ', 'cd ', 'pwd', 'which ', 'echo $']):
        return 'env'

    return 'other'


def classify_error(content: str) -> Optional[str]:
    """Classify error type from execution output"""
    if 'ModuleNotFoundError' in content:
        return 'ModuleNotFoundError'
    elif 'ImportError' in content:
        return 'ImportError'
    elif 'SyntaxError' in content:
        return 'SyntaxError'
    elif 'AttributeError' in content:
        return 'AttributeError'
    elif 'TypeError' in content:
        return 'TypeError'
    elif 'NameError' in content:
        return 'NameError'
    elif 'ValueError' in content:
        return 'ValueError'
    elif 'KeyError' in content:
        return 'KeyError'
    elif 'IndexError' in content:
        return 'IndexError'
    elif 'FileNotFoundError' in content or 'No such file' in content:
        return 'FileNotFoundError'
    elif 'AssertionError' in content:
        return 'AssertionError'
    elif 'FAILED' in content or 'ERRORS' in content:
        return 'TestFailure'
    elif 'Traceback' in content or 'Error' in content:
        return 'OtherError'
    return None


def analyze_openhands_trace(data: list, instance_id: str) -> ExecutionStats:
    """Analyze OpenHands format trace"""
    stats = ExecutionStats(instance_id=instance_id)
    stats.error_types = defaultdict(int)

    total_items = len(data)
    exec_positions = []
    pending_exec = None

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        role = item.get('role', '')
        source = item.get('source', '')
        action = item.get('action', '')

        # Count turns
        if role == 'assistant' or source == 'agent':
            stats.total_turns += 1

        # Old format: role=assistant with tool_calls
        if role == 'assistant':
            tool_calls = item.get('tool_calls', [])
            for tc in tool_calls:
                func = tc.get('function', {})
                if func.get('name') == 'execute_bash':
                    stats.total_executions += 1
                    exec_positions.append(i / max(total_items, 1))

                    # Get command for intent classification
                    args_str = func.get('arguments', '')
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                        cmd = args.get('command', '') if isinstance(args, dict) else ''
                    except:
                        cmd = ''

                    intent = classify_intent(cmd)
                    if intent == 'test':
                        stats.intent_test += 1
                    elif intent == 'debug':
                        stats.intent_debug += 1
                    elif intent == 'explore':
                        stats.intent_explore += 1
                    elif intent == 'env':
                        stats.intent_env += 1
                    else:
                        stats.intent_other += 1

                    pending_exec = True

        # New format: source=agent with action=run
        if source == 'agent' and action == 'run':
            stats.total_executions += 1
            exec_positions.append(i / max(total_items, 1))

            args = item.get('args', {})
            cmd = args.get('command', '') if isinstance(args, dict) else ''

            intent = classify_intent(cmd)
            if intent == 'test':
                stats.intent_test += 1
            elif intent == 'debug':
                stats.intent_debug += 1
            elif intent == 'explore':
                stats.intent_explore += 1
            elif intent == 'env':
                stats.intent_env += 1
            else:
                stats.intent_other += 1

            pending_exec = True

        # Check execution results (tool response) - ONLY if we have a pending execution
        # Support multiple formats:
        # 1. role=tool (old OpenHands)
        # 2. source=environment (some OpenHands)
        # 3. source=agent with observation but no action (Qwen3 format)
        is_result = (
            (role == 'tool') or
            (source == 'environment') or
            (source == 'agent' and not action and item.get('observation'))
        )

        if pending_exec and is_result:
            content = str(item.get('content', ''))
            if len(content) < 10:
                content = str(item.get('observation', ''))

            error_type = classify_error(content)
            if error_type:
                stats.result_error += 1
                stats.error_types[error_type] += 1
            else:
                stats.result_success += 1

            pending_exec = False

    stats.execution_positions = exec_positions
    return stats


def analyze_sweagent_trace(data: dict, instance_id: str) -> ExecutionStats:
    """Analyze SWE-agent format trace"""
    stats = ExecutionStats(instance_id=instance_id)
    stats.error_types = defaultdict(int)

    # SWE-agent uses 'trajectory' list with action/observation pairs
    trajectory = data.get('trajectory', [])
    if not trajectory:
        trajectory = data.get('history', [])

    total_items = len(trajectory)

    for i, step in enumerate(trajectory):
        if not isinstance(step, dict):
            continue

        stats.total_turns += 1
        action = step.get('action', '')
        observation = step.get('observation', '')

        # Check if this is a bash/python execution
        is_execution = False
        cmd = action.strip()

        # SWE-agent commands that are executions
        if cmd.startswith('python ') or cmd.startswith('python3 '):
            is_execution = True
        elif 'pytest' in cmd or 'unittest' in cmd:
            is_execution = True
        elif cmd.startswith('pip ') or cmd.startswith('git '):
            is_execution = True
            stats.intent_env += 1
        elif any(cmd.startswith(x) for x in ['ls', 'cat ', 'grep ', 'find ', 'head ', 'tail ', 'wc ']):
            is_execution = True
            stats.intent_explore += 1
        elif cmd.startswith('cd ') or cmd.startswith('pwd'):
            is_execution = True
            stats.intent_env += 1

        if is_execution:
            stats.total_executions += 1
            stats.execution_positions.append(i / max(total_items, 1))

            # Classify intent if not already done
            if not any([stats.intent_explore, stats.intent_env]):
                intent = classify_intent(cmd)
                if intent == 'test':
                    stats.intent_test += 1
                elif intent == 'debug':
                    stats.intent_debug += 1
                elif intent == 'explore':
                    stats.intent_explore += 1
                elif intent == 'env':
                    stats.intent_env += 1
                else:
                    stats.intent_other += 1

            # Check result from observation
            error_type = classify_error(observation)
            if error_type:
                stats.result_error += 1
                stats.error_types[error_type] += 1
            else:
                stats.result_success += 1

    return stats


def analyze_trace_file(trace_path: Path) -> Optional[ExecutionStats]:
    """Analyze a single trace file"""
    instance_id = trace_path.stem.replace('.traj', '')
    if trace_path.parent.name != 'trajs':
        instance_id = trace_path.parent.name  # For nested structure

    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        return None

    if isinstance(data, list):
        return analyze_openhands_trace(data, instance_id)
    elif isinstance(data, dict):
        # LiveSWEAgent format has 'messages' key
        if 'messages' in data:
            return analyze_livesweagent_trace(data, instance_id)
        # SWE-agent format has 'trajectory' key
        if 'trajectory' in data:
            return analyze_sweagent_trace(data, instance_id)
        return analyze_sweagent_trace(data, instance_id)

    return None


def analyze_livesweagent_trace(data: dict, instance_id: str) -> ExecutionStats:
    """Analyze LiveSWEAgent format trace (messages array)"""
    stats = ExecutionStats(instance_id=instance_id)
    stats.error_types = defaultdict(int)

    messages = data.get('messages', [])
    total_items = len(messages)

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue

        role = msg.get('role', '')
        content = msg.get('content', '')

        if role == 'assistant':
            stats.total_turns += 1
            # Extract bash command from content (between ```bash and ```)
            if '```bash' in content or '```' in content:
                # Find command in code block
                import re
                bash_match = re.search(r'```(?:bash)?\s*\n([^`]+)\n```', content)
                if bash_match:
                    cmd = bash_match.group(1).strip()
                    stats.total_executions += 1
                    stats.execution_positions.append(i / max(total_items, 1))

                    intent = classify_intent(cmd)
                    if intent == 'test':
                        stats.intent_test += 1
                    elif intent == 'debug':
                        stats.intent_debug += 1
                    elif intent == 'explore':
                        stats.intent_explore += 1
                    elif intent == 'env':
                        stats.intent_env += 1
                    else:
                        stats.intent_other += 1

        elif role == 'user' and '<returncode>' in content:
            # Check execution result
            if '<returncode>0</returncode>' in content:
                stats.result_success += 1
            else:
                stats.result_error += 1
                # Classify error
                error_type = classify_error(content)
                if error_type:
                    stats.error_types[error_type] += 1

    return stats


def main():
    data_dir = Path('/home/zhihao/hdd/run_free_run_less_run_full/analysis/RQ_trace/data/traces')

    all_stats = []

    # Analyze all 15 combinations from the paper (12 original + 3 new)
    submissions = [
        # SWE-bench Lite (4 combinations)
        ('lite', '20240402_sweagent_gpt4', 'SWE-agent', 'GPT-4'),
        ('lite', '20240620_sweagent_claude3.5sonnet', 'SWE-agent', 'Claude-3.5-Sonnet'),
        ('lite', '20240728_sweagent_gpt4o', 'SWE-agent', 'GPT-4o'),
        ('lite', '20241025_OpenHands-CodeAct-2.1-sonnet-20241022', 'OpenHands', 'Claude-3.5-Sonnet'),
        # SWE-bench Verified (11 combinations)
        ('verified', '20240402_sweagent_gpt4', 'SWE-agent', 'GPT-4'),
        ('verified', '20240402_sweagent_claude3opus', 'SWE-agent', 'Claude-3-Opus'),
        ('verified', '20240620_sweagent_claude3.5sonnet', 'SWE-agent', 'Claude-3.5-Sonnet'),
        ('verified', '20240728_sweagent_gpt4o', 'SWE-agent', 'GPT-4o'),
        ('verified', '20241029_OpenHands-CodeAct-2.1-sonnet-20241022', 'OpenHands', 'Claude-3.5-Sonnet'),
        ('verified', '20250524_openhands_claude_4_sonnet', 'OpenHands', 'Claude-4-Sonnet'),
        ('verified', '20250716_openhands_kimi_k2', 'OpenHands', 'Kimi-K2'),
        ('verified', '20250805_openhands_qwen3_480b', 'OpenHands', 'Qwen3-480B'),
        ('verified', '20250807_openhands_gpt5', 'OpenHands', 'GPT-5'),
        # New additions
        ('verified', '20251127_openhands_claude-opus-4-5', 'OpenHands', 'Claude-Opus-4.5'),
        ('verified', '20251120_livesweagent_gemini-3-pro-preview', 'LiveSWEAgent', 'Gemini-3-Pro'),
        ('verified', '20251215_livesweagent_claude-opus-4-5', 'LiveSWEAgent', 'Claude-Opus-4.5'),
        # Mini-SWE-agent submissions (uses same format as LiveSWEAgent)
        ('verified', '20251124_mini-v1.16.0_claude-opus-4-5-20251101', 'Mini-SWE-agent', 'Claude-Opus-4.5'),
        ('verified', '20251118_mini-v1.15.0_gemini-3-pro-preview-20251118', 'Mini-SWE-agent', 'Gemini-3-Pro'),
        ('verified', '20251201_mini-v1.17.1_deepseek-v3.2-reasoner', 'Mini-SWE-agent', 'DeepSeek-V3.2'),
        ('verified', '20251211_mini-v1.17.2_gpt-5.2-2025-12-11', 'Mini-SWE-agent', 'GPT-5.2'),
    ]

    for dataset, submission, agent_name, model_name in submissions:
        submission_dir = data_dir / dataset / submission / 'trajs'
        if not submission_dir.exists():
            print(f"Skipping {agent_name} + {model_name} ({dataset}) - not found")
            continue

        print(f"\n{'='*60}")
        print(f"Analyzing {agent_name} + {model_name} ({dataset})...")
        print(f"{'='*60}")

        # Find trace files (support multiple formats)
        trace_files = list(submission_dir.glob('*.json'))  # OpenHands flat
        trace_files.extend(list(submission_dir.glob('*.traj')))  # SWE-agent .traj
        # Always check nested structures too
        trace_files.extend(list(submission_dir.glob('*/trajectory.json')))  # Qwen3 format
        trace_files.extend(list(submission_dir.glob('*/*.traj.json')))  # Mini-SWE-agent, LiveSWEAgent
        if not trace_files:
            # Fallback: any json in nested dirs
            trace_files.extend(list(submission_dir.glob('*/*.json')))

        submission_stats = []
        for tf in trace_files:  # Analyze all traces
            stats = analyze_trace_file(tf)
            if stats and stats.total_executions > 0:
                submission_stats.append(stats)

        if not submission_stats:
            print(f"  No valid traces")
            continue

        # Aggregate statistics
        total_execs = sum(s.total_executions for s in submission_stats)

        # Distribution analysis
        all_positions = []
        for s in submission_stats:
            all_positions.extend(s.execution_positions)

        early = sum(1 for p in all_positions if p < 0.33)
        middle = sum(1 for p in all_positions if 0.33 <= p < 0.66)
        late = sum(1 for p in all_positions if p >= 0.66)
        total_pos = len(all_positions)

        # Intent analysis
        intent_test = sum(s.intent_test for s in submission_stats)
        intent_debug = sum(s.intent_debug for s in submission_stats)
        intent_explore = sum(s.intent_explore for s in submission_stats)
        intent_env = sum(s.intent_env for s in submission_stats)
        intent_other = sum(s.intent_other for s in submission_stats)

        # Result analysis
        result_success = sum(s.result_success for s in submission_stats)
        result_error = sum(s.result_error for s in submission_stats)

        # Error types
        error_types = defaultdict(int)
        for s in submission_stats:
            for et, count in s.error_types.items():
                error_types[et] += count

        print(f"  Traces analyzed: {len(submission_stats)}")
        print(f"  Total executions: {total_execs}")
        print(f"  Avg executions/task: {total_execs / len(submission_stats):.1f}")

        print(f"\n  === Distribution (when executions occur) ===")
        print(f"  Early (0-33%): {early} ({early/max(total_pos,1)*100:.1f}%)")
        print(f"  Middle (33-66%): {middle} ({middle/max(total_pos,1)*100:.1f}%)")
        print(f"  Late (66-100%): {late} ({late/max(total_pos,1)*100:.1f}%)")

        print(f"\n  === Intent (why executions occur) ===")
        print(f"  Test: {intent_test} ({intent_test/max(total_execs,1)*100:.1f}%)")
        print(f"  Debug: {intent_debug} ({intent_debug/max(total_execs,1)*100:.1f}%)")
        print(f"  Explore: {intent_explore} ({intent_explore/max(total_execs,1)*100:.1f}%)")
        print(f"  Environment: {intent_env} ({intent_env/max(total_execs,1)*100:.1f}%)")
        print(f"  Other: {intent_other} ({intent_other/max(total_execs,1)*100:.1f}%)")

        print(f"\n  === Results (execution outcomes) ===")
        print(f"  Success: {result_success} ({result_success/max(result_success+result_error,1)*100:.1f}%)")
        print(f"  Error: {result_error} ({result_error/max(result_success+result_error,1)*100:.1f}%)")

        print(f"\n  === Error Types ===")
        for et, count in sorted(error_types.items(), key=lambda x: -x[1])[:5]:
            print(f"  {et}: {count}")


if __name__ == '__main__':
    main()
