#!/usr/bin/env python3
"""B282 — judge2_ledger_writer.py: his BATCH approvals finally reach the client ledger
(June 20, RABIE's pick — the make_sure detector surfaced its own severance).

THE SEVERED WIRE (Rule #6 — a writer needs its reader; here the READER had no WRITER):
Mohamed taps `approved` / rating>=4 on `judge2_<handle>_<date>` batch cards. Those taps land in
data/mohamed_answers.jsonl — and STOP there. Nothing turns them into a `client_approved` client
event, so writeback_moments (B084) starves: 49 positive judge2 approvals compound ZERO into the
moments well. intel_consumer_health.human_verdict_starvation surfaces it in make_sure.

THIS WRITER closes link one of the chain:
    his judge2 approve  →  client_approved ledger event  →  writeback_moments compounds the
    approved caption into profile/moments_bank.json  →  the renderer draws variety from his taste.

POSITIVE = the SAME predicate the detector counts (imported, never re-defined — Rule #3 / #9 single
source of truth): judge==mohamed, item_id startswith judge2_, and (answer in _POSITIVE_ANSWERS OR
rating>=4). All 49 become a `client_approved` event so the starvation clears; only the rating>=4
subset (13) seeds a MOMENT downstream — weak-but-approved YESes record trust without flooding the
well, exactly B084's contract.

NO INVENTED FACTS (Rule #9): the moment evidence is the post's OWN lead caption, read off disk
(clients/<handle>/posts/<date>__*.json, latest version). If no post is found, the event still lands
(trust moved) but carries no caption — we never fabricate one.

IDEMPOTENT (cursor/dedup): every event carries a stable `src_key`
(judge2|handle|date|variant|answer_ts). Re-running skips any src_key already in the ledger — same
input yields the same ledger, no duplicates.

REFUSE, DON'T WARN (Rule #8): each event is written through ledger_write, which validates against
client_event_v1 and gates the human confirmer (B156) BEFORE it touches disk — a malformed event
raises, never half-writes.

CONSUMER shipped same cycle (Rule #6): writeback_moments._occasion_and_evidence now consumes
`client_approved` (this commit). The wire is live end-to-end, not severed.

Usage:
    python3 scripts/judge2_ledger_writer.py --dry-run     # report, write nothing
    python3 scripts/judge2_ledger_writer.py               # land the events, then run writeback_moments
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

# Single source of truth for "positive" — imported from the DETECTOR so the writer and the make_sure
# count can never drift (Rule #3 consistency, Rule #9 verify-the-number).
from intel_consumer_health import _POSITIVE_ANSWERS  # noqa: E402

_ITEM_RE = re.compile(r"^judge2_(?P<handle>.+)_(?P<date>\d{4}-\d{2}-\d{2})(?:_(?P<variant>[A-Za-z0-9]+))?$")


def is_positive_judge2(row: dict) -> bool:
    """His POSITIVE judge2 batch approval — byte-for-byte the detector's predicate."""
    if row.get("judge") != "mohamed":
        return False
    if not str(row.get("item_id", "")).startswith("judge2_"):
        return False
    ans = str(row.get("answer", "")).strip().lower()
    rating = row.get("rating")
    return ans in _POSITIVE_ANSWERS or (isinstance(rating, int) and rating >= 4)


def parse_item_id(item_id: str):
    """judge2_<handle>_<YYYY-MM-DD>[_<variant>] → (handle, date, variant|None).
    Regex-anchors the ISO date so dotted handles (myfitness.sa) and _b variants both parse."""
    m = _ITEM_RE.match(str(item_id))
    if not m:
        return None, None, None
    return m.group("handle"), m.group("date"), m.group("variant")


def _version_rank(path: str) -> int:
    m = re.search(r"__v(\d+)\.json$", path)
    return int(m.group(1)) if m else 0


