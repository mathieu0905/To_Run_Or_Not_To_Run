#!/usr/bin/env python3
"""共享数据加载工具 - 为各 RQ 分析脚本提供统一的数据加载接口"""

import json
import re
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 高成本执行模式（测试框架）
HIGH_COST_PATTERNS = [
    "pytest", "python -m pytest", "python -m unittest",
    "manage.py test", "python manage.py test",
    "tox", "nose", "nosetests",
    "python -m django test",
    "python tests/runtests.py"
]

# 低成本执行模式（Python 脚本）
PYTHON_SCRIPT_PATTERN = re.compile(r'\bpython\s+[a-zA-Z_][\w/\-]*\.py\b')

# 排除的 agent（GLM）
EXCLUDED_AGENTS = ["claude_code_glm"]

# 数据集映射
DATASETS = {
    "swebenchlite": "SWE-bench Lite",
    "swebenchverified": "SWE-bench Verified"
}

# Mode 顺序（用于排序）
MODE_ORDER = ["run_free", "run_less_k1", "run_less_k3", "run_cost", "run_full"]


def count_tokens_and_execs(trace_path: Path) -> Dict:
    """从 trace.jsonl 统计 token、执行次数、交互轮数和时间"""
    tokens = {"input": 0, "output": 0}
    exec_count = 0
    high_cost_exec = 0
    low_cost_exec = 0
    turns = 0
    duration_ms = 0
    max_item_id = -1

    # 收集所有执行的命令
    commands = []

    prompt_path = trace_path.parent / "prompt.txt"

    with open(trace_path) as f:
        for line in f:
            try:
                item = json.loads(line)

                # Codex 格式
                if item.get("type") == "turn.completed":
                    usage = item.get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)

                if item.get("type") in ["item.started", "item.completed"]:
                    inner = item.get("item", {})
                    item_id = inner.get("id", "")
                    if item_id.startswith("item_"):
                        try:
                            id_num = int(item_id.split("_")[1])
                            max_item_id = max(max_item_id, id_num)
                        except:
                            pass

                    if inner.get("type") == "command_execution":
                        cmd = inner.get("command", "")
                        commands.append(cmd)
                        if any(p in cmd for p in HIGH_COST_PATTERNS):
                            high_cost_exec += 1
                            exec_count += 1
                        elif PYTHON_SCRIPT_PATTERN.search(cmd):
                            low_cost_exec += 1
                            exec_count += 1

                # Claude Code 格式
                if item.get("type") == "assistant":
                    usage = item.get("message", {}).get("usage", {})
                    tokens["input"] += usage.get("input_tokens", 0)
                    tokens["output"] += usage.get("output_tokens", 0)
                    if usage.get("input_tokens", 0) > 0:
                        turns += 1

                    content = item.get("message", {}).get("content", [])
                    for c in content:
                        if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                            cmd = c.get("input", {}).get("command", "")
                            commands.append(cmd)
                            if any(p in cmd for p in HIGH_COST_PATTERNS):
                                high_cost_exec += 1
                                exec_count += 1
                            elif PYTHON_SCRIPT_PATTERN.search(cmd):
                                low_cost_exec += 1
                                exec_count += 1

                if item.get("type") == "result":
                    duration_ms = item.get("duration_ms", 0)
            except:
                continue

    if max_item_id >= 0:
        turns = max_item_id + 1

    # 备用时间计算
    if duration_ms == 0 and prompt_path.exists() and trace_path.exists():
        try:
            prompt_mtime = prompt_path.stat().st_mtime
            trace_mtime = trace_path.stat().st_mtime
            duration_sec = trace_mtime - prompt_mtime
            if duration_sec > 0:
                duration_ms = int(duration_sec * 1000)
        except:
            pass

    return {
        "tokens": tokens,
        "exec_count": exec_count,
        "high_cost_exec": high_cost_exec,
        "low_cost_exec": low_cost_exec,
        "turns": turns,
        "duration_ms": duration_ms,
        "commands": commands
    }


def check_patch(patch_path: Path) -> bool:
    """检查 patch 是否非空"""
    if not patch_path.exists():
        return False
    with open(patch_path) as f:
        content = f.read().strip()
    return len(content) > 0


def load_sb_cli_report(sb_cli_reports_dir: Path, dataset: str, agent: str, mode: str) -> Optional[Dict]:
    """从 sb-cli-reports 目录加载评估报告"""
    if not sb_cli_reports_dir.exists():
        return None

    if "lite" in dataset.lower():
        dataset_pattern = "swe-bench_lite"
    elif "verified" in dataset.lower():
        dataset_pattern = "swe-bench_verified"
    else:
        dataset_pattern = "*"

    patterns = [
        f"{dataset_pattern}*{agent}*{mode}*.json",
        f"{dataset_pattern}*{agent}_{mode}.json",
        f"{dataset_pattern}*{agent}__{mode}.json",
    ]

    for pattern in patterns:
        matches = list(sb_cli_reports_dir.glob(pattern))
        if matches:
            try:
                return json.loads(matches[0].read_text(encoding="utf-8"))
            except:
                pass
    return None


