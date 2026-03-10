"use client";

import Link from "next/link";
import { SPREAD_GUIDE } from "@/lib/tarot-data";

export default function SpreadsPage() {
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
          <div className="text-6xl mb-4 float-animation">🃏</div>
          <h1 className="text-4xl font-bold mb-3" style={{ color: "var(--text-warm)" }}>选择牌阵指南</h1>
          <p style={{ color: "var(--text-muted)" }}>12种牌阵，找到最适合你当下问题的那一个</p>
        </div>

        <div className="space-y-3 mb-12">
          {SPREAD_GUIDE.map((spread) => (
            <div key={spread.id} className="glass rounded-2xl px-6 py-5 flex gap-5 items-start">
              <span className="text-3xl mt-0.5">{spread.emoji}</span>
              <div className="flex-1 min-w-0">
                <div className="text-base font-bold mb-1" style={{ color: "var(--text-warm)" }}>
                  {spread.name}
                </div>
                <div className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>
                  {spread.scenarios}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="glass rounded-3xl p-10 text-center">
          <div className="text-5xl mb-4">🔮</div>
          <h2 className="text-2xl font-bold mb-3" style={{ color: "var(--text-warm)" }}>
            还是拿不准？
          </h2>
          <p className="mb-6" style={{ color: "var(--text-muted)" }}>
            描述你的情况，AI 会自动帮你匹配最合适的牌阵
          </p>
          <Link
            href="/reading"
            className="inline-block px-10 py-4 rounded-full text-white text-lg font-bold transition-all hover:scale-105"
            style={{
              background: "var(--sage-deep)",
              boxShadow: "0 6px 24px rgba(139,154,125,0.25)"
            }}
          >
            开始占卜
          </Link>
        </div>
      </main>
    </div>
  );
}
