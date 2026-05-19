#!/usr/bin/env python3
"""
交叉分析 v3：按 Unrestricted 的 Reproduction 类型分组后，对比同一批 instance 在两种模式下的定位准确度

核心问题：
对于 Unrestricted 模式中有 Actionable reproduction 的那 46 个 instance，
它们在 Prohibited 模式（无执行）下的 Hit Rate 是多少？

这样才能回答：同一批 instance，允许执行（且有 actionable reproduction）后，定位是否更准？
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Set, Dict, Tuple
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


def normalize_path(path: str) -> str:
    if path.startswith('./'):
        path = path[2:]
    if path.startswith('/'):
        path = path.lstrip('/')
    if path.startswith('testbed/'):
        path = path[8:]
    return path


def is_test_execution(cmd: str) -> bool:
    cmd_lower = cmd.lower().strip()
    test_patterns = [
        r'\bpytest\b', r'\bpy\.test\b', r'python[3]?\s+-m\s+pytest',
        r'python[3]?\s+-m\s+unittest', r'manage\.py\s+test',
        r'\btox\b', r'\bnosetests?\b',
    ]
    for pattern in test_patterns:
        if re.search(pattern, cmd_lower):
            return True
    if re.search(r'python[3]?\s+\S+\.py', cmd_lower):
        if not re.search(r'python[3]?\s+-c\s', cmd_lower):
            return True
    return False


def is_test_file(path: str) -> bool:
    path_lower = path.lower()
    if '/test_' in path_lower or '/tests/' in path_lower:
        return True
    if path_lower.endswith('_test.py'):
        return True
    if 'test' in path_lower.split('/')[-1]:
        return True
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return True
    if 'script' in path_lower.split('/')[-1]:
        return True
    if path_lower.count('/') == 0 and path_lower.endswith('.py'):
        return True
    return False


def classify_reproduction_result(content: str) -> str:
    content_lower = content.lower()

    env_errors = ['No module named', 'ModuleNotFoundError', 'command not found',
                  'FileNotFoundError', 'No such file or directory',
                  'Permission denied', 'UnicodeDecodeError', 'encoding']
    for err in env_errors:
        if err in content or err.lower() in content_lower:
            return "non_actionable"

    has_filepath = bool(re.search(r'[a-zA-Z_][a-zA-Z0-9_/]*\.py', content))
    has_traceback = 'Traceback' in content or 'File "' in content
    has_line_number = bool(re.search(r'line \d+', content_lower))

    if has_filepath or has_traceback or has_line_number:
        return "actionable"

    if 'passed' in content_lower and 'failed' not in content_lower:
        return "actionable"
    if content.strip().endswith('OK') or '\nOK' in content:
        return "actionable"

    return "non_actionable"


def extract_files_from_patch(patch_content: str) -> Set[str]:
    files = set()
    for line in patch_content.split('\n'):
        if line.startswith('diff --git'):
            match = re.search(r'diff --git a/(.+?) b/', line)
            if match:
                files.add(normalize_path(match.group(1)))
        elif line.startswith('+++ b/'):
            path = line[6:].strip()
            if path and path != '/dev/null':
                files.add(normalize_path(path))
        elif line.startswith('--- a/'):
            path = line[6:].strip()
            if path and path != '/dev/null':
                files.add(normalize_path(path))
    return files


def load_ground_truth_files(dataset: str, instance_id: str) -> Set[str]:
    dataset_file_map = {
        "swebenchlite": "swe_bench_lite.json",
        "swebenchverified": "swe_bench_verified.json",
    }

    filename = dataset_file_map.get(dataset, f"{dataset}.json")
    swebench_data_file = PROJECT_ROOT / "data" / filename

    if swebench_data_file.exists():
        with open(swebench_data_file) as f:
            data = json.load(f)
        for item in data:
            if item.get("instance_id") == instance_id:
                patch = item.get("patch", "")
                return extract_files_from_patch(patch)

    return set()


@dataclass
class InstancePairAnalysis:
    instance_id: str
    agent: str
    dataset: str
    outcome: str

    gt_files: Set[str] = field(default_factory=set)

    # Prohibited mode
    prohibited_edited_files: Set[str] = field(default_factory=set)
    prohibited_hit: bool = False
    prohibited_recall: float = 0.0

    # Unrestricted mode
    unrestricted_edited_files: Set[str] = field(default_factory=set)
    unrestricted_reproduction_category: str = "none"
    unrestricted_hit: bool = False
    unrestricted_recall: float = 0.0


def analyze_claude_trace(traces: list) -> Tuple[Set[str], str]:
    edited_files = set()
    first_source_edit_found = False
    pending_exec = None
    actionable_count = 0
    non_actionable_count = 0

    for entry in traces:
        entry_type = entry.get("type", "")

        if entry_type == "assistant":
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")

                    if tool_name in ["Edit", "Write"]:
                        file_path = item.get("input", {}).get("file_path", "")
                        if file_path:
                            normalized = normalize_path(file_path)
                            if not is_test_file(normalized):
                                edited_files.add(normalized)
                                first_source_edit_found = True

                    if tool_name == "Bash":
                        cmd = item.get("input", {}).get("command", "")
                        if is_test_execution(cmd):
                            pending_exec = {"is_after_source_edit": first_source_edit_found}

        elif entry_type == "user" and pending_exec:
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    result = item.get("content", "")
                    if isinstance(result, str):
                        if not pending_exec["is_after_source_edit"]:
                            category = classify_reproduction_result(result)
                            if category == "actionable":
                                actionable_count += 1
                            else:
                                non_actionable_count += 1

            pending_exec = None

    total_repro = actionable_count + non_actionable_count
    if total_repro == 0:
        repro_category = "none"
    elif actionable_count > 0:
        repro_category = "actionable"
    else:
        repro_category = "non_actionable"

    return edited_files, repro_category


def analyze_codex_trace(traces: list) -> Tuple[Set[str], str]:
    edited_files = set()
    first_source_edit_found = False
    actionable_count = 0
    non_actionable_count = 0

    for entry in traces:
        entry_type = entry.get("type", "")

        if entry_type == "item.completed":
            item = entry.get("item", {})
            item_type = item.get("type", "")

            if item_type in ["file_edit", "file_change"]:
                file_path = ""
                changes = item.get("changes", [])
                for change in changes:
                    path = change.get("path", "")
                    if path:
                        file_path = path
                        break
                if not file_path:
                    file_path = item.get("file_path", "")

                if file_path:
                    normalized = normalize_path(file_path)
                    if not is_test_file(normalized):
                        edited_files.add(normalized)
                        first_source_edit_found = True

            if item_type == "command_execution":
                cmd = item.get("command", "")
                if "bash -lc" in cmd:
                    match = re.search(r"'([^']+)'[^']*$", cmd)
                    if match:
                        cmd = match.group(1)

                if is_test_execution(cmd):
                    if not first_source_edit_found:
                        result = item.get("aggregated_output", "")
                        category = classify_reproduction_result(result)
                        if category == "actionable":
                            actionable_count += 1
                        else:
                            non_actionable_count += 1

    total_repro = actionable_count + non_actionable_count
    if total_repro == 0:
        repro_category = "none"
    elif actionable_count > 0:
        repro_category = "actionable"
    else:
        repro_category = "non_actionable"

    return edited_files, repro_category


def calculate_localization_metrics(edited_files: Set[str], gt_files: Set[str]) -> Tuple[bool, float]:
    if not gt_files:
        return False, 0.0
    if not edited_files:
        return False, 0.0

    intersection = gt_files & edited_files
    hit = len(intersection) > 0
    recall = len(intersection) / len(gt_files)
    return hit, recall


def load_trace(dataset: str, agent: str, mode: str, instance: str) -> list:
    trace_file = OUTPUT_DIR / dataset / agent / mode / instance / "trace.jsonl"
    if not trace_file.exists():
        return []

    traces = []
    with open(trace_file) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    traces.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return traces


def load_outcome_cases() -> dict:
    pp_file = PROJECT_ROOT / "analysis" / "pp_why_no_execution_needed.json"

    cases = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    if pp_file.exists():
        with open(pp_file) as f:
            data = json.load(f)

        for item in data.get("results", []):
            instance = item["instance"]
            agent = item["agent"]
            group = item["group"]
            dataset = "swebenchlite" if "Lite" in group else "swebenchverified"
            cases[agent]["pp"].append((dataset, instance))

    pp_sets = {
        "claude_code": set(inst for _, inst in cases["claude_code"]["pp"]),
        "codex": set(inst for _, inst in cases["codex"]["pp"])
    }

    for dataset in ["swebenchlite", "swebenchverified"]:
        for agent in ["claude_code", "codex"]:
            free_dir = OUTPUT_DIR / dataset / agent / "run_free"
            full_dir = OUTPUT_DIR / dataset / agent / "run_full"

            if not free_dir.exists() or not full_dir.exists():
                continue

            free_instances = set(d.name for d in free_dir.iterdir() if d.is_dir())
            full_instances = set(d.name for d in full_dir.iterdir() if d.is_dir())
            common = free_instances & full_instances

            for instance in common:
                if instance not in pp_sets[agent]:
                    cases[agent]["ff"].append((dataset, instance))

    return cases


def main():
    print("=" * 80)
    print("交叉分析 v3：同一批 Instance 的配对对比")
    print("=" * 80)

    cases = load_outcome_cases()

    all_analyses: Dict[str, Dict[str, List[InstancePairAnalysis]]] = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    for agent in ["claude_code", "codex"]:
        for outcome in ["pp", "ff"]:
            print(f"\n分析 {agent} {outcome.upper()}...")

            for dataset, instance in cases[agent][outcome]:
                prohibited_traces = load_trace(dataset, agent, "run_free", instance)
                unrestricted_traces = load_trace(dataset, agent, "run_full", instance)

                if not prohibited_traces or not unrestricted_traces:
                    continue

                pair = InstancePairAnalysis(
                    instance_id=instance,
                    agent=agent,
                    dataset=dataset,
                    outcome=outcome
                )

                pair.gt_files = load_ground_truth_files(dataset, instance)

                # Analyze Prohibited mode
                if agent == "claude_code":
                    prohibited_files, _ = analyze_claude_trace(prohibited_traces)
                else:
                    prohibited_files, _ = analyze_codex_trace(prohibited_traces)

                pair.prohibited_edited_files = prohibited_files
                pair.prohibited_hit, pair.prohibited_recall = calculate_localization_metrics(
                    prohibited_files, pair.gt_files
                )

                # Analyze Unrestricted mode
                if agent == "claude_code":
                    unrestricted_files, repro_cat = analyze_claude_trace(unrestricted_traces)
                else:
                    unrestricted_files, repro_cat = analyze_codex_trace(unrestricted_traces)

                pair.unrestricted_edited_files = unrestricted_files
                pair.unrestricted_reproduction_category = repro_cat
                pair.unrestricted_hit, pair.unrestricted_recall = calculate_localization_metrics(
                    unrestricted_files, pair.gt_files
                )

                all_analyses[agent][outcome].append(pair)

    generate_report(all_analyses)


def generate_report(all_analyses: Dict):
    lines = []
    lines.append("# 交叉分析 v3：同一批 Instance 的配对对比")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    lines.append("## 核心问题")
    lines.append("")
    lines.append("对于 Unrestricted 模式中有 **Actionable reproduction** 的那批 instance，")
    lines.append("**同一批 instance** 在 Prohibited 模式（无执行）下的 Hit Rate 是多少？")
    lines.append("")
    lines.append("这样才能回答：**执行提供 actionable 信息后，定位是否真的更准？**")
    lines.append("")

    lines.append("---")
    lines.append("")

    json_results = {}

    for outcome in ["pp", "ff"]:
        outcome_label = "P→P" if outcome == "pp" else "F→F"
        lines.append(f"## {outcome_label} 案例分析")
        lines.append("")

        # 按 Unrestricted 的 reproduction category 分组，展示同一批 instance 在两种模式下的数据
        lines.append("| Agent | Repro Category (Unrestricted) | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |")
        lines.append("|-------|------------------------------|-------|----------------|-------------------|------------------|---------------------|-------|----------|")

        for agent in ["claude_code", "codex"]:
            agent_label = "Claude Code" if agent == "claude_code" else "Codex"

            if agent not in json_results:
                json_results[agent] = {}
            if outcome not in json_results[agent]:
                json_results[agent][outcome] = {}

            pairs = all_analyses[agent][outcome]

            for repro_cat in ["actionable", "non_actionable", "none"]:
                cat_pairs = [p for p in pairs if p.unrestricted_reproduction_category == repro_cat]
                if not cat_pairs:
                    continue

                # 同一批 instance 在 Prohibited 模式下的统计
                prohibited_hits = sum(1 for p in cat_pairs if p.prohibited_hit)
                prohibited_hit_rate = prohibited_hits / len(cat_pairs)
                prohibited_avg_recall = sum(p.prohibited_recall for p in cat_pairs) / len(cat_pairs)

                # 同一批 instance 在 Unrestricted 模式下的统计
                unrestricted_hits = sum(1 for p in cat_pairs if p.unrestricted_hit)
                unrestricted_hit_rate = unrestricted_hits / len(cat_pairs)
                unrestricted_avg_recall = sum(p.unrestricted_recall for p in cat_pairs) / len(cat_pairs)

                # Delta
                delta_hit = unrestricted_hit_rate - prohibited_hit_rate
                delta_recall = unrestricted_avg_recall - prohibited_avg_recall

                cat_label = {
                    "actionable": "Actionable",
                    "non_actionable": "Non-actionable",
                    "none": "No Reproduction"
                }[repro_cat]

                delta_hit_str = f"{delta_hit*100:+.1f}pp"
                delta_recall_str = f"{delta_recall*100:+.1f}pp"

                lines.append(f"| {agent_label} | {cat_label} | {len(cat_pairs)} | {prohibited_hit_rate*100:.1f}% | {prohibited_avg_recall*100:.1f}% | {unrestricted_hit_rate*100:.1f}% | {unrestricted_avg_recall*100:.1f}% | {delta_hit_str} | {delta_recall_str} |")

                json_results[agent][outcome][repro_cat] = {
                    "count": len(cat_pairs),
                    "prohibited_hit_rate": prohibited_hit_rate,
                    "prohibited_avg_recall": prohibited_avg_recall,
                    "unrestricted_hit_rate": unrestricted_hit_rate,
                    "unrestricted_avg_recall": unrestricted_avg_recall,
                    "delta_hit": delta_hit,
                    "delta_recall": delta_recall
                }

        lines.append("")

    # Key findings
    lines.append("---")
    lines.append("")
    lines.append("## 关键发现")
    lines.append("")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        lines.append(f"### {agent_label}")
        lines.append("")

        pp_data = json_results.get(agent, {}).get("pp", {})

        actionable = pp_data.get("actionable", {})
        none = pp_data.get("none", {})

        if actionable:
            lines.append(f"**Actionable 组** ({actionable.get('count', 0)} 个 instance)：")
            lines.append(f"- Prohibited Hit: {actionable.get('prohibited_hit_rate', 0)*100:.1f}% → Unrestricted Hit: {actionable.get('unrestricted_hit_rate', 0)*100:.1f}% (**Δ {actionable.get('delta_hit', 0)*100:+.1f}pp**)")
            lines.append(f"- Prohibited Recall: {actionable.get('prohibited_avg_recall', 0)*100:.1f}% → Unrestricted Recall: {actionable.get('unrestricted_avg_recall', 0)*100:.1f}% (**Δ {actionable.get('delta_recall', 0)*100:+.1f}pp**)")
            lines.append("")

        if none:
            lines.append(f"**No Reproduction 组** ({none.get('count', 0)} 个 instance)：")
            lines.append(f"- Prohibited Hit: {none.get('prohibited_hit_rate', 0)*100:.1f}% → Unrestricted Hit: {none.get('unrestricted_hit_rate', 0)*100:.1f}% (**Δ {none.get('delta_hit', 0)*100:+.1f}pp**)")
            lines.append(f"- Prohibited Recall: {none.get('prohibited_avg_recall', 0)*100:.1f}% → Unrestricted Recall: {none.get('unrestricted_avg_recall', 0)*100:.1f}% (**Δ {none.get('delta_recall', 0)*100:+.1f}pp**)")
            lines.append("")

    lines.append("## 解读")
    lines.append("")
    lines.append("- **Δ > 0**: Unrestricted 模式定位更准 → 执行帮助了定位")
    lines.append("- **Δ ≈ 0**: 两种模式定位相当 → 执行对定位无显著影响")
    lines.append("- **Δ < 0**: Unrestricted 模式定位更差 → 执行可能干扰了定位")
    lines.append("")
    lines.append("如果 Actionable 组的 Δ 显著为正，说明 actionable 的执行反馈确实帮助了文件定位。")
    lines.append("如果 Δ ≈ 0 或为负，说明即使执行提供了 actionable 信息，对定位帮助也有限。")
    lines.append("")

    # Save report
    report_file = ANALYSIS_DIR / "actionable_localization_analysis_v3.md"
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\n报告已保存: {report_file}")

    # Save JSON
    json_file = ANALYSIS_DIR / "actionable_localization_analysis_v3.json"
    with open(json_file, "w") as f:
        json.dump(json_results, f, indent=2)
    print(f"JSON 已保存: {json_file}")


if __name__ == "__main__":
    main()
