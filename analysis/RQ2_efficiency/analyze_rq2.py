#!/usr/bin/env python3
"""
RQ2: Efficiency - 成本与效率的 Pareto 前沿

研究问题: 不同执行权限对成本（tokens）、轮数、时间的影响有多大？
是否存在 Pareto 前沿？Run-Less 能否以显著更低成本获得接近 Run-Full 的成功率？
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, load_pass_rates, get_aggregated_stats, sort_modes
)


def generate_cost_table(stats: dict) -> str:
    """生成成本对比表格"""
    lines = []
    lines.append("## 成本对比表")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Avg Tokens | Avg Turns | Avg Time (s) | High-Cost Exec | Low-Cost Exec |")
        lines.append("|-------|------|------------|-----------|--------------|----------------|---------------|")

        for agent in sorted(stats[dataset].keys()):
            modes = stats[dataset][agent]
            for mode in sort_modes(modes.keys()):
                data = modes[mode]
                lines.append(f"| {agent} | {mode} | {data['avg_total_tokens']:,} | {data['avg_turns']:.1f} | {data['avg_time_sec']:.1f} | {data['avg_high_cost_exec']:.1f} | {data['avg_low_cost_exec']:.1f} |")

        lines.append("")

    return "\n".join(lines)


def generate_relative_change_table(stats: dict) -> str:
    """生成相对变化百分比表（以 run_full 为基准）"""
    lines = []
    lines.append("## 相对变化百分比表 (vs run_full)")
    lines.append("")
    lines.append("以 run_full 为基准，计算各 mode 的成本变化。负值表示成本降低。")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | ΔTokens | ΔTurns | ΔTime |")
        lines.append("|-------|------|---------|--------|-------|")

        for agent in sorted(stats[dataset].keys()):
            modes = stats[dataset][agent]

            # 获取 run_full 作为基准
            run_full = modes.get("run_full", {})
            if not run_full:
                continue

            base_tokens = run_full.get("avg_total_tokens", 1)
            base_turns = run_full.get("avg_turns", 1)
            base_time = run_full.get("avg_time_sec", 1)

            for mode in sort_modes(modes.keys()):
                data = modes[mode]

                delta_tokens = (data["avg_total_tokens"] - base_tokens) / base_tokens * 100
                delta_turns = (data["avg_turns"] - base_turns) / base_turns * 100
                delta_time = (data["avg_time_sec"] - base_time) / base_time * 100

                if mode == "run_full":
                    lines.append(f"| {agent} | {mode} | - | - | - |")
                else:
                    dt = f"+{delta_tokens:.1f}%" if delta_tokens >= 0 else f"{delta_tokens:.1f}%"
                    dtu = f"+{delta_turns:.1f}%" if delta_turns >= 0 else f"{delta_turns:.1f}%"
                    dti = f"+{delta_time:.1f}%" if delta_time >= 0 else f"{delta_time:.1f}%"
                    lines.append(f"| {agent} | {mode} | {dt} | {dtu} | {dti} |")

        lines.append("")

    return "\n".join(lines)


def generate_pareto_data(stats: dict, pass_rates: dict) -> str:
    """生成 Pareto 前沿数据（Pass Rate vs Avg Total Tokens）"""
    lines = []
    lines.append("## Pareto 前沿数据")
    lines.append("")
    lines.append("Pass Rate vs Avg Total Tokens 数据点，用于绘制 Pareto 前沿图。")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Pass Rate (%) | Avg Tokens | Pareto Optimal? |")
        lines.append("|-------|------|---------------|------------|-----------------|")

        # 收集所有数据点
        data_points = []
        for agent in sorted(stats[dataset].keys()):
            if agent not in pass_rates[dataset]:
                continue
            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            for mode in sort_modes(modes.keys()):
                if mode not in pr_modes:
                    continue
                s = modes[mode]
                pr = pr_modes[mode]
                rate = pr["resolved"] / pr["total"] * 100 if pr["total"] > 0 else 0
                tokens = s["avg_total_tokens"]
                data_points.append({
                    "agent": agent,
                    "mode": mode,
                    "rate": rate,
                    "tokens": tokens
                })

        # 判断 Pareto 最优
        for dp in data_points:
            is_pareto = True
            for other in data_points:
                # 如果存在另一个点，rate 更高且 tokens 更低，则当前点不是 Pareto 最优
                if other["rate"] > dp["rate"] and other["tokens"] < dp["tokens"]:
                    is_pareto = False
                    break
                # 如果存在另一个点，rate 相同但 tokens 更低
                if other["rate"] == dp["rate"] and other["tokens"] < dp["tokens"]:
                    is_pareto = False
                    break
            dp["pareto"] = is_pareto

        for dp in data_points:
            pareto_str = "✓" if dp["pareto"] else ""
            lines.append(f"| {dp['agent']} | {dp['mode']} | {dp['rate']:.1f} | {dp['tokens']:,} | {pareto_str} |")

        lines.append("")

    return "\n".join(lines)


def generate_efficiency_analysis(stats: dict, pass_rates: dict) -> str:
    """生成效率分析"""
    lines = []
    lines.append("## 效率分析")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(stats[dataset].keys()):
            if agent not in pass_rates[dataset]:
                continue
            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            lines.append(f"**{agent}:**")
            lines.append("")

            # 计算 run_free 相对 run_full 的效率
            run_free_s = modes.get("run_free", {})
            run_full_s = modes.get("run_full", {})
            run_free_pr = pr_modes.get("run_free", {})
            run_full_pr = pr_modes.get("run_full", {})

            if run_free_s and run_full_s and run_free_pr and run_full_pr:
                free_rate = run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr["total"] > 0 else 0
                full_rate = run_full_pr["resolved"] / run_full_pr["total"] * 100 if run_full_pr["total"] > 0 else 0

                token_saving = (run_full_s["avg_total_tokens"] - run_free_s["avg_total_tokens"]) / run_full_s["avg_total_tokens"] * 100
                time_saving = (run_full_s["avg_time_sec"] - run_free_s["avg_time_sec"]) / run_full_s["avg_time_sec"] * 100
                rate_diff = full_rate - free_rate

                lines.append(f"- Run-Free vs Run-Full:")
                lines.append(f"  - Pass Rate 差异: {rate_diff:+.1f}%")
                lines.append(f"  - Token 节省: {token_saving:.1f}%")
                lines.append(f"  - 时间节省: {time_saving:.1f}%")

                # 计算效率比
                if rate_diff != 0:
                    efficiency = token_saving / abs(rate_diff)
                    lines.append(f"  - 效率比 (Token节省/Pass差异): {efficiency:.1f}")
                lines.append("")

    return "\n".join(lines)


def generate_key_findings(stats: dict, pass_rates: dict) -> str:
    """生成关键发现"""
    lines = []
    lines.append("## 关键发现")
    lines.append("")

    # 收集所有数据
    all_data = []
    for dataset, dataset_name in DATASETS.items():
        if dataset not in stats or dataset not in pass_rates:
            continue
        for agent in stats[dataset].keys():
            if agent not in pass_rates[dataset]:
                continue
            modes = stats[dataset][agent]
            pr_modes = pass_rates[dataset][agent]

            run_free_s = modes.get("run_free", {})
            run_full_s = modes.get("run_full", {})
            run_free_pr = pr_modes.get("run_free", {})
            run_full_pr = pr_modes.get("run_full", {})

            if run_free_s and run_full_s:
                all_data.append({
                    "dataset": dataset_name,
                    "agent": agent,
                    "free_tokens": run_free_s["avg_total_tokens"],
                    "full_tokens": run_full_s["avg_total_tokens"],
                    "free_time": run_free_s["avg_time_sec"],
                    "full_time": run_full_s["avg_time_sec"],
                    "free_rate": run_free_pr["resolved"] / run_free_pr["total"] * 100 if run_free_pr.get("total", 0) > 0 else 0,
                    "full_rate": run_full_pr["resolved"] / run_full_pr["total"] * 100 if run_full_pr.get("total", 0) > 0 else 0,
                })

    lines.append("### 1. Token 消耗对比")
    lines.append("")
    for d in all_data:
        saving = (d["full_tokens"] - d["free_tokens"]) / d["full_tokens"] * 100
        lines.append(f"- **{d['agent']}** ({d['dataset']}): Run-Free {d['free_tokens']:,} vs Run-Full {d['full_tokens']:,} (节省 {saving:.1f}%)")
    lines.append("")

    lines.append("### 2. 时间消耗对比")
    lines.append("")
    for d in all_data:
        saving = (d["full_time"] - d["free_time"]) / d["full_time"] * 100
        lines.append(f"- **{d['agent']}** ({d['dataset']}): Run-Free {d['free_time']:.0f}s vs Run-Full {d['full_time']:.0f}s (节省 {saving:.1f}%)")
    lines.append("")

    lines.append("### 3. 成本效益结论")
    lines.append("")

    # 计算平均节省
    avg_token_saving = sum((d["full_tokens"] - d["free_tokens"]) / d["full_tokens"] * 100 for d in all_data) / len(all_data) if all_data else 0
    avg_time_saving = sum((d["full_time"] - d["free_time"]) / d["full_time"] * 100 for d in all_data) / len(all_data) if all_data else 0
    avg_rate_diff = sum(d["full_rate"] - d["free_rate"] for d in all_data) / len(all_data) if all_data else 0

    lines.append(f"- 平均 Token 节省: **{avg_token_saving:.1f}%**")
    lines.append(f"- 平均时间节省: **{avg_time_saving:.1f}%**")
    lines.append(f"- 平均 Pass Rate 差异: **{avg_rate_diff:+.1f}%**")
    lines.append("")
    lines.append(f"**结论**: Run-Free 模式以 {avg_token_saving:.0f}% 的成本节省换取 {abs(avg_rate_diff):.1f}% 的性能损失，是最具成本效益的选择。")

    return "\n".join(lines)


def main():
    print("正在加载数据...")

    results = load_all_results()
    stats = get_aggregated_stats(results)
    pass_rates = load_pass_rates()

    if not stats:
        print("错误: 无法加载实验结果数据")
        return

    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq2.md"

    content = []
    content.append("# RQ2: Efficiency - 数据表格")
    content.append("")
    content.append("成本与效率的 Pareto 前沿分析数据。")
    content.append("")
    content.append(generate_cost_table(stats))
    content.append(generate_relative_change_table(stats))
    content.append(generate_pareto_data(stats, pass_rates))
    content.append(generate_efficiency_analysis(stats, pass_rates))
    content.append(generate_key_findings(stats, pass_rates))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
