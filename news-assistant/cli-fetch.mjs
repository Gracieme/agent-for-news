import 'dotenv/config';
import { fetchHeadlines } from './fetch-news.mjs';

const articles = await fetchHeadlines(process.env.GNEWS_API_KEY, 3);
console.log(`拉取到 ${articles.length} 条`);
articles.forEach((a, i) => console.log(`${i + 1}. [${a.categoryName}] ${a.title}`));
