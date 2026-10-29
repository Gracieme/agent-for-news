#!/usr/bin/env python3
"""Generate and publish one reviewed beginner Japanese sentence per Auckland day.

Uses Gemini and Google Cloud Text-to-Speech REST APIs; the English SDK integration stays independent.
No email is sent by this job. Credentials come only from the environment.
"""
import base64
import hashlib
import html
import io
import json
import os
import re
import time
import urllib.error
import urllib.request
import wave
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from build_site import DATA_DIR, WEBSITE_DIR, rebuild
from japanese_voice import generate_pair as chirp_audio_pair

TEXT_MODEL = os.environ.get("JAPANESE_MODEL", "gemini-3.8-flash")
TTS_MODEL = os.environ.get("JAPANESE_TTS_MODEL", "gemini-3.8-flash-tts")
LESSON_DIR = WEBSITE_DIR / "japanese"
TOPICS = {
    "N5": ["～が好きです", "～に行きます", "～で～を食べます", "～ませんか", "～たいです", "～てください", "～てもいいですか", "～があります", "～から～まで", "～ましょう"],
    "N4": ["～たことがあります", "～たり～たりします", "～なければなりません", "～と思います", "～ようにしています", "～たほうがいいです", "～ながら", "～ので", "～てから", "～つもりです"],
}


def api_post(endpoint, payload):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is required")
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/" + endpoint,
        data=json.dumps(payload).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            # Google error bodies contain diagnostics, never the request header/key.
            detail = exc.read().decode("utf-8", errors="replace")[:1500]
            if exc.code in (408, 429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"Gemini {endpoint}: HTTP {exc.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise RuntimeError("Gemini request timed out or connection failed") from None
            time.sleep(10 * (attempt + 1))


def generate_json(prompt):
    result = api_post(f"models/{TEXT_MODEL}:generateContent", {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 6000},
    })
    candidates = result.get("candidates", [])
    if not candidates or candidates[0].get("finishReason") != "STOP":
        raise ValueError("Japanese generation incomplete or blocked")
    raw = "".join(p.get("text", "") for p in candidates[0].get("content", {}).get("parts", []) if not p.get("thought"))
    return json.loads(raw)


