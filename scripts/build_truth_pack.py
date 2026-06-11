#!/usr/bin/env python3
"""Truth pack (P2, June 11) — the brief, reimagined as TRUTH ONLY.
The old briefs carried placeholder products ("وجبة جديدة") and poetry seeds. A truth
pack assembles ONLY what's real, by CONNECTING existing assets:
  DNA v3            voice/openers/signatures/length/patterns
  real products     extracted from the brand's own hashtags (no inventions)
  occasion facts    data/occasion_facts.json (validated calendar)
  sector tension    21_strategy_frameworks/cultural_tensions_by_sector.yaml (Mohamed-confirmed)
  precedents        21_campaign_archive matching sector+occasion (+ do-not-transplant)
A truth pack with a placeholder product is INVALID (validator below).
Output: data/truth_packs/{brand_en}__{occasion}.json
"""
import argparse, glob, json, re, sys
from collections import Counter
from pathlib import Path
import yaml

BASE = Path(__file__).parent.parent
OUT = BASE / "data" / "truth_packs"
PLACEHOLDERS = {"وجبة جديدة", "مشروب الموسم", "المنتج", "منتج جديد"}


def real_products(brand_en: str, top=8) -> list[str]:
    files = sorted(glob.glob(str(BASE / "11_who_to_learn_from/_raw_archive" / brand_en / "*" / "*apify_raw.jsonl")), reverse=True)
    if not files:
        return []
    tags = Counter()
    for line in open(files[0], encoding="utf-8"):
        try:
            cap = (json.loads(line).get("caption") or "")
        except Exception:
            continue
        for h in re.findall(r"#[؀-ۿ_]{3,}", cap):
            tags[h] += 1
    # drop the brand's own name tag + generic nation tags; keep product/campaign tags
    drop = {f"#{brand_en}"}
    return [t for t, _ in tags.most_common(top * 2) if t not in drop][:top]


def sector_tensions(sector: str) -> list[dict]:
    f = BASE / "21_strategy_frameworks" / "cultural_tensions_by_sector.yaml"
    if not f.exists():
        return []
    d = yaml.safe_load(f.read_text())
    s = (d.get("sectors", {}) or {}).get(sector, {})
    return [{"id": t.get("id"), "name": t.get("name"), "territory": (t.get("territory") or "").strip()}
            for t in s.get("tensions", [])][:4]


def precedents(sector: str, occasion: str) -> list[dict]:
    out = []
    for f in glob.glob(str(BASE / "21_campaign_archive/campaigns/*.json")):
        d = json.loads(open(f).read())
        if d.get("sector") != sector:
            continue
        if occasion and occasion not in str(d.get("occasion_context", "")).lower() and occasion != "any":
            continue
        out.append({"insight": d.get("strategic_insight", ""),
                     "what_worked": d.get("what_made_it_work", ""),
                     "do_not_transplant": d.get("what_would_NOT_transplant", "")})
    return out[:3]


def build(brand_en: str, brand_ar: str, sector: str, occasion: str) -> dict:
    facts = json.loads((BASE / "data/occasion_facts.json").read_text()).get(occasion, {})
    dna_f = BASE / "logs/brand_dna" / f"{brand_en}_dna_v3.json"
    dna = json.loads(dna_f.read_text()) if dna_f.exists() else {}
    return {
        "brand_en": brand_en, "brand_ar": brand_ar, "sector": sector, "occasion": occasion,
        "real_products": real_products(brand_en),
        "voice": {"openers": dna.get("proven_openers_ar", [])[:6],
                   "signatures": dna.get("signature_phrases_ar", [])[:5],
                   "length_p50": dna.get("length_distribution", {}).get("p50"),
                   "patterns": dna.get("patterns_used", [])},
        "occasion_facts": {"themes": facts.get("themes", []), "dos": facts.get("dos", []),
                            "family_centrality": facts.get("family_centrality", "")},
        "sector_tensions": sector_tensions(sector),
        "precedents": precedents(sector, occasion),
        "_built": "2026-06-11", "_source": "DNA v3 + real hashtags + occasion_facts + strategy_frameworks + campaign_archive",
    }


def validate(pack: dict) -> list[str]:
    errs = []
    if not pack["real_products"]:
        errs.append("no real products extracted")
    if any(p in PLACEHOLDERS for p in pack["real_products"]):
        errs.append("placeholder product present")
    if not pack["voice"]["openers"]:
        errs.append("no DNA voice (brand not covered)")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--occasion", default="national_day")
    a = ap.parse_args()
    m = json.loads((BASE / "data/brief_matrix.json").read_text())
    b = next((x for x in m if x.get("brand_en") == a.brand), None)
    if not b:
        sys.exit(f"brand not in matrix: {a.brand}")
    pack = build(a.brand, b["brand"], b["sector"], a.occasion)
    errs = validate(pack)
    if errs:
        sys.exit(f"INVALID truth pack {a.brand}/{a.occasion}: {errs}")
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{a.brand}__{a.occasion}.json"
    p.write_text(json.dumps(pack, ensure_ascii=False, indent=2))
    print(f"✓ truth pack {a.brand}/{a.occasion}: products={pack['real_products'][:4]} · tensions={len(pack['sector_tensions'])} · precedents={len(pack['precedents'])}")


if __name__ == "__main__":
    main()
