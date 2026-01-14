#!/bin/bash
# 配置 Agent 模型的脚本
# 在 Docker 容器启动时运行

set -e

echo "=========================================="
echo "配置 Agent 模型"
echo "=========================================="

# 配置 Claude Code 模型
CLAUDE_MODEL="${CLAUDE_MODEL:-opus}"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

echo "配置 Claude Code 模型: $CLAUDE_MODEL"

# 如果 settings.json 不存在，创建基础配置
if [ ! -f "$CLAUDE_SETTINGS" ]; then
    mkdir -p "$HOME/.claude"
    cat > "$CLAUDE_SETTINGS" <<EOF
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "${ANTHROPIC_API_KEY}",
    "ANTHROPIC_BASE_URL": "${ANTHROPIC_BASE_URL:-https://api.anthropic.com}",
    "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "API_TIMEOUT_MS": "600000"
  },
  "permissions": {
    "allow": [],
    "deny": []
  },
  "language": "English",
  "model": "$CLAUDE_MODEL"
}
EOF
else
    # 更新现有配置中的 model 和 language 字段
    if command -v jq &> /dev/null; then
        # 使用 jq 更新
        tmp=$(mktemp)
        jq ".model = \"$CLAUDE_MODEL\" | .language = \"English\"" "$CLAUDE_SETTINGS" > "$tmp" && mv "$tmp" "$CLAUDE_SETTINGS"
    else
        # 使用 sed 更新（如果没有 jq）
        if grep -q '"model"' "$CLAUDE_SETTINGS"; then
            sed -i "s/\"model\": *\"[^\"]*\"/\"model\": \"$CLAUDE_MODEL\"/" "$CLAUDE_SETTINGS"
        else
            # 如果没有 model 字段，添加它
            sed -i 's/^{/{\n  "model": "'"$CLAUDE_MODEL"'",/' "$CLAUDE_SETTINGS"
        fi
        # 更新或添加 language 字段
        if grep -q '"language"' "$CLAUDE_SETTINGS"; then
            sed -i "s/\"language\": *\"[^\"]*\"/\"language\": \"English\"/" "$CLAUDE_SETTINGS"
        else
            sed -i 's/^{/{\n  "language": "English",/' "$CLAUDE_SETTINGS"
        fi
    fi
fi

echo "✓ Claude Code 配置完成: $CLAUDE_SETTINGS"

# 配置 Codex 模型
CODEX_MODEL="${CODEX_MODEL:-gpt-5.2}"
CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-xhigh}"
CODEX_CONFIG="$HOME/.config/codex/config.toml"

echo "配置 Codex 模型: $CODEX_MODEL (reasoning_effort: $CODEX_REASONING_EFFORT)"

# 如果 config.toml 不存在，创建基础配置
if [ ! -f "$CODEX_CONFIG" ]; then
    mkdir -p "$HOME/.config/codex"
    cat > "$CODEX_CONFIG" <<EOF
model_provider = "packycode"
model = "$CODEX_MODEL"
model_reasoning_effort = "$CODEX_REASONING_EFFORT"
disable_response_storage = true

[model_providers.packycode]
name = "packycode"
base_url = "https://www.packyapi.com/v1"
wire_api = "responses"
requires_openai_auth = true

[projects."/workspace"]
trust_level = "trusted"
EOF
else
    # 更新现有配置
    sed -i "s/^model = .*/model = \"$CODEX_MODEL\"/" "$CODEX_CONFIG"
    sed -i "s/^model_reasoning_effort = .*/model_reasoning_effort = \"$CODEX_REASONING_EFFORT\"/" "$CODEX_CONFIG"
fi

echo "✓ Codex 配置完成: $CODEX_CONFIG"

echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo "Claude Code 模型: $CLAUDE_MODEL"
echo "Codex 模型: $CODEX_MODEL (reasoning_effort: $CODEX_REASONING_EFFORT)"
echo ""
