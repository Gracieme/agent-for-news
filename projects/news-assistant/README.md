# 新闻总结助手

每天早 8:00、晚 18:00（**丹佛时间 America/Denver**）各向您的邮箱发送 **10 条**新闻摘要，涵盖：**科技、军事、财经、政治、娱乐、民生**。

收件邮箱默认：`jiaxinshen1208@gmail.com`（可在 `.env` 中修改 `TO_EMAIL`）。

---

## 1. 安装依赖

```bash
cd news-assistant
npm install
```

## 2. 配置环境变量

复制示例并填写：

```bash
cp .env.example .env
```

编辑 `.env`：

| 变量 | 说明 |
|------|------|
| **GNEWS_API_KEY** | 必填。到 [GNews](https://gnews.io/) 免费注册，在 Dashboard 复制 API Key。免费版约 100 次/天，早晚各 1 次足够。 |
| **EMAIL_USER** | 必填。发件邮箱（如 Gmail 地址）。 |
| **EMAIL_PASS** | 必填。Gmail 需使用 [应用专用密码](https://support.google.com/accounts/answer/185833)：谷歌账号 → 安全 → 两步验证 → 应用专用密码。 |
| **TO_EMAIL** | 可选。收件邮箱，不填则使用默认 `jiaxinshen1208@gmail.com`。 |
| **GEMINI_API_KEY** | 可选。若填写，则会调用 Gemini，把每条新闻的摘要翻译为简短中文（标题保留英文），实现“标题英文，内容中文”。若不填，则摘要为英文。 |

## 3. 测试一次发送

确认配置无误后，先手动跑一次：

```bash
node --env-file=.env run-once.mjs morning
```

或：

```bash
npm run run-once
```

检查邮箱是否收到「【早报】今日新闻摘要」邮件。

## 4. 启动定时任务

在 **本机或服务器** 上长期运行（需 24 小时不关机的环境）：

```bash
node --env-file=.env scheduler.mjs
```

或：

```bash
npm start
```

程序会按 **丹佛时间 America/Denver** 每天 8:00、18:00 各执行一次拉取并发信。保持终端不关闭即可。

---

## 使用系统 Cron（可选）

若不想常驻进程，可用系统 cron 在 8:00、18:00（丹佛时间）各执行一次：

```bash
# 编辑 crontab
crontab -e

# 添加（请把 /path/to/tarot-app 换成实际路径）：
0 8 * * * cd /path/to/tarot-app/news-assistant && node --env-file=.env run-once.mjs morning
0 18 * * * cd /path/to/tarot-app/news-assistant && node --env-file=.env run-once.mjs evening
```

确保服务器或本机时区为 `America/Denver`，或已在 crontab 中设置 `TZ=America/Denver`。

---

## 脚本说明

| 命令 | 说明 |
|------|------|
| `npm start` | 启动定时器，每天 8:00、18:00 自动发信。 |
| `npm run run-once` | 立即执行一次（早报）。可加参数：`node run-once.mjs evening` 发晚间报。 |
| `npm run fetch` | 仅拉取新闻并打印到控制台，用于检查 GNews API 是否正常。 |

---

## 新闻来源与分类

- 新闻数据来自 [GNews API](https://gnews.io/)，按分类拉取头条后合并、去重，取最新 10 条。
- 分类对应：科技(technology)、军事/国际(world)、财经(business)、政治(nation)、娱乐(entertainment)、民生(health)。

如需改收件邮箱、分类或条数，可修改 `config.mjs`。
