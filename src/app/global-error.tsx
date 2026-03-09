"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="zh">
      <body style={{
        margin: 0,
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        background: "linear-gradient(160deg, #FCFAF6 0%, #F8F5F0 100%)",
        color: "#5c6b4f",
        fontFamily: "system-ui, sans-serif",
        textAlign: "center",
      }}>
        <div style={{ maxWidth: 420 }}>
          <p style={{ fontSize: 28, marginBottom: 16 }}>☽ 格雷西的塔罗驿站</p>
          <p style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 16 }}>
            页面暂时出错，请检查 Vercel 环境变量是否已配置并重新部署。
          </p>
          <p style={{ fontSize: 12, color: "#888", marginBottom: 24 }}>
            需配置：NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY、CLERK_SECRET_KEY、GEMINI_API_KEY
          </p>
          <button
            type="button"
            onClick={() => reset()}
            style={{
              padding: "10px 20px",
              borderRadius: 9999,
              border: "none",
              background: "#6B7A5D",
              color: "#fff",
              fontSize: 14,
              cursor: "pointer",
            }}
          >
            重试
          </button>
        </div>
      </body>
    </html>
  );
}
