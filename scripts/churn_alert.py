#!/usr/bin/env python3
"""B093 — RED/YELLOW churn alert: the CONSUMER of the churn-risk dashboard (Rule #6).

churn_risk.py (B092) WRITES data/churn_risk.json — a GREEN/YELLOW/RED read of the integrity of
Mohamed's judging signal (the scarcest input to the whole creation system). A dashboard no one
reads is a write-only organ (Rule #6); RABIE's B092 verdict was literal: "wire the alert next."
This is that wire.

Writer (already exists): data/churn_risk.json (churn_risk.py).
Consumers built/used HERE (Rule #6 — every writer needs a reader, same cycle):
  1. events/alerts.jsonl       ← append-only churn_alert event stream (fired / resolved)
  2. ~/agents/queue/pending/   ← on RED ONLY: a human-touch outreach task naming the
                                 ogz_account_owner from each pilot's profile/state.json (B160)

SCOPE (honest, Rule #9): churn_risk is currently JUDGE-engagement churn — one aggregate signal;
the pilot has no per-client client-side cadence stream yet (see churn_risk SCOPE NOTE). So a RED
fires ONE outreach task listing ALL pilot owners (each currently null → "UNASSIGNED — Mohamed
must name", B160). When a per-client cadence stream exists, this same consumer fans out per handle.

LEVELS:
  RED    → human-touch outreach task dropped to the queue + 'fired' event logged. The owner acts.
  YELLOW → watch-event logged only (no task, no dispatch). Rule #8: dispatch is reserved for the
           hard condition; YELLOW is signal, not a fire drill.
  GREEN / INSUFFICIENT → auto-close any open alert (Rule #10: one card per condition, self-closing).

DEDUPE (Rule #10): ONE open alert per level. Re-running while still RED does NOT re-fire or
re-drop a task — the level only auto-closes (a 'resolved' event) the moment risk leaves it.

The dropped task uses task_type 'human_touch_outreach', which the orchestrator does not execute
(it falls through to the "Unknown task type" no-op branch) — this is a note for a human, never a
pipeline run.

Deterministic, recompute-idempotent. All inputs injected into reconcile() so it is fully testable.
By default it RECOMPUTES the dashboard first (via churn_risk) so it never acts on a stale read —
the consumer owns its own freshness. Pass --from-file to reconcile the existing data/churn_risk.json.
Usage:
  python3 scripts/churn_alert.py             # recompute churn_risk, then reconcile + act
  python3 scripts/churn_alert.py --from-file # reconcile the existing data/churn_risk.json
  python3 scripts/churn_alert.py --dry-run   # compute + print, write nothing (never drops a task)
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DASH_PATH = BASE / "data" / "churn_risk.json"
ALERTS_PATH = BASE / "events" / "alerts.jsonl"
CLIENTS_DIR = BASE / "clients"
QUEUE_DIR = Path.home() / "agents" / "queue" / "pending"

ALERT_TYPE = "churn_alert"
ACTION_FIRED = "fired"
ACTION_RESOLVED = "resolved"
ACTIONABLE = ("RED", "YELLOW")
UNASSIGNED = "UNASSIGNED — Mohamed must name"


def load_owners(clients_dir=CLIENTS_DIR):
    """{handle: owner-or-None} from every clients/*/profile/state.json (B160 field)."""
    owners = {}
    root = Path(clients_dir)
    if not root.exists():
        return owners
    for state in sorted(root.glob("*/profile/state.json")):
        handle = state.parent.parent.name
        try:
            owners[handle] = json.loads(state.read_text()).get("ogz_account_owner")
        except Exception:
            owners[handle] = None
    return owners


def load_events(path=ALERTS_PATH):
    """Parse the append-only alert log → list of event dicts. Honest [] if absent."""
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for ln in p.read_text().splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def open_levels(events):
    """{level: True/False open} from the log — a level is OPEN iff its LAST action was 'fired'."""
    last = {}
    for e in events:
        if e.get("type") == ALERT_TYPE and e.get("level"):
            last[e["level"]] = e.get("action")
    return {lvl: act == ACTION_FIRED for lvl, act in last.items()}


def owner_roster(owners):
    """Human-readable roster — null owners flagged UNASSIGNED (B160 not yet named by Mohamed)."""
    return [{"handle": h, "owner": o or UNASSIGNED} for h, o in sorted(owners.items())]


