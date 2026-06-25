#!/usr/bin/env python3
"""Docker-free hard-Prohibited runner.

Under hard-Prohibited (--disallowedTools Bash) the agent only uses
Read/Write/Edit/Glob/Grep — no Python runtime, no pytest, no shell.
That makes the SWE-bench testbed container unnecessary. This script
prepares a plain git checkout on the host and invokes the Claude Code
CLI directly against it.

Usage:
    python run_hardlimit.py smoke <instance_id> [dataset]
    python run_hardlimit.py batch <instance_list.txt> [dataset] [concurrency]

Outputs land in:
    output/{dataset_short}/claude_code/run_hard_free/{instance_id}/
        ├── prompt.txt
        ├── trace.jsonl     (Claude CLI --output-format stream-json)
        ├── patch.diff      (git diff after the run)
        └── result_{mode}.json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from prompt_builder import PromptBuilder  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS_PATH = PROJECT_ROOT / ".claude" / "settings.local.json.claude"
OUTPUT_ROOT = PROJECT_ROOT / "output"
WORKSPACE_ROOT = Path("/tmp/hardlimit")

# CLI binary — resolved at import time so failures are loud.
CLAUDE_BIN = os.environ.get("CLAUDE_BIN") or shutil.which("claude") or "claude"


@dataclass
class HardLimitResult:
    instance_id: str
    mode: str
    agent_type: str
    success: bool
    duration_sec: float
    patch_len: int
    error: str = ""


def short_dataset(dataset_name: str) -> str:
    if "Verified" in dataset_name:
        return "swebenchverified"
    if "Lite" in dataset_name:
        return "swebenchlite"
    raise ValueError(f"Unknown dataset: {dataset_name}")


def load_instance(instance_id: str, dataset_name: str) -> Dict:
    from datasets import load_dataset
    ds = load_dataset(dataset_name, split="test")
    for item in ds:
        if item["instance_id"] == instance_id:
            return item
    raise ValueError(f"Instance {instance_id} not in {dataset_name}")


def prepare_workspace(instance: Dict) -> Path:
    """Clone repo at base_commit into /tmp/hardlimit/{instance_id}.

    Uses a reference cache at /tmp/hardlimit/_cache/{owner}__{repo}.git
    so repeated instances for the same repo reuse the objects database
    (a full Django clone is ~200 MB; a 100-instance verified run would
    otherwise re-download the same repo dozens of times).
    """
    inst_id = instance["instance_id"]
    repo_slug = instance["repo"]  # e.g. "django/django"
    base_commit = instance["base_commit"]

    workspace = WORKSPACE_ROOT / inst_id
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)

    cache_dir = WORKSPACE_ROOT / "_cache" / f"{repo_slug.replace('/', '__')}.git"
    cache_dir.parent.mkdir(parents=True, exist_ok=True)

    if not cache_dir.exists():
        # Mirror clone — stores objects only, no working tree. Subsequent
        # checkouts pull from it instead of GitHub.
        subprocess.run(
            [
                "git",
                "clone",
                "--mirror",
                f"https://github.com/{repo_slug}.git",
                str(cache_dir),
            ],
            check=True,
            capture_output=True,
        )
    else:
        # Refresh in case base_commit isn't present yet.
        subprocess.run(
            ["git", "-C", str(cache_dir), "fetch", "--all", "--quiet"],
            check=False,
            capture_output=True,
        )

    # Fast local clone from the cache, then checkout.
    subprocess.run(
        ["git", "clone", "--shared", str(cache_dir), str(workspace)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(workspace), "checkout", "-q", base_commit],
        check=True,
        capture_output=True,
    )
    return workspace


MODE_DIR = os.environ.get("HARD_MODE_DIR", "run_hard_free_v2")


def build_trace_dir(instance_id: str, dataset_name: str) -> Path:
    out = OUTPUT_ROOT / short_dataset(dataset_name) / "claude_code" / MODE_DIR / instance_id
    out.mkdir(parents=True, exist_ok=True)
    return out


def run_claude(
    prompt: str,
    workspace: Path,
    trace_path: Path,
    timeout: int,
) -> tuple[int, str]:
    """Invoke Claude CLI with hard-limit flags; stream JSON to trace_path.

    Returns (exit_code, error_message). A non-zero exit is not fatal by
    itself — we treat any non-empty trace.jsonl and/or patch.diff as a
    usable result.
    """
    # Precise test-execution denylist (hard-v2). We ban only the Bash
    # sub-commands that would execute tests, leaving read/search utilities
    # (`ls`, `find`, `git log`, `cat`, `head`, etc.) available. This mirrors
    # the reviewer's definition of "execution" (running tests) rather than
    # blocking the entire shell surface.
    exec_denylist = [
        "Bash(pytest*)",
        "Bash(py.test*)",
        "Bash(*pytest*)",
        "Bash(python -m pytest*)",
        "Bash(python3 -m pytest*)",
        "Bash(python -m unittest*)",
        "Bash(python3 -m unittest*)",
        "Bash(python -m nose*)",
        "Bash(python -m tox*)",
        "Bash(tox*)",
        "Bash(nose*)",
        "Bash(nosetests*)",
        "Bash(python manage.py test*)",
        "Bash(python3 manage.py test*)",
        "Bash(manage.py test*)",
        "Bash(python tests/runtests.py*)",
        "Bash(python3 tests/runtests.py*)",
        "Bash(*runtests.py*)",
        "Bash(python *.py*)",
        "Bash(python3 *.py*)",
        "Bash(./*.py*)",
    ]
    cmd = [
        CLAUDE_BIN,
        "-p",
        prompt,
        "--settings",
        str(SETTINGS_PATH),
        "--disallowedTools",
        *exec_denylist,
        "--dangerously-skip-permissions",
        "--verbose",
        "--output-format",
        "stream-json",
    ]
    with open(trace_path, "w") as trace_f:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(workspace),
                stdout=trace_f,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True,
            )
            return result.returncode, (result.stderr or "")[:1000]
        except subprocess.TimeoutExpired as e:
            return 124, f"timeout after {timeout}s"
        except Exception as e:
            return 1, f"exception: {e!r}"


def extract_patch(workspace: Path, patch_path: Path) -> int:
    """Write `git diff` of the workspace to patch_path. Returns byte size."""
    result = subprocess.run(
        ["git", "-C", str(workspace), "diff"],
        capture_output=True,
        text=True,
    )
    patch_path.write_text(result.stdout, encoding="utf-8")
    return len(result.stdout)


def run_one(instance_id: str, dataset_name: str, timeout: int = 900) -> HardLimitResult:
    start = time.time()
    try:
        instance = load_instance(instance_id, dataset_name)
        workspace = prepare_workspace(instance)
        trace_dir = build_trace_dir(instance_id, dataset_name)

        prompt = PromptBuilder.build_prompt(instance, "run_hard_free", k=2, agent_type="claude_code")
        (trace_dir / "prompt.txt").write_text(prompt, encoding="utf-8")

        trace_path = trace_dir / "trace.jsonl"
        exit_code, err = run_claude(prompt, workspace, trace_path, timeout)

        patch_path = trace_dir / "patch.diff"
        patch_size = extract_patch(workspace, patch_path)

        result = HardLimitResult(
            instance_id=instance_id,
            mode=MODE_DIR,
            agent_type="claude_code",
            success=patch_size > 0,
            duration_sec=time.time() - start,
            patch_len=patch_size,
            error=err if exit_code not in (0, 124) and patch_size == 0 else "",
        )
        (trace_dir / f"result_{MODE_DIR}.json").write_text(
            json.dumps(asdict(result), indent=2), encoding="utf-8"
        )
        return result
    except Exception as e:
        return HardLimitResult(
            instance_id=instance_id,
            mode=MODE_DIR,
            agent_type="claude_code",
            success=False,
            duration_sec=time.time() - start,
            patch_len=0,
            error=f"{type(e).__name__}: {e}",
        )


def run_batch(
    instance_list_path: Path,
    dataset_name: str,
    concurrency: int = 4,
    timeout: int = 900,
) -> None:
    instances = [
        line.strip()
        for line in instance_list_path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    print(f"loaded {len(instances)} instances, concurrency={concurrency}")

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = {pool.submit(run_one, inst, dataset_name, timeout): inst for inst in instances}
        done = 0
        for fut in as_completed(futures):
            inst = futures[fut]
            result = fut.result()
            done += 1
            status = "ok" if result.success else "FAIL"
            print(
                f"[{done}/{len(instances)}] {inst}: {status} "
                f"({result.duration_sec:.0f}s, {result.patch_len}B)"
                + (f" err={result.error[:120]}" if result.error else "")
            )


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "smoke":
        instance_id = sys.argv[2]
        dataset_name = sys.argv[3] if len(sys.argv) > 3 else "princeton-nlp/SWE-bench_Verified"
        result = run_one(instance_id, dataset_name, timeout=900)
        print(json.dumps(asdict(result), indent=2))
    elif cmd == "batch":
        instance_list_path = Path(sys.argv[2])
        dataset_name = sys.argv[3] if len(sys.argv) > 3 else "princeton-nlp/SWE-bench_Verified"
        concurrency = int(sys.argv[4]) if len(sys.argv) > 4 else 4
        timeout = int(sys.argv[5]) if len(sys.argv) > 5 else 900
        run_batch(instance_list_path, dataset_name, concurrency, timeout)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
