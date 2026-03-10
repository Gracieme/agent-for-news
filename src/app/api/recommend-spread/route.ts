import { GoogleGenerativeAI } from "@google/generative-ai";
import { NextRequest, NextResponse } from "next/server";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY!);

// 二选一/决策类问题的高置信度模式 → 直接返回 decision，避免 LLM 误判
const DECISION_PATTERNS = [
  // 明确"选X还是选Y"
  /选[aA]还是选[bB]/i,
  /选择\s*[aA]\s*和\s*选择\s*[bB]/i,
  /选择\s*[aA]\s*还是\s*选择\s*[bB]/i,
  /选\s*[aA]\s*和\s*选\s*[bB]/i,
  /选[甲乙一二]\s*还是\s*选[甲乙一二]/,
  /选择\s*.+?\s*和\s*选择\s*.+?/,
  /选\s*.+?\s*还是\s*.+?/,
  // "去X还是Y" / "是X还是Y" 结构
  /去.+?还是.+?(读|工作|留|学|去|选|发展)/,
  /去.+?还是.+?读博/,
  /是.+?还是.+?(读博|工作|留学|发展|继续|换)/,
  // 通用 "A还是B" — 两侧各至少2个汉字，中间无句号
  /[\u4e00-\u9fa5]{2,}还是[\u4e00-\u9fa5]{2,}/,
  // 要不要 / 做不做 等
  /要不要\s*(做|去|留|换|买|接受|继续|接)/,
  /去还是不去/,
  /留还是走/,
  /做还是不做/,
  /换还是不换/,
  /接受还是拒绝/,
  /两个选项|二选一|选哪个|纠结选/,
];

function isDecisionQuestion(s: string): boolean {
  const text = (s || "").trim();
  if (!text) return false;
  return DECISION_PATTERNS.some((p) => p.test(s));
}

export async function POST(req: NextRequest) {
  try {
    const { situation } = await req.json();

    // 规则预检：二选一问题直接返回 decision，保证匹配准确
    if (isDecisionQuestion(situation)) {
      return NextResponse.json({
        spreadId: "decision",
        reason:
          "决策天平专为二选一问题设计，能分别呈现两个选项的能量、阻力和结果，帮你更清晰地权衡。",
        refinedQuestion: "",
      });
    }

    const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

    const prompt = `你是一位专业塔罗解读师，根据提问者描述的情况，从以下 12 个牌阵中选出最匹配的一个。

【全部 12 个牌阵及精准适用场景】

1. single · 单牌占卜
   适用：今日能量、今天/最近状态、快速洞察、简单是非、冥想后的单一指引

2. yesno · 是非指引
   适用：明确的是非题——"可不可以""会不会""有没有可能""行不行""能否成功"
   注意：不是二选一，而是对一件事的可行性/结果的判断

3. three · 三牌展开
   适用：事件时间线（过去-现在-未来）、感情进展梳理、情况-建议-结果、需要故事感叙述
   注意：不是二选一！若问「选择A和选择B」「选A还是选B」→ 必须用 decision，不要用 three

4. newMoon · 新月许愿
   适用：设定新目标、新阶段开始、想做某件事可不可行、愿望设定与可行性

5. mindBodySoul · 身心灵三角
   适用：身体状态、情绪困扰、感觉失衡、焦虑失眠、身心脱节、需要身心灵三个层面检视

6. relationship · 关系牌阵
   适用：两人之间的感情、矛盾、吸引力、合作关系、家庭关系——必须有明确的"两个人"

7. selfGrowth · 自我成长
   适用：个人卡点、内在阻力、想突破某个模式、自我限制、成长瓶颈

8. career · 工作牌阵
   适用：职业选择、升职、项目方向、跳槽、工作阻碍、事业规划——明确与工作/事业相关

9. celtic · 凯尔特十字
   适用：复杂纠缠的多层面问题、看不清全貌的大问题、需要从核心-挑战-根源-可能-结果层层剖析
   注意：不是简单的二选一！若问"选A还是选B"则用 decision，不要用 celtic

10. moonCycle · 月亮周期
    适用：情绪周期、能量高低起伏、长期状态梳理、需要六张牌深度能量扫描

11. decision · 决策天平
    适用：在两个选项之间纠结——选A还是选B、选这个还是那个、去还是不去、留还是走、要不要做、做还是不做
    牌阵专门为选项A和选项B各设位置做对比，是二选一问题的最佳牌阵
    关键词：选...还是...、A还是B、要不要、去还是、留还是

12. chakra · 七脉轮
    适用：全身七个能量中心扫描、灵性探索、深度身心能量排查、大范围能量状态检视

【匹配优先级】二选一/决策类（选A还是选B、选择A和选择B、要不要、去还是不去等）→ 必须用 decision，禁止用 three 或 celtic；是非题 → yesno；两人关系 → relationship；工作 → career；复杂但非二选一 → celtic
【禁止】三牌展开（three）和凯尔特十字（celtic）都不能用于二选一/决策类问题。推荐 reason 时不要写「选择A和选择B」与 three/celtic 的搭配。

提问者描述的情况：「${situation}」

请返回JSON格式：
{
  "spreadId": "从上方12个牌阵中选一个ID",
  "reason": "推荐原因（1-2句，温暖说明为什么这个牌阵最适合）",
  "refinedQuestion": "如果原始问题已清晰，返回空字符串\"\"；否则给出优化后的问题（保持核心意图，不改变方向）"
}

只返回JSON，不要其他内容。`;

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
      refinedQuestion: "",
    });
  }
}
