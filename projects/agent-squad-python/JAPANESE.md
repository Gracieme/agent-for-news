# 每日一句日语

网站的「🇯🇵 每日一句日语」栏目由 `.github/workflows/japanese-daily.yml`
每天奥克兰时间早上 8:00 开始生成（定时任务可能有排队延迟，自动适应夏令时）。
N5/N4 隔日轮换，每个等级轮换 10 个基础句型，并避开最近 60 句。

- 内容：`gemini-3.8-flash`；两轮生成/校对，结构校验通过后才合成音频。
- 音频首选：Google Cloud **Chirp 3 HD**，默认日语女声 `ja-JP-Chirp3-HD-Aoede`。同一音色分别以原生 `speakingRate=1.0` 和 `0.75` 合成正常、慢速 WAV。
- 内容密钥：沿用 Actions secret `GEMINI_API_KEY`，不发送到浏览器。
- Cloud TTS 使用 OAuth 身份认证，不能复用 Gemini API Key。GitHub Actions 通过 **Workload Identity Federation + 服务账号**获取短期凭据，不创建服务账号 JSON 密钥，不修改组织的禁用密钥政策。
- 一次性 Cloud 端配置脚本：`scripts/setup-japanese-wif.sh`，在 Google Cloud Shell 中由项目管理员运行。它为现有 `jp-tts` 服务账号创建专用身份池和 GitHub OIDC provider，限制仓库数字 ID、所有者数字 ID、main 分支及日语工作流路径。仅授予 `roles/iam.workloadIdentityUser` 和服务使用者角色；不授予 Owner、Editor 或管理员角色。重新运行时校验已有 provider，不自动扩大信任。
- 脚本启用 Cloud Text-to-Speech、IAM、STS、IAM Credentials API。项目计费必须按 Google Cloud 要求启用；脚本不会创建或更改计费账户。
- 脚本完成后，将输出的三项非秘密配置保存为 GitHub repository variables：`GOOGLE_CLOUD_PROJECT`、`GOOGLE_CLOUD_SERVICE_ACCOUNT`、`GOOGLE_CLOUD_WIF_PROVIDER`。工作流只在 provider 与服务账号都配置时尝试 Cloud 认证；ADC 临时凭据文件由官方 auth action 自动清理。
- 缺少 Cloud 端管理权限或组织禁止创建身份池时，请让项目/组织管理员执行脚本，不关闭组织安全政策。
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
