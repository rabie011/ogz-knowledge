#!/usr/bin/env python3
"""CLIENT DRIFT WATCH (B074, June 12) — diff the newest raw extraction against the
prior one; every delta is a PROPOSAL event (inbox, never auto-applied — One Write
Path). The pyramid's drift alarm: an active client whose extractions never differ
means OUR monitoring broke, not that their brand froze.

Usage: python3 scripts/client_drift_watch.py [--handle X]
"""
import argparse, json
from pathlib import Path

BASE = Path(__file__).parent.parent


def load_day(day_dir: Path) -> dict:
    prof = json.loads((day_dir / "profile.json").read_text())
    posts = [json.loads(l) for l in (day_dir / "posts.jsonl").read_text().strip().split("\n") if l.strip()]
    return {"bio": prof.get("biography", ""), "followers": prof.get("followersCount"),
            "posts_count": prof.get("postsCount"), "ext_url": prof.get("externalUrl"),
            "latest_post_ids": {p.get("id") for p in posts[:10] if p.get("id")}}


def watch(handle: str) -> list[dict]:
    raw = BASE / "clients" / handle / "raw/instagram"
    days = sorted(d for d in raw.iterdir() if d.is_dir())
    if len(days) < 2:
        print(f"  ⏸ {handle}: 1 extraction only — armed, waiting for the next scrape")
        return []
    prev, curr = load_day(days[-2]), load_day(days[-1])
    deltas = []
    if prev["bio"] != curr["bio"]:
        deltas.append({"field": "bio", "from": prev["bio"][:80], "to": curr["bio"][:80]})
    if prev["ext_url"] != curr["ext_url"]:
        deltas.append({"field": "bio_link", "from": str(prev["ext_url"]), "to": str(curr["ext_url"])})
    if prev["followers"] and curr["followers"]:
        jump = abs(curr["followers"] - prev["followers"]) / max(prev["followers"], 1)
        if jump > 0.10:
            deltas.append({"field": "followers", "from": prev["followers"], "to": curr["followers"],
                            "note": f"{jump:.0%} jump — investigate (viral? bought? press?)"})
    new_posts = curr["latest_post_ids"] - prev["latest_post_ids"]
    if new_posts:
        deltas.append({"field": "new_posts", "count": len(new_posts),
                        "note": "client posted on their own — voice/truth refresh candidates"})
    lf = BASE / "clients" / handle / "events/ledger.jsonl"
    existing = lf.read_text() if lf.exists() else ""
    day_key = days[-1].name
    for d in deltas:
        key = f"drift:{d['field']}:{day_key}"
        if key in existing:
            continue
        ev = {"ts": day_key, "type": "intake_answer", "subject": key,
               "note": f"PROPOSAL (drift watch): {json.dumps(d, ensure_ascii=False)[:160]}",
               "confirmer": "drift_watch", "stamp": "PROPOSAL — never auto-applied (One Write Path)"}
        with open(lf, "a") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    print(f"  {'🔔' if deltas else '✅'} {handle}: {len(deltas)} drift deltas → PROPOSAL events")
    return deltas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", default=None)
    a = ap.parse_args()
    clients = ([a.handle] if a.handle else
               sorted(d.name for d in (BASE / "clients").iterdir() if (d / "raw/instagram").is_dir()))
    for h in clients:
        watch(h)


if __name__ == "__main__":
    main()
