#!/usr/bin/env python3
"""
Generate SWE-bench predictions file from output directory
"""

import os
import json
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"

def generate_predictions(output_dir: str, dataset: str, agent: str, mode: str, output_file: str = None):
    """
    Generate predictions JSON file

    Args:
        output_dir: output directory path
        dataset: dataset name (swebenchlite, swebenchverified)
        agent: agent name (claude_code, codex)
        mode: mode name (run_free, run_less_k1, run_less_k3, run_cost, run_full)
        output_file: output file path, defaults to predictions/{dataset}_{agent}_{mode}.json
    """
    base_path = Path(output_dir) / dataset / agent / mode

    if not base_path.exists():
        print(f"Error: Path does not exist: {base_path}")
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
            print(f"Warning: Missing patch.diff: {instance_dir}")

    # Determine output file path
    if output_file is None:
        predictions_dir = Path(output_dir).parent / "predictions"
        predictions_dir.mkdir(exist_ok=True)
        output_file = predictions_dir / f"{dataset}_{agent}_{mode}.json"

    # Save predictions
    with open(output_file, 'w') as f:
        json.dump(predictions, f, indent=2)

    print(f"Generated predictions file: {output_file}")
    print(f"  Number of instances: {len(predictions)}")

    return str(output_file)


def list_available_combinations(output_dir: str):
    """List all available dataset/agent/mode combinations"""
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

                # Count instances
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
    parser = argparse.ArgumentParser(description="Generate SWE-bench predictions file")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR),
                        help="output directory path")
    parser.add_argument("--dataset", help="dataset name")
    parser.add_argument("--agent", help="agent name")
    parser.add_argument("--mode", help="mode name")
    parser.add_argument("--output-file", help="output file path")
    parser.add_argument("--list", action="store_true", help="list all available combinations")
    parser.add_argument("--all", action="store_true", help="generate predictions for all combinations")

    args = parser.parse_args()

    if args.list:
        combinations = list_available_combinations(args.output_dir)
        print("\nAvailable dataset/agent/mode combinations:")
        print("-" * 70)
        print(f"{'Dataset':<20} {'Agent':<15} {'Mode':<15} {'Instances':<10} {'Patches':<10}")
        print("-" * 70)
        for c in combinations:
            print(f"{c['dataset']:<20} {c['agent']:<15} {c['mode']:<15} {c['instances']:<10} {c['patches']:<10}")
        print("-" * 70)
        print(f"Total: {len(combinations)} combinations")
        return

    if args.all:
        combinations = list_available_combinations(args.output_dir)
        predictions_dir = Path(args.output_dir).parent / "predictions"
        predictions_dir.mkdir(exist_ok=True)

        print(f"\nGenerating all predictions files to: {predictions_dir}")
        print("-" * 50)

        for c in combinations:
            generate_predictions(
                args.output_dir,
                c['dataset'],
                c['agent'],
                c['mode']
            )

        print("-" * 50)
        print(f"Complete! Generated {len(combinations)} predictions files")
        return

    if not all([args.dataset, args.agent, args.mode]):
        parser.print_help()
        print("\nError: Need to specify --dataset, --agent, --mode or use --list/--all")
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
