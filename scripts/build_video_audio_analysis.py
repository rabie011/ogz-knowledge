#!/usr/bin/env python3
"""
build_video_audio_analysis.py
Analyse audio_strategy and video_duration_seconds for video/reel obs.

Agency questions answered:
  - Optimal video duration × sector × engagement
  - Voiceover (Arabic) vs music-only vs silence × engagement
  - Subtitles present vs absent × engagement
  - Short-form (≤15s) vs mid-form (15-60s) vs long-form (60s+) performance
  - Music type × engagement (trending_sound vs original_score vs ambient vs silence)

Output: logs/video_audio_analysis.json
"""
import json
from collections import defaultdict, Counter
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {
    "high": 1.0, "very_high": 1.0,
    "above_average": 0.75,
    "medium": 0.5,
    "low": 0.0, "below_average": 0.25,
}
CORPUS_BASELINE = 0.54
VIDEO_TYPES     = {"video", "reel"}


def _duration_bucket(secs) -> str:
    if secs is None:
        return "unknown"
    s = int(secs)
    if s <= 15:
        return "short_0_15s"
    if s <= 30:
        return "medium_16_30s"
    if s <= 60:
        return "long_31_60s"
    return "very_long_60plus"


def main():
    # Buckets for video obs only
    by_duration   = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_voiceover  = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_vo_lang    = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_music      = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    by_subtitles  = defaultdict(lambda: {"count": 0, "high": 0, "sum": 0.0})
    dur_sector    = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0}))
    dur_occasion  = defaultdict(lambda: defaultdict(lambda: {"count": 0, "high": 0}))

    total      = 0
    video_obs  = 0
    audio_filled = 0
    dur_filled   = 0

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        total += 1
        cr  = data.get("content_ref")         or {}
        vo  = data.get("voice_observations")  or {}
        qa  = data.get("quality_assessment")  or {}
        cn  = data.get("cultural_notes")      or {}

        ct = str(cr.get("content_type") or "").lower()
        if ct not in VIDEO_TYPES:
            continue

        video_obs += 1
        eng_raw = str(qa.get("engagement_potential") or "").lower()
        eng     = ENG_MAP.get(eng_raw, 0.5)
        is_high = 1 if eng >= 0.75 else 0
        sector  = data.get("sector")               or "unknown"
        occ     = str(cn.get("occasion_relevance") or "evergreen").lower() or "evergreen"

        # ── Duration ────────────────────────────────────────────────────────────
        dur = cr.get("video_duration_seconds")
        db  = _duration_bucket(dur)
        by_duration[db]["count"]  += 1
        by_duration[db]["high"]   += is_high
        by_duration[db]["sum"]    += eng
        dur_sector[db][sector]["count"] += 1
        dur_sector[db][sector]["high"]  += is_high
        dur_occasion[db][occ]["count"]  += 1
        dur_occasion[db][occ]["high"]   += is_high
        if dur is not None:
            dur_filled += 1

        # ── Audio strategy ──────────────────────────────────────────────────────
        audio = vo.get("audio_strategy")
        if not isinstance(audio, dict):
            continue

        audio_filled += 1

        # Voiceover
        has_vo = audio.get("has_voiceover")
        if has_vo is not None:
            vl = "has_voiceover" if has_vo else "no_voiceover"
            by_voiceover[vl]["count"] += 1
            by_voiceover[vl]["high"]  += is_high
            by_voiceover[vl]["sum"]   += eng

        # Voiceover language
        vo_lang = str(audio.get("voiceover_language") or "").lower() or None
        if vo_lang:
            by_vo_lang[vo_lang]["count"] += 1
            by_vo_lang[vo_lang]["high"]  += is_high
            by_vo_lang[vo_lang]["sum"]   += eng

        # Music type
        music = str(audio.get("music_type") or "").lower() or None
        if music:
            by_music[music]["count"] += 1
            by_music[music]["high"]  += is_high
            by_music[music]["sum"]   += eng

        # Subtitles
        has_subs = audio.get("has_subtitles")
        if has_subs is not None:
            sl = "has_subtitles" if has_subs else "no_subtitles"
            by_subtitles[sl]["count"] += 1
            by_subtitles[sl]["high"]  += is_high
            by_subtitles[sl]["sum"]   += eng

    def _rate(d):
        return round(d["high"] / d["count"], 3) if d["count"] else 0

    def _table(bucket_dict, key_name):
        rows = []
        for k, d in bucket_dict.items():
            n = d["count"]
            r = _rate(d)
            rows.append({
                key_name: k, "count": n,
                "high_engagement_rate": r,
                "avg_engagement": round(d["sum"] / n, 3) if n else 0,
                "lift_vs_baseline": round(r - CORPUS_BASELINE, 3),
            })
        rows.sort(key=lambda x: (-x["high_engagement_rate"], -x["count"]))
        return rows

    duration_table  = _table(by_duration,  "duration_bucket")
    voiceover_table = _table(by_voiceover, "voiceover_presence")
    vo_lang_table   = _table(by_vo_lang,   "voiceover_language")
    music_table     = _table(by_music,     "music_type")
    subtitle_table  = _table(by_subtitles, "subtitle_presence")

    # Duration × sector rows
    dur_sector_rows = []
    for db, sects in dur_sector.items():
        for sect, d in sects.items():
            if d["count"] >= 2:
                r = round(d["high"] / d["count"], 3)
                dur_sector_rows.append({
                    "duration_bucket": db, "sector": sect,
                    "count": d["count"],
                    "high_eng_rate": r,
                    "lift": round(r - CORPUS_BASELINE, 3),
                })
    dur_sector_rows.sort(key=lambda x: -x["high_eng_rate"])

    # Findings
    findings = []
    if duration_table:
        best_d = next((r for r in duration_table if r["count"] >= 5), duration_table[0])
        findings.append(
            f"Best video duration: '{best_d['duration_bucket']}' = "
            f"{int(best_d['high_engagement_rate']*100)}% high-eng "
            f"(n={best_d['count']}, {'+' if best_d['lift_vs_baseline']>=0 else ''}"
            f"{int(best_d['lift_vs_baseline']*100)}pp)"
        )
    if voiceover_table:
        has_vo = next((r for r in voiceover_table if "has_" in r.get("voiceover_presence","")), None)
        no_vo  = next((r for r in voiceover_table if "no_"  in r.get("voiceover_presence","")), None)
        if has_vo and no_vo:
            diff = has_vo["high_engagement_rate"] - no_vo["high_engagement_rate"]
            effect = "HELPS" if diff > 0.05 else "HURTS" if diff < -0.05 else "NEUTRAL"
            findings.append(
                f"Voiceover {effect}: with={int(has_vo['high_engagement_rate']*100)}% "
                f"vs without={int(no_vo['high_engagement_rate']*100)}% "
                f"({'+'if diff>=0 else ''}{int(diff*100)}pp)"
            )
    if music_table:
        best_m = music_table[0]
        findings.append(
            f"Best music type: '{best_m['music_type']}' = "
            f"{int(best_m['high_engagement_rate']*100)}% (n={best_m['count']})"
        )
    if subtitle_table:
        has_s = next((r for r in subtitle_table if "has_" in r.get("subtitle_presence","")), None)
        no_s  = next((r for r in subtitle_table if "no_"  in r.get("subtitle_presence","")), None)
        if has_s and no_s:
            diff = has_s["high_engagement_rate"] - no_s["high_engagement_rate"]
            effect = "HELPS" if diff > 0.05 else "HURTS" if diff < -0.05 else "NEUTRAL"
            findings.append(
                f"Subtitles {effect}: with={int(has_s['high_engagement_rate']*100)}% "
                f"vs without={int(no_s['high_engagement_rate']*100)}% "
                f"({'+'if diff>=0 else ''}{int(diff*100)}pp)"
            )

    agency_rules = []
    if duration_table:
        best = next((r for r in duration_table if r["count"] >= 5), duration_table[0])
        agency_rules.append(f"Target video length: {best['duration_bucket']} — highest engagement")
    if voiceover_table:
        if voiceover_table[0]["lift_vs_baseline"] > 0:
            agency_rules.append(
                f"Use {voiceover_table[0]['voiceover_presence'].replace('_', ' ')} "
                f"— +{int(voiceover_table[0]['lift_vs_baseline']*100)}pp vs baseline"
            )
    if music_table:
        agency_rules.append(f"Audio: '{music_table[0]['music_type']}' is best-performing music type")

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "corpus_baseline": CORPUS_BASELINE,
        "total_obs": total,
        "video_obs": video_obs,
        "with_duration_data": dur_filled,
        "with_audio_data": audio_filled,
        "duration_table": duration_table,
        "voiceover_table": voiceover_table,
        "voiceover_language_table": vo_lang_table,
        "music_type_table": music_table,
        "subtitle_table": subtitle_table,
        "duration_by_sector": dur_sector_rows,
        "key_findings": findings,
        "agency_rules": agency_rules,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "video_audio_analysis.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"Video audio analysis: {video_obs} video obs / {total} total")
    print(f"  With duration data  : {dur_filled}")
    print(f"  With audio data     : {audio_filled}")
    if not audio_filled:
        print("\n  ⚠️  No audio_strategy data yet — fill audio fields first")
        print("  Duration analysis is available if video_duration_seconds is filled")
    print(f"\nVideo duration → engagement:")
    for r in duration_table:
        lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
        print(f"  {r['duration_bucket']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    if voiceover_table:
        print(f"\nVoiceover → engagement:")
        for r in voiceover_table:
            lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
            print(f"  {r['voiceover_presence']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    if music_table:
        print(f"\nMusic type → engagement:")
        for r in music_table:
            lift = f"+{int(r['lift_vs_baseline']*100)}%" if r['lift_vs_baseline'] >= 0 else f"{int(r['lift_vs_baseline']*100)}%"
            print(f"  {r['music_type']:<22} {int(r['high_engagement_rate']*100):>3}%  {lift:>6}  n={r['count']}")
    print(f"\nAgency rules:")
    for rule in agency_rules:
        print(f"  ▸ {rule}")
    print(f"\nOutput: logs/video_audio_analysis.json")


if __name__ == "__main__":
    main()
