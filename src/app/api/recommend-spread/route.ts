import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

export async function POST(req: NextRequest) {
  try {
    const { situation } = await req.json();

    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const prompt = `你是一位专业塔罗解读师，根据提问者描述的情况推荐最合适的牌阵。

可选牌阵：
- single（单牌）：快速洞察、每日指引、简单问题
- three（三牌）：过去/现在/未来的事件梳理，感情、工作、决策类问题
- relationship（关系牌阵）：两人关系、感情矛盾、合作问题
- career（工作牌阵）：职业选择、升职、项目方向
- celtic（凯尔特十字）：复杂情况、重大决定、需要全面深入分析

提问者描述的情况：「${situation}」

请返回JSON格式：
{
  "spreadId": "推荐的牌阵ID（single/three/relationship/career/celtic之一）",
  "reason": "推荐原因（1-2句，温暖地说明为什么这个牌阵适合他/她）"
}

只返回JSON，不要其他内容。严禁修改或优化提问者的原始问题。`;

    const result = await model.generateContent(prompt);
    const text = result.response.text().trim();
    const cleaned = text.replace(/```json\n?/g, "").replace(/```\n?/g, "").trim();
    const recommendation = JSON.parse(cleaned);

    return NextResponse.json(recommendation);
  } catch (error) {
    console.error("Recommend spread error:", error);
    // 默认推荐
    return NextResponse.json({
      spreadId: "three",
      reason: "三牌展开适合大多数问题，能清晰呈现过去、现在、未来的能量流动。",
    });
  }
}
