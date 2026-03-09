/**
 * 执行一次：拉取新闻并发送邮件（用于测试或手动触发）
 * 用法: node run-once.mjs [morning|evening]
 */
import 'dotenv/config';
import { fetchHeadlines } from './fetch-news.mjs';
import { sendNewsEmail } from './send-email.mjs';
import { attachChineseSummaries } from './translate.mjs';

const period = process.argv[2] || 'morning';
const prefix = period === 'evening' ? '【晚间】今日新闻摘要' : '【早报】今日新闻摘要';

async function main() {
  console.log(`[run-once] 开始拉取新闻 (${prefix})...`);
  const apiKey = process.env.GNEWS_API_KEY;
  let articles = await fetchHeadlines(apiKey, 3);
  articles = await attachChineseSummaries(articles);
  console.log(`[run-once] 获取到 ${articles.length} 条`);

  if (articles.length === 0) {
    console.warn('[run-once] 无文章，跳过发送');
    process.exit(0);
    return;
  }

  const { to, subject } = await sendNewsEmail(articles, prefix);
  console.log(`[run-once] 已发送到 ${to}: ${subject}`);
}

main().catch((e) => {
  console.error('[run-once]', e);
  process.exit(1);
});
