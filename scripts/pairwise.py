#!/usr/bin/env python3
"""PAIRWISE TASTE CALIBRATION — the moat (Mohamed 2026-06-14, validated against VPL/FSPO/Best-Worst
Scaling, arXiv:1712.01765). The judge is provably broken on ABSOLUTE 0-10 scoring (47% pass-call,
below chance — it clusters everything at ~6.5). The fix the research + his own data both point to:
stop scoring, ASK A-vs-B. Pairwise forces a real choice (no mushy middle) and is the most reliable
way to capture ONE person's taste (split-half 0.80-0.90 vs 0.55-0.70 for star ratings).

This builds it on our REAL pilot output (eatjurisha/albaik/myfitness — not the old non-pilot ratings):
  form_pairs() — same-brand A-vs-B pairs from produced captions (blind: no brain/approach shown).
  push_cards()  — pairwise cards to his portal; the handler (consume) EXISTS first (Rule #7).
  consume()     — reads his picks from the answers ledger → data/pairwise_prefs.jsonl (the taste signal).
  agreement()   — THE proper metric: of the pairs he judged, how often does the AI judge rank his
                  winner above his loser? Replaces the broken 6.5 threshold. Random = 50%.
Zero-key safe: form/push/consume need no LLM; agreement() uses the CCO judge only on judged pairs.
Usage: python3 scripts/pairwise.py form|push|consume|agreement [--n 8]
"""
import argparse, glob, hashlib, json, sys
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
PREFS = B / "data/pairwise_prefs.jsonl"
PAIRS = B / "data/pairwise_pairs.json"
ANSWERS = B / "data/mohamed_answers.jsonl"   # the file the PORTAL actually writes (June 15: was
# pointed at answers.jsonl which the portal never writes → every live tap was silently lost. The
# Consumer-Law bug: writer (portal) and reader (consume) MUST be the same file.
QUEUE = B / "data/decision_queue.json"
CLIENTS = ["eatjurisha", "albaik", "myfitness.sa"]


def _produced():
    """All produced pilot captions (newest render per slot), as candidates: (handle, date, caption, brain)."""
    out = []
    for h in CLIENTS:
        for f in glob.glob(str(B / f"clients/{h}/posts/*__auto.json")) or glob.glob(str(B / f"clients/{h}/posts/*__v6.json")):
            d = json.loads(Path(f).read_text())
            caps = d.get("captions") or []
            if caps:
                out.append({"handle": h, "date": Path(f).name.split("__")[0],
                            "caption": caps[0], "brain": d.get("brain", "?")})
    return out


def _pid(a, b):
    return "pw_" + hashlib.md5((a["caption"] + "|" + b["caption"]).encode()).hexdigest()[:12]


