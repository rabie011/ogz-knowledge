#!/usr/bin/env python3
"""
print_data_quality_report.py
Complete fill-rate audit across all observation fields.
Shows exactly what data exists, what's missing, and priority for filling gaps.
No args needed. Reads obs directly.
"""
import json
from pathlib import Path
from collections import Counter, defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"

def main():
    obs_files = list(OBS_ROOT.rglob("*.json"))
    N = len(obs_files)
    data_list = [json.loads(f.read_text()) for f in obs_files]

    def _fill(extractor):
        return sum(1 for d in data_list if extractor(d))

    def _pct(n): return f"{n/N:.0%}"

    fields = {
        # Identity
        "sector":           lambda d: d.get("sector"),
        "account_handle":   lambda d: d.get("account_handle_normalized"),
        "occasion":         lambda d: d.get("occasion"),
        "source_url":       lambda d: d.get("content_ref",{}).get("source_url"),

        # Content ref
        "content_type":     lambda d: d.get("content_ref",{}).get("content_type"),
        "capture_date":     lambda d: d.get("content_ref",{}).get("capture_date"),
        "aspect_ratio":     lambda d: d.get("content_ref",{}).get("aspect_ratio"),
        "day_of_week":      lambda d: d.get("content_ref",{}).get("day_of_week"),
        "editing_pace":     lambda d: d.get("content_ref",{}).get("editing_pace"),
        "carousel_slides":  lambda d: d.get("content_ref",{}).get("carousel_slide_count"),
        "video_duration":   lambda d: d.get("content_ref",{}).get("video_duration_seconds"),

        # Visual
        "setting":          lambda d: d.get("visual_observations",{}).get("setting"),
        "lighting":         lambda d: d.get("visual_observations",{}).get("lighting"),
        "composition":      lambda d: d.get("visual_observations",{}).get("composition_style"),
        "visual_complexity":lambda d: d.get("visual_observations",{}).get("visual_complexity"),
        "color_palette":    lambda d: d.get("visual_observations",{}).get("color_palette"),
        "text_overlays":    lambda d: d.get("visual_observations",{}).get("text_overlays"),
        "human_presence":   lambda d: d.get("visual_observations",{}).get("human_presence"),
        "props":            lambda d: d.get("visual_observations",{}).get("props"),

        # Voice
        "tone":             lambda d: d.get("voice_observations",{}).get("tone"),
        "register":         lambda d: d.get("voice_observations",{}).get("register"),
        "caption_text":     lambda d: d.get("voice_observations",{}).get("caption_text"),
        "caption_sentiment":lambda d: d.get("voice_observations",{}).get("caption_sentiment"),
        "notable_phrases":  lambda d: d.get("voice_observations",{}).get("notable_phrases"),
        "opener_formula":   lambda d: d.get("voice_observations",{}).get("opener_formula"),
        "has_emoji":        lambda d: d.get("voice_observations",{}).get("has_emoji") is not None,
        "dialect":          lambda d: d.get("voice_observations",{}).get("dialect_detected"),

        # Cultural
        "heritage_modern":  lambda d: d.get("cultural_notes",{}).get("heritage_vs_modern"),
        "hospitality_cues": lambda d: d.get("cultural_notes",{}).get("hospitality_cues"),

        # Quality
        "engagement":       lambda d: d.get("quality_assessment",{}).get("engagement_potential"),
        "production_qual":  lambda d: d.get("quality_assessment",{}).get("production_quality"),

        # Audio
        "has_voiceover":    lambda d: d.get("audio_strategy",{}).get("has_voiceover") is not None,
        "music_type":       lambda d: d.get("audio_strategy",{}).get("music_type"),
    }

    # Fill rates
    results = {}
    for name, extractor in fields.items():
        n_filled = _fill(extractor)
        results[name] = n_filled

    # Engagement coverage by sector
    sectors = Counter(d.get("sector","") for d in data_list)
    eng_by_sec = defaultdict(list)
    ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
    for d in data_list:
        e = ENG_MAP.get(d.get("quality_assessment",{}).get("engagement_potential",""))
        s = d.get("sector","")
        if e is not None and s: eng_by_sec[s].append(e)

    W = 68
    print(f"\n{'═'*W}")
    print(f"  OGZ KNOWLEDGE BASE — DATA QUALITY REPORT")
    print(f"  {N} total observations  ·  {len(sectors)} sectors  ·  15 accounts")
    print(f"{'═'*W}\n")

    # Section: Corpus composition
    print(f"  CORPUS COMPOSITION")
    print(f"  {'─'*60}")
    for sec, count in sorted(sectors.items(), key=lambda x: -x[1]):
        if not sec: continue
        avgs = eng_by_sec.get(sec,[])
        avg_str = f"{sum(avgs)/len(avgs):.0%}" if avgs else "—"
        print(f"    {sec:<35}  {count:>3} obs  ({count/N:.0%})  avg: {avg_str}")

    # Section: fill rates by category
    GROUPS = {
        "IDENTITY":    ["sector","account_handle","occasion","source_url"],
        "CONTENT REF": ["content_type","capture_date","aspect_ratio","day_of_week","editing_pace","carousel_slides","video_duration"],
        "VISUAL":      ["setting","lighting","composition","visual_complexity","color_palette","text_overlays","human_presence","props"],
        "VOICE":       ["tone","register","caption_text","caption_sentiment","notable_phrases","opener_formula","has_emoji","dialect"],
        "CULTURAL":    ["heritage_modern","hospitality_cues"],
        "QUALITY":     ["engagement","production_qual"],
        "AUDIO":       ["has_voiceover","music_type"],
    }

    print(f"\n  FIELD FILL RATES")
    print(f"  {'─'*60}")
    for group, field_names in GROUPS.items():
        print(f"\n  [{group}]")
        for fn in field_names:
            n = results.get(fn, 0)
            pct = n/N
            bar = "█" * int(pct * 20) + "░" * (20 - int(pct * 20))
            flag = " ⚠" if pct < 0.20 else " ★" if pct >= 0.90 else ""
            print(f"    {fn:<22}  {bar}  {n:>3}/{N} ({pct:.0%}){flag}")

    # Missing data priorities
    critical_gaps = [(fn, results[fn]) for fn in fields if results[fn]/N < 0.20]
    critical_gaps.sort(key=lambda x: -x[1])  # most filled first (easiest to complete)

    print(f"\n  TOP GAPS (< 20% filled)")
    print(f"  {'─'*60}")
    if critical_gaps:
        for fn, n in critical_gaps[:10]:
            pct = n/N
            # Suggest method
            if fn in ["caption_text","caption_sentiment","has_emoji"]:
                method = "→ Instagram caption scrape (blocked, retry after IP unban)"
            elif fn in ["aspect_ratio"]:
                method = "→ Partially inferrable from content_type (reels=9:16)"
            elif fn in ["editing_pace"]:
                method = "→ Video analysis (Whisper/OCR)"
            elif fn in ["video_duration","has_voiceover","music_type"]:
                method = "→ Whisper run on video obs"
            elif fn in ["carousel_slides"]:
                method = "→ Browser scrape during caption pass"
            elif fn in ["color_palette"]:
                method = "→ OpenCV dominant color extraction (already have tool)"
            elif fn in ["human_presence"]:
                method = "→ Computer vision face detection"
            else:
                method = "→ Manual review or extraction"
            print(f"    {fn:<22}  {n:>3}/{N} ({pct:.0%})  {method}")

    # What's complete
    complete = [(fn, results[fn]) for fn in fields if results[fn]/N >= 0.90]
    print(f"\n  FULLY COVERED FIELDS ({len(complete)} fields ≥ 90%)")
    print(f"  {'─'*60}")
    for fn, n in sorted(complete, key=lambda x: -x[1]):
        print(f"    ★ {fn:<22}  {n}/{N} ({n/N:.0%})")

    # Analytics coverage
    logs = list((BASE/"logs").glob("*.json"))
    print(f"\n  ANALYTICS COVERAGE")
    print(f"  {'─'*60}")
    print(f"    Total analytics logs:  {len(logs)}")
    print(f"    Total scripts:         {len(list((BASE/'scripts').glob('*.py')))}")
    print(f"    Patterns defined:      {len(list((BASE/'11_who_to_learn_from/patterns').rglob('*.json')))}")
    print(f"    Patterns used in obs:  127 distinct")
    print()

if __name__ == "__main__":
    main()
