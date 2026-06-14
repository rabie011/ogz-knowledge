#!/usr/bin/env python3
"""THE CLOSED LEARNING LOOP — the system learns from Mohamed's verdicts BY ITSELF.

Mohamed 2026-06-14: "make sure THEY learn, not you only. the system must work by itself.
we are here to make it work, not to do the work for the system." The cold-eyes catch: his
quality_verdict was WRITE-ONLY — his rejection was logged, never learned. This is the reader.

For every judged post (mohamed_answers.jsonl, judge2_*):
  REJECTED → load the post, run pre_ship_gate.
     • gate already KILLS it → lesson already encoded (the gate works); record consumed.
     • gate PASSED it (a BLIND SPOT) → the system LEARNS: derive a rule from his note + the
       post and append it to data/learned_gate_rules.json, so the gate BLOCKS this class
       next time WITHOUT a human. (Gold stays protected by gold_mint's own approved+rating>=4 filter.)
  APPROVED ★4-5 → ensure it's in gold (the few-shot the generator learns from).
Writes a consumption ledger (data/verdict_lessons.jsonl) — so NO verdict is ever write-only.
Idempotent; runs in the make_sure feedback chain every cycle. Self-auditing.

Usage: python3 scripts/learn_from_verdict.py [--dry]
"""
import argparse, json, re, sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
import pre_ship_gate as gate
ANSWERS = B / "data/mohamed_answers.jsonl"
LEARNED = B / "data/learned_gate_rules.json"
LESSONS = B / "data/verdict_lessons.jsonl"
TS = "2026-06-14"

# map his rejection-reason language → a learned rule TYPE the gate can enforce
REASON_PATTERNS = [
    (re.compile(r"occasion|مناسبة|wrong.*beat|beat.*wrong|العيد الوطني|التأسيس"), "occasion_mismatch"),
    (re.compile(r"caption|كابshن|bad|سيئ|ضعيف|generic|same|مكرر|change.*caption"), "weak_caption"),
    (re.compile(r"culture|ثقاف|sensitive|royal|family|سعود|تقاليد|new culture|emotion"), "cultural"),
    (re.compile(r"dine|صالة|cloud"), "format"),
]


def _load_learned():
    if LEARNED.exists():
        return json.loads(LEARNED.read_text())
    return {"version": 1, "note": "rules the system LEARNED from Mohamed's rejections the gate missed",
            "phrase_bans": [], "rules": []}


def _post_path(handle, date):
    hits = list((B / "clients" / handle / "posts").glob(f"{date}*.json")) if handle and date else []
    return hits[0] if hits else None


def _verdicts():
    if not ANSWERS.exists():
        return []
    out = []
    for l in ANSWERS.read_text().splitlines():
        try:
            r = json.loads(l)
        except Exception:
            continue
        it = r.get("item_id", "")
        if it.startswith("judge2_") and r.get("judge") == "mohamed":
            out.append(r)
    return out


def _already(consumed, key):
    return key in consumed


def run(dry=False):
    learned = _load_learned()
    consumed = set()
    if LESSONS.exists():
        for l in LESSONS.read_text().splitlines():
            try:
                consumed.add(json.loads(l)["key"])
            except Exception:
                pass
    new_rules, new_bans, lessons, blind_spots = 0, 0, [], 0
    # product names — NEVER auto-ban these (Rule #9: the learner banned 'رز الكابلي', a product)
    products = set()
    for tp in (B / "clients").glob("*/profile/truth_pack.json"):
        try:
            for c in json.loads(tp.read_text()).get("product_candidates", []):
                n = (c.get("name") or "").strip()
                if n:
                    products.add(n)
                    products.add(" ".join(n.split()[:2]))
        except Exception:
            pass
    rej_openers = {}   # opener → count across rejections (ban only RECURRING, conservative)
    for r in _verdicts():
        it = r.get("item_id", "")
        verdict = str(r.get("answer", "")).lower()
        rating = r.get("rating")
        note = (r.get("note") or r.get("fix") or "").strip()
        key = f"{r.get('ts')}|{it}"
        if _already(consumed, key):
            continue
        # parse judge2_<handle>_<date>
        m = re.match(r"judge2_(.+?)_(\d{4}-\d\d-\d\d)$", it)
        handle, date = (m.group(1), m.group(2)) if m else (None, None)
        lesson = {"key": key, "item": it, "verdict": verdict, "rating": rating,
                  "note": note[:200], "ts": TS}
        if verdict in ("rejected", "flagged") or (isinstance(rating, int) and rating <= 2):
            pp = _post_path(handle, date)
            if pp:
                post = json.loads(pp.read_text())
                g = gate.gate(post, handle)
                if g["verdict"] == "KILL":
                    lesson["outcome"] = f"gate already catches this ({g['hard_kills']}) — system covered"
                else:
                    # BLIND SPOT — the system learns a new rule from his note
                    blind_spots += 1
                    rtype = next((t for rx, t in REASON_PATTERNS if rx.search(note)), "weak_caption")
                    rule = {"learned_from": key, "type": rtype, "note": note[:160],
                            "handle": handle, "occasion": g.get("occasion"), "date": TS}
                    # weak captions: ACCUMULATE the opener (ban only RECURRING non-product ones
                    # after the full pass — conservative, never bans on a single rejection)
                    if rtype == "weak_caption":
                        caps = post.get("captions") or []
                        if caps and caps[0]:
                            opener = " ".join(caps[0].split()[:2])
                            if opener and opener not in products:
                                rej_openers[opener] = rej_openers.get(opener, 0) + 1
                    learned["rules"].append(rule)
                    new_rules += 1
                    lesson["outcome"] = f"BLIND SPOT → learned rule type={rtype}"
            else:
                lesson["outcome"] = "post file not found (older) — verdict noted"
        elif verdict == "approved" or (isinstance(rating, int) and rating >= 4):
            lesson["outcome"] = "approved → gold (gold_mint owns minting)"
        else:
            lesson["outcome"] = f"verdict '{verdict}' noted"
        lessons.append(lesson)

    # ban only openers Mohamed rejected REPEATEDLY (≥2) and that aren't products — conservative
    for opener, cnt in rej_openers.items():
        if cnt >= 2 and opener not in learned["phrase_bans"] and opener not in products:
            learned["phrase_bans"].append(opener)
            new_bans += 1
    if not dry:
        LEARNED.write_text(json.dumps(learned, ensure_ascii=False, indent=1))
        with open(LESSONS, "a") as f:
            for ls in lessons:
                f.write(json.dumps(ls, ensure_ascii=False) + "\n")
    print(f"  learned: {len(lessons)} verdicts consumed (no longer write-only) · "
          f"{blind_spots} gate blind-spots → {new_rules} new rules, {new_bans} phrase-bans")
    for ls in lessons[:6]:
        print(f"    [{ls['verdict']}] {ls['item']}: {ls['outcome']}")
    return {"consumed": len(lessons), "blind_spots": blind_spots, "new_rules": new_rules}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    print(run(ap.parse_args().dry))
