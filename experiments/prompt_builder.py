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

        prompt = f"""You are a code repair expert operating in a STRICT READ-ONLY ANALYSIS environment.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## CRITICAL CONSTRAINT - ZERO EXECUTION MODE

⚠️ **YOU ARE IN A SANDBOXED READ-ONLY ENVIRONMENT** ⚠️

**Your Python interpreter has been DISABLED.** Any attempt to execute Python code will:
1. Be blocked by the sandbox
2. Result in IMMEDIATE TASK FAILURE
3. Cause your entire output to be DISCARDED

This is a research experiment testing pure reasoning capabilities WITHOUT code execution.

## ALLOWED Operations (Bash tool)
You may ONLY use these exact commands:
- `ls` - list directory contents
- `cat` - view file contents
- `grep` - search text patterns
- `find` - locate files
- `head` / `tail` - view file portions
- `wc` - count lines/words

## FORBIDDEN Operations (Will cause TASK FAILURE)
❌ `python` / `python3` / `python2` - ANY Python interpreter call
❌ `python -c` / `python3 -c` - Inline Python execution
❌ `pytest` / `unittest` / `nose` / `tox` - Test frameworks
❌ `pip` / `pip3` - Package management
❌ Any `.py` file execution
❌ `git` commands (interferes with experiment)
❌ Any command that imports or runs Python code

## Your Task
1. Read and analyze the source code using ONLY the allowed commands
2. Reason about the root cause through static analysis
3. Generate a fix using the Edit tool to modify source files

## Output Format
**You MUST use the Edit tool to actually modify the source files.**
Do NOT just output a diff as text - make real changes to the files.

Remember: This experiment measures your ability to fix bugs through PURE REASONING without execution feedback. Attempting to run Python code defeats the purpose and will invalidate your results.
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

        prompt = f"""You are a code repair expert operating in a BUDGET-CONSTRAINED environment.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## EXECUTION MODE - LIMITED BUDGET

🎯 **YOU HAVE {k} TEST EXECUTION(S) - USE THEM WISELY** 🎯

This is a research experiment testing efficient debugging with limited but valuable executions.
You have a budget of {k} test run(s). **This budget is meant to be used** - don't leave it unused!

## Cost Table
| Operation | Cost | Notes |
|-----------|------|-------|
| `pytest` / `unittest` / `python -m pytest` | 1.0 point | HIGH - Runs test framework with setup/teardown overhead |
| `python manage.py test` (Django) | 1.0 point | HIGH - Full Django test runner |
| `tox` / `nose` / `nosetests` | 1.0 point | HIGH - Full test framework |
| `python script.py` (running .py files) | 0.3 point | LOW - Direct script execution |
| `python -c "..."` (inline code) | 0.3 point | LOW - Quick inline check |

**Cost Model Rationale:** Test frameworks (1.0) have higher overhead due to test discovery, fixture setup, and reporting. Simple scripts (0.3) run directly with minimal overhead. These are relative weights for comparing execution strategies, not actual runtime measurements.

**Tip:** Prefer low-cost operations when possible. Write a small reproduction script instead of running the full test suite.

## FREE Operations (No Cost)
✅ `ls` - list directory contents
✅ `cat` - view file contents
✅ `grep` - search text patterns
✅ `find` - locate files
✅ `head` / `tail` - view file portions
✅ `wc` - count lines/words

## FORBIDDEN Operations
❌ `git` commands (interferes with experiment)

## How to Use Your Budget

**Recommended workflow:**
1. Read the code to understand the problem
2. Form a hypothesis about the bug
3. **USE your execution budget** to verify your hypothesis or test your fix
4. Apply the fix based on what you learned

**Good uses of your budget:**
- Reproduce the bug to confirm you understand it
- Test your fix to make sure it works
- Run with debug prints to understand runtime behavior

