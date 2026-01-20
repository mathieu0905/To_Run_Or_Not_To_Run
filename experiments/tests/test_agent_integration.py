#!/usr/bin/env python3
"""
Integration tests: Real calls to Claude Code and Codex
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_caller import AgentCaller, save_trace


def test_claude_code_real_call():
    """Test real call to Claude Code"""
    print("\n=== Testing Claude Code Real Call ===")

    caller = AgentCaller(agent_type="claude_code")
    prompt = "Please write a Python function to calculate the sum of two numbers, function name should be add"

    print(f"Prompt: {prompt}")
    print("Calling...")

    trace = caller.call(prompt, timeout=60)

    print(f"\nResult:")
    print(f"  Agent: {trace.agent_type}")
    print(f"  Tokens: {trace.tokens_used}")
    print(f"  Execution count: {trace.exec_count}")
    print(f"  Duration: {trace.duration_sec:.2f}s")
    print(f"  Output length: {len(trace.output)} characters")

    if trace.error:
        print(f"  Error: {trace.error}")
        return False

    # Save trace
    output_path = Path(__file__).parent / "claude_code_trace.json"
    save_trace(trace, output_path)
    print(f"  Trace saved to: {output_path}")

    # Verify output contains code
    if "def add" in trace.output or "def" in trace.output:
        print("✅ Claude Code call successful, output contains code")
        return True
    else:
        print("⚠️  Expected code not found in output")
        print(f"Output preview: {trace.output[:500]}")
        return False


def test_codex_real_call():
    """Test real call to Codex"""
    print("\n=== Testing Codex Real Call ===")

    caller = AgentCaller(agent_type="codex")
    prompt = "Please write a Python function to calculate the sum of two numbers, function name should be add"

    print(f"Prompt: {prompt}")
    print("Calling...")

    trace = caller.call(prompt, timeout=60)

    print(f"\nResult:")
    print(f"  Agent: {trace.agent_type}")
    print(f"  Tokens: {trace.tokens_used}")
    print(f"  Execution count: {trace.exec_count}")
    print(f"  Duration: {trace.duration_sec:.2f}s")
    print(f"  Output length: {len(trace.output)} characters")

    if trace.error:
        print(f"  Error: {trace.error}")
        return False

    # Save trace
    output_path = Path(__file__).parent / "codex_trace.json"
    save_trace(trace, output_path)
    print(f"  Trace saved to: {output_path}")

    # Verify output contains code
    if "def add" in trace.output or "def" in trace.output:
        print("✅ Codex call successful, output contains code")
        return True
    else:
        print("⚠️  Expected code not found in output")
        print(f"Output preview: {trace.output[:500]}")
        return False


if __name__ == "__main__":
    print("Starting integration tests...")
    print("=" * 60)

    # Test Claude Code
    claude_success = test_claude_code_real_call()

    print("\n" + "=" * 60)

    # Test Codex
    codex_success = test_codex_real_call()

    print("\n" + "=" * 60)
    print("\nTest Summary:")
    print(f"  Claude Code: {'✅ Passed' if claude_success else '❌ Failed'}")
    print(f"  Codex: {'✅ Passed' if codex_success else '❌ Failed'}")

    if claude_success and codex_success:
        print("\n🎉 All integration tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)
