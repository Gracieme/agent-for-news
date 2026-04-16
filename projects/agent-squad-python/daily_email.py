#!/usr/bin/env python3
"""
daily_email.py — 每日学习内容 HTML 邮件发送器
丹佛时间每天早 8:00 自动运行（由 cron 调用）
"""

import os
import re
import html
import json
import time
import logging
import urllib.parse
import unicodedata
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

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
- 预算：平价与中高端均可，优先推荐性价比高的选择

输出格式（必须严格遵守，每个区块都要输出）：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【今日主题】（主题名称）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

（正文：分步骤/要点展示，具体可操作，300字以上）

💡 针对你的肤质/脸型：
（专门针对棱橄榄皮+圆脸的个性化建议，至少3条）

🎨 今日品牌与产品推荐：
（必须推荐3-5款具体产品，格式：品牌名+产品名+色号（如有）+推荐理由+参考价位。
 兼顾：①国际大牌，②平价替代，③国货品牌（如花西子、完美日记、珂拉琪、INTO YOU、colorkey等））

注意事项：
- 圆脸重点：收窄横向视觉、视觉拉长脸型
- 棱橄榄皮底妆：提亮暗沉、控油遮孔
- 色彩：大地色系、棕调、暖粉、砖红——避免冷粉冷紫
- 品牌推荐要具体到产品线和色号，不能只说品牌名"""


RESEARCH_RELEVANCE_SYSTEM = """你是一位应用语言学博士研究助手。你会根据用户当前的研究画像、活跃稿件和当天的研究主线，判断一篇真实论文到底相关在哪一层。

请用 2-3 句中文完成两件事：
1. 说明这篇论文最贴近用户哪条研究主线；
2. 说明它最值得借鉴的是问题意识、理论框架、方法设计、结果表达或英文写法中的哪一点。

不要泛泛而谈。如果只是“部分相关”或“方法层相关”，要明确说出来。只输出关联性说明，不要其他内容。"""


MENTOR_SYSTEM = """你是一位应用语言学教授，也是用户的博士生导师。用户是第一年博士生，想学会如何欣赏一篇好论文、如何拆解论文结构、以及如何写出更像期刊论文的英文。

你会结合用户当前正在写的稿件与研究主线来带读，而不是给出泛泛的论文赏析。

你只能依据用户提供的题目、作者、年份、期刊、检索主题和摘要来讲解；不要假装看过全文。凡是无法直接从摘要确定、但你做了合理推断的地方，必须明确写出“基于摘要推断”。

你的任务不是泛泛夸奖，而是像导师带读一样，帮助学生学会：
1. 这篇论文为什么值得读
2. 作者的论证骨架是怎么搭起来的
3. 哪些英文句子/句式值得抄写和模仿
4. 今天可以立刻做什么小练习

输出格式必须严格如下，不要添加格式说明之外的内容：

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎓 导师带读
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 焦点论文：作者（年份）. 标题
📰 发表信息：期刊/来源
🔗 论文入口：显示文字|链接
📚 论文类型：必须判断为「理论文 / 实证文 / 混合型」，不确定时注明“基于摘要推断”
🗣 用人话说：用一句完全不带术语的话说，这篇文章到底在干什么
🏅 这篇最值得学的是：必须从「idea / 文献综述 / 方法设计 / 研究实操 / 写作表达」里明确选 1-2 项，不许全选
👓 今天主评维度：必须只选 1 个。若是理论文，优先从「idea / 文献综述」里选；若是实证文，优先从「方法设计 / 研究实操」里选；混合型再做判断
👀 先品一品：
1. ...
2. ...
🧩 拆解它是怎么写的：
1. 先指出作者在这个维度上具体做了什么动作
2. 再指出这种写法为什么有效
3. 最后告诉学生写自己的论文时可以直接借什么结构/句法/推进顺序
🎯 今日训练重点：一句话说明今天主要学什么写作能力
🧭 导师开场：用2-4句中文告诉学生为什么今天先读这篇，以及读的时候该盯住什么
🦴 文章骨架：
1. ...
2. ...
3. ...
❓ 导师追问你：
❓ 问题 1：这篇不是“讲了什么”，而是“解决了什么”？
🧑‍🏫 导师回答：...
❓ 问题 2：如果没有这篇，领域里缺的到底是什么？
🧑‍🏫 导师回答：...
❓ 问题 3：作者最聪明的一步是什么？
🧑‍🏫 导师回答：...
❓ 问题 4：这篇最可能被批评的地方是什么？
🧑‍🏫 导师回答：...
❓ 问题 5：你最想偷哪一句、哪一段、哪种推进方式？
🧑‍🏫 导师回答：...
❓ 问题 6：这篇对你的论文，不是“启发了我”，而是“我能立刻拿来怎么写”？
🧑‍🏫 导师回答：...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 好句 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔤 原句：英文短句，尽量直接摘自摘要，控制在18个英文词以内
💬 这句其实在说：用中文白话翻译，不要照字面硬译，要让一年级博士生一看就懂
🔍 为什么强：说明这句好在哪里（如界定问题、压缩贡献、建立对比、控制语气、显示立场）
🛠 你要学的写法：指出可以模仿的具体写作动作
🧪 你的仿写模板：给一个可替换内容的英文模板句

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 好句 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔤 原句：...
💬 这句其实在说：...
🔍 为什么强：...
🛠 你要学的写法：...
🧪 你的仿写模板：...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 好句 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔤 原句：...
💬 这句其实在说：...
🔍 为什么强：...
🛠 你要学的写法：...
🧪 你的仿写模板：...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✍️ 今日练习
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 给一个15分钟内可完成的小写作任务
2. 给一个“如何检查自己有没有写好”的自查标准
3. 给一句导师式鼓励，但不要空泛

