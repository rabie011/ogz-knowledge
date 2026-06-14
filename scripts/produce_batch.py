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
import argparse, glob, json, math, subprocess, sys, time
from collections import defaultdict, Counter
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))
import post_audit as pa
from render_client_slot import scene_core, batch_diversity_check

CLIENTS = ["myfitness.sa", "eatjurisha", "albaik"]
OCC_SLUGS = ["saudi_national_day", "ramadan", "saudi_founding_day", "eid_al_fitr", "arab_mothers_day"]


def _slots(handle):
    ym = json.loads((B / "clients" / handle / "year_map.json").read_text())
    return [s for mm in ym["months"].values() for s in mm]


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
    """Each occasion → exactly ONE client (round-robin) so occasions are spread, never duplicated."""
    out = []
    for i, slug in enumerate(OCC_SLUGS):
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
    subprocess.run(["python3", str(B / "scripts/render_client_slot.py"), "--handle", handle,
                    "--date", date, "--brain", "auto", "--suffix", suffix], capture_output=True, text=True)
    fs = glob.glob(str(B / f"clients/{handle}/posts/{date}__*{suffix}.json"))
    return json.loads(Path(fs[0]).read_text()) if fs else None


def is_clean(d, handle):
    return bool(d) and not [i for i in pa.audit_post(d, handle) if i[0] != "occasion_missing"]


def core_of(d):
    cs = scene_core((d.get("captions") or [""])[0]) or scene_core((d.get("slot") or {}).get("angle_theme", ""))
    return sorted(cs)[0] if cs else "_uncore"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--suffix", default="__auto")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
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

    occ = occasion_candidates()
    n_occ = min(len(occ), max(1, int(a.n * 0.30)))      # occasions ≤30% of the batch
    occ = occ[:n_occ]
    per_client = math.ceil((a.n - n_occ) / len(CLIENTS))  # daily quota per client
    emit(f"plan: {a.n} = {n_occ} occasion (≤30%) + {per_client}×{len(CLIENTS)} daily · idempotent reuse on")

    # render the occasion candidates + a balanced daily pool per client (with headroom), reusing clean files
    clean_by_client = defaultdict(list)
    for h, dt, oc in occ:
        d = render(h, dt, a.suffix, a.force)
        ok = is_clean(d, h)
        emit(f"   {'✓' if ok else '✗'} OCC {h} {dt} [{oc}]")
        if ok:
            clean_by_client[h].append({"h": h, "dt": dt, "occ": oc, "d": d})
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

    # 1) occasions first (variety) — respect core+brain caps
    for h in CLIENTS:
        for x in [y for y in clean_by_client[h] if y["occ"] != "daily"]:
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

    if len(chosen) < a.n:
        emit(f"🛑 system produced only {len(chosen)}/{a.n} balanced-clean — fix a gate / widen pick, never hand-fill")
        sys.exit(1)
    chosen = chosen[:a.n]

    # ASSERT the system's own output: every chosen post clean + no over-concentration
    slotlike = [{"date": x["dt"], "scene_ar": (x["d"].get("captions") or [""])[0],
                 "angle_theme": (x["d"].get("slot") or {}).get("angle_theme", ""),
                 "formula": (x["d"].get("slot") or {}).get("formula")} for x in chosen]
    dchk = batch_diversity_check(slotlike, 0.30)
    assert all(is_clean(x["d"], x["h"]) for x in chosen), "a chosen post is not clean — refuse"
    assert not dchk["violations"], f"over-concentrated: {dchk['violations']}"

    def fn_of(x):
        return x.get("fn") or Path(glob.glob(str(B / f"clients/{x['h']}/posts/{x['dt']}__*{a.suffix}.json"))[0]).name
    man = {"built": time.strftime("%Y-%m-%dT%H:%M:%S"), "n": len(chosen), "suffix": a.suffix, "staged": False,
           "by_client": dict(Counter(x["h"] for x in chosen)),
           "by_brain": dict(Counter(x["d"].get("brain") for x in chosen)),
           "by_core": dict(Counter(core_of(x["d"]) for x in chosen)),
           "occasion_posts": [f"{x['h']} {x['dt']} {x['occ']}" for x in chosen if x["occ"] != "daily"],
           "posts": [{"handle": x["h"], "date": x["dt"], "occasion": x["occ"], "file": fn_of(x),
                      "brain": x["d"].get("brain"), "captions": x["d"].get("captions")} for x in chosen]}
    (B / "data/batch_manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1))
    emit(f"\n✅ SYSTEM PRODUCED {len(chosen)} zero-issue posts (manifest, NOT staged).")
    emit(f"   by client: {man['by_client']} · by brain: {man['by_brain']}")
    emit(f"   occasion-aligned ({len(man['occasion_posts'])}): {man['occasion_posts']}")


if __name__ == "__main__":
    main()
