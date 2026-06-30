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
import argparse, datetime, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base as _base

_PAIR = re.compile(r",(?=[a-z_]+:)")  # comma that begins a new  v:label  pair


def _queue_path() -> Path:
    return _base() / "data/decision_queue.json"


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


def _action_type(item: dict) -> str:
    """Stamp the portal bucket at PUSH time → deterministic (DeepSeek-verify fix, June 29): the portal
    reads action_type directly instead of re-inferring from fragile field-presence. alarm|decision|info."""
    if item.get("action_type") in ("alarm", "decision", "info"):
        return item["action_type"]
    txt = f"{item.get('id','')} {item.get('tag','')} {item.get('title','')}"
    if any(e in txt for e in ("🚨", "🔴", "alarm", "إنذار", "taste_stale")):
        return "alarm"
    return "decision" if (item.get("buttons") or item.get("options") or item.get("text") or item.get("composer")) else "info"


_TAP_EXEMPT = ("judge_", "judge2_", "ratify_")  # judge/ratify lanes own their own dispatch
# NOTE: 'closures_' was REMOVED here (B292). The blanket exemption MASKED a real dead-end —
# the 'reopen_one' tap resolved to None. Now reopen_one has a handler (apply_rulings) and 'seen'
# is an ACK, so closures cards pass the door-check honestly AND a future bogus option is caught.


def _assert_taps_land(item: dict):
    """REFUSE-DON'T-WARN (Rule #8) the dead-end tap at the DOOR (Rule #7): every option on a
    live buttons card must resolve to a handler, or the tap lands nowhere. Born June 30 when a
    money-gate card (vision_2nd_model_fund) was staged WITHOUT the `_fork` suffix and its taps
    (hold/anthropic/gemini) resolved to None — caught only later by the B291 sweep test. This
    moves the invariant from a post-hoc test to the write path: the bad card can't be staged.
    Exemptions mirror the sweep test exactly (judge/closures lanes own their own dispatch)."""
    if item.get("kind") != "buttons":
        return
    iid = item.get("id", "")
    if iid.startswith(_TAP_EXEMPT):
        return
    import apply_rulings  # lazy: apply_rulings imports queue_decision only inside funcs (no cycle)
    dead = [o.get("v", "") for o in item.get("options", [])
            if o.get("v", "") not in apply_rulings.ACK_ANSWERS
            and apply_rulings._resolve((iid, o.get("v", ""))) is None]
    if dead:
        raise SystemExit(
            f"🚫 REFUSED: card '{iid}' has dead-end tap(s) {dead} — no handler resolves them "
            f"(Rule #7: pre-wire the tap). Fix: suffix the id with '_fork' for a record-only "
            f"decision card, or register a handler in apply_rulings before pushing.")


def push(item: dict):
    QUEUE = _queue_path()
    _assert_taps_land(item)                     # Rule #7/#8: no dead-end tap reaches his portal
    item["action_type"] = _action_type(item)   # deterministic bucket for the portal gate (re-look fix)
    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
    q["items"] = [i for i in q["items"] if i["id"] != item["id"]] + [item]
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return len([i for i in q["items"] if i.get("status") != "answered"])


def push_attributed(item: dict, made_by: str = "claude",
                    via: str = "scripts/queue_decision.py", reason: str = ""):
    """The feedback-aware push: ATTRIBUTE BEFORE PUSH (transactional ordering — a crash
    between the two leaves an attributed ghost, never an unattributable card), stamp
    made_by + artifact_version on the card, and refuse loudly for a BENCHED player."""
    import attribute as attr
    bench_f = _base() / "data/bench.json"
    bench = json.loads(bench_f.read_text()) if bench_f.exists() else {}
    if made_by in bench:
        raise SystemExit(f"🧊 REFUSED: {made_by} is benched (cold streak) — "
                         f"Mohamed's reversal or fresh approvals un-bench it")
    entry = attr.attribute(f"card:{item['id']}", "card", made_by, via=via,
                           reason=reason or item.get("title", "")[:100])
    assert attr.latest_version(f"card:{item['id']}") == entry["artifact_version"], \
        "attribution line not on disk — refusing to push"
    item["made_by"] = made_by
    item["artifact_version"] = entry["artifact_version"]
    return push(item)


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
    ap.add_argument("--made-by", default="claude", help="the PLAYER this card's content came from (mind:firaasa etc.)")
    ap.add_argument("--why", default="", help="the one-line WHY shown bold on the card")
    ap.add_argument("--need", default="", help="المطلوب — what we need from Mohamed")
    ap.add_argument("--did", default="", help="سوّاه النظام — what the system did")
    a = ap.parse_args()
    item = {"id": a.id, "title": a.title, "tag": a.tag, "desc": a.desc,
            "clock": a.clock, "priority": "urgent" if a.urgent else "normal",
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "status": "open"}
    for k in ("why", "need", "did"):
        if getattr(a, k):
            item[k] = getattr(a, k)
    if a.buttons:
        item["kind"] = "buttons"
        item["options"] = parse_buttons(a.buttons)
    elif a.text is not None:
        item["kind"] = "text"
        item["placeholder"] = a.text
    else:
        raise SystemExit("need --buttons or --text")
    open_n = push_attributed(item, made_by=a.made_by)
    print(f"✓ pushed '{a.id}' ({'URGENT' if a.urgent else 'normal'}, by {a.made_by}) — {open_n} open on the portal")


if __name__ == "__main__":
    main()
