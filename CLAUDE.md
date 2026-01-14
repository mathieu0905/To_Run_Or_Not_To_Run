# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个研究项目，探索在代码修复任务中执行环境对 LLM Agent 能力的影响。核心研究问题：**执行环境是"必要能力"还是"工程捷径"？**

研究对比四种执行范式：
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
├── batch_runner.py     # 批量运行器：并行执行多个实验
├── prompt_builder.py   # Prompt 构造器：为不同模式生成 system prompt
├── agent_caller.py     # Agent 调用器：统一封装 Claude Code 和 Codex
├── download_datasets.py # 数据集下载工具
└── tests/             # 单元测试和集成测试

output/                # 实验输出目录（实时同步）
├── swebenchlite/      # SWE-bench Lite 数据集结果
│   └── {instance_id}/ # 每个实例的输出
│       ├── trace.jsonl       # Agent 执行 trace
│       ├── patch.diff        # 生成的补丁
│       ├── prompt_{mode}.txt # 使用的 prompt
│       └── result_{mode}.json # 实验结果摘要
└── swebenchverified/  # SWE-bench Verified 数据集结果

SWE-bench/             # SWE-bench 官方代码库（子模块）
├── swebench/harness/  # 评估框架
└── swebench/collect/  # 数据收集工具

docker/                # Docker 镜像构建脚本
docker-compose.yml     # Docker Compose 配置
```

### 关键设计

**运行环境**：
- 所有实验脚本在 Docker 容器内运行
- 通过 volume 挂载实现输出实时同步到宿主机
- 输出目录结构：`output/{dataset}/{instance_id}/`

**Prompt 构造 (prompt_builder.py)**
- 每种模式有独立的 prompt 模板（英文）
- Run-Less 模式强调"执行预算"概念，要求 Agent 输出剩余次数
- Run-Cost 模式要求 Agent 输出信心水平和决策理由
- 所有模式都禁用 git 命令以避免干扰实验环境
- 支持多种测试框架（pytest, unittest, Django tests, tox, nose）

**Agent 调用 (agent_caller.py)**
- 统一接口支持 Claude Code 和 Codex
- 通过 subprocess 调用 CLI，捕获 stream-json 格式的 trace
- 自动统计 token 使用量和执行次数
- 执行次数统计：只计入测试运行（pytest, unittest, Django tests 等），不计入 bash 查看命令

**实验运行 (runner.py)**
- 从 SWE-bench 数据集加载实例
- 构建对应模式的 prompt
- 调用 agent 并记录完整 trace
- 提取 git diff 格式的补丁
- 保存结果到实例目录

**批量运行 (batch_runner.py)**
- 并行执行多个实例（ThreadPoolExecutor）
- 支持断点续传（checkpoint.json）
- 实时进度显示
- 失败处理和自动重试

## 常用命令

### 启动 Docker 容器

```bash
# 启动容器
docker-compose up -d swebench-runner

# 进入容器
docker-compose exec swebench-runner bash
```

### 在容器内运行单个实验

```bash
cd /workspace/experiments

# Run-Free 模式（不执行代码）
python runner.py django__django-11099 run_free

# Run-Less 模式（限制 K 次执行）
python runner.py django__django-11099 run_less 2

# Run-Cost 模式（成本意识决策）
python runner.py django__django-11099 run_cost

# Run-Full 模式（无限制执行）
python runner.py django__django-11099 run_full

# 指定数据集
python runner.py django__django-11099 run_less 2 claude_code 600 princeton-nlp/SWE-bench_Verified
```

### 在容器内运行批量实验

```bash
cd /workspace/experiments

# 运行批量实验
python batch_runner.py ../test_instances.txt run_less 2 4

# 参数说明：
# - ../test_instances.txt: 实例列表文件
# - run_less: 执行模式
# - 2: run_less 的执行次数限制
# - 4: 并发数（同时运行 4 个实例）

# 使用不同数据集
python batch_runner.py instances.txt run_less 2 4 claude_code 600 princeton-nlp/SWE-bench_Verified
```

### 在宿主机查看输出

```bash
# 输出会实时同步到宿主机
ls output/swebenchlite/django__django-11099/

# 查看 trace
tail -f output/swebenchlite/django__django-11099/trace.jsonl

# 查看 patch
cat output/swebenchlite/django__django-11099/patch.diff

# 查看结果
cat output/swebenchlite/django__django-11099/result_run_less_k2.json
```

### 测试

```bash
# 在容器内运行测试
cd /workspace/experiments
pytest tests/

