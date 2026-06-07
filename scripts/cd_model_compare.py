#!/usr/bin/env python3
"""
cd_model_compare.py — Rigorous mini vs gpt-4o comparison for CD-brain generation.

Both models get the IDENTICAL prompt (CD brain methodology + extracted real
templates). Only the model differs. Judged on methodology by gpt-4o.

Reports:
  - avg score per model
  - WIN RATE (how often gpt-4o > mini head-to-head) — robust to judge variance
  - per-sector and per-occasion breakdown — shows WHERE gpt-4o helps most

Usage:
    python3 scripts/cd_model_compare.py            # full 24-brief matrix
    python3 scripts/cd_model_compare.py --pairs 12
"""
from __future__ import annotations
import argparse, json, os, sys, re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from lib.cd_brains import route, build_cd_prompt_block
from cd_judge import judge_caption

ARABIC = re.compile(r'[؀-ۿ]')


def load_env():
    env = {}
    for line in (Path.home() / ".abraham_env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip('"\'')
    return env


# Diverse matrix — all 6 sectors × spread of occasions
BRIEFS = [
    ("albaik", "بروستد", "founding_day", "f_and_b"),
    ("barnscoffee", "قهوة مختصة", "ramadan", "f_and_b"),
    ("hashibasha", "حاشي باشا", "eid_al_adha", "f_and_b"),
    ("mcdonaldsksa", "ماك", "riyadh_season", "f_and_b"),
    ("altazaj_fakieh", "دجاج", "national_day", "f_and_b"),
    ("elixirbunn", "قهوة", "evergreen", "f_and_b"),
    ("mikyajy", "روج", "ramadan", "beauty_personal_care"),
    ("asteribeautysa", "مكياج", "eid_al_fitr", "beauty_personal_care"),
    ("niceonesa", "عطر", "evergreen", "beauty_personal_care"),
    ("tamimimarkets", "منتجات", "eid_al_fitr", "retail_lifestyle"),
    ("pandasaudi", "منتجات", "ramadan", "retail_lifestyle"),
    ("mumzworld", "منتجات أطفال", "evergreen", "retail_lifestyle"),
    ("maxfashionmena", "إطلالات", "eid_al_fitr", "fashion"),
    ("kiabiksa", "ملابس أطفال", "national_day", "fashion"),
    ("roshnksa", "مشروع سكني", "national_day", "real_estate"),
    ("roshnksa", "مشروع سكني", "founding_day", "real_estate"),
    ("myfitness.sa", "اشتراك", "evergreen", "healthcare_wellness"),
    ("albaik", "بروستد", "ramadan", "f_and_b"),
    ("barnscoffee", "قهوة", "national_day", "f_and_b"),
    ("mikyajy", "روج", "eid_al_fitr", "beauty_personal_care"),
    ("tamimimarkets", "منتجات", "founding_day", "retail_lifestyle"),
    ("hashibasha", "حاشي باشا", "jeddah_season", "f_and_b"),
    ("pandasaudi", "منتجات", "white_friday", "retail_lifestyle"),
    ("elixirbunn", "قهوة", "founding_day", "f_and_b"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=int, default=len(BRIEFS))
    args = parser.parse_args()

    env = load_env()
    api_key = env["OPENAI_API_KEY"]
    import openai
    client = openai.OpenAI(api_key=api_key)

    intel = json.loads((REPO / "11_who_to_learn_from" / "intelligence_layer.json").read_text())
    tlib = json.loads((REPO / "11_who_to_learn_from" / "template_library.json").read_text()).get("templates", [])
    ar_templates = [t for t in tlib if ARABIC.search(t.get("caption", ""))]

    def get_templates(sector, occ):
        out = []
        for tier in ["gold", "silver", "bronze", "unverified", "generated"]:
            f = [t for t in ar_templates if t.get("sector") == sector and t.get("tier") == tier
                 and t.get("occasion") in (occ, "evergreen")]
            out.extend(f[:3])
            if len(out) >= 3:
                break
        return out[:5]

    def build_prompt(brand, product, occ, sector):
        cd_brain, _, _ = route(sector, occ)
        block = build_cd_prompt_block(cd_brain)
        tmpls = get_templates(sector, occ)
        ttext = "\n".join(f'- {t["caption"][:150]}' for t in tmpls)
        pn = intel.get("brand_product_names", {}).get(brand, {})
        correct = pn.get("correct", product)
        occ_words = "، ".join(intel.get("occasion_required_words", {}).get(occ, []))
        sig = intel.get("brand_profiles", {}).get(brand, {}).get("signature_phrases", [])
        ar = [s for s in sig if ARABIC.search(s)]
        tag = ar[0] if ar else f"#{brand}"
        return f"""أنت مخرج إبداعي سعودي تكتب لعلامة @{brand}. اكتب كابشن إنستغرام واحد فقط.
{block}
المنتج: {product} (بالعربي: {correct}، في أول 5 كلمات)
المناسبة: {occ} | الكلمات المطلوبة: {occ_words}
الهاشتاق: {tag}
═══ أمثلة حقيقية (التزم بأسلوبها، لا تنسخ) ═══
{ttext}
قواعد: عربي 100% ممنوع الإنجليزي واسم العلامة بالإنجليزي. اللهجة السعودية. اربط التقنية بالمنتج. طبّق التقنية المميزة فعلياً.
اكتب الكابشن فقط:""", cd_brain

    def run_pair(brief):
        brand, product, occ, sector = brief
        prompt, cd_brain = build_prompt(brand, product, occ, sector)
        try:
            mini = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}],
                                                  max_tokens=220, temperature=0.5).choices[0].message.content.strip().strip('"\'')
            gpt = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}],
                                                 max_tokens=220, temperature=0.5).choices[0].message.content.strip().strip('"\'')
            mj = judge_caption(mini, cd_brain, api_key).get("total")
            gj = judge_caption(gpt, cd_brain, api_key).get("total")
            if mj is None or gj is None:
                return None  # judge failed — exclude rather than pollute with 0
            return {"brand": brand, "occasion": occ, "sector": sector, "brain": cd_brain,
                    "mini": mj, "gpt4o": gj, "mini_cap": mini, "gpt_cap": gpt}
        except Exception as e:
            return None

    briefs = BRIEFS[:args.pairs]
    print(f"Running {len(briefs)} pairs (mini vs gpt-4o, same prompt)...\n")

    results = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        for r in pool.map(run_pair, briefs):
            if r:
                results.append(r)
                w = "4o" if r["gpt4o"] > r["mini"] else ("mini" if r["mini"] > r["gpt4o"] else "tie")
                print(f"  {r['brand']:<16} {r['occasion']:<14} {r['brain'][:6]} | mini {r['mini']:>4} | 4o {r['gpt4o']:>4} | win: {w}")

    if not results:
        print("No results"); return

    mini_avg = sum(r["mini"] for r in results) / len(results)
    gpt_avg = sum(r["gpt4o"] for r in results) / len(results)
    gpt_wins = sum(1 for r in results if r["gpt4o"] > r["mini"])
    mini_wins = sum(1 for r in results if r["mini"] > r["gpt4o"])
    ties = len(results) - gpt_wins - mini_wins

    print(f"\n{'='*60}")
    print(f"  Pairs:        {len(results)}")
    print(f"  mini avg:     {mini_avg:.2f}/10")
    print(f"  gpt-4o avg:   {gpt_avg:.2f}/10   (lift {gpt_avg-mini_avg:+.2f})")
    print(f"  WIN RATE:     gpt-4o {gpt_wins} | mini {mini_wins} | tie {ties}")
    print(f"                gpt-4o wins {gpt_wins/len(results)*100:.0f}% of head-to-head")
    print(f"{'='*60}")

    # Per-sector
    print(f"\n  Per-sector (where gpt-4o helps most):")
    by_sec = defaultdict(lambda: {"mini": [], "gpt": []})
    for r in results:
        by_sec[r["sector"]]["mini"].append(r["mini"])
        by_sec[r["sector"]]["gpt"].append(r["gpt4o"])
    for sec in sorted(by_sec, key=lambda s: -(sum(by_sec[s]["gpt"])/len(by_sec[s]["gpt"]) - sum(by_sec[s]["mini"])/len(by_sec[s]["mini"]))):
        d = by_sec[sec]
        m = sum(d["mini"])/len(d["mini"]); g = sum(d["gpt"])/len(d["gpt"])
        print(f"    {sec:<24} mini {m:.1f} → 4o {g:.1f}  ({g-m:+.1f})  n={len(d['mini'])}")

    out = REPO / "logs" / "system" / "cd_model_compare.json"
    out.write_text(json.dumps({
        "pairs": len(results), "mini_avg": round(mini_avg,2), "gpt4o_avg": round(gpt_avg,2),
        "gpt_win_rate": round(gpt_wins/len(results),2), "gpt_wins": gpt_wins, "mini_wins": mini_wins, "ties": ties,
        "results": [{k:v for k,v in r.items() if k not in ('mini_cap','gpt_cap')} for r in results],
    }, ensure_ascii=False, indent=2))
    print(f"\n  Saved → {out}")


if __name__ == "__main__":
    main()
