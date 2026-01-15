import { NextRequest, NextResponse } from "next/server";
import fs from "fs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const path = req.nextUrl.searchParams.get("path");

  if (!path) {
    return NextResponse.json({ error: "Missing path parameter" }, { status: 400 });
  }

  try {
    const content = fs.readFileSync(path, "utf-8");
    return NextResponse.json({ content });
  } catch (error) {
    return NextResponse.json({ error: "Failed to read trace file" }, { status: 500 });
  }
}
