#!/usr/bin/env python3
"""BUILD PUBLISH-CONFIRM CARDS — B095v STEP 2 (the producer half of the go-live wire).

Mohamed ruled fork B095t = A: "🖐️ Our side — I tap 'published' when a piece goes live."
This is that card. For each SYSTEM-PRODUCED post (data/batch_manifest.json, each entry
already carrying the bedrock identity minted by gen_identity in produce_batch — STEP 1),
stage ONE single-button publish-confirm card into data/publish_confirm_staged.json.

The card carries the join-keys (subject_generation_ulid + brand_ulid) the consumer needs;
the consumer is apply_rulings.h_publish_confirm, which on the 'published' tap appends one
event to data/published.jsonl — the ledger BOTH outcome readers (receipt + live-since)
consume. Rule #6: writer + reader built the same cycle. Rule #7: this builder ASSERTS the
handler exists before staging a card whose tap would otherwise vanish. Rule #12: we never
author the identity — the system minted it at produce time; his tap only confirms go-live.

This builder STAGES only. It does NOT push to his live portal (that is the gated, never-flood
step — Rule #10). `--write` persists the staged file; default is a dry-run summary.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base  # noqa: E402

MANIFEST = "data/batch_manifest.json"
STAGED = "data/publish_confirm_staged.json"


def cards_from_posts(posts: list) -> list:
    """Pure core: map produced posts → publish-confirm card items. A post with no minted
    identity is SKIPPED loudly (returned in the 'skipped' bucket by the caller), never
    staged half-formed (Rule #8). One card per distinct subject_generation_ulid."""
    cards, seen = [], set()
    for p in posts:
        gen = (p.get("subject_generation_ulid") or "").strip()
        brand = (p.get("brand_ulid") or "").strip()
        if not gen or not brand or gen in seen:
            continue
        seen.add(gen)
        handle, date = p.get("handle", "?"), p.get("date", "")
        cards.append({
            "id": f"publish_confirm_{gen}",
            "kind": "buttons",
            "lane": "decide",
            "subject_generation_ulid": gen,
            "brand_ulid": brand,
            "handle": handle,
            "date": date,
            "title": f"Did this go live? — {handle} {date}",
            "summary": f"Tap when the {handle} piece for {date} is published. "
                       f"That tap records the go-live so the system can start learning from real outcomes.",
            "options": [{"value": "published", "label": "✅ Published / نُشِر"}],
        })
    return cards


def _skipped(posts: list) -> list:
    return [p for p in posts
            if not (p.get("subject_generation_ulid") or "").strip()
            or not (p.get("brand_ulid") or "").strip()]


def assert_handler_wired() -> None:
    """Rule #7: refuse to stage any card whose 'published' tap has no consumer."""
    import apply_rulings as ar
    fn = ar._resolve((f"publish_confirm_PROBE", "published"))
    if fn is None or getattr(fn, "__name__", "") != "h_publish_confirm":
        raise SystemExit("REFUSED (Rule #7): no consumer for the 'published' tap — "
                         "apply_rulings.h_publish_confirm must be wired before staging cards")


def build(write: bool = False, b: Path | None = None) -> dict:
    b = b or base()
    assert_handler_wired()
    man_p = b / MANIFEST
    posts = json.loads(man_p.read_text(encoding="utf-8")).get("posts", []) if man_p.exists() else []
    cards = cards_from_posts(posts)
    skipped = _skipped(posts)
    out = {"cards": cards}
    if write:
        (b / STAGED).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"staged": len(cards), "skipped": len(skipped), "wrote": write,
            "path": str(b / STAGED) if write else None}


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage publish-confirm cards (B095v step 2)")
    ap.add_argument("--write", action="store_true", help="persist data/publish_confirm_staged.json")
    a = ap.parse_args()
    r = build(write=a.write)
    print(f"publish-confirm cards: {r['staged']} staged" + (f", {r['skipped']} skipped (no identity)" if r['skipped'] else ""))
    if r["wrote"]:
        print(f"  → {r['path']}")
    else:
        print("  (dry-run — pass --write to persist; cards are NOT pushed to the live portal)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
