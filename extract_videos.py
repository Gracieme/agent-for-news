#!/usr/bin/env python3
"""
从Gracie塔罗课程视频提取知识 - 使用 Gemini File API
运行方式: python3 extract_videos.py
"""
import os, json, time, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

# ⚠️ 换成新的 API key 后修改这里
GEMINI_API_KEY = "AIzaSyCPFK-FsxIJKEpT3IOGBq5qlkURIF80gps"

VIDEO_DIR = Path("/Users/geleixizhibao/Downloads/2022年Gracie塔罗课程")
OUTPUT_JSON = Path("/Users/geleixizhibao/Downloads/tarot-app/src/lib/teacher-videos-knowledge.json")
OUTPUT_TS = Path("/Users/geleixizhibao/Downloads/tarot-app/src/lib/teacher-videos-knowledge.ts")

# 视频文件与主题映射（按课程顺序）
VIDEOS = [
    ("00-【0402早上】.mp4", "第一天上午：塔罗基础、牌的历史与整体认知"),
    ("01-【0402下午】.mp4", "第一天下午：大阿卡纳详解"),
    ("02-【0403早上】.mp4", "第二天上午：小阿卡纳与花色能量"),
    ("03-【0403下午】.mp4", "第二天下午：数字能量与宫廷牌"),
    ("04-【0404上午】.mp4", "第三天上午：牌阵基础与解读方法"),
    ("05-【0404下午】.mp4", "第三天下午：感情牌阵与关系解读"),
    ("06.(0405上午).mp4", "第四天上午：工作事业牌阵"),
    ("07-（0405下午）.mp4", "第四天下午：综合练习与案例分析"),
    ("08.mp4", "第五天：逆位详解与进阶技巧"),
    ("09-(0406上午2).mp4", "第五天上午2：直觉解读训练"),
    ("10-(0406下午).mp4", "第五天下午：综合牌阵解读"),
    ("11.mp4", "第六天上午：高阶解读技巧"),
    ("12-【0407】.mp4", "第六天：时间预测与能量解读"),
    ("12.mp4", "补充课：特殊牌阵与场景解读"),
    ("13-【Gracie发起的在线课堂】.mp4", "在线课堂：问答与综合演练"),
]

EXTRACT_PROMPT = """请仔细观看这段塔罗课程视频，这是Gracie的系统塔罗课程。

课程主题：{topic}

请尽可能详细地提取以下内容：

## 🎯 本节课程核心主题

## 🃏 涉及的具体牌义讲解
（每张牌的Gracie专属解读角度，包括正位逆位，越详细越好）

## 📐 牌阵讲解
（老师介绍的牌阵名称、摆放方式、每个位置的含义）

## 💡 解读方法与技巧
（老师的具体操作方法、如何看牌、如何联系牌与牌）

## 🔑 Gracie的独特视角
（与其他老师不同的解读角度、创新观点、特色理念）

## 💬 案例与示范
（老师举的具体例子、实际解读示范、客户案例）

## 🌟 金句与核心观点
（老师说的值得记录的重要话语，用引号标注）

## 📝 其他重要内容
（任何其他值得记录的塔罗知识）

请用中文详细输出，这些内容将用于AI解牌，越详细越能帮助AI准确还原老师的解读风格。"""

