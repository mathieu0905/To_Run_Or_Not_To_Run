#!/usr/bin/env python3
"""
RQ2 深入分析：为什么 Codex 在 run_free 模式下 token 消耗没有显著降低？

核心问题：
- Codex run_free vs run_full 的 token 节省仅 0.8-13.4%
- Claude Code 的节省高达 56-62%
- 这说明 Codex 的行为模式与 Claude Code 有本质区别

分析目标：
1. 对比两种 agent 在不同模式下的命令执行模式
2. 分析 token 消耗的组成（推理 vs 命令输出）
3. 找出 Codex token 消耗高的根本原因
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import re

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def parse_trace_file(trace_path: Path) -> dict:
    """解析 trace.jsonl 文件，提取关键指标。支持 Codex 和 Claude Code 两种格式。"""
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

    # 检测格式类型
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
                    # Claude Code 格式
                    if d.get('type') == 'assistant':
                        message = d.get('message', {})
                        content = message.get('content', [])
                        usage = message.get('usage', {})

                        # 累加 token
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
                                # Claude Code 没有单独的 reasoning 类型，文本输出可以视为推理
                                if item.get('text', '').strip():
                                    result['reasoning_count'] += 1
                else:
                    # Codex 格式
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

                    # 提取 token 使用量
                    if d.get('type') == 'turn.completed':
                        usage = d.get('usage', {})
                        result['input_tokens'] = usage.get('input_tokens', 0)
                        result['output_tokens'] = usage.get('output_tokens', 0)
                        result['cached_tokens'] = usage.get('cached_input_tokens', 0)

            except json.JSONDecodeError:
                continue

    return result


def classify_command(cmd: str) -> str:
    """将命令分类"""
    cmd_lower = cmd.lower()

    # 测试执行
    if any(x in cmd_lower for x in ['pytest', 'python -m pytest', 'python -m unittest', 'manage.py test', 'tox', 'nose']):
        return 'test_execution'

    # Python 代码执行（非测试）
    if 'python' in cmd_lower and ('python -c' in cmd_lower or 'python -' in cmd_lower or 'python <<' in cmd_lower):
        return 'python_snippet'

    # 文件查看
    if any(x in cmd_lower for x in ['cat ', 'head ', 'tail ', 'sed -n', 'less ', 'more ']):
        return 'file_view'

    # 搜索
    if any(x in cmd_lower for x in ['grep', 'rg ', 'find ', 'ag ']):
        return 'search'

    # 目录浏览
    if cmd_lower.strip().startswith('ls') or 'ls ' in cmd_lower:
        return 'directory_browse'

    # Git 操作
    if 'git ' in cmd_lower:
        return 'git'

    return 'other'


def analyze_agent_behavior(agent: str, dataset: str) -> dict:
    """分析特定 agent 在特定数据集上的行为"""
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
    """生成分析报告"""
    report = []
    report.append(f"# {agent} 在 {dataset} 上的行为分析\n")

    # 概览表格
    report.append("## 概览\n")
    report.append("| Mode | Instances | Avg Reasoning | Avg Commands | Avg File Changes | Avg Input Tokens | Avg Output Tokens |")
    report.append("|------|-----------|---------------|--------------|------------------|------------------|-------------------|")

    for mode in ['run_free', 'run_less_k1', 'run_less_k3', 'run_cost', 'run_full']:
        if mode not in results:
            continue
        r = results[mode]
        n = len(r['instances'])
        report.append(f"| {mode} | {n} | {r.get('avg_reasoning', 0):.1f} | {r.get('avg_commands', 0):.1f} | {r.get('avg_file_changes', 0):.1f} | {r.get('avg_input_tokens', 0):,.0f} | {r.get('avg_output_tokens', 0):,.0f} |")

    # 命令类型分布
    report.append("\n## 命令类型分布\n")
    report.append("| Mode | Test Exec | Python Snippet | File View | Search | Dir Browse | Git | Other |")
    report.append("|------|-----------|----------------|-----------|--------|------------|-----|-------|")

    for mode in ['run_free', 'run_less_k1', 'run_less_k3', 'run_cost', 'run_full']:
        if mode not in results:
            continue
        ct = results[mode]['command_types']
        report.append(f"| {mode} | {ct.get('test_execution', 0)} | {ct.get('python_snippet', 0)} | {ct.get('file_view', 0)} | {ct.get('search', 0)} | {ct.get('directory_browse', 0)} | {ct.get('git', 0)} | {ct.get('other', 0)} |")

    # 关键发现
    report.append("\n## 关键发现\n")

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

        report.append(f"- **Token 变化**: run_free vs run_full = {token_diff:+.1f}%")
        report.append(f"- **命令数变化**: run_free vs run_full = {cmd_diff:+.1f}%")

        # 分析命令类型差异
        rf_tests = rf['command_types'].get('test_execution', 0)
        rfu_tests = rfu['command_types'].get('test_execution', 0)
        rf_explore = rf['command_types'].get('file_view', 0) + rf['command_types'].get('search', 0) + rf['command_types'].get('directory_browse', 0)
        rfu_explore = rfu['command_types'].get('file_view', 0) + rfu['command_types'].get('search', 0) + rfu['command_types'].get('directory_browse', 0)

        report.append(f"- **测试执行次数**: run_free={rf_tests}, run_full={rfu_tests}")
        report.append(f"- **代码探索命令**: run_free={rf_explore}, run_full={rfu_explore}")

    return '\n'.join(report)


def main():
    """主函数"""
    print("=" * 60)
    print("RQ2 深入分析：Codex 行为模式")
    print("=" * 60)

    all_reports = []

    for dataset in ['swebenchlite', 'swebenchverified']:
        for agent in ['codex', 'claude_code']:
            print(f"\n分析 {agent} 在 {dataset} 上的行为...")

            results = analyze_agent_behavior(agent, dataset)
            if not results:
                print(f"  未找到数据")
                continue

            report = generate_report(results, agent, dataset)
            all_reports.append(report)
            print(report)

    # 保存完整报告
    output_path = Path(__file__).parent / "codex_behavior_analysis.md"
    with open(output_path, 'w') as f:
        f.write("# RQ2 深入分析：为什么 Codex 在 run_free 模式下 token 消耗没有显著降低？\n\n")
        f.write("## 核心问题\n\n")
        f.write("- Codex run_free vs run_full 的 token 节省仅 0.8-13.4%\n")
        f.write("- Claude Code 的节省高达 56-62%\n")
        f.write("- 这说明 Codex 的行为模式与 Claude Code 有本质区别\n\n")
        f.write('\n\n---\n\n'.join(all_reports))

    print(f"\n报告已保存到: {output_path}")


if __name__ == '__main__':
    main()
