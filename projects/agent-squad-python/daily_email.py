#!/usr/bin/env python3
"""
daily_email.py — 每日学习内容 HTML 邮件发送器
丹佛时间每天早 8:00 自动运行（由 cron 调用）
"""

import os
import re
import html
import logging
from pathlib import Path
from datetime import datetime

import sendgrid
from sendgrid.helpers.mail import Mail

import anthropic
import sys
sys.path.insert(0, str(Path(__file__).parent))
from build_site import save_entry, rebuild as rebuild_site

# ══════════════════════════════════════════════════════════════════
#  ENV LOADING
# ══════════════════════════════════════════════════════════════════

def _load_env():
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "cron.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

client = anthropic.Anthropic()

# ══════════════════════════════════════════════════════════════════
#  SYSTEM PROMPTS
# ══════════════════════════════════════════════════════════════════

ENGLISH_SYSTEM = """你是一位专业的英语口语学习助手，帮助学习者掌握来自英语国家的地道口语表达。

用户背景：居住在美国，同时对英语世界各地的表达感兴趣——美国、英国、爱尔兰、澳大利亚、新西兰，以及全球通用英语。

每天的任务：
1. 精选10条地道英语表达——可来自任何英语国家，优先选真实日常在用的口语、俚语、惯用语、流行短语（涵盖多元地区，不局限于美国）
2. 每条注明来源地区和使用场景
3. 将这10条表达自然融入一段生活化的口语对话（约250-300词），用一问一答的形式呈现，模拟真实日常场景（朋友聊天、同事对话、家庭闲聊等），全部10条表达自然出现在对话中
4. 提供完整中英对照：先写英文对话，再写中文翻译

输出格式（严格遵守）：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【今日主题】（注明主题名称）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【英文原文】
（生活化口语对话，约250-300词，2-3人对话，一问一答，轻松自然，全部10条表达融入其中。格式：
A: ...
B: ...
A: ...）

【中文翻译】
（对应中文对话，每句话翻译，表达用括号注明英文原文）

【本日表达列表】
1. [表达原文] — 含义：[中文释义] | 地区：[如：美国通用 / 美国南方 / Gen Z / 英国 / 爱尔兰 / 澳大利亚 / 新西兰 / 全球通用 等] | 场景：[使用场景]
2. ...（共10条）

内容要求：
- 对话要有真实感，像真人在说话，不要像课本范文
- 每期尽量覆盖2-3个不同地区的表达，兼顾多样性
- 不要过于书面或过时，优先选当代真实在用的表达
- 10条表达自然融入对话，不生硬
- 若对话中还有其他地道表达（如 on the fence、under the weather 等）虽未列入本日10条，请用 __双下划线__ 标出，供读者留意（非学习重点，仅作地道表达提示）"""


BEAUTY_SYSTEM = """你是一位专业的美妆顾问与美容教育助手。

用户档案：
- 肤质：棱橄榄皮（角质层偏厚、皮肤偏黄偏暗、毛孔偏大、出油适中）
- 脸型：圆脸（颧骨较宽、需视觉拉长收窄）

七日主题轮换：
周一：底妆技巧 | 周二：眼妆教程 | 周三：修容高光
周四：唇妆色号 | 周五：护肤成分解析 | 周六：完整妆容教程 | 周日：护肤小贴士

输出格式：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【今日主题】（主题名称）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

（正文：分步骤/要点展示，具体可操作）

💡 针对你的肤质/脸型：
（专门针对棱橄榄皮+圆脸的个性化建议）

🎨 产品/色号推荐：
（若适用，给出具体推荐及理由）

注意事项：
- 圆脸重点：收窄横向视觉、视觉拉长脸型
- 棱橄榄皮底妆：提亮暗沉、控油遮孔
- 色彩：大地色系、棕调、暖粉、砖红——避免冷粉冷紫"""


