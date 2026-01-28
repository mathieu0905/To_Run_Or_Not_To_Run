#!/usr/bin/env python3
"""
RQ3 综合分析：为什么执行对结果影响有限？

统计所有相关信息并输出到一个 markdown 文件
"""

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
ANALYSIS_DIR = Path(__file__).parent


# ============================================================================
# 辅助函数
# ============================================================================

def normalize_path(path: str) -> str:
    """Normalize file path for comparison"""
    if path.startswith('./'):
        path = path[2:]
    if path.startswith('/'):
        path = path.lstrip('/')
    if path.startswith('testbed/'):
        path = path[8:]
    return path


def is_test_file(path: str) -> bool:
    """判断是否是测试文件"""
    path_lower = path.lower()
    if '/test_' in path_lower or '/tests/' in path_lower:
        return True
    if path_lower.endswith('_test.py'):
        return True
    if 'test' in path_lower.split('/')[-1]:
        return True
    if 'reproduce' in path_lower or 'debug' in path_lower:
        return True
    if path_lower.endswith('/script.py') or path_lower == 'script.py':
        return True
    return False


def is_test_execution(cmd: str) -> bool:
    """Check if command is a test execution"""
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


def classify_test_result(content: str) -> str:
    """分类测试结果: success, test_fail, env_error"""
    content_lower = content.lower()

    # 环境错误
    env_errors = ['No module named', 'ModuleNotFoundError', 'command not found',
                  'FileNotFoundError', 'No such file or directory',
                  'Permission denied', 'UnicodeDecodeError', 'encoding']
    for err in env_errors:
        if err in content or err.lower() in content_lower:
            return "env_error"

    # 明确的测试失败
    if 'FAILED' in content:
        return "test_fail"
    if 'AssertionError' in content:
        return "test_fail"
    if 'Traceback (most recent call last)' in content:
        return "test_fail"

    # 成功
    if 'passed' in content_lower and 'failed' not in content_lower:
        return "success"
    if content.strip().endswith('OK') or '\nOK' in content:
        return "success"

    # 默认为失败
    return "test_fail"


def extract_files_from_patch(patch_content: str) -> set:
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
    return files


def load_ground_truth_files(dataset: str, instance_id: str) -> set:
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


def load_trace(dataset: str, agent: str, mode: str, instance: str) -> list:
    """Load trace file"""
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


# ============================================================================
# 数据结构
# ============================================================================

@dataclass
class InstanceAnalysis:
    """单个实例的分析结果"""
    instance_id: str
    dataset: str
    agent: str
    mode: str

    # 编辑信息
    first_edit_file: str = ""
    first_edit_is_test: bool = False
    all_edited_files: Set[str] = field(default_factory=set)

    # Ground Truth
    gt_files: Set[str] = field(default_factory=set)

    # 定位指标
    first_edit_hit: bool = False  # 首次编辑命中 GT
    any_edit_hit: bool = False    # 任一编辑命中 GT
    recall: float = 0.0           # GT 文件召回率

    # Verification 分析
    has_verification: bool = False
    first_verif_result: str = ""  # success, test_fail, env_error
    total_verifications: int = 0
    any_verif_success: bool = False

    # Reproduction 分析
    has_reproduction: bool = False
    reproduction_count: int = 0

    # 对话统计
    total_turns: int = 0
    total_edits: int = 0
    total_test_runs: int = 0


# ============================================================================
# Trace 分析器
# ============================================================================

