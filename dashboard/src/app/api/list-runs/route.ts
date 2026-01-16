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

export async function GET(req: NextRequest): Promise<Response> {
  try {
    const dataset = req.nextUrl.searchParams.get("dataset");

    if (!dataset) {
      return NextResponse.json(
        { error: "Missing dataset parameter" },
        { status: 400 }
      );
    }

    const sbDataset = mapDataset(dataset);
    const envVars = loadEnvFile();

    return new Promise<Response>((resolve) => {
      const command = `source /data/zhihao/miniconda3/etc/profile.d/conda.sh && conda activate swebench && sb-cli list-runs "${sbDataset}" test`;
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
          // 解析输出，提取 run_id 列表（跳过标题行）
          const lines = output.trim().split("\n")
            .filter(line => line.trim() && !line.startsWith("Run IDs"));
          resolve(NextResponse.json({ success: true, runs: lines }));
        } else {
          resolve(
            NextResponse.json(
              { success: false, error: error || output },
              { status: 500 }
            )
          );
        }
      });
    });
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
