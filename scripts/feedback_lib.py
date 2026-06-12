#!/usr/bin/env python3
"""FEEDBACK GRAMMAR — the one source of names (June 12, Mohamed: "receive judgment in
ALL aspects: rabie, you, the system, the minds, the summary").

ONE regex, ONE validate_target(), ONE player roster — every writer imports this module;
nothing duplicates the names (the players come from MINDS + portal_team.json, never a
parallel players.json — the one-module law).

Target grammar:
  PLAYERS    claude | rabie | mind:<id in MINDS> | judge:<id in portal_team> | system:<script>
  ARTIFACTS  card:<id> | caption:<id> | post:<id> | batch:<id> | summary:<id> |
             receipt:<id> | report:<id> | session:<id> | portal:<id>

OGZ_BASE env overrides the repo root (the test harness runs in a sandbox)."""
import fcntl
import json
import os
import re
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent.parent


def base() -> Path:
    return Path(os.environ["OGZ_BASE"]) if os.environ.get("OGZ_BASE") else REPO


PLAYER_RE = re.compile(r"^(claude|rabie|mind:[a-z_]+|judge:[a-z_]+|system:[a-zA-Z0-9_.\-]+)$")
ARTIFACT_RE = re.compile(r"^(card|caption|post|batch|summary|receipt|report|session|portal):[A-Za-z0-9_.\-]+$")
EPHEMERAL_KINDS = {"summary", "receipt", "report"}      # staleness never applies
FORBIDDEN_FIELDS = {"quality_score", "auto_score", "ai_score", "sentiment"}  # no fabricated metrics, ever


def mind_ids() -> set:
    """The minds roster — imported from minds.py, never duplicated."""
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    from minds import MINDS
    return set(MINDS)


def judge_ids() -> set:
    f = base() / "data/portal_team.json"
    if not f.exists():
        return {"mohamed"}
    return {m["id"] for m in json.loads(f.read_text()).get("members", [])}


def validate_target(t: str) -> bool:
    """True iff t is a grammar-valid player or artifact reference with a REAL name."""
    if not t or not isinstance(t, str):
        return False
    if ARTIFACT_RE.match(t):
        return True
    if not PLAYER_RE.match(t):
        return False
    if t.startswith("mind:"):
        return t.split(":", 1)[1] in mind_ids()
    if t.startswith("judge:"):
        return t.split(":", 1)[1] in judge_ids()
    return True   # claude | rabie | system:<anything sane>


def is_player(t: str) -> bool:
    return bool(t) and bool(PLAYER_RE.match(t)) and validate_target(t)


def producer_map() -> dict:
    f = base() / "data/producer_map.json"
    return json.loads(f.read_text()) if f.exists() else {}


def producer_allows(via: str, made_by: str) -> bool:
    """TRUTH check, not form check: may this producing script claim this made_by?
    (the defense against Claude stamping its own weak output made_by:mind:firaasa)"""
    allowed = producer_map().get(via)
    if allowed is None:
        return False
    for pat in allowed:
        if pat == made_by or (pat.endswith("*") and made_by.startswith(pat[:-1])):
            return True
    return False


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def append_jsonl(path: Path, entry: dict):
    """The one append primitive: flocked, atomic-ish, newline-terminated."""
    for k in FORBIDDEN_FIELDS & set(entry):
        raise ValueError(f"forbidden field {k} in a truth ledger (the AI-judge law)")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        fcntl.flock(f, fcntl.LOCK_UN)


def classify_receipt(entry: dict) -> dict:
    """What this judgment BECOMES — one deterministic source of truth shared by the
    portal response, the router, and the end screen (they can never drift).
    Honest tense: 'will_*' = the cron/receipt fold does it, not already done."""
    a = str(entry.get("answer", "")).strip().lower()
    fix = bool((entry.get("fix") or "").strip())
    rating = entry.get("rating")
    rejected = a in ("rejected", "flagged") or (isinstance(rating, int) and rating <= 2)
    return {
        "kind": ("corrected" if fix else "rejected" if rejected
                 else "approved" if a == "approved" else "answered"),
        "will_open_case": rejected or fix,
        "correction_captured": fix,
        "gold_candidate": a == "approved" and isinstance(rating, int) and rating >= 4
                          and bool(entry.get("artifact_id")),
        "player": entry.get("target") or None,
    }


def read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue   # a torn line never kills a reader; make_sure catches truncation
    return out
