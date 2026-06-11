#!/usr/bin/env python3
# ⚠️ DEPRECATED-JUDGE 2026-06-11: this rewards the V3 technique taste the founder
# rejected (audit: old judge buried clean options 240/240). Superseded by: founder ratings (logs/cross_preferences.json) + scorer_v2.
import sys as _s
if "--legacy" not in _s.argv:
    _s.exit("DEPRECATED: old-judge era. Use founder ratings (logs/cross_preferences.json) + scorer_v2. (--legacy to override)")

"""
build_calibration_set.py — Generate captions + judge them, prep for human review.

Purpose: validate the gpt-4o methodology judge against Mohamed's taste.
  1. Generate N captions on the LIVE engine (CD brain + mini — production config)
  2. Judge each with cd_judge (methodology score) — stored HIDDEN
  3. Write review_data.json (round 3) for the mobile UI
  4. Mohamed rates BLIND (excellent/good/weak/fail) — doesn't see judge score
  5. Later: scripts/calibrate_judge.py compares his ratings to judge scores

If his ratings align with the judge → trust the judge for all auto-testing.
If not → recalibrate the judge prompt.

Usage:
    python3 scripts/build_calibration_set.py            # 30 captions
    python3 scripts/build_calibration_set.py --n 20
"""
from __future__ import annotations
import argparse, json, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from cd_judge import judge_caption


def load_env():
    env = {}
    for line in (Path.home() / ".abraham_env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip('"\'')
    return env


# Diverse — all 6 sectors, spread of occasions, strong + weak brands
BRIEFS = [
    ("albaik","بروستد","founding_day"), ("barnscoffee","قهوة مختصة","ramadan"),
    ("hashibasha","حاشي باشا","eid_al_adha"), ("mcdonaldsksa","ماك","riyadh_season"),
    ("altazaj_fakieh","دجاج","national_day"), ("elixirbunn","قهوة","evergreen"),
    ("mikyajy","روج","ramadan"), ("asteribeautysa","مكياج","eid_al_fitr"),
    ("niceonesa","عطر","evergreen"), ("tamimimarkets","منتجات","eid_al_fitr"),
    ("pandasaudi","منتجات","ramadan"), ("mumzworld","منتجات أطفال","evergreen"),
    ("maxfashionmena","إطلالات","eid_al_fitr"), ("kiabiksa","ملابس أطفال","national_day"),
    ("roshnksa","مشروع سكني","national_day"), ("roshnksa","مشروع سكني","founding_day"),
    ("myfitness.sa","اشتراك","evergreen"), ("albaik","بروستد","ramadan"),
    ("barnscoffee","قهوة","national_day"), ("mikyajy","روج","eid_al_fitr"),
    ("tamimimarkets","منتجات","founding_day"), ("hashibasha","حاشي باشا","jeddah_season"),
    ("pandasaudi","منتجات","white_friday"), ("elixirbunn","قهوة","founding_day"),
    ("mcdonaldsksa","ماك","evergreen"), ("niceonesa","عطر","ramadan"),
    ("maxfashionmena","إطلالات","riyadh_season"), ("asteribeautysa","مكياج","evergreen"),
    ("altazaj_fakieh","دجاج","ramadan"), ("kiabiksa","ملابس","eid_al_fitr"),
]

SECTOR = {
    "albaik":"f_and_b","barnscoffee":"f_and_b","hashibasha":"f_and_b","mcdonaldsksa":"f_and_b",
    "altazaj_fakieh":"f_and_b","elixirbunn":"f_and_b","mikyajy":"beauty_personal_care",
    "asteribeautysa":"beauty_personal_care","niceonesa":"beauty_personal_care",
    "tamimimarkets":"retail_lifestyle","pandasaudi":"retail_lifestyle","mumzworld":"retail_lifestyle",
    "maxfashionmena":"fashion","kiabiksa":"fashion","roshnksa":"real_estate","myfitness.sa":"healthcare_wellness",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=30)
    args = parser.parse_args()
    env = load_env()
    api_key = env["OPENAI_API_KEY"]

    briefs = BRIEFS[:args.n]
    print(f"Generating + judging {len(briefs)} captions on live engine (CD brain + mini)...\n")

    def run(idx_brief):
        idx, (brand, product, occ) = idx_brief
        try:
            payload = json.dumps({"brand": brand, "product": product, "occasion": occ}).encode()
            req = urllib.request.Request("http://localhost:4100/api/create", data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            d = json.loads(urllib.request.urlopen(req, timeout=30).read())
            caption = d["content"]["caption"]
            brain = d.get("creative_director", {}).get("primary", "")
            jscore = judge_caption(caption, brain, api_key).get("total")
            return {
                "id": idx + 1, "brand": brand, "occasion": occ,
                "sector": SECTOR.get(brand, "?"), "arabic": caption,
                "tier": d.get("quality", {}).get("template_tier", ""),
                "score": d.get("quality", {}).get("score", 0),     # mechanical gate (shown)
                "cd_brain": brain,
                "judge_score": jscore,                              # HIDDEN — for calibration
                "confidence": d.get("quality", {}).get("confidence", ""),
            }
        except Exception as e:
            return None

    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for r in pool.map(run, enumerate(briefs)):
            if r:
                results.append(r)
                js = r["judge_score"]
                print(f"  #{r['id']:>2} {r['brand']:<16} {r['occasion']:<14} judge={js}")

    # Write review data (judge_score stays in the object but UI won't display it)
    out = REPO / "logs" / "system" / "review_data.json"
    # Archive previous results if any
    prev = REPO / "logs" / "system" / "review_results.json"
    if prev.exists():
        (REPO / "logs" / "system" / "review_results_prev.json").write_text(prev.read_text())
        prev.unlink()
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))

    scored = [r["judge_score"] for r in results if r["judge_score"] is not None]
    print(f"\n{'='*55}")
    print(f"  Generated {len(results)} | judge scored {len(scored)}")
    if scored:
        print(f"  Judge score avg: {sum(scored)/len(scored):.1f}/10")
        print(f"  Distribution: 8+:{sum(1 for s in scored if s>=8)} "
              f"6-8:{sum(1 for s in scored if 6<=s<8)} <6:{sum(1 for s in scored if s<6)}")
    print(f"{'='*55}")
    print(f"  → review_data.json ready ({len(results)} captions)")
    print(f"  → Mohamed rates blind on /review (round 3)")
    print(f"  → then: python3 scripts/calibrate_judge.py")


if __name__ == "__main__":
    main()