def form_pairs(n_per_brand=4):
    """Same-brand A-vs-B pairs (different posts → different approach). Blind. Stable ids."""
    cands = _produced()
    by_h = {}
    for c in cands:
        by_h.setdefault(c["handle"], []).append(c)
    pairs = []
    for h, lst in by_h.items():
        # deterministic spread: pair item i with item (i + half) to avoid adjacent near-dupes
        m = len(lst)
        if m < 2:
            continue
        for i in range(min(n_per_brand, m // 2)):
            a, b = lst[i], lst[(i + m // 2) % m]
            if a["caption"] == b["caption"]:
                continue
            pairs.append({"id": _pid(a, b), "handle": h, "a": a, "b": b})
    PAIRS.write_text(json.dumps(pairs, ensure_ascii=False, indent=1))
    return pairs


def push_cards(n_per_brand=4):
    import queue_decision as qd
    pairs = form_pairs(n_per_brand)
    pushed = 0
    for p in pairs:
        # kind=caption_pick so the portal renders BOTH captions as tappable buttons; the pick posts
        # the option's `v` ("a"/"b") which consume() reads. judge_lane → it lives in the Decide lane.
        card = {
            "id": p["id"], "kind": "caption_pick", "judge_lane": True, "lane": "creative",
            "tag": "Pick", "status": "open", "priority": "normal",
            "title": f"{p['handle']} · which would you post?",
            "handle": p["handle"],
            "need": "Tap the caption you'd actually post — gut only, no scores.",
            "options": [{"label": p["a"]["caption"], "v": "a"},
                        {"label": p["b"]["caption"], "v": "b"}],
            "why": "Taste calibration — your pick teaches the system your eye (it currently judges at ~chance).",
        }
        try:
            qd.push_attributed(card, made_by="system:pairwise", via="scripts/pairwise.py",
                               reason=f"pairwise taste calibration — {p['handle']}")
            pushed += 1
        except Exception as e:
            print(f"  push failed {p['id']}: {str(e)[:50]}")
    print(f"✅ pushed {pushed} pairwise cards ({len(pairs)} pairs) to the portal")
    return pushed


def _pairs_from_cards():
    """The DURABLE pair source: each pushed pw_ card embeds BOTH captions in its options, and the
    card persists in the queue. form_pairs() OVERWRITES pairwise_pairs.json, so a tap on a card
    whose pair was overwritten would be silently dropped (June 15 severed-surface scar: 11 of his
    15 open taps would have vanished). Reconstructing the pair from the card makes every live card
    resolvable regardless of the side-file's state."""
    if not QUEUE.exists():
        return {}
    q = json.loads(QUEUE.read_text())
    out = {}
    for c in (q.get("items", []) if isinstance(q, dict) else q):
        cid = str(c.get("id", ""))
        if not cid.startswith("pw_"):
            continue
        opts = {o.get("v"): o.get("label") for o in (c.get("options") or [])}
        if "a" in opts and "b" in opts and opts["a"] and opts["b"]:
            out[cid] = {"handle": c.get("handle", "?"),
                        "a": {"caption": opts["a"], "brain": "?"},
                        "b": {"caption": opts["b"], "brain": "?"}}
    return out


def consume():
    """Handler (Rule #6/#7): read his A/B picks from the answers ledger → the preference ledger.
    Resolves each pick from the DURABLE card (queue) first, enriched by the pairs side-file where
    present — so no tap is ever lost to a pairs-file overwrite (Consumer-Law backstop)."""
    if not ANSWERS.exists():
        print("no answers yet"); return 0
    file_pairs = {p["id"]: p for p in (json.loads(PAIRS.read_text()) if PAIRS.exists() else [])}
    pairs = {**_pairs_from_cards(), **file_pairs}  # card = durable backstop; file enriches (brain)
    seen = set()
    if PREFS.exists():
        seen = {json.loads(l)["pair_id"] for l in PREFS.read_text().splitlines() if l.strip()}
    n = 0
    for line in ANSWERS.read_text().splitlines():
        try:
            e = json.loads(line)
        except Exception:
            continue
        pid = e.get("item_id")
        if pid not in pairs or pid in seen:
            continue
        ans = (e.get("answer") or "").strip().lower()
        winner = "a" if ans.startswith("a") else ("b" if ans.startswith("b") else None)
        if not winner:
            continue
        p = pairs[pid]
        rec = {"pair_id": pid, "handle": p["handle"], "winner": winner,
               "winner_caption": p[winner]["caption"], "loser_caption": p["b" if winner == "a" else "a"]["caption"],
               "winner_brain": p[winner]["brain"], "judge": e.get("judge"), "ts": e.get("ts")}
        PREFS.open("a").write(json.dumps(rec, ensure_ascii=False) + "\n")
        seen.add(pid); n += 1
    print(f"✅ consumed {n} new pairwise picks → {PREFS.name}")
    return n


def agreement():
    """THE metric: of the pairs Mohamed judged, how often does the AI judge rank his winner above
    his loser? Random=50%. This replaces the broken absolute 6.5 threshold."""
    if not PREFS.exists():
        print("no picks yet — judge some pairs first"); return None
    import c_suite as cs
    prefs = [json.loads(l) for l in PREFS.read_text().splitlines() if l.strip()]
    agree = total = 0
    for r in prefs:
        try:
            ws = cs.cco_pass({"captions": [r["winner_caption"]]}, r["handle"]).get("saudi_score", 0)
            ls = cs.cco_pass({"captions": [r["loser_caption"]]}, r["handle"]).get("saudi_score", 0)
        except Exception:
            continue
        if ws == ls:
            continue
        total += 1
        agree += (ws > ls)
    pct = round(agree / total * 100) if total else None
    print(f"JUDGE↔MOHAMED pairwise agreement: {agree}/{total} ({pct}%)  [random=50%; was 47% on broken absolute scoring]")
    return pct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["form", "push", "consume", "agreement"])
    ap.add_argument("--n", type=int, default=4, help="pairs per brand")
    a = ap.parse_args()
    if a.cmd == "form":
        ps = form_pairs(a.n); print(f"formed {len(ps)} pairs → {PAIRS.name}")
    elif a.cmd == "push":
        push_cards(a.n)
    elif a.cmd == "consume":
        consume()
    elif a.cmd == "agreement":
        agreement()


if __name__ == "__main__":
    main()
