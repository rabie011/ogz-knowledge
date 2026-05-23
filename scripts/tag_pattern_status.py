#!/usr/bin/env python3
"""
tag_pattern_status.py
Adds a 'status' field to every pattern JSON:
  evidence_based   — slug appears in at least 1 obs pattern_matches
  library_only     — defined but no obs use it yet
Writes in-place. Does not delete any patterns.
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
PATTERNS_ROOT = BASE / "11_who_to_learn_from" / "patterns"

def main():
    # Count obs usage per pattern slug
    usage = defaultdict(int)
    for f in OBS_ROOT.rglob("*.json"):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        for pm in data.get("pattern_matches", []):
            slug = pm.get("pattern_slug", "") if isinstance(pm, dict) else pm
            if slug:
                usage[slug] += 1

    evidence_based = 0
    library_only = 0

    for pf in sorted(PATTERNS_ROOT.rglob("*.json")):
        try:
            p = json.loads(pf.read_text())
        except Exception:
            continue
        slug = p.get("pattern_slug", "")
        if not slug:
            continue

        if usage[slug] > 0:
            status = "evidence_based"
            evidence_based += 1
        else:
            status = "library_only"
            library_only += 1

        p["status"] = status
        p["obs_usage_count"] = usage[slug]
        pf.write_text(json.dumps(p, ensure_ascii=False, indent=2))

    print(f"Tagged {evidence_based} evidence_based patterns")
    print(f"Tagged {library_only} library_only patterns")
    print(f"Total: {evidence_based + library_only} pattern files updated")

if __name__ == "__main__":
    main()