def analyze_claude_trace(traces: list, instance_id: str, dataset: str, mode: str) -> InstanceAnalysis:
    """分析 Claude Code trace"""
    analysis = InstanceAnalysis(
        instance_id=instance_id,
        dataset=dataset,
        agent="claude_code",
        mode=mode
    )

    first_edit_found = False
    first_verif_recorded = False
    pending_exec = None

    for entry in traces:
        entry_type = entry.get("type", "")
        analysis.total_turns += 1

        if entry_type == "assistant":
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_use":
                    tool_name = item.get("name", "")

                    # 文件编辑
                    if tool_name in ["Edit", "Write"]:
                        file_path = item.get("input", {}).get("file_path", "")
                        if file_path:
                            norm_path = normalize_path(file_path)
                            analysis.all_edited_files.add(norm_path)
                            analysis.total_edits += 1

                            if not first_edit_found:
                                first_edit_found = True
                                analysis.first_edit_file = norm_path
                                analysis.first_edit_is_test = is_test_file(norm_path)

                    # 测试执行
                    if tool_name == "Bash":
                        cmd = item.get("input", {}).get("command", "")
                        if is_test_execution(cmd):
                            pending_exec = {"is_after_edit": first_edit_found}
                            analysis.total_test_runs += 1

        elif entry_type == "user" and pending_exec:
            content = entry.get("message", {}).get("content", [])
            for item in content:
                if isinstance(item, dict) and item.get("type") == "tool_result":
                    result = item.get("content", "")
                    if isinstance(result, str):
                        result_type = classify_test_result(result)

                        if pending_exec["is_after_edit"]:
                            # Verification
                            analysis.has_verification = True
                            analysis.total_verifications += 1

                            if result_type == "success":
                                analysis.any_verif_success = True

                            if not first_verif_recorded:
                                analysis.first_verif_result = result_type
                                first_verif_recorded = True
                        else:
                            # Reproduction
                            analysis.has_reproduction = True
                            analysis.reproduction_count += 1

            pending_exec = None

    return analysis


def analyze_codex_trace(traces: list, instance_id: str, dataset: str, mode: str) -> InstanceAnalysis:
    """分析 Codex trace"""
    analysis = InstanceAnalysis(
        instance_id=instance_id,
        dataset=dataset,
        agent="codex",
        mode=mode
    )

    first_edit_found = False
    first_verif_recorded = False

    for entry in traces:
        entry_type = entry.get("type", "")
        analysis.total_turns += 1

        if entry_type == "item.completed":
            item = entry.get("item", {})
            item_type = item.get("type", "")

            # 文件编辑
            if item_type in ["file_edit", "file_change"]:
                # Get file path from changes or file_path
                changes = item.get("changes", [])
                for change in changes:
                    path = change.get("path", "")
                    if path:
                        norm_path = normalize_path(path)
                        analysis.all_edited_files.add(norm_path)
                        analysis.total_edits += 1

                        if not first_edit_found:
                            first_edit_found = True
                            analysis.first_edit_file = norm_path
                            analysis.first_edit_is_test = is_test_file(norm_path)

                file_path = item.get("file_path", "")
                if file_path:
                    norm_path = normalize_path(file_path)
                    analysis.all_edited_files.add(norm_path)
                    if not first_edit_found:
                        first_edit_found = True
                        analysis.first_edit_file = norm_path
                        analysis.first_edit_is_test = is_test_file(norm_path)

            # 测试执行
            if item_type == "command_execution":
                cmd = item.get("command", "")
                if "bash -lc" in cmd:
                    match = re.search(r"'([^']+)'[^']*$", cmd)
                    if match:
                        cmd = match.group(1)

                if is_test_execution(cmd):
                    analysis.total_test_runs += 1
                    result = item.get("aggregated_output", "")
                    exit_code = item.get("exit_code")

                    if exit_code is not None:
                        result_type = "success" if exit_code == 0 else "test_fail"
                    else:
                        result_type = classify_test_result(result)

                    if first_edit_found:
                        # Verification
                        analysis.has_verification = True
                        analysis.total_verifications += 1

                        if result_type == "success":
                            analysis.any_verif_success = True

                        if not first_verif_recorded:
                            analysis.first_verif_result = result_type
                            first_verif_recorded = True
                    else:
                        # Reproduction
                        analysis.has_reproduction = True
                        analysis.reproduction_count += 1

    return analysis


