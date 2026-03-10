/**
 * BBC Learning English RSS 数据源
 * - 6 Minute English: https://feeds.bbci.co.uk/learningenglish/english/features/6-minute-english/rss
 * - The English We Speak: https://feeds.bbci.co.uk/learningenglish/english/features/the-english-we-speak/rss
 */
import axios from 'axios';
import { XMLParser } from 'fast-xml-parser';

const USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36';
const TIMEOUT = 12000;

const RSS_URLS = {
  sixMinute: 'https://feeds.bbci.co.uk/learningenglish/english/features/6-minute-english/rss',
  englishWeSpeak: 'https://feeds.bbci.co.uk/learningenglish/english/features/the-english-we-speak/rss',
};

function parseRssItems(xml) {
  const parser = new XMLParser({ ignoreAttributes: false });
  let parsed;
  try {
    parsed = parser.parse(xml);
  } catch {
    return [];
  }
  const channel = parsed?.rss?.channel || parsed?.feed;
  if (!channel) return [];
  let items = channel.item;
  if (!items) items = channel.entry;
  if (!Array.isArray(items)) items = items ? [items] : [];
  return items.map((it) => {
    const title = it.title || (typeof it.title === 'object' ? it.title['#text'] : '') || '';
    const link = it.link;
    let href = typeof link === 'string' ? link : '';
    if (typeof link === 'object') {
      href = link['@_href'] || link['#text'] || link.href || '';
    }
    const desc = it.description || it.summary || '';
    const descText = typeof desc === 'string' ? desc : (desc['#text'] || desc['_'] || '');
    const enclosure = it.enclosure;
    let audioUrl = '';
    if (enclosure) {
      const enc = Array.isArray(enclosure) ? enclosure[0] : enclosure;
      if (enc && (enc['@_type'] || enc.type || '').toString().startsWith('audio/')) {
        audioUrl = enc['@_url'] || enc['@_href'] || enc.url || '';
      }
    }
    const pubDate = it.pubDate || it.published || '';
    return {
      title: String(title).trim(),
      url: href,
      description: String(descText).slice(0, 1000),
      audioUrl: audioUrl || null,
      pubDate,
      source: '6min' in (it || {}) ? '6 Minute English' : 'The English We Speak',
    };
  });
}

export async function fetchBbcSixMinuteEnglish(limit = 3) {
  try {
    const { data } = await axios.get(RSS_URLS.sixMinute, {
      headers: { 'User-Agent': USER_AGENT },
      timeout: TIMEOUT,
    });
    const items = parseRssItems(data);
    return items.slice(0, limit).map((i) => ({ ...i, source: '6 Minute English' }));
  } catch (e) {
    console.warn('[bbc-rss] 6 Minute English 失败:', e.message);
    return [];
  }
}

export async function fetchBbcTheEnglishWeSpeak(limit = 5) {
  try {
    const { data } = await axios.get(RSS_URLS.englishWeSpeak, {
      headers: { 'User-Agent': USER_AGENT },
      timeout: TIMEOUT,
    });
    const items = parseRssItems(data);
    return items.slice(0, limit).map((i) => ({ ...i, source: 'The English We Speak' }));
  } catch (e) {
    console.warn('[bbc-rss] The English We Speak 失败:', e.message);
    return [];
  }
}

/**
 * 只使用 The English We Speak（教俚语/口语表达）
 * 6 Minute English 是话题讨论，非俚语，不纳入每日生活口语
 */
export async function fetchBbcSpokenExpressions(totalLimit = 6) {
  return fetchBbcTheEnglishWeSpeak(totalLimit);
}
