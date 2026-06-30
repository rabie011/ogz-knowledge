#!/usr/bin/env python3
"""GOAL-RATIO WATCHDOG (B001, June 12 — pyramid Growth Law).
Content mix deviating >20% from the client's DECLARED goal ratio = flag BEFORE
anything reaches Mohamed or the client. The declared ratio is law (confirmed
beats inferred — no silent adoption, ever); undeclared = the check politely
waits (and says so — no fake green).

Usage: python3 scripts/goal_ratio_check.py [--handle X]
"""
import argparse, glob, json, re, sys
from pathlib import Path
import fingerprint_status

BASE = Path(__file__).parent.parent
OFFER = re.compile(r"عرض|خصم|كود|اطلب|الجمعة البيضاء|deal|off|discount|order now", re.I)
TOLERANCE = 0.20


def mix(handle: str) -> tuple[int, int]:
    sales = brand = 0
    for f in glob.glob(str(BASE / "clients" / handle / "posts" / "*.json")):
        if "__pick_" in f:
            continue
        try:
            c = json.loads(open(f).read())
        except Exception:
            continue
        caps = c.get("captions") or []
        if not caps:
            continue
        if OFFER.search(caps[0]):
            sales += 1
        else:
            brand += 1
    return sales, brand


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    clients = ([a.handle] if a.handle else
               fingerprint_status.real_clients())
    flags = 0
    for h in clients:
        g = json.loads((BASE / "clients" / h / "profile/goals.json").read_text())
        declared = g.get("goal_ratio")  # e.g. "60_sales_40_brand" or {"sales": 0.6}
        s, b = mix(h)
        total = s + b
        actual = s / total if total else 0
        if not declared:
            print(f"  ⏸ {h}: ratio UNDECLARED (actual mix: {actual:.0%} sales of {total}) — check waits for the client's word")
            continue
        want = declared.get("sales") if isinstance(declared, dict) else None
        if want is None:
            m = re.search(r"(\d+)", str(declared))
            want = int(m.group(1)) / 100 if m else None
        if want is None:
            print(f"  ⚠ {h}: declared ratio unparseable: {declared}")
            continue
        dev = abs(actual - want)
        ok = dev <= TOLERANCE
        flags += not ok
        print(f"  {'✅' if ok else '🔴'} {h}: declared {want:.0%} sales · actual {actual:.0%} ({total} posts) · deviation {dev:.0%}")
        if not ok:
            print(f"     → FLAG: raise a PROPOSED-amendment card to the client — never silently adopt")
    sys.exit(1 if flags else 0)


if __name__ == "__main__":
    main()
