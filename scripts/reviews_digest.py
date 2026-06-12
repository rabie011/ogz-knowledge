#!/usr/bin/env python3
"""MAPS-REVIEWS DETERMINISTIC DIGEST (June 12 — zero-LLM pre-pass).
Counts what needs no judgment: star spread, signal-word frequencies (complaint
and praise classes), branch mentions, recency. The post-refill mini-LLM pass
refines themes; this gives the im-here numbers TODAY.

Usage: python3 scripts/reviews_digest.py
"""
import collections, json, re
from pathlib import Path

BASE = Path(__file__).parent.parent
COMPLAINT = {"انتظار": r"انتظار|طوابير|طابور|زحمة", "slow": r"بطيء|بطيئة|تأخير|متأخر",
              "cold_food": r"بارد|باردة", "quality_drop": r"تغير الطعم|مو زي قبل|نزل المستوى|سيء",
              "price": r"غالي|أسعار مرتفعة|سعر مبالغ", "service": r"تعامل سيء|خدمة سيئة|موظف"}
PRAISE = {"taste": r"لذيذ|طعم رائع|خرافي|يجنن", "speed": r"سريع|بسرعة", "value": r"سعر ممتاز|رخيص|يستاهل",
           "clean": r"نظيف|نظافة", "staff": r"تعامل راقي|موظفين ممتازين|خدمة ممتازة"}


def digest(handle: str) -> dict | None:
    root = BASE / "clients" / handle / "raw/maps_reviews"
    if not root.is_dir():
        return None
    latest = sorted(root.iterdir())[-1]
    reviews = [json.loads(l) for l in (latest / "reviews.jsonl").read_text().strip().split("\n") if l.strip()]
    texts = [(r.get("text") or r.get("reviewText") or "").strip() for r in reviews]
    texts = [t for t in texts if t]
    stars = collections.Counter(int(r.get("stars") or r.get("rating") or 0) for r in reviews)
    comp = {k: sum(1 for t in texts if re.search(p, t)) for k, p in COMPLAINT.items()}
    prai = {k: sum(1 for t in texts if re.search(p, t)) for k, p in PRAISE.items()}
    branches = collections.Counter((r.get("title") or "?")[:35] for r in reviews)
    d = {"handle": handle, "total": len(reviews), "with_text": len(texts),
         "stars": dict(sorted(stars.items(), reverse=True)),
         "complaints": dict(sorted(comp.items(), key=lambda x: -x[1])),
         "praise": dict(sorted(prai.items(), key=lambda x: -x[1])),
         "top_places": dict(branches.most_common(3))}
    return d


def main():
    out = {}
    for h in ("albaik", "eatjurisha"):
        d = digest(h)
        if not d:
            continue
        out[h] = d
        print(f"── {h}: {d['total']} reviews · stars {d['stars']}")
        print(f"   complaints: {d['complaints']}")
        print(f"   praise: {d['praise']}")
    (BASE / "data/reviews_digest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("→ data/reviews_digest.json")


if __name__ == "__main__":
    main()
