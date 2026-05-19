#!/usr/bin/env python3
"""
交叉分析：Actionable Reproduction 是否提升了文件定位准确度？

分析三类案例：
1. Actionable reproduction: 执行结果包含有效信息（文件路径、stacktrace、行号）
2. Non-actionable reproduction: 执行结果是环境错误或无有效信息
3. No reproduction: 没有在编辑前执行测试

对比每类的文件定位准确度 (Hit, Recall)
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Set, Optional, Tuple
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
    """判断是否是测试文件（而非源代码文件）"""
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
    """
    分类 reproduction 执行结果：
    - actionable: 包含有效定位信息
    - non_actionable: 环境错误或无有效信息
    """
    content_lower = content.lower()

    # 环境错误 - non-actionable
    env_errors = ['No module named', 'ModuleNotFoundError', 'command not found',
                  'FileNotFoundError', 'No such file or directory',
                  'Permission denied', 'UnicodeDecodeError', 'encoding']
    for err in env_errors:
        if err in content or err.lower() in content_lower:
            return "non_actionable"

    # 检查是否包含有用的定位信息
    has_filepath = bool(re.search(r'[a-zA-Z_][a-zA-Z0-9_/]*\.py', content))
    has_traceback = 'Traceback' in content or 'File "' in content
    has_line_number = bool(re.search(r'line \d+', content_lower))

    if has_filepath or has_traceback or has_line_number:
        return "actionable"

    # 成功执行也算 actionable（确认了问题存在）
    if 'passed' in content_lower and 'failed' not in content_lower:
        return "actionable"
    if content.strip().endswith('OK') or '\nOK' in content:
        return "actionable"

    return "non_actionable"


def extract_files_from_patch(patch_content: str) -> Set[str]:
    """Extract file paths from a git diff patch"""
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
    """Load ground truth files from SWE-bench dataset"""
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
class InstanceAnalysis:
    instance_id: str
    agent: str
    dataset: str
    outcome: str  # pp or ff

    # Reproduction category
    reproduction_category: str = "none"  # "actionable", "non_actionable", "none"
    reproduction_count: int = 0
    actionable_count: int = 0
    non_actionable_count: int = 0

    # Edited files
    edited_files: Set[str] = field(default_factory=set)

    # Ground truth files
    gt_files: Set[str] = field(default_factory=set)

    # Localization metrics
    hit: bool = False
    recall: float = 0.0


def analyze_claude_trace(traces: list, instance_id: str, dataset: str, outcome: str) -> InstanceAnalysis:
    analysis = InstanceAnalysis(instance_id=instance_id, agent="claude_code",
                                 dataset=dataset, outcome=outcome)

    first_source_edit_found = False
    pending_exec = None

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
                                analysis.edited_files.add(normalized)
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
                            # This is reproduction
                            analysis.reproduction_count += 1
                            category = classify_reproduction_result(result)
                            if category == "actionable":
                                analysis.actionable_count += 1
                            else:
                                analysis.non_actionable_count += 1

            pending_exec = None

    # Determine overall reproduction category
    if analysis.reproduction_count == 0:
        analysis.reproduction_category = "none"
    elif analysis.actionable_count > 0:
        # If any reproduction was actionable, categorize as actionable
        analysis.reproduction_category = "actionable"
    else:
        analysis.reproduction_category = "non_actionable"

    return analysis


def analyze_codex_trace(traces: list, instance_id: str, dataset: str, outcome: str) -> InstanceAnalysis:
    analysis = InstanceAnalysis(instance_id=instance_id, agent="codex",
                                 dataset=dataset, outcome=outcome)

    first_source_edit_found = False

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
                        analysis.edited_files.add(normalized)
                        first_source_edit_found = True

            if item_type == "command_execution":
                cmd = item.get("command", "")
                if "bash -lc" in cmd:
                    match = re.search(r"'([^']+)'[^']*$", cmd)
                    if match:
                        cmd = match.group(1)

                if is_test_execution(cmd):
                    if not first_source_edit_found:
                        # This is reproduction
                        result = item.get("aggregated_output", "")
                        analysis.reproduction_count += 1
                        category = classify_reproduction_result(result)
                        if category == "actionable":
                            analysis.actionable_count += 1
                        else:
                            analysis.non_actionable_count += 1

    # Determine overall reproduction category
    if analysis.reproduction_count == 0:
        analysis.reproduction_category = "none"
    elif analysis.actionable_count > 0:
        analysis.reproduction_category = "actionable"
    else:
        analysis.reproduction_category = "non_actionable"

    return analysis


def calculate_localization_metrics(analysis: InstanceAnalysis):
    """Calculate file localization metrics"""
    if not analysis.gt_files:
        return

    if not analysis.edited_files:
        analysis.hit = False
        analysis.recall = 0.0
        return

    intersection = analysis.gt_files & analysis.edited_files
    analysis.hit = len(intersection) > 0
    analysis.recall = len(intersection) / len(analysis.gt_files)


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
    print("交叉分析：Actionable Reproduction vs Localization Accuracy")
    print("=" * 80)

    cases = load_outcome_cases()

    # Store all analyses
    all_analyses = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    for agent in ["claude_code", "codex"]:
        for outcome in ["pp", "ff"]:
            print(f"\n分析 {agent} {outcome.upper()}...")

            for dataset, instance in cases[agent][outcome]:
                traces = load_trace(dataset, agent, "run_full", instance)
                if not traces:
                    continue

                if agent == "claude_code":
                    analysis = analyze_claude_trace(traces, instance, dataset, outcome)
                else:
                    analysis = analyze_codex_trace(traces, instance, dataset, outcome)

                # Load ground truth
                analysis.gt_files = load_ground_truth_files(dataset, instance)

                # Calculate localization metrics
                calculate_localization_metrics(analysis)

                all_analyses[agent][outcome].append(analysis)

    # Generate cross-analysis report
    generate_report(all_analyses)


def generate_report(all_analyses: dict):
    lines = []
    lines.append("# 交叉分析：Actionable Reproduction 是否提升文件定位准确度？")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    lines.append("## 研究问题")
    lines.append("")
    lines.append("当 Agent 在编辑代码前执行测试（reproduction），且执行结果包含**可操作信息**")
    lines.append("（如文件路径、stacktrace、行号）时，文件定位的准确度是否更高？")
    lines.append("")

    lines.append("## 分类定义")
    lines.append("")
    lines.append("- **Actionable**: 至少一次 reproduction 包含有效定位信息（文件路径、Traceback、行号）")
    lines.append("- **Non-actionable**: 有 reproduction 但全部是环境错误或无有效信息")
    lines.append("- **None**: 没有在编辑前执行测试")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Main results table
    lines.append("## P→P 案例分析 (Unrestricted 模式)")
    lines.append("")
    lines.append("| Agent | Repro Category | Count | Hit Rate | Avg Recall |")
    lines.append("|-------|----------------|-------|----------|------------|")

    json_results = {}

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        json_results[agent] = {"pp": {}, "ff": {}}

        pp_analyses = all_analyses[agent]["pp"]

        for category in ["actionable", "non_actionable", "none"]:
            category_analyses = [a for a in pp_analyses if a.reproduction_category == category]
            count = len(category_analyses)

            if count > 0:
                hit_rate = sum(1 for a in category_analyses if a.hit) / count
                avg_recall = sum(a.recall for a in category_analyses) / count
            else:
                hit_rate = 0
                avg_recall = 0

            category_label = {
                "actionable": "Actionable",
                "non_actionable": "Non-actionable",
                "none": "No Reproduction"
            }[category]

            lines.append(f"| {agent_label} | {category_label} | {count} | {hit_rate*100:.1f}% | {avg_recall*100:.1f}% |")

            json_results[agent]["pp"][category] = {
                "count": count,
                "hit_rate": hit_rate,
                "avg_recall": avg_recall
            }

    lines.append("")

    # F→F analysis
    lines.append("## F→F 案例分析 (Unrestricted 模式)")
    lines.append("")
    lines.append("| Agent | Repro Category | Count | Hit Rate | Avg Recall |")
    lines.append("|-------|----------------|-------|----------|------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"

        ff_analyses = all_analyses[agent]["ff"]

        for category in ["actionable", "non_actionable", "none"]:
            category_analyses = [a for a in ff_analyses if a.reproduction_category == category]
            count = len(category_analyses)

            if count > 0:
                hit_rate = sum(1 for a in category_analyses if a.hit) / count
                avg_recall = sum(a.recall for a in category_analyses) / count
            else:
                hit_rate = 0
                avg_recall = 0

            category_label = {
                "actionable": "Actionable",
                "non_actionable": "Non-actionable",
                "none": "No Reproduction"
            }[category]

            lines.append(f"| {agent_label} | {category_label} | {count} | {hit_rate*100:.1f}% | {avg_recall*100:.1f}% |")

            json_results[agent]["ff"][category] = {
                "count": count,
                "hit_rate": hit_rate,
                "avg_recall": avg_recall
            }

    lines.append("")

    # Key findings
    lines.append("---")
    lines.append("")
    lines.append("## 关键发现")
    lines.append("")

    # Compare actionable vs none for each agent
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp = json_results[agent]["pp"]

        actionable = pp.get("actionable", {"count": 0, "hit_rate": 0, "avg_recall": 0})
        none = pp.get("none", {"count": 0, "hit_rate": 0, "avg_recall": 0})
        non_actionable = pp.get("non_actionable", {"count": 0, "hit_rate": 0, "avg_recall": 0})

        lines.append(f"### {agent_label}")
        lines.append("")

        if actionable["count"] > 0 and none["count"] > 0:
            hit_diff = actionable["hit_rate"] - none["hit_rate"]
            recall_diff = actionable["avg_recall"] - none["avg_recall"]

            if hit_diff > 0.05:
                lines.append(f"- Actionable reproduction **提升**了 Hit Rate: {actionable['hit_rate']*100:.1f}% vs {none['hit_rate']*100:.1f}% (+{hit_diff*100:.1f}pp)")
            elif hit_diff < -0.05:
                lines.append(f"- Actionable reproduction **没有提升** Hit Rate: {actionable['hit_rate']*100:.1f}% vs {none['hit_rate']*100:.1f}% ({hit_diff*100:.1f}pp)")
            else:
                lines.append(f"- Actionable reproduction 对 Hit Rate **无显著影响**: {actionable['hit_rate']*100:.1f}% vs {none['hit_rate']*100:.1f}%")

            if recall_diff > 0.05:
                lines.append(f"- Actionable reproduction **提升**了 Recall: {actionable['avg_recall']*100:.1f}% vs {none['avg_recall']*100:.1f}% (+{recall_diff*100:.1f}pp)")
            elif recall_diff < -0.05:
                lines.append(f"- Actionable reproduction **没有提升** Recall: {actionable['avg_recall']*100:.1f}% vs {none['avg_recall']*100:.1f}% ({recall_diff*100:.1f}pp)")
            else:
                lines.append(f"- Actionable reproduction 对 Recall **无显著影响**: {actionable['avg_recall']*100:.1f}% vs {none['avg_recall']*100:.1f}%")

        if non_actionable["count"] > 0:
            lines.append(f"- Non-actionable reproduction 案例: {non_actionable['count']} (Hit: {non_actionable['hit_rate']*100:.1f}%, Recall: {non_actionable['avg_recall']*100:.1f}%)")

        lines.append("")

    lines.append("## 结论")
    lines.append("")
    lines.append("如果 Actionable reproduction 的 Hit/Recall 与 No reproduction 相近或更低，")
    lines.append("说明即使执行提供了可操作信息，Agent 的定位能力也没有显著提升。")
    lines.append("这进一步支持「问题描述足够清晰」的论点。")
    lines.append("")

    # Save report
    report_file = ANALYSIS_DIR / "actionable_localization_analysis.md"
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\n报告已保存: {report_file}")

    # Save JSON
    json_file = ANALYSIS_DIR / "actionable_localization_analysis.json"
    with open(json_file, "w") as f:
        json.dump(json_results, f, indent=2)
    print(f"JSON 已保存: {json_file}")


if __name__ == "__main__":
    main()
