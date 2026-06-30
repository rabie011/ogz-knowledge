#!/usr/bin/env python3
"""TASTE WRITEBACK BRIDGE (C245, June 30) — closes the loop the B114 tripwire keeps flagging.

THE PROBLEM (grepped, panel-confirmed June 30): founder_taste.json IS the bar the critic judges
against, but NOTHING refreshes it from his ratings. crystallize_loop only DETECTS staleness;
taste_elo derives ELO → taste_elo.json but never touches the bar. So he keeps rating (55 pairs,
latest 2026-06-29) while the bar's _meta.built stays 2026-06-11 → 17d stale → the writeback loop
is broken (test_taste_staleness.test_live_repo_currently_fresh RED).

THE FIX (Option C — RABIE + DeepSeek converged, Rule #20): we never AUTHOR taste (Rule #12).
This bridge PROPOSES kill-candidates from his own lowest-ranked captions (taste_elo.bottom5_he_
rejects) → data/taste_proposals.json, and stages one-tap portal cards. The bar refreshes ONLY on
his confirm tap (consumer: apply_rulings.h_taste_refresh, Rule #7). On confirm → founder_taste.kills
grows + _meta.built re-stamps → tripwire clears HONESTLY (his fresh input, not a faked date — Rule
#11). On reject → the candidate is excluded from the next proposal batch.

This is Rule #6 applied to the taste bar: the write (proposal) ships with its reader (the handler)."""
import argparse, datetime, json, re
from pathlib import Path

B = Path(__file__).parent.parent
ELO = B / "data/taste_elo.json"
TASTE = B / "data/founder_taste.json"
PROPOSALS = B / "data/taste_proposals.json"


def _slug(caption: str) -> str:
    """Stable id from the caption text (so a re-run proposes the SAME card id — idempotent,
    Rule #10 dedupe). Arabic-safe: hash the normalized text rather than transliterate."""
    norm = re.sub(r"\s+", " ", (caption or "").strip())
    import hashlib
    return "k" + hashlib.sha1(norm.encode("utf-8")).hexdigest()[:10]


def _existing_kill_text(taste: dict) -> set:
    """Captions/patterns already in the bar — never re-propose what he already killed."""
    out = set()
    for k in taste.get("kills", []):
        t = k if isinstance(k, str) else (k.get("caption") or k.get("pattern") or k.get("slug") or "")
        if t:
            out.add(re.sub(r"\s+", " ", t.strip()))
    return out


def build_proposals() -> dict:
    """Surface his lowest-ranked captions as kill-CANDIDATES (never kills). Source = his own
    ratings via taste_elo.bottom5_he_rejects. Excludes anything already killed + anything he
    previously rejected as a candidate. Returns the proposals dict (also written to disk)."""
    if not ELO.exists():
        raise RuntimeError("taste_elo.json missing — run taste_elo.py first (the harvest source)")
    elo = json.loads(ELO.read_text())
    taste = json.loads(TASTE.read_text()) if TASTE.exists() else {"_meta": {}, "kills": []}
    prior = json.loads(PROPOSALS.read_text()) if PROPOSALS.exists() else {"candidates": {}}
    prior_cands = prior.get("candidates", {})

    already_killed = _existing_kill_text(taste)
    bottom = elo.get("bottom5_he_rejects", []) or []

    candidates = dict(prior_cands)  # preserve prior verdicts (rejected stay excluded)
    fresh = 0
    for rank, cap in enumerate(bottom, 1):
        cap = (cap or "").strip()
        if not cap:
            continue
        norm = re.sub(r"\s+", " ", cap)
        if norm in already_killed:
            continue
        sid = _slug(cap)
        existing = candidates.get(sid)
        if existing and existing.get("status") in ("confirmed", "rejected"):
            continue  # his verdict already in — don't re-surface (Rule #10)
        candidates[sid] = {
            "slug": sid,
            "caption": cap,
            "elo_rank_from_bottom": rank,
            "source": "taste_elo.bottom5_he_rejects",
            "status": existing.get("status", "proposed") if existing else "proposed",
        }
        if not existing:
            fresh += 1

    out = {
        "_meta": {
            "built": datetime.date.today().isoformat(),
            "rule": "kill-CANDIDATES from his lowest-ranked captions; bar refreshes only on his tap "
                    "(apply_rulings.h_taste_refresh). We never author taste (Rule #12).",
            "source_elo_n_pairs": elo.get("n_pairs"),
        },
        "candidates": candidates,
        "_fresh_this_run": fresh,
    }
    PROPOSALS.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def pending_cards(proposals: dict | None = None) -> list:
    """The candidates still awaiting his tap (status=proposed). These become portal cards."""
    p = proposals or (json.loads(PROPOSALS.read_text()) if PROPOSALS.exists() else {"candidates": {}})
    return [c for c in p.get("candidates", {}).values() if c.get("status") == "proposed"]


def stage_cards(limit: int = 5) -> int:
    """Push one-tap confirm/reject cards for pending candidates (Rule #7 — the consumer
    h_taste_refresh exists before these ship). Returns the number staged. Lean: ≤limit per run
    (Rule #10 — never flood). Requires queue_decision; safe to skip if unavailable."""
    import sys
    sys.path.insert(0, str(B / "scripts"))
    try:
        import queue_decision as qd
    except Exception as e:
        raise RuntimeError(f"queue_decision unavailable: {e}")
    staged = 0
    for c in pending_cards()[:limit]:
        item = {
            "id": f"taste_kill_{c['slug']}",
            "title": "تأكيد: هل هذا الكابشن مرفوض دائمًا؟",
            "tag": "taste_refresh",
            "desc": c["caption"],
            "kind": "buttons",
            "buttons": [{"value": "confirm", "label": "نعم — اقتله من المعيار"},
                        {"value": "reject", "label": "لا — هذا مقبول"}],
        }
        qd.push_attributed(item, made_by="system:taste_refresh")  # valid PLAYER form (system:*); bare "taste_refresh" fails is_player (C245 wire-bug, fixed June 30)
        staged += 1
    return staged


def main():
    ap = argparse.ArgumentParser(description="Taste writeback bridge — propose kill-candidates from his ratings")
    ap.add_argument("--stage", action="store_true", help="also push portal cards for pending candidates")
    ap.add_argument("--limit", type=int, default=5)
    a = ap.parse_args()
    p = build_proposals()
    pend = pending_cards(p)
    print(f"taste_proposals.json: {len(p['candidates'])} candidate(s), {p['_fresh_this_run']} fresh, {len(pend)} pending his tap")
    if a.stage:
        n = stage_cards(limit=a.limit)
        print(f"staged {n} portal card(s) (consumer: apply_rulings.h_taste_refresh)")


if __name__ == "__main__":
    main()
