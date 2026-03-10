import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

export async function POST(req: NextRequest) {
  try {
    const { pastEvent, card } = await req.json();

    const keywords = (card.reversed ? card.keywordsReversed : card.keywords).join("、");
    const meaning  = card.reversed ? card.meaningReversed : card.meaning;

    const prompt = `你是塔罗验证助手，任务是判断一张牌的能量是否与用户描述的过去事件相符。

用户描述的过去事件：
「${pastEvent}」

抽到的牌：${card.nameZh}（${card.reversed ? "逆位" : "正位"}）
关键词：${keywords}
牌意：${meaning}

请判断这张牌与该事件的能量吻合程度，然后给出简短的验证说明。

输出格式（纯文字，不要使用任何Markdown符号）：
吻合度：[高 / 中 / 低]
[2-3句验证说明，具体说明牌面的哪些能量对应了事件的哪些特征，语气温和客观]

注意：不要过度强行对应，如果确实不太吻合请如实说明，这有助于建立信任。`;

    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    const result = await model.generateContent(prompt);
    const text = result.response.text().trim();

    // 解析吻合度
    const matchLine = text.split("\n")[0] ?? "";
    const level = matchLine.includes("高") ? "high" : matchLine.includes("中") ? "medium" : "low";
    const explanation = text.split("\n").slice(1).join("\n").trim();

    return NextResponse.json({ level, explanation, raw: text });
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
