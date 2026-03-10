#!/usr/bin/env python3
"""从塔罗课件PDF提取知识，使用 REST API"""
import os
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

GEMINI_API_KEY = "AIzaSyCPFK-FsxIJKEpT3IOGBq5qlkURIF80gps"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

PDF_DIR = Path("/Users/geleixizhibao/Downloads/2022年宿因塔罗课程/课件")
OUTPUT_JSON = Path("/Users/geleixizhibao/Downloads/tarot-app/public/course_knowledge.json")
OUTPUT_JSON.parent.mkdir(exist_ok=True)

PDF_NAMES = {
    "第一周课件.pdf": "第一周：塔罗基础入门",
    "第二周课件.pdf": "第二周：小阿卡纳与数字能量",
    "第三周.pdf": "第三周：牌阵与解读技巧",
    "第四周课件.pdf": "第四周：高阶解读与综合运用",
}

def extract_from_pdf(pdf_path: Path, topic: str) -> dict:
    print(f"正在处理: {pdf_path.name} ...")
    with open(pdf_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode()

    prompt = f"""请仔细阅读这份塔罗课程课件，提取并整理其中的塔罗知识。课程主题：{topic}

请按以下结构整理输出：

## 📚 课程主题
（一句话概括这份课件的核心主题）

## 🃏 涉及的牌/牌阵
（列出课件中提到的具体牌名、牌阵及其解读要点）

## ✨ 核心知识点
（分点列出最重要的塔罗知识、技巧或概念）

## 💡 解读技巧
（老师分享的实用解读方法和技巧）

## 🌟 金句摘录
（课件中值得记住的重要观点，用引号标注）

## 📝 详细笔记
（其他值得记录的具体内容，尽量详细）

请用中文输出，保持内容专业准确，尽量详细完整。"""

    body = json.dumps({
        "contents": [{
            "parts": [
                {"text": prompt},
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_data}}
            ]
        }],
        "generationConfig": {"maxOutputTokens": 4096}
    }).encode("utf-8")

    req = urllib.request.Request(API_URL, data=body,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return {
                "fileName": pdf_path.name,
                "topic": topic,
                "content": text,
                "date": datetime.now().strftime("%Y年%m月%d日"),
                "source": "course_pdf"
            }
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  HTTP错误 {e.code}: {err[:300]}")
        return None

entries = []
for filename, topic in PDF_NAMES.items():
    pdf_path = PDF_DIR / filename
    if pdf_path.exists():
        entry = extract_from_pdf(pdf_path, topic)
        if entry:
            entries.append(entry)
            print(f"  ✓ 完成 {filename}")
        else:
            print(f"  ✗ 处理失败 {filename}")
    else:
        print(f"  ✗ 找不到 {filename}")

if entries:
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完成！提取了 {len(entries)} 份课件知识")
    print(f"保存到: {OUTPUT_JSON}")
else:
    print("\n❌ 没有成功提取任何内容，请检查 API key 配额")
