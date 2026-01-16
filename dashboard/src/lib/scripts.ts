import { spawn, ChildProcess, execSync } from "child_process";
import fs from "fs";
import path from "path";

export interface ScriptConfig {
  numInstances: number;
  workers: number;
  timeout: number;
  claudeModel: string;
  codexModel: string;
  anthropicBaseUrl: string;
  anthropicAuthToken: string;
  modes: string[];
}

export interface ScriptInfo {
  id: string;
  name: string;
  scriptPath: string;
  status: "idle" | "running" | "completed" | "failed";
  pid?: number;
  logFile?: string;
}

export interface TraceInfo {
  path: string;
  instance: string;
  mode: string;
  agent: string;
  size: number;
  mtime: number;
}

const PROJECT_DIR = "/home/zhihao/hdd/run_free_run_less_run_full";

export const SCRIPTS: ScriptInfo[] = [
  { id: "claude_lite", name: "Claude + Lite", scriptPath: `${PROJECT_DIR}/run_claude.sh`, status: "idle" },
  { id: "claude_verified", name: "Claude + Verified", scriptPath: `${PROJECT_DIR}/run_claude_verified.sh`, status: "idle" },
  { id: "glm_lite", name: "GLM + Lite", scriptPath: `${PROJECT_DIR}/run_glm.sh`, status: "idle" },
  { id: "glm_verified", name: "GLM + Verified", scriptPath: `${PROJECT_DIR}/run_glm_verified.sh`, status: "idle" },
  { id: "codex_lite", name: "Codex + Lite", scriptPath: `${PROJECT_DIR}/run_codex.sh`, status: "idle" },
  { id: "codex_verified", name: "Codex + Verified", scriptPath: `${PROJECT_DIR}/run_codex_verified.sh`, status: "idle" },
];

const runningProcesses = new Map<string, ChildProcess>();
const scriptLogFiles = new Map<string, string>();

// 检测系统中运行的 batch_runner 进程
export function detectRunningScripts(): Record<string, boolean> {
  const result: Record<string, boolean> = {};
  try {
    const ps = execSync("ps aux | grep batch_runner | grep -v grep", { encoding: "utf-8" });
    result.claude_lite = ps.includes("SWE-bench_Lite") && ps.includes("claude_code") && !ps.includes("glm");
    result.claude_verified = ps.includes("SWE-bench_Verified") && ps.includes("claude_code") && !ps.includes("glm");
    result.glm_lite = ps.includes("SWE-bench_Lite") && ps.includes("glm");
    result.glm_verified = ps.includes("SWE-bench_Verified") && ps.includes("glm");
    result.codex_lite = ps.includes("SWE-bench_Lite") && ps.includes("codex");
    result.codex_verified = ps.includes("SWE-bench_Verified") && ps.includes("codex");
  } catch {
    // 没有运行的进程
  }
  return result;
}

export function getScripts(): ScriptInfo[] {
  const running = detectRunningScripts();
  return SCRIPTS.map(s => ({
    ...s,
    status: running[s.id] ? "running" : (runningProcesses.has(s.id) ? "running" : "idle"),
    logFile: scriptLogFiles.get(s.id),
  }));
}

export function startScript(id: string, config: ScriptConfig): { success: boolean; logFile?: string; error?: string } {
  const script = SCRIPTS.find(s => s.id === id);
  if (!script) return { success: false, error: "Script not found" };

  const running = detectRunningScripts();
  if (running[id] || runningProcesses.has(id)) {
    return { success: false, error: "Script already running" };
  }

  // 根据脚本 ID 自动选择配置
  let finalConfig = { ...config };
  if (id.includes("glm")) {
    // GLM 脚本使用 GLM 配置
    finalConfig.claudeModel = "glm-4.7";
    finalConfig.anthropicBaseUrl = "https://open.bigmodel.cn/api/anthropic";
    finalConfig.anthropicAuthToken = "22d3e2814dd24bf1943ced46dc817067.KyGdWHcuJo0EXs0o";
  } else if (id.includes("claude")) {
    // Claude 脚本使用 Claude 配置
    finalConfig.claudeModel = config.claudeModel || "sonnet";
    finalConfig.anthropicBaseUrl = config.anthropicBaseUrl || "https://api.anthropic.com";
    finalConfig.anthropicAuthToken = config.anthropicAuthToken || "";
  }
  // Codex 脚本保持原配置

  const env = {
    ...process.env,
    NUM_INSTANCES: String(finalConfig.numInstances),
    WORKERS: String(finalConfig.workers),
    TIMEOUT: String(finalConfig.timeout),
    CLAUDE_MODEL: finalConfig.claudeModel,
    CODEX_MODEL: finalConfig.codexModel,
    ANTHROPIC_BASE_URL: finalConfig.anthropicBaseUrl,
    ANTHROPIC_AUTH_TOKEN: finalConfig.anthropicAuthToken,
  };

  const proc = spawn("bash", [script.scriptPath, "-f"], {
    env,
    cwd: PROJECT_DIR,
    detached: true,
    stdio: "ignore",
  });

  proc.unref();
  runningProcesses.set(id, proc);

  // 获取最新的日志文件
  const logPattern = getLogPattern(id);
  scriptLogFiles.set(id, logPattern || "");

  proc.on("exit", () => {
    runningProcesses.delete(id);
  });

  return { success: true, logFile: logPattern || undefined };
}

