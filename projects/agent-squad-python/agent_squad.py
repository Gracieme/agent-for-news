#!/usr/bin/env python3
"""
每日学习助手小队 Daily Learning Agent Squad
Colorful, beautiful terminal UI powered by Claude Opus 4.6
"""

import os
import re
import anthropic
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich.table import Table
from rich.align import Align
from rich.padding import Padding
from rich import box


def _load_env():
    """Load .env file into os.environ (won't override existing vars)."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

_load_env()

console = Console(highlight=False)
client = anthropic.Anthropic()

# ══════════════════════════════════════════════════════════════════
#  SYSTEM PROMPTS
# ══════════════════════════════════════════════════════════════════

ENGLISH_AGENT_SYSTEM = """你是一位专业的美式英语学习助手，专注于帮助在美国生活的学习者掌握地道的美式口语表达。

用户背景：居住在美国，需要实际生活中能用上的美式英语表达。

每天的任务：
1. 精选10条地道的美式英语表达——优先选 American idioms、American slang、everyday American colloquialisms、
   US-specific proverbs 和 American pop-culture references（流行度高、实用性强）
2. 每条注明使用场景（如：职场、朋友聚会、日常闲聊、社交媒体等）
3. 将这10条表达自然融入一段生动的英文段落（约250-300词），模拟真实美国人的说话方式
4. 提供完整中英对照：先写英文段落，再写中文翻译

输出格式（严格遵守）：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【今日主题】（注明主题名称）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

【英文原文】
（约250-300词的段落，口语化、接地气，自然融入全部10条表达）

【中文翻译】
（对应中文段落，美式表达用括号注明英文原文）

【本日表达列表】
1. [表达原文] — 含义：[中文释义] | 场景：[使用场景]
2. ...（共10条）

内容要求：
- 优先选美国人日常真实在用的表达，不要过于书面或过时
- 涵盖不同风格：口语俚语、惯用语、流行短语、幽默表达
- 10条表达围绕同一主题，段落读来自然流畅、有美国生活气息"""


BEAUTY_AGENT_SYSTEM = """你是一位专业的美妆顾问与美容教育助手。

用户档案：
- 肤质：棱橄榄皮（角质层偏厚、皮肤偏黄偏暗、毛孔偏大、出油适中、不易过敏）
- 脸型：圆脸（颧骨较宽、脸部线条圆润、需视觉拉长收窄）

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
- 棱橄榄皮底妆：提亮暗沉、控油遮孔、避免偏黄
- 色彩：大地色系、棕调、暖粉、砖红、裸橙——避免冷粉冷紫
- 语言亲切专业，步骤清晰可操作"""


RESEARCH_AGENT_SYSTEM = """你是一位专业的应用语言学学术文献助手，服务对象为该领域的博士研究生。

用户研究背景：

【研究方向一：评估与语言权力】
核心概念：AP Chinese（AP中文考试）、assessment（语言评估）、epistemic injustice（认知不公正）、
hermeneutical injustice（诠释不公正）、washback（反拨效应）、metalinguistic asymmetry（元语言不对称）、
CDA（批评话语分析）

【研究方向二：课堂互动与中介】
核心概念：CSL（中文作为第二语言）、peer interaction（同伴互动）、translanguaging（跨语言实践）、
LRE（语言相关情节）、NoM（意义协商）、mediational architecture（中介架构）、
MICM（多模态互动会话分析）、novice-high（初级高水平）

【研究方向三：教师与制度】
核心概念：charter school / DLI（双语沉浸式教育）、teacher vulnerability（教师脆弱性）、
decoupling（脱耦）、emotional labor（情感劳动）、autoethnography（自传民族志）、
policy implementation（政策实施）

每日任务：推荐3篇真实存在、高度相关的学术论文

每篇论文必须提供：
1. 📌 作者（Authors）
2. 📖 标题（Title）—— 英文原题
3. 📰 期刊（Journal）+ 发表年份
4. 📊 引用量（Citation count）—— 基于已知信息估算，须注明"约X次（估计）"
5. 📝 摘要（Abstract）—— 原文或中文概述（3-5句）
6. 🔗 与本研究的关联性 —— 说明与哪个研究方向相关，有何理论或方法论启发（2-4句）

重要原则：
- 只推荐训练数据中确实存在的真实论文，不编造
- 优先推荐2012年至今的论文
- 每天尽量覆盖不同的研究方向组合

输出格式（每篇论文）：

