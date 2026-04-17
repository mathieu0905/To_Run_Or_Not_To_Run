#!/usr/bin/env python3
"""Per-mode compliance table.

Reviewer C asked: for each execution mode, how many test-framework executions
were attempted, how many succeeded, how many hit environment errors, and how
many produced actionable test signal? This script answers that by walking
every trace.jsonl under output/ and classifying each attempted execution.

Output: compliance_table.md + compliance_table.csv in this directory.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.data_loader import (
    DATASETS,
    EXCLUDED_AGENTS,
    HIGH_COST_PATTERNS,
    MODE_ORDER,
    PROJECT_ROOT,
    PYTHON_SCRIPT_PATTERN,
    sort_modes,
)

# --- Classification patterns ---------------------------------------------------

ENV_ERROR_PATTERNS = [
    re.compile(r"ModuleNotFoundError", re.IGNORECASE),
    re.compile(r"No module named", re.IGNORECASE),
    re.compile(r"ImportError:\s*cannot import", re.IGNORECASE),
    re.compile(r"command not found", re.IGNORECASE),
    re.compile(r"executable not found", re.IGNORECASE),
    re.compile(r"No such file or directory.*(pytest|python|tox)", re.IGNORECASE),
    re.compile(r"error while loading shared libraries", re.IGNORECASE),
    re.compile(r"\bpytest: error: unrecognized arguments", re.IGNORECASE),
]

TEST_PASS_PATTERNS = [
    re.compile(r"\b\d+\s+passed\b", re.IGNORECASE),          # pytest: "42 passed"
    re.compile(r"^OK\b", re.MULTILINE),                      # unittest: "OK"
    re.compile(r"Ran\s+\d+\s+tests?\s+in", re.IGNORECASE),   # unittest header
]

TEST_FAIL_PATTERNS = [
    re.compile(r"\b\d+\s+failed\b", re.IGNORECASE),          # pytest: "3 failed"
    re.compile(r"^FAILED\b", re.MULTILINE),
    re.compile(r"AssertionError", re.IGNORECASE),
    re.compile(r"^FAIL:\s", re.MULTILINE),                   # unittest: "FAIL: test_x"
    re.compile(r"^ERROR:\s", re.MULTILINE),                  # unittest: "ERROR: test_x"
    re.compile(r"Traceback \(most recent call last\)", re.IGNORECASE),
]


def is_test_exec_command(cmd: str) -> bool:
    """Match the same test-frameworks as data_loader.count_tokens_and_execs."""
    if any(p in cmd for p in HIGH_COST_PATTERNS):
        return True
    if PYTHON_SCRIPT_PATTERN.search(cmd):
        return True
    return False


def classify_output(
    output: str,
    exit_code: Optional[int],
) -> Dict[str, bool]:
    """Classify an execution outcome from its stdout/stderr plus exit code.

    Four-column taxonomy for the compliance table:
      * env_error  — blocked by import / missing-module / dependency errors
      * completed  — ran to the test stage (not env_error) and is non-empty
      * actionable — produced a concrete pass/fail test signal (subset of completed)
      * all_passed — every test passed (subset of actionable)
    """
    text = output or ""

    env_error = any(p.search(text) for p in ENV_ERROR_PATTERNS)
    test_pass = any(p.search(text) for p in TEST_PASS_PATTERNS)
    test_fail = any(p.search(text) for p in TEST_FAIL_PATTERNS)

    completed = (not env_error) and bool(text.strip())
    actionable = completed and (test_pass or test_fail)
    all_passed = actionable and test_pass and not test_fail

    # Codex exit_code refines completed: non-zero exit with no test signal and
    # no env error = crashed before completing (e.g. timeout, syntax).
    if exit_code is not None and not (test_pass or test_fail):
        if exit_code != 0 and not env_error:
            completed = False

    return {
        "env_error": env_error,
        "completed": completed,
        "actionable": actionable,
        "all_passed": all_passed,
        "test_pass": test_pass,
        "test_fail": test_fail,
    }


# --- Trace walkers -------------------------------------------------------------

def _tool_result_text(content) -> str:
    """Claude Code tool_result.content can be a string or a list of blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    chunks.append(block.get("text", "") or "")
                elif block.get("type") == "tool_result":
                    inner = block.get("content", "")
                    chunks.append(_tool_result_text(inner))
        return "\n".join(chunks)
    return str(content or "")


