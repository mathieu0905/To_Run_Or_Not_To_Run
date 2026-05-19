#!/usr/bin/env python3
"""Shared data loading utilities - Provides unified data loading interface for all RQ analysis scripts"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# High-cost execution patterns (test frameworks)
HIGH_COST_PATTERNS = [
    "pytest", "python -m pytest", "python -m unittest",
    "manage.py test", "python manage.py test",
    "tox", "nose", "nosetests",
    "python -m django test",
    "python tests/runtests.py"
]

# Low-cost execution patterns (Python scripts)
PYTHON_SCRIPT_PATTERN = re.compile(r'\bpython\s+[a-zA-Z_][\w/\-]*\.py\b')

# Excluded agents (GLM)
EXCLUDED_AGENTS = ["claude_code_glm"]

# Dataset mapping
DATASETS = {
    "swebenchlite": "SWE-bench Lite",
    "swebenchverified": "SWE-bench Verified"
}

# Mode order (for sorting)
MODE_ORDER = ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"]


def count_tokens_and_execs(trace_path: Path) -> Dict:
    """Count tokens, execution count, interaction rounds and time from trace.jsonl"""
    tokens = {"input": 0, "output": 0}
    exec_count = 0
    high_cost_exec = 0
    low_cost_exec = 0
    turns = 0
    duration_ms = 0
    max_item_id = -1

    # Collect all executed commands
    commands = []

    # OpenCode-specific timestamp tracking for duration fallback
    oc_first_ts = None
    oc_last_ts = None
    oc_step_finish_count = 0

    prompt_path = trace_path.parent / "prompt.txt"

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)

                # Codex format
                if item.get("type") == "turn.completed":
                    usage = item.get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)

                if item.get("type") == "item.completed":  # Only record on completed to avoid duplicates
                    inner = item.get("item", {})
                    item_id = inner.get("id", "")
                    if item_id.startswith("item_"):
                        try:
                            id_num = int(item_id.split("_")[1])
                            max_item_id = max(max_item_id, id_num)
                        except:
                            pass

                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        commands.append(cmd)
                        if any(p in cmd for p in HIGH_COST_PATTERNS):
                            high_cost_exec += 1
                            exec_count += 1
                        elif PYTHON_SCRIPT_PATTERN.search(cmd):
                            low_cost_exec += 1
                            exec_count += 1

                # Claude Code format
                if item.get("type") == "assistant":
                    usage = item.get("message", {}).get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)
                    if usage.get("input_tokens", 0) > 0:
                        turns += 1

                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            commands.append(cmd)
                            if any(p in cmd for p in HIGH_COST_PATTERNS):
                                high_cost_exec += 1
                                exec_count += 1
                            elif PYTHON_SCRIPT_PATTERN.search(cmd):
                                low_cost_exec += 1
                                exec_count += 1

                # OpenCode format (OpenCode + vLLM/Qwen2.5-Coder-32B)
                # Events: step_start, text, tool_use, step_finish
                # Tokens accounted per step in step_finish.part.tokens
                # Tool calls appear under tool_use with part.tool == "bash"
                oc_type = item.get("type")
                if oc_type in ("step_start", "step_finish", "tool_use", "text"):
                    ts = item.get("timestamp")
                    if ts is not None:
                        if oc_first_ts is None:
                            oc_first_ts = ts
                        oc_last_ts = ts

                if oc_type == "step_finish":
                    part = item.get("part", {}) or {}
                    tok = part.get("tokens", {}) or {}
                    tokens["input"] += tok.get("input", 0) or 0
                    tokens["output"] += tok.get("output", 0) or 0
                    oc_step_finish_count += 1

                if oc_type == "tool_use":
                    part = item.get("part", {}) or {}
                    if part.get("tool") == "bash":
                        state = part.get("state", {}) or {}
                        if isinstance(state, dict):
                            cmd = (state.get("input", {}) or {}).get("command", "") or ""
                            if cmd:
                                commands.append(cmd)
                                if any(p in cmd for p in HIGH_COST_PATTERNS):
                                    high_cost_exec += 1
                                    exec_count += 1
                                elif PYTHON_SCRIPT_PATTERN.search(cmd):
                                    low_cost_exec += 1
                                    exec_count += 1

                if item.get("type") == "result":
                    duration_ms = item.get("duration_ms", 0)
            except:
                continue

    if max_item_id >= 0:
        turns = max_item_id + 1
    elif oc_step_finish_count > 0:
        # OpenCode: each step_finish corresponds to one assistant turn
        turns = oc_step_finish_count

    # OpenCode: derive duration from first/last event timestamps if missing
    if duration_ms == 0 and oc_first_ts is not None and oc_last_ts is not None:
        delta = oc_last_ts - oc_first_ts
        if delta > 0:
            duration_ms = int(delta)

    # Fallback time calculation
    if duration_ms == 0 and prompt_path.exists() and trace_path.exists():
        try:
            prompt_mtime = prompt_path.stat().st_mtime
            trace_mtime = trace_path.stat().st_mtime
            duration_sec = trace_mtime - prompt_mtime
            if duration_sec > 0:
                duration_ms = int(duration_sec * 1000)
        except:
            pass

    return {
        "tokens": tokens,
        "exec_count": exec_count,
        "high_cost_exec": high_cost_exec,
        "low_cost_exec": low_cost_exec,
        "turns": turns,
        "duration_ms": duration_ms,
        "commands": commands
    }


def check_patch(patch_path: Path) -> bool:
    """Check if patch is non-empty"""
    if not patch_path.exists():
        return False
    with open(patch_path) as f:
        content = f.read().strip()
    return len(content) > 0


def load_sb_cli_report(sb_cli_reports_dir: Path, dataset: str, agent: str, mode: str) -> Optional[Dict]:
    """Load evaluation report from sb-cli-reports directory"""
    if not sb_cli_reports_dir.exists():
        return None

    if "lite" in dataset.lower():
        dataset_pattern = "swe-bench_lite"
    elif "verified" in dataset.lower():
        dataset_pattern = "swe-bench_verified"
    else:
        dataset_pattern = "*"

    patterns = [
        f"{dataset_pattern}*{agent}*{mode}*.json",
        f"{dataset_pattern}*{agent}_{mode}.json",
        f"{dataset_pattern}*{agent}__{mode}.json",
    ]

    for pattern in patterns:
        matches = list(sb_cli_reports_dir.glob(pattern))
        if matches:
            try:
                return json.loads(matches[0].read_text(encoding="utf-8"))
            except:
                pass
    return None


def load_all_results(output_dir: Path = None, exclude_glm: bool = True) -> Dict:
    """
    Load all experimental results

    Return structure:
    {
        "swebenchlite": {
            "claude_code": {
                "run_free": {
                    "instance_id": {...},
                    ...
                },
                ...
            },
            ...
        },
        ...
    }
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "output"

    results = {}

    for dataset_dir in output_dir.iterdir():
        if not dataset_dir.is_dir():
            continue
        dataset = dataset_dir.name
        results[dataset] = {}

        for agent_dir in dataset_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            agent = agent_dir.name

            if exclude_glm and agent in EXCLUDED_AGENTS:
                continue

            results[dataset][agent] = {}

            for mode_dir in agent_dir.iterdir():
                if not mode_dir.is_dir():
                    continue
                mode = mode_dir.name
                results[dataset][agent][mode] = {}

                for instance_dir in mode_dir.iterdir():
                    if not instance_dir.is_dir():
                        continue
                    instance = instance_dir.name

                    trace_path = instance_dir / "trace.jsonl"
                    patch_path = instance_dir / "patch.diff"

                    if trace_path.exists():
                        data = count_tokens_and_execs(trace_path)
                        data["has_patch"] = check_patch(patch_path)
                        data["instance_id"] = instance
                        results[dataset][agent][mode][instance] = data

    return results


