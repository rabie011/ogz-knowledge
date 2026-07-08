#!/usr/bin/env python3
"""THE TEAM PORTAL (June 12 — Mohamed's order: the human-truth layer).
Was the single-judge mini-portal; now multi-judge by ROLE. Each teammate opens
a key-scoped link and sees ONLY their lane's cards (Amira → strategy). Three
actions per card: 💬 comment · ✏️ fix (the correction itself) · ✅/❌ + rating.
Their input is HUMAN TRUTH — captured, attributed, surfaced to Mohamed. The fix
is recorded as a proposal, never silently mutating organs (One Write Path).
Mohamed's key = god view: every lane + the team's input aggregated. Taste stays his.

Still deliberately tiny: ONLY the portal. No brain endpoints, no client raw data.
Run: python3 -m uvicorn api.portal_mini:app --port 4199 --host 127.0.0.1
"""
import hashlib
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

REPO = Path(__file__).parent.parent
DATA_ROOT = Path(os.environ["OGZ_BASE"]) if os.environ.get("OGZ_BASE") else REPO  # test sandbox
STATIC = Path(__file__).parent / "static"
ANSWERS = DATA_ROOT / "data" / "mohamed_answers.jsonl"
UNVERIFIED = DATA_ROOT / "data" / "unverified_answers.jsonl"
QUEUE = DATA_ROOT / "data" / "decision_queue.json"
TEAM_F = DATA_ROOT / "data" / "portal_team.json"
KEYS_F = DATA_ROOT / "data" / "portal_keys.json"
LANEMAP_F = DATA_ROOT / "data" / "portal_lane_map.json"
SCORECARDS_F = DATA_ROOT / "data" / "scorecards.json"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=600)   # 40KB JSON → ~8KB over the tunnel
# serve api/static/ (render images at /static/renders_v37/<f> + the html) so a COMPLETE-POST judge
# card can show the actual photo — the portal had no static mount, so image_url paths 404'd (June 21).
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


def _team() -> dict:
    return json.loads(TEAM_F.read_text()) if TEAM_F.exists() else {"key": "", "members": []}


def _keys() -> dict:
    return json.loads(KEYS_F.read_text()) if KEYS_F.exists() else {"legacy_write": True, "keys": []}


def _lane_map() -> dict:
    return json.loads(LANEMAP_F.read_text()) if LANEMAP_F.exists() else {}


def _resolve_judge(k: str):
    """IDENTITY IS SERVER-SIDE (June 12 feedback system — the line-106 fix).
    Returns (judge, auth):
      per-judge key  → (its judge, 'key')     — body can never override
      legacy shared  → (None, 'shared')        — judge from the in-app picker,
                       honest transition until Mohamed switches links; once
                       legacy_write:false, shared POSTs quarantine
      anything else  → (None, 'none')          — quarantine, NEVER mohamed"""
    if not k:
        return None, "none"
    kh = hashlib.sha256(k.encode()).hexdigest()
    for e in _keys().get("keys", []):
        if e.get("key_hash") == kh and not e.get("revoked"):
            return e["judge"], "key"
    if k == _team().get("key"):
        return None, "shared"
    return None, "none"


def _ok(k: str) -> bool:
    """READ access: any per-judge key or the shared key opens the page."""
    judge, auth = _resolve_judge(k)
    return auth in ("key", "shared")


def _card_lane(card: dict, lm: dict) -> str:
    return lm.get(card.get("tag", ""), card.get("lane", "creative"))


@app.get("/")
def root():
    return {"ogz": "team portal", "hint": "/approvals?k=<your key>"}


@app.get("/approvals")
def page(request: Request, k: str = ""):
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    # private,no-cache + ETag: second open through the tunnel = 304 (~300B, not 45KB)
    f = STATIC / "approvals.html"
    st = f.stat()
    etag = f'W/"{int(st.st_mtime)}-{st.st_size}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return FileResponse(f, headers={"Cache-Control": "private, no-cache", "ETag": etag})


