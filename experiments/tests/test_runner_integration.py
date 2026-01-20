#!/usr/bin/env python3
"""
Runner Integration Tests - Actually calls Claude Code/Codex

Note: These tests will actually call Claude Code/Codex API, therefore:
- Execution time is long (each test may take several minutes)
- Will consume API quota
- Requires network connection
- Results may vary depending on API response

How to run:
    pytest test_runner_integration.py -v -s --tb=short

Skip integration tests:
    pytest test_runner.py -v  # Only run unit tests
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from runner import run_experiment, ExperimentResult
from agent_caller import AgentCaller
from prompt_builder import PromptBuilder


# Mark as integration test, can be skipped with pytest -m "not integration"
pytestmark = pytest.mark.integration


class TestRunnerIntegration:
    """Integration Tests - Actually calls Claude Code"""

    @pytest.fixture
    def mock_simple_instance(self):
        """Create a simple test instance (no real SWE-bench data needed)"""
        return {
            "instance_id": "integration-test-1",
            "problem_statement": "Write a Python function that calculates the sum of two numbers",
            "repo": "test/repo",
            "base_commit": "abc123"
        }

    @patch('runner.get_instance_info')
    def test_integration_simple_task(self, mock_get_instance, mock_simple_instance):
        """
        Integration test: Test complete workflow with simple task

        This test will actually call Claude Code to verify:
        1. PromptBuilder can correctly build prompt
        2. AgentCaller can successfully call Claude Code
        3. Can extract results from output
        4. The entire workflow works properly
        """
        # Mock instance info (avoid loading real dataset)
        mock_get_instance.return_value = mock_simple_instance

        # Run experiment (actually call Claude Code)
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('runner.RESULTS_DIR', Path(tmpdir)):
                result = run_experiment(
                    instance_id="integration-test-1",
                    mode="run_free",
                    agent_type="claude_code",
                    timeout=120  # 2 minute timeout
                )

        # Verify results
        assert isinstance(result, ExperimentResult)
        assert result.instance_id == "integration-test-1"
        assert result.mode == "run_free"
        assert result.agent_type == "claude_code"

        # Verify there is output
        assert result.tokens_used > 0, "Should have token usage"
        assert result.duration_sec > 0, "Should have execution time"

        # Verify output is not empty
        assert len(result.patch) > 0 or result.error, "Should have patch or error message"

        print(f"\nIntegration test results:")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Duration: {result.duration_sec:.2f}s")
        print(f"  Success: {result.success}")
        print(f"  Patch length: {len(result.patch)}")
        if result.error:
            print(f"  Error: {result.error[:200]}")

    def test_agent_caller_direct(self):
        """
        Directly test if AgentCaller can call Claude Code

        This is the most basic integration test, verifying AgentCaller itself works
        """
        caller = AgentCaller(agent_type="claude_code")

        # Use a very simple prompt
        prompt = "Please answer in one sentence: What is 1+1?"

        trace = caller.call(prompt, timeout=60)

        # Verify basic information
        assert trace.agent_type == "claude_code"
        assert trace.tokens_used > 0, "Should have token usage"
        assert len(trace.output) > 0 or trace.error, "Should have output or error"

        print(f"\nAgentCaller direct call results:")
        print(f"  Tokens: {trace.tokens_used}")
        print(f"  Duration: {trace.duration_sec:.2f}s")
        print(f"  Output length: {len(trace.output)}")
        print(f"  Exec count: {trace.exec_count}")
        if trace.error:
            print(f"  Error: {trace.error[:200]}")

    def test_prompt_builder_integration(self, mock_simple_instance):
        """
        Test if PromptBuilder generates reasonable prompts

        Although not calling API, verify the structure of prompts
        """
        # Test three modes
        modes = ["run_free", "run_less", "run_full"]

        for mode in modes:
            prompt = PromptBuilder.build_prompt(
                mock_simple_instance,
                mode,
                k=2 if mode == "run_less" else 0
            )

            # Verify prompt contains key information
            assert "Write a Python function that calculates the sum of two numbers" in prompt
            assert "test/repo" in prompt

            # Verify mode-specific content
            if mode == "run_free":
                assert "cannot execute" in prompt or "cannot run" in prompt
            elif mode == "run_less":
                assert "2" in prompt  # k=2
                assert "execution" in prompt or "run" in prompt
            elif mode == "run_full":
                assert "free" in prompt or "can" in prompt

            print(f"\n{mode} prompt length: {len(prompt)} characters")


@pytest.mark.slow
class TestRunnerIntegrationSlow:
    """
    Slow Integration Tests - Using real SWE-bench data

    These tests require longer time, only run when needed:
        pytest test_runner_integration.py -v -s -m slow
    """

    @pytest.mark.skip(reason="Requires real SWE-bench dataset, run manually")
    def test_real_swebench_instance(self):
        """
        Test with real SWE-bench instance

        Note: This test requires:
        1. Real SWE-bench dataset
        2. Long execution time (possibly 5-10 minutes)
        3. Large token consumption
        """
        # Use a simple SWE-bench instance
        instance_id = "django__django-11099"  # Replace with actual instance ID

        result = run_experiment(
            instance_id=instance_id,
            mode="run_free",
            agent_type="claude_code",
            timeout=600  # 10 minute timeout
        )

        assert result.success or result.error
        print(f"\nReal SWE-bench test results:")
        print(f"  Instance: {result.instance_id}")
        print(f"  Tokens: {result.tokens_used}")
        print(f"  Duration: {result.duration_sec:.2f}s")
        print(f"  Success: {result.success}")


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "-s", "--tb=short"])