def load_pass_rates(sb_cli_reports_dir: Path = None) -> Dict:
    """
    Load all pass rate data

    Return structure:
    {
        "swebenchlite": {
            "claude_code": {
                "run_free": {"resolved": 63, "total": 100},
                ...
            },
            ...
        },
        ...
    }
    """
    if sb_cli_reports_dir is None:
        sb_cli_reports_dir = PROJECT_ROOT / "sb-cli-reports"

    pass_rates = defaultdict(lambda: defaultdict(dict))

    if not sb_cli_reports_dir.exists():
        return pass_rates

    # Version priority (higher = preferred; the one with the highest priority
    # among files matching the same (dataset, agent, mode) wins).
    # _fixed runs are the authoritative post-bracket-bug-fix opencode submissions.
    def _version_priority(fname: str) -> int:
        low = fname.lower()
        if "_fixed" in low:
            return 100
        if "_final" in low:
            return 50
        if "_v2" in low:
            return 40
        if "_snap" in low:
            return 30
        if "_v1" in low:
            return 10
        return 20  # plain (no suffix) — e.g. claude_code / codex canonical

    # Collect candidate reports per (dataset, agent, mode)
    candidates = defaultdict(list)  # (ds, agent, mode) -> [(priority, path)]

    for report_file in sb_cli_reports_dir.glob("*.json"):
        filename = report_file.stem

        if "lite" in filename.lower():
            dataset = "swebenchlite"
        elif "verified" in filename.lower():
            dataset = "swebenchverified"
        else:
            continue

        # Normalise the filename so OpenCode's suffix-less variants
        # (runfree / runfull / runcost / runlessk1 / runlessk3) match the
        # canonical MODE_ORDER names.
        norm = filename.replace("runfree", "run_free") \
                       .replace("runfull", "run_full") \
                       .replace("runcost", "run_cost") \
                       .replace("runlessk1", "run_less_k1") \
                       .replace("runlessk2", "run_less_k2") \
                       .replace("runlessk3", "run_less_k3")

        matched_agent = None
        for agent in ["claude_code", "codex", "opencode"]:
            if agent in norm:
                matched_agent = agent
                break
        if matched_agent is None:
            continue

        matched_mode = None
        # Iterate mode names longest-first so that "run_less_k1" wins over
        # "run_free" when both appear as substrings.
        for mode in sorted(MODE_ORDER, key=len, reverse=True):
            if mode in norm:
                matched_mode = mode
                break
        if matched_mode is None:
            continue

        candidates[(dataset, matched_agent, matched_mode)].append(
            (_version_priority(filename), report_file)
        )

    # For each (ds, agent, mode) pick the highest-priority file.
    for (ds, agent, mode), cands in candidates.items():
        cands.sort(key=lambda x: x[0], reverse=True)
        _, best = cands[0]
        try:
            report = json.loads(best.read_text(encoding="utf-8"))
        except Exception:
            continue
        resolved = report.get("resolved_instances", 0)
        completed = report.get("completed_instances", 0)
        # Keep the 100-sample denominator normalisation; resolved count is
        # independent of how many instances were submitted to sb-cli because
        # empty patches never resolve.
        pass_rates[ds][agent][mode] = {
            "resolved": resolved,
            "total": 100,
            "submitted": completed,
            "_source_file": best.name,
        }

    return pass_rates


