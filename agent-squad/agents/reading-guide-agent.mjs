/**
 * 外刊精读 Agent 2.0
 * 主源：The Economist / The Conversation RSS
 * 结构：article_title, readability_level, core_argument, rhetorical_devices,
 *       vocabulary_tier_3, scaffolding_questions, sentence_logic_map, teaching_prompts
 * 视角：Mandarin Teacher 视角，生成 Scaffolding Questions 和 Sentence Logic Map
 */
import { fetchReadingArticles } from '../lib/reading-rss.mjs';
import { generateWithGemini } from '../lib/gemini.mjs';

const DEFAULT_ARTICLE = {
  source: 'The Economist',
  title: 'Spectacular images reveal unique sea creatures off Caribbean islands',
  url: 'https://www.economist.com',
  date: new Date().getFullYear().toString(),
};

export async function runReadingGuideAgent() {
  const articles = await fetchReadingArticles(1);
  const raw = articles[0] || null;
  const article = raw
    ? {
        source: raw.source || 'The Economist',
        title: raw.title || '',
        url: raw.url || '#',
        date: raw.pubDate ? new Date(raw.pubDate).toLocaleDateString('zh-CN') : '',
        description: raw.description || '',
      }
    : { ...DEFAULT_ARTICLE };

  let excerptHtml = '';
  let vocabCards = [];
  let grammarSpotlight = [];
  let apRows = [];
  let teacherNote = '';
  let readabilityLevel = '';
  let coreArgument = '';
  let rhetoricalDevices = '';
  let scaffoldingQuestions = [];
  let sentenceLogicMap = [];
  let teachingPrompts = '';

  const contentForPrompt = article.description || article.title;
  if (!contentForPrompt) {
    return fallbackReadingGuide(article);
  }

  try {
    const prompt = `You are an AP English Reading teacher (Mandarin Teacher 视角). **User lives in the US — use American English** (spelling: color, -ize, organize; vocabulary and usage reflect American conventions).

Article title: ${article.title}
Source: ${article.source}
Excerpt/description: ${contentForPrompt.slice(0, 1000)}

Output valid JSON only, no markdown fences, with this exact structure:
{
  "readability_level": "如 C1 / B2+ / 学术阅读",
  "core_argument": "2-4 句中文：文章核心论点",
  "rhetorical_devices": "2-4 句：修辞与手法（比喻、对比、数据论证等）",
  "vocabulary_tier_3": [
    { "word": "disparate", "pos": "adjective", "pos_zh": "迥异的", "sent": "文中例句", "zh": "释义与用法说明", "tip": "搭配提示" }
  ],
  "scaffolding_questions": ["支架式提问1：引导学生理解主旨", "支架式提问2：引导学生关注修辞", "支架式提问3：引导学生批判思考"],
  "sentence_logic_map": [
    { "sentence": "长难句原文", "logic_breakdown": "逻辑拆解：主句 + 从句/修饰成分，用中文说明结构", "key_point": "关键信息提取" }
  ],
  "teaching_prompts": "2-4 句中文：教师课堂引导语，用于搭建支架、引导学生进入文本",
  "excerptHtml": "2-3 段英文摘录，用 <p class=\\"ep\\">...</p>，4-6 个关键词用 <mark class=\\"vhl\\">word</mark>。若有英式拼写请改为美式（colour→color, centre→center）。",
  "grammarSpotlight": [
    { "label": "1 — 语法点名称", "quote": "原文引用", "zh": "中文讲解", "model": "句型模板" }
  ],
  "apRows": [
    { "label": "修辞 & 手法", "val": "2-4 句说明" },
    { "label": "受众 & 目的", "val": "2-4 句说明" }
  ],
  "teacherNote": "2-4 句教师笔记"
}

Requirements:
- vocabulary_tier_3: **仅选 C1/C2 级别词汇**。排除 B2 及以下（如 unprecedented, biodiversity, expedition 等常见词）。优先：学术/正式语体、多义短语动词、微妙用法的搭配、领域术语、抽象概念词。
- scaffolding_questions 至少 3 条；sentence_logic_map 至少 1 条长难句拆解；vocabulary_tier_3 4-6 个词；所有中文字段用中文。
- 词汇释义与例句优先用美式用法（e.g. gotten not got, sidewalk not pavement）。`;

    const rawOut = await generateWithGemini(prompt);
    const jsonStr = rawOut.replace(/^[\s\S]*?(\{[\s\S]*\})[\s\S]*$/, '$1').trim();
    const data = JSON.parse(jsonStr);

    excerptHtml = data.excerptHtml || '';
    vocabCards = Array.isArray(data.vocabulary_tier_3) ? data.vocabulary_tier_3 : (data.vocabCards || []);
    grammarSpotlight = Array.isArray(data.grammarSpotlight) ? data.grammarSpotlight : [];
    apRows = Array.isArray(data.apRows) ? data.apRows : [];
    teacherNote = data.teacherNote || '';
    readabilityLevel = data.readability_level || '';
    coreArgument = data.core_argument || '';
    rhetoricalDevices = data.rhetorical_devices || '';
    scaffoldingQuestions = Array.isArray(data.scaffolding_questions) ? data.scaffolding_questions : [];
    sentenceLogicMap = Array.isArray(data.sentence_logic_map) ? data.sentence_logic_map : [];
    teachingPrompts = data.teaching_prompts || '';
  } catch (e) {
    console.warn('[reading-guide-agent] 生成失败:', e.message);
    return fallbackReadingGuide(article);
  }

  return {
    source: article.source,
    date: article.date,
    title: article.title,
    url: article.url,
    excerptHtml: excerptHtml || '<p class="ep">（暂无摘录）</p>',
    vocabCards,
    grammarSpotlight,
    apRows,
    teacherNote,
    readability_level: readabilityLevel,
    core_argument: coreArgument,
    rhetorical_devices: rhetoricalDevices,
    scaffolding_questions: scaffoldingQuestions,
    sentence_logic_map: sentenceLogicMap,
    teaching_prompts: teachingPrompts,
    summary: `外刊精读 · ${article.source} · Scaffolding Questions & Sentence Logic Map`,
  };
}

function fallbackReadingGuide(article) {
  return {
    source: article?.source || 'The Economist',
    date: article?.date || '',
    title: article?.title || '（RSS 暂无文章）',
    url: article?.url || '#',
    excerptHtml: '<p class="ep">（今日 RSS 无内容，请稍后再试）</p>',
    vocabCards: [],
    grammarSpotlight: [],
    apRows: [],
    teacherNote: '外刊精读内容生成暂不可用。',
    readability_level: '',
    core_argument: '',
    rhetorical_devices: '',
    scaffolding_questions: [],
    sentence_logic_map: [],
    teaching_prompts: '',
    summary: '外刊精读 · 暂缺',
  };
}
