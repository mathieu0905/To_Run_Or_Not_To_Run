import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { PROJECT_DIR } from "@/lib/project";

// 从 shell 脚本中提取配置
function extractConfigFromScript(scriptPath: string): Record<string, string> {
  const config: Record<string, string> = {};

  try {
    const content = fs.readFileSync(scriptPath, "utf-8");

    // 提取配置区域的变量
    const patterns = [
      /NUM_INSTANCES=(\d+)/,
      /WORKERS=(\d+)/,
      /TIMEOUT=(\d+)/,
      /DATASET="([^"]+)"/,
      /CLAUDE_MODEL="\$\{CLAUDE_MODEL:-([^}]+)\}"/,
      /CODEX_MODEL="\$\{CODEX_MODEL:-([^}]+)\}"/,
      /ANTHROPIC_BASE_URL="\$\{ANTHROPIC_BASE_URL:-([^}]+)\}"/,
      /CODEX_REASONING_EFFORT="\$\{CODEX_REASONING_EFFORT:-([^}]+)\}"/,
    ];

    for (const pattern of patterns) {
      const match = content.match(pattern);
      if (match) {
        const key = pattern.source.split("=")[0].replace(/[\\^]/g, "");
        config[key] = match[1];
      }
    }

    // 提取 CONFIGS 数组
    const configsMatch = content.match(/CONFIGS=\(([\s\S]*?)\)/);
    if (configsMatch) {
      const configLines = configsMatch[1]
        .split("\n")
        .map(line => line.trim())
        .filter(line => line.startsWith('"') && !line.startsWith("#"));

      config.CONFIGS = JSON.stringify(
        configLines.map(line => {
          const match = line.match(/"([^"]+)"/);
          return match ? match[1] : "";
        }).filter(Boolean)
      );
    }
  } catch (error) {
    console.error(`Failed to read script ${scriptPath}:`, error);
  }

  return config;
}

export async function GET() {
  try {
    // 读取 claude 和 codex 脚本的配置
    const claudeConfig = extractConfigFromScript(path.join(PROJECT_DIR, "scripts", "run_claude.sh"));
    const codexConfig = extractConfigFromScript(path.join(PROJECT_DIR, "scripts", "run_codex.sh"));

    // 合并配置，优先使用 claude 的通用配置
    const config = {
      numInstances: parseInt(claudeConfig.NUM_INSTANCES || "100"),
      workersClaudeCode: parseInt(claudeConfig.WORKERS || "10"),
      workersCodex: parseInt(codexConfig.WORKERS || "30"),
      timeout: parseInt(claudeConfig.TIMEOUT || "1200"),
      dataset: claudeConfig.DATASET || "princeton-nlp/SWE-bench_Lite",
      claudeModel: claudeConfig.CLAUDE_MODEL || "sonnet",
      codexModel: codexConfig.CODEX_MODEL || "gpt-5.2",
      codexReasoningEffort: codexConfig.CODEX_REASONING_EFFORT || "xhigh",
      anthropicBaseUrl: claudeConfig.ANTHROPIC_BASE_URL || "https://api.anthropic.com",
      modes: claudeConfig.CONFIGS ? JSON.parse(claudeConfig.CONFIGS) : [],
    };

    return NextResponse.json(config);
  } catch (error) {
    console.error("Failed to load config:", error);
    return NextResponse.json(
      { error: "Failed to load configuration" },
      { status: 500 }
    );
  }
}
