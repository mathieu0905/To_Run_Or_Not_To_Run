import { NextRequest } from "next/server";
import { spawn } from "child_process";
import { getLatestLogFile, getDetailLogDir } from "@/lib/scripts";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const scriptId = req.nextUrl.searchParams.get("script");
  const type = req.nextUrl.searchParams.get("type") || "main"; // main 或 detail

  if (!scriptId) {
    return new Response("Missing script parameter", { status: 400 });
  }

  let logPath: string | null;

  if (type === "detail") {
    // 详细日志（各模式的日志）
    logPath = getDetailLogDir(scriptId);
    if (!logPath) {
      return new Response("Script not found", { status: 404 });
    }
    logPath = `${logPath}/*.log`;
  } else {
    // 主日志文件
    logPath = getLatestLogFile(scriptId);
    if (!logPath) {
      return new Response("No log file found", { status: 404 });
    }
  }

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      const tail = spawn("bash", ["-c", `tail -F ${logPath} 2>/dev/null || echo "Waiting for logs..."`]);

      tail.stdout.on("data", (data: Buffer) => {
        const lines = data.toString().split("\n").filter(Boolean);
        for (const line of lines) {
          controller.enqueue(encoder.encode(`data: ${line}\n\n`));
        }
      });

      tail.stderr.on("data", (data: Buffer) => {
        controller.enqueue(encoder.encode(`data: [stderr] ${data.toString()}\n\n`));
      });

      tail.on("close", () => {
        controller.close();
      });

      req.signal.addEventListener("abort", () => {
        tail.kill();
      });
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
