#!/usr/bin/env python3
"""
Clean instances where the last line of trace.jsonl contains "is_error":true, and instances without patch.diff
"""
import json
import shutil
from pathlib import Path


def check_trace_has_error(trace_file: Path) -> bool:
    """Check if the last line of trace.jsonl file contains is_error:true"""
    try:
        with open(trace_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                return False

            last_line = lines[-1].strip()
            if not last_line:
                return False

            # Parse last line JSON
            try:
                data = json.loads(last_line)
                return data.get('is_error', False) is True
            except json.JSONDecodeError:
                return False
    except Exception as e:
        print(f"  Warning: Cannot read {trace_file}: {e}")
        return False


def clean_error_instances(base_dir: str):
    """Clean all instances containing errors"""
    base_path = Path(base_dir)

    if not base_path.exists():
        print(f"Directory does not exist: {base_dir}")
        return

    total_deleted = 0

    # Traverse all mode directories (run_free, run_less_k1, etc.)
    for mode_dir in base_path.iterdir():
        if not mode_dir.is_dir():
            continue

        print(f"\nProcessing mode: {mode_dir.name}")

        checkpoint_file = mode_dir / "checkpoint.json"
        checkpoint_data = {}

        # Read checkpoint.json
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoint_data = json.load(f)
            except Exception as e:
                print(f"  Warning: Cannot read checkpoint.json: {e}")

        deleted_instances = []

        # Traverse all instance directories
        for instance_dir in mode_dir.iterdir():
            if not instance_dir.is_dir():
                continue

            instance_id = instance_dir.name
            trace_file = instance_dir / "trace.jsonl"
            patch_file = instance_dir / "patch.diff"

            if not trace_file.exists():
                continue

            # Check if there's an error or missing patch or empty patch
            has_error = check_trace_has_error(trace_file)
            missing_patch = not patch_file.exists()
            empty_patch = patch_file.exists() and patch_file.stat().st_size == 0

            if has_error or missing_patch or empty_patch:
                reason = []
                if has_error:
                    reason.append("trace error")
                if missing_patch:
                    reason.append("missing patch")
                if empty_patch:
                    reason.append("empty patch")
                print(f"  Deleting instance: {instance_id} ({', '.join(reason)})")

                # Delete instance directory
                try:
                    shutil.rmtree(instance_dir)
                    deleted_instances.append(instance_id)
                    total_deleted += 1
                except Exception as e:
                    print(f"    Error: Cannot delete directory {instance_dir}: {e}")

        # Update checkpoint.json
        if deleted_instances and checkpoint_data:
            # checkpoint.json structure: {"completed": ["instance1", "instance2", ...]}
            if "completed" in checkpoint_data:
                original_count = len(checkpoint_data["completed"])
                checkpoint_data["completed"] = [
                    inst for inst in checkpoint_data["completed"]
                    if inst not in deleted_instances
                ]
                removed_count = original_count - len(checkpoint_data["completed"])

                # Write back checkpoint.json
                try:
                    with open(checkpoint_file, 'w') as f:
                        json.dump(checkpoint_data, f, indent=2)
                    print(f"  Updated checkpoint.json, removed {removed_count} instances from completed array")
                except Exception as e:
                    print(f"  Warning: Cannot update checkpoint.json: {e}")
            else:
                print(f"  Warning: checkpoint.json format incorrect, missing 'completed' field")

    print(f"\nTotal deleted {total_deleted} instances containing errors")


if __name__ == "__main__":
    # Optional directory list
    available_dirs = [
        "output/swebenchlite/claude_code",
        "output/swebenchlite/claude_code_glm",
        "output/swebenchlite/codex",
        "output/swebenchverified/claude_code",
        "output/swebenchverified/claude_code_glm",
        "output/swebenchverified/codex",
    ]

    print("=" * 60)
    print("Clean error instances in output directory")
    print("=" * 60)
    print("\nAvailable directories:")

    # Display available directories
    for i, dir_path in enumerate(available_dirs, 1):
        exists = Path(dir_path).exists()
        status = "✓" if exists else "✗"
        print(f"  {i}. [{status}] {dir_path}")

    # Get user input
    print("\nEnter directory numbers to clean (separate multiple numbers with commas or spaces, enter 'all' to clean all):")
    user_input = input("> ").strip()

    # Parse user input
    selected_dirs = []
    if user_input.lower() == 'all':
        selected_dirs = [d for d in available_dirs if Path(d).exists()]
    else:
        # Support comma or space separation
        numbers = user_input.replace(',', ' ').split()
        for num_str in numbers:
            try:
                num = int(num_str)
                if 1 <= num <= len(available_dirs):
                    dir_path = available_dirs[num - 1]
                    if Path(dir_path).exists():
                        selected_dirs.append(dir_path)
                    else:
                        print(f"Warning: Directory {dir_path} does not exist, skipping")
                else:
                    print(f"Warning: Number {num} out of range, skipping")
            except ValueError:
                print(f"Warning: Invalid input '{num_str}', skipping")

    # Confirm cleaning
    if not selected_dirs:
        print("\nNo directories selected, exiting")
    else:
        print(f"\nWill clean the following {len(selected_dirs)} directories:")
        for dir_path in selected_dirs:
            print(f"  - {dir_path}")

        confirm = input("\nConfirm cleaning? (y/N): ").strip().lower()
        if confirm == 'y':
            for dir_path in selected_dirs:
                clean_error_instances(dir_path)
        else:
            print("Cleaning cancelled")
