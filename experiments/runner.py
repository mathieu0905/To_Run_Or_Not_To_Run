#!/usr/bin/env python3
"""
实验运行器：测试 Run-Free / Run-Less / Run-Full 三种模式
"""
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional
from datasets import load_dataset

from agent_caller import AgentCaller, AgentTrace
from prompt_builder import PromptBuilder


PROJ_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJ_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ExperimentResult:
    """实验结果"""
    instance_id: str
    mode: str  # run_free, run_less, run_full
    k: Optional[int]  # run_less 的执行次数限制
    patch: str
    tokens_used: int
    exec_count: int
    duration_sec: float
    success: bool
    error: str = ""
    agent_type: str = "claude_code"


def get_instance_info(instance_id: str, dataset_name: str = "princeton-nlp/SWE-bench_Lite") -> dict:
    """从 SWE-bench 数据集获取实例信息"""
    dataset = load_dataset(dataset_name, split="test")
    for item in dataset:
        if item["instance_id"] == instance_id:
            return item
    raise ValueError(f"Instance {instance_id} not found in dataset {dataset_name}")


def extract_patch(output: str) -> str:
    """从 agent 输出中提取 git diff 格式的补丁"""
    lines = output.split("\n")
    patch_lines = []
    in_patch = False

    for line in lines:
        # 检测 diff 开始标记
        if line.startswith("diff --git") or line.startswith("---") or line.startswith("+++"):
            in_patch = True

        if in_patch:
            patch_lines.append(line)

            # 如果已经收集了足够的内容，可以提前结束
            if line.startswith("@@") and len(patch_lines) > 10:
                # 继续收集直到下一个文件或结束
                continue

    return "\n".join(patch_lines) if patch_lines else ""


def run_experiment(
    instance_id: str,
    mode: str,
    k: int = 2,
    agent_type: str = "claude_code",
    timeout: int = 600,
    dataset_name: str = "princeton-nlp/SWE-bench_Lite"
) -> ExperimentResult:
    """
    运行单个实验

    Args:
        instance_id: SWE-bench 实例 ID
        mode: 执行模式 (run_free, run_less, run_full)
        k: run_less 模式的执行次数限制
        agent_type: agent 类型 (claude_code, codex)
        timeout: 超时时间（秒）

    Returns:
        ExperimentResult 对象
    """
    # 1. 获取实例信息
    print(f"Loading instance: {instance_id}")
    instance = get_instance_info(instance_id, dataset_name)

    # 确定数据集目录名称
    dataset_dir = "swebenchlite" if "Lite" in dataset_name else "swebenchverified"

    # 构建模式目录名（run_less 需要包含 k 值）
    mode_dir = f"{mode}_k{k}" if mode == "run_less" else mode

    # 创建输出目录：output/{dataset}/{agent}/{mode_dir}/{instance_id}/
    instance_output_dir = OUTPUT_DIR / dataset_dir / agent_type / mode_dir / instance_id
    instance_output_dir.mkdir(parents=True, exist_ok=True)

    # 2. 构建 prompt
    print(f"Building prompt for mode: {mode}" + (f" (k={k})" if mode == "run_less" else ""))
    prompt = PromptBuilder.build_prompt(instance, mode, k)

    # 保存 prompt 到实例目录
    prompt_file = instance_output_dir / "prompt.txt"
    prompt_file.write_text(prompt, encoding="utf-8")
    print(f"Prompt saved to: {prompt_file}")

    # 3. 调用 agent（trace 实时写入到输出目录）
    print(f"Calling {agent_type} agent (timeout={timeout}s)...")
    trace_file = instance_output_dir / "trace.jsonl"
    caller = AgentCaller(agent_type=agent_type, instance_id=instance_id)
    trace: AgentTrace = caller.call(prompt, timeout=timeout, trace_output_path=str(trace_file))
    print(f"Trace saved to: {trace_file}")

    # 4. 读取 git diff 生成的补丁（由 agent_caller 在容器内执行 git diff 生成）
    patch_file = instance_output_dir / "patch.diff"
    patch = patch_file.read_text(encoding='utf-8')
    print(f"Patch loaded from git diff: {patch_file}")

    # 5. 构建结果
    result = ExperimentResult(
        instance_id=instance_id,
        mode=mode,
        k=k if mode == "run_less" else None,
        patch=patch,
        tokens_used=trace.tokens_used,
        exec_count=trace.exec_count,
        duration_sec=trace.duration_sec,
        success=bool(patch) and not trace.error,
        error=trace.error or "",
        agent_type=agent_type
    )

    return result


