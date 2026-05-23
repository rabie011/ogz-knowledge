#!/usr/bin/env python3
"""
search_corpus.py
Structured field search over all 474 observations.
Filter by any combination of fields — returns matching obs with source URLs.

Usage examples:
  python3 scripts/search_corpus.py --sector f_and_b --occasion ramadan --engagement high
  python3 scripts/search_corpus.py --pattern heritage_storytelling_hook --setting heritage_setting
  python3 scripts/search_corpus.py --register casual --tone warm --engagement high
  python3 scripts/search_corpus.py --sector beauty --engagement low --limit 10
  python3 scripts/search_corpus.py --account barnscoffee
  python3 scripts/search_corpus.py --pattern product_hero --json
  python3 scripts/search_corpus.py  (no filters = show corpus summary)
"""
import json
import argparse
import sys
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
ENG_MAP  = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
ENG_THRESHOLD = {"high": 0.75, "medium": 0.5, "low": 0.0}


def load_obs():
    records = []
    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except: continue

        qa      = data.get("quality_assessment",{}) or {}
        eng_raw = str(qa.get("engagement_potential","") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)

        cr  = data.get("content_ref",{}) or {}
        vv  = data.get("visual_observations",{}) or {}
        vo  = data.get("voice_observations",{}) or {}
        cn  = data.get("cultural_notes",{}) or {}

        pattern_slugs = []
        for pm in data.get("pattern_matches",[]):
            slug = pm.get("pattern_slug","") if isinstance(pm,dict) else pm
            if slug: pattern_slugs.append(slug)

        records.append({
            "_file":     str(obs_file),
            "account":   data.get("account_handle_normalized","unknown"),
            "sector":    data.get("sector","unknown") or "unknown",
            "date":      cr.get("capture_date") or cr.get("post_date"),
            "source_url":cr.get("source_url") or cr.get("url"),
            "engagement_potential": eng_raw,
            "eng_score": eng,
            "media_type":str(cr.get("content_type","") or "").lower(),
            "setting":   vv.get("setting",""),
            "lighting":  vv.get("lighting",""),
            "composition":vv.get("composition_style",""),
            "register":  str(vo.get("register","") or "").lower(),
            "tone":      str(vo.get("tone","") or "").lower(),
            "dialect":   str(vo.get("dialect_detected","") or "").lower(),
            "occasion":  str(cn.get("occasion_relevance","") or "evergreen").lower(),
            "heritage":  str(cn.get("heritage_vs_modern","") or "").lower(),
            "patterns":  pattern_slugs,
            "hosp_cues": len(cn.get("hospitality_cues") or []),
        })
    return records


def matches(rec, args):
    # Sector
    if args.sector and args.sector.lower() not in rec["sector"].lower():
        return False
    # Account
    if args.account and args.account.lower() not in rec["account"].lower():
        return False
    # Pattern (must contain this slug)
    if args.pattern and args.pattern.lower() not in [p.lower() for p in rec["patterns"]]:
        return False
    # Engagement tier
    if args.engagement:
        tier = args.engagement.lower()
        if tier == "high"   and rec["eng_score"] < 0.75: return False
        if tier == "medium" and not (0.25 < rec["eng_score"] < 0.75): return False
        if tier == "low"    and rec["eng_score"] > 0.25: return False
    # Setting (substring match)
    if args.setting and args.setting.lower() not in (rec["setting"] or "").lower():
        return False
    # Lighting
    if args.lighting and args.lighting.lower() not in (rec["lighting"] or "").lower():
        return False
    # Register
    if args.register and args.register.lower() not in (rec["register"] or "").lower():
        return False
    # Tone
    if args.tone and args.tone.lower() not in (rec["tone"] or "").lower():
        return False
    # Occasion (substring match)
    if args.occasion and args.occasion.lower() not in (rec["occasion"] or "").lower():
        return False
    # Media type
    if args.media_type and args.media_type.lower() not in (rec["media_type"] or "").lower():
        return False
    # Min hospitality cues
    if args.min_hosp is not None and rec["hosp_cues"] < args.min_hosp:
        return False
    return True


