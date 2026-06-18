#!/usr/bin/env python3
"""THE CRYSTALLIZE LOOP (cross-client learning — RABIE's pyramid addition, June 11).
Mohamed's Rule #4 step 7 (every pain becomes a permanent rule) applied across clients:
scan ALL clients' append-only event ledgers; any coded rejection reason appearing
≥3 times ACROSS clients drafts a kill/default-change card — queued to Mohamed as a
60-second yes/no. The machine drafts; only Mohamed crystallizes (no AI rule-making).

Codes counted (from the pyramid's rejection-recovery play):
  culture_breach | off_voice | wrong_goal | too_generic | factual_error | unexplained
Usage: python3 scripts/crystallize_loop.py            # scan + draft
"""
import json, glob, re, collections
from pathlib import Path

BASE = Path(__file__).parent.parent
import datetime as _dt
TODAY = str(_dt.date.today())
THRESHOLD = 3
CODES = {"culture_breach", "off_voice", "wrong_goal", "too_generic", "factual_error", "unexplained"}
STALE_DAYS = 14  # founder_taste >2 weeks behind his latest rating = the loop is broken (B114)
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _max_date_in(values) -> "_dt.date | None":
    """Newest YYYY-MM-DD found anywhere in the given strings (None if none)."""
    found = []
    for v in values:
        for m in _ISO_DATE.findall(str(v)):
            try:
                found.append(_dt.date.fromisoformat(m))
            except ValueError:
                continue
    return max(found) if found else None


def founder_taste_staleness() -> dict:
    """B114 tripwire: founder_taste.json IS the bar the critic judges against; it must be refreshed
    after every rating session. If his latest rating session is >STALE_DAYS newer than the freshest
    date stamped in founder_taste._meta, the WRITEBACK loop is broken — he keeps rating but the bar
    never moves. Pure dates, no LLM (Rule #9). Honest no-data semantics: a missing file or no live
    rating means nothing can be 'behind', so stale=False — we never manufacture an alarm."""
    tf = BASE / "data/founder_taste.json"
    if not tf.exists():
        return {"available": False, "stale": False, "reason": "no founder_taste.json"}
    try:
        meta = (json.loads(tf.read_text()) or {}).get("_meta", {})
    except Exception as e:
        return {"available": False, "stale": False, "reason": f"unreadable founder_taste: {str(e)[:60]}"}
    taste_date = _max_date_in(meta.values())
    if taste_date is None:
        return {"available": False, "stale": False, "reason": "no date stamped in founder_taste._meta"}

    # latest rating session = newest live pairwise pick (his fresh eye; seeds are historical)
    prefs = BASE / "data/pairwise_prefs.jsonl"
    rating_dates = []
    if prefs.exists():
        for line in prefs.read_text().splitlines():
            if not line.strip():
                continue
            try:
                p = json.loads(line)
            except Exception:
                continue
            if p.get("source") == "seed_from_ratings":
                continue
            d = _max_date_in([p.get("ts", "")])
            if d:
                rating_dates.append(d)
    if not rating_dates:
        return {"available": True, "stale": False, "taste_date": str(taste_date),
                "latest_rating_date": None, "gap_days": None, "reason": "no live rating session yet"}

    latest = max(rating_dates)
    gap = (latest - taste_date).days
    return {"available": True, "stale": gap > STALE_DAYS, "taste_date": str(taste_date),
            "latest_rating_date": str(latest), "gap_days": gap, "n_ratings": len(rating_dates),
            "reason": f"founder_taste {gap}d behind his latest rating (threshold {STALE_DAYS}d)"}


def scan() -> dict:
    """Count coded reasons across every client ledger. Returns code → [(client, ts, note)]."""
    hits = collections.defaultdict(list)
    for lf in glob.glob(str(BASE / "clients/*/events/*.jsonl")):
        client = Path(lf).parts[-3]
        for line in open(lf):
            try:
                e = json.loads(line)
            except Exception:
                continue
            code = e.get("reason_code")
            if code in CODES:
                hits[code].append({"client": client, "ts": e.get("ts"), "note": (e.get("note") or "")[:80]})
    return hits


