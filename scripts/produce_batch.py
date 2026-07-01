#!/usr/bin/env python3
"""THE SELF-PRODUCING BATCH PIPELINE (Mohamed 2026-06-14: "the system must produce by itself —
all results from the system; we only fix the machine"). ONE command, ZERO hand-work:

  PICK  — the system chooses diverse slots itself, BALANCED across the 3 pilots (≈n/3 each), with
          DISTINCT theme-cores, plus a CAPPED set of real occasion posts (each occasion assigned to
          ONE client round-robin — never the same occasion on every client). Nothing hardcoded.
  RENDER— interleaved round-robin across clients (so every client is represented even if it stops
          early), through the gated pipeline. Idempotent: a slot already rendered+clean is reused.
  AUDIT — post_audit every post (caption + visual + theme doors). Any issue → DROP.
  BACKFILL— per client: if a client is short of its quota, the system picks MORE of THAT client's
          unused slots and renders, until balanced or it gives up LOUDLY (never short, never hand-filled).
  SELECT— balanced n (≈n/3 per client), occasion ≤30%, no scene-core >30% — all computed, no hardcoded drops.
  MANIFEST— writes data/batch_manifest.json (staged:false). Staging is a SEPARATE gated step.

Usage: python3 scripts/produce_batch.py [--n 20] [--suffix __auto] [--force]
"""
import argparse, glob, json, math, os, subprocess, sys, time
from collections import defaultdict, Counter
from pathlib import Path

B = Path(__file__).parent.parent

# HEADLESS RESILIENCE (B284, June 22 — the 2026-06-22 orchestra stall): the per-slot render
# child (render_client_slot.py) makes external LLM calls and could block at ~0 CPU indefinitely
# (a hung socket, a future blocking call). With no ceiling, ONE stuck slot froze the whole
# unattended batch — which starved the taste→creation wire. A producer that cannot run headless
# is broken. So every slot render is bounded: on timeout the child is killed, the slot fails
# LOUDLY (Rule #8 — refuse, don't hang), render() returns None, and the round-robin moves on
# (the design already represents every client even if one stops early). The child's own LLM
# calls cap at 120s each (max two on the gpt→sonnet fallback path), so 300s covers a slow-but-
# legit slot while still killing a true hang. Override via PRODUCE_SLOT_TIMEOUT (0 = no cap).
SLOT_TIMEOUT = int(os.environ.get("PRODUCE_SLOT_TIMEOUT", "300"))
# PANEL (W1/W3, June 23): when on, each slot's angle is born from the 5-CD-brain PANEL across
# DIFFERENT models (GPT/Gemini/Groq via consult.py). Set by --panel or PRODUCE_PANEL=1. Off by
# default so the cheap single-pen path stays the baseline (money discipline) until flipped on.
PANEL = os.environ.get("PRODUCE_PANEL", "") == "1"
sys.path.insert(0, str(B / "scripts"))
import post_audit as pa
import render_reel as rr
import taste_rank as tr
import gen_identity
import gate_state
from render_client_slot import scene_core, batch_diversity_check

# IMAGE RENDER PATH (June 21 — WIRE THE MASTER): the v3.7 MASTER is the correct image path —
# scripts/render_via_master.py(handle, date) loads a chosen post card, resolves its content-aware
# chain, runs openclaw_convert (→ the full 15-block v3.7 prompt + the REAL brand reference), then
# render_openclaw (flux-2-pro/edit, GATED, dry by default). render_image.py (schnell + an improvised
# string) is the WRONG shortcut and is NOT used here. When the still-render step is wired into this
# batch (behind the same money-gate the reel step already respects), it must call render_via_master —
# never render_image.py. Today the gates hold, so the master path runs DRY (prompt + fill-report only,
# zero spend); produce_batch stays at manifest-of-cards until Mohamed flips no_fal_photos + the key.

