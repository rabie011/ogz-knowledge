#!/usr/bin/env python3
"""PRIOR DEMOTER (B098, L4 Bedrock) — keep sector priors ALIVE by demoting the stale ones.

THE TOP it serves: the system that PRODUCES posts. B096 (sector_prior_aggregator) PROMOTES a value
to a sector prior when ≥3 distinct brands CONFIRM it. This is the inverse half that makes priors a
LIVING system, not a one-way ratchet: when ≥3 distinct NEW clients CONSECUTIVELY OVERRIDE a prior's
default, that prior has lost the sector and earns demotion back to `confidence: experimental`. A
prior that no longer matches reality is a silent quality leak — every brief in its sector inherits
a default the market keeps rejecting. (Mohamed's law: "priors are alive.")

THE FLOOR (Rule #8 — the gate BITES, it does not warn): below `DEMOTE_THRESHOLD` distinct
consecutive overriding brands → HOLD, no demotion. A prior overridden once or twice is noise, not a
verdict on the sector.

NO INFLATION (Rule #9, the fresh-batch scar): the SAME client overriding a prior twice is still ONE
brand. The override streak counts DISTINCT brands, never record count — otherwise one loud client
could demote a sector law alone.

CONSECUTIVE ONLY ("3 in a row"): a single CONFIRMED `accept` (a client who kept the default) BREAKS
the streak and resets it to zero. Demotion requires an unbroken trailing run — a prior the sector
is *currently* rejecting, not one it rejected long ago and then re-accepted.

CONFIRMED ONLY (Rule #9): an override/accept with no confirmer in CONFIRMED_BY is an assumption, not
a fact. Unconfirmed events are DROPPED before counting — they neither extend nor break the streak.

ALREADY AT THE FLOOR: a prior already at `confidence: experimental` cannot be demoted further → no
draft (idempotent; we never manufacture a no-op demotion).

ANONYMIZED (mirror B096): the draft carries only the COUNT and anonymized brand tokens, never the
raw brand→override attribution — a sector signal is a shared truth, not a leak of who rejected what.

THE CONSUMER (Rule #6): this writer is NOT write-only. `write_demotions` stages drafts to
data/prior_demotions.json as PROVISIONAL proposals; the spec's confidence field is never mutated
here (the System Produces — Rule #12 — we stage, a human/PR applies). The draft IS the consumable
artifact, and the synthetic test reads it back end-to-end.
"""
import hashlib
import json
from pathlib import Path

B = Path(__file__).parent.parent
DEMOTIONS = B / "data/prior_demotions.json"
# Where override/accept events would land. Honest-empty on the 2-3 brand pilot (no file yet) — the
# machine fires the instant real client-vs-prior events start flowing here.
OVERRIDE_EVENTS = B / "events/prior_overrides.jsonl"

# An event's confirmer must be in this set to count as a fact (Rule #9). Mirrors B096.
CONFIRMED_BY = {"mohamed", "client", "owner"}

DEMOTE_THRESHOLD = 3   # Rule #8 floor: distinct CONSECUTIVE overriding brands required to demote.

FLOOR_CONFIDENCE = "experimental"   # demotion target + the level that cannot be demoted further.


def _anon(brand):
    """Anonymized, stable token for a brand — same brand → same token, never the raw name."""
    return "b_" + hashlib.sha1(str(brand).encode("utf-8")).hexdigest()[:8]


def consecutive_override_brands(events):
    """Pure core. Walk a prior's events in chronological order and return the ORDERED list of
    DISTINCT brands in the current TRAILING run of overrides.

    Each event: {"brand", "action": "override"|"accept", "confirmer", ...}.
    - a CONFIRMED `override` by a brand not already in the run → extends the run (Rule #9: a brand
      already in the run does not inflate it);
    - a CONFIRMED `accept` → BREAKS the run (resets to empty): the prior is no longer being
      consecutively rejected;
    - an UNCONFIRMED event, or any unknown action → DROPPED (Rule #9): neither extends nor breaks.
    """
    run = []          # ordered distinct brands in the current override run
    seen = set()
    for e in events:
        if e.get("confirmer") not in CONFIRMED_BY:
            continue                          # unconfirmed assumption — not a fact, ignored
        action = e.get("action")
        brand = e.get("brand")
        if action == "override" and brand:
            if brand not in seen:
                seen.add(brand)
                run.append(brand)
        elif action == "accept":
            run = []                          # streak broken — the sector accepted the prior
            seen = set()
        # any other action: ignored (does not touch the run)
    return run


