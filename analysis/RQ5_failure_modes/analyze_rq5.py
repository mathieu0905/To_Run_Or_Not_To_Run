#!/usr/bin/env python3
"""
RQ5: Failure Modes - 失败模式分析

研究问题: 不同执行 regime 会诱发哪些典型失败模式？
这些失败模式是否会增加或降低开发者后续调试与 review 负担？
"""

import sys
import json
import re
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from common.data_loader import (
    PROJECT_ROOT, DATASETS, MODE_ORDER,
    load_all_results, load_pass_rates, sort_modes
)


def analyze_trace_for_failures(trace_path: Path) -> dict:
    """分析 trace 文件中的失败模式"""
    failures = {
        "tool_errors": 0,        # 工具/环境错误
        "repeated_commands": 0,  # 循环试错（同一命令 > 3 次）
        "error_messages": [],    # 错误信息
        "command_history": [],   # 命令历史
    }

    command_counts = defaultdict(int)

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)

                # 检查工具错误
                if item.get("type") == "tool_result":
                    result = item.get("result", "")
                    if isinstance(result, str):
                        # 检查常见错误模式
                        error_patterns = [
                            r"error:", r"Error:", r"ERROR:",
                            r"exception", r"Exception",
                            r"failed", r"Failed", r"FAILED",
                            r"traceback", r"Traceback",
                            r"command not found",
                            r"No such file or directory",
                            r"Permission denied"
                        ]
                        for pattern in error_patterns:
                            if re.search(pattern, result):
                                failures["tool_errors"] += 1
                                # 提取错误信息（前 200 字符）
                                error_snippet = result[:200].replace("\n", " ")
                                failures["error_messages"].append(error_snippet)
                                break

                # Codex 格式
                if item.get("type") in ["item.started", "item.completed"]:
                    inner = item.get("item", {})
                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        if cmd:
                            simplified = re.sub(r'\s+', ' ', cmd.strip())
                            command_counts[simplified] += 1
                            failures["command_history"].append(cmd)

                # Claude Code 格式
                if item.get("type") == "assistant":
                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            if cmd:
                                simplified = re.sub(r'\s+', ' ', cmd.strip())
                                command_counts[simplified] += 1
                                failures["command_history"].append(cmd)

                        # 检查工具结果中的错误
                        if isinstance(c, dict) and c.get("type") == "tool_result":
                            result = c.get("content", "")
                            if isinstance(result, str):
                                error_patterns = [
                                    r"error:", r"Error:", r"ERROR:",
                                    r"exception", r"Exception",
                                    r"failed", r"Failed", r"FAILED"
                                ]
                                for pattern in error_patterns:
                                    if re.search(pattern, result):
                                        failures["tool_errors"] += 1
                                        break

            except:
                continue

    # 统计循环试错
    for cmd, count in command_counts.items():
        if count > 3:
            failures["repeated_commands"] += 1

    return failures


def analyze_patch_for_drift(patch_path: Path, instance_id: str) -> dict:
    """分析 patch 是否存在修偏 drift"""
    drift = {
        "files_modified": 0,
        "lines_added": 0,
        "lines_removed": 0,
        "potentially_unrelated": False
    }

    if not patch_path.exists():
        return drift

    try:
        content = patch_path.read_text()

        # 统计修改的文件数
        file_matches = re.findall(r'^diff --git', content, re.MULTILINE)
        drift["files_modified"] = len(file_matches)

        # 统计添加和删除的行数
        drift["lines_added"] = len(re.findall(r'^\+[^+]', content, re.MULTILINE))
        drift["lines_removed"] = len(re.findall(r'^-[^-]', content, re.MULTILINE))

        # 检查是否修改了可能不相关的文件（如 test 文件、config 文件等）
        # 这是一个简单的启发式规则
        if drift["files_modified"] > 5:
            drift["potentially_unrelated"] = True

    except:
        pass

    return drift