# 运行特定测试
pytest tests/test_runner.py
pytest tests/test_agent_caller.py
```

### SWE-bench 评估

```bash
# 评估补丁（需要 Docker）
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --predictions_path <path_to_predictions> \
    --max_workers <num_workers> \
    --run_id <run_id>
```

## 实验设计要点

### 输出目录结构

每个实例的输出保存在 `output/{dataset}/{instance_id}/` 目录下：
- `trace.jsonl` - Agent 执行的完整 trace（stream-json 格式）
- `patch.diff` - 生成的 git diff 格式补丁
- `prompt_{mode}.txt` - 使用的 prompt
- `result_{mode}.json` - 实验结果摘要（tokens, exec_count, duration, success 等）
- `checkpoint.json` - 批量运行的断点文件（在数据集目录下）

### 执行次数统计规则

**计入执行次数**：
- `pytest` 或 `python -m pytest`
- `python -m unittest`
- `python manage.py test`（Django tests）
- `tox`, `nose`, `nosetests`
- `python script.py`（运行 .py 文件）

**不计入执行次数**：
- `ls`, `cat`, `grep`, `find` 等查看命令
- `git` 命令（实验中禁用）
- `python -c "..."` 简单计算
- `python --version` 等信息查询

### Run-Less 模式的关键机制

1. **测试脚本优先**：Agent 需要先根据问题描述编写测试脚本
2. **识别测试命令**：Agent 需要识别项目使用的测试框架
3. **日志插桩**：在运行测试前，Agent 应在关键位置插入 print/log 语句
4. **假设驱动**：每次执行前明确假设，执行后分析结果
5. **预算追踪**：Agent 必须输出"剩余测试运行次数: X"

### Prompt 设计原则

- **Run-Free**: 强调"一次就对"，不能依赖反馈
- **Run-Less**: 强调"高价值实验"，每次执行都要最大化信息增益
- **Run-Cost**: 强调"理性决策"，根据信心水平决定是否执行
- **Run-Full**: 允许试错，但仍建议先写测试脚本

## 开发注意事项

### Docker 环境

- 所有脚本在 Docker 容器内运行
- 通过 volume 挂载实现输出实时同步
- 环境变量通过 docker-compose.yml 配置
- 使用 `--network host` 共享宿主机网络（用于代理）

### Agent 调用

- Claude Code 需要 `ANTHROPIC_API_KEY` 环境变量
- Codex 需要 `OPENAI_API_KEY` 环境变量
- 两者都通过 CLI 调用，输出为 stream-json 格式
- 超时设置建议 600 秒以上

### 批量运行

- 使用 ThreadPoolExecutor 实现并发
- 默认并发数为 4，可根据机器资源调整
- 支持断点续传：中断后重新运行会跳过已完成的实例
- Checkpoint 文件保存在 `output/{dataset}/checkpoint.json`

### 结果文件

实验结果保存在 `output/{dataset}/{instance_id}/` 目录：
- 所有文件实时同步到宿主机
- trace.jsonl 包含完整的 agent 执行记录
- patch.diff 是标准的 git diff 格式
- result_{mode}.json 包含实验元数据

## 研究目标

目标会议：ISSTA 2026（软件测试与分析国际研讨会）

核心贡献：
1. 提出执行环境的四分法范式（Run-Free/Run-Less/Run-Cost/Run-Full）
2. 证明限制执行 + 智能插桩可能优于无限制执行
3. 将调试过程重新定义为"实验设计问题"而非"搜索问题"
4. 提供 Green AI 视角：降低执行成本，提高推理质量

预期发现：Run-Less + Logging ≈ 或 > Run-Full，但成本显著降低。

## 快速开始

1. **设置环境变量**（在宿主机）：
   ```bash
   export ANTHROPIC_API_KEY="your-api-key"
   export OPENAI_API_KEY="your-api-key"  # 如果使用 Codex
   ```

2. **启动容器**：
   ```bash
   docker-compose up -d swebench-runner
   docker-compose exec swebench-runner bash
   ```

3. **运行测试实验**：
   ```bash
   cd /workspace/experiments
   python runner.py django__django-11099 run_free
   ```

4. **查看输出**（在宿主机）：
   ```bash
   ls output/swebenchlite/django__django-11099/
   cat output/swebenchlite/django__django-11099/patch.diff
   ```

5. **运行批量实验**：
   ```bash
   cd /workspace/experiments
   python batch_runner.py ../test_instances.txt run_less 2 4
   ```

详细使用说明请参考 `DOCKER_USAGE.md`。
