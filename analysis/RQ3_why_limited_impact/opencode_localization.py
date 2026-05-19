#!/usr/bin/env python3
"""OpenCode localization Hit/Recall for Pass->Pass and Fail->Fail cases.

Reuses `extract_files_from_patch` and `load_ground_truth_files` from
`rq3_comprehensive_analysis`, and `load_instance_level_results` from
`statistical_analysis` (which honours the _fixed priority).

Computes the Hit and Recall metrics that the paper reports in
`tab:localization-pp` for Claude Code and Codex.
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.RQ3_why_limited_impact.rq3_comprehensive_analysis import (  # noqa: E402
    extract_files_from_patch,
    load_ground_truth_files,
)
from analysis.common.statistical_analysis import load_instance_level_results  # noqa: E402


def instance_patch_files(dataset: str, agent: str, mode: str, instance: str) -> set:
    patch = PROJECT_ROOT / "output" / dataset / agent / mode / instance / "patch.diff"
    if not patch.exists() or patch.stat().st_size == 0:
        return set()
    try:
        return extract_files_from_patch(patch.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return set()


def compute_hit_recall(dataset: str, agent: str, mode: str, ids: list) -> tuple:
    hit_count = 0
    recall_sum = 0.0
    denom = 0
    for iid in ids:
        gt = load_ground_truth_files(dataset, iid)
        if not gt:
            continue
        preds = instance_patch_files(dataset, agent, mode, iid)
        if not preds:
            # No patch produced -- count as missed localization.
            denom += 1
            continue
        denom += 1
        if preds & gt:
            hit_count += 1
        recall_sum += len(preds & gt) / len(gt)
    if denom == 0:
        return 0.0, 0.0, 0
    return 100.0 * hit_count / denom, 100.0 * recall_sum / denom, denom


def main():
    inst = load_instance_level_results()

    results = {"PP": {}, "FF": {}}
    for dataset in ["swebenchlite", "swebenchverified"]:
        oc = inst.get(dataset, {}).get("opencode", {})
        prohib = set(oc.get("run_free", {}).get("resolved_ids", set()))
        unrestr = set(oc.get("run_full", {}).get("resolved_ids", set()))

        # Build Pass->Pass set (both modes resolved the same instance)
        pp_ids = sorted(prohib & unrestr)
        # Build Fail->Fail: neither mode resolved; we need the full instance
        # universe. Use the 100 instance IDs from dataset JSON.
        dataset_file = PROJECT_ROOT / "data" / (
            "swe_bench_lite.json" if dataset == "swebenchlite" else "swe_bench_verified.json"
        )
        import json
        full_ids = []
        if dataset_file.exists():
            data = json.load(open(dataset_file))
            full_ids = [item["instance_id"] for item in data[:100]]
        ff_ids = sorted(set(full_ids) - prohib - unrestr)

        for mode in ["run_full", "run_free"]:
            hit_pp, rec_pp, n_pp = compute_hit_recall(dataset, "opencode", mode, pp_ids)
            hit_ff, rec_ff, n_ff = compute_hit_recall(dataset, "opencode", mode, ff_ids)
            results["PP"][(dataset, mode)] = (hit_pp, rec_pp, n_pp)
            results["FF"][(dataset, mode)] = (hit_ff, rec_ff, n_ff)

    out = Path(__file__).parent / "opencode_localization.md"
    lines = []
    lines.append("# OpenCode localization Hit/Recall")
    lines.append("")
    lines.append("Computed from output/{dataset}/opencode/{mode}/{instance}/patch.diff")
    lines.append("using the same `extract_files_from_patch` helper as the main RQ3 analysis.")
    lines.append("")
    lines.append("## Pass->Pass cases (Prohibited AND Unrestricted resolved)")
    lines.append("")
    lines.append("| Dataset | Mode | n | Hit | Recall |")
    lines.append("|---------|------|---|-----|--------|")
    for (ds, mode), (hit, rec, n) in results["PP"].items():
        lines.append(f"| {ds} | {mode} | {n} | {hit:.1f}% | {rec:.1f}% |")
    lines.append("")
    lines.append("## Fail->Fail cases (neither mode resolved)")
    lines.append("")
    lines.append("| Dataset | Mode | n | Hit | Recall |")
    lines.append("|---------|------|---|-----|--------|")
    for (ds, mode), (hit, rec, n) in results["FF"].items():
        lines.append(f"| {ds} | {mode} | {n} | {hit:.1f}% | {rec:.1f}% |")
    lines.append("")

    # Also compute agent-level combined averages matching the Table 10 format
    lines.append("## Combined (Lite + Verified, matching tab:localization-pp format)")
    lines.append("")
    lines.append("| Mode | n_PP | Hit_PP | Recall_PP | n_FF | Hit_FF | Recall_FF |")
    lines.append("|------|------|--------|-----------|------|--------|-----------|")
    for mode in ["run_full", "run_free"]:
        hits_pp = [results["PP"][("swebenchlite", mode)], results["PP"][("swebenchverified", mode)]]
        hits_ff = [results["FF"][("swebenchlite", mode)], results["FF"][("swebenchverified", mode)]]
        n_pp = hits_pp[0][2] + hits_pp[1][2]
        n_ff = hits_ff[0][2] + hits_ff[1][2]
        # Weighted averages
        hit_pp_w = (hits_pp[0][0] * hits_pp[0][2] + hits_pp[1][0] * hits_pp[1][2]) / max(n_pp, 1)
        rec_pp_w = (hits_pp[0][1] * hits_pp[0][2] + hits_pp[1][1] * hits_pp[1][2]) / max(n_pp, 1)
        hit_ff_w = (hits_ff[0][0] * hits_ff[0][2] + hits_ff[1][0] * hits_ff[1][2]) / max(n_ff, 1)
        rec_ff_w = (hits_ff[0][1] * hits_ff[0][2] + hits_ff[1][1] * hits_ff[1][2]) / max(n_ff, 1)
        lines.append(f"| {mode} | {n_pp} | {hit_pp_w:.1f}% | {rec_pp_w:.1f}% | {n_ff} | {hit_ff_w:.1f}% | {rec_ff_w:.1f}% |")

    out.write_text("\n".join(lines) + "\n")
    print(f"Saved to: {out}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
