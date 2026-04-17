#!/usr/bin/env python3
"""
Prompt Builder: Generate system prompts for different execution modes

Design Principles:
- Four modes maintain consistent structure
- Only differ in "Python execution" related sections
- Common sections: Repository Info, Problem, FREE Operations, FORBIDDEN, Debugging Strategy, Task, Output Format
"""
from typing import Dict, Any


class PromptBuilder:
    """Build prompts for different execution modes"""

    # Common section: Debugging Strategy
    DEBUGGING_STRATEGY = """## Debugging Strategy

**Read with purpose. Run with purpose.**

- Before reading a file: Know what you're looking for
- Before running a test: Know what hypothesis you're verifying

**Think before you run.** Instead of run-fix-run-fix cycles, reason about the code first. When uncertain about specific behavior, add print/log statements to gather information, then analyze the results."""

    # Common section: FREE Operations
    # NOTE: do NOT enumerate tool names here. The agent runtime injects its
    # own tool schema; listing shell commands by name causes weaker models to
    # try to call them as top-level tools (e.g. `find`) instead of via bash.
    FREE_OPERATIONS = """## Investigation
Use the file-reading and search tools available in your environment to
investigate the codebase. Reading files and searching is unrestricted."""

    # Common section: FORBIDDEN Operations
    FORBIDDEN_OPERATIONS = """## FORBIDDEN Operations
❌ `git` commands (interferes with experiment)"""

    # Common section: Output Format
    OUTPUT_FORMAT = """## CRITICAL: How to Submit Your Fix

⚠️ **You MUST apply your fix by calling the edit tool on the source files.** ⚠️

A textual description of the fix (e.g. "change line 42 to ...") is **NOT a
submission** — it will be discarded. Only edits made via the edit tool are
captured by `git diff` and counted as your answer.

Your response is considered SUCCESSFUL only if it satisfies BOTH:
1. You called the edit tool at least once with a real `filePath`,
   `oldString`, and `newString` matching the file's current contents
2. After your changes, `git diff` shows a non-empty patch

If you finish without calling edit, the run is a FAILURE regardless of how
well you described the bug."""

    # Common section: Cost Table
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
        """Build common header information"""
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
        Build Run-Free mode prompt (no code execution)
        """
        header = PromptBuilder._build_header(instance)

        prompt = f"""You are a code repair expert.

{header}

## EXECUTION MODE - ZERO EXECUTION

⚠️ **PYTHON EXECUTION IS DISABLED** ⚠️

You cannot execute/run any Python code (cannot run tests).

This is a research experiment testing pure reasoning capabilities WITHOUT code execution.

## What You CAN Do
Use the file-reading and search tools available in your environment to
investigate the codebase. Reading files and searching is unrestricted.

## What You CANNOT Do
❌ Run `python` / `python3` (any Python execution)
❌ Run `pytest` / `unittest` / `tox` / `nose` (test frameworks)
❌ Run `pip` / `pip3` (package management)
❌ Run `git` commands (interferes with experiment)

## Debugging Strategy
**Read with purpose.** Before opening a file, know what you're looking for.
Reason deeply about the code based on what you read.

## Your Task
1. Investigate the source code to understand the bug
2. Reason about the root cause through static analysis
3. **Apply the fix by calling the edit tool on real source files**

{PromptBuilder.OUTPUT_FORMAT}
"""
        return prompt

    @staticmethod
    def build_run_less_prompt(instance: Dict[str, Any], k: int = 2) -> str:
        """
        Build Run-Less mode prompt (limited budget)
        """
        header = PromptBuilder._build_header(instance)

        prompt = f"""You are a code repair expert.

{header}

## EXECUTION MODE - LIMITED BUDGET

🎯 **YOU HAVE {k} TEST EXECUTION(S) - USE THEM** 🎯

