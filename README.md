# Run-Free, Run-Less, Run-Full: Impact of Execution Environments on LLM Agent Code Repair Capabilities

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 Project Overview

This project explores **the impact of execution environments on LLM Agent capabilities** in automated code repair tasks. Core research question:

> **Is execution environment a "necessary capability" or an "engineering shortcut"?**

We propose three execution paradigms and conduct comparative experiments on the SWE-bench Lite dataset:

| Mode | Execution Strategy | Core Hypothesis |
|------|---------|---------|
| **Run-Free** | Zero execution, pure reasoning | Models should have "get it right the first time" capability |
| **Run-Less** | Limited K executions + intelligent logging instrumentation | "One smart run is worth ten blind runs" |
| **Run-Cost** | Cost-aware decision making, model autonomously decides whether to execute | Rational agents should weigh execution costs vs. benefits |
| **Run-Full** | Unrestricted execution, trial-and-error loop | Current mainstream approach (baseline) |

## 🎯 Core Hypothesis

**Limited execution count + intelligent logging instrumentation may outperform unrestricted execution**

- Run-Less mode forces agents to view debugging as an "experimental design problem" rather than a "search problem"
- Maximize information gain from each execution through logging instrumentation
- Reduce execution costs and improve reasoning quality (Green AI perspective)

## 🚀 Quick Start

### Requirements

- Python 3.8+
- Docker (for SWE-bench evaluation)
- At least 120GB disk space, 16GB RAM, 8 CPU cores

### Installation

```bash
# Clone repository (including SWE-bench submodule)
git clone --recurse-submodules https://github.com/your-repo/run_free_run_less_run_full.git
cd run_free_run_less_run_full

# Install dependencies
pip install -r requirements.txt

# Download SWE-bench Lite dataset
python experiments/download_datasets.py
```

### Running Experiments

```bash
# Full test suite
bash ./run_all_experiments.sh

# Run-Free mode (zero execution)
python experiments/runner.py django__django-11099 run_free

# Run-Less mode (limited to 2 executions)
python experiments/runner.py django__django-11099 run_less 2

# Run-Cost mode (cost-aware decision making)
python experiments/runner.py django__django-11099 run_cost

# Run-Full mode (unrestricted execution)
python experiments/runner.py django__django-11099 run_full
```

Experiment results are saved in the `experiments/results/` directory.

## 📊 Experimental Design

### Execution Count Rules

**Counted as execution**:
- `pytest` or `python -m pytest`
- `python script.py` (running .py files)
- `python -m module` (running modules)

**Not counted as execution**:
- `ls`, `cat`, `grep`, `find` and other viewing commands
- `git` commands (disabled in experiments)
- `python -c "..."` simple calculations

### Key Mechanisms of Run-Less Mode

1. **Test Script Priority**: Agent needs to write test scripts based on problem description first
2. **Logging Instrumentation**: Insert print/log statements at key locations before running tests
3. **Hypothesis-Driven**: Clearly state hypothesis before each execution, analyze results after execution
4. **Budget Tracking**: Agent must output "Remaining test runs: X"

## 📁 Project Structure

```
.
├── experiments/
│   ├── runner.py              # Experiment runner
│   ├── prompt_builder.py      # Prompt builder
│   ├── agent_caller.py        # Agent caller
│   ├── download_datasets.py   # Dataset download tool
│   ├── tests/                 # Unit tests and integration tests
│   └── results/               # Experiment results output directory
├── SWE-bench/                 # SWE-bench official codebase (submodule)
├── data/                      # Dataset storage directory
├── docker/                    # Docker image build scripts
├── CLAUDE.md                  # Claude Code project guide
└── README.md                  # This file
```

## 🧪 Testing

```bash
# Run all tests
pytest experiments/tests/

# Run specific tests
pytest experiments/tests/test_runner.py
pytest experiments/tests/test_agent_caller.py

# Run integration tests (requires real Agent)
pytest experiments/tests/test_agent_integration.py
pytest experiments/tests/test_runner_integration.py
```

## 📈 Evaluation

You can first simply analyze interaction rounds, tokens, etc.
```bash
python experiments/analyze_results.py
```


Use the SWE-bench official evaluation framework, but it is most recommended to submit to sb-cli for faster evaluation:

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path experiments/results/ \
    --max_workers 4 \
    --run_id my_experiment
```

## 🎓 Research Objectives

**Target Conference**: ISSTA 2026 (International Symposium on Software Testing and Analysis)

**Core Contributions**:
1. Propose a three-paradigm taxonomy of execution environments (Run-Free/Run-Less/Run-Full)
2. Demonstrate that limited execution + intelligent instrumentation may outperform unrestricted execution
3. Reframe the debugging process as an "experimental design problem" rather than a "search problem"
4. Provide a Green AI perspective: reduce execution costs and improve reasoning quality

**Expected Findings**: Run-Less + Logging ≈ or > Run-Full, but with significantly lower costs

## 📝 Citation

If this project is helpful to your research, please cite:

```bibtex
@inproceedings{run-free-run-less-2026,
  title={Run-Free, Run-Less, Run-Full: Rethinking Execution Environments for LLM-based Code Repair},
  author={Your Name},
  booktitle={Proceedings of the 35th ACM SIGSOFT International Symposium on Software Testing and Analysis},
  year={2026}
}
```

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📧 Contact

For questions, please contact: [your-email@example.com](mailto:your-email@example.com)
