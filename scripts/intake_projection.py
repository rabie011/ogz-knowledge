#!/usr/bin/env python3
"""B102 — intake_projection.py: route intake answers into the right organ (June 19, RABIE's pick).

THE GAP (Rule #6 Consumer Law): `intake_answer` is a valid client_event_v1 type and the
schema accepts it, but NOTHING projected it into an organ — a confirmed client/Mohamed answer
landed in the ledger and died there. The 33 staged `mohamed_must` intake taps would each have
been a write with no reader (Rule #7 pre-wire-the-tap). This module is that missing reader.

WHAT IT DOES: a HUMAN-CONFIRMED `intake_answer` carrying a `target` organ + `field` path +
`value` is projected into the organ the same replay cycle:
  • target "red_lines"  → appended (deduped) into red_lines.lines as a {line,source,confirmer}
  • target "goals"      → set at a dotted field path (e.g. "primary", "usp_his_words.raw")
  • target "fingerprint"→ set at a dotted field path (e.g. "l1_strategy.positioning")

The TEMPLATES (clients/_templates/intake_answer_templates.jsonl) are the question→organ routing
table: each line maps one intake question to its target organ + field + op, so the card-builder
emits a well-formed event and the answer lands in the right place. `event_from_template` turns a
(template, answer) pair into a valid client_event_v1 intake_answer event.

LAWS HELD:
  • Rule #8 refuse-don't-warn: a target outside the allow-list, or a routed answer with no
    value, RAISES — we never poison an arbitrary file or write an empty answer.
  • Rule #9 / B156: only HUMAN-confirmed answers move organ state (provisional/machine = ignored).
  • Idempotent: re-derived from the full ledger every run; applying twice yields no new change.

This module is PURE at its core (project_intake) — no IO, no clock. writeback_replay calls it
in the nightly replay (the reader that runs it); the organs it writes are read downstream by the
caption/visual guards (red_lines), the goal-ratio check (goals), and the composer (fingerprint).
"""
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
TEMPLATES = BASE / "clients/_templates/intake_answer_templates.jsonl"

# An intake answer may only route into these organs. Anything else is a contract breach
# (writing to an arbitrary path = file poisoning, the dangerous class) → refuse (Rule #8).
ALLOWED_TARGETS = {"red_lines", "goals", "fingerprint"}
ORGAN_FILE = {t: f"{t}.json" for t in ALLOWED_TARGETS}

# trust moves on human hands only (B156 / writeback_replay._HUMAN_CONFIRMERS)
_HUMAN_CONFIRMERS = {"mohamed", "client", "mohamed_client", "alhareth"}


def _norm(s) -> str:
    return (s or "").strip()


def _is_confirmed(ev: dict) -> bool:
    if ev.get("confirmer") in _HUMAN_CONFIRMERS:
        return True
    stamp = str(ev.get("stamp", "")).upper()
    return stamp.startswith("CONFIRMED BY") and "PROVISIONAL" not in stamp


def _set_path(d: dict, dotted: str, value) -> bool:
    """Set value at a dotted path, creating intermediate dicts. Returns True if it changed."""
    keys = dotted.split(".")
    cur = d
    for k in keys[:-1]:
        nxt = cur.get(k)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[k] = nxt
        cur = nxt
    last = keys[-1]
    if cur.get(last) == value:
        return False
    cur[last] = value
    return True


def _append_path(d: dict, dotted: str, value) -> bool:
    """Append value (deduped) to the list at a dotted path, creating it as a list if needed.
    Returns True if it changed. Idempotent: re-appending an existing value is a no-op (B190)."""
    keys = dotted.split(".")
    cur = d
    for k in keys[:-1]:
        nxt = cur.get(k)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[k] = nxt
        cur = nxt
    last = keys[-1]
    lst = cur.get(last)
    if not isinstance(lst, list):
        lst = []
        cur[last] = lst
    if value in lst:
        return False
    lst.append(value)
    return True


def project_intake(events, organs: dict):
    """PURE core. organs = {"red_lines":..,"goals":..,"fingerprint":..} (any subset; missing
    targets are created as needed only when actually written). Returns (new_organs, changes).

    Deterministic + idempotent: derives from the full event list, no clock, deep-copies inputs.
    """
    out = {k: json.loads(json.dumps(v)) for k, v in organs.items()}
    changes = []

    for ev in events:
        if _norm(ev.get("type")) != "intake_answer":
            continue
        target = _norm(ev.get("target"))
        if not target:
            continue  # legacy/proposal intake_answer with no routing — not ours to project
        if target not in ALLOWED_TARGETS:
            raise ValueError(f"intake_answer target {target!r} not in allow-list "
                             f"{sorted(ALLOWED_TARGETS)} — refusing to poison an arbitrary organ")
        if not _is_confirmed(ev):
            continue  # provisional / machine answers never move organ state (B156)
        value = ev.get("value")
        if value is None or _norm(value) == "":
            raise ValueError(f"intake_answer for {target!r} carries no value — refusing empty answer")

        organ = out.setdefault(target, {})

        if target == "red_lines":
            lines = organ.setdefault("lines", [])
            text = _norm(value)
            if any(_norm(l.get("line")) == text for l in lines if isinstance(l, dict)):
                continue  # idempotent: already present
            lines.append({
                "line": text,
                "source": "intake:" + _norm(ev.get("question_id") or ev.get("subject")),
                "confirmer": ev.get("confirmer"),
                "date": ev.get("ts"),
            })
            changes.append({"kind": "red_line_added", "target": target,
                            "subject": text, "confirmer": ev.get("confirmer")})
        else:  # goals / fingerprint — set or append at dotted field path
            field = _norm(ev.get("field"))
            if not field:
                raise ValueError(f"intake_answer for {target!r} carries no field path")
            if _norm(ev.get("op")) == "append":
                # B190: a voice PICK appends into a list field (e.g. l2_voice.love_lines) —
                # deduped + idempotent, like red_lines but at an arbitrary dotted path.
                if _append_path(organ, field, _norm(value)):
                    changes.append({"kind": "list_appended", "target": target,
                                    "subject": f"{field}+={value}", "confirmer": ev.get("confirmer")})
            elif _set_path(organ, field, value):
                changes.append({"kind": "field_set", "target": target,
                                "subject": f"{field}={value}", "confirmer": ev.get("confirmer")})

    return out, changes


# ---- templates: the question→organ routing table -------------------------------------------

def load_templates(path: Path = TEMPLATES) -> list:
    if not path.exists():
        return []
    rows = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("//"):
            rows.append(json.loads(ln))
    return rows


def event_from_template(template: dict, value: str, confirmer: str, ts: str, stamp: str) -> dict:
    """Build a valid client_event_v1 intake_answer event from a routing template + an answer.
    Caller supplies ts/stamp/confirmer (no clock here). The result is contract-valid and
    self-routing (carries target/field), so project_intake lands it in the right organ."""
    if template.get("target") not in ALLOWED_TARGETS:
        raise ValueError(f"template target {template.get('target')!r} not routable")
    ev = {
        "ts": ts,
        "type": "intake_answer",
        "confirmer": confirmer,
        "stamp": stamp,
        "question_id": template["question_id"],
        "subject": template["question_id"],
        "target": template["target"],
        "value": value,
    }
    if template.get("field"):
        ev["field"] = template["field"]
    if template.get("op") == "append":
        ev["op"] = "append"  # B190: a list-valued voice pick (love/hate lines) appends, not sets
    return ev
