# 每日一句日语

网站的「🇯🇵 每日一句日语」栏目由 `.github/workflows/japanese-daily.yml`
每天奥克兰时间早上 8:00 开始生成（定时任务可能有排队延迟，自动适应夏令时）。
N5/N4 隔日轮换，每个等级轮换 10 个基础句型，并避开最近 60 句。

- 内容：`gemini-3.8-flash`；两轮生成/校对，结构校验通过后才合成音频。
- 音频：`gemini-3.8-flash-tts`；同一句原文、同一声音，分别合成正常和慢速版。
- 密钥：沿用 Actions secret `GEMINI_API_KEY`，不发送到浏览器。
- 覆盖模型：Actions repository variables `JAPANESE_MODEL`、`JAPANESE_TTS_MODEL`。
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
