# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个研究项目，探索在代码修复任务中执行环境对 LLM Agent 能力的影响。核心研究问题：**执行环境是"必要能力"还是"工程捷径"？**

研究对比三种执行范式：
- **Run-Free (Zero-Exec)**: 完全不执行代码，纯推理修复
- **Run-Less (Budget-Exec)**: 有限次执行（K次预算），强调日志插桩
- **Run-Cost (Cost-Aware-Exec)**: 有成本约束，模型自主决策是否执行
- **Run-Full (Unrestricted-Exec)**: 任意执行，试错循环

核心假设：**"One smart run is worth ten blind runs"** - 限制执行次数 + 智能日志插桩可能优于无限制执行。

## 代码架构

### 核心模块

```
experiments/
├── runner.py           # 实验运行器：执行单个实验
├── prompt_builder.py   # Prompt 构造器：为不同模式生成 system prompt
├── agent_caller.py     # Agent 调用器：统一封装 Claude Code 和 Codex
├── download_datasets.py # 数据集下载工具
└── tests/             # 单元测试和集成测试

SWE-bench/             # SWE-bench 官方代码库（子模块）
├── swebench/harness/  # 评估框架
└── swebench/collect/  # 数据收集工具

data/                  # 数据集存储目录
docker/                # Docker 镜像构建脚本
```

### 关键设计

**Prompt 构造 (prompt_builder.py)**
- 每种模式有独立的 prompt 模板
- Run-Less 模式强调"执行预算"概念，要求 Agent 输出剩余次数
- Run-Cost 模式要求 Agent 输出信心水平和决策理由
- 所有模式都禁用 git 命令以避免干扰实验环境

**Agent 调用 (agent_caller.py)**
- 统一接口支持 Claude Code 和 Codex
- 通过 subprocess 调用 CLI，捕获 stream-json 格式的 trace
- 自动统计 token 使用量和执行次数
- 执行次数统计：只计入 pytest 和 Python 脚本运行，不计入 bash 查看命令（ls, cat, grep 等）

**实验运行 (runner.py)**
- 从 SWE-bench Lite 数据集加载实例
- 构建对应模式的 prompt
- 调用 agent 并记录完整 trace
- 提取 git diff 格式的补丁
- 保存结果到 JSON 文件

## 常用命令

### 运行单个实验

```bash
# Run-Free 模式（不执行代码）
python experiments/runner.py <instance_id> run_free

# Run-Less 模式（限制 K 次执行）
python experiments/runner.py <instance_id> run_less 2

# Run-Cost 模式（成本意识决策）
python experiments/runner.py <instance_id> run_cost

# Run-Full 模式（无限制执行）
python experiments/runner.py <instance_id> run_full

# 示例
python experiments/runner.py django__django-11099 run_less 2
```

### 测试

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

### 数据集操作

```bash
# 下载 SWE-bench Lite 数据集
python experiments/download_datasets.py

# 生成 prompt 示例
python experiments/generate_prompt_examples.py
```

### SWE-bench 评估

```bash
# 评估补丁（需要 Docker）
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path <path_to_predictions> \
    --max_workers <num_workers> \
    --run_id <run_id>

# 验证 gold patches
python -m swebench.harness.run_evaluation \
    --predictions_path gold \
    --max_workers 1 \
    --instance_ids sympy__sympy-20590 \
    --run_id validate-gold
```

## 实验设计要点

### 执行次数统计规则

**计入执行次数**：
- `pytest` 或 `python -m pytest`
- `python script.py`（运行 .py 文件）
- `python -m module`（运行模块）

**不计入执行次数**：
- `ls`, `cat`, `grep`, `find` 等查看命令
- `git` 命令（实验中禁用）
- `python -c "..."` 简单计算
- `python --version` 等信息查询

### Run-Less 模式的关键机制

1. **测试脚本优先**：由于 SWE-bench 实例没有现成测试用例，Agent 需要先根据问题描述编写测试脚本
2. **日志插桩**：在运行测试前，Agent 应在关键位置插入 print/log 语句
3. **假设驱动**：每次执行前明确假设，执行后分析结果
4. **预算追踪**：Agent 必须输出"剩余测试运行次数: X"

### Prompt 设计原则

- **Run-Free**: 强调"一次就对"，不能依赖反馈
- **Run-Less**: 强调"高价值实验"，每次执行都要最大化信息增益
- **Run-Cost**: 强调"理性决策"，根据信心水平决定是否执行
- **Run-Full**: 允许试错，但仍建议先写测试脚本

## 开发注意事项

### Agent 调用

- Claude Code 需要 OAuth 认证，使用时需挂载 `~/.claude` 目录
- Codex 需要 API 认证，配置在 `~/.codex/auth.json`
- 两者都通过 CLI 调用，输出为 stream-json 格式
- 超时设置建议 600 秒以上

### Docker 环境

- SWE-bench 使用 Docker 进行隔离评估
- 官方镜像格式：`swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}`
- Agent 增强镜像添加 `-agent` 后缀
- 需要至少 120GB 磁盘空间、16GB RAM、8 CPU 核心

### 结果文件

实验结果保存在 `experiments/results/` 目录：
- `{instance_id}_{mode}_prompt.txt`: 使用的 prompt
- `{instance_id}_{mode}_result.json`: 实验结果（包含 patch、tokens、执行次数等）
- Run-Less 模式文件名包含 K 值：`{instance_id}_run_less_k{K}_result.json`

## 研究目标

目标会议：ISSTA 2026（软件测试与分析国际研讨会）

核心贡献：
1. 提出执行环境的三分法范式（Run-Free/Run-Less/Run-Full）
2. 证明限制执行 + 智能插桩可能优于无限制执行
3. 将调试过程重新定义为"实验设计问题"而非"搜索问题"
4. 提供 Green AI 视角：降低执行成本，提高推理质量

预期发现：Run-Less + Logging ≈ 或 > Run-Full，但成本显著降低。
