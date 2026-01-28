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
class ExecutionRecord:
    """Record for a single execution"""
    position: float  # Normalized 0-1
    intent: str      # test, debug, explore, env, other
    success: bool    # True if success, False if error
    error_type: Optional[str] = None


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

    # Detailed execution records for position vs results analysis
    execution_records: List[ExecutionRecord] = field(default_factory=list)


def is_test_execution(cmd: str) -> bool:
    """Check if command is a test execution (as defined in the paper)"""
    cmd_lower = cmd.lower().strip()

    # Test framework invocations
    test_patterns = [
        r'\bpytest\b',
        r'\bpy\.test\b',
        r'python[3]?\s+-m\s+pytest',
        r'python[3]?\s+-m\s+unittest',
        r'manage\.py\s+test',
        r'\btox\b',
        r'\bnosetests?\b',
    ]

    for pattern in test_patterns:
        if re.search(pattern, cmd_lower):
            return True

    # Python script execution (python xxx.py), excluding python -c
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        if not re.search(r'python[3]?\s+-c\s', cmd_lower):
            return True

    return False


def classify_intent(cmd: str) -> str:
    """Classify command intent - simplified for test executions only"""
    if is_test_execution(cmd):
        return 'test'
    return 'other'


def classify_test_result(content: str) -> tuple:
    """
    Classify test execution result.
    Returns: (is_failure: bool, error_type: Optional[str])

    Test Success indicators:
    - pytest: "passed", "X passed", no "FAILED"
    - unittest: "OK", "Ran X tests"
    - return code 0

    Test Failure indicators:
    - pytest: "FAILED", "ERROR", "error"
    - unittest: "FAILED", "ERROR"
    - Python exceptions before test runs
    - return code != 0
    """
    content_lower = content.lower()

    # Check for explicit test failures first
    # pytest failure patterns
    if 'FAILED' in content or 'failed' in content_lower:
        if 'passed' in content_lower and 'failed' not in content_lower:
            pass  # "X passed" without "failed" is success
        else:
            return (True, 'TestFailure')

    # pytest/unittest error (test collection error, setup error)
    if ' error ' in content_lower or 'ERROR' in content:
        # But not "0 errors" or "no errors"
        if not ('0 error' in content_lower or 'no error' in content_lower):
            return (True, 'TestError')

    # Python exceptions that prevent tests from running
    exception_types = [
        ('ModuleNotFoundError', 'ModuleNotFoundError'),
        ('ImportError', 'ImportError'),
        ('SyntaxError', 'SyntaxError'),
        ('FileNotFoundError', 'FileNotFoundError'),
        ('No such file', 'FileNotFoundError'),
        ('NameError', 'NameError'),
        ('AttributeError', 'AttributeError'),
        ('TypeError', 'TypeError'),
        ('ValueError', 'ValueError'),
        ('KeyError', 'KeyError'),
        ('IndexError', 'IndexError'),
    ]

    for pattern, error_type in exception_types:
        if pattern in content:
            return (True, error_type)

    # AssertionError in traceback (test assertion failed)
    if 'AssertionError' in content:
        return (True, 'AssertionError')

    # Generic traceback without specific error
    if 'Traceback (most recent call last)' in content:
        return (True, 'OtherError')

    # Check for success indicators
    # pytest success: "X passed" without failures
    if 'passed' in content_lower and 'failed' not in content_lower:
        return (False, None)

    # unittest success: "OK"
    if content.strip().endswith('OK') or '\nOK\n' in content or '\nOK' in content:
        return (False, None)

    # Return code 0 (for LiveSWEAgent format)
    if '<returncode>0</returncode>' in content:
        return (False, None)

    # Return code non-zero
    if '<returncode>' in content and '<returncode>0</returncode>' not in content:
        return (True, 'NonZeroExit')

    # Default: if no clear failure indicators, consider it success
    # (This handles cases where output is truncated or minimal)
    return (False, None)


def analyze_openhands_trace(data: list, instance_id: str) -> ExecutionStats:
    """Analyze OpenHands format trace - only count test executions"""
    stats = ExecutionStats(instance_id=instance_id)
    stats.error_types = defaultdict(int)

    total_items = len(data)
    pending_exec = None  # Store (position, cmd) for pending execution

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        role = item.get('role', '')
        source = item.get('source', '')
        action = item.get('action', '')

        # Count turns
        if role == 'assistant' or source == 'agent':
            stats.total_turns += 1

        cmd = ''

        # Old format: role=assistant with tool_calls
        if role == 'assistant':
            tool_calls = item.get('tool_calls', [])
            for tc in tool_calls:
                func = tc.get('function', {})
                if func.get('name') == 'execute_bash':
                    args_str = func.get('arguments', '')
                    try:
                        args = json.loads(args_str) if isinstance(args_str, str) else args_str
                        cmd = args.get('command', '') if isinstance(args, dict) else ''
                    except:
                        cmd = ''

                    # Only count test executions
                    if is_test_execution(cmd):
                        stats.total_executions += 1
                        position = i / max(total_items, 1)
                        stats.execution_positions.append(position)
                        stats.intent_test += 1
                        pending_exec = (position, cmd)

        # New format: source=agent with action=run
        if source == 'agent' and action == 'run':
            args = item.get('args', {})
            cmd = args.get('command', '') if isinstance(args, dict) else ''

            # Only count test executions
            if is_test_execution(cmd):
                stats.total_executions += 1
                position = i / max(total_items, 1)
                stats.execution_positions.append(position)
                stats.intent_test += 1
                pending_exec = (position, cmd)

        # Check execution results (tool response) - ONLY if we have a pending execution
        is_result = (
            (role == 'tool') or
            (source == 'environment') or
            (source == 'agent' and not action and item.get('observation'))
        )

        if pending_exec and is_result:
            content = str(item.get('content', ''))
            if len(content) < 10:
                content = str(item.get('observation', ''))

            is_failure, error_type = classify_test_result(content)
            if is_failure:
                stats.result_error += 1
                if error_type:
                    stats.error_types[error_type] += 1
                stats.execution_records.append(ExecutionRecord(
                    position=pending_exec[0],
                    intent='test',
                    success=False,
                    error_type=error_type
                ))
            else:
                stats.result_success += 1
                stats.execution_records.append(ExecutionRecord(
                    position=pending_exec[0],
                    intent='test',
                    success=True
                ))

            pending_exec = None

    return stats


