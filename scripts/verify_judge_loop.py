#!/usr/bin/env python3
"""verify_judge_loop.py — the $0 gate that BITES: it asserts the JUDGE LOOP (the moat's feedback
circuit) is wired end-to-end, and EXITS NON-ZERO with a named RED for every severed/missing wire
(Rule #6 Consumer-Law + Rule #8 refuse-don't-warn). It calls NO LLM, no fal, no network — pure
on-disk + AST/source inspection — so it is safe to run every heartbeat.

THE LOOP (each arrow is a wire this script proves EXISTS, is TYPED, and is CONSUMED):

  (W1) portal tap            →  data/mohamed_answers.jsonl           (the ONE tap-ledger, readable)
  (W2) answers               →  pairwise.consume() / consume_verdicts (handler exists + REFUSES on
                                                                        a corrupt line, Rule #8)
  (W3) consume()             →  data/pairwise_prefs.jsonl            (prefs ledger TYPED — valid_pref)
  (W4) consumer wired        →  apply_rulings.main()                 (runs every heartbeat, Rule #7)
  (W5) prefs                 →  taste_elo.py → data/taste_elo.json   (the Mohamed-Elo, honest fields)
  (W6) taste_elo honesty     →  LIVE separated from SIM              (no sim number labelled live)
  (W7) taste_elo.strengths   →  taste_rank.select() (the SHADOW reader — Rule #6: no write-only organ)
  (W8) taste_rank            →  produce_batch.py (the feed-back seam) + the gate-closed→ship-unchanged
                                                  assertion (Rule #8/#9 — SHADOW until validated)
  (W9) held-out gauge        →  the ONE computed shadow→live gate is present and currently HONEST
                                                  (it does NOT fire on the unvalidated model — Rule #9)
  (W10) verdict consumers    →  gold_mint + judge2_ledger_writer reachable from the unified consumer

Each failed wire is appended as a RED with its W-id. ZERO reds → exit 0 (loop intact, SHADOW honest).
Any red → exit 1 and print every fault.

Usage: python3 scripts/verify_judge_loop.py
"""
import inspect
import json
import sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))

ANSWERS = B / "data/mohamed_answers.jsonl"
PREFS = B / "data/pairwise_prefs.jsonl"
TASTE_ELO = B / "data/taste_elo.json"

REDS = []          # (wire_id, message)
GREENS = []        # wire_id strings that passed


def _red(wire, msg):
    REDS.append((wire, msg))


def _green(wire, msg=""):
    GREENS.append(f"{wire} {msg}".rstrip())


# ── W1: the ONE tap-ledger exists and is readable ───────────────────────────────
def w1_tap_ledger():
    if not ANSWERS.exists():
        _red("W1", f"tap-ledger missing: {ANSWERS} — the portal's writes have nowhere to land")
        return
    try:
        ANSWERS.read_text(encoding="utf-8")
    except Exception as e:
        _red("W1", f"tap-ledger unreadable ({ANSWERS.name}): {type(e).__name__}: {e}")
        return
    _green("W1", "tap-ledger present + readable")


# ── W2: consume() exists and REFUSES on a corrupt line (Rule #8) ─────────────────
def w2_consume_refuses():
    try:
        import pairwise as pw
    except Exception as e:
        _red("W2", f"pairwise module import failed: {type(e).__name__}: {e}")
        return
    for name in ("consume", "consume_verdicts", "valid_pref", "ConsumeError"):
        if not hasattr(pw, name):
            _red("W2", f"pairwise.{name} missing — the consumer/contract is gone")
            return
    # PROVE the refuse behaviour on a synthetic corrupt ledger (no real file touched).
    import tempfile
    saved = pw.ANSWERS
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write('{"item_id":"pw_x","answer":"a"}\nNOT-JSON-LINE\n')
            tmp = f.name
        pw.ANSWERS = Path(tmp)
        try:
            pw._read_answers_strict()
            _red("W2", "consume() did NOT refuse a malformed tap-ledger line — it would drop his tap "
                       "silently (Rule #8 violated)")
        except pw.ConsumeError:
            _green("W2", "consume() refuses a corrupt tap-ledger line (Rule #8)")
        finally:
            Path(tmp).unlink(missing_ok=True)
    finally:
        pw.ANSWERS = saved


