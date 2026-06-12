#!/usr/bin/env python3
"""BATCH SLOT RENDERER (B066, June 12 — RABIE's pick #3).
One command renders any slice of a client's year map through the FULL armored
pipeline (render_client_slot), rate-limit-safe, resumable, honest about failures.
Marks each slot's status in year_map.json (planned → rendered_<suffix>) so reruns
skip done work — the spine regen becomes incremental, never a 14-hour gamble.

Usage:
  python3 scripts/render_slots_batch.py --handle albaik --type evergreen --suffix __v5 --limit 10
  python3 scripts/render_slots_batch.py --handle eatjurisha --anchors-only --suffix __v5
"""
import argparse, json, subprocess, sys, time
from pathlib import Path

BASE = Path(__file__).parent.parent
PAUSE_S = 4          # between renders — OpenAI 30k TPM discipline
RETRY_PAUSE_S = 20   # one retry after a breath


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--type", default=None, help="slot type filter (evergreen/occasion/ramadan_evergreen)")
    ap.add_argument("--anchors-only", action="store_true")
    ap.add_argument("--suffix", default="__v5")
    ap.add_argument("--brain", default="auto")
    ap.add_argument("--limit", type=int, default=0, help="0 = all matching")
    a = ap.parse_args()

    ymf = BASE / "clients" / a.handle / "year_map.json"
    ymap = json.loads(ymf.read_text())
    done_status = f"rendered{a.suffix}"
    todo = []
    for mm in ymap["months"].values():
        for s in mm:
            if s.get("status") == done_status:
                continue
            if a.anchors_only and not s.get("anchor"):
                continue
            if a.type and s.get("type") != a.type:
                continue
            todo.append(s)
    if a.limit:
        todo = todo[: a.limit]
    print(f"{a.handle}: {len(todo)} slots to render (suffix {a.suffix}, brain {a.brain})")

    ok = failed = 0
    PICK_BRAINS = {"saudi_national_day": ["heritage", "firaasa", "authenticity"],
                    "saudi_founding_day": ["heritage", "firaasa", "metaphor"],
                    "ramadan": ["firaasa", "authenticity", "metaphor"],
                    "eid_al_fitr": ["authenticity", "firaasa", "heritage"],
                    "eid_al_adha": ["firaasa", "authenticity", "paradox"],
                    "white_friday": ["paradox", "metaphor", "firaasa"]}
    for i, s in enumerate(todo, 1):
        # B179 — THE MAJORS LAW MECHANIZED: major day-of slots render 3 brain-variants
        # and push the pick-card to Mohamed's portal automatically. Never single-shot.
        if s.get("major") and s.get("beat") == "day_of":
            brains = PICK_BRAINS.get(s.get("occasion"), ["firaasa", "authenticity", "metaphor"])
            pick_ok = 0
            for br in brains:
                cmd = ["python3", str(BASE / "scripts/render_client_slot.py"),
                       "--handle", a.handle, "--date", s["date"], "--brain", br,
                       "--suffix", f"__pick_{br}"]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                pick_ok += (r.returncode == 0)
                time.sleep(PAUSE_S)
            if pick_ok >= 2:
                slot_slug = f"{s['date']}__{s.get('occasion')}"
                subprocess.run(["python3", str(BASE / "scripts/build_pick_item.py"),
                                "--handle", a.handle, "--slot", slot_slug,
                                "--title", f"اختر بوست {a.handle} × {s.get('occasion')}"],
                               capture_output=True, text=True, timeout=60)
                s["status"] = f"pickset{a.suffix}"
                ok += 1
                print(f"  [{i}/{len(todo)}] 🎯 {s['date']} {s.get('occasion')} — {pick_ok} variants + portal card")
            else:
                failed += 1
                print(f"  [{i}/{len(todo)}] ✗ {s['date']} pick-set failed ({pick_ok}/3)")
            ymf.write_text(json.dumps(ymap, ensure_ascii=False, indent=2))
            continue
        cmd = ["python3", str(BASE / "scripts/render_client_slot.py"),
               "--handle", a.handle, "--date", s["date"], "--brain", a.brain, "--suffix", a.suffix]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0:
            time.sleep(RETRY_PAUSE_S)
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode == 0:
            s["status"] = done_status
            ok += 1
            print(f"  [{i}/{len(todo)}] ✓ {s['date']} {s.get('occasion') or s.get('type')}")
        else:
            failed += 1
            err = (r.stderr or r.stdout).strip().splitlines()
            print(f"  [{i}/{len(todo)}] ✗ {s['date']} — {err[-1][:80] if err else 'unknown'}")
        ymf.write_text(json.dumps(ymap, ensure_ascii=False, indent=2))  # checkpoint each slot
        time.sleep(PAUSE_S)
    print(f"\nBATCH DONE: {ok} ok, {failed} failed — year_map statuses checkpointed")
    sys.exit(1 if failed and not ok else 0)


if __name__ == "__main__":
    main()
