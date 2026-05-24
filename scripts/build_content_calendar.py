#!/usr/bin/env python3
"""
build_content_calendar.py
Generate a data-driven weekly content calendar for any sector + date range.
Uses occasion calendar, format matrix, day-of-week, and sector DNA.

Usage:
  python3 scripts/build_content_calendar.py \
    --sector food_and_beverage --weeks 4 --start 2026-06-01
  python3 scripts/build_content_calendar.py --interactive

Output: logs/content_calendars/{sector}_{start}_{weeks}w.json + stdout
"""
import json, argparse
from pathlib import Path
from datetime import datetime, timedelta, date

BASE = Path(__file__).parent.parent
LOGS = BASE / "logs"

SECTOR_ALIASES = {
    "fb":"food_and_beverage","f&b":"food_and_beverage","food":"food_and_beverage",
    "food_and_beverage":"food_and_beverage","beauty":"beauty_personal_care",
    "personal_care":"beauty_personal_care","retail":"retail_lifestyle",
    "lifestyle":"retail_lifestyle",
}
SECTOR_KEY_MAP = {
    "food_and_beverage":"f_and_b","beauty_personal_care":"beauty","retail_lifestyle":"retail",
}

# Saudi occasions calendar — approximate annual windows
OCCASION_WINDOWS = [
    {"occasion":"ramadan",      "months":[3],     "note":"Ramadan 2027 approx Mar"},
    {"occasion":"eid_al_fitr",  "months":[4],     "note":"Eid al-Fitr after Ramadan"},
    {"occasion":"founding_day", "months":[2],     "note":"Saudi Founding Day Feb 22"},
    {"occasion":"national_day", "months":[9],     "note":"Saudi National Day Sep 23"},
    {"occasion":"eid_al_adha",  "months":[6],     "note":"Eid al-Adha approx Jun 2026"},
    {"occasion":"vision_2030",  "months":[4],     "note":"Vision 2030 milestones April"},
    {"occasion":"new_year",     "months":[1],     "note":"New Year January"},
    {"occasion":"summer_campaign","months":[6,7,8],"note":"Summer Jun-Aug"},
    {"occasion":"back_to_school","months":[8,9],  "note":"Back to school Aug-Sep"},
]

BEST_DAYS_RANKED = ["sunday","monday","saturday","thursday","wednesday","friday","tuesday"]
DAY_NUM = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}


def _get_occasion_for_date(d):
    """Return occasion slug for a given date, or evergreen."""
    month = d.month
    day   = d.day
    if month == 2 and 19 <= day <= 25: return "founding_day"
    if month == 9 and 20 <= day <= 26: return "national_day"
    if month == 4 and 1 <= day <= 10:  return "eid_al_fitr"    # approximate 2026
    if month == 6 and 5 <= day <= 15:  return "eid_al_adha"    # approximate 2026
    if month == 3 and 1 <= day <= 31:  return "ramadan"        # approximate 2027
    if month in [6,7,8]:               return "summer_campaign"
    if month in [8,9] and day >= 15:   return "back_to_school"
    if month == 1 and day <= 10:       return "new_year"
    return "evergreen"


