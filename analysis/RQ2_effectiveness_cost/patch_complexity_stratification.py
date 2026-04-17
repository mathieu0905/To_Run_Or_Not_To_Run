#!/usr/bin/env python3
"""Stratify Prohibited vs. Unrestricted resolve rates by gold-patch complexity.

Reviewer B asked whether the helpfulness of execution feedback correlates
with bug complexity (multi-file edits vs. single-line fixes). We answer by
bucketing each instance by three measures of its ground-truth patch:

  * files touched
  * hunk count (@@ markers)
  * total added+removed lines

For each bucket we report resolve rates under Prohibited and Unrestricted
across the three agents × two benchmarks.

Output: patch_complexity.md next to this script.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.data_loader import PROJECT_ROOT

REPORTS_DIR = PROJECT_ROOT / "sb-cli-reports"

AGENTS = ["claude_code", "codex", "opencode"]
AGENT_DISPLAY = {
    "claude_code": "Claude Code",
    "codex": "Codex",
    "opencode": "OpenCode",
}
DATASETS = [
    ("swe-bench_lite", "princeton-nlp/SWE-bench_Lite", "Lite"),
    ("swe-bench_verified", "princeton-nlp/SWE-bench_Verified", "Verified"),
]


def parse_patch(patch: str) -> Dict[str, int]:
    """Count files, hunks, added+removed lines from a unified diff."""
    if not patch:
        return {"files": 0, "hunks": 0, "delta_lines": 0}
    files = len(re.findall(r"^diff --git ", patch, flags=re.M))
    hunks = len(re.findall(r"^@@ ", patch, flags=re.M))
    delta = 0
    for line in patch.splitlines():
        if line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            delta += 1
    return {"files": files, "hunks": hunks, "delta_lines": delta}


def file_bucket(n: int) -> str:
    if n <= 1:
        return "single-file"
    if n <= 2:
        return "2-file"
    return "multi-file ($\\geq 3$)"


def hunk_bucket(n: int) -> str:
    if n <= 1:
        return "1 hunk"
    if n <= 3:
        return "2--3 hunks"
    return "$\\geq 4$ hunks"


def line_bucket(n: int) -> str:
    if n <= 5:
        return "small ($\\leq 5$)"
    if n <= 20:
        return "medium (6--20)"
    return "large ($> 20$)"


def load_resolved(filename: str) -> set[str]:
    path = REPORTS_DIR / filename
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return set(data.get("resolved_ids", []))


def find_report(dataset_sb: str, agent: str, mode: str) -> str | None:
    """sb-cli reports filenames vary; pick the highest-priority match."""
    def priority(name: str) -> int:
        low = name.lower()
        if "_fixed" in low:
            return 100
        if "_final" in low:
            return 50
        if "_v2" in low:
            return 40
        if "_v1" in low:
            return 10
        return 20

    # Normalise for opencode mixed naming.
    suffix = mode.replace("run_less_k1", "runlessk1").replace("run_less_k3", "runlessk3") \
                 .replace("run_free", "runfree").replace("run_full", "runfull") \
                 .replace("run_cost", "runcost")

    candidates = []
    for path in REPORTS_DIR.glob(f"*{dataset_sb}*.json"):
        name = path.stem
        if agent not in name.replace("opencode_q25c", "opencode"):
            continue
        if mode in name or suffix in name:
            candidates.append((priority(name), path.name))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def main() -> None:
    from datasets import load_dataset

    # Load gold patches.
    patch_features: Dict[Tuple[str, str], Dict] = {}
    for ds_sb, ds_hf, _ in DATASETS:
        ds = load_dataset(ds_hf, split="test")
        count = 0
        for item in ds:
            patch_features[(ds_sb, item["instance_id"])] = parse_patch(item["patch"])
            count += 1
            if count >= 120:  # we only run 100/bench, so stop early
                break

    # Load resolved sets per (agent, dataset, mode).
    resolved: Dict[Tuple[str, str, str], set] = {}
    for ds_sb, _, _ in DATASETS:
        for agent in AGENTS:
            for mode in ("run_free", "run_full"):
                fn = find_report(ds_sb, agent, mode)
                resolved[(agent, ds_sb, mode)] = load_resolved(fn) if fn else set()

    # Load instance lists we actually evaluated.
    # Use the sb-cli report itself — its completed_ids = the 100 we submitted.
    cohort: Dict[Tuple[str, str], set] = {}
    for ds_sb, _, _ in DATASETS:
        for agent in AGENTS:
            fn = find_report(ds_sb, agent, "run_free")
            if not fn:
                cohort[(agent, ds_sb)] = set()
                continue
            data = json.loads((REPORTS_DIR / fn).read_text(encoding="utf-8"))
            ids = set(data.get("completed_ids") or data.get("submitted_ids") or [])
            cohort[(agent, ds_sb)] = ids

    # Bucket and tabulate.
    buckets = {
        "files": file_bucket,
        "hunks": hunk_bucket,
        "delta_lines": line_bucket,
    }

    out: List[str] = []
    out.append("# Patch Complexity Stratification")
    out.append("")
    out.append(
        "For each (agent, benchmark) cell we group the 100 instances by "
        "ground-truth patch complexity (files touched / hunk count / total "
        "added+removed lines) and report resolve rate under Prohibited and "
        "Unrestricted plus the difference. Cells with $N < 5$ are noisy and "
        "flagged."
    )
    out.append("")

    for feature_name, bucket_fn in buckets.items():
        out.append(f"## Stratified by {feature_name}")
        out.append("")
        out.append(
            "| Benchmark | Agent | Bucket | $N$ | Prohibited | Unrestricted | Gap |"
        )
        out.append(
            "|-----------|-------|--------|----:|-----------:|-------------:|----:|"
        )
        for ds_sb, _, ds_label in DATASETS:
            for agent in AGENTS:
                # Group instance_ids by bucket.
                by_bucket: Dict[str, List[str]] = defaultdict(list)
                for inst in cohort[(agent, ds_sb)]:
                    feats = patch_features.get((ds_sb, inst))
                    if not feats:
                        continue
                    by_bucket[bucket_fn(feats[feature_name])].append(inst)

                # Sort buckets with a natural order. For files/hunks/lines we
                # want small→large.
                bucket_keys = sorted(by_bucket.keys(), key=lambda k: (
                    0 if "single" in k or "1 hunk" in k or "small" in k else
                    1 if "2-file" in k or "2--3" in k or "medium" in k else 2
                ))
                for bkey in bucket_keys:
                    instances = by_bucket[bkey]
                    n = len(instances)
                    if n == 0:
                        continue
                    free_resolved = sum(
                        1 for i in instances if i in resolved[(agent, ds_sb, "run_free")]
                    )
                    full_resolved = sum(
                        1 for i in instances if i in resolved[(agent, ds_sb, "run_full")]
                    )
                    gap = (free_resolved - full_resolved) / n * 100.0
                    flag = " $\\star$" if n < 5 else ""
                    out.append(
                        f"| {ds_label} | {AGENT_DISPLAY[agent]} | {bkey} | "
                        f"{n}{flag} | {free_resolved}/{n} ({free_resolved/n*100:.1f}\\%) | "
                        f"{full_resolved}/{n} ({full_resolved/n*100:.1f}\\%) | "
                        f"{gap:+.1f} |"
                    )
        out.append("")

    here = Path(__file__).parent
    (here / "patch_complexity.md").write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {here / 'patch_complexity.md'}")


if __name__ == "__main__":
    main()
