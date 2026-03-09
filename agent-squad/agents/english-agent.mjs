/**
 * 英语学习助手：每日 10 条 C1 水平 idiom/谚语，标注流行地区，写成一段话，中英对照
 */
import { generateWithGemini } from '../lib/gemini.mjs';
import { ENGLISH_LEVEL, IDIOMS_PER_DAY } from '../config.mjs';

export async function runEnglishAgent() {
  const prompt = `You are an English learning assistant for a C1-level learner. Generate exactly ${IDIOMS_PER_DAY} idioms or proverbs suitable for C1 level. For each item:
1. Give the idiom/proverb in English.
2. State which region or variety it is most common in (e.g. British, American, Australian, etc.).
3. Give a short natural-sounding sentence using it in context (English only for this sentence).
4. Give the Chinese translation of the idiom/proverb and the example sentence.

Output format: write ONE coherent paragraph in English that weaves all ${IDIOMS_PER_DAY} items into a flowing text (e.g. a short story or commentary). After that, output "---" on a new line, then the same paragraph in Chinese (translating the whole English paragraph). Then after another "---", list each idiom with its region in a simple list like:
- [idiom] (region)
- ...

Requirements:
- Idioms/proverbs must be C1-appropriate (not too basic, not overly rare).
- Mix regions (e.g. at least 2 British, 2 American, 1–2 others).
- Paragraph should sound natural, not a list.`;

  const text = await generateWithGemini(prompt);
  return {
    raw: text,
    summary: `今日 ${IDIOMS_PER_DAY} 条 ${ENGLISH_LEVEL} 习语/谚语，中英对照段落`,
  };
}
