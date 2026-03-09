"use client";

import { useEffect, useState } from "react";
import { useUser, UserButton } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Reading } from "@/lib/supabase";

export default function HistoryPage() {
  const { isSignedIn, user } = useUser();
  const router = useRouter();
  const [readings, setReadings] = useState<Reading[]>([]);
  const [selected, setSelected] = useState<Reading | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isSignedIn) { router.push("/sign-in"); return; }
    if (!user) return;

    // 先从 localStorage 加载（无需数据库，即时显示）
    try {
      const local: Reading[] = JSON.parse(localStorage.getItem("tarot_readings") || "[]");
      const mine = local.filter(r => r.user_id === user.id);
      if (mine.length > 0) { setReadings(mine); setLoading(false); }
    } catch {}

    // 再从数据库补充（如有配置）
    fetch(`/api/save-reading?user_id=${user.id}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.readings && data.readings.length > 0) {
          try {
            const local: Reading[] = JSON.parse(localStorage.getItem("tarot_readings") || "[]");
            const dbIds = new Set(data.readings.map((r: Reading) => r.id));
            const localOnly = local.filter(r => !dbIds.has(r.id));
            const merged = [...data.readings, ...localOnly].sort(
              (a, b) => new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
            );
            setReadings(merged);
          } catch { setReadings(data.readings); }
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [isSignedIn, user, router]);

  if (!isSignedIn) return null;

  const formatDate = (str?: string) => {
    if (!str) return "";
    const d = new Date(str);
    return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2, "0")}`;
  };

  return (
    <div
      className="min-h-screen"
      style={{ background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 50%, #F5F2EC 100%)" }}
    >
      <nav className="flex justify-between items-center px-8 py-5">
        <Link href="/" className="text-xl font-bold tracking-tight" style={{ color: "var(--text-warm)" }}><span style={{ color: "var(--sage-deep)" }}>☽</span> 格雷西的塔罗驿站</Link>
        <div className="flex items-center gap-4">
          <Link href="/reading" className="text-sm" style={{ color: "var(--sage-deep)" }}>开始占卜</Link>
          <UserButton />
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="text-center mb-10">
          <div className="text-5xl mb-3">📖</div>
          <h2 className="text-3xl font-bold" style={{ color: "var(--text-warm)" }}>占卜历史</h2>
          <p className="mt-2" style={{ color: "var(--text-muted)" }}>每一次指引都是宇宙留给你的礼物</p>
        </div>

        {loading ? (
          <div className="text-center py-20 text-4xl float-animation">🔮</div>
        ) : readings.length === 0 ? (
          <div className="text-center glass rounded-3xl p-16">
            <div className="text-5xl mb-4">🌙</div>
            <p className="text-lg mb-6" style={{ color: "var(--text-muted)" }}>还没有占卜记录，去开启你的第一次星语之旅吧</p>
            <Link
              href="/reading"
              className="px-8 py-3 rounded-full text-white font-bold"
              style={{ background: "var(--sage-deep)" }}
            >
              开始占卜
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 gap-6">
            {/* 列表 */}
            <div className="space-y-3">
              {readings.map((r) => (
                <button
                  key={r.id}
                  onClick={() => setSelected(r)}
                  className={`w-full text-left glass rounded-2xl p-5 transition-all hover:scale-[1.01] hover:shadow-md ${selected?.id === r.id ? "ring-2 ring-[var(--sage)]" : ""}`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm font-medium px-3 py-1 rounded-full" style={{ background: "rgba(155,168,141,0.2)", color: "var(--sage-deep)" }}>
                      {r.spread_type}
                    </span>
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>{formatDate(r.created_at)}</span>
                  </div>
                  <p className="text-sm font-medium mb-2" style={{ color: "var(--text-warm)" }}>
                    {r.question || "宇宙自由解读"}
                  </p>
                  <div className="flex gap-2 flex-wrap">
                    {r.cards.map((c, i) => (
                      <span key={i} className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {c.nameZh}{c.reversed ? "↓" : ""}
                      </span>
                    ))}
                  </div>
                </button>
              ))}
            </div>

            {/* 详情 */}
            <div>
              {selected ? (
                <div className="glass rounded-2xl p-6 sticky top-6">
                  <div className="flex gap-2 flex-wrap mb-4">
                    {selected.cards.map((c, i) => (
                      <div key={i} className="glass rounded-xl px-3 py-1.5 text-center">
                        <div className="text-xs" style={{ color: "var(--sage-deep)" }}>{c.position}</div>
                        <div className="text-sm font-bold" style={{ color: "var(--text-warm)" }}>{c.nameZh}{c.reversed ? " ↓" : ""}</div>
                      </div>
                    ))}
                  </div>
                  {selected.question && (
                    <p className="text-sm mb-4 px-3 py-2 rounded-xl" style={{ background: "rgba(155,168,141,0.15)", color: "var(--sage-deep)" }}>
                      问：{selected.question}
                    </p>
                  )}
                  <div className="text-sm leading-7 whitespace-pre-wrap" style={{ color: "var(--text-warm)" }}>
                    {selected.interpretation}
                  </div>
                  <p className="text-xs mt-4" style={{ color: "var(--text-muted)" }}>{formatDate(selected.created_at)}</p>
                </div>
              ) : (
                <div className="glass rounded-2xl p-12 text-center" style={{ color: "var(--text-muted)" }}>
                  <div className="text-4xl mb-3">👈</div>
                  <p>选择左侧记录查看详情</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
