#!/usr/bin/env python3
"""
print_saudi_occasions_calendar.py
Saudi content calendar: all occasions, optimal posting windows,
recommended formats, and engagement benchmarks from corpus.

No args needed — prints the full year calendar.

Usage:
  python3 scripts/print_saudi_occasions_calendar.py
  python3 scripts/print_saudi_occasions_calendar.py --occasion national_day
  python3 scripts/print_saudi_occasions_calendar.py --sector food_and_beverage
"""
import json, argparse
from pathlib import Path
from collections import defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
def _eng(d): return ENG_MAP.get((d.get("quality_assessment") or {}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}

# Saudi occasions with approximate 2026 dates & posting windows
OCCASIONS = [
    {
        "slug":         "new_year",
        "name":         "New Year",
        "date_approx":  "Jan 1",
        "window":       "Dec 28 – Jan 2",
        "posts":        3,
        "notes":        "Low Saudi resonance — evergreen content preferred",
    },
    {
        "slug":         "founding_day",
        "name":         "Founding Day (يوم التأسيس)",
        "date_approx":  "Feb 22",
        "window":       "Feb 18 – Feb 23",
        "posts":        4,
        "notes":        "Patriotic tone — heritage framing. Rapid growth in brand adoption.",
    },
    {
        "slug":         "ramadan",
        "name":         "Ramadan (رمضان)",
        "date_approx":  "Mar 1 – Mar 30 (approx 2026)",
        "window":       "Feb 25 – Apr 5",
        "posts":        12,
        "notes":        "Spiritual + community tone. Post after Iftar (7–10pm). Heritage framing wins.",
    },
    {
        "slug":         "eid_al_fitr",
        "name":         "Eid Al Fitr (عيد الفطر)",
        "date_approx":  "Mar 31 (approx 2026)",
        "window":       "Mar 28 – Apr 4",
        "posts":        5,
        "notes":        "Celebratory peak. 100% engagement in corpus. Carousel/image best.",
    },
    {
        "slug":         "hajj",
        "name":         "Hajj Season (موسم الحج)",
        "date_approx":  "Jun 4 – Jun 9 (approx 2026)",
        "window":       "Jun 1 – Jun 11",
        "posts":        3,
        "notes":        "Spiritual + hospitality cues. F&B brands: pilgrims & welcome messaging.",
    },
    {
        "slug":         "eid_al_adha",
        "name":         "Eid Al Adha (عيد الأضحى)",
        "date_approx":  "Jun 9 (approx 2026)",
        "window":       "Jun 6 – Jun 13",
        "posts":        5,
        "notes":        "Family & togetherness. Heritage framing. Avoid product-push tone.",
    },
    {
        "slug":         "national_sports_day",
        "name":         "National Sports Day",
        "date_approx":  "Feb 12 (second Thu of Feb)",
        "window":       "Feb 10 – Feb 13",
        "posts":        2,
        "notes":        "Beauty: 0% corpus engagement — skip or reframe as wellness/lifestyle.",
    },
    {
        "slug":         "summer_campaign",
        "name":         "Summer Campaign",
        "date_approx":  "Jun 15 – Aug 31",
        "window":       "Jun 10 – Aug 31",
        "posts":        16,
        "notes":        "High F&B opportunity: 80% avg. Cooling/refreshment sensory language.",
    },
    {
        "slug":         "national_day",
        "name":         "National Day (اليوم الوطني)",
        "date_approx":  "Sep 23",
        "window":       "Sep 19 – Sep 24",
        "posts":        5,
        "notes":        "Green palette. Patriotic tone. 86% F&B avg. Static beats video by +12pp.",
    },
    {
        "slug":         "graduation_season",
        "name":         "Graduation Season",
        "date_approx":  "May – Jun",
        "window":       "May 15 – Jun 30",
        "posts":        4,
        "notes":        "92% F&B avg in corpus — highest of any occasion. Gift + celebration tone.",
    },
    {
        "slug":         "winter_seasonal",
        "name":         "Winter Campaign",
        "date_approx":  "Nov – Jan",
        "window":       "Nov 1 – Jan 31",
        "posts":        8,
        "notes":        "100% F&B corpus avg. Warm tones, indoor setting, comfort food positioning.",
    },
    {
        "slug":         "evergreen",
        "name":         "Evergreen Content",
        "date_approx":  "Year-round",
        "window":       "Always",
        "posts":        3,
        "notes":        "67% F&B avg. Backbone of content calendar. 3 posts/week minimum.",
    },
]

SECTOR_KEY = {
    "food_and_beverage":"f_and_b", "f&b":"f_and_b", "fb":"f_and_b",
    "beauty":"beauty","beauty_personal_care":"beauty",
    "retail":"retail","retail_lifestyle":"retail",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--occasion", type=str, default=None)
    parser.add_argument("--sector",   type=str, default=None)
    args = parser.parse_args()

    # Load analytics
    osf  = _load("occasion_sector_format_matrix.json")
    opp  = _load("occasion_playbook.json")
    dow  = _load("day_of_week_analysis.json")
    tone = _load("tone_register_analysis.json")
    npi  = _load("notable_phrases_intelligence.json")
    hosp = _load("hospitality_intelligence.json")

    # Build corpus stats per occasion
    occ_stats = defaultdict(list)
    for f in OBS_ROOT.rglob("*.json"):
        d = json.loads(f.read_text())
        occ = d.get("occasion","")
        e   = _eng(d)
        if occ and e is not None:
            occ_stats[occ].append({
                "eng": e,
                "sector": d.get("sector",""),
                "ct": (d.get("content_ref") or {}).get("content_type",""),
            })

    # Filter occasions
    show = OCCASIONS
    if args.occasion:
        show = [o for o in OCCASIONS if args.occasion.lower() in o["slug"]]

    W = 72
    print(f"\n{'═'*W}")
    print(f"  SAUDI INSTAGRAM CONTENT CALENDAR  —  OGZ Intelligence")
    print(f"{'═'*W}")

    for occ in show:
        slug  = occ["slug"]
        stats = occ_stats.get(slug, [])
        n     = len(stats)

        # Sector breakdown
        sec_eng = defaultdict(list)
        for s in stats:
            if s["sector"]: sec_eng[s["sector"]].append(s["eng"])
        sec_line = "  |  ".join(
            f"{k.replace('f_and_b','F&B').replace('beauty','BEAUTY').replace('retail','RETAIL')}:{_avg(v):.0%}(n={len(v)})"
            for k,v in sorted(sec_eng.items(), key=lambda x: -_avg(x[1]))
            if len(v) >= 2
        ) or "—"

        # Best format from OSF matrix
        best_fmt = None
        for row in (osf.get("full_table") or []):
            if row.get("occasion") == slug and row.get("count",0) >= 3:
                best_fmt = f"{row.get('content_type','?')} ({row.get('avg_engagement',0):.0%})"
                break

        # Best posting day
        best_day = ((dow.get("best_by_occasion") or {}).get(slug) or {}).get("best_day","sunday")

        # Top phrases
        phrases = [p["phrase"] for p in ((npi.get("best_by_occasion") or {}).get(slug) or [])[:3]]

        # Playbook entry
        pb = next((e for e in (opp.get("playbook") or []) if e.get("occasion") == slug), {})
        best_tone = pb.get("overall_recipe",{}).get("tone","")

        # Section filter
        if args.sector:
            sk = SECTOR_KEY.get(args.sector.lower(), args.sector)
            sec_engs = sec_eng.get(sk,[])
            if not sec_engs and slug != "evergreen":
                continue
            sec_avg = _avg(sec_engs)
            sec_banner = f"  [{sk.upper()}:  avg={sec_avg:.0%}  n={len(sec_engs)}]" if sec_engs else "  [No data for this sector]"
        else:
            sec_banner = None

        # Print
        print(f"\n  ┌{'─'*(W-4)}┐")
        print(f"  │  {occ['name']:<50}  {occ['date_approx']:<12}│")
        print(f"  │  Window: {occ['window']:<30}  Recommended posts: {occ['posts']:<4}   │")
        print(f"  └{'─'*(W-4)}┘")

        if sec_banner:
            print(sec_banner)

        if n >= 2:
            corpus_avg = _avg([s["eng"] for s in stats])
            print(f"  Corpus:   {n} obs  ·  avg {corpus_avg:.0%}  ·  by sector: {sec_line}")
        else:
            print(f"  Corpus:   ⚠ limited data ({n} obs)")

        print(f"  Format:   {best_fmt or '—'}")
        print(f"  Post day: {best_day.title() if best_day else '—'}")
        if best_tone:
            print(f"  Tone:     {best_tone}")
        if phrases:
            print(f"  Arabic:   {' / '.join(phrases)}")
        print(f"  Note:     {occ['notes']}")

        # 3-post schedule
        print(f"\n  Posting schedule:")
        if occ["posts"] >= 3:
            print(f"    D-3:  Teaser — anticipatory tone, product preview")
            print(f"    D+0:  Hero   — {best_fmt.split('(')[0].strip() if best_fmt else 'carousel/image'}, {best_tone or 'celebratory'} tone, {best_day.title() if best_day else 'Sunday'}")
            print(f"    D+2:  Close  — gratitude, community invite, UGC prompt")

    print(f"\n{'═'*W}")
    print(f"  Generated from {sum(len(v) for v in occ_stats.values())} obs across {len(occ_stats)} occasions")
    print(f"  Run python3 scripts/build_occasion_readiness_report.py for full occasion × sector intel\n")


if __name__ == "__main__":
    main()