def print_summary(records):
    from collections import Counter
    sectors = Counter(r["sector"] for r in records)
    engagements = {"high":0,"medium":0,"low":0}
    for r in records:
        if r["eng_score"] >= 0.75: engagements["high"] += 1
        elif r["eng_score"] > 0.25: engagements["medium"] += 1
        else: engagements["low"] += 1
    print(f"\n  Corpus: {len(records)} observations")
    print(f"  Sectors: " + " | ".join(f"{k}={v}" for k,v in sectors.most_common()))
    print(f"  Engagement: high={engagements['high']} ({int(engagements['high']/len(records)*100)}%)  "
          f"medium={engagements['medium']}  low={engagements['low']}")
    print(f"\n  Filters available:")
    print(f"    --sector SECTOR        f_and_b / beauty / retail")
    print(f"    --account HANDLE       account handle substring")
    print(f"    --pattern SLUG         pattern slug (exact)")
    print(f"    --engagement TIER      high / medium / low")
    print(f"    --setting VALUE        setting substring")
    print(f"    --lighting VALUE       lighting substring")
    print(f"    --register VALUE       register substring")
    print(f"    --tone VALUE           tone substring")
    print(f"    --occasion VALUE       occasion substring")
    print(f"    --media-type VALUE     image / carousel_slide / reel / video")
    print(f"    --min-hosp N           minimum hospitality cue count")
    print(f"    --limit N              max results (default 20)")
    print(f"    --json                 output full JSON instead of table")


def main():
    parser = argparse.ArgumentParser(description="Search the OGZ corpus of 474 observations")
    parser.add_argument("--sector",     type=str)
    parser.add_argument("--account",    type=str)
    parser.add_argument("--pattern",    type=str)
    parser.add_argument("--engagement", type=str, choices=["high","medium","low"])
    parser.add_argument("--setting",    type=str)
    parser.add_argument("--lighting",   type=str)
    parser.add_argument("--register",   type=str)
    parser.add_argument("--tone",       type=str)
    parser.add_argument("--occasion",   type=str)
    parser.add_argument("--media-type", type=str, dest="media_type")
    parser.add_argument("--min-hosp",   type=int, dest="min_hosp")
    parser.add_argument("--limit",      type=int, default=20)
    parser.add_argument("--json",       action="store_true", dest="output_json")
    args = parser.parse_args()

    records = load_obs()

    # No filters: show summary
    has_filter = any([args.sector, args.account, args.pattern, args.engagement,
                      args.setting, args.lighting, args.register, args.tone,
                      args.occasion, args.media_type, args.min_hosp])
    if not has_filter:
        print_summary(records)
        return

    results = [r for r in records if matches(r, args)]
    results.sort(key=lambda x: -x["eng_score"])

    # Active filters summary
    active = []
    for k in ["sector","account","pattern","engagement","setting","lighting","register","tone","occasion"]:
        v = getattr(args, k, None)
        if v: active.append(f"{k}={v}")
    if args.media_type: active.append(f"media_type={args.media_type}")
    if args.min_hosp: active.append(f"min_hosp={args.min_hosp}")

    if args.output_json:
        out = {
            "query": active,
            "total_results": len(results),
            "results": results[:args.limit]
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"\n  Query: {' | '.join(active)}")
    print(f"  Results: {len(results)} of {len(records)} observations")

    if not results:
        print("  No matches found.")
        return

    high_count = sum(1 for r in results if r["eng_score"] >= 0.75)
    print(f"  High engagement: {high_count}/{len(results)} ({int(high_count/len(results)*100)}%)\n")

    # Table header
    print(f"  {'Account':<32} {'Date':<12} {'Eng':<6} {'Format':<16} {'Pattern(s)'}")
    print("  " + "─"*95)

    for r in results[:args.limit]:
        eng_icon = "🟢" if r["eng_score"] >= 0.75 else "🟡" if r["eng_score"] > 0.25 else "🔴"
        date_str = str(r["date"])[:10] if r["date"] else "—"
        pats = ", ".join(r["patterns"][:2]) + ("…" if len(r["patterns"]) > 2 else "")
        print(f"  {r['account'][:30]:<32} {date_str:<12} {eng_icon} {r['media_type']:<16} {pats}")
        if r["source_url"]:
            print(f"  {'':32} {'':12}   {r['source_url']}")

    if len(results) > args.limit:
        print(f"\n  … {len(results) - args.limit} more results. Use --limit N to see more.")


if __name__ == "__main__":
    main()
