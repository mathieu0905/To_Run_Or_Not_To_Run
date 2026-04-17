#!/usr/bin/env python3
"""
Experiment Runner: Test Run-Free / Run-Less / Run-Full modes
"""
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from datasets import load_dataset

from agent_caller import AgentCaller, AgentTrace
from prompt_builder import PromptBuilder


# Where we persist prompts/traces/results. Tests patch this constant.
RESULTS_DIR = Path(__file__).parent.parent / "output"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ExperimentResult:
    """Experiment result"""
    instance_id: str
    mode: str  # run_free, run_less, run_full
    k: Optional[int]  # Execution limit for run_less
    patch: str
    tokens_used: int
    exec_count: int
    duration_sec: float
    success: bool
    error: str = ""
    agent_type: str = "claude_code"


def get_instance_info(instance_id: str, dataset_name: str = "princeton-nlp/SWE-bench_Lite") -> dict:
    """Get instance information from SWE-bench dataset"""
    dataset = load_dataset(dataset_name, split="test")
    for item in dataset:
        if item["instance_id"] == instance_id:
            return item
    raise ValueError(f"Instance {instance_id} not found in dataset {dataset_name}")


def extract_patch(output: str) -> str:
    """Extract git diff format patch from agent output"""
    lines = output.split("\n")
    patch_lines = []
    in_patch = False

    for line in lines:
        # Detect diff start markers
        if line.startswith("diff --git") or line.startswith("---") or line.startswith("+++"):
            in_patch = True

        if in_patch:
            patch_lines.append(line)

            # If enough content collected, can end early
            if line.startswith("@@") and len(patch_lines) > 10:
                # Continue collecting until next file or end
                continue

    return "\n".join(patch_lines) if patch_lines else ""


def run_experiment(
    instance_id: str,
    mode: str,
    k: int = 2,
    agent_type: str = "claude_code",
    timeout: int = 600,
    dataset_name: str = "princeton-nlp/SWE-bench_Lite"
) -> ExperimentResult:
    """
    Run single experiment

    Args:
        instance_id: SWE-bench instance ID
        mode: Execution mode (run_free, run_less, run_full)
        k: Execution limit for run_less mode
        agent_type: Agent type (claude_code, codex)
        timeout: Timeout (seconds)

    Returns:
        ExperimentResult object
    """
    # 1. Get instance information
    print(f"Loading instance: {instance_id}")
    instance = get_instance_info(instance_id, dataset_name)

    # Build mode identifier (run_less needs to include k value)
    mode_suffix = f"{mode}_k{k}" if mode == "run_less" else mode

    # Extract short name from dataset_name
    if "Verified" in dataset_name:
        dataset_short = "swebenchverified"
    else:
        dataset_short = "swebenchlite"

    # Result output directory: output/dataset/agent/mode/instance
    instance_output_dir = RESULTS_DIR / dataset_short / agent_type / mode_suffix / instance_id
    instance_output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Build prompt
    print(f"Building prompt for mode: {mode}" + (f" (k={k})" if mode == "run_less" else ""))
    prompt = PromptBuilder.build_prompt(instance, mode, k, agent_type)

    # Save prompt to instance directory
    prompt_file = instance_output_dir / "prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    print(f"Prompt saved to: {prompt_file}")

    # 3. Call agent (trace written in real-time to output directory)
    print(f"Calling {agent_type} agent (timeout={timeout}s)...")
    trace_file = instance_output_dir / "trace.jsonl"
    caller = AgentCaller(agent_type=agent_type, instance_id=instance_id, mode=mode)
    trace: AgentTrace = caller.call(prompt, timeout=timeout, trace_output_path=str(trace_file))
    print(f"Trace saved to: {trace_file}")
    if trace.error:
        print(f"Agent error: {trace.error}")

    # 4. Prefer git-diff patch emitted by agent runner (docker mode); otherwise
    # fall back to extracting a diff block from the agent's text output. We
    # intentionally do NOT fall back to raw trace.output: SWE-bench needs a
    # valid git diff, and counting plain prose as a "patch" was hiding cases
    # where the model never called the edit tool (resulting in misleading
    # success=True for what is really an empty/no-op submission).
    patch = ""
    patch_file = instance_output_dir / "patch.diff"
    if patch_file.exists():
        patch = patch_file.read_text(encoding="utf-8").strip()
        print(f"Patch loaded from git diff: {patch_file}")
    if not patch:
        patch = extract_patch(trace.output).strip()
        if patch:
            print("Patch extracted from agent text output")

    # 5. Build result
    result = ExperimentResult(
        instance_id=instance_id,
        mode=mode,
        k=k if mode == "run_less" else None,
        patch=patch,
        tokens_used=trace.tokens_used,
        exec_count=trace.exec_count,
        duration_sec=trace.duration_sec,
        success=bool(patch) and not trace.error,
        error=trace.error or "",
        agent_type=agent_type
    )

    return result


