#!/usr/bin/env python3
"""TRUTH-CANDIDATE MINER (B017, June 12 — RABIE's pick).
The truth pack's product list came from bio parsing and holds junk («حساب البيك»);
the client's OWN 500+ captions name his real products (التوأم، كرسبي بيك، فيليه).
Mine multi-word product n-grams: frequent in his feed, product-context-anchored,
rare on the rival street. Everything lands as pending_client candidates — the
machine proposes, the client confirms (One Write Path).

Usage: python3 scripts/mine_truth_candidates.py --handle albaik [--write]
"""
import argparse, collections, json, re
from pathlib import Path

BASE = Path(__file__).parent.parent
# words that signal a product is being TALKED ABOUT around the n-gram
CONTEXT = re.compile(r"اطلب|جرب|تذوق|وجبة|ساندويتش|ساندوتش|برجر|طعم|لذيذ|قرمش|جديد|عرض")
# a PRODUCT name contains or touches sector product-class tokens; slogans don't
SECTOR_TOKENS = {
    "f_and_b": r"بيك|كرسبي|فيليه|برجر|ساندوتش|ساندويتش|وجبة|دجاج|روبيان|توأم|بروست|فلافل|صوص|عشاء|فطور|جريش|كبسة|رز|قهوة|حلى",
    "fitness": r"اشتراك|برنامج|تمرين|تمارين|كوتش|مدرب|عضوية|تطبيق|خطة|جلسة|لياقة|تحدي",
}
SECTOR_TOKENS["healthcare_wellness"] = SECTOR_TOKENS["fitness"]
STOP = {"الله", "اللهم", "السعودية", "الرياض", "جدة", "مكة", "اليوم", "العيد", "رمضان",
         "مبارك", "كريم", "الوطني", "حياكم", "تابعونا", "ستوري", "البايو", "الرابط"}


def own_captions(handle: str) -> list[str]:
    raw = BASE / "clients" / handle / "raw/instagram"
    days = sorted(d for d in raw.iterdir() if d.is_dir())
    caps = []
    for l in (days[-1] / "posts.jsonl").read_text().strip().split("\n"):
        try:
            c = json.loads(l).get("caption")
        except Exception:
            continue
        if c:
            caps.append(c)
    return caps


def rival_text(handle: str) -> str:
    cs = json.loads((BASE / "clients" / handle / "profile/competitor_set.json").read_text())
    rivals = [r for r in cs.get("client_given", []) + cs.get("proposed_from_corpus", []) if r != handle]
    out = []
    for r in rivals:
        rd = BASE / "11_who_to_learn_from/_raw_archive" / r
        if not rd.is_dir():
            continue
        latest = sorted(d for d in rd.iterdir() if d.is_dir())[-1]
        for f in latest.glob("*.jsonl"):
            out.append(f.read_text())
    return " ".join(out)


def mine(handle: str) -> tuple:
    ym = json.loads((BASE / "clients" / handle / "year_map.json").read_text())
    FOOD = re.compile(SECTOR_TOKENS.get(ym.get("sector", "f_and_b"), SECTOR_TOKENS["f_and_b"]))
    caps = own_captions(handle)
    rtext = rival_text(handle)
    grams = collections.Counter()       # 1-2-3 word candidates
    ctx_hits = collections.Counter()    # appearing near product-context words
    for cap in caps:
        words = re.findall(r"[؀-ۿ]{3,}", cap)
        has_ctx = bool(CONTEXT.search(cap))
        for n in (1, 2, 3):
            for i in range(len(words) - n + 1):
                g = " ".join(words[i:i + n])
                if any(w in STOP for w in g.split()):
                    continue
                grams[g] += 1
                if has_ctx:
                    ctx_hits[g] += 1
    rcounts = collections.Counter(re.findall(r"[؀-ۿ]{3,}", rtext))
    cands = []
    for g, n in grams.items():
        if n < 4 or ctx_hits[g] < 3:
            continue                     # must recur AND live in product context
        if max(rcounts[w] for w in g.split()) >= 5:
            continue                     # street-common words are nobody's product
        cands.append({"name": g, "own_mentions": n, "in_product_context": ctx_hits[g]})
    # SPLIT: product names carry food tokens; the rest is brand language (slogans) —
    # both real, different organs (slogans feed very_normal anchors, not the menu)
    # campaign/place words disqualify a "product" even when the brand token matches
    NONPRODUCT = re.compile(r"جيران|سوق|عكاظ|بحي|بمدينة|صنع|منطقة")
    products = [c for c in cands if FOOD.search(c["name"]) and not NONPRODUCT.search(c["name"])]
    slogans = [c for c in cands if not FOOD.search(c["name"])]
    for lst in (products, slogans):
        multi = [c for c in lst if " " in c["name"]]
        kept = " ".join(c["name"] for c in multi)
        lst[:] = sorted(multi + [c for c in lst if " " not in c["name"] and c["name"] not in kept],
                         key=lambda c: -c["own_mentions"])
    return products[:12], slogans[:8]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    products, slogans = mine(a.handle)
    print("PRODUCT candidates:")
    for c in products:
        print(f"  {c['own_mentions']:3d}× ({c['in_product_context']} ctx) {c['name']}")
    print("BRAND-LANGUAGE candidates (slogans — very_normal anchors, not menu):")
    for c in slogans:
        print(f"  {c['own_mentions']:3d}× {c['name']}")
    if a.write:
        tpf = BASE / "clients" / a.handle / "profile/truth_pack.json"
        tp = json.loads(tpf.read_text())
        existing = {p.get("name") for p in tp.get("product_candidates", [])}
        added = 0
        for c in products:
            if c["name"] in existing:
                continue
            tp.setdefault("product_candidates", []).append({
                "name": c["name"],
                "evidence": f"{c['own_mentions']} mentions in own captions, {c['in_product_context']} in product context",
                "provenance": {"source": f"corpus-mined ({c['own_mentions']} own captions, {c['in_product_context']} product-context)",
                                "date_added": __import__("datetime").date.today().isoformat(),
                                "confirmer": "pending_client", "confidence": "experimental", "scope": "brand"}})
            added += 1
        tp["brand_language"] = [{"line": c["name"], "own_mentions": c["own_mentions"],
                                   "note": "corpus-mined slogan — anchor, not menu"} for c in slogans]
        from organ_write import write_organ
        write_organ(tpf, tp)
        print(f"  → {added} product candidates (pending_client) + {len(slogans)} brand-language lines")


if __name__ == "__main__":
    main()