RESEARCH_SYSTEM = """你是一位专业的应用语言学学术文献助手，服务对象为该领域的博士研究生。

用户研究背景：

【研究方向一：评估与语言权力】
核心概念：AP Chinese、assessment、epistemic injustice、hermeneutical injustice、
washback、metalinguistic asymmetry、CDA

【研究方向二：课堂互动与中介】
核心概念：CSL、peer interaction、translanguaging、LRE、NoM、
mediational architecture、MICM、novice-high

【研究方向三：教师与制度】
核心概念：charter school / DLI、teacher vulnerability、decoupling、
emotional labor、autoethnography、policy implementation

每日任务：推荐3篇真实存在的学术论文，每篇提供：

📌 作者：
📖 标题：
📰 期刊：
📅 年份：（发表年份）
📊 引用量：（约X次（估计））
📝 摘要：
🔗 与本研究的关联性：
🆔 DOI：（如 10.1000/xyz123，不确定请写"不详"）

在每篇论文前写：━━━━━━━━━━━━━━━━━━━━━━━━
然后写：📄 论文 N
然后再写：━━━━━━━━━━━━━━━━━━━━━━━━
然后是论文各字段。

重要原则：
- 优先推荐 2020–2024 年发表的最新前沿研究，尽量选近3年内的论文
- 避免只选大名鼎鼎的经典文献——重点发掘新兴学者、新视角、新方法论的近期成果
- 只推荐训练数据中真实存在的论文，不要虚构"""


# ══════════════════════════════════════════════════════════════════
#  CONTENT GENERATION
# ══════════════════════════════════════════════════════════════════

WEEKDAY_CN = {
    "Monday":"周一","Tuesday":"周二","Wednesday":"周三",
    "Thursday":"周四","Friday":"周五","Saturday":"周六","Sunday":"周日",
}

def collect(system: str, user_prompt: str, max_tokens: int = 3500, **kwargs) -> str:
    """Call Claude API and return full streamed text."""
    parts = []
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_prompt}],
        **kwargs,
    ) as stream:
        for chunk in stream.text_stream:
            parts.append(chunk)
    return "".join(parts)


def gen_english(today: str, weekday: int) -> str:
    topics = [
        "职场与成功（career, ambition, perseverance）",
        "人生哲理与智慧（life wisdom, choices, consequences）",
        "人际关系与友谊（friendship, trust, communication）",
        "时间与金钱（time, money, priorities）",
        "自然与环境（nature, seasons, environment）",
        "挑战与逆境（adversity, resilience, change）",
        "知识与学习（knowledge, curiosity, growth）",
    ]
    return collect(
        ENGLISH_SYSTEM,
        f"今天是{today}。请围绕主题「{topics[weekday]}」，"
        "为我提供今日的10条美式英语地道表达学习内容，优先选美国人日常真实在用的口语和俚语，"
        "按照规定格式输出完整内容。",
        max_tokens=2800,
    )


def gen_beauty(today: str, weekday: int, day_cn: str) -> str:
    themes = ["底妆技巧","眼妆教程","修容高光","唇妆色号",
              "护肤成分解析","完整妆容教程","护肤小贴士"]
    return collect(
        BEAUTY_SYSTEM,
        f"今天是{today}（{day_cn}）。请围绕今日主题「{themes[weekday]}」，"
        "为我提供针对棱橄榄皮+圆脸的个性化美妆内容推送。",
        max_tokens=1800,
    )


def gen_research(today: str) -> str:
    day_mod = datetime.now().day % 3
    focuses = [
        "今天请优先推荐与【评估与语言权力】相关的论文（washback、epistemic injustice、AP Chinese、CDA），搭配1篇其他方向。",
        "今天请优先推荐与【课堂互动与中介】相关的论文（translanguaging、LRE、peer interaction in CSL、MICM），搭配1篇其他方向。",
        "今天请优先推荐与【教师与制度】相关的论文（teacher vulnerability、emotional labor、DLI policy、autoethnography），搭配1篇其他方向。",
    ]
    return collect(
        RESEARCH_SYSTEM,
        f"今天是{today}，请为我推荐今日3篇学术论文。\n{focuses[day_mod]}\n"
        "请按照规定格式逐一呈现每篇论文的完整信息。",
        max_tokens=4000,
    )


# ══════════════════════════════════════════════════════════════════
#  TEXT → HTML CONVERTERS
# ══════════════════════════════════════════════════════════════════

def e(s: str) -> str:
    return html.escape(str(s))