def save_result(result: ExperimentResult, dataset_name: str = "princeton-nlp/SWE-bench_Lite"):
    """Save experiment result to JSON file"""
    # Extract short name from dataset_name
    if "Verified" in dataset_name:
        dataset_short = "swebenchverified"
    else:
        dataset_short = "swebenchlite"

    mode_suffix = f"{result.mode}_k{result.k}" if result.mode == "run_less" else result.mode

    payload = asdict(result)

    # Backward-compatible flat filename used by unit tests.
    flat_result_file = RESULTS_DIR / f"{result.instance_id}_{mode_suffix}_result.json"
    flat_result_file.parent.mkdir(parents=True, exist_ok=True)
    with open(flat_result_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    # Also write into the per-instance output directory used by the CLI runner.
    result_dir = RESULTS_DIR / dataset_short / result.agent_type / mode_suffix / result.instance_id
    result_dir.mkdir(parents=True, exist_ok=True)
    nested_result_file = result_dir / "result.json"
    with open(nested_result_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"Result saved to: {nested_result_file}")


def print_summary(result: ExperimentResult):
    """Print experiment result summary"""
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    print(f"Instance ID:    {result.instance_id}")
    print(f"Mode:           {result.mode}" + (f" (k={result.k})" if result.k else ""))
    print(f"Agent:          {result.agent_type}")
    print(f"Success:        {result.success}")
    print(f"Tokens Used:    {result.tokens_used}")
    print(f"Exec Count:     {result.exec_count}")
    print(f"Duration:       {result.duration_sec:.2f}s")
    print(f"Patch Length:   {len(result.patch)} chars")

    if result.error:
        print(f"Error:          {result.error[:200]}")

    print("=" * 60)


def main():
    """Main function: Parse command line arguments and run experiment"""
    if len(sys.argv) < 3:
        print("Usage: python runner.py <instance_id> <mode> [k] [agent_type] [timeout]")
        print()
        print("Arguments:")
        print("  instance_id   SWE-bench instance ID (e.g.: django__django-11099)")
        print("  mode          Execution mode: run_free, run_less, run_cost, run_full")
        print("  k             [Optional] Execution limit for run_less mode (default: 2)")
        print("  agent_type    [Optional] Agent type: claude_code, codex (default: claude_code)")
        print("  timeout       [Optional] Timeout in seconds (default: 600)")
        print("  dataset_name  [Optional] Dataset name (default: princeton-nlp/SWE-bench_Lite)")
        print()
        print("Examples:")
        print("  python runner.py django__django-11099 run_free")
        print("  python runner.py django__django-11099 run_less 2")
        print("  python runner.py django__django-11099 run_cost")
        print("  python runner.py django__django-11099 run_full")
        sys.exit(1)

    # Parse arguments
    instance_id = sys.argv[1]
    mode = sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    agent_type = sys.argv[4] if len(sys.argv) > 4 else "claude_code"
    timeout = int(sys.argv[5]) if len(sys.argv) > 5 else 600
    dataset_name = sys.argv[6] if len(sys.argv) > 6 else "princeton-nlp/SWE-bench_Lite"

    # Validate mode
    if mode not in ["run_free", "run_less", "run_cost", "run_full", "run_hard_free"]:
        print(f"Error: Invalid mode '{mode}'. Must be one of: run_free, run_less, run_cost, run_full, run_hard_free")
        sys.exit(1)

    # Run experiment
    try:
        result = run_experiment(instance_id, mode, k, agent_type, timeout, dataset_name)
        save_result(result, dataset_name)
        print_summary(result)

        # Return status code
        sys.exit(0 if result.success else 1)

    except Exception as e:
        print(f"\nError running experiment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
