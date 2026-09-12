# 每日学习邮件与网站

`daily_email.py` 使用 OpenAI Responses API 生成学习内容和新闻翻译，默认模型为 `gpt-5-mini`。

## GitHub Actions 配置

在仓库 Settings → Secrets and variables → Actions 添加 `OPENAI_API_KEY` secret，使用有可用额度的 OpenAI API 项目密钥。原有邮件 secrets 保持不变。

可选：添加 `OPENAI_MODEL` repository variable，选择支持 Responses API 和 `reasoning.effort=low` 的 GPT 模型。未设置时使用 `gpt-5-mini`。

配置后，在 Actions 中选择 **Daily Email + Update Site** → **Run workflow**。需要补发时填写 `target_date`（如 `2026-09-11`）；运行会发送邮件并更新网站。旧失败运行的 Re-run 使用旧提交，不能用于切换后的首次运行。

本地运行：安装 `requirements.txt`，在环境或本目录 `.env` 配置 `OPENAI_API_KEY` 和邮件参数，然后执行 `python daily_email.py`。不要提交密钥。

`agent_squad.py` 是独立的旧版终端程序，仍使用 Anthropic，因此共享依赖文件保留了 `anthropic`；每日任务不再调用它。

## 验证

```sh
python -m unittest discover -s projects/agent-squad-python/tests -v
```

测试使用 OpenAI SDK 与模拟 HTTP 响应，不消耗 API 额度或发送邮件。

接口说明：https://developers.openai.com/api/docs/guides/text
