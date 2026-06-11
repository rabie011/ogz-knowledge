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
import argparse, glob, json, os, sys, urllib.request
from pathlib import Path
import yaml

BASE = Path(__file__).parent.parent

CD_LENSES = {  # salvaged diagnostic questions — ideation only
    "firaasa": "What real Saudi behavioral moment around this product can we observe and honor?",
    "heritage_decoder": "What word or phrase carries a double meaning here — surface + cultural depth?",
    "authenticity_detective": "Where does the polished version break and the honest human moment show?",
    "paradox_hunter": "What's the counterintuitive truth that makes the obvious idea wrong?",
}


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
Use the CD lenses to find the non-obvious moment. Use a formula as the frame.
Return STRICT JSON: {"angles":[{"id":1,"lens":"...","formula":"CF_0x",
"scene_ar":"the concrete moment in one vivid sentence — who+when+what+the product",
"why_it_lands":"why a Saudi feels this — 1 sentence","post_type":
"moment|announcement|question|greeting|story"}]}. Exactly 6 distinct scenes, distinct moments."""


def build(pack: dict) -> dict:
    lenses = "\n".join(f"- {k}: {v}" for k, v in CD_LENSES.items())
    forms = "\n".join(f"- {f['id']} {f['name']}: {f['when']}" for f in formulas())
    body = {"model": "gpt-4o", "temperature": 0.8, "max_tokens": 1600,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SPEC + "\n\nCD LENSES:\n" + lenses + "\n\nFORMULAS:\n" + forms},
                {"role": "user", "content": "TRUTH PACK:\n" + json.dumps(pack, ensure_ascii=False)}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"})
    r = json.loads(urllib.request.urlopen(rq, timeout=120).read())
    out = json.loads(r["choices"][0]["message"]["content"])
    for a in out.get("angles", []):
        a["insight_ar"] = a.get("scene_ar", a.get("insight_ar", ""))   # downstream compat
        a["approach_ar"] = a.get("why_it_lands", a.get("approach_ar", ""))
    out["_brand"] = pack["brand_en"]
    out["_occasion"] = pack["occasion"]
    out["_built"] = "2026-06-11"
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
