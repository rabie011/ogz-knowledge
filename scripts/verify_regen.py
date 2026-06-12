#!/usr/bin/env python3
"""REGEN VERIFIER (B220, June 12 — RABIE's pick). The grinder runs all night;
this audits what it actually built — counts, parse health, caption presence,
version mix, order-tail fraction, EXPIRED stamps, year-map coverage. Numbers
never feelings; anomalies exit 1.

Usage: python3 scripts/verify_regen.py
"""
import collections, json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
DORMANT = {"myfitness.sa"}                # EXPIRED stamps legitimate ONLY here


def audit(handle: str) -> dict:
    pdir = BASE / "clients" / handle / "posts"
    stats = {"files": 0, "parse_fail": 0, "no_captions": 0, "versions": collections.Counter(),
             "order_tail": 0, "expired_stamped": 0, "picksets": 0, "dates": set()}
    for f in sorted(pdir.glob("*.json")):
        stats["files"] += 1
        try:
            c = json.loads(f.read_text())
        except Exception:
            stats["parse_fail"] += 1
            continue
        parts = f.stem.split("__")
        suffix = parts[-1] if len(parts) >= 3 else "v1"
        stats["versions"][suffix if suffix.startswith(("v", "pick", "gold")) else "v1"] += 1
        if suffix.startswith("pick"):
            stats["picksets"] += 1
        if not c.get("captions"):
            stats["no_captions"] += 1
            if str((c.get("provenance") or {}).get("rendered", "")) >= __import__("datetime").date.today().isoformat():
                stats["fresh_captionless"] = stats.get("fresh_captionless", 0) + 1
        if c.get("order_tail"):
            stats["order_tail"] += 1
        if "EXPIRED" in json.dumps(c, ensure_ascii=False):
            stats["expired_stamped"] += 1
        stats["dates"].add(parts[0])
    ym = BASE / "clients" / handle / "year_map.json"
    slots = 0
    if ym.exists():
        slots = json.loads(ym.read_text()).get("total_slots", 0)
    stats["year_slots"] = slots
    stats["dates_covered"] = len(stats["dates"])
    del stats["dates"]
    return stats


def main():
    problems = []
    for h in sorted(d.name for d in (BASE / "clients").iterdir() if (d / "posts").is_dir()):
        s = audit(h)
        cov = f"{s['dates_covered']}/{s['year_slots']}" if s["year_slots"] else f"{s['dates_covered']} dates"
        print(f"── {h}: {s['files']} files · {s['parse_fail']} parse-fail · {s['no_captions']} captionless "
              f"· tails {s['order_tail']} · EXPIRED {s['expired_stamped']} · coverage {cov}")
        print(f"   versions: {dict(s['versions'].most_common(6))}")
        if s["parse_fail"]:
            problems.append(f"{h}: {s['parse_fail']} unparseable cards")
        if s.get("fresh_captionless"):
            problems.append(f"{h}: {s['fresh_captionless']} FRESH captionless renders — guards killing all options again")
        elif s["no_captions"]:
            print(f"   ⚠ {s['no_captions']} historical captionless (pre-fallback guard kills, June 11) — pickers skip them")
        if h not in DORMANT and s["expired_stamped"]:
            problems.append(f"{h}: {s['expired_stamped']} EXPIRED stamps on a NON-dormant client")
        if h in DORMANT:
            # throttle breach = UNCOMMITTED new cards, not historical count (git is the witness)
            import subprocess
            dirty = subprocess.run(["git", "-C", str(BASE), "status", "--short",
                                     f"clients/{h}/posts/"], capture_output=True, text=True).stdout.strip()
            if dirty:
                problems.append(f"{h}: THROTTLED client has uncommitted new cards — money law breach:\n{dirty[:200]}")
    print()
    if problems:
        for p in problems:
            print(f"🔴 {p}")
        sys.exit(1)
    print("🟢 REGEN VERIFIED — all invariants hold")


if __name__ == "__main__":
    main()
