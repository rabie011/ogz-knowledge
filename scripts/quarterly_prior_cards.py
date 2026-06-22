#!/usr/bin/env python3
"""QUARTERLY PRIOR CARDS GENERATOR (B099, L4 Bedrock) — turn promoted sector-prior DRAFTS into
≤5 yes/no cards for Mohamed, once a quarter.

THE TOP it serves: the system that CAPTURES Mohamed's taste. The sector-prior aggregator (B096)
stages PROVISIONAL drafts the moment ≥3 distinct brands confirm a value (data/sector_prior_drafts.json).
A draft is a machine PROPOSAL — it only becomes a sector law when Mohamed says yes. This generator is
the bridge from proposal to his tap: it shapes each promoted draft into ONE clean yes/no card and
stages a quarter's batch (≤5) as the consumable artifact. His tap is the calibration fuel the taste
bridge is starved for.

THE LAWS this obeys (all from CLAUDE.md, learned in pain):
- Rule #11 (≤5, don't flood the 60-second gate): at most 5 cards per quarter; strongest first
  (most confirming brands). If more than 5 drafts qualify, the overflow is LOGGED, never dropped
  silently (Rule #10 — no silent cap), and carried to the next quarter.
- Rule #10 (don't flood): ONE batch per quarter. A quarter already generated HOLDs (idempotent) —
  re-running never re-pushes the same cards. `--force` overrides for testing only.
- Rules #7 + #11 (pre-wire the tap; promotion via human-merged PR): every button value this
  generator offers MUST be in ANSWER_HANDLERS — a value with no consumer is REFUSED (Rule #8, the
  gate bites). A YES never auto-promotes; it records "awaiting_pr". The spec change lands only via a
  human-merged PR (Rule #12 — the System Produces, a human applies).
- Rule #6 (the writer needs a reader): `consume_answers` is built in this same module and tested
  end-to-end; the staged cards artifact is read back by the test.
- Rule #9 (never manufacture work): 0 promoted drafts → 0 cards + an honest HOLD note. Correct, not
  a bug — the aggregator gate held upstream.

Usage:
  python3 scripts/quarterly_prior_cards.py            # generate this quarter's batch (idempotent)
  python3 scripts/quarterly_prior_cards.py --force    # regenerate even if the quarter already ran
  python3 scripts/quarterly_prior_cards.py --show      # print the staged batch, generate nothing
"""
import argparse
import datetime
import json
import re
from pathlib import Path

B = Path(__file__).parent.parent
DRAFTS = B / "data/sector_prior_drafts.json"
CARDS = B / "data/prior_cards.json"
DECISIONS = B / "data/prior_card_decisions.json"

MAX_CARDS = 5  # Rule #11 — the 60-second gate holds at most 5 yes/no cards.

# Rule #7 — the ONLY button values this generator may offer; each is handled by consume_answers.
# Offering any other value is a pre-wire violation and is REFUSED (Rule #8).
ANSWER_HANDLERS = {"approve_prior", "reject_prior"}


def quarter_key(now=None):
    """Deterministic quarter label, e.g. '2026-Q2'. `now` is injectable for tests."""
    now = now or datetime.datetime.now()
    return f"{now.year}-Q{(now.month - 1) // 3 + 1}"


def _slug(*parts):
    raw = "_".join(str(p) for p in parts).lower()
    return re.sub(r"[^a-z0-9]+", "_", raw).strip("_")


def build_cards(drafts, max_cards=MAX_CARDS):
    """Shape promoted drafts into yes/no cards. Returns (cards, dropped).

    Strongest first (most confirming brands). Caps at max_cards; the overflow is RETURNED as
    `dropped` so the caller logs it (Rule #10), never silently swallowed. REFUSES (raises) if any
    button value lacks a consumer (Rule #7)."""
    ranked = sorted(
        drafts,
        key=lambda d: (-d.get("n_brands", 0), d.get("sector", ""), d.get("field", "")),
    )
    cards = []
    for d in ranked:
        n = d.get("n_brands", 0)
        sector, field = d.get("sector", "?"), d.get("field", "?")
        value = d.get("value")
        target = d.get("target_sector_default") or d.get("target_cultural_spec") or "(sector spec)"
        card = {
            "id": _slug("prior", sector, field),
            "tag": "sector_prior",
            "title": f"Sector prior · {sector} · {field}",
            # English for Mohamed's cards (portal convention); the value shown verbatim.
            "desc": (
                f"{n} distinct brands in '{sector}' confirmed {field} = {value!r}. "
                f"Make it a sector prior?  YES → staged for a human-merged PR to {target} "
                f"(Rules 7+11: no auto-promotion). NO → dropped."
            ),
            "buttons": [
                {"value": "approve_prior", "label": "✅ Yes — make it a sector prior"},
                {"value": "reject_prior", "label": "❌ No"},
            ],
            "consumer": "scripts/quarterly_prior_cards.py:consume_answers",
            "source_draft": {"sector": sector, "field": field, "value": value, "n_brands": n},
            "status": "STAGED",  # never live until a human/the orchestra pushes it
        }
        # Rule #7 — pre-wire the tap: every offered value must have a handler, or REFUSE.
        for btn in card["buttons"]:
            if btn["value"] not in ANSWER_HANDLERS:
                raise ValueError(
                    f"card {card['id']} offers unhandled value {btn['value']!r} (Rule #7)"
                )
        cards.append(card)
    return cards[:max_cards], cards[max_cards:]


