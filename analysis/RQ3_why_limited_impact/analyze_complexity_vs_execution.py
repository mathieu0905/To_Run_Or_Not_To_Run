#!/usr/bin/env python3
"""
Q5 分析：执行反馈的价值是否与 bug 复杂度相关？

按 ground truth patch 的复杂度（文件数、hunk 数）分层，
比较 Prohibited (run_free) vs Unrestricted (run_full) 的 resolve rate。
"""

import json
import re
from pathlib import Path
from collections import defaultdict
from datasets import load_dataset

PROJECT_ROOT = Path(__file__).parent.parent.parent
SB_CLI_REPORTS = PROJECT_ROOT / "sb-cli-reports"


def count_patch_complexity(patch: str):
    """从 ground truth patch 中统计文件数和 hunk 数"""
    files = set()
    hunks = 0
    for line in patch.split('\n'):
        if line.startswith('diff --git'):
            # extract file path
            parts = line.split(' b/')
            if len(parts) >= 2:
                files.add(parts[-1])
        elif line.startswith('@@'):
            hunks += 1
    return len(files), hunks


def load_resolved_ids(dataset_key: str, agent: str, mode: str):
    """从 sb-cli-reports 加载 resolved instance ids"""
    for f in SB_CLI_REPORTS.glob("*.json"):
        fname = f.stem.lower()
        if dataset_key in fname and agent in fname and mode in fname:
            data = json.load(open(f))
            return set(data.get("resolved_ids", []))
    return set()


def main():
    for dataset_name, dataset_key, dataset_hf in [
        ("SWE-bench Lite", "lite", "princeton-nlp/SWE-bench_Lite"),
        ("SWE-bench Verified", "verified", "princeton-nlp/SWE-bench_Verified"),
    ]:
        print(f"\n{'='*70}")
        print(f"  {dataset_name}")
        print(f"{'='*70}")

        ds = load_dataset(dataset_hf, split='test')

        # 只取我们实验中涉及的前 100 个实例
        output_dir = PROJECT_ROOT / "output" / dataset_key.replace("lite", "swebenchlite").replace("verified", "swebenchverified")
        if dataset_key == "lite":
            output_dir = PROJECT_ROOT / "output" / "swebenchlite"
        else:
            output_dir = PROJECT_ROOT / "output" / "swebenchverified"

        # 获取实验涉及的 instance ids
        experiment_ids = set()
        for agent in ["claude_code", "codex"]:
            agent_dir = output_dir / agent / "run_full"
            if agent_dir.exists():
                for d in agent_dir.iterdir():
                    if d.is_dir():
                        experiment_ids.add(d.name)

        # 计算每个实例的复杂度
        instance_complexity = {}
        for item in ds:
            iid = item['instance_id']
            if iid in experiment_ids:
                n_files, n_hunks = count_patch_complexity(item['patch'])
                instance_complexity[iid] = {
                    'n_files': n_files,
                    'n_hunks': n_hunks,
                }

        # 分层：单文件 vs 多文件
        single_file_ids = {iid for iid, c in instance_complexity.items() if c['n_files'] == 1}
        multi_file_ids = {iid for iid, c in instance_complexity.items() if c['n_files'] > 1}

        # 分层：单 hunk vs 多 hunk
        single_hunk_ids = {iid for iid, c in instance_complexity.items() if c['n_hunks'] == 1}
        multi_hunk_ids = {iid for iid, c in instance_complexity.items() if c['n_hunks'] > 1}

        print(f"\n实例总数: {len(instance_complexity)}")
        print(f"单文件: {len(single_file_ids)}, 多文件: {len(multi_file_ids)}")
        print(f"单hunk: {len(single_hunk_ids)}, 多hunk: {len(multi_hunk_ids)}")

        for agent in ["claude_code", "codex"]:
            print(f"\n--- {agent} ---")

            resolved_free = load_resolved_ids(dataset_key, agent, "run_free")
            resolved_full = load_resolved_ids(dataset_key, agent, "run_full")

            if not resolved_free and not resolved_full:
                print("  (无数据)")
                continue

            for label, subset_ids in [
                ("单文件 (single-file)", single_file_ids),
                ("多文件 (multi-file)", multi_file_ids),
                ("单hunk (single-hunk)", single_hunk_ids),
                ("多hunk (multi-hunk)", multi_hunk_ids),
            ]:
                n = len(subset_ids)
                if n == 0:
                    continue
                free_resolved = len(resolved_free & subset_ids)
                full_resolved = len(resolved_full & subset_ids)
                free_rate = free_resolved / n * 100
                full_rate = full_resolved / n * 100
                diff = full_rate - free_rate

                print(f"  {label:30s}  n={n:3d}  "
                      f"Prohibited={free_rate:5.1f}% ({free_resolved}/{n})  "
                      f"Unrestricted={full_rate:5.1f}% ({full_resolved}/{n})  "
                      f"Δ={diff:+5.1f}pp")


if __name__ == "__main__":
    main()
