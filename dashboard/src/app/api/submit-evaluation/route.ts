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

    return new Promise<Response>((resolve) => {
      const command = `source /data/zhihao/miniconda3/etc/profile.d/conda.sh && conda activate swebench && sb-cli submit "${sbDataset}" test --predictions_path "${predictionsFile}" --run_id "${finalRunId}"`;
      const proc = spawn("bash", ["-c", command], {
        cwd: PROJECT_DIR,
        env: { ...process.env, ...envVars }
      });

      let output = "";
      let error = "";

      proc.stdout.on("data", (data) => {
        output += data.toString();
      });

      proc.stderr.on("data", (data) => {
        error += data.toString();
      });

      proc.on("close", (code) => {
        if (code === 0) {
          resolve(
            NextResponse.json({
              success: true,
              runId: finalRunId,
              dataset: sbDataset,
              output,
            })
          );
        } else {
          const errorMsg = error || output || "Unknown error";
          console.error("sb-cli submit failed:", errorMsg);
          resolve(
            NextResponse.json(
              { success: false, error: errorMsg, code },
              { status: 200 }
            )
          );
        }
      });

      proc.on("error", (err) => {
        console.error("Process error:", err);
        resolve(
          NextResponse.json(
            { success: false, error: err.message },
            { status: 200 }
          )
        );
      });
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
