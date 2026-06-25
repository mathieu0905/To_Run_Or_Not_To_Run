# SWE-bench Agent Image Build Documentation

## Overview

This document records the complete process of building Docker images for Run-Free/Run-Less/Run-Full experiments.

## Image Architecture

### Base Image Source
Uses SWE-bench official pre-built images:
- Image format: `swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}`
- Example: `swebench/sweb.eval.x86_64.django_1776_django-16408`
- Total: 300 instances (SWE-bench Lite)

### Agent Enhancement Layer
Adds Agent tools on top of official images:
- Node.js 20.x LTS
- Claude Code CLI (@anthropic-ai/claude-code)
- Codex CLI (@openai/codex)

## Build Process

### 1. Dockerfile Design

File: `Dockerfile.agent-overlay`

```dockerfile
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

# Install Node.js 20.x
RUN apt-get update && apt-get install -y curl gnupg
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Agent CLI tools
RUN npm install -g @anthropic-ai/claude-code @openai/codex

# Create configuration directories
RUN mkdir -p /root/.claude /root/.codex
```

### 2. Batch Build Script

File: `build_agent_images_parallel.py`

Key features:
- 32 threads parallel build
- Automatic pull of official images
- Build enhanced images (with -agent suffix)
- Progress tracking and error handling

Usage:
```bash
python build_agent_images_parallel.py
```

### 3. Image Naming Convention

- Official image: `swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}`
- Agent image: `swebench/sweb.eval.x86_64.{repo}_{version}_{issue_id}-agent`

Example:
```
Official: swebench/sweb.eval.x86_64.django_1776_django-16408
Agent: swebench/sweb.eval.x86_64.django_1776_django-16408-agent
```

## Authentication Configuration

### Claude Code Authentication

**Problem**: Claude Code requires OAuth authentication, which cannot be used directly in containers.

**Solution**: Mount the host's `.claude` directory to the container.

Key files:
- `.claude/.credentials.json`: Contains OAuth token (accessToken, refreshToken, expiresAt)
- `.claude/settings.json`: User configuration
- `.claude/history.jsonl`: Conversation history

Container run configuration:
```bash
docker run \
  --network host \
  -v "$HOME/.claude:/root/.claude" \
  -e http_proxy=http://127.0.0.1:15732 \
  -e https_proxy=http://127.0.0.1:15732 \
  swebench/sweb.eval.x86_64.django_1776_django-16408-agent
```

### Codex Authentication

Mount configuration files:
- `.codex/auth.json`: API authentication information
- `.codex/config.toml`: Codex configuration

## Verification Steps

### 1. Verify Image Build Success
```bash
docker images | grep "\-agent"
```

### 2. Verify Tool Installation
```bash
docker run --rm <image_name> node --version
docker run --rm <image_name> npm --version
docker run --rm <image_name> claude --version
```

### 3. Verify Claude Code Authentication
```bash
docker run --rm \
  --network host \
  -v "$HOME/.claude:/root/.claude" \
  -e http_proxy=http://127.0.0.1:15732 \
  <image_name> \
  timeout 60 claude chat "Hello"
```

Expected output: Claude Code returns a response (may timeout but should have output).

## Build Statistics

- Total instances: 300
- Built images: 84+ (building in progress)
- Build threads: 32
- Average build time: ~2-3 minutes/image

## MVP Test Instances

Selected 5 test instances (images already built):
1. django__django-16408
2. django__django-16595
3. django__django-16816
4. django__django-16527
5. django__django-15814

## Notes

1. **Network Configuration**: Use `--network host` to ensure container can access host proxy
2. **Proxy Settings**: Set `http_proxy` and `https_proxy` environment variables
3. **Authentication Files**: Ensure `.claude` directory is mounted with write permissions, Claude Code needs to create subdirectories
4. **Timeout Settings**: Claude Code may take longer to respond, recommend setting timeout of 60 seconds or more

## Related Files

- `Dockerfile.agent-overlay`: Agent enhancement layer Dockerfile
- `build_agent_images_parallel.py`: Batch build script
- `image_list.txt`: List of 300 image names
- `mvp_instances.txt`: MVP test instance list (in experiments/ directory)
