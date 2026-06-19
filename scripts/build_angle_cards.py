#!/usr/bin/env python3
"""Angle cards (P2, June 11) — THE MISSING CREATIVE ORGAN.
Idea-first: before any caption, GPT proposes 5 distinct ANGLES grounded ONLY in a
truth pack (real products + sector tension + occasion facts + precedents), guided
by the CD-brain diagnostic questions (salvaged from the deprecated brains — they
were ruined as caption rhetoric but are sharp as IDEATION lenses) and the 7
Mohamed-confirmed creative formulas. Output is ideas, not captions — the founder
gates angles (cheap) before any rendering (the expensive, taste-heavy step).
Output: data/angle_cards/{brand}__{occasion}.json  ·  feeds /api/angles + the render stage.
"""
import argparse, glob, json, os, re, sys, urllib.request
from pathlib import Path
import yaml
from brain_router import route_brain, brain_method, load_router_rules   # B041/B053: route methodology + sector locks

BASE = Path(__file__).parent.parent

# B041 (June 19) — ROOT FIX. The angle pen used to inject 4 salvaged one-LINE CD questions
# (the front-matter-only trap): every brain collapsed to the generic concrete-scene prompt →
# the brand-mean formula → the #1 repetition cause. Now each angle is ROUTED to a CD brain
# (brain_router.route_brain) and generated through that brain's FULL methodology BODY
# (brain_router.brain_method), spread across the CD range so a batch uses real distinct methods.
_AR = set("ءاأبتثجحخدذرزسشصضطظعغفقكلمنهوي")
_OCC_KEYMAP = {"national_day": "saudi_national_day", "founding_day": "saudi_founding_day"}
_OCC_BRAINS = ("saudi_national_day", "saudi_founding_day", "ramadan",
               "eid_al_fitr", "eid_al_adha", "arab_mothers_day", "hajj_season")
_DAILY = ("metaphor", "paradox", "firaasa", "authenticity")   # the four non-occasion brains


def _has_arabic(s: str) -> bool:
    return any(ch in _AR for ch in (s or ""))


def angle_brains(occasion: str, brand_ar: str = "", n: int = 6, sector: str = "") -> list:
    """Routed CD-brain spread for an angle batch (B041). Occasion batches foreground the
    occasion's brain (route_brain) — with render's heritage→firaasa guard when the brand has
    no Arabic root (RABIE: jurisha national-day drift) — then span the remaining range so the
    6 angles aren't one-brain (June 14 root: one-brain batches collapse to the brand-mean
    formula). Daily/offer batches spread across all four non-occasion brains.

    B053 (June 19): a sector's forbidden brains (sector_safety_locks) are removed from the WHOLE
    batch, not just the lead — else healthcare_wellness would still see paradox at a later index
    (the angle path was the write-only door: it routed without passing sector). Pass sector through."""
    occ = _OCC_KEYMAP.get(occasion, occasion)
    forbidden = load_router_rules()["sector_safety_locks"].get(sector or "", [])
    if occ in _OCC_BRAINS:
        primary = route_brain({"occasion": occ, "sector": sector})
        if primary == "heritage" and not _has_arabic(brand_ar):
            primary = "firaasa"
        spread = [primary] + [b for b in ("firaasa", "authenticity", "metaphor", "paradox", "heritage")
                              if b != primary]
    else:
        spread = list(_DAILY)
    spread = [b for b in spread if b not in forbidden] or spread   # never empty: fall back if all forbidden
    return [spread[i % len(spread)] for i in range(n)]


def key():
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith("OPENAI_API_KEY"):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit("no key")


def formulas() -> list[dict]:
    f = BASE / "21_strategy_frameworks/creative_formulas.yaml"
    d = yaml.safe_load(f.read_text())
    return [{"id": v["id"], "name": v["name_en"], "when": (v.get("when_to_use") or "").strip()[:160]}
            for v in d.get("formulas", {}).values()]


SPEC = """You are a Saudi creative director generating ANGLES (ideas), not captions.
An angle is a CONCRETE SCENE, never an abstract theme. The founder kills abstractions
("the contrast between celebration and family", "the bridge of joy", "food is heritage") —
he rewards a SPECIFIC moment you can SEE.

EVERY angle MUST name:
- WHO: a specific person in a specific role (الجدّة وهي تصب القهوة / الولد الصغير أول ما يدخل / الأب بعد الدوام)
- WHEN: a specific time/beat (الساعة 6 الصبح / أول ما يخلص الأذان / قبل ما يجي الضيوف)
- WHAT: a specific gesture/action (يقسّم آخر قطعة / يحجز الطاولة من بدري / يرجّع الصحن فاضي)
- where the PRODUCT sits naturally inside that exact moment.

BANNED (the ad-trap): metaphors that call the brand "a bridge / a symbol / the soul of",
sentences about "culture" or "heritage" in the abstract, anything that could be a TV-ad voiceover.

Ground ONLY in the truth pack (real products, sector tension, occasion facts, precedents).
Generate each angle AS its ASSIGNED CD brain — APPLY that brain's full methodology (below) to
find the non-obvious moment; never fall back to a generic concrete-scene default. Use a formula
as the frame. Return STRICT JSON: {"angles":[{"id":1,"brain":"<assigned brain key>","lens":"<same as brain>",
"formula":"CF_0x","scene_ar":"the concrete moment in one vivid sentence — who+when+what+the product",
"why_it_lands":"why a Saudi feels this — 1 sentence","post_type":
"moment|announcement|question|greeting|story"}]}. Exactly 6 distinct scenes, distinct moments,
each honoring its assigned brain's method."""