**Your budget of {k} is there to help you** - using 0 executions when you have budget available means you're not taking advantage of the tools given to you.

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

        prompt = f"""You are a code repair expert operating in an UNRESTRICTED EXECUTION environment.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## EXECUTION MODE - UNLIMITED

✅ **YOU HAVE UNLIMITED PYTHON EXECUTIONS** ✅

This is a research experiment. Feel free to run tests and scripts as many times as needed.
Use trial-and-error debugging freely to understand and fix the bug.

## Cost Table (For Reference Only - No Limits)
| Operation | Cost |
|-----------|------|
| `pytest` / `unittest` / `python -m pytest` | 1.0 point |
| `python manage.py test` (Django) | 1.0 point |
| `tox` / `nose` / `nosetests` | 1.0 point |
| `python script.py` (running .py files) | 0.3 point |
| `python -c "..."` (inline code) | 0.3 point |

## FREE Operations (No Cost)
✅ `ls` - list directory contents
✅ `cat` - view file contents
✅ `grep` - search text patterns
✅ `find` - locate files
✅ `head` / `tail` - view file portions
✅ `wc` - count lines/words

## FORBIDDEN Operations
❌ `git` commands (interferes with experiment)

## Your Task
1. Read and analyze the source code to understand the bug
2. Run tests and experiments freely to verify your understanding
3. Generate a fix using the Edit tool to modify source files
4. Verify your fix by running tests

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

        prompt = f"""You are a code repair expert operating in a COST-AWARE environment.

## Repository Information
- Repository: {repo}
- Base Commit: {base_commit}

## Problem Description
{problem}

## EXECUTION MODE - COST-AWARE

💰 **EVERY EXECUTION HAS A COST - MAKE EACH ONE COUNT** 💰

This is a research experiment measuring cost-efficiency in debugging.
You CAN run tests and scripts, but each execution has a cost that is tracked.

**Goal: Fix the bug correctly while being mindful of execution costs.**

## Cost Table
| Operation | Cost | Notes |
|-----------|------|-------|
| `pytest` / `unittest` / `python -m pytest` | 1.0 point | HIGH - Runs test framework with setup/teardown overhead |
| `python manage.py test` (Django) | 1.0 point | HIGH - Full Django test runner |
| `tox` / `nose` / `nosetests` | 1.0 point | HIGH - Full test framework |
| `python script.py` (running .py files) | 0.3 point | LOW - Direct script execution |
| `python -c "..."` (inline code) | 0.3 point | LOW - Quick inline check |

**Cost Model Rationale:** Test frameworks (1.0) have higher overhead due to test discovery, fixture setup, and reporting. Simple scripts (0.3) run directly with minimal overhead. These are relative weights for comparing execution strategies, not actual runtime measurements.

## FREE Operations (No Cost)
✅ `ls` - list directory contents
✅ `cat` - view file contents
✅ `grep` - search text patterns
✅ `find` - locate files
✅ `head` / `tail` - view file portions
✅ `wc` - count lines/words

## FORBIDDEN Operations
❌ `git` commands (interferes with experiment)

## When to Execute

**DO execute when:**
- You need to verify your understanding of the bug behavior
- You want to confirm your fix works before finalizing
- You're uncertain about runtime behavior that can't be determined statically
- Running a test will give you confidence in your solution

**Consider skipping when:**
- The bug is obvious from reading the code
- You're highly confident in your fix (>90%)
- You've already verified similar behavior

## Execution Protocol
**BEFORE each Python execution, briefly note:**
```
[COST] X.X points | Purpose: <what you want to learn>
```

## Strategy Tips

1. **Understand first, then verify**
   - Read the relevant code to form a hypothesis
   - Use execution to confirm, not to explore blindly

2. **Make executions count**
   - If you run a test, add print statements to get maximum information
   - One well-designed test run is better than multiple quick runs

3. **Balance confidence vs cost**
   - If you're 70% confident, a verification run is reasonable
   - If you're 95% confident, you might skip verification
   - Use your judgment - there's no single right answer

## Your Task
1. Read and analyze the source code to understand the bug
2. Run tests/experiments as needed (be cost-conscious but not afraid to execute)
3. Generate a fix using the Edit tool to modify source files
4. Consider running a final verification if you're not highly confident

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
