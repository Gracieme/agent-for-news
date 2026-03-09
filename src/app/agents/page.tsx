"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { UserButton, useUser } from "@clerk/nextjs";

interface ResearchPaper {
  title: string;
  authors: string;
  venue: string;
  citationCount?: number;
  abstract?: string;
  url?: string;
  relevance?: string;
}

interface Digest {
  date: string;
  generatedAt?: string;
  english: { summary: string; raw: string };
  makeup: { summary: string; raw: string };
  research: { summary: string; raw: string; papers: ResearchPaper[] };
}

export default function AgentsPage() {
  const { isSignedIn } = useUser();
  const [digest, setDigest] = useState<Digest | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/agents/digest")
      .then((r) => r.json())
      .then((data) => {
        if (data.digest) {
          setDigest(data.digest);
          setDate(data.date);
        } else {
          setMessage(data.message || "暂无推送");
        }
      })
      .catch(() => setMessage("获取失败"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div
      className="min-h-screen"
      style={{
        background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 35%, #F5F2EC 70%, #F0EDE8 100%)",
      }}
    >
      <nav className="relative z-10 flex justify-between items-center px-8 py-6">
        <Link
          href="/"
          className="text-2xl font-bold tracking-tight"
          style={{ color: "var(--text-warm)" }}
        >
          <span style={{ color: "var(--sage-deep)", marginRight: 6 }}>☽</span>
          格雷西的塔罗驿站
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="px-5 py-2 rounded-full font-medium transition-all hover:scale-[1.02]"
            style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)" }}
          >
            首页
          </Link>
          {isSignedIn && <UserButton />}
        </div>
      </nav>

      <main className="relative z-10 max-w-4xl mx-auto px-6 pb-16">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold" style={{ color: "var(--text-warm)" }}>
            Agent 小队 · 每日推送
          </h1>
          <p className="mt-2" style={{ color: "var(--text-muted)" }}>
            英语习语 · 美妆小贴士 · 科研文献
          </p>
        </div>

        {loading && (
          <p className="text-center" style={{ color: "var(--text-muted)" }}>
            加载中…
          </p>
        )}

        {!loading && (message || !digest) && (
          <div
            className="rounded-2xl p-8 text-center"
            style={{
              background: "var(--cream-light)",
              border: "1px solid var(--border-soft)",
              color: "var(--text-muted)",
            }}
          >
            <p>{message || "暂无推送"}</p>
            <p className="mt-3 text-sm">
              在项目 <code className="px-1.5 py-0.5 rounded bg-white/80">agent-squad</code> 目录运行{" "}
              <code className="px-1.5 py-0.5 rounded bg-white/80">npm run run-once</code>，并配置
              Supabase 同步后即可在此查看。
            </p>
          </div>
        )}

        {!loading && digest && date && (
          <div className="space-y-8">
            <p className="text-sm" style={{ color: "var(--text-muted)" }}>
              推送日期：{date}
            </p>

            {/* 英语学习 */}
            <section
              className="rounded-2xl p-6"
              style={{
                background: "var(--cream-light)",
                border: "1px solid var(--border-soft)",
              }}
            >
              <h2 className="text-lg font-semibold mb-3" style={{ color: "var(--sage-deep)" }}>
                📚 英语学习助手
              </h2>
              <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
                {digest.english.summary}
              </p>
              <div
                className="whitespace-pre-wrap text-[15px] leading-relaxed"
                style={{ color: "var(--text-warm)" }}
              >
                {digest.english.raw}
              </div>
            </section>

            {/* 美妆学习 */}
            <section
              className="rounded-2xl p-6"
              style={{
                background: "var(--cream-light)",
                border: "1px solid var(--border-soft)",
              }}
            >
              <h2 className="text-lg font-semibold mb-3" style={{ color: "var(--sage-deep)" }}>
                💄 美妆学习助手
              </h2>
              <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
                {digest.makeup.summary}
              </p>
              <p className="whitespace-pre-wrap leading-relaxed" style={{ color: "var(--text-warm)" }}>
                {digest.makeup.raw}
              </p>
            </section>

            {/* 科研文献 */}
            <section
              className="rounded-2xl p-6"
              style={{
                background: "var(--cream-light)",
                border: "1px solid var(--border-soft)",
              }}
            >
              <h2 className="text-lg font-semibold mb-3" style={{ color: "var(--sage-deep)" }}>
                📄 科研文献助手
              </h2>
              <p className="text-sm mb-4" style={{ color: "var(--text-muted)" }}>
                {digest.research.summary}
              </p>
              <div className="space-y-6">
                {(digest.research.papers || []).map((p, i) => (
                  <div
                    key={i}
                    className="rounded-xl p-4"
                    style={{
                      background: "rgba(255,255,255,0.6)",
                      border: "1px solid var(--border-soft)",
                    }}
                  >
                    <a
                      href={p.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium block mb-1 hover:underline"
                      style={{ color: "var(--sage-deep)" }}
                    >
                      {p.title}
                    </a>
                    <p className="text-sm mb-1" style={{ color: "var(--text-muted)" }}>
                      {p.authors} · {p.venue}
                      {p.citationCount != null && ` · ${p.citationCount} 引用`}
                    </p>
                    {p.abstract && (
                      <p className="text-sm mb-2 line-clamp-3" style={{ color: "var(--text-warm)" }}>
                        {p.abstract}
                      </p>
                    )}
                    {p.relevance && (
                      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                        <span className="font-medium">与研究的关联：</span> {p.relevance}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
