/**
 * Agent 小队定时任务：每天丹佛时间 8:00 运行一次
 * 在 agent-squad 目录下运行: node --env-file=.env scheduler.mjs
 */
import 'dotenv/config';
import cron from 'node-cron';
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { TZ } from './config.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));

function runOnce() {
  return new Promise((resolve, reject) => {
    const child = spawn('node', ['--env-file=.env', 'run-once.mjs'], {
      cwd: join(__dirname),
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: true,
    });
    child.stdout.pipe(process.stdout);
    child.stderr.pipe(process.stderr);
    child.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`exit ${code}`))));
  });
}

// 每天 8:00 丹佛时间（America/Denver）
cron.schedule('0 8 * * *', async () => {
  console.log(`[scheduler] ${new Date().toLocaleString('zh-CN', { timeZone: TZ })} 执行 Agent 小队`);
  try {
    await runOnce();
  } catch (e) {
    console.error('[scheduler] 执行失败:', e.message);
  }
}, { timezone: TZ });

console.log('[scheduler] Agent 小队已启动，每天 8:00（丹佛时间 America/Denver）运行。按 Ctrl+C 退出。');
