#!/usr/bin/env python3
"""
Runner 集成测试 - 真正调用 Claude Code/Codex

注意：这些测试会真正调用 Claude Code/Codex API，因此：
- 执行时间较长（每个测试可能需要几分钟）
- 会消耗 API 配额
- 需要网络连接
- 结果可能因 API 响应而有所不同

运行方式：
    pytest test_runner_integration.py -v -s --tb=short

跳过集成测试：
    pytest test_runner.py -v  # 只运行单元测试
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import run_experiment, ExperimentResult
from agent_caller import AgentCaller
from prompt_builder import PromptBuilder


# 标记为集成测试，可以通过 pytest -m "not integration" 跳过
pytestmark = pytest.mark.integration


class TestRunnerIntegration:
    """集成测试 - 真正调用 Claude Code"""

    @pytest.fixture
    def mock_simple_instance(self):
        """创建一个简单的测试实例（不需要真实的 SWE-bench 数据）"""
        return {
            "instance_id": "integration-test-1",
            "problem_statement": "写一个 Python 函数，计算两个数的和",
            "repo": "test/repo",
            "base_commit": "abc123"
        }

    @patch('runner.get_instance_info')
    def test_integration_simple_task(self, mock_get_instance, mock_simple_instance):
        """
        集成测试：使用简单任务测试完整流程

        这个测试会真正调用 Claude Code，验证：
        1. PromptBuilder 能正确构建 prompt
        2. AgentCaller 能成功调用 Claude Code
        3. 能从输出中提取结果
        4. 整个流程能正常工作
        """
        # Mock 实例信息（避免加载真实数据集）
        mock_get_instance.return_value = mock_simple_instance

        # 运行实验（真正调用 Claude Code）
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('runner.RESULTS_DIR', Path(tmpdir)):
                result = run_experiment(
                    instance_id="integration-test-1",
                    mode="run_free",
                    agent_type="claude_code",
                    timeout=120  # 2分钟超时
                )

        # 验证结果
        assert isinstance(result, ExperimentResult)
        assert result.instance_id == "integration-test-1"
        assert result.mode == "run_free"
        assert result.agent_type == "claude_code"

        # 验证有输出
        assert result.tokens_used > 0, "应该有 token 使用量"
        assert result.duration_sec > 0, "应该有执行时间"

        # 验证输出不为空
        assert len(result.patch) > 0 or result.error, "应该有补丁或错误信息"

        print(f"\n集成测试结果:")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Duration: {result.duration_sec:.2f}s")
        print(f"  Success: {result.success}")
        print(f"  Patch length: {len(result.patch)}")
        if result.error:
            print(f"  Error: {result.error[:200]}")

    def test_agent_caller_direct(self):
        """
        直接测试 AgentCaller 能否调用 Claude Code

        这是最基础的集成测试，验证 AgentCaller 本身能工作
        """
        caller = AgentCaller(agent_type="claude_code")

        # 使用一个非常简单的 prompt
        prompt = "请用一句话回答：1+1等于几？"

        trace = caller.call(prompt, timeout=60)

        # 验证基本信息
        assert trace.agent_type == "claude_code"
        assert trace.tokens_used > 0, "应该有 token 使用"
        assert len(trace.output) > 0 or trace.error, "应该有输出或错误"

        print(f"\nAgentCaller 直接调用结果:")
        print(f"  Tokens: {trace.tokens_used}")
        print(f"  Duration: {trace.duration_sec:.2f}s")
        print(f"  Output length: {len(trace.output)}")
        print(f"  Exec count: {trace.exec_count}")
        if trace.error:
            print(f"  Error: {trace.error[:200]}")

    def test_prompt_builder_integration(self, mock_simple_instance):
        """
        测试 PromptBuilder 生成的 prompt 是否合理

        虽然不调用 API，但验证 prompt 的结构
        """
        # 测试三种模式
        modes = ["run_free", "run_less", "run_full"]

        for mode in modes:
            prompt = PromptBuilder.build_prompt(
                mock_simple_instance,
                mode,
                k=2 if mode == "run_less" else 0
            )

            # 验证 prompt 包含关键信息
            assert "写一个 Python 函数，计算两个数的和" in prompt
            assert "test/repo" in prompt

            # 验证模式特定的内容
            if mode == "run_free":
                assert "不能执行" in prompt or "不能运行" in prompt
            elif mode == "run_less":
                assert "2" in prompt  # k=2
                assert "执行" in prompt
            elif mode == "run_full":
                assert "自由" in prompt or "可以" in prompt

            print(f"\n{mode} prompt 长度: {len(prompt)} 字符")


@pytest.mark.slow
class TestRunnerIntegrationSlow:
    """
    慢速集成测试 - 使用真实的 SWE-bench 数据

    这些测试需要更长时间，只在需要时运行：
        pytest test_runner_integration.py -v -s -m slow
    """

    @pytest.mark.skip(reason="需要真实的 SWE-bench 数据集，手动运行")
    def test_real_swebench_instance(self):
        """
        使用真实的 SWE-bench 实例测试

        注意：这个测试需要：
        1. 真实的 SWE-bench 数据集
        2. 较长的执行时间（可能 5-10 分钟）
        3. 大量的 token 消耗
        """
        # 使用一个简单的 SWE-bench 实例
        instance_id = "django__django-11099"  # 替换为实际的实例 ID

        result = run_experiment(
            instance_id=instance_id,
            mode="run_free",
            agent_type="claude_code",
            timeout=600  # 10分钟超时
        )

        assert result.success or result.error
        print(f"\n真实 SWE-bench 测试结果:")
        print(f"  Instance: {result.instance_id}")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Duration: {result.duration_sec:.2f}s")
        print(f"  Success: {result.success}")


if __name__ == "__main__":
    # 运行集成测试
    pytest.main([__file__, "-v", "-s", "--tb=short"])
