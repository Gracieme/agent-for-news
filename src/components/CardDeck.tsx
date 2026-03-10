"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { ALL_CARDS, TarotCard } from "@/lib/tarot-data";
import SpreadLayout from "@/components/SpreadLayout";

/* Gracie 风格牌背 SVG：植物学月亮图案，神秘清新优雅 */
function CardBackSVG({ width, height, hover = false }: { width: number; height: number; hover?: boolean }) {
  const id = `cbg-${width}`;
  return (
    <svg viewBox="0 0 56 84" width={width} height={height} xmlns="http://www.w3.org/2000/svg" style={{ display: "block" }}>
      <defs>
        <linearGradient id={id} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor={hover ? "#F9F7F3" : "#F5F2EC"} />
          <stop offset="50%" stopColor={hover ? "#F2EEE8" : "#EDE9E2"} />
          <stop offset="100%" stopColor={hover ? "#EAE6DE" : "#E5E0D8"} />
        </linearGradient>
      </defs>

      {/* 背景 */}
      <rect width="56" height="84" rx="5" fill={`url(#${id})`} />

      {/* 外边框 */}
      <rect x="1.5" y="1.5" width="53" height="81" rx="4.5" fill="none"
        stroke="#9BA88D" strokeWidth="0.7" opacity={hover ? "0.7" : "0.5"} />
      {/* 内边框 */}
      <rect x="3.5" y="3.5" width="49" height="77" rx="3.5" fill="none"
        stroke="#9BA88D" strokeWidth="0.35" opacity="0.35" />

      {/* 四角装饰 ✦ */}
      <text x="7" y="11" fontSize="5" fill="#B8A99A" opacity="0.8" textAnchor="middle">✦</text>
      <text x="49" y="11" fontSize="5" fill="#B8A99A" opacity="0.8" textAnchor="middle">✦</text>
      <text x="7" y="79" fontSize="5" fill="#B8A99A" opacity="0.8" textAnchor="middle">✦</text>
      <text x="49" y="79" fontSize="5" fill="#B8A99A" opacity="0.8" textAnchor="middle">✦</text>

      {/* 顶部小花 */}
      <text x="28" y="21" fontSize="7" fill="#C4A99B" opacity="0.65" textAnchor="middle">✿</text>
      {/* 横线装饰 */}
      <line x1="9" y1="24" x2="22" y2="24" stroke="#9BA88D" strokeWidth="0.4" opacity="0.4" />
      <line x1="34" y1="24" x2="47" y2="24" stroke="#9BA88D" strokeWidth="0.4" opacity="0.4" />

      {/* 中心月亮 */}
      <text x="28" y="52" fontSize="22" fill="#8B9A7D" opacity={hover ? "0.75" : "0.62"} textAnchor="middle">☽</text>
      {/* 月亮两侧小星 */}
      <text x="13" y="47" fontSize="4" fill="#A89BB5" opacity="0.6" textAnchor="middle">✦</text>
      <text x="43" y="47" fontSize="4" fill="#A89BB5" opacity="0.6" textAnchor="middle">✦</text>
      {/* 叶片左 */}
      <path d="M16 52 Q19 49 19 52 Q19 55 16 52Z" fill="#9BA88D" opacity="0.4" />
      {/* 叶片右 */}
      <path d="M40 52 Q37 49 37 52 Q37 55 40 52Z" fill="#9BA88D" opacity="0.4" />

      {/* 横线装饰下 */}
      <line x1="9" y1="60" x2="22" y2="60" stroke="#9BA88D" strokeWidth="0.4" opacity="0.4" />
      <line x1="34" y1="60" x2="47" y2="60" stroke="#9BA88D" strokeWidth="0.4" opacity="0.4" />
      {/* 底部小花 */}
      <text x="28" y="69" fontSize="7" fill="#C4A99B" opacity="0.65" textAnchor="middle">✿</text>

      {/* 顶底中心小点 */}
      <circle cx="28" cy="12" r="0.8" fill="#9BA88D" opacity="0.45" />
      <circle cx="28" cy="73" r="0.8" fill="#9BA88D" opacity="0.45" />
    </svg>
  );
}

interface DrawnCard extends TarotCard {
  position: string;
  reversed: boolean;
  flipped: boolean;
}

interface CardDeckProps {
  spreadId: string;
  count: number;
  positions: string[];
  onComplete: (cards: DrawnCard[]) => void;
}