def compute_localization_metrics(analysis: InstanceAnalysis):
    """计算文件定位指标"""
    if not analysis.gt_files:
        return

    # 首次编辑命中
    if analysis.first_edit_file and analysis.first_edit_file in analysis.gt_files:
        analysis.first_edit_hit = True

    # 任一编辑命中
    if analysis.all_edited_files & analysis.gt_files:
        analysis.any_edit_hit = True

    # 召回率
    if analysis.gt_files:
        intersection = analysis.all_edited_files & analysis.gt_files
        analysis.recall = len(intersection) / len(analysis.gt_files)


# ============================================================================
# 数据加载
# ============================================================================

def load_outcome_cases() -> Dict:
    """加载 P→P 和 F→F 案例"""
    pp_file = PROJECT_ROOT / "analysis" / "pp_why_no_execution_needed.json"

    cases = {
        "claude_code": {"pp": [], "ff": []},
        "codex": {"pp": [], "ff": []}
    }

    # 加载 P→P 案例
    if pp_file.exists():
        with open(pp_file) as f:
            data = json.load(f)

        for item in data.get("results", []):
            instance = item["instance"]
            agent = item["agent"]
            group = item["group"]

            dataset = "swebenchlite" if "Lite" in group else "swebenchverified"
            cases[agent]["pp"].append((dataset, instance))

    # 找出 F→F 案例
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


# ============================================================================
# 主分析逻辑
# ============================================================================

def run_analysis() -> Dict:
    """运行所有分析"""
    cases = load_outcome_cases()

    results = {}

    for agent in ["claude_code", "codex"]:
        results[agent] = {}

        for outcome in ["pp", "ff"]:
            results[agent][outcome] = {}

            for mode in ["run_full", "run_free"]:
                mode_label = "unrestricted" if mode == "run_full" else "prohibited"

                analyses = []

                for dataset, instance in cases[agent][outcome]:
                    traces = load_trace(dataset, agent, mode, instance)
                    if not traces:
                        continue

                    # 分析 trace
                    if agent == "claude_code":
                        analysis = analyze_claude_trace(traces, instance, dataset, mode)
                    else:
                        analysis = analyze_codex_trace(traces, instance, dataset, mode)

                    # 加载 GT
                    analysis.gt_files = load_ground_truth_files(dataset, instance)

                    # 计算指标
                    compute_localization_metrics(analysis)

                    analyses.append(analysis)

                # 汇总统计
                results[agent][outcome][mode_label] = aggregate_stats(analyses)

    return results


def aggregate_stats(analyses: List[InstanceAnalysis]) -> Dict:
    """汇总统计"""
    if not analyses:
        return {"count": 0}

    stats = {
        "count": len(analyses),

        # 首次编辑分析
        "first_edit_is_test": sum(1 for a in analyses if a.first_edit_is_test),
        "first_edit_hit": sum(1 for a in analyses if a.first_edit_hit),

        # 最终编辑分析
        "any_edit_hit": sum(1 for a in analyses if a.any_edit_hit),
        "avg_recall": sum(a.recall for a in analyses) / len(analyses),

        # Verification 分析
        "has_verification": sum(1 for a in analyses if a.has_verification),
        "first_verif_success": sum(1 for a in analyses if a.first_verif_result == "success"),
        "first_verif_test_fail": sum(1 for a in analyses if a.first_verif_result == "test_fail"),
        "first_verif_env_error": sum(1 for a in analyses if a.first_verif_result == "env_error"),
        "any_verif_success": sum(1 for a in analyses if a.any_verif_success),

        # Reproduction 分析
        "has_reproduction": sum(1 for a in analyses if a.has_reproduction),

        # 行为统计
        "avg_turns": sum(a.total_turns for a in analyses) / len(analyses),
        "avg_edits": sum(a.total_edits for a in analyses) / len(analyses),
        "avg_test_runs": sum(a.total_test_runs for a in analyses) / len(analyses),
        "total_verifications": sum(a.total_verifications for a in analyses),
    }

    return stats


