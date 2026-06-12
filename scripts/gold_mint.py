#!/usr/bin/env python3
"""GOLD MINT — the approve→gold wire, REPAIRED (June 12 zoom-out caught it severed ×3:
wrote 'entries' while the renderer reads 'gold'; required a rating the portal rows
didn't carry; and was never asserted END-TO-END. The chair's law: assert at the
SYSTEM layer, not the component layer.)

Rule: judge=mohamed · auth!=none · answer=approved · rating>=4 · card carries
handle+caption → append to clients/<handle>/profile/gold.json under the 'gold' key —
THE KEY render_client_slot.py actually loads few-shot-FIRST (verified line:
json.loads(gf.read_text()).get("gold", [])).

LAW CHECK AT MINT (never silently side with an approval over a law): a caption that
violates a hard law (CTA on a religious/emotional occasion, dua-with-brand) does NOT
mint — it stages a RULING card for Mohamed instead. His approval vs the law is a
conflict only he resolves.

verdict_blind quarantine respected: blind verdicts never mint.
Idempotent byte cursor; assert-by-re-read.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, now_iso, read_jsonl
from organ_write import write_organ

CURSOR = "data/gold_mint_cursor.json"

CTA_WORDS = ("اطلب", "اطلبوا", "عرض ", "خصم", "مجانًا", "مجانا", "احجز", "الآن من")
RELIGIOUS_EMOTIONAL = ("ramadan", "eid", "founding", "national", "arafah", "hajj", "mothers")
ALLAH_TOKENS = ("اللهم", "الله ")


def law_violations(caption: str, occasion: str, brand_tokens: list) -> list:
    """Deterministic hard-law screen — the same rules the cultural gate enforces."""
    v = []
    occ = (occasion or "").lower()
    if any(w in caption for w in CTA_WORDS) and any(o in occ for o in RELIGIOUS_EMOTIONAL):
        v.append("cta_on_religious_or_emotional_occasion")
    if any(a in caption for a in ALLAH_TOKENS) and any(b and b in caption for b in brand_tokens):
        v.append("allah_name_with_brand_in_caption")
    return v


def _cursor() -> dict:
    f = base() / CURSOR
    return json.loads(f.read_text()) if f.exists() else {"offset": 0}


def _blind_ids() -> set:
    f = base() / "data/verdict_quarantine.json"
    return set(json.loads(f.read_text()).get("quarantined_item_ids", [])) if f.exists() else set()


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
    blind = _blind_ids()
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
              and r.get("item_id") not in blind)
        if not ok:
            continue
        card = cards.get(r.get("item_id"), {})
        handle, caption = card.get("handle"), card.get("caption")
        if not (handle and caption and (B / "clients" / handle / "profile").is_dir()):
            continue
        # LAW CHECK — an approval never silently overrides a law
        brand_tokens = [handle, "البيك" if handle == "albaik" else "", "جريشة" if "jurisha" in handle else ""]
        viol = law_violations(caption, str(card.get("occasion", "")), brand_tokens)
        if viol:
            import queue_decision as qd
            rid = f"ruling_{r['item_id']}"
            if rid not in cards:
                qd.push_attributed({
                    "id": rid, "title": "Your approval conflicts with a law — your ruling decides",
                    "tag": "Ruling", "desc": f"Caption: «{caption}» — laws hit: {', '.join(viol)}",
                    "clock": "", "priority": "normal", "created": now_iso(), "status": "open",
                    "kind": "buttons", "judge_lane": False, "lane": "strategy",
                    "why": "You approved a caption that breaks a standing law — only you can rule which wins.",
                    "need": "Rule: mint it as gold anyway, or uphold the law?",
                    "did": "The mint refused to silently side with either — it staged this ruling.",
                    "options": [{"v": "mint_anyway", "label": "Approve it as gold (law gets an exception)"},
                                {"v": "uphold_law", "label": "Uphold the law (no gold)", "rec": True}]},
                    made_by="system:gold_mint", via="scripts/gold_mint.py",
                    reason="law-vs-approval conflict at mint")
            continue
        gold_f = B / "clients" / handle / "profile" / "gold.json"
        # THE RENDERER'S SCHEMA: top key 'gold' (render_client_slot reads .get('gold'))
        gold = json.loads(gold_f.read_text()) if gold_f.exists() else {"gold": []}
        if "gold" not in gold:
            gold["gold"] = gold.pop("entries", [])
        key = hashlib.sha1(caption.encode()).hexdigest()[:12]
        if any(e.get("key") == key for e in gold["gold"]):
            continue
        gold["gold"].append({
            "key": key, "line": caption, "caption": caption, "occasion": card.get("occasion"),
            "rating": r["rating"], "source": f"portal:{r.get('item_id')}",
            "confirmer": "mohamed", "date": now_iso()[:10],
            "made_by": card.get("made_by")})
        write_organ(str(gold_f), gold)
        # ASSERT by re-read at the ORGAN layer
        assert any(e.get("key") == key for e in
                   json.loads(gold_f.read_text())["gold"]), "gold write not on disk"
        minted.append({"handle": handle, "key": key, "caption": caption[:50]})
    (B / CURSOR).write_text(json.dumps({"offset": len(raw)}))
    return minted


if __name__ == "__main__":
    m = mint()
    print(f"minted: {len(m)}" + ("".join(f"\n  ⭐ {x['handle']}: «{x['caption']}»" for x in m)))
