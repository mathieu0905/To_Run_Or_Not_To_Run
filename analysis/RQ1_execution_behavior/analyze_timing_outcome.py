#!/usr/bin/env python3
"""
分析 timing 和 outcome 的关系

对于每次 test execution，记录：
1. timing: 在对话中的位置 (Early 0-33%, Middle 33-66%, Late 66-100%)
2. outcome: 执行结果 (Success/Failure)

输出：每个 agent-model 组合在 Early/Middle/Late 的成功率
"""

import json
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics
import csv


@dataclass
class ExecutionRecord:
    """单次执行的记录"""
    command: str
    position: float  # 0.0-1.0，在对话中的位置
    timing: str  # Early, Middle, Late
    outcome: str  # Success, Failure
    output_preview: str = ""


@dataclass
class TraceAnalysis:
    """单个 trace 的分析结果"""
    instance_id: str
    submission: str
    agent_type: str
    model: str
    dataset: str
    executions: List[ExecutionRecord] = field(default_factory=list)


def extract_agent_model(submission_name: str) -> Tuple[str, str]:
    """从 submission name 提取 agent 和 model"""
    name = submission_name

    # 移除日期前缀
    if re.match(r'^\d{8}_', name):
        name = name[9:]

    # 特定的映射
    mappings = [
        (r'sweagent_gpt4$', 'SWE-agent', 'GPT-4'),
        (r'sweagent_gpt4o', 'SWE-agent', 'GPT-4o'),
        (r'sweagent_claude3opus', 'SWE-agent', 'Claude-3-Opus'),
        (r'sweagent_claude3\.5sonnet', 'SWE-agent', 'Claude-3.5-Sonnet'),
        (r'OpenHands.*sonnet.*20241022', 'OpenHands', 'Claude-3.5-Sonnet'),
        (r'openhands_claude_4_sonnet', 'OpenHands', 'Claude-4-Sonnet'),
        (r'openhands_kimi_k2', 'OpenHands', 'Kimi-K2'),
        (r'openhands_qwen3', 'OpenHands', 'Qwen3-480B'),
        (r'openhands_gpt5$', 'OpenHands', 'GPT-5'),
        (r'openhands$', 'OpenHands', 'Unknown'),
        (r'LiveSWEAgent.*gemini.*pro', 'LiveSWEAgent', 'Gemini-3-Pro'),
        (r'LiveSWEAgent.*claude.*opus', 'LiveSWEAgent', 'Claude-Opus-4.5'),
        (r'mini.*swe.*agent.*claude.*opus', 'Mini-SWE-agent', 'Claude-Opus-4.5'),
        (r'mini.*swe.*agent.*gemini', 'Mini-SWE-agent', 'Gemini-3-Pro'),
        (r'mini.*swe.*agent.*deepseek', 'Mini-SWE-agent', 'DeepSeek-V3.2'),
        (r'mini.*swe.*agent.*gpt.*5\.2', 'Mini-SWE-agent', 'GPT-5.2'),
    ]

    for pattern, agent, model in mappings:
        if re.search(pattern, submission_name, re.IGNORECASE):
            return agent, model

    return 'Other', 'Unknown'


def is_test_command(command: str) -> bool:
    """判断是否是测试执行命令"""
    if not command:
        return False

    cmd_lower = command.lower().strip()

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

    # Python script execution
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        if not re.search(r'python[3]?\s+-c\s', cmd_lower):
            return True

    return False


