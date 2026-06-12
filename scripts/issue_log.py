#!/usr/bin/env python3
"""THE ONE ISSUE LEDGER — sole writer (June 12). Feedback must BECOME something:
open → fix_claimed → verified → closed, with reopened / voided as the side paths.
Any refusal = exit 1 / raise with ZERO bytes written (ASSERT LAW).

EVIDENCE GATES (the 39/44 false-PREPARED scar, mechanized):
- fix_claimed: commit must EXIST (git cat-file -e) AND touch the issue's target_path
  (git show --name-only) — an unrelated-but-real commit is refused.
- verified: verify_cmd executable must live under scripts/ (allowlist), runs with a
  120s timeout, exit 0 required. Rendered everywhere as «اتصلحت (حسب السكربت)» —
  claimed + script passed, NEVER truth. The honest backstop is reopen-on-recurrence
  plus Mohamed's tap.

Telegram intake (the highest-bandwidth mouth — Mohamed complains in chat, not taps):
  python3 scripts/issue_log.py open --player claude --quote "الكابشنز طويلة" \
      --source telegram [--reason-code too_long] [--target caption:x] [--severity normal]
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import append_jsonl, base, is_player, now_iso, read_jsonl

EVENTS = {"open", "fix_claimed", "verified", "closed", "reopened", "voided"}
SEVERITIES = {"blocking", "normal"}


def ledger() -> Path:
    return base() / "data/issues.jsonl"


def fingerprint(player: str, reason_code: str) -> str:
    return hashlib.sha1(f"{player}:{reason_code}".encode()).hexdigest()[:12]


def issue_events(issue_id: str) -> list:
    return [e for e in read_jsonl(ledger()) if e.get("issue_id") == issue_id]


def current_state(issue_id: str) -> str:
    evs = issue_events(issue_id)
    if not evs:
        return "none"
    last = evs[-1]["event"]
    return {"open": "open", "fix_claimed": "fix_claimed", "verified": "verified",
            "closed": "closed", "reopened": "open", "voided": "voided"}[last]


def _refuse(msg: str):
    raise ValueError(msg)


def _common(issue_id: str, event: str, player: str, by: str) -> dict:
    return {"schema_v": 1, "ts": now_iso(), "issue_id": issue_id,
            "event": event, "player": player, "by": by}


def open_issue(player: str, quote: str, reason_code: str = "unspecified",
               target: str = None, target_path: str = None, target_version: int = None,
               severity: str = "normal", source: str = "portal",
               source_answer: dict = None, by: str = "feedback_router") -> dict:
    if not is_player(player):
        _refuse(f"open: invalid player {player!r}")
    if severity not in SEVERITIES:
        _refuse(f"open: invalid severity {severity!r}")
    fp = fingerprint(player, reason_code)
    # recurrence: a closed issue with the same fingerprint within 14 days → REOPEN instead
    for e in reversed(read_jsonl(ledger())):
        if e.get("fingerprint") == fp and e.get("event") == "open":
            iid = e["issue_id"]
            st = current_state(iid)
            if st == "closed":
                closed_ts = max((x["ts"] for x in issue_events(iid) if x["event"] == "closed"), default="")
                from datetime import datetime, timedelta
                if closed_ts and datetime.fromisoformat(now_iso()) - datetime.fromisoformat(closed_ts) <= timedelta(days=14):
                    return reopen(iid, player, cause="recurrence", by=by)
            break
    iid = f"iss_{now_iso()[:10].replace('-','')}_{fp}"
    if current_state(iid) not in ("none", "closed", "voided"):
        return issue_events(iid)[0]      # already open today with same fingerprint — dedupe
    entry = {**_common(iid, "open", player, by), "fingerprint": fp,
             "target": target, "target_path": target_path, "target_version": target_version,
             "severity": severity, "reason_code": reason_code,
             "quote": (quote or "")[:200], "source": source, "source_answer": source_answer}
    append_jsonl(ledger(), entry)
    return entry


def fix_claimed(issue_id: str, commit: str, fix_desc: str, files: list = None,
                by: str = "claude") -> dict:
    evs = issue_events(issue_id)
    if not evs:
        _refuse(f"fix_claimed: unknown issue {issue_id}")
    if current_state(issue_id) not in ("open",):
        _refuse(f"fix_claimed: issue {issue_id} is {current_state(issue_id)}, not open")
    # GATE 1a: the commit must exist
    r = subprocess.run(["git", "-C", str(base()), "cat-file", "-e", commit],
                       capture_output=True, timeout=15)
    if r.returncode != 0:
        _refuse(f"fix_claimed: commit {commit!r} does not exist")
    # GATE 1b: the commit must TOUCH the target (unrelated-commit defense)
    show = subprocess.run(["git", "-C", str(base()), "show", "--name-only", "--format=", commit],
                          capture_output=True, text=True, timeout=15)
    touched = [l.strip() for l in show.stdout.splitlines() if l.strip()]
    opener = evs[0]
    tp = opener.get("target_path")
    required = ([tp] if tp else (files or []))
    if not required:
        _refuse("fix_claimed: issue has no target_path — pass --files the commit must touch")
    if not any(any(t == req or t.startswith(req.rstrip("/") + "/") for t in touched) for req in required):
        _refuse(f"fix_claimed: commit {commit[:9]} touches none of {required} (touched: {touched[:5]})")
    entry = {**_common(issue_id, "fix_claimed", opener["player"], by),
             "commit": commit, "files": touched[:20], "fix_desc": (fix_desc or "")[:200]}
    append_jsonl(ledger(), entry)
    return entry


def verified(issue_id: str, verify_cmd: list, by: str = "claude") -> dict:
    if current_state(issue_id) != "fix_claimed":
        _refuse(f"verified: issue {issue_id} is {current_state(issue_id)}, not fix_claimed")
    # GATE 2: allowlisted executable only — a free-form command is arbitrary shell
    exe = Path(verify_cmd[0] if verify_cmd[0] != "python3" else (verify_cmd[1] if len(verify_cmd) > 1 else ""))
    try:
        exe_resolved = (base() / exe).resolve() if not exe.is_absolute() else exe.resolve()
    except Exception:
        _refuse(f"verified: cannot resolve {exe}")
    if not str(exe_resolved).startswith(str((base() / "scripts").resolve())):
        _refuse(f"verified: {exe} is outside scripts/ (allowlist)")
    r = subprocess.run([c if c != str(exe) else str(exe_resolved) for c in verify_cmd],
                       capture_output=True, text=True, timeout=120, cwd=str(base()))
    if r.returncode != 0:
        _refuse(f"verified REFUSED: verify_cmd exit {r.returncode} — fix stays claimed-only. stderr: {r.stderr[-300:]}")
    opener = issue_events(issue_id)[0]
    entry = {**_common(issue_id, "verified", opener["player"], by),
             "verify_cmd": " ".join(verify_cmd), "exit_code": 0,
             "evidence": (r.stdout or "")[-500:]}
    append_jsonl(ledger(), entry)
    return entry


def close(issue_id: str, closed_by: str, by: str = "claude") -> dict:
    st = current_state(issue_id)
    opener = issue_events(issue_id)[0]
    if closed_by == "auto_verify_timeout" and opener.get("severity") == "blocking":
        _refuse("close: blocking issues only close on Mohamed's tap")
    if closed_by == "target_retired":
        pass                                     # tombstone closure is always legal
    elif st not in ("verified",) and closed_by != "mohamed_tap":
        _refuse(f"close: issue is {st}; needs verified first (or mohamed_tap)")
    entry = {**_common(issue_id, "closed", opener["player"], by), "closed_by": closed_by}
    append_jsonl(ledger(), entry)
    return entry


def reopen(issue_id: str, player: str, cause: str, by: str = "feedback_router") -> dict:
    prior = sum(1 for e in issue_events(issue_id) if e["event"] == "reopened")
    entry = {**_common(issue_id, "reopened", player, by),
             "cause": cause, "recurrence_count": prior + 1}
    append_jsonl(ledger(), entry)
    return entry


def void(issue_id: str, reversal_ref: str, by: str = "feedback_router") -> dict:
    opener = issue_events(issue_id)
    if not opener:
        _refuse(f"void: unknown issue {issue_id}")
    entry = {**_common(issue_id, "voided", opener[0]["player"], by),
             "cause": "source_answer_reversed", "reversal_ref": reversal_ref}
    append_jsonl(ledger(), entry)
    return entry


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("open")
    o.add_argument("--player", required=True)
    o.add_argument("--quote", required=True, help="Mohamed's VERBATIM words")
    o.add_argument("--reason-code", default="unspecified")
    o.add_argument("--target")
    o.add_argument("--target-path")
    o.add_argument("--severity", default="normal", choices=sorted(SEVERITIES))
    o.add_argument("--source", default="telegram")
    f = sub.add_parser("fix")
    f.add_argument("--issue", required=True)
    f.add_argument("--commit", required=True)
    f.add_argument("--desc", required=True)
    f.add_argument("--files", nargs="*")
    v = sub.add_parser("verify")
    v.add_argument("--issue", required=True)
    v.add_argument("--cmd", nargs="+", required=True)
    c = sub.add_parser("close")
    c.add_argument("--issue", required=True)
    c.add_argument("--closed-by", required=True,
                   choices=["mohamed_tap", "auto_verify_timeout", "target_retired"])
    a = ap.parse_args()
    try:
        if a.cmd == "open":
            e = open_issue(a.player, a.quote, a.reason_code, target=a.target,
                           target_path=a.target_path, severity=a.severity,
                           source=a.source, by="telegram" if a.source == "telegram" else "claude")
            print(f"📌 {e['issue_id']} {e['event']}")
        elif a.cmd == "fix":
            e = fix_claimed(a.issue, a.commit, a.desc, files=a.files)
            print(f"🔧 {a.issue} fix_claimed @ {a.commit[:9]}")
        elif a.cmd == "verify":
            e = verified(a.issue, a.cmd)
            print(f"✅ {a.issue} verified (حسب السكربت)")
        elif a.cmd == "close":
            e = close(a.issue, a.closed_by)
            print(f"🔒 {a.issue} closed by {a.closed_by}")
    except ValueError as err:
        print(f"🛑 REFUSED: {err}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
