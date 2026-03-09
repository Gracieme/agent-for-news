# 格雷西的塔罗驿站

塔罗占卜网站，支持牌阵选牌、AI 解读、历史记录与视频知识库增强。

## 本地开发

1. 复制 `.env.example` 为 `.env.local`，填写 API Key
2. 安装依赖：`npm install`
3. 启动：`npm run dev`
4. 访问 [http://localhost:3000](http://localhost:3000)

## 部署到 Vercel

**方式一：命令行（推荐）**

1. 登录：`npx vercel login`（会打开浏览器）
2. 部署预览：`npm run deploy`  
   正式上线：`npm run deploy:prod`
3. 首次部署后，在 [Vercel Dashboard](https://vercel.com/dashboard) 找到项目 → Settings → Environment Variables，添加：
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `GEMINI_API_KEY`
4. 在 [Clerk Dashboard](https://dashboard.clerk.com) → 你的应用 → Paths，把生产域名加入 Sign-in/Sign-up 的 Redirect URLs（如 `https://你的项目.vercel.app/`），否则登录后会跳转失败。
5. 若首页显示「请配置环境变量」，说明上述三项未填或未生效，补全后点 Redeploy 重新部署。

**方式二：GitHub + Vercel 控制台**

1. 推送到 GitHub，在 [vercel.com/new](https://vercel.com/new) 导入项目
2. 在 Vercel 项目 → Settings → Environment Variables 中配置：
   - `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`
   - `CLERK_SECRET_KEY`
   - `GEMINI_API_KEY`
   - （可选）`NEXT_PUBLIC_SUPABASE_URL`、`NEXT_PUBLIC_SUPABASE_ANON_KEY`
3. 如需保存历史，在 Supabase SQL 编辑器中执行 `supabase-setup.sql`
4. 如需使用视频/教材知识库：本地运行 `npm run ingest-videos <视频文件夹>` 或 `npm run ingest-pdfs <PDF路径1> [PDF路径2] ...`，提交 `data/video-knowledge.json` 后再部署

## 环境变量说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `NEXT_PUBLIC_CLERK_*`、`CLERK_SECRET_KEY` | 是 | Clerk 登录 |
| `GEMINI_API_KEY` | 是 | 解读与知识提取 |
| `NEXT_PUBLIC_SUPABASE_*` | 否 | 不填则历史不保存 |
