import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "格雷西的塔罗驿站 · 宇宙的指引",
  description: "用AI的智慧解读塔罗，探索内心深处的声音",
};

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

function ConfigHint() {
  return (
    <div style={{
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
        <p style={{ fontSize: 14, lineHeight: 1.6 }}>
          请在 Vercel 项目 Settings → Environment Variables 中配置：
        </p>
        <ul style={{ textAlign: "left", margin: "16px 0", paddingLeft: 20 }}>
          <li><code>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code></li>
          <li><code>CLERK_SECRET_KEY</code></li>
          <li><code>GEMINI_API_KEY</code></li>
        </ul>
        <p style={{ fontSize: 12, color: "#888" }}>
          配置后重新部署即可使用
        </p>
      </div>
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh">
      <body className="antialiased">
        {publishableKey ? (
          <ClerkProvider publishableKey={publishableKey}>
            {children}
          </ClerkProvider>
        ) : (
          <ConfigHint />
        )}
      </body>
    </html>
  );
}
