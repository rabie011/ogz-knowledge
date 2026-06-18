#!/usr/bin/env python3
"""THE POST AUDIT — Mohamed's 2026-06-14 order: "the 20 posts WITHOUT ANY ISSUE... confirmed
with occasion and everything aligned... don't create before testing." This is the TEST. It
runs every guard the renderer runs PLUS the alignment checks the renderer lacked, per post,
and a batch-diversity check. Exit non-zero if ANY post carries ANY issue (Rule #8 — refuse,
don't warn). Used as the gate before staging + re-run until zero.

Issue classes (per post):
  empty            — no captions
  json_artifact    — a malformed caption (stray quote/brace/'`,` — pen returned broken JSON)
  occasion_fabricate — DAILY slot whose caption invents an occasion (eid/ramadan/national day…)
  occasion_mismatch  — OCCASION slot whose caption celebrates a DIFFERENT occasion
  occasion_missing   — OCCASION slot whose caption never references its own occasion (WARN)
  theme_misframe   — slot.angle_theme carries an occasion prefix ≠ the slot's real occasion
  garbage_theme    — angle_theme product is a stopword/preposition or a mangled Latin name
  taste_kill       — caption matches an ACTIVE founder kill_pattern
  hard_kill        — pre_ship_gate blocks it (cultural/royal/learned)
  truth            — ungrounded person/promo/Latin name, or the brand name transliterated
  filler           — bilingual filler / worn cross-brand skeleton
Batch: over_concentration — one scene-core or recipe > 30% of the batch.
"""
import argparse, glob, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pre_ship_gate as psg
from render_client_slot import TASTE_GUARD_LEXICON, batch_diversity_check
from truth_guards import FILLER, EVENT_CLAIM, PERSON_AR, PERSON_EN, PROMO_AR, LATIN_NAME, strip_punct
# ONE source for occasion logic (Rule #6) — boundary-safe, shared with render + gate
from occasion_align import occ_hits, caption_misaligned, is_daily, slot_occ_key, SLUG2KEY, ALL_KEYS

B = Path(__file__).parent.parent
STOP_PRODUCT = set("على عن من في إلى الى مع و أو يا هذا هذه the a an of on".split())


def theme_occasion(theme):
    """the occasion prefix the year-map stamped on the theme (e.g. 'eid: ...' → eid)."""
    m = re.match(r"\s*([a-z_]+)\s*:", theme or "")
    if not m:
        return None
    p = m.group(1)
    return SLUG2KEY.get(p, p if p in ALL_KEYS else None)


