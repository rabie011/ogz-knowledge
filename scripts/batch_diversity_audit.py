#!/usr/bin/env python3
"""B_div_gate AUDIT — run the batch-diversity gate over a client's year map.

The hard answer to Mohamed's 2026-06-13 scar («still family / make them different»):
slides a window across the year map and flags any window where one scene-core or one
recipe exceeds the ceiling (~30%). Names the EXCESS slots to re-roll. Zero-LLM — reads
the planned angle_theme/formula already on disk.

Usage: python3 scripts/batch_diversity_audit.py --handle eatjurisha [--window 20] [--ceiling 0.30]
Exit 1 if any window violates (so it can gate a batch run).
"""
import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
from render_client_slot import batch_diversity_check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--window", type=int, default=20)  # the batch size (his 20/sitting law)
    ap.add_argument("--ceiling", type=float, default=0.30)
    a = ap.parse_args()
    ymf = BASE / "clients" / a.handle / "year_map.json"
    ymap = json.loads(ymf.read_text())
    slots = [s for mm in ymap["months"].values() for s in mm]
    slots.sort(key=lambda s: s.get("date", ""))

    worst, flagged = None, 0
    for i in range(0, len(slots), a.window):
        win = slots[i:i + a.window]
        r = batch_diversity_check(win, a.ceiling)
        if not r["ok"]:
            flagged += 1
            span = f"{win[0].get('date','?')}..{win[-1].get('date','?')}"
            print(f"  🔴 window {span} ({r['n']} slots, ceiling {r['ceiling_pct']}%):")
            for v in r["violations"]:
                print(f"      {v['kind']} «{v['key']}» = {v['count']}/{r['n']} ({v['pct']}%) "
                      f"→ re-roll {len(v['slots'])}: {v['slots'][:5]}")
            if worst is None or r["violations"][0]["pct"] > worst:
                worst = r["violations"][0]["pct"]
    total_windows = (len(slots) + a.window - 1) // a.window
    print(f"\n{a.handle}: {flagged}/{total_windows} windows violate "
          f"(worst {worst}% vs {round(a.ceiling*100)}% ceiling)" if flagged
          else f"\n🟢 {a.handle}: all {total_windows} windows diverse (no core/recipe > {round(a.ceiling*100)}%)")
    raise SystemExit(1 if flagged else 0)


if __name__ == "__main__":
    main()
