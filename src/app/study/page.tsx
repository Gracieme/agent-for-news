"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { UserButton, useUser } from "@clerk/nextjs";

interface VocabCard {
  word?: string;
  pos?: string;
  pos_zh?: string;
  sent?: string;
  zh?: string;
  tip?: string;
}

interface Expression {
  expression?: string;
  definition?: string;
  nuance?: string;
  cultural_note?: string;
  simulated_dialogue?: string;
}

interface Paper {
  title?: string;
  authors?: string;
  venue?: string;
  citationCount?: number;
  abstract?: string;
  url?: string;
  relevance?: string;
  relevance_to_MICM?: string;
}

interface Digest {
  date: string;
  spoken?: {
    summary?: string;
    cards?: Array<{ word?: string; explanation_zh?: string; example_en?: string; nuance?: string; cultural_note?: string }>;
    expressions?: Expression[];
    practice?: { sceneLabel?: string; storyEn?: string; storyZh?: string };
    studyTip?: string;
  };
  academicFrontier?: {
    summary?: string;
    sections?: Array<{ sectionTitle?: string; papers?: Paper[] }>;
  };
  readingGuide?: {
    summary?: string;
    source?: string;
    date?: string;
    title?: string;
    url?: string;
    excerptHtml?: string;
    vocabCards?: VocabCard[];
    teacherNote?: string;
    core_argument?: string;
    scaffolding_questions?: string[];
    sentence_logic_map?: Array<{ sentence?: string; logic_breakdown?: string }>;
  };
}

