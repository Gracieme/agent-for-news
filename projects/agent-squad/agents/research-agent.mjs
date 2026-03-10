/**
 * 科研文献助手：按研究方向检索论文，每日 3 篇，含作者、期刊、引用量、摘要、与研究的关联性
 * 数据源：Semantic Scholar + OpenAlex（先试 Semantic Scholar，不足时用 OpenAlex 补充）
 */
import axios from 'axios';
import { generateWithGemini } from '../lib/gemini.mjs';
import {
  RESEARCH_TOPICS,
  PAPERS_PER_DAY,
  ACADEMIC_FRONTIER_QUERIES,
  SEMANTIC_SCHOLAR_BASE,
  OPENALEX_BASE,
  TARGET_EMAIL,
} from '../config.mjs';

const FIELDS = 'title,abstract,authors,year,citationCount,venue,url';
const SEARCH_LIMIT = 25;
const REQUEST_TIMEOUT = 15000;

// 很多 API 对无 User-Agent 或明显爬虫的请求会 403；OpenAlex 建议带 mailto 以便限流时联系
const USER_AGENT = 'GracieResearchAgent/1.0 (mailto:' + (process.env.TO_EMAIL || TARGET_EMAIL) + ')';
function getDefaultHeaders() {
  const h = { 'User-Agent': USER_AGENT };
  const key = process.env.SEMANTIC_SCHOLAR_API_KEY;
  if (key) h['x-api-key'] = key;
  return h;
}

function buildSearchQuery(queryMode = 'default') {
  if (queryMode === 'MICM' && Array.isArray(ACADEMIC_FRONTIER_QUERIES) && ACADEMIC_FRONTIER_QUERIES.length) {
    return ACADEMIC_FRONTIER_QUERIES.join(' ');
  }
  const flat = [
    ...RESEARCH_TOPICS.languagePower,
    ...RESEARCH_TOPICS.classroomInteraction,
    ...RESEARCH_TOPICS.teachersAndInstitutions,
  ];
  const unique = [...new Set(flat)];
  return unique.slice(0, 8).join(' ');
}

/** 统一论文结构，供后续筛选与邮件展示 */
function normalizePaper(p) {
  return {
    paperId: p.paperId || p.id || '',
    title: p.title || '',
    abstract: (p.abstract || '').slice(0, 800),
    year: p.year ?? null,
    citationCount: p.citationCount ?? 0,
    venue: p.venue || '',
    authors: p.authors || '',
    url: p.url || '',
  };
}

async function fetchPapersFromSemanticScholar(query) {
  const url = `${SEMANTIC_SCHOLAR_BASE}/paper/search`;
  const { data } = await axios.get(url, {
    params: { query, limit: SEARCH_LIMIT, fields: FIELDS },
    headers: getDefaultHeaders(),
    timeout: REQUEST_TIMEOUT,
  });
  const list = data.data || [];
  const currentYear = new Date().getFullYear();
  const minYear = currentYear - 3;
  return list
    .filter((p) => p.title && (p.abstract || p.title))
    .filter((p) => (p.year ?? 0) >= minYear)
    .map((p) =>
      normalizePaper({
        paperId: p.paperId,
        title: p.title,
        abstract: p.abstract || '',
        year: p.year,
        citationCount: p.citationCount ?? 0,
        venue: p.venue || '',
        authors: (p.authors || []).map((a) => a.name).join(', '),
        url: p.url || `https://www.semanticscholar.org/paper/${p.paperId}`,
      })
    );
}

/**
 * OpenAlex 检索：优先近 3 年论文 + 按引用排序（最新且最有影响力）
 * filter publication_year:>2021 即 2022 及以后
 */
async function fetchPapersFromOpenAlex(query, recentOnly = true) {
  const url = `${OPENALEX_BASE}/works`;
  const params = {
    search: query,
    per_page: SEARCH_LIMIT,
    sort: 'cited_by_count:desc',
    mailto: process.env.TO_EMAIL || TARGET_EMAIL,
  };
  if (recentOnly) {
    params.filter = 'publication_year:>2021';
  }
  const apiKey = process.env.OPENALEX_API_KEY;
  if (apiKey) params.api_key = apiKey;
  const { data } = await axios.get(url, {
    params,
    headers: { 'User-Agent': USER_AGENT },
    timeout: REQUEST_TIMEOUT,
  });
  const list = data.results || [];
  return list
    .filter((w) => w && w.display_name)
    .map((w) => {
      const authors = (w.authorships || [])
        .map((a) => a.author?.display_name)
        .filter(Boolean)
        .join(', ');
      const venue = w.primary_location?.source?.display_name || '';
      let abstract = (w.abstract || '').slice(0, 800);
      const idx = w.abstract_inverted_index;
      if (idx && typeof idx === 'object' && !Array.isArray(idx)) {
        try {
          abstract = Object.keys(idx)
            .sort(
              (a, b) =>
                (Math.min(...(idx[a] || [0])) || 0) - (Math.min(...(idx[b] || [0])) || 0)
            )
            .join(' ')
            .slice(0, 800);
        } catch (_) {}
      }
      const workId = (w.id || '').replace('https://openalex.org/', '');
      const landingUrl = w.primary_location?.landing_page_url || w.doi || w.id;
      return normalizePaper({
        paperId: workId,
        title: w.display_name,
        abstract,
        year: w.publication_year ?? null,
        citationCount: w.cited_by_count ?? 0,
        venue,
        authors,
        url: landingUrl || `https://openalex.org/${workId}`,
      });
    });
}

