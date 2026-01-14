#!/usr/bin/env python3
"""
集成测试：真实调用 Claude Code 和 Codex
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_caller import AgentCaller, save_trace


def test_claude_code_real_call():
    """测试真实调用 Claude Code"""
    print("\n=== 测试 Claude Code 真实调用 ===")

    caller = AgentCaller(agent_type="claude_code")
    prompt = "请用 Python 写一个函数计算两个数的和，函数名为 add"

    print(f"Prompt: {prompt}")
    print("调用中...")

    trace = caller.call(prompt, timeout=60)

    print(f"\n结果:")
    print(f"  Agent: {trace.agent_type}")
    print(f"  Tokens: {trace.tokens_used}")
    print(f"  执行次数: {trace.exec_count}")
    print(f"  耗时: {trace.duration_sec:.2f}s")
    print(f"  输出长度: {len(trace.output)} 字符")

    if trace.error:
        print(f"  错误: {trace.error}")
        return False

    # 保存 trace
    output_path = Path(__file__).parent / "claude_code_trace.json"
    save_trace(trace, output_path)
    print(f"  Trace 已保存到: {output_path}")

    # 验证输出包含代码
    if "def add" in trace.output or "def" in trace.output:
        print("✅ Claude Code 调用成功，输出包含代码")
        return True
    else:
        print("⚠️  输出中未找到预期的代码")
        print(f"输出预览: {trace.output[:500]}")
        return False


def test_codex_real_call():
    """测试真实调用 Codex"""
    print("\n=== 测试 Codex 真实调用 ===")

    caller = AgentCaller(agent_type="codex")
    prompt = "请用 Python 写一个函数计算两个数的和，函数名为 add"

    print(f"Prompt: {prompt}")
    print("调用中...")

    trace = caller.call(prompt, timeout=60)

    print(f"\n结果:")
    print(f"  Agent: {trace.agent_type}")
    print(f"  Tokens: {trace.tokens_used}")
    print(f"  执行次数: {trace.exec_count}")
    print(f"  耗时: {trace.duration_sec:.2f}s")
    print(f"  输出长度: {len(trace.output)} 字符")

    if trace.error:
        print(f"  错误: {trace.error}")
        return False

    # 保存 trace
    output_path = Path(__file__).parent / "codex_trace.json"
    save_trace(trace, output_path)
    print(f"  Trace 已保存到: {output_path}")

    # 验证输出包含代码
    if "def add" in trace.output or "def" in trace.output:
        print("✅ Codex 调用成功，输出包含代码")
        return True
    else:
        print("⚠️  输出中未找到预期的代码")
        print(f"输出预览: {trace.output[:500]}")
        return False


if __name__ == "__main__":
    print("开始集成测试...")
    print("=" * 60)

    # 测试 Claude Code
    claude_success = test_claude_code_real_call()

    print("\n" + "=" * 60)

    # 测试 Codex
    codex_success = test_codex_real_call()

    print("\n" + "=" * 60)
    print("\n测试总结:")
    print(f"  Claude Code: {'✅ 通过' if claude_success else '❌ 失败'}")
    print(f"  Codex: {'✅ 通过' if codex_success else '❌ 失败'}")

    if claude_success and codex_success:
        print("\n🎉 所有集成测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️  部分测试失败")
        sys.exit(1)
