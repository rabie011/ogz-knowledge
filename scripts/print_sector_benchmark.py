#!/usr/bin/env python3
"""
print_sector_benchmark.py
Side-by-side sector comparison across all key dimensions.
Single command for a full cross-sector intelligence snapshot.

Usage:
  python3 scripts/print_sector_benchmark.py
  python3 scripts/print_sector_benchmark.py --sector food_and_beverage
"""
import json, argparse
from pathlib import Path
from collections import defaultdict, Counter

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

ENG_MAP = {"high":1.0,"very_high":1.0,"above_average":0.75,"medium":0.5,"low":0.0,"below_average":0.25}
SECTORS = ["f_and_b", "beauty", "retail"]
SECTOR_LABELS = {"f_and_b":"F&B","beauty":"BEAUTY","retail":"RETAIL"}

def _eng(d): return ENG_MAP.get((d.get("quality_assessment") or {}).get("engagement_potential",""))
def _avg(v): return round(sum(v)/len(v),3) if v else None

def _load(name):
    p = LOGS / name
    try: return json.loads(p.read_text()) if p.exists() else {}
    except: return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", type=str, default=None)
    args = parser.parse_args()

    all_obs = [json.loads(f.read_text()) for f in OBS_ROOT.rglob("*.json")]
    corpus_engs = [_eng(d) for d in all_obs if _eng(d) is not None]
    corpus_avg = _avg(corpus_engs)

    # Partition by sector
    by_sector = defaultdict(list)
    for d in all_obs:
        sec = d.get("sector","")
        if sec: by_sector[sec].append(d)

    # Requested sector filter
    focus_secs = [args.sector] if args.sector else SECTORS

    def _sector_dimension(obs_list, key_fn, top_n=1):
        """Return top-N values for a dimension in a sector."""
        c = Counter()
        eng_map = defaultdict(list)
        for d in obs_list:
            k = key_fn(d)
            e = _eng(d)
            if k and e is not None:
                c[k] += 1
                eng_map[k].append(e)
        # Sort by count, return top-N
        return [(k, c[k], round(_avg(eng_map[k]),2)) for k,_ in c.most_common(top_n)]

    W = 72
    print(f"\n{'═'*W}")
    print(f"  OGZ SECTOR BENCHMARK")
    print(f"  Corpus: {len(all_obs)} obs  ·  avg {corpus_avg:.0%}")
    print(f"{'═'*W}\n")

    # ── Overview table ──────────────────────────────────────────────────────
    print(f"  {'DIMENSION':<30}  {'F&B':>10}  {'BEAUTY':>10}  {'RETAIL':>10}")
    print(f"  {'─'*64}")

    rows = [
        ("Obs count",           lambda s: str(len(by_sector.get(s,[])))),
        ("Avg engagement",      lambda s: f"{_avg([_eng(d) for d in by_sector.get(s,[]) if _eng(d) is not None]) or 0:.0%}"),
        ("Lift vs corpus",      lambda s: f"{(_avg([_eng(d) for d in by_sector.get(s,[]) if _eng(d) is not None]) or 0) - corpus_avg:+.0%}"),
    ]

    for label, fn in rows:
        vals = [fn(s) for s in ["f_and_b","beauty","retail"]]
        print(f"  {label:<30}  {vals[0]:>10}  {vals[1]:>10}  {vals[2]:>10}")

    print()

    # ── Dominant signals per sector ──────────────────────────────────────────
    DIMS = [
        ("Top content_type",   lambda d: (d.get("content_ref") or {}).get("content_type","")),
        ("Top aspect_ratio",   lambda d: (d.get("content_ref") or {}).get("aspect_ratio","")),
        ("Top setting",        lambda d: (d.get("visual_observations") or {}).get("setting","")),
        ("Top lighting",       lambda d: (d.get("visual_observations") or {}).get("lighting","")),
        ("Top composition",    lambda d: (d.get("visual_observations") or {}).get("composition_style","")),
        ("Top visual_complex", lambda d: (d.get("visual_observations") or {}).get("visual_complexity","")),
        ("Top tone",           lambda d: (d.get("voice_observations") or {}).get("tone","")),
        ("Top register",       lambda d: (d.get("voice_observations") or {}).get("register","")),
        ("Top heritage_frame", lambda d: (d.get("cultural_notes") or {}).get("heritage_vs_modern","")),
        ("Top occasion",       lambda d: d.get("occasion","")),
        ("Top day_of_week",    lambda d: (d.get("content_ref") or {}).get("day_of_week","")),
    ]

    print(f"  {'DOMINANT SIGNALS':<30}  {'F&B':>10}  {'BEAUTY':>10}  {'RETAIL':>10}")
    print(f"  {'─'*64}")

    for label, key_fn in DIMS:
        row = []
        for sec in ["f_and_b","beauty","retail"]:
            obs_list = by_sector.get(sec, [])
            top = _sector_dimension(obs_list, key_fn, top_n=1)
            if top:
                val, n, avg = top[0]
                # Truncate long values
                val_short = val[:12] if len(val) > 12 else val
                row.append(f"{val_short}({avg:.0%})")
            else:
                row.append("—")
        print(f"  {label:<30}  {row[0]:>10}  {row[1]:>10}  {row[2]:>10}")

    print()

    # ── Engagement by content type per sector ────────────────────────────────
    print(f"  ENGAGEMENT BY FORMAT")
    print(f"  {'─'*64}")
    for ct in ["image","carousel_slide","video","reel"]:
        row = []
        for sec in ["f_and_b","beauty","retail"]:
            engs = [_eng(d) for d in by_sector.get(sec,[])
                    if (d.get("content_ref") or {}).get("content_type") == ct and _eng(d) is not None]
            if engs:
                row.append(f"{_avg(engs):.0%}(n={len(engs)})")
            else:
                row.append("—")
        print(f"  {ct:<30}  {row[0]:>10}  {row[1]:>10}  {row[2]:>10}")

    print()

    # ── Best occasion per sector ─────────────────────────────────────────────
    print(f"  BEST OCCASION PER SECTOR")
    print(f"  {'─'*64}")
    all_occ = sorted(set(d.get("occasion","") for d in all_obs if d.get("occasion","")))
    for occ in all_occ:
        row = []
        any_data = False
        for sec in ["f_and_b","beauty","retail"]:
            engs = [_eng(d) for d in by_sector.get(sec,[])
                    if d.get("occasion","") == occ and _eng(d) is not None]
            if engs:
                row.append(f"{_avg(engs):.0%}(n={len(engs)})")
                any_data = True
            else:
                row.append("—")
        if any_data:
            print(f"  {occ:<30}  {row[0]:>10}  {row[1]:>10}  {row[2]:>10}")

    print()

    # ── Caption data (once extracted) ────────────────────────────────────────
    cap_counts = {}
    for sec in ["f_and_b","beauty","retail"]:
        obs_list = by_sector.get(sec, [])
        filled = sum(1 for d in obs_list
                     if (d.get("voice_observations") or {}).get("caption_text") is not None)
        cap_counts[sec] = (filled, len(obs_list))

    print(f"  CAPTION EXTRACTION STATUS")
    print(f"  {'─'*64}")
    f_cnt  = cap_counts.get("f_and_b", (0,0))
    b_cnt  = cap_counts.get("beauty",  (0,0))
    r_cnt  = cap_counts.get("retail",  (0,0))
    print(f"  {'caption_text filled':<30}  "
          f"{f_cnt[0]}/{f_cnt[1]:>4}({f_cnt[0]/max(f_cnt[1],1):.0%})  "
          f"{b_cnt[0]}/{b_cnt[1]:>2}({b_cnt[0]/max(b_cnt[1],1):.0%})  "
          f"{r_cnt[0]}/{r_cnt[1]:>2}({r_cnt[0]/max(r_cnt[1],1):.0%})")

    # ── Cross-sector opportunity ─────────────────────────────────────────────
    cso = _load("cross_sector_opportunity.json")
    opp_reports = cso.get("opportunity_reports") or {}
    if opp_reports:
        print(f"\n  TOP CROSS-SECTOR OPPORTUNITIES  (adopt from F&B benchmark)")
        print(f"  {'─'*64}")
        for sec, report in opp_reports.items():
            label = SECTOR_LABELS.get(sec, sec.upper())
            gaps = report.get("top_opportunities") or []
            for g in gaps[:2]:
                dim  = g.get("dimension","")
                best = g.get("adopt_this","")
                lift = g.get("potential_uplift",0)
                cur  = g.get("target_current","")
                src  = g.get("adopt_from_sector","f_and_b")
                print(f"  {label:<8} {dim}: '{cur}' → '{best}' (from {src}) +{lift:.0%} uplift")

    print(f"\n{'═'*W}\n")


if __name__ == "__main__":
    main()
