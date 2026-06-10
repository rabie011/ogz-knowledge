#!/usr/bin/env python3
"""Archive freshness check (L2.7, June 11). Brand archives age — DNA built on stale
posts drifts from the live feed. Reports brands whose newest raw archive is older
than --days (default 30); --enqueue adds them to the extraction queue file the
daemon already consumes. Read-only by default. Run weekly (session-start or cron).
"""
import argparse, datetime, glob, json, os, re
from pathlib import Path

BASE = Path(__file__).parent.parent
QUEUE = BASE / "11_who_to_learn_from" / "_extraction_queue.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--enqueue", action="store_true")
    a = ap.parse_args()
    today = datetime.date.today()
    stale = []
    for d in sorted(glob.glob(str(BASE / "11_who_to_learn_from/_raw_archive/*"))):
        if not os.path.isdir(d):
            continue
        brand = os.path.basename(d)
        dates = [os.path.basename(x) for x in glob.glob(f"{d}/*") if re.match(r"\d{4}-\d{2}-\d{2}", os.path.basename(x))]
        if not dates:
            stale.append((brand, "never", 9999)); continue
        newest = max(dates)
        age = (today - datetime.date.fromisoformat(newest)).days
        if age > a.days:
            stale.append((brand, newest, age))
    print(f"archives older than {a.days}d: {len(stale)}")
    for b, d, age in stale[:50]:
        print(f"  {b:28} last={d} age={age}d")
    if a.enqueue and stale:
        q = json.loads(QUEUE.read_text()) if QUEUE.exists() else []
        existing = {e.get("handle") for e in q if isinstance(e, dict)}
        added = 0
        for b, _, _ in stale:
            if b not in existing:
                q.append({"handle": b, "reason": "freshness_refresh", "queued": str(today)})
                added += 1
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2))
        print(f"enqueued: {added}")


if __name__ == "__main__":
    main()
