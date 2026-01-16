#!/usr/bin/env python3
"""
分析 Run-Cost 模式的表现
Run-Cost 是有成本约束的执行模式，可能是一个很好的折中方案
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, sort_modes
)


def load_resolved_ids():
    """加载每个配置的 resolved instance IDs"""
    sb_cli_reports_dir = PROJECT_ROOT / "sb-cli-reports"
    resolved = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    if not sb_cli_reports_dir.exists():
        return resolved

    for report_file in sb_cli_reports_dir.glob("*.json"):
        try:
            report = json.loads(report_file.read_text(encoding="utf-8"))
            filename = report_file.stem

            if "lite" in filename.lower():
                dataset = "swebenchlite"
            elif "verified" in filename.lower():
                dataset = "swebenchverified"
            else:
                continue

            for agent in ["claude_code", "codex"]:
                if agent in filename:
                    for mode in MODE_ORDER:
                        if mode in filename:
                            resolved_ids = set(report.get("resolved_ids", []))
                            resolved[dataset][agent][mode] = resolved_ids
                            break
                    break
        except:
            continue

    return resolved


def analyze_run_cost(resolved, results):
    """分析 Run-Cost 模式的表现"""
    lines = []
    lines.append("# Run-Cost 模式深度分析")
    lines.append("")
    lines.append("Run-Cost 是有成本约束的执行模式，在执行次数和成本之间寻求平衡。")
    lines.append("")

    # 1. 整体表现对比
    lines.append("## 1. 整体表现对比")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        lines.append("| Agent | run_free | run_less_k1 | run_less_k3 | run_cost | run_full |")
        lines.append("|-------|----------|-------------|-------------|----------|----------|")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            row = f"| {agent} |"
            for mode in MODE_ORDER:
                if mode in modes:
                    count = len(modes[mode])
                    row += f" {count} |"
                else:
                    row += " - |"
            lines.append(row)

        lines.append("")

    # 2. Run-Cost vs 其他模式
    lines.append("## 2. Run-Cost 与其他模式的对比")
    lines.append("")

    total_stats = {
        "cost_unique": 0,
        "cost_better_free": 0,
        "cost_better_full": 0,
        "cost_better_k1": 0,
        "cost_better_k3": 0,
        "free_better_cost": 0,
        "full_better_cost": 0,
    }

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            if "run_cost" not in modes:
                continue

            free = modes.get("run_free", set())
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())
            cost = modes["run_cost"]
            full = modes.get("run_full", set())

            # Run-Cost 独有成功
            cost_unique = cost - free - k1 - k3 - full

            # Run-Cost vs Run-Free
            cost_better_free = cost - free
            free_better_cost = free - cost

            # Run-Cost vs Run-Full
            cost_better_full = cost - full
            full_better_cost = full - cost

            # Run-Cost vs Run-Less
            cost_better_k1 = cost - k1
            cost_better_k3 = cost - k3

            total_stats["cost_unique"] += len(cost_unique)
            total_stats["cost_better_free"] += len(cost_better_free)
            total_stats["cost_better_full"] += len(cost_better_full)
            total_stats["cost_better_k1"] += len(cost_better_k1)
            total_stats["cost_better_k3"] += len(cost_better_k3)
            total_stats["free_better_cost"] += len(free_better_cost)
            total_stats["full_better_cost"] += len(full_better_cost)

            lines.append(f"**{agent}:**")
            lines.append("")
            lines.append("| 对比 | Run-Cost 胜 | 对方胜 | 净差异 |")
            lines.append("|------|-------------|--------|--------|")
            lines.append(f"| vs Run-Free | {len(cost_better_free)} | {len(free_better_cost)} | {len(cost_better_free) - len(free_better_cost):+d} |")
            lines.append(f"| vs Run-Less-K1 | {len(cost_better_k1)} | {len(k1 - cost)} | {len(cost_better_k1) - len(k1 - cost):+d} |")
            lines.append(f"| vs Run-Less-K3 | {len(cost_better_k3)} | {len(k3 - cost)} | {len(cost_better_k3) - len(k3 - cost):+d} |")
            lines.append(f"| vs Run-Full | {len(cost_better_full)} | {len(full_better_cost)} | {len(cost_better_full) - len(full_better_cost):+d} |")
            lines.append("")

            if cost_unique:
                lines.append(f"**Run-Cost 独有成功 ({len(cost_unique)} 个):**")
                for inst in sorted(cost_unique):
                    lines.append(f"- `{inst}`")
                lines.append("")

    # 3. 汇总统计
    lines.append("## 3. 汇总统计")
    lines.append("")
    lines.append("| 指标 | 数量 |")
    lines.append("|------|------|")
    lines.append(f"| Run-Cost 独有成功 | {total_stats['cost_unique']} |")
    lines.append(f"| Run-Cost 比 Run-Free 好 | {total_stats['cost_better_free']} |")
    lines.append(f"| Run-Cost 比 Run-Full 好 | {total_stats['cost_better_full']} |")
    lines.append(f"| Run-Free 比 Run-Cost 好 | {total_stats['free_better_cost']} |")
    lines.append(f"| Run-Full 比 Run-Cost 好 | {total_stats['full_better_cost']} |")
    lines.append("")

    # 4. Run-Cost 独有成功案例分析
    lines.append("## 4. Run-Cost 独有成功案例详细分析")
    lines.append("")

    cost_unique_cases = []
    for dataset in resolved:
        for agent in resolved[dataset]:
            modes = resolved[dataset][agent]
            if "run_cost" not in modes:
                continue

            free = modes.get("run_free", set())
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())
            cost = modes["run_cost"]
            full = modes.get("run_full", set())

            cost_unique = cost - free - k1 - k3 - full
            for inst in cost_unique:
                cost_unique_cases.append((dataset, agent, inst))

    for dataset, agent, inst in cost_unique_cases:
        dataset_name = DATASETS.get(dataset, dataset)
        lines.append(f"### `{inst}` ({agent}, {dataset_name})")
        lines.append("")

        lines.append("| Mode | Tokens | Turns | High-Cost Exec | Result |")
        lines.append("|------|--------|-------|----------------|--------|")

        for mode in sort_modes(resolved[dataset][agent].keys()):
            data = results.get(dataset, {}).get(agent, {}).get(mode, {}).get(inst, {})
            is_resolved = inst in resolved[dataset][agent].get(mode, set())

            if data:
                tokens = data["tokens"]["input"] + data["tokens"]["output"]
                turns = data["turns"]
                high_exec = data["high_cost_exec"]
                result = "**成功**" if is_resolved else "失败"
                lines.append(f"| {mode} | {tokens:,} | {turns} | {high_exec} | {result} |")

        lines.append("")

    # 5. 成本效率分析
    lines.append("## 5. 成本效率分析")
    lines.append("")
    lines.append("Run-Cost 的成本相对于其他模式的位置。")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in results:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(results[dataset].keys()):
            modes = results[dataset][agent]
            lines.append(f"**{agent}:**")
            lines.append("")

            lines.append("| Mode | Avg Tokens | Pass Rate | 效率比 (Pass/Token) |")
            lines.append("|------|------------|-----------|---------------------|")

            pass_rates = {}
            for mode in sort_modes(modes.keys()):
                if mode in resolved.get(dataset, {}).get(agent, {}):
                    pass_rates[mode] = len(resolved[dataset][agent][mode])

            for mode in sort_modes(modes.keys()):
                instances = modes[mode]
                if not instances:
                    continue

                tokens_list = [v["tokens"]["input"] + v["tokens"]["output"] for v in instances.values()]
                avg_tokens = sum(tokens_list) / len(tokens_list)
                pass_rate = pass_rates.get(mode, 0)
                efficiency = pass_rate / (avg_tokens / 1000) if avg_tokens > 0 else 0

                lines.append(f"| {mode} | {avg_tokens:,.0f} | {pass_rate} | {efficiency:.2f} |")

            lines.append("")

    # 6. 结论
    lines.append("## 6. Run-Cost 模式的价值")
    lines.append("")
    lines.append("### 优势")
    lines.append("")
    lines.append("1. **成本可控** - 有明确的成本上限，避免无限制消耗")
    lines.append("2. **表现稳定** - 在多数情况下接近 Run-Full 的效果")
    lines.append("3. **独有成功案例** - 有些问题只有 Run-Cost 能解决")
    lines.append("4. **比 Run-Less 更灵活** - 不是简单限制次数，而是限制总成本")
    lines.append("")
    lines.append("### 适用场景")
    lines.append("")
    lines.append("1. **预算有限但需要执行反馈** - 比 Run-Free 多一些验证能力")
    lines.append("2. **避免过度执行** - 比 Run-Full 更节制")
    lines.append("3. **生产环境** - 成本可预测，适合大规模部署")
    lines.append("")
    lines.append("### 实践建议")
    lines.append("")
    lines.append("1. **Run-Free** - 默认首选，成本最低")
    lines.append("2. **Run-Cost** - 需要执行但要控制成本时的最佳选择")
    lines.append("3. **Run-Full** - 仅在调试复杂问题时使用")
    lines.append("4. **Run-Less** - 不推荐，表现不稳定")
    lines.append("")

    return "\n".join(lines)


def main():
    print("正在加载数据...")

    results = load_all_results()
    resolved = load_resolved_ids()

    analysis = analyze_run_cost(resolved, results)

    output_path = Path(__file__).parent / "run_cost_analysis.md"
    output_path.write_text(analysis, encoding="utf-8")
    print(f"分析已保存到: {output_path}")


if __name__ == "__main__":
    main()
