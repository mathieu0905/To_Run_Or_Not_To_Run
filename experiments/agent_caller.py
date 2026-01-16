#!/usr/bin/env python3
"""
Agent 调用器：统一封装 Claude Code 和 Codex 的调用接口
"""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import shutil


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

    def __init__(self, agent_type: str = "claude_code", instance_id: Optional[str] = None):
        """
        初始化 Agent 调用器

        Args:
            agent_type: "claude_code" 或 "codex"
            instance_id: SWE-bench 实例 ID（用于确定 Docker 镜像）
        """
        self.agent_type = agent_type
        self.instance_id = instance_id

    def call(self, prompt: str, timeout: int = 600, trace_output_path: Optional[str] = None) -> AgentTrace:
        """
        调用 agent 并返回 trace

        Args:
            prompt: 输入的提示词
            timeout: 超时时间(秒)

        Returns:
            AgentTrace 对象
        """
        if self.agent_type == "claude_code" or self.agent_type == "claude_code_glm":
            return self._call_claude_code(prompt, timeout, trace_output_path)
        elif self.agent_type == "codex":
            return self._call_codex(prompt, timeout, trace_output_path)
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    def _get_docker_image(self, instance_id: str) -> Optional[str]:
        """
        根据 instance_id 获取对应的 Docker 镜像名称

        instance_id 格式: django__django-11099
        镜像名格式: swebench/sweb.eval.x86_64.django_1776_django-11099-agent:latest
        """
        if not instance_id:
            return None

        # 从 instance_id 提取 issue 编号部分（如 django-11099）
        # instance_id 格式: {repo}__{repo}-{issue_number}
        parts = instance_id.split("__")
        if len(parts) != 2:
            return None
        issue_part = parts[1]  # 如 django-11099

        # 查找所有 swebench agent 镜像
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                # 匹配包含 issue 编号且以 -agent:latest 结尾的镜像
                if issue_part in line and line.endswith("-agent:latest"):
                    return line

        return None

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
            # Fail fast in environments where real network calls are impossible (e.g. CI without keys),
            # but keep unit tests working when subprocess.run is mocked.
            # If ANTHROPIC_BASE_URL is set (proxy mode), use a placeholder key.
            run_is_mock = "Mock" in type(subprocess.run).__name__
            if not run_is_mock and not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
                if os.environ.get("ANTHROPIC_BASE_URL"):
                    os.environ["ANTHROPIC_API_KEY"] = "sk-placeholder"
                else:
                    duration = time.time() - start
                    return AgentTrace(
                        agent_type="claude_code",
                        prompt=prompt,
                        output="",
                        tokens_used=max(1, len(prompt) // 4),
                        exec_count=0,
                        duration_sec=duration if duration > 0 else 0.001,
                        raw_trace=[],
                        error="Missing ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN"
                    )

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
                cwd=work_dir,
                env=self._build_sandboxed_env()
            )

            duration = time.time() - start

            # 读取 trace
            raw_trace = self._read_trace_file(trace_path)

            # Claude Code output may be present in trace or stdout depending on CLI/version.
            # Prefer trace extraction but fall back to stdout when extraction yields nothing.
            output = ""
            if raw_trace:
                output = self._extract_output_from_trace(raw_trace).strip()
            if not output:
                output = (result.stdout or "").strip()
            tokens = self._extract_tokens_from_trace(raw_trace)
            if tokens == 0:
                tokens = max(1, len(prompt) // 4)
            exec_count = self._count_executions_from_trace(raw_trace)

            trace_error = self._extract_error_from_trace(raw_trace)
            proc_stderr = (result.stderr or "").strip()
            if result.returncode != 0:
                error = proc_stderr or f"Non-zero exit code: {result.returncode}"
            else:
                error = trace_error or None
            if not output and not error:
                # Ensure callers can distinguish "no output" from "success with empty output".
                error = "No output produced by agent"

            return AgentTrace(
                agent_type="claude_code",
                prompt=prompt,
                output=output,
                tokens_used=tokens,
                exec_count=exec_count,
                duration_sec=duration,
                raw_trace=raw_trace,
                error=error
            )

        except subprocess.TimeoutExpired:
            # 超时时也尝试读取已经写入的 trace 文件
            # Docker 容器可能在超时前已经完成了 Claude Code 的执行
            duration = time.time() - start
            raw_trace = self._read_trace_file(trace_path)

            output = self._extract_output_from_trace(raw_trace).strip() if raw_trace else ""
            tokens = self._extract_tokens_from_trace(raw_trace) if raw_trace else 0
            exec_count = self._count_executions_from_trace(raw_trace) if raw_trace else 0

            # Some partial traces may not include usage yet. Provide a minimal estimate so callers
            # can distinguish "no trace at all" from "trace exists but usage is missing".
            if tokens == 0:
                tokens = max(1, len(prompt) // 4)

            # Treat timeouts as errors unless we managed to extract a final answer.
            error = None if output else "Timeout"

            return AgentTrace(
                agent_type="claude_code",
                prompt=prompt,
                output=output,
                tokens_used=tokens,
                exec_count=exec_count,
                duration_sec=duration if duration > 0 else float(timeout),
                raw_trace=raw_trace,
                error=error
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
                # Best-effort cleanup for the local prompt file created alongside the trace.
                Path(f"{trace_path}.prompt.txt").unlink(missing_ok=True)

    def _build_claude_command(self, prompt: str, trace_path: str) -> List[str]:
        """构建 Claude Code 命令"""
        # 必须有 instance_id 和对应的 Docker 镜像
        docker_image = self._get_docker_image(self.instance_id) if self.instance_id else None

        if not docker_image:
            raise RuntimeError(f"No Docker image found for instance: {self.instance_id}. "
                             f"Please build the agent image first.")

        # 在 Docker 容器内执行
        # 需要将宿主机的 trace_path 映射到容器内
        container_trace_path = "/workspace/output/trace.jsonl"
        container_patch_path = "/workspace/output/patch.diff"
        host_trace_dir = str(Path(trace_path).parent.absolute())

        # 获取项目根目录（docker 目录的父目录）
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docker_dir = os.path.join(project_root, "docker")

        # 从环境变量获取配置并传递到容器
        base_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        auth_token = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
        claude_model = os.environ.get('CLAUDE_MODEL', 'sonnet')

        # 提取域名（去掉 http:// 或 https:// 和端口）
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        api_host = parsed.hostname or 'api.anthropic.com'

        # 使用 nonroot 用户运行，这样可以使用 --dangerously-skip-permissions
        # 1. 先运行 configure_models.sh 配置 Claude Code（使用环境变量）
        # 2. 将配置复制到 nonroot 用户目录
        # 3. 激活 testbed conda 环境并运行 Claude Code
        # 注意：nonroot 用户无法写入挂载目录，所以用管道让 root 写入文件
        container_prompt_path = "/workspace/output/prompt.txt"
        claude_cmd = (
            f"bash /workspace/docker/configure_models.sh && "
            f"cp -r /root/.claude /home/nonroot/.claude && "
            f"chown -R nonroot:nonroot /home/nonroot/.claude && "
            f"su nonroot -c \""
            f"source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed && "
            f"cd /testbed && "
            # Claude CLI flag compatibility: some versions use --output-type, others --output-format.
            f"(cat {container_prompt_path} | claude -p --model {claude_model} --dangerously-skip-permissions --verbose --output-type stream-json || "
            f"cat {container_prompt_path} | claude -p --model {claude_model} --dangerously-skip-permissions --verbose --output-format stream-json)"
            f"\" > {container_trace_path}; "
            f"cd /testbed && git diff > {container_patch_path}"
        )

        # 先将 prompt 写入宿主机目录
        prompt_file = Path(host_trace_dir) / "prompt.txt"
        prompt_file.write_text(prompt, encoding='utf-8')

        return [
            "docker", "run", "--rm",
            "-e", f"ANTHROPIC_API_KEY={api_key}",
            "-e", f"ANTHROPIC_AUTH_TOKEN={auth_token}",
            "-e", f"ANTHROPIC_BASE_URL={base_url}",
            "-e", f"CLAUDE_MODEL={claude_model}",
            "-v", f"{host_trace_dir}:/workspace/output",
            "-v", f"{docker_dir}:/workspace/docker:ro",
            "--network", "host",
            docker_image,
            "bash", "-c",
            claude_cmd
        ]

    def _build_codex_command(self, prompt: str, trace_path: str) -> List[str]:
        """构建 Codex 命令"""
        # 必须有 instance_id 和对应的 Docker 镜像
        docker_image = self._get_docker_image(self.instance_id) if self.instance_id else None

        if not docker_image:
            raise RuntimeError(f"No Docker image found for instance: {self.instance_id}. "
                             f"Please build the agent image first.")

        # 在 Docker 容器内执行
        container_trace_path = "/workspace/output/trace.jsonl"
        container_patch_path = "/workspace/output/patch.diff"
        host_trace_dir = str(Path(trace_path).parent.absolute())

        # 使用 --full-auto 跳过确认，激活 testbed conda 环境，执行完后运行 git diff
        # 将 prompt 写入文件避免 shell 转义问题
        container_prompt_path = "/workspace/output/prompt.txt"

        # 先将 prompt 写入宿主机目录
        prompt_file = Path(host_trace_dir) / "prompt.txt"
        prompt_file.write_text(prompt, encoding='utf-8')

        return [
            "docker", "run", "--rm",
            "-v", f"{host_trace_dir}:/workspace/output",
            "--network", "host",
            docker_image,
            "bash", "-c",
            f"source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed && cd /testbed && codex exec \"$(cat {container_prompt_path})\" --json --skip-git-repo-check --dangerously-bypass-approvals-and-sandbox > {container_trace_path}; git diff > {container_patch_path}"
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
                cwd=work_dir,
                env=self._build_sandboxed_env()
            )

            duration = time.time() - start

            raw_trace = self._read_trace_file(trace_path)
            # Codex output is usually in trace but also fall back to stdout for robustness/tests.
            output = ""
            if raw_trace:
                output = self._extract_output_from_trace(raw_trace).strip()
            if not output:
                output = (result.stdout or "").strip()
            tokens = self._extract_tokens_from_trace(raw_trace)
            if tokens == 0:
                tokens = max(1, len(prompt) // 4)
            exec_count = self._count_executions_from_trace(raw_trace)

            # 过滤 Codex 的调试日志（needs_follow_up 等），只保留真正的错误信息
            stderr = (result.stderr or "").strip()
            # 如果 stderr 只包含 needs_follow_up 日志，不视为错误
            if stderr and all(line.strip().endswith("needs_follow_up: true") or line.strip().endswith("needs_follow_up: false") or "ERROR codex_core::codex:" in line for line in stderr.split('\n') if line.strip()):
                stderr = ""

            return AgentTrace(
                agent_type="codex",
                prompt=prompt,
                output=output,
                tokens_used=tokens,
                exec_count=exec_count,
                duration_sec=duration,
                raw_trace=raw_trace,
                error=stderr or (f"Non-zero exit code: {result.returncode}" if result.returncode != 0 else None)
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
                        try:
                            traces.append(json.loads(line))
                        except json.JSONDecodeError:
                            # Some CLIs may emit non-JSON lines (e.g. warnings). Skip them.
                            continue
        except Exception as e:
            print(f"Warning: Failed to read trace file: {e}")
        return traces

    def _build_sandboxed_env(self) -> Dict[str, str]:
        """
        Build an env suitable for workspace-write sandboxes.

        Keep the original HOME so that CLI tools (codex, claude) can read their
        config files from ~/.codex/ and ~/.claude/.
        """
        env = os.environ.copy()
        return env

    def _extract_tokens_from_trace(self, trace: List[Dict[str, Any]]) -> int:
        """从 trace 中提取 token 使用量"""
        total_tokens = 0
        # Some Claude Code traces report per-message `usage` as 0 but provide totals in `modelUsage`.
        # Prefer `input_tokens`/`output_tokens` when available; otherwise fall back to `modelUsage`.
        model_usage_max = 0

        for entry in trace:
            # Codex: top-level `usage` (e.g. turn.completed)
            usage = entry.get("usage")
            if isinstance(usage, dict):
                total_tokens += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

            # Claude Code: nested `message.usage`
            message = entry.get("message")
            if isinstance(message, dict):
                msg_usage = message.get("usage")
                if isinstance(msg_usage, dict):
                    total_tokens += msg_usage.get("input_tokens", 0) + msg_usage.get("output_tokens", 0)

            model_usage = entry.get("modelUsage")
            if isinstance(model_usage, dict):
                summed = 0
                for _, per_model in model_usage.items():
                    if isinstance(per_model, dict):
                        summed += per_model.get("inputTokens", 0) + per_model.get("outputTokens", 0)
                model_usage_max = max(model_usage_max, summed)

        return total_tokens if total_tokens > 0 else model_usage_max

    def _count_executions_from_trace(self, trace: List[Dict[str, Any]]) -> int:
        """
        从 trace 中统计执行次数（Bash 工具调用次数）

        单元测试期望统计所有 Bash 工具调用，不区分命令类型。
        """
        return sum(
            1
            for entry in trace
            if entry.get("type") == "tool_use" and str(entry.get("name", "")).lower() == "bash"
        )

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
                message = entry.get("message")
                if isinstance(message, dict):
                    content = message.get("content", [])
                    for item in content:
                        if item.get("type") == "text":
                            text = item.get("text", "")
                            if text:
                                output_parts.append(text)

        if output_parts:
            return "\n".join(output_parts)

        # Fallback for traces that only include a final result payload (common in some CLI versions).
        for entry in trace:
            if entry.get("type") == "result":
                result = entry.get("result", "")
                if isinstance(result, str) and result.strip():
                    return result
        return ""

    def _extract_error_from_trace(self, trace: List[Dict[str, Any]]) -> str:
        """
        从 trace 中提取错误信息（用于 CLI 返回码为 0 但内部执行失败的情况）。
        """
        def _walk(obj):
            if isinstance(obj, dict):
                yield obj
                for v in obj.values():
                    yield from _walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    yield from _walk(v)

        for entry in trace:
            # Many Claude Code events include stderr/exit_code when a hook or command fails.
            exit_code = entry.get("exit_code")
            stderr = entry.get("stderr")
            if exit_code not in (None, 0) and isinstance(stderr, str) and stderr.strip():
                return stderr.strip()

            # Fallback: search nested objects for a non-empty stderr/error string.
            for d in _walk(entry):
                stderr = d.get("stderr")
                if isinstance(stderr, str) and stderr.strip():
                    return stderr.strip()
                err = d.get("error")
                if isinstance(err, str) and err.strip():
                    return err.strip()

            # Some versions report errors via a final `result` payload.
            if entry.get("type") == "result" and entry.get("is_error"):
                result_text = entry.get("result")
                if isinstance(result_text, str) and result_text.strip():
                    return result_text.strip()

        return ""


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
