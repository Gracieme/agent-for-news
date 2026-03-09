/**
 * 新闻总结助手 - 定时任务
 * 每天 8:00、18:00（丹佛时间 America/Denver）各发送一封含 10 条新闻的邮件
 * 需在 news-assistant 目录下运行: node --env-file=.env scheduler.mjs
 * 或: npm start
 */
import 'dotenv/config';
import cron from 'node-cron';
import { fetchHeadlines } from './fetch-news.mjs';
import { sendNewsEmail } from './send-email.mjs';
import { TZ } from './config.mjs';
import { attachChineseSummaries } from './translate.mjs';

function getPrefix(hour) {
  return hour === 8 ? '【早报】今日新闻摘要' : '【晚间】今日新闻摘要';
}

async function job(hour) {
  const prefix = getPrefix(hour);
  console.log(`[scheduler] ${new Date().toLocaleString('zh-CN', { timeZone: TZ })} 执行 ${prefix}`);
  try {
    let articles = await fetchHeadlines(process.env.GNEWS_API_KEY, 3);
    articles = await attachChineseSummaries(articles);
    if (articles.length === 0) {
      console.warn('[scheduler] 未获取到文章，跳过发送');
      return;
    }
    const { to, subject } = await sendNewsEmail(articles, prefix);
    console.log(`[scheduler] 已发送: ${to} - ${subject}`);
  } catch (e) {
    console.error('[scheduler] 失败:', e.message);
  }
}

// 每天 8:00 和 18:00（丹佛时间 America/Denver）
cron.schedule('0 8 * * *', () => job(8), { timezone: TZ });
cron.schedule('0 18 * * *', () => job(18), { timezone: TZ });

console.log('[scheduler] 已启动。每天 8:00、18:00（丹佛时间 America/Denver）发送新闻摘要到邮箱。');
console.log('[scheduler] 按 Ctrl+C 退出。');
