import nodemailer from 'nodemailer';
import { buildHtml } from './build-email.mjs';
import { TARGET_EMAIL } from './config.mjs';

/**
 * 使用 SMTP 发送新闻摘要邮件
 * 需环境变量: EMAIL_USER, EMAIL_PASS (Gmail 用应用专用密码), TO_EMAIL 可选，默认 config 中的邮箱
 */
export async function sendNewsEmail(articles, subjectPrefix) {
  const user = process.env.EMAIL_USER;
  const pass = process.env.EMAIL_PASS;
  const to = process.env.TO_EMAIL || TARGET_EMAIL;

  if (!user || !pass) throw new Error('请设置 EMAIL_USER 和 EMAIL_PASS（Gmail 需使用应用专用密码）');

  const transporter = nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: Number(process.env.SMTP_PORT) || 587,
    secure: false,
    auth: { user, pass },
  });

  const html = buildHtml(articles, subjectPrefix);
  const subject = `${subjectPrefix} · ${articles.length} 条`;

  await transporter.sendMail({
    from: `"新闻总结助手" <${user}>`,
    to,
    subject,
    html,
  });

  return { to, subject };
}