You only have {k} execution opportunities (use them wisely but don't waste them).

This is a research experiment testing efficient debugging with limited executions.
You have a budget of {k} test run(s). **Unused budget is wasted opportunity!**

{PromptBuilder.COST_TABLE}

{PromptBuilder.FREE_OPERATIONS}

{PromptBuilder.FORBIDDEN_OPERATIONS}

{PromptBuilder.DEBUGGING_STRATEGY}

## Execution Protocol
Before each test execution, briefly state in plain English: which budget unit you are spending and what hypothesis you want to verify.
After each test execution, briefly state in plain English: how many budget units remain and what you learned.

## Your Task
1. Read and analyze the source code to understand the bug
2. Use your {k} execution(s) to verify your understanding or test your fix
3. Generate a fix using the Edit tool to modify source files

{PromptBuilder.OUTPUT_FORMAT}
"""
        return prompt

    @staticmethod
    def build_run_cost_prompt(instance: Dict[str, Any]) -> str:
        """
        Build Run-Cost mode prompt (cost tracking but no limits)
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
Before each test execution, briefly state in plain English: how many points the run will cost and what you want to verify.

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
        Build Run-Full mode prompt (unlimited execution)
        """
        header = PromptBuilder._build_header(instance)

        prompt = f"""You are a code repair expert.

{header}

## EXECUTION MODE - UNLIMITED

✅ **YOU HAVE UNLIMITED PYTHON EXECUTIONS** ✅

You can freely run tests and scripts.

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

    # Tool usage reminder for smaller open-source models (e.g., Qwen2.5-Coder)
    # served via OpenCode. Larger commercial models follow tool-use instructions
    # implicitly; smaller models need explicit reminders to actually invoke
    # tools instead of describing them in prose.
    OPENCODE_TOOL_REMINDER = """
## CRITICAL: TOOL INVOCATION

You have access to tools. You MUST INVOKE them, not describe them in prose.

Available tools (call them by name):
- `read` — read file contents. Args: `{"filePath": "/absolute/path"}`
- `edit` — edit a file by replacing text. Args: `{"filePath": "...", "oldString": "...", "newString": "..."}`
  IMPORTANT: You MUST `read` a file before you can `edit` it.
- `bash` — run a shell command. Args: `{"command": "..."}`
- `glob` — find files by pattern. Args: `{"pattern": "..."}`
- `grep` — search files for a pattern. Args: `{"pattern": "...", "path": "..."}`
- `write` — overwrite a file. Args: `{"filePath": "...", "content": "..."}`

The repository is at `/testbed`. Use absolute paths like `/testbed/django/...`.

DO NOT output `[bash command="..."]` or `{"name": "read", "arguments": {...}}` as plain text.
INSTEAD, actually invoke the tools through the standard tool-call mechanism.
The system will execute them and return results to you.

WORKFLOW:
1. `read` the relevant file(s) to understand the bug
2. `edit` the file to apply the fix (you must have read it first)
3. Stop. Do not produce a final summary."""

    @staticmethod
    def build_prompt(instance: Dict[str, Any], mode: str, k: int = 2,
                     agent_type: str = "claude_code") -> str:
        """
        Build prompt based on mode

        Args:
            instance: SWE-bench instance data
            mode: Execution mode ("run_free", "run_less", "run_cost", "run_full")
            k: Execution limit for Run-Less mode
            agent_type: Agent type ("claude_code", "codex", "opencode")

        Returns:
            Complete prompt string
        """
        if mode == "run_free" or mode == "run_hard_free":
            prompt = PromptBuilder.build_run_free_prompt(instance)
        elif mode == "run_less":
            prompt = PromptBuilder.build_run_less_prompt(instance, k)
        elif mode == "run_cost":
            prompt = PromptBuilder.build_run_cost_prompt(instance)
        elif mode == "run_full":
            prompt = PromptBuilder.build_run_full_prompt(instance)
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # NOTE: previously we appended OPENCODE_TOOL_REMINDER for opencode+Qwen,
        # but the reminder's `read — Args: {"filePath": ...}` descriptions caused
        # the model to pattern-match and emit literal `read {...}` text instead
        # of real tool calls. Rely on OpenCode's native tool schema + vLLM hermes
        # parser instead.
        return prompt


# Example usage
if __name__ == "__main__":
    from datasets import load_dataset

    # Load dataset
    dataset = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    instance = dataset[0]

    for mode in ["run_free", "run_less", "run_cost", "run_full"]:
        print("=" * 60)
        print(f"{mode} Prompt:")
        print("=" * 60)
        print(PromptBuilder.build_prompt(instance, mode, k=3))
        print()
