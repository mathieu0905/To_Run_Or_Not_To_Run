# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research project exploring the impact of execution environments on LLM Agent capabilities in code repair tasks. Core research question: **Is the execution environment a "necessary capability" or an "engineering shortcut"?**

The research compares four execution paradigms:
- **Run-Free (Zero-Exec)**: No code execution at all, pure reasoning-based repair
- **Run-Less (Budget-Exec)**: Limited execution (K-time budget), emphasizing log instrumentation
- **Run-Cost (Cost-Aware-Exec)**: Cost-constrained, model autonomously decides whether to execute
- **Run-Full (Unrestricted-Exec)**: Arbitrary execution, trial-and-error loop

Core hypothesis: **"One smart run is worth ten blind runs"** - Limiting execution count + intelligent log instrumentation may outperform unrestricted execution.

## Code Architecture

### Core Modules

```
experiments/
├── runner.py           # Experiment runner: executes single experiment
├── batch_runner.py     # Batch runner: executes multiple experiments in parallel
├── prompt_builder.py   # Prompt builder: generates system prompts for different modes
├── agent_caller.py     # Agent caller: unified wrapper for Claude Code and Codex
├── download_datasets.py # Dataset download tool
└── tests/             # Unit tests and integration tests

output/                # Experiment output directory (real-time sync)
├── swebenchlite/      # SWE-bench Lite dataset results
│   └── {instance_id}/ # Output for each instance
│       ├── trace.jsonl       # Agent execution trace
│       ├── patch.diff        # Generated patch
│       ├── prompt_{mode}.txt # Prompt used
│       └── result_{mode}.json # Experiment result summary
└── swebenchverified/  # SWE-bench Verified dataset results

SWE-bench/             # SWE-bench official codebase (submodule)
├── swebench/harness/  # Evaluation framework
└── swebench/collect/  # Data collection tools

docker/                # Docker image build scripts
docker-compose.yml     # Docker Compose configuration
```

### Key Design

**Runtime Environment**:
- All experiment scripts run inside Docker containers
- Output real-time sync to host machine via volume mounting
- Output directory structure: `output/{dataset}/{instance_id}/`

**Prompt Construction (prompt_builder.py)**
- Each mode has independent prompt template (in English)
- Run-Less mode emphasizes "execution budget" concept, requires Agent to output remaining count
- Run-Cost mode requires Agent to output confidence level and decision rationale
- All modes disable git commands to avoid interfering with experiment environment
- Supports multiple test frameworks (pytest, unittest, Django tests, tox, nose)

**Agent Invocation (agent_caller.py)**
- Unified interface supporting Claude Code and Codex
- Invokes CLI via subprocess, captures stream-json format trace
- Automatically tracks token usage and execution count
- Execution count statistics: only counts test runs (pytest, unittest, Django tests, etc.), excludes bash view commands

**Experiment Execution (runner.py)**
- Loads instances from SWE-bench dataset
- Builds prompt for corresponding mode
- Invokes agent and records complete trace
- Extracts git diff format patch
- Saves results to instance directory

**Batch Execution (batch_runner.py)**
- Executes multiple instances in parallel (ThreadPoolExecutor)
- Supports checkpoint resume (checkpoint.json)
- Real-time progress display
- Failure handling and automatic retry

## Common Commands

### Start Docker Container

```bash
# Start container
docker-compose up -d swebench-runner

# Enter container
docker-compose exec swebench-runner bash
```

### Run Single Experiment Inside Container

```bash
cd /workspace/experiments

# Run-Free mode (no code execution)
python runner.py django__django-11099 run_free

# Run-Less mode (limited K executions)
python runner.py django__django-11099 run_less 2

# Run-Cost mode (cost-aware decision making)
python runner.py django__django-11099 run_cost

# Run-Full mode (unrestricted execution)
python runner.py django__django-11099 run_full

# Specify dataset
python runner.py django__django-11099 run_less 2 claude_code 600 princeton-nlp/SWE-bench_Verified
```

### Run Batch Experiments Inside Container

```bash
cd /workspace/experiments

# Run batch experiments
python batch_runner.py ../test_instances.txt run_less 2 4

# Parameter explanation:
# - ../test_instances.txt: instance list file
# - run_less: execution mode
# - 2: execution count limit for run_less
# - 4: concurrency (run 4 instances simultaneously)

# Use different dataset
python batch_runner.py instances.txt run_less 2 4 claude_code 600 princeton-nlp/SWE-bench_Verified
```

### View Output on Host Machine

