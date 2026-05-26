#!/usr/bin/env python3
"""
fill_sparse_visual_fields.py
Re-classify 2,134 obs missing color_palette_dominant, lighting, and setting.
Uses OpenAI GPT-4o-mini with caption + context (no image needed).

Fields filled (only if empty/null — never overwrites existing):
  visual_observations.color_palette_dominant  ← list of 1-3 color names
  visual_observations.lighting                ← string
  visual_observations.setting                 ← string

Safe to re-run: skips obs where all 3 fields are already filled.

Usage:
  python3 scripts/fill_sparse_visual_fields.py            # full run
  python3 scripts/fill_sparse_visual_fields.py --dry-run  # plan only
  python3 scripts/fill_sparse_visual_fields.py --batch 50 # process N obs
"""
import json, re, sys, time
from collections import defaultdict
from pathlib import Path

BASE     = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS     = BASE / "logs"

# ── OpenAI client ──────────────────────────────────────────────────────────────
import os
env = {}
env_file = Path.home() / ".abraham_env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")

OPENAI_KEY = env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
if not OPENAI_KEY:
    print("ERROR: OPENAI_API_KEY not found in ~/.abraham_env")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=OPENAI_KEY)

SYSTEM = """You classify Saudi Instagram posts for a production intelligence system.
Return ONLY valid JSON. No markdown. No explanation."""

def classify_visual(handle, sector, content_type, caption, composition_style, patterns):
    cap_snippet = (caption or "")[:300]
    pat_list    = ", ".join(patterns[:5]) if patterns else "none"
    user = f"""Saudi Instagram post:
Account: @{handle} | Sector: {sector} | Type: {content_type}
Composition: {composition_style or "unknown"}
Patterns: {pat_list}
Caption: "{cap_snippet}"

Fill these 3 visual fields. Use context clues from brand, sector, and caption.

Return JSON:
{{
  "color_palette_dominant": ["color1", "color2"],
  "lighting": "natural|warm_studio|cool_studio|golden_hour|flat_bright|dramatic|unknown",
  "setting": "studio|restaurant|outdoor|home|retail_store|office|kitchen|salon|unknown"
}}"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":SYSTEM},{"role":"user","content":user}],
            temperature=0.1,
            max_tokens=100,
        )
        raw = resp.choices[0].message.content.strip()
        # strip markdown fences
        raw = re.sub(r"```(?:json)?", "", raw).strip().strip("`")
        return json.loads(raw)
    except Exception as e:
        return None


def main():
    dry_run   = "--dry-run" in sys.argv
    batch_arg = next((sys.argv[i+1] for i,a in enumerate(sys.argv) if a == "--batch"), None)
    batch_max = int(batch_arg) if batch_arg else None

    if dry_run:
        print("DRY RUN — no files will be written\n")

    # ── 1. Find sparse obs ─────────────────────────────────────────────────────
    to_process = []
    for f in sorted(OBS_ROOT.rglob("*.json")):
        try:
            d = json.loads(f.read_text())
            vo = d.get("visual_observations") or {}
            if not vo.get("color_palette_dominant") or not vo.get("lighting") or not vo.get("setting"):
                to_process.append((f, d))
        except:
            pass

    if batch_max:
        to_process = to_process[:batch_max]

    n = len(to_process)
    eta = round(n * 1.2 / 60, 1)
    print(f"Sparse obs to fill : {n}  (≈{eta} min)")

    if dry_run or n == 0:
        if n == 0: print("Nothing to do.")
        return

    stats = defaultdict(int)
    errors = []

    for i, (f, d) in enumerate(to_process, 1):
        pct = round(i/n*100)
        handle  = d.get("account_handle_normalized","?")
        sector  = d.get("sector","?")
        ct      = d.get("content_ref",{}).get("content_type","image")
        voc     = d.get("voice_observations") or {}
        vo      = d.get("visual_observations") or {}
        caption = voc.get("caption_text","")
        comp    = vo.get("composition_style","")
        patterns = [m.get("pattern_slug","") for m in (d.get("pattern_matches") or [])]

        print(f"[{i:>4}/{n}  {pct:>3}%]  @{handle[:20]:20}", end="  ", flush=True)

        result = classify_visual(handle, sector, ct, caption, comp, patterns)

        if result is None:
            print("FAILED")
            stats["failed"] += 1
            errors.append({"file": f.name, "handle": handle})
            time.sleep(0.5)
            continue

        # Only fill if currently empty
        if not vo.get("color_palette_dominant") and result.get("color_palette_dominant"):
            vo["color_palette_dominant"] = result["color_palette_dominant"]
            stats["palette_filled"] += 1
        if not vo.get("lighting") and result.get("lighting"):
            vo["lighting"] = result["lighting"]
            stats["lighting_filled"] += 1
        if not vo.get("setting") and result.get("setting"):
            vo["setting"] = result["setting"]
            stats["setting_filled"] += 1

        d["visual_observations"] = vo
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        stats["written"] += 1

        palette = result.get("color_palette_dominant",["?"])
        print(f"OK  {result.get('lighting','?'):15}  {result.get('setting','?'):12}  {palette}", flush=True)

        # Gentle rate limiting
        time.sleep(0.1)

    print()
    print("="*60)
    print("FILL COMPLETE")
    print(f"  Written          : {stats['written']}")
    print(f"  Palette filled   : {stats['palette_filled']}")
    print(f"  Lighting filled  : {stats['lighting_filled']}")
    print(f"  Setting filled   : {stats['setting_filled']}")
    print(f"  Failed           : {stats['failed']}")
    print()
    print("Next step: python3 scripts/validate_all.py")


if __name__ == "__main__":
    main()
