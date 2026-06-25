import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import { PROJECT_DIR } from "@/lib/project";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface EvaluationRequest {
  dataset: "swebenchlite" | "swebenchverified";
  agent: string;
  mode: string;
  runId: string;
  maxWorkers?: number;
  timeout?: number;
}

export async function POST(req: NextRequest) {
  const body: EvaluationRequest = await req.json();
  const { dataset, agent, mode, runId, maxWorkers = 4, timeout = 1800 } = body;

  // 检查 predictions.jsonl 是否存在
  const outputDir = path.join(PROJECT_DIR, "output", dataset, agent, mode);
  const predictionsPath = path.join(outputDir, "predictions.jsonl");

  if (!fs.existsSync(predictionsPath)) {
    return NextResponse.json(
      { error: "predictions.jsonl not found. Please generate patches first." },
      { status: 404 }
    );
  }

  // 启动评测进程
  const datasetName = dataset === "swebenchverified"
    ? "SWE-bench/SWE-bench_Verified"
    : "SWE-bench/SWE-bench_Lite";

  const logFile = path.join(PROJECT_DIR, "logs", `eval_${runId}_${Date.now()}.log`);
  fs.mkdirSync(path.dirname(logFile), { recursive: true });

  const proc = spawn(
    "python",
    [
      path.join(PROJECT_DIR, "experiments", "evaluate_patches.py"),
      "--dataset", dataset,
      "--agent", agent,
      "--mode", mode,
      "--run-id", runId,
      "--max-workers", String(maxWorkers),
      "--timeout", String(timeout),
    ],
    {
      cwd: PROJECT_DIR,
      detached: true,
      stdio: ["ignore", "pipe", "pipe"],
    }
  );

  // 将输出写入日志文件
  const logStream = fs.createWriteStream(logFile);
  proc.stdout.pipe(logStream);
  proc.stderr.pipe(logStream);

  proc.unref();

  return NextResponse.json({
    success: true,
    message: "Evaluation started",
    logFile,
    pid: proc.pid,
  });
}

// 获取评测状态
export async function GET(req: NextRequest) {
  const dataset = req.nextUrl.searchParams.get("dataset");
  const agent = req.nextUrl.searchParams.get("agent");
  const mode = req.nextUrl.searchParams.get("mode");

  if (!dataset || !agent || !mode) {
    return NextResponse.json({ error: "Missing parameters" }, { status: 400 });
  }

  const predictionsPath = path.join(
    PROJECT_DIR,
    "output",
    dataset,
    agent,
    mode,
    "predictions.jsonl"
  );

  const hasPredictions = fs.existsSync(predictionsPath);

  // 检查是否有评测结果
  const evalLogsDir = path.join(PROJECT_DIR, "logs", "run_evaluation");
  let evalResults: string[] = [];

  if (fs.existsSync(evalLogsDir)) {
    const runs = fs.readdirSync(evalLogsDir);
    evalResults = runs.filter((run) => {
      const runPath = path.join(evalLogsDir, run);
      return fs.statSync(runPath).isDirectory();
    });
  }

  return NextResponse.json({
    hasPredictions,
    predictionsPath: hasPredictions ? predictionsPath : null,
    evalResults,
  });
}
