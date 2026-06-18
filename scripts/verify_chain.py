#!/usr/bin/env python3
"""THE COMPLETE-POST CHAIN PROOF — $0, BITING (June 18).

The chain: produce_batch (COMPUTED pick → data/batch_manifest.json) → render_image (writes the
file to api/static/renders/<stem>.jpg and sets card['visual']['image_url']) → seed_judge_cards
(reads that key, builds the judge card with image_url) → approvals.html (renders the <img>) →
portal /answer (a handler for every verdict the judge card can send).

This script asserts the chain is WIRED end-to-end WITHOUT spending a cent — no fal, no LLM. It is
a GATE, not a report: it prints one GREEN/RED line per arrow and sys.exit(1) on ANY red (Rule #8 —
gates REFUSE, never warn-and-continue). Rule #6/#7: every writer has a reader, every tap-answer a
handler — this script is the assertion that proves it.

Run:  python3 scripts/verify_chain.py [--n 20]
"""
import argparse
import ast
import json
import re
import sys
from pathlib import Path

B = Path(__file__).parent.parent
MANIFEST = B / "data/batch_manifest.json"
RENDER_DIR = B / "api/static/renders"
SEED = B / "scripts/seed_judge_cards.py"
RENDER = B / "scripts/render_image.py"
PORTAL = B / "api/portal_mini.py"
PORTAL_HTML = B / "api/static/approvals.html"

reds = []


def line(ok, arrow, msg):
    print(f"  {'🟢 GREEN' if ok else '🔴 RED  '} {arrow}: {msg}")
    if not ok:
        reds.append(f"{arrow}: {msg}")


def _parse(maybe):
    if isinstance(maybe, dict):
        return maybe
    try:
        return ast.literal_eval(str(maybe))
    except Exception:
        return {}


def must_cover_majors():
    """Same rule as produce_batch.must_cover_majors (Rule #6 — one logic, two readers): a major
    occasion's central moment (major AND (beat=='day_of' OR anchor)) read from the year_maps."""
    majors = set()
    for h in ("myfitness.sa", "eatjurisha", "albaik"):
        ymf = B / "clients" / h / "year_map.json"
        if not ymf.exists():
            continue
        ym = json.loads(ymf.read_text())
        for s in (sl for mm in ym["months"].values() for sl in mm):
            if s.get("occasion") and s.get("major") and (s.get("beat") == "day_of" or s.get("anchor")):
                majors.add(s["occasion"])
    return majors