```bash
# Output is synced to host machine in real-time
ls output/swebenchlite/django__django-11099/

# View trace
tail -f output/swebenchlite/django__django-11099/trace.jsonl

# View patch
cat output/swebenchlite/django__django-11099/patch.diff

# View results
cat output/swebenchlite/django__django-11099/result_run_less_k2.json
```

### Testing

```bash
# Run tests inside container
cd /workspace/experiments
pytest tests/

# Run specific tests
pytest tests/test_runner.py
pytest tests/test_agent_caller.py
```

### SWE-bench Evaluation

```bash
# Evaluate patches (requires Docker)
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path <path_to_predictions> \
    --max_workers <num_workers> \
    --run_id <run_id>
```

## Experiment Design Key Points

### Output Directory Structure

Output for each instance is saved in the `output/{dataset}/{instance_id}/` directory:
- `trace.jsonl` - Complete Agent execution trace (stream-json format)
- `patch.diff` - Generated git diff format patch
- `prompt_{mode}.txt` - Prompt used
- `result_{mode}.json` - Experiment result summary (tokens, exec_count, duration, success, etc.)
- `checkpoint.json` - Checkpoint file for batch runs (in dataset directory)

### Execution Count Statistics Rules

**Counted as execution**:
- `pytest` or `python -m pytest`
- `python -m unittest`
- `python manage.py test` (Django tests)
- `tox`, `nose`, `nosetests`
- `python script.py` (running .py files)

**Not counted as execution**:
- `ls`, `cat`, `grep`, `find` and other view commands
- `git` commands (disabled in experiments)
- `python -c "..."` simple calculations
- `python --version` and other information queries

### Key Mechanisms of Run-Less Mode

1. **Test Script Priority**: Agent needs to write test script first based on problem description
2. **Identify Test Command**: Agent needs to identify the test framework used by the project
3. **Log Instrumentation**: Before running tests, Agent should insert print/log statements at key locations
4. **Hypothesis-Driven**: Clearly state hypothesis before each execution, analyze results after
5. **Budget Tracking**: Agent must output "Remaining test runs: X"

### Prompt Design Principles

- **Run-Free**: Emphasizes "get it right the first time", cannot rely on feedback
- **Run-Less**: Emphasizes "high-value experiments", maximize information gain from each execution
- **Run-Cost**: Emphasizes "rational decision-making", decide whether to execute based on confidence level
- **Run-Full**: Allows trial-and-error, but still recommends writing test scripts first

## Development Notes

### Docker Environment

- All scripts run inside Docker containers
- Output real-time sync via volume mounting
- Environment variables configured via docker-compose.yml
- Uses `--network host` to share host machine network (for proxy)

### Agent Invocation

- Claude Code requires `ANTHROPIC_API_KEY` environment variable
- Codex requires `OPENAI_API_KEY` environment variable
- Both invoked via CLI, output in stream-json format
- Timeout setting recommended 600 seconds or more

### Batch Execution

- Implemented using ThreadPoolExecutor for concurrency
- Default concurrency is 4, adjustable based on machine resources
- Supports checkpoint resume: re-running after interruption will skip completed instances
- Checkpoint file saved in `output/{dataset}/checkpoint.json`

### Result Files

Experiment results saved in `output/{dataset}/{instance_id}/` directory:
- All files synced to host machine in real-time
- trace.jsonl contains complete agent execution record
- patch.diff is standard git diff format
- result_{mode}.json contains experiment metadata

## Research Objectives

Target Conference: ISSTA 2026 (International Symposium on Software Testing and Analysis)

Core Contributions:
1. Propose a four-paradigm taxonomy of execution environments (Run-Free/Run-Less/Run-Cost/Run-Full)
2. Demonstrate that limited execution + intelligent instrumentation may outperform unrestricted execution
3. Reframe the debugging process as an "experimental design problem" rather than a "search problem"
4. Provide a Green AI perspective: reduce execution costs, improve reasoning quality

Expected Finding: Run-Less + Logging ≈ or > Run-Full, but with significantly lower costs.

## Quick Start

1. **Set environment variables** (on host machine):
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   export OPENAI_API_KEY="your-api-key"  # If using Codex
   ```

2. **Start container**:
   ```bash
   docker-compose up -d swebench-runner
   docker-compose exec swebench-runner bash
   ```

3. **Run test experiment**:
   ```bash
   cd /workspace/experiments
   python runner.py django__django-11099 run_free
   ```

4. **View output** (on host machine):
   ```bash
   ls output/swebenchlite/django__django-11099/
   cat output/swebenchlite/django__django-11099/patch.diff
   ```

5. **Run batch experiments**:
   ```bash
   cd /workspace/experiments
   python batch_runner.py ../test_instances.txt run_less 2 4
   ```

For detailed usage instructions, please refer to `DOCKER_USAGE.md`.
