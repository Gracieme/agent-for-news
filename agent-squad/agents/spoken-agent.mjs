/**
 * 每日生活口语 Agent 2.0
 * 主源：BBC Learning English (6 Minute English / The English We Speak)
 * 结构：expression, definition, nuance, cultural_note, audio_url, simulated_dialogue
 */
import { fetchBbcSpokenExpressions } from '../lib/bbc-rss.mjs';
import { generateWithGemini } from '../lib/gemini.mjs';

const EXPRESSION_COUNT = 6;

export async function runSpokenAgent() {
  const bbcItems = await fetchBbcSpokenExpressions(EXPRESSION_COUNT);
  const expressions = [];
  let practice = { sceneLabel: '', storyEn: '', storyZh: '' };
  let studyTip = '多听多练，把今日短语放进真实对话里用一次。';

  if (bbcItems.length === 0) {
    return fallbackSpoken();
  }

  for (let i = 0; i < bbcItems.length && expressions.length < EXPRESSION_COUNT; i++) {
    const item = bbcItems[i];
    const phrase = extractPhraseFromTitle(item.title);
    if (!phrase) continue;

    try {
      const prompt = `You are a daily spoken-English assistant for a C1 learner. Based on this BBC Learning English episode, generate content in 中文 + English.

Episode title: ${item.title}
Source: ${item.source}
Description (excerpt): ${(item.description || '').slice(0, 400)}

Output valid JSON only, no markdown fences, no extra text. Use this exact structure:
{
  "expression": "${phrase}",
  "definition": "一两句中文讲解：用法、语气、适用场景",
  "nuance": "Nuance Check：与近义表达的辨析，例如 I'm down vs I'm game，用中文说明区别",
  "cultural_note": "Cultural Note：文化背景或使用场合的补充说明",
  "simulated_dialogue": "2-4 句简短英文对话，自然使用该短语，A/B 轮换"
}

Requirements:
- definition, nuance, cultural_note: 中文
- simulated_dialogue: 纯英文，自然对话
- 若无法准确辨析，nuance 可简写`;

      const raw = await generateWithGemini(prompt);
      const cleaned = raw.replace(/^[\s\S]*?(\{[\s\S]*\})[\s\S]*$/m, '$1').trim();
      const data = JSON.parse(cleaned);

      expressions.push({
        expression: data.expression || phrase,
        definition: data.definition || '',
        nuance: data.nuance || '',
        cultural_note: data.cultural_note || '',
        audio_url: item.audioUrl || '',
        simulated_dialogue: data.simulated_dialogue || '',
        source: item.source,
        url: item.url || '',
      });
    } catch (e) {
      console.warn('[spoken-agent] 单条生成失败:', phrase, e.message);
      expressions.push({
        expression: phrase,
        definition: item.description ? item.description.slice(0, 150) + '...' : '（详见 BBC 原文）',
        nuance: '',
        cultural_note: '',
        audio_url: item.audioUrl || '',
        simulated_dialogue: '',
        source: item.source,
        url: item.url || '',
      });
    }
  }

  if (expressions.length === 0) return fallbackSpoken();

  try {
    const prompt = `Generate a combined practice dialogue and study tip. Output valid JSON only:
{
  "sceneLabel": "场景简述（例如：朋友聊 BBC 今日短语）",
  "storyEn": "4-6 句英文对话，每人使用 1-2 个今日短语。用 <mark class=\\"hl-spoken\\">phrase</mark> 标出短语",
  "storyZh": "同上对话的中文版，用 <mark class=\\"hl-spoken-zh\\">对应短语</mark> 标出",
  "studyTip": "一两句学习建议，鼓励开口练、跟读"
}

今日短语: ${expressions.map((e) => e.expression).join(', ')}`;
    const raw = await generateWithGemini(prompt);
    const cleaned = raw.replace(/^[\s\S]*?(\{[\s\S]*\})[\s\S]*$/m, '$1').trim();
    const data = JSON.parse(cleaned);
    practice = {
      sceneLabel: data.sceneLabel || '情景对话',
      storyEn: data.storyEn || '',
      storyZh: data.storyZh || '',
    };
    studyTip = data.studyTip || studyTip;
  } catch (_) {}

  return {
    summary: `今日 ${expressions.length} 条生活口语 · BBC Learning English · 情景对话 + 学习提示`,
    expressions,
    practice,
    studyTip,
    cards: expressions.map((e) => ({
      word: e.expression,
      source: e.source || 'BBC Learning English',
      region: 'UK',
      explanation_zh: e.definition,
      example_en: e.simulated_dialogue,
      translation_zh: '',
      nuance: e.nuance,
      cultural_note: e.cultural_note,
      audio_url: e.audio_url,
    })),
  };
}

function extractPhraseFromTitle(title) {
  if (!title || typeof title !== 'string') return '';
  const t = title.trim();
  const patterns = [
    /The English We Speak\s*\/\s*(.+)$/i,
    /^[^\/]+\/\s*(.+)$/,
    /^[^:]+:\s*(.+)$/,
    /^(.+?)\s*[-–—|]\s*6\s*Minute/i,
    /^(.+?)\s*[-–—]\s*BBC/i,
  ];
  for (const p of patterns) {
    const m = t.match(p);
    if (m && m[1]) return m[1].trim();
  }
  if (t.length > 4 && t.length < 80) return t;
  return '';
}

function fallbackSpoken() {
  return {
    summary: '每日生活口语生成失败：BBC RSS 无数据',
    expressions: [],
    practice: { sceneLabel: '', storyEn: '', storyZh: '' },
    studyTip: '多听多练，把今日短语放进真实对话里用一次。',
    cards: [],
  };
}
