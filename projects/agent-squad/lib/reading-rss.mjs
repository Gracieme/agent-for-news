/**
 * 外刊精读 RSS 数据源
 * - The Economist: Business/Science
 * - The Conversation: 学术视角深度新闻
 */
import axios from 'axios';
import { XMLParser } from 'fast-xml-parser';

const USER_AGENT = 'GracieEnglishAgent/2.0 (mailto:jiaxinshen1208@gmail.com)';
const TIMEOUT = 15000;

const RSS_FEEDS = [
  {
    name: 'The Economist',
    url: 'https://www.economist.com/weeklyedition/rss.xml',
    fallback: 'http://www.economist.com/sections/business-finance/rss.xml',
  },
  {
    name: 'The Conversation',
    url: 'https://theconversation.com/international/articles.atom',
  },
];

function parseRssItems(xml, feedName) {
  const parser = new XMLParser({ ignoreAttributes: false });
  let parsed;
  try {
    parsed = parser.parse(xml);
  } catch {
    return [];
  }
  const channel = parsed?.rss?.channel || parsed?.feed;
  if (!channel) return [];
  let items = channel.item || channel.entry;
  if (!Array.isArray(items)) items = items ? [items] : [];
  return items.map((it) => {
    const title = it.title || (typeof it.title === 'object' ? it.title['#text'] : '') || '';
    let href = '';
    const link = it.link;
    if (typeof link === 'string') href = link;
    else if (typeof link === 'object') {
      href = link['@_href'] || link['#text'] || link.href || '';
      if (!href && Array.isArray(link)) href = link.find((l) => l['@_rel'] !== 'self')?.['@_href'] || link[0]?.['@_href'] || '';
    }
    const desc = it.description || it.summary || it.content;
    const descText = typeof desc === 'string' ? desc : (desc?.['#text'] || desc?.['_'] || '') || '';
    const pubDate = it.pubDate || it.published || it.updated || '';
    return {
      title: String(title).trim(),
      url: href,
      description: String(descText).slice(0, 1500),
      pubDate,
      source: feedName,
    };
  });
}

export async function fetchReadingArticles(limit = 3) {
  const results = [];
  for (const feed of RSS_FEEDS) {
    const urls = [feed.url, feed.fallback].filter(Boolean);
    for (const url of urls) {
      try {
        const { data } = await axios.get(url, {
          headers: { 'User-Agent': USER_AGENT },
          timeout: TIMEOUT,
        });
        const items = parseRssItems(data, feed.name);
        if (items.length > 0) {
          results.push(...items.slice(0, Math.ceil(limit / RSS_FEEDS.length)));
          break;
        }
      } catch (e) {
        console.warn(`[reading-rss] ${feed.name} 失败:`, e.message);
      }
    }
  }
  return results.slice(0, limit);
}
