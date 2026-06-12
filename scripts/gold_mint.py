#!/usr/bin/env python3
"""GOLD MINT — the approve→gold wire (June 12 zoom-out: VERIFIED no path existed from
portal approvals to any gold the renderer reads; the legacy gold_from_ratings.py path
feeds logs/brand_gold/ which render_client_slot never loads).

Rule: judge=mohamed · auth!=none · answer=approved · rating>=4 · artifact resolves to a
client caption (the judged card carries handle+caption) → append to
clients/<handle>/profile/gold.json via organ_write (versioned, atomic) — the organ
render_client_slot.py loads FIRST in few-shot. Idempotent byte cursor; assert-by-re-read.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, now_iso, read_jsonl
from organ_write import write_organ

CURSOR = "data/gold_mint_cursor.json"


def _cursor() -> dict:
    f = base() / CURSOR
    return json.loads(f.read_text()) if f.exists() else {"offset": 0}


def mint() -> list:
    B = base()
    answers_f = B / "data/mohamed_answers.jsonl"
    if not answers_f.exists():
        return []
    cur = _cursor()
    raw = answers_f.read_bytes()
    new = raw[cur["offset"]:]
    q = json.loads((B / "data/decision_queue.json").read_text()) \
        if (B / "data/decision_queue.json").exists() else {"items": []}
    cards = {it["id"]: it for it in q["items"]}
    minted = []
    for bline in new.split(b"\n"):
        if not bline.strip():
            continue
        try:
            r = json.loads(bline)
        except Exception:
            continue
        ok = (r.get("judge") == "mohamed" and r.get("auth") != "none"
              and str(r.get("answer")) == "approved"
              and isinstance(r.get("rating"), int) and r["rating"] >= 4
              and r.get("artifact_id"))
        if not ok:
            continue
        card = cards.get(r.get("item_id"), {})
        handle, caption = card.get("handle"), card.get("caption")
        if not (handle and caption and (B / "clients" / handle / "profile").is_dir()):
            continue
        gold_f = B / "clients" / handle / "profile" / "gold.json"
        gold = json.loads(gold_f.read_text()) if gold_f.exists() else {"entries": []}
        key = hashlib.sha1(caption.encode()).hexdigest()[:12]
        if any(e.get("key") == key for e in gold["entries"]):
            continue
        gold["entries"].append({
            "key": key, "caption": caption, "occasion": card.get("occasion"),
            "rating": r["rating"], "source": f"portal:{r.get('item_id')}",
            "confirmer": "mohamed", "date": now_iso()[:10],
            "made_by": card.get("made_by")})
        write_organ(str(gold_f), gold)
        # ASSERT by re-read (never by eyes)
        assert any(e.get("key") == key for e in
                   json.loads(gold_f.read_text())["entries"]), "gold write not on disk"
        minted.append({"handle": handle, "key": key, "caption": caption[:50]})
    (B / CURSOR).write_text(json.dumps({"offset": len(raw)}))
    return minted


if __name__ == "__main__":
    m = mint()
    print(f"minted: {len(m)}" + ("".join(f"\n  ⭐ {x['handle']}: «{x['caption']}»" for x in m)))