def classify_outcome(content: str) -> str:
    """根据输出判断执行结果 - 使用与 analyze_rq1_detailed.py 相同的逻辑"""
    if not content:
        return "Failure"

    content_lower = content.lower()

    # Check for explicit test failures first
    # pytest failure patterns
    if 'FAILED' in content or 'failed' in content_lower:
        if 'passed' in content_lower and 'failed' not in content_lower:
            pass  # "X passed" without "failed" is success
        else:
            return "Failure"

    # pytest/unittest error (test collection error, setup error)
    if ' error ' in content_lower or 'ERROR' in content:
        # But not "0 errors" or "no errors"
        if not ('0 error' in content_lower or 'no error' in content_lower):
            return "Failure"

    # Python exceptions that prevent tests from running
    exception_types = [
        'ModuleNotFoundError',
        'ImportError',
        'SyntaxError',
        'FileNotFoundError',
        'No such file',
        'NameError',
        'AttributeError',
        'TypeError',
        'ValueError',
        'KeyError',
        'IndexError',
    ]

    for pattern in exception_types:
        if pattern in content:
            return "Failure"

    # AssertionError in traceback (test assertion failed)
    if 'AssertionError' in content:
        return "Failure"

    # Generic traceback without specific error
    if 'Traceback (most recent call last)' in content:
        return "Failure"

    # Check for success indicators
    # pytest success: "X passed" without failures
    if 'passed' in content_lower and 'failed' not in content_lower:
        return "Success"

    # unittest success: "OK"
    if content.strip().endswith('OK') or '\nOK\n' in content or '\nOK' in content:
        return "Success"

    # Return code 0 (for some formats)
    if '<returncode>0</returncode>' in content:
        return "Success"
    if 'exit code 0' in content_lower:
        return "Success"

    # Return code non-zero
    if '<returncode>' in content and '<returncode>0</returncode>' not in content:
        return "Failure"

    # Default: if no clear failure indicators, consider it success
    return "Success"


def get_timing_category(position: float) -> str:
    """根据位置返回 timing 类别"""
    if position < 0.33:
        return "Early"
    elif position < 0.66:
        return "Middle"
    else:
        return "Late"


def parse_sweagent_trace(data: dict, instance_id: str, submission: str, dataset: str) -> Optional[TraceAnalysis]:
    """解析 SWE-agent 格式的 trace"""
    agent_type, model = extract_agent_model(submission)
    analysis = TraceAnalysis(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model,
        dataset=dataset
    )

    trajectory = data.get("trajectory", data.get("history", []))
    total_steps = len(trajectory)

    if total_steps == 0:
        return analysis

    for i, item in enumerate(trajectory):
        if not isinstance(item, dict):
            continue

        action = item.get("action", "")
        observation = item.get("observation", "")

        if not isinstance(action, str):
            continue

        if is_test_command(action):
            position = i / total_steps
            timing = get_timing_category(position)
            outcome = classify_outcome(observation)

            analysis.executions.append(ExecutionRecord(
                command=action[:200],
                position=position,
                timing=timing,
                outcome=outcome,
                output_preview=observation[:500] if observation else ""
            ))

    return analysis


