#!/usr/bin/env python3
"""Regenerate a ZERO-ISSUE, occasion-aligned 20 from the REBUILT clean year_maps (2026-06-14,
after the orchestra + RABIE zoom-out). Strategy: daily-neutral-weighted (occasion-free by
construction now) with VARIED theme-cores to beat over-concentration, plus a few real-occasion
day_of slots (audited — kept only if they pass all 3 doors). Renders __v7, then post_audit must
read ZERO before anything stages. Never creates blind: the audit is the gate (Mohamed's "don't
create before testing" → here it's create-then-prove-zero-before-ship)."""
import json, glob, subprocess, sys, time
from pathlib import Path
from collections import defaultdict

B = Path(__file__).parent.parent
SECTORS = {"eatjurisha": "f_and_b", "albaik": "f_and_b", "myfitness.sa": "healthcare_wellness"}
# per client: how many daily + which occasion day_of slots to attempt
DAILY_PER = {"eatjurisha": 7, "albaik": 7, "myfitness.sa": 6}  # +3 occasion = 23 candidates, keep 20 clean
OCC_ATTEMPT = {  # one occasion per client for variety; audited, dropped if it fails
    "eatjurisha": ["saudi_national_day"],
    "albaik": ["ramadan"],
    "myfitness.sa": ["saudi_founding_day"],
}


def pick_daily(handle, n):
    """n daily slots with DISTINCT theme-cores (occasion-field tag), spread across months."""
    ym = json.loads((B / "clients" / handle / "year_map.json").read_text())
    by_tag = defaultdict(list)
    for mm in ym["months"].values():
        for s in mm:
            if s.get("type") in ("daily", "evergreen", "ramadan_evergreen") and not s.get("occasion"):
                tag = (s.get("angle_theme") or "").split(":")[0][:20]
                by_tag[tag].append(s)
    picked, tags = [], list(by_tag)
    i = 0
    while len(picked) < n and any(by_tag.values()):
        t = tags[i % len(tags)]
        i += 1
        if by_tag[t]:
            picked.append(by_tag[t].pop(len(by_tag[t]) // 2))  # mid-list = spread
    return [(s["date"], "daily") for s in picked[:n]]


def pick_occasions(handle, slugs):
    ym = json.loads((B / "clients" / handle / "year_map.json").read_text())
    out = []
    for slug in slugs:
        cands = [s for mm in ym["months"].values() for s in mm
                 if s.get("occasion") == slug and s.get("beat") == "day_of"]
        if not cands:
            cands = [s for mm in ym["months"].values() for s in mm if s.get("occasion") == slug]
        if cands:
            out.append((cands[0]["date"], slug))
    return out


def main():
    plan = []
    for h in SECTORS:
        plan += [(h, d, kind) for d, kind in pick_daily(h, DAILY_PER[h])]
        plan += [(h, d, kind) for d, kind in pick_occasions(h, OCC_ATTEMPT.get(h, []))]
    log = B / "data/gen_aligned20.log"
    out = []
    for h, d, kind in plan:
        r = subprocess.run(["python3", str(B / "scripts/render_client_slot.py"),
                            "--handle", h, "--date", d, "--brain", "auto", "--suffix", "__v7"],
                           capture_output=True, text=True)
        fs = glob.glob(str(B / f"clients/{h}/posts/{d}__*__v7.json"))
        ncap = len(json.loads(Path(fs[0]).read_text()).get("captions") or []) if fs else 0
        out.append(f"{'✓' if r.returncode == 0 and ncap else '✗'} {h} {d} [{kind}] caps={ncap}")
        log.write_text("\n".join(out))
        time.sleep(1)
    out.append(f"\nrendered {len(plan)} candidates")
    log.write_text("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
