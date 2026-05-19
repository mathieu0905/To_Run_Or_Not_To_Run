#!/usr/bin/env python3
"""
分析模型"只修改一次代码后不再修改"的比例 v2

两个维度：
1. 全局：不考虑执行，统计所有编辑操作中"只编辑一次后不再编辑"的比例
2. 执行后修改：统计执行测试后对同一文件进行再次修改的比例

分析 prohibited (run_free) 和 unrestricted (run_full) 模式
包含 claude_code 和 codex 两个 agent
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set, Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


def is_test_execution(cmd: str) -> bool:
    """判断是否是测试执行命令"""
    if not cmd:
        return False
    cmd_lower = cmd.lower().strip()
    test_patterns = [
        r'\bpytest\b', r'\bpy\.test\b', r'python[3]?\s+-m\s+pytest',
        r'python[3]?\s+-m\s+unittest', r'manage\.py\s+test',
        r'\btox\b', r'\bnosetests?\b',
    ]
    for pattern in test_patterns:
        if re.search(pattern, cmd_lower):
            return True
    # 运行 .py 文件也算执行
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        if not re.search(r'python[3]?\s+-c\s', cmd_lower):
            return True
    return False


def is_source_file(path: str) -> bool:
    """判断是否是源代码文件（排除测试文件和临时文件）"""
    if not path:
        return False
    path_lower = path.lower()

    # 排除测试文件
    if '/test_' in path_lower or '/tests/' in path_lower:
        return False
    if path_lower.endswith('_test.py'):
        return False

    # 排除临时/调试文件
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return False

    # 排除根目录的临时脚本
    if '/testbed/' in path_lower:
        parts = path_lower.split('/testbed/')[-1].split('/')
        if len(parts) == 1 and parts[0].endswith('.py'):
            return False

    # 只关注 .py 文件
    if not path_lower.endswith('.py'):
        return False

    return True


@dataclass
class EditEvent:
    """编辑事件"""
    file_path: str
    tool_name: str
    turn_number: int
    timestamp: int  # 事件序号


@dataclass
class ExecEvent:
    """执行事件"""
    command: str
    turn_number: int
    timestamp: int


@dataclass
class InstanceAnalysis:
    """单个实例的分析结果"""
    instance_id: str
    mode: str
    agent: str

    # 全局统计
    total_source_edits: int = 0
    unique_source_files: int = 0
    edits_per_file: Dict[str, int] = field(default_factory=dict)
    only_one_edit_globally: bool = False  # 每个源文件都只编辑一次

    # 执行后修改统计
    total_executions: int = 0
    edits_after_exec: int = 0  # 执行后的编辑次数
    files_edited_after_exec: Set[str] = field(default_factory=set)  # 执行后被编辑的文件
    has_edit_after_exec: bool = False  # 是否有执行后的编辑


def analyze_trace(trace_path: Path) -> Optional[InstanceAnalysis]:
    """分析单个trace文件"""
    parts = trace_path.parts
    # 找到 mode 和 agent
    try:
        # 路径格式: .../output/{dataset}/{agent}/{mode}/{instance_id}/trace.jsonl
        instance_id = trace_path.parent.name
        mode = trace_path.parent.parent.name
        agent = trace_path.parent.parent.parent.name
    except:
        return None

    analysis = InstanceAnalysis(instance_id=instance_id, mode=mode, agent=agent)

    edits: List[EditEvent] = []
    execs: List[ExecEvent] = []
    event_idx = 0
    turn_number = 0

    try:
        with open(trace_path, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # 统计 turn
                if entry.get('type') == 'assistant':
                    turn_number += 1
                    message = entry.get('message', {})
                    content = message.get('content', [])

                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'tool_use':
                            tool_name = item.get('name', '')
                            input_data = item.get('input', {})

                            # 编辑操作
                            if tool_name in ('Edit', 'Write'):
                                file_path = input_data.get('file_path', '')
                                if is_source_file(file_path):
                                    edits.append(EditEvent(
                                        file_path=file_path,
                                        tool_name=tool_name,
                                        turn_number=turn_number,
                                        timestamp=event_idx
                                    ))
                                    event_idx += 1

                            # 执行操作
                            elif tool_name == 'Bash':
                                command = input_data.get('command', '')
                                if is_test_execution(command):
                                    execs.append(ExecEvent(
                                        command=command,
                                        turn_number=turn_number,
                                        timestamp=event_idx
                                    ))
                                    event_idx += 1
    except Exception as e:
        print(f"Error processing {trace_path}: {e}")
        return None

    if not edits:
        return analysis

    # 全局统计
    analysis.total_source_edits = len(edits)

    file_edit_counts = defaultdict(int)
    for edit in edits:
        file_edit_counts[edit.file_path] += 1

    analysis.unique_source_files = len(file_edit_counts)
    analysis.edits_per_file = dict(file_edit_counts)
    analysis.only_one_edit_globally = all(count == 1 for count in file_edit_counts.values())

    # 执行后修改统计
    analysis.total_executions = len(execs)

    if execs:
        # 找到第一次执行的时间戳
        first_exec_ts = min(e.timestamp for e in execs)

        # 统计执行后的编辑
        edits_after = [e for e in edits if e.timestamp > first_exec_ts]
        analysis.edits_after_exec = len(edits_after)
        analysis.files_edited_after_exec = set(e.file_path for e in edits_after)
        analysis.has_edit_after_exec = len(edits_after) > 0

    return analysis


def find_all_traces(mode: str) -> List[Path]:
    """查找指定模式的所有trace文件（包括所有agent）"""
    traces = []

    mode_mapping = {
        'prohibited': 'run_free',
        'unrestricted': 'run_full',
    }
    actual_mode = mode_mapping.get(mode, mode)

    for dataset_dir in OUTPUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue

        for agent_dir in dataset_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            if agent_dir.name not in ('claude_code', 'codex'):
                continue

            mode_dir = agent_dir / actual_mode
            if mode_dir.exists():
                for instance_dir in mode_dir.iterdir():
                    trace_file = instance_dir / "trace.jsonl"
                    if trace_file.exists():
                        traces.append(trace_file)

    return traces


def analyze_mode(mode: str) -> Dict:
    """分析指定模式"""
    traces = find_all_traces(mode)

    print(f"\n{'='*70}")
    print(f"分析模式: {mode}")
    print(f"找到 {len(traces)} 个trace文件")
    print('='*70)

    analyses = []
    for trace in traces:
        analysis = analyze_trace(trace)
        if analysis and analysis.total_source_edits > 0:
            analyses.append(analysis)

    if not analyses:
        return {"mode": mode, "total_instances": 0}

    total = len(analyses)

    # ========== 全局统计 ==========
    single_edit_globally = sum(1 for a in analyses if a.only_one_edit_globally)
    multiple_edit_globally = total - single_edit_globally
    global_single_ratio = single_edit_globally / total

    # 按 agent 分组
    by_agent = defaultdict(list)
    for a in analyses:
        by_agent[a.agent].append(a)

    print(f"\n【全局统计】不考虑执行，每个源文件只编辑一次的比例")
    print(f"  总实例数（有源文件编辑）: {total}")
    print(f"  只编辑一次: {single_edit_globally} ({global_single_ratio:.1%})")
    print(f"  多次编辑:   {multiple_edit_globally} ({1-global_single_ratio:.1%})")

    for agent, agent_analyses in sorted(by_agent.items()):
        agent_total = len(agent_analyses)
        agent_single = sum(1 for a in agent_analyses if a.only_one_edit_globally)
        print(f"    {agent}: {agent_single}/{agent_total} ({agent_single/agent_total:.1%})")

    # ========== 执行后修改统计 ==========
    # 只统计有执行的实例
    with_exec = [a for a in analyses if a.total_executions > 0]

    if with_exec:
        with_exec_total = len(with_exec)
        edit_after_exec = sum(1 for a in with_exec if a.has_edit_after_exec)
        no_edit_after_exec = with_exec_total - edit_after_exec
        edit_after_exec_ratio = edit_after_exec / with_exec_total

        print(f"\n【执行后修改统计】有执行的实例中，执行后是否再次编辑源文件")
        print(f"  有执行的实例数: {with_exec_total}")
        print(f"  执行后有修改: {edit_after_exec} ({edit_after_exec_ratio:.1%})")
        print(f"  执行后无修改: {no_edit_after_exec} ({1-edit_after_exec_ratio:.1%})")

        for agent, agent_analyses in sorted(by_agent.items()):
            agent_with_exec = [a for a in agent_analyses if a.total_executions > 0]
            if agent_with_exec:
                agent_exec_total = len(agent_with_exec)
                agent_edit_after = sum(1 for a in agent_with_exec if a.has_edit_after_exec)
                print(f"    {agent}: {agent_edit_after}/{agent_exec_total} ({agent_edit_after/agent_exec_total:.1%}) 执行后有修改")
    else:
        with_exec_total = 0
        edit_after_exec = 0
        edit_after_exec_ratio = 0

    # 编辑次数分布
    edit_count_dist = defaultdict(int)
    for a in analyses:
        max_edits = max(a.edits_per_file.values()) if a.edits_per_file else 0
        edit_count_dist[max_edits] += 1

    print(f"\n【编辑次数分布】每文件最大编辑次数")
    for count in sorted(edit_count_dist.keys()):
        num = edit_count_dist[count]
        print(f"  {count}次: {num} ({num/total:.1%})")

    return {
        "mode": mode,
        "total_instances": total,
        # 全局
        "global_single_edit_instances": single_edit_globally,
        "global_multiple_edit_instances": multiple_edit_globally,
        "global_single_edit_ratio": global_single_ratio,
        # 执行后
        "instances_with_execution": with_exec_total,
        "edit_after_execution": edit_after_exec,
        "no_edit_after_execution": with_exec_total - edit_after_exec if with_exec_total > 0 else 0,
        "edit_after_execution_ratio": edit_after_exec_ratio,
        # 分布
        "edit_count_distribution": dict(sorted(edit_count_dist.items())),
        # 按agent
        "by_agent": {
            agent: {
                "total": len(agent_analyses),
                "global_single_edit": sum(1 for a in agent_analyses if a.only_one_edit_globally),
                "with_execution": len([a for a in agent_analyses if a.total_executions > 0]),
                "edit_after_exec": sum(1 for a in agent_analyses if a.total_executions > 0 and a.has_edit_after_exec),
            }
            for agent, agent_analyses in by_agent.items()
        }
    }


def main():
    print("="*70)
    print("分析: 模型只修改一次代码后不再修改的比例 v2")
    print("="*70)

    results = {}
    results['prohibited'] = analyze_mode('prohibited')
    results['unrestricted'] = analyze_mode('unrestricted')

    # 对比分析
    print("\n" + "="*70)
    print("对比分析")
    print("="*70)

    p = results['prohibited']
    u = results['unrestricted']

    if p['total_instances'] > 0 and u['total_instances'] > 0:
        print("\n【全局：只编辑一次后不再编辑的比例】")
        print(f"  Prohibited:   {p['global_single_edit_ratio']:.1%} ({p['global_single_edit_instances']}/{p['total_instances']})")
        print(f"  Unrestricted: {u['global_single_edit_ratio']:.1%} ({u['global_single_edit_instances']}/{u['total_instances']})")
        diff_global = p['global_single_edit_ratio'] - u['global_single_edit_ratio']
        print(f"  差异: {diff_global:+.1%}")

        print("\n【执行后修改的比例】（有执行的实例中）")
        if p['instances_with_execution'] > 0:
            print(f"  Prohibited:   {p['edit_after_execution_ratio']:.1%} ({p['edit_after_execution']}/{p['instances_with_execution']})")
        else:
            print(f"  Prohibited:   N/A (无执行)")
        if u['instances_with_execution'] > 0:
            print(f"  Unrestricted: {u['edit_after_execution_ratio']:.1%} ({u['edit_after_execution']}/{u['instances_with_execution']})")
        else:
            print(f"  Unrestricted: N/A (无执行)")

    # 保存结果
    output_file = ANALYSIS_DIR / "single_edit_ratio_analysis_v2.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n结果已保存到: {output_file}")

    # 生成 Markdown 报告
    md_file = ANALYSIS_DIR / "single_edit_ratio_analysis_v2.md"
    with open(md_file, 'w') as f:
        f.write("# 代码修改次数分析 v2\n\n")
        f.write("## 研究问题\n\n")
        f.write("模型在修改一次代码之后就不再修改的比例是多少？\n\n")
        f.write("两个维度：\n")
        f.write("1. **全局**：不考虑执行，统计每个源文件只被编辑一次的实例比例\n")
        f.write("2. **执行后修改**：在有执行的实例中，执行后是否再次编辑源文件\n\n")

        f.write("## 数据范围\n\n")
        f.write("- Agent: claude_code, codex\n")
        f.write("- 模式: prohibited (run_free), unrestricted (run_full)\n")
        f.write("- 数据集: swebenchlite, swebenchverified\n\n")

        f.write("## 结果\n\n")
        f.write("### 全局：只编辑一次后不再编辑\n\n")
        f.write("| 模式 | 只编辑一次 | 多次编辑 | 比例 |\n")
        f.write("|------|-----------|---------|------|\n")
        f.write(f"| Prohibited | {p['global_single_edit_instances']} | {p['global_multiple_edit_instances']} | **{p['global_single_edit_ratio']:.1%}** |\n")
        f.write(f"| Unrestricted | {u['global_single_edit_instances']} | {u['global_multiple_edit_instances']} | **{u['global_single_edit_ratio']:.1%}** |\n")

        f.write("\n### 执行后修改（有执行的实例中）\n\n")
        f.write("| 模式 | 有执行实例 | 执行后有修改 | 执行后无修改 | 修改比例 |\n")
        f.write("|------|-----------|-------------|-------------|----------|\n")
        if p['instances_with_execution'] > 0:
            f.write(f"| Prohibited | {p['instances_with_execution']} | {p['edit_after_execution']} | {p['no_edit_after_execution']} | **{p['edit_after_execution_ratio']:.1%}** |\n")
        else:
            f.write(f"| Prohibited | 0 | - | - | N/A |\n")
        if u['instances_with_execution'] > 0:
            f.write(f"| Unrestricted | {u['instances_with_execution']} | {u['edit_after_execution']} | {u['no_edit_after_execution']} | **{u['edit_after_execution_ratio']:.1%}** |\n")
        else:
            f.write(f"| Unrestricted | 0 | - | - | N/A |\n")

        f.write("\n### 按 Agent 分组\n\n")
        f.write("#### 全局只编辑一次比例\n\n")
        f.write("| Agent | Prohibited | Unrestricted |\n")
        f.write("|-------|------------|-------------|\n")
        all_agents = set(p.get('by_agent', {}).keys()) | set(u.get('by_agent', {}).keys())
        for agent in sorted(all_agents):
            p_agent = p.get('by_agent', {}).get(agent, {})
            u_agent = u.get('by_agent', {}).get(agent, {})
            p_ratio = p_agent.get('global_single_edit', 0) / p_agent.get('total', 1) if p_agent.get('total', 0) > 0 else 0
            u_ratio = u_agent.get('global_single_edit', 0) / u_agent.get('total', 1) if u_agent.get('total', 0) > 0 else 0
            f.write(f"| {agent} | {p_ratio:.1%} ({p_agent.get('global_single_edit', 0)}/{p_agent.get('total', 0)}) | {u_ratio:.1%} ({u_agent.get('global_single_edit', 0)}/{u_agent.get('total', 0)}) |\n")

        f.write("\n#### 执行后修改比例\n\n")
        f.write("| Agent | Prohibited | Unrestricted |\n")
        f.write("|-------|------------|-------------|\n")
        for agent in sorted(all_agents):
            p_agent = p.get('by_agent', {}).get(agent, {})
            u_agent = u.get('by_agent', {}).get(agent, {})
            p_with_exec = p_agent.get('with_execution', 0)
            u_with_exec = u_agent.get('with_execution', 0)
            p_edit_after = p_agent.get('edit_after_exec', 0)
            u_edit_after = u_agent.get('edit_after_exec', 0)
            p_str = f"{p_edit_after/p_with_exec:.1%} ({p_edit_after}/{p_with_exec})" if p_with_exec > 0 else "N/A"
            u_str = f"{u_edit_after/u_with_exec:.1%} ({u_edit_after}/{u_with_exec})" if u_with_exec > 0 else "N/A"
            f.write(f"| {agent} | {p_str} | {u_str} |\n")

        f.write("\n## 关键发现\n\n")
        diff_global = p['global_single_edit_ratio'] - u['global_single_edit_ratio']
        f.write(f"1. **全局只编辑一次比例**：Prohibited {p['global_single_edit_ratio']:.1%} vs Unrestricted {u['global_single_edit_ratio']:.1%}（差异 {diff_global:+.1%}）\n")

        if u['instances_with_execution'] > 0:
            f.write(f"2. **Unrestricted 执行后修改比例**：{u['edit_after_execution_ratio']:.1%}，说明约 {u['edit_after_execution_ratio']:.0%} 的实例在执行后会根据反馈修改代码\n")

        f.write(f"3. **大多数修复是一次性的**：约 {(p['global_single_edit_ratio']+u['global_single_edit_ratio'])/2:.0%} 的实例只编辑一次后不再修改\n")

    print(f"Markdown报告已保存到: {md_file}")


if __name__ == "__main__":
    main()
