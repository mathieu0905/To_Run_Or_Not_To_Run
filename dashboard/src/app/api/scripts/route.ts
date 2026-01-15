import { NextRequest, NextResponse } from "next/server";
import { getScripts, startScript, stopScript, stopAllScripts, ScriptConfig } from "@/lib/scripts";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(getScripts());
}

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { action, scripts, mode, config } = body;

  if (action === "start") {
    const results: Record<string, { success: boolean; error?: string }> = {};

    if (mode === "parallel") {
      for (const id of scripts) {
        results[id] = startScript(id, config);
      }
    } else {
      // Sequential: start scripts one by one (handled by frontend polling)
      const id = scripts[0];
      if (id) results[id] = startScript(id, config);
    }

    return NextResponse.json({ results });
  }

  if (action === "stop") {
    if (body.scriptId) {
      stopScript(body.scriptId);
    } else {
      stopAllScripts();
    }
    return NextResponse.json({ success: true });
  }

  return NextResponse.json({ error: "Invalid action" }, { status: 400 });
}