def load_all_results(output_dir: Path = None, exclude_glm: bool = True) -> Dict:
    """
    加载所有实验结果

    返回结构:
    {
        "swebenchlite": {
            "claude_code": {
                "run_free": {
                    "instance_id": {...},
                    ...
                },
                ...
            },
            ...
        },
        ...
    }
    """
    if output_dir is None:
        output_dir = PROJECT_ROOT / "output"

    results = {}

    for dataset_dir in output_dir.iterdir():
        if not dataset_dir.is_dir():
            continue
        dataset = dataset_dir.name
        results[dataset] = {}

        for agent_dir in dataset_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            agent = agent_dir.name

            if exclude_glm and agent in EXCLUDED_AGENTS:
                continue

            results[dataset][agent] = {}

            for mode_dir in agent_dir.iterdir():
                if not mode_dir.is_dir():
                    continue
                mode = mode_dir.name
                results[dataset][agent][mode] = {}

                for instance_dir in mode_dir.iterdir():
                    if not instance_dir.is_dir():
                        continue
                    instance = instance_dir.name

                    trace_path = instance_dir / "trace.jsonl"
                    patch_path = instance_dir / "patch.diff"

                    if trace_path.exists():
                        data = count_tokens_and_execs(trace_path)
                        data["has_patch"] = check_patch(patch_path)
                        data["instance_id"] = instance
                        results[dataset][agent][mode][instance] = data

    return results


def load_pass_rates(sb_cli_reports_dir: Path = None) -> Dict:
    """
    加载所有 pass rate 数据

    返回结构:
    {
        "swebenchlite": {
            "claude_code": {
                "run_free": {"resolved": 63, "total": 100},
                ...
            },
            ...
        },
        ...
    }
    """
    if sb_cli_reports_dir is None:
        sb_cli_reports_dir = PROJECT_ROOT / "sb-cli-reports"

    pass_rates = defaultdict(lambda: defaultdict(dict))

    if not sb_cli_reports_dir.exists():
        return pass_rates

    for report_file in sb_cli_reports_dir.glob("*.json"):
        try:
            report = json.loads(report_file.read_text(encoding="utf-8"))

            # 解析文件名获取 dataset, agent, mode
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
                            resolved = report.get("resolved_instances", 0)
                            completed = report.get("completed_instances", 0)
                            pass_rates[dataset][agent][mode] = {
                                "resolved": resolved,
                                "total": completed
                            }
                            break
                    break
        except:
            continue

    return pass_rates


def get_aggregated_stats(results: Dict) -> Dict:
    """
    计算聚合统计数据

    返回结构:
    {
        "swebenchlite": {
            "claude_code": {
                "run_free": {
                    "n": 100,
                    "avg_input_tokens": 66942,
                    "avg_output_tokens": 2103,
                    "avg_total_tokens": 69046,
                    "avg_turns": 35.2,
                    "avg_high_cost_exec": 0.6,
                    "avg_low_cost_exec": 0.2,
                    "avg_time_sec": 530.7,
                    "patch_count": 100
                },
                ...
            },
            ...
        },
        ...
    }
    """
    stats = {}

    for dataset, agents in results.items():
        stats[dataset] = {}
        for agent, modes in agents.items():
            stats[dataset][agent] = {}
            for mode, instances in modes.items():
                n = len(instances)
                if n == 0:
                    continue

                # 只统计有 patch 的实例
                patched = {k: v for k, v in instances.items() if v.get("has_patch", False)}
                patches = len(patched)

                if patches == 0:
                    continue

                total_input = sum(v["tokens"]["input"] for v in patched.values())
                total_output = sum(v["tokens"]["output"] for v in patched.values())
                total_high_cost = sum(v["high_cost_exec"] for v in patched.values())
                total_low_cost = sum(v["low_cost_exec"] for v in patched.values())
                total_turns = sum(v["turns"] for v in patched.values())
                total_duration = sum(v["duration_ms"] for v in patched.values())

                stats[dataset][agent][mode] = {
                    "n": n,
                    "avg_input_tokens": total_input // patches,
                    "avg_output_tokens": total_output // patches,
                    "avg_total_tokens": (total_input + total_output) // patches,
                    "avg_turns": total_turns / patches,
                    "avg_high_cost_exec": total_high_cost / patches,
                    "avg_low_cost_exec": total_low_cost / patches,
                    "avg_time_sec": total_duration / patches / 1000,
                    "patch_count": patches
                }

    return stats


def sort_modes(modes: List[str]) -> List[str]:
    """按预定义顺序排序 modes"""
    return sorted(modes, key=lambda x: MODE_ORDER.index(x) if x in MODE_ORDER else len(MODE_ORDER))
