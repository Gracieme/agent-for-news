"use client";

const SECTION_HEADERS = ["整体能量", "逐牌解读", "综合洞见", "给你的指引"];

function cleanText(t: string): string {
  return t
    .replace(/\*\*/g, "")   // 粗体
    .replace(/\*/g, "")     // 斜体
    .replace(/^#{1,6}\s*/gm, "")  // 标题符号
    .replace(/_{1,2}([^_]+)_{1,2}/g, "$1")  // 下划线
    .replace(/`/g, "")      // 代码块
    .trim();
}

/** 解析并渲染解读内容 - 纯文字，无符号 */
export default function InterpretationContent({ text }: { text: string }) {
  if (!text?.trim()) return null;

  const cleaned = cleanText(text);
  const blocks = cleaned.split(/\n\n+/).filter((b) => b.trim());
  const items: { type: "header" | "body"; content: string }[] = [];

  for (const block of blocks) {
    const trimmed = block.trim();
    const isHeader =
      trimmed.split("\n").length === 1 &&
      (SECTION_HEADERS.includes(trimmed) || (trimmed.length <= 12 && !trimmed.endsWith("。")));
    if (isHeader) {
      items.push({ type: "header", content: trimmed });
    } else {
      items.push({ type: "body", content: trimmed });
    }
  }

  return (
    <div className="interpretation-content space-y-5">
      {items.map((item, i) =>
        item.type === "header" ? (
          <h3
            key={i}
            className="text-base font-semibold pt-4 first:pt-0 first:mt-0 mt-6"
            style={{ color: "var(--text-warm)" }}
          >
            {item.content}
          </h3>
        ) : (
          <div
            key={i}
            className="text-[15px] leading-[1.85]"
            style={{ color: "var(--text-warm)" }}
          >
            {item.content.split("\n").map((para, j) => (
              <p key={j} className="mb-3 last:mb-0">
                {cleanText(para)}
              </p>
            ))}
          </div>
        )
      )}
    </div>
  );
}