export function stopScript(id: string): boolean {
  // 尝试停止我们启动的进程
  const proc = runningProcesses.get(id);
  if (proc) {
    proc.kill("SIGTERM");
    runningProcesses.delete(id);
  }

  // 也尝试停止系统中运行的相关进程
  try {
    const script = SCRIPTS.find(s => s.id === id);
    if (script) {
      execSync(`pkill -f "${script.scriptPath}"`, { encoding: "utf-8" });
    }
  } catch {
    // 可能没有进程
  }

  return true;
}

export function stopAllScripts(): void {
  for (const [id] of runningProcesses) {
    stopScript(id);
  }
  // 停止所有 batch_runner 进程
  try {
    execSync("pkill -f batch_runner", { encoding: "utf-8" });
  } catch {
    // 可能没有进程
  }
}

// 返回日志文件匹配模式
export function getLogPattern(id: string): string | null {
  const patterns: Record<string, { dir: string; pattern: string }> = {
    claude_lite: { dir: "logs", pattern: "run_claude_2*.log" },
    claude_verified: { dir: "logs", pattern: "run_claude_verified_*.log" },
    glm_lite: { dir: "logs/claude_code_glm", pattern: "*.log" },
    glm_verified: { dir: "logs/claude_code_glm", pattern: "*.log" },
    codex_lite: { dir: "logs", pattern: "run_codex_2*.log" },
    codex_verified: { dir: "logs", pattern: "run_codex_verified_*.log" },
  };
  const config = patterns[id];
  return config ? `${PROJECT_DIR}/${config.dir}/${config.pattern}` : null;
}

// 获取最新的日志文件
export function getLatestLogFile(id: string): string | null {
  const pattern = getLogPattern(id);
  if (!pattern) return null;

  try {
    const dir = path.dirname(pattern);
    const prefix = path.basename(pattern).replace("*.log", "").replace("2*.log", "");
    const files = fs.readdirSync(dir)
      .filter(f => f.startsWith(prefix) && f.endsWith(".log"))
      .map(f => ({ name: f, mtime: fs.statSync(path.join(dir, f)).mtime.getTime() }))
      .sort((a, b) => b.mtime - a.mtime);

    return files.length > 0 ? path.join(dir, files[0].name) : null;
  } catch {
    return null;
  }
}

// 返回详细日志目录（各模式的日志）
export function getDetailLogDir(id: string): string | null {
  const agent = id.includes("glm") ? "glm" : id.includes("claude") ? "claude_code" : "codex";
  return `${PROJECT_DIR}/logs/${agent}`;
}

// 扫描 trace.jsonl 文件
export function scanTraceFiles(scriptId: string): TraceInfo[] {
  const traces: TraceInfo[] = [];
  const dataset = scriptId.includes("verified") ? "swebenchverified" : "swebenchlite";
  const agent = scriptId.includes("glm") ? "claude_code_glm" : scriptId.includes("claude") ? "claude_code" : "codex";
  const baseDir = `${PROJECT_DIR}/output/${dataset}/${agent}`;

  try {
    const modes = fs.readdirSync(baseDir);
    for (const mode of modes) {
      const modeDir = path.join(baseDir, mode);
      if (!fs.statSync(modeDir).isDirectory()) continue;

      const instances = fs.readdirSync(modeDir);
      for (const instance of instances) {
        const traceFile = path.join(modeDir, instance, "trace.jsonl");
        if (fs.existsSync(traceFile)) {
          const stat = fs.statSync(traceFile);
          traces.push({
            path: traceFile,
            instance,
            mode,
            agent,
            size: stat.size,
            mtime: stat.mtime.getTime(),
          });
        }
      }
    }
  } catch {
    // 目录可能不存在
  }

  return traces.sort((a, b) => b.mtime - a.mtime);
}
