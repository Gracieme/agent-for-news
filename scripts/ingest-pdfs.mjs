#!/usr/bin/env node
/**
 * 将塔罗相关 PDF 提取为解读知识并写入 data/video-knowledge.json
 * 用法: node scripts/ingest-pdfs.mjs <PDF路径1> [PDF路径2] ...
 * 示例: node scripts/ingest-pdfs.mjs "./塔罗通灵课学习手册.pdf" "./Book T.pdf"
 */

import { readFileSync, readdirSync, writeFileSync, existsSync, mkdirSync } from "fs";
import { join, extname } from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = join(__dirname, "..");
const STORE_PATH = join(PROJECT_ROOT, "data", "video-knowledge.json");

const CHUNK_SIZE = 28000; // 字符数，留足 token 空间给 Gemini
const OVERLAP = 800;

function ensureDir() {
  const dir = join(PROJECT_ROOT, "data");
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

function loadStore() {
  ensureDir();
  if (!existsSync(STORE_PATH)) return [];
  return JSON.parse(readFileSync(STORE_PATH, "utf-8"));
}

function saveStore(entries) {
  ensureDir();
  writeFileSync(STORE_PATH, JSON.stringify(entries, null, 2), "utf-8");
}

function chunkText(text) {
  const chunks = [];
  let start = 0;
  while (start < text.length) {
    let end = Math.min(start + CHUNK_SIZE, text.length);
    if (end < text.length) {
      const lastPeriod = text.lastIndexOf("。", end);
      const lastNewline = text.lastIndexOf("\n", end);
      end = Math.max(lastPeriod, lastNewline, start) + 1 || end;
    }
    chunks.push(text.slice(start, end).trim());
    start = end - (end - start > OVERLAP ? OVERLAP : 0);
  }
  return chunks.filter(Boolean);
}

async function extractKnowledgeFromText(textChunk, fileName, partLabel) {
  const { GoogleGenerativeAI } = await import("@google/generative-ai");
  const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
  const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

  const prompt = `你是一位塔罗教学专家。下面这段文字来自塔罗相关教材/手册的「${partLabel}」部分。请提取其中对「塔罗解读」有直接帮助的知识，用于增强 AI 解读师的能力。

要求：
- 只保留与牌意、牌阵、解读技巧、元素/数字含义、韦特/神秘学体系相关的内容
- 用清晰的小标题和条目整理，便于后续解读时引用
- 中文输出，不要编造原文没有的内容
- 若本段与塔罗解读无关，可回复「本段无塔罗解读相关内容」

原文：
${textChunk.slice(0, 26000)}`;

  const result = await model.generateContent(prompt);
  return result.response.text();
}

async function extractTextFromPdf(filePath) {
  const { PDFParse } = await import("pdf-parse");
  const buffer = readFileSync(filePath);
  const parser = new PDFParse({ data: buffer });
  try {
    const result = await parser.getText();
    return result?.text?.trim() || "";
  } finally {
    await parser.destroy();
  }
}

async function processPdf(filePath) {
  const name = filePath.split(/[/\\]/).pop();
  console.log(`处理: ${name} ...`);

  let text;
  try {
    text = await extractTextFromPdf(filePath);
  } catch (e) {
    console.error(`  ✗ 读取失败: ${e.message}`);
    return null;
  }

  if (!text || text.length < 100) {
    console.error(`  ✗ 无有效文本`);
    return null;
  }

  const chunks = chunkText(text);
  const parts = [];
  for (let i = 0; i < chunks.length; i++) {
    process.stdout.write(`  提取第 ${i + 1}/${chunks.length} 段 ... `);
    try {
      const part = await extractKnowledgeFromText(
        chunks[i],
        name,
        `第 ${i + 1}/${chunks.length} 部分`
      );
      if (part && !/无塔罗解读相关/.test(part)) parts.push(part);
      console.log("✓");
    } catch (e) {
      console.log(`✗ ${e.message}`);
    }
  }

  if (parts.length === 0) {
    console.error(`  ✗ 未提取到塔罗知识`);
    return null;
  }

  return {
    fileName: name,
    topic: "塔罗教材/手册",
    content: parts.join("\n\n---\n\n"),
    date: new Date().toLocaleString("zh-CN"),
  };
}

async function main() {
  if (!process.env.GEMINI_API_KEY) {
    console.error("请设置环境变量 GEMINI_API_KEY（或使用 --env-file=.env.local）");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  const files = [];
  for (const p of args) {
    const resolved = p.startsWith("/") ? p : join(process.cwd(), p);
    if (!existsSync(resolved)) {
      console.error("文件不存在:", resolved);
      continue;
    }
    if (extname(resolved).toLowerCase() !== ".pdf") {
      console.error("跳过非 PDF:", resolved);
      continue;
    }
    files.push(resolved);
  }

  if (files.length === 0) {
    console.log("用法: node scripts/ingest-pdfs.mjs <PDF路径1> [PDF路径2] ...");
    process.exit(0);
  }

  let entries = loadStore();
  for (const filePath of files) {
    const entry = await processPdf(filePath);
    if (entry) {
      entries.unshift(entry);
      console.log(`  ✓ 已加入知识库`);
    }
  }

  saveStore(entries);
  console.log(`\n已保存到 data/video-knowledge.json，共 ${entries.length} 条`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
