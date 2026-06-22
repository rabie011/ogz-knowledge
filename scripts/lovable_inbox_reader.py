#!/usr/bin/env python3
"""LOVABLE-INBOX-READER — the missing READER for inbox/lovable-commits.md (Rule #6, B239b).
lovable_watch.py (B239) is the SENSOR: it WRITES new clone-in-a-snap commits to the harvest
inbox and pings Mira — but nothing READ the inbox, so harvested-or-not the commits piled up
invisibly (a write-only organ, the #1 recurring scar). This gives the inbox its reader: it
counts the commits the sensor landed against a harvest cursor and surfaces what's still
AWAITING design-harvest ("take from lovable" = one-way Lovable→design system). HARVESTING is
the (human/design) stage; this only makes the queue VISIBLE on the standing cadence so it can
never silently vanish again, and it AUTO-CLOSES (Rule #10) when mark_harvested advances the
cursor. Zero-key, read-only by default.

Usage: python3 scripts/lovable_inbox_reader.py             # show pending harvest queue
       python3 scripts/lovable_inbox_reader.py --harvested  # the consumer's hand: advance cursor
"""
import json
import re
import sys
import time
from pathlib import Path

B = Path(__file__).parent.parent
INBOX = B / "inbox" / "lovable-commits.md"
CURSOR = B / "data" / "lovable_harvest_cursor.json"

# Matches the bullets lovable_watch._append_inbox writes:  - `<short>` <subject>  (<date>)
_COMMIT = re.compile(r"^- `([0-9a-f]+)` (.*)")


def landed_commits(inbox_path=INBOX):
    """Every commit bullet the sensor appended → [{short, subject}]. What the Rule #6 reader consumes."""
    p = Path(inbox_path)
    if not p.exists():
        return []
    out = []
    for ln in p.read_text().splitlines():
        m = _COMMIT.match(ln.strip())
        if m:
            out.append({"short": m.group(1), "subject": m.group(2).strip()})
    return out


def _harvested_count(cursor_path=CURSOR):
    p = Path(cursor_path)
    if not p.exists():
        return 0
    try:
        return int(json.loads(p.read_text()).get("harvested_count", 0))
    except Exception:
        return 0


def pending(inbox_path=INBOX, cursor_path=CURSOR):
    """Commits landed in the inbox but not yet marked harvested — the open queue."""
    landed = landed_commits(inbox_path)
    h = _harvested_count(cursor_path)
    h = max(0, min(h, len(landed)))  # cursor never exceeds what actually landed
    return {"total": len(landed), "harvested": h, "pending": len(landed) - h,
            "commits": landed[h:]}


def mark_harvested(inbox_path=INBOX, cursor_path=CURSOR, now=None):
    """The consumer's hand: the design-harvest stage advances the cursor → the queue auto-closes."""
    n = len(landed_commits(inbox_path))
    Path(cursor_path).parent.mkdir(parents=True, exist_ok=True)
    Path(cursor_path).write_text(json.dumps(
        {"harvested_count": n, "updated": now or time.strftime("%Y-%m-%dT%H:%M:%S")},
        ensure_ascii=False, indent=2))
    return n


def summary_line(inbox_path=INBOX, cursor_path=CURSOR):
    """One informational line for the heartbeat surface (not an alarm — Rule #10 no-flood)."""
    st = pending(inbox_path, cursor_path)
    if st["total"] == 0:
        return "🎨 lovable harvest inbox: empty (sensor watching, nothing landed yet)"
    if st["pending"] == 0:
        return f"🎨 lovable harvest inbox: clean ({st['total']} commit(s) all harvested)"
    return (f"🎨 {st['pending']} Lovable commit(s) awaiting design-harvest "
            f"(inbox/lovable-commits.md, 'take from lovable')")


def main():
    if "--harvested" in sys.argv:
        n = mark_harvested()
        print(f"lovable-inbox: cursor advanced — {n} commit(s) marked harvested.")
        return 0
    st = pending()
    print(summary_line())
    for c in st["commits"]:
        print(f"  `{c['short']}` {c['subject'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
