#!/usr/bin/env python3
"""
Evaluate generated patches with the official SWE-bench harness.

This script turns `output/<dataset>/<agent>/<mode>/<instance>/patch.diff` into a
SWE-bench predictions file (`.jsonl`), then runs:
  python -m swebench.harness.run_evaluation ...

Typical usage (evaluate one configuration to control cost):
  python experiments/evaluate_patches.py --dataset swebenchlite --agent claude_code --mode run_less_k2 --run-id issta-lite-claude-k2

After the harness finishes, you can augment the stats table with:
  python experiments/analyze_results.py --eval-run-id issta-lite-claude-k2
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Iterable


PROJ_ROOT = Path(__file__).parent.parent


def _default_dataset_name(dataset_dir_name: str) -> str:
    name = dataset_dir_name.lower()
    if "verified" in name:
        return "SWE-bench/SWE-bench_Verified"
    return "SWE-bench/SWE-bench_Lite"


def _iter_instances(output_root: Path, agent: str, mode: str) -> Iterable[Path]:
    base = output_root / agent / mode
    if not base.exists():
        return []
    return (p for p in base.iterdir() if p.is_dir())


def _read_patch(patch_path: Path) -> str:
    try:
        return patch_path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def build_predictions(
    output_root: Path,
    agent: str,
    mode: str,
    limit: int | None = None,
) -> list[dict]:
    predictions: list[dict] = []
    model_name_or_path = f"{agent}/{mode}"

    instances = sorted(_iter_instances(output_root, agent, mode), key=lambda p: p.name)
    if limit is not None:
        instances = instances[:limit]

    for inst_dir in instances:
        patch_path = inst_dir / "patch.diff"
        patch = _read_patch(patch_path)
        if not patch:
            continue
        predictions.append(
            {
                "instance_id": inst_dir.name,
                "model_name_or_path": model_name_or_path,
                "model_patch": patch,
            }
        )
    return predictions


def write_predictions(predictions: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(pred, ensure_ascii=False) + "\n")


def run_harness(
    dataset_name: str,
    predictions_path: Path,
    run_id: str,
    max_workers: int,
    timeout: int,
    force_rebuild: bool,
    cache_level: str,
    clean: bool,
) -> int:
    cmd = [
        "python",
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        dataset_name,
        "--predictions_path",
        str(predictions_path),
        "--max_workers",
        str(max_workers),
        "--timeout",
        str(timeout),
        "--run_id",
        run_id,
        "--cache_level",
        cache_level,
        "--clean",
        "true" if clean else "false",
        "--force_rebuild",
        "true" if force_rebuild else "false",
    ]
    return subprocess.call(cmd, cwd=str(PROJ_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate patches with SWE-bench harness.")
    parser.add_argument(
        "--dataset",
        required=True,
        choices=["swebenchlite", "swebenchverified"],
        help="Which output dataset folder to use under ./output/",
    )
    parser.add_argument("--agent", required=True, help="Agent directory name (e.g., claude_code, codex)")
    parser.add_argument("--mode", required=True, help="Mode directory name (e.g., run_free, run_less_k2, run_full)")
    parser.add_argument("--run-id", required=True, help="Harness run_id (used as log directory name)")
    parser.add_argument("--dataset-name", default=None, help="Override harness dataset_name (default based on --dataset)")
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=1800, help="Per-instance test timeout (seconds)")
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate first N instances (for smoke tests)")
    parser.add_argument("--dry-run", action="store_true", help="Only generate predictions.jsonl; do not run harness")
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild of images")
    parser.add_argument("--cache-level", default="env", choices=["none", "base", "env", "instance"])
    parser.add_argument("--clean", action="store_true", help="Clean images above cache level before run")
    args = parser.parse_args()

    output_root = PROJ_ROOT / "output" / args.dataset
    if not output_root.exists():
        raise SystemExit(f"Output folder not found: {output_root}")

    predictions = build_predictions(output_root, args.agent, args.mode, limit=args.limit)
    if not predictions:
        raise SystemExit(f"No non-empty patches found under {output_root}/{args.agent}/{args.mode}/")

    predictions_path = output_root / args.agent / args.mode / "predictions.jsonl"
    write_predictions(predictions, predictions_path)
    print(f"Wrote {len(predictions)} predictions to: {predictions_path}")

    if args.dry_run:
        print("Dry run: skipping harness evaluation.")
        return 0

    dataset_name = args.dataset_name or _default_dataset_name(args.dataset)
    print(f"Running harness: dataset={dataset_name} run_id={args.run_id} workers={args.max_workers} timeout={args.timeout}s")
    return run_harness(
        dataset_name=dataset_name,
        predictions_path=predictions_path,
        run_id=args.run_id,
        max_workers=args.max_workers,
        timeout=args.timeout,
        force_rebuild=args.force_rebuild,
        cache_level=args.cache_level,
        clean=args.clean,
    )


if __name__ == "__main__":
    raise SystemExit(main())