def generate_calendar(sector, weeks, start_date):
    sk = SECTOR_KEY_MAP.get(sector, sector[:6])

    # Load analytics
    dow   = _load("day_of_week_analysis.json")
    osf   = _load("occasion_sector_format_matrix.json")
    ct_an = _load("content_type_analysis.json")
    sfp   = _load("sector_fingerprint.json")
    pat   = _load("pattern_engagement.json")
    tone_r= _load("tone_register_analysis.json")
    opp   = _load("occasion_playbook.json")

    # Best days by sector
    best_day_sec = ((dow.get("best_by_sector") or {}).get(sector) or {}).get("best_day", "sunday")
    best_day_ranked = dow.get("ranked_days") or BEST_DAYS_RANKED

    # Sector DNA
    sfp_sec = (sfp.get("sectors") or {}).get(sk) or {}
    sfp_prof= sfp_sec.get("profile") or {}
    sector_tone     = (sfp_prof.get("tone") or {}).get("dominant","")
    sector_register = (sfp_prof.get("register") or {}).get("dominant","")

    # Best format lookup by occasion × sector
    osf_lookup = {}
    for e in (osf.get("best_format_table") or []):
        key = e["occasion"] + "__" + e["sector"]
        osf_lookup[key] = e

    # Elite patterns
    elite_patterns = [(p["pattern"], p["avg_engagement"]) for p in (pat.get("elite_patterns") or [])[:10]]

    # Per-occasion playbook
    pb_entries = {e.get("occasion",""): e for e in (opp.get("playbook") or [])}

    # ── Build weekly plan ──
    weeks_plan = []
    current    = start_date
    post_count = 0

    for week_num in range(1, weeks + 1):
        week_posts = []
        week_start = current

        # 3 posts per week — spread across best days
        # Week posting days: pick top 3 from ranked best days for this sector
        week_days = []
        for day_name in (best_day_ranked or BEST_DAYS_RANKED):
            day_n = DAY_NUM.get(day_name, 6)
            # Find this weekday within the week (Mon=0…Sun=6)
            delta = (day_n - week_start.weekday()) % 7
            post_date = week_start + timedelta(days=delta)
            if post_start := week_start <= post_date < week_start + timedelta(days=7):
                week_days.append((post_date, day_name))
            if len(week_days) >= 3: break

        # If we couldn't find 3 days in the week window, fill with Sun/Mon/Thu
        if len(week_days) < 3:
            for fallback in [6, 0, 3]:  # Sun, Mon, Thu
                d_date = week_start + timedelta(days=(fallback - week_start.weekday()) % 7)
                day_n_name = [k for k,v in DAY_NUM.items() if v==fallback][0]
                if not any(d[0] == d_date for d in week_days):
                    week_days.append((d_date, day_n_name))
                if len(week_days) >= 3: break

        week_days = sorted(week_days, key=lambda x: x[0])[:3]

        for post_date, day_name in week_days:
            post_count += 1
            occ = _get_occasion_for_date(post_date)
            pb  = pb_entries.get(occ) or {}

            # Best format for this occasion × sector
            osf_entry = osf_lookup.get(f"{occ}__{sk}") or {}
            best_fmt  = osf_entry.get("best_format") or \
                        ((ct_an.get("best_by_sector") or {}).get(sector) or [{}])[0].get("content_type") or "image"
            best_eng  = osf_entry.get("best_eng") or 0

            # Recommend pattern
            # Prefer occasion-specific patterns
            occ_pats = [(p["pattern"], p["avg_engagement"])
                        for p in ((pat.get("best_by_occasion") or {}).get(occ) or [])[:2]]
            if not occ_pats:
                occ_pats = elite_patterns[:2]

            # Tone from occasion playbook or sector default
            tone     = (pb.get("overall_recipe") or {}).get("tone") or sector_tone or "celebratory"
            register = (pb.get("overall_recipe") or {}).get("register") or sector_register or "professional"
            hvm      = (pb.get("overall_recipe") or {}).get("heritage_vs_modern") or \
                       (sfp_prof.get("heritage_framing") or {}).get("dominant") or "heritage"

            # Hashtag count
            hashtag_rec = "1-5"

            post = {
                "post_number":  post_count,
                "date":         post_date.strftime("%Y-%m-%d"),
                "day_of_week":  day_name,
                "occasion":     occ,
                "sector":       sector,
                "recommended_format":    best_fmt,
                "predicted_engagement":  round(best_eng, 3) if best_eng else None,
                "recommended_tone":      tone,
                "recommended_register":  register,
                "heritage_framing":      hvm,
                "patterns_to_use":       [p[0] for p in occ_pats[:2]],
                "hashtags":              hashtag_rec,
                "brief_note":           (pb.get("agency_notes") or [""])[0][:80] if pb.get("agency_notes") else None,
            }
            week_posts.append(post)

        weeks_plan.append({
            "week": week_num,
            "week_start": week_start.strftime("%Y-%m-%d"),
            "week_end":   (week_start + timedelta(days=6)).strftime("%Y-%m-%d"),
            "posts": week_posts,
        })
        current += timedelta(weeks=1)

    # Occasion summary for this period
    all_occasions = list({p["occasion"] for w in weeks_plan for p in w["posts"]})

    out = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sector": sector,
        "sector_key": sk,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "weeks": weeks,
        "total_posts": post_count,
        "occasions_covered": all_occasions,
        "sector_avg_engagement": sfp_sec.get("avg_engagement"),
        "weeks_plan": weeks_plan,
    }
    return out