def upload_file(video_path: Path) -> str | None:
    """上传文件到 Gemini File API，返回 file_uri"""
    print(f"  📤 正在上传 {video_path.name}（{video_path.stat().st_size // 1024 // 1024}MB）...")

    # 1. 初始化上传
    init_url = f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={GEMINI_API_KEY}"
    file_size = video_path.stat().st_size
    init_req = urllib.request.Request(
        init_url, data=b"",
        headers={
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(file_size),
            "X-Goog-Upload-Header-Content-Type": "video/mp4",
            "Content-Type": "application/json",
        }, method="POST"
    )

    try:
        with urllib.request.urlopen(init_req, timeout=30) as resp:
            upload_url = resp.headers.get("X-Goog-Upload-URL")
            if not upload_url:
                print(f"  ❌ 未能获取上传URL")
                return None
    except Exception as e:
        print(f"  ❌ 初始化上传失败: {e}")
        return None

    # 2. 分块上传（每块 50MB）
    chunk_size = 50 * 1024 * 1024
    offset = 0
    with open(video_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            is_last = (offset + len(chunk) >= file_size)
            upload_cmd = "upload, finalize" if is_last else "upload"

            upload_req = urllib.request.Request(
                upload_url, data=chunk,
                headers={
                    "X-Goog-Upload-Command": upload_cmd,
                    "X-Goog-Upload-Offset": str(offset),
                    "Content-Length": str(len(chunk)),
                }, method="PUT"
            )
            try:
                with urllib.request.urlopen(upload_req, timeout=120) as resp:
                    if is_last:
                        result = json.loads(resp.read())
                        file_uri = result.get("file", {}).get("uri")
                        file_name = result.get("file", {}).get("name")
                        print(f"  ✅ 上传完成")
                        # 等待处理
                        return wait_for_file(file_uri, file_name)
            except Exception as e:
                print(f"  ❌ 上传失败 offset={offset}: {e}")
                return None

            offset += len(chunk)
            pct = int(offset / file_size * 100)
            print(f"    进度: {pct}%", end="\r")

    return None

def wait_for_file(file_uri: str, file_name: str) -> str | None:
    """等待文件处理完成"""
    print(f"  ⏳ 等待视频处理...")
    for i in range(30):
        time.sleep(10)
        check_url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={GEMINI_API_KEY}"
        try:
            with urllib.request.urlopen(check_url, timeout=15) as resp:
                data = json.loads(resp.read())
                state = data.get("state", "")
                if state == "ACTIVE":
                    print(f"  ✅ 视频已就绪")
                    return file_uri
                elif state == "FAILED":
                    print(f"  ❌ 视频处理失败")
                    return None
        except Exception as e:
            pass
        print(f"    等待中... ({(i+1)*10}秒)", end="\r")
    print(f"  ❌ 超时")
    return None

def extract_knowledge(file_uri: str, topic: str) -> str | None:
    """使用 Gemini 从视频提取知识"""
    print(f"  🤖 Gemini 正在分析视频...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    body = json.dumps({
        "contents": [{
            "parts": [
                {"text": EXTRACT_PROMPT.format(topic=topic)},
                {"file_data": {"mime_type": "video/mp4", "file_uri": file_uri}}
            ]
        }],
        "generationConfig": {"maxOutputTokens": 8192}
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        print(f"  ❌ Gemini 分析失败: {e.read().decode()[:200]}")
        return None

def delete_file(file_name: str):
    """删除已处理的文件（释放配额）"""
    url = f"https://generativelanguage.googleapis.com/v1beta/{file_name}?key={GEMINI_API_KEY}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=10)
    except:
        pass

# 主流程
existing = []
if OUTPUT_JSON.exists():
    with open(OUTPUT_JSON) as f:
        existing = json.load(f)
    existing_names = {e["fileName"] for e in existing}
    print(f"已有 {len(existing)} 条记录，继续提取剩余视频...")
else:
    existing_names = set()

results = existing.copy()

for filename, topic in VIDEOS:
    if filename in existing_names:
        print(f"⏭️  跳过（已提取）: {filename}")
        continue

    video_path = VIDEO_DIR / filename
    if not video_path.exists():
        print(f"⚠️  找不到: {filename}")
        continue

    print(f"\n📹 处理: {filename}")
    print(f"   主题: {topic}")

    # 上传
    file_uri = upload_file(video_path)
    if not file_uri:
        continue

    # 提取知识
    knowledge = extract_knowledge(file_uri, topic)
    if knowledge:
        entry = {
            "fileName": filename,
            "topic": topic,
            "content": knowledge,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        results.append(entry)
        print(f"  ✅ 知识提取成功（{len(knowledge)}字）")

        # 实时保存
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    # 清理文件
    time.sleep(2)

# 生成 TypeScript 知识库
if results:
    combined = "\n\n---\n\n".join([
        f"【{r['topic']}】\n{r['content']}" for r in results
    ])
    ts_content = f'''// Gracie塔罗课程视频知识库 - 自动生成
// 共 {len(results)} 节课，最后更新：{datetime.now().strftime("%Y-%m-%d")}

export const TEACHER_VIDEO_KNOWLEDGE = `
{combined}
`;
'''
    with open(OUTPUT_TS, "w", encoding="utf-8") as f:
        f.write(ts_content)

    print(f"\n✅ 全部完成！共处理 {len(results)} 个视频")
    print(f"知识库已保存到: {OUTPUT_TS}")
else:
    print("\n❌ 没有成功提取任何内容")
