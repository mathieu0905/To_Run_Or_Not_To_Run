# 在 Docker 容器内运行实验指南

## 架构说明

所有实验脚本都在 Docker 容器内运行，通过 volume 挂载实现输出实时同步到宿主机。

**输出目录结构**：
```
output/
├── swebenchlite/          # SWE-bench Lite 数据集
│   └── {instance_id}/     # 实例 ID（如 django__django-11099）
│       ├── trace.jsonl    # Agent 执行 trace
│       ├── patch.diff     # 生成的补丁
│       ├── prompt_{mode}.txt  # 使用的 prompt
│       └── result_{mode}.json # 实验结果摘要
└── swebenchverified/      # SWE-bench Verified 数据集
    └── {instance_id}/
        └── ...
```

## 前置准备

### 1. 设置环境变量

创建 `.env` 文件（或在 shell 中导出）：

```bash
# Claude Code 认证
export ANTHROPIC_API_KEY="your-api-key"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"  # 可选

# Codex 认证（如果使用）
export OPENAI_API_KEY="your-api-key"

# 代理设置（如果需要）
export http_proxy="http://127.0.0.1:15732"
export https_proxy="http://127.0.0.1:15732"
```

### 2. 构建或拉取 Docker 镜像

```bash
# 如果使用官方基础镜像
docker pull swebench/sweb.eval.x86_64.base:latest

# 或者使用你自己构建的 Agent 增强镜像
# docker pull swebench/sweb.eval.x86_64.{repo}_{version}_{issue}-agent:latest
```

## 使用方法

### 方式 1: 使用 Docker Compose（推荐）

#### 启动容器

```bash
# 启动交互式容器
docker-compose up -d swebench-runner

# 进入容器
docker-compose exec swebench-runner bash
```

#### 在容器内运行实验

```bash
# 进入实验目录
cd /workspace/experiments

# 运行单个实验
python runner.py django__django-11099 run_free
python runner.py django__django-11099 run_less 2
python runner.py django__django-11099 run_full

# 指定数据集
python runner.py django__django-11099 run_less 2 claude_code 600 princeton-nlp/SWE-bench_Verified
```

#### 查看输出（在宿主机）

```bash
# 输出会实时同步到宿主机的 output/ 目录
ls output/swebenchlite/django__django-11099/
# 输出：trace.jsonl  patch.diff  prompt_run_free.txt  result_run_free.json
```

#### 停止容器

```bash
docker-compose down
```

### 方式 2: 直接使用 Docker 命令

```bash
# 启动容器并挂载目录
docker run -it --rm \
  --name swebench-runner \
  -v $(pwd):/workspace \
  -v $(pwd)/output:/workspace/output \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  --network host \
  swebench/sweb.eval.x86_64.base:latest \
  bash

# 在容器内运行实验
cd /workspace/experiments
python runner.py django__django-11099 run_free
```

## 批量运行实验

### 创建实例列表文件

```bash
# 在宿主机创建实例列表
cat > instances.txt <<EOF
django__django-11099
django__django-11001
astropy__astropy-12907
EOF
```

### 在容器内运行批量实验

```bash
# 进入容器
docker-compose exec swebench-runner bash

# 运行批量实验
cd /workspace/experiments
python batch_runner.py ../instances.txt run_less 2 4

# 参数说明：
# - ../instances.txt: 实例列表文件
# - run_less: 执行模式
# - 2: run_less 的执行次数限制
# - 4: 并发数（同时运行 4 个实例）
```

## 常见问题

### Q1: 如何查看实时输出？

输出会实时同步到宿主机的 `output/` 目录，你可以在宿主机上查看：

```bash
# 查看 trace
tail -f output/swebenchlite/django__django-11099/trace.jsonl

# 查看 patch
cat output/swebenchlite/django__django-11099/patch.diff
```

### Q2: 如何在容器内安装额外的依赖？

```bash
# 进入容器
docker-compose exec swebench-runner bash

# 安装 Python 包
pip install some-package

# 或者修改 Dockerfile 并重新构建镜像
```

### Q3: 如何使用不同的数据集？

```bash
# SWE-bench Lite（默认）
python runner.py instance_id run_free

# SWE-bench Verified
python runner.py instance_id run_free claude_code 600 princeton-nlp/SWE-bench_Verified
```

### Q4: 如何调试失败的实验？

```bash
# 查看结果 JSON
cat output/swebenchlite/instance_id/result_run_free.json

# 查看完整 trace
cat output/swebenchlite/instance_id/trace.jsonl

# 查看 prompt
cat output/swebenchlite/instance_id/prompt_run_free.txt
```

### Q5: 容器内的修改会丢失吗？

- **代码修改**：通过 volume 挂载，容器内对 `/workspace` 的修改会同步到宿主机
- **输出文件**：通过 volume 挂载，输出会实时同步到宿主机的 `output/` 目录
- **系统级修改**（如 apt install）：容器重启后会丢失，建议修改 Dockerfile

## 性能优化建议

### 1. 并发控制

```bash
# 根据机器资源调整并发数
# 推荐：CPU 核心数的 50-75%
python batch_runner.py instances.txt run_less 2 4  # 4 个并发
```

### 2. 资源限制

在 `docker-compose.yml` 中添加资源限制：

```yaml
services:
  swebench-runner:
    # ...
    deploy:
      resources:
        limits:
          cpus: '8.0'
          memory: 16G
        reservations:
          cpus: '4.0'
          memory: 8G
```

### 3. 使用 SSD 存储

确保 `output/` 目录在 SSD 上，以提高 I/O 性能。

## 下一步

1. **测试单个实例**：先运行一个实例验证环境配置正确
2. **小批量测试**：运行 3-5 个实例测试批量运行功能
3. **完整实验**：运行完整的 SWE-bench Lite（300 个实例）

## 相关文件

- `docker-compose.yml` - Docker Compose 配置
- `experiments/runner.py` - 单个实验运行器
- `experiments/batch_runner.py` - 批量实验运行器（待实现）
- `experiments/prompt_builder.py` - Prompt 构造器
- `experiments/agent_caller.py` - Agent 调用器
