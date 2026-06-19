#!/usr/bin/env python3
"""B173 — format_fit_gap.py: surface-format fit between what the engine CAN make and what it SHIPS.

THE GAP (traces to THE TOP — "a post Mohamed would publish"): a real Instagram brand lives across
FOUR surfaces — feed_single, carousel, story, reel. This measures, deterministically and with zero
LLM, two things and the divergence between them:

  SUPPLY    — the 127-chain visual library, classified by output_type → which surfaces it CAN feed.
  PRODUCED  — every pilot post on disk, classified by its actual structure → which surface it IS.

The finding this organ exists to surface (Rule #11 diagnose, Rule #12 the system produces — this only
MEASURES, it writes no content): the engine is feed-single shaped. carousel chains exist but ship 0;
story/reel have neither supply nor production. A future format-aware router (a downstream consumer,
Rule #6) reads data/format_fit_gap.json to know which surfaces are dark before it claims coverage.

Commands:
  summary  — human table: supply vs produced per surface + the gap verdict.
  json     — write/refresh data/format_fit_gap.json (the organ) and print it.
  verify   — REFUSE-guard (Rule #8): exit non-zero if the report is internally inconsistent
             (counts don't reconcile to totals, or a surface claims production with zero supply).

A surface is DARK = 0 produced. A surface is STARVED = 0 supply (the library literally can't make it).
Neither is fixed here — this is the honest signal that drives the backlog; it never invents content.
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
CHAIN_INDEX = BASE / "02_what_to_build" / "INDEX.json"
POSTS_GLOB = "clients/*/posts/*.json"
OUT = BASE / "data" / "format_fit_gap.json"

# The four Instagram surfaces a real brand publishes across. Order = feed-first reality.
SURFACES = ["feed_single", "carousel", "story", "reel"]

# chain output_type -> the surface that output natively supplies.
# image  -> a single feed image (the engine's default and only shipped shape)
# carousel -> a multi-frame carousel
# video  -> a reel (vertical motion); story is a secondary home, but we credit the primary surface
OUTPUT_TYPE_TO_SURFACE = {
    "image": "feed_single",
    "carousel": "carousel",
    "video": "reel",
}


def classify_chain(output_type):
    """Map a chain's output_type to the surface it supplies. Unknown types -> None (uncredited)."""
    return OUTPUT_TYPE_TO_SURFACE.get((output_type or "").strip().lower())


def classify_post(post):
    """Classify a produced post by its ON-DISK structure — never by any self-declared label.

    The structural truth: a post carries ONE `visual` dict (a single rendered asset) and 1-3 caption
    variants of one idea => feed_single. A multi-asset `visual` (list / explicit frames) => carousel.
    This is intentionally structural so a mislabeled post can't fake a surface it didn't actually ship.
    """
    v = post.get("visual")
    if isinstance(v, list) and len(v) > 1:
        return "carousel"
    if isinstance(v, dict) and isinstance(v.get("frames"), list) and len(v["frames"]) > 1:
        return "carousel"
    # a single visual asset (dict) or a lone string => a single feed image
    if v is not None:
        return "feed_single"
    return None  # no visual -> uncountable as a shipped surface


def load_chains():
    return json.loads(CHAIN_INDEX.read_text())["chains"]


def iter_posts():
    for f in sorted(BASE.glob(POSTS_GLOB)):
        try:
            yield json.loads(f.read_text())
        except Exception:
            continue


