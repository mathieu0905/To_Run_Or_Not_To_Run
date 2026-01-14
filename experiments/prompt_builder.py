#!/usr/bin/env python3
"""
Prompt 构造器：为不同的执行模式生成 system prompt
"""
from typing import Dict, Any


class PromptBuilder:
    """构造不同执行模式的 prompt"""

    @staticmethod
    def build_run_free_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Free 模式的 prompt（完全不执行代码）

        Args:
            instance: SWE-bench 实例数据

        Returns:
            完整的 prompt 字符串
        """
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        prompt = f"""You are a code repair expert. Your task is to fix the following bug.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## Execution Constraint
**You CANNOT run tests or execute Python scripts.**

You must generate a fix by reading code and reasoning about the root cause.

## What You CAN Do
- Use bash commands to view files (ls, cat, grep, find, etc.)
- Read and analyze code

## What You CANNOT Do
- Run pytest or any tests
- Execute Python scripts (python xxx.py)
- Use git commands (git may interfere with the experimental environment)

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.
"""
        return prompt

    @staticmethod
    def build_run_less_prompt(instance: Dict[str, Any], k: int = 2) -> str:
        """
        构造 Run-Less 模式的 prompt（有限成本预算）

        Args:
            instance: SWE-bench 实例数据
            k: 允许的成本预算（成本点数）

        Returns:
            完整的 prompt 字符串
        """
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        prompt = f"""You are a code repair expert. Your task is to fix the following bug.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## Execution Constraint
**You have a limited execution budget of {k}.0 cost points.**

Different executions have different costs. Estimate the cost before each execution:
- Running full test suites (pytest, unittest, Django tests, etc.): ~1.0 point
- Running simple scripts (python script.py): ~0.3 point

Before each execution, output:
```
[EXECUTION] Estimated cost: X.X points | Remaining budget: Y.Y points | Purpose: ...
```

After each execution, output:
```
Remaining budget: X.X points
```

## What You CAN Do
- Use bash commands to view files (ls, cat, grep, find, etc.)
- Read and analyze code
- Run Python code (costs budget points)

## What You CANNOT Do
- Use git commands (git may interfere with the experimental environment)

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.
"""
        return prompt

    @staticmethod
    def build_run_full_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Full 模式的 prompt（不限制执行次数）

        Args:
            instance: SWE-bench 实例数据

        Returns:
            完整的 prompt 字符串
        """
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        prompt = f"""You are a code repair expert. Your task is to fix the following bug.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## Execution Constraint
**You have UNLIMITED Python executions.**

Feel free to run tests and scripts as many times as needed.

## What You CAN Do
- Use bash commands to view files (ls, cat, grep, find, etc.)
- Read and analyze code
- Run Python code (tests, scripts)

## What You CANNOT Do
- Use git commands (git may interfere with the experimental environment)

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.
"""
        return prompt

    @staticmethod
    def build_run_cost_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Cost 模式的 prompt（成本意识但不限制）

        Args:
            instance: SWE-bench 实例数据

        Returns:
            完整的 prompt 字符串
        """
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        prompt = f"""You are a code repair expert. Your task is to fix the following bug.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## Execution Constraint
**Every Python execution has a cost (time, compute, money).**

You can run code without hard limits, but be cost-aware in your decisions.

Different executions have different costs. Estimate the cost before each execution:
- Running full test suites (pytest, unittest, Django tests, etc.): ~1.0 point
- Running simple scripts (python script.py): ~0.3 point

Before each execution, output:
```
[EXECUTION] Estimated cost: X.X points | Purpose: ...
```

## What You CAN Do
- Use bash commands to view files (ls, cat, grep, find, etc.)
- Read and analyze code
- Run Python code (costs resources)

## What You CANNOT Do
- Use git commands (git may interfere with the experimental environment)

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.
"""
        return prompt

    @staticmethod
    def build_prompt(instance: Dict[str, Any], mode: str, k: int = 2) -> str:
        """
        根据模式构造 prompt

        Args:
            instance: SWE-bench 实例数据
            mode: 执行模式 ("run_free", "run_less", "run_full")
            k: Run-Less 模式的执行次数限制

        Returns:
            完整的 prompt 字符串
        """
        if mode == "run_free":
            return PromptBuilder.build_run_free_prompt(instance)
        elif mode == "run_less":
            return PromptBuilder.build_run_less_prompt(instance, k)
        elif mode == "run_cost":
            return PromptBuilder.build_run_cost_prompt(instance)
        elif mode == "run_full":
            return PromptBuilder.build_run_full_prompt(instance)
        else:
            raise ValueError(f"Unknown mode: {mode}")


# 示例用法
if __name__ == "__main__":
    from datasets import load_dataset

    # 加载数据集
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    instance = dataset[0]

    print("=" * 60)
    print("Run-Free Prompt:")
    print("=" * 60)
    print(PromptBuilder.build_run_free_prompt(instance))

    print("\n" + "=" * 60)
    print("Run-Less Prompt (k=2):")
    print("=" * 60)
    print(PromptBuilder.build_run_less_prompt(instance, k=2))

    print("\n" + "=" * 60)
    print("Run-Full Prompt:")
    print("=" * 60)
    print(PromptBuilder.build_run_full_prompt(instance))