const shuffleDeck = () => [...ALL_CARDS].sort(() => Math.random() - 0.5);

const DECK_VISUAL_COUNT = 8; // 洗牌时展示的牌数量

export default function CardDeck({ spreadId, count, positions, onComplete }: CardDeckProps) {
  const [shuffled, setShuffled] = useState(shuffleDeck);
  const [drawn, setDrawn] = useState<number[]>([]);
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const [flipped, setFlipped] = useState<Set<number>>(new Set());
  const [phase, setPhase] = useState<"shuffle" | "draw" | "flip">("shuffle");
  const [shuffleCount, setShuffleCount] = useState(0);
  const [isShuffling, setIsShuffling] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const scrollLeft = useRef(0);
  // 每张牌的逆位预先固定（50%概率），避免每次渲染重新随机
  const reversedMap = useRef<boolean[]>([]);

  const totalCards = shuffled.length; // 22

  // drag-to-scroll
  const onMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true;
    startX.current = e.pageX - (scrollRef.current?.offsetLeft ?? 0);
    scrollLeft.current = scrollRef.current?.scrollLeft ?? 0;
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current || !scrollRef.current) return;
    e.preventDefault();
    const x = e.pageX - scrollRef.current.offsetLeft;
    scrollRef.current.scrollLeft = scrollLeft.current - (x - startX.current);
  };
  const onMouseUp = () => { isDragging.current = false; };

  const handleShuffle = () => {
    setIsShuffling(true);
    setTimeout(() => {
      setShuffled(shuffleDeck());
      setShuffleCount((c) => c + 1);
      setIsShuffling(false);
    }, 800);
  };

  const handlePickCard = (idx: number) => {
    if (isDragging.current) return;
    if (drawn.includes(idx)) return;
    if (drawn.length >= count) return;

    // 抽牌时立刻固定该张牌的逆位（50%概率），后续渲染不会变
    const drawnIndex = drawn.length;
    reversedMap.current[drawnIndex] = Math.random() < 0.5;

    const newDrawn = [...drawn, idx];
    setDrawn(newDrawn);

    if (newDrawn.length === count) {
      setTimeout(() => setPhase("flip"), 400);
    }
  };

  const handleFlip = (drawnIndex: number) => {
    setFlipped(prev => {
      const next = new Set(prev);
      next.add(drawnIndex);
      return next;
    });
  };

  useEffect(() => {
    if (phase === "flip" && flipped.size === count) {
      setTimeout(() => {
        const result: DrawnCard[] = drawn.map((cardIdx, i) => ({
          ...shuffled[cardIdx],
          position: positions[i],
          reversed: reversedMap.current[i] ?? false,
          flipped: true,
        }));
        onComplete(result);
      }, 600);
    }
  }, [flipped, count, phase]);

  return (
    <div className="fade-in">
      {/* 洗牌阶段 */}
      {phase === "shuffle" && (
        <>
          <div className="text-center mb-6">
            <p className="text-lg font-medium" style={{ color: "var(--text-warm)" }}>
              先洗牌，让能量充分混合
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              洗多少次都可以，感觉准备好了再开始选牌
            </p>
          </div>

          {/* 牌堆视觉：洗牌时有动效，模拟牌被搅动的感觉 */}
          <div className="flex justify-center mb-8" style={{ minHeight: 150, width: 240, margin: "0 auto" }}>
            <motion.div
              className="relative"
              style={{ width: 80, height: 110 }}
              initial={false}
              animate={isShuffling ? "shuffle" : "idle"}
              variants={{
                idle: { scale: 1 },
                shuffle: {
                  scale: [1, 1.05, 1],
                  transition: { duration: 0.8, ease: "easeInOut" },
                },
              }}
            >
              {Array.from({ length: DECK_VISUAL_COUNT }).map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute"
                  style={{
                    width: 56,
                    height: 84,
                    left: i * 3,
                    top: i * 2,
                    borderRadius: 8,
                    boxShadow: "0 4px 14px rgba(139,154,125,0.2)",
                  }}
                  initial={false}
                  animate={
                    isShuffling
                      ? {
                          x: [0, (i - 3.5) * 20, 0],
                          y: [0, -8 + (i % 3 - 1) * 12, 0],
                          rotate: [0, (i % 2 ? 1 : -1) * 6, 0],
                        }
                      : {}
                  }
                  transition={{ duration: 0.8, ease: "easeInOut", delay: i * 0.03 }}
                >
                  <CardBackSVG width={56} height={84} />
                </motion.div>
              ))}
            </motion.div>
          </div>

          {shuffleCount > 0 && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center text-sm mb-4"
              style={{ color: "var(--sage-deep)" }}
            >
              已洗 {shuffleCount} 次
            </motion.p>
          )}

          <div className="flex flex-col items-center gap-6">
            <motion.button
              onClick={handleShuffle}
              disabled={isShuffling}
              className="px-10 py-4 rounded-full text-white font-medium transition-all"
              style={{ background: "var(--sage-deep)" }}
              whileHover={!isShuffling ? { scale: 1.03 } : {}}
              whileTap={!isShuffling ? { scale: 0.98 } : {}}
            >
              {isShuffling ? "洗牌中…" : "洗牌"}
            </motion.button>
            <button
              onClick={() => setPhase("draw")}
              className="px-8 py-3 rounded-full font-medium transition-all hover:opacity-90"
              style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)", background: "rgba(255,255,255,0.9)" }}
            >
              开始选牌
            </button>
          </div>
        </>
      )}

      {/* 抽牌阶段 */}
      {phase === "draw" && (
        <>
          {/* 牌阵位置说明 */}
          <div className="glass rounded-2xl p-5 mb-6">
            <div className="text-sm font-medium mb-3" style={{ color: "var(--text-warm)" }}>牌阵位置：</div>
            <div className="flex flex-wrap gap-3">
              {positions.map((pos, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg"
                  style={{
                    background: i < drawn.length ? "var(--sage-deep)" : "rgba(155,168,141,0.15)",
                    color: i < drawn.length ? "#fff" : "var(--text-warm)",
                  }}
                >
                  <span className="text-xs opacity-80">{i + 1}</span>
                  <span className="text-sm font-medium">{pos}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="text-center mb-4">
            <p className="text-lg font-medium" style={{ color: "var(--text-warm)" }}>
              {drawn.length < count
                ? `请选择第 ${drawn.length + 1} 张牌：${positions[drawn.length]}`
                : "已选好，正在展开..."}
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              左右滑动牌堆，点击选牌
            </p>
          </div>

          {/* 进度指示：每个位置 + 已选牌 */}
          <div className="flex gap-3 justify-center flex-wrap mb-6">
            {Array.from({ length: count }).map((_, i) => (
              <div
                key={i}
                className="flex flex-col items-center gap-1 min-w-[72px] rounded-xl px-2 py-2 transition-all border-2"
                style={{
                  borderColor: i < drawn.length ? "var(--sage-deep)" : "var(--border-soft)",
                  background: i < drawn.length ? "var(--sage-deep)" : "rgba(255,255,255,0.6)",
                }}
              >
                <span
                  className="text-xs font-medium"
                  style={{ color: i < drawn.length ? "rgba(255,255,255,0.95)" : "var(--text-muted)" }}
                >
                  {positions[i]}
                </span>
                {i < drawn.length ? (
                  <span className="text-2xl">{shuffled[drawn[i]].imageEmoji}</span>
                ) : (
                  <span className="text-sm" style={{ color: "var(--text-muted)" }}>—</span>
                )}
              </div>
            ))}
          </div>

          {/* 可滑动牌堆 */}
          <div
            ref={scrollRef}
            className="overflow-x-auto pb-4 cursor-grab active:cursor-grabbing select-none"
            style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
            onMouseDown={onMouseDown}
            onMouseMove={onMouseMove}
            onMouseUp={onMouseUp}
            onMouseLeave={onMouseUp}
          >
            <div className="flex gap-2 px-6" style={{ width: "max-content", minWidth: "100%" }}>
              {shuffled.map((card, idx) => {
                const isDrawn = drawn.includes(idx);
                const isHovered = hoveredIdx === idx && !isDrawn;
                return (
                  <div
                    key={idx}
                    className="flex-shrink-0 transition-all duration-200"
                    style={{
                      width: "72px", height: "108px",
                      transform: isHovered ? "translateY(-16px) scale(1.08)" : isDrawn ? "translateY(-8px) scale(0.95)" : "translateY(0)",
                      opacity: isDrawn ? 0.4 : 1,
                      cursor: isDrawn ? "default" : "pointer",
                      zIndex: isHovered ? 10 : 1,
                      position: "relative",
                    }}
                    onMouseEnter={() => !isDrawn && setHoveredIdx(idx)}
                    onMouseLeave={() => setHoveredIdx(null)}
                    onClick={() => handlePickCard(idx)}
                  >
                    {/* 牌背 - Gracie 风格：植物学月亮图案，神秘清新优雅 */}
                    <div
                      className="w-full h-full rounded-xl overflow-hidden"
                      style={{
                        boxShadow: isHovered
                          ? "0 8px 24px rgba(155,168,141,0.3)"
                          : "0 3px 10px rgba(139,154,125,0.15)",
                      }}
                    >
                      {isDrawn
                        ? <div style={{ width: "100%", height: "100%", borderRadius: 12, background: "linear-gradient(145deg, #F5F2EC, #E8E4DC)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, color: "#9BA88D", border: "1px solid rgba(155,168,141,0.4)" }}>✓</div>
                        : <CardBackSVG width={72} height={108} hover={isHovered} />
                      }
                    </div>
                    {isHovered && (
                      <div
                        className="absolute -bottom-6 left-1/2 text-xs font-medium whitespace-nowrap"
                        style={{ transform: "translateX(-50%)", color: "var(--sage-deep)" }}
                      >
                        点击选择
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}

      {/* 翻牌阶段 */}
      {phase === "flip" && (
        <>
          <div className="text-center mb-6">
            <p className="text-lg font-medium" style={{ color: "var(--text-warm)" }}>
              {flipped.size < count ? "点击每张牌，翻开它" : "✨ 全部翻开，获取解读"}
            </p>
            <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
              深呼吸，感受每张牌的能量
            </p>
          </div>

          <SpreadLayout spreadId={spreadId} count={count}>
            {drawn.map((cardIdx, i) => {
              const card = shuffled[cardIdx];
              const isFlipped = flipped.has(i);
              const reversed = reversedMap.current[i] ?? false;
              return (
                <div key={i} className="flex flex-col items-center gap-2">
                  <div className="text-xs font-medium" style={{ color: "var(--sage-deep)" }}>
                    {positions[i]}
                  </div>
                  <div
                    style={{ width: "90px", height: "135px", perspective: "1000px", cursor: isFlipped ? "default" : "pointer" }}
                    onClick={() => !isFlipped && handleFlip(i)}
                  >
                    <div style={{
                      position: "relative", width: "100%", height: "100%",
                      transformStyle: "preserve-3d",
                      transition: "transform 0.65s cubic-bezier(0.4,0,0.2,1)",
                      transform: isFlipped ? "rotateY(180deg)" : "rotateY(0deg)"
                    }}>
                      <div style={{
                        position: "absolute", inset: 0, backfaceVisibility: "hidden", borderRadius: "12px",
                        overflow: "hidden", boxShadow: "0 6px 24px rgba(139,154,125,0.2)",
                      }}>
                        <CardBackSVG width={90} height={135} />
                      </div>
                      <div style={{
                        position: "absolute", inset: 0, backfaceVisibility: "hidden",
                        transform: "rotateY(180deg)", borderRadius: "12px",
                        background: "linear-gradient(145deg, #FCFAF6 0%, #F8F5F0 100%)",
                        border: "1px solid rgba(155,168,141,0.3)",
                        display: "flex", flexDirection: "column", alignItems: "center",
                        justifyContent: "center", padding: "8px",
                        boxShadow: "0 6px 20px rgba(139,154,125,0.15)"
                      }}>
                        <div style={{ fontSize: "28px", marginBottom: "4px" }}>{card.imageEmoji}</div>
                        <div style={{ fontSize: "11px", fontWeight: "bold", color: "var(--text-warm)", textAlign: "center" }}>
                          {card.nameZh}
                        </div>
                        {reversed && (
                          <div style={{ fontSize: "10px", marginTop: "2px", color: "var(--text-muted)" }}>逆位</div>
                        )}
                      </div>
                    </div>
                  </div>
                  {!isFlipped && (
                    <div style={{ fontSize: "11px", color: "var(--text-muted)" }}>点击翻牌</div>
                  )}
                </div>
              );
            })}
          </SpreadLayout>
        </>
      )}
    </div>
  );
}
