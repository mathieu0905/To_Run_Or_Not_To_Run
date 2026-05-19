#!/usr/bin/env python3
"""
深入分析：为什么 Actionable reproduction 反而导致定位下降？

找出那些在 Prohibited 模式下定位成功，但在 Unrestricted 模式下（有 actionable reproduction）定位失败的 instance
"""

import json
import re
from pathlib import Path
from typing import Set, Tuple, List
from dataclasses import dataclass, field

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


def analyze_claude_trace(traces: list) -> Tuple[Set[str], str, List[str]]:
    """Returns: (edited_files, repro_category, reproduction_outputs)"""
    edited_files = set()
    first_source_edit_found = False
    pending_exec = None
    actionable_count = 0
    non_actionable_count = 0
    reproduction_outputs = []

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
                            category = classify_reproduction_result(result)
                            if category == "actionable":
                                actionable_count += 1
                            else:
                                non_actionable_count += 1
                            reproduction_outputs.append({
                                "cmd": pending_exec["cmd"],
                                "category": category,
                                "output_preview": result[:500] if len(result) > 500 else result
                            })
            pending_exec = None

    total_repro = actionable_count + non_actionable_count
    if total_repro == 0:
        repro_category = "none"
    elif actionable_count > 0:
        repro_category = "actionable"
    else:
        repro_category = "non_actionable"

    return edited_files, repro_category, reproduction_outputs


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


def load_pp_cases() -> List[Tuple[str, str]]:
    pp_file = PROJECT_ROOT / "analysis" / "pp_why_no_execution_needed.json"
    cases = []

    if pp_file.exists():
        with open(pp_file) as f:
            data = json.load(f)

        for item in data.get("results", []):
            if item["agent"] == "claude_code":
                instance = item["instance"]
                group = item["group"]
                dataset = "swebenchlite" if "Lite" in group else "swebenchverified"
                cases.append((dataset, instance))

    return cases


def main():
    print("=" * 80)
    print("深入分析：Actionable Reproduction 导致定位下降的案例")
    print("=" * 80)

    cases = load_pp_cases()
    print(f"\nClaude Code P→P 案例数: {len(cases)}")

    # 找出 Actionable 组中，Prohibited 成功但 Unrestricted 失败的案例
    degraded_cases = []
    improved_cases = []
    same_cases = []

    for dataset, instance in cases:
        prohibited_traces = load_trace(dataset, "claude_code", "run_free", instance)
        unrestricted_traces = load_trace(dataset, "claude_code", "run_full", instance)

        if not prohibited_traces or not unrestricted_traces:
            continue

        gt_files = load_ground_truth_files(dataset, instance)
        if not gt_files:
            continue

        # Analyze Prohibited
        prohibited_files, _, _ = analyze_claude_trace(prohibited_traces)
        prohibited_hit = len(gt_files & prohibited_files) > 0

        # Analyze Unrestricted
        unrestricted_files, repro_cat, repro_outputs = analyze_claude_trace(unrestricted_traces)
        unrestricted_hit = len(gt_files & unrestricted_files) > 0

        if repro_cat != "actionable":
            continue

        case_info = {
            "instance": instance,
            "dataset": dataset,
            "gt_files": list(gt_files),
            "prohibited_files": list(prohibited_files),
            "unrestricted_files": list(unrestricted_files),
            "prohibited_hit": prohibited_hit,
            "unrestricted_hit": unrestricted_hit,
            "reproduction_outputs": repro_outputs
        }

        if prohibited_hit and not unrestricted_hit:
            degraded_cases.append(case_info)
        elif not prohibited_hit and unrestricted_hit:
            improved_cases.append(case_info)
        else:
            same_cases.append(case_info)

    print(f"\n=== Actionable 组统计 ===")
    print(f"定位下降 (Prohibited成功, Unrestricted失败): {len(degraded_cases)}")
    print(f"定位提升 (Prohibited失败, Unrestricted成功): {len(improved_cases)}")
    print(f"定位不变: {len(same_cases)}")

    # 详细输出 degraded cases
    if degraded_cases:
        print("\n" + "=" * 80)
        print("=== 定位下降的案例详情 ===")
        print("=" * 80)

        for case in degraded_cases:
            print(f"\n--- {case['instance']} ---")
            print(f"Dataset: {case['dataset']}")
            print(f"Ground Truth 文件: {case['gt_files']}")
            print(f"Prohibited 编辑的文件: {case['prohibited_files']}")
            print(f"Unrestricted 编辑的文件: {case['unrestricted_files']}")
            print(f"Prohibited Hit: {case['prohibited_hit']}")
            print(f"Unrestricted Hit: {case['unrestricted_hit']}")

            print(f"\nReproduction 执行输出 ({len(case['reproduction_outputs'])} 次):")
            for i, repro in enumerate(case['reproduction_outputs']):
                print(f"\n  [{i+1}] Command: {repro['cmd'][:100]}...")
                print(f"      Category: {repro['category']}")
                print(f"      Output preview:")
                for line in repro['output_preview'].split('\n')[:10]:
                    print(f"        {line[:100]}")

    # 保存结果
    results = {
        "summary": {
            "total_actionable": len(degraded_cases) + len(improved_cases) + len(same_cases),
            "degraded": len(degraded_cases),
            "improved": len(improved_cases),
            "same": len(same_cases)
        },
        "degraded_cases": degraded_cases,
        "improved_cases": improved_cases
    }

    json_file = ANALYSIS_DIR / "actionable_degraded_analysis.json"
    with open(json_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n\n结果已保存: {json_file}")


if __name__ == "__main__":
    main()
