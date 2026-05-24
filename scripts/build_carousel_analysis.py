#!/usr/bin/env python3
"""
build_carousel_analysis.py
Deep-dive on carousel content: what makes carousel posts work.
Carousels are 100 obs (15% of corpus) — a distinct format with unique mechanics.

Output: logs/carousel_analysis.json
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
def _lift(avg, baseline): return round(avg - baseline, 3) if avg is not None else None


def main():
    all_obs = [json.loads(f.read_text()) for f in OBS_ROOT.rglob("*.json")]
    carousel_obs = [d for d in all_obs if (d.get("content_ref") or {}).get("content_type") == "carousel_slide"]

    corpus_engs = [_eng(d) for d in all_obs if _eng(d) is not None]
    carousel_engs = [_eng(d) for d in carousel_obs if _eng(d) is not None]
    corpus_baseline = _avg(corpus_engs)
    carousel_avg = _avg(carousel_engs)

    N = len(carousel_obs)

    def _breakdown(key_fn, label_fn=None, min_n=3):
        """Group carousel obs by key, compute engagement per group."""
        groups = defaultdict(list)
        for d in carousel_obs:
            k = key_fn(d)
            e = _eng(d)
            if k and e is not None:
                groups[k].append(e)
        result = []
        for k, engs in sorted(groups.items(), key=lambda x: -_avg(x[1])):
            if len(engs) < min_n: continue
            avg = _avg(engs)
            result.append({
                "value":          label_fn(k) if label_fn else k,
                "count":          len(engs),
                "pct":            round(len(engs)/N, 3),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            })
        return result

    # ── Aspect ratio ──
    by_aspect = _breakdown(
        lambda d: (d.get("content_ref") or {}).get("aspect_ratio",""),
        min_n=2
    )

    # ── Slide count ──
    by_slides = _breakdown(
        lambda d: str((d.get("content_ref") or {}).get("carousel_slide_count","")) if (d.get("content_ref") or {}).get("carousel_slide_count") else None,
        min_n=2
    )

    # ── Setting ──
    by_setting = _breakdown(
        lambda d: (d.get("visual_observations") or {}).get("setting",""),
        min_n=3
    )

    # ── Visual complexity ──
    by_complexity = _breakdown(
        lambda d: (d.get("visual_observations") or {}).get("visual_complexity",""),
        min_n=3
    )

    # ── Tone ──
    by_tone = _breakdown(
        lambda d: (d.get("voice_observations") or {}).get("tone",""),
        min_n=3
    )

    # ── Occasion ──
    by_occasion = _breakdown(
        lambda d: d.get("occasion",""),
        min_n=2
    )

    # ── Sector ──
    by_sector = _breakdown(
        lambda d: d.get("sector",""),
        min_n=2
    )

    # ── Heritage vs modern ──
    by_hvm = _breakdown(
        lambda d: (d.get("cultural_notes") or {}).get("heritage_vs_modern",""),
        min_n=2
    )

    # ── Lighting ──
    by_lighting = _breakdown(
        lambda d: (d.get("visual_observations") or {}).get("lighting",""),
        min_n=3
    )

    # ── Composition ──
    by_composition = _breakdown(
        lambda d: (d.get("visual_observations") or {}).get("composition_style",""),
        min_n=3
    )

    # ── Day of week ──
    by_dow = _breakdown(
        lambda d: (d.get("content_ref") or {}).get("day_of_week",""),
        min_n=2
    )

    # ── Carousel vs other formats comparison ──
    format_comp = {}
    for ct in ["image","video","carousel_slide","reel"]:
        engs = [_eng(d) for d in all_obs
                if (d.get("content_ref") or {}).get("content_type") == ct and _eng(d) is not None]
        if engs:
            avg = _avg(engs)
            format_comp[ct] = {
                "count": len(engs),
                "avg_engagement": avg,
                "lift_vs_corpus": _lift(avg, corpus_baseline),
            }

    # ── High vs low carousel comparison ──
    high = [d for d in carousel_obs if (_eng(d) or 0) >= 0.75]
    low  = [d for d in carousel_obs if (_eng(d) or 0) <= 0.50]

    def _dominant_signals(obs_list, min_n=2):
        keys = [
            ("content_ref","aspect_ratio"),
            ("visual_observations","setting"),
            ("visual_observations","visual_complexity"),
            ("visual_observations","lighting"),
            ("voice_observations","tone"),
            ("cultural_notes","heritage_vs_modern"),
        ]
        signals = []
        for path in keys:
            c = Counter()
            for d in obs_list:
                v = (d.get(path[0]) or {}).get(path[1],"")
                if v: c[v] += 1
            for val, n in c.most_common(2):
                if n >= min_n:
                    signals.append({
                        "dimension": path[1],
                        "value": val,
                        "count": n,
                        "pct": round(n/len(obs_list),3) if obs_list else 0,
                    })
        return sorted(signals, key=lambda x: -x["pct"])[:8]

    # ── Account-level carousel performance ──
    acc_carousel = defaultdict(list)
    for d in carousel_obs:
        e = _eng(d)
        acc = d.get("account_handle_normalized","")
        if acc and e is not None:
            acc_carousel[acc].append(e)

    acc_perf = []
    for acc, engs in sorted(acc_carousel.items(), key=lambda x: -_avg(x[1])):
        avg = _avg(engs)
        acc_perf.append({
            "account": acc,
            "count": len(engs),
            "avg_engagement": avg,
            "lift_vs_carousel_avg": _lift(avg, carousel_avg),
        })

    # ── Winning carousel formula ──
    winning_formula = {}
    for dim_data in by_aspect[:1]:
        winning_formula["aspect_ratio"] = dim_data["value"]
    for dim_data in by_setting[:1]:
        winning_formula["setting"] = dim_data["value"]
    for dim_data in by_complexity[:1]:
        winning_formula["visual_complexity"] = dim_data["value"]
    for dim_data in by_tone[:1]:
        winning_formula["tone"] = dim_data["value"]
    for dim_data in by_lighting[:1]:
        winning_formula["lighting"] = dim_data["value"]
    for dim_data in by_dow[:1]:
        winning_formula["best_day"] = dim_data["value"]
    winning_formula["predicted_engagement"] = carousel_avg

    out = {
        "meta": {
            "schema_version": 1,
            "carousel_obs": N,
            "corpus_obs": len(all_obs),
            "carousel_pct_of_corpus": round(N/len(all_obs),3),
            "carousel_avg_engagement": carousel_avg,
            "carousel_lift_vs_corpus": _lift(carousel_avg, corpus_baseline),
            "corpus_baseline": corpus_baseline,
            "high_eng_count": len(high),
            "low_eng_count":  len(low),
        },
        "format_comparison":   format_comp,
        "by_aspect_ratio":     by_aspect,
        "by_slide_count":      by_slides,
        "by_setting":          by_setting,
        "by_visual_complexity":by_complexity,
        "by_tone":             by_tone,
        "by_occasion":         by_occasion,
        "by_sector":           by_sector,
        "by_heritage_modern":  by_hvm,
        "by_lighting":         by_lighting,
        "by_composition":      by_composition,
        "by_day_of_week":      by_dow,
        "high_eng_signals":    _dominant_signals(high),
        "low_eng_signals":     _dominant_signals(low),
        "account_performance": acc_perf,
        "winning_formula":     winning_formula,
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "carousel_analysis.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2)
    )

    # ── Print summary ──
    W = 68
    print(f"\n{'═'*W}")
    print(f"  CAROUSEL ANALYSIS")
    print(f"  {N} carousel obs  ·  {carousel_avg:.0%} avg eng  ·  "
          f"({_lift(carousel_avg, corpus_baseline):+.0%} vs corpus {corpus_baseline:.0%})")
    print(f"{'═'*W}\n")

    print(f"  FORMAT COMPARISON")
    for ct, v in sorted(format_comp.items(), key=lambda x: -x[1]["avg_engagement"]):
        lift_str = f"{v['lift_vs_corpus']:+.0%}"
        print(f"    {ct:<22}  {v['avg_engagement']:.0%}  (lift {lift_str})  n={v['count']}")

    if by_aspect:
        print(f"\n  ASPECT RATIO × ENGAGEMENT")
        for r in by_aspect:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['value']:<22}  {r['avg_engagement']:.0%}  (lift {lift_str})  n={r['count']}")

    if by_complexity:
        print(f"\n  VISUAL COMPLEXITY × ENGAGEMENT")
        for r in by_complexity:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['value']:<22}  {r['avg_engagement']:.0%}  (lift {lift_str})  n={r['count']}")

    if by_tone:
        print(f"\n  TONE × ENGAGEMENT")
        for r in by_tone[:5]:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['value']:<22}  {r['avg_engagement']:.0%}  (lift {lift_str})  n={r['count']}")

    if by_occasion:
        print(f"\n  OCCASION × ENGAGEMENT")
        for r in by_occasion[:5]:
            lift_str = f"{r['lift_vs_corpus']:+.0%}" if r['lift_vs_corpus'] is not None else "—"
            print(f"    {r['value']:<22}  {r['avg_engagement']:.0%}  (lift {lift_str})  n={r['count']}")

    if out["high_eng_signals"]:
        print(f"\n  HIGH-ENGAGEMENT CAROUSEL SIGNALS (≥75%)")
        for s in out["high_eng_signals"][:6]:
            print(f"    ✓ {s['dimension']}={s['value']}  ({int(s['pct']*100)}% of high-eng carousels)")

    print(f"\n  WINNING FORMULA:")
    for k, v in winning_formula.items():
        if k != "predicted_engagement":
            print(f"    {k}: {v}")
    print(f"    predicted_engagement: {winning_formula.get('predicted_engagement',0):.0%}")

    print(f"\n  Output → logs/carousel_analysis.json\n")


if __name__ == "__main__":
    main()
