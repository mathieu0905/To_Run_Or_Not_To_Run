# SWE-bench Agent 镜像构建文档

## 概述

本文档记录了为 Run-Free/Run-Less/Run-Full 实验构建 Docker 镜像的完整流程。

## 镜像架构

### 基础镜像来源
使用 SWE-bench 官方预构建镜像：
- 镜像格式：`swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}`
- 示例：`swebench/sweb.eval.x86_64.django_1776_django-16408`
- 总数：300 个实例（SWE-bench Lite）

### Agent 增强层
在官方镜像基础上添加 Agent 工具：
- Node.js 20.x LTS
- Claude Code CLI (@anthropic-ai/claude-code)
- Codex CLI (@openai/codex)

## 构建流程

### 1. Dockerfile 设计

文件：`Dockerfile.agent-overlay`

```dockerfile
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# 安装 Node.js 20.x
RUN apt-get update && apt-get install -y curl gnupg
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 安装 Agent CLI 工具
RUN npm install -g @anthropic-ai/claude-code @openai/codex

# 创建配置目录
RUN mkdir -p /root/.claude /root/.codex
```

### 2. 批量构建脚本

文件：`build_agent_images_parallel.py`

关键特性：
- 32 线程并行构建
- 自动拉取官方镜像
- 构建增强版镜像（添加 -agent 后缀）
- 进度跟踪和错误处理

使用方法：
```bash
python build_agent_images_parallel.py
```

### 3. 镜像命名规范

- 官方镜像：`swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}`
- Agent 镜像：`swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}-agent`

示例：
```
官方: swebench/sweb.eval.x86_64.django_1776_django-16408
Agent: swebench/sweb.eval.x86_64.django_1776_django-16408-agent
```

## 认证配置

### Claude Code 认证

**问题**：Claude Code 需要 OAuth 认证，容器中无法直接使用。

**解决方案**：挂载宿主机的 `.claude` 目录到容器。

关键文件：
- `.claude/.credentials.json`：包含 OAuth token（accessToken, refreshToken, expiresAt）
- `.claude/settings.json`：用户配置
- `.claude/history.jsonl`：对话历史

容器运行配置：
```bash
docker run \
  --network host \
  -v /home/zhihao/.claude:/root/.claude \
  -e http_proxy=http://127.0.0.1:15732 \
  -e https_proxy=http://127.0.0.1:15732 \
  swebench/sweb.eval.x86_64.django_1776_django-16408-agent
```

### Codex 认证

挂载配置文件：
- `.codex/auth.json`：API 认证信息
- `.codex/config.toml`：Codex 配置

## 验证步骤

### 1. 验证镜像构建成功
```bash
docker images | grep "\-agent"
```

### 2. 验证工具安装
```bash
docker run --rm <image_name> node --version
docker run --rm <image_name> npm --version
docker run --rm <image_name> claude --version
```

### 3. 验证 Claude Code 认证
```bash
docker run --rm \
  --network host \
  -v /home/zhihao/.claude:/root/.claude \
  -e http_proxy=http://127.0.0.1:15732 \
  <image_name> \
  timeout 60 claude chat "你好"
```

预期输出：Claude Code 返回响应（可能超时但有输出）。

## 构建统计

- 总实例数：300
- 已构建镜像：84+（持续构建中）
- 构建线程数：32
- 平均构建时间：~2-3 分钟/镜像

## MVP 测试实例

选择的 5 个测试实例（镜像已构建）：
1. django__django-16408
2. django__django-16595
3. django__django-16816
4. django__django-16527
5. django__django-15814

## 注意事项

1. **网络配置**：使用 `--network host` 确保容器可以访问宿主机代理
2. **代理设置**：设置 `http_proxy` 和 `https_proxy` 环境变量
3. **认证文件**：确保 `.claude` 目录以可写方式挂载，Claude Code 需要创建子目录
4. **超时设置**：Claude Code 可能需要较长时间响应，建议设置 60 秒以上超时

## 相关文件

- `Dockerfile.agent-overlay`：Agent 增强层 Dockerfile
- `build_agent_images_parallel.py`：批量构建脚本
- `image_list.txt`：300 个镜像名称列表
- `mvp_instances.txt`：MVP 测试实例列表（在 experiments/ 目录）
