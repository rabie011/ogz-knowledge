#!/usr/bin/env python3
"""push_posts_for_review — surface produced posts as APPROVE/REJECT cards in Mohamed's portal.

Mohamed (June 29, portal): "where is the approval button?" — verified root: produced posts sit in
caption_bank.json (judged, passed=false when HUMAIN is down) but were NEVER pushed to decision_queue
as approvable post-cards, so there was no Approve button for a complete post. This pusher closes that:
each produced post becomes a caption_judge card (the existing format that renders image+caption+Approve✓)
with id `post_<bankkey>` so apply_rulings.h_post_review can map the tap back (Rule #6 writer↔reader).

His APPROVE is the AUTHORITATIVE human signal (he is the ground truth — AI can't judge Saudi creative).
It does NOT weaken the machine 2-signal gate (Rule #13) — it is a SEPARATE, higher authority that passes
a post by HUMAN verdict. Idempotent: skips a post already carded or already human-decided.

  python3 scripts/push_posts_for_review.py            # push all judged-but-undecided produced posts
  python3 scripts/push_posts_for_review.py --dry-run  # report only
"""
import json
import sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
BANK = B / "data/caption_bank.json"
QUEUE = B / "data/decision_queue.json"
ANSWERS = B / "data/mohamed_answers.jsonl"


def _img_url(handle, product, chain):
    slug = product.strip().replace(" ", "_").replace("/", "-")
    return f"/static/renders_v37/{handle}_{slug}_{chain}.jpg"


def _already_decided(card_id):
    """True if Mohamed already answered this post-card (idempotency — don't re-push a decided post)."""
    if not ANSWERS.exists():
        return False
    for l in ANSWERS.read_text(encoding="utf-8").splitlines():
        if l.strip():
            try:
                r = json.loads(l)
                if r.get("item_id") == card_id and r.get("answer") in ("approved", "rejected"):
                    return True
            except json.JSONDecodeError:
                continue
    return False


def _queued_ids():
    if not QUEUE.exists():
        return set()
    q = json.loads(QUEUE.read_text())
    items = q if isinstance(q, list) else q.get("items", [])
    return {it.get("id") for it in items if isinstance(it, dict)}


def build_card(bankkey, entry):
    handle, product, chain = (bankkey.split("__") + ["", "", ""])[:3]
    judge = entry.get("judge") or {}
    if isinstance(judge, str):
        try:
            judge = json.loads(judge.replace("'", '"'))
        except Exception:
            judge = {}
    img = _img_url(handle, product, chain)
    score = entry.get("score")
    return {
        "id": f"post_{bankkey}",
        "title": f"{handle} · {product} · {chain}",
        # action_type=decision is REQUIRED: without it _bucket() infers 'info' (no buttons/options field —
        # the Approve✓/Reject✗ come from judge_lane rendering) → the card COLLAPSES behind 'view all' and
        # Mohamed never sees it (June 29 bug: 8 cards shipped invisible). It IS an actionable decision.
        "action_type": "decision",
        "tag": "Judge", "kind": "caption_judge", "judge_lane": "True", "lane": "creative",
        "priority": "normal", "handle": handle, "product": product,
        "caption": entry.get("caption"), "occasion": "evergreen", "image_url": img,
        "why": "Approve ✓ → counts the post DONE (your human verdict is authoritative) + seeds gold. Reject ✗ → kill the setup.",
        "need": "Your verdict on the FULL post: the image above + the Arabic caption.",
        "did": f"System produced + GPT-judged (score {score}); HUMAIN down so it needs YOUR signal to pass.",
        "island_text": entry.get("caption"),
        "made_by": "system:produce", "artifact_version": "1",
    }


PER_CLIENT_CAP = 4   # Rule #10 — don't flood; show the BEST few per client, not every variant


def _score(entry):
    try:
        return float(entry.get("score") or 0)
    except (TypeError, ValueError):
        return 0.0


def main():
    dry = "--dry-run" in sys.argv
    cap = PER_CLIENT_CAP
    for a in sys.argv:
        if a.startswith("--per-client="):
            cap = int(a.split("=")[1])
    bank = json.loads(BANK.read_text())
    queued = _queued_ids()
    import queue_decision as qd

    # eligible = produced + captioned + has image + not already carded/decided
    eligible = []
    for bankkey, entry in bank.items():
        if "__" not in bankkey or not entry.get("caption"):
            continue
        card_id = f"post_{bankkey}"
        if card_id in queued or _already_decided(card_id):
            continue
        handle, product, chain = (bankkey.split("__") + ["", "", ""])[:3]
        if not (B / "api/static" / _img_url(handle, product, chain).split("/static/")[1]).exists():
            continue
        eligible.append((handle, bankkey, entry))

    # Rule #10: cap to the top-CAP per client by GPT score (not every variant → don't flood his phone)
    by_handle = {}
    for handle, bankkey, entry in eligible:
        by_handle.setdefault(handle, []).append((bankkey, entry))
    pushed = []
    for handle, items in by_handle.items():
        items.sort(key=lambda x: -_score(x[1]))
        for bankkey, entry in items[:cap]:
            card = build_card(bankkey, entry)
            if dry:
                print(f"  WOULD push: post_{bankkey} (score {entry.get('score')}) «{(entry.get('caption') or '')[:40]}»")
            else:
                qd.push(card)
                print(f"  ✅ pushed: post_{bankkey} (score {entry.get('score')})")
            pushed.append(bankkey)
        extra = len(items) - cap
        if extra > 0:
            print(f"  ({handle}: held back {extra} lower-scored variants — Rule #10, raise --per-client to see more)")
    print(f"\n{'(dry) ' if dry else ''}pushed {len(pushed)} post-cards across {len(by_handle)} client(s), cap {cap}/client")


if __name__ == "__main__":
    main()