def analyze_sweagent_trace(data: dict, instance_id: str) -> ExecutionStats:
    """Analyze SWE-agent format trace - only count test executions"""
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
        cmd = action.strip()

        # Only count test executions (pytest, unittest, tox, python xxx.py)
        if is_test_execution(cmd):
            stats.total_executions += 1
            position = i / max(total_items, 1)
            stats.execution_positions.append(position)
            stats.intent_test += 1

            # Check result from observation
            is_failure, error_type = classify_test_result(observation)
            if is_failure:
                stats.result_error += 1
                if error_type:
                    stats.error_types[error_type] += 1
                stats.execution_records.append(ExecutionRecord(
                    position=position,
                    intent='test',
                    success=False,
                    error_type=error_type
                ))
            else:
                stats.result_success += 1
                stats.execution_records.append(ExecutionRecord(
                    position=position,
                    intent='test',
                    success=True
                ))

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
    """Analyze LiveSWEAgent format trace - only count test executions"""
    stats = ExecutionStats(instance_id=instance_id)
    stats.error_types = defaultdict(int)

    messages = data.get('messages', [])
    total_items = len(messages)

    pending_exec = None  # Store (position, cmd) for pending execution

    for i, msg in enumerate(messages):
        if not isinstance(msg, dict):
            continue

        role = msg.get('role', '')
        content = msg.get('content', '')

        if role == 'assistant':
            stats.total_turns += 1
            # Extract bash command from content (between ```bash and ```)
            if '```bash' in content or '```' in content:
                bash_match = re.search(r'```(?:bash)?\s*\n([^`]+)\n```', content)
                if bash_match:
                    cmd = bash_match.group(1).strip()

                    # Only count test executions
                    if is_test_execution(cmd):
                        stats.total_executions += 1
                        position = i / max(total_items, 1)
                        stats.execution_positions.append(position)
                        stats.intent_test += 1
                        pending_exec = (position, cmd)

        elif role == 'user' and '<returncode>' in content and pending_exec:
            # Check execution result using the new classifier
            is_failure, error_type = classify_test_result(content)
            if is_failure:
                stats.result_error += 1
                if error_type:
                    stats.error_types[error_type] += 1
                stats.execution_records.append(ExecutionRecord(
                    position=pending_exec[0],
                    intent='test',
                    success=False,
                    error_type=error_type
                ))
            else:
                stats.result_success += 1
                stats.execution_records.append(ExecutionRecord(
                    position=pending_exec[0],
                    intent='test',
                    success=True
                ))
            pending_exec = None

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

        # Result analysis
        result_success = sum(s.result_success for s in submission_stats)
        result_error = sum(s.result_error for s in submission_stats)

        # Error types
        error_types = defaultdict(int)
        for s in submission_stats:
            for et, count in s.error_types.items():
                error_types[et] += count

        print(f"  Traces analyzed: {len(submission_stats)}")
        print(f"  Total test executions: {total_execs}")
        print(f"  Avg test executions/task: {total_execs / len(submission_stats):.1f}")

        print(f"\n  === Execution Position (when test executions occur) ===")
        print(f"  Early (0-33%): {early} ({early/max(total_pos,1)*100:.1f}%)")
        print(f"  Middle (33-66%): {middle} ({middle/max(total_pos,1)*100:.1f}%)")
        print(f"  Late (66-100%): {late} ({late/max(total_pos,1)*100:.1f}%)")

        print(f"\n  === Execution Results ===")
        print(f"  Success: {result_success} ({result_success/max(result_success+result_error,1)*100:.1f}%)")
        print(f"  Error: {result_error} ({result_error/max(result_success+result_error,1)*100:.1f}%)")

        print(f"\n  === Error Types ===")
        for et, count in sorted(error_types.items(), key=lambda x: -x[1])[:5]:
            print(f"  {et}: {count}")

        # Position vs Results analysis
        print(f"\n  === Position vs Results ===")
        all_records = []
        for s in submission_stats:
            all_records.extend(s.execution_records)

        if all_records:
            # Group by position
            early_records = [r for r in all_records if r.position < 0.33]
            middle_records = [r for r in all_records if 0.33 <= r.position < 0.66]
            late_records = [r for r in all_records if r.position >= 0.66]

            for label, records in [("Early (0-33%)", early_records),
                                   ("Middle (33-66%)", middle_records),
                                   ("Late (66-100%)", late_records)]:
                if records:
                    success_count = sum(1 for r in records if r.success)
                    error_count = len(records) - success_count
                    success_rate = success_count / len(records) * 100
                    print(f"  {label}: {len(records)} execs, Success {success_rate:.1f}%, Error {100-success_rate:.1f}%")
                else:
                    print(f"  {label}: 0 execs")


if __name__ == '__main__':
    main()