def get_aggregated_stats(results: Dict) -> Dict:
    """
    Calculate aggregated statistics

    Return structure:
    {
        "swebenchlite": {
            "claude_code": {
                "run_free": {
                    "n": 100,
                    "avg_input_tokens": 66942,
                    "avg_output_tokens": 2103,
                    "avg_total_tokens": 69046,
                    "avg_turns": 35.2,
                    "avg_high_cost_exec": 0.6,
                    "avg_low_cost_exec": 0.2,
                    "avg_time_sec": 530.7,
                    "patch_count": 100
                },
                ...
            },
            ...
        },
        ...
    }
    """
    stats = {}

    for dataset, agents in results.items():
        stats[dataset] = {}
        for agent, modes in agents.items():
            stats[dataset][agent] = {}
            for mode, instances in modes.items():
                n = len(instances)
                if n == 0:
                    continue

                # Only count instances with patches
                patched = {k: v for k, v in instances.items() if v.get("has_patch", False)}
                patches = len(patched)

                if patches == 0:
                    continue

                total_input = sum(v["tokens"]["input"] for v in patched.values())
                total_output = sum(v["tokens"]["output"] for v in patched.values())
                total_high_cost = sum(v["high_cost_exec"] for v in patched.values())
                total_low_cost = sum(v["low_cost_exec"] for v in patched.values())
                total_turns = sum(v["turns"] for v in patched.values())
                total_duration = sum(v["duration_ms"] for v in patched.values())

                stats[dataset][agent][mode] = {
                    "n": n,
                    "avg_input_tokens": total_input // patches,
                    "avg_output_tokens": total_output // patches,
                    "avg_total_tokens": (total_input + total_output) // patches,
                    "avg_turns": total_turns / patches,
                    "avg_high_cost_exec": total_high_cost / patches,
                    "avg_low_cost_exec": total_low_cost / patches,
                    "avg_time_sec": total_duration / patches / 1000,
                    "patch_count": patches
                }

    return stats


def sort_modes(modes: List[str]) -> List[str]:
    """Sort modes by predefined order"""
    return sorted(modes, key=lambda x: MODE_ORDER.index(x) if x in MODE_ORDER else len(MODE_ORDER))
