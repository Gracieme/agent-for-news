# 每日一句日语

网站的「🇯🇵 每日一句日语」栏目由 `.github/workflows/japanese-daily.yml`
每天奥克兰时间早上 8:00 开始生成（定时任务可能有排队延迟，自动适应夏令时）。
N5/N4 隔日轮换，每个等级轮换 10 个基础句型，并避开最近 60 句。

- 内容：`gemini-3.8-flash`；两轮生成/校对，结构校验通过后才合成音频。
- 音频首选：Google Cloud **Chirp 3 HD**，默认日语女声 `ja-JP-Chirp3-HD-Aoede`。同一音色分别以原生 `speakingRate=1.0` 和 `0.75` 合成正常、慢速 WAV。
- 内容密钥：沿用 Actions secret `GEMINI_API_KEY`，不发送到浏览器。
- Cloud TTS 密钥：优先使用 Actions secret `GOOGLE_CLOUD_TTS_API_KEY`；未设置时尝试现有 `GEMINI_API_KEY`，前提是该密钥的 Cloud 项目已启用 Cloud Text-to-Speech API、具备所需计费配置且允许该 API。Gemini API 可用不代表 Cloud TTS 已启用。
- 启用 API：[Google Cloud Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)。需要专用密钥时在 GitHub Actions secrets 添加 `GOOGLE_CLOUD_TTS_API_KEY`。
- 音色变量：`GOOGLE_CHIRP_VOICE`，必须为 `ja-JP-Chirp3-HD-*`。内容模型变量：`JAPANESE_MODEL`；备用语音模型：`JAPANESE_TTS_MODEL`。
- 调用失败时保留已发布音频，必要时使用 Gemini TTS 备用。日志记录失败原因；仅成功合成并验证两版音频后才将来源标记为 Chirp 3 HD。
- 配好 Cloud TTS 后，手动运行 `Daily Japanese + Publish Site` 即可替换当日音频，无需重新生成句子。音频哈希用于刷新缓存。无需 ElevenLabs 账户或密钥，也无需 ffmpeg。
- 原始课程档案：`docs/japanese/YYYY-MM-DD.json`。
- 日报内容：`docs/data/YYYY-MM-DD.json` 的 `japanese` 字段。
- 音频：`docs/audio/YYYY-MM-DD-japanese-{normal,slow}.wav`。

首次推送生成器改动时会自动生成当日内容；手动运行工作流可指定 `target_date` 回填。
重复运行会复用已校对课程和音频。慢速音频必须比正常版至少长 10%；两版都有效后才更新公开日报。
等级为教学参考；模型校对不能替代人工日语教师审定。

与主日报工作流共享并发组，避免生成档案互相覆盖。主日报保存时保留日语字段。
日语工作流只更新网站，不发送邮件。

离线验证：

```sh
python3 -m unittest discover -s projects/agent-squad-python/tests -p test_japanese_daily.py -v
```

本地生成（需环境变量 `GEMINI_API_KEY`）：

```sh
python3 projects/agent-squad-python/japanese_daily.py
```
