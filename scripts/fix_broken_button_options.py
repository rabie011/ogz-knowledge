#!/usr/bin/env python3
"""REPAIR (June 12) — six decision cards were queued with comma-joined buttons in a
SINGLE --buttons arg instead of space-separated args, so queue_decision.py split only
on the first colon and collapsed every card's 2-4 choices into ONE unusable button
(Mohamed: "alot of issue for clicking"). This re-parses the `v:label,v:label` string
back into a proper options array. Idempotent: a card already holding >1 option is left
alone. Pattern: a comma that PRECEDES an ascii-token-then-colon starts a new option;
commas inside a label (none here, but safe) stay put.
"""
import json
import re
from pathlib import Path

QUEUE = Path(__file__).parent.parent / "data" / "decision_queue.json"
SPLIT = re.compile(r",(?=[a-z_]+:)")  # comma that begins a new  v:label  pair


def reparse(option0: dict) -> list:
    raw = f"{option0['v']}:{option0['label']}"
    return [{"v": p.split(":", 1)[0], "label": p.split(":", 1)[1]}
            for p in SPLIT.split(raw)]


def main():
    q = json.loads(QUEUE.read_text())
    fixed = []
    for it in q["items"]:
        if it.get("kind") == "buttons" and len(it.get("options", [])) == 1 \
                and SPLIT.search(it["options"][0].get("label", "")):
            before = len(it["options"])
            it["options"] = reparse(it["options"][0])
            fixed.append((it["id"], before, len(it["options"])))
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    for cid, b, a in fixed:
        print(f"  ✅ {cid}: {b} → {a} options")
    print(f"\nrepaired {len(fixed)} cards" if fixed else "nothing to repair (idempotent)")


if __name__ == "__main__":
    main()
