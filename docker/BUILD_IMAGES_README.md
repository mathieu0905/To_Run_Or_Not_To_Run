# Docker 镜像构建工具使用文档

## 概述

`build_agent_images_parallel.py` 是一个并行构建 SWE-bench Docker 镜像的工具，支持为 Agent 实验环境批量构建增强镜像。

## 功能特性

- 支持 SWE-bench Lite（300 个实例）和 SWE-bench-verified（500 个实例）两个数据集
- 并行构建，默认 16 个 worker 同时工作
- 自动跳过已存在的镜像
- 详细的构建日志记录
- 实时进度显示

## 前置要求

1. Docker 已安装并运行
2. 有足够的磁盘空间（建议至少 120GB）
3. 网络连接正常（需要从 Docker Hub 拉取基础镜像）
4. Python 3.10+

## 使用方法

### 基本语法

```bash
python build_agent_images_parallel.py [dataset]
```

### 参数说明

- `dataset`: 可选参数，指定要构建的数据集
  - `lite`: SWE-bench Lite（300 个实例，默认）
  - `verified`: SWE-bench-verified（500 个实例）

### 使用示例

#### 1. 构建 SWE-bench Lite 镜像（默认）

```bash
# 方式 1：不带参数（默认使用 lite）
python build_agent_images_parallel.py

# 方式 2：显式指定 lite
python build_agent_images_parallel.py lite
```

#### 2. 构建 SWE-bench-verified 镜像

```bash
python build_agent_images_parallel.py verified
```

## 输出说明

### 控制台输出

```
Building 300 images from lite dataset with 16 workers...
[1/300] ✓ django-11099
[2/300] ✗ pytest-7168: build failed (see swebench_sweb.eval.x86_64.pytest-dev_1776_pytest-7168.log)
[3/300] ✓ sympy-20590
...
Done: 298/300 succeeded
Failed (2):
  swebench/sweb.eval.x86_64.pytest-dev_1776_pytest-7168: build failed (see swebench_sweb.eval.x86_64.pytest-dev_1776_pytest-7168.log)
  swebench/sweb.eval.x86_64.django_1776_django-12345: pull failed (see swebench_sweb.eval.x86_64.django_1776_django-12345.log)
```

### 构建日志

所有构建日志保存在 `build_logs/` 目录下，文件名格式：
```
swebench_sweb.eval.x86_64.{repo}_{version}_{issue_id}.log
```

每个日志文件包含：
- 基础镜像拉取过程
- Agent overlay 构建过程
- 错误信息（如果构建失败）

## 镜像命名规则

### 基础镜像
```
swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}:latest
```

### Agent 增强镜像
```
swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}-agent:latest
```

示例：
- 基础镜像：`swebench/sweb.eval.x86_64.django_1776_django-11099:latest`
- Agent 镜像：`swebench/sweb.eval.x86_64.django_1776_django-11099-agent:latest`

## 配置文件

### image_list.txt
包含 SWE-bench Lite 的 300 个镜像列表。

### image_list_verified.txt
包含 SWE-bench-verified 的 500 个镜像列表。

### Dockerfile.agent-overlay
定义 Agent 增强层的 Dockerfile，在基础镜像上添加：
- Agent 运行所需的工具
- 环境配置
- 依赖包

## 性能调优

### 调整并行度

编辑脚本中的 `MAX_WORKERS` 常量：

```python
MAX_WORKERS = 16  # 根据 CPU 核心数和网络带宽调整
```

建议值：
- 8 核 CPU：8-12 workers
- 16 核 CPU：16-24 workers
- 32 核 CPU：24-32 workers

### 磁盘空间管理

定期清理未使用的镜像：

```bash
# 清理悬空镜像
docker image prune -f

# 清理所有未使用的镜像
docker image prune -a -f
```

## 故障排查

### 问题 1：镜像拉取失败

**症状**：日志显示 "pull failed"

**解决方案**：
1. 检查网络连接
2. 检查 Docker Hub 访问权限
3. 重新运行脚本（会自动跳过已成功的镜像）

### 问题 2：构建失败

**症状**：日志显示 "build failed"

**解决方案**：
1. 查看对应的日志文件了解详细错误
2. 检查 Dockerfile.agent-overlay 是否正确
3. 确认基础镜像是否完整

### 问题 3：磁盘空间不足

**症状**：构建过程中出现 "no space left on device"

**解决方案**：
1. 清理 Docker 缓存：`docker system prune -a`
2. 删除不需要的镜像
3. 增加磁盘空间

## 与实验流程的集成

构建完成后，镜像可用于运行 SWE-bench 实验：

```bash
# 运行单个实验
python experiments/runner.py <instance_id> <mode>

# 示例
python experiments/runner.py django__django-11099 run_less 2
```

## 技术细节

### 构建流程

1. 从 `image_list.txt` 或 `image_list_verified.txt` 读取镜像列表
2. 对每个镜像：
   - 检查 Agent 镜像是否已存在（跳过已存在的）
   - 拉取基础镜像
   - 使用 Dockerfile.agent-overlay 构建 Agent 镜像
   - 记录构建日志
3. 汇总构建结果

### 并发控制

使用 Python 的 `ThreadPoolExecutor` 实现并发：
- 每个 worker 独立处理一个镜像
- 自动负载均衡
- 线程安全的日志记录

## 相关文件

- `build_agent_images_parallel.py`: 主脚本
- `Dockerfile.agent-overlay`: Agent 增强层定义
- `image_list.txt`: SWE-bench Lite 镜像列表
- `image_list_verified.txt`: SWE-bench-verified 镜像列表
- `build_logs/`: 构建日志目录

## 许可证

本工具是 run_free_run_less_run_full 研究项目的一部分。
