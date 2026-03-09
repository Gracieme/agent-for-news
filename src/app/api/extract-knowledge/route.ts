import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";
import { addVideoKnowledge } from "@/lib/video-knowledge-store";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const file = formData.get("video") as File | null;
    const topic = (formData.get("topic") as string) || "";

    if (!file) {
      return NextResponse.json({ error: "请上传视频文件" }, { status: 400 });
    }

    // 将文件转为 base64
    const bytes = await file.arrayBuffer();
    const base64 = Buffer.from(bytes).toString("base64");
    const mimeType = file.type || "video/mp4";

    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

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
（老师分享的实用解读方法和技巧，包括如何逐牌分析、如何综合洞见、如何给出温暖有力的建议）

## 金句摘录
（重要观点或金句，用引号标注）

## 学习笔记
（其他值得记录、可用于解读的内容）

请用中文输出，内容专业、可直接用于指导解读。`;

    const result = await model.generateContent([
      prompt,
      {
        inlineData: {
          mimeType,
          data: base64,
        },
      },
    ]);

    const knowledge = result.response.text();

    // 自动保存到解读系统（视频库）
    try {
      addVideoKnowledge({
        fileName: file.name,
        topic: topic || "塔罗课程",
        content: knowledge,
        date: new Date().toLocaleString("zh-CN"),
      });
    } catch (e) {
      console.warn("Failed to save to server knowledge:", e);
    }

    return NextResponse.json({ knowledge, fileName: file.name });
  } catch (error) {
    console.error("Video extraction error:", error);
    return NextResponse.json(
      { error: "视频处理失败，请确认文件格式正确（支持 mp4、mov、avi）" },
      { status: 500 }
    );
  }
}

export const config = {
  api: {
    bodyParser: false,
  },
};
