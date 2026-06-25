# To Run or Not to Run

This repository contains the public artifact for the ISSTA 2026 paper
"To Run or Not to Run: Analyzing the Cost-Effectiveness of Code Execution in
LLM-Based Program Repair".

The artifact studies how different execution policies affect LLM-based program
repair on SWE-bench Lite and SWE-bench Verified. The public release keeps the
experiment runner, prompts, Docker/SWE-bench integration scripts, analysis code,
dashboard source, figures, and compact data files. Raw execution traces,
generated patches, prediction dumps, SB-CLI reports, backups, local build logs,
and credentials are intentionally excluded.

## Execution Policies

The code uses the following mode names:

| Mode | Description |
| --- | --- |
| `run_free` | Prohibited execution: the agent repairs using static reasoning only. |
| `run_less` | Quota-limited execution: the agent receives a small execution budget `k`. |
| `run_cost` | Budget-guided execution: the agent is prompted to trade off execution cost and expected information gain. |
| `run_full` | Unrestricted execution baseline. |

Some hard-limit experiments live under `experiments/hard_limit/` and remove
execution tools at the runner level for stricter policy enforcement.

## Repository Layout

```text
.
├── analysis/                 # Paper analysis scripts and compact summaries
├── dashboard/                # Next.js dashboard for inspecting runs
├── data/                     # SWE-bench Lite/Verified metadata used by scripts
├── docker/                   # Docker image build and test scripts
├── experiments/              # Core runner, prompts, agent wrappers, tests
├── figures/                  # Figure-generation scripts and rendered figures
├── queue_*.tsv               # Batch queues used for release experiments
├── run_*.sh                  # Batch launchers for agents/datasets
└── submit_to_swebench.sh     # Submission helper for SWE-bench evaluation
```

`SWE-bench` and `sb-cli` are tracked as submodules. Initialize them when you
need the full evaluation workflow.

## Setup

```bash
git clone --recurse-submodules https://github.com/mathieu0905/To_Run_Or_Not_To_Run.git
cd To_Run_Or_Not_To_Run
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install datasets pytest pyyaml numpy pandas scipy matplotlib seaborn
```

For Docker-based SWE-bench execution, install Docker and build the required
images with the scripts in `docker/`. Agent credentials are read from
environment variables such as `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, and
`OPENAI_API_KEY`; no credentials are stored in this repository.

The dashboard is optional:

```bash
cd dashboard
npm install
npm run dev
```

## Running Experiments

Single instance:

```bash
python experiments/runner.py django__django-11099 run_free
python experiments/runner.py django__django-11099 run_less 2
python experiments/runner.py django__django-11099 run_cost
python experiments/runner.py django__django-11099 run_full
```

You can choose the agent type and timeout through the optional positional
arguments accepted by `experiments/runner.py`.

Batch scripts are provided for larger runs:

```bash
bash run_codex.sh -f
bash run_claude.sh -f
bash run_codex_verified.sh -f
bash run_claude_verified.sh -f
```

Generated traces, prompts, patches, and result JSON files are written under
ignored output directories such as `output/` and `logs/`.

## Analysis

The public release includes compact analysis inputs and reports under
`analysis/`, plus the scripts used to regenerate paper tables and figures.
Examples:

```bash
python analysis/RQ2_effectiveness_cost/analyze_rq1.py
python analysis/RQ2_effectiveness_cost/analyze_rq2.py
python analysis/RQ3_why_limited_impact/rq3_comprehensive_analysis.py
python figures/fig1_passrate_ci.py
```

Prediction generation and SWE-bench submission helpers:

```bash
python experiments/prepare_sbcli_predictions.py
python generate_predictions.py
bash submit_to_swebench.sh
```

These commands expect regenerated experiment outputs or externally supplied raw
outputs. The large raw traces and report dumps used during paper development are
not committed to keep the artifact lightweight.

## Public Release Notes

This repository was cleaned for public artifact release:

- kept source code, scripts, prompt templates, Docker helpers, dashboard source,
  figure scripts, compact datasets, and summarized analysis outputs;
- removed generated traces, patch dumps, SB-CLI reports, backups, `.next`
  builds, local logs, local Docker auth/config files, editor settings, and
  Python bytecode;
- updated `.gitignore` so regenerated artifacts stay out of version control.

## Citation

If you use this artifact, please cite the corresponding ISSTA 2026 paper. The
final BibTeX entry will be added after the proceedings metadata is available.

