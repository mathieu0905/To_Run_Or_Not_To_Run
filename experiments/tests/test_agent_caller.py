#!/usr/bin/env python3
"""
测试 Agent 调用器
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_caller import AgentCaller, AgentTrace, save_trace


class TestAgentCaller:
    """测试 AgentCaller 类"""

    def test_init_claude_code(self):
        """测试初始化 Claude Code 调用器"""
        caller = AgentCaller(agent_type="claude_code")
        assert caller.agent_type == "claude_code"

    def test_init_codex(self):
        """测试初始化 Codex 调用器"""
        caller = AgentCaller(agent_type="codex")
        assert caller.agent_type == "codex"

    def test_build_claude_command(self):
        """测试构建 Claude Code 命令"""
        caller = AgentCaller(agent_type="claude_code")
        prompt = "测试提示词"
        trace_path = "/tmp/trace.jsonl"

        cmd = caller._build_claude_command(prompt, trace_path)

        assert cmd[0] == "bash"
        assert cmd[1] == "-c"
        assert "claude -p" in cmd[2]
        assert "--verbose" in cmd[2]
        assert "--output-type stream-json" in cmd[2]
        assert trace_path in cmd[2]

    def test_build_codex_command(self):
        """测试构建 Codex 命令"""
        caller = AgentCaller(agent_type="codex")
        prompt = "测试提示词"
        trace_path = "/tmp/trace.jsonl"

        cmd = caller._build_codex_command(prompt, trace_path)

        assert cmd[0] == "bash"
        assert cmd[1] == "-c"
        assert "codex exec" in cmd[2]
        assert "--json" in cmd[2]
        assert trace_path in cmd[2]

    def test_extract_tokens_from_trace(self):
        """测试从 trace 中提取 token"""
        caller = AgentCaller()
        trace = [
            {"type": "message", "usage": {"input_tokens": 100, "output_tokens": 50}},
            {"type": "message", "usage": {"input_tokens": 200, "output_tokens": 100}},
        ]

        tokens = caller._extract_tokens_from_trace(trace)
        assert tokens == 450  # 100 + 50 + 200 + 100

    def test_count_executions_from_trace(self):
        """测试从 trace 中统计执行次数"""
        caller = AgentCaller()
        trace = [
            {"type": "tool_use", "name": "Bash", "input": {"command": "ls"}},
            {"type": "tool_use", "name": "Read", "input": {"file": "test.py"}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "pwd"}},
        ]

        exec_count = caller._count_executions_from_trace(trace)
        assert exec_count == 2  # 只有 Bash 工具调用

    def test_read_trace_file(self):
        """测试读取 trace 文件"""
        caller = AgentCaller()

        # 创建临时 trace 文件
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
        """测试成功调用 Claude Code"""
        # Mock subprocess 返回
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Claude Code 输出"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        caller = AgentCaller(agent_type="claude_code")

        with patch.object(caller, '_read_trace_file', return_value=[
            {"type": "message", "usage": {"input_tokens": 100, "output_tokens": 50}}
        ]):
            trace = caller.call("测试提示词", timeout=10)

        assert trace.agent_type == "claude_code"
        assert trace.output == "Claude Code 输出"
        assert trace.tokens_used == 150
        assert trace.error is None

    @patch('agent_caller.subprocess.run')
    def test_call_codex_success(self, mock_run):
        """测试成功调用 Codex"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Codex 输出"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        caller = AgentCaller(agent_type="codex")

        with patch.object(caller, '_read_trace_file', return_value=[
            {"type": "message", "usage": {"input_tokens": 200, "output_tokens": 100}}
        ]):
            trace = caller.call("测试提示词", timeout=10)

        assert trace.agent_type == "codex"
        assert trace.output == "Codex 输出"
        assert trace.tokens_used == 300
        assert trace.error is None

    def test_save_trace(self):
        """测试保存 trace"""
        trace = AgentTrace(
            agent_type="claude_code",
            prompt="测试提示词",
            output="测试输出",
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
