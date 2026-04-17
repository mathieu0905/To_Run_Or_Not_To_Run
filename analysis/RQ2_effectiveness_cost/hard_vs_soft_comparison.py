#!/usr/bin/env python3
"""Pair Claude Code Verified hard-Prohibited results against soft-Prohibited
and Unrestricted on the same 100 instances.

Loads resolved_ids from sb-cli reports and prints:
  - Resolve rates for all three modes
  - McNemar b/c counts for hard vs soft and hard vs Unrestricted
  - Instance-level pass/fail transitions
  - Attribution: how many soft-pass instances became hard-fail
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "sb-cli-reports"


def load_resolved(filename: str) -> set[str]:
    """Return the set of resolved instance_ids from a sb-cli report."""
    path = REPORTS_DIR / filename
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("resolved_ids", []))


def mcnemar_stats(a: set[str], b: set[str], n_total: int) -> dict:
    """Paired comparison: b_count = A-only wins, c_count = B-only wins."""
    b_only = a - b  # passes in A, fails in B → A wins
    c_only = b - a  # passes in B, fails in A → B wins
    return {
        "a_wins": len(b_only),
        "b_wins": len(c_only),
        "a_wins_ids": sorted(b_only),
        "b_wins_ids": sorted(c_only),
    }


def main() -> None:
    soft = load_resolved("swe-bench_verified__test__swebenchverified_claude_code_run_free.json")
    hard_v1 = load_resolved("Subset.swe_bench_verified__test__claude_code_verified_run_hard_free.json")
    hard = load_resolved("Subset.swe_bench_verified__test__claude_code_verified_run_hard_free_v2.json")
    full = load_resolved("swe-bench_verified__test__swebenchverified_claude_code_run_full.json")

    n = 100
    print(f"Resolve rates on same 100 Verified instances:")
    print(f"  soft-Prohibited:       {len(soft)}/{n} = {len(soft)/n*100:.1f}%")
    print(f"  hard-v1 (all Bash):    {len(hard_v1)}/{n} = {len(hard_v1)/n*100:.1f}%")
    print(f"  hard-v2 (exec-only):   {len(hard)}/{n} = {len(hard)/n*100:.1f}%")
    print(f"  Unrestricted:          {len(full)}/{n} = {len(full)/n*100:.1f}%")
    print()

    print("Paired comparisons:")
    for label, a, b in [
        ("hard-v2 vs soft", hard, soft),
        ("hard-v2 vs Unrestr.", hard, full),
        ("hard-v2 vs hard-v1", hard, hard_v1),
        ("hard-v1 vs soft", hard_v1, soft),
        ("soft vs Unrestr.", soft, full),
    ]:
        stats = mcnemar_stats(a, b, n)
        a_lbl, b_lbl = label.split(" vs ")
        gap = (len(a) - len(b)) / n * 100
        print(
            f"  {label:20s}: {a_lbl}-wins={stats['a_wins']}, "
            f"{b_lbl}-wins={stats['b_wins']}, gap={gap:+.1f}pp"
        )
    print()

    # Instance transitions: focus on soft→hard regressions (instances that
    # passed under soft-Prohibited but failed under hard-Prohibited).
    soft_only = soft - hard
    hard_only = hard - soft
    print(f"soft→hard regressions (pass → fail): {len(soft_only)} instances")
    for i in sorted(soft_only)[:15]:
        in_full = i in full
        print(f"  {i}  (Unrestricted resolves it: {in_full})")
    print(f"hard→soft gains (fail → pass): {len(hard_only)} instances")
    for i in sorted(hard_only)[:10]:
        print(f"  {i}")

    # How many of the soft→hard regressions are explained by Unrestricted
    # also resolving them? That is the portion of instances where execution
    # demonstrably helps beyond prompt-level reasoning.
    regression_with_exec_help = soft_only & full
    print()
    print(
        f"soft→hard regressions that Unrestricted also resolves: "
        f"{len(regression_with_exec_help)}/{len(soft_only)}"
    )
    print(
        "These instances plausibly benefit from even a tiny amount of "
        "execution (as happens under soft-Prohibited's leaked bash calls)."
    )


if __name__ == "__main__":
    main()
