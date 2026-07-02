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

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse

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