# REEL WIRING (June 18, Rule #6 — render_reel is a writer; here it finally gets its reader). A
# slot whose COMPUTED format=='reel' (set in year_map.py off real_winning_formula.json) is
# reel-ified — but ONLY by assembling an ALREADY-ON-DISK still into a 9:16 mp4 ($0 ffmpeg+Pillow,
# the ungated lever). If no still exists yet (today's gated-pilot reality) the manifest marks
# reel_pending and NO fal render is triggered. Reel emission is purely off slot['format'], never a
# hand-authored list → Rule #12 holds.
REELS = B / "data/reels"   # mp4 output dir (created at runtime, only when a reel actually assembles)

# REAL-engagement scoring head (June 18): rank candidates by what actually won (real_winning_formula),
# NOT the random LLM enum. v1 scores by occasion-lift (the trait fresh candidates reliably carry);
# richer traits (emotion/pillar/media) need the candidate analyzed (next step). Behind --rank (default off).
_WF = Path(__file__).parent.parent / "data/real_winning_formula.json"
def _lift(occ):
    try:
        wf = json.loads(_WF.read_text()).get("trait_lift", {}).get("occasion", {})
        return wf.get(occ or "", {}).get("lift", 1.0)
    except Exception:
        return 1.0

CLIENTS = ["myfitness.sa", "eatjurisha", "albaik"]
OCC_SLUGS = ["saudi_national_day", "ramadan", "saudi_founding_day", "eid_al_fitr", "arab_mothers_day"]


def _slots(handle):
    ym = json.loads((B / "clients" / handle / "year_map.json").read_text())
    return [s for mm in ym["months"].values() for s in mm]


def must_cover_majors():
    """The MAJOR occasions the batch MUST represent (June 18 — white_friday + eid_al_adha were
    silently dropped by the 30% cap; coverage is now RESERVED before any cap, Rule #8: never
    silently omit a major). A slot is a must-cover anchor iff it's marked major AND it is the
    occasion's central moment (beat=='day_of' OR anchor==True). Read from the regenerated
    year_maps, NEVER a hand list — so a year-map edit propagates automatically (Rule #12).
    Returns the set of distinct major occasion SLUGS present across the pilots' year_maps."""
    majors = set()
    for h in CLIENTS:
        for s in _slots(h):
            if s.get("occasion") and s.get("major") and (s.get("beat") == "day_of" or s.get("anchor")):
                majors.add(s["occasion"])
    return majors


