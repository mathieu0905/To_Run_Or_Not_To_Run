#!/usr/bin/env python3
"""
批量运行器：并行执行多个实验
"""
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import asdict

from runner import run_experiment, ExperimentResult


PROJ_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJ_ROOT / "output"


class BatchRunner:
    """并行实验执行器"""

    def __init__(
        self,
        max_workers: int = 4,
        dataset_name: str = "princeton-nlp/SWE-bench_Lite"
    ):
        self.max_workers = max_workers
        self.dataset_name = dataset_name

        # 确定数据集目录名称
        self.dataset_dir = "swebenchlite" if "Lite" in dataset_name else "swebenchverified"

    def _get_checkpoint_file(self, agent_type: str, mode: str, k: int) -> Path:
        """获取特定配置的 checkpoint 文件路径"""
        mode_dir = f"{mode}_k{k}" if mode == "run_less" else mode
        checkpoint_dir = OUTPUT_DIR / self.dataset_dir / agent_type / mode_dir
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        return checkpoint_dir / "checkpoint.json"

    def run_batch(
        self,
        instances: List[str],
        mode: str,
        k: int = 2,
        agent_type: str = "claude_code",
        timeout: int = 600
    ) -> Dict[str, Optional[ExperimentResult]]:
        """
        并行运行多个实验

        Args:
            instances: 实例 ID 列表
            mode: 执行模式 (run_free, run_less, run_cost, run_full)
            k: run_less 模式的执行次数限制
            agent_type: agent 类型 (claude_code, codex)
            timeout: 每个实例的超时时间（秒）

        Returns:
            字典，映射 instance_id 到 ExperimentResult（失败则为 None）
        """
        # 获取当前配置的 checkpoint 文件
        self.checkpoint_file = self._get_checkpoint_file(agent_type, mode, k)

        # 加载 checkpoint 以跳过已完成的实例
        completed = self._load_checkpoint()
        remaining = [i for i in instances if i not in completed]

        print(f"总实例数: {len(instances)}")
        print(f"已完成: {len(completed)}")
        print(f"待运行: {len(remaining)}")
        print(f"并发数: {self.max_workers}")
        print(f"模式: {mode}" + (f" (k={k})" if mode == "run_less" else ""))
        print("=" * 60)

        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = {
                executor.submit(
                    run_experiment,
                    instance_id=inst,
                    mode=mode,
                    k=k,
                    agent_type=agent_type,
                    timeout=timeout,
                    dataset_name=self.dataset_name
                ): inst
                for inst in remaining
            }

            # 处理完成的任务
            for i, future in enumerate(as_completed(futures), 1):
                instance_id = futures[future]
                try:
                    result = future.result()
                    results[instance_id] = result

                    # 更新 checkpoint
                    self._update_checkpoint(instance_id)

                    # 打印进度
                    status = "✓" if result.success else "✗"
                    print(f"[{i}/{len(remaining)}] {status} {instance_id} "
                          f"({result.duration_sec:.1f}s, {result.tokens_used} tokens, "
                          f"{result.exec_count} execs)")

                except Exception as e:
                    print(f"[{i}/{len(remaining)}] ✗ {instance_id} - Error: {e}")
                    results[instance_id] = None

        # 打印总结
        print("=" * 60)
        success_count = sum(1 for r in results.values() if r and r.success)
        print(f"完成: {success_count}/{len(instances)} 成功")

        return results

    def _load_checkpoint(self) -> set:
        """加载已完成的实例 ID"""
        if not self.checkpoint_file.exists():
            return set()

        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                return set(data.get("completed", []))
        except Exception as e:
            print(f"Warning: Failed to load checkpoint: {e}")
            return set()

    def _update_checkpoint(self, instance_id: str):
        """添加实例到 checkpoint"""
        completed = self._load_checkpoint()
        completed.add(instance_id)

        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({"completed": list(completed)}, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to update checkpoint: {e}")


def main():
    """CLI 入口"""
    if len(sys.argv) < 3:
        print("Usage: python batch_runner.py <instances_file> <mode> [k] [workers] [agent_type] [timeout] [dataset_name]")
        print()
        print("Arguments:")
        print("  instances_file  包含实例 ID 的文件（每行一个）")
        print("  mode           执行模式: run_free, run_less, run_cost, run_full")
        print("  k              [可选] run_less 模式的执行次数限制 (默认: 2)")
        print("  workers        [可选] 并发数 (默认: 4)")
        print("  agent_type     [可选] agent 类型: claude_code, codex (默认: claude_code)")
        print("  timeout        [可选] 每个实例的超时时间（秒） (默认: 600)")
        print("  dataset_name   [可选] 数据集名称 (默认: princeton-nlp/SWE-bench_Lite)")
        print()
        print("Examples:")
        print("  python batch_runner.py instances.txt run_free")
        print("  python batch_runner.py instances.txt run_less 2 4")
        print("  python batch_runner.py instances.txt run_full 2 8 claude_code 600")
        print("  python batch_runner.py instances.txt run_less 2 4 claude_code 600 princeton-nlp/SWE-bench_Verified")
        sys.exit(1)

    # 解析参数
    instances_file = Path(sys.argv[1])
    mode = sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 2
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    agent_type = sys.argv[5] if len(sys.argv) > 5 else "claude_code"
    timeout = int(sys.argv[6]) if len(sys.argv) > 6 else 600
    dataset_name = sys.argv[7] if len(sys.argv) > 7 else "princeton-nlp/SWE-bench_Lite"

    # 验证模式
    if mode not in ["run_free", "run_less", "run_cost", "run_full"]:
        print(f"Error: Invalid mode '{mode}'. Must be one of: run_free, run_less, run_cost, run_full")
        sys.exit(1)

    # 加载实例列表
    if not instances_file.exists():
        print(f"Error: Instances file not found: {instances_file}")
        sys.exit(1)

    instances = [
        line.strip()
        for line in instances_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not instances:
        print(f"Error: No instances found in {instances_file}")
        sys.exit(1)

    print(f"Loaded {len(instances)} instances from {instances_file}")
    print()

    # 运行批量实验
    try:
        runner = BatchRunner(
            max_workers=workers,
            dataset_name=dataset_name
        )
        results = runner.run_batch(instances, mode, k, agent_type, timeout)

        # 返回状态码
        success_count = sum(1 for r in results.values() if r and r.success)
        sys.exit(0 if success_count == len(instances) else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress has been saved to checkpoint.")
        print("Re-run the same command to resume from where you left off.")
        sys.exit(130)
    except Exception as e:
        print(f"\nError running batch: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
