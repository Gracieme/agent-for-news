#!/usr/bin/env python3
"""
daily_email.py — 每日学习内容 HTML 邮件发送器
丹佛时间每天早 8:00 自动运行（由 cron 调用）
"""

import os
import re
import html
import time
import logging
import urllib.parse
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


RESEARCH_RELEVANCE_SYSTEM = """你是一位应用语言学博士研究助手。用户的研究背景：
【方向一】评估与语言权力：AP Chinese、assessment、epistemic injustice、washback、CDA
【方向二】课堂互动与中介：CSL、translanguaging、LRE、peer interaction、MICM
【方向三】教师与制度：DLI、teacher vulnerability、emotional labor、autoethnography

给你一篇真实论文的标题和摘要，请用2-3句中文说明它与上述研究方向的关联性。只输出关联性说明，不要其他内容。"""


# ══════════════════════════════════════════════════════════════════
#  CONTENT GENERATION
# ══════════════════════════════════════════════════════════════════

WEEKDAY_CN = {
    "Monday":"周一","Tuesday":"周二","Wednesday":"周三",
    "Thursday":"周四","Friday":"周五","Saturday":"周六","Sunday":"周日",
}

def collect(system: str, user_prompt: str, max_tokens: int = 3500, **kwargs) -> str:
    """Call Claude API and return full streamed text."""
    for attempt in range(3):
        try:
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
        except anthropic.APIStatusError as e:
            if e.status_code == 500 and attempt < 2:
                wait = 10 * (attempt + 1)
                log.warning("Anthropic 500 error, retrying in %ds (attempt %d/3)…", wait, attempt + 1)
                time.sleep(wait)
            else:
                raise