要求：
- 把用户当第一年博士生，不假设他已经熟悉 translanguaging、CLIL、ICLHE、multimodality 之类术语
- 每个核心判断先讲白话，再讲学术判断
- 术语第一次出现时，尽量立刻用括号或短句解释
- 整体中文讲解要具体、可操作、像导师批注
- 英文模板句要自然、学术、可直接仿写
- 好句优先选“研究问题、理论定位、贡献表达、结果概括、立场控制”这几类
- 好句讲解必须先让学生听懂句子在说什么，再讲句子为什么写得好
- 必须先判断论文类型，再决定学习重点
- “这篇最值得学的是”必须有判断，不要每次都说每一项都强
- “今天主评维度”只能有 1 个，不要摇摆；并且要服从论文类型：理论文看 idea/综述，实证文看 方法设计/研究实操
- “先品一品”要像导师判断论文长板和短板，不要变成重复摘要
- “拆解它是怎么写的”必须讲写法，不要只讲内容
- “导师追问你”必须逐题回答，不要变成口号；每题后面都必须紧跟一条“🧑‍🏫 导师回答：”
- “🧑‍🏫 导师回答”要先直接下判断，再指出你据以判断的题目/摘要线索；若只能推断，明确写“基于摘要推断”
- 答案要逼学生从“懂内容”走向“会判断”，不要把问题原样抛回给学生
- 不要输出长篇英文原文，不要超过3句引用
- 不要使用“非常厉害”“很高级”这种空话"""


# ══════════════════════════════════════════════════════════════════
#  CONTENT GENERATION
# ══════════════════════════════════════════════════════════════════

WEEKDAY_CN = {
    "Monday":"周一","Tuesday":"周二","Wednesday":"周三",
    "Thursday":"周四","Friday":"周五","Saturday":"周六","Sunday":"周日",
}


RESEARCH_PROFILE_FILE = Path(__file__).parent / "research_profile.json"


GENERIC_RESEARCH_QUERIES = [
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


def _exploration_research_topics() -> list[dict]:
    return [
        {
            "name": "Broad scan: sociolinguistics, bilingualism, and identity",
            "query": "sociolinguistics bilingualism multilingualism identity discourse",
            "fallback_queries": [
                "bilingualism identity sociolinguistics",
                "multilingualism discourse identity language",
                "language and identity bilingual education",
            ],
            "anchors": [],
            "writing_focus": "看概念怎么收束，如何把 identity / multilingualism 写得既大又不散",
            "why": "把你的应用语言学根基向社会语言学、身份与双语研究自然延展",
            "keywords": ["sociolinguistics", "bilingualism", "multilingualism", "identity", "discourse"],
        },
        {
            "name": "Broad scan: language policy, ideology, and critical discourse",
            "query": "language policy ideology discourse critical multilingual education",
            "fallback_queries": [
                "language policy ideology discourse",
                "critical discourse multilingual education",
                "linguistic ideology education policy",
            ],
            "anchors": [],
            "writing_focus": "看制度、话语、意识形态怎样被写成有证据链的论证",
            "why": "覆盖你从考试、公平、制度走向更大社会语言学问题的那一条线",
            "keywords": ["language policy", "ideology", "critical discourse", "multilingual education"],
        },
        {
            "name": "Broad scan: translanguaging, digital discourse, and multilingual practice",
            "query": "translanguaging digital discourse multilingual practice sociolinguistics",
            "fallback_queries": [
                "digital discourse multilingual practice translanguaging",
                "social media multilingual discourse identity",
                "translanguaging digital communication sociolinguistics",
            ],
            "anchors": [],
            "writing_focus": "看新议题怎样写得不浮，不把数字平台写成概念堆叠",
            "why": "保留你对平台、数字语言实践与社会语言学转向的兴趣",
            "keywords": ["translanguaging", "digital discourse", "multilingual practice", "sociolinguistics"],
        },
        {
            "name": "Broad scan: language assessment, fairness, and validity",
            "query": "language assessment fairness validity washback critical language testing",
            "fallback_queries": [
                "language assessment fairness validity",
                "critical language testing washback",
                "assessment literacy language classroom",
            ],
            "anchors": [],
            "writing_focus": "看问题意识、construct界定、fairness/validity怎么写得稳",
            "why": "保留你在评估、公平、制度批判这条大线上的广度，不只盯某一篇稿子",
            "keywords": ["language assessment", "fairness", "validity", "washback", "critical language testing"],
        },
        {
            "name": "Broad scan: classroom interaction, mediation, and participation",
            "query": "classroom interaction mediation participation peer talk sociocultural theory",
            "fallback_queries": [
                "peer interaction sociocultural theory classroom discourse",
                "language-related episodes negotiation of meaning classroom interaction",
                "interactional competence classroom discourse",
            ],
            "anchors": [],
            "writing_focus": "看interaction数据怎么被写成机制，而不是零散例子",
            "why": "保留你对课堂互动、参与、社会文化中介的广义关注",
            "keywords": ["classroom interaction", "mediation", "participation", "peer interaction"],
        },
        {
            "name": "Broad scan: academic writing, feedback, and revision",
            "query": "academic writing feedback revision second language writing",
            "fallback_queries": [
                "written corrective feedback second language writing",
                "peer feedback revision academic writing",
                "genre writing instruction EAP",
            ],
            "anchors": [],
            "writing_focus": "看好论文怎样压缩贡献、组织文献综述、写discussion",
            "why": "你不仅在研究内容上广，也在持续学习更好的论文写法",
            "keywords": ["academic writing", "feedback", "revision", "second language writing"],
        },
        {
            "name": "Broad scan: teacher identity, institutional discourse, and emotion",
            "query": "teacher identity institutional discourse emotional labor language education",
            "fallback_queries": [
                "teacher emotional labor bilingual education",
                "teacher identity language policy education",
                "teacher vulnerability education discourse",
            ],
            "anchors": [],
            "writing_focus": "看叙事如何被升格成结构分析，而不是只停在经验感受",
            "why": "你不排斥教育心理或教师情感，但它们更适合作为边线而不是主航道",
            "keywords": ["teacher identity", "institutional discourse", "emotional labor", "teacher vulnerability"],
        },
    ]


def _default_research_profile() -> dict:
    return {
        "summary": "用户关注应用语言学中的语言权力、课堂互动、教师制度处境与学术写作。",
        "writing_goals": [
            "学会把研究问题、方法和贡献写得更清楚",
            "学会从摘要里拆解作者如何搭建论证",
        ],
        "active_drafts": [],
        "strands": [
            {
                "name": "Applied linguistics fallback topic",
                "query": query,
                "fallback_queries": [query],
                "anchors": [],
                "writing_focus": "研究问题、方法与贡献表达",
                "why": "未读取到个性化研究画像时的通用后备主题",
            }
            for query in GENERIC_RESEARCH_QUERIES
        ],
    }


def _load_research_profile() -> dict:
    profile = _default_research_profile()
    if not RESEARCH_PROFILE_FILE.exists():
        return profile
    try:
        with open(RESEARCH_PROFILE_FILE, encoding="utf-8") as f:
            raw = json.load(f)
    except Exception as ex:
        log.warning("   无法读取 research_profile.json: %s", ex)
        return profile

    if isinstance(raw, dict):
        summary = raw.get("summary")
        if isinstance(summary, str) and summary.strip():
            profile["summary"] = summary.strip()
        writing_goals = raw.get("writing_goals")
        if isinstance(writing_goals, list) and writing_goals:
            profile["writing_goals"] = [str(item).strip() for item in writing_goals if str(item).strip()]
        active_drafts = raw.get("active_drafts")
        if isinstance(active_drafts, list):
            profile["active_drafts"] = [item for item in active_drafts if isinstance(item, dict)]
        strands = raw.get("strands")
        valid_strands = []
        if isinstance(strands, list):
            for item in strands:
                if not isinstance(item, dict):
                    continue
                query = str(item.get("query") or "").strip()
                name = str(item.get("name") or "").strip()
                if not query:
                    continue
                valid_strands.append({
                    "name": name or query,
                    "query": query,
                    "fallback_queries": item.get("fallback_queries") if isinstance(item.get("fallback_queries"), list) else [],
                    "anchors": item.get("anchors") if isinstance(item.get("anchors"), list) else [],
                    "writing_focus": str(item.get("writing_focus") or "研究问题、方法与贡献表达").strip(),
                    "why": str(item.get("why") or "").strip(),
                    "keywords": item.get("keywords") if isinstance(item.get("keywords"), list) else [],
                })
        if valid_strands:
            profile["strands"] = valid_strands
    return profile


def _draft_titles(profile: dict, limit: int = 5) -> list[str]:
    titles = []
    for draft in profile.get("active_drafts", []):
        if not isinstance(draft, dict):
            continue
        title = str(draft.get("short_name") or draft.get("title") or "").strip()
        if title:
            titles.append(title)
        if len(titles) >= limit:
            break
    return titles


def _topic_anchor_text(topic: Optional[dict], limit: int = 4) -> str:
    if not isinstance(topic, dict):
        return "当前研究线索"
    anchors = [str(item).strip() for item in topic.get("anchors", []) if str(item).strip()]
    return " / ".join(anchors[:limit]) if anchors else "当前研究线索"


def _profile_prompt_context(profile: dict, topic: Optional[dict] = None) -> str:
    lines = [f"研究画像：{profile.get('summary', '')}"]
    drafts = _draft_titles(profile)
    if drafts:
        lines.append(f"活跃稿件：{'；'.join(drafts)}")
    if isinstance(topic, dict):
        lines.append(f"今日主线：{topic.get('name', '')}")
        lines.append(f"对应草稿：{_topic_anchor_text(topic)}")
        if topic.get("writing_focus"):
            lines.append(f"今天最该强化的写作能力：{topic['writing_focus']}")
    writing_goals = [str(item).strip() for item in profile.get("writing_goals", []) if str(item).strip()]
    if writing_goals:
        lines.append(f"长期写作目标：{'；'.join(writing_goals[:4])}")
    return "\n".join(line for line in lines if line.strip())

def collect(system: str, user_prompt: str, max_tokens: int = 3500, **kwargs) -> str:
    """Call Claude API and return full streamed text."""
    for attempt in range(5):
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
            if e.status_code in (500, 529) and attempt < 4:
                wait = 30 * (attempt + 1)
                log.warning("Anthropic %d error, retrying in %ds (attempt %d/3)…", e.status_code, wait, attempt + 1)
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
    # 40个细化子主题，按 day_of_year 循环，约40天不重复
    subtopics = [
        # 底妆技巧 × 6
        "底妆技巧·散粉与定妆喷雾：如何让妆容持久不脱妆",
        "底妆技巧·粉底液选色与肤色匹配（橄榄皮避坑指南）",
        "底妆技巧·遮瑕全攻略（黑眼圈、色斑、毛孔、痘印）",
        "底妆技巧·隔离霜与妆前乳的选择与叠涂技巧",
        "底妆技巧·气垫 vs 粉底液 vs BB霜，适合橄榄皮的选择",
        "底妆技巧·持妆补妆：出油后如何快速救场",
        # 眼妆教程 × 6
        "眼妆教程·单眼皮与内双的放大眼法（不用双眼皮贴）",
        "眼妆教程·眼线与眼尾技巧（下垂眼、圆眼的不同画法）",
        "眼妆教程·大地色眼影配色与晕染手法",
        "眼妆教程·睫毛打造（睫毛膏卷翘持久 + 假睫毛选择）",
        "眼妆教程·眉毛修型与填色（圆脸适合的眉形）",
        "眼妆教程·卧蚕与下眼妆：提亮眼神的细节技巧",
        # 修容高光 × 5
        "修容高光·圆脸专属立体感打造（收窄颧骨+拉长脸型）",
        "修容高光·高光提亮打法（鼻梁、眉弓、颧骨）",
        "修容高光·修容粉 vs 修容膏：适合出油肌的选择",
        "修容高光·自然日常修容：通透感而非强阴影",
        "修容高光·小脸效果完整修容教程（圆脸适用）",
        # 唇妆色号 × 6
        "唇妆色号·橄榄皮显白砖红系口红推荐与搭配",
        "唇妆色号·橄榄皮必备棕调豆沙色：色号精选",
        "唇妆色号·口红质地深度对比（哑光/水光/丝绒/镜面）",
        "唇妆色号·唇线笔技巧：让嘴唇更立体饱满",
        "唇妆色号·唇部护理与打底：脱皮干纹急救方案",
        "唇妆色号·韩系渐变唇与日系咬唇妆实操教程",
        # 护肤成分解析 × 6
        "护肤成分解析·烟酰胺：橄榄皮美白提亮的核心成分",
        "护肤成分解析·水杨酸 BHA：控油收毛孔的正确用法",
        "护肤成分解析·视黄醇/A醇：抗老淡纹的使用攻略",
        "护肤成分解析·玻尿酸与保湿锁水成分全解析",
        "护肤成分解析·防晒成分（物理 vs 化学）及选购指南",
        "护肤成分解析·积雪草与神经酰胺：敏感肌屏障修护",
        # 完整妆容教程 × 5
        "完整妆容教程·清透日常通勤妆（15分钟快速上班妆）",
        "完整妆容教程·约会精致感小女人妆（橄榄皮适用）",
        "完整妆容教程·派对浓郁夜妆（高显白度色彩方案）",
        "完整妆容教程·韩系奶油肌妆容（橄榄皮如何打造）",
        "完整妆容教程·极简素颜感妆：三分钟高级感",
        # 护肤小贴士 × 6
        "护肤小贴士·早晚护肤步骤详解（橄榄皮专属顺序）",
        "护肤小贴士·卸妆与深层清洁：大毛孔的正确清洁法",
        "护肤小贴士·面膜使用指南（频次与类型搭配）",
        "护肤小贴士·换季期肌肤调整：油皮秋冬保湿策略",
        "护肤小贴士·眼霜与颈霜：什么时候开始用、怎么用",
        "护肤小贴士·生活习惯对肌肤的影响（睡眠、饮食、运动）",
    ]
    now = datetime.now()
    day_of_year = now.timetuple().tm_yday
    subtopic = subtopics[day_of_year % len(subtopics)]
    return collect(
        BEAUTY_SYSTEM,
        f"今天是{today}（{day_cn}）。请围绕今日细化主题「{subtopic}」，"
        "为我提供针对棱橄榄皮+圆脸的个性化美妆内容推送。"
        "记住：必须在【今日品牌与产品推荐】区块列出3-5款具体产品，包含品牌、产品名、色号和参考价位。",
        max_tokens=2200,
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


_TOP_RESEARCH_VENUE_KEYWORDS = [
    "applied linguistics",
    "applied linguistics review",
    "tesol quarterly",
    "modern language journal",
    "language learning",
    "language testing",
    "system",
    "journal of second language writing",
    "studies in second language acquisition",
    "international journal of bilingual education and bilingualism",
    "linguistics and education",
    "classroom discourse",
    "journal of sociolinguistics",
    "language in society",
    "language policy",
    "multilingua",
    "journal of language, identity & education",
    "journal of multilingual and multicultural development",
    "international journal of the sociology of language",
    "discourse & society",
    "journal of pragmatics",
    "teaching and teacher education",
    "learning and instruction",
    "english for specific purposes",
]

_LOW_PRIORITY_VENUE_KEYWORDS = [
    "educational psychology review",
    "journal of educational psychology",
    "british journal of educational psychology",
    "educational technology research and development",
    "computers & education",
    "internet and higher education",
    "learning environments research",
]


def _paper_venue_name(paper: dict) -> str:
    return ((paper.get("primary_location") or {}).get("source") or {}).get("display_name", "—")


def _is_top_research_venue(venue: str) -> bool:
    venue_lower = venue.lower()
    return any(keyword in venue_lower for keyword in _TOP_RESEARCH_VENUE_KEYWORDS)


def _paper_quality_score(paper: dict) -> float:
    cites = int(paper.get("cited_by_count", 0) or 0)
    year = int(paper.get("publication_year") or datetime.now().year)
    venue = _paper_venue_name(paper)
    age = max(1, datetime.now().year - year + 1)
    cite_density = cites / age

    score = cites * 1.2 + cite_density * 6
    if _is_top_research_venue(venue):
        score += 80
    if cites >= 200:
        score += 40
    elif cites >= 80:
        score += 20
    elif cites >= 30:
        score += 10
    if year >= datetime.now().year - 1 and cites < 5 and not _is_top_research_venue(venue):
        score -= 12
    return score


def _paper_selection_reason(paper: dict) -> str:
    cites = int(paper.get("cited_by_count", 0) or 0)
    year = int(paper.get("publication_year") or datetime.now().year)
    venue = _paper_venue_name(paper)
    age = max(1, datetime.now().year - year + 1)
    cite_density = cites / age

    reasons = []
    if cites >= 100:
        reasons.append(f"高被引（{cites} 次）")
    elif cites >= 30:
        reasons.append(f"被引较高（{cites} 次）")
    elif cite_density >= 8:
        reasons.append(f"年均引用高（约 {cite_density:.1f} 次/年）")
    if _is_top_research_venue(venue):
        reasons.append(f"期刊较强（{venue}）")
    if not reasons:
        if cites >= 10:
            reasons.append(f"有一定引用基础（{cites} 次）")
        else:
            reasons.append("相关性强，但学术影响力仍在观察")
    return " + ".join(reasons)


def _paper_domain_penalty(paper: dict, topic: Optional[dict]) -> float:
    venue = _paper_venue_name(paper).lower()
    if any(keyword in venue for keyword in _LOW_PRIORITY_VENUE_KEYWORDS):
        topic_score = _paper_topic_relevance_score(paper, topic)
        if topic_score < 28:
            return 28.0
    return 0.0


def _paper_topic_relevance_score(paper: dict, topic: Optional[dict]) -> float:
    if not isinstance(topic, dict):
        return 0.0
    keywords = [str(item).strip().lower() for item in topic.get("keywords", []) if str(item).strip()]
    if not keywords:
        return 0.0
    text = " ".join([
        str(paper.get("title") or ""),
        _paper_venue_name(paper),
        _reconstruct_abstract(paper.get("abstract_inverted_index") or {}),
    ]).lower()
    score = 0.0
    for keyword in keywords:
        if keyword and keyword in text:
            score += 18 if " " in keyword else 8
    return score


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
    venue    = _paper_venue_name(paper)
    doi      = paper.get("doi", "")
    abstract = _reconstruct_abstract(paper.get("abstract_inverted_index") or {})
    abstract_short = (abstract[:400] + "…") if len(abstract) > 400 else abstract or "摘要不可用"
    selection_reason = _paper_selection_reason(paper)

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
        f"⭐ 入选理由：{selection_reason}\n"
        f"📝 摘要：{abstract_short}\n"
        f"🔗 与本研究的关联性：{relevance}\n"
        f"🆔 DOI：{link_text}|{link_url}\n"
    )


def _select_research_topic(today: str, profile: Optional[dict] = None) -> tuple[dict, int]:
    profile = profile or _load_research_profile()
    target_dt = _parse_target_date(today)
    day_of_year = target_dt.timetuple().tm_yday
    core_topics = [item for item in profile.get("strands", []) if isinstance(item, dict) and item.get("query")]
    broad_topics = _exploration_research_topics()

    if not core_topics:
        topics = _default_research_profile()["strands"]
        topic_idx = day_of_year % len(topics)
        topic = topics[topic_idx]
        page = (day_of_year // len(topics)) + 1
        return topic, page

    if day_of_year % 4 == 0:
        topics = broad_topics
        topic_idx = (day_of_year // 4) % len(topics)
        topic = topics[topic_idx]
        page = (day_of_year // max(1, len(topics) * 4)) + 1
    else:
        topics = core_topics
        topic_idx = day_of_year % len(topics)
        topic = topics[topic_idx]
        page = (day_of_year // len(topics)) + 1
    return topic, page


def _topic_query_candidates(topic: Optional[dict], page: int) -> list[tuple[str, int]]:
    if not isinstance(topic, dict):
        return []
    raw_queries = []
    primary = str(topic.get("query") or "").strip()
    if primary:
        raw_queries.append(primary)
    for fallback in topic.get("fallback_queries", []):
        fallback_text = str(fallback).strip()
        if fallback_text:
            raw_queries.append(fallback_text)
    keywords = [str(item).strip() for item in topic.get("keywords", []) if str(item).strip()]
    if len(keywords) >= 4:
        raw_queries.append(" ".join(keywords[:4]))
    if len(keywords) >= 3:
        raw_queries.append(" ".join(keywords[:3]))

    candidates = []
    seen = set()
    for idx, query in enumerate(raw_queries):
        page_options = [page] if idx == 0 else [1]
        if idx == 0 and page != 1:
            page_options.append(1)
        for q_page in page_options:
            key = (query.lower(), q_page)
            if key in seen:
                continue
            seen.add(key)
            candidates.append((query, q_page))
    return candidates


def fetch_research_papers(today: str, limit: int = 3, profile: Optional[dict] = None) -> tuple[dict, list]:
    topic, page = _select_research_topic(today, profile=profile)
    query = topic.get("query", "")
    log.info("   OpenAlex 搜索: %s | %s (第 %s 页)", topic.get("name", "研究主线"), query, page)

    candidates = []
    seen_candidates = set()
    for query_variant, query_page in _topic_query_candidates(topic, page):
        try:
            batch = _openalex_search(query_variant, limit=max(limit * 4, 12), page=query_page)
        except Exception as ex:
            log.warning("   OpenAlex 请求失败: %s | %s", query_variant, ex)
            continue
        if batch:
            log.info("   OpenAlex 备选检索命中: %s (第 %s 页) -> %s 条", query_variant, query_page, len(batch))
        for paper in batch:
            key = (str(paper.get("doi") or paper.get("title") or "")).strip().lower()
            if not key or key in seen_candidates:
                continue
            seen_candidates.add(key)
            candidates.append(paper)
        if len(candidates) >= max(limit * 4, 12):
            break

    ranked = sorted(
        candidates,
        key=lambda paper: _paper_quality_score(paper) + _paper_topic_relevance_score(paper, topic) - _paper_domain_penalty(paper, topic),
        reverse=True,
    )
    preferred = []
    fallback = []
    for paper in ranked:
        cites = int(paper.get("cited_by_count", 0) or 0)
        venue = _paper_venue_name(paper)
        year = int(paper.get("publication_year") or datetime.now().year)
        age = max(1, datetime.now().year - year + 1)
        cite_density = cites / age
        topic_relevance = _paper_topic_relevance_score(paper, topic)
        if topic_relevance >= 18 and (cites >= 10 or cite_density >= 4 or _is_top_research_venue(venue)):
            preferred.append(paper)
        elif topic_relevance >= 30:
            preferred.append(paper)
        else:
            fallback.append(paper)

    papers = (preferred if len(preferred) >= limit else ranked)[:limit]
    if papers:
        log.info(
            "   选文优先级: %s",
            " | ".join(
                f"{_paper_venue_name(p)} / {int(p.get('cited_by_count', 0) or 0)} cites"
                for p in papers
            ),
        )
    return topic, papers


def _research_intro_lines(topic: Optional[dict]) -> list[str]:
    if not isinstance(topic, dict):
        return []
    lines = [
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 今日研究主线",
        "━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🧭 选题方向：{topic.get('name', '应用语言学')}",
        f"🧷 对应草稿：{_topic_anchor_text(topic)}",
        f"🔎 检索主题：{topic.get('query', '')}",
    ]
    why = str(topic.get("why") or "").strip()
    if why:
        lines.append(f"🪄 为什么是它：{why}")
    writing_focus = str(topic.get("writing_focus") or "").strip()
    if writing_focus:
        lines.append(f"✍️ 今天重点：{writing_focus}")
    return lines


def gen_research(
    today: str,
    papers: Optional[list] = None,
    topic: Optional[dict] = None,
    profile: Optional[dict] = None,
) -> str:
    profile = profile or _load_research_profile()
    if papers is None:
        topic, papers = fetch_research_papers(today, limit=3, profile=profile)

    parts = _research_intro_lines(topic)

    if not papers:
        parts.append("（今日无法获取论文数据，请稍后查看）")
        return "\n".join(parts)

    for i, paper in enumerate(papers, 1):
        title    = paper.get("title", "")
        abstract = _reconstruct_abstract(paper.get("abstract_inverted_index") or {})
        try:
            relevance = collect(
                RESEARCH_RELEVANCE_SYSTEM,
                (
                    f"{_profile_prompt_context(profile, topic)}\n\n"
                    f"标题：{title}\n"
                    f"摘要：{abstract[:600]}"
                ),
                max_tokens=200,
            ).strip()
        except Exception:
            relevance = "（关联性分析暂不可用）"
        parts.append(_paper_to_text(paper, i, relevance))

    return "\n".join(parts)


def _paper_authors_short(paper: dict) -> str:
    authors = [
        a["author"]["display_name"]
        for a in paper.get("authorships", [])[:3]
        if a.get("author")
    ]
    if not authors:
        return "作者未知"
    if len(paper.get("authorships", [])) > 3:
        authors.append("et al.")
    return ", ".join(authors)


def _paper_link_parts(paper: dict) -> tuple[str, str]:
    doi = paper.get("doi", "")
    title = paper.get("title", "") or "Google Scholar"
    if doi:
        link_url = doi if doi.startswith("http") else f"https://doi.org/{doi}"
        link_text = doi.replace("https://doi.org/", "")
        return link_text, link_url
    q = urllib.parse.quote(title)
    return "Google Scholar 搜索", f"https://scholar.google.com/scholar?q={q}"


def _mentor_focus_header_lines(
    authors: str,
    year: str,
    title: str,
    venue: str,
    link_text: str,
    link_url: str,
    paper_type: str,
) -> list[str]:
    return [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎓 导师带读",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"📄 焦点论文：{authors}（{year}）. {title}",
        f"📰 发表信息：{venue}",
        f"🔗 论文入口：{link_text}|{link_url}",
        f"📚 论文类型：{paper_type}",
    ]


def _inject_mentor_focus_metadata(
    text: str,
    *,
    authors: str,
    year: str,
    title: str,
    venue: str,
    link_text: str,
    link_url: str,
    paper_type: str,
) -> str:
    """Force the mentor section to display the exact selected focus paper metadata."""
    header_lines = _mentor_focus_header_lines(authors, year, title, venue, link_text, link_url, paper_type)
    if not text.strip():
        return "\n".join(header_lines)

    skip_prefixes = (
        "📄 焦点论文：",
        "📰 发表信息：",
        "🔗 论文入口：",
        "📚 论文类型：",
    )
    body_lines = []
    for raw in text.splitlines():
        s = raw.strip()
        if s == "🎓 导师带读":
            continue
        if s.startswith(skip_prefixes):
            continue
        body_lines.append(raw)

    while body_lines and (
        not body_lines[0].strip()
        or all(ch in "━─═-" for ch in body_lines[0].strip())
    ):
        body_lines.pop(0)

    return "\n".join(header_lines + body_lines)


def _infer_paper_type(title: str, abstract: str) -> tuple[str, list[str], str]:
    text = f"{title} {abstract}".lower()

    empirical_hits = 0
    theoretical_hits = 0

    empirical_markers = [
        "data", "dataset", "participants", "sample", "interview", "survey", "questionnaire",
        "corpus", "recording", "recordings", "classroom", "students", "teachers",
        "case study", "action research", "ethnograph", "autoethnograph", "experiment",
        "results", "findings", "analysis", "analyze", "examines", "reports", "episodes",
        "chi-square", "anova", "regression", "coding", "coded", "observed",
    ]
    theoretical_markers = [
        "conceptual", "theoretical", "framework", "reconceptualizing", "reconceptualises",
        "reconceptualizing", "argues", "argue", "proposes", "proposal", "revisits",
        "rethinking", "toward", "towards", "ontology", "epistemic", "politics",
        "review", "literature review", "synthesis", "critique", "commentary",
        "analytic lens", "concept", "model", "theory",
    ]

    for marker in empirical_markers:
        if marker in text:
            empirical_hits += 1
    for marker in theoretical_markers:
        if marker in text:
            theoretical_hits += 1

    has_sample_signal = bool(re.search(r"\b\d+\b", text)) and any(
        marker in text for marker in ["participants", "posts", "comments", "episodes", "students", "teachers"]
    )
    if has_sample_signal:
        empirical_hits += 2

    if empirical_hits >= theoretical_hits + 2:
        return (
            "实证文（基于摘要推断）",
            ["方法设计", "研究实操"],
            "摘要里有明显的数据、样本、课堂/语料或分析过程信号，适合优先学习研究设计与执行。",
        )
    if theoretical_hits >= empirical_hits + 2:
        return (
            "理论文（基于摘要推断）",
            ["idea", "文献综述"],
            "摘要更强调概念重构、理论主张或文献位置，适合优先学习问题意识与综述搭建。",
        )
    return (
        "混合型（基于摘要推断）",
        ["idea", "方法设计"],
        "摘要同时有理论推进和经验材料，适合先看作者如何把概念主张与证据链扣在一起。",
    )


def gen_paper_mentor(
    today: str,
    focus_paper: Optional[dict] = None,
    topic: Optional[dict] = None,
    profile: Optional[dict] = None,
) -> str:
    profile = profile or _load_research_profile()
    if focus_paper is None:
        topic, papers = fetch_research_papers(today, limit=1, profile=profile)
        focus_paper = papers[0] if papers else None

    if not focus_paper:
        return "（今日暂无可精读的论文，请稍后查看）"

    title = focus_paper.get("title", "")
    authors = _paper_authors_short(focus_paper)
    year = focus_paper.get("publication_year", "")
    venue = ((focus_paper.get("primary_location") or {}).get("source") or {}).get("display_name", "—")
    abstract = _reconstruct_abstract(focus_paper.get("abstract_inverted_index") or {})
    link_text, link_url = _paper_link_parts(focus_paper)
    paper_type, suggested_axes, paper_type_note = _infer_paper_type(title, abstract)

    prompt = (
        f"今天是 {today}。\n"
        f"{_profile_prompt_context(profile, topic)}\n"
        f"今天的检索主题：{(topic or {}).get('query', '应用语言学相关主题')}\n"
        f"作者：{authors}\n"
        f"年份：{year}\n"
        f"标题：{title}\n"
        f"期刊/来源：{venue}\n"
        f"论文入口：{link_text}|{link_url}\n\n"
        f"基于标题与摘要预判论文类型：{paper_type}\n"
        f"建议优先学习维度：{' / '.join(suggested_axes)}\n"
        f"判断说明：{paper_type_note}\n\n"
        "焦点论文必须就是我上面给你的这一篇，不允许换成别的论文，不允许改写成你更熟悉的文章。\n"
        "请把这篇论文当成与用户当前稿件对话的一篇样本来带读，优先讲清它对用户现有写作最有帮助的地方。"
        "请优先用第一年博士生能听懂的白话表达，再补学术判断。"
        "如果用了术语，第一次出现时要立刻解释。\n"
        "如果某处只能根据摘要合理推断，必须明确写“基于摘要推断”。\n\n"
        f"摘要：\n{abstract[:1800] or '摘要不可用'}"
    )

    try:
        mentor_text = collect(MENTOR_SYSTEM, prompt, max_tokens=1800).strip()
        return _inject_mentor_focus_metadata(
            mentor_text,
            authors=authors,
            year=str(year),
            title=title,
            venue=venue,
            link_text=link_text,
            link_url=link_url,
            paper_type=paper_type,
        )
    except Exception as ex:
        log.warning(f"   导师带读生成失败: {ex}")
        fallback_text = (
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎓 导师带读\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📄 焦点论文：{authors}（{year}）. {title}\n"
            f"📰 发表信息：{venue}\n"
            f"🔗 论文入口：{link_text}|{link_url}\n"
            f"📚 论文类型：{paper_type}\n"
            "🗣 用人话说：这篇文章主要是在告诉读者，这个研究主题为什么值得研究，以及作者准备从哪个重点切进去。\n"
            f"🏅 这篇最值得学的是：{' + '.join(suggested_axes)}\n"
            f"👓 今天主评维度：{suggested_axes[0]}\n"
            "👀 先品一品：\n"
            f"1. 类型判断：{paper_type_note}\n"
            f"2. 学习重点：今天不要平均用力，先盯住 {suggested_axes[0]}，再用 {suggested_axes[-1]} 辅助判断这篇文章的精华在哪里。\n"
            "🧩 拆解它是怎么写的：\n"
            f"1. 作者先围绕 {suggested_axes[0]} 做核心推进，而不是同时想把所有东西都讲满。\n"
            f"2. 这样写有效，是因为读者会更快抓住这篇文章真正的长板，而不是被背景信息冲散注意力。\n"
            f"3. 你自己写时，也要先决定这篇稿子最该靠 {suggested_axes[0]} 站住，还是靠 {suggested_axes[-1]} 站住，再安排段落顺序。\n"
            "🎯 今日训练重点：先学会如何从标题与摘要看出作者真正的研究贡献\n"
            "🧭 导师开场：今天先别急着做大而空的评论。先问自己三件事：作者在解决什么问题？凭什么这个问题值得研究？摘要里哪一句最像“贡献句”？\n"
            "🦴 文章骨架：\n"
            "1. 先界定研究对象与问题。\n"
            "2. 再说明理论/方法如何介入。\n"
            "3. 最后看作者如何压缩贡献与意义。\n"
            "❓ 导师追问你：\n"
            "❓ 问题 1：这篇不是“讲了什么”，而是“解决了什么”？\n"
            f"🧑‍🏫 导师回答：从摘要看，它真正要解决的是：在“{(topic or {}).get('query', '当前研究主题')}”这个方向里，研究者究竟该怎样更清楚地界定问题与贡献，而不只是把相关概念摆在一起。\n"
            "❓ 问题 2：如果没有这篇，领域里缺的到底是什么？\n"
            "🧑‍🏫 导师回答：如果没有这篇，读者会继续缺少一个更清楚的抓手，不知道这个主题到底该从什么角度切入、用什么证据或论证来推进。\n"
            "❓ 问题 3：作者最聪明的一步是什么？\n"
            f"🧑‍🏫 导师回答：作者最聪明的一步，是把注意力集中在 {suggested_axes[0]} 上，而不是平均用力地把每个方面都讲一遍；这会让整篇文章的长板更清楚。\n"
            "❓ 问题 4：这篇最可能被批评的地方是什么？\n"
            "🧑‍🏫 导师回答：最可能的批评通常是边界不够清、概念铺得太大，或者摘要里的证据还不足以完全支撑结论；读的时候要特别盯住作者有没有把范围收住。\n"
            "❓ 问题 5：你最想偷哪一句、哪一段、哪种推进方式？\n"
            f"🧑‍🏫 导师回答：最值得偷学的，是作者把问题意识压缩成几句核心判断的方式，尤其是从背景过渡到 {suggested_axes[0]} 的那种推进顺序。\n"
            "❓ 问题 6：这篇对你的论文，不是“启发了我”，而是“我能立刻拿来怎么写”？\n"
            f"🧑‍🏫 导师回答：你明天写自己的论文时，可以直接学它先界定问题、再压缩贡献、最后收束边界的顺序，而不是只写一大段背景再说“more research is needed”。\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "✍️ 今日练习\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1. 用 3 句英文写出这篇论文的“问题—方法—贡献”摘要。\n"
            "2. 检查每句是否都在推进论点，而不是重复背景信息。\n"
            "3. 今天先写短句、写清楚，比写得华丽更重要。\n"
        )
        return _inject_mentor_focus_metadata(
            fallback_text,
            authors=authors,
            year=str(year),
            title=title,
            venue=venue,
            link_text=link_text,
            link_url=link_url,
            paper_type=paper_type,
        )


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
        ("美联社亚洲",         "https://rsshub.app/apnews/topics/apf-asiapacific"),
        ("经济学人",           "https://www.economist.com/china/rss.xml"),
    ],
    # 北美：左中右立场兼顾，加入外交政策专业媒体
    "🇺🇸 北美视角": [
        ("NPR(公共广播,中偏左)",    "https://feeds.npr.org/1001/rss.xml"),
        ("AP通讯社(中立)",          "https://rsshub.app/apnews/topics/apf-topnews"),
        ("华尔街日报(中右)",        "https://feeds.a.dj.com/rss/RSSWorldNews.xml"),
        ("The Atlantic(中偏左)",    "https://feeds.feedburner.com/TheAtlantic"),
        ("外交政策(外交专业)",      "https://foreignpolicy.com/feed/"),
        ("Axios(简报风)",           "https://api.axios.com/feed/"),
        ("Politico",               "https://www.politico.com/rss/politics08.xml"),
    ],
    # 欧洲：英/德/法/泛欧，立场各异
    "🌍 欧洲视角": [
        ("卫报(英国,中左)",   "https://www.theguardian.com/world/rss"),
        ("DW(德国,中立)",     "https://rss.dw.com/rdf/rss-en-world"),
        ("法国24(法国)",      "https://www.france24.com/en/rss"),
        ("欧洲新闻台(泛欧)",  "https://www.euronews.com/rss"),
        ("BBC世界",           "http://feeds.bbci.co.uk/news/world/rss.xml"),
        ("爱尔兰时报",        "https://www.irishtimes.com/cmlink/the-irish-times-world-news-1.1319192"),
        ("西班牙El País",     "https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada"),
    ],
    # 亚太：新加坡/日/澳/印度，地区多元
    "🌏 亚太视角": [
        ("海峡时报(新加坡)",  "https://www.straitstimes.com/news/asia/rss.xml"),
        ("日本时报",          "https://www.japantimes.co.jp/news/feed/"),
        ("澳洲ABC新闻",       "https://www.abc.net.au/news/feed/51120/rss.xml"),
        ("印度教徒报",        "https://www.thehindu.com/news/international/?service=rss"),
        ("菲律宾每日问询者",  "https://newsinfo.inquirer.net/feed"),
        ("韩国中央日报",      "https://koreajoongangdaily.joins.com/rss/feeds"),
        ("澳洲卫报",          "https://www.theguardian.com/australia-news/rss"),
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
        ("以色列国土报",       "https://www.haaretz.com/cmlink/1.4564"),
        ("土耳其每日新闻",     "https://www.hurriyetdailynews.com/rss"),
    ],
}

# ══════════════════════════════════════════════════════════════════
#  NEWS CROSS-DAY DEDUPLICATION
# ══════════════════════════════════════════════════════════════════

_NEWS_SEEN_FILE = Path(__file__).parent / "seen_news.json"
_NEWS_DEDUP_DAYS = 7  # 跳过最近7天出现过的文章
_NEWS_SOURCE_COOLDOWN_DAYS = 2  # 同一来源连续几天内尽量不重复上榜
_NEWS_MAX_ARTICLE_AGE_DAYS = 3  # 优先显示最近3天内的新文章
_NEWS_HISTORY_RETENTION_DAYS = 21  # 状态文件最多保留近3周，避免无限增长


def _parse_target_date(value: str) -> datetime:
    """Accept either 2026-04-13 or 2026年04月13日; fall back to now."""
    for fmt in ("%Y-%m-%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(value, fmt)
        except Exception:
            pass
    return datetime.now()


def _cutoff_str(days: int, today_dt: datetime) -> str:
    return (today_dt - timedelta(days=days)).strftime("%Y-%m-%d")


def _prune_recent_map(records: dict, days: int, today_dt: datetime) -> dict:
    cutoff = _cutoff_str(days, today_dt)
    return {k: v for k, v in records.items() if isinstance(v, str) and v >= cutoff}


def _load_seen_news() -> dict:
    """Load persisted news state; support the legacy {url: date} format."""
    empty = {"urls": {}, "titles": {}, "sources": {}}
    if _NEWS_SEEN_FILE.exists():
        try:
            with open(_NEWS_SEEN_FILE, encoding="utf-8") as f:
                raw = json.load(f)
            if not isinstance(raw, dict):
                return empty
            # Legacy format: {url_key: "YYYY-MM-DD"}
            if raw and all(isinstance(v, str) for v in raw.values()) and not any(
                key in raw for key in ("urls", "titles", "sources")
            ):
                return {"urls": raw, "titles": {}, "sources": {}}
            return {
                "urls": raw.get("urls", {}) if isinstance(raw.get("urls", {}), dict) else {},
                "titles": raw.get("titles", {}) if isinstance(raw.get("titles", {}), dict) else {},
                "sources": raw.get("sources", {}) if isinstance(raw.get("sources", {}), dict) else {},
            }
        except Exception:
            return empty
    return empty


def _save_seen_news(seen: dict, today_dt: datetime) -> None:
    """Persist seen news state, pruning stale URL/title/source history."""
    pruned = {
        "urls": _prune_recent_map(seen.get("urls", {}), _NEWS_HISTORY_RETENTION_DAYS, today_dt),
        "titles": _prune_recent_map(seen.get("titles", {}), _NEWS_HISTORY_RETENTION_DAYS, today_dt),
        "sources": _prune_recent_map(seen.get("sources", {}), _NEWS_HISTORY_RETENTION_DAYS, today_dt),
    }
    try:
        with open(_NEWS_SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(pruned, f, ensure_ascii=False, indent=2)
    except Exception as ex:
        log.warning(f"   无法保存 seen_news.json: {ex}")


def _is_recent(key: str, records: dict, days: int, today_dt: datetime) -> bool:
    """Return True if key was seen within the requested time window."""
    if not key:
        return False
    return records.get(key, "0000-00-00") >= _cutoff_str(days, today_dt)


def _normalize_news_url(link: str) -> str:
    if not link:
        return ""
    try:
        parsed = urllib.parse.urlsplit(link.strip())
        return urllib.parse.urlunsplit(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",
                "",
            )
        )
    except Exception:
        return link.split("?")[0].rstrip("/")


def _normalize_news_title(title: str) -> str:
    text = html.unescape(title or "")
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[\u2018\u2019\u201c\u201d'\"`]", "", text)
    text = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Use a stable prefix so tiny suffix changes do not create a new “story”.
    return " ".join(text.split()[:14])


def _source_history_key(region: str, source: str) -> str:
    return f"{region}::{source}"


def _entry_is_fresh(entry: dict, today_dt: datetime) -> bool:
    published = entry.get("published_parsed")
    if not published:
        return True
    try:
        pub_dt = datetime(*published[:6])
    except Exception:
        return True
    return pub_dt >= (today_dt - timedelta(days=_NEWS_MAX_ARTICLE_AGE_DAYS))


def _ordered_feeds_for_day(region: str, feeds: list, seen_state: dict, today_dt: datetime) -> list:
    """Rotate source order daily, but deprioritize sources used very recently."""
    if not feeds:
        return []
    rotation = today_dt.toordinal() % len(feeds)
    rotated = feeds[rotation:] + feeds[:rotation]
    preferred = []
    cooldown = []
    source_history = seen_state.get("sources", {})
    for src_name, url in rotated:
        key = _source_history_key(region, src_name)
        if _is_recent(key, source_history, _NEWS_SOURCE_COOLDOWN_DAYS, today_dt):
            cooldown.append((src_name, url))
        else:
            preferred.append((src_name, url))
    return preferred + cooldown


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
                items.append({
                    "title": title,
                    "link": link,
                    "published_parsed": entry.get("published_parsed") or entry.get("updated_parsed"),
                })
        return items
    except Exception as ex:
        log.warning(f"   RSS 获取失败 ({url}): {ex}")
        return []


def gen_news(today: str) -> list:
    """
    Fetch top-5 news per region via RSS, translate titles to Chinese with Claude,
    and return a list of region dicts ready for news_to_html().
    Uses cross-day URL deduplication to avoid repeating articles across multiple days.
    """
    today_dt = _parse_target_date(today)
    today_str = today_dt.strftime("%Y-%m-%d")
    seen_state = _load_seen_news()
    newly_seen = {"urls": {}, "titles": {}, "sources": {}}
    seen_title_keys_global: set[str] = set()

    # Step 1: collect raw items per region.
    # Strategy:
    # - rotate source order by day so later feeds also get a turn
    # - avoid sources used very recently when alternatives exist
    # - dedup both by URL and normalized title fingerprint
    # - prefer newer stories first, then relax freshness/source cooldown only if needed
    region_raw: dict[str, list] = {}
    for region, feeds in NEWS_REGIONS.items():
        seen_titles_today: set[str] = set()
        items: list = []
        ordered_feeds = _ordered_feeds_for_day(region, feeds, seen_state, today_dt)

        def try_collect(allow_recent_source: bool, allow_stale_story: bool) -> None:
            for src_name, url in ordered_feeds:
                if len(items) >= 5:
                    break
                if any(existing.get("source") == src_name for existing in items):
                    continue
                source_key = _source_history_key(region, src_name)
                if (
                    not allow_recent_source
                    and _is_recent(source_key, seen_state.get("sources", {}), _NEWS_SOURCE_COOLDOWN_DAYS, today_dt)
                ):
                    continue
                for entry in _fetch_rss(url, limit=20):
                    url_key = _normalize_news_url(entry.get("link", ""))
                    title_key = _normalize_news_title(entry.get("title", ""))
                    if not url_key or not title_key:
                        continue
                    if _is_recent(url_key, seen_state.get("urls", {}), _NEWS_DEDUP_DAYS, today_dt):
                        continue
                    if _is_recent(title_key, seen_state.get("titles", {}), _NEWS_DEDUP_DAYS, today_dt):
                        continue
                    if title_key in seen_titles_today or title_key in seen_title_keys_global:
                        continue
                    if not allow_stale_story and not _entry_is_fresh(entry, today_dt):
                        continue
                    seen_titles_today.add(title_key)
                    seen_title_keys_global.add(title_key)
                    entry["source"] = src_name
                    items.append(entry)
                    newly_seen["urls"][url_key] = today_str
                    newly_seen["titles"][title_key] = today_str
                    newly_seen["sources"][source_key] = today_str
                    break

        try_collect(allow_recent_source=False, allow_stale_story=False)
        if len(items) < 3:
            try_collect(allow_recent_source=True, allow_stale_story=False)
        if len(items) < 3:
            try_collect(allow_recent_source=True, allow_stale_story=True)
        region_raw[region] = items[:5]

    # Persist newly seen state
    seen_state["urls"].update(newly_seen["urls"])
    seen_state["titles"].update(newly_seen["titles"])
    seen_state["sources"].update(newly_seen["sources"])
    _save_seen_news(seen_state, today_dt)
    log.info(
        "   新闻去重：新增 URL %s 条、标题指纹 %s 条、来源记录 %s 条",
        len(newly_seen["urls"]),
        len(newly_seen["titles"]),
        len(newly_seen["sources"]),
    )

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
        "🎯": ("#455a64", "研究主线"),
        "🧭": ("#546e7a", "选题方向"),
        "🧷": ("#6a1b9a", "对应草稿"),
        "🔎": ("#1565c0", "检索主题"),
        "🪄": ("#8e24aa", "为什么是它"),
        "✍️": ("#2e7d32", "今天重点"),
        "📌": ("#c62828", "作者"),
        "📖": ("#1565c0", "标题"),
        "📰": ("#00838f", "期刊"),
        "📅": ("#e65100", "年份"),
        "📊": ("#2e7d32", "引用量"),
        "⭐": ("#f9a825", "入选理由"),
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

        if s == "🎯 今日研究主线":
            if in_card:
                parts.append("</div>")
            parts.append(
                '<div style="background:#fff;border:1px solid #d9eef2;border-radius:10px;'
                'padding:20px 22px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,0.05)">'
                '<div style="background:linear-gradient(135deg,#00838f,#26c6da);'
                'color:#fff;padding:10px 16px;border-radius:6px;margin:-20px -22px 16px;'
                'font-weight:700;font-size:15px;letter-spacing:0.6px">🎯 今日研究主线</div>'
            )
            in_card = True
            current_title = ""
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


def mentor_to_html(text: str) -> str:
    """Render the daily PhD mentor-guided paper reading column."""
    import urllib.parse

    parts = []
    in_card = False

    CARD_STYLES = {
        "🎓 导师带读": ("linear-gradient(135deg,#455a64,#607d8b)", "#fff"),
        "✨ 好句": ("linear-gradient(135deg,#ffb300,#ef6c00)", "#fff"),
        "✍️ 今日练习": ("linear-gradient(135deg,#43a047,#2e7d32)", "#fff"),
    }
    FIELD_STYLES = {
        "📄": "#5d4037",
        "📰": "#00695c",
        "🔗": "#1565c0",
        "📚": "#3949ab",
        "🗣": "#2e7d32",
        "🏅": "#ad1457",
        "👓": "#283593",
        "👀": "#6d4c41",
        "🧩": "#00838f",
        "🎯": "#6a1b9a",
        "🧭": "#455a64",
        "🦴": "#8d6e63",
        "❓": "#ef6c00",
        "🧑‍🏫": "#1565c0",
        "🔤": "#c62828",
        "💬": "#2e7d32",
        "🔍": "#6d4c41",
        "🛠": "#00838f",
        "🧪": "#7b1fa2",
    }

    def start_card(title: str) -> None:
        nonlocal in_card
        if in_card:
            parts.append("</div>")
        bg, fg = CARD_STYLES["🎓 导师带读"]
        for prefix, style in CARD_STYLES.items():
            if title.startswith(prefix):
                bg, fg = style
                break
        parts.append(
            f'<div style="background:#fff;border:1px solid #e0e0e0;border-radius:12px;'
            f'padding:20px 22px;margin:16px 0;box-shadow:0 2px 8px rgba(0,0,0,.06)">'
            f'<div style="background:{bg};color:{fg};padding:11px 16px;border-radius:8px;'
            f'margin:-20px -22px 16px;font-weight:700;font-size:15px;letter-spacing:0.5px">'
            f'{e(title)}</div>'
        )
        in_card = True

    for raw in text.splitlines():
        s = raw.strip()

        if s and all(c in "━─═-" for c in s):
            continue

        if s in ("🎓 导师带读", "✍️ 今日练习") or s.startswith("✨ 好句"):
            start_card(s)
            continue

        matched_field = False
        for icon, color in FIELD_STYLES.items():
            if s.startswith(icon):
                key_end = s.find("：") + 1 if "：" in s else len(icon)
                key_part = s[:key_end]
                body_part = s[key_end:].strip()

                if icon == "🔗":
                    raw_link = body_part.strip()
                    if "|" in raw_link:
                        link_text, link_url = raw_link.split("|", 1)
                    else:
                        q = urllib.parse.quote(raw_link)
                        link_text = "Google Scholar 搜索"
                        link_url = f"https://scholar.google.com/scholar?q={q}"
                    body_html = (
                        f'<a href="{e(link_url)}" target="_blank" rel="noopener" '
                        f'style="color:#1a73e8;text-decoration:none">🔍 {e(link_text)}</a>'
                    )
                elif not body_part:
                    body_html = ""
                else:
                    body_html = md(body_part)

                if icon == "❓" and body_part:
                    parts.append(
                        f'<div style="margin:10px 0 6px;padding:10px 13px;background:#fff7ed;'
                        f'border:1px solid #fed7aa;border-radius:10px;color:#9a3412;'
                        f'font-size:14px;line-height:1.75;font-weight:600">{e(key_part)} '
                        f'<span style="font-weight:500;color:#7c2d12">{body_html}</span></div>'
                    )
                elif icon == "🧑‍🏫" and body_part:
                    parts.append(
                        f'<div style="margin:0 0 12px 16px;padding:12px 14px;background:#f4f8ff;'
                        f'border-left:4px solid #90caf9;border-radius:0 10px 10px 0;'
                        f'box-shadow:inset 0 0 0 1px #dbeafe">'
                        f'<div style="color:{color};font-weight:700;font-size:13px;margin-bottom:4px">{e(key_part)}</div>'
                        f'<div style="color:#234;font-size:14px;line-height:1.8">{body_html}</div>'
                        f'</div>'
                    )
                elif not body_part:
                    parts.append(
                        f'<div style="margin:16px 0 8px;color:{color};font-size:14px;'
                        f'font-weight:700;padding-bottom:5px;border-bottom:1px solid #eceff1">{e(key_part)}</div>'
                    )
                else:
                    parts.append(
                        f'<table width="100%" cellpadding="0" cellspacing="0" '
                        f'style="margin:8px 0;border-collapse:collapse"><tr>'
                        f'<td width="102" valign="top" style="color:{color};font-weight:700;'
                        f'font-size:13px;padding-right:8px;white-space:nowrap">{e(key_part)}</td>'
                        f'<td valign="top" style="color:#333;font-size:14px;line-height:1.8">{body_html}</td>'
                        f'</tr></table>'
                    )
                matched_field = True
                break
        if matched_field:
            continue

        m = re.match(r"^(\d{1,2})[.)、]\s+(.+)", s)
        if m:
            num, content = m.groups()
            parts.append(
                f'<div style="display:flex;align-items:flex-start;margin:8px 0;padding:10px 14px;'
                f'background:#f7fafc;border-radius:9px;border:1px solid #e6edf3">'
                f'<span style="color:#455a64;font-weight:700;min-width:28px;font-size:13px">{num}.</span>'
                f'<span style="color:#333;font-size:14px;line-height:1.75">{md(content)}</span>'
                f'</div>'
            )
            continue

        if s.startswith("⚠"):
            parts.append(
                f'<div style="background:#fff8e1;border-left:4px solid #fb8c00;'
                f'padding:9px 14px;margin:10px 0;border-radius:0 6px 6px 0;'
                f'color:#bf360c;font-size:13px;line-height:1.7">{md(s)}</div>'
            )
            continue

        if not s:
            parts.append('<div style="height:6px"></div>')
            continue

        parts.append(
            f'<p style="margin:6px 0;color:#555;font-size:14px;line-height:1.8">{md(s)}</p>'
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


def build_mentor_email_html(
    mentor_html: str,
    date_str: str,
    day_cn: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>导师带读 · {date_str}</title>
</head>
<body style="margin:0;padding:20px 0;background:#eef2f6;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif">

  <div style="max-width:760px;margin:0 auto">

    <div style="background:linear-gradient(135deg,#455a64 0%,#1f3b4d 100%);
      border-radius:16px 16px 0 0;padding:36px 38px 28px;text-align:center">
      <div style="font-size:34px;margin-bottom:8px">🎓</div>
      <h1 style="color:#fff;margin:0;font-size:28px;letter-spacing:2px;font-weight:700">
        导师带读
      </h1>
      <p style="color:rgba(255,255,255,0.78);margin:12px 0 0;font-size:14px;line-height:1.7">
        今天不求多，只陪你读透一篇值得学的论文。先听懂它在解决什么，再学它为什么写得站得住。
      </p>
      <div style="margin-top:16px;display:inline-block;background:rgba(255,255,255,0.14);
        border-radius:20px;padding:6px 20px">
        <span style="color:#fff;font-size:14px;font-weight:600">
          📅 &nbsp;{date_str} &nbsp;{day_cn}
        </span>
      </div>
    </div>

    <div style="background:#ffffff;padding:24px 28px;border-left:1px solid #dde5eb;border-right:1px solid #dde5eb">
      <div style="background:#f6f9fc;border:1px solid #dbe5ee;border-radius:12px;padding:14px 16px;
        color:#425466;font-size:13px;line-height:1.8;margin-bottom:18px">
        今日带读顺序：先用人话听懂论文在干嘛，再判断它最值得学的地方，接着逐题看导师怎么回答，最后把可偷学的写法拿回你自己的稿子里。
      </div>
      {mentor_html}
    </div>

    <div style="background:#22313a;border-radius:0 0 16px 16px;padding:20px 28px;text-align:center">
      <p style="color:#b9c4cc;margin:0 0 6px;font-size:12px">
        一封邮件只做一件事：帮你把一篇论文读懂、读透、读出写法。
      </p>
      <p style="color:#7f8f99;margin:0;font-size:11px">
        PhD Writing Mentor &nbsp;·&nbsp; 焦点论文 &nbsp;·&nbsp; 导师追问 &nbsp;·&nbsp; 句子仿写
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

    research_profile = _load_research_profile()
    log.info(
        "🧭 已载入研究画像：%s 条主线，活跃稿件 %s 个",
        len(research_profile.get("strands", [])),
        len(research_profile.get("active_drafts", [])),
    )

    log.info("🔬 生成科研文献推荐...")
    research_topic, research_papers = fetch_research_papers(date_str, limit=3, profile=research_profile)
    res_text = gen_research(date_str, papers=research_papers, topic=research_topic, profile=research_profile)
    log.info(f"   完成，{len(res_text)} 字符")

    log.info("🎓 生成导师带读栏目...")
    mentor_text = gen_paper_mentor(
        date_str,
        focus_paper=research_papers[0] if research_papers else None,
        topic=research_topic,
        profile=research_profile,
    )
    log.info(f"   完成，{len(mentor_text)} 字符")

    log.info("📰 抓取每日全球新闻...")
    news_groups = gen_news(date_str)
    log.info(f"   完成，{sum(len(g['items']) for g in news_groups)} 条新闻")

    log.info("🎨 转换为 HTML...")
    eng_html  = english_to_html(eng_text)
    bty_html  = beauty_to_html(bty_text)
    res_html  = research_to_html(res_text)
    mentor_html = mentor_to_html(mentor_text)
    news_html = news_to_html(news_groups)

    full_html = build_email_html(eng_html, bty_html, res_html, news_html, date_str, day_cn)
    mentor_email_html = build_mentor_email_html(mentor_html, date_str, day_cn)

    subject = f"✨ 每日学习推送 · {date_str} {day_cn}"
    mentor_subject = f"🎓 导师带读 · {date_str} {day_cn}"

    log.info(f"📨 发送邮件到 {os.environ.get('EMAIL_TO', '(未配置)')}...")
    send_email(subject, full_html)
    log.info("✅ 综合日报发送成功！")
    send_email(mentor_subject, mentor_email_html)
    log.info("✅ 导师带读专属邮件发送成功！")

    log.info("🏡 更新格雷西学习小屋网站...")
    date_key = now.strftime("%Y-%m-%d")
    save_entry(date_key, date_str, day_cn, eng_html, bty_html, res_html, mentor_html, news_html)
    site_path, count = rebuild_site()
    log.info(f"   网站已更新 ({count} 天记录) → {site_path}")


if __name__ == "__main__":
    main()