def save_result(result: ExperimentResult, dataset_name: str = "princeton-nlp/SWE-bench_Lite"):
    """保存实验结果到 JSON 文件"""
    # 确定数据集目录名称
    dataset_dir = "swebenchlite" if "Lite" in dataset_name else "swebenchverified"

    # 构建输出目录路径
    instance_output_dir = OUTPUT_DIR / dataset_dir / result.instance_id
    instance_output_dir.mkdir(parents=True, exist_ok=True)

    # 保存结果 JSON
    mode_suffix = f"{result.mode}_k{result.k}" if result.mode == "run_less" else result.mode
    result_file = instance_output_dir / f"result_{mode_suffix}.json"

    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(asdict(result), f, indent=2, ensure_ascii=False)

    print(f"Result saved to: {result_file}")


def print_summary(result: ExperimentResult):
    """打印实验结果摘要"""
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    print(f"Instance ID:    {result.instance_id}")
    print(f"Mode:           {result.mode}" + (f" (k={result.k})" if result.k else ""))
    print(f"Agent:          {result.agent_type}")
    print(f"Success:        {result.success}")
    print(f"Tokens Used:    {result.tokens_used}")
    print(f"Exec Count:     {result.exec_count}")
    print(f"Duration:       {result.duration_sec:.2f}s")
    print(f"Patch Length:   {len(result.patch)} chars")

    if result.error:
        print(f"Error:          {result.error[:200]}")

    print("=" * 60)


def main():
    """主函数：解析命令行参数并运行实验"""
    if len(sys.argv) < 3:
        print("Usage: python runner.py <instance_id> <mode> [k] [agent_type] [timeout]")
        print()
        print("Arguments:")
        print("  instance_id   SWE-bench 实例 ID (例如: django__django-11099)")
        print("  mode          执行模式: run_free, run_less, run_cost, run_full")
        print("  k             [可选] run_less 模式的执行次数限制 (默认: 2)")
        print("  agent_type    [可选] agent 类型: claude_code, codex (默认: claude_code)")
        print("  timeout       [可选] 超时时间（秒） (默认: 600)")
        print("  dataset_name  [可选] 数据集名称 (默认: princeton-nlp/SWE-bench_Lite)")
        print()
        print("Examples:")
        print("  python runner.py django__django-11099 run_free")
        print("  python runner.py django__django-11099 run_less 2")
        print("  python runner.py django__django-11099 run_cost")
        print("  python runner.py django__django-11099 run_full")
        sys.exit(1)

    # 解析参数
    instance_id = sys.argv[1]
    mode = sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    agent_type = sys.argv[4] if len(sys.argv) > 4 else "claude_code"
    timeout = int(sys.argv[5]) if len(sys.argv) > 5 else 600
    dataset_name = sys.argv[6] if len(sys.argv) > 6 else "princeton-nlp/SWE-bench_Lite"

    # 验证模式
    if mode not in ["run_free", "run_less", "run_cost", "run_full"]:
        print(f"Error: Invalid mode '{mode}'. Must be one of: run_free, run_less, run_cost, run_full")
        sys.exit(1)

    # 运行实验
    try:
        result = run_experiment(instance_id, mode, k, agent_type, timeout, dataset_name)
        save_result(result, dataset_name)
        print_summary(result)

        # 返回状态码
        sys.exit(0 if result.success else 1)

    except Exception as e:
        print(f"\nError running experiment: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
