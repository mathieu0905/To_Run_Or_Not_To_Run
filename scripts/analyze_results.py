#!/usr/bin/env python3
"""Script for analyzing experiment results

Default statistics:
- tokens (input/output)
- execution count (high-cost/low-cost)
- interaction turns
- duration
- whether patch was generated

Optional: If SWE-bench harness `run_id` is provided, additional statistics:
- whether patch was successfully applied (patch_successfully_applied)
- whether it passed official evaluation (resolved)
"""

import json
import os
import argparse
from pathlib import Path
from collections import defaultdict

def count_tokens_and_execs(trace_path):
    """Count tokens, execution count, interaction turns, and time from trace.jsonl"""
    tokens = {"input": 0, "output": 0}
    exec_count = 0
    high_cost_exec = 0  # High-cost execution (test frameworks)
    low_cost_exec = 0   # Low-cost execution (scripts)
    turns = 0
    duration_ms = 0
    max_item_id = -1
    cost_points = 0.0  # Cost points for run_cost mode

    # High-cost execution: test frameworks (running entire test suite)
    high_cost_patterns = [
        "pytest", "python -m pytest", "python -m unittest",
        "manage.py test", "python manage.py test",
        "tox", "nose", "nosetests",
        "python -m django test",
        "python tests/runtests.py"
    ]
    # Low-cost execution: directly running Python scripts
    import re
    python_script_pattern = re.compile(r'\bpython\s+[a-zA-Z_][\w/\-]*\.py\b')
    # [COST] X.X points pattern
    cost_pattern = re.compile(r'\[COST\]\s*([\d.]+)\s*points?', re.IGNORECASE)

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)
                # Codex format: turn.completed (count tokens)
                if item.get("type") == "turn.completed":
                    usage = item.get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)
                # Codex format: count max item id as turn count
                if item.get("type") in ["item.started", "item.completed"]:
                    inner = item.get("item", {})
                    item_id = inner.get("id", "")
                    if item_id.startswith("item_"):
                        try:
                            id_num = int(item_id.split("_")[1])
                            max_item_id = max(max_item_id, id_num)
                        except:
                            pass
                    # Count execution count
                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        # First check if it's high-cost execution
                        if any(p in cmd for p in high_cost_patterns):
                            high_cost_exec += 1
                            exec_count += 1
                        # Otherwise check if it's low-cost execution (python script.py)
                        elif python_script_pattern.search(cmd):
                            low_cost_exec += 1
                            exec_count += 1
                # Claude Code format: usage in assistant messages
                if item.get("type") == "assistant":
                    usage = item.get("message", {}).get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)
                    # Each assistant message counts as one turn
                    if usage.get("input_tokens", 0) > 0:
                        turns += 1
                    # Count execution count (Claude Code)
                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            # First check if it's high-cost execution
                            if any(p in cmd for p in high_cost_patterns):
                                high_cost_exec += 1
                                exec_count += 1
                            # Otherwise check if it's low-cost execution (python script.py)
                            elif python_script_pattern.search(cmd):
                                low_cost_exec += 1
                                exec_count += 1
                # Extract time information (last line's result)
                if item.get("type") == "result":
                    duration_ms = item.get("duration_ms", 0)
            except:
                continue

    # If it's Codex (has max_item_id), use max_item_id + 1 as turn count
    if max_item_id >= 0:
        turns = max_item_id + 1

    return tokens, exec_count, high_cost_exec, low_cost_exec, turns, duration_ms

def check_patch(patch_path):
    """Check if patch is non-empty"""
    if not os.path.exists(patch_path):
        return False
    with open(patch_path) as f:
        content = f.read().strip()
    return len(content) > 0

def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _find_eval_report(
    eval_root: Path,
    run_id: str,
    agent: str,
    mode: str,
    instance: str,
) -> Path | None:
    """
    SWE-bench harness report location:
      logs/run_evaluation/{run_id}/{model_name_or_path}/{instance_id}/report.json

    Note: harness will replace "/" with "__" when creating the model directory.
    """
    model_dir_candidates = [
        f"{agent}__{mode}",     # if model_name_or_path = "{agent}/{mode}"
        f"{agent}_{mode}",      # fallback (if someone uses underscores)
        f"{agent}-{mode}",      # fallback
        mode,                   # fallback
    ]
    for model_dir in model_dir_candidates:
        candidate = eval_root / run_id / model_dir / instance / "report.json"
        if candidate.exists():
            return candidate
    return None


def _get_eval_status(
    eval_root: Path,
    run_id: str | None,
    agent: str,
    mode: str,
    instance: str,
) -> dict | None:
    if not run_id:
        return None
    report_path = _find_eval_report(eval_root, run_id, agent, mode, instance)
    if not report_path:
        return None
    report = _read_json(report_path)
    if not isinstance(report, dict):
        return None
    per_instance = report.get(instance)
    if not isinstance(per_instance, dict):
        return None
    return {
        "patch_successfully_applied": bool(per_instance.get("patch_successfully_applied", False)),
        "resolved": bool(per_instance.get("resolved", False)),
    }


