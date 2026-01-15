#!/usr/bin/env python3
"""
从 output 目录生成 SWE-bench predictions 文件
"""

import os
import json
import argparse
from pathlib import Path


def generate_predictions(output_dir: str, dataset: str, agent: str, mode: str, output_file: str = None):
    """
    生成 predictions JSON 文件

    Args:
        output_dir: output 目录路径
        dataset: 数据集名称 (swebenchlite, swebenchverified)
        agent: agent 名称 (claude_code, codex)
        mode: 模式名称 (run_free, run_less_k1, run_less_k3, run_cost, run_full)
        output_file: 输出文件路径，默认为 predictions/{dataset}_{agent}_{mode}.json
    """
    base_path = Path(output_dir) / dataset / agent / mode

    if not base_path.exists():
        print(f"错误: 路径不存在: {base_path}")
        return None

    predictions = []
    instance_dirs = [d for d in base_path.iterdir() if d.is_dir()]

    for instance_dir in sorted(instance_dirs):
        instance_id = instance_dir.name
        patch_file = instance_dir / "patch.diff"

        if patch_file.exists():
            with open(patch_file, 'r') as f:
                patch_content = f.read()

            predictions.append({
                "instance_id": instance_id,
                "model_patch": patch_content,
                "model_name_or_path": f"{agent}_{mode}"
            })
        else:
            print(f"警告: 缺少 patch.diff: {instance_dir}")

    # 确定输出文件路径
    if output_file is None:
        predictions_dir = Path(output_dir).parent / "predictions"
        predictions_dir.mkdir(exist_ok=True)
        output_file = predictions_dir / f"{dataset}_{agent}_{mode}.json"

    # 保存 predictions
    with open(output_file, 'w') as f:
        json.dump(predictions, f, indent=2)

    print(f"生成 predictions 文件: {output_file}")
    print(f"  实例数量: {len(predictions)}")

    return str(output_file)


def list_available_combinations(output_dir: str):
    """列出所有可用的 dataset/agent/mode 组合"""
    output_path = Path(output_dir)
    combinations = []

    for dataset_dir in output_path.iterdir():
        if not dataset_dir.is_dir():
            continue
        dataset = dataset_dir.name

        for agent_dir in dataset_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            agent = agent_dir.name

            for mode_dir in agent_dir.iterdir():
                if not mode_dir.is_dir():
                    continue
                mode = mode_dir.name

                # 统计实例数量
                instance_count = len([d for d in mode_dir.iterdir() if d.is_dir()])
                patch_count = len(list(mode_dir.glob("*/patch.diff")))

                combinations.append({
                    "dataset": dataset,
                    "agent": agent,
                    "mode": mode,
                    "instances": instance_count,
                    "patches": patch_count
                })

    return combinations


def main():
    parser = argparse.ArgumentParser(description="生成 SWE-bench predictions 文件")
    parser.add_argument("--output-dir", default="/home/zhihao/hdd/run_free_run_less_run_full/output",
                        help="output 目录路径")
    parser.add_argument("--dataset", help="数据集名称")
    parser.add_argument("--agent", help="agent 名称")
    parser.add_argument("--mode", help="模式名称")
    parser.add_argument("--output-file", help="输出文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有可用组合")
    parser.add_argument("--all", action="store_true", help="生成所有组合的 predictions")

    args = parser.parse_args()

    if args.list:
        combinations = list_available_combinations(args.output_dir)
        print("\n可用的 dataset/agent/mode 组合:")
        print("-" * 70)
        print(f"{'Dataset':<20} {'Agent':<15} {'Mode':<15} {'Instances':<10} {'Patches':<10}")
        print("-" * 70)
        for c in combinations:
            print(f"{c['dataset']:<20} {c['agent']:<15} {c['mode']:<15} {c['instances']:<10} {c['patches']:<10}")
        print("-" * 70)
        print(f"总计: {len(combinations)} 个组合")
        return

    if args.all:
        combinations = list_available_combinations(args.output_dir)
        predictions_dir = Path(args.output_dir).parent / "predictions"
        predictions_dir.mkdir(exist_ok=True)

        print(f"\n生成所有 predictions 文件到: {predictions_dir}")
        print("-" * 50)

        for c in combinations:
            generate_predictions(
                args.output_dir,
                c['dataset'],
                c['agent'],
                c['mode']
            )

        print("-" * 50)
        print(f"完成! 共生成 {len(combinations)} 个 predictions 文件")
        return

    if not all([args.dataset, args.agent, args.mode]):
        parser.print_help()
        print("\n错误: 需要指定 --dataset, --agent, --mode 或使用 --list/--all")
        return

    generate_predictions(
        args.output_dir,
        args.dataset,
        args.agent,
        args.mode,
        args.output_file
    )


if __name__ == "__main__":
    main()