def drop_outreach_task(owners, dash, now_iso, queue_dir=QUEUE_DIR):
    """Drop a HUMAN-TOUCH task (not a pipeline) naming the account owner(s). Returns the path."""
    qd = Path(queue_dir)
    qd.mkdir(parents=True, exist_ok=True)
    stamp = now_iso.replace("-", "").replace(":", "").replace("T", "_")[:15]
    path = qd / f"churn_touch_{stamp}.json"
    task = {
        "task_type": "human_touch_outreach",   # not a pipeline — orchestrator no-ops this type
        "human": True,
        "source": "churn_alert.py (B093)",
        "risk": dash.get("risk"),
        "reasons": dash.get("reasons", []),
        "owners": owner_roster(owners),
        "request": "RED churn-risk on the judging signal — owner: reach Mohamed and re-engage the "
                   "judging cadence (the taste calibration is starving).",
        "created": now_iso,
        "priority": 1,
    }
    path.write_text(json.dumps(task, ensure_ascii=False, indent=1))
    return path


def reconcile(dash, owners, now_iso, events, queue_dir=QUEUE_DIR, drop_task=True):
    """PURE planner. Returns the list of NEW events to append. Side effect: writes ONE queue task
    iff a RED actually fires AND drop_task. Auto-closes stale levels, dedupes open levels."""
    risk = (dash or {}).get("risk")
    opened = open_levels(events)
    new = []
    # AUTO-CLOSE — any open level that is no longer the current risk (Rule #10, self-closing card).
    for lvl in ACTIONABLE:
        if opened.get(lvl) and risk != lvl:
            new.append({"ts": now_iso, "type": ALERT_TYPE, "action": ACTION_RESOLVED,
                        "level": lvl, "now_risk": risk})
    # FIRE — current risk, only if actionable and not already open (dedupe).
    if risk in ACTIONABLE and not opened.get(risk):
        task_file = None
        if risk == "RED" and drop_task:
            task_file = drop_outreach_task(owners, dash, now_iso, queue_dir)
        new.append({"ts": now_iso, "type": ALERT_TYPE, "action": ACTION_FIRED, "level": risk,
                    "reasons": (dash or {}).get("reasons", []), "owners": owner_roster(owners),
                    "task_file": str(task_file) if task_file else None})
    return new


def append_events(new, path=ALERTS_PATH):
    if not new:
        return
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        for e in new:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def fresh_dashboard():
    """Recompute the churn-risk read from source so the consumer never acts on a stale file.
    Single-sources the computation in churn_risk (never re-derives it here). Falls back to the
    on-disk dashboard if churn_risk is unavailable for any reason (honest, never crashes)."""
    try:
        import churn_risk
        answers = churn_risk.load_answers()
        receipts = (json.loads(churn_risk.RECEIPTS.read_text())
                    if churn_risk.RECEIPTS.exists() else None)
        dash = churn_risk.compute(answers, receipts, datetime.now(), churn_risk._load_thresholds())
        dash["computed"] = datetime.now().isoformat(timespec="seconds")
        DASH_PATH.write_text(json.dumps(dash, ensure_ascii=False, indent=1))
        return dash
    except Exception:
        return json.loads(DASH_PATH.read_text()) if DASH_PATH.exists() else {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-file", action="store_true", help="reconcile existing churn_risk.json (no recompute)")
    ap.add_argument("--dry-run", action="store_true", help="compute + print only; never write or drop")
    a = ap.parse_args()
    if a.from_file:
        dash = json.loads(DASH_PATH.read_text()) if DASH_PATH.exists() else {}
    else:
        dash = fresh_dashboard()
    owners = load_owners()
    events = load_events()
    now_iso = datetime.now().isoformat(timespec="seconds")
    new = reconcile(dash, owners, now_iso, events, drop_task=not a.dry_run)
    risk = dash.get("risk", "?")
    icon = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢", "INSUFFICIENT": "⚪"}.get(risk, "•")
    print(f"{icon} churn={risk}  open={[k for k, v in open_levels(events).items() if v]}  new-events={len(new)}")
    for e in new:
        tf = f" → {e['task_file']}" if e.get("task_file") else ""
        print(f"   • {e['action']} {e['level']}{tf}")
    if a.dry_run:
        print("   (dry-run: nothing written)")
        return
    append_events(new)
    print(f"   → {ALERTS_PATH}")


if __name__ == "__main__":
    main()
