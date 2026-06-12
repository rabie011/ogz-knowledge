#!/usr/bin/env python3
"""PUSH A DECISION TO MOHAMED'S PORTAL (June 12).
The pair's one-liner: any moment work needs Mohamed, push it here and MOVE ON.
It appears on his always-live link within 25s (the page polls). --urgent jumps
the line and lights the emergency banner.

Usage:
  python3 scripts/queue_decision.py --id my_id --title "..." --tag "..." \
      --desc "..." --buttons "yes:✅ نعم" "no:❌ لا" [--urgent] [--clock "⏰ ..."]
  python3 scripts/queue_decision.py --id ask_x --title "..." --text "اكتب رأيك"
"""
import argparse, datetime, json, re
from pathlib import Path

QUEUE = Path(__file__).parent.parent / "data/decision_queue.json"
_PAIR = re.compile(r",(?=[a-z_]+:)")  # comma that begins a new  v:label  pair


def parse_buttons(args: list) -> list:
    """Tolerant: accepts space-separated args ("v:lbl" "v:lbl") AND the common
    mistake of comma-joining them into ONE arg ("v:lbl,v:lbl,v:lbl") — the bug that
    collapsed 13 cards into single unusable buttons (June 12). Either way → clean array."""
    out = []
    for b in args:
        for piece in _PAIR.split(b):
            v, _, label = piece.partition(":")
            out.append({"v": v, "label": label})
    return out


def push(item: dict):
    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
    q["items"] = [i for i in q["items"] if i["id"] != item["id"]] + [item]
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return len([i for i in q["items"] if i.get("status") != "answered"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--tag", default="")
    ap.add_argument("--desc", default="")
    ap.add_argument("--clock", default="")
    ap.add_argument("--urgent", action="store_true")
    ap.add_argument("--buttons", nargs="*", default=None, help='each "value:label"')
    ap.add_argument("--text", default=None, help="free-text question placeholder")
    a = ap.parse_args()
    item = {"id": a.id, "title": a.title, "tag": a.tag, "desc": a.desc,
            "clock": a.clock, "priority": "urgent" if a.urgent else "normal",
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "status": "open"}
    if a.buttons:
        item["kind"] = "buttons"
        item["options"] = parse_buttons(a.buttons)
    elif a.text is not None:
        item["kind"] = "text"
        item["placeholder"] = a.text
    else:
        raise SystemExit("need --buttons or --text")
    open_n = push(item)
    print(f"✓ pushed '{a.id}' ({'URGENT' if a.urgent else 'normal'}) — {open_n} open on the portal")


if __name__ == "__main__":
    main()