def gen_english(today: str, weekday: int) -> str:
    topics = [
        # 职场 & 职业发展
        "职场沟通与汇报（meetings, updates, feedback loops）",
        "求职与面试（job hunting, interviews, networking）",
        "升职与谈薪（promotion, salary negotiation, self-advocacy）",
        "远程办公与协作（remote work, async communication, Slack culture）",
        "职场八卦与办公室政治（office drama, gossip, workplace dynamics）",
        # 人际关系 & 社交
        "友谊与闺蜜（friendship, bestie, hanging out）",
        "约会与恋爱（dating, relationships, situationships）",
        "分手与疗愈（breakups, moving on, self-care）",
        "家庭与代际（family dynamics, generational clash, holidays）",
        "社交媒体与网络文化（social media slang, viral moments, online drama）",
        # 日常生活 & 消费
        "购物与砍价（shopping, deals, buyer's remorse）",
        "餐厅点餐与美食（ordering food, foodie culture, tipping）",
        "出行与旅行（travel, road trips, tourist vs local）",
        "租房与买房（housing market, landlords, roommates）",
        "理财与省钱（budgeting, frugal hacks, financial anxiety）",
        # 情绪 & 心理健康
        "压力与焦虑（stress, burnout, anxiety spirals）",
        "自我提升与习惯养成（self-improvement, routines, accountability）",
        "边界感与说不（setting boundaries, saying no, people-pleasing）",
        "拖延与自律（procrastination, ADHD brain, getting things done）",
        "正念与慢生活（mindfulness, slowing down, digital detox）",
        # 流行文化 & 娱乐
        "追剧与电影（binge-watching, plot twists, fandoms）",
        "音乐与演唱会（concerts, playlists, music taste）",
        "体育与球赛（sports culture, game day, trash talk）",
        "健身与运动（gym talk, workout slang, fitness culture）",
        "游戏与科技（gaming slang, tech talk, app culture）",
        # 校园 & 学习
        "大学校园生活（campus culture, college slang, dorm life）",
        "考试与截止日期（exams, deadlines, academic pressure）",
        "留学与文化冲击（study abroad, culture shock, homesickness）",
        # 社会议题 & 时事
        "环保与可持续（sustainability, climate anxiety, green living）",
        "多元文化与包容（diversity, code-switching, microaggressions）",
        "Gen Z 与千禧代代沟（generational differences, OK boomer, adulting）",
        "网络梗与表情包文化（meme culture, internet humor, viral slang）",
        # 节日 & 季节
        "节日聚会与礼物（holiday parties, gift-giving, awkward gatherings）",
        "夏日与户外（summer vibes, BBQ, outdoor activities）",
        "冬天与室内（cozy season, winter blues, hot drinks）",
        "新年计划与目标（New Year resolutions, fresh starts, goal-setting）",
    ]
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday
    topic = topics[day_of_year % len(topics)]
    return collect(
        ENGLISH_SYSTEM,
        f"今天是{today}。请围绕主题「{topic}」，"
        "为我提供今日的10条地道英语表达学习内容，优先选真实日常在用的口语、俚语和惯用语，"
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


def _openalex_search(query: str, limit: int = 3, page: int = 1) -> list:
    """Search OpenAlex API (no key required) and return work dicts."""
    import urllib.request, json as _json
    url = (
        f"https://api.openalex.org/works"
        f"?search={urllib.parse.quote(query)}"
        f"&filter=publication_year:2019-2025"
        f"&per_page={limit}&page={page}&sort=relevance_score:desc"
        f"&select=title,authorships,publication_year,abstract_inverted_index,cited_by_count,primary_location,doi"
        f"&mailto=research-emailer@example.com"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "research-emailer/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return _json.loads(r.read())["results"]


def _reconstruct_abstract(inverted_index: dict) -> str:
    """Reconstruct abstract text from OpenAlex inverted index format."""
    if not inverted_index:
        return ""
    words = [""] * (max(pos for positions in inverted_index.values() for pos in positions) + 1)
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words)


def _paper_to_text(paper: dict, n: int, relevance: str) -> str:
    authors = ", ".join(
        a["author"]["display_name"]
        for a in paper.get("authorships", [])[:3]
        if a.get("author")
    )
    if len(paper.get("authorships", [])) > 3:
        authors += " et al."
    title    = paper.get("title", "")
    year     = paper.get("publication_year", "")
    cites    = paper.get("cited_by_count", 0)
    venue    = ((paper.get("primary_location") or {}).get("source") or {}).get("display_name", "—")
    doi      = paper.get("doi", "")
    abstract = _reconstruct_abstract(paper.get("abstract_inverted_index") or {})
    abstract_short = (abstract[:400] + "…") if len(abstract) > 400 else abstract or "摘要不可用"

    if doi:
        link_url  = doi if doi.startswith("http") else f"https://doi.org/{doi}"
        link_text = doi.replace("https://doi.org/", "")
    else:
        q = urllib.parse.quote(title)
        link_url  = f"https://scholar.google.com/scholar?q={q}"
        link_text = "Google Scholar"

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📄 论文 {n}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 作者：{authors}\n"
        f"📖 标题：{title}\n"
        f"📰 期刊：{venue}\n"
        f"📅 年份：{year}\n"
        f"📊 引用量：{cites} 次\n"
        f"📝 摘要：{abstract_short}\n"
        f"🔗 与本研究的关联性：{relevance}\n"
        f"🆔 DOI：{link_text}|{link_url}\n"
    )