━━━━━━━━━━━━━━━━━━━━━━━━
📄 论文 [编号]
━━━━━━━━━━━━━━━━━━━━━━━━
📌 作者：
📖 标题：
📰 期刊：
📊 引用量：
📝 摘要：
🔗 与本研究的关联性："""


# ══════════════════════════════════════════════════════════════════
#  SMART STREAMER — real-time line-by-line colorized output
# ══════════════════════════════════════════════════════════════════

class SmartStreamer:
    """Buffer streaming chunks, print each complete line with rich colors."""

    def __init__(self, theme: str):
        self.theme = theme   # 'english' | 'beauty' | 'research'
        self.buf = ""

    def feed(self, chunk: str):
        self.buf += chunk
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            self._emit(line)

    def flush(self):
        if self.buf:
            self._emit(self.buf)
            self.buf = ""

    # ── dispatch ──────────────────────────────────────────────────
    def _emit(self, raw: str):
        handlers = {
            "english":  self._english,
            "beauty":   self._beauty,
            "research": self._research,
        }
        t = handlers[self.theme](raw)
        if t is None:
            console.print()          # blank line
        else:
            console.print(t)

    # ── English theme ─────────────────────────────────────────────
    def _english(self, raw: str):
        s = raw.rstrip()

        # Separator  ━━━
        if s and all(c in "━─═" for c in s):
            t = Text(s, style="bright_blue dim")
            return t

        # Section header 【...】
        if s.startswith("【") and "】" in s:
            t = Text()
            t.append("  ◆  ", style="bold bright_yellow")
            t.append(s, style="bold bright_yellow")
            return t

        # Numbered idiom list  1. ... — ...
        m = re.match(r"^(\d{1,2})\.\s+(.+)", s.strip())
        if m:
            num, rest = m.group(1), m.group(2)
            t = Text()
            t.append(f"  {num.zfill(2)}. ", style="bold bright_cyan")
            # split at em-dash or regular dash followed by space
            parts = re.split(r"\s*[—–-]{1,2}\s*", rest, 1)
            if len(parts) == 2:
                t.append(parts[0], style="bold white")
                t.append("  —  ", style="dim")
                # try to split 含义 and 场景/地区
                sub = re.split(r"\|\s*(?:场景|地区)：", parts[1])
                meaning = sub[0].replace("含义：", "").strip()
                t.append(meaning, style="bright_cyan")
                if len(sub) == 2:
                    t.append("   📍 ", style="dim")
                    t.append(sub[1].strip(), style="dim bright_green")
            else:
                t.append(rest, style="white")
            return t

        # Empty line
        if not s:
            return None

        # Regular paragraph text
        t = Text("  " + s, style="white")
        return t

    # ── Beauty theme ──────────────────────────────────────────────
    def _beauty(self, raw: str):
        s = raw.rstrip()

        if s and all(c in "━─═" for c in s):
            return Text(s, style="bright_magenta dim")

        if s.startswith("【") and "】" in s:
            t = Text()
            t.append("  ♡  ", style="bold bright_magenta")
            t.append(s, style="bold bright_magenta")
            return t

        if s.startswith("💡"):
            t = Text()
            t.append(s, style="bold bright_yellow")
            return t

        if s.startswith("🎨"):
            t = Text()
            t.append(s, style="bold bright_cyan")
            return t

        # Numbered steps
        m = re.match(r"^(Step\s*\d+|步骤\s*\d+|\d+[\.、])\s*(.+)", s.strip())
        if m:
            t = Text()
            t.append(f"  {m.group(1)} ", style="bold bright_magenta")
            t.append(m.group(2), style="bright_white")
            return t

        # Bullet points
        if re.match(r"^[-·•]", s.strip()):
            t = Text()
            t.append("  ✦ ", style="bright_magenta")
            t.append(s.lstrip("-·• "), style="white")
            return t

        # 注意事项 block
        if s.startswith("注意") or s.startswith("⚠"):
            return Text("  " + s, style="dim bright_red")

        if not s:
            return None

        return Text("  " + s, style="bright_white")

    # ── Research theme ────────────────────────────────────────────
    def _research(self, raw: str):
        s = raw.rstrip()

        if s and all(c in "━─═" for c in s):
            return Text(s, style="bright_cyan dim")

        # Paper card header  📄 论文 N
        if "📄" in s:
            t = Text()
            t.append("\n")
            t.append(f"  {s}  ", style="bold white on navy_blue")
            t.append("\n")
            return t

        icon_styles = {
            "📌": ("bold bright_red",     ""),
            "📖": ("bold bright_yellow",  "bold bright_white"),
            "📰": ("bold bright_cyan",    "bright_cyan"),
            "📊": ("bold bright_green",   "bright_green"),
            "📝": ("bold white",          "white"),
            "🔗": ("bold bright_magenta", "bright_magenta"),
        }
        for icon, (icon_style, body_style) in icon_styles.items():
            if s.startswith(icon):
                key_end = s.find("：") + 1 if "：" in s else len(icon) + 2
                key_part = s[:key_end]
                body_part = s[key_end:]
                t = Text()
                t.append("  ")
                t.append(key_part, style=icon_style)
                if body_part:
                    t.append(body_part, style=body_style or "white")
                return t

        if not s:
            return None

        return Text("  " + s, style="white")


# ══════════════════════════════════════════════════════════════════
#  BEAUTIFUL UI COMPONENTS
# ══════════════════════════════════════════════════════════════════

WEEKDAY_CN = {
    "Monday":"周一","Tuesday":"周二","Wednesday":"周三",
    "Thursday":"周四","Friday":"周五","Saturday":"周六","Sunday":"周日",
}

def print_main_header():
    now = datetime.now()
    date_str  = now.strftime("%Y年%m月%d日")
    day_cn    = WEEKDAY_CN.get(now.strftime("%A"), "")

    # ── Gradient title ────────────────────────────────────────────
    title = Text(justify="center")
    for ch, st in zip("每日学习助手小队", [
        "bold bright_red","bold bright_yellow","bold bright_green",
        "bold bright_cyan","bold bright_blue","bold bright_magenta",
        "bold bright_red","bold bright_yellow",
    ]):
        title.append(ch, style=st)

    sub = Text("  Daily Learning Squad  ", style="dim white", justify="center")
    date_txt = Text(justify="center")
    date_txt.append("📅  ", style="bright_yellow")
    date_txt.append(date_str, style="bold white")
    date_txt.append(f"  {day_cn}", style="bold bright_cyan")

    content = Text(justify="center")
    content.append_text(title)
    content.append("\n")
    content.append_text(sub)
    content.append("\n\n")
    content.append_text(date_txt)

    console.print(Panel(
        Padding(Align.center(content), (1, 6)),
        box=box.DOUBLE_EDGE,
        border_style="bright_blue",
    ))
    console.print()


def print_agent_header(name: str, subtitle: str, emoji: str, color: str):
    t = Text()
    t.append(f"{emoji}  ", style="bold")
    t.append(name, style=f"bold {color}")
    t.append("   │   ", style="dim white")
    t.append(subtitle, style="dim white")
    console.print()
    console.print(Panel(
        Padding(t, (0, 1)),
        box=box.ROUNDED,
        border_style=color,
    ))
    console.print()


def print_done_bar(color: str = "bright_green"):
    console.print(Rule(
        Text("✦  Done & dusted  ✦", style=f"bold {color}"),
        style=color,
    ))
    console.print()


def print_menu():
    rows = [
        ("1", "bright_blue",    "📚", "英语学习助手",
         "10条美式英语地道表达 + 中英对照"),
        ("2", "bright_magenta", "💄", "美妆学习助手",
         "棱橄榄皮 · 圆脸专属今日推送"),
        ("3", "bright_cyan",    "🔬", "科研文献助手",
         "今日3篇应用语言学论文推荐"),
        ("4", "bright_yellow",  "🚀", "全部运行",
         "一键获取今日所有推送"),
        ("0", "dim white",      "👋", "退出", "See ya!"),
    ]

    table = Table(
        box=box.ROUNDED,
        border_style="bright_blue dim",
        show_header=False,
        padding=(0, 3),
        expand=False,
        title=Text("✦  今天想学啥？Pick your agent  ✦", style="bold bright_yellow"),
        title_style="bold bright_yellow",
    )
    table.add_column("key",   width=4,  justify="center")
    table.add_column("icon",  width=4,  justify="center")
    table.add_column("agent", min_width=18)
    table.add_column("desc",  style="dim", min_width=32)

    for key, color, icon, agent, desc in rows:
        table.add_row(
            Text(f"[{key}]", style=f"bold {color}"),
            Text(icon),
            Text(agent, style=f"bold {color}"),
            Text(desc),
        )

    console.print(Align.center(table))
    console.print()


# ══════════════════════════════════════════════════════════════════
#  AGENT RUNNERS
# ══════════════════════════════════════════════════════════════════

def run_english_agent():
    print_agent_header("英语学习助手", "English Learning Assistant",
                       "📚", "bright_blue")

    today   = datetime.now().strftime("%Y年%m月%d日")
    weekday = datetime.now().weekday()
    topics  = [
        "职场与成功（career, ambition, perseverance）",
        "人生哲理与智慧（life wisdom, choices, consequences）",
        "人际关系与友谊（friendship, trust, communication）",
        "时间与金钱（time, money, priorities）",
        "自然与环境（nature, seasons, environment）",
        "挑战与逆境（adversity, resilience, change）",
        "知识与学习（knowledge, curiosity, growth）",
    ]
    prompt = (
        f"今天是{today}。请围绕主题「{topics[weekday]}」，"
        "为我提供今日的10条美式英语地道表达学习内容，"
        "优先选美国人日常真实在用的口语和俚语，"
        "按照规定格式输出完整内容。"
    )

    streamer = SmartStreamer("english")
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=2500,
        system=ENGLISH_AGENT_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            streamer.feed(chunk)
    streamer.flush()
    print_done_bar("bright_blue")


def run_beauty_agent():
    print_agent_header("美妆学习助手", "Beauty Learning Assistant",
                       "💄", "bright_magenta")

    today   = datetime.now().strftime("%Y年%m月%d日")
    weekday = datetime.now().weekday()
    days    = ["周一","周二","周三","周四","周五","周六","周日"]
    themes  = ["底妆技巧","眼妆教程","修容高光","唇妆色号",
               "护肤成分解析","完整妆容教程","护肤小贴士"]
    prompt = (
        f"今天是{today}（{days[weekday]}）。"
        f"请围绕今日主题「{themes[weekday]}」，"
        "为我提供针对棱橄榄皮+圆脸的个性化美妆内容推送。"
    )

    streamer = SmartStreamer("beauty")
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1800,
        system=BEAUTY_AGENT_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            streamer.feed(chunk)
    streamer.flush()
    print_done_bar("bright_magenta")


def run_research_agent():
    print_agent_header("科研文献助手", "Research Literature Assistant",
                       "🔬", "bright_cyan")

    today   = datetime.now().strftime("%Y年%m月%d日")
    day_mod = datetime.now().day % 3
    focuses = [
        "今天请优先推荐与【评估与语言权力】相关的论文（washback、epistemic injustice、AP Chinese、CDA），搭配1篇其他方向。",
        "今天请优先推荐与【课堂互动与中介】相关的论文（translanguaging、LRE、peer interaction in CSL、MICM），搭配1篇其他方向。",
        "今天请优先推荐与【教师与制度】相关的论文（teacher vulnerability、emotional labor、DLI policy、autoethnography），搭配1篇其他方向。",
    ]
    prompt = (
        f"今天是{today}，请为我推荐今日3篇学术论文。\n"
        f"{focuses[day_mod]}\n"
        "请按照规定格式逐一呈现每篇论文的完整信息。"
    )

    streamer = SmartStreamer("research")
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=RESEARCH_AGENT_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            streamer.feed(chunk)
    streamer.flush()
    print_done_bar("bright_cyan")


# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    console.clear()
    print_main_header()

    while True:
        print_menu()
        choice = console.input(
            Text.assemble(
                ("  Your pick", "bold bright_yellow"),
                (" (0–4)", "dim"),
                (" ▶  ", "bold bright_yellow"),
            )
        ).strip()

        if choice == "0":
            console.print()
            console.print(Panel(
                Align.center(Text("Catch you later! 每天进步一点点 🌱", style="bold bright_green")),
                border_style="bright_green",
                padding=(1, 8),
            ))
            console.print()
            break
        elif choice == "1":
            run_english_agent()
        elif choice == "2":
            run_beauty_agent()
        elif choice == "3":
            run_research_agent()
        elif choice == "4":
            run_english_agent()
            run_beauty_agent()
            run_research_agent()
            console.print(Rule(
                Text("✦  That's a wrap — 今日所有推送已完成！  ✦", style="bold bright_yellow"),
                style="bright_yellow",
            ))
        else:
            console.print(Text(
                "  ⚠️  Oops! That's not a thing — please enter 0–4",
                style="bold bright_red",
            ))
        console.print()


if __name__ == "__main__":
    main()