# year_map emits calendar SLUGS that differ from occasion_facts KEYS; without this map
# the lens lookup silently misses → sector-blind angles (the weak pocket the lens kills).
# B061/B062 slug-alias wire — RABIE root-hunt, June 19: lenses existed but were severed
# for these two slugs (singles_day_11_11, mdl_beast_soundstorm) until this was connected.
_SLUG_TO_LENS_KEY = {
    "national_day": "saudi_national_day",
    "singles_day_11_11": "11_11_shopping",
    "mdl_beast_soundstorm": "mdl_beast",
}


def sector_lens(occasion: str, sector: str) -> dict | None:
    """Per-sector occasion lens (June 11) — the fix for sector-blind occasion facts.
    Root: ramadan-for-coffee ≠ ramadan-for-restaurants; one generic fact set pushed
    every non-restaurant brand into abstract themes (the coffee×ramadan weak pocket)."""
    facts = json.loads((BASE / "data/occasion_facts.json").read_text())
    occ = _SLUG_TO_LENS_KEY.get(occasion, occasion)
    return (facts.get(occ, {}).get("sector_lenses") or {}).get(sector)


def brand_identity(brand_en: str) -> str:
    """One line of WHAT THE BRAND SELLS from its DNA — guards against hashtag-only
    product lists (barns' real_products were all hashtags, no products)."""
    f = BASE / "logs/brand_dna" / f"{brand_en}.json"
    if not f.exists():
        return ""
    d = json.loads(f.read_text())
    return (d.get("identity") or d.get("voice_summary") or "")[:300]


def angle_messages(pack: dict):
    """Build the (messages, brains) for the angle call — PURE, so B041's routing+method
    injection is testable without an API call. brains[i] is the CD brain angle i+1 is routed to;
    each routed brain's FULL methodology body is injected (the fix), with an angle→brain map."""
    brains = angle_brains(pack["occasion"], pack.get("brand_ar", ""), sector=pack.get("sector", ""))
    uniq = list(dict.fromkeys(brains))
    methods = "\n\n".join(f"## {b} brain\n{brain_method(b)}" for b in uniq if brain_method(b))
    assign = " · ".join(f"angle {i + 1} → {b}" for i, b in enumerate(brains))
    forms = "\n".join(f"- {f['id']} {f['name']}: {f['when']}" for f in formulas())
    sys_p = (SPEC + "\n\nCD METHODOLOGIES (apply the method of each angle's assigned brain):\n" + methods
             + "\n\nANGLE→BRAIN ASSIGNMENTS (each angle MUST carry its \"brain\" and be found through "
               "that brain's method):\n" + assign + "\n\nFORMULAS:\n" + forms)
    user = "TRUTH PACK:\n" + json.dumps(pack, ensure_ascii=False)
    ident = brand_identity(pack["brand_en"])
    if ident:
        user += f"\n\nBRAND IDENTITY (what they actually sell — every scene must fit THIS product):\n{ident}"
    lens = sector_lens(pack["occasion"], pack.get("sector", ""))
    if lens:
        user += ("\n\nOCCASION×SECTOR LENS (how this occasion is ACTUALLY lived around this sector's product — "
                 "ground WHO/WHEN in these real moments, but use ONLY moments where THIS brand's product belongs):\n"
                 + json.dumps(lens, ensure_ascii=False))
    return [{"role": "system", "content": sys_p}, {"role": "user", "content": user}], brains


def build(pack: dict) -> dict:
    messages, brains = angle_messages(pack)
    body = {"model": "gpt-4o", "temperature": 0.8, "max_tokens": 1800,
            "response_format": {"type": "json_object"}, "messages": messages}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(rq, timeout=120).read())
    out = json.loads(r["choices"][0]["message"]["content"])
    valid = set(brains)
    for i, a in enumerate(out.get("angles", [])):
        a["insight_ar"] = a.get("scene_ar", a.get("insight_ar", ""))   # downstream compat
        a["approach_ar"] = a.get("why_it_lands", a.get("approach_ar", ""))
        m = re.match(r"(CF_\d+)", str(a.get("formula", "")))           # "CF_02 Paradox Play" → "CF_02"
        if m:
            a["formula"] = m.group(1)
        if a.get("brain") not in valid:                                # enforce the routed assignment
            a["brain"] = brains[i] if i < len(brains) else brains[i % len(brains)]
        a["lens"] = a["brain"]                                          # backward-compat (creative_line reads lens)
    out["_brand"] = pack["brand_en"]
    out["_occasion"] = pack["occasion"]
    out["_brains"] = brains
    out["_built"] = "2026-06-19"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--occasion", default="national_day")
    a = ap.parse_args()
    pf = BASE / "data/truth_packs" / f"{a.brand}__{a.occasion}.json"
    if not pf.exists():
        sys.exit(f"build truth pack first: python3 scripts/build_truth_pack.py --brand {a.brand} --occasion {a.occasion}")
    cards = build(json.loads(pf.read_text()))
    out = BASE / "data" / "angle_cards"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{a.brand}__{a.occasion}.json").write_text(json.dumps(cards, ensure_ascii=False, indent=2))
    print(f"✓ {len(cards.get('angles', []))} angles for {a.brand}/{a.occasion}:")
    for ang in cards.get("angles", []):
        print(f"  [{ang.get('formula')}·{ang.get('lens')}] {ang.get('scene_ar', ang.get('insight_ar',''))[:90]}")


if __name__ == "__main__":
    main()
