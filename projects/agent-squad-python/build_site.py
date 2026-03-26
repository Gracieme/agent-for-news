#!/usr/bin/env python3
"""
build_site.py — 格雷西学习小屋 静态网站生成器
每次邮件推送后自动调用，把当日内容存档并重建 index.html。
也可单独运行：  python build_site.py
"""

import json
from pathlib import Path

WEBSITE_DIR = Path(__file__).parent.parent.parent / "docs"
DATA_DIR    = WEBSITE_DIR / "data"


# ══════════════════════════════════════════════════════════════════
#  DATA I/O
# ══════════════════════════════════════════════════════════════════

def save_entry(date_key: str, date_cn: str, day_cn: str,
               english_html: str, beauty_html: str, research_html: str,
               news_html: str = ""):
    """Save one day's rendered HTML sections as a JSON file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "date_key": date_key,
        "date_cn":  date_cn,
        "day_cn":   day_cn,
        "english":  english_html,
        "beauty":   beauty_html,
        "research": research_html,
        "news":     news_html,
    }
    out = DATA_DIR / f"{date_key}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)


def load_entries() -> list:
    """Load all entries sorted newest-first."""
    if not DATA_DIR.exists():
        return []
    entries = []
    for f in sorted(DATA_DIR.glob("*.json"), reverse=True):
        try:
            with open(f, encoding="utf-8") as fp:
                entries.append(json.load(fp))
        except Exception:
            pass
    return entries


# ══════════════════════════════════════════════════════════════════
#  HTML TEMPLATE  (uses __ENTRIES_JSON__ as the only placeholder)
# ══════════════════════════════════════════════════════════════════

SITE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>格雷西学习小屋 🏡</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --blue:   #1a73e8;
      --pink:   #c2185b;
      --teal:   #00838f;
      --purple: #667eea;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background: #f0f2f5;
      color: #333;
      min-height: 100vh;
    }

    /* ── Header ── */
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 0 32px;
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 2px 14px rgba(102,126,234,.4);
    }
    .header-brand { display: flex; align-items: baseline; gap: 10px; }
    .header-brand h1 { color: #fff; font-size: 20px; font-weight: 800; letter-spacing: 1px; }
    .header-brand span { color: rgba(255,255,255,.6); font-size: 12px; }
    .header-pill {
      background: rgba(255,255,255,.18);
      border-radius: 20px;
      padding: 5px 16px;
      color: #fff;
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
    }
    .header-pill em { font-style: normal; font-size: 20px; font-weight: 800; }

    /* ── Layout ── */
    .layout {
      display: flex;
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px 16px;
      gap: 20px;
      align-items: flex-start;
    }

    /* ── Sidebar ── */
    .sidebar {
      width: 196px;
      flex-shrink: 0;
      position: sticky;
      top: 76px;
      max-height: calc(100vh - 96px);
      overflow-y: auto;
    }
    .sidebar::-webkit-scrollbar { width: 4px; }
    .sidebar::-webkit-scrollbar-thumb { background: #ddd; border-radius: 4px; }

    .sidebar-label {
      font-size: 11px;
      font-weight: 700;
      color: #999;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      padding: 0 4px;
      margin-bottom: 10px;
    }

    .date-item {
      background: #fff;
      border-radius: 10px;
      padding: 10px 13px;
      margin-bottom: 6px;
      cursor: pointer;
      border: 2px solid transparent;
      transition: all .15s ease;
      box-shadow: 0 1px 3px rgba(0,0,0,.06);
    }
    .date-item:hover { border-color: #c4b7f0; transform: translateX(2px); }
    .date-item.active {
      border-color: var(--purple);
      background: linear-gradient(135deg, #f3f0ff, #faf0ff);
    }
    .date-item .di-en  { font-size: 12px; font-weight: 700; color: #555; }
    .date-item.active .di-en { color: var(--purple); }
    .date-item .di-cn  { font-size: 11px; color: #bbb; margin-top: 1px; }
    .date-item .di-dots { display: flex; gap: 3px; margin-top: 5px; }
    .dot {
      font-size: 11px;
      padding: 1px 5px;
      border-radius: 6px;
      background: #f0f0f0;
      color: #888;
    }

    /* ── Main ── */
    .main { flex: 1; min-width: 0; }

    /* ── Tab bar ── */
    .tab-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
    .tab-btn {
      padding: 9px 20px;
      border-radius: 10px;
      border: 2px solid #e8e8e8;
      background: #fff;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: all .15s;
      color: #888;
      box-shadow: 0 1px 3px rgba(0,0,0,.05);
    }
    .tab-btn:hover { border-color: #bbb; color: #555; }

    .tab-btn[data-tab="english"].active {
      border-color: var(--blue); background: #e8f0fe; color: var(--blue);
      box-shadow: 0 2px 10px rgba(26,115,232,.18);
    }
    .tab-btn[data-tab="beauty"].active {
      border-color: var(--pink); background: #fce4ec; color: var(--pink);
      box-shadow: 0 2px 10px rgba(194,24,91,.18);
    }
    .tab-btn[data-tab="research"].active {
      border-color: var(--teal); background: #e0f7fa; color: var(--teal);
      box-shadow: 0 2px 10px rgba(0,131,143,.18);
    }
    .tab-btn[data-tab="news"].active {
      border-color: #e65100; background: #fff3e0; color: #e65100;
      box-shadow: 0 2px 10px rgba(230,81,0,.18);
    }

    /* ── Content panel ── */
    .content-panel {
      background: #fff;
      border-radius: 14px;
      padding: 28px 30px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06);
      min-height: 420px;
    }

    /* ── States ── */
    .center-msg {
      text-align: center;
      padding: 80px 20px;
      color: #bbb;
      font-size: 15px;
      line-height: 1.9;
    }
    .center-msg .big { font-size: 52px; margin-bottom: 16px; }

    @media (max-width: 680px) {
      .layout { flex-direction: column; padding: 12px; }
      .sidebar { width: 100%; position: static; max-height: 180px; }
      .header-pill { display: none; }
      .header-brand h1 { font-size: 16px; }
    }
  </style>
</head>
<body>

<header class="header">
  <div class="header-brand">
    <h1>🏡 格雷西学习小屋</h1>
    <span>Gracie's Learning Hub</span>
  </div>
  <div class="header-pill"><em id="total-days">0</em> days of learning</div>
</header>

<div class="layout">

  <nav class="sidebar">
    <div class="sidebar-label">📅 Archive</div>
    <div id="date-list"></div>
  </nav>

  <main class="main">
    <div class="tab-bar" id="tab-bar">
      <button class="tab-btn active" data-tab="english">📚 英语表达</button>
      <button class="tab-btn"        data-tab="beauty">💄 美妆</button>
      <button class="tab-btn"        data-tab="research">🔬 科研文献</button>
      <button class="tab-btn"        data-tab="news">📰 全球新闻</button>
    </div>
    <div class="content-panel" id="content-panel">
      <div class="center-msg">
        <div class="big">🏡</div>
        还没有学习记录哦～<br>
        每次发送邮件后内容会自动同步到这里！
      </div>
    </div>
  </main>

</div>

<script>
const ENTRIES = __ENTRIES_JSON__;

let selIdx = ENTRIES.length > 0 ? 0 : -1;
let selTab = 'english';

document.getElementById('total-days').textContent = ENTRIES.length;

/* ── Format date_key "2026-03-09" → "Mon, Mar 9" ── */
function fmtUS(dateKey) {
  const d = new Date(dateKey + 'T12:00:00');
  return d.toLocaleDateString('en-US', { weekday:'short', month:'short', day:'numeric' });
}

/* ── Sidebar ── */
function renderSidebar() {
  const list = document.getElementById('date-list');
  if (!ENTRIES.length) {
    list.innerHTML = '<div style="color:#ccc;font-size:12px;padding:6px">No entries yet</div>';
    return;
  }
  list.innerHTML = ENTRIES.map((e, i) => `
    <div class="date-item ${i === selIdx ? 'active' : ''}" onclick="selectEntry(${i})">
      <div class="di-en">${fmtUS(e.date_key)}</div>
      <div class="di-cn">${e.day_cn}</div>
      <div class="di-dots">
        ${e.english  ? '<span class="dot">📚</span>' : ''}
        ${e.beauty   ? '<span class="dot">💄</span>' : ''}
        ${e.research ? '<span class="dot">🔬</span>' : ''}
        ${e.news     ? '<span class="dot">📰</span>' : ''}
      </div>
    </div>
  `).join('');
}

/* ── Content ── */
function renderContent() {
  const panel = document.getElementById('content-panel');
  if (selIdx < 0) {
    panel.innerHTML = ENTRIES.length
      ? '<div class="center-msg">← Pick a date from the left</div>'
      : '<div class="center-msg"><div class="big">🏡</div>No entries yet.<br>Run the daily email script to get started!</div>';
    return;
  }
  const html = ENTRIES[selIdx][selTab];
  panel.innerHTML = html
    || '<div class="center-msg" style="color:#ccc">No content for this section</div>';
}

function selectEntry(i) {
  selIdx = i;
  renderSidebar();
  renderContent();
}

/* ── Tab clicks ── */
document.getElementById('tab-bar').addEventListener('click', e => {
  const btn = e.target.closest('.tab-btn');
  if (!btn) return;
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selTab = btn.dataset.tab;
  renderContent();
});

/* ── Init ── */
renderSidebar();
renderContent();
</script>

</body>
</html>"""


# ══════════════════════════════════════════════════════════════════
#  BUILDER
# ══════════════════════════════════════════════════════════════════

def rebuild() -> tuple[Path, int]:
    """Read all entries and regenerate website/index.html."""
    entries      = load_entries()
    entries_json = json.dumps(entries, ensure_ascii=False)
    html         = SITE_TEMPLATE.replace("__ENTRIES_JSON__", entries_json)
    WEBSITE_DIR.mkdir(parents=True, exist_ok=True)
    out = WEBSITE_DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    return out, len(entries)


if __name__ == "__main__":
    out, count = rebuild()
    print(f"✅  Site rebuilt → {out}  ({count} entries)")