def load_evaluation_results() -> dict:
    """加载评估结果"""
    eval_results = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    sb_cli_reports_dir = PROJECT_ROOT / "sb-cli-reports"
    if not sb_cli_reports_dir.exists():
        return eval_results

    for report_file in sb_cli_reports_dir.glob("*.json"):
        try:
            report = json.loads(report_file.read_text(encoding="utf-8"))
            filename = report_file.stem

            # 确定数据集
            if "lite" in filename.lower():
                dataset = "swebenchlite"
            elif "verified" in filename.lower():
                dataset = "swebenchverified"
            else:
                continue

            # 确定 agent 和 mode
            for agent in ["claude_code", "codex"]:
                if agent in filename:
                    for mode in MODE_ORDER:
                        if mode in filename:
                            resolved_ids = report.get("resolved_ids", [])
                            for instance_id in resolved_ids:
                                eval_results[dataset][agent][mode][instance_id] = True
                            break
                    break
        except:
            continue

    return eval_results


def find_interesting_cases(results: dict, eval_results: dict) -> dict:
    """找出有趣的案例（free 成功 full 失败，或 full 成功 free 失败）"""
    cases = {
        "free_success_full_fail": [],
        "full_success_free_fail": [],
    }

    for dataset in results:
        for agent in results[dataset]:
            free_mode = results[dataset][agent].get("run_free", {})
            full_mode = results[dataset][agent].get("run_full", {})

            free_resolved = eval_results.get(dataset, {}).get(agent, {}).get("run_free", {})
            full_resolved = eval_results.get(dataset, {}).get(agent, {}).get("run_full", {})

            # 找出所有实例
            all_instances = set(free_mode.keys()) | set(full_mode.keys())

            for instance_id in all_instances:
                free_success = free_resolved.get(instance_id, False)
                full_success = full_resolved.get(instance_id, False)

                if free_success and not full_success:
                    cases["free_success_full_fail"].append({
                        "dataset": dataset,
                        "agent": agent,
                        "instance_id": instance_id
                    })
                elif full_success and not free_success:
                    cases["full_success_free_fail"].append({
                        "dataset": dataset,
                        "agent": agent,
                        "instance_id": instance_id
                    })

    return cases


def generate_failure_mode_distribution(results: dict, pass_rates: dict) -> str:
    """生成失败模式分布表"""
    lines = []
    lines.append("## 失败模式分布")
    lines.append("")

    for dataset, dataset_name in DATASETS.items():
        if dataset not in results:
            continue

        lines.append(f"### {dataset_name}")
        lines.append("")
        lines.append("| Agent | Mode | Total | Resolved | Failed | Tool Errors | Repeated Cmds |")
        lines.append("|-------|------|-------|----------|--------|-------------|---------------|")

        for agent in sorted(results[dataset].keys()):
            modes = results[dataset][agent]
            pr_modes = pass_rates.get(dataset, {}).get(agent, {})

            for mode in sort_modes(modes.keys()):
                instances = modes[mode]
                n = len(instances)

                # 获取 pass rate
                pr = pr_modes.get(mode, {})
                resolved = pr.get("resolved", 0)
                failed = n - resolved

                # 统计失败模式
                total_tool_errors = 0
                total_repeated = 0

                for instance_id, data in instances.items():
                    # 分析 trace
                    trace_path = PROJECT_ROOT / "output" / dataset / agent / mode / instance_id / "trace.jsonl"
                    if trace_path.exists():
                        failures = analyze_trace_for_failures(trace_path)
                        total_tool_errors += failures["tool_errors"]
                        total_repeated += failures["repeated_commands"]

                avg_errors = total_tool_errors / n if n > 0 else 0
                avg_repeated = total_repeated / n if n > 0 else 0

                lines.append(f"| {agent} | {mode} | {n} | {resolved} | {failed} | {avg_errors:.1f} | {avg_repeated:.1f} |")

        lines.append("")

    return "\n".join(lines)


def generate_failure_type_analysis(results: dict) -> str:
    """生成失败类型分析"""
    lines = []
    lines.append("## 失败类型分析")
    lines.append("")

    lines.append("### 失败模式分类")
    lines.append("")
    lines.append("| 类别 | 描述 | 识别规则 |")
    lines.append("|------|------|----------|")
    lines.append("| 工具/环境错误 | 命令执行失败、文件不存在等 | trace 中包含 error, exception, failed |")
    lines.append("| 循环试错 | 同一命令重复执行多次 | 同一命令执行 > 3 次 |")
    lines.append("| 修偏 drift | 修改了不相关的文件 | patch 修改文件数 > 5 |")
    lines.append("| 无效 patch | 生成了 patch 但未通过测试 | has_patch=True 但 resolved=False |")
    lines.append("")

    return "\n".join(lines)


