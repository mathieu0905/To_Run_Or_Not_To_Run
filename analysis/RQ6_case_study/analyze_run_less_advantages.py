#!/usr/bin/env python3
"""
分析 Run-Less 模式的优势场景
找出适度执行比完全不执行更好的案例
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


def find_run_less_advantages(resolved, results):
    """找出 Run-Less 模式的优势场景"""
    lines = []
    lines.append("# Run-Less 模式的优势场景分析")
    lines.append("")
    lines.append("虽然整体数据显示 Run-Less 不如 Run-Free，但在某些特定场景下，适度执行确实有帮助。")
    lines.append("")

    # 1. 找出 Run-Less 独有成功的案例
    lines.append("## 1. Run-Less 独有成功的案例")
    lines.append("")
    lines.append("这些案例中，Run-Free 和 Run-Full 都失败，但 Run-Less 成功了。")
    lines.append("")

    run_less_unique = []

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            if not all(m in modes for m in ["run_free", "run_less_k1", "run_less_k3", "run_full"]):
                continue

            free = modes["run_free"]
            k1 = modes["run_less_k1"]
            k3 = modes["run_less_k3"]
            full = modes["run_full"]

            # Run-Less-K1 独有成功（Free 和 Full 都失败）
            k1_unique = k1 - free - full
            # Run-Less-K3 独有成功
            k3_unique = k3 - free - full
            # 任一 Run-Less 独有成功
            any_less_unique = (k1 | k3) - free - full

            lines.append(f"**{agent}:**")
            lines.append("")
            lines.append(f"- Run-Less-K1 独有成功: {len(k1_unique)} 个")
            lines.append(f"- Run-Less-K3 独有成功: {len(k3_unique)} 个")
            lines.append(f"- 任一 Run-Less 独有成功: {len(any_less_unique)} 个")
            lines.append("")

            if any_less_unique:
                lines.append("**案例列表:**")
                for inst in sorted(any_less_unique):
                    in_k1 = "K1" if inst in k1 else ""
                    in_k3 = "K3" if inst in k3 else ""
                    modes_str = ", ".join(filter(None, [in_k1, in_k3]))
                    lines.append(f"- `{inst}` ({modes_str})")
                    run_less_unique.append((dataset, agent, inst))
                lines.append("")

    # 2. 分析 Run-Less 独有成功案例的特点
    lines.append("## 2. Run-Less 独有成功案例的详细分析")
    lines.append("")

    for dataset, agent, inst in run_less_unique[:10]:
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
        lines.append("**分析**: 适度执行（1-3次）帮助验证修复，但过多执行反而有害。")
        lines.append("")

    # 3. 找出 Run-Less 比 Run-Free 更好的场景
    lines.append("## 3. Run-Less 比 Run-Free 更好的案例")
    lines.append("")
    lines.append("这些案例中，Run-Free 失败但 Run-Less 成功。")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in resolved:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")

        for agent in sorted(resolved[dataset].keys()):
            modes = resolved[dataset][agent]
            if "run_free" not in modes:
                continue

            free = modes["run_free"]
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())

            # Run-Less 成功但 Run-Free 失败
            k1_better = k1 - free
            k3_better = k3 - free

            lines.append(f"**{agent}:**")
            lines.append("")
            lines.append(f"- Run-Less-K1 成功但 Run-Free 失败: {len(k1_better)} 个")
            lines.append(f"- Run-Less-K3 成功但 Run-Free 失败: {len(k3_better)} 个")
            lines.append("")

            if k1_better or k3_better:
                lines.append("**案例:**")
                for inst in sorted(k1_better)[:5]:
                    lines.append(f"- `{inst}` (K1 成功)")
                for inst in sorted(k3_better - k1_better)[:5]:
                    lines.append(f"- `{inst}` (K3 成功)")
                lines.append("")

    # 4. 分析适度执行的价值
    lines.append("## 4. 适度执行的价值分析")
    lines.append("")

    # 统计各模式的独有成功数
    stats = defaultdict(lambda: {"unique": 0, "better_than_free": 0, "better_than_full": 0})

    for dataset in resolved:
        for agent in resolved[dataset]:
            modes = resolved[dataset][agent]
            if len(modes) < 4:
                continue

            free = modes.get("run_free", set())
            k1 = modes.get("run_less_k1", set())
            k3 = modes.get("run_less_k3", set())
            cost = modes.get("run_cost", set())
            full = modes.get("run_full", set())

            # 独有成功
            stats["run_less_k1"]["unique"] += len(k1 - free - k3 - cost - full)
            stats["run_less_k3"]["unique"] += len(k3 - free - k1 - cost - full)
            stats["run_cost"]["unique"] += len(cost - free - k1 - k3 - full)

            # 比 Run-Free 更好
            stats["run_less_k1"]["better_than_free"] += len(k1 - free)
            stats["run_less_k3"]["better_than_free"] += len(k3 - free)
            stats["run_cost"]["better_than_free"] += len(cost - free)

            # 比 Run-Full 更好
            stats["run_less_k1"]["better_than_full"] += len(k1 - full)
            stats["run_less_k3"]["better_than_full"] += len(k3 - full)
            stats["run_cost"]["better_than_full"] += len(cost - full)

    lines.append("| 模式 | 独有成功 | 比 Run-Free 好 | 比 Run-Full 好 |")
    lines.append("|------|----------|----------------|----------------|")
    for mode in ["run_less_k1", "run_less_k3", "run_cost"]:
        s = stats[mode]
        lines.append(f"| {mode} | {s['unique']} | {s['better_than_free']} | {s['better_than_full']} |")
    lines.append("")

    # 5. 总结
    lines.append("## 5. 核心发现：适度执行的价值")
    lines.append("")
    lines.append("### 适度执行有帮助的场景")
    lines.append("")
    lines.append("1. **需要验证但不需要迭代的问题**")
    lines.append("   - 1-3 次执行足以验证修复是否正确")
    lines.append("   - 更多执行反而引入噪声和干扰")
    lines.append("")
    lines.append("2. **Run-Free 推理不足的问题**")
    lines.append("   - 纯推理无法确定正确答案")
    lines.append("   - 但少量执行反馈就能指明方向")
    lines.append("")
    lines.append("3. **Run-Full 过度执行有害的问题**")
    lines.append("   - 过多执行导致试错循环")
    lines.append("   - 适度执行避免了这个问题")
    lines.append("")
    lines.append("### 实践建议")
    lines.append("")
    lines.append("1. **Run-Free 仍是默认首选** - 成本最低，效果接近最佳")
    lines.append("2. **Run-Less-K1 可作为备选** - 当 Run-Free 失败时，尝试 1 次执行")
    lines.append("3. **避免 Run-Full** - 除非确实需要大量迭代调试")
    lines.append("4. **适度执行的价值在于验证** - 不是探索，而是确认")
    lines.append("")

    return "\n".join(lines)


def main():
    print("正在加载数据...")

    results = load_all_results()
    resolved = load_resolved_ids()

    analysis = find_run_less_advantages(resolved, results)

    output_path = Path(__file__).parent / "run_less_advantages.md"
    output_path.write_text(analysis, encoding="utf-8")
    print(f"分析已保存到: {output_path}")


if __name__ == "__main__":
    main()
