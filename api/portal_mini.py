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

from fastapi import FastAPI, Request
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
def page(k: str = ""):
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    return FileResponse(STATIC / "approvals.html", headers={"Cache-Control": "no-store"})


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


@app.get("/api/approvals/items")
def items(k: str = ""):
    if not _ok(k):
        return JSONResponse([], status_code=403)
    lm = _lane_map()
    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
    out = [dict(it, lane=_card_lane(it, lm)) for it in q["items"]]
    out.sort(key=lambda x: (x.get("status") == "answered",
                            0 if x.get("priority") == "urgent" else 1, x.get("created", "")))
    return out


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
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text())
        for it in q["items"]:
            if it["id"] == entry["item_id"]:
                it["status"] = "answered"
                it["answered"] = entry["answer"][:60]
                it["answered_by"] = judge
                if entry["fix"]:
                    it["human_fix"] = entry["fix"][:200]
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return {"ok": True}


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
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return {"ok": True}
