#!/usr/bin/env python3
"""OpenCode reproduction-execution analysis for Pass->Pass cases.

For each PP instance (OpenCode run_free AND run_full both resolved), parse
the run_full trace and:
 1. Identify reproduction executions: bash tool calls matching pytest/
    unittest/tox/python-script patterns that occur BEFORE the first `edit`
    tool call on a non-test source file.
 2. Classify each execution's output as `actionable` (contains file path,
    stack trace, or line number) or `non-actionable` (env error, empty,
    uninformative).

Output fields mirror the paper's tab:reproduction-stats part (a).
Also computes part (b): Hit-rate comparison on actionable instances
between Prohibited and Unrestricted.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.common.statistical_analysis import load_instance_level_results  # noqa: E402
from analysis.RQ3_why_limited_impact.rq3_comprehensive_analysis import (  # noqa: E402
    extract_files_from_patch,
    load_ground_truth_files,
    is_test_file,
)


HIGH_COST_PATTERNS = [
    "pytest", "python -m pytest", "python -m unittest",
    "manage.py test", "python manage.py test",
    "tox", "nose", "nosetests", "python -m django test",
    "python tests/runtests.py",
]
PYTHON_SCRIPT_RE = re.compile(r"\bpython3?\s+[a-zA-Z_./][\w/\-]*\.py\b")

# "Actionable" signals: file path with line number, traceback keywords
LINE_NUM_RE = re.compile(r"\b(?:line|\.py:)\s*\d+", re.IGNORECASE)
TRACE_KEYWORDS = ["Traceback", "File \"", "Error:", "AssertionError"]
ENV_ERROR_PATTERNS = [
    "ModuleNotFoundError",
    "No module named",
    "command not found",
    "permission denied",
    "OperationalError",
    "ImportError",
]


def is_test_cmd(cmd: str) -> bool:
    if any(p in cmd for p in HIGH_COST_PATTERNS):
        return True
    if PYTHON_SCRIPT_RE.search(cmd):
        return True
    return False


def classify_output(output: str) -> str:
    """Return 'actionable', 'env_error', or 'uninformative'."""
    if not output:
        return "uninformative"
    if any(pat in output for pat in ENV_ERROR_PATTERNS):
        return "env_error"
    if LINE_NUM_RE.search(output) or any(k in output for k in TRACE_KEYWORDS):
        return "actionable"
    return "uninformative"


def parse_opencode_trace(trace_path: Path):
    """Yield (event_kind, tool, cmd, output) tuples in order."""
    if not trace_path.exists():
        return
    with open(trace_path) as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") != "tool_use":
                continue
            part = d.get("part", {}) or {}
            tool = part.get("tool", "?")
            state = part.get("state", {}) or {}
            inp = state.get("input", {}) or {}
            output = state.get("output", "")
            if tool == "bash":
                cmd = inp.get("command", "")
                yield ("bash", tool, cmd, output if isinstance(output, str) else "")
            elif tool == "edit":
                file_path = inp.get("filePath", "")
                yield ("edit", tool, file_path, output if isinstance(output, str) else "")


def reproduction_stats_for_instance(instance_dir: Path):
    """Return (n_repro_execs, n_actionable, n_nonactionable).

    Reproduction execs = test-style bash commands before the first
    non-test-file edit.
    """
    trace = instance_dir / "trace.jsonl"
    repro = []  # list of (cmd, output)
    saw_source_edit = False
    for kind, tool, cmd_or_path, output in parse_opencode_trace(trace):
        if kind == "edit":
            if not is_test_file(cmd_or_path):
                saw_source_edit = True
                break
        elif kind == "bash" and not saw_source_edit:
            if is_test_cmd(cmd_or_path):
                repro.append((cmd_or_path, output))

    n_act = 0
    n_non = 0
    for _, out in repro:
        if classify_output(out) == "actionable":
            n_act += 1
        else:
            n_non += 1
    return len(repro), n_act, n_non, repro


def patch_files(dataset: str, mode: str, instance: str) -> set:
    p = PROJECT_ROOT / "output" / dataset / "opencode" / mode / instance / "patch.diff"
    if not p.exists() or p.stat().st_size == 0:
        return set()
    try:
        return extract_files_from_patch(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return set()


def main():
    inst = load_instance_level_results()

    pp_ids = {}  # dataset -> sorted list
    for dataset in ["swebenchlite", "swebenchverified"]:
        oc = inst.get(dataset, {}).get("opencode", {})
        prohib = set(oc.get("run_free", {}).get("resolved_ids", set()))
        unrestr = set(oc.get("run_full", {}).get("resolved_ids", set()))
        pp_ids[dataset] = sorted(prohib & unrestr)

    total_pp = sum(len(v) for v in pp_ids.values())
    inst_with_repro = 0
    total_execs = 0
    total_actionable = 0
    total_non = 0
    actionable_instances = []  # instances where at least one execution was actionable

    for dataset, ids in pp_ids.items():
        for iid in ids:
            inst_dir = PROJECT_ROOT / "output" / dataset / "opencode" / "run_full" / iid
            n, n_act, n_non, repro = reproduction_stats_for_instance(inst_dir)
            if n > 0:
                inst_with_repro += 1
                total_execs += n
                total_actionable += n_act
                total_non += n_non
                if n_act > 0:
                    actionable_instances.append((dataset, iid))

    # Part (b): Hit rate for actionable instances, comparing run_free and run_full
    hit_prohib = 0
    hit_unrestr = 0
    n_act_inst = len(actionable_instances)
    for dataset, iid in actionable_instances:
        gt = load_ground_truth_files(dataset, iid)
        if not gt:
            continue
        f_unrestr = patch_files(dataset, "run_full", iid)
        f_prohib = patch_files(dataset, "run_free", iid)
        if f_unrestr & gt:
            hit_unrestr += 1
        if f_prohib & gt:
            hit_prohib += 1

    lines = []
    lines.append("# OpenCode reproduction-execution analysis (Pass->Pass, Unrestricted)")
    lines.append("")
    lines.append(f"Total P->P instances for OpenCode: {total_pp}")
    lines.append("")
    lines.append("## Part (a) — reproduction execution outcomes")
    lines.append("")
    lines.append(f"- Instances with reproduction: {inst_with_repro}/{total_pp} ({100*inst_with_repro/max(total_pp,1):.1f}%)")
    lines.append(f"- Total reproduction executions: {total_execs}")
    if total_execs > 0:
        lines.append(f"- Actionable: {total_actionable} ({100*total_actionable/total_execs:.1f}%)")
        lines.append(f"- Non-actionable: {total_non} ({100*total_non/total_execs:.1f}%)")
    lines.append("")
    lines.append("## Part (b) — localization accuracy on actionable instances")
    lines.append("")
    lines.append(f"Actionable instances: n={n_act_inst}")
    if n_act_inst > 0:
        lines.append(f"- Prohibited Hit: {100*hit_prohib/n_act_inst:.1f}% ({hit_prohib}/{n_act_inst})")
        lines.append(f"- Unrestricted Hit: {100*hit_unrestr/n_act_inst:.1f}% ({hit_unrestr}/{n_act_inst})")
        delta = (hit_unrestr - hit_prohib) * 100 / n_act_inst
        lines.append(f"- Δ = {delta:+.1f}pp")
    lines.append("")

    out = Path(__file__).parent / "opencode_reproduction.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
