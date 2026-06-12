#!/usr/bin/env python3
"""THE FEEDBACK ROUTER — the consumer (June 12). Feedback that lands in a ledger and
is never read = the 88-day dead-orchestrator scar relocated. This tails
mohamed_answers.jsonl from a byte cursor and turns every new row into action:

  rejected / rating<=2  → OPEN an issue against the resolved player
  fix box non-empty     → OPEN + append the VERBATIM correction to corrections.jsonl
                          (the richest taste signal — must be CONSUMED, not ticketed)
  REVERSED              → VOID any issue opened by the reversed verdict (the inverse
                          cascade all four lenses missed — innocent players cleared)
  plain comment         → no issue (a note is not a complaint)

Cursor discipline: write-then-advance (the event is appended BEFORE the cursor moves —
a crash replays, never loses). last_line_sha detects append-only violations.
Player resolution order: explicit target → attribution join (artifact_id) →
card made_by (item_id) → system:unattributed (counted, red, never guessed).
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import append_jsonl, base, is_player, now_iso, read_jsonl
import attribute as attr
import issue_log


def cursor_path() -> Path:
    return base() / "data/feedback_router_cursor.json"


def answers_path() -> Path:
    return base() / "data/mohamed_answers.jsonl"


def corrections_path() -> Path:
    return base() / "data/corrections.jsonl"


def load_cursor() -> dict:
    p = cursor_path()
    return json.loads(p.read_text()) if p.exists() else {"offset": 0, "last_ts": "", "last_line_sha": ""}


def save_cursor(c: dict):
    cursor_path().write_text(json.dumps(c))


def resolve_player(row: dict) -> str:
    """explicit target → attribution(artifact_id) → card made_by(item_id) → unattributed."""
    t = row.get("target")
    if t and is_player(t):
        return t
    aid = row.get("artifact_id")
    if aid:
        mb, _, _ = attr.made_by_of(aid)
        if mb:
            return mb
    iid = row.get("item_id")
    if iid:
        mb, _, _ = attr.made_by_of(f"card:{iid}")
        if mb:
            return mb
        # the card itself may carry made_by (stamped by queue_decision going forward)
        q = base() / "data/decision_queue.json"
        if q.exists():
            for it in json.loads(q.read_text()).get("items", []):
                if it.get("id") == iid and it.get("made_by") and is_player(it["made_by"]):
                    return it["made_by"]
    return "system:unattributed"


def check_append_only() -> bool:
    """The cursor's last processed line must still sit at its offset — else the
    truth ledger was rewritten under us (blocking issue)."""
    c = load_cursor()
    if not c["last_line_sha"] or c["offset"] == 0:
        return True
    p = answers_path()
    if not p.exists():
        return False
    with open(p, "rb") as f:
        data = f.read(c["offset"])
    if len(data) < c["offset"]:
        return False
    last_line = data.rstrip(b"\n").rsplit(b"\n", 1)[-1]
    return hashlib.sha256(last_line).hexdigest() == c["last_line_sha"]


def _is_reject(row: dict) -> bool:
    if str(row.get("answer", "")).strip().lower() in ("rejected", "flagged"):
        return True
    r = row.get("rating")
    return isinstance(r, int) and r <= 2


def process(verbose: bool = False) -> dict:
    """One pass: consume all rows past the cursor. Idempotent (cursor + issue dedupe)."""
    stats = {"rows": 0, "issues_opened": 0, "corrections": 0, "voided": 0, "skipped": 0}
    p = answers_path()
    if not p.exists():
        return stats
    if not check_append_only():
        issue_log.open_issue("system:mohamed_answers", "append-only violated — ledger rewritten under the cursor",
                             reason_code="ledger_integrity", target_path="data/mohamed_answers.jsonl",
                             severity="blocking", source="make_sure", by="feedback_router")
        # fall through: reset sha so we don't loop the alarm forever; offset stays
    c = load_cursor()
    raw = p.read_bytes()
    new = raw[c["offset"]:]
    if not new.strip():
        return stats
    offset = c["offset"]
    for bline in new.split(b"\n"):
        if not bline.strip():
            offset += len(bline) + 1
            continue
        line_end = offset + len(bline) + 1
        try:
            row = json.loads(bline.decode("utf-8"))
        except Exception:
            offset = line_end
            continue
        stats["rows"] += 1
        judge = row.get("judge", "")
        # quarantined / unverified rows never drive issues
        if judge in ("", "unverified"):
            stats["skipped"] += 1
        elif str(row.get("answer", "")) == "REVERSED":
            # VOID the issues that the reversed verdict opened (inverse cascade)
            ref = f"{row.get('ts','')}+{row.get('item_id','')}"
            for ev in read_jsonl(base() / "data/issues.jsonl"):
                if (ev.get("event") == "open" and ev.get("source_answer")
                        and ev["source_answer"].get("item_id") == row.get("item_id")
                        and issue_log.current_state(ev["issue_id"]) in ("open", "fix_claimed", "verified")):
                    issue_log.void(ev["issue_id"], reversal_ref=ref)
                    stats["voided"] += 1
        else:
            fix_text = (row.get("fix") or "").strip()
            player = resolve_player(row)
            if fix_text:
                append_jsonl(corrections_path(), {
                    "ts": now_iso(), "source_answer": {"ts": row.get("ts"), "item_id": row.get("item_id")},
                    "judge": judge, "player": player, "artifact_id": row.get("artifact_id"),
                    "lane": row.get("lane"), "fix_text": fix_text})
                stats["corrections"] += 1
            if _is_reject(row) or fix_text:
                codes = row.get("reason_codes") or []
                e = issue_log.open_issue(
                    player, quote=(row.get("note") or fix_text or row.get("answer") or "")[:200],
                    reason_code=(codes[0] if codes else "unspecified"),
                    target=row.get("target") or (f"card:{row['item_id']}" if row.get("item_id") else None),
                    target_version=row.get("artifact_version"),
                    source="portal", source_answer={"ts": row.get("ts"), "item_id": row.get("item_id")})
                if e.get("event") in ("open", "reopened"):
                    stats["issues_opened"] += 1
        # WRITE-THEN-ADVANCE: events are on disk before the cursor moves
        save_cursor({"offset": line_end if line_end <= len(raw) else len(raw),
                     "last_ts": row.get("ts", ""),
                     "last_line_sha": hashlib.sha256(bline).hexdigest()})
        offset = line_end
    if verbose:
        print(json.dumps(stats))
    return stats


if __name__ == "__main__":
    s = process(verbose=True)
    print(f"routed: {s}", file=sys.stderr)
