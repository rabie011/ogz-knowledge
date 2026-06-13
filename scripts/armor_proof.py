#!/usr/bin/env python3
"""B131 — ARMOR PROOF: today's full armor stack over our own past output.

RABIE's zoom-out hammer (04:45): «you tested armor 38 times on zero posts». This
runs the CURRENT guards over every caption the system itself rendered (the client
post cards, v2→v6 eras) and produces the proof numbers:
  - kill rate by VERSION ERA  → must FALL if the system actually improved
  - kills by GUARD            → which laws carry the weight
  - kills by CLIENT           → where the bleeding was
Honest caveats baked in: old captions predate many bans (worn list, dialect, سدر,
taste kills) — a high early kill-rate is the POINT, not an alarm. Zero-LLM.

Output: data/armor_proof.json + printed table (feeds the morning brief + his /rate20).
"""
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE / "scripts"))
from caption_filter import check
from truth_guards import apply_guards
from render_client_slot import taste_guard


def main():
    by_era = defaultdict(lambda: {"captions": 0, "killed": 0})
    by_guard = Counter()
    by_client = defaultdict(lambda: {"captions": 0, "killed": 0})
    examples = defaultdict(list)
    kill_patterns = {}

    files = sorted(glob.glob(str(BASE / "clients/*/posts/*.json")))
    for f in files:
        m = re.search(r"__v(\d+)", Path(f).name)
        era = f"v{m.group(1)}" if m else "v?"
        handle = Path(f).parts[-3]
        if handle not in kill_patterns:
            tf = BASE / "clients" / handle / "profile" / "taste.json"
            kill_patterns[handle] = (json.loads(tf.read_text()).get("kill_patterns", [])
                                     if tf.exists() else [])
        try:
            d = json.loads(Path(f).read_text())
        except Exception:
            continue
        caps = d.get("captions") or []
        slot = d.get("slot") if isinstance(d.get("slot"), dict) else {}
        corpus = ""  # corpus-blind run: noun-grounding (G3) is skipped to avoid
        # false invented-name kills without each brand's real corpus loaded
        for cap in caps:
            if not isinstance(cap, str) or len(cap.strip()) < 6:
                continue
            by_era[era]["captions"] += 1
            by_client[handle]["captions"] += 1
            reasons = []
            ok, rs = check(cap)
            if not ok:
                reasons += rs
            _, guard_kills = apply_guards([cap], cap,  # corpus=cap → G3 self-grounded (skip)
                                          {"occasion": (slot.get("occasion") or "")})
            reasons += [k["guard"] for k in guard_kills]
            _, taste_kills = taste_guard([cap], kill_patterns[handle])
            reasons += [f"taste:{h}" for _, h in taste_kills]
            if reasons:
                by_era[era]["killed"] += 1
                by_client[handle]["killed"] += 1
                primary = reasons[0].split(":")[0] if ":" in reasons[0] else reasons[0]
                by_guard[primary] += 1
                if len(examples[primary]) < 3:
                    examples[primary].append(cap[:70])

    out = {"generated": datetime.now().isoformat(timespec="seconds"),
           "doc": "today's FULL armor over the system's own past output — high early-era "
                  "kill rates are expected (captions predate the bans); the curve matters",
           "by_era": {k: {**v, "kill_pct": round(v["killed"] / v["captions"] * 100, 1) if v["captions"] else 0}
                      for k, v in sorted(by_era.items())},
           "by_guard": dict(by_guard.most_common()),
           "by_client": {k: {**v, "kill_pct": round(v["killed"] / v["captions"] * 100, 1) if v["captions"] else 0}
                         for k, v in by_client.items()},
           "kill_examples": dict(examples)}
    (BASE / "data/armor_proof.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))

    total = sum(v["captions"] for v in by_era.values())
    killed = sum(v["killed"] for v in by_era.values())
    print(f"ARMOR PROOF — {total} captions from {len(files)} cards:")
    print(f"  overall: {killed}/{total} would be killed today ({round(killed/total*100,1)}%)")
    print("  by era (the curve):")
    for era, v in sorted(out["by_era"].items()):
        print(f"    {era}: {v['kill_pct']}% killed ({v['killed']}/{v['captions']})")
    print("  top guards:", dict(by_guard.most_common(6)))
    assert total > 500, f"only {total} captions scanned — corpus path wrong"


if __name__ == "__main__":
    main()
