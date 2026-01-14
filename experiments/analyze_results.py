#!/usr/bin/env python3
"""分析实验结果的脚本"""

import json
import os
from pathlib import Path
from collections import defaultdict

def count_tokens_and_execs(trace_path):
    """从 trace.jsonl 统计 token、执行次数、交互轮数和时间"""
    tokens = {"input": 0, "output": 0}
    exec_count = 0
    high_cost_exec = 0  # 高成本执行（测试框架）
    low_cost_exec = 0   # 低成本执行（脚本）
    turns = 0
    duration_ms = 0
    max_item_id = -1

    # 高成本执行：测试框架（运行整个测试套件）
    high_cost_patterns = [
        "pytest", "python -m pytest", "python -m unittest",
        "manage.py test", "python manage.py test",
        "tox", "nose", "nosetests",
        "python -m django test",
        "python tests/runtests.py"
    ]
    # 低成本执行：直接运行 Python 脚本
    import re
    python_script_pattern = re.compile(r'\bpython\s+[a-zA-Z_][\w/\-]*\.py\b')

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)
                # Codex 格式: turn.completed (统计 tokens)
                if item.get("type") == "turn.completed":
                    usage = item.get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)
                # Codex 格式: 统计 item id 的最大值作为轮数
                if item.get("type") in ["item.started", "item.completed"]:
                    inner = item.get("item", {})
                    item_id = inner.get("id", "")
                    if item_id.startswith("item_"):
                        try:
                            id_num = int(item_id.split("_")[1])
                            max_item_id = max(max_item_id, id_num)
                        except:
                            pass
                    # 统计执行次数
                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        # 先检查是否是高成本执行
                        if any(p in cmd for p in high_cost_patterns):
                            high_cost_exec += 1
                            exec_count += 1
                        # 否则检查是否是低成本执行（python script.py）
                        elif python_script_pattern.search(cmd):
                            low_cost_exec += 1
                            exec_count += 1
                # Claude Code 格式: assistant 消息里的 usage
                if item.get("type") == "assistant":
                    usage = item.get("message", {}).get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)
                    # 每个 assistant 消息算一轮
                    if usage.get("input_tokens", 0) > 0:
                        turns += 1
                    # 统计执行次数 (Claude Code)
                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            # 先检查是否是高成本执行
                            if any(p in cmd for p in high_cost_patterns):
                                high_cost_exec += 1
                                exec_count += 1
                            # 否则检查是否是低成本执行（python script.py）
                            elif python_script_pattern.search(cmd):
                                low_cost_exec += 1
                                exec_count += 1
                # 提取时间信息 (最后一行的 result)
                if item.get("type") == "result":
                    duration_ms = item.get("duration_ms", 0)
            except:
                continue

    # 如果是 Codex (有 max_item_id)，使用 max_item_id + 1 作为轮数
    if max_item_id >= 0:
        turns = max_item_id + 1

    return tokens, exec_count, high_cost_exec, low_cost_exec, turns, duration_ms

def check_patch(patch_path):
    """检查 patch 是否非空"""
    if not os.path.exists(patch_path):
        return False
    with open(patch_path) as f:
        content = f.read().strip()
    return len(content) > 0

def analyze(output_dir):
    """分析输出目录"""
    output_dir = Path(output_dir)
    results = defaultdict(lambda: defaultdict(dict))

    for agent_dir in output_dir.iterdir():
        if not agent_dir.is_dir():
            continue
        agent = agent_dir.name

        for mode_dir in agent_dir.iterdir():
            if not mode_dir.is_dir():
                continue
            mode = mode_dir.name

            for instance_dir in mode_dir.iterdir():
                if not instance_dir.is_dir():
                    continue
                instance = instance_dir.name

                trace_path = instance_dir / "trace.jsonl"
                patch_path = instance_dir / "patch.diff"

                if trace_path.exists():
                    tokens, exec_count, high_cost_exec, low_cost_exec, turns, duration_ms = count_tokens_and_execs(trace_path)
                    has_patch = check_patch(patch_path)

                    results[agent][mode][instance] = {
                        "tokens": tokens,
                        "exec_count": exec_count,
                        "high_cost_exec": high_cost_exec,
                        "low_cost_exec": low_cost_exec,
                        "turns": turns,
                        "duration_ms": duration_ms,
                        "has_patch": has_patch
                    }

    return results

def print_summary(results):
    """打印汇总"""
    print("=" * 110)
    print("实验结果分析")
    print("=" * 110)

    for agent, modes in sorted(results.items()):
        print(f"\n### Agent: {agent}")
        print("-" * 130)
        print(f"{'Mode':<15} {'N':<5} {'Avg Input':<12} {'Avg Output':<12} {'Avg Total':<12} {'Avg Turns':<10} {'High-Cost':<11} {'Low-Cost':<10} {'Avg Time':<12} {'Patch'}")
        print("-" * 130)

        for mode, instances in sorted(modes.items()):
            n = len(instances)
            total_input = sum(v["tokens"]["input"] for v in instances.values())
            total_output = sum(v["tokens"]["output"] for v in instances.values())
            total_execs = sum(v["exec_count"] for v in instances.values())
            total_high_cost = sum(v["high_cost_exec"] for v in instances.values())
            total_low_cost = sum(v["low_cost_exec"] for v in instances.values())
            total_turns = sum(v["turns"] for v in instances.values())
            total_duration = sum(v["duration_ms"] for v in instances.values())
            patches = sum(1 for v in instances.values() if v["has_patch"])

            avg_input = total_input // n if n > 0 else 0
            avg_output = total_output // n if n > 0 else 0
            avg_total = (total_input + total_output) // n if n > 0 else 0
            avg_turns = total_turns / n if n > 0 else 0
            avg_high_cost = total_high_cost / n if n > 0 else 0
            avg_low_cost = total_low_cost / n if n > 0 else 0
            avg_duration_sec = (total_duration / n / 1000) if n > 0 else 0

            print(f"{mode:<15} {n:<5} {avg_input:<12} {avg_output:<12} {avg_total:<12} {avg_turns:<10.1f} {avg_high_cost:<11.1f} {avg_low_cost:<10.1f} {avg_duration_sec:<12.1f} {patches}/{n}")

    # 详细信息
    # print("\n" + "=" * 110)
    # print("详细结果")
    # print("=" * 110)

    # for agent, modes in sorted(results.items()):
    #     for mode, instances in sorted(modes.items()):
    #         print(f"\n[{agent}] {mode}:")
    #         for inst, data in sorted(instances.items()):
    #             t = data["tokens"]
    #             patch_mark = "✓" if data["has_patch"] else "✗"
    #             duration_sec = data["duration_ms"] / 1000
    #             print(f"  {inst}: input={t['input']}, output={t['output']}, total={t['input']+t['output']}, turns={data['turns']}, execs={data['exec_count']}, time={duration_sec:.1f}s, patch={patch_mark}")

if __name__ == "__main__":
    import sys

    # 默认分析两个数据集
    if len(sys.argv) > 1:
        output_dirs = [sys.argv[1]]
    else:
        base_dir = "/home/zhihao/hdd/run_free_run_less_run_full/output"
        output_dirs = [
            f"{base_dir}/swebenchlite",
            f"{base_dir}/swebenchverified"
        ]

    # 分析每个数据集
    for output_dir in output_dirs:
        if not os.path.exists(output_dir):
            print(f"\n跳过不存在的目录: {output_dir}")
            continue

        print(f"\n{'='*120}")
        print(f"数据集: {os.path.basename(output_dir)}")
        print(f"{'='*120}")

        results = analyze(output_dir)
        print_summary(results)
