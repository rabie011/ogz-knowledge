#!/usr/bin/env python3
"""GOLD pipeline (L4.10, June 11) — the founder's taps become the system's taste.

Reads logs/cross_preferences.json; every comparison with rating >= 4 promotes the
winning caption to GOLD:
  1. appended to docs/consultations/GOLD_OUTPUTS_HUMAIN.md (human-readable record)
  2. written to logs/brand_gold/{brand_en}_gold.json — consumed by v5_prompt as
     PRIORITY few-shot (founder-rated > engagement-ranked)
Idempotent: tracks promoted comparison timestamps. Run after any rating session
(wired into session-start checklist + can be cron'd).
"""
import json, re
from pathlib import Path

BASE = Path(__file__).parent.parent
PREFS = BASE / "logs" / "cross_preferences.json"
GOLD_MD = BASE / "docs" / "consultations" / "GOLD_OUTPUTS_HUMAIN.md"
GOLD_DIR = BASE / "logs" / "brand_gold"
STATE = BASE / "logs" / "gold_promoted.json"

BRAND_EN = {}
for b in json.loads((BASE / "data/brief_matrix.json").read_text()):
    BRAND_EN[b["brand"]] = b["brand_en"]


def main():
    if not PREFS.exists():
        print("no preferences yet")
        return
    prefs = json.loads(PREFS.read_text())
    done = set(json.loads(STATE.read_text())) if STATE.exists() else set()
    GOLD_DIR.mkdir(exist_ok=True)
    promoted = 0
    md_rows = []
    for c in prefs.get("comparisons", []):
        ts = c.get("timestamp", "")
        rating = c.get("rating")
        cap = (c.get("winner_caption") or "").strip()
        if ts in done or not rating or rating < 4 or len(cap) < 6:
            continue
        brand_ar = c.get("brief_key", "|").split("|")[0]
        occasion = c.get("brief_key", "|").split("|")[-1]
        brand_en = BRAND_EN.get(brand_ar, re.sub(r"\W+", "_", brand_ar)[:20])
        gf = GOLD_DIR / f"{brand_en}_gold.json"
        gold = json.loads(gf.read_text()) if gf.exists() else []
        if cap not in [g.get("caption") for g in gold]:
            gold.append({"caption": cap, "occasion": occasion, "rating": rating,
                          "model": c.get("winner_model", ""), "ts": ts})
            gf.write_text(json.dumps(gold, ensure_ascii=False, indent=2))
        md_rows.append(f"| {len(done)+promoted+1} | {brand_ar} | — | {occasion} | rated {rating}/5 ({c.get('winner_model','')}) | {cap[:120]} |")
        done.add(ts)
        promoted += 1
    if md_rows and GOLD_MD.exists():
        GOLD_MD.write_text(GOLD_MD.read_text().rstrip() + "\n" + "\n".join(md_rows) + "\n")
    STATE.write_text(json.dumps(sorted(done)))
    print(f"promoted to GOLD: {promoted} (total tracked: {len(done)})")


if __name__ == "__main__":
    main()
