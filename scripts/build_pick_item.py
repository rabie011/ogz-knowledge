#!/usr/bin/env python3
"""BUILD A POST-UNIT PICK ITEM for the decision portal (June 12 — Mohamed's law:
"i need to judge the idea with the photo... we agreed on this and it was much better").
A caption is never judged naked: the card carries WHO the brand is, his real voice
(2 of his own captions), and per option the IDEA + the PHOTO (shoot-card) + the
caption standalone. Becomes the standard for every future pick on the portal.

Usage: python3 scripts/build_pick_item.py --handle myfitness.sa --slot 2027-02-08__ramadan --title "..."
"""
import argparse, datetime, glob, json
from pathlib import Path

BASE = Path(__file__).parent.parent
QUEUE = BASE / "data/decision_queue.json"


def brand_context(handle: str) -> dict:
    pdir = BASE / "clients" / handle / "profile"
    fp = json.loads((pdir / "fingerprint.json").read_text())
    st = json.loads((pdir / "state.json").read_text())
    tp = json.loads((pdir / "truth_pack.json").read_text())
    raw = sorted((BASE / "clients" / handle / "raw/instagram").iterdir())[-1]
    posts = [json.loads(l) for l in (raw / "posts.jsonl").read_text().strip().split("\n") if l.strip()]
    prof = json.loads((raw / "profile.json").read_text())
    best = sorted([p for p in posts if p.get("caption")], key=lambda x: -(x.get("likesCount") or 0))[:2]
    v = fp.get("l2_voice", {})
    voice_bits = [x for x in [v.get("dialect"), v.get("tone")] if x]
    return {
        "name": prof.get("fullName") or handle,
        "who": (prof.get("biography") or "")[:160],
        "state_line": f"{st.get('state','')} · {st.get('followers','?')} متابع · {st.get('posts_count','?')} منشور",
        "voice_line": " · ".join(voice_bits) if voice_bits else "صوت جديد (يُولد الآن)",
        "products": [x["name"] for x in tp.get("product_candidates", [])][:4],
        "real_examples": [b["caption"][:150] for b in best],
    }


def build(handle: str, slot: str, title: str, meaning: str) -> dict:
    opts = []
    for f in sorted(glob.glob(str(BASE / "clients" / handle / "posts" / f"{slot}__pick_*.json"))):
        c = json.loads(open(f).read())
        brain = f.split("pick_")[1].replace(".json", "")
        if not c.get("captions"):
            continue
        vis = c.get("visual") or {}
        opts.append({"v": brain, "who": brain,
                      "label": c["captions"][0],
                      "idea": (c.get("idea") or {}).get("scene_ar", "")[:220],
                      "shots": (vis.get("phone_shoot_card") or [])[:3],
                      "image_url": vis.get("image_url"),
                      "ai_generated": bool(vis.get("ai_generated")),
                      "ai_blocked": (vis.get("ai_imagery") or {}).get("blocked", False)})
    # DIVERSITY GUARD (Mohamed June 12, after rejecting 3 sets «why the same idea»):
    # a pick-set where 2+ options share the core scene is a FAILURE — flag it so the
    # batch builder skips it (re-render with different-scene constraint when keys live).
    import re as _re
    def _scene_key(o):
        s = _re.sub(r"[^؀-ۿ ]", " ", (o.get("idea") or "")).split()
        return " ".join(s[:6])          # first 6 content words = the scene fingerprint
    keys = [_scene_key(o) for o in opts]
    converged = len(keys) >= 2 and len(set(keys)) < len(keys)
    # also catch single-occasion person-repeat (myfitness Captain-Adel case)
    persons = [(_re.search(r"(الكابتن|الكاب[تط]ن|المدرب)\s+\S+", o.get("idea","")) or [None])[0] for o in opts]
    same_person = len([p for p in persons if p]) >= 2 and len(set(p for p in persons if p)) == 1

    return {"id": f"pick_{handle}", "kind": "post_pick", "cat": "اختيارات",
            "diversity_ok": not (converged or same_person),
            "diversity_note": ("⚠ converged scenes" if converged else "⚠ same person" if same_person else "ok"),
            "tag": "اختيارك = ذهب المناسبات", "title": title,
            "meaning": meaning, "priority": "normal", "status": "open",
            "created": __import__("datetime").date.today().isoformat(), "brand_context": brand_context(handle),
            "options": opts}


def record_pick(card: dict, answer: str, judge: str, *, writer=None, base: Path = BASE):
    """WRITER for a post_pick tap (B180). When a HUMAN taps a post_pick card on the portal,
    record his choice as a `pick_selected` client event so the READERS — trust_ladder +
    approvers_registry — actually receive it. Without this the post_pick wire is SEVERED:
    the card is built (build, above) and tapped, but nothing reaches the client ledger, so
    the readers starve (Rule #6: a writer needs its reader; here the reader had no writer).
    Returns the written event, or None when this isn't a writable post_pick by a human.
    `writer` is injectable (defaults to ledger_write) so the path is unit-testable without
    touching a real client ledger; `base` lets a test point the handle-dir check elsewhere."""
    if not card or card.get("kind") != "post_pick":
        return None
    judge_l = (judge or "").lower()
    if judge_l not in ("mohamed", "alhareth", "client"):
        return None                                   # only human confirmers move trust (B156)
    cid = str(card.get("id", ""))
    if not cid.startswith("pick_"):
        return None
    handle = cid[len("pick_"):]
    if not handle or not (base / "clients" / handle).is_dir():
        return None                                   # never write into a phantom client
    ev = {
        "ts": datetime.date.today().isoformat(),
        "type": "pick_selected",
        "subject": f"{card.get('title', cid)} → {str(answer)[:120]}",
        "pick": str(answer)[:120],        # structured winner (option id/brain) — readers don't parse the subject blob
        "confirmer": judge_l,
        "stamp": f"CONFIRMED BY {judge_l.upper()} (decision portal)",
    }
    if writer is None:
        from ledger_write import ledger_write as writer   # validates + B156-gates at write time
    writer(handle, ev)
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--slot", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--meaning", default="اختيارك يصير «ذهب» يعلّم النظام ذوقك. احكم على البوست كامل: الفكرة + الصورة + الكابشن.")
    a = ap.parse_args()
    item = build(a.handle, a.slot, a.title, a.meaning)
    q = json.loads(QUEUE.read_text())
    q["items"] = [i for i in q["items"] if i["id"] != item["id"]] + [item]
    QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(f"✓ post-unit pick item '{item['id']}' on the portal — {len(item['options'])} full post cards")


if __name__ == "__main__":
    main()
