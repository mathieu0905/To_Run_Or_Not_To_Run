import fs from "fs";
import path from "path";

export const PROJECT_DIR =
  process.env.RUNLESS_PROJECT_DIR || path.resolve(process.cwd(), "..");

export function loadEnvFile(): Record<string, string> {
  const envPath = path.join(PROJECT_DIR, ".env");
  const env: Record<string, string> = {};

  if (fs.existsSync(envPath)) {
    const content = fs.readFileSync(envPath, "utf-8");
    content.split("\n").forEach((line) => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith("#")) {
        const [key, ...valueParts] = trimmed.split("=");
        if (key && valueParts.length > 0) {
          env[key.trim()] = valueParts.join("=").trim();
        }
      }
    });
  }

  return env;
}
