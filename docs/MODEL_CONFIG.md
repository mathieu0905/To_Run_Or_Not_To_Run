# Model Configuration Guide

## Overview

Now supports configuring Claude Code and Codex models through environment variables. The configuration script runs automatically when the container starts.

## Environment Variables

### Claude Code Model Configuration

```bash
export CLAUDE_MODEL="sonnet"  # or "opus"
```

Supported values:
- `sonnet` (default) - Claude Sonnet 4.5
- `opus` - Claude Opus 4.5

### Codex Model Configuration

```bash
export CODEX_MODEL="gpt-5.2"  # default value
export CODEX_REASONING_EFFORT="xhigh"  # default value used by the release scripts
```

Supported values:
- `CODEX_MODEL`: Any model name supported by Codex
- `CODEX_REASONING_EFFORT`: `low`, `medium`, `high`

## Usage

### Method 1: Set environment variables before starting the container

```bash
# Set models
export CLAUDE_MODEL="opus"
export CODEX_MODEL="gpt-5.2"
export CODEX_REASONING_EFFORT="high"

# Start container
docker-compose up -d swebench-runner
docker-compose exec swebench-runner bash
```

### Method 2: Specify in docker-compose command

```bash
CLAUDE_MODEL=opus CODEX_MODEL=gpt-5.2 docker-compose up -d swebench-runner
```

### Method 3: Modify .env file

Create or edit the `.env` file in the project root directory:

```bash
# .env
CLAUDE_MODEL=opus
CODEX_MODEL=gpt-5.2
CODEX_REASONING_EFFORT=high
```

Then start the container normally:

```bash
docker-compose up -d swebench-runner
```

## Configuration File Locations

The configuration script automatically modifies the following files:

### Claude Code
- Configuration file: `~/.claude/settings.json`
- Modified field: `"model": "sonnet"` or `"model": "opus"`

### Codex
- Configuration file: `~/.config/codex/config.toml`
- Modified fields:
  - `model = "gpt-5.2"`
  - `model_reasoning_effort = "medium"`

## Verify Configuration

After entering the container, you can check if the configuration is effective:

```bash
# Check Claude Code configuration
cat ~/.claude/settings.json | grep model

# Check Codex configuration
cat ~/.config/codex/config.toml | grep model
```

## Using Different Models in Batch Experiments

### Example 1: Run all experiments with Opus

```bash
export CLAUDE_MODEL="opus"
bash scripts/run_claude.sh -f
```

### Example 2: Use different models for different agents

Since Claude Code and Codex use different configuration files, you can:

1. First run Claude Code experiments (using Opus):
```bash
export CLAUDE_MODEL="opus"
bash scripts/run_claude.sh -f
```

2. Then run Codex experiments (using a different model):
```bash
export CODEX_MODEL="gpt-5.2"
export CODEX_REASONING_EFFORT="high"
bash scripts/run_codex.sh -f
```

## Configuration Script

The configuration script is located at: `docker/configure_models.sh`

This script runs automatically when the container starts and configures models based on environment variables.

## Troubleshooting

### Configuration not taking effect

1. Check if environment variables are set correctly:
```bash
echo $CLAUDE_MODEL
echo $CODEX_MODEL
```

2. Restart the container:
```bash
docker-compose down
docker-compose up -d swebench-runner
```

3. Manually run the configuration script:
```bash
docker-compose exec swebench-runner /workspace/docker/configure_models.sh
```

### View configuration logs

The container displays configuration information on startup:
```bash
docker-compose logs swebench-runner | grep "Configuration"
```
