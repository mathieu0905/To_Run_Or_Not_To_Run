import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const PROJECT_DIR = "/home/zhihao/hdd/run_free_run_less_run_full";

function loadEnvFile(): Record<string, string> {
  const envPath = path.join(PROJECT_DIR, ".env");
  const env: Record<string, string> = {};

  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, "utf-8");
    content.split("\n").forEach(line => {
      line = line.trim();
      if (line && !line.startsWith("#")) {
        const [key, ...valueParts] = line.split("=");
        if (key && valueParts.length > 0) {
          env[key.trim()] = valueParts.join("=").trim();
        }
      }
    });
  }

  return env;
}

function mapDataset(dataset: string): string {
  const mapping: Record<string, string> = {
    swebenchlite: "swe-bench_lite",
    swebenchverified: "swe-bench_verified",
  };
  return mapping[dataset] || dataset;
}

export async function POST(req: NextRequest) {
  try {
    const { dataset, agent, mode, runId } = await req.json();

    if (!dataset || !agent || !mode) {
      return NextResponse.json(
        { error: "Missing required parameters" },
        { status: 400 }
      );
    }

    const predictionsFile = path.join(
      PROJECT_DIR,
      "predictions",
      `${dataset}_${agent}_${mode}.json`
    );

    if (!fs.existsSync(predictionsFile)) {
      return NextResponse.json(
        { error: "Predictions file not found. Please generate predictions first." },
        { status: 400 }
      );
    }

    const sbDataset = mapDataset(dataset);
    const finalRunId = runId || `${dataset}_${agent}_${mode}`;

    // 加载环境变量
    const envVars = loadEnvFile();

    // 在后台运行提交任务，立即返回响应
    const logFile = path.join(PROJECT_DIR, "logs", `submit_${finalRunId}_${Date.now()}.log`);

    // 确保 logs 目录存在
    const logsDir = path.join(PROJECT_DIR, "logs");
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }

    const command = `source /data/zhihao/miniconda3/etc/profile.d/conda.sh && conda activate swebench && sb-cli submit "${sbDataset}" test --predictions_path "${predictionsFile}" --run_id "${finalRunId}" > "${logFile}" 2>&1`;

    const proc = spawn("bash", ["-c", command], {
      cwd: PROJECT_DIR,
      env: { ...process.env, ...envVars },
      detached: true,
      stdio: "ignore"
    });

    proc.unref();

    return NextResponse.json({
      success: true,
      runId: finalRunId,
      dataset: sbDataset,
      message: "提交任务已在后台启动",
      logFile,
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
