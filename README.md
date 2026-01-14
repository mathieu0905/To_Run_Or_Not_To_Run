# Run-Free, Run-Less, Run-Full: 执行环境对 LLM Agent 代码修复能力的影响研究

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📖 项目简介

本项目探索在自动化代码修复任务中，**执行环境对 LLM Agent 能力的影响**。核心研究问题：

> **执行环境是"必要能力"还是"工程捷径"？**

我们提出三种执行范式，并在 SWE-bench Lite 数据集上进行对比实验：

| 模式 | 执行策略 | 核心假设 |
|------|---------|---------|
| **Run-Free** | 零执行，纯推理 | 模型应具备"一次就对"的能力 |
| **Run-Less** | 限制 K 次执行 + 智能日志插桩 | "One smart run is worth ten blind runs" |
| **Run-Cost** | 成本意识决策，模型自主判断是否执行 | 理性 Agent 应权衡执行成本与收益 |
| **Run-Full** | 无限制执行，试错循环 | 当前主流方法（基线） |

## 🎯 核心假设

**限制执行次数 + 智能日志插桩可能优于无限制执行**

- Run-Less 模式强制 Agent 将调试过程视为"实验设计问题"而非"搜索问题"
- 通过日志插桩最大化每次执行的信息增益
- 降低执行成本，提高推理质量（Green AI 视角）

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Docker（用于 SWE-bench 评估）
- 至少 120GB 磁盘空间、16GB RAM、8 CPU 核心

### 安装

```bash
# 克隆仓库（包含 SWE-bench 子模块）
git clone --recurse-submodules https://github.com/your-repo/run_free_run_less_run_full.git
cd run_free_run_less_run_full

# 安装依赖
pip install -r requirements.txt

# 下载 SWE-bench Lite 数据集
python experiments/download_datasets.py
```

### 运行实验

```bash
# 全流程测试
bash ./run_all_experiments.sh

# Run-Free 模式（零执行）
python experiments/runner.py django__django-11099 run_free

# Run-Less 模式（限制 2 次执行）
python experiments/runner.py django__django-11099 run_less 2

# Run-Cost 模式（成本意识决策）
python experiments/runner.py django__django-11099 run_cost

# Run-Full 模式（无限制执行）
python experiments/runner.py django__django-11099 run_full
```

实验结果保存在 `experiments/results/` 目录。

## 📊 实验设计

### 执行次数统计规则

**计入执行次数**：
- `pytest` 或 `python -m pytest`
- `python script.py`（运行 .py 文件）
- `python -m module`（运行模块）

**不计入执行次数**：
- `ls`, `cat`, `grep`, `find` 等查看命令
- `git` 命令（实验中禁用）
- `python -c "..."` 简单计算

### Run-Less 模式的关键机制

1. **测试脚本优先**：Agent 需要先根据问题描述编写测试脚本
2. **日志插桩**：在运行测试前，在关键位置插入 print/log 语句
3. **假设驱动**：每次执行前明确假设，执行后分析结果
4. **预算追踪**：Agent 必须输出"剩余测试运行次数: X"

## 📁 项目结构

```
.
├── experiments/
│   ├── runner.py              # 实验运行器
│   ├── prompt_builder.py      # Prompt 构造器
│   ├── agent_caller.py        # Agent 调用器
│   ├── download_datasets.py   # 数据集下载工具
│   ├── tests/                 # 单元测试和集成测试
│   └── results/               # 实验结果输出目录
├── SWE-bench/                 # SWE-bench 官方代码库（子模块）
├── data/                      # 数据集存储目录
├── docker/                    # Docker 镜像构建脚本
├── CLAUDE.md                  # Claude Code 项目指南
└── README.md                  # 本文件
```

## 🧪 测试

```bash
# 运行所有测试
pytest experiments/tests/

# 运行特定测试
pytest experiments/tests/test_runner.py
pytest experiments/tests/test_agent_caller.py

# 运行集成测试（需要真实 Agent）
pytest experiments/tests/test_agent_integration.py
pytest experiments/tests/test_runner_integration.py
```

## 📈 评估

可以先简单地分析交互轮数，token等
```bash
python experiments/analyze_results.py
```


使用 SWE-bench 官方评估框架,但是最建议还是提交到sb-cli上评估比较快：

```bash
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path experiments/results/ \
    --max_workers 4 \
    --run_id my_experiment
```

## 🎓 研究目标

**目标会议**: ISSTA 2026（软件测试与分析国际研讨会）

**核心贡献**:
1. 提出执行环境的三分法范式（Run-Free/Run-Less/Run-Full）
2. 证明限制执行 + 智能插桩可能优于无限制执行
3. 将调试过程重新定义为"实验设计问题"而非"搜索问题"
4. 提供 Green AI 视角：降低执行成本，提高推理质量

**预期发现**: Run-Less + Logging ≈ 或 > Run-Full，但成本显著降低

## 📝 引用

如果本项目对您的研究有帮助，请引用：

```bibtex
@inproceedings{run-free-run-less-2026,
  title={Run-Free, Run-Less, Run-Full: Rethinking Execution Environments for LLM-based Code Repair},
  author={Your Name},
  booktitle={Proceedings of the 35th ACM SIGSOFT International Symposium on Software Testing and Analysis},
  year={2026}
}
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题，请联系：[your-email@example.com](mailto:your-email@example.com)
