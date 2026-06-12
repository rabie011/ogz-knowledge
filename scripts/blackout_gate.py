#!/usr/bin/env python3
"""THE NEGATIVE-SPACE GATE (FLANK-02, June 11) — when NOT to publish.
Born from the pyramid critic: a scheduled celebratory post on a national mourning
day passes every text gate we have — the most screenshotable embarrassment in
Saudi social media. Every other gate decides WHAT goes out; this one decides
WHETHER anything goes out at all.

Two mechanisms:
1. THE BLACKOUT SWITCH (data/blackout/switch.json) — manual, human-flipped.
   ON = ALL publishing halts, including approved batches. Mourning, crisis,
   client emergency. No automation may flip it ON or OFF — human hands only
   (the AI-judge scar applied to safety: AI may never decide a mourning day
   is over).
2. ETIQUETTE WINDOWS (data/blackout/etiquette.json) — advisory send windows:
   prayer buffers, late-night quiet, Ramadan's inverted hours. These WARN
   (soft), the switch BLOCKS (hard).

Usage:
  from blackout_gate import check
  verdict = check()                      # {"publish_allowed": bool, "hard_block": ..., "warnings": [...]}
  python3 scripts/blackout_gate.py            # status
  python3 scripts/blackout_gate.py --on "وفاة — حداد وطني" --by mohamed
  python3 scripts/blackout_gate.py --off --by mohamed
"""
import argparse, datetime, json, sys
from pathlib import Path

BASE = Path(__file__).parent.parent
SWITCH = BASE / "data/blackout/switch.json"
ETIQUETTE = BASE / "data/blackout/etiquette.json"

DEFAULT_ETIQUETTE = {
    "quiet_hours": {"start": "01:30", "end": "06:30",
                    "note": "late-night sends read as bot behavior; ramadan inverts this — see ramadan_mode"},
    "prayer_buffer_minutes": 20,
    "prayers_note": "advisory: avoid sends ±20min around maghrib and jumu'ah (the two with social weight); exact times shift daily — scheduler should consult a prayer-times source, this gate only flags the policy",
    "ramadan_mode": {"peak_windows": ["21:30-01:30 (post-taraweeh)", "02:30-04:00 (sahur)"],
                      "avoid": ["17:00-19:30 (pre-maghrib fatigue + iftar itself)"],
                      "note": "normal quiet_hours suspended in ramadan — nights ARE the day"},
}


def _switch() -> dict:
    if not SWITCH.exists():
        return {"blackout": False, "reason": None, "set_by": None, "ts": None}
    return json.loads(SWITCH.read_text())


# B138: Riyadh maghrib by month (approx mid-month, bundled — no API per money law)
MAGHRIB_BY_MONTH = {1: "17:30", 2: "17:50", 3: "18:05", 4: "18:20", 5: "18:35", 6: "18:45",
                     7: "18:45", 8: "18:30", 9: "18:00", 10: "17:35", 11: "17:15", 12: "17:15"}


def check(now: datetime.datetime | None = None) -> dict:
    """The one question every publish path must ask. Hard block = switch only."""
    now = now or datetime.datetime.now()
    sw = _switch()
    warnings = []
    et = json.loads(ETIQUETTE.read_text()) if ETIQUETTE.exists() else DEFAULT_ETIQUETTE
    qh = et.get("quiet_hours", {})
    if qh:
        t = now.strftime("%H:%M")
        start, end = qh.get("start", "01:30"), qh.get("end", "06:30")
        in_quiet = (t >= start) and (t < end) if start < end else (t >= start or t < end)
        if in_quiet:
            warnings.append(f"quiet hours ({start}–{end}): {qh.get('note','')}")
    # B138: prayer-aware warnings (warn only - the switch alone blocks)
    mag = MAGHRIB_BY_MONTH.get(now.month, "18:00")
    mag_t = now.replace(hour=int(mag[:2]), minute=int(mag[3:]))
    if abs((now - mag_t).total_seconds()) <= 20 * 60:
        warnings.append(f"maghrib window (~{mag} +-20min) - hold sends if possible")
    if now.weekday() == 4 and "11:30" <= now.strftime("%H:%M") <= "13:30":
        warnings.append("jumuah window (Fri 11:30-13:30) - hold sends until after prayer")
    return {
        "publish_allowed": not sw["blackout"],
        "hard_block": ({"reason": sw["reason"], "set_by": sw["set_by"], "since": sw["ts"]}
                        if sw["blackout"] else None),
        "warnings": warnings,
    }


def flip(on: bool, reason: str | None, by: str):
    """Human hands only — callers must pass --by. Every flip is logged append-only."""
    SWITCH.parent.mkdir(parents=True, exist_ok=True)
    state = {"blackout": on, "reason": reason if on else None, "set_by": by,
             "ts": datetime.datetime.now().isoformat(timespec="seconds")}
    SWITCH.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    with open(SWITCH.parent / "switch_log.jsonl", "a") as f:
        f.write(json.dumps(state, ensure_ascii=False) + "\n")
    if not ETIQUETTE.exists():
        ETIQUETTE.write_text(json.dumps(DEFAULT_ETIQUETTE, ensure_ascii=False, indent=2))
    return state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--on", metavar="REASON", help="halt ALL publishing (reason required)")
    ap.add_argument("--off", action="store_true", help="lift the blackout")
    ap.add_argument("--by", default=None, help="who flips (required for any flip)")
    a = ap.parse_args()
    if a.on or a.off:
        if not a.by:
            sys.exit("refused: every flip needs --by <human> — the switch is human-hands-only")
        state = flip(bool(a.on), a.on, a.by)
        print(("🔴 BLACKOUT ON — all publishing halted: " + state["reason"]) if state["blackout"]
              else "🟢 blackout lifted")
        return
    v = check()
    print(("🟢 publishing allowed" if v["publish_allowed"]
           else f"🔴 BLACKOUT — {v['hard_block']['reason']} (by {v['hard_block']['set_by']} since {v['hard_block']['since']})"))
    for w in v["warnings"]:
        print(f"⚠️  {w}")


if __name__ == "__main__":
    main()