def parse_openhands_trace(data: list, instance_id: str, submission: str, dataset: str) -> Optional[TraceAnalysis]:
    """解析 OpenHands 格式的 trace"""
    agent_type, model = extract_agent_model(submission)
    analysis = TraceAnalysis(
        instance_id=instance_id,
        submission=submission,
        agent_type=agent_type,
        model=model,
        dataset=dataset
    )

    total_steps = len(data)
    if total_steps == 0:
        return analysis

    # 收集所有执行及其输出
    pending_cmd = None
    pending_idx = 0

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue

        # Format 1: Old OpenHands (role=assistant, tool_calls)
        role = item.get("role", "")
        if role == "assistant":
            tool_calls = item.get("tool_calls", [])
            if isinstance(tool_calls, list):
                for tc in tool_calls:
                    if not isinstance(tc, dict):
                        continue
                    func = tc.get("function", {})
                    if not isinstance(func, dict):
                        continue

                    func_name = func.get("name", "")
                    args_str = func.get("arguments", "")

                    if func_name == "execute_bash":
                        cmd = ""
                        if isinstance(args_str, str) and args_str:
                            try:
                                args_dict = json.loads(args_str)
                                cmd = args_dict.get("command", "")
                            except json.JSONDecodeError:
                                cmd = args_str

                        if cmd and is_test_command(cmd):
                            pending_cmd = cmd
                            pending_idx = i

        # 检查 tool 角色的输出
        if role == "tool" and pending_cmd:
            content = item.get("content", "")
            # content 可能是 list 或 string
            if isinstance(content, list):
                # 提取 text 内容
                text_parts = []
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "text":
                        text_parts.append(c.get("text", ""))
                content = "\n".join(text_parts)

            if isinstance(content, str) and content:
                position = pending_idx / total_steps
                timing = get_timing_category(position)
                outcome = classify_outcome(content)

                analysis.executions.append(ExecutionRecord(
                    command=pending_cmd[:200],
                    position=position,
                    timing=timing,
                    outcome=outcome,
                    output_preview=content[:500]
                ))
            pending_cmd = None

        # Format 2: New OpenHands (source=agent, action=run)
        source = item.get("source", "")
        action = item.get("action", "")
        if source == "agent" and action == "run":
            args = item.get("args", {})
            if isinstance(args, dict):
                cmd = args.get("command", "")
                if cmd and is_test_command(cmd):
                    pending_cmd = cmd
                    pending_idx = i

        # observation 包含输出
        if item.get("source") == "environment" and pending_cmd:
            content = item.get("content", "")
            if isinstance(content, str):
                position = pending_idx / total_steps
                timing = get_timing_category(position)
                outcome = classify_outcome(content)

                analysis.executions.append(ExecutionRecord(
                    command=pending_cmd[:200],
                    position=position,
                    timing=timing,
                    outcome=outcome,
                    output_preview=content[:500]
                ))
            pending_cmd = None

    return analysis


def parse_trace_file(trace_path: Path, submission: str, dataset: str) -> Optional[TraceAnalysis]:
    """解析 trace 文件，自动检测格式"""
    instance_id = trace_path.stem.replace(".traj", "").replace(".json", "")

    try:
        with open(trace_path, 'r', encoding='utf-8') as f:
            content = f.read()

        data = json.loads(content)

        if isinstance(data, list):
            return parse_openhands_trace(data, instance_id, submission, dataset)
        elif isinstance(data, dict):
            if "trajectory" in data or "history" in data:
                return parse_sweagent_trace(data, instance_id, submission, dataset)

        return None

    except Exception as e:
        return None


def find_trace_files(submission_dir: Path) -> List[Path]:
    """找到所有 trace 文件"""
    trace_files = []

    trajs_dir = submission_dir / "trajs"
    if trajs_dir.exists():
        for ext in ["*.json", "*.traj"]:
            trace_files.extend(trajs_dir.glob(ext))

        if not trace_files:
            trace_files.extend(trajs_dir.glob("*/trajectory.json"))

    return trace_files


