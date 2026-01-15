import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const PROJECT_DIR = "/home/zhihao/hdd/run_free_run_less_run_full";
const REPORTS_DIR = path.join(PROJECT_DIR, "sb-cli-reports");

export async function GET(req: NextRequest): Promise<Response> {
  try {
    const action = req.nextUrl.searchParams.get("action");
    const filename = req.nextUrl.searchParams.get("filename");

    if (action === "list") {
      // 列出所有报告文件
      if (!fs.existsSync(REPORTS_DIR)) {
        return NextResponse.json({ reports: [] });
      }

      const files = fs.readdirSync(REPORTS_DIR);
      const reports = files
        .filter(f => f.endsWith(".json"))
        .map(f => {
          const stats = fs.statSync(path.join(REPORTS_DIR, f));
          return {
            filename: f,
            size: stats.size,
            mtime: stats.mtimeMs,
          };
        })
        .sort((a, b) => b.mtime - a.mtime);

      return NextResponse.json({ reports });
    } else if (action === "read" && filename) {
      // 读取指定报告文件
      const filepath = path.join(REPORTS_DIR, filename);
      if (!fs.existsSync(filepath)) {
        return NextResponse.json(
          { error: "Report file not found" },
          { status: 404 }
        );
      }

      const content = fs.readFileSync(filepath, "utf-8");
      const report = JSON.parse(content);
      return NextResponse.json({ report });
    } else {
      return NextResponse.json(
        { error: "Invalid action or missing filename" },
        { status: 400 }
      );
    }
  } catch (error: any) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
