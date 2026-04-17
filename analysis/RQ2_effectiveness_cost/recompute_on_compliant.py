#!/usr/bin/env python3
"""Recompute Prohibited vs. Unrestricted resolve rates on compliant subsets.

Reviewer C asked whether the main result holds when restricted to runs that
actually complied with the execution protocol. We compute two subsets per
(dataset, agent):

  * env-clean: instances that never hit an environment error in ANY of the
    five execution modes. These are instances where the test environment is
    properly configured, so Prohibited vs. Unrestricted differences cannot
    be attributed to env-error noise.
  * prohibit-strict: instances where the agent produced zero actionable
    executions in Prohibited mode. This is the subset that strictly obeyed
    the prompt-level restriction, per the intention-to-treat robustness
    check promised in the rebuttal.

For each subset we report the Prohibited/Unrestricted resolve rates pulled
from sb-cli reports, restricted to instances in the subset, and the paired
difference.

Output: compliant_subset.md + compliant_subset.csv next to this script.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.data_loader import (
    DATASETS,
    EXCLUDED_AGENTS,
    PROJECT_ROOT,
    load_pass_rates,
)

# Re-use the parser and classifier from compute_compliance.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compute_compliance import parse_trace  # noqa: E402

MODES = ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"]
HARD_MODES = ["run_hard_free"]
ALL_MODES = MODES + HARD_MODES


def per_instance_flags(output_dir: Path) -> Dict[Tuple[str, str, str], Dict]:
    """Return {(dataset, agent, instance): {mode: {env_error_n, actionable_n}}}"""
    flags: Dict[Tuple[str, str, str], Dict] = defaultdict(lambda: defaultdict(dict))
    for dataset_dir in output_dir.iterdir():
        if not dataset_dir.is_dir() or dataset_dir.name not in DATASETS:
            continue
        for agent_dir in dataset_dir.iterdir():
            if not agent_dir.is_dir() or agent_dir.name in EXCLUDED_AGENTS:
                continue
            for mode_dir in agent_dir.iterdir():
                if not mode_dir.is_dir() or mode_dir.name not in ALL_MODES:
                    continue
                for inst_dir in mode_dir.iterdir():
                    if not inst_dir.is_dir():
                        continue
                    trace = inst_dir / "trace.jsonl"
                    if not trace.exists():
                        continue
                    try:
                        recs = parse_trace(trace)
                    except Exception:
                        continue
                    env_error_n = sum(int(r["env_error"]) for r in recs)
                    actionable_n = sum(int(r["actionable"]) for r in recs)
                    attempted_n = len(recs)
                    key = (dataset_dir.name, agent_dir.name, inst_dir.name)
                    flags[key][mode_dir.name] = {
                        "env_error": env_error_n,
                        "actionable": actionable_n,
                        "attempted": attempted_n,
                    }
    return flags


def load_instance_resolutions(reports_dir: Path) -> Dict[Tuple[str, str, str, str], bool]:
    """Load instance-level pass/fail for each (dataset, agent, mode, instance).

    Returns {(dataset, agent, mode, instance_id): resolved_bool}. Missing =
    not resolved (empty patch or not submitted).
    """
    resolutions: Dict[Tuple[str, str, str, str], bool] = {}
    if not reports_dir.exists():
        return resolutions

    # Priority: _fixed > _final > _v2 > _snap > plain > _v1 (mirrors load_pass_rates).
    def prio(fname: str) -> int:
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
        return 20

    candidates = defaultdict(list)
    for report_file in reports_dir.glob("*.json"):
        filename = report_file.stem
        if "lite" in filename.lower():
            dataset = "swebenchlite"
        elif "verified" in filename.lower():
            dataset = "swebenchverified"
        else:
            continue

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
        for mode in sorted(ALL_MODES, key=len, reverse=True):
            if mode in norm:
                matched_mode = mode
                break
        if matched_mode is None:
            continue

        candidates[(dataset, matched_agent, matched_mode)].append((prio(filename), report_file))

    for key, cands in candidates.items():
        cands.sort(key=lambda x: x[0], reverse=True)
        _, best = cands[0]
        try:
            report = json.loads(best.read_text(encoding="utf-8"))
        except Exception:
            continue
        resolved_ids = set(report.get("resolved_ids", []) or [])
        for inst_id in resolved_ids:
            resolutions[(*key, inst_id)] = True
        # Mark all completed_ids / unresolved_ids as not-resolved so we can
        # distinguish "submitted-and-failed" from "not-submitted" downstream.
        all_submitted = set(report.get("submitted_ids", []) or []) | resolved_ids | set(
            report.get("completed_ids", []) or []
        )
        for inst_id in all_submitted - resolved_ids:
            resolutions.setdefault((*key, inst_id), False)

    return resolutions


def build_subsets(flags: Dict, N_PER_CELL: int = 100) -> Dict:
    """Compute the two compliant subsets per (dataset, agent)."""
    subsets: Dict[Tuple[str, str], Dict[str, Set[str]]] = defaultdict(
        lambda: {"env_clean": set(), "prohibit_strict": set(), "all": set()}
    )

    # Group instances by (dataset, agent)
    by_da: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
    for (ds, agent, inst), _ in flags.items():
        by_da[(ds, agent)].add(inst)

    for (ds, agent), instances in by_da.items():
        for inst in instances:
            per_mode = flags[(ds, agent, inst)]
            # Only consider instance if we have data for all five modes.
            if any(m not in per_mode for m in MODES):
                continue
            subsets[(ds, agent)]["all"].add(inst)
            if all(per_mode[m]["env_error"] == 0 for m in MODES):
                subsets[(ds, agent)]["env_clean"].add(inst)
            if per_mode["run_free"]["attempted"] == 0:
                subsets[(ds, agent)]["prohibit_strict"].add(inst)
    return subsets


def compute_rates(
    subsets: Dict,
    resolutions: Dict,
) -> Dict:
    """For each (dataset, agent, subset), compute Prohibited / Unrestricted resolve rates."""
    rows = []
    for (ds, agent), subs in subsets.items():
        for subset_name, inst_set in subs.items():
            n = len(inst_set)
            if n == 0:
                continue
            resolved_free = sum(
                1 for inst in inst_set
                if resolutions.get((ds, agent, "run_free", inst), False)
            )
            resolved_full = sum(
                1 for inst in inst_set
                if resolutions.get((ds, agent, "run_full", inst), False)
            )
            rows.append(
                {
                    "dataset": ds,
                    "agent": agent,
                    "subset": subset_name,
                    "n": n,
                    "prohibited_resolved": resolved_free,
                    "prohibited_rate": resolved_free / n,
                    "unrestricted_resolved": resolved_full,
                    "unrestricted_rate": resolved_full / n,
                    "gap_pp": (resolved_free - resolved_full) / n * 100.0,
                }
            )
    return rows


AGENT_DISPLAY = {
    "claude_code": "Claude Code",
    "codex": "Codex",
    "opencode": "OpenCode+Qwen2.5-Coder",
}
DS_DISPLAY = {"swebenchlite": "Lite", "swebenchverified": "Verified"}
SUBSET_DISPLAY = {
    "all": "All (100)",
    "env_clean": "Env-clean",
    "prohibit_strict": "Prohibit-strict",
}


def render_md(rows) -> str:
    lines = [
        "# Prohibited vs. Unrestricted Resolve Rates on Compliant Subsets",
        "",
        "For each (dataset, agent) pair we compute three subsets and report the "
        "Prohibited and Unrestricted resolve rates on each. \"All\" is the full 100 "
        "instances. \"Env-clean\" keeps only instances whose executions never hit "
        "an environment error in any of the five modes---so Prohibited vs. "
        "Unrestricted comparisons on this subset are not affected by env-error "
        "noise. \"Prohibit-strict\" keeps only instances where the agent produced "
        "zero actionable executions in Prohibited mode, i.e. the subset that "
        "strictly obeyed the prompt-level restriction.",
        "",
        "| Dataset | Agent | Subset | N | Prohibited | Unrestricted | Gap (pp) |",
        "|---------|-------|--------|--:|-----------:|-------------:|---------:|",
    ]
    rows_sorted = sorted(
        rows,
        key=lambda r: (
            r["dataset"],
            list(AGENT_DISPLAY).index(r["agent"]) if r["agent"] in AGENT_DISPLAY else 99,
            ["all", "env_clean", "prohibit_strict"].index(r["subset"]),
        ),
    )
    for r in rows_sorted:
        lines.append(
            f"| {DS_DISPLAY.get(r['dataset'], r['dataset'])} "
            f"| {AGENT_DISPLAY.get(r['agent'], r['agent'])} "
            f"| {SUBSET_DISPLAY.get(r['subset'], r['subset'])} "
            f"| {r['n']} "
            f"| {r['prohibited_resolved']}/{r['n']} ({r['prohibited_rate']*100:.1f}\\%) "
            f"| {r['unrestricted_resolved']}/{r['n']} ({r['unrestricted_rate']*100:.1f}\\%) "
            f"| {r['gap_pp']:+.1f} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    output_dir = PROJECT_ROOT / "output"
    reports_dir = PROJECT_ROOT / "sb-cli-reports"

    flags = per_instance_flags(output_dir)
    subsets = build_subsets(flags)
    resolutions = load_instance_resolutions(reports_dir)
    rows = compute_rates(subsets, resolutions)

    here = Path(__file__).parent
    (here / "compliant_subset.md").write_text(render_md(rows), encoding="utf-8")
    with open(here / "compliant_subset.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {here / 'compliant_subset.md'}")
    print(f"wrote {here / 'compliant_subset.csv'}")


if __name__ == "__main__":
    main()