def print_calendar(cal):
    W = 72
    print(f"\n{'═'*W}")
    print(f"  OGZ CONTENT CALENDAR — {cal['sector'].upper()}")
    print(f"  {cal['start_date']}  ·  {cal['weeks']} weeks  ·  {cal['total_posts']} posts")
    sec_avg = cal.get("sector_avg_engagement")
    if sec_avg: print(f"  Sector baseline: {sec_avg:.0%}")
    print(f"{'═'*W}\n")

    for week in cal["weeks_plan"]:
        print(f"  WEEK {week['week']}  {week['week_start']} — {week['week_end']}")
        print(f"  {'─'*66}")
        for p in week["posts"]:
            occ_tag = f"[{p['occasion'].replace('_',' ')}]" if p['occasion'] != "evergreen" else "[evergreen]"
            eng_str = f" → {p['predicted_engagement']:.0%}" if p.get("predicted_engagement") else ""
            print(f"  {p['date']}  {p['day_of_week']:<10} {occ_tag:<22} {p['recommended_format']:<16}{eng_str}")
            pats = ", ".join(p["patterns_to_use"][:2])
            print(f"    Tone: {p['recommended_tone']} | {p['recommended_register']} | {p['heritage_framing']}")
            if pats: print(f"    Patterns: {pats}")
            if p.get("brief_note"): print(f"    Note: {p['brief_note']}")
        print()


def main():
    parser = argparse.ArgumentParser(description="OGZ Content Calendar Generator")
    parser.add_argument("--sector",  type=str)
    parser.add_argument("--weeks",   type=int, default=4)
    parser.add_argument("--start",   type=str, default=None)
    parser.add_argument("--save",    action="store_true")
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()

    if args.interactive or not args.sector:
        print("\nOGZ Content Calendar Generator")
        print("─"*35)
        print("Sectors: food_and_beverage | beauty_personal_care | retail_lifestyle")
        sector = SECTOR_ALIASES.get(input("Sector: ").strip().lower(), "food_and_beverage")
        weeks  = int(input("Weeks [4]: ").strip() or "4")
        start_str = input("Start date [today]: ").strip()
    else:
        sector    = SECTOR_ALIASES.get(args.sector.lower(), args.sector.lower())
        weeks     = args.weeks
        start_str = args.start or ""

    if start_str:
        try: start = datetime.strptime(start_str, "%Y-%m-%d").date()
        except: start = date.today()
    else:
        start = date.today()

    cal = generate_calendar(sector, weeks, start)
    print_calendar(cal)

    save = args.save or (args.interactive and input("Save? [y/N]: ").lower() == "y")
    if save:
        d = LOGS / "content_calendars"
        d.mkdir(exist_ok=True)
        fn = f"{sector}_{start.strftime('%Y%m%d')}_{weeks}w.json"
        (d / fn).write_text(json.dumps(cal, ensure_ascii=False, indent=2))
        print(f"  Saved: logs/content_calendars/{fn}")

if __name__ == "__main__":
    main()
