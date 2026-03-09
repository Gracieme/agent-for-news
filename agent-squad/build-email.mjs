import { TZ } from './config.mjs';

function formatDate(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleString('zh-CN', {
      timeZone: TZ,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return iso;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** 科研：绿色学术风格 */
const RESEARCH_STYLES = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
      background: #f0f4f0;
      color: #1a2e1a;
      line-height: 1.75;
      padding: 24px 16px;
    }
    .wrapper {
      max-width: 700px;
      margin: 0 auto;
      background: #fff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(0,60,0,0.10);
    }
    .header {
      background: linear-gradient(135deg, #1b4332 0%, #2d6a4f 55%, #40916c 100%);
      padding: 36px 40px 28px;
      text-align: center;
      color: #fff;
    }
    .header .label {
      font-size: 11px;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: rgba(255,255,255,0.5);
      margin-bottom: 10px;
    }
    .header h1 { font-size: 26px; font-weight: 800; margin-bottom: 8px; }
    .header .subtitle { font-size: 12px; color: rgba(255,255,255,0.6); line-height: 1.7; }
    .header hr { border: none; border-top: 1px solid rgba(255,255,255,0.15); margin-top: 18px; }
    .body { padding: 32px 36px 40px; }
    .paper-card {
      border: 1px solid #c8dfc8;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 3px 14px rgba(0,60,0,0.08);
      margin-bottom: 20px;
    }
    .paper-meta {
      background: #f0f7f0;
      padding: 12px 20px;
      border-bottom: 1px solid #c8dfc8;
    }
    .paper-meta-table { width: 100%; border-collapse: collapse; }
    .paper-meta-table td { padding: 0; vertical-align: middle; }
    .paper-year {
      font-size: 12px;
      font-weight: 800;
      color: #fff;
      background: #2d6a4f;
      padding: 4px 12px;
      border-radius: 999px;
      margin-right: 10px;
    }
    .journal-badge {
      font-size: 12px;
      color: #2d6a4f;
      font-weight: 600;
      font-style: italic;
      margin-right: 10px;
    }
    .citation-badge { font-size: 11px; color: #888; }
    .paper-title {
      font-size: 20px;
      font-weight: 800;
      color: #1b4332;
      padding: 18px 20px 8px;
      line-height: 1.4;
      margin: 0;
    }
    .paper-authors {
      font-size: 13px;
      color: #666;
      padding: 0 20px 16px;
      font-style: italic;
      border-bottom: 1px solid #eef5ee;
    }
    .section-label {
      font-size: 10.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #40916c;
      padding: 14px 20px 6px;
      margin: 0;
      display: block;
    }
    .abstract-text {
      font-size: 13.5px;
      color: #455a64;
      padding: 8px 20px 16px;
      line-height: 1.8;
      background: #f8fff8;
      border-bottom: 1px solid #eef5ee;
      margin: 0;
    }
    .relevance-text {
      font-size: 14.5px;
      color: #1a2e1a;
      padding: 8px 20px 16px;
      line-height: 1.8;
      border-bottom: 1px solid #eef5ee;
      margin: 0;
    }
    .paper-links {
      padding: 16px 20px;
      background: #f0f7f0;
      text-align: center;
    }
    .paper-link {
      display: inline-block;
      background: #1565c0;
      color: #fff !important;
      text-decoration: none;
      font-size: 14px;
      font-weight: 700;
      padding: 10px 28px;
      border-radius: 8px;
      letter-spacing: 0.3px;
      box-shadow: 0 2px 4px rgba(21,101,192,0.3);
    }
    .content-card .paper-title { font-size: 18px; }
    .content-card .abstract-text { white-space: pre-wrap; }
    .digest-section-header {
      font-size: 13px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      color: #2d6a4f;
      padding: 24px 0 10px;
      border-bottom: 2px solid #c8dfc8;
      margin-bottom: 18px;
    }
    .findings-list {
      padding: 8px 20px 16px;
      background: #f8fff8;
      border-bottom: 1px solid #eef5ee;
      margin: 0;
    }
    .finding-item {
      font-size: 14px;
      color: #2d3b2d;
      padding: 7px 0;
      line-height: 1.75;
      border-bottom: 1px dashed #d8ecd8;
    }
    .finding-item:last-child { border-bottom: none; }
    .implications-text {
      font-size: 14.5px;
      color: #1b4332;
      background: #e8f5e9;
      border-left: 4px solid #40916c;
      padding: 14px 20px;
      line-height: 1.8;
      border-bottom: 1px solid #c8dfc8;
    }
    .bibtex-block {
      font-family: monospace;
      font-size: 11px;
      background: #f0f7f0;
      padding: 12px 20px;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-all;
      border: 1px solid #c8dfc8;
      border-radius: 6px;
      margin: 8px 20px 16px;
      line-height: 1.5;
    }
    .footer {
      text-align: center;
      padding: 16px 32px;
      font-size: 12px;
      color: #aaa;
      border-top: 1px solid #eee;
      background: #f7faf7;
    }
`;

/** 英语：橙色风格 */
const ENGLISH_STYLES = `
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
      background: #fff8f0;
      color: #2e1a0a;
      line-height: 1.75;
      padding: 24px 16px;
    }
    .wrapper {
      max-width: 700px;
      margin: 0 auto;
      background: #fff;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 24px rgba(230, 81, 0, 0.12);
    }
    .header {
      background: linear-gradient(135deg, #e65100 0%, #f57c00 50%, #ffb74d 100%);
      padding: 36px 40px 28px;
      text-align: center;
      color: #fff;
    }
    .header .label {
      font-size: 11px;
      letter-spacing: 3px;
      text-transform: uppercase;
      color: rgba(255,255,255,0.7);
      margin-bottom: 10px;
    }
    .header h1 { font-size: 26px; font-weight: 800; margin-bottom: 8px; }
    .header .subtitle { font-size: 12px; color: rgba(255,255,255,0.85); line-height: 1.7; }
    .header hr { border: none; border-top: 1px solid rgba(255,255,255,0.25); margin-top: 18px; }
    .body { padding: 32px 36px 40px; }
    .paper-card {
      border: 1px solid #ffe0b2;
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 3px 14px rgba(230, 81, 0, 0.08);
      margin-bottom: 20px;
    }
    .paper-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      background: #fff3e0;
      padding: 10px 18px;
      border-bottom: 1px solid #ffe0b2;
    }
    .journal-badge { font-size: 12px; color: #e65100; font-weight: 600; font-style: italic; }
    .paper-title {
      font-size: 20px;
      font-weight: 800;
      color: #bf360c;
      padding: 18px 20px 6px;
      line-height: 1.4;
    }
    .section-label {
      font-size: 10.5px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #ef6c00;
      padding: 14px 20px 5px;
    }
    .abstract-text {
      font-size: 13.5px;
      color: #4e342e;
      padding: 4px 20px 16px;
      line-height: 1.8;
      background: #fff8f0;
      border-bottom: 1px solid #ffe0b2;
      white-space: pre-wrap;
      font-weight: 700;
    }
    .content-card .paper-title { font-size: 18px; }
    .footer {
      text-align: center;
      padding: 16px 32px;
      font-size: 12px;
      color: #a08060;
      border-top: 1px solid #ffe0b2;
      background: #fff8f0;
    }
`;

/** 每日生活口语：紫粉渐变、expr 卡片、练习对话、学习提示（与你提供的邮件格式一致） */
const SPOKEN_STYLES = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
    background: #f0f4f8;
    color: #1a1a2e;
    line-height: 1.75;
    padding: 0;
    margin: 0;
  }
  .email-wrapper {
    max-width: 680px;
    margin: 32px auto;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.10);
  }
  .email-header {
    background: linear-gradient(135deg, #1b0036 0%, #6a1b9a 60%, #ad1457 100%);
    padding: 36px 40px 28px;
    text-align: center;
    color: #fff;
  }
  .email-header h1 {
    margin: 0 0 6px;
    color: #fff;
    font-size: 26px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }
  .email-header .subtitle {
    margin: 0;
    color: rgba(255,255,255,0.78);
    font-size: 13px;
    letter-spacing: 0.3px;
  }
  .email-body { padding: 32px 40px 40px; max-width: 680px; }
  .expr-card {
    border: 1px solid #ede7f6;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    box-shadow: 0 2px 8px rgba(106,27,154,0.07);
  }
  .expr-header {
    background: #f9f5ff;
    padding: 16px 20px;
    border-bottom: 1px solid #ede7f6;
  }
  .expr-header-table { width: 100%; border-collapse: collapse; }
  .expr-header-table td { padding: 0; vertical-align: middle; }
  .expr-word {
    font-size: 19px;
    font-weight: 800;
    color: #4a148c;
    letter-spacing: 0.2px;
    margin: 0 0 8px 0;
  }
  .expr-tags { padding-top: 6px; }
  .expr-tags .source-tag,
  .expr-tags .region-tag,
  .expr-tags .audio-link { margin-right: 8px; margin-bottom: 4px; }
  .source-tag {
    display: inline-block;
    font-size: 11.5px;
    font-weight: 600;
    color: #6a1b9a;
    background: #ede7f6;
    padding: 4px 10px;
    border-radius: 999px;
  }
  .region-tag {
    display: inline-block;
    font-size: 11.5px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 999px;
  }
  .expr-body { padding: 20px; }
  .expr-body p {
    margin: 0 0 12px 0;
    font-size: 14.5px;
    color: #37474f;
  }
  .expr-body .field-label {
    font-size: 10.5px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    color: #7b1fa2;
    margin: 12px 0 6px 0;
    padding: 0;
  }
  .expr-body .field-label:first-child { margin-top: 0; }
  .example-en {
    background: #f3e5f5;
    border-left: 3px solid #8e24aa;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    font-size: 14.5px;
    font-style: italic;
    color: #3e0054;
    margin: 0 0 12px 0;
    line-height: 1.65;
  }
  .example-en.alt {
    background: #e8f5e9;
    border-left: 3px solid #43a047;
    color: #1b5e20;
  }
  .example-zh {
    background: #fff8e1;
    border-left: 3px solid #ffa000;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    font-size: 14.5px;
    color: #4e342e;
    margin: 0 0 12px 0;
    line-height: 1.65;
  }
  .nuance-box {
    background: #fff3e0;
    border-left: 3px solid #ff6d00;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    font-size: 13.5px;
    color: #4e342e;
    margin: 12px 0 0 0;
    line-height: 1.6;
  }
  .cultural-note-box {
    background: #e8eaf6;
    border-left: 3px solid #3f51b5;
    padding: 12px 16px;
    border-radius: 0 6px 6px 0;
    font-size: 13.5px;
    color: #1a237e;
    margin: 12px 0 0 0;
    line-height: 1.6;
  }
  .audio-link {
    display: inline-block;
    font-size: 11px;
    color: #fff !important;
    background: #7b1fa2;
    padding: 4px 10px;
    border-radius: 999px;
    text-decoration: none;
    vertical-align: middle;
  }
  .practice-box {
    border: 2px solid #ff6d00;
    border-radius: 12px;
    overflow: hidden;
    margin-top: 36px;
    margin-bottom: 8px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  }
  .practice-title {
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 0.4px;
    padding: 12px 18px;
    text-transform: uppercase;
    background: #ff6d00;
    color: #fff;
  }
  .practice-intro {
    font-size: 13px;
    color: #666;
    padding: 12px 20px 4px;
    margin: 0;
  }
  .scene-label {
    font-size: 13px;
    font-weight: 600;
    color: #bf360c;
    padding: 8px 20px 4px;
  }
  .story-text {
    font-size: 14.5px;
    line-height: 1.9;
    color: #1a1a2e;
    padding: 12px 20px 16px;
  }
  .story-zh {
    font-size: 14px;
    line-height: 1.8;
    color: #37474f;
    background: #fafafa;
    border-top: 1px solid #eee;
    padding: 12px 20px 16px;
  }
  mark.hl-spoken {
    background: #ffe0b2;
    color: #bf360c;
    font-weight: 700;
    border-radius: 3px;
    padding: 0 2px;
  }
  mark.hl-spoken-zh {
    background: #ffe0b2;
    color: #bf360c;
    font-weight: 700;
    border-radius: 3px;
    padding: 0 2px;
  }
  .study-tip {
    background: linear-gradient(135deg, #6a1b9a 0%, #ad1457 100%);
    color: #fff;
    border-radius: 12px;
    padding: 18px 24px;
    font-size: 14.5px;
    font-weight: 500;
    line-height: 1.7;
    margin-top: 32px;
  }
  .email-footer {
    background: #f5f7fa;
    border-top: 1px solid #ede7f6;
    padding: 18px 40px;
    text-align: center;
    color: #9e9e9e;
    font-size: 12px;
  }
`;

/**
 * 每日生活口语邮件（2.0：支持 expression, definition, nuance, cultural_note, audio_url, simulated_dialogue）
 * @param {Object} spoken - { cards/expressions, practice, studyTip }
 */
export function buildSpokenHtml(spoken, dateStr) {
  const cards = spoken?.cards || spoken?.expressions?.map((e) => ({
    word: e.expression,
    source: e.source || 'BBC Learning English',
    region: e.region || 'UK',
    explanation_zh: e.definition || e.explanation_zh,
    example_en: e.simulated_dialogue || e.example_en,
    translation_zh: e.translation_zh,
    alt_en: e.alt_en,
    nuance: e.nuance,
    cultural_note: e.cultural_note,
    audio_url: e.audio_url,
  })) || [];
  if (!spoken || cards.length === 0) {
    return buildSpokenHtmlPlaceholder(dateStr);
  }
  const cardsHtml = cards.map((c) => {
    const regionStyle = (c.region === 'US' || (c.region && c.region.includes('美')))
      ? 'background:#e3f2fd;color:#1565c0'
      : 'background:#f3e5f5;color:#6a1b9a';
    const altClass = c.alt_en ? ' example-en alt' : ' example-en';
    let nuance = '';
    if (c.nuance) {
      nuance = `<div class="nuance-box"><strong>Nuance Check</strong> ${escapeHtml(c.nuance)}</div>`;
    }
    let culturalNote = '';
    if (c.cultural_note) {
      culturalNote = `<div class="cultural-note-box"><strong>Cultural Note</strong> ${escapeHtml(c.cultural_note)}</div>`;
    }
    const audioLink = c.audio_url ? `<a href="${escapeHtml(c.audio_url)}" class="audio-link">🔊 收听原音</a>` : '';
    return `
<div class="expr-card">
  <div class="expr-header">
    <table class="expr-header-table" cellpadding="0" cellspacing="0"><tr><td>
      <div class="expr-word">${escapeHtml(c.word)}</div>
      <div class="expr-tags">
        <span class="source-tag">${escapeHtml(c.source || 'BBC Learning English')}</span>
        <span class="region-tag" style="${regionStyle}">${escapeHtml(c.region || 'UK')}</span>
        ${audioLink}
      </div>
    </td></tr></table>
  </div>
  <div class="expr-body">
    <div class="field-label">口语讲解</div>
    <p>${escapeHtml(c.explanation_zh || '')}</p>
    <div class="field-label">情景对话 / 例句</div>
    <div class="${altClass.trim()}">${escapeHtml(c.example_en || '')}</div>
    ${c.translation_zh ? `<div class="field-label">口语翻译</div><div class="example-zh">${escapeHtml(c.translation_zh)}</div>` : ''}
    ${c.alt_en ? `<div class="field-label">地道说法</div><div class="example-en alt">${escapeHtml(c.alt_en)}</div>` : ''}
    ${nuance}
    ${culturalNote}
  </div>
</div>`;
  }).join('');

  const practice = spoken.practice || {};
  const sceneLabel = escapeHtml(practice.sceneLabel || '场景');
  const rawEn = practice.storyEn || '';
  const rawZh = practice.storyZh || '';
  const storyEn = rawEn.includes('<mark') ? rawEn : escapeHtml(rawEn);
  const storyZh = rawZh.includes('<mark') ? rawZh : escapeHtml(rawZh);
  const studyTip = escapeHtml(spoken.studyTip || '多听多练，把今日短语放进真实对话里用一次。');

  const dateFormatted = (() => {
    const [y, m, d] = (dateStr || '').split('-');
    return y && m && d ? `${y}年${parseInt(m, 10)}月${parseInt(d, 10)}日` : (dateStr || '');
  })();

  const title = `每日生活口语 · ${dateFormatted}`;
  const subtitle = `C1 口语 © ${dateFormatted} © 美式 / 英式 / YouTube 口语 等 12`;

  return `<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <style>${SPOKEN_STYLES}</style>
</head>
<body>
<div class="email-wrapper">
  <div class="email-header">
    <h1>🎬 每日生活口语</h1>
    <p class="subtitle">${subtitle}</p>
  </div>
  <div class="email-body">
    ${cardsHtml}
    <div class="practice-box">
      <div class="practice-title">🎬 情景对话 · 开口练</div>
      <p class="practice-intro">围绕 12 条短语设计一段对话，开口跟读并尝试替换<mark class="hl-spoken-zh">今日短语</mark>。</p>
      <div class="scene-label">${sceneLabel}</div>
      <div class="story-text">${storyEn}</div>
      <div class="story-zh">${storyZh}</div>
    </div>
    <div class="study-tip">${studyTip}</div>
  </div>
  <div class="email-footer">
    由 English Agent 生成 © 每日发送 9:00 晨间
  </div>
</div>
</body>
</html>`;
}

function buildSpokenHtmlPlaceholder(dateStr) {
  const dateFormatted = (() => {
    const [y, m, d] = (dateStr || '').split('-');
    return y && m && d ? `${y}年${parseInt(m, 10)}月${parseInt(d, 10)}日` : (dateStr || '');
  })();
  const title = `每日生活口语 · ${dateFormatted}`;
  return `<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <style>${SPOKEN_STYLES}</style>
</head>
<body>
<div class="email-wrapper">
  <div class="email-header">
    <h1>🎬 每日生活口语</h1>
    <p class="subtitle">C1 口语 © ${dateFormatted}</p>
  </div>
  <div class="email-body">
    <p style="color:#666;">今日口语内容生成中，请稍后再查看。</p>
  </div>
  <div class="email-footer">由 English Agent 生成 © 每日发送 9:00 晨间</div>
</div>
</body>
</html>`;
}

function wrapEmail(title, dateStr, subtitle, bodyHtml, footerText, styles = RESEARCH_STYLES) {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <title>${escapeHtml(title)}</title>
  <style>${styles}</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="label">${escapeHtml(dateStr)}</div>
    <h1>${escapeHtml(title)}</h1>
    <div class="subtitle">${subtitle}</div>
    <hr>
  </div>
  <div class="body">${bodyHtml}</div>
  <div class="footer">${escapeHtml(footerText)}</div>
</div>
</body>
</html>`;
}

/** 仅英语：C1 习语/谚语，一封邮件（橙色风格） */
export function buildEnglishHtml(english, dateStr) {
  const raw = english?.raw || '';
  const cleaned = raw.replace(/\*/g, '');
  const block = escapeHtml(cleaned);
  const title = `📚 英语 · C1 习语/谚语 · ${dateStr}`;
  const body = `
    <div class="paper-card content-card">
      <div class="paper-meta">
        <span class="journal-badge">English Agent · 多地区</span>
      </div>
      <div class="paper-title">C1 习语 / 谚语 · 中英对照</div>
      <div class="section-label">📝 今日段落</div>
      <div class="abstract-text">${block || '（暂无内容）'}</div>
    </div>`;
  return wrapEmail(
    title,
    dateStr,
    '由 Gracie Agent 小队 · Gemini 生成',
    body,
    '早安 English Agent · 8:00 丹佛时间',
    ENGLISH_STYLES
  );
}

/** 美妆专用样式：仿「每日化妆课」粉紫风格 */
const MAKEUP_STYLES = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: #fce4ec;
    color: #2c1a22;
    line-height: 1.85;
    padding: 24px 12px;
  }
  .card-wrapper {
    max-width: 680px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(176, 0, 60, 0.12);
  }
  .email-header {
    background: linear-gradient(135deg, #b5003c 0%, #e91e8c 100%);
    padding: 36px 32px 28px;
    text-align: center;
    color: #ffffff;
  }
  .email-header h1 { font-size: 26px; font-weight: 800; letter-spacing: 2px; margin-bottom: 6px; }
  .email-header .subtitle { font-size: 13px; opacity: 0.88; letter-spacing: 1px; }
  .email-header .date-badge {
    display: inline-block;
    margin-top: 12px;
    background: rgba(255,255,255,0.2);
    border-radius: 20px;
    padding: 4px 16px;
    font-size: 12px;
    letter-spacing: 1px;
  }
  .email-body { padding: 32px 32px 24px; }
  .section-title {
    font-size: 17px;
    font-weight: 700;
    color: #b5003c;
    margin: 28px 0 12px;
    padding-bottom: 6px;
    border-bottom: 2px solid #f8bbd0;
  }
  .section-title:first-of-type { margin-top: 0; }
  .step-card {
    background: #fff8fa;
    border: 1px solid #f8bbd0;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 18px;
  }
  .step-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #b5003c, #e91e8c);
    color: #fff;
    font-size: 13px;
    font-weight: 800;
    margin-bottom: 10px;
  }
  .step-title { font-size: 16px; font-weight: 700; color: #880e4f; margin-bottom: 10px; }
  .step-card ul { padding-left: 18px; margin-bottom: 12px; font-size: 14px; color: #3a1a28; }
  .step-card ul li { margin-bottom: 6px; }
  .pro-tip {
    background: #fff0f5;
    border-left: 4px solid #e91e8c;
    border-radius: 0 8px 8px 0;
    padding: 14px 16px;
    margin: 12px 0;
    font-size: 14px;
    color: #4a1030;
    line-height: 1.8;
    white-space: pre-wrap;
    font-weight: 700;
  }
  .round-face-tip {
    background: #f3e5f5;
    border-left: 4px solid #ab47bc;
    border-radius: 0 8px 8px 0;
    padding: 14px 16px;
    margin: 12px 0;
    font-size: 14px;
    color: #2e0040;
  }
  .warning-box {
    background: #fff8e1;
    border-left: 4px solid #fb8c00;
    border-radius: 0 8px 8px 0;
    padding: 14px 16px;
    margin: 12px 0;
    font-size: 14px;
    color: #3e2000;
  }
  .email-footer {
    text-align: center;
    padding: 18px 32px 24px;
    border-top: 1px solid #fce4ec;
    font-size: 12px;
    color: #b0789a;
    letter-spacing: 0.5px;
  }
  p { margin: 10px 0; font-size: 14px; }
`;

/** 仅美妆：冷橄榄皮·圆脸，一封邮件（每日化妆课风格） */
export function buildMakeupHtml(makeup, dateStr) {
  const raw = makeup?.raw || '';
  const cleaned = raw.replace(/\*/g, '');
  const block = escapeHtml(cleaned);
  const title = `💄 美妆 · 冷橄榄皮圆脸 · ${dateStr}`;
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <style>${MAKEUP_STYLES}</style>
</head>
<body>
  <div class="card-wrapper">
    <div class="email-header">
      <h1>💄 每日化妆课</h1>
      <div class="subtitle">今日推荐 · 护肤 · 化妆 · 圆脸修容</div>
      <div class="date-badge">${escapeHtml(dateStr)}</div>
    </div>
    <div class="email-body">
      <h2 class="section-title">👐 今日主题：冷橄榄皮 · 圆脸</h2>
      <div class="step-card">
        <div class="step-number">小贴士</div>
        <div class="step-title">今日美妆提示</div>
        <div class="pro-tip">${block || '（暂无内容）'}</div>
      </div>
    </div>
    <div class="email-footer">
      早安 Makeup Learning Agent · 由 Gracie 等 · 8:00 丹佛时间
    </div>
  </div>
</body>
</html>`;
}

/** 仅科研文献：3 篇论文，一封邮件 */
export function buildResearchHtml(research, dateStr) {
  const papers = research?.papers || [];
  const paperCards = papers.map((p) => {
    const title = escapeHtml(p.title || '');
    const authors = escapeHtml(p.authors || '');
    const venue = escapeHtml(p.venue || '');
    const year = (p.year && String(p.year).slice(0, 4)) || '—';
    const citations =
      typeof p.citationCount === 'number' ? `📊 ${p.citationCount} citations` : '';
    const abstractSource = (p.abstract || '').replace(/\*/g, '');
    const abstract = escapeHtml(abstractSource.slice(0, 320));
    const relevanceSource = (p.relevance || '').replace(/\*/g, '');
    const relevance = escapeHtml(relevanceSource);
    const url = p.url || '';
    return `
<div class="paper-card">
  <div class="paper-meta">
    <span class="paper-year">${year}</span>
    <span class="journal-badge">${venue || '期刊'}</span>
    <span class="citation-badge">${citations || ''}</span>
  </div>
  <div class="paper-title">${title}</div>
  <div class="paper-authors">${authors}</div>
  <div class="section-label">📝 Abstract</div>
  <div class="abstract-text">${abstract}${(p.abstract || '').length > 320 ? '…' : ''}</div>
  <div class="section-label">🔗 Relevance to Your Work</div>
  <div class="relevance-text">${relevance}</div>
  <div class="paper-links">${url ? `<a class="paper-link" href="${url}">📄 查看原文</a>` : ''}</div>
</div>`;
  }).join('');
  const body = paperCards || '<p style="color:#666;">今日暂无文献。</p>';
  return wrapEmail(
    `🔬 科研文献 · ${dateStr}`,
    dateStr,
    '由 Gracie Agent 小队 · Semantic Scholar / OpenAlex / Gemini',
    body,
    '早安 Research Digest Agent · 8:00 丹佛时间'
  );
}

/**
 * 学术前沿邮件（格式：分节 + 每篇 Abstract / Relevance / Key Findings / Implications）
 * @param {Object} academicFrontier - { sections: [{ sectionTitle, papers: [{ title, authors, year, venue, citationCount, abstract, relevance, keyFindings[], implications, url }] }] }
 */
export function buildAcademicFrontierHtml(academicFrontier, dateStr) {
  const sections = academicFrontier?.sections || [];
  const dateFormatted = (() => {
    const [y, m, d] = (dateStr || '').split('-');
    return y && m && d ? `${y}年${parseInt(m, 10)}月${parseInt(d, 10)}日` : (dateStr || '');
  })();
  const bodyParts = [];
  for (const sec of sections) {
    const sectionTitle = escapeHtml(sec.sectionTitle || '');
    bodyParts.push(`<div class="digest-section-header">${sectionTitle}</div>`);
    const papers = sec.papers || [];
    for (const p of papers) {
      const title = escapeHtml(p.title || '');
      const authors = escapeHtml(p.authors || '');
      const venue = escapeHtml(p.venue || '');
      const year = (p.year && String(p.year).slice(0, 4)) || '—';
      const citations = typeof p.citationCount === 'number' ? `📊 ${p.citationCount} citations` : '';
      const abstract = escapeHtml((p.abstract || '').slice(0, 400));
      const relevance = escapeHtml(p.relevance_to_MICM || p.relevance || '');
      const methodology = escapeHtml(p.methodology_snapshot || '');
      const gap = escapeHtml(p.gap_identified || '');
      const bibtex = escapeHtml(p.bibtex || '');
      const keyFindings = Array.isArray(p.keyFindings) ? p.keyFindings : [];
      const findingsHtml = keyFindings.length
        ? `<div class="section-label">🔑 Key Findings</div><div class="findings-list">${keyFindings.map((f) => `<div class="finding-item">${escapeHtml(f)}</div>`).join('')}</div>`
        : '';
      const implications = escapeHtml(p.implications || '');
      const implicationsHtml = implications ? `<div class="section-label">💡 Implications</div><div class="implications-text">${implications}</div>` : '';
      const micmBlock = relevance ? `<div class="section-label">🎯 MICM 维度启发</div><div class="relevance-text">${relevance}</div>` : '';
      const methodologyBlock = methodology ? `<div class="section-label">📐 方法概览</div><div class="abstract-text">${methodology}</div>` : '';
      const gapBlock = gap ? `<div class="section-label">⚠️ 研究空白</div><div class="abstract-text">${gap}</div>` : '';
      const bibtexBlock = bibtex ? `<div class="section-label">📚 BibTeX</div><pre class="bibtex-block">${bibtex}</pre>` : '';
      const url = p.url || '';
      bodyParts.push(`
<div class="paper-card">
  <div class="paper-meta">
    <table class="paper-meta-table" cellpadding="0" cellspacing="0"><tr><td>
      <span class="paper-year">${year}</span>
      <span class="journal-badge">${venue || '期刊'}</span>
      <span class="citation-badge">${citations}</span>
    </td></tr></table>
  </div>
  <div class="paper-title">${title}</div>
  <div class="paper-authors">${authors}</div>
  <div class="section-label">📝 Abstract</div>
  <div class="abstract-text">${abstract}${(p.abstract || '').length > 400 ? '…' : ''}</div>
  ${micmBlock}
  ${methodologyBlock}
  ${gapBlock}
  ${findingsHtml}
  ${implicationsHtml}
  ${bibtexBlock}
  <div class="paper-links">${url ? `<a class="paper-link" href="${url}">📄 查看原文</a>` : ''}</div>
</div>`);
    }
  }
  const body = bodyParts.length ? bodyParts.join('') : '<p style="color:#666;">今日暂无学术前沿。</p>';
  return wrapEmail(
    `🔬 学术前沿 · ${dateFormatted}`,
    dateStr,
    'Applied Linguistics · Translanguaging · CDEA · Multilingual Education · 由 Gracie Shen 语义学者',
    body,
    '早安 Research Digest Agent · 8:00 晨间'
  );
}

/** 外刊精读邮件（BBC Future 等）：mast + 文章头 + 摘录 + 词汇卡 + 语法 + AP 修辞表 + 教师笔记 */
const READING_GUIDE_STYLES = `
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
    background: #f5f0e8;
    color: #1c1008;
    line-height: 1.7;
    padding: 20px 12px;
  }
  .outer { max-width: 660px; margin: 0 auto; }
  .mast {
    background: linear-gradient(135deg, #5c2d00 0%, #9a4e10 50%, #c47a1e 100%);
    border-radius: 14px 14px 0 0;
    padding: 32px 36px 22px;
    text-align: center;
    color: #fff;
  }
  .mast-eyebrow { font-size: 10px; letter-spacing: 3.5px; text-transform: uppercase; color: rgba(255,255,255,0.45); margin-bottom: 10px; }
  .mast-title { font-size: 24px; font-weight: 800; margin-bottom: 5px; }
  .mast-sub { font-size: 12px; color: rgba(255,255,255,0.55); margin-bottom: 16px; }
  .mast hr { border: none; border-top: 1px solid rgba(255,255,255,0.15); }
  .card {
    background: #fff;
    border-radius: 0 0 14px 14px;
    overflow: hidden;
    box-shadow: 0 6px 28px rgba(80,40,0,0.13);
  }
  .card-body { padding: 28px 32px 36px; max-width: 660px; }
  .article-header {
    background: #fffaf2;
    border: 1.5px solid #e8d5a8;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 28px;
  }
  .article-meta-row { margin-bottom: 12px; }
  .source-pill {
    display: inline-block;
    background: #c47a1e;
    color: #fff;
    font-size: 10.5px;
    font-weight: 800;
    letter-spacing: 0.4px;
    padding: 4px 12px;
    border-radius: 999px;
    margin-right: 10px;
  }
  .article-date { font-size: 11.5px; color: #888; }
  .article-title {
    font-size: 21px;
    font-weight: 800;
    color: #5c2d00;
    line-height: 1.4;
    margin: 12px 0 14px 0;
    font-family: Georgia, "Times New Roman", serif;
  }
  .btn-read {
    display: inline-block;
    background: #5c2d00;
    color: #fff !important;
    font-size: 12.5px;
    font-weight: 700;
    padding: 7px 20px;
    border-radius: 999px;
    text-decoration: none;
    letter-spacing: 0.2px;
  }
  .sec-head {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #9a4e10;
    border-bottom: 2px solid #e8d5a8;
    padding-bottom: 8px;
    margin: 28px 0 14px 0;
    display: block;
  }
  .sec-head .level-badge {
    font-size: 9px;
    font-weight: 700;
    text-transform: uppercase;
    background: #9a4e10;
    color: #fff;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 8px;
    vertical-align: middle;
  }
  .excerpt-wrap {
    background: #fffaf2;
    border-left: 4px solid #c47a1e;
    border-radius: 0 8px 8px 0;
    padding: 18px 20px;
  }
  .ep {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 15.5px;
    color: #1c1008;
    line-height: 2;
    margin-bottom: 16px;
  }
  .ep:last-child { margin-bottom: 0; }
  mark.vhl {
    background: #ffe08a;
    color: #5c2d00;
    padding: 1px 3px;
    border-radius: 3px;
    font-weight: 700;
    font-style: normal;
  }
  .vc {
    border: 1.5px solid #e8d5a8;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 16px;
    background: #fff;
  }
  .vc:last-of-type { margin-bottom: 0; }
  .vc-num {
    width: 44px;
    min-width: 44px;
    background: #9a4e10;
    color: #fff;
    font-size: 12px;
    font-weight: 800;
    text-align: center;
    padding: 16px 8px;
    vertical-align: top;
  }
  .vc td:last-child { padding: 16px 20px 16px 18px; vertical-align: top; }
  .vc-head { margin-bottom: 10px; }
  .vc-word { font-size: 18px; font-weight: 800; color: #5c2d00; display: inline; margin-right: 8px; }
  .vc-pos { font-size: 11px; color: #9a4e10; font-style: italic; display: inline; }
  .vc-pos-zh { font-size: 12px; color: #7a4a0a; margin-left: 6px; }
  .vc-sent {
    font-size: 13px;
    font-style: italic;
    color: #444;
    line-height: 1.7;
    margin: 0 0 10px 0;
    padding: 10px 12px;
    background: #fffaf2;
    border-left: 3px solid #c47a1e;
    border-radius: 0 6px 6px 0;
  }
  .vc-zh { font-size: 13.5px; color: #1c1008; line-height: 1.65; margin: 0 0 6px 0; font-weight: 500; }
  .vc-tip { font-size: 12px; color: #777; line-height: 1.5; margin: 0; }
  .gs {
    border: 1.5px solid #e8d5a8;
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 12px;
  }
  .gs-label {
    background: #f5e8cc;
    color: #5c2d00;
    font-size: 11.5px;
    font-weight: 800;
    letter-spacing: 0.3px;
    padding: 8px 16px;
    border-bottom: 1px solid #e8d5a8;
  }
  .gs-quote {
    font-size: 13.5px;
    font-style: italic;
    color: #444;
    padding: 10px 16px 8px;
    line-height: 1.7;
    border-bottom: 1px dashed #e8d5a8;
    background: #fffaf2;
  }
  .gs-zh { font-size: 13.5px; color: #1c1008; padding: 9px 16px 6px; line-height: 1.7; }
  .gs-model {
    font-size: 13px;
    color: #9a4e10;
    font-style: italic;
    padding: 6px 16px 12px;
    background: #fffaf2;
    line-height: 1.6;
  }
  .ap-table { border-collapse: collapse; width: 100%; margin: 0; }
  .ap-table tr { border-bottom: 1px solid #e0dbd0; }
  .ap-last { border-bottom: none !important; }
  .ap-label {
    font-size: 12px;
    font-weight: 700;
    color: #5c2d00;
    background: #fdf8ee;
    padding: 14px 16px;
    width: 120px;
    min-width: 120px;
    vertical-align: top;
    white-space: nowrap;
  }
  .ap-val {
    font-size: 14px;
    color: #1c1008;
    line-height: 1.75;
    padding: 14px 16px 14px 0;
    vertical-align: top;
  }
  .teacher-note {
    background: #fffaf2;
    border: 1.5px solid #e8d5a8;
    border-left: 5px solid #c47a1e;
    border-radius: 0 10px 10px 0;
    padding: 16px 20px;
    font-size: 14.5px;
    color: #1c1008;
    line-height: 1.85;
  }
  .scaffold-list {
    background: #fffaf2;
    border-left: 4px solid #c47a1e;
    padding: 16px 20px 16px 20px;
    margin: 0 0 20px 0;
    border-radius: 0 8px 8px 0;
  }
  .scaffold-list ol { margin: 0; padding-left: 20px; }
  .scaffold-list li { margin-bottom: 10px; line-height: 1.7; font-size: 14px; }
  .scaffold-list li:last-child { margin-bottom: 0; }
  .logic-map-item {
    border: 1px solid #e8d5a8;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 14px;
  }
  .logic-map-item:last-child { margin-bottom: 0; }
  .logic-map-quote {
    background: #fffaf2;
    padding: 12px 16px;
    font-style: italic;
    font-size: 14px;
    border-bottom: 1px dashed #e8d5a8;
  }
  .logic-map-breakdown {
    padding: 12px 16px;
    font-size: 14px;
    color: #1c1008;
    line-height: 1.75;
  }
  .footer {
    text-align: center;
    padding: 14px 28px;
    font-size: 11.5px;
    color: #bbb;
    border-top: 1px solid #e8d5a8;
    background: #fffaf2;
    border-radius: 0 0 14px 14px;
  }
`;

/**
 * 外刊精读邮件 2.0（支持 scaffolding_questions, sentence_logic_map, teaching_prompts）
 * @param {Object} readingGuide - { source, title, url, excerptHtml, vocabCards, grammarSpotlight, apRows, teacherNote, readability_level, core_argument, scaffolding_questions, sentence_logic_map, teaching_prompts }
 */
export function buildReadingGuideHtml(readingGuide, dateStr) {
  const dateFormatted = (() => {
    const [y, m, d] = (dateStr || '').split('-');
    return y && m && d ? `${y}年${parseInt(m, 10)}月${parseInt(d, 10)}日` : (dateStr || '');
  })();
  const source = escapeHtml(readingGuide?.source || 'BBC Future');
  const date = escapeHtml(readingGuide?.date || dateFormatted);
  const title = escapeHtml(readingGuide?.title || '');
  const url = readingGuide?.url || '#';
  const excerptHtml = readingGuide?.excerptHtml || '<p class="ep">（暂无摘录）</p>';
  const vocabCards = readingGuide?.vocabCards || [];
  const formatPos = (v) => {
    const pos = (v.pos || '').split('|')[0].trim();
    const posZh = v.pos_zh || (v.pos || '').split('|')[1]?.trim() || '';
    return { pos, posZh };
  };
  const vocabHtml = vocabCards
    .map(
      (v, i) => {
        const { pos, posZh } = formatPos(v);
        const sentHtml = v.sent ? `<div class="vc-sent">${escapeHtml(v.sent)}</div>` : '';
        const zhHtml = v.zh ? `<div class="vc-zh">${escapeHtml(v.zh)}</div>` : '';
        const tipHtml = v.tip ? `<div class="vc-tip">${escapeHtml(v.tip)}</div>` : '';
        return `
<div class="vc">
  <table width="100%" cellpadding="0" cellspacing="0"><tr>
    <td class="vc-num">${String(i + 1).padStart(2, '0')}</td>
    <td>
      <div class="vc-head">
        <span class="vc-word">${escapeHtml(v.word || '')}</span>
        <span class="vc-pos">${escapeHtml(pos)}</span>
        ${posZh ? `<span class="vc-pos-zh">${escapeHtml(posZh)}</span>` : ''}
      </div>
      ${sentHtml}
      ${zhHtml}
      ${tipHtml}
    </td>
  </tr></table>
</div>`;
      }
    )
    .join('');
  const grammarSpotlight = readingGuide?.grammarSpotlight || [];
  const grammarHtml = grammarSpotlight
    .map(
      (g) => `
<div class="gs">
  <div class="gs-label">${escapeHtml(g.label || '')}</div>
  <div class="gs-quote">${escapeHtml(g.quote || '')}</div>
  <div class="gs-zh">${escapeHtml(g.zh || '')}</div>
  <div class="gs-model">${escapeHtml(g.model || '')}</div>
</div>`
    )
    .join('');
  const apRows = readingGuide?.apRows || [];
  const apTableHtml =
    apRows.length > 0
      ? `<table class="ap-table" width="100%" cellpadding="0" cellspacing="0">${apRows
          .map(
            (r, i) =>
              `<tr class="${i === apRows.length - 1 ? 'ap-last' : ''}"><td class="ap-label">${escapeHtml(r.label || '')}</td><td class="ap-val">${escapeHtml(r.val || '')}</td></tr>`
          )
          .join('')}</table>`
      : '';
  const teacherNote = escapeHtml(readingGuide?.teacherNote || '');

  const readability = escapeHtml(readingGuide?.readability_level || '');
  const coreArgument = escapeHtml(readingGuide?.core_argument || '');
  const rhetoricalDevices = escapeHtml(readingGuide?.rhetorical_devices || '');
  const scaffoldingQuestions = readingGuide?.scaffolding_questions || [];
  const scaffoldingHtml =
    scaffoldingQuestions.length > 0
      ? `<div class="sec-head">🎯 Scaffolding Questions（支架式提问）</div><div class="scaffold-list"><ol>${scaffoldingQuestions.map((q) => `<li>${escapeHtml(q)}</li>`).join('')}</ol></div>`
      : '';
  const sentenceLogicMap = readingGuide?.sentence_logic_map || [];
  const logicMapHtml =
    sentenceLogicMap.length > 0
      ? `<div class="sec-head">📊 Sentence Logic Map（长难句逻辑拆解）</div>${sentenceLogicMap
          .map(
            (item) =>
              `<div class="logic-map-item"><div class="logic-map-quote">${escapeHtml(item.sentence || item.quote || '')}</div><div class="logic-map-breakdown">${escapeHtml(item.logic_breakdown || item.zh || '')}</div></div>`
          )
          .join('')}`
      : '';
  const teachingPrompts = escapeHtml(readingGuide?.teaching_prompts || '');
  const teachingPromptsBlock = teachingPrompts
    ? `<div class="sec-head">💬 Teaching Prompts（教师引导语）</div><div class="teacher-note">${teachingPrompts}</div>`
    : '';

  const metaBlock =
    readability || coreArgument || rhetoricalDevices
      ? `<div class="sec-head">📋 阅读难度与核心论点</div><div class="meta-block" style="background:#fffaf2;border:1.5px solid #e8d5a8;border-radius:10px;padding:20px;margin:0 0 24px 0;">${readability ? `<p style="margin:0 0 10px 0;"><strong>Readability:</strong> ${readability}</p>` : ''}${coreArgument ? `<p style="margin:0 0 10px 0;"><strong>核心论点：</strong> ${coreArgument}</p>` : ''}${rhetoricalDevices ? `<p style="margin:0;"><strong>修辞手法：</strong> ${rhetoricalDevices}</p>` : ''}</div>`
      : '';

  return `<!DOCTYPE html>
<html lang="zh">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>外刊精读 · ${dateFormatted}</title>
  <style>${READING_GUIDE_STYLES}</style>
</head>
<body>
<div class="outer">
  <div class="mast">
    <div class="mast-eyebrow">${dateFormatted} · AP English Reading</div>
    <div class="mast-title">📖 外刊精读</div>
    <div class="mast-sub">词汇卡 · 外刊 · 修辞分析 · 由 Gracie Shen</div>
    <hr class="mast-rule">
  </div>
  <div class="card">
    <div class="card-body">
      <div class="article-header">
        <div class="article-meta-row">
          <span class="source-pill">${source}</span>
          <span class="article-date">${date}</span>
        </div>
        <div class="article-title">${title}</div>
        <div><a class="btn-read" href="${url}">📄 Read the full article →</a></div>
      </div>
      ${metaBlock}
      <div class="sec-head">📚 Annotated Excerpt</div>
      <div class="excerpt-wrap">${excerptHtml}</div>
      <div class="sec-head">📖 Vocabulary in Context <span class="level-badge">C1/C2</span></div>
      ${vocabHtml}
      <div class="sec-head">🔍 Grammar Spotlight</div>
      ${grammarHtml}
      <div class="sec-head">📐 Rhetorical Analysis</div>
      ${apTableHtml}
      ${scaffoldingHtml}
      ${logicMapHtml}
      ${teachingPromptsBlock}
      <div class="sec-head">📝 教师笔记</div>
      <div class="teacher-note">${teacherNote}</div>
    </div>
    <div class="footer">由 Reading Agent 生成 © 每日发送 7:30 晨间</div>
  </div>
</div>
</body>
</html>`;
}

/**
 * 合订版（三块一封）：保留以便需要时使用
 */
export function buildDigestHtml(digest, subject) {
  const dateStr = formatDate(digest.generatedAt || new Date().toISOString());
  const englishBlock = escapeHtml(digest.english?.raw || '');
  const makeupBlock = escapeHtml(digest.makeup?.raw || '');
  const papers = digest.research?.papers || [];
  const paperCards = papers.map((p) => {
    const title = escapeHtml(p.title || '');
    const authors = escapeHtml(p.authors || '');
    const venue = escapeHtml(p.venue || '');
    const year = (p.year && String(p.year).slice(0, 4)) || '—';
    const citations = typeof p.citationCount === 'number' ? `📊 ${p.citationCount} citations` : '';
    const abstract = escapeHtml((p.abstract || '').slice(0, 320));
    const relevance = escapeHtml(p.relevance || '');
    const url = p.url || '';
    return `
<div class="paper-card">
  <div class="paper-meta">
    <span class="paper-year">${year}</span>
    <span class="journal-badge">${venue || '期刊'}</span>
    <span class="citation-badge">${citations || ''}</span>
  </div>
  <div class="paper-title">${title}</div>
  <div class="paper-authors">${authors}</div>
  <div class="section-label">📝 Abstract</div>
  <div class="abstract-text">${abstract}${(p.abstract || '').length > 320 ? '…' : ''}</div>
  <div class="section-label">🔗 Relevance to Your Work</div>
  <div class="relevance-text">${relevance}</div>
  <div class="paper-links">${url ? `<a class="paper-link" href="${url}">📄 查看原文</a>` : ''}</div>
</div>`;
  }).join('');
  const body = `
    <div class="paper-card content-card">
      <div class="paper-meta"><span class="journal-badge">English Agent</span></div>
      <div class="paper-title">C1 习语/谚语</div>
      <div class="section-label">今日段落</div>
      <div class="abstract-text">${englishBlock || '（暂无）'}</div>
    </div>
    <div class="paper-card content-card">
      <div class="paper-meta"><span class="journal-badge">Beauty Agent</span></div>
      <div class="paper-title">冷橄榄皮·圆脸</div>
      <div class="section-label">美妆提示</div>
      <div class="abstract-text">${makeupBlock || '（暂无）'}</div>
    </div>
    ${paperCards}`;
  return wrapEmail(subject, dateStr, '由 Gracie Agent 小队 · 合订版', body, '早安 Agent 小队 · 8:00 丹佛时间');
}
