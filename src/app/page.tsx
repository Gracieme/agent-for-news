"use client";

import Link from "next/link";
import { UserButton, useUser } from "@clerk/nextjs";

/* Gracie 风格：清新优雅的植物浮动装饰 */
const floatingElements = [
  { x: 8, y: 15, char: "✿", size: 14, delay: 0 },
  { x: 22, y: 8, char: "✦", size: 10, delay: 0.5 },
  { x: 78, y: 20, char: "✿", size: 12, delay: 1 },
  { x: 92, y: 10, char: "✦", size: 9, delay: 1.5 },
  { x: 5, y: 55, char: "✦", size: 8, delay: 0.8 },
  { x: 15, y: 72, char: "✿", size: 13, delay: 2 },
  { x: 85, y: 65, char: "✿", size: 11, delay: 0.3 },
  { x: 95, y: 80, char: "✦", size: 9, delay: 1.2 },
  { x: 45, y: 5, char: "✦", size: 7, delay: 0.6 },
  { x: 60, y: 88, char: "✿", size: 10, delay: 1.8 },
  { x: 35, y: 92, char: "✦", size: 8, delay: 2.5 },
  { x: 72, y: 3, char: "✿", size: 11, delay: 0.4 },
];

export default function HomePage() {
  const { isSignedIn } = useUser();

  return (
    <div className="min-h-screen relative overflow-hidden" style={{ background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 35%, #F5F2EC 70%, #F0EDE8 100%)" }}>
      {/* 背景植物装饰 - 清新优雅 */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        {floatingElements.map((el, i) => (
          <div
            key={i}
            className="absolute select-none"
            style={{
              left: `${el.x}%`,
              top: `${el.y}%`,
              fontSize: el.size,
              color: el.char === "✿" ? "var(--dusty-rose)" : "var(--sage)",
              opacity: 0.25 + (i % 3) * 0.07,
              animation: `float ${4.5 + i * 0.35}s ease-in-out infinite`,
              animationDelay: `${el.delay}s`,
              lineHeight: 1,
            }}
          >
            {el.char}
          </div>
        ))}
      </div>

      {/* 导航栏 */}
      <nav className="relative z-10 flex justify-between items-center px-8 py-6">
        <div className="text-2xl font-bold tracking-tight" style={{ color: "var(--text-warm)" }}>
          <span style={{ color: "var(--sage-deep)", marginRight: 6 }}>☽</span> 格雷西的塔罗驿站
        </div>
        <div className="flex items-center gap-3">
          {isSignedIn ? (
            <>
              <Link
                href="/reading"
                className="px-5 py-2 rounded-full text-white font-medium transition-all hover:scale-[1.02]"
                style={{ background: "var(--sage-deep)", boxShadow: "0 2px 12px rgba(139,154,125,0.25)" }}
              >
                开始占卜
              </Link>
              <Link
                href="/history"
                className="px-5 py-2 rounded-full font-medium transition-all hover:scale-[1.02]"
                style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)" }}
              >
                历史记录
              </Link>
              <Link
                href="/learn"
                className="px-5 py-2 rounded-full font-medium transition-all hover:scale-[1.02]"
                style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)" }}
              >
                塔罗入门
              </Link>
              <Link
                href="/agents"
                className="px-5 py-2 rounded-full font-medium transition-all hover:scale-[1.02]"
                style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)" }}
              >
                Agent 小队
              </Link>
              <UserButton />
            </>
          ) : (
            <>
              <Link
                href="/sign-in"
                className="px-5 py-2 rounded-full font-medium transition-all hover:scale-[1.02]"
                style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)" }}
              >
                登录
              </Link>
              <Link
                href="/sign-up"
                className="px-5 py-2 rounded-full text-white font-medium transition-all hover:scale-[1.02]"
                style={{ background: "var(--sage-deep)", boxShadow: "0 2px 12px rgba(139,154,125,0.25)" }}
              >
                注册
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* 主内容 */}
      <main className="relative z-10 flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
        <div className="text-7xl mb-6 float-animation" style={{ opacity: 0.85 }}>☽</div>

        <h1 className="text-5xl md:text-6xl font-bold mb-4 tracking-tight" style={{ color: "var(--text-warm)" }}>
          格雷西的塔罗驿站
        </h1>
        <p className="text-xl mb-3 shimmer-text font-medium">
          宇宙为你守候，答案已在星光中
        </p>
        <p className="text-lg mb-12 max-w-xl leading-relaxed" style={{ color: "var(--text-muted)" }}>
          通过AI的智慧与塔罗的神秘力量，探索内心深处的声音，
          获得属于你的宇宙指引
        </p>

        {/* 按钮 */}
        <div className="flex flex-col sm:flex-row gap-4 mb-16">
          {isSignedIn ? (
            <Link
              href="/reading"
              className="px-10 py-4 rounded-full text-white text-xl font-bold transition-all hover:scale-[1.02]"
              style={{
                background: "var(--sage-deep)",
                boxShadow: "0 6px 24px rgba(139,154,125,0.3)"
              }}
            >
              ☽ 开始今日占卜
            </Link>
          ) : (
            <>
              <Link
                href="/sign-up"
                className="px-10 py-4 rounded-full text-white text-xl font-bold transition-all hover:scale-[1.02]"
                style={{
                  background: "var(--sage-deep)",
                  boxShadow: "0 6px 24px rgba(139,154,125,0.3)"
                }}
              >
                ☽ 免费开始占卜
              </Link>
              <Link
                href="/sign-in"
                className="px-10 py-4 rounded-full text-xl font-medium transition-all hover:scale-[1.02]"
                style={{
                  color: "var(--sage-deep)",
                  border: "2px solid var(--sage-deep)",
                  background: "rgba(255,255,255,0.85)"
                }}
              >
                已有账号登录
              </Link>
            </>
          )}
        </div>

        {/* 特性卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full">
          {[
            { emoji: "📖", title: "小白入门", desc: "从零了解塔罗、学会怎么问问题、什么情况用什么牌阵", href: "/learn" },
            { emoji: "☽", title: "AI推荐牌阵", desc: "描述你的情况，AI根据Gracie老师方法帮你选最合适的牌阵", href: "/reading" },
            { emoji: "✦", title: "融合老师解读", desc: "融入Gracie塔罗课程知识体系，解读更专业、更有深度", href: "/reading" },
          ].map((item, i) => (
            <Link
              key={i}
              href={item.href}
              className="glass rounded-2xl p-8 transition-all hover:scale-[1.02] hover:shadow-lg block text-left"
            >
              <div className="text-3xl mb-3" style={{ opacity: 0.9 }}>{item.emoji}</div>
              <h3 className="text-lg font-bold mb-2" style={{ color: "var(--text-warm)" }}>{item.title}</h3>
              <p className="text-sm leading-relaxed" style={{ color: "var(--text-muted)" }}>{item.desc}</p>
            </Link>
          ))}
        </div>
      </main>

      {/* 底部 */}
      <footer className="relative z-10 text-center py-8" style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
        <p>格雷西的塔罗驿站 · 每一张牌都是一面镜子</p>
      </footer>
    </div>
  );
}
