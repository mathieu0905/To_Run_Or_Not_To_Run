#!/usr/bin/env python3
"""
RQ1: Effectiveness - 执行权限对修复成功率的影响

研究问题: Run-Free、Run-Less、Run-Full 三种执行权限对 agent 修复成功率有什么影响？
是否存在"执行越多越强"的单调关系？
"""

import sys
from pathlib import Path

# 添加 common 模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, load_pass_rates, get_aggregated_stats, sort_modes
)


def generate_pass_rate_table(pass_rates: dict) -> str:
    """生成 Pass Rate 表格"""
    lines = []
    lines.append("## Pass Rate 对比表")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Resolved | Total | Pass Rate |")
        lines.append("|-------|------|----------|-------|-----------|")

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                resolved = data["resolved"]
                total = data["total"]
                rate = f"{resolved * 100 / total:.1f}%" if total > 0 else "N/A"
                lines.append(f"| {agent} | {mode} | {resolved} | {total} | {rate} |")

        lines.append("")

    return "\n".join(lines)


def generate_comparison_table(pass_rates: dict) -> str:
    """生成差异对比表（ΔPass）"""
    lines = []
    lines.append("## 差异分析表 (ΔPass)")
    lines.append("")
    lines.append("以 run_full 为基准，计算各 mode 的 Pass Rate 差异。")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Pass Rate | vs run_full | ΔPass |")
        lines.append("|-------|------|-----------|-------------|-------|")

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]

            # 获取 run_full 的 pass rate 作为基准
            run_full_data = modes.get("run_full", {})
            run_full_rate = run_full_data.get("resolved", 0) / run_full_data.get("total", 1) * 100 if run_full_data.get("total", 0) > 0 else 0

            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                resolved = data["resolved"]
                total = data["total"]
                rate = resolved * 100 / total if total > 0 else 0
                delta = rate - run_full_rate
                delta_str = f"+{delta:.1f}%" if delta >= 0 else f"{delta:.1f}%"

                if mode == "run_full":
                    delta_str = "-"

                lines.append(f"| {agent} | {mode} | {rate:.1f}% | {run_full_rate:.1f}% | {delta_str} |")

        lines.append("")

    return "\n".join(lines)


def generate_monotonicity_analysis(pass_rates: dict) -> str:
    """生成单调性分析"""
    lines = []
    lines.append("## 单调性分析")
    lines.append("")
    lines.append("检验是否存在'执行越多越强'的单调关系。")
    lines.append("")
    lines.append("执行权限排序（从少到多）: run_free < run_less_k1 < run_less_k3 < run_cost ≈ run_full")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]
            lines.append(f"**{agent}:**")

            # 按执行权限排序获取 pass rate
            rates = []
            for mode in MODE_ORDER:
                if mode in modes:
                    data = modes[mode]
                    rate = data["resolved"] / data["total"] * 100 if data["total"] > 0 else 0
                    rates.append((mode, rate))

            # 检查单调性
            is_monotonic = True
            for i in range(1, len(rates)):
                if rates[i][1] < rates[i-1][1]:
                    is_monotonic = False
                    break

            rate_str = " → ".join([f"{m}: {r:.1f}%" for m, r in rates])
            lines.append(f"- {rate_str}")

            if is_monotonic:
                lines.append(f"- 结论: ✓ 存在单调递增关系")
            else:
                lines.append(f"- 结论: ✗ 不存在单调递增关系")

            lines.append("")

    return "\n".join(lines)


def generate_key_findings(pass_rates: dict) -> str:
    """生成关键发现"""
    lines = []
    lines.append("## 关键发现")
    lines.append("")

    findings = []

    for dataset, dataset_name in DATASETS.items():
        if dataset not in pass_rates:
            continue

        for agent in sorted(pass_rates[dataset].keys()):
            modes = pass_rates[dataset][agent]

            run_free = modes.get("run_free", {})
            run_full = modes.get("run_full", {})

            if run_free.get("total", 0) > 0 and run_full.get("total", 0) > 0:
                free_rate = run_free["resolved"] / run_free["total"] * 100
                full_rate = run_full["resolved"] / run_full["total"] * 100
                diff = full_rate - free_rate

                findings.append({
                    "dataset": dataset_name,
                    "agent": agent,
                    "free_rate": free_rate,
                    "full_rate": full_rate,
                    "diff": diff
                })

    # 总结发现
    lines.append("### 1. Run-Free vs Run-Full 对比")
    lines.append("")
    for f in findings:
        diff_str = f"+{f['diff']:.1f}%" if f['diff'] >= 0 else f"{f['diff']:.1f}%"
        lines.append(f"- **{f['agent']}** ({f['dataset']}): Run-Free {f['free_rate']:.1f}% vs Run-Full {f['full_rate']:.1f}% (Δ = {diff_str})")
    lines.append("")

    # 计算平均差异
    avg_diff = sum(f['diff'] for f in findings) / len(findings) if findings else 0
    lines.append(f"### 2. 平均差异")
    lines.append("")
    lines.append(f"- Run-Full 相比 Run-Free 的平均提升: **{avg_diff:.1f}%**")
    lines.append("")

    # 判断执行是否必要
    lines.append("### 3. 结论")
    lines.append("")
    if abs(avg_diff) < 5:
        lines.append("- 执行权限对修复成功率的影响**较小**（< 5%）")
        lines.append("- Run-Free 模式已能达到接近最佳的性能")
        lines.append("- 执行环境可能**不是必要条件**，而是'工程捷径'")
    else:
        lines.append("- 执行权限对修复成功率有**显著影响**（≥ 5%）")
        lines.append("- 执行反馈对 Agent 修复能力有重要贡献")

    return "\n".join(lines)


def main():
    print("正在加载数据...")

    # 加载 pass rate 数据
    pass_rates = load_pass_rates()

    if not pass_rates:
        print("错误: 无法加载 pass rate 数据，请确保 sb-cli-reports 目录存在")
        return

    # 生成数据文件
    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq1.md"

    content = []
    content.append("# RQ1: Effectiveness - 数据表格")
    content.append("")
    content.append("执行权限对修复成功率的影响分析数据。")
    content.append("")
    content.append(generate_pass_rate_table(pass_rates))
    content.append(generate_comparison_table(pass_rates))
    content.append(generate_monotonicity_analysis(pass_rates))
    content.append(generate_key_findings(pass_rates))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
