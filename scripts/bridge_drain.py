#!/usr/bin/env python3
"""B186b — THE STAGE→PORTAL DRAINER for confirm cards (low-queue bridge).

Both staged confirm files (data/truth_confirm_staged.json, data/v37_confirm_staged.json) are
WRITTEN by their builders but have NO wire onto data/decision_queue.json — a Rule #6 write-only
organ: truth-confirm cards (real consumer h_truth_confirm) and v37 visual cards (NO consumer) sit
in files, invisible to Mohamed, forever. This closes the end-to-end wire:

    card (staged file) -> normalize -> decision_queue -> portal renders -> his tap -> apply_rulings

Four laws are enforced STRUCTURALLY, not by comment:

  Rule #10 (don't flood): drains ONLY when his VISIBLE load is low, a small batch, and NEVER
    outruns his pairwise taste taps (the actual TOP). Visible load = open NON-pw cards + 1 for the
    whole collapsed pw_ stack (portal_mini._single_open_pw shows one pairwise card at a time).

  Rule #7  (pre-wire the tap): asserts a consumer RESOLVES (apply_rulings._resolve) for every
    answer the card can return, BEFORE draining. A card whose tap cannot land is HELD, never drained.

  Rule #8  (refuse, don't warn): a consumer-less card is EXCLUDED and REPORTED — never silently
    dropped, never drained-with-a-note. (Today: the 10 v37 visual_dna text cards have no handler.)

  Rule #6  (severed surface): normalizes the staged shape  buttons:[{value,label}]  into the
    queue/portal shape  options:[{v,label}]  — drained raw, the card would render NO buttons
    (approvals.html iterates it.options and sends options[choice].v), an untappable dead card.

Idempotent: a card already on the queue (by id, any status) is never re-added.

Usage:
  python3 scripts/bridge_drain.py            # drain a small batch if his queue is low
  python3 scripts/bridge_drain.py --dry-run  # report what WOULD drain, touch nothing
"""
import argparse, datetime, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base as _default_base

STAGED_FILES = ("truth_confirm_staged.json", "v37_confirm_staged.json")
LOW_WATER = 8     # his phone comfortably shows <= this many open cards
MAX_BATCH = 4     # never add more than this in one drain (conservative top-up)


