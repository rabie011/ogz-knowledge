#!/usr/bin/env python3
"""RESCUE Mohamed's past feedback into the live taste signal (2026-06-14: "update my feedback to
what we have now so it could learn from it — don't waste what I reviewed"). His 30 blind ratings
(logs/system/review_results.json: excellent/good/weak/fail + review_data.json: the captions) were
only used to DIAGNOSE the broken judge. This converts them into PAIRWISE preference data — the same
shape the new pilot picks use — so the taste model learns from ALL of it, not just future picks.

Method (standard absolute→pairwise): within a brand, every higher-rated caption beats every
lower-rated one → a winner/loser pair. Tagged source=seed_from_ratings (distinct from fresh picks).
Idempotent. Usage: python3 scripts/seed_taste_from_ratings.py
"""
import json, hashlib
from pathlib import Path

B = Path(__file__).parent.parent
PREFS = B / "data/pairwise_prefs.jsonl"
ORDER = {"excellent": 3, "good": 2, "weak": 1, "fail": 0, "bad": 0}
BRAND2HANDLE = {"albaik": "albaik", "eatjurisha": "eatjurisha", "jurisha": "eatjurisha",
                "myfitness": "myfitness.sa", "myfitness.sa": "myfitness.sa"}


def main():
    rr = json.loads((B / "logs/system/review_results.json").read_text())
    rd = json.loads((B / "logs/system/review_data.json").read_text())
    results = list(rr.values()) if isinstance(rr, dict) else rr
    data = rd if isinstance(rd, list) else list(rd.values())[0]
    # align by id when present, else by position
    by_id = {d.get("id"): d for d in data if isinstance(d, dict) and d.get("id") is not None}
    items = []
    for i, r in enumerate(results):
        if not isinstance(r, dict):
            continue
        d = by_id.get(r.get("id")) or (data[i] if i < len(data) else None)
        cap = (d or {}).get("arabic") or (d or {}).get("caption")
        rating = (r.get("rating") or "").lower()
        if cap and rating in ORDER:
            items.append({"caption": cap, "brand": r.get("brand") or (d or {}).get("brand") or "?",
                          "occasion": r.get("occasion") or (d or {}).get("occasion") or "",
                          "rank": ORDER[rating], "rating": rating})

    # existing prefs (idempotent — don't double-seed)
    seen = set()
    if PREFS.exists():
        seen = {json.loads(l).get("pair_id") for l in PREFS.read_text().splitlines() if l.strip()}

    # His taste is CROSS-BRAND: a "good" caption beats a "fail" caption regardless of brand. Pair every
    # higher-rated against lower-rated, PREFERRING same-sector pairs first (less topic-noise), capped.
    highs = sorted([x for x in items if x["rank"] >= 2], key=lambda x: -x["rank"])
    lows = sorted([x for x in items if x["rank"] <= 1], key=lambda x: x["rank"])
    SECTOR = {"albaik": "f_and_b", "eatjurisha": "f_and_b", "mcdonaldsksa": "f_and_b", "barnscoffee": "f_and_b",
              "myfitness": "fitness", "myfitness.sa": "fitness"}
    CAP = 30
    seeded = 0
    # same-sector pairs first, then the rest
    def _pairs():
        for w in highs:
            for l in lows:
                same = SECTOR.get(w["brand"], "_w") == SECTOR.get(l["brand"], "_l")
                yield (0 if same else 1), w, l
    for _, w, l in sorted(_pairs(), key=lambda t: t[0]):
        if seeded >= CAP:
            break
        if w["caption"] == l["caption"]:
            continue
        pid = "seed_" + hashlib.md5((w["caption"] + "|" + l["caption"]).encode()).hexdigest()[:12]
        if pid in seen:
            continue
        rec = {"pair_id": pid, "handle": BRAND2HANDLE.get(w["brand"], w["brand"]),
               "winner": "a", "winner_caption": w["caption"], "loser_caption": l["caption"],
               "winner_brain": "?", "source": "seed_from_ratings",
               "his_rating_winner": w["rating"], "his_rating_loser": l["rating"],
               "win_brand": w["brand"], "lose_brand": l["brand"], "judge": "mohamed", "ts": "seed"}
        PREFS.open("a").write(json.dumps(rec, ensure_ascii=False) + "\n")
        seen.add(pid); seeded += 1

    print(f"✅ rescued {len(items)} of your ratings → {seeded} pairwise preference pairs (source=seed_from_ratings)")
    print(f"   the taste model now learns from your PAST feedback + your new pilot picks — nothing wasted")
    return seeded


if __name__ == "__main__":
    main()