def demote(prior, events, threshold=DEMOTE_THRESHOLD):
    """Return a PROVISIONAL demotion draft if the prior's trailing override run has ≥threshold
    distinct confirmed brands AND the prior is above the floor; else None (the gate bites, Rule #8).

    A prior: {"sector", "field", "value", "confidence", ...}.
    """
    if prior.get("confidence") == FLOOR_CONFIDENCE:
        return None                           # already at the floor — nothing to demote
    run = consecutive_override_brands(events)
    if len(run) < threshold:
        return None                           # Rule #8 — the gate bites
    return {
        "sector": prior.get("sector"),
        "field": prior.get("field"),
        "value": prior.get("value"),
        "from_confidence": prior.get("confidence"),
        "to_confidence": FLOOR_CONFIDENCE,
        "n_overrides": len(run),
        "brands_anon": sorted(_anon(b) for b in run),
        "status": "PROVISIONAL",              # never auto-applied; a PR/human lands it (Rule #12)
    }


def demote_all(priors, events_by_key, threshold=DEMOTE_THRESHOLD):
    """Run `demote` over every prior; return the list of demotion drafts (held priors excluded).

    `priors`: list of prior dicts. `events_by_key`: {(sector, field, value) -> [events]} — the
    override/accept history keyed to the prior it concerns. A prior with no events HOLDs.
    """
    drafts = []
    for p in priors:
        key = (p.get("sector"), p.get("field"), _vkey(p.get("value")))
        d = demote(p, events_by_key.get(key, []), threshold=threshold)
        if d is not None:
            drafts.append(d)
    # deterministic order: strongest rejection first, then stable by sector/field/value
    drafts.sort(key=lambda d: (-d["n_overrides"], d["sector"] or "", d["field"] or "",
                               json.dumps(d["value"], ensure_ascii=False, sort_keys=True)))
    return drafts


def _vkey(value):
    """Stable string key for a prior value so events can be matched to the prior they concern."""
    if isinstance(value, str):
        return value.strip().casefold()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def write_demotions(drafts, path=DEMOTIONS):
    """Stage demotion drafts as the consumable artifact (Rule #6 — the reader is the PR review / the
    test). Provisional staging only; spec confidence fields are never mutated here (Rule #12)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"n_demotions": len(drafts), "threshold": DEMOTE_THRESHOLD, "demotions": drafts}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_events(path=OVERRIDE_EVENTS):
    """Real source: read override/accept events from events/prior_overrides.jsonl and group them by
    (sector, field, value). On the 2-3 brand pilot the file does not exist yet → {} (honest empty,
    not a bug). The loader exists so the machine fires the instant real events start flowing."""
    path = Path(path)
    grouped = {}
    if not path.exists():
        return grouped
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue                          # a malformed line is dropped, never crashes the run
        key = (e.get("sector"), e.get("field"), _vkey(e.get("value")))
        grouped.setdefault(key, []).append(e)
    return grouped


def load_priors(path=DEMOTIONS.parent / "sector_prior_drafts.json"):
    """The priors at risk of demotion: the promoted drafts B096 staged (each a live sector prior).
    Honest-empty when none are promoted yet (the pilot today). Safe on missing/malformed file."""
    path = Path(path)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    priors = []
    for d in data.get("drafts", []):
        priors.append({
            "sector": d.get("sector"),
            "field": d.get("field"),
            "value": d.get("value"),
            "confidence": d.get("confidence", "confirmed"),   # a promoted prior is above the floor
        })
    return priors


def main():
    priors = load_priors()
    events = load_events()
    drafts = demote_all(priors, events)
    write_demotions(drafts)
    held = len(priors) - len(drafts)
    print(f"prior_demoter: {len(priors)} live prior(s) checked · {len(drafts)} demotion draft(s) · "
          f"{held} HELD above the {DEMOTE_THRESHOLD}-override floor (Rule #8)")
    if not drafts:
        print("  → 0 demotions: no prior has ≥3 distinct consecutive confirmed overrides yet "
              "(correct on a 2-3 brand pilot with no override events; the machine fires when they land).")


if __name__ == "__main__":
    main()
