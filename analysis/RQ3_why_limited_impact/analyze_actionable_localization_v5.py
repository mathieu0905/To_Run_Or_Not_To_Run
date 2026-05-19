#!/usr/bin/env python3
"""
交叉分析 v5：修复 Actionable 分类逻辑

改进点：
1. Success 合并到 Actionable（测试成功本身就是有效信息）
2. 减少 Unclear，提高分类覆盖率
3. 更严格区分环境错误 vs 业务错误

分类逻辑：
- Actionable: 测试成功 OR 有效的测试失败（AssertionError, 具体失败信息）
- Non-actionable: 环境错误（模块缺失、数据库问题、配置问题等）
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


def classify_reproduction_result_v5(content: str) -> Tuple[str, str]:
    """
    改进的分类逻辑 v5

    返回 (category, reason)
    - actionable: 测试成功 或 有效的测试失败信息
    - non_actionable: 环境错误或无法提供有效定位信息
    """
    content_lower = content.lower()

    # ============================================
    # 1. 首先检查环境错误（Non-actionable）
    # ============================================

    # 模块导入错误
    if 'ModuleNotFoundError' in content or 'No module named' in content:
        return ("non_actionable", "module_not_found")
    if 'ImportError' in content and 'cannot import' in content_lower:
        return ("non_actionable", "import_error")

    # 文件系统错误
    if 'FileNotFoundError' in content or 'No such file or directory' in content:
        return ("non_actionable", "file_not_found")
    if 'PermissionError' in content or 'Permission denied' in content:
        return ("non_actionable", "permission_error")

    # 数据库错误（测试环境问题）
    if 'OperationalError' in content:
        return ("non_actionable", "db_operational_error")
    if 'table' in content_lower and 'already exists' in content_lower:
        return ("non_actionable", "db_table_exists")
    if 'database is locked' in content_lower:
        return ("non_actionable", "db_locked")

    # 编码错误
    if 'UnicodeDecodeError' in content or 'UnicodeEncodeError' in content:
        return ("non_actionable", "encoding_error")

    # 命令错误
    if 'command not found' in content_lower:
        return ("non_actionable", "command_not_found")

    # pytest 配置错误
    if 'pytest: error' in content_lower:
        return ("non_actionable", "pytest_config_error")
    if 'collected 0 items' in content_lower and 'error' in content_lower:
        return ("non_actionable", "pytest_collection_error")

    # Django 配置错误
    if 'ImproperlyConfigured' in content:
        return ("non_actionable", "django_config_error")
    if 'DJANGO_SETTINGS_MODULE' in content and 'define' in content_lower:
        return ("non_actionable", "django_settings_error")

    # 语法错误（脚本写错了）
    if 'SyntaxError' in content:
        return ("non_actionable", "syntax_error")
    if 'IndentationError' in content:
        return ("non_actionable", "indentation_error")

    # 连接错误
    if 'ConnectionError' in content or 'ConnectionRefusedError' in content:
        return ("non_actionable", "connection_error")
    if 'TimeoutError' in content:
        return ("non_actionable", "timeout_error")

    # ============================================
    # 2. 检查测试成功（Actionable）
    # ============================================

    # pytest 成功
    if re.search(r'\d+\s+passed', content_lower):
        if 'failed' not in content_lower and 'error' not in content_lower:
            return ("actionable", "pytest_passed")
        # 有 passed 也有 failed，仍然是 actionable（提供了有效信息）
        if 'failed' in content_lower:
            return ("actionable", "pytest_partial_pass")

    # unittest 成功
    if re.search(r'\bOK\b', content) and 'Ran' in content:
        return ("actionable", "unittest_ok")

    # 简单的成功标志
    if content.strip().endswith('OK'):
        return ("actionable", "test_ok")

    # ============================================
    # 3. 检查有效的测试失败（Actionable）
    # ============================================

    # pytest 失败（有具体信息）
    if 'FAILED' in content:
        return ("actionable", "pytest_failed")

    # AssertionError（测试断言失败）
    if 'AssertionError' in content:
        return ("actionable", "assertion_error")

    # 有 Traceback 且指向业务代码
    if 'Traceback (most recent call last)' in content:
        # 检查是否有业务代码路径（非 Python 标准库）
        if re.search(r'File "/testbed/', content) or re.search(r'File "\./[^"]+\.py"', content):
            # 常见的业务逻辑错误
            if any(err in content for err in ['TypeError', 'ValueError', 'KeyError',
                                               'AttributeError', 'IndexError', 'NameError',
                                               'RuntimeError', 'NotImplementedError']):
                return ("actionable", "runtime_error")

    # 有具体的测试输出（即使不是标准格式）
    if 'Expected' in content and ('Actual' in content or 'Got' in content or 'but' in content_lower):
        return ("actionable", "expectation_mismatch")

    # 有 assert 关键字
    if re.search(r'\bassert\b', content_lower) and ('false' in content_lower or 'fail' in content_lower):
        return ("actionable", "assert_failed")

    # ============================================
    # 4. 其他情况
    # ============================================

    # 有实质性输出（可能包含有用信息）
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    if len(lines) >= 3:
        # 检查是否有 "passed" 或 "failed" 等测试相关词汇
        if 'passed' in content_lower or 'failed' in content_lower:
            return ("actionable", "test_output")
        # 有输出但不确定是否有用
        return ("non_actionable", "unclear_output")

    # 输出太少，无法判断
    return ("non_actionable", "minimal_output")


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
class ReproductionInfo:
    cmd: str
    category: str
    reason: str
    output_preview: str


@dataclass
class InstancePairAnalysis:
    instance_id: str
    agent: str
    dataset: str
    outcome: str

    gt_files: Set[str] = field(default_factory=set)

    prohibited_edited_files: Set[str] = field(default_factory=set)
    prohibited_hit: bool = False
    prohibited_recall: float = 0.0

    unrestricted_edited_files: Set[str] = field(default_factory=set)
    unrestricted_reproduction_category: str = "none"
    unrestricted_hit: bool = False
    unrestricted_recall: float = 0.0

    reproductions: List[ReproductionInfo] = field(default_factory=list)


def analyze_claude_trace(traces: list) -> Tuple[Set[str], str, List[ReproductionInfo]]:
    edited_files = set()
    first_source_edit_found = False
    pending_exec = None
    reproductions = []

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
                            pending_exec = {"is_after_source_edit": first_source_edit_found, "cmd": cmd}

        elif entry_type == "user" and pending_exec:
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    result = item.get("content", "")
                    if isinstance(result, str):
                        if not pending_exec["is_after_source_edit"]:
                            category, reason = classify_reproduction_result_v5(result)
                            reproductions.append(ReproductionInfo(
                                cmd=pending_exec["cmd"],
                                category=category,
                                reason=reason,
                                output_preview=result[:500] if len(result) > 500 else result
                            ))
            pending_exec = None

    # 确定总体 reproduction category
    if not reproductions:
        overall_category = "none"
    else:
        has_actionable = any(r.category == "actionable" for r in reproductions)
        if has_actionable:
            overall_category = "actionable"
        else:
            overall_category = "non_actionable"

    return edited_files, overall_category, reproductions


def analyze_codex_trace(traces: list) -> Tuple[Set[str], str, List[ReproductionInfo]]:
    edited_files = set()
    first_source_edit_found = False
    reproductions = []

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
                        category, reason = classify_reproduction_result_v5(result)
                        reproductions.append(ReproductionInfo(
                            cmd=cmd,
                            category=category,
                            reason=reason,
                            output_preview=result[:500] if len(result) > 500 else result
                        ))

    if not reproductions:
        overall_category = "none"
    else:
        has_actionable = any(r.category == "actionable" for r in reproductions)
        if has_actionable:
            overall_category = "actionable"
        else:
            overall_category = "non_actionable"

    return edited_files, overall_category, reproductions


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
    print("交叉分析 v5：修复 Actionable 分类逻辑（合并 Success）")
    print("=" * 80)

    cases = load_outcome_cases()

    all_analyses: Dict[str, Dict[str, List[InstancePairAnalysis]]] = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    # 详细的分类统计
    reason_stats = {
        "claude_code": {},
        "codex": {}
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

                if agent == "claude_code":
                    prohibited_files, _, _ = analyze_claude_trace(prohibited_traces)
                else:
                    prohibited_files, _, _ = analyze_codex_trace(prohibited_traces)

                pair.prohibited_edited_files = prohibited_files
                pair.prohibited_hit, pair.prohibited_recall = calculate_localization_metrics(
                    prohibited_files, pair.gt_files
                )

                if agent == "claude_code":
                    unrestricted_files, repro_cat, repros = analyze_claude_trace(unrestricted_traces)
                else:
                    unrestricted_files, repro_cat, repros = analyze_codex_trace(unrestricted_traces)

                pair.unrestricted_edited_files = unrestricted_files
                pair.unrestricted_reproduction_category = repro_cat
                pair.unrestricted_hit, pair.unrestricted_recall = calculate_localization_metrics(
                    unrestricted_files, pair.gt_files
                )
                pair.reproductions = repros

                # 统计每次 reproduction 的分类原因
                for r in repros:
                    key = f"{r.category}:{r.reason}"
                    reason_stats[agent][key] = reason_stats[agent].get(key, 0) + 1

                all_analyses[agent][outcome].append(pair)

    # 输出分类统计
    print("\n" + "=" * 80)
    print("Reproduction 分类详细统计（按原因）")
    print("=" * 80)

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        print(f"\n{agent_label}:")

        # 按类别分组
        actionable_reasons = {}
        non_actionable_reasons = {}

        for key, count in sorted(reason_stats[agent].items(), key=lambda x: -x[1]):
            category, reason = key.split(":", 1)
            if category == "actionable":
                actionable_reasons[reason] = count
            else:
                non_actionable_reasons[reason] = count

        total = sum(reason_stats[agent].values())
        actionable_total = sum(actionable_reasons.values())
        non_actionable_total = sum(non_actionable_reasons.values())

        print(f"\n  Actionable ({actionable_total}, {actionable_total/total*100:.1f}%):")
        for reason, count in sorted(actionable_reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason}: {count}")

        print(f"\n  Non-actionable ({non_actionable_total}, {non_actionable_total/total*100:.1f}%):")
        for reason, count in sorted(non_actionable_reasons.items(), key=lambda x: -x[1]):
            print(f"    {reason}: {count}")

    generate_report(all_analyses, reason_stats)


def generate_report(all_analyses: Dict, reason_stats: Dict):
    lines = []
    lines.append("# 交叉分析 v5：修复 Actionable 分类逻辑（合并 Success）")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    lines.append("## 改进的分类逻辑")
    lines.append("")
    lines.append("**Actionable** (有效信息，可帮助定位):")
    lines.append("- 测试成功 (pytest passed, unittest OK)")
    lines.append("- 测试失败但有具体信息 (FAILED, AssertionError)")
    lines.append("- 业务代码运行时错误 (TypeError, ValueError 等，指向 /testbed/)")
    lines.append("")
    lines.append("**Non-actionable** (无效信息):")
    lines.append("- 环境错误 (ModuleNotFoundError, OperationalError, SyntaxError)")
    lines.append("- 配置错误 (Django settings, pytest config)")
    lines.append("- 无实质性输出")
    lines.append("")

    lines.append("---")
    lines.append("")

    # 分类统计表
    lines.append("## Reproduction 分类统计")
    lines.append("")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        lines.append(f"### {agent_label}")
        lines.append("")

        actionable_reasons = {}
        non_actionable_reasons = {}

        for key, count in reason_stats[agent].items():
            category, reason = key.split(":", 1)
            if category == "actionable":
                actionable_reasons[reason] = count
            else:
                non_actionable_reasons[reason] = count

        total = sum(reason_stats[agent].values())
        actionable_total = sum(actionable_reasons.values())
        non_actionable_total = sum(non_actionable_reasons.values())

        lines.append(f"| Category | Count | Percentage |")
        lines.append(f"|----------|------:|------------|")
        lines.append(f"| **Actionable** | {actionable_total} | {actionable_total/total*100:.1f}% |")
        lines.append(f"| **Non-actionable** | {non_actionable_total} | {non_actionable_total/total*100:.1f}% |")
        lines.append(f"| **Total** | {total} | 100% |")
        lines.append("")

    lines.append("---")
    lines.append("")

    json_results = {}

    for outcome in ["pp", "ff"]:
        outcome_label = "P→P" if outcome == "pp" else "F→F"
        lines.append(f"## {outcome_label} 案例分析")
        lines.append("")

        lines.append("| Agent | Repro Category | Count | Prohibited Hit | Unrestricted Hit | Δ Hit |")
        lines.append("|-------|----------------|------:|---------------:|-----------------:|------:|")

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

                prohibited_hits = sum(1 for p in cat_pairs if p.prohibited_hit)
                prohibited_hit_rate = prohibited_hits / len(cat_pairs)

                unrestricted_hits = sum(1 for p in cat_pairs if p.unrestricted_hit)
                unrestricted_hit_rate = unrestricted_hits / len(cat_pairs)

                delta_hit = unrestricted_hit_rate - prohibited_hit_rate

                cat_label = {
                    "actionable": "Actionable",
                    "non_actionable": "Non-actionable",
                    "none": "No Reproduction"
                }[repro_cat]

                delta_hit_str = f"{delta_hit*100:+.1f}pp"

                lines.append(f"| {agent_label} | {cat_label} | {len(cat_pairs)} | {prohibited_hit_rate*100:.1f}% | {unrestricted_hit_rate*100:.1f}% | **{delta_hit_str}** |")

                json_results[agent][outcome][repro_cat] = {
                    "count": len(cat_pairs),
                    "prohibited_hit_rate": prohibited_hit_rate,
                    "unrestricted_hit_rate": unrestricted_hit_rate,
                    "delta_hit": delta_hit
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
        non_actionable = pp_data.get("non_actionable", {})
        none = pp_data.get("none", {})

        if actionable:
            lines.append(f"**Actionable 组** ({actionable.get('count', 0)} instances):")
            lines.append(f"- Δ Hit: **{actionable.get('delta_hit', 0)*100:+.1f}pp**")
            lines.append("")

        if non_actionable:
            lines.append(f"**Non-actionable 组** ({non_actionable.get('count', 0)} instances):")
            lines.append(f"- Δ Hit: **{non_actionable.get('delta_hit', 0)*100:+.1f}pp**")
            lines.append("")

        if none:
            lines.append(f"**No Reproduction 组** ({none.get('count', 0)} instances):")
            lines.append(f"- Δ Hit: **{none.get('delta_hit', 0)*100:+.1f}pp**")
            lines.append("")

    # Save report
    report_file = ANALYSIS_DIR / "reproduction_localization_analysis_v5.md"
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\n报告已保存: {report_file}")

    # Save JSON
    json_file = ANALYSIS_DIR / "reproduction_localization_analysis_v5.json"
    with open(json_file, "w") as f:
        json.dump(json_results, f, indent=2)
    print(f"JSON 已保存: {json_file}")


if __name__ == "__main__":
    main()