def parse_trace(trace_path: Path) -> List[Dict]:
    """Return one record per attempted test-framework execution.

    Each record: {cmd, output, exit_code} plus the classify_output flags.
    """
    records: List[Dict] = []

    # --- Pass 1: collect tool_use invocations + pending Claude Code results --
    pending_claude: Dict[str, Dict] = {}  # tool_use_id -> {cmd, exit_code=None}
    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)
            except Exception:
                continue

            t = item.get("type")

            # Codex: command_execution is self-contained (has output + exit_code).
            if t == "item.completed":
                inner = item.get("item", {}) or {}
                if inner.get("type") == "command_execution":
                    cmd = inner.get("command", "") or ""
                    if not is_test_exec_command(cmd):
                        continue
                    out = inner.get("aggregated_output", "") or ""
                    ec = inner.get("exit_code")
                    rec = {"cmd": cmd, "output": out, "exit_code": ec}
                    rec.update(classify_output(out, ec))
                    records.append(rec)

            # Claude Code: tool_use in assistant message, result in next user message.
            elif t == "assistant":
                for c in item.get("message", {}).get("content", []) or []:
                    if (
                        isinstance(c, dict)
                        and c.get("type") == "tool_use"
                        and c.get("name") == "Bash"
                    ):
                        cmd = (c.get("input") or {}).get("command", "") or ""
                        tid = c.get("id")
                        if tid and is_test_exec_command(cmd):
                            pending_claude[tid] = {"cmd": cmd}

            elif t == "user":
                for c in item.get("message", {}).get("content", []) or []:
                    if not isinstance(c, dict):
                        continue
                    if c.get("type") != "tool_result":
                        continue
                    tid = c.get("tool_use_id")
                    if tid not in pending_claude:
                        continue
                    out = _tool_result_text(c.get("content", ""))
                    cmd = pending_claude.pop(tid)["cmd"]
                    rec = {"cmd": cmd, "output": out, "exit_code": None}
                    rec.update(classify_output(out, None))
                    records.append(rec)

            # OpenCode: tool_use has state.output inline.
            elif t == "tool_use":
                part = item.get("part", {}) or {}
                if part.get("tool") != "bash":
                    continue
                state = part.get("state", {}) or {}
                if not isinstance(state, dict):
                    continue
                cmd = ((state.get("input") or {}).get("command") or "")
                if not is_test_exec_command(cmd):
                    continue
                out = state.get("output", "") or ""
                # OpenCode doesn't expose exit code; infer from text.
                rec = {"cmd": cmd, "output": out, "exit_code": None}
                rec.update(classify_output(out, None))
                records.append(rec)

    # Orphaned Claude Code tool_uses (no matching result) -> attempted but
    # unknown outcome. Count as attempted, nothing else.
    for tid, info in pending_claude.items():
        rec = {
            "cmd": info["cmd"],
            "output": "",
            "exit_code": None,
            "env_error": False,
            "completed": False,
            "actionable": False,
            "all_passed": False,
            "test_pass": False,
            "test_fail": False,
        }
        records.append(rec)

    return records


# --- Aggregation --------------------------------------------------------------

def aggregate(output_dir: Path) -> Dict:
    """Walk output/ and compute per-(dataset, agent, mode) compliance stats."""
    agg: Dict[Tuple[str, str, str], Dict] = defaultdict(
        lambda: {
            "instances": 0,
            "instances_with_exec": 0,
            "attempted": 0,
            "completed": 0,
            "env_error": 0,
            "actionable": 0,
            "all_passed": 0,
            "test_pass": 0,
            "test_fail": 0,
        }
    )

    for dataset_dir in sorted(output_dir.iterdir()):
        if not dataset_dir.is_dir() or dataset_dir.name not in DATASETS:
            continue
        for agent_dir in sorted(dataset_dir.iterdir()):
            if not agent_dir.is_dir() or agent_dir.name in EXCLUDED_AGENTS:
                continue
            for mode_dir in sorted(agent_dir.iterdir()):
                if not mode_dir.is_dir():
                    continue
                key = (dataset_dir.name, agent_dir.name, mode_dir.name)
                for inst_dir in sorted(mode_dir.iterdir()):
                    if not inst_dir.is_dir():
                        continue
                    trace = inst_dir / "trace.jsonl"
                    if not trace.exists():
                        continue
                    agg[key]["instances"] += 1
                    try:
                        recs = parse_trace(trace)
                    except Exception as e:
                        print(f"[warn] {trace}: {e}", file=sys.stderr)
                        continue
                    if recs:
                        agg[key]["instances_with_exec"] += 1
                    for r in recs:
                        agg[key]["attempted"] += 1
                        agg[key]["completed"] += int(r["completed"])
                        agg[key]["env_error"] += int(r["env_error"])
                        agg[key]["actionable"] += int(r["actionable"])
                        agg[key]["all_passed"] += int(r["all_passed"])
                        agg[key]["test_pass"] += int(r["test_pass"])
                        agg[key]["test_fail"] += int(r["test_fail"])
    return agg