def resolve_post(handle: str, date: str, base: Path = BASE):
    """(occasion, caption) for a handle+date, read off disk — the LATEST version's lead caption.
    Returns (None, None) when no post exists (we never invent a caption — Rule #9)."""
    matches = glob.glob(str(base / "clients" / handle / "posts" / f"{date}__*.json"))
    if not matches:
        return None, None
    best = max(matches, key=lambda p: (_version_rank(p), p))
    try:
        post = json.loads(Path(best).read_text())
    except Exception:
        return None, None
    occasion = (post.get("slot") or {}).get("type") or "evergreen"
    caps = post.get("captions") or []
    caption = (caps[0] if caps else "").strip() or None
    return str(occasion)[:40], (caption[:200] if caption else None)


def build_event(row: dict, occasion, caption):
    """A HUMAN-confirmed client_approved event. subject mirrors pick_selected's
    'DATE__occasion → angle' shape so writeback_moments parses it with one shared branch.
    note = the approved caption (the evidence the moments well cites)."""
    handle, date, variant = parse_item_id(row.get("item_id", ""))
    ts = (row.get("ts") or "")[:10]
    occ = occasion or "evergreen"
    head = f"{date}__{occ}"
    subject = f"{head} → {caption[:80]}" if caption else f"{head} (no caption on disk)"
    src_key = f"judge2|{handle}|{date}|{variant or ''}|{row.get('ts','')}"
    ev = {
        "ts": ts,
        "type": "client_approved",
        "subject": subject,
        "confirmer": "mohamed",
        "stamp": "CONFIRMED BY MOHAMED (judge2 batch approve)",
        "src_key": src_key,
    }
    if caption:
        ev["note"] = caption          # evidence consumed by writeback_moments
    r = row.get("rating")
    if isinstance(r, int):
        ev["rating"] = r              # rating>=4 → seeds a moment; lower → trust only
    return handle, ev


def _existing_src_keys(handle: str, base: Path) -> set:
    lf = base / "clients" / handle / "events/ledger.jsonl"
    keys = set()
    if lf.exists():
        for ln in lf.read_text().splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                k = json.loads(ln).get("src_key")
            except Exception:
                continue
            if k:
                keys.add(k)
    return keys


def _read_answers(path: Path) -> list:
    rows = []
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return rows
    for ln in text.splitlines():
        ln = ln.strip()
        if ln:
            try:
                rows.append(json.loads(ln))
            except json.JSONDecodeError:
                continue
    return rows


def run(answers_path: Path = None, base: Path = BASE, writer=None, dry_run: bool = False) -> dict:
    """Consume positive judge2 approvals → client_approved events, IDEMPOTENTLY.
    `writer(handle, event)` is injectable (defaults to ledger_write) so the path is unit-testable
    without touching a real client ledger."""
    answers_path = answers_path or (base / "data/mohamed_answers.jsonl")
    if writer is None:
        from ledger_write import ledger_write as writer

    seen_by_handle = {}
    written, skipped_dup, skipped_phantom, no_caption = [], 0, 0, 0
    for row in _read_answers(answers_path):
        if not is_positive_judge2(row):
            continue
        handle, date, _variant = parse_item_id(row.get("item_id", ""))
        if not handle or not (base / "clients" / handle).is_dir():
            skipped_phantom += 1
            continue                                  # never write into a phantom client
        occasion, caption = resolve_post(handle, date, base)
        if not caption:
            no_caption += 1
        h, ev = build_event(row, occasion, caption)
        seen = seen_by_handle.setdefault(h, _existing_src_keys(h, base))
        if ev["src_key"] in seen:
            skipped_dup += 1
            continue
        seen.add(ev["src_key"])
        if not dry_run:
            writer(h, ev)
        written.append((h, ev["src_key"]))
    return {"written": len(written), "events": written, "skipped_dup": skipped_dup,
            "skipped_phantom": skipped_phantom, "no_caption": no_caption, "dry_run": dry_run}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    r = run(dry_run=a.dry_run)
    tag = "DRY" if a.dry_run else "WROTE"
    print(f"[{tag}] judge2→ledger: {r['written']} client_approved event(s); "
          f"{r['skipped_dup']} dup-skipped, {r['skipped_phantom']} phantom-skipped, "
          f"{r['no_caption']} without on-disk caption")
    for h, k in r["events"]:
        print(f"   + {h}: {k}")


if __name__ == "__main__":
    main()
