/**
 * 新闻分类与 GNews API 映射
 * 科技、军事、财经、政治、娱乐、民生
 */
export const CATEGORIES = [
  { key: 'technology', name: '科技', gnews: 'technology' },
  { key: 'world', name: '军事/国际', gnews: 'world' },
  { key: 'business', name: '财经', gnews: 'business' },
  { key: 'nation', name: '政治', gnews: 'nation' },
  { key: 'entertainment', name: '娱乐', gnews: 'entertainment' },
  { key: 'health', name: '民生', gnews: 'health' },
];

// 使用丹佛时间（山地时区）
export const TZ = 'America/Denver';

export const TARGET_EMAIL = 'jiaxinshen1208@gmail.com';

export const ARTICLES_PER_EMAIL = 10;
