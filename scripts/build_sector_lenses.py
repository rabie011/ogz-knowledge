#!/usr/bin/env python3
"""SECTOR-LENS GENERATOR + VALIDATOR (B058/B059, June 12 — RABIE's pick).
Every occasion in occasion_facts.json gets per-sector lenses (how THIS occasion is
actually lived through THIS sector's product) — the fix that killed the coffee×ramadan
weak pocket, generalized to the whole calendar. Grounded in mined occasion plays.
Validator: every lens carries concrete moments (WHO+WHEN), timing_peaks, product_role —
an empty or abstract lens fails the build.

Usage: python3 scripts/build_sector_lenses.py [--only <occasion>] [--validate-only]
"""
import argparse, glob, json, os, sys, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
SECTORS = ["f_and_b", "beauty_personal_care", "retail_lifestyle", "fashion",
            "healthcare_wellness", "real_estate"]


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit(f"no {k}")


def plays_evidence(occ: str) -> str:
    out = []
    key = occ.split("_")[0]
    for f in glob.glob(str(BASE / "11_who_to_learn_from/patterns/occasion_plays/*.json")):
        d = json.loads(open(f).read())
        name, desc = d.get("pattern_name", ""), (d.get("description") or "")[:110]
        if key in name.lower() or key in desc.lower():
            out.append(f"- [{','.join(d.get('observed_in_sectors', [])[:3])}] {name}: {desc}")
    return "\n".join(out)[:1800]


def generate(occ: str, base: dict) -> dict:
    body = {"model": "gpt-4o", "temperature": 0.4, "max_tokens": 1800,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content":
                 "You write SECTOR LENSES for a Saudi occasion — how it is ACTUALLY lived through each "
                 "sector's product. NOT generic facts: sector-specific real moments. Example: ramadan for "
                 "COFFEE is the 2:30am sahur run and post-taraweeh cafe meetups, not iftar tables. "
                 'Return JSON: {"lenses": {"<sector>": {"moments": ["3-4 concrete moments, each WHO+WHEN"], '
                 '"product_role": "one sentence", "timing_peaks": ["when this sector\'s customers act"]}}} '
                 "for ALL requested sectors."},
                {"role": "user", "content":
                 f"OCCASION: {occ} — {base.get('name_ar', '')}\n"
                 f"BASE FACTS: {json.dumps(base.get('themes', [])[:4], ensure_ascii=False)}\n"
                 f"SECTORS: {SECTORS}\nMINED PLAY EVIDENCE:\n{plays_evidence(occ)}"}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}",
                                         "Content-Type": "application/json"})
    return json.loads(json.loads(urllib.request.urlopen(rq, timeout=120).read())
                      ["choices"][0]["message"]["content"]).get("lenses", {})


def validate(facts: dict) -> int:
    fails = 0
    for occ, d in facts.items():
        lenses = d.get("sector_lenses") or {}
        for sec in SECTORS:
            l = lenses.get(sec)
            if not l:
                print(f"  ❌ {occ}×{sec}: MISSING")
                fails += 1
                continue
            moms = l.get("moments") or []
            if len(moms) < 2 or not l.get("product_role") or not l.get("timing_peaks"):
                print(f"  ❌ {occ}×{sec}: thin (moments={len(moms)})")
                fails += 1
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    ap.add_argument("--validate-only", action="store_true")
    a = ap.parse_args()
    ff = BASE / "data/occasion_facts.json"
    facts = json.loads(ff.read_text())
    if not a.validate_only:
        todo = [o for o, d in facts.items()
                if (not a.only or o == a.only) and not d.get("sector_lenses")]
        print(f"{len(todo)} occasions need lenses: {todo}")
        for occ in todo:
            lenses = generate(occ, facts[occ])
            facts[occ]["sector_lenses"] = lenses
            ff.write_text(json.dumps(facts, ensure_ascii=False, indent=2))  # checkpoint
            print(f"  ✓ {occ}: {len(lenses)} lenses")
    fails = validate(facts)
    total = sum(len(d.get("sector_lenses") or {}) for d in facts.values())
    print(f"\n{'✅' if not fails else '❌'} lens coverage: {total} lenses, {fails} validation failures")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
