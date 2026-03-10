"use client";

import { useState, useEffect } from "react";
import { TarotCard } from "@/lib/tarot-data";

// 现代取象 & 心理画像（来自Gracie课程知识库）
const MODERN_ANALOGIES: Record<number, { analogy: string; insight?: string }> = {
  0:  { analogy: "盲盒 / 拆盲盒", insight: "不管结果是什么都欣然接受，不设预期" },
  1:  { analogy: "WiFi路由器", insight: "一手接天，一手接地，自己是能量中转站" },
  2:  { analogy: "庙里的木鱼", insight: "需要精神连接才能打动，不在乎物质展示" },
  3:  { analogy: "农场主 / 大地母亲", insight: "左脑规则与右脑灵感的完美平衡，有深层原则不易被左右" },
  4:  { analogy: "CEO / 严格的父亲", insight: "规则就是规则，不容商量" },
  5:  { analogy: "导师 / 合同公证人", insight: "代表契约、传统、有经验的引路人" },
  12: { analogy: "在绳上晃荡的瑜伽倒立者", insight: "甘愿牺牲与等待，悬停是一种修行" },
  13: { analogy: "马桶冲水 / 法律红线", insight: "彻底终结，不容商量。金句：阎王要人三更死，不会留人到五更" },
  14: { analogy: "空乘 / 调酒师", insight: "两种元素的精准调和，过程平稳但持续流动" },
  15: { analogy: "加班文化 / 996 / 枷锁", insight: "拿命换钱，明知是锁还是不愿离开" },
  16: { analogy: "地震预警 / 公司暴雷", insight: "突发性断裂，反而是重建的起点" },
  21: { analogy: "毕业典礼 / 剧组杀青", insight: "圆满不是拥有最多，而是欲望与拥有达到平衡" },
  // 小牌
  26: { analogy: "群聊里多方开麦互怼", insight: "混战局面，谁也没有绝对优势" },
  30: { analogy: "受伤的老兵最后一道防线", insight: "防御心极重，精力即将耗尽" },
  31: { analogy: "扛着所有行李的搬家工", insight: "承担了太多不属于自己的重量" },
  40: { analogy: "失去后才看见失去了什么", insight: "深层动机：因能力自卑而逃避，不是不爱，是不知如何开口" },
  58: { analogy: "深夜刷手机失眠焦虑循环", insight: "上三轮（思维）过载，下三轮（行动）堵塞" },
  59: { analogy: "背刺时刻 / 黎明前最黑暗", insight: "这是终点，但天亮了——最坏的已经过去" },
  // 宫廷牌
  32: { analogy: "刚入职充满热情的实习生", insight: "火之风，单纯冲动，是传递消息的使者" },
  33: { analogy: "空中飞人 / 到处出差的骑士", insight: "行动力强但缺耐心，冲劲大于计划" },
  47: { analogy: "心动了还没行动的浪漫主义者", insight: "心动先于行动，水之火，情感丰富但执行慢" },
};

const SUIT_LABELS: Record<string, string> = {
  wands: "权杖 🔥 火元素",
  cups: "圣杯 💧 水元素",
  swords: "宝剑 🌬️ 风元素",
  pentacles: "星币 🌍 土元素",
};

interface CardDetailModalProps {
  card: (TarotCard & { position: string; reversed: boolean }) | null;
  onClose: () => void;
}

export default function CardDetailModal({ card, onClose }: CardDetailModalProps) {
  const [showReversed, setShowReversed] = useState(false);

  useEffect(() => {
    if (card) setShowReversed(card.reversed);
  }, [card]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!card) return null;

  const extra = MODERN_ANALOGIES[card.id];
  const suitLabel = card.suit ? SUIT_LABELS[card.suit] : "大阿卡纳";
  const keywords = showReversed ? card.keywordsReversed : card.keywords;
  const meaning  = showReversed ? card.meaningReversed  : card.meaning;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4"
      style={{ background: "rgba(0,0,0,0.45)", backdropFilter: "blur(4px)" }}
      onClick={onClose}
    >
      <div
        className="w-full sm:max-w-md rounded-t-3xl sm:rounded-2xl p-6 pb-8 sm:p-8 relative"
        style={{ background: "linear-gradient(160deg, #FCFAF6, #F8F5F0)", maxHeight: "90vh", overflowY: "auto" }}
        onClick={e => e.stopPropagation()}
      >
        {/* 关闭按钮 */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 w-8 h-8 flex items-center justify-center rounded-full text-lg"
          style={{ background: "rgba(139,154,125,0.15)", color: "var(--sage-deep)" }}
        >
          ×
        </button>

        {/* 位置标签 */}
        <div className="text-xs font-medium mb-3 tracking-wide" style={{ color: "var(--sage-deep)" }}>
          {card.position}
        </div>

        {/* 牌名 + emoji */}
        <div className="flex items-center gap-4 mb-4">
          <span className="text-5xl">{card.imageEmoji}</span>
          <div>
            <div className="text-xl font-bold" style={{ color: "var(--text-warm)" }}>
              {card.nameZh}
              {card.reversed && (
                <span className="ml-2 text-sm font-normal" style={{ color: "var(--text-muted)" }}>逆位</span>
              )}
            </div>
            <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
              {suitLabel}
              {card.number !== undefined && ` · 数字${card.number}`}
            </div>
          </div>
        </div>

        {/* 现代取象 */}
        {extra && (
          <div className="rounded-xl px-4 py-3 mb-4" style={{ background: "rgba(139,154,125,0.1)", border: "1px solid rgba(139,154,125,0.2)" }}>
            <div className="text-xs font-semibold mb-1" style={{ color: "var(--sage-deep)" }}>现代取象</div>
            <div className="text-sm font-medium" style={{ color: "var(--text-warm)" }}>{extra.analogy}</div>
            {extra.insight && (
              <div className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-muted)" }}>{extra.insight}</div>
            )}
          </div>
        )}

        {/* 正/逆位切换 */}
        <div className="flex rounded-xl overflow-hidden mb-4" style={{ border: "1px solid rgba(139,154,125,0.25)" }}>
          {[false, true].map(rev => (
            <button
              key={String(rev)}
              onClick={() => setShowReversed(rev)}
              className="flex-1 py-2 text-sm font-medium transition-colors"
              style={{
                background: showReversed === rev ? "var(--sage-deep)" : "transparent",
                color: showReversed === rev ? "#fff" : "var(--sage-deep)",
              }}
            >
              {rev ? "逆位" : "正位"}
            </button>
          ))}
        </div>

        {/* 关键词 */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {keywords.map(kw => (
            <span key={kw} className="text-xs px-2.5 py-1 rounded-full" style={{ background: "rgba(139,154,125,0.12)", color: "var(--sage-deep)" }}>
              {kw}
            </span>
          ))}
        </div>

        {/* 牌意 */}
        <div className="text-sm leading-relaxed" style={{ color: "var(--text-warm)" }}>
          {meaning}
        </div>
      </div>
    </div>
  );
}
