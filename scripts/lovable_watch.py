#!/usr/bin/env python3
"""lovable_watch.py — watch the Lovable design repo (~/ogz-website = clone-in-a-snap) for new
commits and land them in the harvest inbox, idempotently (B239, Ops & Memory).

Mohamed's dictionary: "take from lovable" = one-way harvest Lovable→design system. This is the
SENSOR for that pipeline: it git-fetches the repo, diffs origin/main against a last-seen-SHA state
file, and appends only the GENUINELY NEW commits to inbox/lovable-commits.md, then notifies Mira.

Idempotent by construction (Rule #6 — the state file is the consumer of its own writes): the second
run over an unchanged HEAD prints "no new commits" and appends NOTHING. Cold start (no state) records
a BASELINE at the current HEAD without flooding the inbox with the whole history — only commits that
land AFTER the watch began are reported as new.

Run:  python3 scripts/lovable_watch.py
Test: scripts/tests/test_lovable_watch.py (temp git repo, do_fetch=False — no network)."""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REPO = Path.home() / "ogz-website"
STATE = BASE / "data" / "lovable_watch_state.json"
INBOX = BASE / "inbox" / "lovable-commits.md"


def _git(repo, *args):
    """Run a git command in `repo`; return (rc, stdout). Never raises."""
    try:
        p = subprocess.run(["git", "-C", str(repo), *args],
                           capture_output=True, text=True, timeout=60)
        return p.returncode, p.stdout.strip()
    except Exception as e:
        return 1, f"__error__ {e}"


def _notify(msg):
    """Best-effort Mira ping — the watch's real job is the inbox + state; notify is a courtesy."""
    try:
        sys.path.insert(0, str(Path.home() / "agents"))
        import mira
        return bool(mira.mira_send(msg))
    except Exception:
        return False


def watch(repo=REPO, state_path=STATE, inbox_path=INBOX,
          do_fetch=True, ref=None, notify=True, now=None):
    """Core sensor. Returns a dict: {new, head, commits, baseline?, reason?}.

    do_fetch=False / ref="HEAD" let the test drive a local temp repo with no network.
    `ref` defaults to origin/main when present, else HEAD (so a fetch-less local repo still works)."""
    repo, state_path, inbox_path = Path(repo), Path(state_path), Path(inbox_path)
    if _git(repo, "rev-parse", "--git-dir")[0] != 0:
        return {"new": 0, "head": None, "commits": [], "reason": f"not a git repo: {repo}"}

    if do_fetch:
        _git(repo, "fetch", "--quiet", "origin")  # offline → ignored; we still read local refs

    if ref is None:
        ref = "origin/main" if _git(repo, "rev-parse", "--verify", "--quiet", "origin/main")[0] == 0 else "HEAD"

    rc, head = _git(repo, "rev-parse", ref)
    if rc != 0 or not head:
        return {"new": 0, "head": None, "commits": [], "reason": f"cannot resolve ref {ref}"}

    last_seen = None
    if state_path.exists():
        try:
            last_seen = json.loads(state_path.read_text()).get("last_seen_sha")
        except Exception:
            last_seen = None

    # Cold start: baseline at HEAD, never replay the whole history into the inbox.
    if not last_seen:
        _write_state(state_path, head, ref)
        _append_inbox(inbox_path, [], head, ref, baseline=True, now=now)
        print(f"lovable-watch: baseline set at {head[:8]} ({ref}) — watching from here.")
        return {"new": 0, "head": head, "commits": [], "baseline": True}

    if last_seen == head:
        print("lovable-watch: no new commits.")
        return {"new": 0, "head": head, "commits": []}

    # last_seen must be a real object reachable from ref to form a range; else baseline-reset to head.
    valid_range = (_git(repo, "cat-file", "-e", last_seen)[0] == 0 and
                   _git(repo, "merge-base", "--is-ancestor", last_seen, ref)[0] == 0)
    if valid_range:
        rc, out = _git(repo, "log", "--no-merges", "--pretty=format:%H%x09%h%x09%cI%x09%s",
                       f"{last_seen}..{ref}")
        commits = [_parse_log_line(ln) for ln in out.splitlines() if ln.strip()] if rc == 0 else []
    else:
        # The recorded SHA fell out of history (force-push/rebase) — re-baseline rather than lie.
        _write_state(state_path, head, ref)
        _append_inbox(inbox_path, [], head, ref, baseline=True, now=now,
                      note="previous SHA no longer in history — re-baselined")
        print(f"lovable-watch: previous SHA gone (rebase/force-push) — re-baselined at {head[:8]}.")
        return {"new": 0, "head": head, "commits": [], "baseline": True}

    if not commits:
        # HEAD moved but only merge commits / nothing loggable — advance state, append nothing.
        _write_state(state_path, head, ref)
        print("lovable-watch: head moved but no harvestable commits; state advanced.")
        return {"new": 0, "head": head, "commits": []}

    _append_inbox(inbox_path, commits, head, ref, baseline=False, now=now)
    _write_state(state_path, head, ref)
    msg = f"🎨 Lovable: {len(commits)} new commit(s) in clone-in-a-snap → inbox/lovable-commits.md"
    if notify:
        _notify(msg)
    print(f"lovable-watch: {len(commits)} new commit(s) appended → {inbox_path}")
    return {"new": len(commits), "head": head, "commits": commits}


def _parse_log_line(ln):
    parts = ln.split("\t")
    while len(parts) < 4:
        parts.append("")
    return {"sha": parts[0], "short": parts[1], "date": parts[2], "subject": parts[3]}


def _write_state(state_path, head, ref):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(
        {"last_seen_sha": head, "ref": ref, "updated": time.strftime("%Y-%m-%dT%H:%M:%S")},
        ensure_ascii=False, indent=2))


def _append_inbox(inbox_path, commits, head, ref, baseline=False, now=None, note=""):
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    ts = now or time.strftime("%Y-%m-%dT%H:%M:%S")
    if not inbox_path.exists():
        inbox_path.write_text("# Lovable harvest inbox — new commits in clone-in-a-snap "
                              "(one-way Lovable→design system)\n\n")
    with open(inbox_path, "a", encoding="utf-8") as f:
        if baseline:
            extra = f" — {note}" if note else ""
            f.write(f"## {ts} — watch baseline at `{head[:8]}` ({ref}){extra}\n\n")
            return
        f.write(f"## {ts} — {len(commits)} new commit(s) (head `{head[:8]}`, {ref})\n")
        for c in commits:
            f.write(f"- `{c['short']}` {c['subject']}  ({c['date']})\n")
        f.write("\n")


def main():
    res = watch()
    if res.get("reason"):
        print(f"lovable-watch: {res['reason']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
