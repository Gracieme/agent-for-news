# Agent 小队

三个每日推送助手：**英语学习**、**美妆学习**、**科研文献**。

## 助手说明

| 助手 | 说明 |
|------|------|
| 英语学习 | 每日 10 条 C1 水平 idiom/谚语，标注流行地区（英/美/澳等），写成一段话，中英对照 |
| 美妆学习 | 针对 **冷橄榄皮 + 圆脸** 推送适合的妆容/色号/修容建议 |
| 科研文献 | 针对博士生研究方向（语言权力、课堂互动与中介、教师与制度）每日 3 篇论文，含作者、期刊、引用量、摘要、与研究的关联性。数据来自 **Semantic Scholar** + **OpenAlex**（均免费、无需 API key），先查 Semantic Scholar，结果不足时用 OpenAlex 补充并去重。 |

---

## 通过这个办法让 Agent 给你发邮件

按下面做一次，之后每次运行（或定时任务）都会把当日推送发到你邮箱。

### 1. 复制并编辑环境变量

```bash
cd agent-squad
cp .env.example .env
```

用编辑器打开 `agent-squad/.env`，**必填**三项：

| 变量 | 填什么 |
|------|--------|
| `GEMINI_API_KEY` | 你的 Gemini API Key |
| `EMAIL_USER` | 发件邮箱，例如 `jiaxinshen1208@gmail.com` |
| `EMAIL_PASS` | Gmail 的**应用专用密码**（16 位，**连在一起写，不要空格**） |

> Gmail 应用专用密码：Google 账号 → 安全 → 两步验证 → 应用专用密码，生成后把 4 组字母连成一行填到 `EMAIL_PASS=` 后面。**不要**把密码发到任何聊天或代码里。

收件邮箱默认就是 `config.mjs` 里的 `jiaxinshen1208@gmail.com`；要发到别的邮箱时，在 `.env` 里加一行 `TO_EMAIL=你的邮箱`。

### 2. 安装依赖（只需一次）

```bash
cd agent-squad
npm install
```

### 3. 发一封测试邮件

```bash
cd agent-squad
npm run run-once
```

脚本会跑三个 Agent，生成当日内容，然后**自动发一封彩色 HTML 邮件**到你邮箱。主题类似：`Agent 小队 · 每日推送 · 2025-xx-xx`。

若提示「未配置 EMAIL_USER/EMAIL_PASS」，说明 `.env` 里没填对或没生效，检查后重试。若提示「发送邮件失败」，多半是 `EMAIL_PASS` 错误或未用应用专用密码。

### 4. 每天自动发（推荐：零运维）

**方式 A：GitHub Actions（推荐，无需开电脑）**

把代码推送到 GitHub 后，在仓库 **Settings → Secrets and variables → Actions** 中添加：

| Secret 名称 | 必填 | 说明 |
|-------------|------|------|
| `GEMINI_API_KEY` | ✓ | 你的 Gemini API Key |
| `EMAIL_USER` | ✓ | 发件邮箱 |
| `EMAIL_PASS` | ✓ | Gmail 应用专用密码（16 位连写） |
| `TO_EMAIL` | 可选 | 收件邮箱，不填则用 config 默认 |
| `SEMANTIC_SCHOLAR_API_KEY` | 可选 | 学术检索可申请免费 key |

配置好后，GitHub 会每天 **丹佛时间 8:00** 自动运行并发邮件，你什么都不用做。

也可在 **Actions** 页手动点 **Run workflow** 立即发一封。

---

**方式 B：本地常开电脑**

在常开的电脑或服务器上：

```bash
cd agent-squad
npm start
```

会按**丹佛时间每天早上 8:00** 自动执行一次并发邮件。

---

## 环境变量一览

- `GEMINI_API_KEY`（必填）：生成英语、美妆、文献关联性
- `EMAIL_USER`、`EMAIL_PASS`（发邮件必填）：发件邮箱与 Gmail 应用专用密码
- `TO_EMAIL`（可选）：收件邮箱，不填则用 config 里默认
- `SEMANTIC_SCHOLAR_API_KEY`（可选）：若科研文献一直「今日暂无匹配文献」且日志里 Semantic Scholar 403，可到 [Semantic Scholar API](https://www.semanticscholar.org/product/api) 申请免费 key 填上
- `OPENALEX_API_KEY`（可选）：[OpenAlex](https://openalex.org/settings/api) 免费 key，提高文献检索成功率
- `SUPABASE_URL`、`SUPABASE_SERVICE_ROLE_KEY`（可选）：同步到 Supabase 以便网页查看

## 安装与运行

```bash
cd agent-squad
npm install
npm run run-once   # 执行一次并发邮件（需先配置 .env）
```

## 定时任务

每天**丹佛时间 8:00** 自动运行并发邮件：

```bash
npm start
# 或: node --env-file=.env scheduler.mjs
```

## 在网页中查看（可选）

1. 在 Supabase 中创建表：

```sql
create table if not exists agent_digests (
  date text primary key,
  digest jsonb not null,
  created_at timestamptz default now()
);

-- 若需匿名只读（供 Next 前端拉取），可对 agent_digests 启用 RLS 并允许 select
alter table agent_digests enable row level security;
create policy "Allow public read" on agent_digests for select using (true);
```

2. 在 `agent-squad/.env` 中配置 `SUPABASE_URL` 与 `SUPABASE_SERVICE_ROLE_KEY`，运行 `npm run run-once` 后数据会写入 Supabase。
3. 在 Next 应用中打开 `/agents` 页面即可查看最新一日推送（需在 Next 项目中配置 `NEXT_PUBLIC_SUPABASE_URL` 与 `NEXT_PUBLIC_SUPABASE_ANON_KEY`）。