# ── W3: prefs ledger exists and every record is TYPED ───────────────────────────
def w3_prefs_typed():
    try:
        import pairwise as pw
    except Exception as e:
        _red("W3", f"pairwise import failed: {type(e).__name__}: {e}")
        return
    if not PREFS.exists():
        _red("W3", f"prefs ledger missing: {PREFS} — consume() has never written (severed W2→W3)")
        return
    bad = []
    for i, line in enumerate(PREFS.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            bad.append(f"line {i}: not JSON")
            continue
        # seed rows are a legitimate shape too; the contract checks the load-bearing pick fields.
        if not pw.valid_pref(rec):
            bad.append(f"line {i}: fails valid_pref ({ {k: rec.get(k) for k in pw.PREF_REQUIRED} })")
    if bad:
        _red("W3", f"prefs ledger has {len(bad)} malformed record(s): {bad[:3]}")
        return
    _green("W3", "prefs ledger present + every record typed (valid_pref)")


# ── W4: the consumer is wired into the heartbeat (apply_rulings.main) ────────────
def w4_consumer_wired():
    try:
        import apply_rulings as ar
    except Exception as e:
        _red("W4", f"apply_rulings import failed: {type(e).__name__}: {e}")
        return
    src = inspect.getsource(ar.main)
    if "pairwise" not in src or "consume" not in src:
        _red("W4", "pairwise.consume() not called in apply_rulings.main() — taps would sit UNCONSUMED")
        return
    # And the pw_ tap must resolve to a handler so make_sure never flags it UNCONSUMED (Rule #7).
    if ar._resolve(("pw_deadbeef", "a")) is None:
        _red("W4", "pw_ pick has NO handler in apply_rulings — Rule #7 (a tap with nowhere to land)")
        return
    # The old silent swallow must be gone: a ConsumeError must propagate, not be hidden.
    if "except Exception:\n        pass" in src and "_pw.consume()" not in src:
        _red("W4", "apply_rulings still swallows the consume wire in a bare except — Rule #8 violated")
        return
    _green("W4", "consumer wired into the heartbeat + pw_ handler present")


# ── W5: prefs → taste_elo.json (the Mohamed-Elo) ─────────────────────────────────
def w5_taste_elo():
    if not TASTE_ELO.exists():
        _red("W5", f"taste_elo.json missing: {TASTE_ELO} — the Elo consumer never ran (severed W3→W5)")
        return None
    try:
        t = json.loads(TASTE_ELO.read_text())
    except Exception as e:
        _red("W5", f"taste_elo.json unreadable: {type(e).__name__}: {e}")
        return None
    needed = ("strengths", "held_out_live_n_testable", "held_out_live_pct", "live_n")
    miss = [k for k in needed if k not in t]
    if miss:
        _red("W5", f"taste_elo.json missing fields {miss} — the Elo organ is incomplete")
        return t
    if not isinstance(t.get("strengths"), dict) or not t["strengths"]:
        _red("W5", "taste_elo.strengths empty — no per-caption Mohamed-Elo to read")
        return t
    _green("W5", f"taste_elo.json present ({len(t['strengths'])} caption-strengths)")
    return t


# ── W6: LIVE is honestly separated from SIM (no sim number labelled live) ────────
def w6_honest_elo(t):
    if t is None:
        _red("W6", "no taste_elo.json to check honesty on (W5 red)")
        return
    # The mixed/degenerate number must NEVER masquerade as his live eye.
    if t.get("held_out_agreement_degenerate") and t.get("live_validated"):
        _red("W6", "DISHONEST: held-out agreement is degenerate (sim) yet live_validated is true — "
                   "a simulation number is being passed off as his live eye (Rule #9)")
        return
    # held_out_live_pct must be None whenever nothing is testable (no fabricated number).
    if (t.get("held_out_live_n_testable", 0) or 0) == 0 and t.get("held_out_live_pct") is not None:
        _red("W6", "DISHONEST: held_out_live_n_testable==0 but held_out_live_pct is a number — "
                   "a live % was fabricated with no testable pick (Rule #9)")
        return
    _green("W6", f"Elo honest (live_validated={t.get('live_validated')}, "
                 f"testable={t.get('held_out_live_n_testable')})")


# ── W7: taste_elo.strengths has a READER (taste_rank) — no write-only organ ──────
def w7_taste_rank_reads():
    try:
        import taste_rank as tr
    except Exception as e:
        _red("W7", f"taste_rank import failed: {type(e).__name__}: {e}")
        return None
    for name in ("select", "wire_live", "gate_status", "rank_candidates"):
        if not hasattr(tr, name):
            _red("W7", f"taste_rank.{name} missing — the SHADOW reader is incomplete")
            return tr
    # Prove it actually reads strengths: rank three captions, the known ones must carry a strength.
    try:
        t = tr.load_taste()
        sample = list((t.get("strengths") or {}).keys())[:2]
        rows = tr.rank_candidates(sample + ["__caption_the_elo_never_saw__"])
        known = [r for r in rows if r["caption"] in sample]
        if sample and not any(r["strength"] is not None for r in known):
            _red("W7", "taste_rank.rank_candidates did NOT read strengths for known captions — "
                       "the reader is severed from taste_elo.json")
            return tr
    except Exception as e:
        _red("W7", f"taste_rank.select/rank failed at runtime: {type(e).__name__}: {e}")
        return tr
    _green("W7", "taste_rank reads taste_elo.strengths (Rule #6 — no write-only organ)")
    return tr


# ── W8: produce_batch consumes taste_rank + asserts gate-closed → ship unchanged ─
def w8_producer_seam(tr):
    pb = B / "scripts/produce_batch.py"
    if not pb.exists():
        _red("W8", "produce_batch.py missing — the feed-back seam has no producer")
        return
    src = pb.read_text()
    if "taste_rank" not in src and "import taste_rank" not in src:
        _red("W8", "produce_batch.py does not import taste_rank — the taste→creation wire is severed "
                   "at the producer (Rule #6)")
        return
    if ".select(" not in src:
        _red("W8", "produce_batch.py never calls taste_rank.select() — the SHADOW reader isn't consumed")
        return
    # The Rule #8 guard: gate closed → ship order MUST equal the chosen order.
    if 'wire_live"] or' not in src and "wire_live'] or" not in src:
        _red("W8", "produce_batch.py lacks the gate-closed→ship-unchanged assertion — a SHADOW signal "
                   "could silently reorder what ships (Rule #8/#9)")
        return
    # Runtime proof of the invariant: with the gate closed, select() must NOT reorder.
    if tr is not None:
        try:
            caps = ["alpha caption", "beta caption", "gamma caption"]
            ordered, meta = tr.select(caps)
            if not meta.get("wire_live") and ordered != caps:
                _red("W8", "gate is CLOSED yet taste_rank.select() reordered the captions — the SHADOW "
                           "wire is leaking into ship order (Rule #8/#9)")
                return
        except Exception as e:
            _red("W8", f"taste_rank.select() failed in the seam check: {type(e).__name__}: {e}")
            return
    _green("W8", "producer consumes taste_rank + gate-closed→ship-unchanged holds")


# ── W9: the ONE computed shadow→live gate is present + currently HONEST ──────────
def w9_gate_honest(tr, t):
    if tr is None:
        _red("W9", "no taste_rank to read the gate from (W7 red)")
        return
    try:
        g = tr.gate_status(t)
    except Exception as e:
        _red("W9", f"taste_rank.gate_status() failed: {type(e).__name__}: {e}")
        return
    # The gate must be a COMPUTED condition over the held-out gauge, not a hardcoded bool.
    src = inspect.getsource(tr.wire_live)
    if "held_out_live_n_testable" not in src or "held_out_live_pct" not in src:
        _red("W9", "wire_live() is not computed from the held-out LIVE gauge — the flip is not the "
                   "ONE computed gate the loop requires")
        return
    # Rule #9 HONESTY: while the model is NOT validated, the gate MUST be closed (SHADOW). If it
    # fired on an unvalidated/degenerate model this is the exact failure the task forbids.
    unvalidated = t is None or t.get("held_out_agreement_degenerate") or not t.get("live_validated")
    if unvalidated and g.get("wire_live"):
        _red("W9", "the shadow→live gate FIRED on an UNVALIDATED model (held-out LIVE not proven) — "
                   "an unvalidated taste signal is steering production (Rule #9 violated)")
        return
    state = "LIVE" if g.get("wire_live") else "SHADOW (honest — awaits validation)"
    _green("W9", f"shadow→live gate is the ONE computed gate, currently {state}")


# ── W10: the verdict consumers (gold + judge2) are reachable ─────────────────────
def w10_verdict_consumers():
    ok = True
    try:
        import gold_mint  # noqa: F401
    except Exception as e:
        _red("W10", f"gold_mint (approve→gold wire) import failed: {type(e).__name__}: {e}")
        ok = False
    try:
        import judge2_ledger_writer  # noqa: F401
    except Exception as e:
        _red("W10", f"judge2_ledger_writer (verdict→moments wire) import failed: {type(e).__name__}: {e}")
        ok = False
    # And the unified consumer must route to BOTH.
    try:
        import pairwise as pw
        usrc = inspect.getsource(pw.consume_verdicts)
        if "gold_mint" not in usrc or "judge2_ledger_writer" not in usrc:
            _red("W10", "consume_verdicts() does not route to both gold_mint AND judge2_ledger_writer")
            ok = False
    except Exception as e:
        _red("W10", f"consume_verdicts inspection failed: {type(e).__name__}: {e}")
        ok = False
    if ok:
        _green("W10", "verdict consumers (gold + judge2) reachable + routed from the unified consumer")


def run():
    w1_tap_ledger()
    w2_consume_refuses()
    w3_prefs_typed()
    w4_consumer_wired()
    t = w5_taste_elo()
    w6_honest_elo(t)
    tr = w7_taste_rank_reads()
    w8_producer_seam(tr)
    w9_gate_honest(tr, t)
    w10_verdict_consumers()
    return REDS, GREENS


def main():
    reds, greens = run()
    print("JUDGE-LOOP WIRING VERIFICATION ($0, no LLM, no fal)")
    for g in greens:
        print(f"  🟢 {g}")
    for wire, msg in reds:
        print(f"  🔴 {wire}: {msg}")
    if reds:
        print(f"\n❌ {len(reds)} severed wire(s) — the judge loop is NOT closed (exit 1, Rule #8).")
        sys.exit(1)
    print(f"\n✅ all {len(greens)} wires intact — loop closed end-to-end, taste signal SHADOW (honest).")
    sys.exit(0)


if __name__ == "__main__":
    main()