def major_dates():
    """Map major slug → sorted list of its dates across the pilots (for window-intersection)."""
    out = {}
    for h in ("myfitness.sa", "eatjurisha", "albaik"):
        ymf = B / "clients" / h / "year_map.json"
        if not ymf.exists():
            continue
        ym = json.loads(ymf.read_text())
        for s in (sl for mm in ym["months"].values() for sl in mm):
            if s.get("occasion") and s.get("major"):
                out.setdefault(s["occasion"], set()).add(s.get("date", ""))
    return {k: sorted(v) for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="judge-card slice size to validate (first-N of manifest)")
    a = ap.parse_args()

    print("THE COMPLETE-POST CHAIN — $0 proof (no fal, no LLM)\n")

    # ── ARROW 1: MANIFEST — exists, staged:false, N posts each with a resolvable card_path ──
    man = None
    if not MANIFEST.exists():
        line(False, "produce_batch → manifest", f"{MANIFEST} does not exist — run produce_batch first")
    else:
        try:
            man = json.loads(MANIFEST.read_text())
        except Exception as e:
            line(False, "produce_batch → manifest", f"manifest unreadable: {e}")
    if man is not None:
        staged = man.get("staged", None)
        line(staged is False, "produce_batch → manifest",
             f"staged={staged} (must be False — staging is a separate gated step)")
        posts = man.get("posts", [])
        slice_n = posts[:a.n]
        line(len(slice_n) > 0, "manifest → posts",
             f"{len(posts)} posts, validating first {len(slice_n)} (--n {a.n})")
        bad_paths = []
        for p in slice_n:
            cp = p.get("card_path")
            if not cp or not Path(cp).exists():
                bad_paths.append(f"{p.get('handle')} {p.get('date')} → {cp}")
        line(not bad_paths, "manifest → card files",
             f"all {len(slice_n)} card_path resolve on disk" if not bad_paths
             else f"{len(bad_paths)} card_path MISSING: {bad_paths[:3]}")
    else:
        slice_n = []

    # ── ARROW 2: OCCASION COVERAGE — every must-cover major whose window intersects the manifest
    #    date span must appear in the manifest (Rule #8 — name the missing major, REFUSE). ──
    majors = must_cover_majors()
    if slice_n:
        dates = sorted(p.get("date", "") for p in slice_n if p.get("date"))
        span_lo, span_hi = (dates[0], dates[-1]) if dates else ("", "")
        present = {p.get("occasion") for p in slice_n}
        mdates = major_dates()
        # a major INTERSECTS the window iff any of its dates fall within [span_lo, span_hi]
        in_window = {m for m in majors
                     if any(span_lo <= d <= span_hi for d in mdates.get(m, []))}
        missing = sorted(in_window - present)
        line(not missing, "manifest → occasion coverage",
             f"all {len(in_window)} window-intersecting majors covered ({sorted(in_window)})"
             if not missing
             else f"MISSING majors in window [{span_lo}..{span_hi}]: {missing} — REFUSE (never silently omit)")
    else:
        line(False, "manifest → occasion coverage", "no posts to check coverage against")

    # ── ARROW 3: PHOTO WIRE — the WRITER (render_image) and the READER (seed_judge_cards +
    #    approvals.html) agree on the SAME key path, and any on-disk render lives under
    #    api/static/renders/. In dry state (no renders yet) the WIRE is asserted, not a file. ──
    render_src = RENDER.read_text() if RENDER.exists() else ""
    seed_src = SEED.read_text() if SEED.exists() else ""
    html_src = PORTAL_HTML.read_text() if PORTAL_HTML.exists() else ""
    # writer writes card['visual']['image_url'] = "/static/renders/<name>" into RENDER_DIR
    writer_key = ('card["visual"]["image_url"]' in render_src and "/static/renders/" in render_src)
    line(writer_key, "render_image → visual.image_url (writer)",
         "render_image writes card['visual']['image_url'] = /static/renders/<stem>.jpg" if writer_key
         else "render_image does NOT write the visual.image_url key — writer severed")
    # reader (seed) parses visual then reads visual.image_url (NOT the old top-level d['image_url']).
    # Strip comments first so the assertion judges CODE, not prose (the fixup comment legitimately
    # mentions the old d.get('image_url') key — that must not read as a live use).
    seed_code = "\n".join(re.sub(r"#.*$", "", ln) for ln in seed_src.splitlines())
    reader_visual = re.search(r"_parse\(d\.get\(['\"]visual['\"]\)\)", seed_code) is not None
    reader_key = ('visual.get("image_url")' in seed_code or "visual.get('image_url')" in seed_code)
    sets_card = ('"image_url": img' in seed_code or "'image_url': img" in seed_code)
    no_topkey_check = "d.get('image_url')" not in seed_code and 'd.get("image_url")' not in seed_code
    seed_ok = reader_visual and reader_key and sets_card and no_topkey_check
    line(seed_ok, "render_image → seed_judge_cards (reader)",
         "build_card reads visual.image_url and sets card['image_url'] = img (old top-level check removed)"
         if seed_ok
         else f"reader wire broken: parse={reader_visual} reads_visual_key={reader_key} "
              f"sets_card={sets_card} no_stale_topkey={no_topkey_check}")
    # portal HTML renders the <img> off it.image_url for the caption_judge card
    html_ok = "it.image_url" in html_src and re.search(r"<img src=.\$\{esc\(it\.image_url\)\}", html_src) is not None
    line(html_ok, "seed_judge_cards → approvals.html <img>",
         "approvals.html renders <img src=it.image_url> in the caption_judge path" if html_ok
         else "approvals.html does NOT render the judge-card image_url — viewer wire severed")
    # any on-disk render must live under api/static/renders/ (dry state: none yet → wire-only assert)
    renders = list(RENDER_DIR.glob("*.jpg")) + list(RENDER_DIR.glob("*.png")) if RENDER_DIR.exists() else []
    # the manifest cards' own visual.image_url must, when present, point under /static/renders/
    leaked = []
    have_url = 0
    for p in slice_n:
        cp = p.get("card_path")
        if not cp or not Path(cp).exists():
            continue
        try:
            d = json.loads(Path(cp).read_text())
        except Exception:
            continue
        url = _parse(d.get("visual")).get("image_url")
        if url:
            have_url += 1
            if not url.startswith("/static/renders/"):
                leaked.append(f"{p.get('handle')} {p.get('date')} → {url}")
            else:
                # if the card claims a render, the FILE must exist where the contract says
                stem = Path(cp).stem
                if not (RENDER_DIR / f"{stem}.jpg").exists() and not (RENDER_DIR / f"{stem}.png").exists():
                    leaked.append(f"{p.get('handle')} {p.get('date')} claims {url} but no file at renders/{stem}.*")
    if have_url == 0:
        line(True, "manifest cards → renders dir",
             f"dry state: 0/{len(slice_n)} cards carry a render yet — WIRE asserted, no file required "
             f"(no_fal_photos holds, $0)")
    else:
        line(not leaked, "manifest cards → renders dir",
             f"all {have_url} rendered cards point under api/static/renders/ and the file exists"
             if not leaked else f"render-path violations: {leaked[:3]}")

    # ── ARROW 4: HANDLER — every judge-card answer-value has a handler in the portal /answer path
    #    (Rule #7 — a tap whose answer has nowhere to land is a severed wire). A caption_judge card
    #    has NO options, so its answer is one of: approved | rejected | comment (approvals.html:
    #    `answer = j.verdict || 'comment'`). The /answer route must consume any of these. ──
    portal_src = PORTAL.read_text() if PORTAL.exists() else ""
    route_ok = '@app.post("/api/approvals/answer")' in portal_src
    # the handler stores any answer string + marks the card answered (generic consumer for verdicts)
    consumes = ('body.get("answer"' in portal_src and 'it["status"] = "answered"' in portal_src)
    # confirm approvals.html actually emits these three values for a no-options judge card
    emits = ("answer=j.verdict||'comment'" in html_src or 'answer=j.verdict||"comment"' in html_src)
    handler_ok = route_ok and consumes and emits
    line(handler_ok, "approvals.html verdict → /answer handler",
         "verdict values {approved,rejected,comment} all land in POST /api/approvals/answer "
         "(stored + card marked answered)" if handler_ok
         else f"handler wire broken: route={route_ok} consumes={consumes} emits={emits}")

    # ── verdict ──
    print()
    if reds:
        print(f"🛑 CHAIN REFUSED — {len(reds)} RED arrow(s):")
        for r in reds:
            print(f"   • {r}")
        sys.exit(1)
    print("✅ CHAIN GREEN — every arrow wired, $0, no fal/LLM touched.")


if __name__ == "__main__":
    main()
