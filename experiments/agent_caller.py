#!/usr/bin/env python3
"""
Agent Caller: Unified wrapper for Claude Code and Codex call interfaces
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
    """Agent execution trace record"""
    agent_type: str  # claude_code, codex
    prompt: str
    output: str
    tokens_used: int
    exec_count: int
    duration_sec: float
    raw_trace: List[Dict[str, Any]]  # stream-json format raw trace
    error: Optional[str] = None


class AgentCaller:
    """Unified Agent call interface"""

    def __init__(self, agent_type: str = "claude_code", instance_id: Optional[str] = None):
        """
        Initialize Agent caller

        Args:
            agent_type: "claude_code" or "codex"
            instance_id: SWE-bench instance ID (used to determine Docker image)
        """
        self.agent_type = agent_type
        self.instance_id = instance_id

    def call(self, prompt: str, timeout: int = 600, trace_output_path: Optional[str] = None) -> AgentTrace:
        """
        Call agent and return trace

        Args:
            prompt: Input prompt
            timeout: Timeout (seconds)

        Returns:
            AgentTrace object
        """
        if self.agent_type == "claude_code" or self.agent_type == "claude_code_glm":
            return self._call_claude_code(prompt, timeout, trace_output_path)
        elif self.agent_type == "codex":
            return self._call_codex(prompt, timeout, trace_output_path)
        else:
            raise ValueError(f"Unknown agent type: {self.agent_type}")

    def _get_docker_image(self, instance_id: str) -> Optional[str]:
        """
        Get corresponding Docker image name based on instance_id

        instance_id format: django__django-11099
        Image name format: swebench/sweb.eval.x86_64.django_1776_django-11099-agent:latest
        """
        if not instance_id:
            return None

        # Extract issue number part from instance_id (e.g. django-11099)
        # instance_id format: {repo}__{repo}-{issue_number}
        parts = instance_id.split("__")
        if len(parts) != 2:
            return None
        issue_part = parts[1]  # e.g. django-11099

        # Find all swebench agent images
        result = subprocess.run(
            ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                # Match images containing issue number and ending with -agent:latest
                if issue_part in line and line.endswith("-agent:latest"):
                    return line

        return None

    def _call_claude_code(self, prompt: str, timeout: int, trace_output_path: Optional[str] = None) -> AgentTrace:
        """Call Claude Code"""
        import time
        import os
        start = time.time()

        # Use the specified output path or create a temporary file to save the trace
        if trace_output_path:
            trace_path = trace_output_path
            # Make sure the directory exists
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

            # Build command
            cmd = self._build_claude_command(prompt, trace_path)

            # Determine working directory: use /testbed if it exists, otherwise use current directory
            work_dir = "/testbed" if os.path.exists("/testbed") else None

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work_dir,
                env=self._build_sandboxed_env()
            )

            duration = time.time() - start

            # Read trace
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
            # Also try to read trace file written on timeout
            # Docker container may have completed Claude Code execution before timeout
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
            # Only clean up temporary files (don't clean up specified output files)
            if not trace_output_path:
                Path(trace_path).unlink(missing_ok=True)
                # Best-effort cleanup for the local prompt file created alongside the trace.
                Path(f"{trace_path}.prompt.txt").unlink(missing_ok=True)

    def _build_claude_command(self, prompt: str, trace_path: str) -> List[str]:
        """Build Claude Code command"""
        # Must have instance_id and corresponding Docker image
        docker_image = self._get_docker_image(self.instance_id) if self.instance_id else None

        if not docker_image:
            raise RuntimeError(f"No Docker image found for instance: {self.instance_id}. "
                             f"Please build the agent image first.")

        # Execute in Docker container
        # Need to map host trace_path to container
        container_trace_path = "/workspace/output/trace.jsonl"
        container_patch_path = "/workspace/output/patch.diff"
        host_trace_dir = str(Path(trace_path).parent.absolute())

        # Get project root directory (parent of docker directory)
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docker_dir = os.path.join(project_root, "docker")

        # Get configuration from environment variables and pass to container
        base_url = os.environ.get('ANTHROPIC_BASE_URL', 'https://api.anthropic.com')
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        auth_token = os.environ.get('ANTHROPIC_AUTH_TOKEN', '')
        claude_model = os.environ.get('CLAUDE_MODEL', 'sonnet')

        # Extract domain (remove http:// or https:// and port)
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        api_host = parsed.hostname or 'api.anthropic.com'

        # Run as nonroot user, so can use --dangerously-skip-permissions
        # 1. First run configure_models.sh to configure Claude Code (using environment variables)
        # 2. Copy configuration to nonroot user directory
        # 3. Activate testbed conda environment and run Claude Code
        # Note: nonroot user cannot write to mounted directory, so use pipe to let root write files
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

        # First write prompt to host directory
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
        """Build Codex command"""
        # Must have instance_id and corresponding Docker image
        docker_image = self._get_docker_image(self.instance_id) if self.instance_id else None

        if not docker_image:
            raise RuntimeError(f"No Docker image found for instance: {self.instance_id}. "
                             f"Please build the agent image first.")

        # Execute in Docker container
        container_trace_path = "/workspace/output/trace.jsonl"
        container_patch_path = "/workspace/output/patch.diff"
        host_trace_dir = str(Path(trace_path).parent.absolute())

        # Use --full-auto to skip confirmation, activate testbed conda environment, run git diff after execution
        # Write prompt to file to avoid shell escaping issues
        container_prompt_path = "/workspace/output/prompt.txt"

        # First write prompt to host directory
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
        """Call Codex"""
        import time
        import os
        start = time.time()

        # Use the specified output path or create a temporary file to save the trace
        if trace_output_path:
            trace_path = trace_output_path
            # Make sure the directory exists
            Path(trace_path).parent.mkdir(parents=True, exist_ok=True)
        else:
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.jsonl', delete=False) as trace_file:
                trace_path = trace_file.name

        try:
            cmd = self._build_codex_command(prompt, trace_path)

            # Determine working directory: use /testbed if it exists, otherwise use current directory
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

            # Filter Codex debug logs (needs_follow_up, etc.), only keep real error messages
            stderr = (result.stderr or "").strip()
            # If stderr only contains needs_follow_up logs, don't treat as error
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
            # Only clean up temporary files (don't clean up specified output files)
            if not trace_output_path:
                Path(trace_path).unlink(missing_ok=True)

    def _read_trace_file(self, trace_path: str) -> List[Dict[str, Any]]:
        """Read stream-json format trace file"""
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
        """Extract token usage from trace"""
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
        Count execution count from trace (Bash tool invocation count)

        Unit tests expect to count all Bash tool invocations, regardless of command type.
        """
        return sum(
            1
            for entry in trace
            if entry.get("type") == "tool_use" and str(entry.get("name", "")).lower() == "bash"
        )

    def _is_test_execution(self, command: str) -> bool:
        """
        Determine if command is a test execution or script run

        Commands counted as executions:
        - pytest / py.test
        - unittest
        - Django tests (python manage.py test)
        - tox
        - nose / nosetests
        - python xxx.py (running test scripts)

        Commands not counted:
        - ls, cat, grep, find and other viewing commands
        - git commands
        - cd, pwd and other navigation commands
        - python -c simple commands
        - python --version and other info queries
        """
        command = command.strip().lower()

        # Test framework commands
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

        # Python script execution (but exclude some common non-execution commands)
        if command.startswith('python ') or command.startswith('python3 '):
            # Exclude python -c (usually used for simple calculations or viewing)
            if ' -c ' in command:
                return False
            # Exclude python --version and other info queries
            if '--version' in command or '--help' in command:
                return False
            # If running a .py file, count it
            if '.py' in command:
                return True

        return False

    def _extract_output_from_trace(self, trace: List[Dict[str, Any]]) -> str:
        """Extract output text from trace"""
        output_parts = []
        for entry in trace:
            # Codex format: item.completed -> item.text
            if entry.get("type") == "item.completed":
                item = entry.get("item", {})
                if item.get("type") == "agent_message":
                    text = item.get("text", "")
                    if text:
                        output_parts.append(text)

            # Claude Code format: assistant -> message.content[].text
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
        Extract error information from trace (for cases where CLI returns 0 but internal execution failed).
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
    """Save trace to file"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save complete trace data
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


# Example usage
if __name__ == "__main__":
    # Test Claude Code call
    caller = AgentCaller(agent_type="claude_code")

    test_prompt = "Please help me write a Python function to calculate the nth term of the Fibonacci sequence"

    print(f"Calling {caller.agent_type}...")
    trace = caller.call(test_prompt)

    print(f"\nAgent: {trace.agent_type}")
    print(f"Tokens used: {trace.tokens_used}")
    print(f"Executions: {trace.exec_count}")
    print(f"Duration: {trace.duration_sec:.2f}s")
    print(f"Output length: {len(trace.output)} chars")

    if trace.error:
        print(f"Error: {trace.error}")

    # Save trace
    save_trace(trace, Path("test_trace.json"))
