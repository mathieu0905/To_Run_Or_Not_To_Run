#!/usr/bin/env python3
"""
分析模型"只修改一次代码后不再修改"的比例

研究问题：在 prohibited (run_free) 和 unrestricted (run_full) 模式下，
模型第一次修改代码后就不再修改的比例是多少？

这有助于理解：
- 模型是否倾向于"一次修复"还是"迭代修复"
- 执行权限对修改行为的影响
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Set
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


@dataclass
class EditInfo:
    """记录一次编辑操作的信息"""
    file_path: str
    tool_name: str  # Edit or Write
    turn_number: int


@dataclass
class InstanceAnalysis:
    """单个实例的分析结果"""
    instance_id: str
    mode: str
    total_edits: int = 0  # 总编辑次数
    unique_files_edited: int = 0  # 编辑的唯一文件数
    edits_per_file: Dict[str, int] = field(default_factory=dict)  # 每个文件被编辑的次数
    first_edit_turn: int = -1  # 第一次编辑的turn
    last_edit_turn: int = -1  # 最后一次编辑的turn
    total_turns: int = 0  # 总turn数
    only_one_edit_session: bool = False  # 是否只有一次编辑（对同一文件只编辑一次）


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
    if 'test' in path_lower.split('/')[-1] and 'test' != path_lower.split('/')[-1].replace('.py', ''):
        return False

    # 排除临时/调试文件
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return False
    if 'script' in path_lower.split('/')[-1]:
        return False

    # 排除根目录的临时脚本
    if path_lower.count('/') == 0 and path_lower.endswith('.py'):
        return False
    if path_lower.startswith('/testbed/') and path_lower.count('/') == 2 and path_lower.endswith('.py'):
        # /testbed/xxx.py 是临时脚本
        return False

    # 只关注 .py 文件
    if not path_lower.endswith('.py'):
        return False

    return True


def analyze_trace(trace_path: Path) -> InstanceAnalysis:
    """分析单个trace文件"""
    instance_id = trace_path.parent.name
    mode = trace_path.parent.parent.name

    analysis = InstanceAnalysis(instance_id=instance_id, mode=mode)

    edits: List[EditInfo] = []
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

                # 检查是否是编辑操作
                if entry.get('type') == 'assistant':
                    message = entry.get('message', {})
                    content = message.get('content', [])

                    for item in content:
                        if isinstance(item, dict) and item.get('type') == 'tool_use':
                            tool_name = item.get('name', '')
                            if tool_name in ('Edit', 'Write'):
                                input_data = item.get('input', {})
                                file_path = input_data.get('file_path', '')

                                if is_source_file(file_path):
                                    edits.append(EditInfo(
                                        file_path=file_path,
                                        tool_name=tool_name,
                                        turn_number=turn_number
                                    ))
    except Exception as e:
        print(f"Error processing {trace_path}: {e}")
        return analysis

    analysis.total_turns = turn_number

    if not edits:
        return analysis

    # 统计编辑信息
    analysis.total_edits = len(edits)

    file_edits = defaultdict(list)
    for edit in edits:
        file_edits[edit.file_path].append(edit.turn_number)

    analysis.unique_files_edited = len(file_edits)
    analysis.edits_per_file = {f: len(turns) for f, turns in file_edits.items()}

    analysis.first_edit_turn = min(e.turn_number for e in edits)
    analysis.last_edit_turn = max(e.turn_number for e in edits)

    # 判断是否只有一次编辑session
    # 定义：每个文件只被编辑一次
    analysis.only_one_edit_session = all(count == 1 for count in analysis.edits_per_file.values())

    return analysis


def find_trace_files(mode: str) -> List[Path]:
    """查找指定模式的所有trace文件"""
    traces = []

    # 映射：prohibited -> run_free, unrestricted -> run_full
    mode_mapping = {
        'prohibited': 'run_free',
        'unrestricted': 'run_full',
        'run_free': 'run_free',
        'run_full': 'run_full',
    }

    actual_mode = mode_mapping.get(mode, mode)

    for dataset_dir in OUTPUT_DIR.iterdir():
        if not dataset_dir.is_dir():
            continue

        # 检查 claude_code 目录
        claude_code_dir = dataset_dir / "claude_code" / actual_mode
        if claude_code_dir.exists():
            for instance_dir in claude_code_dir.iterdir():
                trace_file = instance_dir / "trace.jsonl"
                if trace_file.exists():
                    traces.append(trace_file)

    return traces


def analyze_mode(mode: str) -> Dict:
    """分析指定模式的所有实例"""
    traces = find_trace_files(mode)

    print(f"\n{'='*60}")
    print(f"分析模式: {mode}")
    print(f"找到 {len(traces)} 个trace文件")
    print('='*60)

    analyses = []
    for trace in traces:
        analysis = analyze_trace(trace)
        if analysis.total_edits > 0:  # 只统计有编辑的实例
            analyses.append(analysis)

    if not analyses:
        return {"mode": mode, "total_instances": 0}

    # 统计
    total_instances = len(analyses)
    single_edit_instances = sum(1 for a in analyses if a.only_one_edit_session)
    multiple_edit_instances = total_instances - single_edit_instances

    single_edit_ratio = single_edit_instances / total_instances if total_instances > 0 else 0

    # 更详细的统计
    avg_edits = sum(a.total_edits for a in analyses) / total_instances
    avg_files = sum(a.unique_files_edited for a in analyses) / total_instances

    # 统计编辑次数分布
    edit_count_dist = defaultdict(int)
    for a in analyses:
        max_edits_per_file = max(a.edits_per_file.values()) if a.edits_per_file else 0
        edit_count_dist[max_edits_per_file] += 1

    result = {
        "mode": mode,
        "total_instances": total_instances,
        "single_edit_instances": single_edit_instances,
        "multiple_edit_instances": multiple_edit_instances,
        "single_edit_ratio": single_edit_ratio,
        "avg_edits_per_instance": avg_edits,
        "avg_files_per_instance": avg_files,
        "max_edits_per_file_distribution": dict(sorted(edit_count_dist.items())),
    }

    # 打印结果
    print(f"\n总实例数（有编辑）: {total_instances}")
    print(f"只修改一次的实例: {single_edit_instances} ({single_edit_ratio:.1%})")
    print(f"多次修改的实例: {multiple_edit_instances} ({1-single_edit_ratio:.1%})")
    print(f"\n平均每实例编辑次数: {avg_edits:.2f}")
    print(f"平均每实例编辑文件数: {avg_files:.2f}")
    print(f"\n每文件最大编辑次数分布:")
    for count, num in sorted(edit_count_dist.items()):
        print(f"  {count}次: {num} 个实例 ({num/total_instances:.1%})")

    # 列出多次修改的实例
    if multiple_edit_instances > 0:
        print(f"\n多次修改的实例详情:")
        for a in analyses:
            if not a.only_one_edit_session:
                files_info = ", ".join(f"{f.split('/')[-1]}({c}次)"
                                      for f, c in a.edits_per_file.items())
                print(f"  {a.instance_id}: {files_info}")

    return result


def main():
    print("="*70)
    print("分析: 模型只修改一次代码后不再修改的比例")
    print("="*70)

    results = {}

    # 分析 prohibited (run_free) 模式
    results['prohibited'] = analyze_mode('prohibited')

    # 分析 unrestricted (run_full) 模式
    results['unrestricted'] = analyze_mode('unrestricted')

    # 对比分析
    print("\n" + "="*70)
    print("对比分析")
    print("="*70)

    if results['prohibited']['total_instances'] > 0 and results['unrestricted']['total_instances'] > 0:
        p_ratio = results['prohibited']['single_edit_ratio']
        u_ratio = results['unrestricted']['single_edit_ratio']

        print(f"\n只修改一次代码后不再修改的比例:")
        print(f"  Prohibited (run_free):   {p_ratio:.1%} ({results['prohibited']['single_edit_instances']}/{results['prohibited']['total_instances']})")
        print(f"  Unrestricted (run_full): {u_ratio:.1%} ({results['unrestricted']['single_edit_instances']}/{results['unrestricted']['total_instances']})")

        diff = p_ratio - u_ratio
        print(f"\n差异: {diff:+.1%}")

        if diff > 0.05:
            print("→ Prohibited模式下更倾向于一次性修复（无法通过执行反馈迭代）")
        elif diff < -0.05:
            print("→ Unrestricted模式下更倾向于一次性修复（可能一次就修对了）")
        else:
            print("→ 两种模式下一次性修复比例相近")

    # 保存结果
    output_file = ANALYSIS_DIR / "single_edit_ratio_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n结果已保存到: {output_file}")

    # 生成 Markdown 报告
    md_file = ANALYSIS_DIR / "single_edit_ratio_analysis.md"
    with open(md_file, 'w') as f:
        f.write("# 代码修改次数分析\n\n")
        f.write("## 研究问题\n\n")
        f.write("模型在修改一次代码之后这个代码后面就不再修改了，这个比例大概是多少？\n\n")
        f.write("## 方法\n\n")
        f.write("- 统计每个实例中对源代码文件（排除测试文件和临时脚本）的编辑操作\n")
        f.write("- 如果每个被编辑的文件都只被编辑了一次，则认为是\"只修改一次\"\n")
        f.write("- 分别分析 Prohibited (run_free) 和 Unrestricted (run_full) 模式\n\n")

        f.write("## 结果\n\n")
        f.write("| 指标 | Prohibited (run_free) | Unrestricted (run_full) |\n")
        f.write("|------|----------------------|------------------------|\n")

        p = results.get('prohibited', {})
        u = results.get('unrestricted', {})

        f.write(f"| 总实例数（有编辑） | {p.get('total_instances', 0)} | {u.get('total_instances', 0)} |\n")
        f.write(f"| 只修改一次的实例 | {p.get('single_edit_instances', 0)} ({p.get('single_edit_ratio', 0):.1%}) | {u.get('single_edit_instances', 0)} ({u.get('single_edit_ratio', 0):.1%}) |\n")
        f.write(f"| 多次修改的实例 | {p.get('multiple_edit_instances', 0)} | {u.get('multiple_edit_instances', 0)} |\n")
        f.write(f"| 平均编辑次数/实例 | {p.get('avg_edits_per_instance', 0):.2f} | {u.get('avg_edits_per_instance', 0):.2f} |\n")
        f.write(f"| 平均编辑文件数/实例 | {p.get('avg_files_per_instance', 0):.2f} | {u.get('avg_files_per_instance', 0):.2f} |\n")

        f.write("\n## 关键发现\n\n")

        if p.get('total_instances', 0) > 0 and u.get('total_instances', 0) > 0:
            p_ratio = p.get('single_edit_ratio', 0)
            u_ratio = u.get('single_edit_ratio', 0)

            f.write(f"1. **Prohibited 模式**: {p_ratio:.1%} 的实例只修改一次代码后不再修改\n")
            f.write(f"2. **Unrestricted 模式**: {u_ratio:.1%} 的实例只修改一次代码后不再修改\n")

            diff = p_ratio - u_ratio
            if abs(diff) > 0.05:
                if diff > 0:
                    f.write(f"3. Prohibited 模式比 Unrestricted 模式高 {diff:.1%}，说明无执行反馈时模型更倾向于一次性尝试修复\n")
                else:
                    f.write(f"3. Unrestricted 模式比 Prohibited 模式高 {-diff:.1%}，说明有执行反馈时模型可能更快收敛到正确答案\n")
            else:
                f.write(f"3. 两种模式差异不大（{diff:+.1%}），说明模型的修改策略相对稳定\n")

    print(f"Markdown报告已保存到: {md_file}")


if __name__ == "__main__":
    main()
