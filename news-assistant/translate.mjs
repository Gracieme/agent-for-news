import { GoogleGenerativeAI } from '@google/generative-ai';

let model;

function getModel() {
  if (!process.env.GEMINI_API_KEY) {
    throw new Error('缺少 GEMINI_API_KEY，无法生成中文摘要');
  }
  if (!model) {
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });
  }
  return model;
}

async function summarizeToChinese(article) {
  const m = getModel();
  const base = `${article.title || ''}\n\n${article.description || ''}`.trim();
  const prompt = `
你是一名新闻编辑，请根据下面的英文新闻标题和摘要，用**简洁的中文**写出 1–2 句新闻概要。

要求：
- 不要逐字翻译标题，而是用中文概括新闻在讲什么
- 保持客观、中立，不加入个人观点
- 长度控制在 40 字以内，尽量精炼

英文原文：
${base || '（无更多内容，仅根据标题概括）'}
`.trim();

  const res = await m.generateContent(prompt);
  const text = res.response.text().trim();
  return text;
}

export async function attachChineseSummaries(articles) {
  // 如果没有配置 GEMINI_API_KEY，则直接返回英文内容
  if (!process.env.GEMINI_API_KEY) {
    return articles;
  }

  const output = [];
  for (const a of articles) {
    try {
      const cn = await summarizeToChinese(a);
      output.push({ ...a, cnSummary: cn });
    } catch (e) {
      console.warn('[translate] 生成中文摘要失败:', e.message);
      output.push(a);
    }
  }
  return output;
}

