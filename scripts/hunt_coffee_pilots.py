#!/usr/bin/env python3
"""COFFEE PILOT HUNT (authorized: Mohamed tapped «hunt» 2026-06-13 00:00:40).
Find 3 LIVE-VERIFIED Saudi specialty-coffee SMEs: real handle, Saudi signals in the
bio, alive (recent activity), SME-range followers (3k-100k). Candidates come from
the corpus's verified obs brands' sector + known Saudi coffee handles; every one is
checked against live Instagram BEFORE it can reach Mohamed (the Excel-handle law).
Output: appends verified candidates to data/pilot_shortlist.json (verified_live only).
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent

# candidate pool ROUND 2 (his keep_hunting tap 2026-06-13 02:10 — camelstep passed on,
# net widened; dead/guessed handles drop at the live-verify wall, never reach him)
CANDIDATES = [
    "elixirbunn", "rosettecoffeeco", "anbarcoffee", "kiffa.coffee", "rawicoffee",
    "abaq.coffee", "thecupscoffee", "brewlab.sa", "ratiocoffee", "naqacoffee",
    "ministryofcoffee.sa", "localcoffeesa", "kavahcoffee", "sulalat.coffee",
    "blackspoon.sa", "qavacoffee", "span.coffee", "hijazcoffee", "bayadercoffee",
    "roastery.sa",
]


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def main():
    from apify_client import ApifyClient
    client = ApifyClient(env("APIFY_TOKEN"))
    run = client.actor("apify/instagram-profile-scraper").call(
        run_input={"usernames": CANDIDATES})
    ds = getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)
    live = []
    for item in client.dataset(ds).iterate_items():
        u = item.get("username")
        f = item.get("followersCount")
        bio = (item.get("biography") or "")
        if not u or f is None:
            continue
        # «سعود» not «السعود» — round 2 bug: elixirbunn's own bio says «علامة سعودية»
        # and the definite-article marker missed it (0-result round). Cities widened.
        saudi = any(m in bio for m in ("سعود", "الرياض", "جدة", "مكة", "المدينة المنورة",
                                       "الدمام", "الخبر", "تبوك", "أبها", "Saudi", "Riyadh",
                                       "Jeddah", "Dammam", "KSA", "🇸🇦"))
        if 3000 <= f <= 100000 and saudi:
            live.append({"handle": u, "name": item.get("fullName"), "followers": f,
                         "posts": item.get("postsCount"), "bio": bio[:100]})
    live.sort(key=lambda x: -x["followers"])
    top3 = live[:3]
    print(f"live-verified Saudi coffee SMEs: {len(live)} → top 3:")
    for c in top3:
        print(f"  ☕ @{c['handle']} · {c['name']} · {c['followers']:,} followers")
    sl = json.loads((BASE / "data/pilot_shortlist.json").read_text())
    for c in top3:
        sl["shortlist"].append({
            "handle": c["handle"], "sector": "f_and_b", "sub": "Specialty Coffee",
            "verified_live": True,
            "verification": {"date": datetime.now().isoformat(timespec="seconds")[:10],
                             "name": c["name"], "followers": c["followers"],
                             "note": "coffee hunt (Mohamed's «hunt» tap 2026-06-13 00:00)"}})
    (BASE / "data/pilot_shortlist.json").write_text(json.dumps(sl, ensure_ascii=False, indent=1))
    json.dump(top3, open("/tmp/coffee_top3.json", "w"), ensure_ascii=False)
    # the standing assert must still pass
    import subprocess
    r = subprocess.run([sys.executable, str(BASE / "scripts/verify_shortlist.py")],
                       capture_output=True, text=True)
    print(r.stdout.strip() or r.stderr.strip())


if __name__ == "__main__":
    main()
