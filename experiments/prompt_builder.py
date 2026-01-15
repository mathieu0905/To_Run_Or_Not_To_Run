#!/usr/bin/env python3
"""
Prompt 构造器：为不同的执行模式生成 system prompt

设计原则：
- 四种模式保持结构一致
- 只在"执行 Python"相关部分有差异
- 共同部分：Repository Info, Problem, FREE Operations, FORBIDDEN, Debugging Strategy, Task, Output Format
"""
from typing import Dict, Any


class PromptBuilder:
    """构造不同执行模式的 prompt"""

    # 共同部分：调试策略
    DEBUGGING_STRATEGY = """## Debugging Strategy

**Read with purpose. Run with purpose.**

- Before reading a file: Know what you're looking for
- Before running a test: Know what hypothesis you're verifying

**Think before you run.** Instead of run-fix-run-fix cycles, reason about the code first. When uncertain about specific behavior, add print/log statements to gather information, then analyze the results."""

    # 共同部分：FREE Operations
    FREE_OPERATIONS = """## FREE Operations (No Cost)
✅ `ls` - list directory contents
✅ `cat` - view file contents
✅ `grep` - search text patterns
✅ `find` - locate files
✅ `head` / `tail` - view file portions
✅ `wc` - count lines/words"""

    # 共同部分：FORBIDDEN Operations
    FORBIDDEN_OPERATIONS = """## FORBIDDEN Operations
❌ `git` commands (interferes with experiment)"""

    # 共同部分：Output Format
    OUTPUT_FORMAT = """## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files."""

    # 共同部分：Cost Table
    COST_TABLE = """## Cost Table
| Operation | Cost | Notes |
|-----------|------|-------|
| `pytest` / `unittest` / `python -m pytest` | 1.0 point | HIGH - Runs test framework |
| `python manage.py test` (Django) | 1.0 point | HIGH - Full Django test runner |
| `tox` / `nose` / `nosetests` | 1.0 point | HIGH - Full test framework |
| `python script.py` (running .py files) | 0.3 point | LOW - Direct script execution |
| `python -c "..."` (inline code) | 0.3 point | LOW - Quick inline check |"""

    @staticmethod
    def _build_header(instance: Dict[str, Any]) -> str:
        """构造共同的头部信息"""
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        return f"""## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}"""

    @staticmethod
    def build_run_free_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Free 模式的 prompt（完全不执行代码）
        """
        header = PromptBuilder._build_header(instance)

        prompt = f"""You are a code repair expert.

{header}

## EXECUTION MODE - ZERO EXECUTION

⚠️ **PYTHON EXECUTION IS DISABLED** ⚠️

你不能执行/运行任何 Python 代码（不能运行测试）。  

This is a research experiment testing pure reasoning capabilities WITHOUT code execution.
Any attempt to execute Python code will be blocked by the sandbox.

## ALLOWED Operations
You may ONLY use these commands:
- `ls` - list directory contents
- `cat` - view file contents
- `grep` - search text patterns
- `find` - locate files
- `head` / `tail` - view file portions
- `wc` - count lines/words

## FORBIDDEN Operations
❌ `python` / `python3` - ANY Python execution
❌ `pytest` / `unittest` / `tox` / `nose` - Test frameworks
❌ `pip` / `pip3` - Package management
❌ `git` commands (interferes with experiment)

## Debugging Strategy

**Read with purpose.**

- Before reading a file: Know what you're looking for
- Reason deeply about the code based on what you read

## Your Task
1. Read and analyze the source code to understand the bug
2. Reason about the root cause through static analysis
3. Generate a fix using the Edit tool to modify source files

{PromptBuilder.OUTPUT_FORMAT}
"""
        return prompt

    @staticmethod
    def build_run_less_prompt(instance: Dict[str, Any], k: int = 2) -> str:
        """
        构造 Run-Less 模式的 prompt（有限预算）
        """
        header = PromptBuilder._build_header(instance)

        prompt = f"""You are a code repair expert.

{header}

## EXECUTION MODE - LIMITED BUDGET

🎯 **YOU HAVE {k} TEST EXECUTION(S) - USE THEM** 🎯

你只有 {k} 次执行机会（请谨慎但不要浪费执行次数）。  

This is a research experiment testing efficient debugging with limited executions.
You have a budget of {k} test run(s). **Unused budget is wasted opportunity!**

{PromptBuilder.COST_TABLE}

{PromptBuilder.FREE_OPERATIONS}

{PromptBuilder.FORBIDDEN_OPERATIONS}

{PromptBuilder.DEBUGGING_STRATEGY}

## Execution Protocol
**BEFORE each execution, note:**
```
[BUDGET] Using 1 of {k} | Purpose: <what you want to verify>
```

**AFTER each execution, note:**
```
[BUDGET] Remaining: X of {k}
```

## Your Task
1. Read and analyze the source code to understand the bug
2. **Use your {k} execution(s)** to verify your understanding or test your fix
3. Generate a fix using the Edit tool to modify source files

{PromptBuilder.OUTPUT_FORMAT}
"""
        return prompt

    @staticmethod
    def build_run_cost_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Cost 模式的 prompt（成本追踪但不限制）
        """
        header = PromptBuilder._build_header(instance)

        prompt = f"""You are a code repair expert.

{header}

## EXECUTION MODE - COST-AWARE

📊 **BALANCE CORRECTNESS AND COST** 📊

This is a research experiment measuring cost-efficiency in debugging.
You CAN run tests and scripts, but each execution has a cost.

**Goal: Fix the bug correctly while being mindful of execution costs.**

{PromptBuilder.COST_TABLE}

{PromptBuilder.FREE_OPERATIONS}

{PromptBuilder.FORBIDDEN_OPERATIONS}

{PromptBuilder.DEBUGGING_STRATEGY}

## Execution Protocol
**BEFORE each Python execution, briefly note:**
```
[COST] X.X points | Purpose: <what you want to verify>
```

## Your Task
1. Read and analyze the source code to understand the bug
2. Run tests/experiments as needed to verify your understanding and test your fix
3. Generate a fix using the Edit tool to modify source files

{PromptBuilder.OUTPUT_FORMAT}
"""
        return prompt

    @staticmethod
    def build_run_full_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Full 模式的 prompt（无限制执行）
        """
        header = PromptBuilder._build_header(instance)

        prompt = f"""You are a code repair expert.

{header}

## EXECUTION MODE - UNLIMITED

✅ **YOU HAVE UNLIMITED PYTHON EXECUTIONS** ✅

你可以自由运行测试和脚本。  

This is a research experiment. Feel free to run tests and scripts as many times as needed.

{PromptBuilder.COST_TABLE}

{PromptBuilder.FREE_OPERATIONS}

{PromptBuilder.FORBIDDEN_OPERATIONS}

{PromptBuilder.DEBUGGING_STRATEGY}

## Your Task
1. Read and analyze the source code to understand the bug
2. Run tests and experiments freely to verify your understanding
3. Generate a fix using the Edit tool to modify source files

{PromptBuilder.OUTPUT_FORMAT}
"""
        return prompt

    @staticmethod
    def build_prompt(instance: Dict[str, Any], mode: str, k: int = 2) -> str:
        """
        根据模式构造 prompt

        Args:
            instance: SWE-bench 实例数据
            mode: 执行模式 ("run_free", "run_less", "run_cost", "run_full")
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

    for mode in ["run_free", "run_less", "run_cost", "run_full"]:
        print("=" * 60)
        print(f"{mode} Prompt:")
        print("=" * 60)
        print(PromptBuilder.build_prompt(instance, mode, k=3))
        print()