def consume_answers(answers, now=None):
    """THE READER (Rule #6). Take Mohamed's taps and record decisions — NEVER mutate a spec.

    `answers`: list of {"id", "value"} where value ∈ ANSWER_HANDLERS. approve_prior → recorded
    'awaiting_pr' (the spec change lands via a human-merged PR, Rule #12 — NOT applied here).
    reject_prior → 'rejected'. An unhandled value is REFUSED (Rule #8)."""
    out = []
    for a in answers:
        v = a.get("value")
        if v not in ANSWER_HANDLERS:
            raise ValueError(f"unhandled answer value {v!r} for card {a.get('id')!r} (Rule #7)")
        out.append({
            "id": a.get("id"),
            "value": v,
            "outcome": "awaiting_pr" if v == "approve_prior" else "rejected",
            "applied": False,  # Rule #12 — a human/PR applies; this reader never does.
            "decided_at": (now or datetime.datetime.now()).isoformat(timespec="seconds"),
        })
    return out


def stage_cards(cards, dropped, quarter, path=CARDS, now=None):
    """Stage the quarter's batch as the consumable artifact (Rule #6). Provisional staging only."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "quarter": quarter,
        "generated_at": (now or datetime.datetime.now()).isoformat(timespec="seconds"),
        "n_cards": len(cards),
        "n_dropped": len(dropped),
        "dropped_to_next_quarter": [d["source_draft"]["sector"] + "/" + d["source_draft"]["field"]
                                    for d in dropped],
        "cards": cards,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _load_drafts(path=DRAFTS):
    if not Path(path).exists():
        return []
    return json.loads(Path(path).read_text(encoding="utf-8")).get("drafts", [])


def main():
    ap = argparse.ArgumentParser(description="Quarterly sector-prior cards generator (B099)")
    ap.add_argument("--force", action="store_true", help="regenerate even if the quarter already ran")
    ap.add_argument("--show", action="store_true", help="print the staged batch, generate nothing")
    args = ap.parse_args()

    qk = quarter_key()
    if args.show:
        if CARDS.exists():
            print(CARDS.read_text(encoding="utf-8"))
        else:
            print("(no staged batch yet)")
        return

    # Rule #10 — idempotent per quarter: never re-push the same quarter's cards.
    if CARDS.exists() and not args.force:
        existing = json.loads(CARDS.read_text(encoding="utf-8"))
        if existing.get("quarter") == qk:
            print(f"🟡 HOLD — {qk} batch already generated ({existing.get('n_cards', 0)} cards). "
                  f"Use --force to regenerate.")
            return

    drafts = _load_drafts()
    cards, dropped = build_cards(drafts)
    stage_cards(cards, dropped, qk)

    if not cards:
        print(f"🟡 HOLD — {qk}: 0 promoted drafts → 0 cards. Correct (the aggregator gate held "
              f"upstream — <3 distinct brands on any value), not a bug.")
        return
    print(f"✅ {qk}: staged {len(cards)} prior card(s) → {CARDS.relative_to(B)}")
    for c in cards:
        print(f"   • {c['id']}  ({c['source_draft']['n_brands']} brands)")
    if dropped:
        print(f"⚠️  {len(dropped)} draft(s) over the 5-card cap, carried to next quarter "
              f"(Rule #10, not dropped): "
              f"{', '.join(d['source_draft']['sector'] + '/' + d['source_draft']['field'] for d in dropped)}")


if __name__ == "__main__":
    main()