def md(s: str) -> str:
    """HTML-escape then convert inline markdown (**bold**, *italic*, __idiom__) to HTML tags."""
    s = html.escape(str(s))
    # __地道表达__ → 次级高亮（非本日重点，仅作提示）
    s = re.sub(r'__(.+?)__', r'<span style="background:#f5f0e6;color:#8b7355;padding:1px 4px;border-radius:3px;font-size:0.98em">\1</span>', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', s)
    return s


def english_to_html(text: str) -> str:
    parts = []
    current_section = None

    for raw in text.splitlines():
        s = raw.strip()

        # Separator line — skip
        if s and all(c in "━─═-" for c in s):
            continue

        # Section header 【...】
        if s.startswith("【") and "】" in s:
            close_idx = s.index("】")
            label = s[1: close_idx]
            suffix = s[close_idx + 1:].strip()
            color_map = {
                "今日主题":  ("#1a73e8", "#e8f0fe"),
                "英文原文":  ("#0d47a1", "#e3f2fd"),
                "中文翻译":  ("#1b5e20", "#e8f5e9"),
                "本日表达列表": ("#4a148c", "#f3e5f5"),
            }
            bg, border_color = ("#f5f5f5", "#ccc")
            for key, (bc, bg_) in color_map.items():
                if key in label:
                    border_color, bg = bc, bg_
                    break
            current_section = label
            suffix_html = f'<span style="margin-left:8px;font-weight:400;color:{border_color}">{md(suffix)}</span>' if suffix else ""
            parts.append(
                f'<div style="background:{bg};border-left:4px solid {border_color};'
                f'padding:10px 16px;margin:18px 0 10px;border-radius:0 6px 6px 0">'
                f'<strong style="color:{border_color};font-size:15px">【{e(label)}】</strong>{suffix_html}</div>'
            )
            continue

        # Markdown headings
        hm = re.match(r"^(#{1,3})\s+(.+)", s)
        if hm:
            level, heading = len(hm.group(1)), hm.group(2)
            sz = {1: "17px", 2: "15px", 3: "14px"}.get(level, "14px")
            parts.append(
                f'<div style="color:#1a73e8;font-weight:700;font-size:{sz};'
                f'margin:16px 0 6px;padding-bottom:4px;border-bottom:1px solid #e8f0fe">'
                f'{md(heading)}</div>'
            )
            continue

        # Numbered idiom  1. ... — 含义：... | 场景/地区：...
        m = re.match(r"^(\d{1,2})[.、]\s+(.+)", s)
        if m and current_section and "表达" in current_section:
            num, rest = m.group(1), m.group(2)
            dash_m = re.split(r"\s*[—–]\s*", rest, 1)
            idiom_raw = dash_m[0].strip()
            detail    = dash_m[1].strip() if len(dash_m) > 1 else ""

            # Parse 含义 | 地区 | 场景
            parts_detail = re.split(r"\|\s*(?:地区|场景)：", detail)
            meaning  = parts_detail[0].replace("含义：", "").strip()
            region_m = re.search(r"\|\s*地区：([^|]+)", detail)
            scene_m  = re.search(r"\|\s*场景：([^|]+)", detail)
            region   = region_m.group(1).strip() if region_m else ""
            scene    = scene_m.group(1).strip() if scene_m else ""

            tags_html = ""
            if region:
                tags_html += (f'<span style="display:inline-block;padding:2px 8px;'
                              f'background:#e8f0fe;border-radius:10px;font-size:11px;'
                              f'color:#1a73e8;white-space:nowrap;margin-left:6px">📍 {e(region)}</span>')
            if scene:
                tags_html += (f'<span style="display:inline-block;padding:2px 8px;'
                              f'background:#e8f5e9;border-radius:10px;font-size:11px;'
                              f'color:#2e7d32;white-space:nowrap;margin-left:6px">💬 {e(scene)}</span>')

            parts.append(
                f'<table width="100%" cellpadding="0" cellspacing="0" '
                f'style="margin:6px 0;border-collapse:collapse">'
                f'<tr>'
                f'<td width="28" valign="top" style="padding:10px 8px 10px 14px;'
                f'color:#1a73e8;font-weight:700;font-size:13px;white-space:nowrap;'
                f'background:#f0f4ff;border-radius:8px 0 0 8px;border:1px solid #d0d9ff;'
                f'border-right:none">{num.zfill(2)}.</td>'
                f'<td valign="top" style="padding:10px 14px 10px 8px;'
                f'background:#f8f9ff;border-radius:0 8px 8px 0;border:1px solid #d0d9ff;'
                f'border-left:none">'
                f'<strong style="color:#1a73e8;font-size:14px">{md(idiom_raw)}</strong>'
                f'<span style="color:#555;font-size:13px;margin-left:8px">— {md(meaning)}</span>'
                f'{tags_html}'
                f'</td></tr></table>'
            )
            continue

        # Empty line
        if not s:
            parts.append('<div style="height:8px"></div>')
            continue

        # Dialogue line: A: ... / B: ... / C: ...
        dm = re.match(r"^([A-Z][a-z]?)\s*:\s+(.+)", s)
        if dm:
            speaker, line = dm.group(1), dm.group(2)
            colors = ["#1a73e8", "#e53935", "#2e7d32", "#6a1b9a"]
            idx = (ord(speaker[0]) - ord("A")) % len(colors)
            color = colors[idx]
            parts.append(
                f'<table width="100%" cellpadding="0" cellspacing="0" '
                f'style="margin:5px 0;border-collapse:collapse"><tr>'
                f'<td width="28" valign="top" style="padding:8px 6px 8px 0;'
                f'font-weight:700;font-size:14px;color:{color};white-space:nowrap">{e(speaker)}:</td>'
                f'<td valign="top" style="padding:8px 0;font-size:14px;color:#333;line-height:1.7">'
                f'{md(line)}</td></tr></table>'
            )
            continue

        # Regular paragraph
        parts.append(
            f'<p style="margin:6px 0;line-height:1.8;color:#333;font-size:14px">{md(s)}</p>'
        )

    return "\n".join(parts)


def beauty_to_html(text: str) -> str:
    parts = []

    for raw in text.splitlines():
        s = raw.strip()

        if s and all(c in "━─═-" for c in s):
            continue

        if s.startswith("【") and "】" in s:
            close_idx = s.index("】")
            label = s[1: close_idx]
            suffix = s[close_idx + 1:].strip()
            suffix_html = f'<span style="margin-left:8px;font-weight:400;color:#c2185b">{md(suffix)}</span>' if suffix else ""
            parts.append(
                f'<div style="background:#fce4ec;border-left:4px solid #e91e8c;'
                f'padding:10px 16px;margin:18px 0 10px;border-radius:0 6px 6px 0">'
                f'<strong style="color:#c2185b;font-size:15px">【{e(label)}】</strong>{suffix_html}</div>'
            )
            continue

        # Markdown headings ## / ###
        hm = re.match(r"^(#{1,3})\s+(.+)", s)
        if hm:
            level, heading = len(hm.group(1)), hm.group(2)
            sz = {1: "17px", 2: "15px", 3: "14px"}.get(level, "14px")
            parts.append(
                f'<div style="color:#c2185b;font-weight:700;font-size:{sz};'
                f'margin:16px 0 6px;padding-bottom:4px;border-bottom:1px solid #fce4ec">'
                f'{md(heading)}</div>'
            )
            continue

        # 💡 tip block
        if s.startswith("💡"):
            parts.append(
                f'<div style="background:#fff9c4;border-left:4px solid #f9a825;'
                f'padding:12px 16px;margin:14px 0;border-radius:0 8px 8px 0">'
                f'<strong style="color:#e65100">{md(s)}</strong></div>'
            )
            continue

        # 🎨 product block
        if s.startswith("🎨"):
            parts.append(
                f'<div style="background:#e0f7fa;border-left:4px solid #00bcd4;'
                f'padding:12px 16px;margin:14px 0;border-radius:0 8px 8px 0">'
                f'<strong style="color:#006064">{md(s)}</strong></div>'
            )
            continue

        # Numbered step
        m = re.match(r"^(Step\s*\d+|步骤\s*\d+|\d+[.、])\s*(.+)", s)
        if m:
            step, content = m.group(1), m.group(2)
            parts.append(
                f'<div style="display:flex;align-items:flex-start;margin:8px 0;'
                f'padding:10px 14px;background:#fdf0f7;border-radius:8px">'
                f'<span style="color:#e91e8c;font-weight:700;min-width:70px;font-size:13px">{e(step)}</span>'
                f'<span style="color:#333;font-size:14px;line-height:1.7">{md(content)}</span>'
                f'</div>'
            )
            continue

        # Bullet point
        if re.match(r"^[-·•·]", s):
            content = re.sub(r"^[-·•·]\s*", "", s)
            parts.append(
                f'<div style="padding:4px 0 4px 16px;color:#444;font-size:14px;line-height:1.7">'
                f'<span style="color:#e91e8c;margin-right:8px">✦</span>{md(content)}</div>'
            )
            continue

        # 注意事项
        if s.startswith("注意") or s.startswith("⚠"):
            parts.append(
                f'<div style="background:#fff3e0;border-left:4px solid #ff9800;'
                f'padding:8px 16px;margin:10px 0;border-radius:0 6px 6px 0;'
                f'color:#bf360c;font-size:13px">{md(s)}</div>'
            )
            continue

        if not s:
            parts.append('<div style="height:8px"></div>')
            continue

        parts.append(
            f'<p style="margin:6px 0;line-height:1.8;color:#333;font-size:14px">{md(s)}</p>'
        )

    return "\n".join(parts)


def research_to_html(text: str) -> str:
    """Parse paper entries and render as styled cards."""
    import urllib.parse
    parts = []

    ICON_STYLES = {
        "📌": ("#c62828", "作者"),
        "📖": ("#1565c0", "标题"),
        "📰": ("#00838f", "期刊"),
        "📅": ("#e65100", "年份"),
        "📊": ("#2e7d32", "引用量"),
        "📝": ("#4a148c", "摘要"),
        "🔗": ("#6a1b9a", "关联性"),
        "🆔": ("#37474f", "DOI"),
    }

    in_card = False
    current_title = ""

    for raw in text.splitlines():
        s = raw.strip()

        if s and all(c in "━─═-" for c in s):
            continue

        # Paper card header
        if "📄" in s:
            if in_card:
                parts.append("</div>")
            parts.append(
                f'<div style="background:#fff;border:1px solid #e0e0e0;border-radius:10px;'
                f'padding:20px 22px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,0.06)">'
                f'<div style="background:linear-gradient(135deg,#00bcd4,#00897b);'
                f'color:#fff;padding:10px 16px;border-radius:6px;margin:-20px -22px 16px;'
                f'font-weight:700;font-size:15px;letter-spacing:1px">{e(s)}</div>'
            )
            in_card = True
            current_title = ""
            continue

        # Icon fields
        matched = False
        for icon, (color, _label) in ICON_STYLES.items():
            if s.startswith(icon):
                key_end = s.find("：") + 1 if "：" in s else 2
                key_part  = s[:key_end]
                body_part = s[key_end:].strip()

                # Save title for fallback link
                if icon == "📖":
                    current_title = body_part

                # DOI field → render as clickable link
                if icon == "🆔":
                    doi = body_part.strip()
                    if doi and doi != "不详" and re.match(r"10\.\d{4,}", doi):
                        link_url  = f"https://doi.org/{doi}"
                        link_text = doi
                    else:
                        # Fallback: Google Scholar search by title
                        q = urllib.parse.quote(current_title or doi)
                        link_url  = f"https://scholar.google.com/scholar?q={q}"
                        link_text = "Google Scholar 搜索"
                    parts.append(
                        f'<table width="100%" cellpadding="0" cellspacing="0" '
                        f'style="margin:7px 0;border-collapse:collapse"><tr>'
                        f'<td width="88" valign="top" style="color:{color};font-weight:600;'
                        f'font-size:13px;padding-right:8px;white-space:nowrap">{e(key_part)}</td>'
                        f'<td valign="top" style="font-size:13px;line-height:1.7">'
                        f'<a href="{e(link_url)}" target="_blank" '
                        f'style="color:#1a73e8;text-decoration:none">🔍 {e(link_text)}</a>'
                        f'</td></tr></table>'
                    )
                    matched = True
                    break

                bold = "font-weight:700;" if icon == "📖" else ""
                parts.append(
                    f'<table width="100%" cellpadding="0" cellspacing="0" '
                    f'style="margin:7px 0;border-collapse:collapse">'
                    f'<tr>'
                    f'<td width="88" valign="top" style="color:{color};font-weight:600;'
                    f'font-size:13px;padding-right:8px;white-space:nowrap">{e(key_part)}</td>'
                    f'<td valign="top" style="color:#333;font-size:14px;line-height:1.7;{bold}">'
                    f'{md(body_part)}</td>'
                    f'</tr></table>'
                )
                matched = True
                break
        if matched:
            continue

        if not s:
            parts.append('<div style="height:6px"></div>')
            continue

        parts.append(
            f'<p style="margin:5px 0;line-height:1.8;color:#555;font-size:13px;'
            f'padding-left:96px">{md(s)}</p>'
        )

    if in_card:
        parts.append("</div>")

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════
#  HTML EMAIL TEMPLATE
# ══════════════════════════════════════════════════════════════════

def build_email_html(
    eng_html: str,
    bty_html: str,
    res_html: str,
    date_str: str,
    day_cn: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>每日学习助手小队 · {date_str}</title>
</head>
<body style="margin:0;padding:20px 0;background:#f0f2f5;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif">

  <div style="max-width:680px;margin:0 auto">

    <!-- ══ HEADER ══ -->
    <div style="background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
      border-radius:14px 14px 0 0;padding:36px 36px 28px;text-align:center">
      <div style="font-size:32px;margin-bottom:8px">✨</div>
      <h1 style="color:#fff;margin:0;font-size:26px;letter-spacing:3px;font-weight:700">
        每日学习助手小队
      </h1>
      <p style="color:rgba(255,255,255,0.75);margin:10px 0 0;font-size:14px;letter-spacing:1px">
        Daily Learning Squad
      </p>
      <div style="margin-top:16px;display:inline-block;background:rgba(255,255,255,0.15);
        border-radius:20px;padding:6px 20px">
        <span style="color:#fff;font-size:14px;font-weight:600">
          📅 &nbsp;{date_str} &nbsp;{day_cn}
        </span>
      </div>
    </div>

    <!-- ══ ENGLISH SECTION ══ -->
    <div style="background:#fff;border-top:5px solid #4285f4;
      padding:28px 32px;margin-top:0">
      <div style="display:flex;align-items:center;margin-bottom:20px">
        <div style="width:48px;height:48px;background:linear-gradient(135deg,#4285f4,#1565c0);
          border-radius:12px;display:flex;align-items:center;justify-content:center;
          font-size:22px;flex-shrink:0">📚</div>
        <div style="margin-left:14px">
          <h2 style="margin:0;font-size:19px;color:#1a73e8;font-weight:700">英语学习助手</h2>
          <p style="margin:3px 0 0;font-size:12px;color:#888;letter-spacing:0.5px">
            English Learning Assistant &nbsp;·&nbsp; C1 Idioms &amp; Proverbs
          </p>
        </div>
      </div>
      {eng_html}
    </div>

    <!-- ══ DIVIDER ══ -->
    <div style="height:6px;background:linear-gradient(90deg,#4285f4,#e91e8c,#00bcd4)"></div>

    <!-- ══ BEAUTY SECTION ══ -->
    <div style="background:#fffaf9;border-top:5px solid #e91e8c;padding:28px 32px">
      <div style="display:flex;align-items:center;margin-bottom:20px">
        <div style="width:48px;height:48px;background:linear-gradient(135deg,#f06292,#c2185b);
          border-radius:12px;display:flex;align-items:center;justify-content:center;
          font-size:22px;flex-shrink:0">💄</div>
        <div style="margin-left:14px">
          <h2 style="margin:0;font-size:19px;color:#c2185b;font-weight:700">美妆学习助手</h2>
          <p style="margin:3px 0 0;font-size:12px;color:#888;letter-spacing:0.5px">
            Beauty Assistant &nbsp;·&nbsp; 棱橄榄皮 &nbsp;·&nbsp; 圆脸
          </p>
        </div>
      </div>
      {bty_html}
    </div>

    <!-- ══ DIVIDER ══ -->
    <div style="height:6px;background:linear-gradient(90deg,#e91e8c,#00bcd4,#667eea)"></div>

    <!-- ══ RESEARCH SECTION ══ -->
    <div style="background:#f9fdfd;border-top:5px solid #00bcd4;padding:28px 32px">
      <div style="display:flex;align-items:center;margin-bottom:20px">
        <div style="width:48px;height:48px;background:linear-gradient(135deg,#26c6da,#00838f);
          border-radius:12px;display:flex;align-items:center;justify-content:center;
          font-size:22px;flex-shrink:0">🔬</div>
        <div style="margin-left:14px">
          <h2 style="margin:0;font-size:19px;color:#00838f;font-weight:700">科研文献助手</h2>
          <p style="margin:3px 0 0;font-size:12px;color:#888;letter-spacing:0.5px">
            Research Assistant &nbsp;·&nbsp; Applied Linguistics PhD
          </p>
        </div>
      </div>
      {res_html}
    </div>

    <!-- ══ FOOTER ══ -->
    <div style="background:#2d2d2d;border-radius:0 0 14px 14px;
      padding:20px 32px;text-align:center">
      <p style="color:#aaa;margin:0 0 6px;font-size:12px">
        🤖 &nbsp;Powered by Claude Opus 4.6 &nbsp;·&nbsp; Hits your inbox every morning at 8:00 AM Denver time
      </p>
      <p style="color:#666;margin:0;font-size:11px">
        American English &nbsp;·&nbsp; 美妆护肤 &nbsp;·&nbsp; 应用语言学科研
      </p>
    </div>

  </div>
</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
#  EMAIL SENDING
# ══════════════════════════════════════════════════════════════════

def send_email(subject: str, html_body: str):
    api_key   = os.environ["SENDGRID_API_KEY"]
    from_addr = os.environ["EMAIL_FROM"]
    to_addr   = os.environ["EMAIL_TO"]

    message = Mail(
        from_email=(from_addr, "格雷西学习小屋"),
        to_emails=to_addr,
        subject=subject,
        html_content=html_body,
    )
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    sg.send(message)


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    now      = datetime.now()
    date_str = now.strftime("%Y年%m月%d日")
    day_cn   = {
        "Monday":"周一","Tuesday":"周二","Wednesday":"周三",
        "Thursday":"周四","Friday":"周五","Saturday":"周六","Sunday":"周日",
    }.get(now.strftime("%A"), "")
    weekday  = now.weekday()

    log.info("═" * 50)
    log.info(f"开始生成今日邮件内容  {date_str} {day_cn}")

    log.info("📚 生成英语学习内容...")
    eng_text = gen_english(date_str, weekday)
    log.info(f"   完成，{len(eng_text)} 字符")

    log.info("💄 生成美妆学习内容...")
    bty_text = gen_beauty(date_str, weekday, day_cn)
    log.info(f"   完成，{len(bty_text)} 字符")

    log.info("🔬 生成科研文献推荐...")
    res_text = gen_research(date_str)
    log.info(f"   完成，{len(res_text)} 字符")

    log.info("🎨 转换为 HTML...")
    eng_html = english_to_html(eng_text)
    bty_html = beauty_to_html(bty_text)
    res_html = research_to_html(res_text)

    full_html = build_email_html(eng_html, bty_html, res_html, date_str, day_cn)

    subject = f"✨ 每日学习推送 · {date_str} {day_cn}"

    log.info(f"📨 发送邮件到 {os.environ.get('EMAIL_TO', '(未配置)')}...")
    send_email(subject, full_html)
    log.info("✅ 邮件发送成功！")

    log.info("🏡 更新格雷西学习小屋网站...")
    date_key = now.strftime("%Y-%m-%d")
    save_entry(date_key, date_str, day_cn, eng_html, bty_html, res_html)
    site_path, count = rebuild_site()
    log.info(f"   网站已更新 ({count} 天记录) → {site_path}")


if __name__ == "__main__":
    main()
