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
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse

REPO = Path(__file__).parent.parent
STATIC = Path(__file__).parent / "static"
ANSWERS = REPO / "data" / "mohamed_answers.jsonl"
QUEUE = REPO / "data" / "decision_queue.json"
TEAM_F = REPO / "data" / "portal_team.json"
LANEMAP_F = REPO / "data" / "portal_lane_map.json"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def _team() -> dict:
    return json.loads(TEAM_F.read_text()) if TEAM_F.exists() else {"key": "", "members": []}


def _lane_map() -> dict:
    return json.loads(LANEMAP_F.read_text()) if LANEMAP_F.exists() else {}


def _ok(k: str) -> bool:
    """ONE shared team key gates the link. Identity is picked inside the app."""
    return bool(k) and k == _team().get("key")


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
    """ONE link — returns the team roster so the app shows an identity picker."""
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    return {"members": _team().get("members", [])}


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


@app.post("/api/approvals/answer")
async def answer(request: Request, k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    # identity is PICKED in the app (one link); validated against the roster
    members = {m["id"]: m for m in _team().get("members", [])}
    judge = body.get("judge") if body.get("judge") in members else "mohamed"
    entry = {"ts": datetime.now().isoformat(timespec="seconds"),
             "item_id": body.get("item_id"), "answer": str(body.get("answer", ""))[:2000],
             "note": str(body.get("note", ""))[:2000],
             "fix": str(body.get("fix", ""))[:3000],          # the correction itself (human truth)
             "rating": body.get("rating") if isinstance(body.get("rating"), int) else None,
             "judge": judge, "lane": members.get(judge, {}).get("lane", "all"),
             "source": "team_portal"}
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
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    if not (body.get("note") or "").strip():
        return {"ok": False, "error": "reversal needs a reason"}
    entry = {"ts": datetime.now().isoformat(timespec="seconds"),
             "item_id": body.get("item_id"), "answer": "REVERSED",
             "note": str(body.get("note", ""))[:2000],
             "judge": (body.get("judge") if body.get("judge") in {m["id"] for m in _team().get("members", [])} else "mohamed"),
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
