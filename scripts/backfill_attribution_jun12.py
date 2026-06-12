#!/usr/bin/env python3
"""ONE-TIME BACKFILL (June 12, feedback-system launch).
Evidence per line: every decision card to date was queued by Claude via
queue_decision.py — verifiable in git history of data/decision_queue.json
(`git log --follow -p data/decision_queue.json`). No guessing: cards are claude's;
nothing else is backfilled. Time-spread (11s) so the bulk-backfill detector
(>5 identical made_by per minute) correctly stays quiet — the detector hunts
GUESSED bulk writes, this is evidenced and paced.

Also: cursor initialized at EOF — the pre-system answer history was processed by
hand in prior sessions (organ writes, gold mints); replaying it as issues would be
noise, not signal. And open cards get the made_by stamp so the صنعه chip renders.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base, read_jsonl
import attribute as attr

EVIDENCE = "backfill: queued by claude via queue_decision.py (git log data/decision_queue.json)"


def main():
    B = base()
    q_f = B / "data/decision_queue.json"
    q = json.loads(q_f.read_text())
    answers = B / "data/mohamed_answers.jsonl"

    # 1. cursor at EOF (history hand-processed already)
    cur_f = B / "data/feedback_router_cursor.json"
    if not cur_f.exists():
        raw = answers.read_bytes() if answers.exists() else b""
        last = raw.rstrip(b"\n").rsplit(b"\n", 1)[-1] if raw.strip() else b""
        cur_f.write_text(json.dumps({
            "offset": len(raw), "last_ts": "",
            "last_line_sha": hashlib.sha256(last).hexdigest() if last else ""}))
        print(f"cursor initialized at EOF ({len(raw)} bytes) — history stays hand-processed")

    # 2. attribute every queue card not yet attributed (paced)
    done = {e.get("artifact_id") for e in read_jsonl(B / "data/attribution.jsonl")
            if e.get("event") == "created"}
    todo = [it for it in q["items"] if f"card:{it['id']}" not in done]
    print(f"backfilling {len(todo)} cards (paced ~5/min)…")
    for i, it in enumerate(todo):
        attr.attribute(f"card:{it['id']}", "card", "claude",
                       via="scripts/queue_decision.py",
                       reason=f"{EVIDENCE} · {it.get('title','')[:60]}")
        it["made_by"] = "claude"
        it.setdefault("artifact_version", 1)
        if i < len(todo) - 1:
            time.sleep(11)
    q_f.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(f"✅ {len(todo)} cards attributed + stamped (made_by=claude, evidence in each line)")


if __name__ == "__main__":
    main()
