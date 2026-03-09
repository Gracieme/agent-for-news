import { NextRequest, NextResponse } from "next/server";
import { addVideoKnowledge } from "@/lib/video-knowledge-store";

export async function POST(req: NextRequest) {
  try {
    const { content, topic, fileName } = await req.json();

    if (!content || typeof content !== "string") {
      return NextResponse.json({ error: "缺少 content" }, { status: 400 });
    }

    addVideoKnowledge({
      fileName: fileName || "未知",
      topic: topic || "塔罗课程",
      content: content.trim(),
      date: new Date().toLocaleString("zh-CN"),
    });

    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error("Save knowledge error:", error);
    return NextResponse.json({ error: "保存失败" }, { status: 500 });
  }
}
