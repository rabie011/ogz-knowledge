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
    card["pw_rank"] = p.get("pw_rank", 2)   # serving priority: bridge<active<random (lower served first)
    return card


def _push(pairs, rank=2):
    """rank = which open pairwise card the portal serves NEXT (lower first): bridge=0 (unlocks
    held-out testability), active=1 (information gain), random=2. The portal shows ONE pw card at a
    time (the 60-sec gate); without this, his scarce taps drained in created-order and the
    active/bridge ranking the producers compute was thrown away at the serving layer (Rule #6 — a
    producer's ranking the consumer ignored). Verified by tests/test_pw_serving_rank.py."""
    import queue_decision as qd
    pushed = 0
    for p in pairs:
        p.setdefault("pw_rank", rank)
        try:
            qd.push_attributed(_card_for(p), made_by="system:pairwise", via="scripts/pairwise.py",
                               reason=f"pairwise taste calibration — {p['handle']}")
            pushed += 1
        except Exception as e:
            print(f"  push failed {p['id']}: {str(e)[:50]}")
    print(f"✅ pushed {pushed} pairwise cards ({len(pairs)} pairs) to the portal")
    return pushed


def push_cards(n_per_brand=4):
    return _push(form_pairs(n_per_brand), rank=2)


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
    the live 11 are never touched. The active-vs-random benefit is now MEASURED (no longer a bare
    claim): taste_sim.py replays this exact rule on his rescued ratings → data/taste_sim.json
    (ACTIVE 7 vs RANDOM ~14.85 taps to 90%, 2.12× as of June 18). Quote that as SIM-on-rescued-
    ratings only, never as his live agreement, which stays 0-testable until his bridge taps land
    (Rule #9). This function only proposes the pairs; bridge_status() surfaces the measured number."""
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
    return _push(active_pairs(n), rank=1)


def _max_matching(nodes, adj):
    """Maximum-cardinality matching on a SMALL general graph (the per-brand live-caption graph,
    typically <=15 nodes). Returns a list of (a, b) pairs. Exact DP over the set of still-free nodes
    (memoised on the frozenset of free indices) — small enough here to be exact; above a size guard it
    falls back to a greedy maximal matching so it can never blow up (coverage is then completed by the
    spare/already-covered pass in bridge_pairs). This replaces the old greedy i<j scan, which is only
    MAXIMAL not MAXIMUM: it could leave a node unmatched while a perfect matching existed, because an
    earlier pick consumed the node's only remaining free partner (B280 — albaik's stranded pick)."""
    order = list(nodes)
    nidx = {u: i for i, u in enumerate(order)}
    adj_i = {nidx[u]: {nidx[v] for v in vs if v in nidx} for u, vs in adj.items()}
    if len(order) > 20:                       # guard: stay cheap on the rare large brand
        used, out = set(), []
        for i, u in enumerate(order):
            if i in used:
                continue
            for j in adj_i.get(i, ()):
                if j not in used:
                    out.append((u, order[j])); used.add(i); used.add(j); break
        return out
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def best(free):
        if not free:
            return ()
        u = min(free)                          # always branch on the lowest free index (canonical)
        rest = free - frozenset((u,))
        bestpairs = best(rest)                 # option: leave u unmatched
        for v in adj_i.get(u, ()):
            if v in free and v != u:
                cand = ((u, v),) + best(free - frozenset((u, v)))
                if len(cand) > len(bestpairs):
                    bestpairs = cand
        return bestpairs

    return [(order[a], order[b]) for a, b in best(frozenset(range(len(order))))]


def bridge_pairs(n=8, handle=None, exclude=None):
    """BRIDGE the disconnected graph (Step 5c, June 17). The honest held-out LIVE test
    (taste_elo.held_out_live) is 0-testable because every one of his judged captions is a SINGLETON:
    leave-one-out drops a pick when neither caption appears in any OTHER pair, so n_live_picks can
    reach 50 and still measure 0. active_pairs makes it worse — it rewards degree-0 (never-compared)
    captions and so never reuses his judged ones. bridge_pairs proposes NEW same-brand pairs that
    REUSE a caption from his live picks, pairing two of his singletons together where possible, so
    each judged caption gains a 2nd comparison and the comparison graph CONNECTS. n bridge pairs make
    up to 2n live captions held-out-testable. Like active_pairs it proposes only NEW pids (the live
    cards are never touched); the '+testable' gain is MEASURED by re-running taste_elo afterward,
    never asserted here (Rule #9). handle: restrict to ONE pilot (so a brand with stranded live
    picks — e.g. albaik — gets bridges without re-flooding a brand that already has them, Rule #10)."""
    prod = _produced()
    by_h = {}
    for c in prod:
        by_h.setdefault(c["handle"], []).append(c)
    rec = {c["caption"]: c for c in prod}                 # caption → produced record
    # his live-pick captions still in the produced pool, grouped by brand (order-preserving, unique)
    live_caps = []
    if PREFS.exists():
        for line in PREFS.read_text().splitlines():
            if not line.strip():
                continue
            p = json.loads(line)
            if p.get("source") == "seed_from_ratings":
                continue
            for c in (p.get("winner_caption", ""), p.get("loser_caption", "")):
                if c in rec:
                    live_caps.append(c)
    live_by_h = {}
    for c in dict.fromkeys(live_caps):
        live_by_h.setdefault(rec[c]["handle"], []).append(c)
    if handle is not None:
        live_by_h = {h: caps for h, caps in live_by_h.items() if h == handle}
    # `exclude` lets a caller (B281's reconcile) compute the matcher's CLEAN-SLATE target — i.e. what
    # it would want if the currently-open bridge cards weren't already on the portal — so the reconcile
    # can KEEP the open bridges it still wants instead of being forced to a disjoint set. Default None
    # preserves the never-re-push-anything-open behaviour every other caller relies on.
    excluded = _judged_or_live_pids() if exclude is None else set(exclude)

    def _new(a_rec, b_rec):
        # NEW only: neither ordering already judged/live, and not a self-pair
        if a_rec["caption"] == b_rec["caption"]:
            return None
        pid = _pid(a_rec, b_rec)
        if pid in excluded or _pid(b_rec, a_rec) in excluded:
            return None
        return pid

    picked, covered = [], set()
    # Per-brand so the --handle filter is a clean same-brand subset (Rule #10) and matching never
    # crosses brands. PASS 1 is now a MAXIMUM MATCHING among the brand's live captions — not the old
    # greedy i<j scan. Greedy consumed a caption's only free partner early and could strand a caption
    # whose sole remaining partner was its own already-judged pick-mate (excluded). albaik (10 live, 0
    # spares) hit exactly this, leaving 1 pick at degree 1 → an 11/12 ceiling (B280). A maximum
    # matching covers every live caption a perfect matching can reach (albaik: 5 cards cover all 10).
    for h, caps in live_by_h.items():
        adj = {c: [] for c in caps}
        for i in range(len(caps)):
            for j in range(i + 1, len(caps)):
                if _new(rec[caps[i]], rec[caps[j]]):
                    adj[caps[i]].append(caps[j]); adj[caps[j]].append(caps[i])
        for a, b in _max_matching(caps, adj):
            picked.append({"id": _new(rec[a], rec[b]), "handle": h, "a": rec[a], "b": rec[b]})
            covered.add(a); covered.add(b)
        # PASS 2 — every still-uncovered live caption gets one bridge so no COVERABLE caption is left
        # stranded: prefer a non-live spare partner; if the brand has none (albaik), fall back to ANY
        # NEW-allowed live caption (even an already-covered one — it only gains extra degree). A live
        # caption stays uncovered ONLY when it has no allowed partner at all in its brand.
        live_set = set(caps)
        spares = [c for c in by_h.get(h, []) if c["caption"] not in live_set]
        for a in caps:
            if a in covered:
                continue
            pid = pc = None
            for cand in spares:
                pid = _new(rec[a], cand)
                if pid:
                    pc = cand; break
            if pc is None:
                for other in caps:
                    if other != a and (pid := _new(rec[a], rec[other])):
                        pc = rec[other]; break
            if pc is not None:
                picked.append({"id": pid, "handle": h, "a": rec[a], "b": pc})
                covered.add(a)
    return picked[:n]


def push_bridge(n=8, handle=None):
    return _push(bridge_pairs(n, handle), rank=0)


def _answered_pids():
    """pids he has already TAPPED (in the answers ledger). The reconcile must never close one of these
    mid-decision: a superseded card he already touched stays open so his choice is never lost when
    consume() next runs (Consumer Law, Rule #6)."""
    seen = set()
    if ANSWERS.exists():
        for line in ANSWERS.read_text().splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            pid = e.get("item_id") or e.get("id") or e.get("card_id") or e.get("pair_id")
            if pid:
                seen.add(pid)
    return seen


def reconcile_bridges(n=50, handle=None, apply=False):
    """B281 — STAGING-AWARE bridge reconcile (SUPERSEDE, NEVER STACK — Rule #10). The improved
    maximum-matcher (B280) proposes a bridge set that beats the already-staged one (closes the 11/12
    ceiling → 12/12) but DISJOINT from it. Pushing it blind would FLOOD his portal with two competing
    bridge sets and double his pw queue. This reconciles instead: compute the matcher's CLEAN-SLATE
    target (open bridges no longer excluded, so it may re-want them), KEEP the open bridges it still
    wants, CLOSE (status→superseded) the ones it no longer wants, and PUSH ONLY the delta. A card he
    has already TAPPED is NEVER closed (Consumer Law) — it stays open until consume() banks the tap.

    Order under --apply: PUSH the delta FIRST, then CLOSE the superseded — so the live bridge set is a
    momentary SUPERSET of the target during the swap and never momentarily disconnects (a bridge must
    never reduce testability mid-operation, the invariant test_bridge.py locks). End state = the target
    set only. The +testability gain is MEASURED by re-running taste_elo/bridge_status afterward, never
    asserted here (Rule #9). Returns {target, keep, close, push, skipped_midtap}."""
    q = json.loads(QUEUE.read_text()) if QUEUE.exists() else {"items": []}
    items = q.get("items", []) if isinstance(q, dict) else q
    open_bridges = {str(c.get("id", "")): c for c in items
                    if str(c.get("id", "")).startswith("pw_") and c.get("status") == "open"
                    and c.get("pw_rank") == 0}
    answered = _answered_pids()
    # CLEAN-SLATE target: drop the currently-open bridges (and only those) from the exclusion so the
    # matcher is free to re-want them; judged picks and already-tapped/answered pw_ cards stay excluded.
    exclude = _judged_or_live_pids() - set(open_bridges)
    target = bridge_pairs(n, handle, exclude=exclude)
    tpids = {p["id"] for p in target}
    keep = set(open_bridges) & tpids
    superseded = set(open_bridges) - tpids
    close = superseded - answered
    skipped_midtap = superseded & answered
    push_pairs = [p for p in target if p["id"] not in open_bridges]
    result = {"target": len(target), "keep": len(keep), "close": len(close),
              "push": len(push_pairs), "skipped_midtap": len(skipped_midtap)}
    if apply:
        if push_pairs:
            _push(push_pairs, rank=0)                       # PUSH delta first (never disconnect)
        if close:
            q = json.loads(QUEUE.read_text())               # re-read (the push above mutated it)
            items = q.get("items", []) if isinstance(q, dict) else q
            for c in items:
                if str(c.get("id", "")) in close:
                    c["status"] = "superseded"
                    c["superseded_reason"] = ("B281: replaced by the improved maximum-matcher bridge set "
                                              "(12/12 vs the staged 11/12 held-out-testable)")
            QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
        if skipped_midtap:
            print(f"  ⚠️  kept {len(skipped_midtap)} superseded bridge card(s) OPEN — he has tapped them "
                  f"(Consumer Law); consume() will bank the tap before they are reconciled")
        print(f"✅ reconciled bridges: kept {len(keep)}, closed {len(close)}, pushed {len(push_pairs)} "
              f"(target {len(target)})")
    return result


def structural_testable(prefs, extra_edges=()):
    """A live pick (w,l) is held-out-testable iff, with it removed, BOTH its captions still appear
    in some other pair — i.e. degree(w)>=2 AND degree(l)>=2 over all edges. Pure graph structure:
    winner-INDEPENDENT and tie-free, so the number is honest regardless of who he ends up picking.

    This is an UPPER BOUND on the real consumer (taste_elo.held_out_live), NOT equal to it: degree>=2
    is NECESSARY for Bradley-Terry to rank a held-out pick but NOT sufficient — its two captions must
    also land in the same connected BT component (disjoint components tie and stay untestable). So
    BT-rankable <= structural, always. Kept only as the cheap bound the regression test locks; the
    founder-facing `after taps=N` is computed by bridge_status THROUGH the consumer, never from this
    (Rule #6/#9: the number on his phone must equal what BT delivers — June 19 it diverged 11 vs 13)."""
    from collections import Counter
    deg = Counter()
    edges = [(p.get("winner_caption", ""), p.get("loser_caption", "")) for p in prefs]
    edges += list(extra_edges)
    for a, b in edges:
        deg[a] += 1; deg[b] += 1
    live = [p for p in prefs if p.get("source") != "seed_from_ratings"]
    return sum(1 for p in live
               if deg[p.get("winner_caption", "")] >= 2 and deg[p.get("loser_caption", "")] >= 2)


def bridge_status():
    """HONEST gated-on-taps status (Step 5d, June 18). The held-out LIVE number sits at 0 not because
    the machine is broken but because his judged captions are singletons — and bridge cards that fix
    that may already be STAGED on his portal, invisibly waiting. This surfaces the wait as a verified
    number so a one-tap-session-away HOLD never reads as a stall (Rule #6: the staged bridges get a
    consumer; Rule #10: one status line, no new card). It reports the TESTABILITY unlock only — which
    is winner-INDEPENDENT (it depends purely on which captions get compared, not who he picks) — and
    deliberately does NOT quote any agreement %, because that awaits his REAL taps (Rule #9).
    Returns {staged, n_testable_now, n_testable_after}.

    THE NUMBER IS BT-TRUE, NOT A DEGREE PROXY (Rule #6/#9, fixed June 19). Earlier it reported
    structural_testable (degree>=2), which OVER-states the consumer: degree is necessary but not
    sufficient — captions in disjoint Bradley-Terry components tie and stay untestable. Two shifts
    (June 17, June 19) caught the degree proxy diverging from the real consumer; the "coincidentally
    equal" defense then DRIFTED (degree said 11 while the consumer delivered 13). So `now`/`after` are
    now computed through the real gate (taste_elo.held_out_live). `after` counts his picks PLUS the
    bridge taps as live (both are real choices) — exactly this line's own framing — so it equals what
    Bradley-Terry actually delivers once he taps. structural_testable stays only as a cheap upper bound
    for the regression test, never as the founder-facing number."""
    prefs = [json.loads(l) for l in PREFS.read_text().splitlines() if l.strip()] if PREFS.exists() else []
    live_caps = set()
    for p in prefs:
        if p.get("source") != "seed_from_ratings":
            live_caps.add(p.get("winner_caption", "")); live_caps.add(p.get("loser_caption", ""))
    live_caps.discard("")
    # staged bridges = OPEN pw_ cards on the portal that reuse one of his judged captions
    staged = []
    if QUEUE.exists():
        q = json.loads(QUEUE.read_text())
        for c in (q.get("items", []) if isinstance(q, dict) else q):
            if not str(c.get("id", "")).startswith("pw_") or c.get("status") != "open":
                continue
            opts = {o.get("v"): o.get("label") for o in (c.get("options") or [])}
            a, b = opts.get("a", ""), opts.get("b", "")
            if a and b and (a in live_caps or b in live_caps):
                staged.append((a, b))
    import taste_elo as te
    def _hl_pairs(rows):
        return [(r.get("winner_caption", ""), r.get("loser_caption", "")) for r in rows]
    _, now = te.held_out_live(_hl_pairs(prefs), prefs)
    after_rows = prefs + [{"winner_caption": a, "loser_caption": b, "source": "live_bridge"}
                          for a, b in staged]
    _, after = te.held_out_live(_hl_pairs(after_rows), after_rows)
    now, after = now or 0, after or 0
    # Rule #6: give taste_sim.json (written by taste_sim.py, today read by nothing) its consumer.
    # The MEASURED active-vs-random advantage is the honest replacement for the old unmeasured
    # "~5 taps ≈ 15" claim — surfaced here, but labelled SIM (rescued ratings), never "his agreement"
    # (Rule #9): his LIVE advantage stays 0-testable until the bridge taps land.
    sim_clause, sim = "", None
    SIM = PREFS.parent / "taste_sim.json"
    if SIM.exists():
        try:
            sim = json.loads(SIM.read_text())
            if sim.get("ok"):
                sim_clause = (f" · sim advantage (rescued ratings, NOT his live eye): ACTIVE "
                              f"{sim['active_taps_to_threshold']} vs RANDOM "
                              f"{sim['random_taps_to_threshold_mean']} taps to "
                              f"{int(sim['threshold']*100)}% = {sim['speedup_x']}× fewer")
        except Exception:
            sim = None
    # `after` is the structural degree-bound counted over his EXISTING picks; it equals the realistic
    # held_out_live only because his bridge TAPS are themselves measurable picks (his picks + the taps).
    # Said plainly so the number cannot be misread as "9 of your existing picks are eye-measured" — only
    # ~4 of the existing are BT-rankable; the rest come from the taps. Agreement % still awaits real taps.
    print(f"BRIDGE STATUS: {len(staged)} bridge cards staged on his portal · "
          f"held-out-testable picks on record now={now} → after his taps={after} "
          f"(his picks + the bridge taps, both real choices; BT-true held_out_live count, "
          f"agreement % awaits his real taps, Rule #9){sim_clause}")
    return {"staged": len(staged), "n_testable_now": now, "n_testable_after": after,
            "sim_speedup_x": (sim or {}).get("speedup_x"),
            "sim_active_taps": (sim or {}).get("active_taps_to_threshold"),
            "sim_random_taps": (sim or {}).get("random_taps_to_threshold_mean")}


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


def _live_caps():
    """His live-pick caption set (excludes rescued seeds) — same source bridge_status uses."""
    caps = set()
    if PREFS.exists():
        for line in PREFS.read_text().splitlines():
            if not line.strip():
                continue
            p = json.loads(line)
            if p.get("source") == "seed_from_ratings":
                continue
            caps.add(p.get("winner_caption", "")); caps.add(p.get("loser_caption", ""))
    caps.discard("")
    return caps


def backfill_pw_rank():
    """Repair the SERVING-RANK wire on cards that predate it (Rule #6, June 19). The serving-rank
    fix (test_pw_serving_rank.py) stamps pw_rank at push time, but every pw_ card pushed BEFORE that
    fix carries no rank, so portal_mini._single_open_pw falls back to created-order and serves a
    NON-bridge card first — his scarce taps drain on pairs that DON'T unlock held-out testability,
    the exact loss bridge_pairs was built to prevent. This re-derives the missing rank the same way
    bridge_status detects bridges (caption reuse): a card reusing one of his judged captions → 0
    (bridge, unlocks testability), else → 2 (random). Idempotent: cards that already carry pw_rank
    are untouched (active=1 tiers stay intact). Returns {scanned, bridged, randomed}."""
    if not QUEUE.exists():
        print("no queue"); return {"scanned": 0, "bridged": 0, "randomed": 0}
    q = json.loads(QUEUE.read_text())
    items = q.get("items", []) if isinstance(q, dict) else q
    live = _live_caps()
    scanned = bridged = randomed = 0
    for c in items:
        if not str(c.get("id", "")).startswith("pw_") or c.get("status") != "open":
            continue
        if c.get("pw_rank") is not None:
            continue
        scanned += 1
        opts = {o.get("v"): o.get("label") for o in (c.get("options") or [])}
        a, b = opts.get("a", ""), opts.get("b", "")
        if a and b and (a in live or b in live):
            c["pw_rank"] = 0; bridged += 1
        else:
            c["pw_rank"] = 2; randomed += 1
    if scanned:
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    print(f"✅ backfill pw_rank: {scanned} rankless open cards → {bridged} bridge(0) + {randomed} random(2)")
    return {"scanned": scanned, "bridged": bridged, "randomed": randomed}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["form", "push", "consume", "agreement", "active", "active-preview",
                                    "bridge", "bridge-preview", "bridge-status", "backfill-rank",
                                    "reconcile", "reconcile-preview"])
    ap.add_argument("--n", type=int, default=4, help="pairs (per brand for form/push; total for active)")
    ap.add_argument("--handle", default=None, help="restrict bridge to one pilot (e.g. albaik)")
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
    elif a.cmd == "bridge-preview":
        ps = bridge_pairs(a.n if a.n != 4 else 8, a.handle)
        scope = f" [{a.handle}]" if a.handle else ""
        print(f"bridge proposes {len(ps)} NEW pairs{scope} (reuse his judged captions → held-out testable):")
        for p in ps:
            print(f"  {p['handle']}: {p['a']['caption'][:40]}  ⚔  {p['b']['caption'][:40]}")
    elif a.cmd == "bridge":
        push_bridge(a.n if a.n != 4 else 8, a.handle)
    elif a.cmd == "bridge-status":
        bridge_status()
    elif a.cmd == "backfill-rank":
        backfill_pw_rank()
    elif a.cmd == "reconcile-preview":
        r = reconcile_bridges(a.n if a.n != 4 else 50, a.handle, apply=False)
        print(f"bridge reconcile (preview — supersede, never stack, Rule #10): target {r['target']} · "
              f"KEEP {r['keep']} open · CLOSE {r['close']} superseded · PUSH {r['push']} new"
              + (f" · {r['skipped_midtap']} mid-tap kept open (Consumer Law)" if r['skipped_midtap'] else ""))
    elif a.cmd == "reconcile":
        reconcile_bridges(a.n if a.n != 4 else 50, a.handle, apply=True)


if __name__ == "__main__":
    main()
