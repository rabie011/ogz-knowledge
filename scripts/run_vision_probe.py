#!/usr/bin/env python3
"""Run the bounded vision probe over the 4 pilots → aggregate brand-level visual DNA from the REAL
top-engagement local images → write data/openclaw_v37/grounded.vision.json in apply_grounded_v37's
contract (every value YELLOW/candidate). Also dumps logs/vision_probe_raw.json for eyeballing the
raw reads BEFORE anything is written to client organs (Rule #9). Money-disciplined: <=8 images/pilot,
gpt-4o-mini, detail='low' (~$0.0002/image → ~$0.007 total). Media is LOCAL (no Apify).
Usage: python3 scripts/run_vision_probe.py [--n 8]
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import vision_probe as vp

B = Path(__file__).parent.parent
PILOTS = ["albaik", "eatjurisha", "alnasserjewelry", "myfitness.sa"]
OUT = B / "data/openclaw_v37/grounded.vision.json"
RAW = B / "logs/vision_probe_raw.json"


def _norm(s):
    return re.sub(r"#[0-9a-fA-F]{3,6}", "", str(s or "")).strip().lower()


def _modal(vals):
    vals = [v for v in vals if v]
    return Counter(_norm(v) for v in vals).most_common(1)[0][0] if vals else ""


def run(n=8):
    vp._load_env()
    grounded, raw_all = [], {}
    for h in PILOTS:
        tops, cov = vp.top_posts_with_local_media(h, n)
        reads = []
        for sc, likes, path in tops:
            d = vp.vision_describe(path)
            if d:
                d["_sc"] = sc; d["_likes"] = likes
                reads.append(d)
            print(f"  {h}: {sc} ({likes} likes) → {_norm(d.get('palette_primary'))[:30]}")
        raw_all[h] = reads
        if not reads:
            continue
        ev = f"vision of top {len(reads)} local posts ({', '.join(r['_sc'] for r in reads[:5])}); coverage {len(reads)}/{cov}"
        # keep the most specific hex if any read produced one
        hexes = [m.group(0) for r in reads for m in [re.search(r"#[0-9a-fA-F]{3,6}", str(r.get("palette_primary","")))] if m]
        prim = _modal([r.get("palette_primary") for r in reads]) + (f" {hexes[0]}" if hexes else "")
        colors = Counter(c.lower().strip() for r in reads for c in (r.get("color_field_palette") or [] if isinstance(r.get("color_field_palette"), list) else [r.get("color_field_palette")]) if c)
        cfp = ", ".join(c for c, _ in colors.most_common(4))
        grounded.append({"handle": h, "brand": {
            "palette_primary": {"value": prim.strip(), "evidence": ev},
            "background_tone": {"value": _modal([r.get("background_tone") for r in reads]), "evidence": ev},
            "color_field_palette": {"value": cfp, "evidence": ev},
        }, "products": []})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(grounded, ensure_ascii=False, indent=1))
    RAW.write_text(json.dumps(raw_all, ensure_ascii=False, indent=1))
    print(f"\n✅ wrote {OUT.relative_to(B)} ({len(grounded)} brands) + {RAW.relative_to(B)} (raw, for eyeballing)")
    return grounded


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=8)
    run(ap.parse_args().n)
