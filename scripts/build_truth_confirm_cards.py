#!/usr/bin/env python3
"""B186 — Truth-confirm cards for all 3 pilots (Spine, June 19).

The producer must never invent a product (Rule #12). The truth_pack carries the
brand's REAL products, but every one mined from the corpus lands UNCONFIRMED
(confirmer ∈ {pending_client, data_diagnosis}). This generator turns each
unconfirmed candidate into a one-tap ✓/✗ confirm card so the client/Mohamed can
ratify the brand's own truth — and adds a jurisha price-blank text card so the
khwila pack carries real prices instead of empty slots.

It only SURFACES mined facts for a tap; it authors no content. The consumer is
apply_rulings.h_truth_confirm (Rule #6 — writer + reader built the same cycle):
  ✅ confirm → provenance.confirmer=mohamed, confidence=confirmed
  ❌ reject  → confidence=rejected (kept, never deleted), confirmer=mohamed
  💬 text on a *_prices card → written into truth_pack["prices"], candidates confirmed

Output: data/truth_confirm_staged.json  ({staged, note, cards:[...]}), deduped by id.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent
PILOTS = ["eatjurisha", "albaik", "myfitness.sa"]
# confirmer values that mean "not yet ratified by a human"
UNCONFIRMED = {"pending_client", "data_diagnosis", "?", "", None}


def _slug(name: str, i: int) -> str:
    """Stable per-card suffix. Arabic names → index-based slug (ids must be ascii-safe
    for the portal/ledger); i keeps it unique and order-stable."""
    ascii_part = re.sub(r"[^a-z0-9]+", "", name.lower())[:12]
    return f"{i}{('_' + ascii_part) if ascii_part else ''}"


def cards_for(base: Path, handle: str) -> list:
    tpf = base / "clients" / handle / "profile" / "truth_pack.json"
    if not tpf.exists():
        return []
    tp = json.loads(tpf.read_text(encoding="utf-8"))
    out = []
    cands = tp.get("product_candidates", [])
    for i, c in enumerate(cands):
        prov = c.get("provenance", {}) or {}
        if prov.get("confirmer") not in UNCONFIRMED:
            continue  # already ratified — no card
        if prov.get("confidence") == "rejected":
            continue  # his ❌ already recorded — don't re-ask
        name = c.get("name", "")
        out.append({
            "id": f"truth_confirm_{handle}_{_slug(name, i)}",
            "kind": "buttons",
            "lane": "strategy",
            "organ": "truth_pack",
            "tag": "تأكيد منتج",
            "handle": handle,
            "candidate": name,
            "title": f"✅ {handle} — تأكيد منتج",
            "why": f"النظام لقى «{name}» مذكور ({c.get('evidence','')}) في حسابكم. "
                   f"هل هذا منتج حقيقي من المنيو؟",
            "need": "أكدوا أو احذفوا — يثبّت truth_pack ويمنع النظام يخترع منتجات.",
            "buttons": [
                {"value": "confirm", "label": "✅ نعم، منتج حقيقي"},
                {"value": "reject", "label": "❌ لا، احذفوه"},
            ],
        })
    # jurisha price-blank card — the confirmed products need real prices for the khwila pack
    if handle == "eatjurisha" and not tp.get("prices"):
        named = "، ".join(c.get("name", "") for c in cands[:6])
        out.append({
            "id": f"truth_confirm_{handle}_prices",
            "kind": "text",
            "lane": "strategy",
            "organ": "truth_pack",
            "tag": "أسعار المنيو",
            "handle": handle,
            "candidate": "__prices__",
            "title": "💬 جريش — أسعار المنيو",
            "why": f"عشان الكابتشن يقدر يذكر السعر بدون اختراع: المنتجات «{named}». "
                   f"اكتبوا الأسعار (فردي/عائلي) — تنحفظ في الـ khwila pack.",
            "need": "اكتبوا الأسعار النصية — تروح مباشرة لـ truth_pack.prices.",
            "text": "مثال: جريش فردي 18، عائلي 45 …",
        })
    return out


def build(base: Path) -> dict:
    cards, by_client = [], {}
    for h in PILOTS:
        c = cards_for(base, h)
        by_client[h] = len(c)
        cards.extend(c)
    return {
        "staged": date.today().isoformat(),
        "note": "B186 truth-confirm cards — ✓/✗ per unconfirmed product candidate; "
                "deduped by id; consumer = apply_rulings.h_truth_confirm.",
        "by_client": by_client,
        "cards": cards,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write data/truth_confirm_staged.json")
    a = ap.parse_args()
    doc = build(BASE)
    for h, n in doc["by_client"].items():
        print(f"  {h:14s} {n} card(s)")
    print(f"  TOTAL {len(doc['cards'])} truth-confirm cards")
    if a.write:
        out = BASE / "data" / "truth_confirm_staged.json"
        sys.path.insert(0, str(Path(__file__).parent))
        from organ_write import write_organ
        write_organ(out, doc)
        print(f"  → {out}")


if __name__ == "__main__":
    main()
