"use client";

import { useState } from "react";
import { DimensionEntry } from "@/lib/reading-types";

const DIMS = [
  { key: "numerology", emoji: "🔢", label: "数字能量" },
  { key: "color",      emoji: "🎨", label: "色彩信号" },
  { key: "astrology",  emoji: "⭐", label: "星象背景" },
  { key: "elements",   emoji: "🌊", label: "元素分析" },
  { key: "symbolism",  emoji: "🔮", label: "符号解读" },
  { key: "kabbalah",   emoji: "🌳", label: "卡巴拉路径" },
] as const;

function DimRow({ emoji, label, summary, detail }: { emoji: string; label: string; summary: string; detail?: string }) {
  return (
    <div className="flex gap-3 py-2.5" style={{ borderBottom: "1px solid rgba(139,154,125,0.12)" }}>
      <span className="text-base flex-shrink-0 w-6 text-center">{emoji}</span>
      <div className="flex-1 min-w-0">
        <span className="text-xs font-semibold mr-2" style={{ color: "var(--sage-deep)" }}>{label}</span>
        <span className="text-sm" style={{ color: "var(--text-warm)" }}>{summary}</span>
        {detail && (
          <p className="text-xs mt-1 leading-relaxed" style={{ color: "var(--text-muted)" }}>{detail}</p>
        )}
      </div>
    </div>
  );
}

function CardDimension({ entry, defaultOpen }: { entry: DimensionEntry; defaultOpen: boolean }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="rounded-xl overflow-hidden mb-3" style={{ border: "1px solid rgba(139,154,125,0.2)", background: "rgba(250,249,246,0.7)" }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-3 text-left transition-colors"
        style={{ background: open ? "rgba(139,154,125,0.1)" : "transparent" }}
      >
        <span className="text-sm font-semibold" style={{ color: "var(--text-warm)" }}>
          {entry.cardName}
          {entry.reversed && <span className="ml-1.5 text-xs font-normal" style={{ color: "var(--text-muted)" }}>逆位</span>}
        </span>
        <span className="text-xs" style={{ color: "var(--sage-deep)" }}>{open ? "收起 ▲" : "展开 ▼"}</span>
      </button>

      {open && (
        <div className="px-4 pb-2">
          {entry.numerology.number !== null && (
            <DimRow
              emoji="🔢" label="数字能量"
              summary={`数字${entry.numerology.number} · ${entry.numerology.energy}`}
              detail={entry.numerology.meaning}
            />
          )}
          <DimRow
            emoji="🎨" label="色彩信号"
            summary={entry.color.dominant.join("、")}
            detail={entry.color.signals}
          />
          <DimRow
            emoji="⭐" label="星象背景"
            summary={`${entry.astrology.sign} · ${entry.astrology.planet}`}
            detail={entry.astrology.influence}
          />
          <DimRow
            emoji="🌊" label="元素分析"
            summary={entry.elements.composition}
            detail={entry.elements.analysis}
          />
          <DimRow
            emoji="🔮" label="符号解读"
            summary={entry.symbolism.symbols.join("、")}
            detail={entry.symbolism.interpretation}
          />
          {entry.kabbalah && (
            <DimRow
              emoji="🌳" label="卡巴拉路径"
              summary={`${entry.kabbalah.path} · ${entry.kabbalah.planets}`}
              detail={entry.kabbalah.depth}
            />
          )}
        </div>
      )}
    </div>
  );
}

export default function SixDimensionPanel({ dimensions }: { dimensions: DimensionEntry[] }) {
  if (!dimensions || dimensions.length === 0) return null;

  return (
    <div className="glass rounded-2xl p-6 md:p-8 mb-6">
      <h3 className="text-base font-semibold mb-4 flex items-center gap-2" style={{ color: "var(--text-warm)" }}>
        <span>✦</span> 六维度深度解读
        <span className="text-xs font-normal ml-1" style={{ color: "var(--text-muted)" }}>数字 · 色彩 · 星象 · 元素 · 符号 · 卡巴拉</span>
      </h3>
      {dimensions.map((entry, i) => (
        <CardDimension key={i} entry={entry} defaultOpen={i === 0} />
      ))}
    </div>
  );
}
