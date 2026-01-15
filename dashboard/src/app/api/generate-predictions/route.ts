import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const PROJECT_DIR = "/home/zhihao/hdd/run_free_run_less_run_full";

export async function POST(req: NextRequest): Promise<Response> {
  try {
    const { dataset, agent, mode } = await req.json();

    if (!dataset || !agent || !mode) {
      return NextResponse.json(
        { error: "Missing required parameters" },
        { status: 400 }
      );
    }

    return new Promise<Response>((resolve) => {
      const proc = spawn(
        "python3",
        [
          "generate_predictions.py",
          "--dataset",
          dataset,
          "--agent",
          agent,
          "--mode",
          mode,
        ],
        { cwd: PROJECT_DIR }
      );

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
          const predictionsFile = path.join(
            PROJECT_DIR,
            "predictions",
            `${dataset}_${agent}_${mode}.json`
          );
          resolve(
            NextResponse.json({
              success: true,
              predictionsFile,
              output,
            })
          );
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
