import { TZ } from './config.mjs';

/**
 * 根据文章列表生成 HTML 邮件内容
 * 排版参照主流新闻站：清晰层次、留白、可读字体
 * - 标题：英文
 * - 摘要：优先 cnSummary（中文），否则 description
 */
export function buildHtml(articles, subjectPrefix) {
  const dateStr = formatDate(new Date().toISOString(), true);

  const items = articles
    .map((a, i) => {
      const summary = a.cnSummary || a.description || '';
      const summarySnippet = summary
        ? escapeHtml(summary.slice(0, 140)) + (summary.length > 140 ? '…' : '')
        : '';

      return `
  <tr>
    <td class="item" style="padding: 20px 0 24px; border-bottom: 1px solid #e8e8e8;">
      <p class="meta" style="margin: 0 0 6px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; color: #888;">
        ${escapeHtml(a.categoryName)}
      </p>
      <a href="${a.url}" class="headline" style="display: block; margin: 0 0 8px; font-size: 17px; line-height: 1.35; font-weight: 600; color: #1a1a1a; text-decoration: none;">${escapeHtml(a.title)}</a>
      ${summarySnippet ? `<p class="summary" style="margin: 0 0 10px; font-size: 14px; line-height: 1.55; color: #4a4a4a;">${summarySnippet}</p>` : ''}
      <p class="source" style="margin: 0; font-size: 12px; color: #999;">${escapeHtml(a.source)} · ${formatDate(a.publishedAt)}</p>
    </td>
  </tr>`;
    })
    .join('');

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>${escapeHtml(subjectPrefix)}</title>
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
</head>
<body style="margin: 0; padding: 0; background-color: #f0f0f0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; line-height: 1.5; color: #1a1a1a;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #f0f0f0;">
    <tr>
      <td align="center" style="padding: 32px 16px 40px;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width: 560px; margin: 0 auto; background-color: #ffffff; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
          <tr>
            <td style="padding: 28px 32px 20px;">
              <p style="margin: 0 0 4px; font-size: 11px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: #999;">News Digest</p>
              <h1 style="margin: 0 0 8px; font-size: 22px; font-weight: 700; letter-spacing: -0.02em; color: #1a1a1a;">${escapeHtml(subjectPrefix)}</h1>
              <p style="margin: 0; font-size: 13px; color: #666;">${dateStr} · ${articles.length} 条</p>
            </td>
          </tr>
          <tr>
            <td style="padding: 0 32px 28px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                ${items}
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding: 20px 32px 24px; border-top: 1px solid #e8e8e8;">
              <p style="margin: 0; font-size: 11px; color: #aaa;">新闻总结助手 · 请勿直接回复</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDate(iso, full = false) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    if (full) {
      return d.toLocaleDateString('zh-CN', {
        timeZone: TZ,
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
    return d.toLocaleString('zh-CN', {
      timeZone: TZ,
      month: 'numeric',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return typeof iso === 'string' ? iso.slice(0, 16) : '';
  }
}
