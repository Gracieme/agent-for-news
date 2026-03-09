#!/usr/bin/env node
/**
 * 批量导入视频到解读系统
 * 用法: node scripts/batch-ingest-videos.mjs <视频文件夹路径>
 * 示例: node scripts/batch-ingest-videos.mjs ./videos
 */

import { readdirSync, readFileSync } from "fs";
import { join, extname } from "path";

const VIDEO_EXTS = [".mp4", ".mov", ".avi", ".webm", ".mkv"];

const extractFromVideo = async (filePath, topic = "") => {
  const { GoogleGenerativeAI } = await import("@google/generative-ai");
  const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
  const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

  const bytes = readFileSync(filePath);
  const base64 = bytes.toString("base64");
  const ext = extname(filePath).toLowerCase();
  const mimeType =
    ext === ".mp4"
      ? "video/mp4"
      : ext === ".mov"
        ? "video/quicktime"
        : ext === ".webm"
          ? "video/webm"
          : "video/mp4";

  const prompt = `请仔细观看这段塔罗课程视频，提取并整理其中的塔罗解读知识。
这些知识将用于增强AI对塔罗牌的解读能力，请重点关注：如何解读牌意、如何结合位置/元素/数字分析、老师的解读风格和技巧。

${topic ? `重点关注的主题：${topic}` : ""}

请按以下结构整理输出（使用纯文字标题，不要 emoji）：

## 课程主题
（一句话概括核心主题）

## 涉及的牌/牌阵
（列出具体牌名、牌阵及其解读要点）

## 核心知识点
（分点列出最重要的塔罗知识、技巧或概念）

## 解读技巧
（老师分享的实用解读方法和技巧）

## 金句摘录
（重要观点或金句，用引号标注）

## 学习笔记
（其他值得记录、可用于解读的内容）

请用中文输出，内容专业、可直接用于指导解读。`;

  const result = await model.generateContent([
    prompt,
    { inlineData: { mimeType, data: base64 } },
  ]);
  return result.response.text();
};

const main = async () => {
  const folder = process.argv[2] || "./videos";
  if (!process.env.GEMINI_API_KEY) {
    console.error("请设置环境变量 GEMINI_API_KEY");
    process.exit(1);
  }

  let entries = [];
  try {
    const raw = readFileSync(
      join(process.cwd(), "data", "video-knowledge.json"),
      "utf-8"
    );
    entries = JSON.parse(raw);
  } catch {
    const { mkdirSync, writeFileSync } = await import("fs");
    mkdirSync(join(process.cwd(), "data"), { recursive: true });
  }

  const files = readdirSync(folder)
    .filter((f) => VIDEO_EXTS.includes(extname(f).toLowerCase()))
    .map((f) => join(folder, f));

  if (files.length === 0) {
    console.log(`未在 ${folder} 中找到视频文件（支持 ${VIDEO_EXTS.join(", ")}）`);
    process.exit(0);
  }

  console.log(`找到 ${files.length} 个视频，开始提取...`);

  for (const filePath of files) {
    const name = filePath.split(/[/\\]/).pop();
    try {
      console.log(`处理: ${name} ...`);
      const content = await extractFromVideo(filePath);
      entries.unshift({
        fileName: name,
        topic: "塔罗课程",
        content,
        date: new Date().toLocaleString("zh-CN"),
      });
      console.log(`  ✓ 完成`);
    } catch (e) {
      console.error(`  ✗ 失败:`, e.message);
    }
  }

  const { writeFileSync } = await import("fs");
  writeFileSync(
    join(process.cwd(), "data", "video-knowledge.json"),
    JSON.stringify(entries, null, 2),
    "utf-8"
  );
  console.log(`\n已保存到 data/video-knowledge.json，共 ${entries.length} 条`);
};

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
