# 模型配置说明

## 概述

现在支持通过环境变量配置 Claude Code 和 Codex 的模型。容器启动时会自动运行配置脚本。

## 环境变量

### Claude Code 模型配置

```bash
export CLAUDE_MODEL="sonnet"  # 或 "opus"
```

支持的值：
- `sonnet` (默认) - Claude Sonnet 4.5
- `opus` - Claude Opus 4.5

### Codex 模型配置

```bash
export CODEX_MODEL="gpt-5.2"  # 默认值
export CODEX_REASONING_EFFORT="medium"  # 默认值
```

支持的值：
- `CODEX_MODEL`: 任何 Codex 支持的模型名称
- `CODEX_REASONING_EFFORT`: `low`, `medium`, `high`

## 使用方式

### 方式 1：在启动容器前设置环境变量

```bash
# 设置模型
export CLAUDE_MODEL="opus"
export CODEX_MODEL="gpt-5.2"
export CODEX_REASONING_EFFORT="high"

# 启动容器
docker-compose up -d swebench-runner
docker-compose exec swebench-runner bash
```

### 方式 2：在 docker-compose 命令中指定

```bash
CLAUDE_MODEL=opus CODEX_MODEL=gpt-5.2 docker-compose up -d swebench-runner
```

### 方式 3：修改 .env 文件

创建或编辑项目根目录的 `.env` 文件：

```bash
# .env
CLAUDE_MODEL=opus
CODEX_MODEL=gpt-5.2
CODEX_REASONING_EFFORT=high
```

然后正常启动容器：

```bash
docker-compose up -d swebench-runner
```

## 配置文件位置

配置脚本会自动修改以下文件：

### Claude Code
- 配置文件：`~/.claude/settings.json`
- 修改字段：`"model": "sonnet"` 或 `"model": "opus"`

### Codex
- 配置文件：`~/.config/codex/config.toml`
- 修改字段：
  - `model = "gpt-5.2"`
  - `model_reasoning_effort = "medium"`

## 验证配置

进入容器后，可以查看配置是否生效：

```bash
# 查看 Claude Code 配置
cat ~/.claude/settings.json | grep model

# 查看 Codex 配置
cat ~/.config/codex/config.toml | grep model
```

## 在批量实验中使用不同模型

### 示例 1：使用 Opus 运行所有实验

```bash
export CLAUDE_MODEL="opus"
./run_all_experiments.sh
```

### 示例 2：为不同 agent 使用不同模型

由于 Claude Code 和 Codex 使用不同的配置文件，你可以：

1. 先运行 Claude Code 实验（使用 Opus）：
```bash
export CLAUDE_MODEL="opus"
# 修改 run_all_experiments.sh，只运行 claude_code
```

2. 再运行 Codex 实验（使用不同模型）：
```bash
export CODEX_MODEL="gpt-5.2"
export CODEX_REASONING_EFFORT="high"
# 修改 run_all_experiments.sh，只运行 codex
```

## 配置脚本

配置脚本位于：`docker/configure_models.sh`

该脚本会在容器启动时自动运行，根据环境变量配置模型。

## 故障排查

### 配置未生效

1. 检查环境变量是否正确设置：
```bash
echo $CLAUDE_MODEL
echo $CODEX_MODEL
```

2. 重新启动容器：
```bash
docker-compose down
docker-compose up -d swebench-runner
```

3. 手动运行配置脚本：
```bash
docker-compose exec swebench-runner /workspace/docker/configure_models.sh
```

### 查看配置日志

容器启动时会显示配置信息：
```bash
docker-compose logs swebench-runner | grep "配置"
```
