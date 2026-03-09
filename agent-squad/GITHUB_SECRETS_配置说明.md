# 在 GitHub 上配置 Secrets（照着点就行）

先确保代码已推到 GitHub。下面是在网页上配置的完整步骤。

---

## 一、进入 Secrets 设置页

1. 打开浏览器，登录 [github.com](https://github.com)
2. 点进你的 **tarot-app 仓库**（或你放 agent-squad 的仓库）
3. 点仓库顶部的 **Settings** 标签（在 Code、Issues 旁边）
4. 左侧一栏往下滚，找到 **Secrets and variables** 这一项
5. 点开它，再点 **Actions**
6. 你会看到 "Actions secrets and variables" 页面，右上角有绿色按钮 **New repository secret**

---

## 二、添加第一个 Secret：GEMINI_API_KEY

1. 点 **New repository secret**
2. 在 **Name** 框里填（必须一模一样）：`GEMINI_API_KEY`
3. 在 **Secret** 框里粘贴你的 Gemini API Key  
   - 没有的话去 [aistudio.google.com/apikey](https://aistudio.google.com/apikey) 免费申请
4. 点 **Add secret**

---

## 三、添加第二个 Secret：EMAIL_USER

1. 再点一次 **New repository secret**
2. **Name** 填：`EMAIL_USER`
3. **Secret** 填你的发件邮箱，例如：`jiaxinshen1208@gmail.com`
4. 点 **Add secret**

---

## 四、添加第三个 Secret：EMAIL_PASS

1. 再点 **New repository secret**
2. **Name** 填：`EMAIL_PASS`
3. **Secret** 填 Gmail 的**应用专用密码**（不是登录密码）

**Gmail 应用专用密码怎么获取：**
- 打开 [myaccount.google.com](https://myaccount.google.com) → **安全**
- 确认已开启**两步验证**
- 点「应用专用密码」→ 选择「邮件」和「其他」→ 输入设备名（随便填）→ 点**生成**
- 出现 16 位密码，**去掉空格**后粘贴到 Secret 框

4. 点 **Add secret**

---

## 五、检查是否配好

在 "Actions secrets and variables" 页面，你应该能看到 3 个：

- `GEMINI_API_KEY`
- `EMAIL_USER`
- `EMAIL_PASS`

---

## 六、发一封测试邮件

1. 点仓库顶部的 **Actions** 标签
2. 左侧找到 **Daily Email Digest**，点进去
3. 右侧点 **Run workflow** → 再点 **Run workflow**
4. 等 1–2 分钟，看到绿色 ✓ 表示成功
5. 去邮箱查收三封邮件

---

## 可选：同步到网站「学习天地」

若想让每日推送同步到网站 `/study` 随时复习，再添加两个 Secret：

- Name：`SUPABASE_URL`，Secret：Supabase 项目 URL（supabase.com 创建项目后在 Settings → API 复制）
- Name：`SUPABASE_SERVICE_ROLE_KEY`，Secret：Supabase 的 service_role key（同页面）

并在 Supabase SQL Editor 执行：

```sql
create table if not exists agent_digests (date text primary key, digest jsonb not null, created_at timestamptz default now());
alter table agent_digests enable row level security;
create policy "Allow public read" on agent_digests for select using (true);
```

网站（Vercel）需配置 `NEXT_PUBLIC_SUPABASE_URL` 和 `NEXT_PUBLIC_SUPABASE_ANON_KEY`。

---

## 可选：换收件邮箱

如果想发到别的邮箱，再点 **New repository secret** 添加：

- Name：`TO_EMAIL`
- Secret：你要收邮件的地址

---

## 找不到 Settings？

- 只有仓库**所有者**能看到 Settings
- 如果是 fork 的仓库，需要在**你自己的 fork** 里配置
