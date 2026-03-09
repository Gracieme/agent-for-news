"use client";

import { useState } from "react";
import { useUser, UserButton } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { TarotCard, SPREADS } from "@/lib/tarot-data";
import CardDeck from "@/components/CardDeck";
import InterpretationContent from "@/components/InterpretationContent";

type Step = "situation" | "spread" | "draw" | "result";

interface DrawnCard extends TarotCard {
  position: string;
  reversed: boolean;
  flipped: boolean;
}

interface SpreadOption {
  id: string;
  name: string;
  description: string;
  count: number;
  emoji: string;
  positions: string[];
}

const ALL_SPREADS: SpreadOption[] = [
  ...SPREADS,
  {
    id: "relationship",
    name: "关系牌阵",
    description: "两人关系 · 感情分析",
    count: 4,
    emoji: "💕",
    positions: ["你的能量", "对方能量", "关系核心", "建议"]
  },
  {
    id: "career",
    name: "工作牌阵",
    description: "事业方向 · 职业决策",
    count: 5,
    emoji: "💼",
    positions: ["现状", "阻碍", "建议", "潜力", "结果"]
  },
];

export default function ReadingPage() {
  const { isSignedIn, user } = useUser();
  const router = useRouter();

  const [step, setStep] = useState<Step>("situation");
  const [situation, setSituation] = useState("");
  const [recommendedSpread, setRecommendedSpread] = useState<SpreadOption | null>(null);
  const [recommendReason, setRecommendReason] = useState("");
  const [refinedQuestion, setRefinedQuestion] = useState("");
  const [recommending, setRecommending] = useState(false);
  const [selectedSpread, setSelectedSpread] = useState<SpreadOption>(ALL_SPREADS[1]);
  const [drawnCards, setDrawnCards] = useState<DrawnCard[]>([]);
  const [interpretation, setInterpretation] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isSignedIn) { router.push("/sign-in"); return null; }

  const handleGetRecommendation = async () => {
    setRecommending(true);
    if (!situation.trim()) {
      setStep("spread");
      setRecommending(false);
      return;
    }
    try {
      const res = await fetch("/api/recommend-spread", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ situation }),
      });
      const data = await res.json();
      const spread = ALL_SPREADS.find(s => s.id === data.spreadId) || ALL_SPREADS[1];
      setRecommendedSpread(spread);
      setRecommendReason(data.reason || "");
      setRefinedQuestion(data.question || situation);
      setStep("spread");
    } catch {
      setStep("spread");
    }
    setRecommending(false);
  };

  const handleSelectSpread = (spread: SpreadOption) => {
    setSelectedSpread(spread);
    setStep("draw");
  };

  const handleCardsComplete = (cards: DrawnCard[]) => {
    setDrawnCards(cards);
    handleInterpret(cards);
  };

  const getKnowledgeFromVideos = (): string => {
    if (typeof window === "undefined") return "";
    try {
      const stored = localStorage.getItem("tarot_knowledge");
      if (!stored) return "";
      const entries: { content: string }[] = JSON.parse(stored);
      return entries.slice(0, 10).map((e) => e.content).join("\n\n---\n\n");
    } catch {
      return "";
    }
  };

  const handleInterpret = async (cards: DrawnCard[]) => {
    setLoading(true);
    setStep("result");
    try {
      const knowledgeFromVideos = getKnowledgeFromVideos();
      const res = await fetch("/api/interpret", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: refinedQuestion || situation,
          cards,
          spreadType: selectedSpread.name,
          knowledgeFromVideos,
        }),
      });
      const data = await res.json();
      setInterpretation(data.interpretation || data.error);

      if (user && data.interpretation) {
        const record = {
          id: Date.now().toString(),
          user_id: user.id,
          spread_type: selectedSpread.name,
          question: refinedQuestion || situation,
          cards: cards.map(c => ({ id: c.id, nameZh: c.nameZh, reversed: c.reversed, position: c.position })),
          interpretation: data.interpretation,
          created_at: new Date().toISOString(),
        };
        // 先存 localStorage（备用，无需数据库）
        try {
          const prev = JSON.parse(localStorage.getItem("tarot_readings") || "[]");
          localStorage.setItem("tarot_readings", JSON.stringify([record, ...prev].slice(0, 50)));
        } catch {}
        // 再尝试存数据库（如有配置）
        fetch("/api/save-reading", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(record),
        }).catch(() => {});
      }
    } catch {
      setInterpretation("解读失败，请稍后重试");
    }
    setLoading(false);
  };

  const reset = () => {
    setStep("situation");
    setSituation("");
    setRecommendedSpread(null);
    setRecommendReason("");
    setRefinedQuestion("");
    setDrawnCards([]);
    setInterpretation("");
  };

  return (
    <div className="min-h-screen" style={{ background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 50%, #F5F2EC 100%)" }}>
      <nav className="flex justify-between items-center px-8 py-5">
        <Link href="/" className="text-xl font-bold tracking-tight" style={{ color: "var(--text-warm)" }}><span style={{ color: "var(--sage-deep)" }}>☽</span> 格雷西的塔罗驿站</Link>
        <div className="flex items-center gap-4">
          <Link href="/learn" className="text-sm" style={{ color: "var(--sage-deep)" }}>塔罗入门</Link>
          <Link href="/history" className="text-sm" style={{ color: "var(--sage-deep)" }}>历史记录</Link>
          <UserButton />
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-4 py-8">

        {/* 步骤一：描述情况 */}
        {step === "situation" && (
          <div className="fade-in text-center">
            <div className="text-6xl mb-4 float-animation">🌙</div>
            <h2 className="text-3xl font-bold mb-2" style={{ color: "var(--text-warm)" }}>告诉我，你在思考什么？</h2>
            <p className="mb-8" style={{ color: "var(--text-muted)" }}>
              描述你的情况，AI帮你选最合适的牌阵<br />
              <span className="text-sm">也可以直接跳过，让宇宙给你最需要的指引</span>
            </p>
            <textarea
              className="glass w-full rounded-2xl p-5 text-base resize-none outline-none mb-6 text-left"
              style={{ color: "var(--text-warm)", minHeight: "130px" }}
              placeholder="例如：最近和伴侣关系有些紧张，不知道是否该主动沟通...&#10;&#10;或者：对现在的工作感到迷茫，想知道要不要换方向...&#10;&#10;或者：最近状态很差，想看看整体能量..."
              value={situation}
              onChange={e => setSituation(e.target.value)}
            />
            <div className="flex gap-4 justify-center flex-wrap">
              <button
                onClick={handleGetRecommendation}
                disabled={recommending}
                className="px-10 py-4 rounded-full text-white font-bold transition-all hover:scale-105 disabled:opacity-60"
                style={{ background: "var(--sage-deep)", boxShadow: "0 6px 24px rgba(139,154,125,0.25)" }}
              >
                {recommending ? "🔮 分析中..." : "✨ AI帮我推荐牌阵"}
              </button>
              <button
                onClick={() => setStep("spread")}
                className="px-8 py-4 rounded-full font-medium"
                style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)", background: "rgba(255,255,255,0.9)" }}
              >
                我自己选牌阵
              </button>
            </div>
            <p className="mt-6 text-sm">
              <Link href="/learn" style={{ color: "var(--sage-deep)" }}>🌱 第一次来？先了解塔罗牌是什么 →</Link>
            </p>
          </div>
        )}

        {/* 步骤二：选牌阵 */}
        {step === "spread" && (
          <div className="fade-in">
            {recommendedSpread && (
              <div className="glass rounded-2xl p-6 mb-6 text-center">
                <p className="text-sm mb-2" style={{ color: "var(--sage-deep)" }}>✨ 根据你的情况，推荐</p>
                <div className="flex items-center justify-center gap-3 mb-3">
                  <span className="text-4xl">{recommendedSpread.emoji}</span>
                  <div className="text-left">
                    <div className="text-xl font-bold" style={{ color: "var(--text-warm)" }}>{recommendedSpread.name}</div>
                    <div className="text-sm" style={{ color: "var(--text-muted)" }}>{recommendReason}</div>
                  </div>
                </div>
                {refinedQuestion && refinedQuestion !== situation && (
                  <div className="mt-3 px-4 py-2 rounded-xl text-sm" style={{ background: "rgba(155,168,141,0.15)", color: "var(--sage-deep)" }}>
                    优化后的问题：「{refinedQuestion}」
                  </div>
                )}
                <button
                  onClick={() => handleSelectSpread(recommendedSpread)}
                  className="mt-4 px-10 py-3 rounded-full text-white font-bold transition-all hover:scale-105"
                  style={{ background: "var(--sage-deep)" }}
                >
                  🌟 就用这个牌阵，开始抽牌
                </button>
              </div>
            )}

            <h3 className="text-center text-lg font-bold mb-4" style={{ color: "var(--text-warm)" }}>
              {recommendedSpread ? "或选择其他牌阵" : "选择牌阵"}
            </h3>
            <div className="grid gap-3">
              {ALL_SPREADS.map(spread => (
                <button
                  key={spread.id}
                  onClick={() => handleSelectSpread(spread)}
                  className="glass rounded-2xl p-5 text-left transition-all hover:scale-101 hover:shadow-md flex items-center gap-4"
                >
                  <span className="text-3xl">{spread.emoji}</span>
                  <div className="flex-1">
                    <div className="font-bold" style={{ color: "var(--text-warm)" }}>{spread.name}</div>
                    <div className="text-sm" style={{ color: "var(--text-muted)" }}>{spread.description} · {spread.count}张牌</div>
                    <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{spread.positions.join(" · ")}</div>
                  </div>
                  <span style={{ color: "var(--sage-deep)" }}>→</span>
                </button>
              ))}
            </div>
            <div className="text-center mt-4">
              <button onClick={() => setStep("situation")} className="text-sm" style={{ color: "var(--text-muted)" }}>
                ← 返回
              </button>
            </div>
          </div>
        )}

        {/* 步骤三：手动抽牌 */}
        {step === "draw" && (
          <div className="fade-in">
            <div className="text-center mb-6">
              <div className="text-4xl mb-2">🃏</div>
              <h2 className="text-2xl font-bold" style={{ color: "var(--text-warm)" }}>
                {selectedSpread.name}
              </h2>
              {(refinedQuestion || situation) && (
                <div className="mt-3 inline-block glass rounded-xl px-5 py-2 text-sm" style={{ color: "var(--sage-deep)" }}>
                  「{refinedQuestion || situation}」
                </div>
              )}
            </div>
            <CardDeck
              count={selectedSpread.count}
              positions={selectedSpread.positions}
              onComplete={handleCardsComplete}
            />
          </div>
        )}

        {/* 步骤四：解读结果 - 专业温暖呈现 */}
        {step === "result" && (
          <div className="fade-in">
            <div className="text-center mb-10">
              <h2 className="text-2xl md:text-3xl font-bold tracking-tight" style={{ color: "var(--text-warm)" }}>
                为你解读
              </h2>
              <p className="mt-3 text-[15px] max-w-lg mx-auto" style={{ color: "var(--text-muted)" }}>
                {selectedSpread.name} · {refinedQuestion || situation || "宇宙自由解读"}
              </p>
            </div>

            {/* 牌面 - 简洁清晰 */}
            <div className="mb-10">
              <div className="grid gap-4 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
                {drawnCards.map((card, i) => (
                  <div key={i} className="glass rounded-xl p-4 text-center min-w-0">
                    <div className="text-xs font-medium tracking-wide mb-1" style={{ color: "var(--sage-deep)" }}>
                      {card.position}
                    </div>
                    <div className="text-2xl mb-1">{card.imageEmoji}</div>
                    <div className="text-sm font-semibold" style={{ color: "var(--text-warm)" }}>
                      {card.nameZh}
                    </div>
                    {card.reversed && (
                      <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>逆位</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* 解读内容 */}
            <div className="glass rounded-2xl p-8 md:p-10 mb-10">
              {loading ? (
                <div className="py-16 text-center">
                  <div className="inline-block w-10 h-10 rounded-full border-2 border-t-transparent animate-spin mb-4" style={{ borderColor: "var(--sage)" }} />
                  <p className="text-base font-medium" style={{ color: "var(--text-warm)" }}>Gracie 的智慧正在为你汇聚</p>
                  <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>请稍候片刻</p>
                </div>
              ) : (
                <InterpretationContent text={interpretation} />
              )}
            </div>

            {!loading && (
              <div className="flex gap-3 justify-center flex-wrap">
                <button
                  onClick={reset}
                  className="px-8 py-3 rounded-full text-white font-medium transition-all hover:opacity-90"
                  style={{ background: "var(--sage-deep)" }}
                >
                  再次占卜
                </button>
                <Link
                  href="/history"
                  className="px-8 py-3 rounded-full font-medium transition-all hover:opacity-90"
                  style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)" }}
                >
                  查看历史
                </Link>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