def build_gap(chains=None, posts=None):
    """Pure core — injectable so the report is testable with crafted fixtures.

    Returns the gap organ: per-surface supply & produced counts + a status verdict + totals.
    status: LIVE (supply>0, produced>0) · DARK (supply>0, produced=0) · STARVED (supply=0).
    """
    chains = load_chains() if chains is None else chains
    posts = list(iter_posts()) if posts is None else posts

    supply = {s: 0 for s in SURFACES}
    uncredited_chains = 0
    for c in chains:
        s = classify_chain(c.get("output_type"))
        if s in supply:
            supply[s] += 1
        else:
            uncredited_chains += 1

    produced = {s: 0 for s in SURFACES}
    uncountable_posts = 0
    for p in posts:
        s = classify_post(p)
        if s in produced:
            produced[s] += 1
        else:
            uncountable_posts += 1

    surfaces = {}
    for s in SURFACES:
        if supply[s] == 0:
            status = "STARVED"  # library can't even make it
        elif produced[s] == 0:
            status = "DARK"     # can make it, never ships it
        else:
            status = "LIVE"
        surfaces[s] = {"supply_chains": supply[s], "produced_posts": produced[s], "status": status}

    return {
        "_meta": {
            "id": "B173",
            "what": "Format-fit gap: chain SUPPLY vs post PRODUCTION across the 4 IG surfaces.",
            "rule_basis": "Rule #11 (diagnose, don't barrel) · #12 (measure only, the system produces) · #6 (a downstream format-router is the reader).",
            "note": "Structural classification only — a post's surface is read from its on-disk shape, never a self-label.",
        },
        "surfaces": surfaces,
        "totals": {
            "chains": len(chains),
            "posts": len(posts),
            "uncredited_chains": uncredited_chains,
            "uncountable_posts": uncountable_posts,
        },
        "dark": [s for s in SURFACES if surfaces[s]["status"] == "DARK"],
        "starved": [s for s in SURFACES if surfaces[s]["status"] == "STARVED"],
    }


def verify(report=None):
    """Rule #8 refuse-guard. Returns a list of inconsistency errors ([] = clean)."""
    r = report if report is not None else build_gap()
    errs = []
    t = r["totals"]
    sup = sum(s["supply_chains"] for s in r["surfaces"].values())
    if sup + t["uncredited_chains"] != t["chains"]:
        errs.append(f"supply {sup}+{t['uncredited_chains']} != total chains {t['chains']}")
    prod = sum(s["produced_posts"] for s in r["surfaces"].values())
    if prod + t["uncountable_posts"] != t["posts"]:
        errs.append(f"produced {prod}+{t['uncountable_posts']} != total posts {t['posts']}")
    for name, s in r["surfaces"].items():
        if s["produced_posts"] > 0 and s["supply_chains"] == 0:
            errs.append(f"surface '{name}' ships {s['produced_posts']} posts with ZERO supply — impossible")
        if s["status"] == "STARVED" and s["supply_chains"] != 0:
            errs.append(f"surface '{name}' STARVED but supply={s['supply_chains']}")
        if s["status"] == "DARK" and (s["supply_chains"] == 0 or s["produced_posts"] != 0):
            errs.append(f"surface '{name}' DARK but supply={s['supply_chains']} produced={s['produced_posts']}")
    return errs


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "summary"
    r = build_gap()
    if cmd == "verify":
        errs = verify(r)
        if errs:
            print("🔴 format_fit_gap VERIFY FAILED:")
            for e in errs:
                print("  -", e)
            sys.exit(1)
        print("✅ format_fit_gap consistent")
        return
    if cmd == "json":
        OUT.write_text(json.dumps(r, indent=2, ensure_ascii=False))
        print(f"✅ wrote {OUT.relative_to(BASE)}")
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    # summary
    print(f"FORMAT-FIT GAP — {r['totals']['chains']} chains supply · {r['totals']['posts']} posts produced")
    print(f"  {'surface':<13} {'supply':>7} {'produced':>9}  status")
    for s in SURFACES:
        d = r["surfaces"][s]
        print(f"  {s:<13} {d['supply_chains']:>7} {d['produced_posts']:>9}  {d['status']}")
    if r["dark"]:
        print(f"  DARK (can make, ships 0): {', '.join(r['dark'])}")
    if r["starved"]:
        print(f"  STARVED (no library supply): {', '.join(r['starved'])}")


if __name__ == "__main__":
    main()
