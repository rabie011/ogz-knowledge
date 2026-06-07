#!/usr/bin/env python3
"""
cd_technique_scan.py — Run the 5 CD-brain lenses over REAL Saudi captions.

Direction B: instead of using CD brains to WRITE, use them to ANALYZE.
For each real caption (with real likes), detect which CD technique it uses.
Then cross-reference with engagement: which techniques drove the most likes
in actual Saudi Instagram posts?

This turns the knowledge base into a creative-pattern-discovery layer.

Usage:
    python3 scripts/cd_technique_scan.py            # sample 300 real captions
    python3 scripts/cd_technique_scan.py --n 600
    python3 scripts/cd_technique_scan.py --tier gold   # only gold tier
"""
from __future__ import annotations
import argparse, json, os, re, sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TLIB = REPO / "11_who_to_learn_from" / "template_library.json"


def load_env():
    env = {}
    for line in (Path.home() / ".abraham_env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k] = v.strip('"\'')
    return env


TECHNIQUES = {
    "double_meaning":     "كلمة بمعنيين كمفتاح (الـ Heritage Decoder)",
    "performance_reality":"تباين الأداء مقابل الواقع (الـ Authenticity Detective)",
    "counterintuitive":   "قلب مضاد للحدس (الـ Paradox Hunter)",
    "metaphor_system":    "نظام استعاري كامل (الـ Metaphor Architect)",
    "human_truth":        "حقيقة إنسانية قبل المنتج (الـ Firaasa Architect)",
    "none":               "لا تقنية إبداعية — تسويق مباشر",
}

DETECT_PROMPT = """حلّل هذا الكابشن السعودي. أي تقنية إبداعية يستخدم؟

الكابشن: {caption}

التقنيات:
- double_meaning: كلمة عربية بمعنيين كلاهما صحيح، تُستخدم كمفتاح هيكلي
- performance_reality: تباين بين مشهد "أداء/تظاهر" ومشهد "حقيقة"
- counterintuitive: يبدأ بقلب توقع الجمهور بثقة
- metaphor_system: استعارة ممتدة تبني نظام كامل
- human_truth: يبدأ بحقيقة إنسانية عميقة قبل ذكر المنتج
- none: تسويق مباشر بدون تقنية إبداعية

رد JSON فقط: {{"technique": "اسم_التقنية", "evidence": "الدليل بكلمتين"}}"""


def detect(caption: str, client) -> str:
    prompt = DETECT_PROMPT.format(caption=caption[:300])
    try:
        r = client.chat.completions.create(model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}], max_tokens=60, temperature=0)
        raw = r.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = re.sub(r"```[a-z]*\n?", "", raw).strip("` ")
        d = json.loads(raw)
        t = d.get("technique", "none")
        return t if t in TECHNIQUES else "none"
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=300)
    parser.add_argument("--tier", help="Filter to one tier (gold/silver/bronze)")
    args = parser.parse_args()

    env = load_env()
    import openai
    client = openai.OpenAI(api_key=env["OPENAI_API_KEY"])

    tlib = json.loads(TLIB.read_text()).get("templates", [])
    # Real captions with real likes only
    pool = [t for t in tlib if (t.get("original_likes") or 0) > 0
            and re.search(r'[؀-ۿ]', t.get("caption", ""))
            and (not args.tier or t.get("tier") == args.tier)]
    # Sort by likes desc, sample top N (the high-engagement ones we want to learn from)
    pool.sort(key=lambda t: -(t.get("original_likes") or 0))
    sample = pool[:args.n]

    print(f"Scanning {len(sample)} real Saudi captions (with real likes) through 5 CD lenses...\n")

    def classify(t):
        tech = detect(t.get("caption", ""), client)
        return {"technique": tech, "likes": t.get("original_likes") or 0,
                "sector": t.get("sector", "?"), "occasion": t.get("occasion", "?"),
                "tier": t.get("tier", "?")} if tech else None

    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for i, r in enumerate(ex.map(classify, sample)):
            if r:
                results.append(r)
                if (i+1) % 50 == 0:
                    print(f"  ...{i+1}/{len(sample)}")

    if not results:
        print("No results"); return

    # Aggregate: prevalence + avg likes per technique
    by_tech = defaultdict(list)
    for r in results:
        by_tech[r["technique"]].append(r["likes"])

    overall_avg = sum(r["likes"] for r in results) / len(results)

    print(f"\n{'='*64}")
    print(f"  CD TECHNIQUE SCAN — {len(results)} real Saudi captions")
    print(f"  overall avg likes: {overall_avg:,.0f}")
    print(f"{'='*64}")
    print(f"  {'technique':<22}{'count':>6}{'%':>6}{'avg likes':>12}{'vs avg':>9}")
    print(f"  {'-'*58}")
    rows = []
    for tech in sorted(by_tech, key=lambda t: -sum(by_tech[t])/len(by_tech[t])):
        likes = by_tech[tech]
        avg = sum(likes)/len(likes)
        pct = len(likes)/len(results)*100
        lift = (avg/overall_avg - 1) * 100
        rows.append((tech, len(likes), pct, avg, lift))
        print(f"  {tech:<22}{len(likes):>6}{pct:>5.0f}%{avg:>12,.0f}{lift:>+8.0f}%")

    print(f"\n  KEY FINDINGS:")
    used = [r for r in rows if r[0] != "none"]
    if used:
        best = max(used, key=lambda r: r[3])
        none_avg = next((r[3] for r in rows if r[0]=="none"), overall_avg)
        print(f"  • Highest-engagement technique: {best[0]} (avg {best[3]:,.0f} likes, {best[4]:+.0f}% vs avg)")
        creative = sum(r[1] for r in used)
        print(f"  • {creative}/{len(results)} ({creative/len(results)*100:.0f}%) of top Saudi captions use a creative technique")
        none_count = next((r[1] for r in rows if r[0]=="none"), 0)
        if none_count:
            best_lift = (best[3]/none_avg - 1)*100 if none_avg else 0
            print(f"  • Captions with a technique vs plain marketing: {best[0]} gets {best_lift:+.0f}% more likes than 'none'")

    out = REPO / "logs" / "system" / "cd_technique_scan.json"
    out.write_text(json.dumps({
        "scanned": len(results), "overall_avg_likes": round(overall_avg),
        "by_technique": {t: {"count": len(l), "avg_likes": round(sum(l)/len(l))} for t, l in by_tech.items()},
    }, ensure_ascii=False, indent=2))
    print(f"\n  Saved → {out}")


if __name__ == "__main__":
    main()
