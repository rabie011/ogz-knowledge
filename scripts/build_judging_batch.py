#!/usr/bin/env python3
"""D3 JUDGING BATCH BUILDER (June 12 — RABIE's slice, step 1).
Picks the 20 strongest judging candidates so Mohamed's fal tap → render → portal
is ONE command. Selection law: complete post-units only (idea + shoot-card +
captions), NEVER order_tail-tagged, clients balanced (myfitness throttled out),
brains and occasions spread. Image prompts STAGED at zero cost (no key = prompt
written to card, money law).

Usage: python3 scripts/build_judging_batch.py            # build + stage
Fire-day (after Mohamed's fal one-liner):
  python3 scripts/render_image.py --batch /tmp/judging_batch_paths.txt
"""
import collections, json, subprocess, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from visual_gate_checklist import human_rejected   # Rule #6: read the visual-gate verdict
CLIENTS = ["albaik", "eatjurisha"]          # myfitness throttled: EXPIRED truth
PER_CLIENT = 10
BATCH = 20


def candidates(handle: str) -> list[dict]:
    out = []
    for f in sorted((BASE / "clients" / handle / "posts").glob("*.json")):
        if any(x in f.name for x in ("__ctatest", "__recovery", "__gold")):
            continue
        try:
            c = json.loads(f.read_text())
        except Exception:
            continue
        if (c.get("order_tail") or c.get("very_normal") or c.get("truth_violation")
                or not c.get("captions")):
            continue
        if human_rejected(c):
            continue                          # Rule #13: a human-rejected visual never re-reaches Mohamed
        idea = (c.get("idea") or {}).get("scene_ar", "")
        shots = (c.get("visual") or {}).get("phone_shoot_card") or []
        if not idea or not shots:
            continue                          # post-unit completeness law
        # occasion lives in the FILENAME (card body often lacks it): DATE__OCCASION__...
        parts = f.stem.split("__")
        occ = parts[1] if len(parts) >= 2 and not parts[1].startswith(("v", "pick", "like")) else "evergreen"
        out.append({"path": str(f.relative_to(BASE)), "client": handle,
                     "brain": c.get("brain", "?"), "occasion": occ,
                     "date": parts[0]})
    return out


def spread_pick(cands: list[dict], n: int) -> list[dict]:
    """Round-robin across brains, then occasions — maximum diversity per client."""
    by_brain = collections.defaultdict(list)
    for c in cands:
        by_brain[c["brain"]].append(c)
    picked, seen_occ = [], collections.Counter()
    brains = sorted(by_brain, key=lambda b: -len(by_brain[b]))
    while len(picked) < n and any(by_brain.values()):
        for b in brains:
            if len(picked) >= n:
                break
            pool = sorted(by_brain[b], key=lambda c: seen_occ[c["occasion"]])
            if pool:
                c = pool[0]
                by_brain[b].remove(c)
                picked.append(c)
                seen_occ[c["occasion"]] += 1
    return picked


def main():
    batch = []
    for h in CLIENTS:
        cs = candidates(h)
        pick = spread_pick(cs, PER_CLIENT)
        print(f"  {h}: {len(cs)} candidates → {len(pick)} picked "
              f"({len({p['brain'] for p in pick})} brains, {len({p['occasion'] for p in pick})} occasions)")
        batch += pick
    batch = batch[:BATCH]
    mf = BASE / "data/judging_batch.json"
    mf.write_text(json.dumps({"built": __import__("datetime").date.today().isoformat(), "status": "STAGED — awaiting fal key",
                                "fire_command": "python3 scripts/render_image.py --batch /tmp/judging_batch_paths.txt",
                                "cards": batch}, ensure_ascii=False, indent=1))
    paths = "\n".join(str(BASE / c["path"]) for c in batch)
    Path("/tmp/judging_batch_paths.txt").write_text(paths + "\n")
    # stage image prompts NOW (no key = zero cost, prompt written into each card)
    r = subprocess.run(["python3", str(BASE / "scripts/render_image.py"),
                        "--batch", "/tmp/judging_batch_paths.txt"], capture_output=True, text=True)
    staged = r.stdout.count("prompt staged")
    print(f"  manifest: {len(batch)} cards → data/judging_batch.json · {staged} prompts staged (zero spend)")


if __name__ == "__main__":
    main()
