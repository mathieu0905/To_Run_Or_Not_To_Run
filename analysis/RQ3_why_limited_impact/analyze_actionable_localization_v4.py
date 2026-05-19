#!/usr/bin/env python3
"""
交叉分析 v4：修复 Actionable 分类逻辑

问题：
1. 环境错误列表不完整（缺少 OperationalError, SyntaxError 等）
2. 只要有 Traceback 就标记为 actionable 太宽泛
3. 环境错误的 Traceback 也包含 .py 路径，被误判为 actionable

改进：
1. 扩展环境错误列表
2. 更严格的 actionable 定义：只有真正有助于定位 bug 的信息才算 actionable
3. 环境错误的 Traceback 应该是 non-actionable
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


def classify_reproduction_result_v2(content: str) -> Tuple[str, str]:
    """
    改进的分类逻辑，返回 (category, reason)

    Category:
    - actionable: 包含真正有助于定位 bug 的信息（业务代码的 AssertionError、具体的失败信息）
    - env_error: 环境配置错误（模块缺失、数据库问题、权限等）
    - success: 测试成功通过
    - unclear: 有输出但不确定是否有用
    """
    content_lower = content.lower()

    # 1. 环境错误 - 扩展列表
    env_error_patterns = [
        # 模块导入错误
        ('No module named', 'module_not_found'),
        ('ModuleNotFoundError', 'module_not_found'),
        ('ImportError', 'import_error'),
        # 文件系统错误
        ('FileNotFoundError', 'file_not_found'),
        ('No such file or directory', 'file_not_found'),
        ('PermissionError', 'permission_error'),
        ('Permission denied', 'permission_error'),
        # 编码错误
        ('UnicodeDecodeError', 'encoding_error'),
        ('UnicodeEncodeError', 'encoding_error'),
        # 命令错误
        ('command not found', 'command_not_found'),
        ('not recognized as', 'command_not_found'),
        # 数据库错误（测试环境配置问题）
        ('OperationalError', 'db_error'),
        ('table already exists', 'db_error'),
        ('already exists', 'db_error'),
        ('database is locked', 'db_error'),
        ('no such table', 'db_error'),
        ('table .* doesn\'t exist', 'db_error'),
        # 语法错误（脚本写错）
        ('SyntaxError', 'syntax_error'),
        ('IndentationError', 'syntax_error'),
        # pytest 配置错误
        ('pytest: error', 'pytest_config_error'),
        ('no tests ran', 'no_tests'),
        ('collected 0 items', 'no_tests'),
        # 路径错误
        ('directory not found', 'path_error'),
        ('path does not exist', 'path_error'),
        # 连接错误
        ('ConnectionError', 'connection_error'),
        ('ConnectionRefusedError', 'connection_error'),
        ('TimeoutError', 'timeout_error'),
        # Django 特定
        ('django.core.exceptions.ImproperlyConfigured', 'django_config_error'),
        ('DJANGO_SETTINGS_MODULE', 'django_config_error'),
        # 其他常见环境问题
        ('OSError', 'os_error'),
        ('IOError', 'io_error'),
    ]

    for pattern, reason in env_error_patterns:
        if pattern in content or pattern.lower() in content_lower:
            return ("env_error", reason)

    # 2. 成功执行
    # pytest 成功
    if re.search(r'\d+ passed', content_lower) and 'failed' not in content_lower and 'error' not in content_lower:
        return ("success", "pytest_passed")
    # unittest 成功
    if content.strip().endswith('OK') or '\nOK\n' in content:
        return ("success", "unittest_ok")
    # 自定义测试成功
    if 'passed' in content_lower and 'failed' not in content_lower:
        return ("success", "test_passed")

    # 3. 真正的测试失败（有助于定位）
    has_traceback = 'Traceback (most recent call last)' in content
    has_assertion_error = 'AssertionError' in content
    has_failed = 'FAILED' in content or 'failed' in content_lower

    # pytest 风格的失败信息，包含具体的测试名和断言
    if has_failed and (has_assertion_error or 'assert' in content_lower):
        return ("actionable", "test_assertion_failed")

    # 有 Traceback 且是 AssertionError（真正的测试失败）
    if has_traceback and has_assertion_error:
        return ("actionable", "assertion_error_with_traceback")

    # 有具体的测试失败信息
    if re.search(r'FAILED .+::', content):
        return ("actionable", "pytest_failed")

    # 4. 有 Traceback 但不是 AssertionError（可能是代码运行时错误，需要区分）
    if has_traceback:
        # 检查是否是业务代码的运行时错误（如 TypeError, ValueError 等）
        runtime_errors = ['TypeError', 'ValueError', 'KeyError', 'AttributeError', 'IndexError', 'NameError']
        for err in runtime_errors:
            if err in content:
                # 需要进一步检查是否指向项目代码而非标准库
                # 简化处理：如果有 File 指向非标准库路径，认为是 actionable
                if re.search(r'File "/testbed/', content) or re.search(r'File "\./', content):
                    return ("actionable", f"runtime_error_{err.lower()}")

        # 其他 Traceback 可能是环境问题
        return ("unclear", "traceback_unknown")

    # 5. 输出了一些信息但不确定是否有用
    if len(content.strip()) > 50:
        return ("unclear", "has_output")

    # 6. 空输出或很少输出
    return ("unclear", "minimal_output")


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
    """单次 reproduction 的信息"""
    cmd: str
    category: str  # actionable, env_error, success, unclear
    reason: str
    output_preview: str


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
    unrestricted_reproduction_category: str = "none"  # actionable, non_actionable, none
    unrestricted_hit: bool = False
    unrestricted_recall: float = 0.0

    # 详细的 reproduction 信息
    reproductions: List[ReproductionInfo] = field(default_factory=list)


def analyze_claude_trace(traces: list) -> Tuple[Set[str], str, List[ReproductionInfo]]:
    """
    Analyze Claude Code trace.
    Returns: (edited_files, reproduction_category, reproductions)
    """
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
                            category, reason = classify_reproduction_result_v2(result)
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
        # 只有当至少有一次 actionable 执行时，才算 actionable
        has_actionable = any(r.category == "actionable" for r in reproductions)
        has_success = any(r.category == "success" for r in reproductions)

        if has_actionable or has_success:
            overall_category = "actionable"
        else:
            overall_category = "non_actionable"

    return edited_files, overall_category, reproductions


def analyze_codex_trace(traces: list) -> Tuple[Set[str], str, List[ReproductionInfo]]:
    """
    Analyze Codex trace.
    Returns: (edited_files, reproduction_category, reproductions)
    """
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
                        category, reason = classify_reproduction_result_v2(result)
                        reproductions.append(ReproductionInfo(
                            cmd=cmd,
                            category=category,
                            reason=reason,
                            output_preview=result[:500] if len(result) > 500 else result
                        ))

    # 确定总体 reproduction category
    if not reproductions:
        overall_category = "none"
    else:
        has_actionable = any(r.category == "actionable" for r in reproductions)
        has_success = any(r.category == "success" for r in reproductions)

        if has_actionable or has_success:
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
    print("交叉分析 v4：修复 Actionable 分类逻辑")
    print("=" * 80)

    cases = load_outcome_cases()

    all_analyses: Dict[str, Dict[str, List[InstancePairAnalysis]]] = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    # 统计分类情况
    category_stats = {
        "claude_code": {"actionable": 0, "env_error": 0, "success": 0, "unclear": 0},
        "codex": {"actionable": 0, "env_error": 0, "success": 0, "unclear": 0}
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
                    prohibited_files, _, _ = analyze_claude_trace(prohibited_traces)
                else:
                    prohibited_files, _, _ = analyze_codex_trace(prohibited_traces)

                pair.prohibited_edited_files = prohibited_files
                pair.prohibited_hit, pair.prohibited_recall = calculate_localization_metrics(
                    prohibited_files, pair.gt_files
                )

                # Analyze Unrestricted mode
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

                # 统计每次 reproduction 的分类
                for r in repros:
                    if r.category in category_stats[agent]:
                        category_stats[agent][r.category] += 1

                all_analyses[agent][outcome].append(pair)

    # 输出分类统计
    print("\n" + "=" * 80)
    print("Reproduction 分类统计（按次数）")
    print("=" * 80)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        stats = category_stats[agent]
        total = sum(stats.values())
        print(f"\n{agent_label}:")
        for cat, count in stats.items():
            pct = count / total * 100 if total > 0 else 0
            print(f"  {cat}: {count} ({pct:.1f}%)")

    generate_report(all_analyses)


def generate_report(all_analyses: Dict):
    lines = []
    lines.append("# 交叉分析 v4：修复 Actionable 分类逻辑后的结果")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    lines.append("## 改进的分类逻辑")
    lines.append("")
    lines.append("**Actionable** (真正有助于定位):")
    lines.append("- 测试成功 (pytest passed, unittest OK)")
    lines.append("- AssertionError + Traceback")
    lines.append("- 业务代码的运行时错误 (TypeError, ValueError 等，且指向 /testbed/)")
    lines.append("")
    lines.append("**Non-actionable** (环境错误或无用信息):")
    lines.append("- 模块导入错误 (ModuleNotFoundError, ImportError)")
    lines.append("- 文件系统错误 (FileNotFoundError, PermissionError)")
    lines.append("- 数据库错误 (OperationalError, table already exists)")
    lines.append("- 语法错误 (SyntaxError)")
    lines.append("- 配置错误 (pytest: error, DJANGO_SETTINGS_MODULE)")
    lines.append("- 其他无法提供定位信息的输出")
    lines.append("")

    lines.append("---")
    lines.append("")

    json_results = {}

    for outcome in ["pp", "ff"]:
        outcome_label = "P→P" if outcome == "pp" else "F→F"
        lines.append(f"## {outcome_label} 案例分析")
        lines.append("")

        lines.append("| Agent | Repro Category | Count | Prohibited Hit | Prohibited Recall | Unrestricted Hit | Unrestricted Recall | Δ Hit | Δ Recall |")
        lines.append("|-------|----------------|-------|----------------|-------------------|------------------|---------------------|-------|----------|")

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
                prohibited_avg_recall = sum(p.prohibited_recall for p in cat_pairs) / len(cat_pairs)

                unrestricted_hits = sum(1 for p in cat_pairs if p.unrestricted_hit)
                unrestricted_hit_rate = unrestricted_hits / len(cat_pairs)
                unrestricted_avg_recall = sum(p.unrestricted_recall for p in cat_pairs) / len(cat_pairs)

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
        non_actionable = pp_data.get("non_actionable", {})
        none = pp_data.get("none", {})

        if actionable:
            lines.append(f"**Actionable 组** ({actionable.get('count', 0)} 个 instance)：")
            lines.append(f"- Prohibited Hit: {actionable.get('prohibited_hit_rate', 0)*100:.1f}% → Unrestricted Hit: {actionable.get('unrestricted_hit_rate', 0)*100:.1f}% (**Δ {actionable.get('delta_hit', 0)*100:+.1f}pp**)")
            lines.append(f"- Prohibited Recall: {actionable.get('prohibited_avg_recall', 0)*100:.1f}% → Unrestricted Recall: {actionable.get('unrestricted_avg_recall', 0)*100:.1f}% (**Δ {actionable.get('delta_recall', 0)*100:+.1f}pp**)")
            lines.append("")

        if non_actionable:
            lines.append(f"**Non-actionable 组** ({non_actionable.get('count', 0)} 个 instance)：")
            lines.append(f"- Prohibited Hit: {non_actionable.get('prohibited_hit_rate', 0)*100:.1f}% → Unrestricted Hit: {non_actionable.get('unrestricted_hit_rate', 0)*100:.1f}% (**Δ {non_actionable.get('delta_hit', 0)*100:+.1f}pp**)")
            lines.append("")

        if none:
            lines.append(f"**No Reproduction 组** ({none.get('count', 0)} 个 instance)：")
            lines.append(f"- Prohibited Hit: {none.get('prohibited_hit_rate', 0)*100:.1f}% → Unrestricted Hit: {none.get('unrestricted_hit_rate', 0)*100:.1f}% (**Δ {none.get('delta_hit', 0)*100:+.1f}pp**)")
            lines.append("")

    lines.append("## 解读")
    lines.append("")
    lines.append("- **Δ > 0**: Unrestricted 模式定位更准 → 执行帮助了定位")
    lines.append("- **Δ ≈ 0**: 两种模式定位相当 → 执行对定位无显著影响")
    lines.append("- **Δ < 0**: Unrestricted 模式定位更差 → 执行可能干扰了定位")
    lines.append("")

    # Save report
    report_file = ANALYSIS_DIR / "actionable_localization_analysis_v4.md"
    with open(report_file, "w") as f:
        f.write("\n".join(lines))
    print(f"\n报告已保存: {report_file}")

    # Save JSON
    json_file = ANALYSIS_DIR / "actionable_localization_analysis_v4.json"
    with open(json_file, "w") as f:
        json.dump(json_results, f, indent=2)
    print(f"JSON 已保存: {json_file}")


if __name__ == "__main__":
    main()
