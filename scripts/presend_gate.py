#!/usr/bin/env python3
"""B029 — PRESEND GATE: grep before any outbound question. Re-ask = trust death.

Before ANY question goes to a client, this gate checks whether the answer already
exists on disk: the client's profile organs, the founder's q-card answers in the
ledger, and the intake manifests. Already-answered → BLOCK (exit 1) + a violation
event in data/trust_violations.jsonl. The trust budget law: violations target = 0
forever (B030 meters it).

Deterministic topic matching: a question is mapped to topics by keyword, each topic
declares its evidence sources; ANY live evidence = block with the evidence path.

Usage:
  python3 scripts/presend_gate.py --handle eatjurisha --question "وش منتجاتكم الأساسية؟"
  python3 scripts/presend_gate.py --handle X --file draft_questions.json   # ["q1", ...]
Exit 0 = all clear to send · exit 1 = at least one blocked (the script refuses).
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from feedback_lib import base

VIOLATIONS = "data/trust_violations.jsonl"

# topic → (question-keyword regex, evidence checks)
# an evidence check returns a string (the evidence) or None
def _organ(b, handle, name):
    p = b / f"clients/{handle}/profile/{name}.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _ledger_answer(b, handle, q_key):
    """His q-card answers: jurisha_q_voice etc. — an answer row = answered, period."""
    short = handle.replace("eat", "").replace(".sa", "").replace("jewelry", "")
    af = b / "data/mohamed_answers.jsonl"
    if not af.exists():
        return None
    for l in af.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        iid = r.get("item_id", "")
        if (q_key in iid and (short in iid or handle in iid)
                and r.get("answer") not in (None, "", "rejected")):
            return f"ledger: {iid} → {r.get('answer')}" + (f" «{(r.get('note') or '')[:40]}»" if r.get("note") else "")
    return None


TOPICS = [
    ("products", r"منتج|أطباق|أصناف|قائمة|منيو|products?|menu|dishes",
     lambda b, h: (lambda tp: f"truth_pack.confirmed: {[c.get('name') for c in tp['confirmed']]}"
                   if tp.get("confirmed") else None)(_organ(b, h, "truth_pack"))
                  or _ledger_answer(b, h, "_q_products")),
    ("voice", r"صوت|نبرة|لهجة|أسلوب|voice|tone|dialect|speaks?",
     lambda b, h: (lambda fp: f"fingerprint.l2_voice.speaker={fp['l2_voice']['speaker']} "
                              f"({fp['l2_voice'].get('speaker_ruling', {}).get('source', '')})"
                   if fp.get("l2_voice", {}).get("speaker") else None)(_organ(b, h, "fingerprint"))
                  or _ledger_answer(b, h, "_q_voice")
                  or _ledger_answer(b, h, "_voice_v")),
    ("goal", r"هدف|أهداف|تطمح|goals?|objective|aim",
     lambda b, h: (lambda g: f"goals organ: {json.dumps(g.get('primary'), ensure_ascii=False)[:60]}"
                   if g.get("primary") else None)(_organ(b, h, "goals"))
                  or _ledger_answer(b, h, "_q_goal")),
    ("capacity", r"طاقة|استيعاب|كم طلب|قدرة|capacity|orders per",
     lambda b, h: _ledger_answer(b, h, "_q_capacity")),
    ("usp", r"يميزكم|ميزة|تنافس|الفرق|usp|unique|différenc|differentiat",
     lambda b, h: _ledger_answer(b, h, "_q_usp")),
    ("redlines", r"خطوط حمراء|ممنوع|ما تبون|red.?lines?|never post|avoid",
     lambda b, h: (lambda rl: f"red_lines organ: {len(rl['lines'])} lines on disk"
                   if rl.get("lines") else None)(_organ(b, h, "red_lines"))
                  or _ledger_answer(b, h, "_q_redlines")),
    ("audience", r"جمهور|شريحة|عملاءكم|زبائن|audience|target|customers",
     lambda b, h: (lambda am: f"audience_mirror organ: {len(am.get('segments', []))} segments"
                   if am.get("segments") else None)(_organ(b, h, "audience_mirror"))),
    ("location", r"موقع|فرع|مدينة|وين|location|branch|city|where",
     lambda b, h: (lambda m: f"manifest bio: «{m['surfaces']['profile'].get('bio', '')[:50]}»"
                   if (m.get("surfaces", {}).get("profile", {}).get("bio") or "").strip() else None)(
                       json.loads((b / f"clients/{h}/manifest.json").read_text())
                       if (b / f"clients/{h}/manifest.json").exists() else {})),
]


def check_question(b: Path, handle: str, question: str) -> dict:
    hits = []
    for topic, pat, ev_fn in TOPICS:
        if re.search(pat, question, re.IGNORECASE):
            try:
                ev = ev_fn(b, handle)
            except Exception:
                ev = None
            if ev:
                hits.append({"topic": topic, "evidence": ev})
    return {"question": question, "blocked": bool(hits), "hits": hits}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--question", action="append", default=[])
    ap.add_argument("--file", help="json file: list of question strings")
    a = ap.parse_args()
    b = base()
    qs = list(a.question)
    if a.file:
        qs += json.loads(Path(a.file).read_text())
    if not qs:
        raise SystemExit("no questions given")
    blocked = []
    for q in qs:
        r = check_question(b, a.handle, q)
        if r["blocked"]:
            blocked.append(r)
            with open(b / VIOLATIONS, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                    "handle": a.handle, "question": q[:160],
                                    "evidence": r["hits"], "blocked_presend": True},
                                   ensure_ascii=False) + "\n")
            print(f"  🔴 BLOCKED: «{q[:60]}»")
            for h in r["hits"]:
                print(f"      already answered — {h['topic']}: {h['evidence'][:90]}")
        else:
            print(f"  ✅ clear: «{q[:60]}»")
    if blocked:
        print(f"\n🔴 {len(blocked)}/{len(qs)} blocked — re-asking an answered question is trust death")
    else:
        print(f"\n🟢 all {len(qs)} clear to send")
    raise SystemExit(1 if blocked else 0)


if __name__ == "__main__":
    main()
