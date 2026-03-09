import { readFileSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join } from "path";

export interface VideoKnowledgeEntry {
  fileName: string;
  topic: string;
  content: string;
  date: string;
}

const STORE_PATH = join(process.cwd(), "data", "video-knowledge.json");

function ensureDir() {
  const dir = join(process.cwd(), "data");
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }
}

export function getVideoKnowledge(): string {
  try {
    ensureDir();
    if (!existsSync(STORE_PATH)) {
      return "";
    }
    const raw = readFileSync(STORE_PATH, "utf-8");
    const entries: VideoKnowledgeEntry[] = JSON.parse(raw);
    return entries.map((e) => e.content).join("\n\n---\n\n");
  } catch {
    return "";
  }
}

export function addVideoKnowledge(entry: VideoKnowledgeEntry): void {
  try {
    ensureDir();
    let entries: VideoKnowledgeEntry[] = [];
    if (existsSync(STORE_PATH)) {
      const raw = readFileSync(STORE_PATH, "utf-8");
      entries = JSON.parse(raw);
    }
    entries.unshift(entry);
    writeFileSync(STORE_PATH, JSON.stringify(entries, null, 2), "utf-8");
  } catch {
    // Vercel 等 serverless 环境无持久化文件系统，忽略写入
  }
}
