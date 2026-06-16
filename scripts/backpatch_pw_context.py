#!/usr/bin/env python3
"""BACK-PATCH SCENE CONTEXT onto the live pairwise cards (Step 3a, June 16 calibration rebuild).
The 11 open pw_ cards carry only two bare captions — Mohamed was asked "which would you post?" with
no idea WHAT each is for. This matches each option's caption back to its produced post file and stamps
a short scene-context onto it, so he judges IN context. CRITICAL: it preserves every card id and every
options[i].v / options[i].label EXACTLY (the durable-card wire pairwise._pairs_from_cards reads — the
June-15 severed-surface scar). It only ADDS fields. Re-runnable (idempotent). Zero-key.
Usage: python3 scripts/backpatch_pw_context.py [--apply]   (default: dry-run report)
"""
import glob, json, sys
from pathlib import Path

B = Path(__file__).parent.parent
QUEUE = B / "data/decision_queue.json"
CLIENTS = ["eatjurisha", "albaik", "myfitness.sa", "alnasserjewelry"]


def _post_index():
    """captions[0] → context dict, across all pilot produced posts."""
    idx = {}
    for h in CLIENTS:
        for f in glob.glob(str(B / f"clients/{h}/posts/*__auto.json")) + \
                 glob.glob(str(B / f"clients/{h}/posts/*__v6.json")):
            try:
                d = json.loads(Path(f).read_text())
            except Exception:
                continue
            caps = d.get("captions") or []
            if not caps:
                continue
            slot = d.get("slot") or {}
            idea = d.get("idea") or {}
            occ = slot.get("occasion") or slot.get("type") or slot.get("angle_theme")  # None-guarded
            idx[caps[0]] = {
                "occasion": occ if occ and occ != "daily" else (slot.get("angle_theme") or "يومي"),
                "scene": idea.get("scene_ar"),
                "reasoning": idea.get("why_it_lands") or slot.get("angle_theme"),
                "visual": d.get("visual", {}).get("phone_shoot_card"),
            }
    return idx


def _ctx_line(c):
    """Short per-option context: «occasion — scene»."""
    occ = (c.get("occasion") or "").strip()
    scene = (c.get("scene") or "").strip()
    if occ and scene:
        return f"{occ} — {scene[:90]}"
    return occ or (scene[:90] if scene else "")


def transform(q, idx):
    """Pure: stamp scene-context onto open pw_ cards in queue dict q (mutates in place). Returns stats.
    Preserves every id and every options[i].v / options[i].label — only ADDS 'scene' / card-level fields."""
    matched = divergent = shared = unmatched = touched = 0
    for card in q.get("items", []):
        if not str(card.get("id", "")).startswith("pw_") or card.get("status") == "answered":
            continue
        opts = card.get("options") or []
        if len(opts) != 2:
            continue
        ca = idx.get(opts[0].get("label"))
        cb = idx.get(opts[1].get("label"))
        if not ca and not cb:
            unmatched += 1
            continue
        matched += 1
        # per-option scene line (the divergent context) — preserve v + label EXACTLY, only add 'scene'
        if ca:
            opts[0]["scene"] = _ctx_line(ca)
        if cb:
            opts[1]["scene"] = _ctx_line(cb)
        # card-level block only when BOTH match AND share the same occasion (a real shared frame)
        if ca and cb and ca.get("occasion") and ca["occasion"] == cb["occasion"]:
            shared += 1
            card["post_occasion"] = ca["occasion"]
            if ca.get("scene"):
                card["post_idea"] = ca["scene"]
            if ca.get("reasoning"):
                card["post_reasoning"] = ca["reasoning"]
            if ca.get("visual"):
                card["post_visual"] = ca["visual"]
        else:
            divergent += 1
        touched += 1
    return {"matched": matched, "shared": shared, "divergent": divergent, "unmatched": unmatched, "touched": touched}


def backpatch(apply=False):
    q = json.loads(QUEUE.read_text())
    stats = transform(q, _post_index())
    print(f"pairwise cards: matched {stats['matched']} · shared-occasion {stats['shared']} · "
          f"divergent {stats['divergent']} · unmatched {stats['unmatched']}")
    if apply:
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))   # mtime bump → ETag miss → context surfaces
        print(f"✅ applied — {stats['touched']} cards now carry scene context (ids + options.v preserved)")
    else:
        print("(dry-run — pass --apply to write)")
    return stats


if __name__ == "__main__":
    backpatch(apply="--apply" in sys.argv)
