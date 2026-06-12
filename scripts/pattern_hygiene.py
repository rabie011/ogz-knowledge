#!/usr/bin/env python3
"""DATA RE-LAYERING — LAYER 2: PATTERN HYGIENE (June 12 go-build).
The 1,176 extracted 'patterns' are mostly tags, not mechanisms (arabic_caption: 905
obs — that's a property, not a move). A pattern survives only if it could become an
APPLICABLE mechanism card:

  killed as TAG    — matches >8% of the whole corpus (a property of everything is a
                     mechanism of nothing) OR name on the generic kill-list OR malformed
  killed as WEAK   — <5 supporting obs (no evidence)
  killed as DIRTY  — >50% of its support is law-flagged/duplicate obs (it learned
                     from poison)
  SURVIVOR         — ranked by clean_support; these feed the pattern-card drafting

Reads obs_quality_index.json (L1). Output: data/pattern_quality_index.json.
Patterns are NOT yet registered as players — lineage starts at RATIFICATION
(avoids bulk attribution writes; a pattern becomes a player when Mohamed lets it
into the prompt menu). Zero-LLM, deterministic, nothing deleted.
"""
import json
import glob
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, now_iso

TAG_SHARE = 0.08
MIN_SUPPORT = 5
GENERIC_NAMES = re.compile(
    r"^(arabic_caption|brand_promotional|trending.*|content_types.*|collab_post|"
    r".*_promotional|promotional.*|generic.*|engagement.*|hashtag.*|emoji.*|"
    r"caption_.*_language|.*_content)$")


def main():
    B = base()
    qi = json.loads((B / "data/obs_quality_index.json").read_text())["index"]
    support = defaultdict(list)          # slug → [(ulid, tier)]
    confidences = defaultdict(list)
    for f in glob.glob(str(B / "11_who_to_learn_from/observations/*/*.json")):
        try:
            o = json.loads(Path(f).read_text())
        except Exception:
            continue
        ulid = o.get("observation_ulid") or Path(f).stem
        tier = qi.get(ulid, {}).get("tier", "?")
        for pm in (o.get("pattern_matches") or []):
            slug = pm.get("pattern_slug", "")
            if slug:
                support[slug].append((ulid, tier))
                confidences[slug].append(pm.get("confidence", ""))

    total_obs = len(qi)
    out, counts = {}, defaultdict(int)
    for slug, obs in support.items():
        n = len(obs)
        clean = [u for u, t in obs if t == "clean"]
        clean_pct = len(clean) / n if n else 0
        malformed = not re.match(r"^[a-z0-9_]+$", slug)
        if malformed or GENERIC_NAMES.match(slug) or n > TAG_SHARE * total_obs:
            status = "tag"
        elif n < MIN_SUPPORT:
            status = "weak"
        elif clean_pct < 0.5:
            status = "dirty"
        else:
            status = "survivor"
        counts[status] += 1
        out[slug] = {"status": status, "support": n, "clean_support": len(clean),
                     "clean_pct": round(clean_pct, 2),
                     "strong_conf": sum(1 for c in confidences[slug] if c == "strong"),
                     "sample_clean_ulids": clean[:5]}

    survivors = sorted([(s, d) for s, d in out.items() if d["status"] == "survivor"],
                       key=lambda x: -x[1]["clean_support"])
    res = {"generated": now_iso(), "patterns_total": len(out), "counts": dict(counts),
           "survivors_ranked": [s for s, _ in survivors], "index": out}
    (B / "data/pattern_quality_index.json").write_text(json.dumps(res, ensure_ascii=False))
    re_read = json.loads((B / "data/pattern_quality_index.json").read_text())
    assert re_read["patterns_total"] == len(out), "index write mismatch"
    print(f"patterns scored: {len(out)}")
    for k, v in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    print("\ntop 15 survivors (by clean support):")
    for s, d in survivors[:15]:
        print(f"  {d['clean_support']:4d}  {s}")


if __name__ == "__main__":
    main()
