#!/usr/bin/env node
/**
 * 检查当前环境是否已配置好「发邮件」所需的变量（不输出任何密码）
 * 使用：node --env-file=.env check-email-config.mjs
 */
const hasGemini = !!process.env.GEMINI_API_KEY;
const hasUser = !!process.env.EMAIL_USER;
const hasPass = !!process.env.EMAIL_PASS;

console.log('');
console.log('  Agent 小队 · 发邮件配置检查');
console.log('  -----------------------------');
console.log('  GEMINI_API_KEY:  ' + (hasGemini ? '已设置 ✓' : '未设置 ✗'));
console.log('  EMAIL_USER:      ' + (hasUser ? '已设置 ✓' : '未设置 ✗'));
console.log('  EMAIL_PASS:      ' + (hasPass ? '已设置 ✓' : '未设置 ✗'));
console.log('  -----------------------------');

if (hasUser && hasPass) {
  const to = process.env.TO_EMAIL || 'jiaxinshen1208@gmail.com（默认）';
  console.log('  收件邮箱:        ' + to);
  console.log('');
  console.log('  → 可以发邮件。运行: npm run run-once');
} else {
  console.log('');
  console.log('  → 请先在 .env 中填写 EMAIL_USER 和 EMAIL_PASS（Gmail 用应用专用密码，16 位连写）');
  console.log('  → 参考 README「通过这个办法让 Agent 给你发邮件」');
}
console.log('');
