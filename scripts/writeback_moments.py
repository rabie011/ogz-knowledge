#!/usr/bin/env python3
"""B084 — writeback_moments.py: approved angles compound the idea well (June 19, RABIE's pick).

Every angle Mohamed says YES to (rating >=4 on a HUMAN-confirmed ledger event) is appended to
that client's profile/moments_bank.json — the well the renderer draws variety from
(render_client_slot.py:280, year_map.py, client_strategy.py all read it). "The bank compounds
with every YES."

HUMAN HANDS ONLY (B156, mirrors writeback_replay): the moments bank feeds the producer, so only a
HUMAN confirmer (mohamed/alhareth/client) moves it. A PROVISIONAL RABIE rating — even rating 5 —
NEVER compounds into the renderer's well; it waits for Mohamed. This is why all current
occasion_gold (rabie_provisional) events write back NOTHING while the 3 pick_selected (mohamed)
events do.

PROVENANCE (Rule #9, no invented facts): each written moment cites its originating event by a
stable content key in provenance.source ("approved_angle:<key>") — ledger events carry no ULID, so
we mirror writeback_replay's content-key convention rather than inventing one. confidence=confirmed
because a human confirmed it.

IDEMPOTENT BY DESIGN (mirrors writeback_replay): the bank is recomputed from the FULL ledger every
run; a moment is skipped if its content key already cites an existing moment OR its evidence[:50]
already appears (the mine_moments dedup convention). Re-running yields the same bank and appends no
new writeback event. Every applied add appends a deduped event to events/writeback.jsonl — the human
ledger stays human-hands-only (B156).

REFUSE, DON'T WARN (Rule #8): the new bank is validated against client_moments_bank_v1 BEFORE it
touches disk; a contract breach raises (never half-writes a malformed organ).

CONSUMER (Rule #6 — a writer ships with its reader): moments_bank is already read by the renderer,
the year map, and the strategy organ — the wire is live, not severed.

Usage:
    python3 scripts/writeback_moments.py                 # every pilot client
    python3 scripts/writeback_moments.py --handle albaik
    python3 scripts/writeback_moments.py --dry-run       # report, write nothing
"""
import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).parent.parent

# Trust moves on human hands only (B156 / approvers_registry.HUMANS). Provisional RABIE ratings
# never compound into the renderer's well.
HUMANS = {"mohamed", "alhareth", "client"}


def _occasion_and_evidence(ev: dict):
    """Map an approved-angle event to (occasion, evidence), or (None, None) if it is not one.
    pick_selected.subject = 'DATE__occasion → angle', evidence = the chosen caption (note).
    occasion_gold.subject = the occasion, evidence = the gold line."""
    t = ev.get("type")
    if t == "pick_selected":
        subj = ev.get("subject", "") or ""
        occ = subj.split("__", 1)[1] if "__" in subj else subj
        occ = (occ.split("→")[0].strip() or "evergreen")
        evidence = (ev.get("note") or "").strip()
    elif t == "occasion_gold":
        occ = (ev.get("subject") or "evergreen").strip()
        evidence = (ev.get("line") or "").strip()
    else:
        return None, None
    if not evidence:
        return None, None
    return occ[:40], evidence[:200]


def _moment_key(handle: str, occasion: str, evidence: str) -> str:
    raw = f"{handle}|{occasion}|{evidence[:80]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def derive_moments(handle: str, events: list, bank: dict):
    """PURE core — no IO, no clock. Returns (new_bank, changes). A moment is written back ONLY for a
    HUMAN-confirmed angle rated >=4 (B156). Dedup by content key (provenance.source) AND evidence[:50]
    (mine_moments convention). Provenance.date_added = the EVENT's own ts (clock-free, more honest)."""
    moments = [dict(m) for m in bank.get("moments", [])]
    seen_keys = set()
    for m in moments:
        prov = m.get("provenance") or {}
        src = str(prov.get("source", ""))
        if src.startswith("approved_angle:"):
            seen_keys.add(src.split("approved_angle:", 1)[1])
    seen_ev = {(m.get("evidence") or "")[:50] for m in moments}

    changes = []
    for ev in events:
        r = ev.get("rating")
        if not (isinstance(r, (int, float)) and not isinstance(r, bool) and r >= 4):
            continue
        if ev.get("confirmer") not in HUMANS:
            continue
        occasion, evidence = _occasion_and_evidence(ev)
        if not occasion or not evidence:
            continue
        key = _moment_key(handle, occasion, evidence)
        if key in seen_keys or evidence[:50] in seen_ev:
            continue
        seen_keys.add(key)
        seen_ev.add(evidence[:50])
        moments.append({
            "occasion": occasion,
            "evidence": evidence,
            "provenance": {
                "source": f"approved_angle:{key}",
                "date_added": (ev.get("ts") or "")[:10],
                "confirmer": ev.get("confirmer"),
                "confidence": "confirmed",
                "scope": "brand",
            },
        })
        changes.append({"occasion": occasion, "key": key, "confirmer": ev.get("confirmer"),
                        "ts": (ev.get("ts") or "")[:10]})

    new_bank = dict(bank)
    new_bank["moments"] = moments
    return new_bank, changes


