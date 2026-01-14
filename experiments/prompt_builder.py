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
        构造 Run-Less 模式的 prompt（有限次执行，强调日志插桩）

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

**CRITICAL CONSTRAINT: You can run tests at most {k} times.**

Test executions are a scarce resource. You must treat each execution as a "high-value experiment."

Note: Different projects use different test frameworks (pytest, unittest, Django tests, etc.). Identify the appropriate test command for this project.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## What You CAN Do
✅ Unlimited use of bash commands to view files (ls, cat, grep, find, etc.)
✅ Read and analyze code
✅ Run tests at most {k} times (using pytest, unittest, Django tests, or project-specific test commands)

## What You CANNOT Do
❌ Use git commands (git may interfere with the experimental environment)

## Execution Strategy (CRITICAL!)

### Step 1: Write Test Script to Reproduce the Issue
Since you don't have ready-made test cases, you need to:
1. **Write a simple test script based on the problem description** to reproduce the issue
2. Run this test script to confirm the problem exists
3. This will help you accurately locate the bug

### Step 2: Instrumented Debugging
Before running tests, you should:
1. **Identify test command**: Determine the appropriate test command for this project (pytest, python -m unittest, python manage.py test, etc.)
2. **Formulate a hypothesis**: Clearly state where you suspect the problem is
3. **Insert logging**: Add print/log statements at key locations to capture:
   - Variable values
   - Function inputs and outputs
   - Branch paths
   - Exception context
4. **Run tests**: Execute the test using the appropriate command to obtain high-density debugging information
5. **Output remaining count**: After each run, explicitly output "Remaining test runs: X"
6. **Analyze results**: Determine the fix based on log output

### Step 3: Verify the Fix
After fixing, run the test script again to verify the problem is resolved

## Test Script Example
```python
# test_bug.py - Test script to reproduce and verify the issue
def test_issue():
    # Construct test case based on problem description
    result = calculate(-5)
    print(f"Result: {{result}}")
    assert result == -10, f"Expected -10, got {{result}}"
```

## Logging Instrumentation Example
```python
# Insert debug logs in source code
def calculate(x):
    print(f"DEBUG: calculate() input x={{{{x}}}}, type={{{{type(x)}}}}")  # Instrumentation
    result = x * 2
    print(f"DEBUG: calculate() output result={{{{result}}}}")  # Instrumentation
    return result
```

## Execution Budget Tracking
- Initial test runs: {k}
- **IMPORTANT**: After each test execution (pytest, unittest, Django tests, or any test command), you MUST output:
  "✅ Used X test runs, Y remaining"

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.
After editing, the changes will be captured by git diff automatically.

Remember:
- Bash commands (ls, cat, grep, etc.) do NOT count toward execution budget, use freely
- Only test executions (pytest, unittest, Django tests, or running test scripts) count toward execution budget
- Treat test runs as expensive experiments, not free trial-and-error buttons
- One smart run is worth ten blind runs
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

You can freely execute code to debug and verify your fix.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## Recommended Workflow

### Step 1: Write Test Script to Reproduce the Issue
Since you don't have ready-made test cases, it's recommended to:
1. **Write a test script based on the problem description** to reproduce the issue
2. Run the test script to confirm the problem exists
3. This will help you accurately locate the bug

### Step 2: Locate and Fix
1. Read relevant code
2. Analyze error messages
3. Attempt the fix
4. You can add logging to assist debugging

### Step 3: Verify the Fix
1. Run the test script to verify the problem is resolved
2. If tests fail, repeat steps 2-3
3. Ensure the fix doesn't introduce new issues

## Test Script Example
```python
# test_bug.py - Test script to reproduce and verify the issue
def test_issue():
    # Construct test case based on problem description
    result = some_function(test_input)
    assert result == expected_output
```

## Output Format
Finally, output your fix as a git diff patch.

## Important Reminders
- ❌ Do NOT use git commands (git may interfere with the experimental environment)
- Bash commands (ls, cat, grep, etc.) can be used freely
- Recommended to write test script first to reproduce and verify the issue

You can run code and tests multiple times until all tests pass.
"""
        return prompt

    @staticmethod
    def build_run_cost_prompt(instance: Dict[str, Any]) -> str:
        """
        构造 Run-Cost 模式的 prompt（有成本约束，但模型自己决定）

        Args:
            instance: SWE-bench 实例数据

        Returns:
            完整的 prompt 字符串
        """
        problem = instance["problem_statement"]
        repo = instance["repo"]
        base_commit = instance.get("base_commit", "")

        prompt = f"""You are a code repair expert. Your task is to fix the following bug.

**IMPORTANT: Every test execution has a cost (time, resources, money).**

You need to decide whether it's worth running tests based on your confidence in the task.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## Cost-Aware Decision Making

Every test run (pytest, unittest, Django tests, or any test command) consumes resources. Before deciding whether to run tests, you must:

### 1. Assess Your Confidence Level
- **High confidence (>90%)**: You are very certain about the problem location and fix
- **Medium confidence (50-90%)**: You have a reasonable hypothesis, but not completely certain
- **Low confidence (<50%)**: You are uncertain about the problem location and need more information

### 2. Decision Framework

**If confidence is high (>90%)**:
- Consider fixing directly without running tests
- But if the fix involves complex logic, testing may still be worthwhile

**If confidence is medium (50-90%)**:
- Evaluate the expected value of testing
- If testing can significantly increase confidence, it's worth running
- Consider writing a simple test script to verify the hypothesis

**If confidence is low (<50%)**:
- Testing is usually necessary
- Write test script first to reproduce the issue
- Use logging instrumentation to obtain more information

### 3. Decision Output Format

Each time you decide whether to run tests, you MUST output:

```
[DECISION]
- Current confidence level: X%
- Decision: [Run tests / Don't run tests]
- Reasoning: [Explain why this decision is reasonable]
```

## Recommended Workflow

### Step 1: Understand the Problem
1. Read the problem description and relevant code
2. Form initial hypothesis
3. Assess confidence level

### Step 2: Decide Whether to Test
1. If confidence is low, write test script to reproduce the issue
2. If more information is needed, use logging instrumentation
3. Run tests to obtain feedback

### Step 3: Fix and Verify
1. Implement the fix
2. Assess whether running tests for verification is needed
3. If confidence is high enough, can directly submit the fix

## Test Script Example
```python
# test_bug.py - Test script to reproduce and verify the issue
def test_issue():
    # Construct test case based on problem description
    result = some_function(test_input)
    assert result == expected_output
```

## What You CAN Do
✅ Unlimited use of bash commands to view files (ls, cat, grep, find, etc.)
✅ Read and analyze code
✅ Decide whether to run tests based on confidence level

## What You CANNOT Do
❌ Use git commands (git may interfere with the experimental environment)

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.
After editing, the changes will be captured by git diff automatically.

Remember:
- Bash commands (ls, cat, grep, etc.) have no cost, use freely
- Only test executions (pytest, unittest, Django tests, or running test scripts) have cost
- Make rational decisions based on your confidence level
- If truly necessary, don't hesitate to run tests
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
