#!/usr/bin/env python3
"""
build_text_overlay_analysis.py
Mine text_overlays — 399 structured records, completely unmined.
Each obs has: [{'language': 'arabic', 'content_summary': '...'}]
Agency questions:
  - Does Arabic text overlay on video/image help engagement?
  - Arabic vs English vs bilingual overlay — which performs best?
  - What type of text overlay (title/price/CTA/brand name) drives engagement?
  - Does overlay presence hurt authentic content (too commercial)?
Output: logs/text_overlay_analysis.json
"""
import json
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
CORPUS_BASELINE = 0.54

# Overlay content type inference from content_summary keywords
OVERLAY_TYPE_KEYWORDS = [
    ("price_offer",    ["price","ريال","sar","discount","offer","off%","promo","خصم","عرض"]),
    ("product_name",   ["new","جديد","product","menu","item","burger","coffee","قهوة","بروغر","تجربة"]),
    ("occasion_title", ["national","eid","ramadan","founding","يوم","عيد","رمضان","تأسيس","احتفال"]),
    ("brand_identity", ["logo","brand","sign","name","@","#"]),
    ("storytelling",   ["story","حكاية","journey","رحلة","since","since ","منذ","تاريخ"]),
    ("trivia_question",["?","question","guess","quiz","trivia","أين","كيف","ماذا","من"]),
    ("cta_overlay",    ["now","الآن","download","حمل","order","اطلب","visit","زور","follow","تابع"]),
]


def classify_overlay(content_summary: str) -> str:
    cs = str(content_summary).lower()
    for cat, kws in OVERLAY_TYPE_KEYWORDS:
        if any(k in cs for k in kws):
            return cat
    return "other"


