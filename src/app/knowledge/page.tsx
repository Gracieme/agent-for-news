"use client";

import { useState, useRef } from "react";
import { useUser, UserButton } from "@clerk/nextjs";
import { useRouter } from "next/navigation";
import Link from "next/link";

interface KnowledgeEntry {
  fileName: string;
  topic: string;
  content: string;
  date: string;
}

export default function KnowledgePage() {
  const { isSignedIn } = useUser();
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState("");
  const [topic, setTopic] = useState("");
  const [result, setResult] = useState("");
  const [fileName, setFileName] = useState("");
  const [entries, setEntries] = useState<KnowledgeEntry[]>(() => {
    if (typeof window !== "undefined") {
      try { return JSON.parse(localStorage.getItem("tarot_knowledge") || "[]"); } catch { return []; }
    }
    return [];
  });
  const [selectedEntry, setSelectedEntry] = useState<KnowledgeEntry | null>(null);

  if (!isSignedIn) { router.push("/sign-in"); return null; }

  const handleUpload = async () => {
    const file = fileRef.current?.files?.[0];
    if (!file) { alert("请先选择视频文件"); return; }

    setUploading(true);
    setResult("");
    setProgress("正在上传视频，Gemini 正在观看并分析...");

    const formData = new FormData();
    formData.append("video", file);
    formData.append("topic", topic);

    try {
      setProgress("Gemini 正在提取塔罗知识（可能需要1-2分钟）...");
      const res = await fetch("/api/extract-knowledge", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.error) {
        setResult(`错误：${data.error}`);
      } else {
        setResult(data.knowledge);
        setFileName(data.fileName);

        // 保存到 localStorage
        const newEntry: KnowledgeEntry = {
          fileName: data.fileName,
          topic: topic || "塔罗课程笔记",
          content: data.knowledge,
          date: new Date().toLocaleString("zh-CN"),
        };
        const updated = [newEntry, ...entries];
        setEntries(updated);
        localStorage.setItem("tarot_knowledge", JSON.stringify(updated));
      }
    } catch {
      setResult("上传失败，请重试");
    }

    setUploading(false);
    setProgress("");
  };

  return (
    <div
      className="min-h-screen"
      style={{ background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 50%, #F5F2EC 100%)" }}
    >
      <nav className="flex justify-between items-center px-8 py-5">
        <Link href="/" className="text-xl font-bold tracking-tight" style={{ color: "var(--text-warm)" }}>
          <span style={{ color: "var(--sage-deep)" }}>☽</span> 格雷西的塔罗驿站
        </Link>
        <div className="flex items-center gap-4">
          <Link href="/reading" className="text-sm" style={{ color: "var(--sage-deep)" }}>开始占卜</Link>
          <Link href="/history" className="text-sm" style={{ color: "var(--sage-deep)" }}>历史记录</Link>
          <UserButton />
        </div>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-8">
        <div className="text-center mb-10">
          <div className="text-5xl mb-3">🎓</div>
          <h2 className="text-3xl font-bold" style={{ color: "var(--text-warm)" }}>塔罗知识库</h2>
          <p className="mt-2" style={{ color: "var(--text-muted)" }}>
            上传课程视频，提取的知识会<strong>自动保存到解读系统</strong>，所有占卜解读都会融入
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* 上传区 */}
          <div>
            <div className="glass rounded-3xl p-8 mb-6">
              <h3 className="text-xl font-bold mb-6" style={{ color: "var(--text-warm)" }}>📹 上传课程视频</h3>

              <div
                className="border-2 border-dashed rounded-2xl p-8 text-center mb-5 cursor-pointer transition-all hover:border-purple-400"
                style={{ borderColor: "#c4a0e8" }}
                onClick={() => fileRef.current?.click()}
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept="video/*"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) setFileName(f.name);
                  }}
                />
                <div className="text-4xl mb-3">🎬</div>
                {fileName ? (
                  <p className="font-medium" style={{ color: "var(--sage-deep)" }}>{fileName}</p>
                ) : (
                  <>
                    <p className="font-medium mb-1" style={{ color: "var(--text-warm)" }}>点击选择视频</p>
                    <p className="text-sm" style={{ color: "var(--text-muted)" }}>支持 MP4、MOV、AVI · 建议30分钟以内</p>
                  </>
                )}
              </div>

              <div className="mb-5">
                <label className="block text-sm font-medium mb-2" style={{ color: "var(--text-warm)" }}>
                  重点关注主题（可选）
                </label>
                <input
                  type="text"
                  className="glass w-full rounded-xl px-4 py-3 outline-none"
                  style={{ color: "var(--text-warm)" }}
                  placeholder="例如：大阿卡纳、情感牌阵、逆位解读..."
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                />
              </div>

              <button
                onClick={handleUpload}
                disabled={uploading}
                className="w-full py-4 rounded-full text-white font-bold transition-all hover:scale-105 disabled:opacity-60 disabled:cursor-not-allowed"
                style={{ background: "var(--sage-deep)" }}
              >
                {uploading ? "🔮 分析中..." : "✨ 开始提取知识"}
              </button>

              {progress && (
                <p className="mt-4 text-sm text-center shimmer-text">{progress}</p>
              )}
            </div>

            {/* 历史条目列表 */}
            {entries.length > 0 && (
              <div className="glass rounded-3xl p-6">
                <h3 className="text-lg font-bold mb-4" style={{ color: "var(--text-warm)" }}>📚 已提取的课程</h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {entries.map((entry, i) => (
                    <button
                      key={i}
                      onClick={() => { setSelectedEntry(entry); setResult(entry.content); }}
                      className={`w-full text-left rounded-xl px-4 py-3 transition-all hover:scale-101 ${selectedEntry === entry ? "ring-2 ring-purple-400" : ""}`}
                      style={{ background: "rgba(255,255,255,0.5)" }}
                    >
                      <div className="font-medium text-sm truncate" style={{ color: "var(--text-warm)" }}>{entry.topic}</div>
                      <div className="text-xs truncate mt-0.5" style={{ color: "var(--text-muted)" }}>{entry.fileName} · {entry.date}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 结果展示 */}
          <div>
            {result ? (
              <div className="glass rounded-3xl p-8 h-full">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold" style={{ color: "var(--text-warm)" }}>
                    📝 {selectedEntry?.topic || topic || "课程笔记"}
                  </h3>
                  <button
                    onClick={() => navigator.clipboard.writeText(result)}
                    className="text-sm px-3 py-1 rounded-full"
                    style={{ background: "rgba(155,168,141,0.15)", color: "var(--sage-deep)" }}
                  >
                    复制
                  </button>
                </div>
                <div
                  className="text-sm leading-7 whitespace-pre-wrap overflow-y-auto"
                  style={{ color: "var(--text-warm)", maxHeight: "600px" }}
                >
                  {result}
                </div>
              </div>
            ) : (
              <div className="glass rounded-3xl p-12 text-center h-full flex flex-col items-center justify-center">
                <div className="text-6xl mb-4 float-animation">📖</div>
                <p className="text-lg font-medium mb-2" style={{ color: "var(--text-warm)" }}>知识将在这里显示</p>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>上传老师的课程视频<br />Gemini 会自动整理成结构化笔记</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
