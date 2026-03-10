import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";
import { buildTeacherKnowledgePrompt } from "@/lib/teacher-knowledge";
import { getVideoKnowledge } from "@/lib/video-knowledge-store";
import { DimensionEntry, TimingReference } from "@/lib/reading-types";

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

    const prosePrompt = `${teacherKnowledge}${videoContext}

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

    const jsonPrompt = `你是塔罗六维度分析助手。请对以下抽到的牌，严格输出一个JSON对象，不要输出任何JSON以外的文字，不要用代码块包裹。

牌阵：${spreadType}
问题：${question || "宇宙自由指引"}

抽到的牌：
${cardDescriptions}

输出格式（必须严格遵守，全部中文）：
{
  "dimensions": [
    {
      "cardName": "牌的中文名",
      "reversed": false,
      "numerology": {
        "number": 1,
        "energy": "开创能量",
        "meaning": "数字1代表新开始与独立意志，是所有事物的起点"
      },
      "color": {
        "dominant": ["红色", "白色"],
        "signals": "红色象征行动力与热情；白色代表纯洁与精神清明"
      },
      "astrology": {
        "sign": "双子座",
        "planet": "水星",
        "influence": "水星赋予沟通与思维敏锐的能力"
      },
      "elements": {
        "composition": "风元素主导",
        "analysis": "思维活跃灵动，擅长沟通与变通"
      },
      "symbolism": {
        "symbols": ["无限符号∞", "权杖"],
        "interpretation": "无限符号代表无尽潜力，四件工具代表掌握所有资源"
      },
      "kabbalah": {
        "path": "路径12",
        "planets": "冥王星 ↔ 土星",
        "depth": "将无形力量通过秩序具象化"
      }
    }
  ],
  "timing": {
    "cardName": "最核心位置的牌名",
    "cardNumber": 1,
    "suit": null,
    "weeksEstimate": 1,
    "zodiacMonth": null,
    "summary": "基于魔术师（数字1）→ 约1周内可能出现变化"
  }
}

规则：
- dimensions数组长度必须等于牌的数量（${cards.length}张）
- reversed字段根据实际逆正位填写
- timing使用牌阵中最核心/代表结果的那张牌；数字周算法：牌面数字=周数；若是小牌则suit填写元素（cups/wands/swords/pentacles）
- 大阿卡纳的suit填null；zodiacMonth填null
- kabbalah字段如无明确对应可省略
- cardNumber为null时weeksEstimate也填null`;

    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    // 两个调用并行，不增加等待时间
    const [proseResult, jsonResult] = await Promise.all([
      model.generateContent(prosePrompt),
      model.generateContent(jsonPrompt),
    ]);

    const interpretation = proseResult.response.text();

    let dimensions: DimensionEntry[] = [];
    let timing: TimingReference | null = null;
    try {
      const raw = jsonResult.response.text().trim()
        .replace(/^```json\s*/i, "").replace(/^```\s*/i, "").replace(/```\s*$/, "");
      const parsed = JSON.parse(raw);
      dimensions = parsed.dimensions ?? [];
      timing = parsed.timing ?? null;
    } catch {
      // 静默降级，UI不显示六维度
    }

    return NextResponse.json({ interpretation, dimensions, timing });
  } catch (error) {
    const msg = error instanceof Error ? error.message : String(error);
    console.error("Gemini interpret error:", msg);
    return NextResponse.json({ error: "解读失败：" + msg }, { status: 500 });
  }
}
