#!/usr/bin/env python3
"""
build_text_overlay_intelligence.py
Mine 699 text_overlay summaries × engagement.
English overlays 84% vs Arabic 61% — massive signal for brief direction.
Output: logs/text_overlay_intelligence.json
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

# Overlay content type classifier
def _classify_overlay(summary):
    s = summary.lower()
    if any(x in s for x in ["price","sar","ريال","riyal","%","offer","discount","free","مجان","خصم","عرض"]): return "price_offer"
    if any(x in s for x in ["logo","brand","name","شعار"]): return "brand_identity"
    if any(x in s for x in ["date","time","when","where","location","موعد","مكان"]): return "event_info"
    if any(x in s for x in ["cta","order","call","click","اطلب","تواصل","اشترك","حمل","download"]): return "cta"
    if any(x in s for x in ["product","item","new","جديد","منتج"]): return "product_name"
    if any(x in s for x in ["ingredient","recipe","how","كيف","طريقة","وصفة"]): return "how_to"
    if any(x in s for x in ["hashtag","#"]): return "hashtag"
    if any(x in s for x in ["quote","saying","مقولة","حكمة"]): return "quote"
    return "other"

def main():
    lang_eng    = defaultdict(list)
    type_eng    = defaultdict(list)
    overlay_count= 0
    sec_lang    = defaultdict(lambda: defaultdict(list))
    occ_lang    = defaultdict(lambda: defaultdict(list))

    # Track obs with vs without overlays
    has_overlay_eng = []
    no_overlay_eng  = []

    for f in OBS_ROOT.rglob("*.json"):
        d   = json.loads(f.read_text())
        e   = _eng(d)
        if e is None: continue
        vis = d.get("visual_observations",{})
        sec = d.get("sector","")
        occ = d.get("occasion","") or "evergreen"
        overlays = vis.get("text_overlays",[]) or []

        if overlays:
            has_overlay_eng.append(e)
        else:
            no_overlay_eng.append(e)

        for ov in overlays:
            if not isinstance(ov, dict): continue
            lang    = (ov.get("language","") or "").strip().lower()
            summary = (ov.get("content_summary","") or "").strip()
            overlay_count += 1

            if lang:
                lang_eng[lang].append(e)
                if sec: sec_lang[sec][lang].append(e)
                if occ: occ_lang[occ][lang].append(e)

            if summary:
                otype = _classify_overlay(summary)
                type_eng[otype].append(e)

    global_avg = _avg([v for vals in lang_eng.values() for v in vals]) or 0

    def _build(eng_dict, min_n=3):
        return {
            k: {"count":len(v),"avg_engagement":_avg(v),
                "lift_vs_avg":round((_avg(v) or 0)-global_avg,3)}
            for k,v in sorted(eng_dict.items(), key=lambda x:-(_avg(x[1]) or 0))
            if len(v) >= min_n
        }

    by_lang = _build(lang_eng, min_n=3)
    by_type = _build(type_eng, min_n=3)

    best_lang_by_sector = {
        sec: sorted([{"lang":k,"avg_engagement":_avg(v),"n":len(v)}
                     for k,v in langs.items() if len(v)>=3],
                    key=lambda x:-(x["avg_engagement"] or 0))[:3]
        for sec, langs in sec_lang.items()
    }

    # Has overlay vs no overlay
    overlay_lift = round((_avg(has_overlay_eng) or 0) - (_avg(no_overlay_eng) or 0), 3)

    rules = []
    if by_lang:
        best = list(by_lang.items())[0]
        worst = list(by_lang.items())[-1]
        rules.append(f"Best overlay language: '{best[0]}' ({best[1]['avg_engagement']:.0%}) vs '{worst[0]}' ({worst[1]['avg_engagement']:.0%})")
    rules.append(f"Has text overlay: {_avg(has_overlay_eng):.0%} vs no overlay: {_avg(no_overlay_eng):.0%} (lift {overlay_lift:+.2f})")
    if by_type:
        best_t = list(by_type.items())[0]
        rules.append(f"Best overlay type: '{best_t[0]}' ({best_t[1]['avg_engagement']:.0%})")

    out = {
        "total_overlays":     overlay_count,
        "obs_with_overlays":  len(has_overlay_eng),
        "obs_without":        len(no_overlay_eng),
        "has_overlay_avg":    _avg(has_overlay_eng),
        "no_overlay_avg":     _avg(no_overlay_eng),
        "overlay_presence_lift": overlay_lift,
        "global_avg":         round(global_avg,3),
        "by_language":        by_lang,
        "by_overlay_type":    by_type,
        "best_lang_by_sector":best_lang_by_sector,
        "agency_rules":       rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS/"text_overlay_intelligence.json").write_text(json.dumps(out,ensure_ascii=False,indent=2))

    print(f"Text overlay intelligence — {overlay_count} overlays  (global {global_avg:.0%})\n")
    print(f"Has overlay: {_avg(has_overlay_eng):.0%}  No overlay: {_avg(no_overlay_eng):.0%}  (lift {overlay_lift:+.2f})\n")
    print("By language:")
    for lang, data in by_lang.items():
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {lang:<20}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    print("\nBy overlay type:")
    for t, data in by_type.items():
        lift = f"+{data['lift_vs_avg']:.2f}" if data['lift_vs_avg']>=0 else f"{data['lift_vs_avg']:.2f}"
        print(f"  {t:<15}  {data['avg_engagement']:.0%}  lift {lift}  n={data['count']}")
    for r in rules: print(f"\n  ▸ {r}")
    print("  Output → logs/text_overlay_intelligence.json")

if __name__ == "__main__":
    main()
