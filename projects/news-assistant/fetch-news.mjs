import axios from 'axios';
import { CATEGORIES, ARTICLES_PER_EMAIL } from './config.mjs';

const GNEWS_BASE = 'https://gnews.io/api/v4';

/**
 * 从 GNews 按分类拉取头条（英文），合并去重后返回前 N 条
 * 标题保持英文，摘要后续用 Gemini 转成中文
 */
export async function fetchHeadlines(apiKey, maxPerCategory = 3) {
  if (!apiKey) throw new Error('缺少 GNEWS_API_KEY');

  const results = [];
  for (const cat of CATEGORIES) {
    try {
      const { data } = await axios.get(`${GNEWS_BASE}/top-headlines`, {
        params: {
          category: cat.gnews,
          lang: 'en',
          max: maxPerCategory,
          apikey: apiKey,
        },
        timeout: 10000,
      });
      const articles = (data.articles || []).map((a) => ({
        title: a.title || 'Untitled',
        description: a.description || a.content || '',
        url: a.url || '#',
        source: a.source?.name || 'Unknown',
        publishedAt: a.publishedAt || '',
        categoryName: cat.name,
        categoryKey: cat.key,
      }));
      results.push(...articles);
    } catch (e) {
      console.warn(`[fetch] ${cat.name} 拉取失败:`, e.message);
    }
  }

  // 按时间倒序，去重（同 URL 只保留一条），取前 N 条
  const seen = new Set();
  const deduped = results
    .filter((a) => {
      if (seen.has(a.url)) return false;
      seen.add(a.url);
      return true;
    })
    .sort((a, b) => new Date(b.publishedAt) - new Date(a.publishedAt))
    .slice(0, ARTICLES_PER_EMAIL);

  return deduped;
}
