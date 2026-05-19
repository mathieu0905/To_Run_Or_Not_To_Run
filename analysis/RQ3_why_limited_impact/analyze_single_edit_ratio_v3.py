#!/usr/bin/env python3
"""
分析模型"只修改一次代码后不再修改"的比例 v3

改进：
1. 使用 data_loader.py 中的执行定义（HIGH_COST_PATTERNS + PYTHON_SCRIPT_PATTERN）
2. 分析所有二次修改是否由执行触发
3. 正确统计所有 agent（claude_code + codex）共 400 条 trace

两个维度：
1. 全局：不考虑执行，统计所有编辑操作中"只编辑一次后不再编辑"的比例
2. 执行后修改：统计执行测试后对同一文件进行再次修改的比例
3. 二次修改触发原因：是执行触发还是其他原因
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent

# 从 data_loader.py 复制的执行定义
HIGH_COST_PATTERNS = [
    "pytest", "python -m pytest", "python -m unittest",
    "manage.py test", "python manage.py test",
    "tox", "nose", "nosetests",
    "python -m django test",
    "python tests/runtests.py"
]
PYTHON_SCRIPT_PATTERN = re.compile(r'\bpython\s+[a-zA-Z_][\w/\-]*\.py\b')

# 排除的 agent
EXCLUDED_AGENTS = ["claude_code_glm"]


def is_execution(cmd: str) -> bool:
    """判断是否是执行命令（与 data_loader.py 保持一致）"""
    if not cmd:
        return False
    # 高成本执行（测试框架）
    if any(p in cmd for p in HIGH_COST_PATTERNS):
        return True
    # 低成本执行（Python 脚本）
    if PYTHON_SCRIPT_PATTERN.search(cmd):
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
    if 'demo' in path_lower or 'example' in path_lower:
        return False

    # 排除根目录的临时脚本 /testbed/xxx.py
    if '/testbed/' in path_lower:
        parts = path_lower.split('/testbed/')[-1].split('/')
        if len(parts) == 1 and parts[0].endswith('.py'):
            return False

    # 只关注 .py 文件
    if not path_lower.endswith('.py'):
        return False

    return True


@dataclass
class Event:
    """事件基类"""
    timestamp: int  # 事件序号
    turn_number: int


@dataclass
class EditEvent(Event):
    """编辑事件"""
    file_path: str
    tool_name: str  # Edit or Write


@dataclass
class ExecEvent(Event):
    """执行事件"""
    command: str


@dataclass
class InstanceAnalysis:
    """单个实例的分析结果"""
    instance_id: str
    mode: str
    agent: str
    dataset: str

    # 全局统计
    total_source_edits: int = 0
    unique_source_files: int = 0
    edits_per_file: Dict[str, int] = field(default_factory=dict)
    only_one_edit_globally: bool = False

    # 执行统计
    total_executions: int = 0

    # 执行后修改统计
    edits_after_exec: int = 0
    has_edit_after_exec: bool = False

    # 二次修改触发分析
    has_multiple_edits: bool = False
    multiple_edit_triggered_by_exec: bool = False  # 二次修改是否由执行触发
    multiple_edit_without_exec: bool = False  # 二次修改但没有执行


def parse_trace_claude_code(trace_path: Path) -> tuple[List[EditEvent], List[ExecEvent]]:
    """解析 Claude Code 格式的 trace"""
    edits = []
    execs = []
    event_idx = 0
    turn_number = 0

    with open(trace_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if entry.get('type') == 'assistant':
                turn_number += 1
                content = entry.get('message', {}).get('content', [])

                for item in content:
                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                        tool_name = item.get('name', '')
                        input_data = item.get('input', {})

                        if tool_name in ('Edit', 'Write'):
                            file_path = input_data.get('file_path', '')
                            if is_source_file(file_path):
                                edits.append(EditEvent(
                                    timestamp=event_idx,
                                    turn_number=turn_number,
                                    file_path=file_path,
                                    tool_name=tool_name
                                ))
                                event_idx += 1

                        elif tool_name == 'Bash':
                            command = input_data.get('command', '')
                            if is_execution(command):
                                execs.append(ExecEvent(
                                    timestamp=event_idx,
                                    turn_number=turn_number,
                                    command=command
                                ))
                                event_idx += 1

    return edits, execs


def parse_trace_codex(trace_path: Path) -> tuple[List[EditEvent], List[ExecEvent]]:
    """解析 Codex 格式的 trace"""
    edits = []
    execs = []
    event_idx = 0
    turn_number = 0

    with open(trace_path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Codex 使用 item.completed 格式
            if entry.get('type') == 'item.completed':
                inner = entry.get('item', {})
                item_type = inner.get('type', '')

                if item_type == 'command_execution':
                    command = inner.get('command', '')
                    if is_execution(command):
                        execs.append(ExecEvent(
                            timestamp=event_idx,
                            turn_number=turn_number,
                            command=command
                        ))
                        event_idx += 1

                elif item_type == 'file_edit':
                    file_path = inner.get('file_path', '') or inner.get('path', '')
                    if is_source_file(file_path):
                        edits.append(EditEvent(
                            timestamp=event_idx,
                            turn_number=turn_number,
                            file_path=file_path,
                            tool_name='Edit'
                        ))
                        event_idx += 1

            if entry.get('type') == 'turn.completed':
                turn_number += 1

    return edits, execs


def analyze_trace(trace_path: Path) -> Optional[InstanceAnalysis]:
    """分析单个 trace 文件"""
    try:
        # 解析路径: output/{dataset}/{agent}/{mode}/{instance_id}/trace.jsonl
        instance_id = trace_path.parent.name
        mode = trace_path.parent.parent.name
        agent = trace_path.parent.parent.parent.name
        dataset = trace_path.parent.parent.parent.parent.name
    except:
        return None

    if agent in EXCLUDED_AGENTS:
        return None

    analysis = InstanceAnalysis(
        instance_id=instance_id,
        mode=mode,
        agent=agent,
        dataset=dataset
    )

    # 根据 agent 选择解析器
    if agent == 'codex':
        edits, execs = parse_trace_codex(trace_path)
    else:
        edits, execs = parse_trace_claude_code(trace_path)

    # 全局统计
    analysis.total_source_edits = len(edits)
    analysis.total_executions = len(execs)

    if not edits:
        return analysis

    # 按文件统计编辑次数
    file_edit_counts = defaultdict(int)
    file_first_edit_ts = {}  # 每个文件第一次编辑的时间戳

    for edit in edits:
        file_edit_counts[edit.file_path] += 1
        if edit.file_path not in file_first_edit_ts:
            file_first_edit_ts[edit.file_path] = edit.timestamp

    analysis.unique_source_files = len(file_edit_counts)
    analysis.edits_per_file = dict(file_edit_counts)
    analysis.only_one_edit_globally = all(count == 1 for count in file_edit_counts.values())

    # 检查是否有多次编辑
    analysis.has_multiple_edits = any(count > 1 for count in file_edit_counts.values())

    # 执行后修改统计
    if execs:
        first_exec_ts = min(e.timestamp for e in execs)
        edits_after = [e for e in edits if e.timestamp > first_exec_ts]
        analysis.edits_after_exec = len(edits_after)
        analysis.has_edit_after_exec = len(edits_after) > 0

    # 分析二次修改的触发原因
    if analysis.has_multiple_edits:
        # 找到所有有多次编辑的文件
        multi_edit_files = [f for f, c in file_edit_counts.items() if c > 1]

        # 检查每个多次编辑的文件，看第二次编辑是否在某次执行之后
        exec_timestamps = [e.timestamp for e in execs]

        triggered_by_exec = False
        for f in multi_edit_files:
            # 获取该文件所有编辑的时间戳
            file_edits = sorted([e.timestamp for e in edits if e.file_path == f])
            if len(file_edits) >= 2:
                first_edit_ts = file_edits[0]
                second_edit_ts = file_edits[1]

                # 检查第一次和第二次编辑之间是否有执行
                exec_between = any(first_edit_ts < ts < second_edit_ts for ts in exec_timestamps)
                if exec_between:
                    triggered_by_exec = True
                    break

        analysis.multiple_edit_triggered_by_exec = triggered_by_exec
        analysis.multiple_edit_without_exec = not triggered_by_exec

    return analysis


def find_all_traces(mode: str) -> List[Path]:
    """查找指定模式的所有 trace 文件"""
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
            if agent_dir.name in EXCLUDED_AGENTS:
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
    print(f"找到 {len(traces)} 个 trace 文件")
    print('='*70)

    analyses = []
    for trace in traces:
        try:
            analysis = analyze_trace(trace)
            if analysis:
                analyses.append(analysis)
        except Exception as e:
            print(f"Error: {trace}: {e}")

    # 过滤有编辑的实例
    with_edits = [a for a in analyses if a.total_source_edits > 0]
    total = len(with_edits)

    print(f"\n总 trace 数: {len(analyses)}")
    print(f"有源文件编辑的实例: {total}")

    if total == 0:
        return {"mode": mode, "total_instances": 0}

    # 按 agent 分组
    by_agent = defaultdict(list)
    for a in with_edits:
        by_agent[a.agent].append(a)

    # ========== 1. 全局统计 ==========
    single_edit = sum(1 for a in with_edits if a.only_one_edit_globally)
    multiple_edit = total - single_edit
    single_ratio = single_edit / total

    print(f"\n【1. 全局统计】每个源文件只编辑一次的比例")
    print(f"  只编辑一次: {single_edit} ({single_ratio:.1%})")
    print(f"  多次编辑:   {multiple_edit} ({1-single_ratio:.1%})")
    for agent in sorted(by_agent.keys()):
        agent_list = by_agent[agent]
        agent_single = sum(1 for a in agent_list if a.only_one_edit_globally)
        print(f"    {agent}: {agent_single}/{len(agent_list)} ({agent_single/len(agent_list):.1%})")

    # ========== 2. 执行后修改统计 ==========
    with_exec = [a for a in with_edits if a.total_executions > 0]
    if with_exec:
        with_exec_total = len(with_exec)
        edit_after = sum(1 for a in with_exec if a.has_edit_after_exec)
        edit_after_ratio = edit_after / with_exec_total

        print(f"\n【2. 执行后修改】有执行的实例中，执行后是否再次编辑")
        print(f"  有执行的实例: {with_exec_total}")
        print(f"  执行后有修改: {edit_after} ({edit_after_ratio:.1%})")
        print(f"  执行后无修改: {with_exec_total - edit_after} ({1-edit_after_ratio:.1%})")
        for agent in sorted(by_agent.keys()):
            agent_exec = [a for a in by_agent[agent] if a.total_executions > 0]
            if agent_exec:
                agent_edit_after = sum(1 for a in agent_exec if a.has_edit_after_exec)
                print(f"    {agent}: {agent_edit_after}/{len(agent_exec)} ({agent_edit_after/len(agent_exec):.1%})")
    else:
        with_exec_total = 0
        edit_after = 0
        edit_after_ratio = 0

    # ========== 3. 二次修改触发原因 ==========
    with_multiple = [a for a in with_edits if a.has_multiple_edits]
    if with_multiple:
        triggered_by_exec = sum(1 for a in with_multiple if a.multiple_edit_triggered_by_exec)
        without_exec = sum(1 for a in with_multiple if a.multiple_edit_without_exec)

        print(f"\n【3. 二次修改触发原因】有多次编辑的实例中")
        print(f"  有多次编辑的实例: {len(with_multiple)}")
        print(f"  由执行触发: {triggered_by_exec} ({triggered_by_exec/len(with_multiple):.1%})")
        print(f"  非执行触发: {without_exec} ({without_exec/len(with_multiple):.1%})")
        for agent in sorted(by_agent.keys()):
            agent_multi = [a for a in by_agent[agent] if a.has_multiple_edits]
            if agent_multi:
                agent_by_exec = sum(1 for a in agent_multi if a.multiple_edit_triggered_by_exec)
                print(f"    {agent}: 执行触发 {agent_by_exec}/{len(agent_multi)} ({agent_by_exec/len(agent_multi):.1%})")
    else:
        triggered_by_exec = 0
        without_exec = 0

    # 编辑次数分布
    edit_dist = defaultdict(int)
    for a in with_edits:
        max_edits = max(a.edits_per_file.values()) if a.edits_per_file else 0
        edit_dist[max_edits] += 1

    print(f"\n【编辑次数分布】每文件最大编辑次数")
    for count in sorted(edit_dist.keys()):
        num = edit_dist[count]
        print(f"  {count}次: {num} ({num/total:.1%})")

    return {
        "mode": mode,
        "total_traces": len(analyses),
        "total_with_edits": total,
        # 全局
        "global_single_edit": single_edit,
        "global_multiple_edit": multiple_edit,
        "global_single_ratio": single_ratio,
        # 执行后
        "instances_with_exec": with_exec_total,
        "edit_after_exec": edit_after,
        "edit_after_exec_ratio": edit_after_ratio,
        # 二次修改触发
        "instances_with_multiple_edits": len(with_multiple) if with_multiple else 0,
        "multiple_triggered_by_exec": triggered_by_exec,
        "multiple_without_exec": without_exec,
        # 分布
        "edit_distribution": dict(sorted(edit_dist.items())),
        # 按 agent
        "by_agent": {
            agent: {
                "total": len(agent_list),
                "single_edit": sum(1 for a in agent_list if a.only_one_edit_globally),
                "with_exec": len([a for a in agent_list if a.total_executions > 0]),
                "edit_after_exec": sum(1 for a in agent_list if a.total_executions > 0 and a.has_edit_after_exec),
                "multiple_edits": sum(1 for a in agent_list if a.has_multiple_edits),
                "multi_by_exec": sum(1 for a in agent_list if a.multiple_edit_triggered_by_exec),
            }
            for agent, agent_list in by_agent.items()
        }
    }


def main():
    print("="*70)
    print("分析: 模型只修改一次代码后不再修改的比例 v3")
    print("="*70)

    results = {}
    results['prohibited'] = analyze_mode('prohibited')
    results['unrestricted'] = analyze_mode('unrestricted')

    # 对比分析
    print("\n" + "="*70)
    print("对比总结")
    print("="*70)

    p = results['prohibited']
    u = results['unrestricted']

    print(f"\n                              Prohibited    Unrestricted")
    print(f"总 trace 数                   {p['total_traces']:>10}    {u['total_traces']:>10}")
    print(f"有源文件编辑                  {p['total_with_edits']:>10}    {u['total_with_edits']:>10}")
    print(f"")
    print(f"【全局只编辑一次】")
    print(f"  比例                        {p['global_single_ratio']:>10.1%}    {u['global_single_ratio']:>10.1%}")
    print(f"  数量                        {p['global_single_edit']:>10}    {u['global_single_edit']:>10}")
    print(f"")
    print(f"【执行后修改】")
    print(f"  有执行的实例                {p['instances_with_exec']:>10}    {u['instances_with_exec']:>10}")
    if p['instances_with_exec'] > 0 and u['instances_with_exec'] > 0:
        print(f"  执行后修改比例              {p['edit_after_exec_ratio']:>10.1%}    {u['edit_after_exec_ratio']:>10.1%}")
    print(f"")
    print(f"【二次修改触发原因】")
    print(f"  有多次编辑的实例            {p['instances_with_multiple_edits']:>10}    {u['instances_with_multiple_edits']:>10}")
    if p['instances_with_multiple_edits'] > 0:
        p_exec_ratio = p['multiple_triggered_by_exec'] / p['instances_with_multiple_edits']
        print(f"  由执行触发 (prohibited)     {p_exec_ratio:>10.1%}")
    if u['instances_with_multiple_edits'] > 0:
        u_exec_ratio = u['multiple_triggered_by_exec'] / u['instances_with_multiple_edits']
        print(f"  由执行触发 (unrestricted)   {u_exec_ratio:>10.1%}")

    # 保存结果
    output_file = ANALYSIS_DIR / "single_edit_ratio_analysis_v3.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n结果已保存到: {output_file}")

    # 生成 Markdown
    md_file = ANALYSIS_DIR / "single_edit_ratio_analysis_v3.md"
    with open(md_file, 'w') as f:
        f.write("# 代码修改次数分析 v3\n\n")
        f.write("## 研究问题\n\n")
        f.write("1. 模型在修改一次代码之后就不再修改的比例是多少？\n")
        f.write("2. 执行后进行修改的比例是多少？\n")
        f.write("3. 二次修改是否都由执行触发？\n\n")

        f.write("## 数据范围\n\n")
        f.write(f"- Prohibited (run_free): {p['total_traces']} traces\n")
        f.write(f"- Unrestricted (run_full): {u['total_traces']} traces\n")
        f.write("- Agent: claude_code + codex\n\n")

        f.write("## 结果\n\n")
        f.write("### 1. 全局：只编辑一次后不再编辑\n\n")
        f.write("| 模式 | 有编辑实例 | 只编辑一次 | 多次编辑 | 只编辑一次比例 |\n")
        f.write("|------|-----------|-----------|---------|---------------|\n")
        f.write(f"| Prohibited | {p['total_with_edits']} | {p['global_single_edit']} | {p['global_multiple_edit']} | **{p['global_single_ratio']:.1%}** |\n")
        f.write(f"| Unrestricted | {u['total_with_edits']} | {u['global_single_edit']} | {u['global_multiple_edit']} | **{u['global_single_ratio']:.1%}** |\n")

        f.write("\n### 2. 执行后修改\n\n")
        f.write("| 模式 | 有执行实例 | 执行后有修改 | 执行后无修改 | 修改比例 |\n")
        f.write("|------|-----------|-------------|-------------|----------|\n")
        if p['instances_with_exec'] > 0:
            f.write(f"| Prohibited | {p['instances_with_exec']} | {p['edit_after_exec']} | {p['instances_with_exec']-p['edit_after_exec']} | **{p['edit_after_exec_ratio']:.1%}** |\n")
        else:
            f.write(f"| Prohibited | 0 | - | - | N/A |\n")
        if u['instances_with_exec'] > 0:
            f.write(f"| Unrestricted | {u['instances_with_exec']} | {u['edit_after_exec']} | {u['instances_with_exec']-u['edit_after_exec']} | **{u['edit_after_exec_ratio']:.1%}** |\n")

        f.write("\n### 3. 二次修改触发原因\n\n")
        f.write("| 模式 | 有多次编辑 | 由执行触发 | 非执行触发 | 执行触发比例 |\n")
        f.write("|------|-----------|-----------|-----------|-------------|\n")
        if p['instances_with_multiple_edits'] > 0:
            p_ratio = p['multiple_triggered_by_exec'] / p['instances_with_multiple_edits']
            f.write(f"| Prohibited | {p['instances_with_multiple_edits']} | {p['multiple_triggered_by_exec']} | {p['multiple_without_exec']} | **{p_ratio:.1%}** |\n")
        if u['instances_with_multiple_edits'] > 0:
            u_ratio = u['multiple_triggered_by_exec'] / u['instances_with_multiple_edits']
            f.write(f"| Unrestricted | {u['instances_with_multiple_edits']} | {u['multiple_triggered_by_exec']} | {u['multiple_without_exec']} | **{u_ratio:.1%}** |\n")

        f.write("\n### 按 Agent 分组\n\n")
        f.write("| Agent | 模式 | 总数 | 只编辑一次 | 有执行 | 执行后修改 |\n")
        f.write("|-------|------|-----|-----------|-------|----------|\n")
        for agent in sorted(set(p.get('by_agent', {}).keys()) | set(u.get('by_agent', {}).keys())):
            for mode_name, mode_data in [('Prohibited', p), ('Unrestricted', u)]:
                agent_data = mode_data.get('by_agent', {}).get(agent, {})
                if agent_data:
                    total = agent_data.get('total', 0)
                    single = agent_data.get('single_edit', 0)
                    with_exec = agent_data.get('with_exec', 0)
                    edit_after = agent_data.get('edit_after_exec', 0)
                    single_r = f"{single/total:.1%}" if total > 0 else "-"
                    edit_r = f"{edit_after}/{with_exec}" if with_exec > 0 else "-"
                    f.write(f"| {agent} | {mode_name} | {total} | {single_r} | {with_exec} | {edit_r} |\n")

        f.write("\n## 关键发现\n\n")
        f.write(f"1. **全局只编辑一次比例**：Prohibited {p['global_single_ratio']:.1%} vs Unrestricted {u['global_single_ratio']:.1%}\n")
        if u['instances_with_exec'] > 0:
            f.write(f"2. **Unrestricted 执行后修改**：{u['edit_after_exec_ratio']:.1%} 的实例在执行后会修改代码\n")
        if u['instances_with_multiple_edits'] > 0:
            u_exec_ratio = u['multiple_triggered_by_exec'] / u['instances_with_multiple_edits']
            f.write(f"3. **二次修改触发**：Unrestricted 中 {u_exec_ratio:.1%} 的二次修改由执行触发\n")

    print(f"Markdown 报告已保存到: {md_file}")


if __name__ == "__main__":
    main()
