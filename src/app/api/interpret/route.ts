import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";
import { buildTeacherKnowledgePrompt } from "@/lib/teacher-knowledge";
import { getVideoKnowledge } from "@/lib/video-knowledge-store";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

export async function POST(req: NextRequest) {
  try {
    const { question, cards, spreadType, knowledgeFromVideos } = await req.json();

    const cardDescriptions = cards
      .map(
        (c: {
          nameZh: string; name: string; position: string; reversed: boolean;
          meaning: string; meaningReversed: string;
          keywords: string[]; keywordsReversed: string[];
          imageEmoji: string;
        }, i: number) =>
          `${i + 1}. 【${c.position}】${c.imageEmoji} ${c.nameZh}（${c.name}）${c.reversed ? " — 逆位" : " — 正位"}
   关键词：${(c.reversed ? c.keywordsReversed : c.keywords).join("、")}
   牌意：${c.reversed ? c.meaningReversed : c.meaning}`
      )
      .join("\n\n");

    const teacherKnowledge = buildTeacherKnowledgePrompt();
    const serverKnowledge = getVideoKnowledge();
    const clientKnowledge = typeof knowledgeFromVideos === "string" && knowledgeFromVideos.trim()
      ? knowledgeFromVideos.trim()
      : "";
    const combinedVideoKnowledge = [serverKnowledge, clientKnowledge]
      .filter(Boolean)
      .join("\n\n---\n\n");
    const videoContext = combinedVideoKnowledge
      ? `\n\n【以下来自Gracie老师课程视频提取的解读知识，请严格融入你的解读逻辑和风格】\n\n${combinedVideoKnowledge}\n`
      : "";

    const prompt = `${teacherKnowledge}${videoContext}

---

现在请为以下问题进行塔罗解读：

提问者的问题：「${question || "请为我解读当下的能量与宇宙指引"}」

牌阵：${spreadType}

抽到的牌：
${cardDescriptions}

请按以下结构给出完整解读。输出纯文字，绝对不能使用任何 Markdown 格式（禁止 **、*、#、_ 等所有符号）：

整体能量
（2-3句，描述这组牌的整体氛围）

逐牌解读
（结合位置含义、元素、数字逐牌分析）

综合洞见
（将所有牌融合，给出核心洞见）

给你的指引
（温暖有力量的具体建议）

【强制规则】如果提问者的问题含有「可不可以」「能不能」「会不会」「有没有可能」「行不行」「成不成」「有没有机会」等，解读结构必须改为：

可能性：XX%
（直接给出一个明确的百分比数字，禁止用「较高」「偏低」等模糊词代替）

支持的理由
（牌面中支持这个结果的具体依据）

需要注意的风险
（牌面提示的阻碍或需要改变的地方）

给你的建议
（基于以上分析的具体可执行建议）

百分比必须出现在第一行，必须是具体数字如「68%」，绝对禁止出现「可能可以」「要看情况」「难以判断」等回避性表述。

语气专业而温暖，像一位懂你的智慧朋友。全程使用中文，严禁出现任何英文单词或英文章节标题，300-500字。`;

    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });
    const result = await model.generateContent(prompt);
    const interpretation = result.response.text();

    return NextResponse.json({ interpretation });
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    console.error("Gemini interpret error:", msg);
    return NextResponse.json({ error: "解读失败：" + msg }, { status: 500 });
  }
}
