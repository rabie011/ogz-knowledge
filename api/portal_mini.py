#!/usr/bin/env python3
"""THE PUBLIC MINI-PORTAL (June 12 — Mohamed's portal answer: mini_service ✅).
A deliberately TINY app: ONLY the decision portal — page, items, answer, reverse.
Nothing else exists here: no brain endpoints, no client raw data, no pipelines.
This is the only thing the public tunnel may expose. Key-gated on every route.

Run: python3 -m uvicorn api.portal_mini:app --port 4199 --host 127.0.0.1
(127.0.0.1 — reachable ONLY through the cloudflared tunnel, not the LAN)
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

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def _key():
    for l in open(Path.home() / ".abraham_env"):
        if l.startswith("APPROVALS_KEY="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def _ok(k):
    real = _key()
    return bool(real) and k == real


@app.get("/")
def root():
    return {"ogz": "decision portal", "hint": "/approvals?k=..."}


@app.get("/approvals")
def page(k: str = ""):
    if not _ok(k):
        return JSONResponse({"error": "key required"}, status_code=403)
    return FileResponse(STATIC / "approvals.html", headers={"Cache-Control": "no-store"})


@app.get("/api/approvals/items")
def items(k: str = ""):
    if not _ok(k):
        return JSONResponse([], status_code=403)
    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
    out = q["items"]
    out.sort(key=lambda x: (x.get("status") == "answered",
                             0 if x.get("priority") == "urgent" else 1, x.get("created", "")))
    return out


@app.post("/api/approvals/answer")
async def answer(request: Request, k: str = ""):
    if not _ok(k):
        return JSONResponse({"ok": False}, status_code=403)
    body = await request.json()
    entry = {"ts": datetime.now().isoformat(timespec="seconds"),
              "item_id": body.get("item_id"), "answer": str(body.get("answer", ""))[:2000],
              "note": str(body.get("note", ""))[:2000],
              "rating": body.get("rating") if isinstance(body.get("rating"), int) else None,
              "source": "public_portal"}
    with open(ANSWERS, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text())
        for it in q["items"]:
            if it["id"] == entry["item_id"]:
                it["status"] = "answered"
                it["answered"] = entry["answer"][:60]
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
              "note": str(body.get("note", ""))[:2000], "source": "public_portal"}
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
