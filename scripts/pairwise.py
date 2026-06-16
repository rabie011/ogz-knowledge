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
OUT_ELO = B / "data/taste_elo.json"   # the Mohamed-Elo signal the active selector reads (Step 5)
CLIENTS = ["eatjurisha", "albaik", "myfitness.sa"]


def _produced():
    """All produced pilot captions (newest render per slot), as candidates with scene CONTEXT so
    cards are born judgeable-in-context (June 16): (handle, date, caption, brain, occasion, scene)."""
    out = []
    for h in CLIENTS:
        for f in glob.glob(str(B / f"clients/{h}/posts/*__auto.json")) or glob.glob(str(B / f"clients/{h}/posts/*__v6.json")):
            d = json.loads(Path(f).read_text())
            caps = d.get("captions") or []
            if caps:
                slot = d.get("slot") or {}
                idea = d.get("idea") or {}
                occ = slot.get("occasion") or slot.get("type") or slot.get("angle_theme")
                out.append({"handle": h, "date": Path(f).name.split("__")[0],
                            "caption": caps[0], "brain": d.get("brain", "?"),
                            "occasion": occ if occ and occ != "daily" else (slot.get("angle_theme") or "يومي"),
                            "scene": idea.get("scene_ar")})
    return out


def _scene_line(c):
    """Short per-option context «occasion — scene» (matches backpatch_pw_context._ctx_line)."""
    occ, scene = (c.get("occasion") or "").strip(), (c.get("scene") or "").strip()
    if occ and scene:
        return f"{occ} — {scene[:90]}"
    return occ or (scene[:90] if scene else "")


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


def _card_for(p):
    """Build the caption_pick card for a pair — born WITH context (per-option scene + shared occasion).
    kind=caption_pick → the portal renders BOTH captions as tappable buttons; the pick posts the
    option's `v` ("a"/"b") which consume() reads. Shared by random (push_cards) and active (push_active)."""
    a, b = p["a"], p["b"]
    card = {
        "id": p["id"], "kind": "caption_pick", "judge_lane": True, "lane": "creative",
        "tag": "Pick", "status": "open", "priority": "normal",
        "title": f"{p['handle']} · which would you post?",
        "handle": p["handle"],
        "need": "Tap the caption you'd actually post — gut only, no scores.",
        "options": [{"label": a["caption"], "v": "a", "scene": _scene_line(a)},
                    {"label": b["caption"], "v": "b", "scene": _scene_line(b)}],
        "why": "Taste calibration — your pick teaches the system your eye (it currently judges at ~chance).",
    }
    if a.get("occasion") and a["occasion"] == b.get("occasion"):
        card["post_occasion"] = a["occasion"]
    return card


def _push(pairs):
    import queue_decision as qd
    pushed = 0
    for p in pairs:
        try:
            qd.push_attributed(_card_for(p), made_by="system:pairwise", via="scripts/pairwise.py",
                               reason=f"pairwise taste calibration — {p['handle']}")
            pushed += 1
        except Exception as e:
            print(f"  push failed {p['id']}: {str(e)[:50]}")
    print(f"✅ pushed {pushed} pairwise cards ({len(pairs)} pairs) to the portal")
    return pushed


def push_cards(n_per_brand=4):
    return _push(form_pairs(n_per_brand))


def _judged_or_live_pids():
    """pids we must NOT re-push: already judged (in prefs), or already on the portal (open OR answered
    pw_ cards). The active selector only ever proposes NEW pairs — it never touches the live 11."""
    seen = set()
    if PREFS.exists():
        seen |= {json.loads(l).get("pair_id") for l in PREFS.read_text().splitlines() if l.strip()}
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text())
        seen |= {str(c.get("id", "")) for c in q.get("items", []) if str(c.get("id", "")).startswith("pw_")}
    return seen


def active_pairs(n=5, w_close=0.5, w_conn=0.5):
    """ACTIVE-PICK (Step 5b, June 16): rank candidate same-brand pairs by INFORMATION GAIN so a few
    taps teach the model the most. score = w_close·(close strength = hardest discrimination) +
    w_conn·(low comparison degree = improves a star-shaped, barely-connected graph). Connectivity
    matters most early (most captions are never-compared), so w_conn ties weight with w_close and
    breaks ties. HARD-excludes anything already judged or already on the portal. NEW pairs only —
    the live 11 are never touched. The '~5 taps ≈ 15' benefit is a CLAIM that must be MEASURED
    (agreement vs random) before it's stated to Mohamed (Rule #9) — this only proposes the pairs."""
    cands = _produced()
    by_h = {}
    for c in cands:
        by_h.setdefault(c["handle"], []).append(c)
    # the elo signal (guard missing: never-compared → degree 0, neutral strength 1.0)
    elo = json.loads(OUT_ELO.read_text()) if OUT_ELO.exists() else {}
    strength = elo.get("strengths", {})
    degree = elo.get("n_comparisons", {})
    excluded = _judged_or_live_pids()
    cands = []
    for h, lst in by_h.items():
        for i in range(len(lst)):
            for j in range(i + 1, len(lst)):
                a, b = lst[i], lst[j]
                if a["caption"] == b["caption"]:
                    continue
                pid = _pid(a, b)
                if pid in excluded:
                    continue
                cands.append({"id": pid, "handle": h, "a": a, "b": b,
                              "sa": strength.get(a["caption"], 1.0), "sb": strength.get(b["caption"], 1.0),
                              "da": degree.get(a["caption"], 0), "db": degree.get(b["caption"], 0)})
    # GREEDY coverage: after each pick, bump a virtual degree on its two captions so the next pick
    # favors STILL-uncovered captions — otherwise one zero-degree caption dominates the whole batch.
    from collections import Counter
    used = Counter()
    picked = []
    while cands and len(picked) < n:
        def _score(c):
            close = 1.0 / (1.0 + abs(c["sa"] - c["sb"]))
            da, db = c["da"] + used[c["a"]["caption"]], c["db"] + used[c["b"]["caption"]]
            conn = 1.0 / (1.0 + da) + 1.0 / (1.0 + db)
            return (w_close * close + w_conn * conn, conn)
        best = max(cands, key=_score)
        picked.append({"id": best["id"], "handle": best["handle"], "a": best["a"], "b": best["b"]})
        used[best["a"]["caption"]] += 1
        used[best["b"]["caption"]] += 1
        cands.remove(best)
    return picked


def push_active(n=5):
    return _push(active_pairs(n))


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
    ap.add_argument("cmd", choices=["form", "push", "consume", "agreement", "active", "active-preview"])
    ap.add_argument("--n", type=int, default=4, help="pairs (per brand for form/push; total for active)")
    a = ap.parse_args()
    if a.cmd == "form":
        ps = form_pairs(a.n); print(f"formed {len(ps)} pairs → {PAIRS.name}")
    elif a.cmd == "push":
        push_cards(a.n)
    elif a.cmd == "consume":
        consume()
    elif a.cmd == "agreement":
        agreement()
    elif a.cmd == "active-preview":
        ps = active_pairs(a.n)
        print(f"active-pick proposes {len(ps)} NEW pairs (ranked by info-gain; live 11 untouched):")
        for p in ps:
            print(f"  {p['handle']}: {p['a']['caption'][:40]}  ⚔  {p['b']['caption'][:40]}")
    elif a.cmd == "active":
        push_active(a.n)


if __name__ == "__main__":
    main()
