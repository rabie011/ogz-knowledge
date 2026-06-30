#!/usr/bin/env python3
"""OGZ Live Feed — one browser tab at http://localhost:4141 (SSE, plain summaries)."""
from __future__ import annotations

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EVENTS = ROOT / "data/live_feed/events.jsonl"
PORT = 4141

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>OGZ Live</title>
<style>
  :root { --bg:#0d1117; --card:#161b22; --text:#e6edf3; --muted:#8b949e;
    --cursor:#58a6ff; --executor:#3fb950; --orchestra:#d2a8ff; --brain:#f0883e;
    --digest:#ffa657; --deepseek:#a371f7; --memory:#56d4dd; --summary:#ffa657; --error:#f85149; }
  * { box-sizing: border-box; }
  body { margin:0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background:var(--bg); color:var(--text); min-height:100vh; }
  header { padding:16px 20px; border-bottom:1px solid #30363d; position:sticky; top:0;
    background:rgba(13,17,23,.95); backdrop-filter:blur(8px); z-index:10; }
  h1 { margin:0 0 6px; font-size:1.25rem; font-weight:600; }
  .sub { color:var(--muted); font-size:.85rem; }
  .digest { margin-top:12px; padding:12px 14px; background:#1c2128; border-radius:8px;
    border-left:3px solid var(--summary); font-size:.95rem; line-height:1.45; }
  #feed { padding:12px 16px 40px; max-width:900px; margin:0 auto; }
  .evt { display:flex; gap:10px; padding:10px 12px; margin-bottom:8px; background:var(--card);
    border-radius:8px; border:1px solid #30363d; animation: fadeIn .3s ease; }
  @keyframes fadeIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; } }
  .evt.summary { border-color: var(--summary); background:#1c1912; }
  .evt.error { border-color: var(--error); }
  .time { color:var(--muted); font-size:.75rem; min-width:52px; padding-top:2px; }
  .badge { font-size:.7rem; font-weight:600; text-transform:uppercase; padding:2px 6px;
    border-radius:4px; height:fit-content; }
  .badge.cursor { background:#1f3a5f; color:var(--cursor); }
  .badge.executor { background:#1a3d2a; color:var(--executor); }
  .badge.orchestra { background:#2d1f4e; color:var(--orchestra); }
  .badge.brain { background:#3d2814; color:var(--brain); }
  .badge.digest { background:#3d2a14; color:var(--digest); }
  .badge.deepseek { background:#2d1f4e; color:var(--deepseek); }
  .badge.memory { background:#1a3d3d; color:var(--memory); }
  .badge.live-feed { background:#1a2d3d; color:#79c0ff; }
  .badge.mac { background:#1a2d3d; color:#79c0ff; }
  .msg { flex:1; line-height:1.45; font-size:.92rem; }
  .status { color:var(--executor); }
  .status.off { color:var(--error); }
</style>
</head>
<body>
<header>
  <h1>OGZ Live</h1>
  <div class="sub">Mac debug only — use Cursor on mobile. Summaries from executor, digest, brain.</div>
  <div class="sub">Connection: <span id="conn" class="status off">connecting…</span></div>
  <div id="digest" class="digest" style="display:none"></div>
</header>
<div id="feed"></div>
<script>
const feed = document.getElementById('feed');
const digest = document.getElementById('digest');
const conn = document.getElementById('conn');
const seen = new Set();

function fmtTime(ts) {
  try { return new Date(ts).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}); }
  catch { return ''; }
}

function addEvent(e, prepend) {
  const key = e.ts + '|' + e.source + '|' + e.message;
  if (seen.has(key)) return;
  seen.add(key);
  if (e.type === 'summary' || e.type === 'digest') {
    digest.style.display = 'block';
    digest.textContent = e.message;
  }
  const div = document.createElement('div');
  div.className = 'evt' + (e.type === 'summary' || e.type === 'digest' ? ' summary' : '') +
    (e.level === 'error' ? ' error' : '');
  const src = (e.source || 'system').toLowerCase();
  div.innerHTML = '<span class="time">' + fmtTime(e.ts) + '</span>' +
    '<span class="badge ' + src + '">' + (e.source || 'system') + '</span>' +
    '<span class="msg">' + escapeHtml(e.message) + '</span>';
  if (prepend) feed.prepend(div); else feed.appendChild(div);
}

function escapeHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

fetch('/api/recent').then(r => r.json()).then(events => {
  events.forEach(e => addEvent(e, false));
  feed.scrollTop = feed.scrollHeight;
});

const es = new EventSource('/api/stream');
es.onopen = () => { conn.textContent = 'live'; conn.classList.remove('off'); };
es.onerror = () => { conn.textContent = 'reconnecting…'; conn.classList.add('off'); };
es.onmessage = (ev) => {
  try { addEvent(JSON.parse(ev.data), true); } catch {}
};
</script>
</body>
</html>
"""


def _read_from(offset: int) -> tuple[list[dict], int]:
    if not EVENTS.exists():
        return [], 0
    data = EVENTS.read_bytes()
    if offset > len(data):
        offset = 0
    chunk = data[offset:]
    new_offset = len(data)
    events: list[dict] = []
    for line in chunk.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events, new_offset


class Handler(BaseHTTPRequestHandler):
    server_version = "OGZLiveFeed/1.0"

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/recent":
            sys.path.insert(0, str(ROOT / "scripts"))
            from live_feed import read_recent

            body = json.dumps(read_recent(150), ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            offset = EVENTS.stat().st_size if EVENTS.exists() else 0
            try:
                while True:
                    events, offset = _read_from(offset)
                    for ev in events:
                        payload = f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"
                        self.wfile.write(payload.encode("utf-8"))
                        self.wfile.flush()
                    time.sleep(1)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

        self.send_response(404)
        self.end_headers()


def main() -> int:
    EVENTS.parent.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"OGZ Live Feed at http://127.0.0.1:{PORT}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
