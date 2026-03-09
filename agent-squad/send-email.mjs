import nodemailer from 'nodemailer';
import {
  buildDigestHtml,
  buildSpokenHtml,
  buildAcademicFrontierHtml,
  buildReadingGuideHtml,
} from './build-email.mjs';
import { TARGET_EMAIL } from './config.mjs';

function getTransporter() {
  const user = process.env.EMAIL_USER;
  const pass = process.env.EMAIL_PASS;
  if (!user || !pass) {
    throw new Error('请在 agent-squad/.env 中设置 EMAIL_USER 和 EMAIL_PASS（Gmail 需使用应用专用密码）');
  }
  return nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: Number(process.env.SMTP_PORT) || 587,
    secure: false,
    auth: { user, pass },
  });
}

function getTo() {
  return process.env.TO_EMAIL || TARGET_EMAIL;
}

/** 日期格式 2026-03-08 → 2026年03月08日 */
function dateFormatted(dateStr) {
  const m = (dateStr || '').match(/(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${m[1]}年${m[2]}月${m[3]}日` : dateStr || '';
}

/**
 * 仅发送三封邮件：每日生活口语、学术前沿、外刊精读
 * 需环境变量: EMAIL_USER, EMAIL_PASS
 */
export async function sendDigestEmails(digest) {
  const transporter = getTransporter();
  const to = getTo();
  const dateStr =
    digest.date ||
    new Date()
      .toLocaleDateString('zh-CN', { timeZone: 'America/Denver', year: 'numeric', month: '2-digit', day: '2-digit' })
      .replace(/\//g, '-');
  const formatted = dateFormatted(dateStr);
  const results = [];

  const spokenSubject = `🎬 每日生活口语 · ${formatted}`;
  await transporter.sendMail({
    from: `"Gracie English Agent" <${process.env.EMAIL_USER}>`,
    to,
    subject: spokenSubject,
    html: buildSpokenHtml(digest.spoken, dateStr),
  });
  results.push({ to, subject: spokenSubject });

  const academicSubject = `🔬 学术前沿 · ${formatted}`;
  await transporter.sendMail({
    from: `"Gracie Research Agent" <${process.env.EMAIL_USER}>`,
    to,
    subject: academicSubject,
    html: buildAcademicFrontierHtml(digest.academicFrontier, dateStr),
  });
  results.push({ to, subject: academicSubject });

  const readingSubject = `📖 外刊精读 · BBC · Future · ${formatted}`;
  await transporter.sendMail({
    from: `"Gracie Reading Agent" <${process.env.EMAIL_USER}>`,
    to,
    subject: readingSubject,
    html: buildReadingGuideHtml(digest.readingGuide, dateStr),
  });
  results.push({ to, subject: readingSubject });

  return results;
}

/**
 * 发送一封合订版邮件（保留，需要时可调用）
 */
export async function sendDigestEmail(digest, subject) {
  const transporter = getTransporter();
  const to = getTo();
  const html = buildDigestHtml(digest, subject);
  await transporter.sendMail({
    from: `"Gracie Agent Squad" <${process.env.EMAIL_USER}>`,
    to,
    subject,
    html,
  });
  return { to, subject };
}