# --- Reporting ----------------------------------------------------------------

AGENT_DISPLAY = {
    "claude_code": "Claude Code",
    "codex": "Codex",
    "opencode": "OpenCode+Qwen2.5-Coder",
}

MODE_DISPLAY = {
    "run_free": "Prohibited",
    "run_less_k1": "Quota-1",
    "run_less_k3": "Quota-3",
    "run_cost": "Budget-Guided",
    "run_full": "Unrestricted",
}


def render_markdown(agg: Dict) -> str:
    lines: List[str] = []
    lines.append("# Execution Compliance by Mode")
    lines.append("")
    lines.append(
        "For each (dataset, agent, mode) cell: **Attempted** = test-framework "
        "invocations launched by the agent (pytest / unittest / manage.py test / "
        "tox / nose / direct `.py` script); **Env-Error** = blocked by import / "
        "missing-module / dependency errors before reaching the test stage; "
        "**Completed** = reached the test stage (i.e. not blocked by env errors) "
        "and produced non-empty output; **Actionable** = produced a concrete "
        "pass/fail test signal the agent could use to guide the next edit "
        "(subset of Completed). Counts are totals across 100 instances; "
        "per-task averages are in parentheses."
    )
    lines.append("")

    for dataset in sorted(agg.keys() and {k[0] for k in agg.keys()}):
        ds_title = DATASETS.get(dataset, dataset)
        lines.append(f"## {ds_title}")
        lines.append("")
        lines.append(
            "| Agent | Mode | Instances (with exec) | Attempted | Env-Error | Completed | Actionable |"
        )
        lines.append(
            "|-------|------|----------------------:|----------:|----------:|----------:|-----------:|"
        )
        ds_keys = [k for k in agg.keys() if k[0] == dataset]
        ds_keys.sort(
            key=lambda k: (
                list(AGENT_DISPLAY.keys()).index(k[1])
                if k[1] in AGENT_DISPLAY
                else 99,
                MODE_ORDER.index(k[2]) if k[2] in MODE_ORDER else 99,
            )
        )
        for key in ds_keys:
            ds, agent, mode = key
            v = agg[key]
            n = v["instances"] or 1

            def fmt(total: int) -> str:
                return f"{total} ({total / n:.2f})"

            lines.append(
                "| {agent} | {mode} | {inst} ({we}) | {att} | {env} | {comp} | {act} |".format(
                    agent=AGENT_DISPLAY.get(agent, agent),
                    mode=MODE_DISPLAY.get(mode, mode),
                    inst=v["instances"],
                    we=v["instances_with_exec"],
                    att=fmt(v["attempted"]),
                    env=fmt(v["env_error"]),
                    comp=fmt(v["completed"]),
                    act=fmt(v["actionable"]),
                )
            )
        lines.append("")

    return "\n".join(lines)


def write_csv(agg: Dict, csv_path: Path) -> None:
    rows = []
    for key, v in agg.items():
        ds, agent, mode = key
        n = v["instances"] or 1
        rows.append(
            {
                "dataset": ds,
                "agent": agent,
                "mode": mode,
                "instances": v["instances"],
                "instances_with_exec": v["instances_with_exec"],
                "attempted": v["attempted"],
                "attempted_per_task": round(v["attempted"] / n, 3),
                "completed": v["completed"],
                "completed_per_task": round(v["completed"] / n, 3),
                "env_error": v["env_error"],
                "env_error_per_task": round(v["env_error"] / n, 3),
                "actionable": v["actionable"],
                "actionable_per_task": round(v["actionable"] / n, 3),
                "all_passed": v["all_passed"],
                "all_passed_per_task": round(v["all_passed"] / n, 3),
                "test_pass": v["test_pass"],
                "test_fail": v["test_fail"],
            }
        )
    rows.sort(
        key=lambda r: (
            r["dataset"],
            list(AGENT_DISPLAY.keys()).index(r["agent"])
            if r["agent"] in AGENT_DISPLAY
            else 99,
            MODE_ORDER.index(r["mode"]) if r["mode"] in MODE_ORDER else 99,
        )
    )
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    output_dir = PROJECT_ROOT / "output"
    agg = aggregate(output_dir)

    out_md = Path(__file__).parent / "compliance_table.md"
    out_csv = Path(__file__).parent / "compliance_table.csv"

    out_md.write_text(render_markdown(agg), encoding="utf-8")
    write_csv(agg, out_csv)

    print(f"wrote {out_md}")
    print(f"wrote {out_csv}")


if __name__ == "__main__":
    main()