def generate_case_comparison(cases: dict) -> str:
    """生成案例对比"""
    lines = []
    lines.append("## 典型案例对比")
    lines.append("")

    lines.append("### Run-Free 成功但 Run-Full 失败的案例")
    lines.append("")
    if cases["free_success_full_fail"]:
        lines.append("| Dataset | Agent | Instance ID |")
        lines.append("|---------|-------|-------------|")
        for case in cases["free_success_full_fail"][:10]:  # 最多显示 10 个
            lines.append(f"| {case['dataset']} | {case['agent']} | {case['instance_id']} |")
        lines.append("")
        lines.append(f"共 {len(cases['free_success_full_fail'])} 个案例")
    else:
        lines.append("无")
    lines.append("")

    lines.append("### Run-Full 成功但 Run-Free 失败的案例")
    lines.append("")
    if cases["full_success_free_fail"]:
        lines.append("| Dataset | Agent | Instance ID |")
        lines.append("|---------|-------|-------------|")
        for case in cases["full_success_free_fail"][:10]:  # 最多显示 10 个
            lines.append(f"| {case['dataset']} | {case['agent']} | {case['instance_id']} |")
        lines.append("")
        lines.append(f"共 {len(cases['full_success_free_fail'])} 个案例")
    else:
        lines.append("无")
    lines.append("")

    return "\n".join(lines)


def generate_key_findings(cases: dict, results: dict, pass_rates: dict) -> str:
    """生成关键发现"""
    lines = []
    lines.append("## 关键发现")
    lines.append("")

    # 统计案例数量
    free_win = len(cases["free_success_full_fail"])
    full_win = len(cases["full_success_free_fail"])

    lines.append("### 1. 案例统计")
    lines.append("")
    lines.append(f"- Run-Free 成功但 Run-Full 失败: **{free_win}** 个案例")
    lines.append(f"- Run-Full 成功但 Run-Free 失败: **{full_win}** 个案例")
    lines.append(f"- 净差异: **{full_win - free_win}** 个案例（Run-Full 优势）")
    lines.append("")

    lines.append("### 2. 失败模式分析")
    lines.append("")
    lines.append("**Run-Full 模式的典型失败模式:**")
    lines.append("- 循环试错：反复执行同一测试命令，期望不同结果")
    lines.append("- 过度修改：修改了不必要的文件，引入新问题")
    lines.append("- 工具错误：执行过程中遇到环境问题")
    lines.append("")
    lines.append("**Run-Free 模式的典型失败模式:**")
    lines.append("- 推理错误：对问题理解不准确")
    lines.append("- 缺少验证：无法确认修复是否正确")
    lines.append("- 环境假设：对运行环境的假设不正确")
    lines.append("")

    lines.append("### 3. 结论")
    lines.append("")
    if full_win > free_win:
        lines.append(f"- Run-Full 模式在 **{full_win - free_win}** 个案例上优于 Run-Free")
        lines.append("- 执行反馈在某些情况下确实有帮助")
    elif free_win > full_win:
        lines.append(f"- Run-Free 模式在 **{free_win - full_win}** 个案例上优于 Run-Full")
        lines.append("- 执行反馈有时会误导 Agent")
    else:
        lines.append("- 两种模式各有优劣，没有明显的整体优势")

    lines.append("- 不同失败模式需要不同的应对策略")
    lines.append("- 开发者 review 负担取决于失败模式类型")

    return "\n".join(lines)


def main():
    print("正在加载数据...")

    results = load_all_results()
    pass_rates = load_pass_rates()
    eval_results = load_evaluation_results()

    if not results:
        print("错误: 无法加载实验结果数据")
        return

    print("正在分析失败模式...")
    cases = find_interesting_cases(results, eval_results)

    output_dir = Path(__file__).parent
    data_file = output_dir / "data_rq5.md"

    content = []
    content.append("# RQ5: Failure Modes - 数据表格")
    content.append("")
    content.append("失败模式分析数据。")
    content.append("")
    content.append(generate_failure_type_analysis(results))
    content.append(generate_failure_mode_distribution(results, pass_rates))
    content.append(generate_case_comparison(cases))
    content.append(generate_key_findings(cases, results, pass_rates))

    with open(data_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"数据已保存到: {data_file}")


if __name__ == "__main__":
    main()
