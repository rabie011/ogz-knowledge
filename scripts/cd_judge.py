#!/usr/bin/env python3
"""
cd_judge.py — Judge a caption against its CD brain's methodology.

The quality gate checks MECHANICS (Saudi markers, product name, hashtags).
It scores 88% of output 90-100 — it cannot tell good from great.

This judge measures CREATIVE QUALITY: did the caption actually apply the
CD brain's methodology? It uses a strong model (gpt-4o) to score 4 axes:
  - technique:   did it use the signature technique?
  - register:    does the voice register match?
  - anti_pattern: did it AVOID the methodology's anti-patterns?
  - distinctive:  is it genuinely creative vs generic marketing?

This is the learning signal a real loop needs — specific, creative, scalable.

Usage:
    python3 scripts/cd_judge.py                    # head-to-head: generic vs CD brain (proof)
    python3 scripts/cd_judge.py --judge "caption" --brain cd_04_heritage_decoder
"""
from __future__ import annotations
import argparse, json, os, sys, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from lib.cd_brains import _load_brains, route, build_cd_prompt_block


def load_env():
    env = {}
    for line in (Path.home() / ".abraham_env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip('"\'')
    return env


JUDGE_PROMPT = """أنت ناقد إبداعي خبير في الإعلان السعودي. قيّم هذا الكابشن مقابل المنهجية الإبداعية المطلوبة.

المنهجية المطلوبة:
{methodology}

الكابشن المُقيَّم:
{caption}

قيّم على 4 محاور، كل محور من 0 إلى 10:
1. technique — هل طبّق التقنية المميزة للمنهجية فعلاً؟ (مش مجرد كلام عام)
2. register — هل السجل الصوتي يطابق المطلوب؟
3. anti_pattern — هل تجنّب أخطاء المنهجية؟ (10 = تجنّبها كلها)
4. distinctive — هل هو إبداعي ومميز فعلاً، مش كلام تسويقي عام؟

رد JSON فقط، بدون markdown:
{{"technique": N, "register": N, "anti_pattern": N, "distinctive": N, "verdict": "سبب قصير بالعربي — ما الذي نجح أو فشل"}}"""


def judge_caption(caption: str, brain_slug: str, api_key: str) -> dict:
    """Score a caption against a CD brain's methodology. Returns axis scores + verdict."""
    import openai
    client = openai.OpenAI(api_key=api_key)

    methodology = build_cd_prompt_block(brain_slug)
    prompt = JUDGE_PROMPT.format(methodology=methodology[:1200], caption=caption)

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",  # strong model for creative judgment
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = re.sub(r"```[a-z]*\n?", "", raw).strip("` ")
        d = json.loads(raw)
        axes = ["technique", "register", "anti_pattern", "distinctive"]
        d["total"] = round(sum(d.get(a, 0) for a in axes) / len(axes), 1)
        return d
    except Exception as e:
        return {"error": str(e)[:100], "total": 0}


