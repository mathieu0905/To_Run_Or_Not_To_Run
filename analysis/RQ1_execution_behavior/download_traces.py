#!/usr/bin/env python3
"""
Download SWE-bench experiment traces from GitHub/S3

This script downloads agent traces from the official SWE-bench/experiments repository.
Each submission folder contains:
- all_preds.jsonl: predictions
- metadata.yaml: submission metadata
- logs/: execution logs
- trajs/: reasoning traces
"""

import os
import subprocess
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional
import argparse


# List of submissions to download (agent+model combinations)
# Focus on popular agents with different models for comparison
SUBMISSIONS_LITE = [
    # SWE-agent variants
    "20240402_sweagent_gpt4",
    "20240402_sweagent_claude3opus",
    "20240620_sweagent_claude3.5sonnet",
    "20240728_sweagent_gpt4o",
    "20250226_sweagent_claude-3-7-sonnet-20250219",
    "20250526_sweagent_claude-4-sonnet-20250514",

    # Moatless variants
    "20240617_moatless_gpt4o",
    "20240623_moatless_claude35sonnet",
    "20241117_moatless_claude-3.5-sonnet-20241022",
    "20250111_moatless_deepseek_v3",
    "20250114_moatless_claude-3.5-sonnet-20241022",

    # Agentless variants
    "20240630_agentless_gpt4o",
    "20241028_agentless-1.5_gpt4o",
    "20241202_agentless-1.5_claude-3.5-sonnet-20241022",
    "20250214_agentless_lite_o3_mini",

    # OpenHands
    "20241025_OpenHands-CodeAct-2.1-sonnet-20241022",

    # AutoCoderover
    "20240530_autocoderover-v20240408",
    "20240621_autocoderover-v20240620",

    # Other notable agents
    "20240523_aider",
    "20240612_MASAI_gpt4o",
    "20240806_SuperCoder2.0",
    "20241016_IBM-SWE-1.0",
]

SUBMISSIONS_VERIFIED = [
    # We'll populate this after checking verified submissions
]


def clone_experiments_repo(output_dir: Path, sparse: bool = True) -> bool:
    """Clone the SWE-bench experiments repository"""
    repo_url = "https://github.com/SWE-bench/experiments.git"
    repo_dir = output_dir / "swe-bench-experiments"

    if repo_dir.exists():
        print(f"Repository already exists at {repo_dir}")
        return True

    print(f"Cloning {repo_url}...")

    if sparse:
        # Sparse checkout to only get evaluation folder
        try:
            subprocess.run(
                ["git", "clone", "--filter=blob:none", "--sparse", repo_url, str(repo_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            subprocess.run(
                ["git", "sparse-checkout", "set", "evaluation"],
                cwd=str(repo_dir),
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Sparse clone completed to {repo_dir}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Sparse clone failed: {e.stderr}")
            return False
    else:
        # Full clone
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, str(repo_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            print(f"Clone completed to {repo_dir}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Clone failed: {e.stderr}")
            return False


def download_from_s3(submission: str, split: str, output_dir: Path) -> bool:
    """Download traces from S3 bucket (if available)"""
    # S3 bucket structure: s3://swe-bench-experiments/{split}/{submission}/
    s3_path = f"s3://swe-bench-experiments/{split}/{submission}/"
    local_path = output_dir / split / submission

    local_path.mkdir(parents=True, exist_ok=True)

    try:
        # Try to sync from S3 (public bucket, no credentials needed)
        result = subprocess.run(
            ["aws", "s3", "sync", s3_path, str(local_path), "--no-sign-request"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print(f"Downloaded {submission} from S3")
            return True
        else:
            print(f"S3 download failed for {submission}: {result.stderr}")
            return False
    except FileNotFoundError:
        print("AWS CLI not found. Please install it or use git clone method.")
        return False
    except subprocess.TimeoutExpired:
        print(f"S3 download timed out for {submission}")
        return False


def list_available_submissions(repo_dir: Path, split: str = "lite") -> List[str]:
    """List all available submissions for a given split"""
    eval_dir = repo_dir / "evaluation" / split

    if not eval_dir.exists():
        print(f"Directory not found: {eval_dir}")
        return []

    submissions = []
    for item in eval_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            submissions.append(item.name)

    return sorted(submissions)


def get_submission_info(submission_dir: Path) -> Dict:
    """Extract metadata from a submission directory"""
    info = {
        "name": submission_dir.name,
        "has_preds": (submission_dir / "all_preds.jsonl").exists(),
        "has_metadata": (submission_dir / "metadata.yaml").exists(),
        "has_logs": (submission_dir / "logs").exists(),
        "has_trajs": (submission_dir / "trajs").exists(),
    }

    # Try to read metadata
    metadata_file = submission_dir / "metadata.yaml"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                info["metadata"] = yaml.safe_load(f)
        except Exception as e:
            info["metadata_error"] = str(e)

    # Count logs and trajs
    if info["has_logs"]:
        logs_dir = submission_dir / "logs"
        info["num_logs"] = len(list(logs_dir.glob("*")))

    if info["has_trajs"]:
        trajs_dir = submission_dir / "trajs"
        info["num_trajs"] = len(list(trajs_dir.glob("*")))

    return info


def main():
    parser = argparse.ArgumentParser(description="Download SWE-bench experiment traces")
    parser.add_argument("--output-dir", type=str, default="./data",
                        help="Output directory for downloaded data")
    parser.add_argument("--method", type=str, choices=["git", "s3"], default="git",
                        help="Download method: git clone or S3 sync")
    parser.add_argument("--split", type=str, choices=["lite", "verified", "both"], default="lite",
                        help="Which split to download")
    parser.add_argument("--list-only", action="store_true",
                        help="Only list available submissions, don't download")
    parser.add_argument("--submissions", type=str, nargs="+",
                        help="Specific submissions to download (default: predefined list)")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("SWE-bench Experiments Trace Downloader")
    print("=" * 60)
    print()

    if args.method == "git":
        # Clone the repository
        success = clone_experiments_repo(output_dir, sparse=True)
        if not success:
            print("Failed to clone repository. Trying full clone...")
            success = clone_experiments_repo(output_dir, sparse=False)

        if not success:
            print("Failed to clone repository. Try using --method s3")
            return

        repo_dir = output_dir / "swe-bench-experiments"

        # List available submissions
        splits = ["lite", "verified"] if args.split == "both" else [args.split]

        for split in splits:
            print(f"\n--- {split.upper()} ---")
            submissions = list_available_submissions(repo_dir, split)
            print(f"Found {len(submissions)} submissions")

            if args.list_only:
                for s in submissions:
                    info = get_submission_info(repo_dir / "evaluation" / split / s)
                    logs = info.get("num_logs", 0)
                    trajs = info.get("num_trajs", 0)
                    print(f"  {s}: logs={logs}, trajs={trajs}")
            else:
                # Process specified submissions or default list
                target_submissions = args.submissions or SUBMISSIONS_LITE

                for submission in target_submissions:
                    if submission in submissions:
                        info = get_submission_info(repo_dir / "evaluation" / split / submission)
                        print(f"  {submission}: logs={info.get('num_logs', 0)}, trajs={info.get('num_trajs', 0)}")
                    else:
                        print(f"  {submission}: NOT FOUND")

    elif args.method == "s3":
        splits = ["lite", "verified"] if args.split == "both" else [args.split]
        target_submissions = args.submissions or SUBMISSIONS_LITE

        for split in splits:
            print(f"\n--- {split.upper()} ---")
            for submission in target_submissions:
                download_from_s3(submission, split, output_dir)

    print()
    print("=" * 60)
    print("Download complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
