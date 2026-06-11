#!/usr/bin/env python3
"""FINGERPRINT STATUS (pyramid GAP-08, June 11) — the inference quarantine view.
Voice and identity rendered side-by-side per client so statistics can never
impersonate completeness: voice can be GREEN from data; identity is RED until
the CLIENT speaks. The albaik lesson made visible, permanently.

Usage: python3 scripts/fingerprint_status.py            # all clients
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
G, Y, R = "🟢", "🟡", "🔴"


def status(handle: str) -> dict:
    pdir = BASE / "clients" / handle / "profile"
    fp = json.loads((pdir / "fingerprint.json").read_text())
    tp = json.loads((pdir / "truth_pack.json").read_text())
    rl = json.loads((pdir / "red_lines.json").read_text())
    go = json.loads((pdir / "goals.json").read_text())
    st = json.loads((pdir / "state.json").read_text())
    v = fp["l2_voice"]
    voice = (G if v.get("love_lines") else (Y if v.get("dialect") else R),
             "client-confirmed" if v.get("love_lines") else
             ("stats only — describes the past, not a contract" if v.get("dialect") else
              "no voice — needs birth (newborn) or extraction"))
    l1 = fp["l1_strategy"]
    identity = (G if l1.get("who_speaks") else R,
                "confirmed" if l1.get("who_speaks") else "client-only: who-speaks/USP/positioning all empty")
    truth = (G if tp["confirmed"] else (Y if tp["product_candidates"] else R),
             f"{len(tp['confirmed'])} confirmed / {len(tp['product_candidates'])} candidates / {len(tp['channels'])} channels")
    red = (G if rl["lines"] else R,
           f"{len(rl['lines'])} lines — strictest defaults govern" if not rl["lines"] else f"{len(rl['lines'])} lines")
    goals = (G if go["answered"] >= 4 else (Y if go["answered"] else R), f"{go['answered']}/{go['of']} answered")
    return {"handle": handle, "state": st["state"], "silent_days": st.get("silent_days"),
            "rows": [("VOICE", *voice), ("IDENTITY", *identity), ("TRUTH", *truth),
                      ("RED LINES", *red), ("GOALS", *goals)]}


def main():
    clients = sorted(d.name for d in (BASE / "clients").iterdir() if (d / "profile").is_dir())
    for h in clients:
        s = status(h)
        print(f"\n═══ {h} — {s['state']}" + (f" (silent {s['silent_days']}d)" if s.get("silent_days") else ""))
        for name, light, note in s["rows"]:
            print(f"  {light} {name:10} {note}")
    print("\nLAW: a profile is PRODUCTION-READY only when no row is 🔴. "
          "Stats may light VOICE yellow — never green, never identity.")


if __name__ == "__main__":
    main()