def main():
    data_dir = Path(__file__).parent / "data" / "traces"
    output_dir = Path(__file__).parent

    print("=" * 70)
    print("Timing-Outcome Analysis for SWE-bench Traces")
    print("=" * 70)

    # 收集所有分析结果
    all_analyses: Dict[Tuple[str, str, str], List[TraceAnalysis]] = defaultdict(list)

    for dataset in ["lite", "verified"]:
        dataset_dir = data_dir / dataset
        if not dataset_dir.exists():
            continue

        print(f"\nAnalyzing {dataset.upper()} dataset...")

        submissions = [d for d in dataset_dir.iterdir() if d.is_dir()]

        for submission_dir in sorted(submissions):
            trace_files = find_trace_files(submission_dir)
            submission_name = submission_dir.name

            for trace_path in trace_files:
                analysis = parse_trace_file(trace_path, submission_name, dataset)
                if analysis and analysis.executions:
                    key = (analysis.agent_type, analysis.model, dataset)
                    all_analyses[key].append(analysis)

    # 计算每个 agent-model-dataset 组合的 timing-outcome 统计
    results = []

    print("\n" + "=" * 70)
    print("Results: Success Rate by Timing Stage")
    print("=" * 70)
    print(f"\n{'Agent':<15} {'Model':<20} {'Dataset':<10} {'Early':<12} {'Middle':<12} {'Late':<12}")
    print("-" * 85)

    for key in sorted(all_analyses.keys()):
        agent_type, model, dataset = key
        analyses = all_analyses[key]

        # 统计每个 timing 的成功/失败次数
        timing_stats = {
            "Early": {"success": 0, "total": 0},
            "Middle": {"success": 0, "total": 0},
            "Late": {"success": 0, "total": 0},
        }

        for analysis in analyses:
            for exec_record in analysis.executions:
                timing_stats[exec_record.timing]["total"] += 1
                if exec_record.outcome == "Success":
                    timing_stats[exec_record.timing]["success"] += 1

        # 计算成功率
        early_rate = timing_stats["Early"]["success"] / timing_stats["Early"]["total"] * 100 if timing_stats["Early"]["total"] > 0 else 0
        middle_rate = timing_stats["Middle"]["success"] / timing_stats["Middle"]["total"] * 100 if timing_stats["Middle"]["total"] > 0 else 0
        late_rate = timing_stats["Late"]["success"] / timing_stats["Late"]["total"] * 100 if timing_stats["Late"]["total"] > 0 else 0

        early_str = f"{early_rate:.1f}% ({timing_stats['Early']['total']})"
        middle_str = f"{middle_rate:.1f}% ({timing_stats['Middle']['total']})"
        late_str = f"{late_rate:.1f}% ({timing_stats['Late']['total']})"

        print(f"{agent_type:<15} {model:<20} {dataset:<10} {early_str:<12} {middle_str:<12} {late_str:<12}")

        results.append({
            "agent": agent_type,
            "model": model,
            "dataset": dataset,
            "early_success": timing_stats["Early"]["success"],
            "early_total": timing_stats["Early"]["total"],
            "early_rate": early_rate,
            "middle_success": timing_stats["Middle"]["success"],
            "middle_total": timing_stats["Middle"]["total"],
            "middle_rate": middle_rate,
            "late_success": timing_stats["Late"]["success"],
            "late_total": timing_stats["Late"]["total"],
            "late_rate": late_rate,
        })

    # 保存 CSV
    csv_path = output_dir / "timing_outcome_analysis.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
        writer.writeheader()
        writer.writerows(results)

    print(f"\nCSV saved to: {csv_path}")

    # 生成 LaTeX 表格
    print("\n" + "=" * 70)
    print("LaTeX Table")
    print("=" * 70)

    latex_lines = [
        r"\begin{table}[h]",
        r"  \centering",
        r"  \small",
        r"  \caption{Test execution success rate by timing stage. Early = 0--33\% of conversation, Middle = 33--66\%, Late = 66--100\%.}",
        r"  \label{tab:timing-outcome}",
        r"  \begin{tabular}{llccc}",
        r"    \toprule",
        r"    Agent & Model & Early & Middle & Late \\",
        r"    \midrule",
    ]

    for r in results:
        if r["early_total"] > 0 or r["middle_total"] > 0 or r["late_total"] > 0:
            early = f"{r['early_rate']:.0f}\\%" if r['early_total'] > 0 else "--"
            middle = f"{r['middle_rate']:.0f}\\%" if r['middle_total'] > 0 else "--"
            late = f"{r['late_rate']:.0f}\\%" if r['late_total'] > 0 else "--"
            latex_lines.append(f"    {r['agent']} & {r['model']} & {early} & {middle} & {late} \\\\")

    latex_lines.extend([
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ])

    print("\n".join(latex_lines))

    # 保存 LaTeX
    latex_path = output_dir / "timing_outcome_table.tex"
    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(latex_lines))

    print(f"\nLaTeX table saved to: {latex_path}")


if __name__ == "__main__":
    main()
