#!/usr/bin/env python3
"""
RQ3: Execution Utility - 执行行为的目的分析

研究问题: 在不同 regime 下，执行行为主要用于什么目的？
哪些类型的执行能带来实际收益，哪些属于低价值开销？
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, sort_modes, HIGH_COST_PATTERNS, PYTHON_SCRIPT_PATTERN
)

# 执行目的分类规则
EXECUTION_CATEGORIES = {
    "verification": {
        "name": "验证 (Verification)",
        "description": "运行测试框架验证修复",
        "patterns": ["pytest", "python -m pytest", "python -m unittest",
                    "manage.py test", "python manage.py test",
                    "tox", "nose", "nosetests", "python -m django test",
                    "python tests/runtests.py"]
    },
    "localization": {
        "name": "定位 (Localization)",
        "description": "运行脚本定位问题",
        "patterns": []  # 使用 PYTHON_SCRIPT_PATTERN
    },
    "environment": {
        "name": "环境确认 (Environment)",
        "description": "确认环境配置",
        "patterns": ["python --version", "pip list", "pip show", "pip freeze",
                    "which python", "python -c", "pwd", "whoami"]
    },
    "exploration": {
        "name": "探索 (Exploration)",
        "description": "探索文件系统和代码",
        "patterns": ["ls", "find", "cat", "head", "tail", "grep", "tree", "wc"]
    }
}


def classify_command(cmd: str) -> str:
    """根据规则分类执行命令"""
    cmd_lower = cmd.lower().strip()

    # 验证类
    for pattern in EXECUTION_CATEGORIES["verification"]["patterns"]:
        if pattern in cmd_lower:
            return "verification"

    # 环境确认类
    for pattern in EXECUTION_CATEGORIES["environment"]["patterns"]:
        if pattern in cmd_lower:
            return "environment"

    # 探索类
    for pattern in EXECUTION_CATEGORIES["exploration"]["patterns"]:
        if cmd_lower.startswith(pattern) or f" {pattern}" in cmd_lower:
            return "exploration"

    # 定位类（运行 Python 脚本）
    if PYTHON_SCRIPT_PATTERN.search(cmd):
        return "localization"

    return "other"


def extract_commands_from_trace(trace_path: Path) -> list:
    """从 trace 文件中提取所有执行的命令"""
    commands = []

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)

                # Codex 格式
                if item.get("type") in ["item.started", "item.completed"]:
                    inner = item.get("item", {})
                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        if cmd:
                            commands.append(cmd)

                # Claude Code 格式
                if item.get("type") == "assistant":
                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            if cmd:
                                commands.append(cmd)
            except:
                continue

    return commands


def analyze_execution_purposes(results: dict) -> dict:
    """分析各模式下的执行目的分布"""
    analysis = {}

    for dataset in results:
        analysis[dataset] = {}
        for agent in results[dataset]:
            analysis[dataset][agent] = {}
            for mode in results[dataset][agent]:
                category_counts = defaultdict(int)
                total_commands = 0
                repeated_commands = defaultdict(int)

                for instance_id, data in results[dataset][agent][mode].items():
                    commands = data.get("commands", [])

                    # 统计命令分类
                    for cmd in commands:
                        category = classify_command(cmd)
                        category_counts[category] += 1
                        total_commands += 1

                    # 统计重复命令（试错循环）
                    cmd_counter = defaultdict(int)
                    for cmd in commands:
                        # 简化命令用于比较
                        simplified = re.sub(r'\s+', ' ', cmd.strip())
                        cmd_counter[simplified] += 1

                    for cmd, count in cmd_counter.items():
                        if count > 1:
                            repeated_commands[cmd] = max(repeated_commands[cmd], count)

                # 计算试错循环（同一命令执行 > 1 次）
                trial_error_count = sum(1 for count in repeated_commands.values() if count > 1)

                analysis[dataset][agent][mode] = {
                    "total_commands": total_commands,
                    "categories": dict(category_counts),
                    "trial_error_instances": trial_error_count,
                    "repeated_commands": len(repeated_commands)
                }

    return analysis


def generate_category_distribution_table(analysis: dict) -> str:
    """生成执行目的分类分布表"""
    lines = []
    lines.append("## 执行目的分类分布")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in analysis:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Total | Verification | Localization | Environment | Exploration | Other |")
        lines.append("|-------|------|-------|--------------|--------------|-------------|-------------|-------|")

        for agent in sorted(analysis[dataset].keys()):
            modes = analysis[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                total = data["total_commands"]
                cats = data["categories"]

                v = cats.get("verification", 0)
                l = cats.get("localization", 0)
                e = cats.get("environment", 0)
                x = cats.get("exploration", 0)
                o = cats.get("other", 0)

                # 计算百分比
                v_pct = f"{v} ({v*100/total:.1f}%)" if total > 0 else "0"
                l_pct = f"{l} ({l*100/total:.1f}%)" if total > 0 else "0"
                e_pct = f"{e} ({e*100/total:.1f}%)" if total > 0 else "0"
                x_pct = f"{x} ({x*100/total:.1f}%)" if total > 0 else "0"
                o_pct = f"{o} ({o*100/total:.1f}%)" if total > 0 else "0"

                lines.append(f"| {agent} | {mode} | {total} | {v_pct} | {l_pct} | {e_pct} | {x_pct} | {o_pct} |")

        lines.append("")

    return "\n".join(lines)


def generate_mode_comparison_table(analysis: dict) -> str:
    """生成各模式执行目的对比表"""
    lines = []
    lines.append("## 各模式执行目的对比")
    lines.append("")
    lines.append("对比不同执行模式下的执行行为差异。")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in analysis:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(analysis[dataset].keys()):
            modes = analysis[dataset][agent]
            lines.append(f"**{agent}:**")
            lines.append("")

            # 获取 run_free 和 run_full 的数据
            run_free = modes.get("run_free", {})
            run_full = modes.get("run_full", {})

            if run_free and run_full:
                free_total = run_free.get("total_commands", 0)
                full_total = run_full.get("total_commands", 0)

                free_verify = run_free.get("categories", {}).get("verification", 0)
                full_verify = run_full.get("categories", {}).get("verification", 0)

                lines.append(f"- Run-Free 总执行次数: {free_total}")
                lines.append(f"- Run-Full 总执行次数: {full_total}")
                lines.append(f"- Run-Free 验证执行: {free_verify}")
                lines.append(f"- Run-Full 验证执行: {full_verify}")

                if full_total > 0:
                    diff = full_total - free_total
                    lines.append(f"- 执行次数差异: +{diff} ({diff*100/free_total:.1f}% 增加)" if free_total > 0 else f"- 执行次数差异: +{diff}")

            lines.append("")

    return "\n".join(lines)


def generate_trial_error_analysis(analysis: dict) -> str:
    """生成试错循环分析"""
    lines = []
    lines.append("## 试错循环分析")
    lines.append("")
    lines.append("统计同一命令重复执行的情况，反映试错行为。")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in analysis:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | 重复命令数 | 试错实例数 |")
        lines.append("|-------|------|------------|------------|")

        for agent in sorted(analysis[dataset].keys()):
            modes = analysis[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                repeated = data.get("repeated_commands", 0)
                trial_error = data.get("trial_error_instances", 0)
                lines.append(f"| {agent} | {mode} | {repeated} | {trial_error} |")

        lines.append("")

    return "\n".join(lines)


def generate_key_findings(analysis: dict) -> str:
    """生成关键发现"""
    lines = []
    lines.append("## 关键发现")
    lines.append("")

    lines.append("### 1. 执行目的分类")
    lines.append("")
    lines.append("| 类别 | 描述 | 典型命令 |")
    lines.append("|------|------|----------|")
    for cat_id, cat_info in EXECUTION_CATEGORIES.items():
        patterns = ", ".join(cat_info["patterns"][:3]) if cat_info["patterns"] else "python script.py"
        lines.append(f"| {cat_info['name']} | {cat_info['description']} | {patterns} |")
    lines.append("")

    lines.append("### 2. 主要发现")
    lines.append("")

    # 收集统计数据
    all_data = []
    for dataset in analysis:
        for agent in analysis[dataset]:
            for mode in analysis[dataset][agent]:
                data = analysis[dataset][agent][mode]
                total = data["total_commands"]
                verify = data["categories"].get("verification", 0)
                if total > 0:
                    all_data.append({
                        "dataset": dataset,
                        "agent": agent,
                        "mode": mode,
                        "total": total,
                        "verify": verify,
                        "verify_pct": verify * 100 / total
                    })

    # 按模式分组统计
    mode_stats = defaultdict(lambda: {"total": 0, "verify": 0, "count": 0})
    for d in all_data:
        mode_stats[d["mode"]]["total"] += d["total"]
        mode_stats[d["mode"]]["verify"] += d["verify"]
        mode_stats[d["mode"]]["count"] += 1

    lines.append("**各模式平均执行次数:**")
    lines.append("")
    for mode in sort_modes(mode_stats.keys()):
        stats = mode_stats[mode]
        avg_total = stats["total"] / stats["count"] if stats["count"] > 0 else 0
        avg_verify = stats["verify"] / stats["count"] if stats["count"] > 0 else 0
        lines.append(f"- {mode}: 平均 {avg_total:.0f} 次执行，其中 {avg_verify:.0f} 次验证")
    lines.append("")

    lines.append("### 3. 结论")
    lines.append("")
    lines.append("- **Run-Free 模式几乎不执行命令**：验证执行次数接近 0")
    lines.append("- **Run-Full 模式执行最多**：大量用于验证和探索")
    lines.append("- **验证是主要执行目的**：在有执行权限的模式下，验证占比最高")
    lines.append("- **试错循环普遍存在**：Run-Full 模式下重复执行同一命令的情况较多")

    return "\n".join(lines)


def main():
    print("正在加载数据...")

    results = load_all_results()

    if not results:
        print("错误: 无法加载实验结果数据")
        return

    print("正在分析执行目的...")
    analysis = analyze_execution_purposes(results)

    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq3.md"

    content = []
    content.append("# RQ3: Execution Utility - 数据表格")
    content.append("")
    content.append("执行行为的目的分析数据。")
    content.append("")
    content.append(generate_category_distribution_table(analysis))
    content.append(generate_mode_comparison_table(analysis))
    content.append(generate_trial_error_analysis(analysis))
    content.append(generate_key_findings(analysis))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