def _load(p: Path, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def is_dead(card: dict) -> bool:
    """A TERMINAL, no-longer-actionable card. 'superseded*' is set by the stagers + pairwise
    (B281) when a newer card REPLACES this one; nothing ever reads a superseded card back
    (grep: zero consumers). But approvals.html hides only status=='answered', so every dead
    'superseded' card still RENDERS as open — 52 of them buried his live pairwise tap in the
    creative/judge lane, the bedrock reason his picks stopped flowing. We do NOT retire
    'answered' (they power the portal's done-list) nor unknown statuses (kept = safe)."""
    return str(card.get("status", "")).startswith("superseded")


def retire_dead(base: Path, dry_run: bool = False) -> dict:
    """Move dead (superseded*) cards OFF the active queue into decision_queue_archive.json.
    Reversible (archived, never deleted — no DELETE APPROVED needed). Idempotent."""
    qf = base / "data" / "decision_queue.json"
    af = base / "data" / "decision_queue_archive.json"
    q = _load(qf, {"items": []})
    dead = [c for c in q["items"] if is_dead(c)]
    if dead and not dry_run:
        arch = _load(af, {"items": []})
        if not isinstance(arch, dict):
            arch = {"items": arch}
        have = {str(c.get("id", "")) for c in arch["items"]}
        arch["items"].extend(c for c in dead if str(c.get("id", "")) not in have)
        af.write_text(json.dumps(arch, ensure_ascii=False, indent=1), encoding="utf-8")
        q["items"] = [c for c in q["items"] if not is_dead(c)]
        qf.write_text(json.dumps(q, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"retired": [str(c.get("id", "")) for c in dead], "dry_run": dry_run}


def _resolver():
    """The REAL dispatcher from apply_rulings — so the consumer-assert matches exactly what
    runs when he taps. No mock: if apply_rulings can't route the answer, neither can his tap."""
    import apply_rulings
    return apply_rulings._resolve


def normalize(card: dict) -> dict:
    """Staged card -> queue/portal card shape. buttons:[{value,label}] -> options:[{v,label}]."""
    out = dict(card)
    if "buttons" in out and "options" not in out:
        out["options"] = [{"v": b.get("value"), "label": b.get("label"),
                           **({"rec": b["rec"]} if "rec" in b else {})}
                          for b in out.pop("buttons")]
    else:
        out.pop("buttons", None)
    out.setdefault("kind", "buttons" if out.get("options") else "text")
    out["status"] = "open"
    out.setdefault("priority", "normal")
    out.setdefault("created", datetime.datetime.now().isoformat(timespec="seconds"))
    out["drained_by"] = "bridge_drain B186b"
    return out


def consumer_ok(card: dict, resolve) -> bool:
    """Rule #7: a handler must resolve for EVERY answer the card can return.
    buttons -> each option value must route; text/free -> the (id, "") item-prefix must route."""
    cid = card.get("id", "")
    if card.get("kind") == "buttons" and card.get("options"):
        vals = [o.get("v") for o in card["options"]]
        return bool(vals) and all(resolve((cid, v)) is not None for v in vals)
    return resolve((cid, "")) is not None   # free-text: item-prefix handler


def visible_open(items: list) -> int:
    """His real on-phone load. The portal collapses the whole pw_ stack to ONE visible card, so
    18 open pairwise taps count as 1 — counting them all would wrongly starve the drainer."""
    def _open(c):
        return c.get("status") != "answered" and not is_dead(c)
    non_pw = [c for c in items if _open(c) and not str(c.get("id", "")).startswith("pw_")]
    has_pw = any(_open(c) and str(c.get("id", "")).startswith("pw_") for c in items)
    return len(non_pw) + (1 if has_pw else 0)


def _staged_candidates(base: Path):
    """Yield staged cards round-robin across files+clients, so one client/file never dominates
    a small drain batch. Each yielded item is (source_file, normalized_card)."""
    per_file = []
    for fn in STAGED_FILES:
        cards = _load(base / "data" / fn, {}).get("cards", [])
        per_file.append([(fn, normalize(c)) for c in cards if c.get("id")])
    i = 0
    while any(per_file):
        lst = per_file[i % len(per_file)]
        if lst:
            yield lst.pop(0)
        i += 1


def drain(base: Path = None, dry_run: bool = False,
          low_water: int = LOW_WATER, max_batch: int = MAX_BATCH) -> dict:
    base = base or _default_base()
    resolve = _resolver()
    retired = retire_dead(base, dry_run=dry_run)["retired"]   # clear dead corpses FIRST
    qf = base / "data" / "decision_queue.json"
    q = _load(qf, {"items": []})
    items = q["items"]
    on_queue = {str(c.get("id", "")) for c in items}

    visible = visible_open(items)
    slots = max(0, min(low_water - visible, max_batch))

    drained, held_no_consumer, already = [], [], []
    for fn, card in _staged_candidates(base):
        cid = card["id"]
        if cid in on_queue:
            already.append(cid)
            continue
        if not consumer_ok(card, resolve):
            held_no_consumer.append({"id": cid, "file": fn})   # Rule #8 — held + reported
            continue
        if len(drained) >= slots:
            continue                                            # eligible but no room (Rule #10)
        if not dry_run:
            items.append(card)
            on_queue.add(cid)
        drained.append(cid)

    if drained and not dry_run:
        qf.write_text(json.dumps(q, ensure_ascii=False, indent=1), encoding="utf-8")

    return {"retired_dead": retired, "visible_before": visible, "slots": slots,
            "drained": drained, "held_no_consumer": held_no_consumer,
            "already_on_queue": len(already), "dry_run": dry_run}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--low-water", type=int, default=LOW_WATER)
    ap.add_argument("--max-batch", type=int, default=MAX_BATCH)
    a = ap.parse_args()
    rep = drain(dry_run=a.dry_run, low_water=a.low_water, max_batch=a.max_batch)
    tag = "DRY-RUN" if rep["dry_run"] else "DRAINED"
    if rep["retired_dead"]:
        print(f"BRIDGE-DRAIN [{tag}]: retired {len(rep['retired_dead'])} DEAD card(s) off his "
              f"portal (superseded, no reader) -> archive")
    print(f"BRIDGE-DRAIN [{tag}]: visible_load={rep['visible_before']} slots={rep['slots']} "
          f"-> {len(rep['drained'])} card(s) onto his portal: {rep['drained']}")
    if rep["held_no_consumer"]:
        ids = [h["id"] for h in rep["held_no_consumer"]]
        print(f"  HELD (Rule #7/#8 — no consumer, NOT drained): {len(ids)} -> {ids[:6]}"
              f"  [next step: build their handler before they can reach him]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