# ============================================================================
# Markdown 报告生成
# ============================================================================

def generate_markdown(results: Dict) -> str:
    """生成 markdown 报告"""
    lines = []

    # 标题
    lines.append("# RQ3 综合分析：为什么执行对结果影响有限？")
    lines.append("")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    lines.append("")

    # 目录
    lines.append("## 目录")
    lines.append("")
    lines.append("1. [数据概览](#1-数据概览)")
    lines.append("2. [RQ3.1 Verification 分析](#2-rq31-verification-分析)")
    lines.append("3. [RQ3.2 文件定位分析](#3-rq32-文件定位分析)")
    lines.append("4. [Agent 行为对比](#4-agent-行为对比)")
    lines.append("5. [核心发现与结论](#5-核心发现与结论)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 1. 数据概览
    lines.append("## 1. 数据概览")
    lines.append("")
    lines.append("### 案例分布")
    lines.append("")
    lines.append("| Agent | P→P (两者都成功) | F→F (两者都失败) |")
    lines.append("|-------|-----------------|-----------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp_count = results[agent]["pp"]["unrestricted"]["count"]
        ff_count = results[agent]["ff"]["unrestricted"]["count"]
        lines.append(f"| {agent_label} | {pp_count} | {ff_count} |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # 2. Verification 分析
    lines.append("## 2. RQ3.1 Verification 分析")
    lines.append("")
    lines.append("**问题**：首次编辑后的验证执行结果如何？能否说明验证是冗余的？")
    lines.append("")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        lines.append(f"### {agent_label}")
        lines.append("")

        # P→P 分析
        lines.append("#### P→P 案例（两种模式都成功）")
        lines.append("")

        pp_unres = results[agent]["pp"]["unrestricted"]
        pp_proh = results[agent]["pp"]["prohibited"]

        lines.append("| 指标 | Unrestricted | Prohibited |")
        lines.append("|------|-------------|------------|")

        if pp_unres["count"] > 0:
            # 有验证的实例
            has_verif_unres = pp_unres["has_verification"]
            has_verif_proh = pp_proh["has_verification"]
            lines.append(f"| 有验证执行的实例 | {has_verif_unres} ({has_verif_unres/pp_unres['count']*100:.1f}%) | {has_verif_proh} ({has_verif_proh/pp_proh['count']*100:.1f}%) |")

            # 首次验证结果分布
            if has_verif_unres > 0:
                success_pct = pp_unres["first_verif_success"] / has_verif_unres * 100
                fail_pct = pp_unres["first_verif_test_fail"] / has_verif_unres * 100
                env_pct = pp_unres["first_verif_env_error"] / has_verif_unres * 100
            else:
                success_pct = fail_pct = env_pct = 0

            if has_verif_proh > 0:
                success_pct_p = pp_proh["first_verif_success"] / has_verif_proh * 100
                fail_pct_p = pp_proh["first_verif_test_fail"] / has_verif_proh * 100
                env_pct_p = pp_proh["first_verif_env_error"] / has_verif_proh * 100
            else:
                success_pct_p = fail_pct_p = env_pct_p = 0

            lines.append(f"| 首次验证成功 | {pp_unres['first_verif_success']} ({success_pct:.1f}%) | {pp_proh['first_verif_success']} ({success_pct_p:.1f}%) |")
            lines.append(f"| 首次验证失败（测试） | {pp_unres['first_verif_test_fail']} ({fail_pct:.1f}%) | {pp_proh['first_verif_test_fail']} ({fail_pct_p:.1f}%) |")
            lines.append(f"| 首次验证失败（环境） | {pp_unres['first_verif_env_error']} ({env_pct:.1f}%) | {pp_proh['first_verif_env_error']} ({env_pct_p:.1f}%) |")

        lines.append("")

        # F→F 分析
        lines.append("#### F→F 案例（两种模式都失败）")
        lines.append("")

        ff_unres = results[agent]["ff"]["unrestricted"]
        ff_proh = results[agent]["ff"]["prohibited"]

        lines.append("| 指标 | Unrestricted | Prohibited |")
        lines.append("|------|-------------|------------|")

        if ff_unres["count"] > 0:
            has_verif_unres = ff_unres["has_verification"]
            has_verif_proh = ff_proh["has_verification"]
            lines.append(f"| 有验证执行的实例 | {has_verif_unres} ({has_verif_unres/ff_unres['count']*100:.1f}%) | {has_verif_proh} ({has_verif_proh/ff_proh['count']*100:.1f}%) |")

            if has_verif_unres > 0:
                any_success = ff_unres["any_verif_success"]
                lines.append(f"| 任一验证曾成功 | {any_success} ({any_success/has_verif_unres*100:.1f}%) | N/A |")

        lines.append("")

        # 解读
        lines.append("**解读**：")
        lines.append("")
        if pp_unres["count"] > 0 and pp_unres["has_verification"] > 0:
            success_rate = pp_unres["first_verif_success"] / pp_unres["has_verification"] * 100
            if success_rate < 30:
                lines.append(f"- P→P 案例中首次验证成功率仅 {success_rate:.1f}%，说明 Agent 需要多次迭代才能通过验证")
            else:
                lines.append(f"- P→P 案例中首次验证成功率为 {success_rate:.1f}%")

            env_rate = pp_unres["first_verif_env_error"] / pp_unres["has_verification"] * 100
            if env_rate > 20:
                lines.append(f"- {env_rate:.1f}% 的首次验证失败是环境错误（pytest 未安装等），不是代码问题")

        if ff_unres["count"] > 0 and ff_unres["has_verification"] > 0:
            any_success_rate = ff_unres["any_verif_success"] / ff_unres["has_verification"] * 100
            if any_success_rate > 50:
                lines.append(f"- F→F 案例中 {any_success_rate:.1f}% 验证曾成功，但最终仍失败 → Agent 测试与评估测试不一致")

        lines.append("")

    lines.append("---")
    lines.append("")

    # 3. 文件定位分析
    lines.append("## 3. RQ3.2 文件定位分析")
    lines.append("")
    lines.append("**问题**：Agent 能否准确定位需要修改的文件？执行是否帮助定位？")
    lines.append("")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        lines.append(f"### {agent_label}")
        lines.append("")

        # P→P 分析
        lines.append("#### P→P 案例")
        lines.append("")

        pp_unres = results[agent]["pp"]["unrestricted"]
        pp_proh = results[agent]["pp"]["prohibited"]

        lines.append("| 指标 | Unrestricted | Prohibited |")
        lines.append("|------|-------------|------------|")

        if pp_unres["count"] > 0:
            # 首次编辑是测试文件
            test_pct_u = pp_unres["first_edit_is_test"] / pp_unres["count"] * 100
            test_pct_p = pp_proh["first_edit_is_test"] / pp_proh["count"] * 100
            lines.append(f"| 首次编辑是测试文件 | {pp_unres['first_edit_is_test']} ({test_pct_u:.1f}%) | {pp_proh['first_edit_is_test']} ({test_pct_p:.1f}%) |")

            # 首次编辑命中
            hit_pct_u = pp_unres["first_edit_hit"] / pp_unres["count"] * 100
            hit_pct_p = pp_proh["first_edit_hit"] / pp_proh["count"] * 100
            lines.append(f"| 首次编辑命中 GT | {pp_unres['first_edit_hit']} ({hit_pct_u:.1f}%) | {pp_proh['first_edit_hit']} ({hit_pct_p:.1f}%) |")

            # 最终编辑命中
            any_hit_u = pp_unres["any_edit_hit"] / pp_unres["count"] * 100
            any_hit_p = pp_proh["any_edit_hit"] / pp_proh["count"] * 100
            lines.append(f"| 最终编辑命中 GT | {pp_unres['any_edit_hit']} ({any_hit_u:.1f}%) | {pp_proh['any_edit_hit']} ({any_hit_p:.1f}%) |")

            # 平均召回率
            lines.append(f"| 平均召回率 | {pp_unres['avg_recall']*100:.1f}% | {pp_proh['avg_recall']*100:.1f}% |")

            # Reproduction 使用
            repro_u = pp_unres["has_reproduction"]
            repro_p = pp_proh["has_reproduction"]
            lines.append(f"| 使用 Reproduction | {repro_u} ({repro_u/pp_unres['count']*100:.1f}%) | {repro_p} ({repro_p/pp_proh['count']*100:.1f}%) |")

        lines.append("")

        # 解读
        lines.append("**解读**：")
        lines.append("")
        if pp_unres["count"] > 0:
            test_diff = test_pct_u - test_pct_p
            if test_diff > 20:
                lines.append(f"- Unrestricted 模式 {test_pct_u:.1f}% 首次编辑是测试文件（vs Prohibited {test_pct_p:.1f}%）")
                lines.append("  - 这解释了首次编辑命中率的差异：Unrestricted 先写测试复现问题")

            if any_hit_u > 95 and any_hit_p > 95:
                lines.append(f"- 最终编辑命中率都很高（{any_hit_u:.1f}% vs {any_hit_p:.1f}%），说明定位能力相当")

            if repro_u / pp_unres["count"] < 0.2:
                lines.append(f"- 仅 {repro_u/pp_unres['count']*100:.1f}% 使用 Reproduction，说明问题描述足够清晰")

        lines.append("")

    lines.append("---")
    lines.append("")

    # 4. Agent 行为对比
    lines.append("## 4. Agent 行为对比")
    lines.append("")
    lines.append("### P→P 案例行为统计")
    lines.append("")
    lines.append("| Agent | Mode | 平均对话轮数 | 平均编辑次数 | 平均测试次数 |")
    lines.append("|-------|------|------------|------------|------------|")

    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        for mode_key, mode_label in [("unrestricted", "Unrestricted"), ("prohibited", "Prohibited")]:
            s = results[agent]["pp"][mode_key]
            if s["count"] > 0:
                lines.append(f"| {agent_label} | {mode_label} | {s['avg_turns']:.1f} | {s['avg_edits']:.1f} | {s['avg_test_runs']:.1f} |")

    lines.append("")

    # 对比分析
    lines.append("### 行为差异分析")
    lines.append("")

    cc_unres = results["claude_code"]["pp"]["unrestricted"]
    cc_proh = results["claude_code"]["pp"]["prohibited"]

    if cc_unres["count"] > 0 and cc_proh["count"] > 0:
        lines.append("**Claude Code**:")
        lines.append(f"- Unrestricted 平均 {cc_unres['avg_test_runs']:.1f} 次测试执行 vs Prohibited {cc_proh['avg_test_runs']:.1f} 次")
        lines.append(f"- Unrestricted 平均 {cc_unres['avg_edits']:.1f} 次编辑 vs Prohibited {cc_proh['avg_edits']:.1f} 次")

        if cc_unres['avg_test_runs'] > cc_proh['avg_test_runs'] * 3:
            lines.append(f"- **更多迭代并未带来更好结果**：两者都成功，但 Unrestricted 消耗更多资源")
        lines.append("")

    lines.append("---")
    lines.append("")

    # 5. 核心发现与结论
    lines.append("## 5. 核心发现与结论")
    lines.append("")
    lines.append("### 核心发现")
    lines.append("")
    lines.append("| # | 发现 | 证据 |")
    lines.append("|---|------|------|")

    findings = []

    finding_num = 1

    # 发现: 验证反馈有限 (两个 Agent)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp = results[agent]["pp"]["unrestricted"]
        if pp["count"] > 0 and pp["has_verification"] > 0:
            first_success = pp["first_verif_success"] / pp["has_verification"] * 100
            findings.append(f"| {finding_num} | **{agent_label}: 验证反馈价值有限** | P→P 首次验证成功率仅 {first_success:.1f}% |")
            finding_num += 1

    # 发现: 环境错误干扰 (Claude Code)
    cc_pp = results["claude_code"]["pp"]["unrestricted"]
    if cc_pp["count"] > 0 and cc_pp["has_verification"] > 0:
        env_rate = cc_pp["first_verif_env_error"] / cc_pp["has_verification"] * 100
        if env_rate > 10:
            findings.append(f"| {finding_num} | **Claude Code: 环境错误干扰验证** | {env_rate:.1f}% 首次验证是环境错误 |")
            finding_num += 1

    # 发现: 测试不一致 (两个 Agent)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        ff = results[agent]["ff"]["unrestricted"]
        if ff["count"] > 0 and ff["has_verification"] > 0:
            any_success = ff["any_verif_success"] / ff["has_verification"] * 100
            if any_success > 50:
                findings.append(f"| {finding_num} | **{agent_label}: 验证与评估不一致** | F→F 中 {any_success:.1f}% 验证曾成功但最终失败 |")
                finding_num += 1

    # 发现: 定位不需执行 (两个 Agent)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        pp = results[agent]["pp"]["unrestricted"]
        if pp["count"] > 0:
            repro_rate = pp["has_reproduction"] / pp["count"] * 100
            any_hit = pp["any_edit_hit"] / pp["count"] * 100
            if repro_rate < 30 and any_hit > 90:
                findings.append(f"| {finding_num} | **{agent_label}: 定位不需要执行** | 仅 {repro_rate:.1f}% 用 Reproduction，但 {any_hit:.1f}% 命中 GT |")
                finding_num += 1

    # 发现: 更多迭代不等于更好结果 (两个 Agent)
    for agent in ["claude_code", "codex"]:
        agent_label = "Claude Code" if agent == "claude_code" else "Codex"
        unres = results[agent]["pp"]["unrestricted"]
        proh = results[agent]["pp"]["prohibited"]
        if unres["count"] > 0 and proh["count"] > 0:
            if unres["avg_test_runs"] > proh["avg_test_runs"] + 1:
                findings.append(f"| {finding_num} | **{agent_label}: 更多迭代 ≠ 更好** | Unrestricted {unres['avg_test_runs']:.1f}次测试 vs Prohibited {proh['avg_test_runs']:.1f}次 |")
                finding_num += 1

    for f in findings:
        lines.append(f)

    lines.append("")
    lines.append("### 结论")
    lines.append("")
    lines.append("**为什么执行对结果影响有限？**")
    lines.append("")
    lines.append("1. **问题描述足够清晰**：Agent 可以通过静态分析定位文件，不需要动态执行复现")
    lines.append("2. **验证反馈有噪声**：环境错误和测试不一致降低了验证的价值")
    lines.append("3. **迭代可能带来过度修复**：更多编辑可能引入不必要的改动")
    lines.append("4. **核心能力是理解能力**：无论有无执行，Agent 的代码理解能力是成功的关键")
    lines.append("")
    lines.append("> **执行反馈是双刃剑**：它能帮助发现问题，但也可能误导 Agent 进行不必要的修改。")
    lines.append("> 当问题描述足够清晰时，\"一次性正确\"比\"试错迭代\"更有效。")
    lines.append("")

    return "\n".join(lines)


# ============================================================================
# 主函数
# ============================================================================

def main():
    print("=" * 80)
    print("RQ3 综合分析")
    print("=" * 80)

    print("\n正在分析...")
    results = run_analysis()

    print("\n生成报告...")
    md_content = generate_markdown(results)

    # 保存 markdown
    md_file = ANALYSIS_DIR / "rq3_comprehensive_report.md"
    with open(md_file, "w") as f:
        f.write(md_content)
    print(f"\n报告已保存: {md_file}")

    # 保存 JSON
    json_file = ANALYSIS_DIR / "rq3_comprehensive_data.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"数据已保存: {json_file}")

    print("\n完成！")


if __name__ == "__main__":
    main()