export default function StudyPage() {
  const { isSignedIn } = useUser();
  const [digest, setDigest] = useState<Digest | null>(null);
  const [date, setDate] = useState<string | null>(null);
  const [dates, setDates] = useState<string[]>([]);
  const [tab, setTab] = useState<"文献" | "英语">("文献");
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadDigest = (d?: string) => {
    const url = d ? `/api/agents/digest?date=${d}` : "/api/agents/digest";
    return fetch(url)
      .then((r) => r.json())
      .then((data) => {
        if (data.digest) {
          setDigest(data.digest);
          setDate(data.date);
        } else {
          setMessage(data.message || "暂无推送");
        }
      });
  };

  useEffect(() => {
    Promise.all([
      fetch("/api/agents/digest?list=1").then((r) => r.json()),
      loadDigest(),
    ])
      .then(([listData]) => {
        if (listData.dates) setDates(listData.dates);
      })
      .catch(() => setMessage("获取失败"))
      .finally(() => setLoading(false));
  }, []);

  const papers = digest?.academicFrontier?.sections?.flatMap((s) => s.papers || []) || [];
  const expressions = digest?.spoken?.expressions || digest?.spoken?.cards || [];
  const readingGuide = digest?.readingGuide;

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
          <Link
            href="/agents"
            className="px-5 py-2 rounded-full font-medium transition-all hover:scale-[1.02]"
            style={{ color: "var(--sage-deep)", border: "2px solid var(--sage-deep)" }}
          >
            Agent 小队
          </Link>
          {isSignedIn && <UserButton />}
        </div>
      </nav>

      <main className="relative z-10 max-w-4xl mx-auto px-6 pb-16">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold" style={{ color: "var(--text-warm)" }}>
            📚 格雷西的学习天地
          </h1>
          <p className="mt-2" style={{ color: "var(--text-muted)" }}>
            每日邮件内容同步，随时复习 文献 · 英语
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
              配置 GitHub Secrets：<code className="px-1.5 py-0.5 rounded bg-white/80">SUPABASE_URL</code>、
              <code className="px-1.5 py-0.5 rounded bg-white/80">SUPABASE_SERVICE_ROLE_KEY</code>
              ，并确保 agent-squad 已同步到 Supabase。
            </p>
          </div>
        )}

        {!loading && digest && date && (
          <>
            <div className="flex items-center gap-4 mb-6 flex-wrap">
              <span className="text-sm" style={{ color: "var(--text-muted)" }}>
                推送日期：
              </span>
              <select
                value={date}
                onChange={(e) => {
                  const d = e.target.value;
                  if (d) {
                    setLoading(true);
                    loadDigest(d).finally(() => setLoading(false));
                  }
                }}
                className="rounded-lg px-3 py-2 border"
                style={{ borderColor: "var(--border-soft)", background: "white" }}
              >
                {dates.length ? dates.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                )) : (
                  <option value={date}>{date}</option>
                )}
              </select>
              <div className="flex gap-2">
                <button
                  onClick={() => setTab("文献")}
                  className="px-4 py-2 rounded-full font-medium transition-all"
                  style={{
                    background: tab === "文献" ? "var(--sage-deep)" : "transparent",
                    color: tab === "文献" ? "white" : "var(--sage-deep)",
                    border: "2px solid var(--sage-deep)",
                  }}
                >
                  1. 文献
                </button>
                <button
                  onClick={() => setTab("英语")}
                  className="px-4 py-2 rounded-full font-medium transition-all"
                  style={{
                    background: tab === "英语" ? "var(--sage-deep)" : "transparent",
                    color: tab === "英语" ? "white" : "var(--sage-deep)",
                    border: "2px solid var(--sage-deep)",
                  }}
                >
                  2. 英语
                </button>
              </div>
            </div>

            {tab === "文献" && (
              <section
                className="rounded-2xl p-6"
                style={{
                  background: "var(--cream-light)",
                  border: "1px solid var(--border-soft)",
                }}
              >
                <h2 className="text-xl font-bold mb-4" style={{ color: "var(--sage-deep)" }}>
                  📄 学术前沿
                </h2>
                <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
                  {digest.academicFrontier?.summary}
                </p>
                <div className="space-y-6">
                  {papers.length === 0 && (
                    <p style={{ color: "var(--text-muted)" }}>今日暂无文献</p>
                  )}
                  {papers.map((p, i) => (
                    <div
                      key={i}
                      className="rounded-xl p-5"
                      style={{
                        background: "rgba(255,255,255,0.8)",
                        border: "1px solid var(--border-soft)",
                      }}
                    >
                      <a
                        href={p.url || "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-semibold text-lg block mb-2 hover:underline"
                        style={{ color: "var(--sage-deep)" }}
                      >
                        {p.title}
                      </a>
                      <p className="text-sm mb-2" style={{ color: "var(--text-muted)" }}>
                        {p.authors} · {p.venue}
                        {p.citationCount != null && ` · ${p.citationCount} 引用`}
                      </p>
                      {p.abstract && (
                        <p className="text-sm mb-3 line-clamp-3" style={{ color: "var(--text-warm)" }}>
                          {p.abstract}
                        </p>
                      )}
                      {(p.relevance || p.relevance_to_MICM) && (
                        <div
                          className="text-sm p-3 rounded-lg"
                          style={{
                            background: "rgba(155,168,141,0.12)",
                            color: "var(--text-warm)",
                          }}
                        >
                          <span className="font-medium">与 MICM 的关联：</span>{" "}
                          {p.relevance || p.relevance_to_MICM}
                        </div>
                      )}
                      {p.url && (
                        <a
                          href={p.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-block mt-3 text-sm font-medium"
                          style={{ color: "var(--link-accent)" }}
                        >
                          查看原文 →
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}

            {tab === "英语" && (
              <div className="space-y-8">
                {/* 每日生活口语 */}
                <section
                  className="rounded-2xl p-6"
                  style={{
                    background: "var(--cream-light)",
                    border: "1px solid var(--border-soft)",
                  }}
                >
                  <h2 className="text-xl font-bold mb-4" style={{ color: "var(--sage-deep)" }}>
                    🗣 每日生活口语
                  </h2>
                  <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
                    {digest.spoken?.summary}
                  </p>
                  <div className="space-y-6">
                    {expressions.map((e, i) => {
                        const ex = e as Expression & { word?: string; explanation_zh?: string; example_en?: string };
                        return (
                      <div
                        key={i}
                        className="rounded-xl p-5"
                        style={{
                          background: "rgba(255,255,255,0.8)",
                          border: "1px solid var(--border-soft)",
                        }}
                      >
                        <div className="font-bold text-lg mb-2" style={{ color: "var(--sage-deep)" }}>
                          {ex.expression || ex.word}
                        </div>
                        {(ex.definition || ex.explanation_zh) && (
                          <p className="text-sm mb-2" style={{ color: "var(--text-warm)" }}>
                            {ex.definition || ex.explanation_zh}
                          </p>
                        )}
                        {ex.nuance && (
                          <p className="text-sm mb-2" style={{ color: "var(--text-muted)" }}>
                            <span className="font-medium">Nuance：</span>
                            {ex.nuance}
                          </p>
                        )}
                        {ex.cultural_note && (
                          <p className="text-sm mb-2" style={{ color: "var(--text-muted)" }}>
                            <span className="font-medium">Cultural Note：</span>
                            {ex.cultural_note}
                          </p>
                        )}
                        {(ex.simulated_dialogue || ex.example_en) && (
                          <div
                            className="text-sm p-3 rounded-lg mt-2 italic"
                            style={{
                              background: "rgba(155,168,141,0.1)",
                              color: "var(--text-warm)",
                            }}
                          >
                            {ex.simulated_dialogue || ex.example_en}
                          </div>
                        )}
                      </div>
                    );
                    })}
                  </div>
                  {digest.spoken?.studyTip && (
                    <div
                      className="mt-6 p-4 rounded-xl"
                      style={{
                        background: "linear-gradient(135deg, rgba(107,122,93,0.15), rgba(184,169,154,0.15))",
                        border: "1px solid var(--border-soft)",
                      }}
                    >
                      <span className="font-medium">学习提示：</span> {digest.spoken.studyTip}
                    </div>
                  )}
                </section>

                {/* 外刊精读 */}
                <section
                  className="rounded-2xl p-6"
                  style={{
                    background: "var(--cream-light)",
                    border: "1px solid var(--border-soft)",
                  }}
                >
                  <h2 className="text-xl font-bold mb-4" style={{ color: "var(--sage-deep)" }}>
                    📖 外刊精读
                  </h2>
                  <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
                    {readingGuide?.summary}
                  </p>
                  {readingGuide?.title && (
                    <div className="mb-6">
                      <a
                        href={readingGuide.url || "#"}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-semibold text-lg block mb-2 hover:underline"
                        style={{ color: "var(--sage-deep)" }}
                      >
                        {readingGuide.title}
                      </a>
                      <p className="text-sm" style={{ color: "var(--text-muted)" }}>
                        {readingGuide.source} · {readingGuide.date}
                      </p>
                    </div>
                  )}
                  {readingGuide?.core_argument && (
                    <div className="mb-6 p-4 rounded-lg" style={{ background: "rgba(255,255,255,0.8)", border: "1px solid var(--border-soft)" }}>
                      <span className="font-medium">核心论点：</span>
                      {readingGuide.core_argument}
                    </div>
                  )}
                  {(readingGuide?.vocabCards?.length || 0) > 0 && (
                    <div className="mb-6">
                      <h3 className="font-semibold mb-3" style={{ color: "var(--sage-deep)" }}>
                        词汇卡 C1/C2
                      </h3>
                      <div className="space-y-4">
                        {(readingGuide?.vocabCards ?? []).map((v, i) => (
                          <div
                            key={i}
                            className="rounded-lg p-4"
                            style={{ background: "rgba(255,255,255,0.8)", border: "1px solid var(--border-soft)" }}
                          >
                            <div className="flex items-baseline gap-2 mb-2">
                              <span className="font-bold" style={{ color: "var(--sage-deep)" }}>
                                {v.word}
                              </span>
                              <span className="text-sm italic" style={{ color: "var(--text-muted)" }}>
                                {v.pos}
                                {v.pos_zh && ` · ${v.pos_zh}`}
                              </span>
                            </div>
                            {v.sent && (
                              <p className="text-sm italic mb-2" style={{ color: "var(--text-warm)" }}>
                                {v.sent}
                              </p>
                            )}
                            {v.zh && <p className="text-sm mb-1">{v.zh}</p>}
                            {v.tip && <p className="text-xs" style={{ color: "var(--text-muted)" }}>{v.tip}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {readingGuide?.teacherNote && (
                    <div
                      className="p-4 rounded-lg"
                      style={{
                        background: "rgba(155,168,141,0.12)",
                        borderLeft: "4px solid var(--sage-deep)",
                      }}
                    >
                      <span className="font-medium">教师笔记：</span> {readingGuide.teacherNote}
                    </div>
                  )}
                  {(!readingGuide?.title && !readingGuide?.vocabCards?.length) && (
                    <p style={{ color: "var(--text-muted)" }}>今日暂无外刊精读</p>
                  )}
                </section>
              </div>
            )}
          </>
        )}
      </main>

      <footer className="text-center py-6" style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
        格雷西的学习天地 · 每日邮件同步 · 随时复习
      </footer>
    </div>
  );
}
