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
An angle = a strategic approach to ONE post: the insight + the formula + why it fits THIS brand.
Ground every angle ONLY in the truth pack — real products, the sector tension, occasion facts,
precedents. Never invent products. Use the CD lenses to find non-obvious angles. Use the formulas
as strategic frames. Return STRICT JSON: {"angles":[{"id":1,"lens":"...","formula":"CF_0x",
"insight_ar":"one sentence — the human truth this post lands","approach_ar":"how the post works,
1 sentence","why_this_brand":"1 sentence tying to the brand's real voice/products","post_type":
"announcement|question|moment|greeting|story"}]}. Exactly 5 distinct angles, distinct formulas/lenses."""


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
        print(f"  [{ang.get('formula')}·{ang.get('lens')}] {ang.get('insight_ar', '')[:80]}")


if __name__ == "__main__":
    main()
