#!/usr/bin/env python3
"""
print_sector_occasion_matrix.py
Cross-tab: for every sector × occasion combo (n≥5), what format + tone + heritage wins?
Answers: "F&B × Ramadan — what should we make?"

Usage:
  python3 scripts/print_sector_occasion_matrix.py
  python3 scripts/print_sector_occasion_matrix.py --sector food_and_beverage
  python3 scripts/print_sector_occasion_matrix.py --occasion ramadan
  python3 scripts/print_sector_occasion_matrix.py --min_n 3
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

SECTOR_KEY = {
    "food_and_beverage":"f_and_b","f&b":"f_and_b","fb":"f_and_b","food":"f_and_b",
    "beauty":"beauty","beauty_personal_care":"beauty",
    "retail":"retail","retail_lifestyle":"retail",
}
SECTOR_LABELS = {"f_and_b":"F&B","beauty":"BEAUTY","retail":"RETAIL"}


def _best(by_val, min_n=3):
    """Return (best_value, best_avg, n) for a dimension counter."""
    candidates = [(v, _avg(engs), len(engs)) for v, engs in by_val.items() if len(engs) >= min_n]
    if not candidates:
        candidates = [(v, _avg(engs), len(engs)) for v, engs in by_val.items() if engs]
    if not candidates: return "?", 0, 0
    best = max(candidates, key=lambda x: (x[1] or 0))
    return best[0], best[1] or 0, best[2]


def build_matrix(min_n=5):
    # cell[sector][occasion] = {eng: [], content_type: {}, tone: {}, heritage: {}, complexity: {}}
    cell = defaultdict(lambda: defaultdict(lambda: {
        "eng": [],
        "content_type": defaultdict(list),
        "aspect_ratio":  defaultdict(list),
        "tone":          defaultdict(list),
        "heritage":      defaultdict(list),
        "complexity":    defaultdict(list),
        "composition":   defaultdict(list),
    }))

    for f in OBS_ROOT.rglob("*.json"):
        d    = json.loads(f.read_text())
        sec  = d.get("sector","")
        occ  = d.get("occasion","") or "evergreen"
        e    = _eng(d)
        if not sec or e is None: continue

        cr   = d.get("content_ref")  or {}
        vo   = d.get("voice_observations") or {}
        vis  = d.get("visual_observations") or {}
        cult = d.get("cultural_notes") or {}

        ct   = cr.get("content_type","")
        ar   = cr.get("aspect_ratio","")
        tone = vo.get("tone","")
        hvm  = cult.get("heritage_vs_modern","")
        cpx  = vis.get("visual_complexity","")
        comp = vis.get("composition_style","")

        c = cell[sec][occ]
        c["eng"].append(e)
        for dim, val in [("content_type",ct),("aspect_ratio",ar),("tone",tone),
                          ("heritage",hvm),("complexity",cpx),("composition",comp)]:
            if val: c[dim][val].append(e)

    # Flatten to rows
    rows = []
    for sec, occ_data in cell.items():
        for occ, c in occ_data.items():
            n = len(c["eng"])
            if n < min_n: continue
            avg = _avg(c["eng"]) or 0

            best_ct,   avg_ct,   n_ct   = _best(c["content_type"])
            best_ar,   avg_ar,   n_ar   = _best(c["aspect_ratio"])
            best_tone, avg_tone, n_tone = _best(c["tone"])
            best_hvm,  avg_hvm,  n_hvm  = _best(c["heritage"])
            best_cpx,  avg_cpx,  n_cpx  = _best(c["complexity"])
            best_comp, avg_comp, n_comp = _best(c["composition"])

            rows.append({
                "sector": sec, "occasion": occ, "n": n, "avg": avg,
                "best_format":      best_ct,
                "best_aspect":      best_ar,
                "best_tone":        best_tone,
                "best_heritage":    best_hvm,
                "best_complexity":  best_cpx,
                "best_composition": best_comp,
            })

    rows.sort(key=lambda x: (x["sector"], -x["avg"]))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector",   type=str, default=None)
    parser.add_argument("--occasion", type=str, default=None)
    parser.add_argument("--min_n",    type=int, default=5)
    args = parser.parse_args()

    sec_filter = SECTOR_KEY.get(args.sector.lower(), args.sector) if args.sector else None
    occ_filter = args.occasion.lower().replace(" ","_") if args.occasion else None

    rows = build_matrix(min_n=args.min_n)

    if sec_filter: rows = [r for r in rows if r["sector"] == sec_filter]
    if occ_filter: rows = [r for r in rows if r["occasion"] == occ_filter]

    W = 72
    scope = ""
    if sec_filter: scope += f" · sector={sec_filter}"
    if occ_filter: scope += f" · occasion={occ_filter}"

    print(f"\n{'═'*W}")
    print(f"  SECTOR × OCCASION FORMAT MATRIX{scope}")
    print(f"  {len(rows)} combo(s)  ·  min n={args.min_n}")
    print(f"{'═'*W}")

    current_sec = None
    for r in rows:
        if r["sector"] != current_sec:
            current_sec = r["sector"]
            label = SECTOR_LABELS.get(current_sec, current_sec.upper())
            print(f"\n  ── {label} ──────────────────────────────────────────────────")
            print(f"  {'OCCASION':<20} {'AVG':>5} {'N':>4}  {'FORMAT':<16} {'TONE':<16} {'HERITAGE':<12} COMPLEXITY")
            print(f"  {'─'*66}")

        occ_display = r["occasion"].replace("_"," ")
        grade = "★" if r["avg"] >= 0.80 else "◆" if r["avg"] >= 0.70 else "○"
        print(f"  {occ_display:<20} {r['avg']:.0%}  {r['n']:>3}  "
              f"{r['best_format']:<16} {r['best_tone']:<16} {r['best_heritage']:<12} {r['best_complexity']}")

    if not rows:
        print(f"\n  No combos with n≥{args.min_n} found.\n")
        return

    # Save to logs
    out_path = LOGS / "sector_occasion_matrix.json"
    LOGS.mkdir(exist_ok=True)
    out_path.write_text(json.dumps({
        "schema_version": 1,
        "generated_at": "2026-05-25T00:00:00Z",
        "min_n": args.min_n,
        "rows": rows,
    }, ensure_ascii=False, indent=2))

    # Agency summary — highlight the top recipe per sector
    print(f"\n  {'─'*W}")
    print(f"  AGENCY RULES — top occasion per sector")
    print(f"  {'─'*60}")
    by_sec = {}
    for r in rows:
        if r["sector"] not in by_sec or r["avg"] > by_sec[r["sector"]]["avg"]:
            by_sec[r["sector"]] = r
    for sec, r in sorted(by_sec.items()):
        label = SECTOR_LABELS.get(sec, sec.upper())
        n_warn = " ⚠ low n" if r["n"] < 10 else ""
        print(f"  {label:<8}  best occasion: {r['occasion'].replace('_',' '):<18} "
              f"({r['avg']:.0%}, n={r['n']}{n_warn})  →  {r['best_format']} + {r['best_tone']} + {r['best_heritage']}")

    print(f"\n  Log saved: logs/sector_occasion_matrix.json")
    print(f"{'═'*W}\n")


if __name__ == "__main__":
    main()