def generate(brand: str, product: str, occasion: str, use_cd: bool, api_key: str) -> dict:
    """Generate a caption either with CD brain (live API) or generic prompt (direct)."""
    import urllib.request
    if use_cd:
        # Live API already uses CD brains
        payload = json.dumps({"brand": brand, "product": product, "occasion": occasion}).encode()
        req = urllib.request.Request("http://localhost:4100/api/create", data=payload,
                                     headers={"Content-Type": "application/json"}, method="POST")
        d = json.loads(urllib.request.urlopen(req, timeout=30).read())
        return {"caption": d["content"]["caption"], "cd_brain": d.get("creative_director", {}).get("primary")}
    else:
        # Generic prompt — the old "professional content writer"
        import openai
        client = openai.OpenAI(api_key=api_key)
        prompt = f"""أنت كاتب محتوى سعودي محترف تكتب لعلامة @{brand}. اكتب كابشن إنستغرام واحد فقط باللهجة السعودية.
المنتج: {product} | المناسبة: {occasion}
استخدم اللهجة السعودية، اسم المنتج في أول 5 كلمات، هاشتاق #{brand}.
اكتب الكابشن فقط:"""
        resp = client.chat.completions.create(model="gpt-4o-mini",
                                              messages=[{"role": "user", "content": prompt}],
                                              max_tokens=200, temperature=0.7)
        return {"caption": resp.choices[0].message.content.strip().strip('"\''), "cd_brain": None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--judge", help="Judge a single caption")
    parser.add_argument("--brain", help="CD brain slug for --judge")
    parser.add_argument("--pairs", type=int, default=8, help="Head-to-head pairs to run")
    args = parser.parse_args()

    env = load_env()
    api_key = env["OPENAI_API_KEY"]

    if args.judge:
        result = judge_caption(args.judge, args.brain or "cd_01_firaasa_architect", api_key)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Head-to-head: generic vs CD brain, judged by methodology
    test_briefs = [
        ("albaik", "بروستد", "founding_day"),
        ("roshnksa", "مشروع سكني", "national_day"),
        ("hashibasha", "حاشي باشا", "ramadan"),
        ("barnscoffee", "قهوة مختصة", "eid_al_fitr"),
        ("mikyajy", "روج", "ramadan"),
        ("tamimimarkets", "منتجات", "eid_al_adha"),
        ("altazaj_fakieh", "دجاج", "founding_day"),
        ("elixirbunn", "قهوة", "national_day"),
    ][:args.pairs]

    print(f"{'='*70}")
    print(f"HEAD-TO-HEAD: Generic prompt vs CD Brain — judged on methodology")
    print(f"{'='*70}\n")

    generic_totals, cd_totals = [], []
    for brand, product, occasion in test_briefs:
        # Which CD brain would this route to?
        cd_brain, _, _ = route(
            {"albaik":"f_and_b","roshnksa":"real_estate","hashibasha":"f_and_b",
             "barnscoffee":"f_and_b","mikyajy":"beauty_personal_care","tamimimarkets":"retail_lifestyle",
             "altazaj_fakieh":"f_and_b","elixirbunn":"f_and_b"}.get(brand,"f_and_b"),
            occasion)

        gen = generate(brand, product, occasion, use_cd=False, api_key=api_key)
        cd  = generate(brand, product, occasion, use_cd=True, api_key=api_key)

        gen_score = judge_caption(gen["caption"], cd_brain, api_key)
        cd_score  = judge_caption(cd["caption"], cd_brain, api_key)

        generic_totals.append(gen_score.get("total", 0))
        cd_totals.append(cd_score.get("total", 0))

        print(f"@{brand} | {occasion} | brain: {cd_brain}")
        print(f"  GENERIC  {gen_score.get('total',0):>4}/10  {gen['caption'][:75]}")
        print(f"  CD BRAIN {cd_score.get('total',0):>4}/10  {cd['caption'][:75]}")
        print(f"  judge (CD): {cd_score.get('verdict','')[:80]}")
        print()

    g_avg = sum(generic_totals)/len(generic_totals) if generic_totals else 0
    c_avg = sum(cd_totals)/len(cd_totals) if cd_totals else 0
    print(f"{'='*70}")
    print(f"  GENERIC prompt avg:  {g_avg:.1f}/10")
    print(f"  CD BRAIN avg:        {c_avg:.1f}/10")
    print(f"  LIFT:                {c_avg-g_avg:+.1f} ({(c_avg-g_avg)/max(g_avg,0.1)*100:+.0f}%)")
    print(f"{'='*70}")

    # Write result for the record
    out = REPO / "logs" / "system" / "cd_judge_headtohead.json"
    out.write_text(json.dumps({
        "generic_avg": round(g_avg,2), "cd_avg": round(c_avg,2),
        "lift": round(c_avg-g_avg,2), "pairs": len(test_briefs),
    }, ensure_ascii=False, indent=2))
    print(f"\nSaved → {out}")


if __name__ == "__main__":
    main()
