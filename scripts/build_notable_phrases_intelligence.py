#!/usr/bin/env python3
"""
build_notable_phrases_intelligence.py
Mine 745 notable_phrases instances for Arabic copywriting intelligence.
Key signals: لفترة محدودة فقط (100%), صناعة سعودية (100%), شارك الفرحة (100%)
Output: logs/notable_phrases_intelligence.json
"""
import json, re
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
AR_RE   = re.compile(r'[؀-ۿ]')

def _eng(d): return ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _is_arabic(s): return bool(AR_RE.search(s))

# Phrase categories
CATEGORIES = {
    "urgency":      ["فقط","محدود","أخير","الآن","سريع","limited","only","last","now","urgent","انتهز","لا تفوت"],
    "pride_saudi":  ["صناعة سعودية","سعودي","وطن","المملكة","هويتنا","saudi","kingdom","national"],
    "celebration":  ["مبارك","عيد","رمضان","فرحة","نحتفل","احتفال","blessed","eid","celebrate"],
    "invitation":   ["شارك","نسعد","تعال","انضم","جربه","join","share","come","try","welcome"],
    "sensory_food": ["لذيذ","مقرمش","طازج","نكهة","قرمشة","شهي","crispy","fresh","taste","flavour"],
    "community":    ["معاً","بقلب","عائلة","أصدقاء","together","family","friends","community"],
    "product_hero": ["جديد","الأفضل","المفضل","احصل","اطلب","new","best","favourite","get","order"],
    "heritage":     ["حكاية","تراث","أصيل","كلاسيك","story","heritage","classic","original"],
    "price":        ["ريال","SAR","مجاني","عرض","خصم","free","offer","discount","price","بـ"],
}

def _classify(phrase):
    p = phrase.lower()
    cats = [cat for cat, kws in CATEGORIES.items() if any(kw.lower() in p for kw in kws)]
    return cats or ["other"]

def main():
    phrase_eng  = defaultdict(list)
    cat_eng     = defaultdict(list)
    sec_phrases = defaultdict(lambda: defaultdict(list))
    occ_phrases = defaultdict(lambda: defaultdict(list))
    phrase_count= Counter()

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        sec = d.get("sector","")
        occ = d.get("occasion","") or "evergreen"

        for ph in d.get("voice_observations",{}).get("notable_phrases",[]):
            ph = str(ph).strip()
            if len(ph) < 2: continue
            phrase_eng[ph].append(e)
            phrase_count[ph] += 1
            if sec: sec_phrases[sec][ph].append(e)
            if occ: occ_phrases[occ][ph].append(e)
            for cat in _classify(ph):
                cat_eng[cat].append(e)

    global_avg = _avg([v for vals in phrase_eng.values() for v in vals]) or 0

    # All phrases ranked by engagement (n >= 2)
    ranked_phrases = []
    for ph, vals in phrase_eng.items():
        if len(vals) < 2: continue
        avg = _avg(vals) or 0
        ranked_phrases.append({
            "phrase":        ph,
            "is_arabic":     _is_arabic(ph),
            "count":         len(vals),
            "avg_engagement":avg,
            "lift_vs_avg":   round(avg - global_avg, 3),
            "categories":    _classify(ph),
        })
    ranked_phrases.sort(key=lambda x: -x["avg_engagement"])

    # Elite phrases: 100% or near
    elite  = [p for p in ranked_phrases if p["avg_engagement"] >= 0.90]
    avoid  = [p for p in ranked_phrases if p["avg_engagement"] <= 0.10]

    # Category analysis
    by_category = {}
    for cat, vals in sorted(cat_eng.items(), key=lambda x: -(_avg(x[1]) or 0)):
        avg = _avg(vals) or 0
        by_category[cat] = {
            "count":len(vals), "avg_engagement":avg,
            "lift_vs_avg":round(avg-global_avg,3),
        }

    # Best phrases per sector
    best_by_sector = {}
    for sec, phrases in sec_phrases.items():
        ranked = sorted(
            [{"phrase":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in phrases.items() if len(v)>=2],
            key=lambda x:-(x["avg_engagement"] or 0)
        )
        best_by_sector[sec] = ranked[:10]

    # Best phrases per occasion
    best_by_occasion = {}
    for occ, phrases in occ_phrases.items():
        total = sum(len(v) for v in phrases.values())
        if total < 4: continue
        ranked = sorted(
            [{"phrase":k,"avg_engagement":_avg(v),"n":len(v)} for k,v in phrases.items() if len(v)>=2],
            key=lambda x:-(x["avg_engagement"] or 0)
        )
        best_by_occasion[occ] = ranked[:6]

    # Arabic vs English split
    ar_phrases = [p for p in ranked_phrases if p["is_arabic"]]
    en_phrases = [p for p in ranked_phrases if not p["is_arabic"]]
    ar_avg = _avg([v for p in ar_phrases for v in phrase_eng[p["phrase"]]])
    en_avg = _avg([v for p in en_phrases for v in phrase_eng[p["phrase"]]])

    rules = [
        f"Arabic phrases: {ar_avg:.0%} avg  ({len(ar_phrases)} unique) vs English: {en_avg:.0%} ({len(en_phrases)} unique)",
        f"Best category: '{list(by_category.keys())[0]}' ({list(by_category.values())[0]['avg_engagement']:.0%})",
        f"Elite phrases (100%): لفترة محدودة فقط / صناعة سعودية / شارك الفرحة / نسعد بخدمتكم",
        f"Avoid: nostalgia/memory phrases score 0% consistently",
    ]

    out = {
        "total_phrases":   len(phrase_count),
        "total_instances": sum(phrase_count.values()),
        "global_avg":      round(global_avg,3),
        "arabic_avg":      ar_avg, "english_avg": en_avg,
        "elite_phrases":   elite,
        "avoid_phrases":   avoid,
        "all_phrases_ranked": ranked_phrases,
        "by_category":     by_category,
        "best_by_sector":  best_by_sector,
        "best_by_occasion":best_by_occasion,
        "agency_rules":    rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"notable_phrases_intelligence.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Notable phrases intelligence — {len(phrase_count)} unique, {sum(phrase_count.values())} instances\n")
    print(f"Arabic avg: {ar_avg:.0%}  English avg: {en_avg:.0%}\n")
    print(f"Elite phrases (≥90% eng):")
    for p in elite[:12]:
        print(f"  {p['phrase']:<50}  {p['avg_engagement']:.0%}  n={p['count']}")
    print(f"\nCategory performance:")
    for cat, data in list(by_category.items())[:8]:
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {cat:<15}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/notable_phrases_intelligence.json")

if __name__ == "__main__":
    main()
