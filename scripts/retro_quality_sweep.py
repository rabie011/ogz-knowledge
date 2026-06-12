#!/usr/bin/env python3
"""RETRO QUALITY SWEEP (June 12 — RABIE's midday direction).
The day's new armor (CTA gate, very_normal, worn-grams, truth guards) arrived
AFTER most of the 1,000+ cards were rendered. This sweep runs every detector
over the FULL corpus and surfaces THE NUMBER: how many cards would today's
armor have caught? That number is Mohamed's calibration evidence.
Read-only on captions; writes one report. TAGS stay as they are.

Usage: python3 scripts/retro_quality_sweep.py
"""
import collections, json, re, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
from truth_guards import apply_guards


def worn_endemic(handle: str, cards: list[dict]) -> tuple[set, int]:
    """Grams appearing across >15% of the client's full corpus = endemic pen tics."""
    grams = collections.Counter()
    per_card_grams = []
    for c in cards:
        g = set()
        for cap in c.get("captions") or []:
            w = re.sub(r"[^؀-ۿ\s]", " ", cap).split()
            g |= {" ".join(w[i:i + 3]) for i in range(len(w) - 2)}
        per_card_grams.append(g)
        for x in g:
            grams[x] += 1
    n = max(len(cards), 1)
    endemic = {g for g, c in grams.items() if c / n > 0.15 and c >= 10}
    carriers = sum(1 for g in per_card_grams if g & endemic)
    return endemic, carriers


def main():
    report = {}
    for cdir in sorted((BASE / "clients").iterdir()):
        posts = cdir / "posts"
        if not posts.is_dir():
            continue
        cards = []
        for f in sorted(posts.glob("*.json")):
            try:
                c = json.loads(f.read_text())
            except Exception:
                continue
            if c.get("captions"):
                cards.append(c)
        if not cards:
            continue
        total = len(cards)
        tails = sum(1 for c in cards if c.get("order_tail"))
        vn = sum(1 for c in cards if c.get("very_normal"))
        endemic, worn_carriers = worn_endemic(cdir.name, cards)
        guard_kills = 0
        for c in cards:
            surv, kills = apply_guards(list(c["captions"]), "", {"occasion": c.get("occasion")})
            if kills and len(kills) == len(c["captions"]):
                guard_kills += 1
        caught = len({i for i, c in enumerate(cards)
                       if c.get("order_tail") or c.get("very_normal")})
        report[cdir.name] = {
            "cards": total, "order_tail": tails, "very_normal": vn,
            "endemic_grams": sorted(endemic)[:6], "worn_carriers": worn_carriers,
            "worn_pct": round(100 * worn_carriers / total),
            "all_options_guard_killed": guard_kills,
            "armor_caught_pct": round(100 * (tails + vn) / total),
        }
        r = report[cdir.name]
        print(f"── {cdir.name}: {total} cards · tails {tails} ({round(100*tails/total)}%) · "
              f"very_normal {vn} · worn-carriers {worn_carriers} ({r['worn_pct']}%) · "
              f"full-guard-kills {guard_kills}")
        if endemic:
            print(f"   endemic tics: {' | '.join(sorted(endemic)[:4])}")
    out = BASE / "data/retro_sweep.json"
    out.write_text(json.dumps({"swept": __import__("datetime").date.today().isoformat(),
                                 "report": report}, ensure_ascii=False, indent=1))
    print(f"\n→ data/retro_sweep.json (the calibration number for Mohamed's judging)")


if __name__ == "__main__":
    main()
