# GitHub Secrets 配置说明（一步步来）

按顺序做完下面几步，每天就会自动收到邮件。

---

## 第一步：把代码推到 GitHub

1. 如果还没有 GitHub 仓库，去 [github.com/new](https://github.com/new) 新建一个
2. 在本地项目目录执行：

```bash
cd /Users/geleixizhibao/Downloads/tarot-app
git init
git add .
git commit -m "agent-squad daily email"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

---

## 第二步：添加 3 个必填的 Secrets

1. 打开你的仓库页面，点顶部的 **Settings**（设置）
2. 左侧菜单往下滑，找到 **Secrets and variables** → **Actions**
3. 点 **New repository secret**（新建仓库密钥）
4. 按下面表格，一个一个添加：

| 第几次 | Name（名称）填这个 | Secret（密钥）填什么 |
|--------|--------------------|----------------------|
| 1 | `GEMINI_API_KEY` | 你的 [Gemini API Key](https://aistudio.google.com/apikey)（一串字母数字） |
| 2 | `EMAIL_USER` | 发件邮箱，例如 `jiaxinshen1208@gmail.com` |
| 3 | `EMAIL_PASS` | Gmail 的**应用专用密码**（见下方说明） |

### Gmail 应用专用密码怎么弄？

1. 打开 [Google 账号](https://myaccount.google.com/) → **安全**
2. 开启**两步验证**（如果还没开）
3. 回到安全页，找到「应用专用密码」→ 点进去
4. 选择「邮件」和你的设备，生成密码
5. 会出现 **16 位密码**（类似 `abcd efgh ijkl mnop`）
6. **复制时去掉空格**，粘贴到 Secret 的 value 里，例如：`abcdefghijklmnop`

---

## 第三步：确认配置好了

1. 在仓库页面点顶部的 **Actions**
2. 左侧找到 **Daily Email Digest**
3. 点右边的 **Run workflow** → **Run workflow**
4. 等 1–2 分钟，如果显示绿色勾，就去邮箱查收三封邮件

---

## 可选：换收件邮箱

如果想发到别的邮箱，再添加一个 Secret：

- Name: `TO_EMAIL`
- Secret: 你要接收的邮箱地址

---

## 出问题时

- **Actions 失败**：点进去看红色错误信息，把内容发给我
- **收不到邮件**：检查 `EMAIL_PASS` 是否是应用专用密码（不是登录密码）
- **学术前沿为空**：可加 `SEMANTIC_SCHOLAR_API_KEY`（[免费申请](https://www.semanticscholar.org/product/api)）