def lesson_plan(day):
    level = "N5" if day.toordinal() % 2 == 0 else "N4"
    targets = TOPICS[level]
    return level, targets[(day.toordinal() // 2) % len(targets)]


def validate_lesson(lesson, level, target):
    if not isinstance(lesson, dict):
        raise ValueError("Lesson must be a JSON object")
    for field in ("sentence", "kana", "translation", "scene", "structure", "grammar", "practice", "practice_answer"):
        if not isinstance(lesson.get(field), str) or not lesson[field].strip():
            raise ValueError(f"Missing Japanese lesson field: {field}")
    if lesson.get("level") != level or lesson.get("target") != target:
        raise ValueError("Lesson level or target differs from today's plan")
    sentence = lesson["sentence"]
    if not 5 <= len(sentence) <= 70 or not re.fullmatch(r"[^。！？!?\n]+[。！？]", sentence):
        raise ValueError("Expected exactly one short Japanese sentence")
    if not re.fullmatch(r"[\u3040-\u30ffー、。！？\s]+", lesson["kana"]):
        raise ValueError("Kana reading must not contain kanji or Latin characters")
    tokens = lesson.get("tokens")
    if not isinstance(tokens, list) or not tokens:
        raise ValueError("Missing ruby tokens")
    for token in tokens:
        if not isinstance(token, dict) or not isinstance(token.get("text"), str) or not token["text"]:
            raise ValueError("Malformed ruby token")
        reading = token.get("reading", "")
        if not isinstance(reading, str) or (reading and not re.fullmatch(r"[\u3040-\u30ffー]+", reading)):
            raise ValueError("Invalid ruby reading")
        if re.search(r"[\u4e00-\u9fff]", token["text"]) and not reading:
            raise ValueError("Every kanji token needs a kana reading")
    if "".join(t["text"] for t in tokens) != sentence:
        raise ValueError("Ruby tokens must reconstruct the exact sentence")
    vocabulary = lesson.get("vocabulary")
    if not isinstance(vocabulary, list) or not 2 <= len(vocabulary) <= 8:
        raise ValueError("Expected 2–8 vocabulary items")
    for item in vocabulary:
        if not isinstance(item, dict) or any(not isinstance(item.get(k), str) or not item[k].strip() for k in ("word", "reading", "meaning")):
            raise ValueError("Incomplete vocabulary item")
    return lesson


def recent_sentences(day):
    lessons = []
    for path in sorted(LESSON_DIR.glob("*.json"), reverse=True):
        if path.stem >= day.isoformat():
            continue
        lesson = json.loads(path.read_text(encoding="utf-8"))
        lessons.append(lesson["sentence"])
        if len(lessons) >= 60:
            break
    return lessons


def gen_lesson(day):
    level, target = lesson_plan(day)
    recent = recent_sentences(day)
    prompt = f"""你是一位严谨的日语初级教师，为中文学习者生成每日一句。
日期 {day}；教学参考等级 {level}；今日唯一重点句型 {target}。
句子自然、适合生活使用，日文5–70字符，只写一句。N5用基础词汇和简单句；N4只引入一个主要新语法点，其他词汇尽量N5。
避免复杂从句、商务敬语、文学表达和难词。JLPT等级是教学参考，不声称来自官方词表。
不重复这些旧句子：{json.dumps(recent, ensure_ascii=False)}。
输出JSON对象，不要Markdown：
{{"level":"{level}","target":"{target}","scene":"中文生活场景",
"sentence":"一句日文，含句末标点", "kana":"全句假名，保留助词は/へ/を的拼写",
"tokens":[{{"text":"句子连续片段","reading":"该片段的假名读音；纯假名或标点可用空字符串"}}],
"translation":"自然准确的中文翻译",
"structure":"按原句顺序拆分，用中文标明主语/时间/宾语/谓语等，并解释省略部分",
"grammar":"中文150–250字：解释每个助词的作用、重点句型的接续和含义；涉及变形时写出原形→中间步骤→句中形式，避免只解释整句意思",
"vocabulary":[{{"word":"句中词汇","reading":"假名","meaning":"中文词义与词性"}}],
"practice":"一道中文提示的替换造句题，只用本日句型", "practice_answer":"日语参考答案及假名和中文"}}
tokens拼接必须与sentence逐字相同，所有汉字必须有准确读音；vocabulary列2–8项。
"""
    last_error = ""
    for _ in range(3):
        try:
            lesson = validate_lesson(generate_json(prompt + "\n上次需修正：" + last_error), level, target)
            if lesson["sentence"] in recent:
                raise ValueError("Sentence repeats recent content")
            review = generate_json(
                "请作为第二轮日语教师校对，检查以下JSON的日语自然度、所有假名读音、翻译、助词、动词变形、接续、练习答案及难度。"
                f"目标是{level}，重点{target}。如有任何事实错误或明显超纲，输出"
                '{"approved":false,"issues":"中文问题列表"}；全部正确才输出{"approved":true,"issues":""}。\n'
                + json.dumps(lesson, ensure_ascii=False)
            )
            if review.get("approved") is not True:
                raise ValueError(str(review.get("issues", "Review failed")))
            lesson.update(date=day.isoformat(), text_model=TEXT_MODEL, tts_model=TTS_MODEL)
            return lesson
        except (ValueError, KeyError, TypeError) as exc:
            last_error = str(exc)
    raise RuntimeError("Japanese lesson failed validation: " + last_error)


def validate_wav(data):
    with wave.open(io.BytesIO(data), "rb") as audio:
        duration = audio.getnframes() / audio.getframerate()
        if not 0.5 <= duration <= 90 or audio.getnchannels() != 1 or audio.getsampwidth() != 2:
            raise ValueError("Unexpected Japanese TTS WAV format or duration")
        return duration


def gen_audio(sentence, slow=False):
    style = (
        "標準的な日本語の発音で、初級学習者向けに普段の約70パーセントの速度でゆっくり読む。単語の間に短い間を置き、自然な高低アクセントを保つ。"
        if slow else "標準的な日本語の発音と自然な高低アクセントで、明瞭な日常会話の普通の速さで読む。"
    )
    result = api_post("interactions", {
        "model": TTS_MODEL,
        "input": [{"type": "user_input", "content": [{"type": "text", "text": sentence,
            "annotations": [{"type": "speech_metadata", "style": style}]}]}],
        "response_format": {"type": "audio", "mime_type": "audio/wav", "sample_rate": 24000},
        "generation_config": {"speech_config": [{"voice": "Kore"}]},
    })
    # output_audio is an SDK convenience property, not a raw REST field.
    audio_blocks = [content for step in result.get("steps", [])
                    if step.get("type") == "model_output"
                    for content in step.get("content", []) if content.get("type") == "audio"]
    encoded = audio_blocks[-1].get("data") if audio_blocks else None
    if not encoded:
        raise RuntimeError("Japanese TTS returned no audio")
    data = base64.b64decode(encoded, validate=True)
    validate_wav(data)
    return data


def render_lesson(lesson):
    esc = html.escape
    day = date.fromisoformat(lesson["date"]).isoformat()
    revision = "?v=" + esc(str(lesson["audio_revision"]), quote=True) if lesson.get("audio_revision") else ""
    ruby = "".join(
        f'<ruby>{esc(t["text"])}<rp>（</rp><rt>{esc(t["reading"])}</rt><rp>）</rp></ruby>'
        if t.get("reading") else esc(t["text"]) for t in lesson["tokens"]
    )
    vocab = "".join(f'<tr><td lang="ja">{esc(v["word"])}</td><td lang="ja">{esc(v["reading"])}</td><td>{esc(v["meaning"])}</td></tr>' for v in lesson["vocabulary"])
    players = "".join(
        f'<div class="jp-player"><label for="jp-{speed}">{label}</label>'
        f'<audio id="jp-{speed}" controls preload="none" aria-label="{label}"><source src="audio/{day}-japanese-{speed}.wav{revision}" type="audio/wav"></audio>'
        f'<label class="jp-loop"><input type="checkbox" data-jp-loop="jp-{speed}"> 循环跟读</label></div>'
        for speed, label in (("normal", "正常语速"), ("slow", "慢速跟读"))
    )
    return f'''<article class="jp-lesson">
<div class="jp-eyebrow">每日一句 · {esc(lesson['level'])} · {day}</div>
<h2>🇯🇵 今天，学会一句日语</h2><p class="jp-scene">{esc(lesson['scene'])}</p>
<div class="jp-sentence" lang="ja">{ruby}</div>
<p class="jp-kana" lang="ja">{esc(lesson['kana'])}</p>
<p class="jp-translation">{esc(lesson['translation'])}</p>
<div class="jp-audio">{players}</div>
<section><h3>🧩 中文语法拆解 · <span lang="ja">{esc(lesson['target'])}</span></h3>
<p class="jp-structure">{esc(lesson['structure'])}</p><p>{esc(lesson['grammar'])}</p></section>
<section><h3>📖 句中词汇</h3><div class="jp-table"><table><thead><tr><th>日语</th><th>假名</th><th>中文与词性</th></tr></thead><tbody>{vocab}</tbody></table></div></section>
<section><h3>✏️ 试着说一句</h3><p>{esc(lesson['practice'])}</p>
<details><summary>查看参考答案</summary><p>{esc(lesson['practice_answer'])}</p></details></section>
<p class="jp-note">N5 / N4 隔日交替 · 等级为教学参考 · 每天奥克兰时间早上 8 点开始更新</p>
</article>'''


def publish_lesson(day):
    """Reuse complete daily artifacts on reruns, then merge into the daily archive."""
    LESSON_DIR.mkdir(parents=True, exist_ok=True)
    path = LESSON_DIR / f"{day}.json"
    level, target = lesson_plan(day)
    lesson = validate_lesson(json.loads(path.read_text(encoding="utf-8")), level, target) if path.exists() else gen_lesson(day)
    # Persist the approved transcript before synthesis: retries must never reuse
    # an audio file belonging to a newly regenerated, different sentence.
    path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    audio_dir = WEBSITE_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_paths = [audio_dir / f"{day}-japanese-{speed}.wav" for speed in ("normal", "slow")]
    cloud_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    desired_model = "chirp-3-hd"
    desired_voice = os.environ.get("GOOGLE_CHIRP_VOICE", "").strip() or "ja-JP-Chirp3-HD-Aoede"
    needs_upgrade = (lesson.get("tts_provider") != "google-cloud" or lesson.get("tts_model") != desired_model
                     or (desired_voice and lesson.get("tts_voice_id") != desired_voice)
                     or not all(p.exists() for p in audio_paths))
    if cloud_credentials and needs_upgrade:
        try:
            normal, slow, metadata = chirp_audio_pair(lesson["sentence"])
            if validate_wav(slow) < validate_wav(normal) * 1.1:
                raise ValueError("Google Chirp 3 HD slow track is not measurably slower")
            # Both versions must validate before replacing a working pair.
            for output, data in zip(audio_paths, (normal, slow)):
                output.write_bytes(data)
            lesson.update(metadata)
            lesson["audio_revision"] = hashlib.sha256(normal + slow).hexdigest()[:12]
            print("Japanese audio upgraded to " + desired_voice)
        except (RuntimeError, ValueError, wave.Error, EOFError) as exc:
            print(f"::warning::Google Chirp 3 HD unavailable; retaining working audio / using Gemini fallback. {exc}")
    elif not cloud_credentials:
        print("::warning::Chirp 3 HD needs Google Cloud OAuth credentials (GOOGLE_CLOUD_TTS_CREDENTIALS Actions secret); retaining existing audio / Gemini fallback.")
    if lesson.get("tts_provider") == "google-cloud" and not all(p.exists() for p in audio_paths):
        # If a historical Google Chirp 3 HD pair is damaged and cannot be regenerated,
        # replace both tracks together rather than mixing speakers/providers.
        normal, slow = gen_audio(lesson["sentence"]), gen_audio(lesson["sentence"], slow=True)
        if validate_wav(slow) < validate_wav(normal) * 1.1:
            raise RuntimeError("Fallback audio pair failed speed validation")
        for output, data in zip(audio_paths, (normal, slow)):
            output.write_bytes(data)
        lesson.update(tts_provider="gemini", tts_model=TTS_MODEL)
        lesson.pop("tts_voice_id", None)
        lesson.pop("slow_method", None)
        lesson["audio_revision"] = hashlib.sha256(normal + slow).hexdigest()[:12]
    durations = {}
    for speed in ("normal", "slow"):
        audio_path = audio_dir / f"{day}-japanese-{speed}.wav"
        data = audio_path.read_bytes() if audio_path.exists() else gen_audio(lesson["sentence"], slow=speed == "slow")
        durations[speed] = validate_wav(data)
        if not audio_path.exists():
            audio_path.write_bytes(data)
    if durations["slow"] < durations["normal"] * 1.1:
        # Retry the slow performance once; do not publish mislabeled normal-speed audio.
        data = gen_audio(lesson["sentence"], slow=True)
        if validate_wav(data) < durations["normal"] * 1.1:
            raise RuntimeError("Slow Japanese audio is not measurably slower; publication stopped")
        (audio_dir / f"{day}-japanese-slow.wav").write_bytes(data)
        durations["slow"] = validate_wav(data)
    path.write_text(json.dumps(lesson, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entry_path = DATA_DIR / f"{day}.json"
    entry = json.loads(entry_path.read_text(encoding="utf-8")) if entry_path.exists() else {
        "date_key": day.isoformat(), "date_cn": day.strftime("%Y年%m月%d日"),
        "day_cn": ("周一", "周二", "周三", "周四", "周五", "周六", "周日")[day.weekday()],
    }
    entry["japanese"] = render_lesson(lesson)
    entry_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rebuild()
    print(f"Published Japanese {day} ({level}); normal={durations['normal']:.1f}s; slow={durations['slow']:.1f}s")


if __name__ == "__main__":
    target = os.environ.get("TARGET_DATE", "").strip()
    day = date.fromisoformat(target) if target else datetime.now(ZoneInfo("Pacific/Auckland")).date()
    publish_lesson(day)
