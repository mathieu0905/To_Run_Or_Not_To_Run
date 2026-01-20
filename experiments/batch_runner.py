#!/usr/bin/env python3
"""
Batch Runner: Execute multiple experiments in parallel
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import asdict

from runner import run_experiment, ExperimentResult


PROJ_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJ_ROOT / "output"


class BatchRunner:
    """Parallel experiment executor"""

    def __init__(
        self,
        max_workers: int = 4,
        dataset_name: str = "princeton-nlp/SWE-bench_Lite"
    ):
        self.max_workers = max_workers
        self.dataset_name = dataset_name

        # Determine dataset directory name
        self.dataset_dir = "swebenchlite" if "Lite" in dataset_name else "swebenchverified"

    def _get_checkpoint_file(self, agent_type: str, mode: str, k: int) -> Path:
        """Get checkpoint file path for specific configuration"""
        mode_dir = f"{mode}_k{k}" if mode == "run_less" else mode
        checkpoint_dir = OUTPUT_DIR / self.dataset_dir / agent_type / mode_dir
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        return checkpoint_dir / "checkpoint.json"

    def _get_output_dir(self, agent_type: str, mode: str, k: int) -> Path:
        """Get output directory path"""
        mode_dir = f"{mode}_k{k}" if mode == "run_less" else mode
        return OUTPUT_DIR / self.dataset_dir / agent_type / mode_dir

    def _has_valid_patch(self, instance_id: str, agent_type: str, mode: str, k: int) -> bool:
        """Check if instance has a valid patch file (exists and not empty)"""
        output_dir = self._get_output_dir(agent_type, mode, k)
        patch_file = output_dir / instance_id / "patch.diff"
        return patch_file.exists() and patch_file.stat().st_size > 0

    def run_batch(
        self,
        instances: List[str],
        mode: str,
        k: int = 2,
        agent_type: str = "claude_code",
        timeout: int = 600
    ) -> Dict[str, Optional[ExperimentResult]]:
        """
        Run multiple experiments in parallel

        Args:
            instances: List of instance IDs
            mode: Execution mode (run_free, run_less, run_cost, run_full)
            k: Execution limit for run_less mode
            agent_type: Agent type (claude_code, codex)
            timeout: Timeout per instance (seconds)

        Returns:
            Dictionary mapping instance_id to ExperimentResult (None if failed)
        """
        # Get checkpoint file for current configuration
        self.checkpoint_file = self._get_checkpoint_file(agent_type, mode, k)

        # Skip instances with valid patches (exists and not empty)
        remaining = [
            i for i in instances
            if not self._has_valid_patch(i, agent_type, mode, k)
        ]
        completed = len(instances) - len(remaining)

        print(f"Total instances: {len(instances)}")
        print(f"Completed: {completed}")
        print(f"Remaining: {len(remaining)}")
        print(f"Concurrency: {self.max_workers}")
        print(f"Mode: {mode}" + (f" (k={k})" if mode == "run_less" else ""))
        print("=" * 60)

        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(
                    run_experiment,
                    instance_id=inst,
                    mode=mode,
                    k=k,
                    agent_type=agent_type,
                    timeout=timeout,
                    dataset_name=self.dataset_name
                ): inst
                for inst in remaining
            }

            # Process completed tasks
            for i, future in enumerate(as_completed(futures), 1):
                instance_id = futures[future]
                try:
                    result = future.result()
                    results[instance_id] = result

                    # Update checkpoint
                    self._update_checkpoint(instance_id)

                    # Print progress
                    status = "✓" if result.success else "✗"
                    print(f"[{i}/{len(remaining)}] {status} {instance_id} "
                          f"({result.duration_sec:.1f}s, {result.tokens_used} tokens, "
                          f"{result.exec_count} execs)")

                except Exception as e:
                    print(f"[{i}/{len(remaining)}] ✗ {instance_id} - Error: {e}")
                    results[instance_id] = None

        # Print summary
        print("=" * 60)
        success_count = sum(1 for r in results.values() if r and r.success)
        print(f"Completed: {success_count}/{len(instances)} successful")

        return results

    def _load_checkpoint(self) -> set:
        """Load completed instance IDs"""
        if not self.checkpoint_file.exists():
            return set()

        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                return set(data.get("completed", []))
        except Exception as e:
            print(f"Warning: Failed to load checkpoint: {e}")
            return set()

    def _update_checkpoint(self, instance_id: str):
        """Add instance to checkpoint"""
        completed = self._load_checkpoint()
        completed.add(instance_id)

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({"completed": list(completed)}, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to update checkpoint: {e}")


def main():
    """CLI entry point"""
    if len(sys.argv) < 3:
        print("Usage: python batch_runner.py <instances_file> <mode> [k] [workers] [agent_type] [timeout] [dataset_name]")
        print()
        print("Arguments:")
        print("  instances_file  File containing instance IDs (one per line)")
        print("  mode           Execution mode: run_free, run_less, run_cost, run_full")
        print("  k              [Optional] Execution limit for run_less mode (default: 2)")
        print("  workers        [Optional] Concurrency level (default: 4)")
        print("  agent_type     [Optional] Agent type: claude_code, codex (default: claude_code)")
        print("  timeout        [Optional] Timeout per instance in seconds (default: 600)")
        print("  dataset_name   [Optional] Dataset name (default: princeton-nlp/SWE-bench_Lite)")
        print()
        print("Examples:")
        print("  python batch_runner.py instances.txt run_free")
        print("  python batch_runner.py instances.txt run_less 2 4")
        print("  python batch_runner.py instances.txt run_full 2 8 claude_code 600")
        print("  python batch_runner.py instances.txt run_less 2 4 claude_code 600 princeton-nlp/SWE-bench_Verified")
        sys.exit(1)

    # Parse arguments
    instances_file = Path(sys.argv[1])
    mode = sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    agent_type = sys.argv[5] if len(sys.argv) > 5 else "claude_code"
    timeout = int(sys.argv[6]) if len(sys.argv) > 6 else 600
    dataset_name = sys.argv[7] if len(sys.argv) > 7 else "princeton-nlp/SWE-bench_Lite"

    # Validate mode
    if mode not in ["run_free", "run_less", "run_cost", "run_full"]:
        print(f"Error: Invalid mode '{mode}'. Must be one of: run_free, run_less, run_cost, run_full")
        sys.exit(1)

    # Load instance list
    if not instances_file.exists():
        print(f"Error: Instances file not found: {instances_file}")
        sys.exit(1)

    instances = [
        line.strip()
        for line in instances_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not instances:
        print(f"Error: No instances found in {instances_file}")
        sys.exit(1)

    print(f"Loaded {len(instances)} instances from {instances_file}")
    print()

    # Run batch experiments
    try:
        runner = BatchRunner(
            max_workers=workers,
            dataset_name=dataset_name
        )
        results = runner.run_batch(instances, mode, k, agent_type, timeout)

        # Return status code
        # If no new instances were run (all skipped), return success
        if len(results) == 0:
            print("All instances already completed, no need to re-run")
            sys.exit(0)

        # Otherwise, check if all newly run instances succeeded
        success_count = sum(1 for r in results.values() if r and r.success)
        sys.exit(0 if success_count == len(results) else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress has been saved to checkpoint.")
        print("Re-run the same command to resume from where you left off.")
        sys.exit(130)
    except Exception as e:
        print(f"\nError running batch: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
