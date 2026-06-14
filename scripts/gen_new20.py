#!/usr/bin/env python3
"""Mohamed's order (2026-06-14): a NEW 20-batch — updated + creative, after the repetition
root-hunt + fixes. Spreads across ALL 3 pilots (myfitness leads — breaks 'everything food')
and across MONTHS (not 7 sequential days) so occasions/cores vary. Renders via the fixed
render_client_slot (brain-method body + door diversity + regen-don't-readmit + few-shot
quarantine). Suffix __v6 = the new fixed-pipeline batch; seed_judge_cards stages the gated ones.
"""
import json, subprocess, sys, time
from pathlib import Path

B = Path(__file__).parent.parent
# myfitness FIRST + most slots: the non-food pilot leads the batch to break the food monoculture
PLAN = [("myfitness.sa", 7), ("eatjurisha", 7), ("albaik", 6)]


def spread_dates(handle, n):
    """Pick n dates spread across distinct months (max variety of season/occasion)."""
    ym = json.loads((B / "clients" / handle / "year_map.json").read_text())
    months = list(ym["months"].items())  # [(YYYY-MM, [slots])...] in window order
    picked = []
    # walk months round-robin, taking a slot near the middle of each, until we have n
    mid_idx, round_no = {}, 0
    while len(picked) < n and round_no < 40:
        for mk, slots in months:
            if len(picked) >= n:
                break
            if not slots:
                continue
            j = (len(slots) // 3 + round_no * 7) % len(slots)
            s = slots[j]
            d = s.get("date")
            if d and d not in [p[0] for p in picked]:
                picked.append((d, s.get("occasion") or s.get("type") or "daily"))
        round_no += 1
    return picked[:n]


def main():
    log = B / "data/gen_new20.log"
    total_ok = total_fail = 0
    out = []
    for handle, n in PLAN:
        dates = spread_dates(handle, n)
        out.append(f"\n=== {handle}: {len(dates)} slots ===")
        for d, occ in dates:
            cmd = ["python3", str(B / "scripts/render_client_slot.py"),
                   "--handle", handle, "--date", d, "--brain", "auto", "--suffix", "__v6"]
            r = subprocess.run(cmd, capture_output=True, text=True)
            ok = r.returncode == 0
            total_ok += ok
            total_fail += (not ok)
            tail = (r.stderr or r.stdout).strip().splitlines()
            note = tail[-1][:80] if tail else ""
            out.append(f"  {'✓' if ok else '✗'} {d} [{occ}] {note}")
            log.write_text("\n".join(out))
            time.sleep(1)
    out.append(f"\nDONE: {total_ok} rendered, {total_fail} failed")
    log.write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
