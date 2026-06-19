#!/usr/bin/env python3
"""B082 — writeback_replay.py: the nightly replay core (June 19, RABIE's pick).

Replays each client's HUMAN-CONFIRMED ledger verdicts into DERIVED organ state:

  1. truth_pack — a `truth_confirmed` event promotes a matching product_candidate's
     provenance.confidence candidate→confirmed and lifts it into the `confirmed` list.
     (Covers "promote provenance confidences" + "confirm truth_pack".)

  2. taste.json kills — a verdict event carrying a `reason_code` that is a KNOWN
     founder_taste kill slug propagates that slug into the client's taste.kills.
     It NEVER invents a kill: only a slug that already exists in data/founder_taste.json
     and is carried in the STRUCTURED reason_code field (never parsed from free text) can
     propagate (Rule #9 — no metric/state from unverified substrings).

IDEMPOTENT BY DESIGN: derived additions are recomputed from the FULL ledger every run and
written only when they change (organ_write → versioned + atomic). Re-running yields the
same organs and no new events. Every applied change appends a writeback event to
events/writeback.jsonl (deduped by a content key) — the human ledger stays human-hands-only
(B156). Replay never invents, never double-applies.

CONSUMER (Rule #6 — a writer ships with its reader): the derived state this writes is read
downstream — taste.kills by the caption/visual guards, truth_pack.confirmed by the renderer
and truth guards. The output is consumed the same cycle; no severed wire.

Usage:
    python3 scripts/writeback_replay.py                 # replay every pilot client
    python3 scripts/writeback_replay.py --handle eatjurisha
    python3 scripts/writeback_replay.py --dry-run       # report changes, write nothing
"""
import argparse
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).parent.parent

# A verdict counts only if a HUMAN confirmed it. Provisional (RABIE) verdicts and machine
# rows never move derived state — trust moves on human hands only (B156, mirrors approvers).
_HUMAN_CONFIRMERS = {"mohamed", "client", "mohamed_client", "alhareth"}


def _norm(s) -> str:
    return (s or "").strip()


def _is_confirmed(ev: dict) -> bool:
    if ev.get("confirmer") in _HUMAN_CONFIRMERS:
        return True
    stamp = str(ev.get("stamp", "")).upper()
    # explicit human stamp; PROVISIONAL stamps are excluded
    return stamp.startswith("CONFIRMED BY") and "PROVISIONAL" not in stamp


def _founder_kill_vocab() -> set:
    """The ONLY kill slugs allowed to propagate — the confirmed founder vocabulary."""
    d = json.loads((BASE / "data/founder_taste.json").read_text())
    return {_norm(k.get("name")) for k in d.get("kills", []) if k.get("name")}


def _change_key(handle: str, kind: str, subject: str) -> str:
    raw = f"{handle}|{kind}|{subject}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def derive(events, truth_pack: dict, taste: dict, founder_kills: set):
    """PURE core — no IO, no clock. Returns (new_truth_pack, new_taste, changes).

    Deterministic and idempotent: it re-derives the additions from the full event list,
    so applying the result twice produces no further changes. `changes` is the list of
    derivations made *relative to the organs passed in*.
    """
    tp = json.loads(json.dumps(truth_pack))   # deep copy — never mutate caller's dict
    ts = json.loads(json.dumps(taste))
    changes = []

    candidates = tp.setdefault("product_candidates", [])
    confirmed = tp.setdefault("confirmed", [])
    confirmed_names = {_norm(c.get("name")) for c in confirmed}
    kills = ts.setdefault("kills", [])

    for ev in events:
        if not _is_confirmed(ev):
            continue
        etype = ev.get("type")
        subj = _norm(ev.get("subject"))

        # 1. truth_pack provenance promotion: truth_confirmed → candidate becomes confirmed
        if etype == "truth_confirmed" and subj:
            for cand in candidates:
                if _norm(cand.get("name")) != subj:
                    continue
                prov = cand.setdefault("provenance", {})
                if prov.get("confidence") != "confirmed":
                    prov["confidence"] = "confirmed"
                    prov["promoted_by"] = "writeback_replay"
                    changes.append({"kind": "provenance_promoted", "subject": subj,
                                    "confirmer": ev.get("confirmer")})
            if subj not in confirmed_names:
                confirmed.append({
                    "name": subj,
                    "source": "writeback:truth_confirmed",
                    "confirmer": ev.get("confirmer"),
                    "confidence": "confirmed",
                    "date": ev.get("ts"),
                })
                confirmed_names.add(subj)
                changes.append({"kind": "truth_confirmed", "subject": subj,
                                "confirmer": ev.get("confirmer")})

        # 2. taste kills propagation: a STRUCTURED reason_code that is a known founder kill
        rc = _norm(ev.get("reason_code"))
        if rc and rc in founder_kills and rc not in kills:
            kills.append(rc)
            changes.append({"kind": "kill_propagated", "subject": rc,
                            "confirmer": ev.get("confirmer")})

    return tp, ts, changes


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


def replay_client(handle: str, dry_run: bool = False) -> dict:
    pdir = BASE / "clients" / handle / "profile"
    tp_path, taste_path = pdir / "truth_pack.json", pdir / "taste.json"
    if not tp_path.exists() or not taste_path.exists():
        return {"handle": handle, "skipped": "missing organs", "changes": []}

    ledger = BASE / "clients" / handle / "events/ledger.jsonl"
    events = []
    if ledger.exists():
        for ln in ledger.read_text().splitlines():
            ln = ln.strip()
            if ln:
                try:
                    events.append(json.loads(ln))
                except Exception:
                    pass

    truth_pack = json.loads(tp_path.read_text())
    taste = json.loads(taste_path.read_text())
    founder_kills = _founder_kill_vocab()

    new_tp, new_taste, changes = derive(events, truth_pack, taste, founder_kills)
    if dry_run or not changes:
        return {"handle": handle, "changes": changes, "wrote": False}

    from organ_write import write_organ
    if new_tp != truth_pack:
        write_organ(tp_path, new_tp)
    if new_taste != taste:
        write_organ(taste_path, new_taste)

    # every applied change → a deduped writeback event (NOT the human ledger)
    seen = _load_writeback_keys(handle)
    wf = BASE / "clients" / handle / "events/writeback.jsonl"
    wf.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with open(wf, "a") as f:
        for ch in changes:
            key = _change_key(handle, ch["kind"], ch["subject"])
            if key in seen:
                continue
            seen.add(key)
            f.write(json.dumps({
                "type": "writeback_" + ch["kind"],
                "subject": ch["subject"],
                "confirmer": ch.get("confirmer"),
                "source": "writeback_replay",
                "key": key,
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
                         if p.is_dir() and (p / "profile/truth_pack.json").exists())

    total = 0
    for h in handles:
        r = replay_client(h, dry_run=args.dry_run)
        n = len(r.get("changes", []))
        total += n
        tag = "DRY" if args.dry_run else ("WROTE" if r.get("wrote") else "no-op")
        if r.get("skipped"):
            tag = "skip:" + r["skipped"]
        print(f"  {h}: {n} change(s) [{tag}]")
        for ch in r.get("changes", []):
            print(f"      → {ch['kind']}: {ch['subject']}")
    print(f"\nwriteback_replay: {total} derivation(s) across {len(handles)} client(s)"
          + (" (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