def scan_operational() -> list:
    """D6 PREP (June 12, RABIE's pick): the loop was blind to OPERATIONAL scars —
    it read client ledgers only. Zoom-out findings triaged REAL (verified + fixed
    at source) are law candidates too: the full-circle law applied to the system
    itself, not only to client verdicts."""
    ml = BASE / "data/make_sure_log.jsonl"
    scars = []
    if not ml.exists():
        return scars
    for line in open(ml):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") != "zoom_out":
            continue
        for key, verdict in (e.get("triage") or {}).items():
            if str(verdict).upper().startswith("REAL"):
                scars.append({"key": key, "ts": e.get("ts"), "verdict": str(verdict)[:140]})
    return scars


def draft_operational_cards(scars: list) -> list:
    """One scar = one draft (already evidence-backed: cold eyes found it, we verified
    and fixed it). The machine drafts; only Mohamed crystallizes."""
    return [{"draft": f"operational law candidate: {s['key']} (zoom-out verified+fixed)",
              "evidence": [s],
              "proposed_action": "crystallize the fix as permanent law (CLAUDE.md rule / guard / gate)",
              "status": "DRAFT — Mohamed's yes/no only", "drafted": TODAY,
              "source": "operational_scar"} for s in scars]


def draft_cards(hits: dict) -> list:
    """≥THRESHOLD occurrences across ≥2 clients → a draft card for Mohamed. Never auto-applies."""
    cards = []
    for code, evs in hits.items():
        clients = {e["client"] for e in evs}
        if len(evs) >= THRESHOLD and len(clients) >= 2:
            cards.append({
                "draft": f"founder_taste candidate: recurring '{code}' ({len(evs)}x across {len(clients)} clients)",
                "evidence": evs[:5],
                "proposed_action": {"culture_breach": "new cultural default (strictest) — and park the theme",
                                      "too_generic": "new kill pattern from the common shape of these rejections",
                                      "factual_error": "truth-gate tightening at the failing node",
                                      "off_voice": "voice-law amendment proposal (hate-line candidates)",
                                      "wrong_goal": "goal-ratio gate tightening",
                                      "unexplained": "human call — pattern exists but reason unknown"}.get(code, "review"),
                "status": "DRAFT — Mohamed's yes/no only",
                "drafted": TODAY,
            })
    return cards


def main():
    hits = scan()
    total = sum(len(v) for v in hits.values())
    print(f"scanned ledgers: {len(glob.glob(str(BASE / 'clients/*/events/*.jsonl')))} files, {total} coded events")
    for code, evs in sorted(hits.items(), key=lambda kv: -len(kv[1])):
        print(f"  {code}: {len(evs)} ({len({e['client'] for e in evs})} clients)")
    cards = draft_cards(hits)
    scars = scan_operational()
    cards += draft_operational_cards(scars)
    print(f"  operational scars (zoom-out REAL): {len(scars)}")
    out = BASE / "data/crystallize_queue.json"
    existing = json.loads(out.read_text()) if out.exists() else {"cards": []}
    seen = {c["draft"] for c in existing["cards"]}
    new = [c for c in cards if c["draft"] not in seen]
    existing["cards"] += new
    existing["last_run"] = TODAY
    out.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    print(f"\n{len(new)} new draft cards → data/crystallize_queue.json (queue total: {len(existing['cards'])})")
    st = founder_taste_staleness()
    if st.get("stale"):
        print(f"🔴 LOOP-BROKEN: {st['reason']} — refresh founder_taste.json from his ratings")
    else:
        print(f"founder_taste freshness: {st.get('reason', 'ok')}")
    if not total:
        print("honest state: ledgers are young — the machine waits for real verdicts. It runs; it does not invent.")


if __name__ == "__main__":
    main()
