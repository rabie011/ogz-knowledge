#!/usr/bin/env python3
"""
build_video_strategy_analysis.py
Analysis of video + reel content: what drives engagement in motion content.
Video = 222 obs, Reel = 37 obs → 259 total motion content obs (40% of corpus).

Output: logs/video_strategy_analysis.json
"""
import json
from pathlib import Path
from collections import Counter, defaultdict

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}

def _eng(d): return ENG_MAP.get((d.get("quality_assessment") or {}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None
def _lift(avg, baseline): return round(avg - baseline, 3) if avg is not None and baseline is not None else None


def main():
    all_obs = [json.loads(f.read_text()) for f in OBS_ROOT.rglob("*.json")]

    corpus_engs = [_eng(d) for d in all_obs if _eng(d) is not None]
    corpus_baseline = _avg(corpus_engs)

    video_obs = [d for d in all_obs if (d.get("content_ref") or {}).get("content_type") in ("video","reel")]
    reel_obs  = [d for d in all_obs if (d.get("content_ref") or {}).get("content_type") == "reel"]
    vid_only  = [d for d in all_obs if (d.get("content_ref") or {}).get("content_type") == "video"]
    static_obs= [d for d in all_obs if (d.get("content_ref") or {}).get("content_type") in ("image","carousel_slide")]

    N = len(video_obs)

    # ── Video duration buckets ──
    dur_buckets = defaultdict(list)
    for d in video_obs:
        dur = (d.get("content_ref") or {}).get("video_duration_seconds")
        e   = _eng(d)
        if dur and e is not None:
            if dur <= 15:   bucket = "short_0_15s"
            elif dur <= 30: bucket = "medium_16_30s"
            elif dur <= 60: bucket = "long_31_60s"
            else:           bucket = "extended_60s_plus"
            dur_buckets[bucket].append((e, dur))

    by_duration = []
    for bucket in ["short_0_15s","medium_16_30s","long_31_60s","extended_60s_plus"]:
        items = dur_buckets.get(bucket, [])
        if len(items) >= 2:
            engs = [x[0] for x in items]
            avg_dur = round(sum(x[1] for x in items)/len(items), 1)
            by_duration.append({
                "bucket": bucket,
                "count": len(items),
                "avg_duration_s": avg_dur,
                "avg_engagement": _avg(engs),
                "lift_vs_corpus": _lift(_avg(engs), corpus_baseline),
            })

    # ── Video type: video vs reel ──
    video_eng = [_eng(d) for d in vid_only  if _eng(d) is not None]
    reel_eng  = [_eng(d) for d in reel_obs  if _eng(d) is not None]
    static_eng= [_eng(d) for d in static_obs if _eng(d) is not None]

    type_comparison = {
        "video":          {"count": len(vid_only),   "avg": _avg(video_eng),  "lift": _lift(_avg(video_eng),  corpus_baseline)},
        "reel":           {"count": len(reel_obs),   "avg": _avg(reel_eng),   "lift": _lift(_avg(reel_eng),   corpus_baseline)},
        "static_content": {"count": len(static_obs), "avg": _avg(static_eng), "lift": _lift(_avg(static_eng), corpus_baseline)},
    }

    # ── Aspect ratio for video ──
    def _breakdown(obs_list, key_fn, min_n=3):
        groups = defaultdict(list)
        for d in obs_list:
            k = key_fn(d)
            e = _eng(d)
            if k and e is not None:
                groups[k].append(e)
        result = []
        for k, engs in sorted(groups.items(), key=lambda x: -_avg(x[1])):
            if len(engs) < min_n: continue
            avg = _avg(engs)
            result.append({
                "value": k,
                "count": len(engs),
                "pct": round(len(engs)/len(obs_list),3),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            })
        return result

    by_aspect      = _breakdown(video_obs, lambda d: (d.get("content_ref") or {}).get("aspect_ratio",""), min_n=2)
    by_setting     = _breakdown(video_obs, lambda d: (d.get("visual_observations") or {}).get("setting",""))
    by_complexity  = _breakdown(video_obs, lambda d: (d.get("visual_observations") or {}).get("visual_complexity",""))
    by_tone        = _breakdown(video_obs, lambda d: (d.get("voice_observations") or {}).get("tone",""))
    by_occasion    = _breakdown(video_obs, lambda d: d.get("occasion",""), min_n=2)
    by_sector      = _breakdown(video_obs, lambda d: d.get("sector",""), min_n=2)
    by_lighting    = _breakdown(video_obs, lambda d: (d.get("visual_observations") or {}).get("lighting",""))
    by_composition = _breakdown(video_obs, lambda d: (d.get("visual_observations") or {}).get("composition_style",""))
    by_hvm         = _breakdown(video_obs, lambda d: (d.get("cultural_notes") or {}).get("heritage_vs_modern",""), min_n=2)
    by_dow         = _breakdown(video_obs, lambda d: (d.get("content_ref") or {}).get("day_of_week",""), min_n=3)
    by_editing     = _breakdown(video_obs, lambda d: (d.get("content_ref") or {}).get("editing_pace",""), min_n=2)

    # ── Video with audio data (has_voiceover etc.) ──
    voiceover_data = []
    for d in video_obs:
        aud = d.get("audio_strategy") or {}
        hv  = aud.get("has_voiceover")
        mt  = aud.get("music_type")
        e   = _eng(d)
        if hv is not None or mt:
            voiceover_data.append({"has_voiceover": hv, "music_type": mt, "eng": e})

    # Group by has_voiceover
    vo_groups = defaultdict(list)
    for item in voiceover_data:
        k = "with_voiceover" if item["has_voiceover"] else "music_only"
        if item["eng"] is not None: vo_groups[k].append(item["eng"])

    by_voiceover = [
        {"value": k, "count": len(v), "avg_engagement": _avg(v), "lift_vs_corpus": _lift(_avg(v), corpus_baseline)}
        for k, v in vo_groups.items() if len(v) >= 2
    ]

    # Group by music_type
    mt_groups = defaultdict(list)
    for item in voiceover_data:
        if item["music_type"] and item["eng"] is not None:
            mt_groups[item["music_type"]].append(item["eng"])

    by_music_type = [
        {"value": k, "count": len(v), "avg_engagement": _avg(v), "lift_vs_corpus": _lift(_avg(v), corpus_baseline)}
        for k, v in sorted(mt_groups.items(), key=lambda x: -_avg(x[1])) if len(v) >= 2
    ]

    # ── High vs low comparison for video ──
    high = [d for d in video_obs if (_eng(d) or 0) >= 0.75]
    low  = [d for d in video_obs if (_eng(d) or 0) <= 0.50]

    def _dominant(obs_list, min_n=2):
        keys = [
            ("content_ref","aspect_ratio"),("content_ref","content_type"),
            ("visual_observations","setting"),("visual_observations","visual_complexity"),
            ("voice_observations","tone"),("cultural_notes","heritage_vs_modern"),
        ]
        out = []
        for path in keys:
            c = Counter()
            for d in obs_list:
                v = (d.get(path[0]) or {}).get(path[1],"")
                if v: c[v] += 1
            for val, n in c.most_common(2):
                if n >= min_n:
                    out.append({"dimension": path[1], "value": val, "count": n,
                                "pct": round(n/len(obs_list),3) if obs_list else 0})
        return sorted(out, key=lambda x: -x["pct"])[:8]

    # ── Video vs static: head-to-head by occasion ──
    occasions_all = set(d.get("occasion","") for d in all_obs)
    video_vs_static = []
    for occ in sorted(occasions_all):
        if not occ: continue
        v_engs = [_eng(d) for d in video_obs if d.get("occasion","") == occ and _eng(d) is not None]
        s_engs = [_eng(d) for d in static_obs if d.get("occasion","") == occ and _eng(d) is not None]
        if len(v_engs) >= 3 and len(s_engs) >= 3:
            v_avg = _avg(v_engs)
            s_avg = _avg(s_engs)
            video_vs_static.append({
                "occasion": occ,
                "video_avg": v_avg, "video_n": len(v_engs),
                "static_avg": s_avg, "static_n": len(s_engs),
                "winner": "video" if v_avg > s_avg else "static",
                "gap": round(abs(v_avg - s_avg), 3),
            })

    # ── Winning video formula ──
    video_avg = _avg([_eng(d) for d in video_obs if _eng(d) is not None])
    winning_formula = {}
    for r in by_aspect[:1]:   winning_formula["aspect_ratio"]      = r["value"]
    for r in by_setting[:1]:  winning_formula["setting"]           = r["value"]
    for r in by_complexity[:1]:winning_formula["visual_complexity"] = r["value"]
    for r in by_tone[:1]:     winning_formula["tone"]              = r["value"]
    for r in by_dow[:1]:      winning_formula["best_day"]          = r["value"]
    for r in by_hvm[:1]:      winning_formula["heritage_framing"]  = r["value"]
    winning_formula["predicted_engagement"] = video_avg

    out = {
        "meta": {
            "schema_version": 1,
            "video_obs": N,
            "reel_obs": len(reel_obs),
            "video_only_obs": len(vid_only),
            "corpus_obs": len(all_obs),
            "video_pct_of_corpus": round(N/len(all_obs), 3),
            "video_avg_engagement": video_avg,
            "video_lift_vs_corpus": _lift(video_avg, corpus_baseline),
            "corpus_baseline": corpus_baseline,
            "audio_data_count": len(voiceover_data),
        },
        "type_comparison":   type_comparison,
        "by_duration":       by_duration,
        "by_aspect_ratio":   by_aspect,
        "by_setting":        by_setting,
        "by_visual_complexity": by_complexity,
        "by_tone":           by_tone,
        "by_occasion":       by_occasion,
        "by_sector":         by_sector,
        "by_lighting":       by_lighting,
        "by_composition":    by_composition,
        "by_heritage_modern":by_hvm,
        "by_day_of_week":    by_dow,
        "by_editing_pace":   by_editing,
        "by_voiceover":      by_voiceover,
        "by_music_type":     by_music_type,
        "high_eng_signals":  _dominant(high),
        "low_eng_signals":   _dominant(low),
        "video_vs_static_by_occasion": video_vs_static,
        "winning_formula":   winning_formula,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "video_strategy_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    # ── Print summary ──
    W = 68
    print(f"\n{'═'*W}")
    print(f"  VIDEO STRATEGY ANALYSIS")
    print(f"  {N} video/reel obs  ·  avg {video_avg:.0%}  ·  "
          f"({_lift(video_avg, corpus_baseline):+.0%} vs corpus {corpus_baseline:.0%})")
    print(f"{'═'*W}\n")

    print(f"  VIDEO vs REEL vs STATIC")
    for k, v in sorted(type_comparison.items(), key=lambda x: -(x[1]["avg"] or 0)):
        lift_str = f"{v['lift']:+.0%}" if v["lift"] is not None else "—"
        print(f"    {k:<22}  avg={v['avg']:.0%}  lift={lift_str}  n={v['count']}")

    if by_aspect:
        print(f"\n  ASPECT RATIO × ENGAGEMENT")
        for r in by_aspect:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['value']:<22}  {r['avg_engagement']:.0%}  ({lift_str})  n={r['count']}")

    if by_duration:
        print(f"\n  DURATION BUCKETS × ENGAGEMENT  (n={sum(r['count'] for r in by_duration)} obs with duration)")
        for r in sorted(by_duration, key=lambda x: -(x["avg_engagement"] or 0)):
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['bucket']:<22}  avg={r['avg_engagement']:.0%}  ({lift_str})  avg_len={r['avg_duration_s']}s  n={r['count']}")

    if by_complexity:
        print(f"\n  VISUAL COMPLEXITY × ENGAGEMENT")
        for r in by_complexity:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['value']:<22}  {r['avg_engagement']:.0%}  ({lift_str})  n={r['count']}")

    if by_tone:
        print(f"\n  TONE × ENGAGEMENT")
        for r in by_tone[:5]:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['value']:<22}  {r['avg_engagement']:.0%}  ({lift_str})  n={r['count']}")

    if video_vs_static:
        print(f"\n  VIDEO vs STATIC BY OCCASION")
        for v in sorted(video_vs_static, key=lambda x: -x["gap"]):
            winner = v["winner"].upper()
            print(f"    {v['occasion']:<22}  winner={winner:<7}  gap={v['gap']:.0%}  "
                  f"(video={v['video_avg']:.0%} n={v['video_n']}  "
                  f"static={v['static_avg']:.0%} n={v['static_n']})")

    if out["high_eng_signals"]:
        print(f"\n  HIGH-ENGAGEMENT VIDEO SIGNALS (≥75%)")
        for s in out["high_eng_signals"][:5]:
            print(f"    ✓ {s['dimension']}={s['value']}  ({int(s['pct']*100)}% of high-eng videos)")

    print(f"\n  Output → logs/video_strategy_analysis.json\n")


if __name__ == "__main__":
    main()
