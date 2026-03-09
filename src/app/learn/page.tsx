"use client";

import Link from "next/link";
import { useState } from "react";

const sections = [
  {
    emoji: "🔮",
    title: "塔罗牌是什么？",
    content: `塔罗牌是一套有78张牌的卡牌系统，起源于15世纪的欧洲。

它不是用来"算命"的——塔罗牌是一面镜子，反映你内心深处的真实状态和潜意识的声音。

当你凝视一张牌，它呈现的图像会触动你内心某个角落，帮助你看见那些平时被忽略的感受、恐惧或渴望。

**塔罗能做什么？**
• 帮你理清思路，看清事情的来龙去脉
• 揭示你意识不到的内在模式和能量
• 在困惑时提供新的视角和可能性
• 让你更深地了解自己

**塔罗不能做什么？**
• 预测固定的命运（未来可以改变）
• 代替你做决定
• 保证某个结果一定发生`,
  },
  {
    emoji: "📚",
    title: "78张牌怎么理解？",
    content: `塔罗牌分为两个部分：

**🌟 大阿卡纳（22张）**
描述人生的重大主题和灵魂课题。从"愚者"的出发，经历各种原型力量，到"世界"的圆满——这是一段灵魂成长的旅程。

抽到大阿卡纳，通常意味着这件事有重要的灵魂意义，需要认真对待。

**🃏 小阿卡纳（56张）**
描述日常生活的细节。分为四个花色：

🔥 **权杖**（火元素）— 激情、创造力、工作、行动
💧 **圣杯**（水元素）— 情感、爱情、直觉、内心世界
🌬️ **宝剑**（风元素）— 思维、冲突、真相、沟通
🌍 **金币**（土元素）— 金钱、物质、身体、实际事务

每个花色14张：Ace到10的数字牌，加上侍者、骑士、皇后、国王四张宫廷牌。`,
  },
  {
    emoji: "🌙",
    title: "什么是逆位？",
    content: `当牌倒置出现时，称为"逆位"。很多初学者害怕逆位，觉得一定是坏事——这是误解。

**逆位的常见含义：**
• 这张牌的能量被阻碍、压抑或内化
• 需要更深地向内看，而非向外行动
• 某件事还没准备好，时机未到
• 需要特别注意的地方

**举例：**
正位太阳 ☀️ = 喜悦、成功、光明
逆位太阳 ☀️ = 短暂的阴云，但阳光终会穿透；或者过于依赖外部认可

记住：没有任何一张牌是纯粹的"凶牌"。即使是死神、塔、恶魔，也有它积极的转化意义。`,
  },
  {
    emoji: "🃏",
    title: "什么情况选什么牌阵？",
    content: `**🎯 单牌** — 最简单
适合：每天早晨问今日指引、临时有个简单的疑问、冥想时需要一个主题
问法示例：「今天的能量是什么？」「这件事我该注意什么？」

---

**🌙 三牌展开** — 最常用
适合：了解事情的发展脉络、面临选择时、感情/工作/日常问题
经典用法：过去・现在・未来 / 情况・建议・结果
问法示例：「我和他的感情走向如何？」「换工作这个决定怎么样？」

---

**💕 关系牌阵** — 感情专用
适合：两段关系的分析、感情困惑、合作问题
呈现：双方各自的能量状态，以及关系的核心议题
问法示例：「我们之间到底是什么问题？」

---

**💼 工作牌阵** — 事业专用
适合：职业方向、项目决策、升职机会
呈现：现状、阻碍、建议、潜力、结果
问法示例：「我现在的工作方向对吗？」

---

**✨ 凯尔特十字** — 最全面
适合：复杂的情况、重大的人生决定、需要深度分析时
建议：有一定塔罗基础再尝试，或让解读者帮你理清
问法示例：「关于这段关系/这次转变，我需要了解什么？」

---

💡 **不知道选哪个？** 直接描述你的情况，我们的AI会帮你推荐最合适的牌阵！`,
  },
  {
    emoji: "💫",
    title: "怎么问出好问题？",
    content: `塔罗解读的质量，很大程度取决于问题的质量。

**❌ 不好的问问方式：**
「他爱我吗？」（是非题，答案太局限）
「我会发财吗？」（把主动权交给命运）
「XX会发生吗？」（期待固定答案）

**✅ 好的问问方式：**
「我和他的关系能量现在是什么状态？」
「关于我的财务状况，我需要了解什么？」
「什么在阻碍我，我如何突破？」
「我在感情/工作上需要注意什么？」

**关键原则：**
把主动权放在自己身上，问"我需要了解什么"而不是"结果会怎样"。

记住：塔罗描述的是当下的能量趋势，你永远有力量去选择和改变。`,
  },
];

export default function LearnPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <div
      className="min-h-screen"
      style={{ background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 50%, #F5F2EC 100%)" }}
    >
      <nav className="flex justify-between items-center px-8 py-5">
        <Link href="/" className="text-xl font-bold tracking-tight" style={{ color: "var(--text-warm)" }}>
          <span style={{ color: "var(--sage-deep)" }}>☽</span> 格雷西的塔罗驿站
        </Link>
        <Link
          href="/reading"
          className="px-5 py-2 rounded-full text-white font-medium"
          style={{ background: "var(--sage-deep)" }}
        >
          开始占卜
        </Link>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8">
        <div className="text-center mb-12">
          <div className="text-6xl mb-4 float-animation">📖</div>
          <h1 className="text-4xl font-bold mb-3" style={{ color: "var(--text-warm)" }}>塔罗入门指南</h1>
          <p style={{ color: "var(--text-muted)" }}>从零开始，了解塔罗牌的世界</p>
        </div>

        <div className="space-y-4 mb-12">
          {sections.map((section, i) => (
            <div key={i} className="glass rounded-2xl overflow-hidden">
              <button
                className="w-full text-left px-6 py-5 flex items-center gap-4 transition-all hover:bg-white/20"
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
              >
                <span className="text-3xl">{section.emoji}</span>
                <span className="text-lg font-bold flex-1" style={{ color: "var(--text-warm)" }}>{section.title}</span>
                <span className="text-xl" style={{ color: "var(--sage-deep)" }}>
                  {openIndex === i ? "▲" : "▼"}
                </span>
              </button>
              {openIndex === i && (
                <div className="px-6 pb-6">
                  <div
                    className="text-sm leading-8 whitespace-pre-wrap"
                    style={{ color: "var(--text-warm)" }}
                    dangerouslySetInnerHTML={{
                      __html: section.content
                        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                        .replace(/---/g, '<hr style="border-color:var(--border-soft); margin: 16px 0"/>')
                    }}
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="glass rounded-3xl p-10 text-center">
          <div className="text-5xl mb-4">🔮</div>
          <h2 className="text-2xl font-bold mb-3" style={{ color: "var(--text-warm)" }}>
            准备好了吗？
          </h2>
          <p className="mb-6" style={{ color: "var(--text-muted)" }}>
            描述你的情况，AI会帮你选择最合适的牌阵，然后开始你的第一次塔罗之旅
          </p>
          <Link
            href="/reading"
            className="inline-block px-10 py-4 rounded-full text-white text-lg font-bold transition-all hover:scale-105"
            style={{
              background: "var(--sage-deep)",
              boxShadow: "0 6px 24px rgba(139,154,125,0.25)"
            }}
          >
            🌙 开始第一次占卜
          </Link>
        </div>
      </main>
    </div>
  );
}