_SCHEMA = None


def _schema():
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads((BASE / "12_data_shapes/client_moments_bank_v1.schema.json").read_text())
    return _SCHEMA


def _read_ledger(path: Path) -> list:
    events = []
    if path.exists():
        for ln in path.read_text().splitlines():
            ln = ln.strip()
            if ln:
                try:
                    events.append(json.loads(ln))
                except Exception:
                    pass
    return events


def _load_writeback_keys(handle: str) -> set:
    wf = BASE / "clients" / handle / "events/writeback.jsonl"
    if not wf.exists():
        return set()
    keys = set()
    for ln in wf.read_text().splitlines():
        try:
            keys.add(json.loads(ln).get("key"))
        except Exception:
            pass
    return keys


def writeback_client(handle: str, dry_run: bool = False) -> dict:
    mf = BASE / "clients" / handle / "profile/moments_bank.json"
    if not mf.exists():
        return {"handle": handle, "skipped": "no moments_bank", "changes": []}

    bank = json.loads(mf.read_text())
    events = _read_ledger(BASE / "clients" / handle / "events/ledger.jsonl")
    new_bank, changes = derive_moments(handle, events, bank)

    if dry_run or not changes:
        return {"handle": handle, "changes": changes, "wrote": False}

    # Rule #8 — validate BEFORE writing; raise (never half-write a malformed organ).
    import jsonschema
    jsonschema.validate(new_bank, _schema())

    from organ_write import write_organ
    write_organ(mf, new_bank)

    # every applied add → a deduped writeback event (NOT the human ledger)
    seen = _load_writeback_keys(handle)
    wf = BASE / "clients" / handle / "events/writeback.jsonl"
    wf.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(wf, "a") as f:
        for ch in changes:
            if ch["key"] in seen:
                continue
            seen.add(ch["key"])
            # This is a MACHINE audit record, not a human tap — so confirmer is the system and the
            # human who approved the underlying angle is preserved in source_confirmer. (If it carried
            # confirmer="mohamed" the events-integrity audit would read it as his decision left
            # provisional — verify_events_wired, B121.) The human attribution that consumers read
            # lives on the moment's own provenance.confirmer.
            f.write(json.dumps({
                "ts": ch.get("ts", ""),
                "type": "writeback_moment_added",
                "subject": ch["occasion"],
                "confirmer": "writeback_moments",
                "source_confirmer": ch.get("confirmer"),
                "stamp": "DERIVED (writeback_moments)",
                "source": "writeback_moments",
                "key": ch["key"],
            }, ensure_ascii=False) + "\n")
            written += 1
    return {"handle": handle, "changes": changes, "wrote": True, "events_appended": written}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", help="one client; default = all pilots")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.handle:
        handles = [args.handle]
    else:
        handles = sorted(p.name for p in (BASE / "clients").iterdir()
                         if p.is_dir() and (p / "profile/moments_bank.json").exists())

    total = 0
    for h in handles:
        r = writeback_client(h, dry_run=args.dry_run)
        n = len(r.get("changes", []))
        total += n
        tag = "DRY" if args.dry_run else ("WROTE" if r.get("wrote") else "no-op")
        if r.get("skipped"):
            tag = "skip:" + r["skipped"]
        print(f"  {h}: {n} approved-angle moment(s) [{tag}]")
    print(f"\n✓ moments writeback: {total} approved angle(s) across {len(handles)} client(s)")


if __name__ == "__main__":
    main()
