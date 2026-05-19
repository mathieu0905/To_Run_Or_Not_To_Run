#!/usr/bin/env python3
"""
分析模型"只修改一次代码后不再修改"的比例 v4

修复：
1. Codex 使用 file_change 类型记录编辑，不是 file_edit
2. 正确统计 claude_code 和 codex 两个 agent
3. 使用 data_loader.py 中的执行定义
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

EXCLUDED_AGENTS = ["claude_code_glm"]


def is_execution(cmd: str) -> bool:
    """判断是否是执行命令"""
    if not cmd:
        return False
    if any(p in cmd for p in HIGH_COST_PATTERNS):
        return True
    if PYTHON_SCRIPT_PATTERN.search(cmd):
        return True
    return False


def is_source_file(path: str) -> bool:
    """判断是否是源代码文件"""
    if not path:
        return False
    path_lower = path.lower()

    # 排除测试文件
    if '/test_' in path_lower or '/tests/' in path_lower:
        return False
    if path_lower.endswith('_test.py'):
        return False

    # 排除临时文件
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return False
    if 'demo' in path_lower or 'example' in path_lower:
        return False

    # 排除 /testbed/xxx.py
    if '/testbed/' in path_lower:
        parts = path_lower.split('/testbed/')[-1].split('/')
        if len(parts) == 1 and parts[0].endswith('.py'):
            return False

    if not path_lower.endswith('.py'):
        return False

    return True


@dataclass
class Event:
    timestamp: int
    turn_number: int


@dataclass
class EditEvent(Event):
    file_path: str
    tool_name: str


@dataclass
class ExecEvent(Event):
    command: str


@dataclass
class InstanceAnalysis:
    instance_id: str
    mode: str
    agent: str
    dataset: str

    total_source_edits: int = 0
    unique_source_files: int = 0
    edits_per_file: Dict[str, int] = field(default_factory=dict)
    only_one_edit_globally: bool = False

    total_executions: int = 0
    edits_after_exec: int = 0
    has_edit_after_exec: bool = False

    has_multiple_edits: bool = False
    multiple_edit_triggered_by_exec: bool = False
    multiple_edit_without_exec: bool = False


def parse_trace_claude_code(trace_path: Path) -> tuple[List[EditEvent], List[ExecEvent]]:
    """解析 Claude Code 格式"""
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
    """解析 Codex 格式 - 使用 file_change 和 command_execution"""
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

            # turn 计数
            if entry.get('type') == 'turn.started':
                turn_number += 1

            # Codex 的 item.completed 事件
            if entry.get('type') == 'item.completed':
                inner = entry.get('item', {})
                item_type = inner.get('type', '')

                # 文件编辑 - Codex 使用 file_change
                if item_type == 'file_change':
                    changes = inner.get('changes', [])
                    for change in changes:
                        file_path = change.get('path', '')
                        if is_source_file(file_path):
                            edits.append(EditEvent(
                                timestamp=event_idx,
                                turn_number=turn_number,
                                file_path=file_path,
                                tool_name='file_change'
                            ))
                            event_idx += 1

                # 命令执行
                elif item_type == 'command_execution':
                    command = inner.get('command', '')
                    if is_execution(command):
                        execs.append(ExecEvent(
                            timestamp=event_idx,
                            turn_number=turn_number,
                            command=command
                        ))
                        event_idx += 1

    return edits, execs


def analyze_trace(trace_path: Path) -> Optional[InstanceAnalysis]:
    """分析单个 trace"""
    try:
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

    analysis.total_source_edits = len(edits)
    analysis.total_executions = len(execs)

    if not edits:
        return analysis

    # 按文件统计
    file_edit_counts = defaultdict(int)
    for edit in edits:
        file_edit_counts[edit.file_path] += 1

    analysis.unique_source_files = len(file_edit_counts)
    analysis.edits_per_file = dict(file_edit_counts)
    analysis.only_one_edit_globally = all(count == 1 for count in file_edit_counts.values())
    analysis.has_multiple_edits = any(count > 1 for count in file_edit_counts.values())

    # 执行后修改
    if execs:
        first_exec_ts = min(e.timestamp for e in execs)
        edits_after = [e for e in edits if e.timestamp > first_exec_ts]
        analysis.edits_after_exec = len(edits_after)
        analysis.has_edit_after_exec = len(edits_after) > 0

    # 二次修改触发分析
    if analysis.has_multiple_edits:
        multi_edit_files = [f for f, c in file_edit_counts.items() if c > 1]
        exec_timestamps = [e.timestamp for e in execs]

        triggered_by_exec = False
        for f in multi_edit_files:
            file_edits = sorted([e.timestamp for e in edits if e.file_path == f])
            if len(file_edits) >= 2:
                first_ts, second_ts = file_edits[0], file_edits[1]
                if any(first_ts < ts < second_ts for ts in exec_timestamps):
                    triggered_by_exec = True
                    break

        analysis.multiple_edit_triggered_by_exec = triggered_by_exec
        analysis.multiple_edit_without_exec = not triggered_by_exec

    return analysis


def find_all_traces(mode: str) -> List[Path]:
    """查找所有 trace 文件"""
    traces = []
    mode_mapping = {'prohibited': 'run_free', 'unrestricted': 'run_full'}
    actual_mode = mode_mapping.get(mode, mode)

    for dataset_dir in OUTPUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue
        for agent_dir in dataset_dir.iterdir():
            if not agent_dir.is_dir() or agent_dir.name in EXCLUDED_AGENTS:
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

    with_edits = [a for a in analyses if a.total_source_edits > 0]
    total = len(with_edits)

    by_agent = defaultdict(list)
    for a in with_edits:
        by_agent[a.agent].append(a)

    print(f"\n总 trace 数: {len(analyses)}")
    print(f"有源文件编辑的实例: {total}")
    for agent in sorted(by_agent.keys()):
        print(f"  {agent}: {len(by_agent[agent])}")

    if total == 0:
        return {"mode": mode, "total_instances": 0}

    # 1. 全局统计
    single_edit = sum(1 for a in with_edits if a.only_one_edit_globally)
    multiple_edit = total - single_edit
    single_ratio = single_edit / total

    print(f"\n【1. 全局统计】每个源文件只编辑一次的比例")
    print(f"  只编辑一次: {single_edit}/{total} ({single_ratio:.1%})")
    print(f"  多次编辑:   {multiple_edit}/{total} ({1-single_ratio:.1%})")
    for agent in sorted(by_agent.keys()):
        agent_list = by_agent[agent]
        agent_single = sum(1 for a in agent_list if a.only_one_edit_globally)
        print(f"    {agent}: {agent_single}/{len(agent_list)} ({agent_single/len(agent_list):.1%})")

    # 2. 执行后修改
    with_exec = [a for a in with_edits if a.total_executions > 0]
    if with_exec:
        with_exec_total = len(with_exec)
        edit_after = sum(1 for a in with_exec if a.has_edit_after_exec)
        edit_after_ratio = edit_after / with_exec_total

        print(f"\n【2. 执行后修改】有执行的实例中")
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

    # 3. 二次修改触发
    with_multiple = [a for a in with_edits if a.has_multiple_edits]
    if with_multiple:
        triggered_by_exec = sum(1 for a in with_multiple if a.multiple_edit_triggered_by_exec)
        without_exec = sum(1 for a in with_multiple if a.multiple_edit_without_exec)

        print(f"\n【3. 二次修改触发原因】")
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

    return {
        "mode": mode,
        "total_traces": len(analyses),
        "total_with_edits": total,
        "global_single_edit": single_edit,
        "global_multiple_edit": multiple_edit,
        "global_single_ratio": single_ratio,
        "instances_with_exec": with_exec_total,
        "edit_after_exec": edit_after,
        "edit_after_exec_ratio": edit_after_ratio,
        "instances_with_multiple_edits": len(with_multiple) if with_multiple else 0,
        "multiple_triggered_by_exec": triggered_by_exec,
        "multiple_without_exec": without_exec,
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
    print("分析: 模型只修改一次代码后不再修改的比例 v4")
    print("="*70)

    results = {}
    results['prohibited'] = analyze_mode('prohibited')
    results['unrestricted'] = analyze_mode('unrestricted')

    # 对比
    print("\n" + "="*70)
    print("对比总结")
    print("="*70)

    p = results['prohibited']
    u = results['unrestricted']

    print(f"\n{'':30} {'Prohibited':>12} {'Unrestricted':>12}")
    print(f"{'总 trace 数':30} {p['total_traces']:>12} {u['total_traces']:>12}")
    print(f"{'有源文件编辑':30} {p['total_with_edits']:>12} {u['total_with_edits']:>12}")
    print()
    print(f"{'【全局只编辑一次】':30}")
    print(f"{'  比例':30} {p['global_single_ratio']:>12.1%} {u['global_single_ratio']:>12.1%}")
    print(f"{'  数量':30} {p['global_single_edit']:>12} {u['global_single_edit']:>12}")
    print()
    print(f"{'【执行后修改】':30}")
    print(f"{'  有执行的实例':30} {p['instances_with_exec']:>12} {u['instances_with_exec']:>12}")
    if p['instances_with_exec'] > 0 and u['instances_with_exec'] > 0:
        print(f"{'  执行后修改比例':30} {p['edit_after_exec_ratio']:>12.1%} {u['edit_after_exec_ratio']:>12.1%}")
    print()
    print(f"{'【二次修改触发原因】':30}")
    print(f"{'  有多次编辑的实例':30} {p['instances_with_multiple_edits']:>12} {u['instances_with_multiple_edits']:>12}")
    if p['instances_with_multiple_edits'] > 0:
        p_ratio = p['multiple_triggered_by_exec'] / p['instances_with_multiple_edits']
        print(f"{'  由执行触发 (prohibited)':30} {p_ratio:>12.1%}")
    if u['instances_with_multiple_edits'] > 0:
        u_ratio = u['multiple_triggered_by_exec'] / u['instances_with_multiple_edits']
        print(f"{'  由执行触发 (unrestricted)':30} {u_ratio:>12.1%}")

    # 保存
    output_file = ANALYSIS_DIR / "single_edit_ratio_analysis_v4.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n结果已保存到: {output_file}")

    # Markdown
    md_file = ANALYSIS_DIR / "single_edit_ratio_analysis_v4.md"
    with open(md_file, 'w') as f:
        f.write("# 代码修改次数分析 v4\n\n")
        f.write("## 研究问题\n\n")
        f.write("1. 模型在修改一次代码之后就不再修改的比例是多少？\n")
        f.write("2. 执行后进行修改的比例是多少？\n")
        f.write("3. 二次修改是否都由执行触发？\n\n")

        f.write("## 数据\n\n")
        f.write(f"- Prohibited: {p['total_traces']} traces ({p['total_with_edits']} 有编辑)\n")
        f.write(f"- Unrestricted: {u['total_traces']} traces ({u['total_with_edits']} 有编辑)\n")
        f.write("- Agent: claude_code + codex\n\n")

        f.write("## 结果\n\n")
        f.write("### 1. 全局：只编辑一次后不再编辑\n\n")
        f.write("| 模式 | 有编辑 | 只编辑一次 | 多次编辑 | 比例 |\n")
        f.write("|------|-------|-----------|---------|------|\n")
        f.write(f"| Prohibited | {p['total_with_edits']} | {p['global_single_edit']} | {p['global_multiple_edit']} | **{p['global_single_ratio']:.1%}** |\n")
        f.write(f"| Unrestricted | {u['total_with_edits']} | {u['global_single_edit']} | {u['global_multiple_edit']} | **{u['global_single_ratio']:.1%}** |\n")

        f.write("\n### 2. 执行后修改\n\n")
        f.write("| 模式 | 有执行 | 执行后修改 | 执行后无修改 | 修改比例 |\n")
        f.write("|------|-------|-----------|-------------|----------|\n")
        if p['instances_with_exec'] > 0:
            f.write(f"| Prohibited | {p['instances_with_exec']} | {p['edit_after_exec']} | {p['instances_with_exec']-p['edit_after_exec']} | **{p['edit_after_exec_ratio']:.1%}** |\n")
        if u['instances_with_exec'] > 0:
            f.write(f"| Unrestricted | {u['instances_with_exec']} | {u['edit_after_exec']} | {u['instances_with_exec']-u['edit_after_exec']} | **{u['edit_after_exec_ratio']:.1%}** |\n")

        f.write("\n### 3. 二次修改触发原因\n\n")
        f.write("| 模式 | 多次编辑 | 执行触发 | 非执行触发 | 执行触发比例 |\n")
        f.write("|------|---------|---------|-----------|-------------|\n")
        if p['instances_with_multiple_edits'] > 0:
            p_r = p['multiple_triggered_by_exec'] / p['instances_with_multiple_edits']
            f.write(f"| Prohibited | {p['instances_with_multiple_edits']} | {p['multiple_triggered_by_exec']} | {p['multiple_without_exec']} | **{p_r:.1%}** |\n")
        if u['instances_with_multiple_edits'] > 0:
            u_r = u['multiple_triggered_by_exec'] / u['instances_with_multiple_edits']
            f.write(f"| Unrestricted | {u['instances_with_multiple_edits']} | {u['multiple_triggered_by_exec']} | {u['multiple_without_exec']} | **{u_r:.1%}** |\n")

        f.write("\n### 按 Agent 分组\n\n")
        f.write("| Agent | 模式 | 总数 | 只编辑一次 | 有执行 | 执行后修改 | 多次编辑 | 执行触发 |\n")
        f.write("|-------|------|-----|-----------|-------|-----------|---------|----------|\n")
        for agent in sorted(set(p.get('by_agent', {}).keys()) | set(u.get('by_agent', {}).keys())):
            for mode_name, mode_data in [('Prohibited', p), ('Unrestricted', u)]:
                ad = mode_data.get('by_agent', {}).get(agent, {})
                if ad:
                    t = ad.get('total', 0)
                    s = ad.get('single_edit', 0)
                    we = ad.get('with_exec', 0)
                    ea = ad.get('edit_after_exec', 0)
                    me = ad.get('multiple_edits', 0)
                    mbe = ad.get('multi_by_exec', 0)
                    sr = f"{s/t:.1%}" if t > 0 else "-"
                    ear = f"{ea}/{we}" if we > 0 else "-"
                    mber = f"{mbe}/{me}" if me > 0 else "-"
                    f.write(f"| {agent} | {mode_name} | {t} | {sr} | {we} | {ear} | {me} | {mber} |\n")

        f.write("\n## 关键发现\n\n")
        f.write(f"1. **全局只编辑一次**：Prohibited {p['global_single_ratio']:.1%} vs Unrestricted {u['global_single_ratio']:.1%}\n")
        if u['instances_with_exec'] > 0:
            f.write(f"2. **执行后修改**：Unrestricted 中 {u['edit_after_exec_ratio']:.1%} 会在执行后修改\n")
        if u['instances_with_multiple_edits'] > 0:
            u_r = u['multiple_triggered_by_exec'] / u['instances_with_multiple_edits']
            f.write(f"3. **二次修改触发**：Unrestricted 中仅 {u_r:.1%} 的二次修改由执行触发\n")

    print(f"Markdown 已保存到: {md_file}")


if __name__ == "__main__":
    main()