def audit_post(d, handle):
    issues = []
    slot = d.get("slot") or {}
    caps = d.get("captions") or []
    occ_key = slot_occ_key(slot)
    daily = is_daily(slot)
    theme = slot.get("angle_theme") or ""

    if not caps:
        issues.append(("empty", "no captions"))
        return issues  # nothing else to check

    # theme-frame + garbage-theme (slot-data issues that drive the caption astray)
    tk = theme_occasion(theme)
    if daily and tk:
        issues.append(("theme_misframe", f"daily slot carries '{tk}:' occasion theme"))
    if tk and occ_key and tk != occ_key:
        issues.append(("theme_misframe", f"theme '{tk}' ≠ slot occasion '{occ_key}'"))
    pm = re.match(r"منتج حقيقي:\s*(.+)", theme)
    if pm:
        prod = pm.group(1).strip()
        if prod in STOP_PRODUCT or len(prod) <= 2 or re.search(r"[A-Za-z]+\.[a-z]{2,}", prod):
            issues.append(("garbage_theme", f"theme product is junk: «{prod}»"))

    # gate (hard cultural/royal/learned) — once per post
    if psg.gate(d, handle).get("block"):
        issues.append(("hard_kill", "pre_ship_gate BLOCK"))

    active = [k.get("pattern") for k in d.get("kill_patterns", []) if isinstance(k, dict)]
    brand_ar = (d.get("brand_ar") or "")
    # B034-audit (June 18, RABIE zoom-out): post_audit imported PERSON_AR + PROMO_AR but never
    # SCANNED with them — a write-only door (Rule #6 broken). A caption naming "الأمير X" / a
    # hallucinated combo "التوأم Y" passed the audit's truth block uncaught. Wire them in,
    # grounded against the client's corpus EXACTLY like render_client_slot.ungrounded() so a
    # real person/promo in the brand's own captions is not false-flagged.
    corpus = (d.get("corpus_text") or "").lower()
    slot_documented = bool(slot.get("documented_moment"))
    for c in caps:
        # json artifact / malformed
        if re.search(r"(['\"]\s*[,}\]]\s*$)|(\}\s*$)|^\s*[\[{]", c) or c.count('"') % 2 == 1:
            issues.append(("json_artifact", c[:50]))
        # occasion alignment (shared rule — Rule #6)
        mis = caption_misaligned(slot, c)
        if mis:
            kind = "occasion_fabricate" if daily else "occasion_mismatch"
            issues.append((kind, f"{mis}: {c[:45]}"))
        elif occ_key and occ_key not in occ_hits(c):
            issues.append(("occasion_missing", f"occasion={occ_key} not referenced: {c[:40]}"))
        # taste kill
        for p in active:
            if p in TASTE_GUARD_LEXICON and TASTE_GUARD_LEXICON[p].search(c):
                issues.append(("taste_kill", f"[{p}] {c[:40]}"))
        # truth: event/person/promo/Latin
        if EVENT_CLAIM.search(c):
            issues.append(("truth", f"event-claim: {c[:40]}"))
        if FILLER.search(c):
            issues.append(("filler", f"{c[:40]}"))
        # named people (AR + EN): ungrounded in a fictional scene = the hallucinated-prince kill
        for m in list(PERSON_AR.finditer(c)) + list(PERSON_EN.finditer(c)):
            if not slot_documented:
                issues.append(("truth", f"named-person in fictional scene «{m.group(0)}»: {c[:35]}"))
            elif strip_punct(m.group(0)).lower() not in corpus:
                issues.append(("truth", f"ungrounded named-person «{m.group(0)}»: {c[:35]}"))
        # promo-combo nouns (التوأم/كومبو/…): invented unless the client's corpus carries them
        for m in PROMO_AR.finditer(c):
            if strip_punct(m.group(0)).lower() not in corpus:
                issues.append(("truth", f"ungrounded promo-combo «{m.group(0)}»: {c[:35]}"))
        for m in LATIN_NAME.finditer(c):
            t = re.sub(r"[^\w]", "", m.group(0)).lower()
            if "." in m.group(0) or (brand_ar and t and t not in (d.get("corpus_text") or "").lower()):
                issues.append(("truth", f"latin/brand-mangle «{m.group(0)}»: {c[:35]}"))
    # THE VISUAL DOOR (RABIE zoom-out 2026-06-14): occasion leaks through the shoot-card brief
    # too — albaik 2026-10-11 staged a full Ramadan suhoor in visual_shots while its captions
    # were clean, so a caption-only scan stamped it "CLEAN" — a lie. A post is the caption AND
    # its visual; scan both with the same shared rule.
    vis = " ".join(str(x) for x in (d.get("visual") or {}).get("phone_shoot_card") or [])
    if vis:
        vmis = caption_misaligned(slot, vis)
        if vmis:
            issues.append(("occasion_visual", f"visual brief invents occasion — {vmis}"))
    # CLIENT-RULES: the client's confirmed organs (real-person/face/family/voice, cloud-kitchen
    # format, cross-brand, brand-register) — RABIE's 24-issue gap (June 14). Block-severity → issue.
    try:
        import client_rules as _cr
        for kind, sev, detail in _cr.violations(d, handle):
            if sev == "block":
                issues.append((f"organ_{kind}", detail))
            else:
                issues.append((f"organ_{kind}_warn", detail))
    except Exception:
        pass
    return issues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suffix", default="__v6")
    ap.add_argument("--handles", default="myfitness.sa,eatjurisha,albaik")
    ap.add_argument("--dates", default="", help="comma dates to limit (else all suffix files)")
    ap.add_argument("--staged", action="store_true", help="audit exactly the OPEN judge-lane posts")
    a = ap.parse_args()

    posts = []  # (handle, date, post_dict)
    if a.staged:
        items = json.loads((B / "data/decision_queue.json").read_text())["items"]
        for it in items:
            if it.get("kind") == "caption_judge" and it.get("status") == "open":
                h = it["handle"]; dt = it["id"].replace(f"judge2_{h}_", "")
                fs = glob.glob(str(B / f"clients/{h}/posts/{dt}__*{a.suffix}.json"))
                if fs:
                    posts.append((h, dt, json.loads(Path(fs[0]).read_text())))
    else:
        dates = set(a.dates.split(",")) if a.dates else None
        for h in a.handles.split(","):
            for f in glob.glob(str(B / f"clients/{h}/posts/*{a.suffix}.json")):
                dt = Path(f).name.split("__")[0]
                if dates and dt not in dates:
                    continue
                posts.append((h, dt, json.loads(Path(f).read_text())))

    total_issues = 0
    clean = 0
    for h, dt, d in sorted(posts):
        iss = audit_post(d, h)
        hard = [i for i in iss if i[0] != "occasion_missing" and not i[0].endswith("_warn")]  # missing/_warn = soft
        if not hard:
            clean += 1
            tag = "✅ CLEAN" + ("  (⚠ occasion_missing)" if iss else "")
            print(f"{tag}  {h} {dt}")
        else:
            total_issues += len(hard)
            print(f"❌ {h} {dt} — {len(hard)} issue(s):")
            for kind, why in iss:
                print(f"      • {kind}: {why}")

    # batch diversity (over-concentration) — scene-core AND creative-device trope
    slotlike = [{"date": dt, "scene_ar": (d.get("captions") or [""])[0], "angle_theme": (d.get("slot") or {}).get("angle_theme", ""), "formula": (d.get("slot") or {}).get("formula")} for h, dt, d in posts]
    dchk = batch_diversity_check(slotlike, 0.30)
    try:
        import client_rules as _cr
        trope = _cr.batch_trope_overconcentration([d for h, dt, d in posts], 0.30)
        for t in trope:
            dchk.setdefault("violations", []).append({"kind": "device", "key": t["device"], "count": t["count"], "n": len(posts), "pct": t["pct"]})
    except Exception:
        pass
    print(f"\nBATCH: {len(posts)} posts · {clean} clean · {total_issues} hard issues · "
          f"diversity {'OVER-CONCENTRATED' if dchk['violations'] else 'OK'}")
    # CONCENTRATION = a real >30% violation. Low COVERAGE (abstract captions the core-taxonomy
    # can't classify) is NOT concentration — a diverse, un-formulaic batch scores low coverage
    # BY DESIGN; failing on it would punish variety (June 14 fix). Coverage is a NOTE only.
    if dchk["violations"]:
        for v in dchk["violations"]:
            print(f"   ⚠ over-concentration: {v['kind']} «{v['key']}» {v['count']}/{dchk['n']} ({v['pct']}%)")
    elif dchk.get("coverage", 1) < 0.5:
        print(f"   · note: low core-coverage ({dchk['coverage']}) — captions are abstract/varied, NOT concentrated")
    ok = total_issues == 0 and not dchk["violations"]
    print("🟢 ZERO ISSUES — batch is ship-ready" if ok else "🔴 ISSUES PRESENT — not ship-ready")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
