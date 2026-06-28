#!/usr/bin/env python3
"""feedback_autoclose — reap stale portal cards (feedback re-look, June 29, orchestra).

The re-look found 16 pending cards — a flood (Rule #10). Root cause: the queue is UNMAINTAINED;
cards pile up and never die. This reaps them: a card pending > AUTOCLOSE_H with no action →
status=answered, answer='auto_closed_stale'. Cron-able. NEVER touches alarms or mission/render
decisions — those wait for Mohamed however long it takes. Rule #10 (one card per condition,
auto-close on resolve) made real.

  python3 scripts/feedback_autoclose.py --dry    # count only
  python3 scripts/feedback_autoclose.py          # apply
"""
import datetime
import json
import sys
from pathlib import Path

QUEUE = Path(__file__).parent.parent / "data" / "decision_queue.json"
AUTOCLOSE_H = 72
# never auto-close: alarms (urgent), or anything Mohamed must rule (mission, render spend, money)
KEEP = ("alarm", "🚨", "🔴", "render", "mission", "money", "spend")


def _age_h(cr, now):
    try:
        return (now - datetime.datetime.fromisoformat(str(cr)[:19])).total_seconds() / 3600.0
    except Exception:
        return None


def autoclose(dry=False):
    q = json.loads(QUEUE.read_text())
    now = datetime.datetime.now()
    closed = []
    for it in q["items"]:
        if it.get("status") == "answered":
            continue
        age = _age_h(it.get("created"), now)
        if age is None or age <= AUTOCLOSE_H:
            continue
        tag = f"{it.get('id','')} {it.get('tag','')} {it.get('title','')}".lower()
        if any(k.lower() in tag for k in KEEP):
            continue
        closed.append((it.get("id"), round(age), (it.get("title") or "")[:40]))
        if not dry:
            it["status"] = "answered"
            it["answer"] = "auto_closed_stale"
            it["auto_closed"] = now.isoformat(timespec="seconds")
    if not dry:
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return closed


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    rows = autoclose(dry=dry)
    print(f"{'WOULD close' if dry else 'auto-closed'} {len(rows)} stale cards (>{AUTOCLOSE_H}h, excl alarms/mission/render):")
    for cid, age, title in rows:
        print(f"  · {cid} ({age}h) — {title}")