def analyze(output_dir: str, eval_root: str | None = None, eval_run_id: str | None = None):
    """Analyze output directory"""
    output_dir = Path(output_dir)
    eval_root_path = Path(eval_root) if eval_root else (Path(__file__).parent.parent / "logs" / "run_evaluation")
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
                    eval_status = _get_eval_status(eval_root_path, eval_run_id, agent, mode, instance)

                    results[agent][mode][instance] = {
                        "tokens": tokens,
                        "exec_count": exec_count,
                        "high_cost_exec": high_cost_exec,
                        "low_cost_exec": low_cost_exec,
                        "turns": turns,
                        "duration_ms": duration_ms,
                        "has_patch": has_patch,
                        "eval": eval_status,
                    }

    return results

def print_summary(results, show_eval: bool = False):
    """Print summary"""
    print("=" * 110)
    print("Experiment Results Analysis")
    print("=" * 110)

    for agent, modes in sorted(results.items()):
        print(f"\n### Agent: {agent}")
        print("-" * 130)
        if show_eval:
            print(f"{'Mode':<15} {'N':<5} {'Avg Input':<12} {'Avg Output':<12} {'Avg Total':<12} {'Avg Turns':<10} {'High-Cost':<11} {'Low-Cost':<10} {'Avg Time':<12} {'Patch':<9} {'Applied':<9} {'Resolved'}")
        else:
            print(f"{'Mode':<15} {'N':<5} {'Avg Input':<12} {'Avg Output':<12} {'Avg Total':<12} {'Avg Turns':<10} {'High-Cost':<11} {'Low-Cost':<10} {'Avg Time':<12} {'Patch'}")
        print("-" * 130)

        for mode, instances in sorted(modes.items()):
            n = len(instances)
            # Only count instances with patches
            patched = {k: v for k, v in instances.items() if v["has_patch"]}
            patches = len(patched)

            total_input = sum(v["tokens"]["input"] for v in patched.values())
            total_output = sum(v["tokens"]["output"] for v in patched.values())
            total_high_cost = sum(v["high_cost_exec"] for v in patched.values())
            total_low_cost = sum(v["low_cost_exec"] for v in patched.values())
            total_turns = sum(v["turns"] for v in patched.values())
            total_duration = sum(v["duration_ms"] for v in patched.values())

            avg_input = total_input // patches if patches > 0 else 0
            avg_output = total_output // patches if patches > 0 else 0
            avg_total = (total_input + total_output) // patches if patches > 0 else 0
            avg_turns = total_turns / patches if patches > 0 else 0
            avg_high_cost = total_high_cost / patches if patches > 0 else 0
            avg_low_cost = total_low_cost / patches if patches > 0 else 0
            avg_duration_sec = (total_duration / patches / 1000) if patches > 0 else 0

            if show_eval:
                applied = 0
                resolved = 0
                evaluated = 0
                for v in instances.values():
                    ev = v.get("eval")
                    if not ev:
                        continue
                    evaluated += 1
                    if ev.get("patch_successfully_applied"):
                        applied += 1
                    if ev.get("resolved"):
                        resolved += 1
                applied_str = f"{applied}/{evaluated}" if evaluated else "NA"
                resolved_str = f"{resolved}/{evaluated}" if evaluated else "NA"
                print(f"{mode:<15} {n:<5} {avg_input:<12} {avg_output:<12} {avg_total:<12} {avg_turns:<10.1f} {avg_high_cost:<11.1f} {avg_low_cost:<10.1f} {avg_duration_sec:<12.1f} {patches}/{n:<9} {applied_str:<9} {resolved_str}")
            else:
                print(f"{mode:<15} {n:<5} {avg_input:<12} {avg_output:<12} {avg_total:<12} {avg_turns:<10.1f} {avg_high_cost:<11.1f} {avg_low_cost:<10.1f} {avg_duration_sec:<12.1f} {patches}/{n}")

    # Detailed information
    # print("\n" + "=" * 110)
    # print("Detailed Results")
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
    parser = argparse.ArgumentParser(description="Analyze experiment outputs.")
    parser.add_argument("output_dir", nargs="?", default=None, help="Output directory to analyze (default: both datasets under ./output)")
    parser.add_argument("--eval-run-id", default=None, help="SWE-bench harness run_id (enables Applied/Resolved columns)")
    parser.add_argument("--eval-root", default=None, help="Path to logs/run_evaluation (default: ./logs/run_evaluation)")
    args = parser.parse_args()

    # Default: analyze both datasets
    if args.output_dir:
        output_dirs = [args.output_dir]
    else:
        base_dir = "output"
        output_dirs = [
            f"{base_dir}/swebenchlite",
            f"{base_dir}/swebenchverified"
        ]

    # Analyze each dataset
    for output_dir in output_dirs:
        if not os.path.exists(output_dir):
            print(f"\nSkipping non-existent directory: {output_dir}")
            continue

        print(f"\n{'='*120}")
        print(f"Dataset: {os.path.basename(output_dir)}")
        print(f"{'='*120}")

        results = analyze(output_dir, eval_root=args.eval_root, eval_run_id=args.eval_run_id)
        print_summary(results, show_eval=bool(args.eval_run_id))
