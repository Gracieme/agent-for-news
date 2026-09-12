# 每日学习邮件与网站

`daily_email.py` 使用 Gemini API 生成每日内容。英语、科研推荐和导师带读默认使用 `gemini-3.1-pro-preview`；新闻翻译使用 `gemini-2.5-flash` 的结构化输出。英语栏目会检查最近 45 天的表达以减少重复，并通过 `gemini-2.5-pro-preview-tts` 生成 A 男声、B 女声的双人对话音频；音频随日报附上，也可在学习小屋播放。

## 运行时间

每日按奥克兰当地时间早上 8:00 启动（`Pacific/Auckland`），自动适应新西兰夏令时。邮件日期和补发日期也使用奥克兰时区；实际送达时间取决于 GitHub 排队及内容生成耗时。

## GitHub Actions 配置

在仓库 Settings → Secrets and variables → Actions 添加 `GEMINI_API_KEY` secret。原有邮件 secrets 保持不变。

可选：添加 `GEMINI_MODEL` repository variable。未设置时使用 `gemini-3.1-pro-preview`。新闻翻译可通过 `GEMINI_NEWS_MODEL` 单独覆盖，默认使用 `gemini-2.5-flash`。

可选：添加 `GEMINI_TTS_MODEL` repository variable 来覆盖语音模型，默认使用质量更高的 `gemini-2.5-pro-preview-tts`（需启用 Gemini API 付费层）。

配置后，在 Actions 中选择 **Daily Email + Update Site** → **Run workflow**。需要补发时填写 `target_date`（如 `2026-09-11`）；运行会发送邮件并更新网站。旧失败运行的 Re-run 使用旧提交，不能用于切换后的首次运行。

本地运行：安装 `requirements.txt`，在环境或本目录 `.env` 配置 `GEMINI_API_KEY` 和邮件参数，然后执行 `python daily_email.py`。不要提交密钥。

`agent_squad.py` 是独立的旧版终端程序，仍使用 Anthropic，因此共享依赖文件保留了 `anthropic`；每日任务不再调用它。

## 验证

```sh
python -m unittest discover -s projects/agent-squad-python/tests -v
```

测试使用模拟 Gemini 响应，不消耗 API 额度或发送邮件。

接口说明：https://ai.google.dev/gemini-api/docs/generate-content/text-generation
