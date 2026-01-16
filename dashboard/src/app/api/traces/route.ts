import { NextRequest, NextResponse } from "next/server";
import { scanTraceFiles } from "@/lib/scripts";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const scriptId = req.nextUrl.searchParams.get("script");

  if (!scriptId) {
    return NextResponse.json({ error: "Missing script parameter" }, { status: 400 });
  }

  const traces = scanTraceFiles(scriptId);

  // 返回所有 trace 文件（不再限制数量）
  return NextResponse.json({
    total: traces.length,
    traces: traces,
  });
}
