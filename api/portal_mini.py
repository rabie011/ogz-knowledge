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
    """Of the OPEN pairwise (pw_) cards, surface only the FIRST in the given (already-sorted) order —
    the rest stay queued and surface one after each tap. ALL non-pw open cards and ALL answered cards
    pass through untouched. Derived purely from queue state, so the ETag (queue mtime) stays valid:
    answering a pw_ card rewrites the queue → mtime bumps → the next pw_ appears on the next poll.
    Born June 16: 15 pw_ cards stacked = a wall against Mohamed's own no-flood rule + the ADHD
    60-second-gate contract. This makes calibration a gate, not a wall."""
    seen_open_pw = False
    kept = []
    for it in out:
        if str(it.get("id", "")).startswith("pw_") and it.get("status") != "answered":
            if seen_open_pw:
                continue            # withhold — only ONE open pairwise card at a time
            seen_open_pw = True
        kept.append(it)
    return kept


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
            out.append(dict(it, lane=_card_lane(it, lm)))
    # coerce None → "" : a card with created:null (or a slim answered dict missing it) crashed
    # the sort (None < str) → the WHOLE items API 500'd → the live link showed no cards (2026-06-14)
    out.sort(key=lambda x: (x.get("status") == "answered",
                            0 if x.get("priority") == "urgent" else 1, x.get("created") or ""))
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
    entry = {"schema_v": 2,
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
             "source": body.get("source") if body.get("source") in ("team_portal", "after_strip", "flag_sheet") else "team_portal"}
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
