#!/usr/bin/env python3
"""
index_freshness.py  — B261

Staleness checks for the 4 LIVE "learn-from" indexes that feed the producing
machine. If any of these silently ages out, the system keeps few-shotting from
stale gold / stale benchmarks and every post quietly degrades (the Rule #6
"writer with a dead reader" failure). This module surfaces that as a WARNING.

WARN-only by design (per backlog B261: "warns when ... >30d"). Staleness is an
aging-data advisory, not a correctness gate on output — a 31-day-old index must
not block a commit. So this never flips an exit code; it only reports.

Importable + side-effect-free so it can be unit-tested directly. Each index
carries its timestamp in a different place, so the config lists the dotted keys
to try in order, falling back to the file mtime when no embedded timestamp
exists.
"""
import json
import datetime
from pathlib import Path

BASE = Path(__file__).parent.parent

STALE_DAYS = 30

# name -> (relative path, [dotted timestamp keys to try in order])
# Empty key list = no embedded timestamp; fall back to file mtime.
LEARN_FROM_INDEXES = [
    ("accounts_index",
     "11_who_to_learn_from/accounts_index.json", []),
    ("target_accounts",
     "11_who_to_learn_from/target_accounts.json", ["updated_at"]),
    ("content_types_canonical_index",
     "11_who_to_learn_from/content_types_canonical_index.json", ["_meta.built"]),
    ("intelligence_layer",
     "11_who_to_learn_from/intelligence_layer.json", ["meta.updated_at", "meta.generated_at"]),
]


def _parse_ts(val):
    """Parse a timestamp that may be date-only ('2026-06-11'), ISO with 'Z',
    or ISO with offset/microseconds. Returns a naive-UTC datetime or None."""
    if not isinstance(val, str) or not val.strip():
        return None
    s = val.strip().replace("Z", "+00:00")
    dt = None
    try:
        dt = datetime.datetime.fromisoformat(s)
    except ValueError:
        try:
            dt = datetime.datetime.strptime(s[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    return dt


def _dig(d, dotted):
    """Walk a dotted path through nested dicts; None if any hop is missing."""
    cur = d
    for part in dotted.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def index_age(path, keys, now=None):
    """Return (age_days, source) for one index file, or (None, 'MISSING').
    source names the timestamp used: a dotted key, or 'file_mtime'."""
    now = now or datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    p = Path(path)
    if not p.exists():
        return (None, "MISSING")
    ts = None
    src = None
    try:
        d = json.loads(p.read_text())
    except Exception:
        d = None
    if isinstance(d, dict):
        for k in keys:
            ts = _parse_ts(_dig(d, k))
            if ts:
                src = k
                break
    if ts is None:
        ts = datetime.datetime.fromtimestamp(p.stat().st_mtime, datetime.timezone.utc).replace(tzinfo=None)
        src = "file_mtime"
    return ((now - ts).days, src)


def check_index_staleness(base=BASE, now=None, stale_days=STALE_DAYS,
                          indexes=LEARN_FROM_INDEXES):
    """Return a list of (name, age_days_or_None, source) for indexes that are
    MISSING or older than stale_days. Empty list = all fresh."""
    base = Path(base)
    stale = []
    for name, rel, keys in indexes:
        age, src = index_age(base / rel, keys, now=now)
        if src == "MISSING" or (age is not None and age > stale_days):
            stale.append((name, age, src))
    return stale


def format_warnings(stale, stale_days=STALE_DAYS):
    """Human-readable WARN lines for a stale list (never raises)."""
    lines = []
    for name, age, src in stale:
        if src == "MISSING":
            lines.append(f"⚠️  [STALE] {name}: file MISSING")
        else:
            lines.append(f"⚠️  [STALE] {name}: {age}d old (via {src}) — exceeds {stale_days}d")
    return lines


if __name__ == "__main__":
    stale = check_index_staleness()
    if stale:
        print(f"⚠️  {len(stale)} learn-from index(es) stale (>{STALE_DAYS}d):")
        for line in format_warnings(stale):
            print("   " + line)
    else:
        print(f"✅ All {len(LEARN_FROM_INDEXES)} learn-from indexes fresh (≤{STALE_DAYS}d)")
