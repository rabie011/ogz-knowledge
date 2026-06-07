#!/usr/bin/env python3
"""
calibrate_judge.py — Does the gpt-4o judge agree with Mohamed's taste?

Reads:
  - review_data.json     (each caption has a HIDDEN judge_score)
  - review_results.json  (Mohamed's blind ratings: excellent/good/weak/fail)

Computes:
  - agreement on the binary pass call (Mohamed good+ vs judge >= 6.5)
  - rank correlation (does higher judge score → better human rating?)
  - the disagreements (where to look — judge says good, human says weak, or vice versa)

If agreement is high → trust the judge for all future auto-testing.
If low → the judge prompt needs recalibration to Mohamed's eye.

Usage:
    python3 scripts/calibrate_judge.py
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "logs" / "system" / "review_data.json"
RESULTS = REPO / "logs" / "system" / "review_results.json"

# Map human rating → numeric (1-4) and a "pass" boolean
RATING_NUM = {"excellent": 4, "good": 3, "weak": 2, "fail": 1}
RATING_PASS = {"excellent": True, "good": True, "weak": False, "fail": False}
JUDGE_PASS_THRESHOLD = 6.5  # judge >= this = "pass"


def main():
    if not RESULTS.exists():
        print("No review_results.json yet — Mohamed needs to rate on /review first.")
        return

    data = {d["id"]: d for d in json.loads(DATA.read_text())}
    results = json.loads(RESULTS.read_text())

    pairs = []  # (id, brand, occasion, human_rating, judge_score)
    for item_id, r in results.items():
        rating = r.get("rating")
        d = data.get(int(item_id))
        if not d or not rating or d.get("judge_score") is None:
            continue
        pairs.append({
            "id": int(item_id), "brand": d["brand"], "occasion": d["occasion"],
            "human": rating, "judge": d["judge_score"],
            "human_pass": RATING_PASS.get(rating, False),
            "judge_pass": d["judge_score"] >= JUDGE_PASS_THRESHOLD,
        })

    if not pairs:
        print("No rated captions with judge scores found.")
        return

    n = len(pairs)
    agree_pass = sum(1 for p in pairs if p["human_pass"] == p["judge_pass"])

    # Rank correlation (Spearman, simple implementation)
    def rank(values):
        srt = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0] * len(values)
        for r, i in enumerate(srt):
            ranks[i] = r
        return ranks
    human_nums = [RATING_NUM[p["human"]] for p in pairs]
    judge_nums = [p["judge"] for p in pairs]
    hr, jr = rank(human_nums), rank(judge_nums)
    d2 = sum((hr[i] - jr[i]) ** 2 for i in range(n))
    spearman = 1 - (6 * d2) / (n * (n**2 - 1)) if n > 1 else 0

    print(f"{'='*60}")
    print(f"  JUDGE CALIBRATION — does gpt-4o judge match Mohamed?")
    print(f"{'='*60}")
    print(f"  Rated pairs:        {n}")
    print(f"  Pass-call agreement: {agree_pass}/{n} ({agree_pass/n*100:.0f}%)")
    print(f"    (Mohamed good+ vs judge >= {JUDGE_PASS_THRESHOLD})")
    print(f"  Rank correlation:   {spearman:+.2f}  (1.0 = perfect, 0 = random)")
    print()

    verdict = ("✅ TRUST THE JUDGE — high agreement, use it for auto-testing"
               if agree_pass/n >= 0.75 and spearman >= 0.4
               else "⚠️  RECALIBRATE — judge doesn't match Mohamed's eye well enough")
    print(f"  {verdict}")
    print()

    # Disagreements — the interesting cases
    disagree = [p for p in pairs if p["human_pass"] != p["judge_pass"]]
    if disagree:
        print(f"  Disagreements ({len(disagree)}):")
        for p in disagree:
            who = "judge HIGH, human LOW" if p["judge_pass"] else "judge LOW, human HIGH"
            print(f"    @{p['brand']:<14} {p['occasion']:<13} human={p['human']:<10} judge={p['judge']}  [{who}]")

    # Per-rating: what judge score does each human rating get?
    print(f"\n  Avg judge score by human rating:")
    for rating in ["excellent", "good", "weak", "fail"]:
        scores = [p["judge"] for p in pairs if p["human"] == rating]
        if scores:
            print(f"    {rating:<11} → judge avg {sum(scores)/len(scores):.1f}  (n={len(scores)})")

    out = REPO / "logs" / "system" / "judge_calibration.json"
    out.write_text(json.dumps({
        "pairs": n, "pass_agreement": round(agree_pass/n, 2),
        "spearman": round(spearman, 2), "trust": agree_pass/n >= 0.75 and spearman >= 0.4,
    }, ensure_ascii=False, indent=2))
    print(f"\n  Saved → {out}")


if __name__ == "__main__":
    main()
