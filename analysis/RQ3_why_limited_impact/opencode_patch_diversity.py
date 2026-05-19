#!/usr/bin/env python3
"""OpenCode patch similarity: Prohibited vs Unrestricted, instance-matched.

Matches the paper's tab:patch-diversity metrics:
- Identical: pct of instance pairs where normalised patches are 100% equal
- Same file, different code: pct where same files edited but <10% code overlap
- Average similarity: mean SequenceMatcher ratio
"""
from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent


def normalize_patch(text: str) -> str:
    """Strip git metadata and collapse whitespace for fair comparison."""
    out = []
    for line in text.split("\n"):
        if line.startswith("diff --git"):
            continue
        if line.startswith("index "):
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        if line.startswith("@@ "):
            continue
        out.append(line.strip())
    return "\n".join(l for l in out if l)


def extract_files(text: str) -> set:
    files = set()
    for line in text.split("\n"):
        m = re.match(r"diff --git a/(.+?) b/", line)
        if m:
            files.add(m.group(1))
    return files


def load_patch(dataset: str, mode: str, instance: str) -> str:
    p = PROJECT_ROOT / "output" / dataset / "opencode" / mode / instance / "patch.diff"
    if not p.exists() or p.stat().st_size == 0:
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def main():
    identical = 0
    same_file_diff_code = 0
    ratios = []
    total_pairs = 0

    for dataset in ["swebenchlite", "swebenchverified"]:
        md = PROJECT_ROOT / "output" / dataset / "opencode" / "run_free"
        if not md.is_dir():
            continue
        for inst_dir in sorted(md.iterdir()):
            if not inst_dir.is_dir():
                continue
            instance = inst_dir.name
            p_prohib = load_patch(dataset, "run_free", instance)
            p_unrestr = load_patch(dataset, "run_full", instance)
            if not p_prohib or not p_unrestr:
                continue  # need both patches to compare
            total_pairs += 1

            n1 = normalize_patch(p_prohib)
            n2 = normalize_patch(p_unrestr)
            ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
            ratios.append(ratio)

            if ratio >= 0.999:
                identical += 1
                continue

            files1 = extract_files(p_prohib)
            files2 = extract_files(p_unrestr)
            if files1 and files1 == files2 and ratio < 0.10:
                same_file_diff_code += 1

    if not total_pairs:
        print("No matched patch pairs found")
        return

    pct_id = 100.0 * identical / total_pairs
    pct_same = 100.0 * same_file_diff_code / total_pairs
    avg_sim = 100.0 * sum(ratios) / len(ratios)

    out = Path(__file__).parent / "opencode_patch_diversity.md"
    out.write_text(
        f"# OpenCode patch diversity (Prohibited vs Unrestricted)\n\n"
        f"Total matched pairs: {total_pairs}\n\n"
        f"| Metric | OpenCode |\n"
        f"|--------|----------|\n"
        f"| Identical | {pct_id:.0f}% ({identical}/{total_pairs}) |\n"
        f"| Same file, diff code | {pct_same:.0f}% ({same_file_diff_code}/{total_pairs}) |\n"
        f"| Avg similarity | {avg_sim:.0f}% |\n"
    )
    print(out.read_text())


if __name__ == "__main__":
    main()
