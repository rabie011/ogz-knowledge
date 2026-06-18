#!/usr/bin/env python3
"""taste_clause_ab.py — the EYES-TEST for the founder-taste→pen wire (June 18, RABIE-ordered).

The 3-shift thread: founder_taste.json was a DEAD READ in the producing pen (render_client_slot);
last shift spliced it into sys_p and proved it CONNECTED (test_wires). But connected ≠ better
(Rule #13). This harness proves whether his taste law actually SHARPENS the pen, by holding the
ANGLE fixed and rendering the SAME real pilot slot two ways:
    BEFORE = OGZ_TASTE_OFF=1  → pen runs without his law
    AFTER  = (default)        → pen runs with his kills/rewards woven in
The only variable is the clause. Output is a before/after pair for Mohamed's thumb — never a
quality CLAIM, only the artifact his eye judges. gpt-only (Anthropic dry); ~1 angle + a few
caption passes per arm — bounded, cheap (money discipline).

Usage: python3 scripts/taste_clause_ab.py --handle eatjurisha --date 2026-07-01
"""
import argparse, json, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_client_slot as R

BASE = R.BASE


def render_arm(c, slot, angle, taste_off: bool) -> list:
    if taste_off:
        os.environ["OGZ_TASTE_OFF"] = "1"
    else:
        os.environ.pop("OGZ_TASTE_OFF", None)
    try:
        return R.render_captions(c, slot, angle)
    finally:
        os.environ.pop("OGZ_TASTE_OFF", None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default="eatjurisha")
    ap.add_argument("--date", default="2026-07-01")
    a = ap.parse_args()

    ym = json.loads((BASE / "clients" / a.handle / "year_map.json").read_text())
    slot = next((s for mm in ym["months"].values() for s in mm if s["date"] == a.date), None)
    if not slot:
        sys.exit(f"no slot {a.date} in {a.handle} year map")

    c = R.load_client(a.handle)
    if c.get("gold_entries"):
        c["exemplars"] = R.rank_gold_exemplars(c["gold_entries"], slot.get("occasion"), c["exemplars"])
    brain = R.route_brain(slot, alt=int(a.date.replace("-", "")))
    # ONE angle, shared by both arms — isolates the taste-clause as the only variable.
    angle = R.make_angle(c, slot, ym["sector"], brain=brain)

    before = render_arm(c, slot, angle, taste_off=True)
    after = render_arm(c, slot, angle, taste_off=False)

    out = {"handle": a.handle, "date": a.date, "brain": brain,
           "angle": angle.get("scene_ar", ""),
           "before_no_taste_law": before, "after_with_taste_law": after}
    dest = BASE / "data" / f"taste_ab_{a.handle}_{a.date}.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    print(f"ANGLE (fixed): {angle.get('scene_ar','')[:130]}\n")
    print("── BEFORE (no taste law) ──")
    for i, x in enumerate(before, 1):
        print(f"  {i}. {x[:140]}")
    print("\n── AFTER (taste law ON) ──")
    for i, x in enumerate(after, 1):
        print(f"  {i}. {x[:140]}")
    print(f"\n→ {dest}")


if __name__ == "__main__":
    main()
