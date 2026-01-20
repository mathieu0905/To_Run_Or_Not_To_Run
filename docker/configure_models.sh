#!/bin/bash
# Script to configure Agent models
# Run when Docker container starts

set -e

echo "=========================================="
echo "Configuring Agent Models"
echo "=========================================="

# Configure Claude Code model
CLAUDE_MODEL="${CLAUDE_MODEL:-opus}"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"

echo "Configuring Claude Code model: $CLAUDE_MODEL"

# If settings.json does not exist, create basic configuration
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
    # Update existing configuration using Python
    python3 << PYEOF
import json

with open("$CLAUDE_SETTINGS", "r") as f:
    config = json.load(f)

config["model"] = "$CLAUDE_MODEL"
config["language"] = "English"

if "env" not in config:
    config["env"] = {}

config["env"]["ANTHROPIC_BASE_URL"] = "${ANTHROPIC_BASE_URL:-https://api.anthropic.com}"
config["env"]["ANTHROPIC_API_KEY"] = "${ANTHROPIC_API_KEY}"
config["env"]["ANTHROPIC_AUTH_TOKEN"] = "${ANTHROPIC_API_KEY}"

with open("$CLAUDE_SETTINGS", "w") as f:
    json.dump(config, f, indent=2)
PYEOF
fi

echo "✓ Claude Code configuration completed: $CLAUDE_SETTINGS"

# Configure Codex model
CODEX_MODEL="${CODEX_MODEL:-gpt-5.2}"
CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-xhigh}"
CODEX_CONFIG="$HOME/.config/codex/config.toml"

echo "Configuring Codex model: $CODEX_MODEL (reasoning_effort: $CODEX_REASONING_EFFORT)"

# If config.toml does not exist, create basic configuration
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
    # Update existing configuration
    sed -i "s/^model = .*/model = \"$CODEX_MODEL\"/" "$CODEX_CONFIG"
    sed -i "s/^model_reasoning_effort = .*/model_reasoning_effort = \"$CODEX_REASONING_EFFORT\"/" "$CODEX_CONFIG"
fi

echo "✓ Codex configuration completed: $CODEX_CONFIG"

echo "=========================================="
echo "Configuration completed!"
echo "=========================================="
echo "Claude Code model: $CLAUDE_MODEL"
echo "Codex model: $CODEX_MODEL (reasoning_effort: $CODEX_REASONING_EFFORT)"
echo ""