@app.get("/dashboard")
def dashboard(request: Request, k: str = ""):
    """THE FEEDBACK DASHBOARD (July 2 — Mohamed's order: the one place he lives in).
    Same key auth, same items API, same answer write path as /approvals — this route
    only serves the richer surface (full decks, full posts, inline element comments)."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = STATIC / "dashboard.html"
    st = f.stat()
    etag = f'W/"{int(st.st_mtime)}-{st.st_size}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return FileResponse(f, headers={"Cache-Control": "private, no-cache", "ETag": etag})


OGZ_ROOT = Path.home() / "OGZ-System"
_ACTIVITY_SOURCES = [OGZ_ROOT / "journal/journal.jsonl", OGZ_ROOT / "journal/runs.log"]


@app.get("/plan")
def agents_plan(k: str = ""):
    """AGENTS-PLAN.pdf for Mohamed's remote read (July 2) — same key gate as everything."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = OGZ_ROOT / "AGENTS-PLAN.pdf"
    if not f.exists():
        return JSONResponse({"error": "plan not found"}, status_code=404)
    return FileResponse(f, media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/plan-v2")
def agents_plan_v2(k: str = ""):
    """AGENTS-PLAN-v2.pdf — the corrected v2 for Mohamed's remote read (July 3). Same key
    gate as /plan; v1 stays served at /plan (append-only, nothing overwritten)."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = OGZ_ROOT / "AGENTS-PLAN-v2.pdf"
    if not f.exists():
        return JSONResponse({"error": "plan v2 not found"}, status_code=404)
    return FileResponse(f, media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/state")
def state_of_everything(k: str = ""):
    """STATE-OF-EVERYTHING.pdf — the deep-understanding pass across all know-how, data,
    systems, clients, and history (July 3). Same key gate as /plan. Surfaced before the plan."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = OGZ_ROOT / "STATE-OF-EVERYTHING.pdf"
    if not f.exists():
        return JSONResponse({"error": "state doc not found"}, status_code=404)
    return FileResponse(f, media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/best-plan")
def best_stack_plan(k: str = ""):
    """OGZ-BEST-STACK-PLAN.pdf — the best-in-class multi-tool architecture plan
    (money no object, data anywhere; July 5). Same key gate as /plan."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = OGZ_ROOT / "OGZ-BEST-STACK-PLAN.pdf"
    if not f.exists():
        return JSONResponse({"error": "best-plan not found"}, status_code=404)
    return FileResponse(f, media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/charter")
def ogz_charter(k: str = ""):
    """OGZ-CHARTER.pdf — the persistent company context every agent loads first (July 5).
    Same key gate as /plan."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = OGZ_ROOT / "OGZ-CHARTER.pdf"
    if not f.exists():
        return JSONResponse({"error": "charter not found"}, status_code=404)
    return FileResponse(f, media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/day-report")
def day_report(k: str = ""):
    """DAY-REPORT-2026-07-02.pdf for Mohamed's remote read (July 3) — same key gate as /plan."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = OGZ_ROOT / "DAY-REPORT-2026-07-02.pdf"
    if not f.exists():
        return JSONResponse({"error": "day report not found"}, status_code=404)
    return FileResponse(f, media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/jadarat")
def jadarat_deck(k: str = ""):
    """The HRDF/Jadarat proposal DECK (rendered through the OGZ design system) for Mohamed's
    phone — visual-first judging (July 5). Same key gate as /plan. Serves the NEWEST amira
    render so a re-polish auto-updates this link; falls back to any hrdf-jadarat deck."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    cands = sorted(JOBS_ROOT.glob("*hrdf-jadarat-amira*/DECK-CLOUD-DESIGN.pdf"),
                   key=lambda p: p.stat().st_mtime, reverse=True) or \
            sorted(JOBS_ROOT.glob("*hrdf-jadarat*/DECK*.pdf"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        return JSONResponse({"error": "jadarat deck not found"}, status_code=404)
    return FileResponse(cands[0], media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/jadarat-design")
def jadarat_design_deck(k: str = ""):
    """The CLOUD-DESIGNED Jadarat deck — rendered by the ogz-deck-design GitHub loop (deck_design_pro,
    the divergent editorial system), driven by the proposal agent's design handoff (2026-07-05). The
    consumer for the agent→push→Action→pull round-trip (Rule #6: this route is the deck's reader).
    Serves the newest cloud-designed render so a re-push auto-updates the link."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    cands = sorted(JOBS_ROOT.glob("*hrdf-jadarat-design*/DECK-CLOUD-DESIGN.pdf"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        return JSONResponse({"error": "cloud-designed jadarat deck not found"}, status_code=404)
    return FileResponse(cands[0], media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/jadarat-full")
def jadarat_full(k: str = ""):
    """The FULL Jadarat technical-envelope SUBMISSION file (14-page A4 bid document, بند 44)
    for Mohamed's phone (July 5). Same key gate as /plan and /jadarat. Serves the newest
    full-submission PDF so a rebuild auto-updates this link."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    cands = sorted(JOBS_ROOT.glob("*hrdf-jadarat-full-submission/JADARAT-FULL-SUBMISSION.pdf"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        return JSONResponse({"error": "jadarat full submission not found"}, status_code=404)
    return FileResponse(cands[0], media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/jadarat-design")
def jadarat_design(k: str = ""):
    """The DESIGN-SYSTEM-OWNED Jadarat deck (deck_design_pro — the fuller redesign that owns
    composition/hierarchy/imagery), separate from the base /jadarat. For Mohamed's phone
    (July 5). Same key gate as /jadarat. Serves the newest design-owned render so a re-design
    auto-updates this link."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    cands = sorted(JOBS_ROOT.glob("*jadarat-design-owned/DECK-DESIGN-OWNED.pdf"),
                   key=lambda p: p.stat().st_mtime, reverse=True) or \
            sorted(JOBS_ROOT.glob("*jadarat-design*/DECK-DESIGN*.pdf"),
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        return JSONResponse({"error": "jadarat design deck not found"}, status_code=404)
    return FileResponse(cands[0], media_type="application/pdf",
                        headers={"Cache-Control": "private, no-cache"})


def _epoch(ts) -> float:
    """All activity sources are ISO-ish strings (some naive, some +0300) — normalize to
    epoch BEFORE sorting (DeepSeek consult activity-panel: string-sort across formats lies)."""
    try:
        dt = datetime.fromisoformat(str(ts).strip())
        if dt.tzinfo is None:
            dt = dt.astimezone()          # naive = this machine's local time
        return dt.timestamp()
    except Exception:
        return 0.0


@app.get("/api/dashboard/activity")
def activity(request: Request, k: str = ""):
    """EVERY SESSION'S ACTIVITY IN ONE VIEW (July 2, Mohamed-approved) — read-only merge of
    the EXISTING ledgers (no new tracking system): the cross-project journal (file bursts,
    collapsed per run+event+top-dir), runs.log (session-level sync/scan story), the minds'
    learning ledger, and portal verdicts. Newest first, capped, epoch-sorted."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    # ETag over the mtimes of every source — unchanged ledgers → 304, zero payload
    lmon = sorted((OGZ_ROOT / "journal/learnings").glob("*.jsonl"))[-2:] \
        if (OGZ_ROOT / "journal/learnings").exists() else []
    srcs = [p for p in _ACTIVITY_SOURCES + lmon + [ANSWERS] if p.exists()]
    etag = 'W/"' + "-".join(str(int(p.stat().st_mtime)) for p in srcs) + '"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    rows = []

    def _tail_jsonl(path: Path, n: int):
        if not path.exists():
            return []
        out = []
        for ln in path.read_bytes().splitlines()[-n:]:
            try:
                out.append(json.loads(ln.decode("utf-8", errors="replace")))
            except Exception:
                continue
        return out

    # 1 — file changes: journal.jsonl bursts collapsed per (run ts, event, top-level dir)
    groups = {}
    for e in _tail_jsonl(OGZ_ROOT / "journal/journal.jsonl", 1200):
        if e.get("event") == "baseline":
            continue
        top = str(e.get("path", "")).split("/", 1)[0]
        key = (e.get("ts"), e.get("event"), top)
        g = groups.setdefault(key, {"n": 0, "paths": []})
        g["n"] += 1
        if len(g["paths"]) < 3:
            g["paths"].append(str(e.get("path", "")).rsplit("/", 1)[-1])
    _EV_AR = {"added": "ملف جديد", "modified": "تعديل", "vanished": "اختفى"}
    for (ts, ev, top), g in groups.items():
        label = _EV_AR.get(ev, ev)
        rows.append({"ts": _epoch(ts), "kind": "files-" + str(ev), "who": top or "OGZ-System",
                     "text": (f"{g['n']} × {label} in {top}/" if g["n"] > 1 else f"{label}: {g['paths'][0]}"),
                     "detail": " · ".join(g["paths"]) if g["n"] > 1 else ""})

    # 2 — session story: runs.log ("<iso ts> | <tool> | <message>") — the commit-level narrative
    runs_f = OGZ_ROOT / "journal/runs.log"
    if runs_f.exists():
        for ln in runs_f.read_bytes().splitlines()[-80:]:
            parts = ln.decode("utf-8", errors="replace").split(" | ", 2)
            if len(parts) == 3:
                rows.append({"ts": _epoch(parts[0]), "kind": "session", "who": parts[1],
                             "text": parts[2][:220], "detail": ""})

    # 3 — agent learnings/corrections/verdicts (month-sharded ledger; who = the mind)
    for shard in lmon:
        for e in _tail_jsonl(shard, 300):
            rows.append({"ts": _epoch(e.get("ts")), "kind": "learning-" + str(e.get("kind", "learned")),
                         "who": "mind:" + str(e.get("mind", "?")), "text": str(e.get("text", ""))[:240],
                         "detail": str(e.get("source", ""))[:120]})

    # 4 — human verdicts from this portal's own ledger (who = the judge)
    for e in _tail_jsonl(ANSWERS, 120):
        if e.get("judge") in ("", "unverified", None):
            continue
        npins = len(e.get("comments") or [])
        txt = f"{e.get('answer','?')} — {e.get('item_id','')}"
        if e.get("rating"):
            txt += f" · ★{e['rating']}"
        if npins:
            txt += f" · {npins} 📌"
        rows.append({"ts": _epoch(e.get("ts")), "kind": "verdict", "who": str(e.get("judge")),
                     "text": txt[:220], "detail": str(e.get("note") or e.get("fix") or "")[:140]})

    rows = [r for r in rows if r["ts"] > 0]
    rows.sort(key=lambda r: r["ts"], reverse=True)
    return JSONResponse({"rows": rows[:120]},
                        headers={"ETag": etag, "Cache-Control": "private, no-cache"})


JOBS_ROOT = OGZ_ROOT / "studio" / "jobs"
SOFFICE = "/opt/homebrew/bin/soffice"


def _deck_pdf_for(stem: str):
    """Newest DECK*.pdf in the card's job dir; falls back to converting the newest
    DECK*.pptx via soffice (write-once cache next to it — never deleted, never redone).
    Returns (pdf_path|None, pptx_to_convert|None). Path-guarded: stem resolved under jobs/."""
    if not stem or any(c in stem for c in "/\\\x00") or ".." in stem:
        return None, None
    d = (JOBS_ROOT / stem).resolve()
    if not (str(d).startswith(str(JOBS_ROOT.resolve()) + "/") and d.is_dir()):
        return None, None
    pdfs = sorted(d.glob("DECK*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if pdfs:
        return pdfs[0], None
    ppts = sorted(d.glob("DECK*.pptx"), key=lambda p: p.stat().st_mtime, reverse=True)
    return None, (ppts[0] if ppts else None)


@app.get("/api/dashboard/deck")
async def deck(item: str = "", k: str = "", meta: int = 0, dl: int = 0):
    """MOHAMED'S VISUAL-FIRST RULE (July 2): the rendered deck IS the card. Serves the
    job's DECK pdf; a pptx-only job is converted ONCE at first view (flock + re-check —
    DeepSeek consult deck-embed-20260702: no double-convert race, async so the worker
    never blocks the event loop). ?meta=1 → availability JSON; ?dl=1 → download headers."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    stem = item[len("studio_"):] if item.startswith("studio_") else item
    pdf, pptx = _deck_pdf_for(stem)
    if pdf is None and pptx is not None:
        import asyncio
        import fcntl as _f
        lock = open(pptx.parent / ".deck_convert.lock", "w")
        try:
            _f.flock(lock, _f.LOCK_EX)
            npdf, _ = _deck_pdf_for(stem)          # double-check after the lock
            if npdf is None:
                proc = await asyncio.create_subprocess_exec(
                    SOFFICE, "--headless", "--convert-to", "pdf",
                    "--outdir", str(pptx.parent), str(pptx),
                    stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                try:
                    await asyncio.wait_for(proc.wait(), timeout=120)
                except asyncio.TimeoutError:
                    proc.kill()
            pdf, _ = _deck_pdf_for(stem)
        finally:
            _f.flock(lock, _f.LOCK_UN)
            lock.close()
    if meta:
        return {"ok": pdf is not None, "name": pdf.name if pdf else None,
                "convertible": pptx is not None}
    if pdf is None:
        return JSONResponse({"ok": False, "error": "no deck"}, status_code=404)
    headers = {"Cache-Control": "private, no-cache"}
    if dl:
        headers["Content-Disposition"] = f'attachment; filename="{stem}-{pdf.name}"'
    return FileResponse(pdf, media_type="application/pdf", headers=headers)


@app.get("/control")
def control_center(request: Request, k: str = ""):
    """THE FULL-SYSTEM CONTROL CENTER (July 4 — Mohamed's order: 'see everything happening
    across all aspects, live, from my phone'). Extends the portal — same key gate, same
    tunnel, same /static. Read-only views (agents, live pipeline, review, know-how, budget,
    health, activity) all read the EXISTING ledgers; nothing new-tracks, nothing writes here
    except the review flow which reuses /api/approvals/answer (one write path)."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    f = STATIC / "control.html"
    st = f.stat()
    etag = f'W/"{int(st.st_mtime)}-{st.st_size}"'
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers={"ETag": etag})
    return FileResponse(f, headers={"Cache-Control": "private, no-cache", "ETag": etag})


# =====================================================================================
# SPEC-001 — /brain : PLATFORM v0 (NOW + HEALTH cards, truth-only)
# Every number is read at REQUEST TIME from disk (queue/ + ledgers/ + NEEDS-MOHAMED.md).
# ZERO hardcoded data, ZERO model prose. Missing source -> "no data yet", never fake.
# Open route (no key gate) so the two hands' live state is glanceable from the phone,
# same as "/" returns 200. Only reads operational spine files — no client data.
# =====================================================================================

# Spine paths the /brain cards read from. Defaults to the real OGZ-System; tests point
# OGZ_JAIL_ROOT at a tmp sandbox so they never touch the live queue/ledgers.
def _brain_paths():
    """Resolve spine paths at REQUEST time (honors OGZ_JAIL_ROOT for tests)."""
    root = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT
    return (root / "queue" / "claimed", root / "ledgers" / "health.jsonl",
            root / "ledgers" / "spend.jsonl", root / "NEEDS-MOHAMED.md")


def _brain_delta_path() -> Path:
    """The SPEC-008 arena delta ledger (reader = the DELTA card, Consumer Law #6)."""
    root = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT
    return root / "ledgers" / "delta.jsonl"


def _brain_age(seconds: float) -> str:
    """Compact human age from a delta in seconds."""
    s = int(max(0, seconds))
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h"
    return f"{s // 86400}d"


def _brain_now() -> list[dict]:
    """One row per claimed task file under queue/claimed/<worker>/. Truth from disk."""
    rows = []
    claimed, _, _, _ = _brain_paths()
    if not claimed.exists():
        return rows
    now = datetime.now().timestamp()
    for worker_dir in sorted(claimed.iterdir()):
        if not worker_dir.is_dir():
            continue
        worker = worker_dir.name
        for tf in sorted(worker_dir.glob("task_*.json")):
            try:
                task = json.loads(tf.read_text(encoding="utf-8"))
            except Exception:
                task = {}
            try:
                mtime = tf.stat().st_mtime
            except OSError:
                mtime = now
            budget = task.get("budget") or {}
            rows.append({
                "worker": worker,
                "id": task.get("id", tf.stem.replace("task_", "")),
                "client": task.get("client", "?"),
                "task_type": task.get("task_type", "?"),
                "lane": task.get("lane", worker),
                "age": _brain_age(now - mtime),
                "max_calls": budget.get("max_calls"),
                "max_usd": budget.get("max_usd"),
                "max_minutes": budget.get("max_minutes"),
            })
    return rows


def _brain_health_lines(limit: int = 20) -> list[dict]:
    """Last `limit` lines of ledgers/health.jsonl, newest last, each with a computed age."""
    out = []
    _, health_f, _, _ = _brain_paths()
    if not health_f.exists():
        return out
    try:
        raw = [l for l in health_f.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return out
    now_utc = datetime.utcnow().timestamp()
    for l in raw[-limit:]:
        try:
            rec = json.loads(l)
        except Exception:
            continue
        ts = rec.get("ts", "")
        age = ""
        try:
            # health ts is UTC ("...Z"); compare as UTC epoch deltas
            epoch = (datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
                     - datetime(1970, 1, 1)).total_seconds()
            age = _brain_age(now_utc - epoch)
        except Exception:
            age = ""
        out.append({"check": rec.get("check", "?"), "status": rec.get("status", "?"),
                    "ts": ts, "age": age})
    return out


def _brain_spend_today() -> dict:
    """Sum today's spend.jsonl by worker: calls, usd. Today = UTC date match on ts."""
    summary = {"total_calls": 0, "total_usd": 0.0, "by_worker": {}, "has_data": False}
    _, _, spend_f, _ = _brain_paths()
    if not spend_f.exists():
        return summary
    today = datetime.utcnow().strftime("%Y-%m-%d")
    try:
        lines = [l for l in spend_f.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return summary
    for l in lines:
        try:
            rec = json.loads(l)
        except Exception:
            continue
        if not str(rec.get("ts", "")).startswith(today):
            continue
        summary["has_data"] = True
        w = rec.get("worker", "?")
        calls = rec.get("calls", 0) or 0
        usd = rec.get("usd", 0) or 0
        bw = summary["by_worker"].setdefault(w, {"calls": 0, "usd": 0.0})
        bw["calls"] += calls
        bw["usd"] += usd
        summary["total_calls"] += calls
        summary["total_usd"] += usd
    return summary


def _brain_needs_open() -> int:
    """Count OPEN NEEDS-MOHAMED ids that have no matching RESOLVED (mirrors needs_mohamed.py)."""
    _, _, _, needs_f = _brain_paths()
    if not needs_f.exists():
        return 0
    import re as _re
    opened, resolved = set(), set()
    try:
        for line in needs_f.read_text(encoding="utf-8").splitlines():
            m = _re.match(r"- \[(OPEN|RESOLVED) ([0-9a-f]{8})\]", line)
            if not m:
                continue
            if m.group(1) == "OPEN":
                opened.add(m.group(2))
            else:
                resolved.add(m.group(2))
    except Exception:
        return 0
    return len(opened - resolved)


def _brain_arena_root() -> Path:
    root = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT
    return root / "arena"


def _brain_compiled_path() -> Path:
    root = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT
    return root / "ledgers" / "compiled.jsonl"


def _brain_rabie_verdicts_path() -> Path:
    """rabie_verdicts_v2.jsonl lives under this app's own data/ (DATA_ROOT), NOT the OGZ_ROOT
    spine — honors OGZ_BASE for tests, same as ANSWERS/UNVERIFIED/QUEUE above."""
    return DATA_ROOT / "data" / "rabie_verdicts_v2.jsonl"


def _brain_misses_from_arena(limit: int) -> list[dict]:
    """Per-round gate kills, read at REQUEST time from each arena/<brief_id>/.state.json.
    gate_fail is keyed by SLOT (A/B); 'slots' maps slot->lane (claude/codex) for that round.

    A round with a top-level "gate_results_voided" note is SKIPPED entirely — those gate_fail
    entries were graded before the gate-artifact fix (2026-07-06) and are known-false (they
    graded unrelated live client data, not the round's own artifact). The gate_fail data stays
    on disk for the record; it just never surfaces as a MISS."""
    out = []
    arena = _brain_arena_root()
    if not arena.exists():
        return out
    for brief_dir in sorted(arena.iterdir()):
        if not brief_dir.is_dir() or brief_dir.name.startswith("."):
            continue
        sf = brief_dir / ".state.json"
        if not sf.exists():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if st.get("gate_results_voided"):
            continue
        slots = st.get("slots") or {}
        gate_fail = st.get("gate_fail") or {}
        ts = st.get("updated", "")
        for slot, fails in gate_fail.items():
            lane = slots.get(slot, slot)
            for g in (fails or []):
                out.append({
                    "agent": lane,
                    "miss": f"gate:{g.get('gate_id', '?')} failed — {g.get('detail', '')}".strip(" —"),
                    "source": f"arena/{brief_dir.name}/.state.json",
                    "ts": ts,
                })
    out.sort(key=lambda r: r.get("ts") or "", reverse=True)
    return out[:limit]


def _brain_retracted_lesson_texts() -> set[str]:
    """Lesson TEXTS (normalized) marked retracted in outputs/learned-candidates/*.json.
    A candidate file carries "retracted": true + "retracted_lessons": [...] listing the exact
    lesson strings that were compiled from a since-voided source (e.g. pre-gate-artifact-fix
    gate_fail rows). Read at REQUEST time — never cached — so a retraction takes effect
    immediately without a restart."""
    out: set[str] = set()
    root = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT
    cdir = root / "outputs" / "learned-candidates"
    if not cdir.is_dir():
        return out
    for path in cdir.glob("*.json"):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not obj.get("retracted"):
            continue
        for lesson in (obj.get("retracted_lessons") or []):
            if isinstance(lesson, str):
                out.add(lesson.strip())
    return out


def _brain_misses_from_compiled(limit: int) -> list[dict]:
    """Per-contract learned misses from ledgers/compiled.jsonl — lines in lessons_added that
    are gate-kill lines ('gate:X failed ...'), one row per line, newest ledger entries first.

    Lines whose lesson text matches a RETRACTED lesson (see _brain_retracted_lesson_texts) are
    skipped — those were compiled from gate runs later voided as false (graded unrelated live
    client data, not the round's own artifact; pre gate-artifact-fix 2026-07-06). The ledger
    line itself is never edited (append-only law); only the MISSES view filters it out."""
    out = []
    p = _brain_compiled_path()
    if not p.exists():
        return out
    retracted = _brain_retracted_lesson_texts()
    try:
        raw = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return out
    for l in reversed(raw):
        try:
            rec = json.loads(l)
        except Exception:
            continue
        contract = rec.get("contract", "?")
        ts = rec.get("ts", "")
        for line in (rec.get("lessons_added") or []):
            if "gate:" not in line or "failed" not in line:
                continue
            # line shape: "- {date} · {lesson text} · src:{id}" — extract the lesson text to
            # compare against the retracted set (which holds raw lesson text, no date/src wrap).
            body = line.split("· src:")[0].strip(" -")
            lesson_text = body.split("· ", 1)[1].strip() if "· " in body else body
            if lesson_text in retracted:
                continue
            out.append({
                "agent": contract,
                "miss": body,
                "source": "ledgers/compiled.jsonl",
                "ts": ts,
            })
            if len(out) >= limit:
                return out
    return out


def _brain_misses_from_rabie(limit: int) -> list[dict]:
    """Kill verdicts from brain/data/rabie_verdicts_v2.jsonl (RABIE judge, Rule #14 ledger).
    One row per kill, newest first, one-liner = the first what_is_wrong entry."""
    out = []
    p = _brain_rabie_verdicts_path()
    if not p.exists():
        return out
    try:
        raw = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return out
    for l in reversed(raw):
        try:
            rec = json.loads(l)
        except Exception:
            continue
        if rec.get("verdict") != "kill":
            continue
        wrong = (rec.get("what_is_wrong") or ["killed — no detail"])[0]
        ts = rec.get("ts", "")
        try:
            ts_str = datetime.utcfromtimestamp(float(ts)).strftime("%Y-%m-%dT%H:%M:%SZ")
        except Exception:
            ts_str = str(ts)
        out.append({
            "agent": rec.get("handle", "?"),
            "miss": wrong,
            "source": "brain/data/rabie_verdicts_v2.jsonl",
            "ts": ts_str,
        })
        if len(out) >= limit:
            break
    return out


def _brain_misses(limit: int = 20) -> list[dict]:
    """SPEC-008 MISSES card: per-agent gate kills + judge-found misses, truth-only from disk
    at request time. Sources (each independently guarded — one failing source never blanks the
    others): arena/*/.state.json gate_fail, ledgers/compiled.jsonl gate-kill lesson lines,
    brain/data/rabie_verdicts_v2.jsonl kill verdicts. Missing source contributes nothing (never
    fake); empty overall -> caller shows 'no data yet'. Newest first, capped at `limit`."""
    rows = []
    rows.extend(_brain_misses_from_arena(limit))
    rows.extend(_brain_misses_from_compiled(limit))
    rows.extend(_brain_misses_from_rabie(limit))
    rows.sort(key=lambda r: r.get("ts") or "", reverse=True)
    return rows[:limit]


def _brain_delta(limit: int = 12) -> list[dict]:
    """SPEC-008 DELTA card: the last `limit` arena rounds from ledgers/delta.jsonl, newest first,
    DEDUPED BY brief_id — a refolded round (a late judge verdict superseding an earlier row via
    "supersedes": "<prev ts>") shows only its newest row; the superseded row is kept in the
    ledger (append-only law) but never shown. Batch-over-batch improvement — every row read at
    REQUEST time from disk. Missing file = empty (the card shows 'no rounds yet', never fake)."""
    p = _brain_delta_path()
    if not p.exists():
        return []
    try:
        raw = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception:
        return []
    latest_by_brief: dict[str, dict] = {}
    order: list[str] = []  # first-seen order of each brief_id, for stable "newest first" output
    for l in raw:
        try:
            rec = json.loads(l)
        except Exception:
            continue
        bid = rec.get("brief_id", "?")
        if bid not in latest_by_brief:
            order.append(bid)
        latest_by_brief[bid] = rec  # last occurrence in file order wins (append-only -> newest)
    out = []
    for bid in order:
        rec = latest_by_brief[bid]
        out.append({
            "brief_id": rec.get("brief_id", "?"),
            "task_type": rec.get("task_type", "?"),
            "winner": rec.get("winner", "?"),
            "score_claude": rec.get("score_claude"),
            "score_codex": rec.get("score_codex"),
            "gap": rec.get("gap"),
            "ts": rec.get("ts", ""),
        })
    out.reverse()  # newest first
    return out[:limit]


@app.get("/api/brain")
def brain_api(request: Request):
    """Truth-only JSON for the /brain page. Read fresh from disk every call."""
    return JSONResponse({
        "now": _brain_now(),
        "health": _brain_health_lines(20),
        "spend_today": _brain_spend_today(),
        "needs_open": _brain_needs_open(),
        "delta": _brain_delta(12),
        "misses": _brain_misses(20),
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }, headers={"Cache-Control": "no-store"})


_BRAIN_HTML = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OGZ · brain</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0d11;color:#e8ecf1;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;
     padding:14px;max-width:760px;margin:0 auto;-webkit-font-smoothing:antialiased}
h1{font-size:26px;font-weight:800;letter-spacing:-.5px;margin-bottom:2px}
.sub{color:#6b7686;font-size:12px;margin-bottom:16px}
.card{background:#12161c;border:1px solid #1e252e;border-radius:14px;padding:16px;margin-bottom:14px}
.card h2{font-size:13px;text-transform:uppercase;letter-spacing:1.5px;color:#8b97a7;margin-bottom:12px;font-weight:700}
.row{display:flex;align-items:center;gap:10px;padding:10px 0;border-top:1px solid #1a212a}
.row:first-of-type{border-top:none}
.w{font-weight:700;font-size:14px;min-width:56px}
.claude{color:#7cc4ff}.codex{color:#c5a3ff}
.meta{color:#9aa6b6;font-size:12.5px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.age{color:#6b7686;font-size:12px;font-variant-numeric:tabular-nums}
.budget{color:#5b6675;font-size:11px;margin-top:2px}
.idle{color:#6b7686;font-style:italic;padding:6px 0}
.dot{width:9px;height:9px;border-radius:50%;flex:none}
.green{background:#3ddc84}.red{background:#ff5a5a}.grey{background:#4a5361}
.hname{flex:1;font-size:13.5px}
.big{font-size:34px;font-weight:800;letter-spacing:-1px;font-variant-numeric:tabular-nums}
.spendgrid{display:flex;gap:22px;flex-wrap:wrap;margin-top:4px}
.spendgrid .l{color:#8b97a7;font-size:11px;text-transform:uppercase;letter-spacing:1px}
.byw{color:#9aa6b6;font-size:12.5px;margin-top:10px}
.needs{display:flex;align-items:baseline;gap:10px}
.needs .n{font-size:34px;font-weight:800;font-variant-numeric:tabular-nums}
.needs .z{color:#3ddc84}.needs .o{color:#ffb454}
.phase{opacity:.42}
.phase .tag{display:inline-block;font-size:10px;letter-spacing:1px;color:#6b7686;border:1px solid #2a323d;
     border-radius:6px;padding:2px 7px;margin-left:8px;text-transform:uppercase;vertical-align:middle}
.phase .ph{color:#6b7686;font-size:13px;padding:6px 0}
.foot{color:#4a5361;font-size:11px;text-align:center;margin-top:6px}
</style></head><body>
<h1>brain</h1>
<div class="sub">the two hands, live · auto-refresh 30s · every number read from disk</div>

<div class="card"><h2>NOW</h2><div id="now"><div class="idle">loading…</div></div></div>

<div class="card"><h2>Health</h2><div id="health"></div>
  <div class="row" style="margin-top:6px">
    <div style="flex:1"><div class="l" style="color:#8b97a7;font-size:11px;text-transform:uppercase;letter-spacing:1px">today's spend</div>
      <div id="spend"></div></div></div>
  <div class="row"><div style="flex:1"><div class="l" style="color:#8b97a7;font-size:11px;text-transform:uppercase;letter-spacing:1px">needs-mohamed open</div>
      <div id="needs" class="needs"></div></div></div>
</div>

<div class="card"><h2>Misses</h2><div id="misses"><div class="idle">loading…</div></div></div>
<div class="card"><h2>Delta</h2><div id="delta"><div class="idle">loading…</div></div></div>
<div class="card phase"><h2>Your Queue <span class="tag">Phase 1</span></h2>
  <div class="ph">what awaits Mohamed's taps — not yet wired</div></div>

<div class="foot" id="foot"></div>

<script>
function esc(s){return String(s==null?"":s).replace(/[&<>]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c];});}
function budget(r){var p=[];if(r.max_calls!=null)p.push(r.max_calls+" calls");if(r.max_usd!=null)p.push("$"+r.max_usd);if(r.max_minutes!=null)p.push(r.max_minutes+"m");return p.join(" · ");}
async function load(){
  let d;
  try{ d=await (await fetch("/api/brain",{cache:"no-store"})).json(); }
  catch(e){ document.getElementById("foot").textContent="offline — retrying"; return; }
  // NOW
  var now=d.now||[];var nh="";
  if(!now.length){ nh='<div class="idle">both hands idle</div>'; }
  else{ now.forEach(function(r){
    nh+='<div class="row"><span class="w '+esc(r.worker)+'">'+esc(r.worker)+'</span>'
      +'<div class="meta">'+esc(r.client)+' · '+esc(r.task_type)+' · <span style="color:#6b7686">'+esc(r.id)+'</span>'
      +(budget(r)?'<div class="budget">'+esc(budget(r))+'</div>':'')+'</div>'
      +'<span class="age">'+esc(r.age)+'</span></div>';
  }); }
  document.getElementById("now").innerHTML=nh;
  // MISSES — per-agent gate kills + judge-found misses (SPEC-008), newest first
  var ms=d.misses||[];var mh="";
  if(!ms.length){ mh='<div class="idle">no data yet</div>'; }
  else{ ms.forEach(function(r){
    mh+='<div class="row"><div class="meta"><span class="w" style="min-width:0">'+esc(r.agent)+'</span> · '
      +esc(r.miss)+' <span style="color:#4a5361">('+esc(r.source)+')</span></div>'
      +'<span class="age">'+esc((r.ts||"").slice(0,10))+'</span></div>';
  }); }
  document.getElementById("misses").innerHTML=mh;
  // HEALTH lines
  var hl=d.health||[];var hh="";
  if(!hl.length){ hh='<div class="idle">no data yet</div>'; }
  else{ hl.slice().reverse().forEach(function(h){
    var cls=h.status==="green"?"green":(h.status==="red"?"red":"grey");
    hh+='<div class="row"><span class="dot '+cls+'"></span><span class="hname">'+esc(h.check)+'</span>'
      +'<span class="age">'+esc(h.age)+'</span></div>';
  }); }
  document.getElementById("health").innerHTML=hh;
  // SPEND
  var s=d.spend_today||{};var sh="";
  if(!s.has_data){ sh='<div class="idle">no data yet</div>'; }
  else{
    sh='<div class="spendgrid"><div><span class="big">'+ (s.total_calls||0) +'</span> <span class="l">calls</span></div>'
      +'<div><span class="big">$'+ (Number(s.total_usd||0).toFixed(2)) +'</span> <span class="l">spend</span></div></div>';
    var byw=s.by_worker||{};var parts=[];
    Object.keys(byw).forEach(function(w){parts.push(esc(w)+": "+byw[w].calls+" calls · $"+Number(byw[w].usd).toFixed(2));});
    if(parts.length)sh+='<div class="byw">'+parts.join(" &nbsp;·&nbsp; ")+'</div>';
  }
  document.getElementById("spend").innerHTML=sh;
  // NEEDS
  var n=d.needs_open||0;
  document.getElementById("needs").innerHTML='<span class="n '+(n?"o":"z")+'">'+n+'</span>'
    +'<span class="l" style="color:#8b97a7">'+(n?"awaiting you":"all clear")+'</span>';
  // DELTA — arena batch-over-batch (SPEC-008), newest first
  var dl=d.delta||[];var dh="";
  if(!dl.length){ dh='<div class="idle">no rounds yet</div>'; }
  else{ dl.forEach(function(r){
    var w=String(r.winner||"?");
    var wcls=w==="claude"?"claude":(w==="codex"?"codex":"");
    var sc=(r.score_claude==null||r.score_claude<0)?"–":r.score_claude;
    var sx=(r.score_codex==null||r.score_codex<0)?"–":r.score_codex;
    dh+='<div class="row"><div class="meta"><span style="color:#6b7686">'+esc(r.brief_id)+'</span> · '
      +esc(r.task_type)+' &nbsp; <span class="claude">C '+esc(sc)+'</span> / <span class="codex">X '+esc(sx)+'</span></div>'
      +'<span class="w '+wcls+'">'+esc(w)+'</span></div>';
  }); }
  document.getElementById("delta").innerHTML=dh;
  document.getElementById("foot").textContent="updated "+esc(d.ts);
}
load();setInterval(load,30000);
</script>
</body></html>"""


@app.get("/brain")
def brain_page():
    """PLATFORM v0 dashboard — NOW + HEALTH cards, phone-first, dark, auto-refresh.
    Open (no key) so it always renders; all data pulled client-side from /api/brain,
    which reads the queue + ledgers fresh on every request. No hardcoded numbers."""
    return HTMLResponse(_BRAIN_HTML, headers={"Cache-Control": "no-store"})


# ---- control-center data (all READ-ONLY; each source guarded so one failure never 500s) ----

def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _last_entry(mem: Path):
    """newest '## ...' dated header + the line under it from a mind's memory.md."""
    txt = _safe_read(mem)
    if not txt:
        return None, None
    header, body = None, ""
    for ln in txt.splitlines():
        if ln.startswith("## "):
            header, body = ln[3:].strip(), ""
        elif header is not None and ln.strip() and not body:
            body = ln.strip()
    return header, body


def _age_status(mtime: float) -> str:
    if not mtime:
        return "unknown"
    age = datetime.now().timestamp() - mtime
    if age < 86400:
        return "working"       # <1d
    if age < 3 * 86400:
        return "recent"        # <3d
    return "idle"


_MINDS = [
    ("ceo", "CEO", "Executive council", "orchestrator/minds/ceo", "Mohamed",
     "Brief classification → go/no-go → direction frame → human-gate triggers"),
    ("coo", "COO", "Executive council", "orchestrator/minds/coo", "CEO",
     "Queue order, capacity enforcement, confidence states, readiness"),
    ("cfo", "CFO", "Executive council", "orchestrator/minds/cfo", "CEO",
     "Pricing sanity, margin, resource budgets, cost discipline — owns the model router"),
    ("cco", "CCO", "THE GATE", "02-Platform-AI/Knowledge/minds/cco", "Mohamed (taste-proxy)",
     "Quality gate (dual rubric) — is it Saudi-native, on-taste, good enough to leave the building"),
    ("creative-director", "Creative Director", "Writers' room", "02-Platform-AI/Knowledge/minds/creative-director", "CCO",
     "Brief interrogation, 5-brain routing, the creative-direction brief"),
    ("copywriter", "Copywriter", "Writers' room", "02-Platform-AI/Knowledge/minds/copywriter", "Creative Director",
     "Long-form proposal prose + campaign copy, bilingual"),
    ("caption-writer", "Caption Writer", "Writers' room", "02-Platform-AI/Knowledge/minds/caption-writer", "Creative Director",
     "Saudi Arabic short-form captions from the pattern-card menu"),
    ("scriptwriter", "Scriptwriter", "Writers' room", "02-Platform-AI/Knowledge/minds/scriptwriter", "Creative Director",
     "Film scripts + VO, bilingual — beat-by-beat"),
    ("designer", "Designer", "Visual room", "02-Platform-AI/Design/minds/designer", "Creative Director",
     "Slide/deck design, token-law enforcement, image-first discipline"),
    ("treatment-cinematography", "Treatment / Cinematography", "Visual room", "02-Platform-AI/Design/minds/treatment-cinematography", "Creative Director",
     "Director's treatment, shot choreography, mood/reference direction"),
    ("marketing-strategist", "Marketing Strategist", "Council + solo", "01-OGZ-Studios/Emails/minds/marketing-strategist", "CEO",
     "Opportunity surfacing, positioning frames, market map"),
    ("data-analyst", "Data / Insight Analyst", "Solo, feeds every room", "02-Platform-AI/Knowledge/minds/data-analyst", "COO",
     "Corpus reading, pattern verification, eyeballed metrics behind every claim"),
]

# core agents (umbrella owners) — activity rolls up from their child minds
_CORE = [
    ("proposal", "Proposal Agent", "01-OGZ-Studios/Proposals", "RFP → strategy → proposal assembly → learnings", ["copywriter"]),
    ("client-intel", "Client-Intel & Inbox Agent", "01-OGZ-Studios/Emails", "Client bible, market intel, BD outreach drafts", ["marketing-strategist"]),
    ("knowledge", "Knowledge Agent", "02-Platform-AI/Knowledge", "Index, taste-moat keeper, enrichment, corpus search", ["cco", "creative-director", "copywriter", "caption-writer", "scriptwriter", "data-analyst"]),
    ("design", "Design & Render Agent", "02-Platform-AI/Design", "Design-system stewardship, token law, render canon", ["designer", "treatment-cinematography"]),
]


def _method_steps(txt: str):
    """Parse a `## Method` section (inline or multiline `N. `) into a list of step strings."""
    import re as _re
    m = _re.search(r"^##+\s*Method.*?$(.*?)(?=^##\s|\Z)", txt, _re.S | _re.M)
    if not m:
        return []
    body = _re.sub(r"\s+", " ", m.group(1)).strip()
    parts = _re.split(r"(?:^|\s)(\d+)\.\s+", body)
    out = []
    for i in range(1, len(parts) - 1, 2):
        s = parts[i + 1].strip().rstrip(".")
        if s:
            out.append(s)
    return out


def _workflow_steps(rel: str):
    """The agent's numbered workflow — from WORKFLOW.md if present (canonical), else parsed
    live from AGENT.md `## Method` (so cross-umbrella minds still show their real workflow)."""
    import re as _re
    wf = OGZ_ROOT / rel / "WORKFLOW.md"
    if wf.exists():
        txt = _safe_read(wf)
        m = _re.search(r"^##+\s*Steps.*?$(.*?)(?=^##\s|\Z)", txt, _re.S | _re.M)
        if m:
            steps = [_re.sub(r"^\s*\d+\.\s*", "", ln).strip()
                     for ln in m.group(1).splitlines() if _re.match(r"^\s*\d+\.", ln)]
            if steps:
                return steps
    return _method_steps(_safe_read(OGZ_ROOT / rel / "AGENT.md"))


def _memory_last_today(rel: str):
    """(newest dated '## ...' header, count of TODAY-dated entries) from a mind's memory.md."""
    import re as _re
    txt = _safe_read(OGZ_ROOT / rel / "memory.md")
    heads = _re.findall(r"^##\s+(.+)$", txt, _re.M)
    tdy = today_str()
    today_n = sum(1 for h in heads if tdy in h)
    return (heads[-1].strip() if heads else None), today_n


def _active_phase():
    """What the live pipeline is doing NOW + which agent roles it implicates — from the newest
    heartbeat line + recent model_usage capabilities. Evidence-based; no fabrication."""
    hb = _hb_lines(1)
    phase_txt = (hb[-1]["msg"] if hb else "")
    caps = []
    for ln in _safe_read(OGZ_ROOT / "journal/model_usage.jsonl").splitlines()[-12:]:
        try:
            r = json.loads(ln)
        except Exception:
            continue
        ts = _epoch(r.get("ts", ""))
        if ts and (datetime.now().timestamp() - ts) < 1800 and r.get("capability"):
            caps.append(str(r["capability"]))
    low = (phase_txt + " " + " ".join(caps)).lower()
    roles = set()
    if any(w in low for w in ("proposal", "compose", "draft", "amira", "voice", "template")):
        roles |= {"copywriter", "creative-director"}
    if any(w in low for w in ("gate", "review", "regression", "cco", "critique", "8.5", "panel")):
        roles |= {"cco", "data-analyst"}
    if any(w in low for w in ("render", "deck", "deck_studio", "font", "design")):
        roles |= {"designer"}
    return phase_txt, roles, caps


def _current_step(steps, phase_txt, role=None):
    """The step the live pipeline signal points to (inferred from the heartbeat/capabilities —
    labelled 'live' in the UI, never presented as a literal step-emitter). Stem/substring overlap
    so 'rendered'↔'render', 'gated'↔'gate' match; a role→keyword fallback keeps a working agent on
    a sensible step instead of showing nothing."""
    import re as _re
    if not steps or not phase_txt:
        return None
    pt = [w for w in _re.findall(r"[a-zء-ي]+", phase_txt.lower()) if len(w) > 3]
    best, bi = 0, None
    for i, s in enumerate(steps):
        st = [w for w in _re.findall(r"[a-zء-ي]+", s.lower()) if len(w) > 3]
        ov = sum(1 for a in pt for b in st if a == b or (len(a) >= 4 and len(b) >= 4 and (a[:4] == b[:4])))
        if ov > best:
            best, bi = ov, i + 1
    if bi:
        return bi
    # role fallback: land on the step matching the role's live verb
    FB = {"designer": ("render", "lay out", "deck"), "cco": ("gate", "score", "review"),
          "data-analyst": ("verif", "eyeball", "score", "read"),
          "copywriter": ("author", "draft", "idea"), "creative-director": ("route", "brief", "brain")}
    for verb in FB.get(role or "", ()):
        for i, s in enumerate(steps):
            if verb in s.lower():
                return i + 1
    return None


@app.get("/api/control/agents")
def control_agents(k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    phase_txt, active_roles, caps = _active_phase()
    minds = {}
    for mid, name, room, rel, reports, what in _MINDS:
        mem = OGZ_ROOT / rel / "memory.md"
        mt = mem.stat().st_mtime if mem.exists() else 0
        _hdr, ktoday = _memory_last_today(rel)
        _h2, last_body = _last_entry(mem)          # the actual learning text, not the date header
        last_out = (last_body or _hdr or "")[:160] or None
        steps = _workflow_steps(rel)
        working = mid in active_roles
        status = "working" if working else _age_status(mt)
        cur = _current_step(steps, phase_txt, mid) if working else None
        minds[mid] = {
            "id": mid, "name": name, "room": room, "reports_to": reports, "what": what,
            "model": "Claude (scoped agent)", "home": rel, "local": True,
            "workflow": steps, "n_steps": len(steps),
            "current_step": cur, "status": status,
            "doing_now": (phase_txt if working else None),
            "last_output": last_out, "memory_mtime": int(mt),
            "knowledge_today": ktoday or None,
        }
    try:
        stt = json.loads(_safe_read(OGZ_ROOT / "studio/training/state.json") or "{}")
        gm = (stt.get("grader_seat") or {}).get("model")
        if gm and "cco" in minds:
            minds["cco"]["model"] = f"Claude (gate) · grader seat: {gm}"
    except Exception:
        pass
    # core agents (umbrella owners): 4 short coordination steps; activity + live step roll up from children
    CORE_WF = {
        "proposal": ["Receive the RFP/brief + past learnings", "Council sets direction + price",
                     "Writers' room drafts (copy/caption/script)", "CCO gate → review-queue → Mohamed"],
        "client-intel": ["Watch inbox + client bibles", "Pull market intel on demand",
                         "Draft BD outreach", "Hand the brief to the council"],
        "knowledge": ["Index + embed the corpus", "Serve know-how to every mind",
                      "Capture new learnings", "Keep the taste-moat current"],
        "design": ["Read the CD route + tokens", "Lay out image-first slides/deck",
                   "Self-audit vs the visual rules", "Render + hand off"],
    }
    core = []
    for cid, name, rel, what, children in _CORE:
        cms = [minds[c] for c in children if c in minds]
        working = any(c["status"] == "working" for c in cms)
        mt = max([c["memory_mtime"] for c in cms] or [0])
        steps = CORE_WF.get(cid, [])
        cur = None
        if working:
            # current step of the core = the phase mapped onto its own 4 steps
            cur = _current_step(steps, phase_txt)
        kt = sum(c.get("knowledge_today") or 0 for c in cms)
        core.append({"id": cid, "name": name, "home": rel, "what": what, "local": True,
                     "model": "Claude (scoped agent)", "children": children,
                     "workflow": steps, "n_steps": len(steps), "current_step": cur,
                     "status": "working" if working else _age_status(mt),
                     "doing_now": (phase_txt if working else None),
                     "active_child": next((c["name"] for c in cms if c["status"] == "working"), None),
                     "knowledge_today": kt or None, "memory_mtime": mt})
    return JSONResponse({"ok": True, "core": core, "minds": list(minds.values()),
                         "phase": phase_txt, "active_roles": sorted(active_roles),
                         "counts": {"core": len(core), "minds": len(minds)}})


@app.get("/api/control/agentdoc")
def control_agentdoc(id: str = "", k: str = ""):
    """The role/method doc (AGENT.md) for a mind — the drill-down the Agents view opens.
    (No WORKFLOW.md exists per mind; AGENT.md IS the role + method.) Read-only, id-guarded."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    rel = next((m[3] for m in _MINDS if m[0] == id), None)
    if not rel:
        return JSONResponse({"ok": False, "error": "unknown agent"}, status_code=404)
    doc = _safe_read(OGZ_ROOT / rel / "AGENT.md")[:12000]
    mem = _safe_read(OGZ_ROOT / rel / "memory.md")
    # last ~1200 chars of memory = the freshest learnings
    return JSONResponse({"ok": True, "id": id, "agent_md": doc,
                         "memory_tail": mem[-1600:] if mem else ""})


@app.get("/api/control/knowhow")
def control_knowhow(aspect: str = "", who: str = "", k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    KH = OGZ_ROOT / "02-Platform-AI/Knowledge/know-how"
    # drill-down: return one aspect's atoms (read-only; Alhareth's are protected → view only)
    if aspect:
        aspect = "".join(c for c in aspect if c.isalnum() or c in "-_")   # guard
        base = KH / ("_alhareth_atoms" if who == "alhareth" else "_atoms")
        pre = ("alhareth__" + aspect) if who == "alhareth" else aspect
        atoms = []
        try:
            for p in sorted(base.glob(pre + "__*.txt"))[:60]:
                atoms.append(_safe_read(p).strip()[:600])
        except Exception:
            pass
        return JSONResponse({"ok": True, "aspect": aspect, "who": who or "mohamed",
                             "atoms": atoms, "count": len(atoms)})
    # overview: aspects + counts from INDEX.md + atom-dir counts + calibration
    def _count(dirp: Path, pre=""):
        try:
            return len([p for p in dirp.glob(pre + "*.txt")]) if dirp.exists() else 0
        except Exception:
            return 0
    aspects = []
    idx = _safe_read(KH / "INDEX.md")
    import re as _re
    for m in _re.finditer(r"^\|\s*([a-z0-9-]+)\s*\|\s*(\d+)\s*\|", idx, _re.M):
        nm = m.group(1)
        aspects.append({"name": nm, "findings": int(m.group(2)),
                        "atoms": _count(KH / "_atoms", nm + "__")})
    al_aspects = []
    albase = KH / "_alhareth_atoms"
    seen = {}
    if albase.exists():
        for p in albase.glob("alhareth__*__*.txt"):
            asp = p.name.split("__")[1] if len(p.name.split("__")) > 2 else "other"
            seen[asp] = seen.get(asp, 0) + 1
    for nm, c in sorted(seen.items(), key=lambda x: -x[1]):
        al_aspects.append({"name": nm, "atoms": c})
    total = sum(a["findings"] for a in aspects)
    cal = {}
    try:
        stt = json.loads(_safe_read(OGZ_ROOT / "studio/training/state.json") or "{}")
        c = stt.get("calibration", {})
        g = stt.get("grader_seat", {})
        seed = c.get("seeded_from_history", {})
        cal = {"epoch": c.get("calibration_epoch"), "last_intake": c.get("last_intake_ts"),
               "last_mohamed_score": c.get("last_mohamed_score"),
               "samples_since_feedback": c.get("samples_since_last_feedback"),
               "hard_stopped": c.get("hard_stopped"),
               "grader_model": g.get("model"), "grader_verdict": g.get("verdict"),
               "seeded_samples": (seed.get("distribution", {}) or {}).get("portal_answers_total")
               or seed.get("portal_answers_total")}
    except Exception:
        pass
    return JSONResponse({"ok": True, "total": total, "aspects": aspects,
                         "alhareth_total": _count(albase), "alhareth_aspects": al_aspects,
                         "calibration": cal})


@app.get("/api/control/budget")
def control_budget(k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    usage = OGZ_ROOT / "journal/model_usage.jsonl"
    by_model, by_provider = {}, {}
    today_usd = month_usd = 0.0
    last_provider = last_model = None
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")
    for ln in _safe_read(usage).splitlines():
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if not r.get("provider"):
            continue      # skip tool/skip meter rows (no provider)
        usd = float(r.get("usd") or 0)
        prov, mdl = r.get("provider"), r.get("model", "?")
        bm = by_model.setdefault(mdl, {"model": mdl, "usd": 0.0, "calls": 0})
        bm["usd"] += usd; bm["calls"] += 1
        bp = by_provider.setdefault(prov, {"provider": prov, "usd": 0.0, "calls": 0})
        bp["usd"] += usd; bp["calls"] += 1
        ts = str(r.get("ts", ""))
        if ts[:10] == today:
            today_usd += usd
        if ts[:7] == month:
            month_usd += usd
        last_provider, last_model = prov, mdl
    _TIER = {"local": "LOCAL", "gemini": "FREE_POOL", "groq": "FREE_POOL",
             "deepseek": "CHEAP", "openai": "PAID", "fable": "FABLE"}
    tier = _TIER.get(last_provider or "", (last_provider or "—"))
    if last_model and "fable" in str(last_model):
        tier = "FABLE"
    caps, state = {}, {}
    try:
        cfg = json.loads(_safe_read(OGZ_ROOT / "tools/model_router.json") or "{}")
        b = cfg.get("budget", {})
        caps = {"usd_per_day": b.get("usd_per_day"), "usd_per_month": b.get("usd_per_month"),
                "openai_usd_per_day": b.get("openai_usd_per_day"),
                "fable_per_day": b.get("fable_escalations_per_day"),
                "apify_usd_per_day": ((b.get("tools", {}) or {}).get("apify", {}) or {}).get("usd_per_day"),
                "proposal_monthly_usd": b.get("openai_proposal_monthly_usd")}
    except Exception:
        pass
    try:
        state = json.loads(_safe_read(OGZ_ROOT / "journal/model_router_state.json") or "{}")
    except Exception:
        pass
    rnd = lambda x: round(x, 4)
    for d in (by_model, by_provider):
        for v in d.values():
            v["usd"] = rnd(v["usd"])
    return JSONResponse({"ok": True, "today_usd": rnd(today_usd), "month_usd": rnd(month_usd),
                         "by_model": sorted(by_model.values(), key=lambda x: -x["usd"]),
                         "by_provider": sorted(by_provider.values(), key=lambda x: -x["usd"]),
                         "caps": caps, "current_tier": tier,
                         "state": {kk: state.get(kk) for kk in
                                   ("day", "usd_day", "usd_month", "fable_day", "usd_day_by",
                                    "proposal_month_usd") if kk in state}})


def _hb_lines(n=12):
    """parse heartbeat.md: dated 'YYYY-MM-DD HH:MM · msg' then bare 'HH:MM · msg' inherit the date."""
    out, cur_date = [], None
    import re as _re
    for ln in _safe_read(OGZ_ROOT / "journal/heartbeat.md").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        m = _re.match(r"^(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s*·?\s*(.*)$", ln)
        if m:
            cur_date = m.group(1)
            out.append({"date": cur_date, "time": m.group(2), "msg": m.group(3)})
            continue
        m2 = _re.match(r"^(\d{2}:\d{2})\s*·?\s*(.*)$", ln)
        if m2:
            out.append({"date": cur_date or today_str(), "time": m2.group(1), "msg": m2.group(2)})
        else:
            out.append({"date": cur_date, "time": "", "msg": ln})
    return out[-n:]


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


@app.get("/api/control/pipeline")
def control_pipeline(k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    usage = OGZ_ROOT / "journal/model_usage.jsonl"
    rows = []
    for ln in _safe_read(usage).splitlines()[-40:]:
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    prop = [r for r in rows if str(r.get("capability", "")).startswith("proposal")]
    last = rows[-1] if rows else {}
    first_today = None
    tdy = today_str()
    for r in rows:
        if str(r.get("ts", ""))[:10] == tdy and str(r.get("capability", "")).startswith("proposal"):
            first_today = r; break
    last_ts = str(last.get("ts", "")) if last else ""
    # running vs stalled from the newest ts age
    age_secs = None
    try:
        age_secs = datetime.now().timestamp() - _epoch(last_ts)
    except Exception:
        pass
    status = "unknown"
    if age_secs is not None:
        status = "RUNNING" if age_secs < 600 else ("STALLED" if age_secs < 3600 else "PAUSED/idle")
    # newest jadarat job dir + its files
    jobsdir = OGZ_ROOT / "studio/jobs"
    job = None
    try:
        jd = sorted([p for p in jobsdir.glob("*jadarat*") if p.is_dir()],
                    key=lambda p: p.stat().st_mtime, reverse=True)
        job = jd[0] if jd else None
    except Exception:
        pass
    files = []
    if job:
        try:
            for p in sorted(job.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if p.is_file():
                    files.append({"name": p.name, "size": p.stat().st_size,
                                  "mtime": int(p.stat().st_mtime), "job": job.name})
        except Exception:
            pass
    cur = {"client": "HRDF · Jadarat", "job_id": job.name if job else None,
           "stage": (last.get("capability") if prop else None),
           "agent": (f"{last.get('model')} ({last.get('provider')})" if last.get("provider") else None),
           "started_at": (first_today.get("ts") if first_today else None),
           "last_activity": last_ts, "status": status,
           "deadline": "Sun 20:00 Riyadh (Jadarat first draft)"}
    recent = [{"ts": r.get("ts"), "event": r.get("capability"), "model": r.get("model"),
               "usd": r.get("usd")} for r in rows[-14:][::-1]]
    return JSONResponse({"ok": True, "current": cur, "heartbeat": _hb_lines(12),
                         "recent_calls": recent, "files": files[:16]})


@app.get("/api/control/jobfile")
def control_jobfile(job: str = "", name: str = "", k: str = ""):
    """Serve one file from a studio job dir (the pipeline 'open file' buttons). Read-only,
    path-guarded under studio/jobs (rejects .., slashes)."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    if not job or not name or any(c in job + name for c in "/\\\x00") or ".." in job + name:
        return JSONResponse({"ok": False, "error": "bad path"}, status_code=400)
    p = (OGZ_ROOT / "studio/jobs" / job / name).resolve()
    root = (OGZ_ROOT / "studio/jobs").resolve()
    if not (str(p).startswith(str(root) + "/") and p.is_file()):
        return JSONResponse({"ok": False, "error": "not found"}, status_code=404)
    mt = "application/pdf" if p.suffix == ".pdf" else (
        "text/plain; charset=utf-8" if p.suffix in (".md", ".txt", ".json", ".jsonl", ".log") else "application/octet-stream")
    return FileResponse(p, media_type=mt, headers={"Cache-Control": "private, no-cache"})


@app.get("/api/control/health")
def control_health(k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    import subprocess
    import shutil

    def run(cmd, timeout=8):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip(), r.returncode
        except Exception as e:
            return f"(err {type(e).__name__})", 1

    services = []
    for name, port in (("brain_api", 4140), ("portal", 4199)):
        out, _ = run(["curl", "-s", "-m", "3", "-o", "/dev/null",
                      "-w", "%{http_code} %{time_total}", f"http://127.0.0.1:{port}/"], 5)
        code = (out.split() + ["", ""])[0]
        up = code.isdigit()
        services.append({"name": name, "port": port, "up": up,
                         "http_code": code if up else "—",
                         "detail": "listening" if up else "no response"})
    # tunnels
    tunnels = []
    cf, _ = run(["pgrep", "-fl", "cloudflared"], 5)
    tunnels.append({"name": "cloudflared · ogz-brain", "up": "ogz-brain" in cf,
                    "detail": (cf.splitlines()[0][:90] if cf and "ogz-brain" in cf else "not running")})
    if shutil.which("tailscale"):
        ts, _ = run(["tailscale", "ip", "-4"], 5)
        tunnels.append({"name": "tailscale", "up": bool(ts and ts[0:1].isdigit()),
                        "detail": ts.splitlines()[0] if ts else "status unavailable"})
    # launchagents
    la = []
    lo, _ = run(["launchctl", "list"], 6)
    for line in lo.splitlines():
        if any(t in line for t in ("com.ogz", "abraham", "com.abraham")):
            parts = line.split("\t")
            if len(parts) >= 3:
                la.append({"label": parts[2], "pid": parts[0],
                           "loaded": parts[0] != "-", "exit": parts[1]})
    # last scan
    last_scan = {}
    try:
        cr = _safe_read(OGZ_ROOT / "journal/corpus-refresh.jsonl").splitlines()
        if cr:
            j = json.loads(cr[-1])
            ts = j.get("ts", "")
            last_scan = {"ts": ts, "age_hours": round((datetime.now().timestamp() - _epoch(ts)) / 3600, 1),
                         "steps": list((j.get("steps") or {}).keys()) if isinstance(j.get("steps"), dict) else j.get("steps")}
    except Exception:
        pass
    # commits
    commits = []
    for label, repo in (("OGZ-System", OGZ_ROOT), ("brain", OGZ_ROOT / "02-Platform-AI/Knowledge/brain")):
        out, rc = run(["git", "-C", str(repo), "log", "-1", "--format=%h|%s|%aI"], 8)
        if rc == 0 and "|" in out:
            h, msg, ts = (out.split("|", 2) + ["", "", ""])[:3]
            commits.append({"repo": label, "hash": h, "msg": msg[:100], "ts": ts,
                            "age_hours": round((datetime.now().timestamp() - _epoch(ts)) / 3600, 1)})
    # heartbeat freshness
    hbf = OGZ_ROOT / "journal/heartbeat.md"
    hb = {}
    if hbf.exists():
        mt = hbf.stat().st_mtime
        lines = [l for l in _safe_read(hbf).splitlines() if l.strip()]
        hb = {"mtime": int(mt), "fresh_secs": int(datetime.now().timestamp() - mt),
              "last_line": lines[-1][:160] if lines else ""}
    # overall
    down = [s for s in services if not s["up"]]
    stale_scan = last_scan.get("age_hours", 0) and last_scan["age_hours"] > 36
    status = "healthy"
    if len(down) >= 2:
        status = "critical"
    elif down or stale_scan or (hb.get("fresh_secs", 0) > 3600):
        status = "degraded"
    return JSONResponse({"ok": True, "status": status, "services": services, "tunnels": tunnels,
                         "launchagents": la, "last_scan": last_scan, "commits": commits,
                         "heartbeat": hb, "checked_at": datetime.now().isoformat(timespec="seconds")})


@app.get("/api/control/review")
def control_review(k: str = ""):
    """A lightweight summary for the Review tab (open cards + recent verdicts) — the full
    judging flow stays at /dashboard (reused, one write path). This never writes."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    q = json.loads(_safe_read(QUEUE) or '{"items":[]}') if QUEUE.exists() else {"items": []}
    items = q.get("items", []) if isinstance(q, dict) else q
    open_n = sum(1 for it in items if it.get("status") != "answered")
    proposals = sum(1 for it in items if it.get("kind") == "proposal_judge" and it.get("status") != "answered")
    posts = sum(1 for it in items if it.get("kind") == "caption_judge" and it.get("status") != "answered")
    verdicts = []
    for ln in _safe_read(ANSWERS).splitlines()[-30:][::-1]:
        try:
            e = json.loads(ln)
        except Exception:
            continue
        if e.get("judge") in ("", "unverified", None):
            continue
        verdicts.append({"ts": e.get("ts"), "judge": e.get("judge"), "item": e.get("item_id"),
                         "answer": e.get("answer"), "rating": e.get("rating"),
                         "pins": len(e.get("comments") or [])})
    # TODAY'S GAUNTLET STATS — read fresh from the verdict spine (drafts+judgments ledgers).
    # Counting only; schema never touched (DO NOT TOUCH verdict spine schema).
    tdy = today_str()
    today_drafts = today_kills = today_pass = 0
    kill_reasons: dict[str, int] = {}
    for ln in _safe_read(OGZ_ROOT / "ledgers" / "drafts.jsonl").splitlines():
        try:
            r = json.loads(ln)
            if str(r.get("ts", "")).startswith(tdy):
                today_drafts += 1
        except Exception:
            continue
    for ln in _safe_read(OGZ_ROOT / "ledgers" / "judgments.jsonl").splitlines():
        try:
            r = json.loads(ln)
            if not str(r.get("ts", "")).startswith(tdy):
                continue
            if r.get("verdict") == "kill":
                today_kills += 1
                for reason in (r.get("reasons") or []):
                    tag = str(reason).split(":")[0].strip()[:40]
                    kill_reasons[tag] = kill_reasons.get(tag, 0) + 1
            elif r.get("verdict") == "pass":
                today_pass += 1
        except Exception:
            continue
    kill_histogram = sorted(kill_reasons.items(), key=lambda x: -x[1])
    return JSONResponse({"ok": True, "open": open_n, "proposals": proposals, "posts": posts,
                         "verdicts": verdicts[:12],
                         "today_drafts": today_drafts, "today_kills": today_kills,
                         "today_pass": today_pass,
                         "kill_histogram": [{"reason": r, "n": n} for r, n in kill_histogram[:10]]})


def _ranked_taps_needs_path() -> Path:
    root = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT
    return root / "NEEDS-MOHAMED.md"


def _ranked_taps_score(row: dict) -> tuple:
    txt = " ".join(str(row.get(k, "")) for k in ("title", "tag", "why", "need", "source", "priority")).lower()
    score = 1000
    if "due today" in txt or "today" in txt or "اليوم" in txt:
        score -= 500
    if row.get("priority") == "urgent":
        score -= 300
    if row.get("source") == "nsg-interest":
        score -= 250
    if "external send" in txt or "send from your mail" in txt:
        score -= 220
    if row.get("kind") in ("proposal_judge", "caption_judge") or "judge" in txt:
        score -= 120
    if row.get("tag") == "mohamed_must":
        score -= 90
    return (score, row.get("created") or row.get("ts") or "", row.get("id", ""))


def _needs_ranked_taps() -> tuple[list[dict], int]:
    import re as _re
    opened, resolved = {}, set()
    for line in _safe_read(_ranked_taps_needs_path()).splitlines():
        head = _re.match(r"- \[(OPEN|RESOLVED) ([0-9a-f]{8})\]", line)
        if not head:
            continue
        kind, eid = head.group(1), head.group(2)
        if kind == "RESOLVED":
            resolved.add(eid)
            continue
        m = _re.match(r"- \[OPEN [0-9a-f]{8}\]\s+([^·]+?)\s+·\s*([^·]+)\s*·\s*(.*)$", line)
        if not m:
            continue
        source = (m.group(2) or "needs").strip()
        msg = (m.group(3) or "").strip()
        title = msg.split(". ")[0].split(" — ")[0][:110] or source
        dm = _re.search(r"draft ready:\s*'([^']+)'", msg)
        draft = dm.group(1) if dm else msg[:1200]
        opened[eid] = {
            "source": source, "id": eid, "kind": "need", "tag": source,
            "title": title, "why": msg[:260], "need": "Mohamed-only gate from NEEDS-MOHAMED.",
            "did": "", "priority": "urgent" if ("TODAY" in msg or "DUE" in msg or source == "nsg-interest") else "normal",
            "created": (m.group(1) or "").strip(), "copy_text": draft,
        }
    rows = [r for eid, r in opened.items() if eid not in resolved]
    for r in rows:
        r["rank_score"] = _ranked_taps_score(r)[0]
        r["actions"] = [{"kind": "copy", "label": "Copy staged text", "copy_text": r.pop("copy_text", "")}]
    return rows, len(rows)


def _decision_ranked_taps() -> tuple[list[dict], int]:
    try:
        q = json.loads(_safe_read(QUEUE) or '{"items":[]}')
    except Exception:
        q = {"items": []}
    items = q.get("items", []) if isinstance(q, dict) else q
    rows = []
    for it in items:
        if it.get("status") in ("answered", "superseded"):
            continue
        opts = []
        for o in (it.get("options") or [])[:3]:
            if isinstance(o, dict):
                opts.append({"label": str(o.get("label") or o.get("v") or "")[:90],
                             "recommended": bool(o.get("rec"))})
            else:
                opts.append({"label": str(o)[:90], "recommended": False})
        row = {
            "source": "decision_queue", "id": it.get("id", "?"), "kind": it.get("kind", "decision"),
            "tag": it.get("tag", ""), "title": it.get("title") or it.get("id", "?"),
            "why": it.get("why", ""), "need": it.get("need", ""), "did": it.get("did", ""),
            "priority": it.get("priority") or "normal", "created": it.get("created") or "",
            "option_labels": opts,
            "actions": [{"kind": "dashboard", "label": "Open dashboard"}],
        }
        row["rank_score"] = _ranked_taps_score(row)[0]
        rows.append(row)
    return rows, len(rows)


_RIYADH = ZoneInfo("Asia/Riyadh")
_DAY_STRIP_PHASES = [
    {"id": "brief", "time": "09:00", "label": "Fake brief",
     "what": "daily-cycle creates or promotes today's real-shaped brief", "mode": "brief"},
    {"id": "produce", "time": "11:00", "label": "Produce",
     "what": "full post, full proposal, and rotating department file are enqueued", "mode": "produce"},
    {"id": "stage", "time": "17:30", "label": "Stage",
     "what": "judge --once, judge --batch, and shadow predictions refresh the board", "mode": "stage"},
    {"id": "judge", "time": "18:00", "label": "Mohamed judges",
     "what": "Mohamed judges complete results on /control, never drafts", "mode": "judge"},
    {"id": "scribe", "time": "21:30", "label": "Scribe",
     "what": "shadow predictions are scored and Mohamed's verdict words fold into book/27", "mode": "scribe"},
]


def _hm_on(base: datetime, hm: str) -> datetime:
    h, m = [int(x) for x in hm.split(":", 1)]
    return base.replace(hour=h, minute=m, second=0, microsecond=0)


def _human_eta(seconds: int) -> str:
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m"


def _day_strip_source_check() -> dict:
    book = _safe_read(OGZ_ROOT / "book" / "07-DAILY-CYCLE.md")
    script = _safe_read(OGZ_ROOT / "tools" / "jail" / "daily_cycle.sh")
    plist = _safe_read(OGZ_ROOT / "tools" / "headless" / "com.ogz.daily-cycle.plist")
    times = [p["time"] for p in _DAY_STRIP_PHASES]
    modes = [p["mode"] for p in _DAY_STRIP_PHASES if p["mode"] != "judge"]
    return {
        "book_has_times": all(t in book for t in ["09:00", "17:30", "18:00"]),
        "script_has_modes": all(m in script for m in modes),
        "plist_has_fires": all(t.split(":")[0].lstrip("0") in plist and t.split(":")[1] in plist
                               for t in ["09:00", "11:00", "17:30", "21:30"]),
        "times": times,
    }


def _day_strip_state() -> dict:
    now = datetime.now(_RIYADH)
    today = now.date()
    today_events = [(p, _hm_on(now, p["time"])) for p in _DAY_STRIP_PHASES]
    tomorrow_base = now + timedelta(days=1)
    yesterday_base = now - timedelta(days=1)
    future = [(p, dt) for p, dt in today_events if dt > now]
    if future:
        next_phase, next_dt = future[0]
    else:
        next_phase, next_dt = _DAY_STRIP_PHASES[0], _hm_on(tomorrow_base, _DAY_STRIP_PHASES[0]["time"])
    past = [(p, dt) for p, dt in today_events if dt <= now]
    if past:
        current_phase, current_dt = past[-1]
    else:
        current_phase, current_dt = _DAY_STRIP_PHASES[-1], _hm_on(yesterday_base, _DAY_STRIP_PHASES[-1]["time"])
    rows = []
    for p, dt in today_events:
        if p["id"] == current_phase["id"]:
            state = "current"
        elif dt < now:
            state = "done"
        elif p["id"] == next_phase["id"] and next_dt.date() == today:
            state = "next"
        else:
            state = "upcoming"
        rows.append({**p, "state": state})
    return {
        "ok": True,
        "tz": "Asia/Riyadh",
        "now": now.isoformat(timespec="seconds"),
        "date": now.strftime("%Y-%m-%d"),
        "current": {**current_phase, "since": current_dt.isoformat(timespec="seconds")},
        "next": {**next_phase, "at": next_dt.isoformat(timespec="seconds"),
                 "eta_seconds": max(0, int((next_dt - now).total_seconds())),
                 "eta": _human_eta((next_dt - now).total_seconds())},
        "phases": rows,
        "source_files": [
            "book/07-DAILY-CYCLE.md",
            "tools/jail/daily_cycle.sh",
            "tools/headless/com.ogz.daily-cycle.plist",
        ],
        "source_check": _day_strip_source_check(),
    }


def _load_task(p: Path) -> dict:
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        d = {}
    tid = d.get("id") or p.stem.replace("task_", "")
    d["_id"] = tid
    d["_mtime"] = p.stat().st_mtime if p.exists() else 0
    return d


def _queue_bucket(root: Path, state: str) -> dict:
    if state == "claimed":
        files = sorted((root / "claimed").glob("*/*.json"))
    else:
        files = sorted((root / state).glob("task_*.json"))
    by_lane: dict[str, int] = {}
    recent = []
    for p in files:
        d = _load_task(p)
        lane = d.get("lane") or (p.parent.name if state == "claimed" else "unknown")
        by_lane[lane] = by_lane.get(lane, 0) + 1
        recent.append({
            "id": d.get("_id"), "lane": lane, "client": d.get("client", ""),
            "task_type": d.get("task_type", ""), "req": d.get("req", ""),
            "mtime": datetime.fromtimestamp(d.get("_mtime", 0)).isoformat(timespec="seconds"),
        })
    recent.sort(key=lambda x: x.get("mtime", ""), reverse=True)
    return {"count": len(files), "by_lane": by_lane, "recent": recent[:6]}


def _ledger_count(path: Path, tdy: str) -> dict:
    lines = [ln for ln in _safe_read(path).splitlines() if ln.strip()]
    today = 0
    for ln in lines:
        try:
            r = json.loads(ln)
            if str(r.get("ts", "")).startswith(tdy):
                today += 1
        except Exception:
            if tdy in ln:
                today += 1
    return {"total": len(lines), "today": today}


def _pipeline_river_state() -> dict:
    root = (Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT) / "queue"
    tdy = today_str()
    pending = _queue_bucket(root, "pending")
    claimed = _queue_bucket(root, "claimed")
    done = _queue_bucket(root, "done")
    parked = _queue_bucket(root, "parked")
    done_today = sum(1 for p in (root / "done").glob("task_*.json")
                     if datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d") == tdy)
    ledgers = {
        "health": _ledger_count(OGZ_ROOT / "ledgers" / "health.jsonl", tdy),
        "spend": _ledger_count(OGZ_ROOT / "ledgers" / "spend.jsonl", tdy),
        "drafts": _ledger_count(OGZ_ROOT / "ledgers" / "drafts.jsonl", tdy),
        "judgments": _ledger_count(OGZ_ROOT / "ledgers" / "judgments.jsonl", tdy),
    }
    counts = {
        "pending": pending["count"], "claimed": claimed["count"],
        "done_total": done["count"], "done_today": done_today, "parked": parked["count"],
        "ledger_rows_total": sum(v["total"] for v in ledgers.values()),
        "ledger_rows_today": sum(v["today"] for v in ledgers.values()),
    }
    return {
        "ok": True,
        "ts": datetime.now(_RIYADH).isoformat(timespec="seconds"),
        "counts": counts,
        "buckets": {"pending": pending, "claimed": claimed, "done": done, "parked": parked},
        "ledgers": ledgers,
        "source_paths": {
            "pending": "queue/pending/task_*.json",
            "claimed": "queue/claimed/*/task_*.json",
            "done": "queue/done/task_*.json",
            "parked": "queue/parked/task_*.json",
            "ledgers": "ledgers/{health,spend,drafts,judgments}.jsonl",
        },
    }


def _client_slug(raw: str) -> str:
    s = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(raw or "").strip())
    s = "-".join([p for p in s.split("-") if p])
    return s[:48] or "unknown"


def _client_from_card(it: dict) -> tuple[str, str]:
    raw = it.get("handle") or it.get("client") or it.get("brand") or ""
    if not raw:
        ident = str(it.get("id") or "")
        title = str(it.get("title") or "")
        if ident.startswith("judge2_"):
            raw = ident[len("judge2_"):].split("_", 1)[0]
        elif ident.startswith("post_"):
            raw = ident[len("post_"):].split("__", 1)[0]
        elif ident.startswith("taste_kill_"):
            raw = "taste-kills"
        elif ident.startswith("closures_"):
            raw = "system-closures"
        elif ident.startswith("devs_"):
            raw = "dev-platform"
        elif ident.startswith("vision_"):
            raw = "compliance"
        elif "myfitness" in title.lower():
            raw = "myfitness.sa"
        elif ident.startswith("studio_"):
            tail = ident.replace("studio_", "", 1)
            parts = tail.split("-")
            raw = parts[3] if len(parts) > 3 else tail
        else:
            if "·" in title:
                parts = [p.strip() for p in title.split("·") if p.strip()]
                head = parts[0] if parts else ""
                raw = parts[-1] if head.lower().replace("🔴", "").strip() in {"live", "training"} else head
            else:
                raw = title.split()[0] if title else "unknown"
    slug = _client_slug(raw)
    label = str(raw).strip()[:42] or slug
    return slug, label


def _client_from_task(t: dict) -> tuple[str, str]:
    raw = t.get("client") or t.get("handle") or t.get("brand") or t.get("task_type") or "unknown"
    slug = _client_slug(raw)
    return slug, str(raw).strip()[:42] or slug


def _control_clients_state() -> dict:
    clients: dict[str, dict] = {}

    def ensure(slug: str, label: str) -> dict:
        row = clients.setdefault(slug, {
            "id": slug, "label": label, "open_taps": 0, "judge_open": 0,
            "answered": 0, "pending": 0, "claimed": 0, "latest": "",
        })
        if label and (not row.get("label") or row["label"] == slug):
            row["label"] = label
        return row

    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
    for it in q.get("items", []):
        if it.get("status") == "superseded":
            continue
        slug, label = _client_from_card(it)
        row = ensure(slug, label)
        if it.get("status") == "answered":
            row["answered"] += 1
        else:
            row["open_taps"] += 1
            if it.get("kind") == "caption_judge" or str(it.get("id", "")).startswith(("post_", "studio_")):
                row["judge_open"] += 1
        row["latest"] = max(row.get("latest", ""), str(it.get("created") or ""))

    root = Path(os.environ["OGZ_JAIL_ROOT"]) if os.environ.get("OGZ_JAIL_ROOT") else OGZ_ROOT
    for state in ("pending", "claimed"):
        files = sorted((root / "claimed").glob("*/*.json")) if state == "claimed" else sorted((root / "pending").glob("task_*.json"))
        for p in files:
            t = _load_task(p)
            slug, label = _client_from_task(t)
            row = ensure(slug, label)
            row[state] += 1
            row["latest"] = max(row.get("latest", ""), datetime.fromtimestamp(t.get("_mtime", 0)).isoformat(timespec="seconds"))

    rows = sorted(clients.values(), key=lambda x: (-(x["open_taps"] + x["claimed"] + x["pending"]), x["label"].lower()))
    totals = {
        "clients": len(rows),
        "open_taps": sum(r["open_taps"] for r in rows),
        "judge_open": sum(r["judge_open"] for r in rows),
        "answered": sum(r["answered"] for r in rows),
        "pending": sum(r["pending"] for r in rows),
        "claimed": sum(r["claimed"] for r in rows),
    }
    return {"ok": True, "totals": totals, "clients": rows[:80],
            "source_paths": ["data/decision_queue.json", "queue/pending/task_*.json", "queue/claimed/*/task_*.json"],
            "ts": datetime.now(_RIYADH).isoformat(timespec="seconds")}


@app.get("/api/control/ranked-taps")
def control_ranked_taps(k: str = ""):
    """Read-only Focus Lane selector. It ranks Mohamed-only gates from NEEDS-MOHAMED
    plus actionable decision_queue cards; writes stay on the existing dashboard/answer path."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    needs_rows, needs_n = _needs_ranked_taps()
    decision_rows, decision_n = _decision_ranked_taps()
    rows = sorted(needs_rows + decision_rows, key=_ranked_taps_score)[:3]
    for i, row in enumerate(rows):
        row["recommended"] = (i == 0)
    return JSONResponse({"ok": True,
                         "source_counts": {"needs_open": needs_n, "decision_open": decision_n},
                         "items": rows,
                         "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")},
                        headers={"Cache-Control": "private, no-cache"})


@app.get("/api/control/day-strip")
def control_day_strip(k: str = ""):
    """Read-only daily ritual state for /control. Source of truth is book/07 +
    daily_cycle.sh + the launchd calendar; the UI only renders this calculation."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    return JSONResponse(_day_strip_state(), headers={"Cache-Control": "private, no-cache"})


@app.get("/api/control/pipeline-river")
def control_pipeline_river(k: str = ""):
    """Read-only queue/ledger river for /control. Every number is counted from disk;
    no sample jobs, no fabricated animation state."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    return JSONResponse(_pipeline_river_state(), headers={"Cache-Control": "private, no-cache"})


@app.get("/api/control/clients")
def control_clients(k: str = ""):
    """Read-only client rail summary for /control. Derived from decision_queue
    and queue claims; it scopes the UI without changing the underlying write paths."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    return JSONResponse(_control_clients_state(), headers={"Cache-Control": "private, no-cache"})


@app.get("/api/control/gauntlet-today")
def control_gauntlet_today(k: str = ""):
    """SPEC-C: per-draft view of today's gauntlet — each draft joined to its newest judgment.
    Reads ledgers/drafts.jsonl + ledgers/judgments.jsonl only; verdict spine schema unchanged."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    tdy = today_str()
    # index today's drafts by job_id (last row wins for duplicate job_ids)
    drafts: dict = {}
    draft_order: list = []
    for ln in _safe_read(OGZ_ROOT / "ledgers" / "drafts.jsonl").splitlines():
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if not str(r.get("ts", "")).startswith(tdy):
            continue
        jid = r.get("job_id", "")
        if not jid:
            continue
        if jid not in drafts:
            draft_order.append(jid)
        drafts[jid] = r
    # index today's judgments by job_id; append-only → last row = newest judgment
    judgments: dict = {}
    for ln in _safe_read(OGZ_ROOT / "ledgers" / "judgments.jsonl").splitlines():
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if not str(r.get("ts", "")).startswith(tdy):
            continue
        jid = r.get("job_id", "")
        if jid:
            judgments[jid] = r
    # join drafts → judgments
    total_pass = total_kill = total_unjudged = 0
    result_drafts = []
    for jid in draft_order:
        dr = drafts[jid]
        jd = judgments.get(jid)
        verdict = jd.get("verdict") if jd else None
        if verdict == "pass":
            total_pass += 1
        elif verdict == "kill":
            total_kill += 1
        else:
            total_unjudged += 1
        result_drafts.append({
            "job_id": jid,
            "handle": dr.get("handle", "?"),
            "draft_path": dr.get("draft_path", ""),
            "ts": dr.get("ts", ""),
            "judgment": {
                "verdict": jd.get("verdict"),
                "overall": jd.get("overall"),
                "reasons": jd.get("reasons") or [],
                "usd": jd.get("usd"),
            } if jd else None,
        })
    return JSONResponse({
        "ok": True,
        "date": tdy,
        "drafts": result_drafts,
        "summary": {"total": len(result_drafts), "pass": total_pass,
                    "kill": total_kill, "unjudged": total_unjudged},
    })


# ---- THE SYSTEM ASSISTANT CHAT (July 4 — Mohamed: "talk to the system on everything") ----
CHAT_F = DATA_ROOT / "data" / "control_chat.jsonl"


def _env(key: str):
    p = Path.home() / ".abraham_env"
    if not p.exists():
        return None
    import re as _re
    for ln in p.read_text().splitlines():
        ln = _re.sub(r"^export\s+", "", ln.strip())
        if ln.startswith(key + "="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def _control_snapshot() -> str:
    """A compact, TRUE snapshot of the live system for the assistant's grounding — read
    straight off the same ledgers the control views use (no fabrication)."""
    L = []
    # agents
    try:
        buckets = {"working": [], "recent": [], "idle": []}
        for mid, name, room, rel, reports, what in _MINDS:
            mt = (OGZ_ROOT / rel / "memory.md").stat().st_mtime if (OGZ_ROOT / rel / "memory.md").exists() else 0
            buckets.setdefault(_age_status(mt), []).append(name)
        L.append(f"AGENTS: 4 core + 12 minds. working={buckets.get('working',[])} recent={len(buckets.get('recent',[]))} idle={len(buckets.get('idle',[]))}.")
    except Exception:
        pass
    # pipeline
    try:
        rows = [json.loads(x) for x in _safe_read(OGZ_ROOT / "journal/model_usage.jsonl").splitlines()[-8:] if x.strip()]
        last = rows[-1] if rows else {}
        hb = _hb_lines(3)
        L.append(f"PIPELINE: stage={last.get('capability')} model={last.get('model')} last={last.get('ts')}. "
                 f"heartbeat: " + " | ".join(f"{h.get('time')} {h.get('msg')}" for h in hb))
    except Exception:
        pass
    # budget
    try:
        tdy = today_str()
        tu = mu = 0.0
        for x in _safe_read(OGZ_ROOT / "journal/model_usage.jsonl").splitlines():
            try:
                r = json.loads(x)
            except Exception:
                continue
            if not r.get("provider"):
                continue
            u = float(r.get("usd") or 0)
            if str(r.get("ts", ""))[:10] == tdy:
                tu += u
            if str(r.get("ts", ""))[:7] == tdy[:7]:
                mu += u
        L.append(f"BUDGET: today=${tu:.3f} month=${mu:.3f} (caps from model_router.json).")
    except Exception:
        pass
    # review queue
    try:
        q = json.loads(_safe_read(QUEUE) or '{"items":[]}')
        items = q.get("items", []) if isinstance(q, dict) else q
        openn = sum(1 for it in items if it.get("status") != "answered")
        L.append(f"REVIEW: {openn} open cards (of {len(items)}).")
    except Exception:
        pass
    # health (lite — no subprocess to stay fast for chat)
    try:
        hbf = OGZ_ROOT / "journal/heartbeat.md"
        fresh = int(datetime.now().timestamp() - hbf.stat().st_mtime) if hbf.exists() else None
        L.append(f"HEALTH: heartbeat {fresh}s old; portal+brain serving.")
    except Exception:
        pass
    return "\n".join(L)


def _knowhow_retrieve(q: str) -> str:
    """Query the brain's know-how + Alhareth engineering know-how (the same /know-how, /alhareth
    endpoints the platform exposes) so the assistant is grounded in the real corpus."""
    import urllib.request
    out = []
    for path, label in (("/know-how", "MOHAMED KNOW-HOW"), ("/alhareth", "ALHARETH ENG")):
        try:
            rq = urllib.request.Request("http://127.0.0.1:4140" + path,
                                        data=json.dumps({"q": q, "top_k": 4}).encode(),
                                        headers={"Content-Type": "application/json"})
            d = json.loads(urllib.request.urlopen(rq, timeout=12).read())
            for h in (d.get("hits") or [])[:4]:
                out.append(f"[{label} · {h.get('source','')}] {str(h.get('text',''))[:280]}")
        except Exception:
            continue
    return "\n".join(out) if out else "(no know-how hits for this query)"


def _chat_history(session: str, n=40):
    rows = []
    for ln in _safe_read(CHAT_F).splitlines()[-200:]:
        try:
            e = json.loads(ln)
        except Exception:
            continue
        if e.get("session") == session:
            rows.append(e)
    return rows[-n:]


@app.get("/api/control/chat/history")
def chat_history(session: str = "mohamed", k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    return JSONResponse({"ok": True, "turns": _chat_history(session)})


@app.post("/api/control/chat")
async def chat(request: Request, k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    msg = str(body.get("message", "")).strip()[:2000]
    session = str(body.get("session", "mohamed"))[:40]
    if not msg:
        return JSONResponse({"ok": False, "error": "empty message"}, status_code=400)
    judge, _ = _resolve_judge(k)
    # persist the user turn FIRST (append-only; survives even if the model call fails)
    with open(CHAT_F, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                            "role": "user", "text": msg, "session": session,
                            "by": judge or "shared"}, ensure_ascii=False) + "\n")
    key = _env("OPENAI_API_KEY")
    if not key:
        return JSONResponse({"ok": False, "error": "no OPENAI_API_KEY on the box"}, status_code=503)
    snapshot = _control_snapshot()
    know = _knowhow_retrieve(msg)
    system = (
        "You are the OGZ SYSTEM ASSISTANT — the voice of Mohamed's autonomous studio, speaking from "
        "inside the OGZ brain. You are grounded ONLY in the real system state and know-how given below; "
        "never invent numbers, agents, or facts — if it is not in the context, say you don't see it. "
        "You COMPLEMENT Mohamed's Dispatch chat with Claude Code (the operator that actually builds/changes "
        "things); you answer questions about what's happening and note simple requests, but you do NOT execute "
        "changes yourself. Be concise, concrete, honest. Mohamed has ADHD — lead with the answer, short. "
        "Arabic or English, follow his language.\n\n"
        f"=== LIVE SYSTEM STATE ===\n{snapshot}\n\n=== RELEVANT KNOW-HOW (retrieved) ===\n{know}\n\n"
        "If he asks you to DO something beyond answering, tell him plainly you've logged it for the operator "
        "(Claude Code) and what you understood — you don't change the system yourself.")
    hist = _chat_history(session, n=8)
    messages = [{"role": "system", "content": system}]
    for t in hist:
        if t.get("role") in ("user", "assistant"):
            messages.append({"role": t["role"], "content": str(t.get("text", ""))[:1500]})
    messages.append({"role": "user", "content": msg})
    import urllib.request
    answer, usage = None, {}
    try:
        rq = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 700,
                             "messages": messages}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        out = json.loads(urllib.request.urlopen(rq, timeout=60).read())
        answer = out["choices"][0]["message"]["content"].strip()
        usage = out.get("usage", {})
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"gpt-4o: {type(e).__name__}: {str(e)[:160]}"}, status_code=502)
    # meter to the CFO ledger so the Budget view stays honest (control_chat capability)
    try:
        it, ot = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        usd = it / 1e6 * 0.15 + ot / 1e6 * 0.6
        with open(OGZ_ROOT / "journal/model_usage.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "capability": "control_chat", "provider": "openai", "model": "gpt-4o-mini",
                                "in_tokens": it, "out_tokens": ot, "usd": round(usd, 6),
                                "flags": ["control_center"], "purpose": "system assistant"}) + "\n")
    except Exception:
        pass
    with open(CHAT_F, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                            "role": "assistant", "text": answer, "session": session},
                           ensure_ascii=False) + "\n")
    _touch_sync()
    return JSONResponse({"ok": True, "answer": answer})


# ---- PER-AGENT CHAT (July 4 — Mohamed: a chat for EVERY agent, grounded in ITS own context) ----
AGENT_CHAT_DIR = DATA_ROOT / "data" / "agent_chat"
# id -> (name, role/what, home rel). Built from the same rosters the Agents view uses.
_CORE_WF_FALLBACK = {
    "proposal": ["Receive the RFP/brief + past learnings", "Council sets direction + price",
                 "Writers' room drafts", "CCO gate → review-queue → Mohamed"],
    "client-intel": ["Watch inbox + client bibles", "Pull market intel on demand",
                     "Draft BD outreach", "Hand the brief to the council"],
    "knowledge": ["Index + embed the corpus", "Serve know-how to every mind",
                  "Capture new learnings", "Keep the taste-moat current"],
    "design": ["Read the CD route + tokens", "Lay out image-first slides/deck",
               "Self-audit vs the visual rules", "Render + hand off"],
}


def _agent_lookup(aid: str):
    for mid, name, room, rel, reports, what in _MINDS:
        if mid == aid:
            return name, what, rel
    for cid, name, rel, what, children in _CORE:
        if cid == aid:
            return name, what, rel
    return None


def _agent_memory_info(rel: str):
    mem = OGZ_ROOT / rel / "memory.md"
    if not mem.exists():
        return {"exists": False, "path": rel + "/memory.md"}
    txt = _safe_read(mem)
    _h, body = _last_entry(mem)
    return {"exists": True, "path": rel + "/memory.md", "mtime": int(mem.stat().st_mtime),
            "lines": len(txt.splitlines()), "last_entry": (body or _h or "")[:180]}


def _agent_context(aid: str):
    """The agent's OWN grounding: role, its numbered workflow, and the tail of its memory."""
    look = _agent_lookup(aid)
    if not look:
        return None
    name, what, rel = look
    steps = _workflow_steps(rel) or _CORE_WF_FALLBACK.get(aid, [])
    wf_src = "WORKFLOW.md" if (OGZ_ROOT / rel / "WORKFLOW.md").exists() else (
        "AGENT.md Method" if _method_steps(_safe_read(OGZ_ROOT / rel / "AGENT.md")) else "core-fallback")
    mem_tail = _safe_read(OGZ_ROOT / rel / "memory.md")[-1800:]
    return {"name": name, "what": what, "rel": rel, "steps": steps,
            "wf_src": wf_src, "mem_tail": mem_tail}


def _agent_chat_file(aid: str) -> Path:
    safe = "".join(c for c in aid if c.isalnum() or c in "_-")
    return AGENT_CHAT_DIR / (safe + ".jsonl")


def _agent_chat_history(aid: str, n=40):
    f = _agent_chat_file(aid)
    rows = []
    for ln in _safe_read(f).splitlines()[-200:]:
        try:
            rows.append(json.loads(ln))
        except Exception:
            continue
    return rows[-n:]


@app.get("/api/control/agent-chat/history")
def agent_chat_history(agent: str = "", k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    if not _agent_lookup(agent):
        return JSONResponse({"ok": False, "error": "unknown agent"}, status_code=404)
    return JSONResponse({"ok": True, "agent": agent, "turns": _agent_chat_history(agent)})


@app.post("/api/control/agent-chat")
async def agent_chat(request: Request, k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    aid = str(body.get("agent", "")).strip()
    msg = str(body.get("message", "")).strip()[:2000]
    ctx = _agent_context(aid)
    if not ctx:
        return JSONResponse({"ok": False, "error": "unknown agent"}, status_code=404)
    if not msg:
        return JSONResponse({"ok": False, "error": "empty message"}, status_code=400)
    judge, _ = _resolve_judge(k)
    AGENT_CHAT_DIR.mkdir(parents=True, exist_ok=True)
    cf = _agent_chat_file(aid)
    # READ-BEFORE is ctx (its memory + workflow); WRITE-AFTER starts with the user turn (append-only)
    with open(cf, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "role": "user",
                            "text": msg, "by": judge or "shared"}, ensure_ascii=False) + "\n")
    key = _env("OPENAI_API_KEY")
    if not key:
        return JSONResponse({"ok": False, "error": "no OPENAI_API_KEY on the box"}, status_code=503)
    know = _knowhow_retrieve(msg)
    steps_txt = "\n".join(f"{i+1}. {s}" for i, s in enumerate(ctx["steps"])) or "(no steps documented)"
    system = (
        f"You ARE the OGZ '{ctx['name']}' agent — speaking in the first person as this specific agent inside "
        f"Mohamed's autonomous studio. Your job: {ctx['what']}.\n"
        f"You are grounded ONLY in YOUR OWN workflow, YOUR OWN memory, and the retrieved know-how below — never "
        f"invent facts, numbers, or steps you don't see. If asked about something outside your lane, say which "
        f"agent owns it. You run LOCALLY on the brain and read the shared know-how base every cycle.\n\n"
        f"=== YOUR WORKFLOW (the steps you follow) ===\n{steps_txt}\n\n"
        f"=== YOUR MEMORY (your dated lessons/verdicts, append-only) ===\n{ctx['mem_tail'] or '(memory empty)'}\n\n"
        f"=== RELEVANT KNOW-HOW (retrieved from the brain for this question) ===\n{know}\n\n"
        f"Answer AS this agent: concise, concrete, honest, grounded in the above. Mohamed has ADHD — lead with "
        f"the answer. Arabic or English, follow his language. You don't change the system yourself — you explain "
        f"your work and note requests for the operator (Claude Code).")
    hist = _agent_chat_history(aid, n=8)
    messages = [{"role": "system", "content": system}]
    for t in hist:
        if t.get("role") in ("user", "assistant"):
            messages.append({"role": t["role"], "content": str(t.get("text", ""))[:1500]})
    messages.append({"role": "user", "content": msg})
    import urllib.request
    answer, usage = None, {}
    try:
        rq = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps({"model": "gpt-4o-mini", "temperature": 0.3, "max_tokens": 700,
                             "messages": messages}).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        out = json.loads(urllib.request.urlopen(rq, timeout=60).read())
        answer = out["choices"][0]["message"]["content"].strip()
        usage = out.get("usage", {})
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"gpt-4o: {type(e).__name__}: {str(e)[:160]}"}, status_code=502)
    try:
        it, ot = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        usd = it / 1e6 * 0.15 + ot / 1e6 * 0.6
        with open(OGZ_ROOT / "journal/model_usage.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "capability": "agent_chat", "provider": "openai", "model": "gpt-4o-mini",
                                "in_tokens": it, "out_tokens": ot, "usd": round(usd, 6),
                                "flags": ["control_center", aid], "purpose": f"chat as {aid}"}) + "\n")
    except Exception:
        pass
    with open(cf, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"), "role": "assistant",
                            "text": answer}, ensure_ascii=False) + "\n")
    _touch_sync()   # Mohamed chatted with an agent → mirror it for the coordinator
    return JSONResponse({"ok": True, "agent": aid, "answer": answer})


@app.get("/api/control/agent-wiring")
def agent_wiring(k: str = ""):
    """PART B — the memory+wiring proof map: for EVERY agent, does it have its own memory
    (read-before / write-after), does it read its workflow, is it wired to the brain/know-how.
    All fields are evidenced from real files; gaps are stated plainly."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    rows = []
    order = [("core", c[0]) for c in _CORE] + [("mind", m[0]) for m in _MINDS]
    for kind, aid in order:
        look = _agent_lookup(aid)
        if not look:
            continue
        name, what, rel = look
        mem = _agent_memory_info(rel)
        steps = _workflow_steps(rel) or _CORE_WF_FALLBACK.get(aid, [])
        wf_src = "WORKFLOW.md" if (OGZ_ROOT / rel / "WORKFLOW.md").exists() else (
            "AGENT.md Method" if _method_steps(_safe_read(OGZ_ROOT / rel / "AGENT.md")) else
            ("core-fallback" if steps else "none"))
        chist = _agent_chat_history(aid, n=500)
        gaps = []
        if not mem["exists"]:
            gaps.append("no own memory.md")
        if not steps:
            gaps.append("no workflow")
        rows.append({
            "id": aid, "kind": kind, "name": name, "home": rel,
            "own_memory": mem["exists"], "memory_path": mem.get("path"),
            "memory_lines": mem.get("lines"), "memory_mtime": mem.get("mtime"),
            "memory_last": mem.get("last_entry"),
            "reads_workflow": bool(steps), "workflow_source": wf_src, "workflow_steps": len(steps),
            "knowhow_wired": True,   # constitutional (MINDS.md) + the chat retrieves /know-how + /alhareth
            "read_before": mem["exists"] and bool(steps),   # chat loads memory + workflow before answering
            "write_after": True,     # chat appends every turn to data/agent_chat/<id>.jsonl
            "chat_turns": len(chist),
            "connected": not gaps, "gaps": gaps,
        })
    return JSONResponse({"ok": True, "agents": rows,
                         "summary": {"total": len(rows),
                                     "connected": sum(1 for r in rows if r["connected"]),
                                     "with_memory": sum(1 for r in rows if r["own_memory"]),
                                     "with_workflow": sum(1 for r in rows if r["reads_workflow"])}})


# ---- COORDINATOR SYNC LAYER (July 4 — Mohamed: the coordinator always mirrors agent state) ----
import sys as _sys_sync
_sys_sync.path.insert(0, str(OGZ_ROOT / "tools"))


def _touch_sync():
    """Refresh the coordinator mirror (journal/SYNC.md) — best-effort, never breaks the caller."""
    try:
        import sync_build
        sync_build.write()
    except Exception:
        pass


@app.get("/sync")
def sync_view(k: str = ""):
    """The coordinator's live state mirror — refreshed on read (always current), served as the
    same SYNC.md the Dispatch coordinator reads on every Mohamed message. Same key gate."""
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    md = ""
    try:
        import sync_build
        md = sync_build.write()          # refresh-on-read → always current
    except Exception:
        md = _safe_read(OGZ_ROOT / "journal/SYNC.md")
    return Response(content=md or "(sync unavailable)",
                    media_type="text/markdown; charset=utf-8",
                    headers={"Cache-Control": "no-store"})


@app.get("/api/approvals/whoami")
def whoami(k: str = ""):
    """Per-judge key → fixed identity (no picker). Shared key → roster picker."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    judge, auth = _resolve_judge(k)
    return {"members": _team().get("members", []), "judge": judge, "auth": auth}


@app.get("/api/approvals/reasons")
def reasons(k: str = ""):
    """The optional reason-chip vocabulary (closed, never mandatory)."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    f = REPO / "data" / "reason_codes.json"
    return json.loads(f.read_text()) if f.exists() else {"codes": []}


@app.get("/api/approvals/scorecards")
def scorecards(k: str = ""):
    """READ-ONLY players view — rendered 100% from the derived file."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    sc = json.loads(SCORECARDS_F.read_text()) if SCORECARDS_F.exists() else {"players": {}}
    bench_f = REPO / "data" / "bench.json"
    issues_f = REPO / "data" / "issues_state.json"
    return {"scorecards": sc,
            "bench": json.loads(bench_f.read_text()) if bench_f.exists() else {},
            "issues": json.loads(issues_f.read_text()) if issues_f.exists() else {"open_count": 0}}


SLIM_KEYS = ("id", "title", "status", "answered", "answered_by", "created", "tag")


def _single_open_pw(out):
    """Of the OPEN pairwise (pw_) cards, surface only ONE — the rest stay queued and surface one
    after each tap. The one shown is the HIGHEST-VALUE open card: lowest `pw_rank` (bridge=0 unlocks
    held-out testability, active=1 information gain, random=2), ties broken by earliest `created`
    (out arrives already created-sorted, so stable-min picks the oldest among equals). ALL non-pw
    open cards and ALL answered cards pass through untouched. Derived purely from queue state, so the
    ETag (queue mtime) stays valid: answering a pw_ rewrites the queue → mtime bumps → the next-best
    pw_ appears on the next poll. Born June 16 as a no-flood gate (15 stacked cards = a wall vs the
    ADHD 60-sec contract); June 18 it also honors the producer's ranking (Rule #6 — created-order
    threw away the active/bridge information-gain the selectors computed, wasting his scarce taps)."""
    open_pw = [it for it in out
               if str(it.get("id", "")).startswith("pw_") and it.get("status") != "answered"]
    if not open_pw:
        return out
    winner = min(open_pw, key=lambda it: (it.get("pw_rank", 2), it.get("created") or ""))  # rank, then earliest created
    kept = []
    for it in out:
        if (str(it.get("id", "")).startswith("pw_") and it.get("status") != "answered"
                and it is not winner):
            continue                # withhold — only the single highest-value pw_ card surfaces
        kept.append(it)
    return kept


def _bucket(it: dict) -> str:
    """FEEDBACK RE-LOOK (June 29, orchestra): 3 buckets for the 60-sec ADHD gate —
    'alarm' (urgent flags), 'decision' (Mohamed can ACT), 'info' (no action: client-needs).
    DeepSeek-verify fix: prefer the EXPLICIT action_type the pusher stamps (deterministic) — the
    field-presence inference below is only a legacy fallback (a label-only `text` would misfire)."""
    bt = it.get("action_type")
    if bt in ("alarm", "decision", "info"):
        return bt
    # a judge-lane card IS a decision — Mohamed can ACT on it (July 2 fix: the legacy
    # field-presence inference filed 'training ·' proposal cards as no-action info and
    # COLLAPSED them off the dashboard, while '🔴 LIVE' siblings matched the alarm emoji)
    if it.get("kind") in ("proposal_judge", "caption_judge"):
        return "decision"
    txt = f"{it.get('title','')} {it.get('tag','')} {it.get('id','')}"
    if any(e in txt for e in ("🚨", "🔴", "alarm", "إنذار", "taste_stale")):
        return "alarm"
    return "decision" if (it.get("buttons") or it.get("options") or it.get("text") or it.get("composer")) else "info"


@app.get("/api/approvals/items")
def items(request: Request, k: str = ""):
    if not _ok(k):
        return JSONResponse([], status_code=403)
    # ETag from the queue file mtime+size: unchanged queue → 304, zero payload (polling diet)
    if QUEUE.exists():
        st = QUEUE.stat()
        etag = f'W/"{int(st.st_mtime)}-{st.st_size}"'
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers={"ETag": etag})
    else:
        etag = 'W/"empty"'
    lm = _lane_map()
    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
    out = []
    for it in q["items"]:
        if it.get("status") == "superseded":
            continue                                            # hidden: a newer version replaced it
        if it.get("status") == "answered":
            out.append({kk: it.get(kk) for kk in SLIM_KEYS})   # answered = slim (payload diet)
        else:
            out.append(dict(it, lane=_card_lane(it, lm), bucket=_bucket(it)))
    # coerce None → "" : a card with created:null (or a slim answered dict missing it) crashed
    # the sort (None < str) → the WHOLE items API 500'd → the live link showed no cards (2026-06-14)
    # FEEDBACK RE-LOOK (June 29, orchestra): bucket order first — 🚨 alarms, ✅ decisions, 📋 info —
    # so the actionable cards surface and the no-action client-needs sink (the flood fix).
    _BORDER = {"alarm": 0, "decision": 1, "info": 2}
    out.sort(key=lambda x: (x.get("status") == "answered",
                            _BORDER.get(x.get("bucket"), 1),
                            0 if x.get("priority") == "urgent" else 1, x.get("created") or ""))
    # collapse ALL no-action INFO cards behind "view all" (Rule #10 — the flood is the no-action
    # client-needs; alarms + decisions stay open because they need Mohamed's tap).
    for x in out:
        if x.get("status") != "answered" and x.get("bucket") == "info":
            x["collapsed"] = True
    out = _single_open_pw(out)   # one open pairwise card at a time (60-sec gate, not a 15-card wall)
    # private,no-cache makes the browser attach If-None-Match automatically → free 304 polling
    return JSONResponse(out, headers={"ETag": etag, "Cache-Control": "private, no-cache"})


@app.get("/api/approvals/team")
def team(k: str = ""):
    """The aggregated human-truth view: every teammate's verdict, attributed."""
    if not _ok(k):
        return JSONResponse([], status_code=403)
    if not ANSWERS.exists():
        return []
    rows = []
    for line in ANSWERS.read_text().strip().split("\n"):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("judge") and e.get("judge") not in ("mohamed", ""):
            rows.append({"ts": e["ts"], "judge": e["judge"], "lane": e.get("lane"),
                         "item_id": e["item_id"], "answer": e["answer"],
                         "fix": e.get("fix", ""), "note": e.get("note", ""), "rating": e.get("rating")})
    return rows[-100:]


def _clamp_client_ts(raw):
    """client_ts bounded to [now-48h, now] — clock skew can't reorder streaks."""
    if not raw:
        return None, False
    try:
        ct = datetime.fromisoformat(str(raw))
    except Exception:
        return None, False
    now = datetime.now()
    if ct > now:
        return now.isoformat(timespec="seconds"), True
    if ct < now - timedelta(hours=48):
        return (now - timedelta(hours=48)).isoformat(timespec="seconds"), True
    return ct.isoformat(timespec="seconds"), False


def _dedupe_hit(ledger: Path, client_ts, judge, item_id) -> bool:
    """(client_ts, judge, item_id) replay → drop silently (offline double-flush)."""
    if not (client_ts and ledger.exists()):
        return False
    tail = ledger.read_text().splitlines()[-200:]
    for line in tail:
        try:
            e = json.loads(line)
        except Exception:
            continue
        if (e.get("client_ts") == client_ts and e.get("judge") == judge
                and e.get("item_id") == item_id):
            return True
    return False


@app.post("/api/approvals/answer")
async def answer(request: Request, k: str = ""):
    body = await request.json()
    judge, auth = _resolve_judge(k)
    members = {m["id"]: m for m in _team().get("members", [])}
    legacy_write = _keys().get("legacy_write", True)
    if auth == "shared" and legacy_write:
        # honest transition: judge from the in-app picker, row flagged auth:'shared'.
        # NEVER defaults to mohamed — an unknown picker value quarantines.
        judge = body.get("judge") if body.get("judge") in members else None
    quarantine = (auth == "none") or (judge is None) or (auth == "shared" and not legacy_write)

    client_ts, skewed = _clamp_client_ts(body.get("client_ts"))
    # validate optional target against the grammar — invalid targets are dropped, never guessed
    target = body.get("target")
    if target:
        import sys as _s
        _s.path.insert(0, str(REPO / "scripts"))
        from feedback_lib import validate_target
        if not validate_target(str(target)):
            target = None
    # ELEMENT COMMENTS (July 2, DeepSeek consult feedback-dashboard-ux: ONE row + comments[]
    # array — never N rows, so the byte-cursor consumers see one answer processed once).
    # Each comment pins a sub-element: ref (stable selector, e.g. slide:2/blk:4), the quoted
    # text (agent context — survives regeneration), quote_hash (drift detection vs
    # artifact_version), el_kind (drives studio-side mind routing), text (the comment itself).
    _EL_KINDS = {"copy", "price", "visual", "caption", "script", "strategy", "data", "idea"}
    comments = []
    for c in (body.get("comments") or [])[:20]:
        if not isinstance(c, dict) or not str(c.get("ref", "")).strip():
            continue
        comments.append({"ref": str(c["ref"])[:80],
                         "text": str(c.get("text", ""))[:500],
                         "quote": str(c.get("quote", ""))[:280],
                         "quote_hash": str(c.get("quote_hash", ""))[:64],
                         "el_kind": c.get("el_kind") if c.get("el_kind") in _EL_KINDS else "copy"})
    entry = {"schema_v": 3 if comments else 2,
             **({"comments": comments} if comments else {}),
             "ts": datetime.now().isoformat(timespec="seconds"),
             "client_ts": client_ts, **({"skewed": True} if skewed else {}),
             "item_id": body.get("item_id"), "answer": str(body.get("answer", ""))[:2000],
             "note": str(body.get("note", ""))[:2000],
             "fix": str(body.get("fix", ""))[:3000],          # the correction itself (human truth)
             "rating": body.get("rating") if isinstance(body.get("rating"), int) else None,
             "judge": judge or "unverified", "auth": auth if not quarantine else "none",
             "lane": members.get(judge or "", {}).get("lane", "all"),
             "target": target, "artifact_id": body.get("artifact_id"),
             "artifact_version": body.get("artifact_version") if isinstance(body.get("artifact_version"), int) else None,
             "reason_codes": [str(c)[:40] for c in (body.get("reason_codes") or [])][:3],
             "in_reply_to": body.get("in_reply_to"),
             "source": body.get("source") if body.get("source") in ("team_portal", "after_strip", "flag_sheet", "dashboard") else "team_portal"}
    if quarantine:
        with open(UNVERIFIED, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return JSONResponse({"ok": False, "quarantined": True}, status_code=403)
    if _dedupe_hit(ANSWERS, client_ts, judge, entry["item_id"]):
        return {"ok": True, "deduped": True}
    # repudiation («مو أنا»): server fills in_reply_to from this judge's previous row
    if entry["item_id"] == "_repudiation" and ANSWERS.exists():
        for line in reversed(ANSWERS.read_text().splitlines()[-200:]):
            try:
                prev = json.loads(line)
            except Exception:
                continue
            if prev.get("judge") == judge and prev.get("item_id") != "_repudiation":
                entry["in_reply_to"] = f"{prev.get('ts')}+{prev.get('item_id')}"
                break
    with open(ANSWERS, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    picked_card = None
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text())
        for it in q["items"]:
            if it["id"] == entry["item_id"]:
                it["status"] = "answered"
                it["answered"] = entry["answer"][:60]
                it["answered_by"] = judge
                if entry["fix"]:
                    it["human_fix"] = entry["fix"][:200]
                picked_card = it
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    # REAL-TIME LEARNING LOOP (Mohamed, July 5): a studio_ proposal verdict feeds the agent's
    # memory IMMEDIATELY (Rule #14 write-after made live, not session-start). Non-blocking Popen
    # so the tap response is never delayed; proposal_memory --ingest is idempotent + append-only.
    if str(entry["item_id"]).startswith("studio_"):
        try:
            import subprocess as _sp, sys as _s3
            _sp.Popen([_s3.executable, str(OGZ_ROOT / "tools" / "proposal_memory.py"), "--ingest"],
                      stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
        except Exception:
            pass   # the learning wire never fails the tap
    # the routing receipt — same classifier the router/end-screen use (no drift)
    import sys as _s2
    _s2.path.insert(0, str(REPO / "scripts"))
    from feedback_lib import classify_receipt
    resp = {"ok": True, "receipt": classify_receipt(entry)}
    # POST-PICK WRITER (B180): a post_pick tap is a trust-moving human pick — record it as a
    # pick_selected client event so trust_ladder + approvers_registry (the readers) receive it.
    # Without this the post_pick wire is severed (Rule #6). Gated to pick_ ids; never fails the tap.
    if str(entry["item_id"]).startswith("pick_") and picked_card is not None:
        try:
            import build_pick_item as _bpi
            if _bpi.record_pick(picked_card, entry["answer"], judge):
                resp["pick_recorded"] = True
        except Exception:
            pass   # the wire is a nicety on the response — never fail the tap on it
    # INSTANT TASTE FEEDBACK for a pairwise pick (June 16): consume this fresh tap → recompute the
    # Mohamed-Elo (pure-numpy, instant, zero-key) → surface the honest nudge. pw_-gated so the shared
    # classify_receipt is never touched. Makes the tap feel like it landed, not like a survey.
    if str(entry["item_id"]).startswith("pw_"):
        try:
            import pairwise as _pw, taste_elo as _te
            _pw.consume(); _te.main()
            _tj = json.loads((DATA_ROOT / "data" / "taste_elo.json").read_text())
            if _tj.get("last_pick_feedback"):
                resp["taste"] = _tj["last_pick_feedback"]
        except Exception:
            pass   # feedback is a nicety — never fail the tap on it
    _touch_sync()   # a verdict landed → mirror it for the coordinator
    return resp


@app.get("/api/approvals/receipt")
def receipt(k: str = "", since: str = ""):
    """END SCREEN — 'Your taste, applied'. Runs the fold pipeline (router → gold →
    scorecards) under the file lock, then returns the LEDGER DIFF by RE-READING the
    files the mutators just wrote (ASSERT law: post-write re-reads, never predictions)."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    import fcntl
    import sys as _s3
    _s3.path.insert(0, str(REPO / "scripts"))
    lock = open(DATA_ROOT / "data" / ".fold_lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        import feedback_router, gold_mint, scorecards as _sc
        feedback_router.process()
        minted = gold_mint.mint()
        try:
            import subprocess as _sp, sys as _sys
            _sp.run([_sys.executable, str(REPO / "scripts/apply_rulings.py")],
                    capture_output=True, timeout=60)
        except Exception:
            pass  # make_sure_feedback red-flags unapplied rulings — never crash the receipt
        _sc.write_all()
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()
    from feedback_lib import read_jsonl as _rj
    since = since or "1970"
    rows = [r for r in _rj(ANSWERS) if (r.get("client_ts") or r.get("ts", "")) >= since
            and r.get("judge") not in ("", "unverified")]
    tally = {"judged": 0, "approved": 0, "rejected": 0, "corrected": 0}
    for r in rows:
        a = str(r.get("answer", "")).lower()
        if r.get("item_id") in ("_general_note", "_repudiation"):
            continue
        tally["judged"] += 1
        if (r.get("fix") or "").strip():
            tally["corrected"] += 1
        elif a in ("rejected", "flagged"):
            tally["rejected"] += 1
        elif a == "approved":
            tally["approved"] += 1
    issues_st = json.loads((DATA_ROOT / "data/issues_state.json").read_text()) \
        if (DATA_ROOT / "data/issues_state.json").exists() else {"issues": {}}
    cases = [{"player": s["player"], "quote": s["quote"], "status": s["status"]}
             for s in issues_st.get("issues", {}).values() if s.get("opened", "") >= since]
    corrections = [c for c in _rj(DATA_ROOT / "data/corrections.jsonl") if c.get("ts", "") >= since]
    blocked = json.loads((DATA_ROOT / "data/bench.json").read_text()) \
        if (DATA_ROOT / "data/bench.json").exists() else {}
    return {"ok": True, "tally": tally,
            "cases_opened": cases[:6],
            "gold_kept": minted,
            "corrections_saved": len(corrections),
            "benched": list(blocked),
            "open_left": sum(1 for s in issues_st.get("issues", {}).values()
                             if s["status"] in ("open", "fix_claimed", "verified"))}


@app.post("/api/approvals/reverse")
async def reverse(request: Request, k: str = ""):
    body = await request.json()
    judge, auth = _resolve_judge(k)
    members = {m["id"] for m in _team().get("members", [])}
    if auth == "shared" and _keys().get("legacy_write", True):
        judge = body.get("judge") if body.get("judge") in members else None
    if auth == "none" or judge is None:
        return JSONResponse({"ok": False, "quarantined": True}, status_code=403)
    if not (body.get("note") or "").strip():
        return {"ok": False, "error": "reversal needs a reason"}
    entry = {"schema_v": 2, "ts": datetime.now().isoformat(timespec="seconds"),
             "item_id": body.get("item_id"), "answer": "REVERSED",
             "note": str(body.get("note", ""))[:2000],
             "judge": judge, "auth": auth,
             "in_reply_to": body.get("in_reply_to"),
             "source": "team_portal"}
    with open(ANSWERS, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text())
        for it in q["items"]:
            if it["id"] == entry["item_id"]:
                it["status"] = "open"
                it.pop("answered", None)
                it.pop("answered_by", None)   # no ghost attribution on a reopened card
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return {"ok": True}
