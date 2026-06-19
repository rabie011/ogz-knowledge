#!/usr/bin/env python3
"""B063 consumer (Rule #6): the RABIE provisional lens pass in data/lens_review.json is a WRITE;
this is its reader. It surfaces the flagged-for-regen worklist that B065 (lens/angle regen) consumes,
and verifies the review against the live lenses so a stale flag never silently mis-fires.

Commands:
  flagged    — print occasions rated <3 (the regen worklist), one per line. Empty = nothing to regen.
  summary    — print the full pass: rating + flag + why, sorted worst-first.
  verify     — REFUSE-guard (Rule #8): exit non-zero unless every reviewed occasion exists in
               occasion_facts.json with a non-empty sector_lenses block, and every flag is a real <3.

The flag worklist is winner-independent structured data — a regen step does:
  for occ in lens_review.flagged(): build_sector_lenses.py --only <occ>   (the SYSTEM regenerates; Rule #12)
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
REVIEW = BASE / "data" / "lens_review.json"
FACTS = BASE / "data" / "occasion_facts.json"


def load_review():
    return json.loads(REVIEW.read_text())


def flagged():
    """Occasions rated < 3 (flagged True) — the regen worklist B065 consumes."""
    rv = load_review()["reviews"]
    return [occ for occ, r in rv.items() if r.get("flag") or r.get("rating", 3) < 3]


def verify():
    """Rule #8: refuse on any drift between the review and the live lenses. Returns list of errors."""
    rv = load_review()["reviews"]
    facts = json.loads(FACTS.read_text()) if FACTS.exists() else {}
    return _verify_against(rv, facts)


def _verify_against(rv, facts):
    """Pure core of verify() — injectable so the refuse-guard is testable with crafted drift."""
    errs = []
    for occ, r in rv.items():
        if occ not in facts:
            errs.append(f"reviewed occasion '{occ}' is absent from occasion_facts.json")
            continue
        if not (facts[occ].get("sector_lenses") or {}):
            errs.append(f"reviewed occasion '{occ}' has no sector_lenses to judge")
        rating = r.get("rating")
        if not isinstance(rating, int) or not (0 <= rating <= 5):
            errs.append(f"'{occ}' has invalid rating {rating!r}")
        # flag must agree with rating<3 (no silent rubber-stamp / mismatch)
        if bool(r.get("flag")) != (isinstance(rating, int) and rating < 3):
            errs.append(f"'{occ}' flag={r.get('flag')} disagrees with rating={rating} (<3 must flag)")
    return errs


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    if cmd == "flagged":
        for occ in flagged():
            print(occ)
    elif cmd == "verify":
        errs = verify()
        if errs:
            print("❌ lens_review verify FAILED:")
            for e in errs:
                print("  -", e)
            sys.exit(1)
        rv = load_review()["reviews"]
        print(f"✅ lens_review verified: {len(rv)} occasions, {len(flagged())} flagged for regen")
    else:
        rv = load_review()["reviews"]
        for occ, r in sorted(rv.items(), key=lambda x: x[1].get("rating", 3)):
            mark = "🚩" if (r.get("flag") or r.get("rating", 3) < 3) else "  "
            print(f"{mark} {r.get('rating')}/5  {occ}")
            print(f"       {r.get('why','')}")


if __name__ == "__main__":
    main()