def gen_research(today: str) -> str:
    queries = [
        # 语言评估 & 考试效度
        "language assessment validity washback Chinese EFL",
        "high-stakes testing fairness equity language proficiency",
        "CET college English test China validity construct",
        "language testing bias standard exam score interpretation",
        # 批判性思维
        "critical thinking EFL Chinese university students",
        "epistemic injustice language assessment washback Chinese",
        "critical literacy academic writing second language",
        "argument writing L2 English reasoning skills",
        # 课堂互动 & 身份
        "translanguaging peer interaction Chinese as second language classroom",
        "identity negotiation multilingual classroom discourse",
        "classroom interaction talk participation second language",
        "language socialization heritage learners community",
        # 教师情感 & 政策
        "teacher emotional labor dual language immersion policy autoethnography",
        "language policy bilingual education teacher beliefs",
        "teacher identity professional development language classroom",
        "emotion regulation teacher burnout language instruction",
        # 写作 & 反馈
        "written corrective feedback L2 writing revision",
        "peer feedback academic writing EFL Chinese students",
        "automated essay scoring NLP language learning",
        "genre writing instruction English for academic purposes",
    ]
    now = datetime.now()
    # 用年积日而不是月内日期，保证整年内不重复
    day_of_year = now.timetuple().tm_yday
    query_idx = day_of_year % len(queries)
    query = queries[query_idx]
    # 每轮完整循环后翻到下一页，避免同一查询反复返回相同结果
    page = (day_of_year // len(queries)) + 1
    log.info(f"   OpenAlex 搜索: {query} (第 {page} 页)")

    try:
        papers = _openalex_search(query, limit=3, page=page)
    except Exception as ex:
        log.warning(f"   OpenAlex 请求失败: {ex}")
        papers = []

    if not papers:
        return "（今日无法获取论文数据，请稍后查看）"

    parts = []
    for i, paper in enumerate(papers, 1):
        title    = paper.get("title", "")
        abstract = _reconstruct_abstract(paper.get("abstract_inverted_index") or {})
        try:
            relevance = collect(
                RESEARCH_RELEVANCE_SYSTEM,
                f"标题：{title}\n摘要：{abstract[:600]}",
                max_tokens=200,
            ).strip()
        except Exception:
            relevance = "（关联性分析暂不可用）"
        parts.append(_paper_to_text(paper, i, relevance))

    return "\n".join(parts)


# ══════════════════════════════════════════════════════════════════
#  NEWS FETCHER
# ══════════════════════════════════════════════════════════════════

NEWS_REGIONS = {
    # 大中华区：兼收官方、独立港媒、台湾、BBC、RFA，呈现多元视角
    "🇨🇳 大中华视角": [
        ("南华早报(独立港媒)", "https://www.scmp.com/rss/91/feed"),
        ("台北时报(台湾)",     "https://www.taipeitimes.com/xml/index.rss"),
        ("BBC中国报道",        "http://feeds.bbci.co.uk/news/world/asia/china/rss.xml"),
        ("中国日报(官方)",     "https://www.chinadaily.com.cn/rss/china_rss.xml"),
        ("自由亚洲电台",       "https://www.rfa.org/english/news/china/rss2.xml"),
    ],
    # 北美：左中右立场兼顾，加入外交政策专业媒体
    "🇺🇸 北美视角": [
        ("NPR(公共广播,中偏左)",    "https://feeds.npr.org/1001/rss.xml"),
        ("AP通讯社(中立)",          "https://rsshub.app/apnews/topics/apf-topnews"),
        ("华尔街日报(中右)",        "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
        ("The Atlantic(中偏左)",    "https://feeds.feedburner.com/TheAtlantic"),
        ("外交政策(外交专业)",      "https://foreignpolicy.com/feed/"),
    ],
    # 欧洲：英/德/法/泛欧，立场各异
    "🌍 欧洲视角": [
        ("卫报(英国,中左)",   "https://www.theguardian.com/world/rss"),
        ("DW(德国,中立)",     "https://rss.dw.com/rdf/rss-en-world"),
        ("法国24(法国)",      "https://www.france24.com/en/rss"),
        ("欧洲新闻台(泛欧)",  "https://www.euronews.com/rss"),
        ("BBC世界",           "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ],
    # 亚太：新加坡/日/澳/印度，地区多元
    "🌏 亚太视角": [
        ("海峡时报(新加坡)",  "https://www.straitstimes.com/news/asia/rss.xml"),
        ("日本时报",          "https://www.japantimes.co.jp/news/feed/"),
        ("澳洲ABC新闻",       "https://www.abc.net.au/news/feed/51120/rss.xml"),
        ("印度教徒报",        "https://www.thehindu.com/news/international/?service=rss"),
        ("菲律宾每日问询者",  "https://newsinfo.inquirer.net/feed"),
    ],
    # 新西兰：公共广播/主流报纸/独立媒体，全面呈现本地视角
    "🇳🇿 新西兰视角": [
        ("RNZ(新西兰国家广播)", "https://www.rnz.co.nz/rss/news.xml"),
        ("新西兰先驱报",        "https://www.nzherald.co.nz/arcio/rss/"),
        ("Stuff新闻",           "https://www.stuff.co.nz/rss"),
        ("The Spinoff(独立媒体)","https://thespinoff.co.nz/feed"),
        ("Newsroom(深度报道)",  "https://www.newsroom.co.nz/feed"),
    ],
    # 中东/非洲/全球南方：代表性强的独立声音
    "🌐 中东·非洲·全球南方": [
        ("半岛电视台(卡塔尔)", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("BBC非洲",            "http://feeds.bbci.co.uk/news/world/africa/rss.xml"),
        ("BBC中东",            "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml"),
        ("路透社世界",         "https://feeds.reuters.com/reuters/worldNews"),
        ("BBC拉丁美洲",        "http://feeds.bbci.co.uk/news/world/latin_america/rss.xml"),
    ],
}


def _fetch_rss(url: str, limit: int = 10) -> list:
    """Fetch RSS feed and return list of {title, link, source} dicts."""
    try:
        import feedparser
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:limit]:
            title = (entry.get("title") or "").strip()
            link  = (entry.get("link")  or "").strip()
            if title and link:
                items.append({"title": title, "link": link})
        return items
    except Exception as ex:
        log.warning(f"   RSS 获取失败 ({url}): {ex}")
        return []


def gen_news(today: str) -> list:
    """
    Fetch top-5 news per region via RSS, translate titles to Chinese with Claude,
    and return a list of region dicts ready for news_to_html().
    """
    # Step 1: collect raw items per region (5 per region, 1 per source to ensure diversity)
    region_raw: dict[str, list] = {}
    for region, feeds in NEWS_REGIONS.items():
        seen_titles: set = set()
        items: list = []
        for src_name, url in feeds:
            if len(items) >= 5:
                break
            for entry in _fetch_rss(url, limit=8):
                title_lower = entry["title"].lower()[:80]
                if title_lower not in seen_titles:
                    seen_titles.add(title_lower)
                    entry["source"] = src_name
                    items.append(entry)
                    break  # one item per source to ensure all sources are represented
        region_raw[region] = items[:5]

    # Step 2: batch-translate all titles with one Claude call
    all_items = []
    for region, items in region_raw.items():
        for item in items:
            all_items.append({"region": region, **item})

    if not all_items:
        return []

    numbered = "\n".join(
        f"[{i+1}] {it['title']}" for i, it in enumerate(all_items)
    )
    prompt = (
        "下面是今日各媒体新闻标题列表，请为每条提供：\n"
        "① 中文标题（如原标题已是中文则直接保留，否则翻译）\n"
        "② 一句话中文简介，25字以内，概括新闻要点；\n"
        "   若能判断该媒体立场（官方/独立/左/右/中立），\n"
        "   可在简介末尾用括号注明，如（官方视角）（西方主流）（批评性报道）等，\n"
        "   无法判断则不加\n\n"
        "输出格式严格按照（每条占一行，用|分隔，不要其他内容）：\n"
        "[序号]|中文标题|简介\n\n"
        "原始标题：\n" + numbered
    )
    try:
        raw = collect("你是专业新闻翻译和摘要助手。", prompt, max_tokens=1200).strip()
    except Exception as ex:
        log.warning(f"   新闻翻译失败: {ex}")
        raw = ""

    # Parse Claude's output
    translations: dict[int, tuple[str, str]] = {}
    for line in raw.splitlines():
        m = re.match(r"\[(\d+)\]\s*\|([^|]+)\|(.+)", line.strip())
        if m:
            idx      = int(m.group(1)) - 1
            cn_title = m.group(2).strip()
            summary  = m.group(3).strip()
            translations[idx] = (cn_title, summary)

    # Step 3: merge translations back
    for i, item in enumerate(all_items):
        cn_title, summary = translations.get(i, ("", ""))
        item["title_cn"] = cn_title or item["title"]
        item["summary"]  = summary

    # Step 4: re-group by region
    region_result: dict[str, list] = {r: [] for r in NEWS_REGIONS}
    for item in all_items:
        region_result[item["region"]].append(item)

    return [
        {"region": region, "items": region_result[region]}
        for region in NEWS_REGIONS
        if region_result[region]
    ]


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

                # DOI field → render as clickable link (format: "link_text|link_url")
                if icon == "🆔":
                    raw = body_part.strip()
                    if "|" in raw:
                        link_text, link_url = raw.split("|", 1)
                    else:
                        q = urllib.parse.quote(current_title or raw)
                        link_text = "Google Scholar 搜索"
                        link_url  = f"https://scholar.google.com/scholar?q={q}"
                    links_html = (
                        f'<a href="{e(link_url)}" target="_blank" '
                        f'style="color:#1a73e8;text-decoration:none">🔍 {e(link_text)}</a>'
                    )
                    parts.append(
                        f'<table width="100%" cellpadding="0" cellspacing="0" '
                        f'style="margin:7px 0;border-collapse:collapse"><tr>'
                        f'<td width="88" valign="top" style="color:{color};font-weight:600;'
                        f'font-size:13px;padding-right:8px;white-space:nowrap">{e(key_part)}</td>'
                        f'<td valign="top" style="font-size:13px;line-height:1.7">'
                        f'{links_html}'
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

def news_to_html(region_groups: list) -> str:
    """Render news region groups as HTML for email and website."""
    if not region_groups:
        return '<p style="color:#aaa;text-align:center;padding:20px">今日暂无新闻数据</p>'

    region_colors = {
        "🇨🇳 中国":   ("#c62828", "#fff5f5", "#ffd9d9"),
        "🇺🇸 美国":   ("#1565c0", "#f0f4ff", "#d0deff"),
        "🇳🇿 新西兰": ("#2e7d32", "#f0fff4", "#c8e6c9"),
        "🌍 欧洲":    ("#6a1b9a", "#faf0ff", "#e1bee7"),
        "🌏 亚洲":    ("#e65100", "#fff8f0", "#ffe0b2"),
        "🌐 其他地区":("#00695c", "#f0fafa", "#b2dfdb"),
    }
    default_color = ("#455a64", "#f5f5f5", "#cfd8dc")

    parts = []
    for group in region_groups:
        region = group["region"]
        items  = group["items"]
        if not items:
            continue
        hdr_color, bg_color, tag_bg = region_colors.get(region, default_color)

        parts.append(
            f'<div style="margin-bottom:22px">'
            f'<div style="background:{hdr_color};color:#fff;font-weight:700;font-size:14px;'
            f'padding:7px 14px;border-radius:8px 8px 0 0;letter-spacing:0.5px">'
            f'{html.escape(region)}</div>'
            f'<div style="background:{bg_color};border:1px solid {tag_bg};border-top:none;'
            f'border-radius:0 0 8px 8px;padding:4px 0">'
        )
        for item in items:
            en_title = html.escape(item.get("title", ""))
            cn_title = html.escape(item.get("title_cn", ""))
            summary  = html.escape(item.get("summary", ""))
            source   = html.escape(item.get("source", ""))
            link     = item.get("link", "#")

            parts.append(
                f'<div style="padding:10px 14px;border-bottom:1px solid {tag_bg}">'
                # Chinese title (primary, linkable)
                f'<a href="{link}" target="_blank" rel="noopener" '
                f'style="display:block;color:{hdr_color};font-weight:700;font-size:14px;'
                f'text-decoration:none;margin-bottom:3px;line-height:1.4">'
                f'{cn_title or en_title}</a>'
                # English title
                f'<div style="color:#555;font-size:12px;margin-bottom:4px;line-height:1.4">'
                f'{en_title}</div>'
                # Summary + source tag
                f'<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">'
                f'<span style="color:#777;font-size:12px;flex:1">{summary}</span>'
                f'<span style="background:{tag_bg};color:{hdr_color};font-size:11px;'
                f'padding:2px 8px;border-radius:10px;white-space:nowrap;font-weight:600">'
                f'{source}</span>'
                f'</div>'
                f'</div>'
            )
        parts.append('</div></div>')

    return "\n".join(parts)


def build_email_html(
    eng_html: str,
    bty_html: str,
    res_html: str,
    news_html: str,
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

    <!-- ══ DIVIDER ══ -->
    <div style="height:6px;background:linear-gradient(90deg,#00bcd4,#ff9800,#4caf50)"></div>

    <!-- ══ NEWS SECTION ══ -->
    <div style="background:#fafafa;border-top:5px solid #ff6f00;padding:28px 32px">
      <div style="display:flex;align-items:center;margin-bottom:20px">
        <div style="width:48px;height:48px;background:linear-gradient(135deg,#ff9800,#e65100);
          border-radius:12px;display:flex;align-items:center;justify-content:center;
          font-size:22px;flex-shrink:0">📰</div>
        <div style="margin-left:14px">
          <h2 style="margin:0;font-size:19px;color:#e65100;font-weight:700">每日全球新闻</h2>
          <p style="margin:3px 0 0;font-size:12px;color:#888;letter-spacing:0.5px">
            Daily World News &nbsp;·&nbsp; 中英双语 &nbsp;·&nbsp; 权威媒体
          </p>
        </div>
      </div>
      {news_html}
    </div>

    <!-- ══ FOOTER ══ -->
    <div style="background:#2d2d2d;border-radius:0 0 14px 14px;
      padding:20px 32px;text-align:center">
      <p style="color:#aaa;margin:0 0 6px;font-size:12px">
        🤖 &nbsp;Powered by Claude Opus 4.6 &nbsp;·&nbsp; Hits your inbox every morning at 8:00 AM Denver time
      </p>
      <p style="color:#666;margin:0;font-size:11px">
        American English &nbsp;·&nbsp; 美妆护肤 &nbsp;·&nbsp; 应用语言学科研 &nbsp;·&nbsp; 全球新闻
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

    log.info("📰 抓取每日全球新闻...")
    news_groups = gen_news(date_str)
    log.info(f"   完成，{sum(len(g['items']) for g in news_groups)} 条新闻")

    log.info("🎨 转换为 HTML...")
    eng_html  = english_to_html(eng_text)
    bty_html  = beauty_to_html(bty_text)
    res_html  = research_to_html(res_text)
    news_html = news_to_html(news_groups)

    full_html = build_email_html(eng_html, bty_html, res_html, news_html, date_str, day_cn)

    subject = f"✨ 每日学习推送 · {date_str} {day_cn}"

    log.info(f"📨 发送邮件到 {os.environ.get('EMAIL_TO', '(未配置)')}...")
    send_email(subject, full_html)
    log.info("✅ 邮件发送成功！")

    log.info("🏡 更新格雷西学习小屋网站...")
    date_key = now.strftime("%Y-%m-%d")
    save_entry(date_key, date_str, day_cn, eng_html, bty_html, res_html, news_html)
    site_path, count = rebuild_site()
    log.info(f"   网站已更新 ({count} 天记录) → {site_path}")


if __name__ == "__main__":
    main()
