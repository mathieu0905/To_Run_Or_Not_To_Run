#!/usr/bin/env python3
"""
交叉分析 v2：Actionable Reproduction 是否提升了文件定位准确度？

正确的对比方法：
对于同一个 instance，比较 Prohibited vs Unrestricted 的定位准确度
然后按 Unrestricted 中是否有 Actionable reproduction 分组

分析维度：
1. Prohibited 模式的定位准确度（baseline，无执行）
2. Unrestricted 模式的定位准确度，按 reproduction 类型分组：
   - Actionable: 有 reproduction 且包含有效信息
   - Non-actionable: 有 reproduction 但无有效信息
   - None: 没有 reproduction
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
class ModeAnalysis:
    """Analysis for one mode of one instance"""
    edited_files: Set[str] = field(default_factory=set)
    reproduction_category: str = "none"  # actionable, non_actionable, none
    hit: bool = False
    recall: float = 0.0


@dataclass
class InstancePairAnalysis:
    """Paired analysis for one instance across both modes"""
    instance_id: str
    agent: str
    dataset: str
    outcome: str  # pp or ff

    gt_files: Set[str] = field(default_factory=set)

    # Prohibited mode analysis
    prohibited: ModeAnalysis = field(default_factory=ModeAnalysis)

    # Unrestricted mode analysis
    unrestricted: ModeAnalysis = field(default_factory=ModeAnalysis)


def analyze_claude_trace(traces: list) -> Tuple[Set[str], str]:
    """
    Analyze Claude Code trace.
    Returns: (edited_files, reproduction_category)
    """
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
                            # This is reproduction
                            category = classify_reproduction_result(result)
                            if category == "actionable":
                                actionable_count += 1
                            else:
                                non_actionable_count += 1

            pending_exec = None

    # Determine overall reproduction category
    total_repro = actionable_count + non_actionable_count
    if total_repro == 0:
        repro_category = "none"
    elif actionable_count > 0:
        repro_category = "actionable"
    else:
        repro_category = "non_actionable"

    return edited_files, repro_category


def analyze_codex_trace(traces: list) -> Tuple[Set[str], str]:
    """
    Analyze Codex trace.
    Returns: (edited_files, reproduction_category)
    """
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

    # Determine overall reproduction category
    total_repro = actionable_count + non_actionable_count
    if total_repro == 0:
        repro_category = "none"
    elif actionable_count > 0:
        repro_category = "actionable"
    else:
        repro_category = "non_actionable"

    return edited_files, repro_category


def calculate_localization_metrics(edited_files: Set[str], gt_files: Set[str]) -> Tuple[bool, float]:
    """Calculate hit and recall"""
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
    print("交叉分析 v2：Prohibited vs Unrestricted 定位准确度对比")
    print("=" * 80)

    cases = load_outcome_cases()

    # Store all paired analyses
    all_analyses: Dict[str, Dict[str, List[InstancePairAnalysis]]] = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    for agent in ["claude_code", "codex"]:
        for outcome in ["pp", "ff"]:
            print(f"\n分析 {agent} {outcome.upper()}...")

            for dataset, instance in cases[agent][outcome]:
                # Load both traces
                prohibited_traces = load_trace(dataset, agent, "run_free", instance)
                unrestricted_traces = load_trace(dataset, agent, "run_full", instance)

                if not prohibited_traces or not unrestricted_traces:
                    continue

                # Create paired analysis
                pair = InstancePairAnalysis(
                    instance_id=instance,
                    agent=agent,
                    dataset=dataset,
                    outcome=outcome
                )

                # Load ground truth
                pair.gt_files = load_ground_truth_files(dataset, instance)

                # Analyze Prohibited mode
                if agent == "claude_code":
                    prohibited_files, _ = analyze_claude_trace(prohibited_traces)
                else:
                    prohibited_files, _ = analyze_codex_trace(prohibited_traces)

                pair.prohibited.edited_files = prohibited_files
                pair.prohibited.reproduction_category = "none"  # No execution in prohibited
                pair.prohibited.hit, pair.prohibited.recall = calculate_localization_metrics(
                    prohibited_files, pair.gt_files
                )

                # Analyze Unrestricted mode
                if agent == "claude_code":
                    unrestricted_files, repro_cat = analyze_claude_trace(unrestricted_traces)
                else:
                    unrestricted_files, repro_cat = analyze_codex_trace(unrestricted_traces)

                pair.unrestricted.edited_files = unrestricted_files
                pair.unrestricted.reproduction_category = repro_cat
                pair.unrestricted.hit, pair.unrestricted.recall = calculate_localization_metrics(
                    unrestricted_files, pair.gt_files
                )

                all_analyses[agent][outcome].append(pair)

    # Generate report
    generate_report(all_analyses)


def generate_report(all_analyses: Dict):
    lines = []
    lines.append("# 交叉分析 v2：Prohibited vs Unrestricted 定位准确度对比")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    lines.append("## 研究问题")
    lines.append("")
    lines.append("对于**同一个 instance**，比较：")
    lines.append("1. **Prohibited 模式**（禁止执行）的定位准确度")
    lines.append("2. **Unrestricted 模式**（允许执行）的定位准确度，按 reproduction 类型分组")
    lines.append("")
    lines.append("这样可以控制问题难度，回答：**「执行是否真的帮助了定位？」**")
    lines.append("")

    lines.append("---")
    lines.append("")

    json_results = {}

    for outcome in ["pp", "ff"]:
        outcome_label = "P→P" if outcome == "pp" else "F→F"
        lines.append(f"## {outcome_label} 案例分析")
        lines.append("")

        # Table header
        lines.append("| Agent | Mode | Repro Category | Count | Hit Rate | Avg Recall |")
        lines.append("|-------|------|----------------|-------|----------|------------|")

        for agent in ["claude_code", "codex"]:
            agent_label = "Claude Code" if agent == "claude_code" else "Codex"

            if agent not in json_results:
                json_results[agent] = {}
            if outcome not in json_results[agent]:
                json_results[agent][outcome] = {}

            pairs = all_analyses[agent][outcome]
            if not pairs:
                continue

            # 1. Prohibited mode (all instances)
            prohibited_hits = sum(1 for p in pairs if p.prohibited.hit)
            prohibited_recall = sum(p.prohibited.recall for p in pairs) / len(pairs) if pairs else 0

            lines.append(f"| {agent_label} | **Prohibited** | N/A (无执行) | {len(pairs)} | {prohibited_hits/len(pairs)*100:.1f}% | {prohibited_recall*100:.1f}% |")

            json_results[agent][outcome]["prohibited"] = {
                "count": len(pairs),
                "hit_rate": prohibited_hits / len(pairs) if pairs else 0,
                "avg_recall": prohibited_recall
            }

            # 2. Unrestricted mode, grouped by reproduction category
            for repro_cat in ["actionable", "non_actionable", "none"]:
                cat_pairs = [p for p in pairs if p.unrestricted.reproduction_category == repro_cat]
                if not cat_pairs:
                    continue

                cat_hits = sum(1 for p in cat_pairs if p.unrestricted.hit)
                cat_recall = sum(p.unrestricted.recall for p in cat_pairs) / len(cat_pairs)

                cat_label = {
                    "actionable": "Actionable",
                    "non_actionable": "Non-actionable",
                    "none": "No Reproduction"
                }[repro_cat]

                lines.append(f"| {agent_label} | Unrestricted | {cat_label} | {len(cat_pairs)} | {cat_hits/len(cat_pairs)*100:.1f}% | {cat_recall*100:.1f}% |")

                json_results[agent][outcome][f"unrestricted_{repro_cat}"] = {
                    "count": len(cat_pairs),
                    "hit_rate": cat_hits / len(cat_pairs) if cat_pairs else 0,
                    "avg_recall": cat_recall
                }

            # Add separator between agents
            if agent == "claude_code":
                lines.append("|  |  |  |  |  |  |")

        lines.append("")

        # Paired comparison: same instance, different modes
        lines.append(f"### {outcome_label} 配对对比：同一 Instance 在两种模式下的定位变化")
        lines.append("")
        lines.append("| Agent | Repro Category | Count | Prohibited→Unrestricted Hit变化 | Recall变化 |")
        lines.append("|-------|----------------|-------|--------------------------------|------------|")

        for agent in ["claude_code", "codex"]:
            agent_label = "Claude Code" if agent == "claude_code" else "Codex"
            pairs = all_analyses[agent][outcome]

            for repro_cat in ["actionable", "non_actionable", "none"]:
                cat_pairs = [p for p in pairs if p.unrestricted.reproduction_category == repro_cat]
                if not cat_pairs:
                    continue

                # Compare same instance across modes
                hit_improved = sum(1 for p in cat_pairs if not p.prohibited.hit and p.unrestricted.hit)
                hit_degraded = sum(1 for p in cat_pairs if p.prohibited.hit and not p.unrestricted.hit)
                hit_same = len(cat_pairs) - hit_improved - hit_degraded

                recall_diff = sum(p.unrestricted.recall - p.prohibited.recall for p in cat_pairs) / len(cat_pairs)

                cat_label = {
                    "actionable": "Actionable",
                    "non_actionable": "Non-actionable",
                    "none": "No Reproduction"
                }[repro_cat]

                hit_change = f"+{hit_improved}/-{hit_degraded}/={hit_same}"
                recall_change = f"{recall_diff*100:+.1f}pp"

                lines.append(f"| {agent_label} | {cat_label} | {len(cat_pairs)} | {hit_change} | {recall_change} |")

                # Store in JSON
                json_results[agent][outcome][f"paired_{repro_cat}"] = {
                    "count": len(cat_pairs),
                    "hit_improved": hit_improved,
                    "hit_degraded": hit_degraded,
                    "hit_same": hit_same,
                    "avg_recall_diff": recall_diff
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

        prohibited = pp_data.get("prohibited", {})
        actionable = pp_data.get("paired_actionable", {})
        none = pp_data.get("paired_none", {})

        if prohibited and actionable:
            lines.append(f"**Actionable Reproduction 组** ({actionable.get('count', 0)} 个 instance)：")
            lines.append(f"- Hit 变化: +{actionable.get('hit_improved', 0)} 提升 / -{actionable.get('hit_degraded', 0)} 下降 / ={actionable.get('hit_same', 0)} 不变")
            lines.append(f"- Recall 平均变化: {actionable.get('avg_recall_diff', 0)*100:+.1f}pp")
            lines.append("")

        if prohibited and none:
            lines.append(f"**No Reproduction 组** ({none.get('count', 0)} 个 instance)：")
            lines.append(f"- Hit 变化: +{none.get('hit_improved', 0)} 提升 / -{none.get('hit_degraded', 0)} 下降 / ={none.get('hit_same', 0)} 不变")
            lines.append(f"- Recall 平均变化: {none.get('avg_recall_diff', 0)*100:+.1f}pp")
            lines.append("")

    lines.append("## 解读")
    lines.append("")
    lines.append("- **+Hit 提升**: Prohibited 模式定位失败，Unrestricted 模式定位成功 → 执行帮助了定位")
    lines.append("- **-Hit 下降**: Prohibited 模式定位成功，Unrestricted 模式定位失败 → 执行可能干扰了定位")
    lines.append("- **=Hit 不变**: 两种模式定位结果一致 → 执行对定位无影响")
    lines.append("")
    lines.append("如果 Actionable 组的「提升」数量远大于「下降」，说明执行确实帮助了定位。")
    lines.append("如果两者接近或「下降」更多，说明执行对定位帮助有限甚至有负面影响。")
    lines.append("")

    # Save report
    report_file = ANALYSIS_DIR / "actionable_localization_analysis_v2.md"
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\n报告已保存: {report_file}")

    # Save JSON
    json_file = ANALYSIS_DIR / "actionable_localization_analysis_v2.json"
    with open(json_file, "w") as f:
        json.dump(json_results, f, indent=2)
    print(f"JSON 已保存: {json_file}")


if __name__ == "__main__":
    main()
