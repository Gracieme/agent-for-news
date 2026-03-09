/**
 * 一次性运行三个 Agent：每日生活口语、学术前沿、外刊精读
 * 输出 JSON 到 stdout，并写入 output、可选 Supabase、可选邮件（仅此三封）
 *
 * 使用：node --env-file=.env run-once.mjs
 */
import { runSpokenAgent } from './agents/spoken-agent.mjs';
import { runAcademicFrontierAgent } from './agents/academic-frontier-agent.mjs';
import { runReadingGuideAgent } from './agents/reading-guide-agent.mjs';
import { TZ } from './config.mjs';
import { writeFile, mkdir } from 'fs/promises';
import { join } from 'path';
import { sendDigestEmails } from './send-email.mjs';

const today = () => new Date().toLocaleDateString('zh-CN', { timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit' }).replace(/\//g, '-');

async function main() {
  const date = today();
  console.error(`[agent-squad] ${date} 开始运行…`);

  const [spoken, academicFrontier, readingGuide] = await Promise.all([
    runSpokenAgent().catch((e) => ({ cards: [], practice: {}, studyTip: '', summary: `口语助手暂不可用: ${e.message}` })),
    runAcademicFrontierAgent().catch((e) => ({ sections: [], summary: `学术前沿暂不可用: ${e.message}` })),
    runReadingGuideAgent().catch((e) => ({ source: 'BBC Future', date: '', title: '', url: '', excerptHtml: '', vocabCards: [], grammarSpotlight: [], apRows: [], teacherNote: '', summary: `外刊精读暂不可用: ${e.message}` })),
  ]);

  const digest = {
    date,
    generatedAt: new Date().toISOString(),
    spoken: {
      summary: spoken.summary,
      cards: spoken.cards || [],
      expressions: spoken.expressions || spoken.cards || [],
      practice: spoken.practice || {},
      studyTip: spoken.studyTip || '',
    },
    academicFrontier: {
      summary: academicFrontier.summary,
      sections: academicFrontier.sections || [],
    },
    readingGuide: {
      summary: readingGuide.summary,
      source: readingGuide.source,
      date: readingGuide.date,
      title: readingGuide.title,
      url: readingGuide.url,
      excerptHtml: readingGuide.excerptHtml,
      vocabCards: readingGuide.vocabCards || [],
      grammarSpotlight: readingGuide.grammarSpotlight || [],
      apRows: readingGuide.apRows || [],
      teacherNote: readingGuide.teacherNote || '',
      readability_level: readingGuide.readability_level || '',
      core_argument: readingGuide.core_argument || '',
      rhetorical_devices: readingGuide.rhetorical_devices || '',
      scaffolding_questions: readingGuide.scaffolding_questions || [],
      sentence_logic_map: readingGuide.sentence_logic_map || [],
      teaching_prompts: readingGuide.teaching_prompts || '',
    },
  };

  console.log(JSON.stringify(digest, null, 2));

  const outDir = join(process.cwd(), 'output');
  try {
    await mkdir(outDir, { recursive: true });
    const path = join(outDir, `digest-${date}.json`);
    await writeFile(path, JSON.stringify(digest, null, 2), 'utf8');
    console.error(`[agent-squad] 已写入 ${path}`);
  } catch (e) {
    console.error('[agent-squad] 写入 output 目录失败:', e.message);
  }

  if (process.env.EMAIL_USER && process.env.EMAIL_PASS) {
    try {
      const results = await sendDigestEmails(digest);
      const to = results[0]?.to;
      const count = results.length;
      console.error(`[agent-squad] 已发送 ${count} 封邮件到 ${to}：每日生活口语、学术前沿、外刊精读`);
    } catch (e) {
      console.error('[agent-squad] 发送邮件失败:', e.message);
    }
  } else {
    console.error('[agent-squad] 未配置 EMAIL_USER/EMAIL_PASS，跳过邮件发送');
  }

  if (process.env.SUPABASE_URL && process.env.SUPABASE_SERVICE_ROLE_KEY) {
    try {
      const { createClient } = await import('@supabase/supabase-js');
      const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_ROLE_KEY);
      await supabase.from('agent_digests').upsert([{ date, digest }], { onConflict: 'date' });
      console.error('[agent-squad] 已同步到 Supabase agent_digests');
    } catch (e) {
      console.error('[agent-squad] Supabase 同步失败:', e.message);
    }
  }

  console.error('[agent-squad] 完成');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
