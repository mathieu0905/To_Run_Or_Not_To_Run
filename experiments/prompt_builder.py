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

**CRITICAL CONSTRAINT: You CANNOT run tests or execute Python scripts.**

You must generate a fix by reading code, understanding logic, and reasoning about the root cause.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## What You CAN Do
✅ Use bash commands to view files (ls, cat, grep, find, etc.)
✅ Read and analyze code
✅ Reason and think

## What You CANNOT Do
❌ Run pytest or any tests
❌ Execute Python scripts (python xxx.py)
❌ Run any commands that execute code
❌ Use git commands (git may interfere with the experimental environment)

## Task Requirements
1. Carefully read relevant code files (you can read multiple times)
2. Analyze the root cause of the problem
3. Reason out the correct fix
4. Double-check your fix logic
5. **Use the Edit tool to actually modify the source files**

## CRITICAL: You MUST Actually Modify Files
- Do NOT just output a diff as text
- You MUST use the Edit tool to make actual changes to the source files
- After editing, the changes will be captured by git diff automatically

Remember: You can use bash commands to view code, but cannot run tests or scripts to verify. Ensure correctness through careful logical reasoning.
"""
        return prompt

    @staticmethod
    def build_run_less_prompt(instance: Dict[str, Any], k: int = 2) -> str:
        """
        构造 Run-Less 模式的 prompt（有限次执行）

        Args:
            instance: SWE-bench 实例数据
            k: 允许的最大执行次数

        Returns:
            完整的 prompt 字符串
        """
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        prompt = f"""You are a code repair expert. Your task is to fix the following bug.

**EXECUTION CONSTRAINT: You can run Python code at most {k} times.**

Each execution is precious. Use your execution budget wisely.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## What You CAN Do
- Use bash commands to view files (ls, cat, grep, find, etc.) - UNLIMITED
- Read and analyze code - UNLIMITED
- Run Python code (tests, scripts) - **at most {k} times**

## What You CANNOT Do
- Use git commands (git may interfere with the experimental environment)

## How Execution Can Help
Running code is valuable for:
1. **Reproducing the bug**: A failing test helps you understand exactly what's broken
2. **Verifying your fix**: A passing test confirms your solution actually works

You decide how to use your {k} execution opportunities. Consider:
- If the problem description is clear, you might analyze the code and implement a fix directly
- If the bug is unclear, you might use an execution to reproduce and understand it first
- If you're confident in your fix, you might use an execution to verify it works
- If you have very high confidence, you might not need to execute at all

## Execution Budget
- Total allowed: {k} runs
- After each run, output: "Remaining runs: X"

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

**EXECUTION CONSTRAINT: You have UNLIMITED Python executions.**

Feel free to run tests and scripts as many times as needed to debug and verify your fix.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## What You CAN Do
- Use bash commands to view files (ls, cat, grep, find, etc.) - UNLIMITED
- Read and analyze code - UNLIMITED
- Run Python code (tests, scripts) - **UNLIMITED**

## What You CANNOT Do
- Use git commands (git may interfere with the experimental environment)

## Why Running Tests Helps
Running tests is valuable for:
1. **Locating the bug**: A failing test pinpoints exactly where the problem occurs
2. **Verifying the fix**: A passing test confirms your fix actually works
3. **Catching regressions**: Tests ensure you haven't broken other functionality

## Recommended Workflow

### Step 1: Write a Test Script
Based on the problem description, write a simple test script to reproduce the issue:
```python
# test_bug.py
def test_issue():
    result = some_function(test_input)
    print(f"Result: {{result}}")
    assert result == expected_output, f"Expected X, got {{result}}"

if __name__ == "__main__":
    test_issue()
```

### Step 2: Run Test to Confirm the Bug
Run your test script to verify the bug exists and understand the failure.

### Step 3: Analyze and Fix
1. Read the relevant source code
2. Identify the root cause
3. Implement the fix

### Step 4: Run Test to Verify the Fix
Run the test again to confirm your fix works. If it fails, iterate on steps 3-4.

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.
"""
        return prompt

    @staticmethod
    def build_run_cost_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Cost 模式的 prompt（每次执行有成本）

        Args:
            instance: SWE-bench 实例数据

        Returns:
            完整的 prompt 字符串
        """
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        prompt = f"""You are a code repair expert. Your task is to fix the following bug.

**EXECUTION CONSTRAINT: Every Python execution has a cost (time, compute, money).**

You can run code, but each execution costs resources. Decide wisely whether to run based on expected value.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## What You CAN Do
- Use bash commands to view files (ls, cat, grep, find, etc.) - FREE, no cost
- Read and analyze code - FREE, no cost
- Run Python code (tests, scripts) - **each run has a cost**

## What You CANNOT Do
- Use git commands (git may interfere with the experimental environment)

## Why Running Tests Helps
Running tests is valuable for:
1. **Locating the bug**: A failing test pinpoints exactly where the problem occurs
2. **Verifying the fix**: A passing test confirms your fix actually works
3. **Catching regressions**: Tests ensure you haven't broken other functionality

## Cost-Aware Decision Making

Before each execution, evaluate:
- **High confidence (>90%)**: You may skip testing if very certain
- **Medium confidence (50-90%)**: Testing is likely worth the cost
- **Low confidence (<50%)**: Testing is strongly recommended

Output your decision:
```
[DECISION] Confidence: X% | Action: Run/Skip | Reason: ...
```

## Recommended Workflow

### Step 1: Write a Test Script
Based on the problem description, write a simple test script to reproduce the issue:
```python
# test_bug.py
def test_issue():
    result = some_function(test_input)
    print(f"Result: {{result}}")
    assert result == expected_output, f"Expected X, got {{result}}"

if __name__ == "__main__":
    test_issue()
```

### Step 2: Decide Whether to Run
Assess your confidence and decide if running the test is worth the cost.

### Step 3: Analyze and Fix
1. Read the relevant source code
2. Identify the root cause
3. Implement the fix

### Step 4: Decide Whether to Verify
If confident in your fix, you may skip verification. Otherwise, run the test.

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
