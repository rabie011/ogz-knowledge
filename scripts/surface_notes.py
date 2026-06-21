#!/usr/bin/env python3
"""SURFACE MOHAMED'S WRITTEN NOTES — the Consumer-Law fix (June 21, after he asked "do u check
what i send" and 3 nights of _general_note instructions had sat UNREAD).

His TAPS (pairwise picks, judge verdicts) were consumed; his WRITTEN notes were not — a severed
wire. This reader closes it: every free-text note he writes in the portal (item_id _general_note,
judge=mohamed) is pulled from data/mohamed_answers.jsonl, de-duped against a seen-ledger, and
written to data/mohamed_notes_inbox.md — the file the session-start + every RABIE shift reads FIRST.
A note is a directive until I've acted on it; --mark-seen records that I have (with what I did).

  python3 scripts/surface_notes.py            # show UNSEEN notes + (re)write the inbox
  python3 scripts/surface_notes.py --all       # show every note, newest first
  python3 scripts/surface_notes.py --mark-seen "did X, Y"   # mark current unseen as acted-on
"""
import argparse, hashlib, json, time
from pathlib import Path

B = Path(__file__).parent.parent
ANS = B / "data/mohamed_answers.jsonl"
SEEN = B / "data/mohamed_notes_seen.json"
INBOX = B / "data/mohamed_notes_inbox.md"


def _notes():
    """His free-text notes, newest first: _general_note OR any long free-text answer from him."""
    if not ANS.exists():
        return []
    out, seen_text = [], set()
    for l in ANS.read_text().splitlines():
        if not l.strip():
            continue
        try:
            r = json.loads(l)
        except Exception:
            continue
        if r.get("judge") != "mohamed":
            continue
        ans = str(r.get("answer", "")).strip()
        iid = str(r.get("item_id", ""))
        is_note = iid == "_general_note" or (len(ans) > 18 and ans.lower() not in
                  ("approved", "rejected", "comment", "yes", "no", "a", "b"))
        if not is_note or not ans:
            continue
        key = hashlib.md5((r.get("ts", "") + ans).encode()).hexdigest()[:12]
        if key in seen_text:
            continue
        seen_text.add(key)
        out.append({"key": key, "ts": r.get("ts", ""), "item": iid, "text": ans})
    return sorted(out, reverse=True, key=lambda x: x["ts"])


def _seen_keys():
    if SEEN.exists():
        try:
            return {e["key"]: e for e in json.loads(SEEN.read_text()).get("seen", [])}
        except Exception:
            return {}
    return {}


def write_inbox(notes, seen):
    unseen = [n for n in notes if n["key"] not in seen]
    lines = ["# MOHAMED'S NOTES INBOX — READ FIRST (auto: scripts/surface_notes.py)",
             f"# {len(unseen)} UNREAD · {len(notes)} total · refreshed {time.strftime('%Y-%m-%d %H:%M')}",
             "# A note is a DIRECTIVE until acted on. After acting: surface_notes.py --mark-seen \"what I did\"",
             ""]
    if unseen:
        lines.append("## 🔴 UNREAD — act on these")
        for n in unseen:
            lines.append(f"- **[{n['ts'][:16]}]** «{n['text']}»")
        lines.append("")
    lines.append("## ✅ acted-on (history, newest first)")
    for n in notes:
        if n["key"] in seen:
            did = seen[n["key"]].get("did", "")
            lines.append(f"- [{n['ts'][:16]}] «{n['text'][:90]}{'…' if len(n['text'])>90 else ''}»"
                         + (f" → _{did}_" if did else ""))
    INBOX.write_text("\n".join(lines) + "\n")
    return unseen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--mark-seen", dest="mark", default=None,
                    help="mark all current UNSEEN notes as acted-on, recording what was done")
    a = ap.parse_args()
    notes = _notes()
    seen = _seen_keys()
    if a.mark is not None:
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        for n in notes:
            if n["key"] not in seen:
                seen[n["key"]] = {"key": n["key"], "ts": n["ts"], "did": a.mark, "acted": now}
        SEEN.write_text(json.dumps({"seen": list(seen.values())}, ensure_ascii=False, indent=1))
        print(f"✅ marked {len([n for n in notes if seen.get(n['key'],{}).get('acted')==now])} notes acted-on: {a.mark}")
    unseen = write_inbox(notes, seen)
    print(f"📥 {len(unseen)} UNREAD note(s) · inbox → {INBOX.relative_to(B)}")
    for n in (notes if a.all else unseen):
        flag = "🔴" if n["key"] not in seen else "  "
        print(f"  {flag} [{n['ts'][:16]}] «{n['text'][:120]}{'…' if len(n['text'])>120 else ''}»")


if __name__ == "__main__":
    main()
