#!/usr/bin/env python3
"""
Agent 调用器：统一封装 Claude Code 和 Codex 的调用接口
"""
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


@dataclass
class AgentTrace:
    """Agent 执行的 trace 记录"""
    agent_type: str  # claude_code, codex
    prompt: str
    output: str
    tokens_used: int
    exec_count: int
    duration_sec: float
    raw_trace: List[Dict[str, Any]]  # stream-json 格式的原始 trace
    error: Optional[str] = None


class AgentCaller:
    """统一的 Agent 调用接口"""

    def __init__(self, agent_type: str = "claude_code"):
        """
        初始化 Agent 调用器

        Args:
            agent_type: "claude_code" 或 "codex"
        """
        self.agent_type = agent_type

    def call(self, prompt: str, timeout: int = 600, trace_output_path: Optional[str] = None) -> AgentTrace:
        """
        调用 agent 并返回 trace

        Args:
            prompt: 输入的提示词
            timeout: 超时时间(秒)

        Returns:
            AgentTrace 对象
        """
        if self.agent_type == "claude_code":
            return self._call_claude_code(prompt, timeout, trace_output_path)
        elif self.agent_type == "codex":
            return self._call_codex(prompt, timeout, trace_output_path)
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    def _call_claude_code(self, prompt: str, timeout: int, trace_output_path: Optional[str] = None) -> AgentTrace:
        """调用 Claude Code"""
        import time
        import os
        start = time.time()

        # 使用指定的输出路径或创建临时文件保存 trace
        if trace_output_path:
            trace_path = trace_output_path
            # 确保目录存在
            Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as trace_file:
                trace_path = trace_file.name

        try:
            # 构建命令
            cmd = self._build_claude_command(prompt, trace_path)

            # 确定工作目录：如果 /testbed 存在则使用，否则使用当前目录
            work_dir = "/testbed" if os.path.exists("/testbed") else None

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir
            )

            duration = time.time() - start

            # 读取 trace
            raw_trace = self._read_trace_file(trace_path)

            # 解析输出 - Claude Code 的输出在 trace 中，不在 stdout
            output = self._extract_output_from_trace(raw_trace) if raw_trace else result.stdout
            tokens = self._extract_tokens_from_trace(raw_trace)
            exec_count = self._count_executions_from_trace(raw_trace)

            return AgentTrace(
                agent_type="claude_code",
                prompt=prompt,
                output=output,
                tokens_used=tokens,
                exec_count=exec_count,
                duration_sec=duration,
                raw_trace=raw_trace,
                error=result.stderr if result.returncode != 0 else None
            )

        except subprocess.TimeoutExpired:
            return AgentTrace(
                agent_type="claude_code",
                prompt=prompt,
                output="",
                tokens_used=0,
                exec_count=0,
                duration_sec=timeout,
                raw_trace=[],
                error="Timeout"
            )
        except Exception as e:
            return AgentTrace(
                agent_type="claude_code",
                prompt=prompt,
                output="",
                tokens_used=0,
                exec_count=0,
                duration_sec=time.time() - start,
                raw_trace=[],
                error=str(e)
            )
        finally:
            # 只清理临时文件（不清理指定的输出文件）
            if not trace_output_path:
                Path(trace_path).unlink(missing_ok=True)

    def _build_claude_command(self, prompt: str, trace_path: str) -> List[str]:
        """构建 Claude Code 命令"""
        return [
            "bash", "-c",
            f"claude -p --verbose --output-format stream-json {json.dumps(prompt)} > {trace_path}"
        ]

    def _build_codex_command(self, prompt: str, trace_path: str) -> List[str]:
        """构建 Codex 命令"""
        return [
            "bash", "-c",
            f"codex exec {json.dumps(prompt)} --json --skip-git-repo-check > {trace_path}"
        ]

    def _call_codex(self, prompt: str, timeout: int, trace_output_path: Optional[str] = None) -> AgentTrace:
        """调用 Codex"""
        import time
        import os
        start = time.time()

        # 使用指定的输出路径或创建临时文件保存 trace
        if trace_output_path:
            trace_path = trace_output_path
            # 确保目录存在
            Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as trace_file:
                trace_path = trace_file.name

        try:
            cmd = self._build_codex_command(prompt, trace_path)

            # 确定工作目录：如果 /testbed 存在则使用，否则使用当前目录
            work_dir = "/testbed" if os.path.exists("/testbed") else None

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir
            )

            duration = time.time() - start

            raw_trace = self._read_trace_file(trace_path)
            # Codex 的输出在 trace 中，不在 stdout
            output = self._extract_output_from_trace(raw_trace) if raw_trace else result.stdout
            tokens = self._extract_tokens_from_trace(raw_trace)
            exec_count = self._count_executions_from_trace(raw_trace)

            return AgentTrace(
                agent_type="codex",
                prompt=prompt,
                output=output,
                tokens_used=tokens,
                exec_count=exec_count,
                duration_sec=duration,
                raw_trace=raw_trace,
                error=result.stderr if result.returncode != 0 else None
            )

        except subprocess.TimeoutExpired:
            return AgentTrace(
                agent_type="codex",
                prompt=prompt,
                output="",
                tokens_used=0,
                exec_count=0,
                duration_sec=timeout,
                raw_trace=[],
                error="Timeout"
            )
        except Exception as e:
            return AgentTrace(
                agent_type="codex",
                prompt=prompt,
                output="",
                tokens_used=0,
                exec_count=0,
                duration_sec=time.time() - start,
                raw_trace=[],
                error=str(e)
            )
        finally:
            # 只清理临时文件（不清理指定的输出文件）
            if not trace_output_path:
                Path(trace_path).unlink(missing_ok=True)

    def _read_trace_file(self, trace_path: str) -> List[Dict[str, Any]]:
        """读取 stream-json 格式的 trace 文件"""
        traces = []
        try:
            with open(trace_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        traces.append(json.loads(line))
        except Exception as e:
            print(f"Warning: Failed to read trace file: {e}")
        return traces

    def _extract_tokens_from_trace(self, trace: List[Dict[str, Any]]) -> int:
        """从 trace 中提取 token 使用量"""
        total_tokens = 0
        for entry in trace:
            if "usage" in entry:
                usage = entry["usage"]
                total_tokens += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        return total_tokens

    def _count_executions_from_trace(self, trace: List[Dict[str, Any]]) -> int:
        """
        从 trace 中统计测试执行次数

        只统计 pytest/python 脚本运行，不统计普通 bash 命令（如 ls, cat, grep 等）
        """
        exec_count = 0
        for entry in trace:
            # 查找 Bash 工具调用
            if entry.get("type") == "tool_use" and entry.get("name") == "Bash":
                command = entry.get("input", {}).get("command", "")
                # 只统计测试运行和脚本执行
                if self._is_test_execution(command):
                    exec_count += 1
        return exec_count

    def _is_test_execution(self, command: str) -> bool:
        """
        判断命令是否为测试执行或脚本运行

        计入执行次数的命令：
        - pytest / py.test
        - unittest
        - Django tests (python manage.py test)
        - tox
        - nose / nosetests
        - python xxx.py (运行测试脚本)

        不计入的命令：
        - ls, cat, grep, find 等查看命令
        - git 命令
        - cd, pwd 等导航命令
        - python -c 简单命令
        - python --version 等信息查询
        """
        command = command.strip().lower()

        # 测试框架命令
        test_patterns = [
            'pytest',
            'python -m pytest',
            'python3 -m pytest',
            'py.test',
            'unittest',
            'python -m unittest',
            'python3 -m unittest',
            'manage.py test',  # Django tests
            'python manage.py test',
            'python3 manage.py test',
            'tox',
            'nose',
            'nosetests',
            'python -m nose',
            'python3 -m nose',
        ]

        for pattern in test_patterns:
            if pattern in command:
                return True

        # Python 脚本执行（但排除一些常见的非执行命令）
        if command.startswith('python ') or command.startswith('python3 '):
            # 排除 python -c (通常用于简单计算或查看)
            if ' -c ' in command:
                return False
            # 排除 python --version 等信息查询
            if '--version' in command or '--help' in command:
                return False
            # 如果是运行 .py 文件，计入
            if '.py' in command:
                return True

        return False

    def _extract_output_from_trace(self, trace: List[Dict[str, Any]]) -> str:
        """从 trace 中提取输出文本"""
        output_parts = []
        for entry in trace:
            # Codex 格式: item.completed -> item.text
            if entry.get("type") == "item.completed":
                item = entry.get("item", {})
                if item.get("type") == "agent_message":
                    text = item.get("text", "")
                    if text:
                        output_parts.append(text)

            # Claude Code 格式: assistant -> message.content[].text
            if entry.get("type") == "assistant":
                message = entry.get("message", {})
                content = message.get("content", [])
                for item in content:
                    if item.get("type") == "text":
                        text = item.get("text", "")
                        if text:
                            output_parts.append(text)

        return "\n".join(output_parts)


def save_trace(trace: AgentTrace, output_path: Path):
    """保存 trace 到文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存完整的 trace 数据
    trace_data = {
        "agent_type": trace.agent_type,
        "prompt": trace.prompt,
        "output": trace.output,
        "tokens_used": trace.tokens_used,
        "exec_count": trace.exec_count,
        "duration_sec": trace.duration_sec,
        "error": trace.error,
        "raw_trace": trace.raw_trace
    }

    with open(output_path, 'w') as f:
        json.dump(trace_data, f, indent=2, ensure_ascii=False)

    print(f"Trace saved to: {output_path}")


# 示例用法
if __name__ == "__main__":
    # 测试 Claude Code 调用
    caller = AgentCaller(agent_type="claude_code")

    test_prompt = "请帮我写一个 Python 函数，计算斐波那契数列的第 n 项"

    print(f"Calling {caller.agent_type}...")
    trace = caller.call(test_prompt)

    print(f"\nAgent: {trace.agent_type}")
    print(f"Tokens used: {trace.tokens_used}")
    print(f"Executions: {trace.exec_count}")
    print(f"Duration: {trace.duration_sec:.2f}s")
    print(f"Output length: {len(trace.output)} chars")

    if trace.error:
        print(f"Error: {trace.error}")

    # 保存 trace
    save_trace(trace, Path("test_trace.json"))
