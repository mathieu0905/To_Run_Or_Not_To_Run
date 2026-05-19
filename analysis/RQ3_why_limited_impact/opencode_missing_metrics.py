#!/usr/bin/env python3
"""Compute OpenCode-only numbers for three tables that the RQ3 analysis
originally only reported on Claude Code and Codex:

  * tab:single-edit (single-edit ratio per mode, post-exec modification ratio)
  * tab:validation-total (validation executions after first edit, by P->P / F->F)
  * tab:validation-ff (F->F cases where some agent test passed)

The full pipelines for Claude Code / Codex live in
analyze_single_edit_ratio_v5.py and analyze_verification_reproduction_v2.py
but they only walk the Claude / Codex trace formats. This script gives the
OpenCode numbers by walking the OpenCode `tool_use` events directly.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = PROJECT_ROOT / "output"
REPORTS = PROJECT_ROOT / "sb-cli-reports"

HIGH_COST = [
    "pytest", "python -m pytest", "python -m unittest",
    "manage.py test", "python manage.py test",
    "tox", "nose", "nosetests", "python tests/runtests.py",
]
PY_SCRIPT = re.compile(r"\bpython\s+[a-zA-Z_][\w/\-]*\.py\b")

ENV_ERROR = [
    re.compile(r"ModuleNotFoundError", re.I),
    re.compile(r"No module named", re.I),
    re.compile(r"ImportError:\s*cannot import", re.I),
]
PASS_SIG = [
    re.compile(r"\b\d+\s+passed\b", re.I),
    re.compile(r"^OK\b", re.M),
    re.compile(r"Ran\s+\d+\s+tests?\s+in", re.I),
]
FAIL_SIG = [
    re.compile(r"\b\d+\s+failed\b", re.I),
    re.compile(r"^FAILED\b", re.M),
    re.compile(r"AssertionError", re.I),
    re.compile(r"^FAIL:\s", re.M),
    re.compile(r"^ERROR:\s", re.M),
    re.compile(r"Traceback \(most recent call last\)", re.I),
]


def is_exec(cmd: str) -> bool:
    return bool(cmd) and (any(p in cmd for p in HIGH_COST) or bool(PY_SCRIPT.search(cmd)))


def classify(output: str) -> str:
    if not output:
        return "empty"
    if any(p.search(output) for p in ENV_ERROR):
        return "env_error"
    if any(p.search(output) for p in FAIL_SIG):
        return "test_fail"
    if any(p.search(output) for p in PASS_SIG):
        return "test_pass"
    return "other"


def is_code_file(fp: str) -> bool:
    if not fp or not fp.endswith(".py"):
        return False
    low = fp.lower()
    if "/testbed/" in low:
        tail = low.split("/testbed/", 1)[1].split("/")
        if len(tail) == 1:
            return False  # temp script
    return True


def parse_opencode(trace_path: Path) -> Dict:
    """Return a time-ordered list of (kind, detail) events.

    kind ∈ {'edit', 'exec'}. For edit: detail = file_path (only code files).
    For exec: detail = {'cmd': str, 'class': 'env_error'|'test_pass'|...}.
    """
    events: List[Tuple[str, Dict]] = []
    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)
            except Exception:
                continue
            if item.get("type") != "tool_use":
                continue
            part = item.get("part", {}) or {}
            tool = part.get("tool")
            state = part.get("state", {}) or {}
            if not isinstance(state, dict):
                continue
            inp = state.get("input") or {}
            if tool in ("edit", "write"):
                fp = inp.get("filePath") or inp.get("file_path") or ""
                if is_code_file(fp):
                    events.append(("edit", {"file": fp}))
            elif tool == "bash":
                cmd = inp.get("command", "") or ""
                if is_exec(cmd):
                    events.append(
                        ("exec", {
                            "cmd": cmd,
                            "class": classify(state.get("output", "") or ""),
                        })
                    )
    return events


def find_opencode_traces(mode_dir: str) -> List[Path]:
    out = []
    for ds in ("swebenchlite", "swebenchverified"):
        base = OUTPUT / ds / "opencode" / mode_dir
        if not base.exists():
            continue
        for inst_dir in base.iterdir():
            t = inst_dir / "trace.jsonl"
            if t.exists():
                out.append(t)
    return out


def load_resolved(filename: str) -> set[str]:
    p = REPORTS / filename
    if not p.exists():
        return set()
    try:
        return set(json.loads(p.read_text()).get("resolved_ids", []))
    except Exception:
        return set()


def outcome(inst_id: str, prohib: set, unres: set) -> str:
    in_p, in_u = inst_id in prohib, inst_id in unres
    if in_p and in_u:
        return "pp"
    if (not in_p) and (not in_u):
        return "ff"
    if in_p and not in_u:
        return "pf"
    return "fp"


def single_edit_stats(events: List[Tuple[str, Dict]]) -> Dict:
    """Only-one-edit: every code-file appears exactly once in the edit list."""
    file_counts: Dict[str, int] = defaultdict(int)
    for k, d in events:
        if k == "edit":
            file_counts[d["file"]] += 1
    if not file_counts:
        return {"no_edit": True, "only_one": False, "post_exec_mod": False}
    only_one = all(c == 1 for c in file_counts.values())

    exec_positions = [i for i, (k, _) in enumerate(events) if k == "exec"]
    if exec_positions:
        first_exec = exec_positions[0]
        post_mod = any(k == "edit" and i > first_exec for i, (k, _) in enumerate(events))
    else:
        post_mod = False
    return {"no_edit": False, "only_one": only_one, "post_exec_mod": post_mod}


def validation_stats(events: List[Tuple[str, Dict]]) -> Dict:
    """Validation = test executions after the first code edit."""
    edit_positions = [i for i, (k, _) in enumerate(events) if k == "edit"]
    if not edit_positions:
        return {"n_valid": 0, "pass": 0, "fail": 0, "env": 0, "has_any_pass": False}
    first_edit = edit_positions[0]
    classes = [d["class"] for i, (k, d) in enumerate(events) if k == "exec" and i > first_edit]
    return {
        "n_valid": len(classes),
        "pass": sum(1 for c in classes if c == "test_pass"),
        "fail": sum(1 for c in classes if c == "test_fail"),
        "env": sum(1 for c in classes if c == "env_error"),
        "has_any_pass": any(c == "test_pass" for c in classes),
    }


def main() -> None:
    prohib_lite = load_resolved("swe-bench_lite__test__swebenchlite_opencode_run_free.json")
    prohib_ver = load_resolved("swe-bench_verified__test__swebenchverified_opencode_run_free.json")
    unres_lite = load_resolved("swe-bench_lite__test__swebenchlite_opencode_run_full.json")
    unres_ver = load_resolved("swe-bench_verified__test__swebenchverified_opencode_run_full.json")

    # Fallback sb-cli filenames for opencode (they use _q25c naming).
    if not prohib_lite:
        for name in [
            "swe-bench_lite__test__opencode_q25c_lite_run_free_fixed.json",
            "swe-bench_lite__test__opencode_q25c_lite_runfree_final.json",
        ]:
            prohib_lite = load_resolved(name)
            if prohib_lite:
                break
    if not unres_lite:
        unres_lite = load_resolved("swe-bench_lite__test__opencode_q25c_lite_run_full_final.json") \
            or load_resolved("swe-bench_lite__test__opencode_q25c_lite_runfull_final.json")
    if not prohib_ver:
        prohib_ver = load_resolved("swe-bench_verified__test__opencode_q25c_verified_run_free_fixed.json")
    if not unres_ver:
        unres_ver = load_resolved("swe-bench_verified__test__opencode_q25c_verified_run_full_final.json") \
            or load_resolved("swe-bench_verified__test__opencode_q25c_verified_runfull_final.json")

    resolved = {
        ("swebenchlite", "prohibited"): prohib_lite,
        ("swebenchlite", "unrestricted"): unres_lite,
        ("swebenchverified", "prohibited"): prohib_ver,
        ("swebenchverified", "unrestricted"): unres_ver,
    }
    print(f"Resolved set sizes (lite/ver x prohib/unres): "
          f"{len(prohib_lite)}/{len(prohib_ver)}/{len(unres_lite)}/{len(unres_ver)}")

    # --- Single-edit (two modes) and post-exec modification (unres only) ---
    per_inst_single_edit: Dict[Tuple[str, str, str], Dict] = {}  # (dataset, mode, inst) -> stats
    per_inst_validation: Dict[Tuple[str, str, str], Dict] = {}
    per_inst_outcome: Dict[Tuple[str, str], str] = {}            # (dataset, inst) -> pp/ff/pf/fp

    for mode_dir, mode_label in (("run_free", "prohibited"), ("run_full", "unrestricted")):
        for trace in find_opencode_traces(mode_dir):
            inst = trace.parent.name
            dataset = trace.parent.parent.parent.parent.name  # output/<ds>/opencode/<mode>/<inst>/trace.jsonl
            events = parse_opencode(trace)
            per_inst_single_edit[(dataset, mode_label, inst)] = single_edit_stats(events)
            if mode_label == "unrestricted":
                per_inst_validation[(dataset, "unrestricted", inst)] = validation_stats(events)
                per_inst_outcome[(dataset, inst)] = outcome(
                    inst,
                    resolved[(dataset, "prohibited")],
                    resolved[(dataset, "unrestricted")],
                )

    # --- Aggregate single-edit ratio & post-exec modification ---
    agg_se: Dict[Tuple[str, str], Dict] = defaultdict(lambda: {"n": 0, "one": 0, "post_mod": 0})
    for (dataset, mode, _), stats in per_inst_single_edit.items():
        if stats.get("no_edit"):
            continue
        agg_se[(dataset, mode)]["n"] += 1
        if stats["only_one"]:
            agg_se[(dataset, mode)]["one"] += 1
        if stats.get("post_exec_mod"):
            agg_se[(dataset, mode)]["post_mod"] += 1

    # --- Aggregate validation-total (per outcome) and validation-ff ---
    agg_vt: Dict[Tuple[str, str], Dict] = defaultdict(lambda: {"pass": 0, "fail": 0, "env": 0, "n_valid": 0, "n_inst": 0})
    agg_ff_any_pass = {"ds_lite": {"inst_with_val": 0, "any_pass": 0},
                       "ds_ver": {"inst_with_val": 0, "any_pass": 0}}

    for (dataset, mode, inst), val in per_inst_validation.items():
        oc = per_inst_outcome.get((dataset, inst))
        if oc not in ("pp", "ff"):
            continue
        key = (dataset, oc)
        agg_vt[key]["n_inst"] += 1
        agg_vt[key]["n_valid"] += val["n_valid"]
        agg_vt[key]["pass"] += val["pass"]
        agg_vt[key]["fail"] += val["fail"]
        agg_vt[key]["env"] += val["env"]
        if oc == "ff":
            bucket = "ds_lite" if dataset == "swebenchlite" else "ds_ver"
            if val["n_valid"] > 0:
                agg_ff_any_pass[bucket]["inst_with_val"] += 1
                if val["has_any_pass"]:
                    agg_ff_any_pass[bucket]["any_pass"] += 1

    # --- Emit results ---
    print("\n=== tab:single-edit — (a) Single-edit ratio ===")
    for mode in ("prohibited", "unrestricted"):
        for dataset in ("swebenchlite", "swebenchverified"):
            s = agg_se[(dataset, mode)]
            pct = (s["one"] / s["n"] * 100) if s["n"] else 0.0
            print(f"  {dataset:>20s} / {mode:>12s}: {s['one']}/{s['n']} = {pct:.1f}%")
    # Combined across Lite + Verified (mode-level):
    for mode in ("prohibited", "unrestricted"):
        total_n = sum(agg_se[(ds, mode)]["n"] for ds in ("swebenchlite", "swebenchverified"))
        total_one = sum(agg_se[(ds, mode)]["one"] for ds in ("swebenchlite", "swebenchverified"))
        pct = (total_one / total_n * 100) if total_n else 0.0
        print(f"  COMBINED / {mode:>12s}: {total_one}/{total_n} = {pct:.1f}%")

    print("\n=== tab:single-edit — (b) Post-exec modification ratio ===")
    for mode in ("prohibited", "unrestricted"):
        for dataset in ("swebenchlite", "swebenchverified"):
            s = agg_se[(dataset, mode)]
            pct = (s["post_mod"] / s["n"] * 100) if s["n"] else 0.0
            print(f"  {dataset:>20s} / {mode:>12s}: {s['post_mod']}/{s['n']} = {pct:.1f}%")
        total_n = sum(agg_se[(ds, mode)]["n"] for ds in ("swebenchlite", "swebenchverified"))
        total_pm = sum(agg_se[(ds, mode)]["post_mod"] for ds in ("swebenchlite", "swebenchverified"))
        print(f"  COMBINED / {mode:>12s}: {total_pm}/{total_n} = "
              f"{total_pm / total_n * 100 if total_n else 0.0:.1f}%")

    print("\n=== tab:validation-total — OpenCode, Unrestricted ===")
    for oc_label, oc in [("Pass->Pass", "pp"), ("Fail->Fail", "ff")]:
        # Sum across Lite + Verified
        total_valid = sum(agg_vt[(ds, oc)]["n_valid"] for ds in ("swebenchlite", "swebenchverified"))
        total_pass = sum(agg_vt[(ds, oc)]["pass"] for ds in ("swebenchlite", "swebenchverified"))
        total_fail = sum(agg_vt[(ds, oc)]["fail"] for ds in ("swebenchlite", "swebenchverified"))
        total_env = sum(agg_vt[(ds, oc)]["env"] for ds in ("swebenchlite", "swebenchverified"))
        total_inst = sum(agg_vt[(ds, oc)]["n_inst"] for ds in ("swebenchlite", "swebenchverified"))
        if total_valid == 0:
            print(f"  {oc_label}: n_inst={total_inst}, no validation executions")
            continue
        print(f"  {oc_label}: n_inst={total_inst}, validations={total_valid}, "
              f"pass={total_pass} ({total_pass / total_valid * 100:.1f}%), "
              f"fail={total_fail} ({total_fail / total_valid * 100:.1f}%), "
              f"env={total_env} ({total_env / total_valid * 100:.1f}%)")

    print("\n=== tab:validation-ff — Fail->Fail, any agent test passed ===")
    total_with_val = sum(b["inst_with_val"] for b in agg_ff_any_pass.values())
    total_ff_inst = sum(agg_vt[(ds, "ff")]["n_inst"] for ds in ("swebenchlite", "swebenchverified"))
    total_any_pass = sum(b["any_pass"] for b in agg_ff_any_pass.values())
    print(f"  OpenCode F->F: inst_with_validation={total_with_val}/{total_ff_inst}, "
          f"any_test_passed={total_any_pass} "
          f"({total_any_pass / total_with_val * 100 if total_with_val else 0.0:.1f}% of those with val.)")


if __name__ == "__main__":
    main()