def daily_candidates(handle, n):
    """n daily slots with DISTINCT theme-tags (core variety), spread within each tag."""
    by_tag = defaultdict(list)
    for s in _slots(handle):
        if s.get("type") in ("daily", "evergreen", "ramadan_evergreen") and not s.get("occasion"):
            by_tag[(s.get("angle_theme") or "").split(":")[0][:24]].append(s)
    out, tags, i = [], list(by_tag), 0
    while len(out) < n and any(by_tag.values()):
        t = tags[i % len(tags)]; i += 1
        if by_tag[t]:
            out.append(by_tag[t].pop(len(by_tag[t]) // 2))
    return [(handle, s["date"], "daily") for s in out]


def occasion_candidates():
    """Each occasion → exactly ONE client (round-robin) so occasions are spread, never duplicated.
    The candidate set is OCC_SLUGS (variety) UNIONED with every must-cover major (June 18 — the
    hardcoded 5-slug subset omitted white_friday + eid_al_adha entirely, so the cap had nothing to
    keep). Majors lead the list so they get the first, cleanest client assignment. Derived from the
    year_maps, never a curated date list (Rule #12)."""
    majors = must_cover_majors()
    slugs = [s for s in OCC_SLUGS if s in majors] + sorted(majors - set(OCC_SLUGS)) \
        + [s for s in OCC_SLUGS if s not in majors]
    out = []
    for i, slug in enumerate(slugs):
        h = CLIENTS[i % len(CLIENTS)]
        cands = [s for s in _slots(h) if s.get("occasion") == slug and s.get("beat") == "day_of"] \
            or [s for s in _slots(h) if s.get("occasion") == slug]
        if cands:
            out.append((h, cands[0]["date"], slug))
    return out


def render(handle, date, suffix, force=False):
    fs = glob.glob(str(B / f"clients/{handle}/posts/{date}__*{suffix}.json"))
    if fs and not force:  # idempotent reuse — don't re-spend on a slot already rendered
        try:
            return json.loads(Path(fs[0]).read_text())
        except Exception:
            pass
    try:
        cmd = ["python3", str(B / "scripts/render_client_slot.py"), "--handle", handle,
               "--date", date, "--brain", "auto", "--suffix", suffix]
        if PANEL:
            cmd.append("--panel")
        subprocess.run(cmd, capture_output=True, text=True,
                       timeout=(SLOT_TIMEOUT if SLOT_TIMEOUT > 0 else None))
    except subprocess.TimeoutExpired:
        # the child hung past the ceiling — it was killed. Fail this slot LOUDLY and return None
        # so is_clean()→False and the round-robin continues; never freeze the headless batch.
        print(f"   🛑 SLOT TIMEOUT {handle} {date} — render child exceeded {SLOT_TIMEOUT}s, killed; "
              f"slot dropped (Rule #8, B284). Batch continues.", flush=True)
        return None
    fs = glob.glob(str(B / f"clients/{handle}/posts/{date}__*{suffix}.json"))
    return json.loads(Path(fs[0]).read_text()) if fs else None


def is_clean(d, handle):
    return bool(d) and not [i for i in pa.audit_post(d, handle) if i[0] != "occasion_missing"]


def core_of(d):
    cs = scene_core((d.get("captions") or [""])[0]) or scene_core((d.get("slot") or {}).get("angle_theme", ""))
    return sorted(cs)[0] if cs else "_uncore"


def _still_for(handle, date):
    """Resolve a generated still co-located with the post, or None. NO fal, NO download, NO render —
    returns a path ONLY if it ALREADY exists on disk (this is the hard money-gate guard: assembly
    can never trigger a new fal spend). Glob over the system's per-slot still naming."""
    for cand in (glob.glob(str(B / f"clients/{handle}/posts/{date}__*.jpg"))
                 + glob.glob(str(B / f"clients/{handle}/posts/{date}__*.png"))):
        if Path(cand).exists():
            return cand
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--suffix", default="__auto")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--rank", action="store_true", help="rank candidates by REAL-engagement occasion-lift (June 18)")
    ap.add_argument("--daily-only", dest="daily_only", action="store_true",
                    help="first-proof/near-term mode: daily posts only, NO occasion reservation (June 19)")
    ap.add_argument("--panel", action="store_true",
                    help="born-from-the-minds mode: each angle from the 5-CD-brain PANEL on DIFFERENT "
                         "models (GPT/Gemini/Groq); the lead leads, rivals seed the caption (W1/W3, June 23)")
    a = ap.parse_args()
    global PANEL
    if a.panel:
        PANEL = True
    log = B / "data/produce_batch.log"; lines = []

    def emit(s):
        lines.append(s); log.write_text("\n".join(lines)); print(s)

    # PHASE 2: the C-suite STRATEGY STAGE runs first (research → analyse the full organs → brief),
    # so the CD brains produce INSIDE the CEO frame. Idempotent: only (re)built if the brief is
    # missing or stale (>7 days); the CD brains read clients/<h>/profile/strategy_brief.json.
    import subprocess as _sp
    for h in CLIENTS:
        sb = B / "clients" / h / "profile" / "strategy_brief.json"
        stale = (not sb.exists())
        if not stale:
            try:
                import datetime as _dt
                built = json.loads(sb.read_text()).get("built", "")
                stale = bool(built) and (time.strftime("%Y-%m-%d") > built[:10])  # rebuilt daily at most
            except Exception:
                stale = True
        if stale:
            _sp.run(["python3", str(B / "scripts/client_strategy.py"), "--handle", h], capture_output=True, text=True)
            emit(f"   ◆ strategy brief refreshed for {h}")

    majors = must_cover_majors()
    clean_by_client = defaultdict(list)
    if getattr(a, "daily_only", False):
        # FIRST-PROOF / NEAR-TERM mode (June 19): daily posts ONLY, NO occasion reservation. The
        # major-coverage guarantee is right for an ongoing calendar but wrong for the first proof
        # batch — the big occasions are months out, undrafted, and need a funded caption model. This
        # is a batch MODE, not a hand-pick: the system still PICKS its daily slots by rule (Rule #12
        # intact). Occasions enter a later batch; verify_chain --daily-only matches this contract.
        occ, must_occ, n_occ = [], [], 0
        per_client = math.ceil(a.n / len(CLIENTS))
        emit(f"plan: {a.n} = DAILY-ONLY (near-term first-proof, no occasion reservation) · "
             f"{per_client}×{len(CLIENTS)} daily · idempotent reuse on")
    else:
        occ = occasion_candidates()
        # RESERVE must-cover majors BEFORE the 30% truncation (June 18 — white_friday + eid_al_adha
        # were silently dropped when the cap sliced the occasion list; Rule #8: a major is never
        # silently omitted). Majors lead, so even if the occasion budget is < their count the cap is
        # RAISED to keep them (a loud line, never a silent drop). Derived from year_maps, no hand list.
        must_occ = [t for t in occ if t[2] in majors]            # (handle, date, slug) for each must-cover major
        rest_occ = [t for t in occ if t[2] not in majors]
        n_occ_budget = min(len(occ), max(1, int(a.n * 0.30)))    # the diversity target (≤30%)
        n_occ = max(n_occ_budget, len(must_occ))                 # RAISE the cap rather than drop a major
        if n_occ > n_occ_budget:
            emit(f"   ⚠ occasion cap RAISED {n_occ_budget}→{n_occ}: {len(must_occ)} must-cover majors "
                 f"({[t[2] for t in must_occ]}) exceed the 30% budget — Rule #8: keep majors, never silently drop")
        occ = (must_occ + rest_occ)[:n_occ]                      # majors first → survive the slice
        per_client = math.ceil((a.n - n_occ) / len(CLIENTS))  # daily quota per client
        emit(f"plan: {a.n} = {n_occ} occasion ({len(must_occ)} must-cover majors reserved) + {per_client}×{len(CLIENTS)} daily · idempotent reuse on")
        # render the occasion candidates + a balanced daily pool per client (with headroom), reusing clean files
        clean_majors = set()                                      # which must-cover majors produced a clean card
        for h, dt, oc in occ:
            d = render(h, dt, a.suffix, a.force)
            ok = is_clean(d, h)
            emit(f"   {'✓' if ok else '✗'} OCC {h} {dt} [{oc}]")
            if ok:
                clean_by_client[h].append({"h": h, "dt": dt, "occ": oc, "d": d})
                if oc in majors:
                    clean_majors.add(oc)
        # Rule #8 — a reserved major with NO clean card is made LOUD (never a silent absence). The
        # batch is not aborted (other posts are valid) but the missing major is named so the gap is
        # visible to the producer log + the downstream verify_chain gate.
        missing_majors = {t[2] for t in must_occ} - clean_majors
        for m in sorted(missing_majors):
            emit(f"   🛑 MUST-COVER MAJOR «{m}» has NO clean produced card — coverage GAP (fix the gate / "
                 f"the slot, never hand-fill). verify_chain will REFUSE on this until covered.")
    for h in CLIENTS:
        need = per_client + 4  # headroom for drops
        for (hh, dt, oc) in daily_candidates(h, need):
            if sum(1 for x in clean_by_client[h] if x["occ"] == "daily") >= per_client + 2:
                break
            d = render(hh, dt, a.suffix, a.force)
            ok = is_clean(d, hh)
            emit(f"   {'✓' if ok else '✗'} {hh} {dt}")
            if ok:
                clean_by_client[h].append({"h": hh, "dt": dt, "occ": oc, "d": d, "fn": Path(glob.glob(str(B / f'clients/{hh}/posts/{dt}__*{a.suffix}.json'))[0]).name})
            time.sleep(0.5)

    # SELECT: balanced per client, occasion ≤30%, no scene-core >30%, no single BRAIN >35%
    # (brain cap added June 14 — one brain's signature dominating reads as "same creative").
    cap_core = max(1, int(a.n * 0.30))
    cap_brain = max(2, int(a.n * 0.35))
    chosen, core_n, brain_n = [], Counter(), Counter()

    def take(x):
        chosen.append(x); core_n[core_of(x["d"])] += 1; brain_n[x["d"].get("brain")] += 1

    def blocked(x, relax_brain=False, relax_core=False):
        c = core_of(x["d"]); br = x["d"].get("brain")
        if not relax_core and c != "_uncore" and core_n[c] >= cap_core:
            return True
        if not relax_brain and brain_n[br] >= cap_brain:
            return True
        return False

    # REAL-engagement ranking (June 18, --rank): within each client, prefer higher occasion-lift
    # candidates so the producer leans toward what actually won — within the balance/cap structure,
    # not replacing it. Default off → selection order byte-identical.
    if getattr(a, "rank", False):
        for h in CLIENTS:
            clean_by_client[h].sort(key=lambda x: _lift(x["occ"]), reverse=True)

    # 1) occasions first (variety). MUST-COVER MAJORS are RESERVED — taken BEFORE the diversity
    #    caps and bypassing them (Rule #8: a major is kept, never dropped by a core/brain cap).
    #    Each major is seated once (its first clean client). Then the rest of the occasions are
    #    taken respecting the caps.
    seated_major = set()
    for h in CLIENTS:
        for x in [y for y in clean_by_client[h] if y["occ"] in majors]:
            if len(chosen) < a.n and x["occ"] not in seated_major:
                take(x); seated_major.add(x["occ"])          # reserved → ignore caps
    for h in CLIENTS:
        for x in [y for y in clean_by_client[h] if y["occ"] != "daily" and y not in chosen]:
            if len(chosen) < a.n and not blocked(x):
                take(x)
    # 2) round-robin daily across clients to EQUALIZE TOTALS (a client with more occasions gets
    #    fewer daily) — cap each client at ceil(n/clients) so all three end ≈balanced.
    cap_client = math.ceil(a.n / len(CLIENTS))
    pools = {h: [y for y in clean_by_client[h] if y["occ"] == "daily"] for h in CLIENTS}
    for relax_b, relax_cap in ((False, False), (True, False), (True, True)):
        progress = True
        while len(chosen) < a.n and progress:
            progress = False
            for h in CLIENTS:
                if not relax_cap and len([c for c in chosen if c["h"] == h]) >= cap_client:
                    continue
                taken = None
                for x in pools[h]:
                    if not blocked(x, relax_brain=relax_b):
                        taken = x; break
                if taken:
                    pools[h].remove(taken); take(taken); progress = True
                if len(chosen) >= a.n:
                    break
    # 3) last resort: fill remainder ignoring caps, keeping clients balanced
    if len(chosen) < a.n:
        leftovers = [y for h in CLIENTS for y in clean_by_client[h] if y not in chosen]
        for x in sorted(leftovers, key=lambda y: len([c for c in chosen if c["h"] == y["h"]])):
            if len(chosen) >= a.n:
                break
            take(x)

    # SHADOW ADVISORY helper — the TASTE→CREATION wire's end consumer at the real seam (B266, Rule #6).
    # taste_rank reads Mohamed's learned taste-strengths (taste_elo's write-only organ). We call it over
    # the system's CHOSEN captions and record what it WOULD prefer — but while its gate is closed (his
    # bridge taps not yet landed → held-out LIVE undefined) it steers NOTHING: select() returns the
    # captions in original order, so ship order is byte-identical (Rule #8: the influence path is closed,
    # not whispering; Rule #9: no unverified signal touches what ships). When his taps land, wire_live()
    # flips and this same call reorders — no rewrite, the consumer already exists.
    # The measurement is recorded over WHATEVER clean set the system produced — INDEPENDENT of the
    # ship-balance gate below, so the divergence FLOOR fills even on a short batch (a valid n>=2
    # measurement was being discarded when the batch couldn't balance — Rule #6). append_shadow_log
    # self-refuses n<MIN_ORDERABLE_N at the source (Rule #8). Returns the taste_advisory for the manifest.
    def _record_shadow(chosen_list):
        caps = [(x["d"].get("captions") or [""])[0] for x in chosen_list]
        ordered, ta = tr.select(caps)
        assert ta["wire_live"] or ordered == caps, \
            "taste wire gate closed but ship order changed — refuse (Rule #8)"
        sh = tr.append_shadow_log(tr.shadow_entry(ordered, ta, baseline_caps=caps))
        emit(f"   taste→creation wire: {'🟢 LIVE — steered selection' if ta['wire_live'] else '⚪ SHADOW — advisory only, ship order unchanged'} "
             f"(n_testable={ta['n_testable']}, live_pct={ta['live_pct']}, order_diff={sh['order_diff']}/{sh['n']})")
        return {"wire_live": ta["wire_live"], "n_testable": ta["n_testable"],
                "live_pct": ta["live_pct"], "steered_ship_order": ta["wire_live"],
                "advisory_rank": ta["advisory_rank"]}

    if len(chosen) < a.n:
        # capture the divergence over the clean set BEFORE refusing to ship short — the measurement is
        # independent of the ship-balance gate (Rule #6: a writer with no reader is a lie; here the
        # measurement was being dropped on every short batch, starving the FLOOR).
        _record_shadow(chosen)
        emit(f"🛑 system produced only {len(chosen)}/{a.n} balanced-clean — fix a gate / widen pick, never hand-fill")
        sys.exit(1)
    chosen = chosen[:a.n]

    # ASSERT the system's own output: every chosen post clean + no over-concentration
    slotlike = [{"date": x["dt"], "scene_ar": (x["d"].get("captions") or [""])[0],
                 "angle_theme": (x["d"].get("slot") or {}).get("angle_theme", ""),
                 "formula": (x["d"].get("slot") or {}).get("formula")} for x in chosen]
    dchk = batch_diversity_check(slotlike, 0.30)
    assert all(is_clean(x["d"], x["h"]) for x in chosen), "a chosen post is not clean — refuse"
    # over-concentration is DEGENERATE for a tiny batch (1 post is trivially 100% of its own recipe/
    # core) — only assert diversity once the batch is large enough for the % to mean something. The
    # per-post cleanliness assert above still bites at any n. (June 21: n=1 post-#1-first proof.)
    if len(chosen) >= 4:
        assert not dchk["violations"], f"over-concentrated: {dchk['violations']}"

    def fn_of(x):
        return x.get("fn") or Path(glob.glob(str(B / f"clients/{x['h']}/posts/{x['dt']}__*{a.suffix}.json"))[0]).name

    def cardpath_of(x):
        # the ABSOLUTE on-disk path of the chosen post card — so render + stage + judge-seed
        # consume the SAME computed set instead of independently re-globbing (Rule #6/#12: one
        # computed pick, many readers — no three re-pickers drifting apart).
        return str(B / f"clients/{x['h']}/posts/{fn_of(x)}")

    def _post_entry(x):
        # media format is the COMPUTED slot['format'] (year_map, off real_winning_formula) — never a
        # hand list (Rule #12). A 'reel' slot is assembled from an already-on-disk still ($0); if no
        # still yet, it's marked reel_pending and NO fal is triggered (Rule #8: loud, never silent).
        fmt = (x["d"].get("slot") or {}).get("format", "image")
        _file = fn_of(x)
        # B095v step 1 — stamp the BEDROCK identity layer at produce time (Rule #6: one source for
        # generation ids; Rule #12: identity only, no output content touched). These are the join
        # keys the publish-confirm card (step 2, staged) and both outcome readers consume; minted
        # deterministically so re-runs keep the same id for the same piece.
        e = {"handle": x["h"], "date": x["dt"], "occasion": x["occ"], "file": _file,
             "subject_generation_ulid": gen_identity.subject_generation_ulid(x["h"], x["dt"], _file),
             "brand_ulid": gen_identity.brand_ulid(x["h"]),
             "card_path": cardpath_of(x),
             # B_gate_state (Rule #6, live consumer): the machine's autonomy for this slot's occasion
             # family. Fail-closed to SAMPLED — every slot needs the human eye until a human sets the
             # family's active_level=FULL (AI never advances). B_occasion_crit will branch on this.
             "gate_mode": gate_state.gate_mode(x["h"], x["occ"] or "daily"),
             "brain": x["d"].get("brain"), "captions": x["d"].get("captions"), "media": fmt}
        if fmt == "reel":
            still = _still_for(x["h"], x["dt"])
            cap = (x["d"].get("captions") or [""])[0]   # caption from the post card, never a literal
            if still:
                REELS.mkdir(parents=True, exist_ok=True)
                outp = str(REELS / f"{x['h']}_{x['dt']}.mp4")
                try:
                    rr.render(still, cap, outp)         # $0 ffmpeg+Pillow over an existing still — no fal
                    e["reel_path"] = outp
                    _fr = outp.replace(".mp4", "_frame.jpg")
                    if Path(_fr).exists():              # preview frame is best-effort — only claim a real file
                        e["frame_path"] = _fr
                except SystemExit as ex:                # ffmpeg/font/missing-image refusal → degrade this one
                    e["media"] = "image"; e["reel_error"] = str(ex)[:120]
                    emit(f"   ⚠ reel ffmpeg/refuse {x['h']} {x['dt']} — fell back to image: {str(ex)[:80]}")
                except Exception as ex:                 # any Pillow/draw error → degrade, never abort the batch
                    e["media"] = "image"; e["reel_error"] = str(ex)[:120]
                    emit(f"   ⚠ reel render error {x['h']} {x['dt']} — fell back to image: {str(ex)[:80]}")
            else:
                e["reel_pending"] = True                # gated-pilot: still not generated yet — zero spend
                emit(f"   ⏳ reel slot {x['h']} {x['dt']}: no still yet (awaits the $3 no_fal+key tap) — manifest marks reel_pending, NO fal triggered")
        return e

    # B267/B268 — record this full-batch run to the append-only divergence history so active-pick-vs-
    # random can be MEASURED at the real seam once the gate opens (not just the rescued-seed sim —
    # Rule #9). Same helper as the short-batch path above: the system's PRE-taste selection is the
    # control baseline, taste's order is what it WOULD ship (== baseline while the gate is closed).
    taste_advisory = _record_shadow(chosen)

    man = {"built": time.strftime("%Y-%m-%dT%H:%M:%S"), "n": len(chosen), "suffix": a.suffix, "staged": False,
           "taste_advisory": taste_advisory,
           "by_client": dict(Counter(x["h"] for x in chosen)),
           "by_brain": dict(Counter(x["d"].get("brain") for x in chosen)),
           "by_core": dict(Counter(core_of(x["d"]) for x in chosen)),
           "occasion_posts": [f"{x['h']} {x['dt']} {x['occ']}" for x in chosen if x["occ"] != "daily"],
           "posts": [_post_entry(x) for x in chosen]}
    (B / "data/batch_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1))
    emit(f"\n✅ SYSTEM PRODUCED {len(chosen)} zero-issue posts (manifest, NOT staged).")
    emit(f"   by client: {man['by_client']} · by brain: {man['by_brain']}")
    emit(f"   occasion-aligned ({len(man['occasion_posts'])}): {man['occasion_posts']}")
    _reels = sum(1 for p in man["posts"] if p.get("media") == "reel")
    _pend = sum(1 for p in man["posts"] if p.get("reel_pending"))
    emit(f"   reels: {_reels} (computed format) · {_reels - _pend} assembled $0 · {_pend} reel_pending (no still yet, NO fal)")


if __name__ == "__main__":
    # B285 (June 22): hold the in-flight lock for the WHOLE run so the ogz_enricher `git add -A`
    # cycle never banks a partial/aborted batch (the 2026-06-22 scar, reverted abafc540). The lock
    # is the ONE source the enricher reads to defer its commit. try/finally releases it on every
    # path Python can unwind; a SIGKILL leaves it, but the enricher sweeps stale locks (TTL + PID).
    import produce_lock
    produce_lock.acquire()
    try:
        main()
    finally:
        produce_lock.release()