/** 按标题简单去重（保留先出现的） */
function dedupeByTitle(papers) {
  const seen = new Set();
  return papers.filter((p) => {
    const key = (p.title || '').toLowerCase().replace(/\s+/g, ' ').trim();
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/** @param {string} [queryMode] - 'default' | 'MICM' */
export async function runResearchAgent(queryMode = 'default') {
  const query = buildSearchQuery(queryMode);
  let papers = [];

  try {
    papers = await fetchPapersFromSemanticScholar(query);
    if (papers.length > 0) {
      console.error('[research-agent] Semantic Scholar 返回', papers.length, '篇');
    }
  } catch (e) {
    console.warn('[research-agent] Semantic Scholar 请求失败:', e.message);
  }

  if (papers.length < 10) {
    try {
      const openAlexPapers = await fetchPapersFromOpenAlex(query, true);
      if (openAlexPapers.length > 0) {
        console.error('[research-agent] OpenAlex 返回', openAlexPapers.length, '篇（近 3 年）');
        papers = dedupeByTitle([...papers, ...openAlexPapers]);
      }
    } catch (e) {
      console.warn('[research-agent] OpenAlex 请求失败:', e.message);
    }
  }

  // 主查询无结果时用更短、更通用的检索词再试 OpenAlex（放宽年份限制以保证有结果）
  if (papers.length === 0) {
    const fallbackQuery = 'second language classroom interaction L2';
    try {
      const openAlexPapers = await fetchPapersFromOpenAlex(fallbackQuery, false);
      if (openAlexPapers.length > 0) {
        console.error('[research-agent] OpenAlex 备用查询返回', openAlexPapers.length, '篇');
        papers = dedupeByTitle(openAlexPapers);
      }
    } catch (e) {
      console.warn('[research-agent] OpenAlex 备用查询失败:', e.message);
    }
  }

  if (papers.length === 0) {
    return {
      raw: '',
      papers: [],
      summary: '今日暂无匹配文献',
    };
  }

  const researchContext = `
研究方向：
1) 语言与权力：AP Chinese, assessment, epistemic injustice, hermeneutical injustice, washback, metalinguistic asymmetry, CDA
2) 课堂互动与中介：CSL, peer interaction, translanguaging, LRE, NoM, mediational architecture, MICM, novice-high
3) 教师与制度：charter/DLI, teacher vulnerability, decoupling, emotional labor, autoethnography, policy implementation
`;

  // 排序：优先近年（year 降序），同年内按引用量降序
  const sorted = [...papers].sort((a, b) => {
    const yearA = a.year ?? 0;
    const yearB = b.year ?? 0;
    if (yearB !== yearA) return yearB - yearA;
    return (b.citationCount || 0) - (a.citationCount || 0);
  });
  const top = sorted.slice(0, 15);

  const papersText = top
    .map(
      (p, i) =>
        `[${i + 1}] Title: ${p.title}\nAuthors: ${p.authors}\nYear: ${p.year}\nVenue: ${p.venue}\nCitations: ${p.citationCount}\nAbstract: ${p.abstract}`
    )
    .join('\n\n');

  const prompt = `You are a research assistant for a PhD student in language education / applied linguistics. The student's research interests are:
${researchContext}

From the following candidate papers, choose exactly ${PAPERS_PER_DAY} that are MOST relevant. Reply with only the numbers of the chosen papers, in order of relevance (most first), on one line, e.g.: 3, 7, 1

Candidate papers:
${papersText}`;

  let indicesLine;
  try {
    indicesLine = await generateWithGemini(prompt);
  } catch (e) {
    console.warn('[research-agent] Gemini 筛选失败:', e.message);
    const fallback = top.slice(0, PAPERS_PER_DAY).map((p) => ({ ...p, relevance: '（关联性解析暂不可用）' }));
    return { raw: '', papers: fallback, summary: `今日 ${PAPERS_PER_DAY} 篇文献` };
  }

  const nums = indicesLine
    .replace(/[^\d,]/g, '')
    .split(',')
    .map((s) => parseInt(s.trim(), 10))
    .filter((n) => n >= 1 && n <= top.length);
  const chosenIndices = [...new Set(nums)].slice(0, PAPERS_PER_DAY);
  const chosenPapers = chosenIndices.map((i) => top[i - 1]).filter(Boolean);

  if (chosenPapers.length === 0) {
    chosenPapers.push(...top.slice(0, PAPERS_PER_DAY));
  }

  const relevancePrompt = `For each of these ${chosenPapers.length} papers, write 2-4 sentences in 中文 explaining how it connects to the PhD student's research (language power / assessment, classroom interaction / CSL, or teachers / policy). Output only ${chosenPapers.length} short paragraphs, one per line, no labels. Order: same as the list.

Papers:
${chosenPapers.map((p) => p.title).join('\n')}`;

  let relevanceParagraphs = [];
  try {
    const relText = await generateWithGemini(relevancePrompt);
    relevanceParagraphs = relText.split(/\n+/).map((s) => s.trim()).filter(Boolean);
  } catch (_) {}

  const papersWithRelevance = chosenPapers.map((p, i) => ({
    ...p,
    relevance: relevanceParagraphs[i] || '（关联性说明暂无）',
  }));

  return {
    raw: papersWithRelevance
      .map(
        (p) =>
          `${p.title}\n${p.authors} | ${p.venue} | ${p.citationCount} 引用\n${p.abstract?.slice(0, 200)}…\n关联：${p.relevance}`
      )
      .join('\n\n'),
    papers: papersWithRelevance,
    summary: `今日 ${PAPERS_PER_DAY} 篇文献推荐（与您的研究方向关联）`,
  };
}
