# 批量实验计划

## 实验配置

### 测试实例（3个）
来自 `test_3_instances.txt`：
1. `django__django-11099`
2. `django__django-11001`
3. `astropy__astropy-12907`

### Agent 类型（2个）
1. **claude_code** - Claude Code CLI
2. **codex** - OpenAI Codex

### 执行模式（6个配置）
1. **run_free** - 完全不执行代码，纯推理修复
2. **run_less K=1** - 最多执行 1 次测试（极限约束）
3. **run_less K=2** - 最多执行 2 次测试（中等约束）
4. **run_less K=3** - 最多执行 3 次测试（宽松约束）
5. **run_cost** - 成本意识决策，模型自主决定是否执行
6. **run_full** - 无限制执行，允许试错循环

### 实验总数
**3 实例 × 2 agents × 6 模式 = 36 个实验**

## 输出目录结构

```
output/
└── swebenchlite/
    ├── claude_code/
    │   ├── run_free/
    │   │   ├── django__django-11099/
    │   │   │   ├── trace.jsonl
    │   │   │   ├── patch.diff
    │   │   │   ├── prompt_run_free.txt
    │   │   │   └── result_run_free.json
    │   │   ├── django__django-11001/
    │   │   └── astropy__astropy-12907/
    │   ├── run_less/
    │   │   ├── django__django-11099/
    │   │   │   ├── trace.jsonl
    │   │   │   ├── patch.diff
    │   │   │   ├── prompt_run_less_k1.txt
    │   │   │   └── result_run_less_k1.json
    │   │   └── ...
    │   ├── run_cost/
    │   └── run_full/
    └── codex/
        ├── run_free/
        ├── run_less/
        ├── run_cost/
        └── run_full/
```

## 运行方式

### 方式 1：使用批量脚本（推荐）

```bash
# 在项目根目录运行
./run_all_experiments.sh
```

这个脚本会：
- 自动遍历所有 agent 和模式组合
- 使用 8 个并发 worker（可在脚本中调整）
- 为每个配置运行 batch_runner.py
- 显示进度和彩色输出
- 在配置之间添加短暂延迟避免资源冲突

### 方式 2：手动运行单个配置

```bash
cd experiments

# Claude Code + run_free
python batch_runner.py ../test_3_instances.txt run_free 2 8 claude_code 600

# Claude Code + run_less K=1
python batch_runner.py ../test_3_instances.txt run_less 1 8 claude_code 600

# Claude Code + run_less K=2
python batch_runner.py ../test_3_instances.txt run_less 2 8 claude_code 600

# Claude Code + run_less K=3
python batch_runner.py ../test_3_instances.txt run_less 3 8 claude_code 600

# Claude Code + run_cost
python batch_runner.py ../test_3_instances.txt run_cost 2 8 claude_code 600

# Claude Code + run_full
python batch_runner.py ../test_3_instances.txt run_full 2 8 claude_code 600

# Codex + run_free
python batch_runner.py ../test_3_instances.txt run_free 2 8 codex 600

# Codex + run_less K=1
python batch_runner.py ../test_3_instances.txt run_less 1 8 codex 600

# ... 以此类推
```

## Docker 容器命名说明

由于输出目录结构已经按 `{agent}/{mode}/{instance}` 分层，不同的配置会自动分开：
- 不同的 agent（claude_code vs codex）会使用不同的输出目录
- 不同的 mode（run_free vs run_less 等）会使用不同的输出目录
- 相同 instance 的不同配置不会同时运行（串行执行）

因此 **不会出现 Docker 容器命名冲突**。

## 并发设置

- **WORKERS=8**：每个配置内部并行运行 8 个实例
- 由于只有 3 个实例，实际并发数为 3
- 不同配置之间串行执行，避免资源冲突

## 预计运行时间

假设每个实验平均 600 秒（10 分钟）：
- 36 个实验 × 10 分钟 = 360 分钟 = **6 小时**

实际时间可能更短，因为：
1. run_free 模式不执行代码，速度较快
2. run_less 模式执行次数有限，速度中等
3. 只有 run_full 模式可能需要较长时间

## 监控进度

### 查看实时输出
```bash
# 查看某个实例的 trace
tail -f output/swebenchlite/claude_code/run_free/django__django-11099/trace.jsonl

# 查看生成的补丁
cat output/swebenchlite/claude_code/run_free/django__django-11099/patch.diff

# 查看结果摘要
cat output/swebenchlite/claude_code/run_free/django__django-11099/result_run_free.json
```

### 统计完成情况
```bash
# 统计已完成的实验数量
find output/swebenchlite -name "result_*.json" | wc -l

# 列出所有已完成的实验
find output/swebenchlite -name "result_*.json" -exec echo {} \;
```

## 结果分析

每个实验的结果文件（`result_*.json`）包含：
- `instance_id`: 实例 ID
- `mode`: 执行模式
- `k`: run_less 的执行次数限制（如果适用）
- `agent_type`: agent 类型
- `tokens_used`: 使用的 token 数量
- `exec_count`: 实际执行次数
- `duration_sec`: 运行时长（秒）
- `success`: 是否成功生成补丁
- `error`: 错误信息（如果有）

## 注意事项

1. **环境变量**：确保设置了 `ANTHROPIC_API_KEY` 和 `OPENAI_API_KEY`
2. **Docker**：确保 Docker 服务正在运行
3. **磁盘空间**：每个实验会生成 trace 和 patch 文件，确保有足够空间
4. **网络**：需要访问 Hugging Face 下载数据集和 API 调用
5. **断点续传**：如果中断，重新运行相同命令会自动跳过已完成的实验

## 故障排查

### 如果某个配置失败
```bash
# 重新运行该配置（会自动跳过已完成的实例）
cd experiments
python batch_runner.py ../test_3_instances.txt <mode> <k> 8 <agent> 600
```

### 清理 checkpoint 重新运行
```bash
# 删除 checkpoint 文件
rm output/swebenchlite/checkpoint.json

# 重新运行
./run_all_experiments.sh
```

### 查看详细错误
```bash
# 查看某个实例的完整 trace
cat output/swebenchlite/claude_code/run_free/django__django-11099/trace.jsonl | jq .
```
