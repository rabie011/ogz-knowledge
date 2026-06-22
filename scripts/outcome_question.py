#!/usr/bin/env python3
"""MONTHLY OWNER-OUTCOME QUESTION GENERATOR (B095, L4 Bedrock) — the qualitative half of the full circle.

THE FULL CIRCLE (Rule #5.9): the system PRODUCES → Mohamed JUDGES → the post goes live → its outcome
flows back. B094 (outcome_receipt.py) reads the QUANTITATIVE outcome (T+7d countables vs own baseline).
This is the QUALITATIVE half: once a month it asks the brand OWNER one felt-difference question —
«هل حسّيتي بفرق بالطلبات؟ أكثر / نفس الشي / أقل» — the signal numbers can't capture.

TWO HALVES, BOTH BUILT THIS STEP (Consumer Law, Rule #6 — a writer with no reader is a lie):
  WRITER  generate_questions(now): for each brand live >= a month whose last question is >= a month old,
          STAGES one button-card (status pending_mohamed_approval). It is NEVER auto-sent — the actual
          client-facing send rides Mohamed's approval (Rule #7: the tap that sends is his alone).
  READER  record_answer(...): the CONSUMER of the card's answer. Accepts only the three allowed options
          (refuses anything else — Rule #8), and appends an owner_felt_outcome event to owner_outcomes.jsonl.

DELIBERATE DESIGN (matches outcome_receipt.py):
  - The question instrument is a FIXED constant (the specified survey, not authored content — Rule #12).
  - "Live since" = a brand's EARLIEST published piece (data/published.jsonl). Empty ledger → 0 eligible,
    honest "nothing to ask" (Pre-Build Q2), never a crash.
  - event_ulid is DETERMINISTIC from (brand, period) → idempotent: a brand is asked at most once per
    monthly period; re-runs emit 0 new cards.
  - No Date.now() in the source path — `now` is injected so tests are deterministic.

Usage:
  python3 scripts/outcome_question.py            # stage due questions; append to ledger; print report
  python3 scripts/outcome_question.py --dry-run  # report only, write nothing
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent
PUBLISHED_LEDGER = BASE / "data/published.jsonl"
QUESTIONS_LEDGER = BASE / "data/outcome_questions.jsonl"   # staged cards (writer output)
ANSWERS_LEDGER = BASE / "data/owner_outcomes.jsonl"        # recorded answers (reader output)

PERIOD_DAYS = 28          # monthly cadence: live >= this, and last question >= this old
ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

# THE FIXED INSTRUMENT (the specified survey question — a measurement organ, not authored creative).
QUESTION_TEXT = "هل حسّيتي بفرق بالطلبات؟"
# canonical answer key → the Arabic label the owner taps. The ONLY accepted answers (Rule #8 gate).
ANSWER_OPTIONS = {"more": "أكثر", "same": "نفس الشي", "less": "أقل"}


def deterministic_ulid(seed: str) -> str:
    """Deterministic 26-char Crockford-base32 ULID from a seed (mirrors outcome_receipt.py)."""
    val = int(hashlib.sha256(seed.encode()).hexdigest()[:32], 16)
    out = []
    for _ in range(26):
        out.append(ULID_ALPHABET[val % 32])
        val //= 32
    return "".join(reversed(out))


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            rows.append(json.loads(ln))
    return rows


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _scope(brand: str) -> str:
    # provenance_mixin scope pattern: brand:<lowercase slug> (never the bare word)
    return "brand:" + re.sub(r"[^a-z0-9_]", "_", str(brand).lower())


def generate_questions(now: datetime | None = None, dry_run: bool = False) -> dict:
    """Stage one monthly owner-outcome card per eligible brand. Returns a report dict; appends new
    staged cards to QUESTIONS_LEDGER unless dry_run. `now` is injectable for deterministic tests."""
    now = now or datetime.now(timezone.utc)

    published = _read_jsonl(PUBLISHED_LEDGER)
    # live-since = earliest published timestamp per brand
    live_since: dict[str, datetime] = {}
    for pub in published:
        brand, ts = pub.get("brand_ulid"), pub.get("timestamp")
        if not (brand and ts):
            continue  # malformed publish row — skip, never guess
        t = _parse_ts(ts)
        if brand not in live_since or t < live_since[brand]:
            live_since[brand] = t

    # last question asked per brand (most recent period_start in the ledger)
    existing = _read_jsonl(QUESTIONS_LEDGER)
    last_asked: dict[str, datetime] = {}
    for q in existing:
        brand, ps = q.get("brand_ulid"), q.get("period_start")
        if not (brand and ps):
            continue
        t = _parse_ts(ps)
        if brand not in last_asked or t > last_asked[brand]:
            last_asked[brand] = t

    new_cards, skipped = [], []
    for brand, since in sorted(live_since.items()):
        age_days = (now - since).total_seconds() / 86400.0
        if age_days < PERIOD_DAYS:
            skipped.append({"brand_ulid": brand, "reason": "not_live_a_month",
                            "age_days": round(age_days, 1)})
            continue
        last = last_asked.get(brand)
        if last is not None and (now - last).total_seconds() / 86400.0 < PERIOD_DAYS:
            skipped.append({"brand_ulid": brand, "reason": "asked_this_period",
                            "days_since": round((now - last).total_seconds() / 86400.0, 1)})
            continue

        # period index from live-since → deterministic, idempotent within a month
        period_idx = int(age_days // PERIOD_DAYS)
        period_start = now  # the card opens now; period_idx makes the id unique per month
        card = {
            "event_ulid": deterministic_ulid(f"owner_q:{brand}:{period_idx}"),
            "event_type": "owner_outcome_question",
            "id": f"owner_outcome_{re.sub(r'[^a-z0-9]', '_', str(brand).lower())}_p{period_idx}",
            "brand_ulid": brand,
            "period_start": period_start.isoformat(),
            "period_idx": period_idx,
            "question": QUESTION_TEXT,
            "options": [{"v": k, "label": v} for k, v in ANSWER_OPTIONS.items()],
            "kind": "buttons",
            "audience": "client_owner",
            "status": "pending_mohamed_approval",   # NEVER auto-sent — the send is his tap (Rule #7)
            "provenance": {
                "source": "outcome_question.py (B095)",
                "date_added": now.date().isoformat(),
                "confirmer": "system",
                "confidence": "experimental",
                "scope": _scope(brand),
            },
        }
        new_cards.append(card)

    report = {
        "brands_live": len(live_since),
        "new_cards": len(new_cards),
        "cards": new_cards,
        "skipped": skipped,
        "dry_run": dry_run,
    }

    if new_cards and not dry_run:
        with QUESTIONS_LEDGER.open("a", encoding="utf-8") as fh:
            for c in new_cards:
                fh.write(json.dumps(c, ensure_ascii=False) + "\n")

    return report


def record_answer(brand_ulid: str, period_idx: int, answer: str,
                  now: datetime | None = None, dry_run: bool = False) -> dict:
    """THE CONSUMER (Rule #6/#7): record the owner's tapped answer. `answer` must be one of the three
    canonical keys (more/same/less) — anything else is REFUSED (Rule #8), never silently coerced.
    Appends an owner_felt_outcome event to ANSWERS_LEDGER (idempotent per brand+period). Returns the event."""
    now = now or datetime.now(timezone.utc)
    if answer not in ANSWER_OPTIONS:
        raise ValueError(
            f"REFUSED: '{answer}' is not an allowed owner-outcome answer "
            f"(must be one of {sorted(ANSWER_OPTIONS)}) — no silent coercion (Rule #8).")

    event_ulid = deterministic_ulid(f"owner_a:{brand_ulid}:{period_idx}")
    # idempotent: do not re-record the same brand+period answer
    for e in _read_jsonl(ANSWERS_LEDGER):
        if e.get("event_ulid") == event_ulid:
            return e

    event = {
        "event_ulid": event_ulid,
        "event_type": "owner_felt_outcome",
        "timestamp": now.isoformat(),
        "brand_ulid": brand_ulid,
        "period_idx": period_idx,
        "answer": answer,                       # canonical key
        "answer_label": ANSWER_OPTIONS[answer],  # the Arabic label the owner saw
        "provenance": {
            "source": "outcome_question.py (B095) record_answer",
            "date_added": now.date().isoformat(),
            "confirmer": "client_owner",
            "confidence": "experimental",
            "scope": _scope(brand_ulid),
        },
    }
    if not dry_run:
        with ANSWERS_LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def _print(report: dict) -> None:
    print("── MONTHLY OWNER-OUTCOME QUESTION GENERATOR (B095)")
    print(f"  brands live         : {report['brands_live']}")
    print(f"  new cards staged    : {report['new_cards']}"
          + ("  (dry-run, not written)" if report["dry_run"] else ""))
    for c in report["cards"]:
        print(f"  • {c['brand_ulid']}  p{c['period_idx']}  «{c['question']}»  "
              f"[{' / '.join(o['label'] for o in c['options'])}]  → pending Mohamed's approval")
    for s in report["skipped"]:
        print(f"    – {s['brand_ulid']} skipped ({s['reason']})")
    if not report["brands_live"]:
        print("  (no published pieces yet — nothing to ask; the reader is live, awaiting the publish writer)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="report only; write nothing")
    args = ap.parse_args()
    _print(generate_questions(dry_run=args.dry_run))
