#!/usr/bin/env python3
"""B083 — writeback_metrics.py: the promotion counter + severed-wire detector.

THE CONSUMER (Rule #6) for B082's clients/<handle>/events/writeback.jsonl. B082 WRITES
derivations (a human verdict promoting derived organ state); this READS them and answers the
one bedrock question of "the system that captures his taste": ARE his taps turning into
learned organ state at all?

For each pilot it computes, from the REAL ledger + writeback files (never a template):
  • confirmed_verdicts — human-confirmed events present in the ledger (the feed signal)
  • feedable_now        — of those, how many are in a form B082 can ACTUALLY consume
                          (type==truth_confirmed with a subject, OR a reason_code that is a
                          known founder-kill slug). This is the honest "the loop could fire"
                          number — it mirrors exactly what writeback_replay.derive() acts on.
  • promotions          — writeback events made (by kind), total + within the window
  • status:
      live    — promotions in window > 0                        (the loop is learning)
      stalled — feedable_now > 0 but zero promotions             (WIRE BROKEN: should have fired)
      severed — confirmed_verdicts > 0 but feedable_now == 0     (his taps exist, none consumable)
      idle    — no confirmed verdicts yet                        (waits honestly, no alarm)

ALARM SET = clients whose status is `stalled` or `severed` (active but not promoting). `idle`
NEVER alarms (mirrors B001's goal-ratio watchdog: wait honestly while undeclared). This is a
REPORT, not a gate or a card-pusher — it never floods his portal (Rule #10) and never hard-reds
make_sure (a chronic red masks real failures). It surfaces the truth; the fix (wiring the emit
path so his verdicts carry truth_confirmed / structured reason_code) is the next bedrock step.

Usage:
    python3 scripts/writeback_metrics.py                # report every pilot
    python3 scripts/writeback_metrics.py --handle albaik
    python3 scripts/writeback_metrics.py --json
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent.parent

# reuse B082's exact human-verdict criterion so "confirmed_verdicts" here == what the
# replay would act on (no second, drifting definition of "confirmed").
from writeback_replay import _is_confirmed, _norm, _founder_kill_vocab, load_crosswalk  # noqa: E402

ALARM_STATUSES = {"stalled", "severed"}


def _ev_date(ev: dict):
    """Parse the YYYY-MM-DD prefix of an event ts → date, or None."""
    ts = str(ev.get("ts") or "")
    if len(ts) >= 10:
        try:
            return datetime.strptime(ts[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _is_feedable(ev: dict, founder_kills: set, crosswalk: dict | None = None) -> bool:
    """True iff writeback_replay.derive() could act on this confirmed event — a reason_code
    counts when it is a founder-kill slug directly OR translates to one via the CONFIRMED
    crosswalk (mirrors derive()'s exact rule, so the detector never claims feedable for
    something the replay would skip)."""
    if _norm(ev.get("type")) == "truth_confirmed" and _norm(ev.get("subject")):
        return True
    rc = _norm(ev.get("reason_code"))
    if not rc:
        return False
    return rc in founder_kills or rc in (crosswalk or {})


def diagnose(ledger_events, writeback_events, founder_kills, now=None, window_days=60,
             crosswalk=None):
    """PURE core — no IO. Returns the per-client metric dict.

    `now` is a date (defaults to today); window_days bounds the promotion-recency check.
    Deterministic: same inputs → same output.
    """
    now = now or datetime.now(timezone.utc).date()

    confirmed = [e for e in ledger_events if _is_confirmed(e)]
    feedable = [e for e in confirmed if _is_feedable(e, founder_kills, crosswalk)]

    by_kind = {}
    promos_in_window = 0
    for w in writeback_events:
        kind = _norm(w.get("type")).replace("writeback_", "") or "unknown"
        by_kind[kind] = by_kind.get(kind, 0) + 1
        d = _ev_date(w)
        # undated writeback events (legacy, pre-ts) count toward the window — absence of a
        # date must never let a stale loop look "fresh" by hiding from the window check.
        if d is None or (now - d).days <= window_days:
            promos_in_window += 1

    promos_total = sum(by_kind.values())

    if promos_in_window > 0:
        status = "live"
    elif feedable:
        status = "stalled"      # the loop COULD fire and didn't — broken wire
    elif confirmed:
        status = "severed"      # his taps exist but none are in a consumable form
    else:
        status = "idle"         # nothing confirmed yet — wait honestly

    return {
        "confirmed_verdicts": len(confirmed),
        "feedable_now": len(feedable),
        "promotions_total": promos_total,
        "promotions_in_window": promos_in_window,
        "promotions_by_kind": by_kind,
        "status": status,
        "alarm": status in ALARM_STATUSES,
    }


def _load_jsonl(path: Path):
    out = []
    if path.exists():
        for ln in path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln:
                try:
                    out.append(json.loads(ln))
                except Exception:
                    pass
    return out


def diagnose_client(handle: str, now=None, window_days=60) -> dict:
    cdir = BASE / "clients" / handle / "events"
    ledger = _load_jsonl(cdir / "ledger.jsonl")
    writeback = _load_jsonl(cdir / "writeback.jsonl")
    founder_kills = _founder_kill_vocab()
    crosswalk = load_crosswalk(founder_kills)
    r = diagnose(ledger, writeback, founder_kills, now=now, window_days=window_days,
                 crosswalk=crosswalk)
    r["handle"] = handle
    return r


def diagnose_all(now=None, window_days=60):
    handles = sorted(p.name for p in (BASE / "clients").iterdir()
                     if p.is_dir() and (p / "profile/truth_pack.json").exists())
    return [diagnose_client(h, now=now, window_days=window_days) for h in handles]


def alarm_clients(now=None, window_days=60):
    """The clients an operator should see: active (taps present) but not promoting."""
    return [r for r in diagnose_all(now=now, window_days=window_days) if r["alarm"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    ap.add_argument("--window-days", type=int, default=60)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = ([diagnose_client(args.handle, window_days=args.window_days)]
            if args.handle else diagnose_all(window_days=args.window_days))

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    print(f"WRITEBACK METRICS — promotion counter + severed-wire detector "
          f"({args.window_days}d window)")
    print(f"  {'client':<16}{'confirmed':>10}{'feedable':>10}{'promos':>8}  status")
    for r in rows:
        flag = "  🔴" if r["alarm"] else ""
        print(f"  {r['handle']:<16}{r['confirmed_verdicts']:>10}{r['feedable_now']:>10}"
              f"{r['promotions_total']:>8}  {r['status']}{flag}")
    alarmed = [r for r in rows if r["alarm"]]
    if alarmed:
        sev = [r['handle'] for r in alarmed if r['status'] == 'severed']
        stl = [r['handle'] for r in alarmed if r['status'] == 'stalled']
        print()
        if sev:
            print(f"  SEVERED ({len(sev)}): {', '.join(sev)} — human verdicts present but NONE "
                  f"in a form the loop consumes (no truth_confirmed / structured reason_code). "
                  f"FIX = wire the emit path, not more organs.")
        if stl:
            print(f"  STALLED ({len(stl)}): {', '.join(stl)} — feedable verdicts exist but zero "
                  f"promotions. The replay wire is broken.")
    else:
        print("\n  no active-but-stalled clients.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