def main():
    # Presence: has overlay vs no overlay
    has_overlay = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    # Overlay language
    by_lang     = defaultdict(lambda: {"count":0,"high":0,"sum":0.0,"sectors":Counter()})
    # Overlay content type
    by_type     = defaultdict(lambda: {"count":0,"high":0,"sum":0.0})
    # Lang × sector
    lang_sector = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # Lang × media_type
    lang_media  = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # Lang × occasion
    lang_occ    = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))
    # Type × engagement
    type_sector = defaultdict(lambda: defaultdict(lambda: {"count":0,"high":0}))

    total = 0
    obs_with_overlay = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        total += 1
        vv   = data.get("visual_observations",{}) or {}
        qa   = data.get("quality_assessment",{}) or {}
        cn   = data.get("cultural_notes",{}) or {}
        cr   = data.get("content_ref",{}) or {}

        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector","unknown") or "unknown"
        occ     = str(cn.get("occasion_relevance","") or "evergreen").lower() or "evergreen"
        media   = str(cr.get("content_type","") or "").lower() or "unknown"

        overlays = vv.get("text_overlays") or []
        if isinstance(overlays, str):
            try:
                import ast
                overlays = ast.literal_eval(overlays)
            except:
                overlays = []

        if not isinstance(overlays, list):
            overlays = []

        # Filter out empty/None entries
        overlays = [o for o in overlays if isinstance(o, dict) and o.get("language")]

        present_label = "has_overlay" if overlays else "no_overlay"
        has_overlay[present_label]["count"]  += 1
        has_overlay[present_label]["high"]   += is_high
        has_overlay[present_label]["sum"]    += eng

        if not overlays:
            continue

        obs_with_overlay += 1

        # Use first overlay (primary) for analysis
        primary = overlays[0]
        lang = str(primary.get("language","") or "").lower().strip()
        content_summary = str(primary.get("content_summary","") or "")

        # Normalize language
        if "bilingual" in lang or ("english" in lang and "arabic" in lang):
            lang = "bilingual"
        elif "arabic" in lang:
            lang = "arabic"
        elif "english" in lang:
            lang = "english"
        else:
            lang = lang or "unknown"

        overlay_type = classify_overlay(content_summary)

        by_lang[lang]["count"]   += 1
        by_lang[lang]["high"]    += is_high
        by_lang[lang]["sum"]     += eng
        by_lang[lang]["sectors"][sector] += 1

        by_type[overlay_type]["count"] += 1
        by_type[overlay_type]["high"]  += is_high
        by_type[overlay_type]["sum"]   += eng

        lang_sector[lang][sector]["count"] += 1
        lang_sector[lang][sector]["high"]  += is_high

        lang_media[lang][media]["count"]   += 1
        lang_media[lang][media]["high"]    += is_high

        lang_occ[lang][occ]["count"]       += 1
        lang_occ[lang][occ]["high"]        += is_high

        type_sector[overlay_type][sector]["count"] += 1
        type_sector[overlay_type][sector]["high"]  += is_high

    def rate(d): return round(d["high"]/d["count"], 3) if d["count"] else 0

    # Presence table
    presence_table = []
    for label, d in has_overlay.items():
        n = d["count"]
        r = round(d["high"]/n, 3) if n else 0
        presence_table.append({
            "overlay_presence": label, "count": n,
            "high_engagement_rate": r,
            "avg_engagement": round(d["sum"]/n, 3) if n else 0,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
        })
    presence_table.sort(key=lambda x: -x["high_engagement_rate"])

    # Language table
    lang_table = []
    for lang, d in by_lang.items():
        n = d["count"]
        r = round(d["high"]/n, 3) if n else 0
        lang_table.append({
            "overlay_language": lang, "count": n,
            "high_engagement_rate": r,
            "avg_engagement": round(d["sum"]/n, 3) if n else 0,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
            "top_sector": d["sectors"].most_common(1)[0][0] if d["sectors"] else None,
        })
    lang_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["count"]))

    # Content type table
    type_table = []
    for t, d in by_type.items():
        n = d["count"]
        r = round(d["high"]/n, 3) if n else 0
        type_table.append({
            "overlay_type": t, "count": n,
            "high_engagement_rate": r,
            "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
        })
    type_table.sort(key=lambda x: (-x["high_engagement_rate"], -x["count"]))

    # Lang × occasion
    lang_occ_rows = []
    for lang, occs in lang_occ.items():
        for occ, d in occs.items():
            n = d["count"]
            r = round(d["high"]/n, 3) if n else 0
            if n >= 2:
                lang_occ_rows.append({
                    "language": lang, "occasion": occ, "count": n,
                    "high_eng_rate": r, "lift": round(r - CORPUS_BASELINE, 3)
                })
    lang_occ_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Findings
    findings = []
    has_o = next((r for r in presence_table if r["overlay_presence"]=="has_overlay"), None)
    no_o  = next((r for r in presence_table if r["overlay_presence"]=="no_overlay"), None)
    if has_o and no_o:
        diff = has_o["high_engagement_rate"] - no_o["high_engagement_rate"]
        effect = "HELPS" if diff > 0.05 else "HURTS" if diff < -0.05 else "NEUTRAL"
        findings.append(
            f"Text overlay {effect} engagement: "
            f"with_overlay={int(has_o['high_engagement_rate']*100)}% vs without={int(no_o['high_engagement_rate']*100)}% "
            f"({'+'if diff>=0 else ''}{int(diff*100)}pp)"
        )
    if lang_table:
        best = lang_table[0]
        findings.append(f"Best overlay language: '{best['overlay_language']}' = {int(best['high_engagement_rate']*100)}% (n={best['count']})")
    if type_table:
        best_t = type_table[0]
        findings.append(f"Best overlay type: '{best_t['overlay_type']}' = {int(best_t['high_engagement_rate']*100)}% (n={best_t['count']})")
        worst_t = type_table[-1]
        findings.append(f"Worst overlay type: '{worst_t['overlay_type']}' = {int(worst_t['high_engagement_rate']*100)}% — use sparingly")

    agency_rules = []
    if has_o and no_o:
        diff = has_o["high_engagement_rate"] - no_o["high_engagement_rate"]
        if diff > 0.05:
            agency_rules.append("Add text overlays — they lift engagement across corpus")
        elif diff < -0.05:
            agency_rules.append("Avoid text overlays on storytelling/heritage content — they hurt engagement")
        else:
            agency_rules.append("Text overlay impact is neutral — use when it adds context, not decoration")
    if lang_table:
        top = lang_table[0]
        agency_rules.append(f"Best overlay language: '{top['overlay_language']}' ({int(top['high_engagement_rate']*100)}%) — default to this for visual text")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "obs_with_text_overlay": obs_with_overlay,
        "overlay_presence_table": presence_table,
        "overlay_language_table": lang_table,
        "overlay_content_type_table": type_table,
        "language_by_occasion": lang_occ_rows,
        "agency_rules": agency_rules,
        "key_findings": findings,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "text_overlay_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Text overlay analysis: {obs_with_overlay}/{total} obs have overlays")
    print(f"\nOverlay presence → engagement:")
    for r in presence_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['overlay_presence']:<18} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['count']}")
    print(f"\nOverlay language → engagement:")
    for r in lang_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['overlay_language']:<14} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['count']}")
    print(f"\nOverlay type → engagement:")
    for r in type_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline']>=0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['overlay_type']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift}  n={r['count']}")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/text_overlay_analysis.json")


if __name__ == "__main__":
    main()
