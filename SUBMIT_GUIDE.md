# SWE-bench 提交指南

## 环境准备

1. 安装 sb-cli：
```bash
conda activate swebench
pip install -e sb-cli/
```

2. 配置 API Key（已保存在 `.env` 文件中）：
```bash
# .env 文件内容
SWEBENCH_API_KEY=swb_xxx...
```

## 查看配额

```bash
conda activate swebench
export SWEBENCH_API_KEY=swb_xxx...
sb-cli get-quotas
```

## 使用 submit_to_swebench.sh

### 列出所有可用组合

```bash
./submit_to_swebench.sh --list
```

输出示例：
```
Dataset              Agent           Mode            Instances  Patches
----------------------------------------------------------------------
swebenchlite         codex           run_free        100        100
swebenchverified     claude_code     run_free        33         33
swebenchverified     codex           run_free        99         99
...
```

### 生成 predictions 文件（不提交）

```bash
./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free --gen-only
```

生成的文件保存在 `predictions/` 目录下。

### 提交到 SWE-bench

```bash
# 使用默认 run_id (agent_mode)
./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free

# 自定义 run_id
./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free --run-id my_experiment_v1
```

### 生成所有 predictions 文件

```bash
./submit_to_swebench.sh --all --gen-only
```

## 直接使用 sb-cli

### 提交命令格式

```bash
sb-cli submit <subset> <split> --predictions_path <file> --run_id <id>
```

参数说明：
- `subset`: `swe-bench_lite` | `swe-bench_verified` | `swe-bench-m`
- `split`: `test` | `dev`
- `--predictions_path`: predictions JSON 文件路径
- `--run_id`: 运行标识符

### 示例

```bash
# 提交到 SWE-bench Verified test 集
sb-cli submit swe-bench_verified test \
    --predictions_path predictions/swebenchverified_codex_run_free.json \
    --run_id codex_run_free

# 提交到 SWE-bench Lite test 集
sb-cli submit swe-bench_lite test \
    --predictions_path predictions/swebenchlite_codex_run_free.json \
    --run_id codex_run_free
```

### 查看结果

```bash
# 获取报告
sb-cli get-report swe-bench_verified test <run_id>

# 列出所有运行
sb-cli list-runs swe-bench_verified test
```

## Predictions 文件格式

```json
[
    {
        "instance_id": "django__django-11099",
        "model_patch": "diff --git a/...",
        "model_name_or_path": "codex_run_free"
    },
    ...
]
```

## 数据集映射

| 本地目录名 | sb-cli subset 名称 |
|-----------|-------------------|
| swebenchlite | swe-bench_lite |
| swebenchverified | swe-bench_verified |

## 注意事项

- test 集提交有配额限制，请谨慎使用
- 提交前建议先用 `--gen-only` 检查生成的 predictions 文件
- 每次提交的 run_id 应该唯一，便于追踪结果

./submit_to_swebench.sh --dataset swebenchverified --agent codex --mode run_free