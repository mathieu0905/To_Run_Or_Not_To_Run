#!/usr/bin/env python3
"""
分析模型"只修改一次代码后不再修改"的比例 v5

修复：
1. 不过度过滤文件 - 统计所有 .py 文件的编辑（排除临时脚本）
2. 正确统计 claude_code 和 codex
3. 报告 prohibited 模式下的违规执行情况
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent

# 执行定义
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
    if not cmd:
        return False
    if any(p in cmd for p in HIGH_COST_PATTERNS):
        return True
    if PYTHON_SCRIPT_PATTERN.search(cmd):
        return True
    return False


def is_code_file(path: str) -> bool:
    """判断是否是代码文件（包括源文件和测试文件，但排除临时脚本）"""
    if not path:
        return False
    path_lower = path.lower()

    if not path_lower.endswith('.py'):
        return False

    # 排除临时脚本（/testbed/xxx.py 或 reproduce/debug 脚本）
    if '/testbed/' in path_lower:
        parts = path_lower.split('/testbed/')[-1].split('/')
        # /testbed/xxx.py 是临时脚本
        if len(parts) == 1:
            return False

    # 排除常见临时文件名
    filename = path_lower.split('/')[-1]
    temp_names = ['reproduce', 'debug', 'demo', 'example', 'scratch', 'temp', 'tmp']
    if any(t in filename for t in temp_names):
        return False

    return True


@dataclass
class Event:
    timestamp: int
    turn_number: int


@dataclass
class EditEvent(Event):
    file_path: str


@dataclass
class ExecEvent(Event):
    command: str


@dataclass
class InstanceAnalysis:
    instance_id: str
    mode: str
    agent: str
    dataset: str

    total_edits: int = 0
    unique_files: int = 0
    edits_per_file: Dict[str, int] = field(default_factory=dict)
    only_one_edit: bool = False

    total_executions: int = 0
    has_edit_after_exec: bool = False

    has_multiple_edits: bool = False
    multiple_triggered_by_exec: bool = False


def parse_trace_claude_code(trace_path: Path) -> tuple[List[EditEvent], List[ExecEvent]]:
    edits, execs = [], []
    event_idx, turn = 0, 0

    with open(trace_path) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except:
                continue

            if entry.get('type') == 'assistant':
                turn += 1
                for item in entry.get('message', {}).get('content', []):
                    if isinstance(item, dict) and item.get('type') == 'tool_use':
                        name = item.get('name', '')
                        inp = item.get('input', {})

                        if name in ('Edit', 'Write'):
                            fp = inp.get('file_path', '')
                            if is_code_file(fp):
                                edits.append(EditEvent(event_idx, turn, fp))
                                event_idx += 1
                        elif name == 'Bash':
                            cmd = inp.get('command', '')
                            if is_execution(cmd):
                                execs.append(ExecEvent(event_idx, turn, cmd))
                                event_idx += 1
    return edits, execs


def parse_trace_codex(trace_path: Path) -> tuple[List[EditEvent], List[ExecEvent]]:
    edits, execs = [], []
    event_idx, turn = 0, 0

    with open(trace_path) as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except:
                continue

            if entry.get('type') == 'turn.started':
                turn += 1

            if entry.get('type') == 'item.completed':
                item = entry.get('item', {})
                itype = item.get('type', '')

                if itype == 'file_change':
                    for c in item.get('changes', []):
                        fp = c.get('path', '')
                        if is_code_file(fp):
                            edits.append(EditEvent(event_idx, turn, fp))
                            event_idx += 1

                elif itype == 'command_execution':
                    cmd = item.get('command', '')
                    if is_execution(cmd):
                        execs.append(ExecEvent(event_idx, turn, cmd))
                        event_idx += 1
    return edits, execs


def analyze_trace(trace_path: Path) -> Optional[InstanceAnalysis]:
    try:
        instance_id = trace_path.parent.name
        mode = trace_path.parent.parent.name
        agent = trace_path.parent.parent.parent.name
        dataset = trace_path.parent.parent.parent.parent.name
    except:
        return None

    if agent in EXCLUDED_AGENTS:
        return None

    analysis = InstanceAnalysis(instance_id, mode, agent, dataset)

    if agent == 'codex':
        edits, execs = parse_trace_codex(trace_path)
    else:
        edits, execs = parse_trace_claude_code(trace_path)

    analysis.total_edits = len(edits)
    analysis.total_executions = len(execs)

    if not edits:
        return analysis

    file_counts = defaultdict(int)
    for e in edits:
        file_counts[e.file_path] += 1

    analysis.unique_files = len(file_counts)
    analysis.edits_per_file = dict(file_counts)
    analysis.only_one_edit = all(c == 1 for c in file_counts.values())
    analysis.has_multiple_edits = any(c > 1 for c in file_counts.values())

    if execs:
        first_exec = min(e.timestamp for e in execs)
        analysis.has_edit_after_exec = any(e.timestamp > first_exec for e in edits)

    if analysis.has_multiple_edits and execs:
        exec_ts = [e.timestamp for e in execs]
        for fp, cnt in file_counts.items():
            if cnt > 1:
                file_ts = sorted(e.timestamp for e in edits if e.file_path == fp)
                if len(file_ts) >= 2:
                    if any(file_ts[0] < ts < file_ts[1] for ts in exec_ts):
                        analysis.multiple_triggered_by_exec = True
                        break

    return analysis


def find_traces(mode: str) -> List[Path]:
    mode_map = {'prohibited': 'run_free', 'unrestricted': 'run_full'}
    actual = mode_map.get(mode, mode)
    traces = []

    for ds in OUTPUT_DIR.iterdir():
        if not ds.is_dir():
            continue
        for ag in ds.iterdir():
            if not ag.is_dir() or ag.name in EXCLUDED_AGENTS:
                continue
            if ag.name not in ('claude_code', 'codex'):
                continue
            md = ag / actual
            if md.exists():
                for inst in md.iterdir():
                    tf = inst / 'trace.jsonl'
                    if tf.exists():
                        traces.append(tf)
    return traces


def analyze_mode(mode: str) -> Dict:
    traces = find_traces(mode)

    print(f"\n{'='*70}")
    print(f"模式: {mode} (找到 {len(traces)} 个 trace)")
    print('='*70)

    analyses = []
    for t in traces:
        try:
            a = analyze_trace(t)
            if a:
                analyses.append(a)
        except Exception as e:
            print(f"Error: {t}: {e}")

    with_edits = [a for a in analyses if a.total_edits > 0]
    total = len(with_edits)

    by_agent = defaultdict(list)
    for a in with_edits:
        by_agent[a.agent].append(a)

    print(f"\n总 trace: {len(analyses)}, 有编辑: {total}")
    for ag in sorted(by_agent):
        print(f"  {ag}: {len(by_agent[ag])}")

    if total == 0:
        return {"mode": mode, "total": 0}

    # 1. 全局只编辑一次
    single = sum(1 for a in with_edits if a.only_one_edit)
    print(f"\n【全局只编辑一次】{single}/{total} ({single/total:.1%})")
    for ag in sorted(by_agent):
        lst = by_agent[ag]
        s = sum(1 for a in lst if a.only_one_edit)
        print(f"  {ag}: {s}/{len(lst)} ({s/len(lst):.1%})")

    # 2. 执行后修改
    with_exec = [a for a in with_edits if a.total_executions > 0]
    print(f"\n【有执行的实例】{len(with_exec)}")
    for ag in sorted(by_agent):
        lst = [a for a in by_agent[ag] if a.total_executions > 0]
        print(f"  {ag}: {len(lst)}")

    if with_exec:
        edit_after = sum(1 for a in with_exec if a.has_edit_after_exec)
        print(f"\n【执行后修改】{edit_after}/{len(with_exec)} ({edit_after/len(with_exec):.1%})")
        for ag in sorted(by_agent):
            lst = [a for a in by_agent[ag] if a.total_executions > 0]
            if lst:
                ea = sum(1 for a in lst if a.has_edit_after_exec)
                print(f"  {ag}: {ea}/{len(lst)} ({ea/len(lst):.1%})")
    else:
        edit_after = 0

    # 3. 二次修改触发
    with_multi = [a for a in with_edits if a.has_multiple_edits]
    if with_multi:
        by_exec = sum(1 for a in with_multi if a.multiple_triggered_by_exec)
        print(f"\n【二次修改触发】共 {len(with_multi)} 个多次编辑实例")
        print(f"  由执行触发: {by_exec} ({by_exec/len(with_multi):.1%})")
        print(f"  非执行触发: {len(with_multi)-by_exec} ({(len(with_multi)-by_exec)/len(with_multi):.1%})")
        for ag in sorted(by_agent):
            lst = [a for a in by_agent[ag] if a.has_multiple_edits]
            if lst:
                be = sum(1 for a in lst if a.multiple_triggered_by_exec)
                print(f"  {ag}: 执行触发 {be}/{len(lst)} ({be/len(lst):.1%})")
    else:
        by_exec = 0

    return {
        "mode": mode,
        "total_traces": len(analyses),
        "total_with_edits": total,
        "single_edit": single,
        "single_ratio": single / total,
        "with_exec": len(with_exec),
        "edit_after_exec": edit_after,
        "edit_after_ratio": edit_after / len(with_exec) if with_exec else 0,
        "multiple_edits": len(with_multi) if with_multi else 0,
        "multi_by_exec": by_exec,
        "by_agent": {
            ag: {
                "total": len(lst),
                "single": sum(1 for a in lst if a.only_one_edit),
                "with_exec": len([a for a in lst if a.total_executions > 0]),
                "edit_after": sum(1 for a in lst if a.total_executions > 0 and a.has_edit_after_exec),
                "multi": sum(1 for a in lst if a.has_multiple_edits),
                "multi_by_exec": sum(1 for a in lst if a.multiple_triggered_by_exec),
            }
            for ag, lst in by_agent.items()
        }
    }


def main():
    print("="*70)
    print("代码修改次数分析 v5")
    print("="*70)

    results = {}
    results['prohibited'] = analyze_mode('prohibited')
    results['unrestricted'] = analyze_mode('unrestricted')

    p, u = results['prohibited'], results['unrestricted']

    print("\n" + "="*70)
    print("总结对比")
    print("="*70)
    print(f"\n{'指标':<30} {'Prohibited':>12} {'Unrestricted':>12}")
    print("-"*56)
    print(f"{'总 trace 数':<30} {p['total_traces']:>12} {u['total_traces']:>12}")
    print(f"{'有编辑的实例':<30} {p['total_with_edits']:>12} {u['total_with_edits']:>12}")
    print(f"{'只编辑一次比例':<30} {p['single_ratio']:>12.1%} {u['single_ratio']:>12.1%}")
    print(f"{'有执行的实例':<30} {p['with_exec']:>12} {u['with_exec']:>12}")
    if p['with_exec'] > 0 and u['with_exec'] > 0:
        print(f"{'执行后修改比例':<30} {p['edit_after_ratio']:>12.1%} {u['edit_after_ratio']:>12.1%}")
    print(f"{'有多次编辑的实例':<30} {p['multiple_edits']:>12} {u['multiple_edits']:>12}")
    if p['multiple_edits'] > 0:
        print(f"{'执行触发比例 (prohibited)':<30} {p['multi_by_exec']/p['multiple_edits']:>12.1%}")
    if u['multiple_edits'] > 0:
        print(f"{'执行触发比例 (unrestricted)':<30} {u['multi_by_exec']/u['multiple_edits']:>12.1%}")

    # 保存
    with open(ANALYSIS_DIR / "single_edit_ratio_analysis_v5.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Markdown
    with open(ANALYSIS_DIR / "single_edit_ratio_analysis_v5.md", 'w') as f:
        f.write("# 代码修改次数分析 v5\n\n")
        f.write("## 数据\n\n")
        f.write(f"- Prohibited: {p['total_traces']} traces, {p['total_with_edits']} 有编辑\n")
        f.write(f"- Unrestricted: {u['total_traces']} traces, {u['total_with_edits']} 有编辑\n\n")

        f.write("## 结果\n\n")
        f.write("### 1. 只编辑一次后不再编辑\n\n")
        f.write("| 模式 | 有编辑 | 只编辑一次 | 比例 |\n")
        f.write("|------|-------|-----------|------|\n")
        f.write(f"| Prohibited | {p['total_with_edits']} | {p['single_edit']} | **{p['single_ratio']:.1%}** |\n")
        f.write(f"| Unrestricted | {u['total_with_edits']} | {u['single_edit']} | **{u['single_ratio']:.1%}** |\n\n")

        f.write("### 2. 执行后修改\n\n")
        f.write("| 模式 | 有执行 | 执行后修改 | 比例 |\n")
        f.write("|------|-------|-----------|------|\n")
        f.write(f"| Prohibited | {p['with_exec']} | {p['edit_after_exec']} | **{p['edit_after_ratio']:.1%}** |\n")
        f.write(f"| Unrestricted | {u['with_exec']} | {u['edit_after_exec']} | **{u['edit_after_ratio']:.1%}** |\n\n")

        f.write("### 3. 二次修改触发原因\n\n")
        f.write("| 模式 | 多次编辑 | 执行触发 | 比例 |\n")
        f.write("|------|---------|---------|------|\n")
        if p['multiple_edits'] > 0:
            f.write(f"| Prohibited | {p['multiple_edits']} | {p['multi_by_exec']} | **{p['multi_by_exec']/p['multiple_edits']:.1%}** |\n")
        if u['multiple_edits'] > 0:
            f.write(f"| Unrestricted | {u['multiple_edits']} | {u['multi_by_exec']} | **{u['multi_by_exec']/u['multiple_edits']:.1%}** |\n")

        f.write("\n### 按 Agent 分组\n\n")
        f.write("| Agent | 模式 | 总数 | 只编辑一次 | 有执行 | 执行后修改 |\n")
        f.write("|-------|------|-----|-----------|-------|----------|\n")
        for ag in sorted(set(p.get('by_agent', {}).keys()) | set(u.get('by_agent', {}).keys())):
            for mn, md in [('Prohibited', p), ('Unrestricted', u)]:
                ad = md.get('by_agent', {}).get(ag, {})
                if ad:
                    t = ad['total']
                    s = ad['single']
                    we = ad['with_exec']
                    ea = ad['edit_after']
                    sr = f"{s/t:.1%}" if t > 0 else "-"
                    ear = f"{ea}/{we}" if we > 0 else "-"
                    f.write(f"| {ag} | {mn} | {t} | {sr} | {we} | {ear} |\n")

        f.write("\n## 关键发现\n\n")
        f.write(f"1. **只编辑一次比例**：Prohibited {p['single_ratio']:.1%} vs Unrestricted {u['single_ratio']:.1%}，差异仅 {abs(p['single_ratio']-u['single_ratio']):.1%}\n")
        f.write(f"2. **Prohibited 违规执行**：有 {p['with_exec']} 个实例在禁止执行的模式下仍执行了测试\n")
        if u['with_exec'] > 0:
            f.write(f"3. **执行后修改**：Unrestricted 中 {u['edit_after_ratio']:.1%} 的实例执行后会修改代码\n")
        if u['multiple_edits'] > 0:
            f.write(f"4. **二次修改触发**：Unrestricted 中仅 {u['multi_by_exec']/u['multiple_edits']:.1%} 的二次修改由执行触发\n")

    print(f"\n结果已保存")


if __name__ == "__main__":
    main()
