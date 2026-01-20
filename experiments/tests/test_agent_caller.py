#!/usr/bin/env python3
"""
Test Agent Caller
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_caller import AgentCaller, AgentTrace, save_trace


class TestAgentCaller:
    """Test AgentCaller class"""

    def test_init_claude_code(self):
        """Test initializing Claude Code caller"""
        caller = AgentCaller(agent_type="claude_code")
        assert caller.agent_type == "claude_code"

    def test_init_codex(self):
        """Test initializing Codex caller"""
        caller = AgentCaller(agent_type="codex")
        assert caller.agent_type == "codex"

    def test_build_claude_command(self):
        """Test building Claude Code command"""
        caller = AgentCaller(agent_type="claude_code")
        prompt = "test prompt"
        trace_path = "/tmp/trace.jsonl"

        cmd = caller._build_claude_command(prompt, trace_path)

        assert cmd[0] == "bash"
        assert cmd[1] == "-c"
        assert "claude -p" in cmd[2]
        assert "--verbose" in cmd[2]
        assert "--output-type stream-json" in cmd[2]
        assert trace_path in cmd[2]

    def test_build_codex_command(self):
        """Test building Codex command"""
        caller = AgentCaller(agent_type="codex")
        prompt = "test prompt"
        trace_path = "/tmp/trace.jsonl"

        cmd = caller._build_codex_command(prompt, trace_path)

        assert cmd[0] == "bash"
        assert cmd[1] == "-c"
        assert "codex exec" in cmd[2]
        assert "--json" in cmd[2]
        assert trace_path in cmd[2]

    def test_extract_tokens_from_trace(self):
        """Test extracting tokens from trace"""
        caller = AgentCaller()
        trace = [
            {"type": "message", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {"type": "message", "usage": {"input_tokens": 200, "output_tokens": 100}},
        ]

        tokens = caller._extract_tokens_from_trace(trace)
        assert tokens == 450  # 100 + 50 + 200 + 100

    def test_count_executions_from_trace(self):
        """Test counting executions from trace"""
        caller = AgentCaller()
        trace = [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
            {"type": "tool_use", "name": "Read", "input": {"file": "test.py"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "pwd"}},
        ]

        exec_count = caller._count_executions_from_trace(trace)
        assert exec_count == 2  # Only Bash tool calls

    def test_read_trace_file(self):
        """Test reading trace file"""
        caller = AgentCaller()

        # Create temporary trace file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"type": "message", "content": "test1"}\n')
            f.write('{"type": "message", "content": "test2"}\n')
            trace_path = f.name

        try:
            traces = caller._read_trace_file(trace_path)
            assert len(traces) == 2
            assert traces[0]["content"] == "test1"
            assert traces[1]["content"] == "test2"
        finally:
            Path(trace_path).unlink()

    @patch('agent_caller.subprocess.run')
    def test_call_claude_code_success(self, mock_run):
        """Test successfully calling Claude Code"""
        # Mock subprocess return
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Claude Code output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        caller = AgentCaller(agent_type="claude_code")

        with patch.object(caller, '_read_trace_file', return_value=[
            {"type": "message", "usage": {"input_tokens": 100, "output_tokens": 50}}
        ]):
            trace = caller.call("test prompt", timeout=10)

        assert trace.agent_type == "claude_code"
        assert trace.output == "Claude Code output"
        assert trace.tokens_used == 150
        assert trace.error is None

    @patch('agent_caller.subprocess.run')
    def test_call_codex_success(self, mock_run):
        """Test successfully calling Codex"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Codex output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        caller = AgentCaller(agent_type="codex")

        with patch.object(caller, '_read_trace_file', return_value=[
            {"type": "message", "usage": {"input_tokens": 200, "output_tokens": 100}}
        ]):
            trace = caller.call("test prompt", timeout=10)

        assert trace.agent_type == "codex"
        assert trace.output == "Codex output"
        assert trace.tokens_used == 300
        assert trace.error is None

    def test_save_trace(self):
        """Test saving trace"""
        trace = AgentTrace(
            agent_type="claude_code",
            prompt="test prompt",
            output="test output",
            tokens_used=100,
            exec_count=2,
            duration_sec=5.5,
            raw_trace=[{"type": "test"}],
            error=None
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_trace.json"
            save_trace(trace, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert data["agent_type"] == "claude_code"
            assert data["tokens_used"] == 100
            assert data["exec_count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
