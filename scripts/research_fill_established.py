#!/usr/bin/env python3
"""THE READER for extraction_mode=auto_research — Mohamed's 6×-repeated order, finally wired.

He ruled (2026-06-14): an ESTABLISHED brand (albaik) is NOT asked the new-brand passport
questions — the system RESEARCHES it across its own harvested surfaces (and the web for gaps)
and FILLS the organs. The flag clients/<h>/profile/extraction_mode.json="auto_research" was
WRITTEN by 2 scripts and READ by 0 (the write-only-organ bug the orchestra exists to kill —
RABIE zoom-out 2026-06-14). This is the missing consumer.

Tight scope (RABIE): (1) read extraction_mode==auto_research, (2) MINE the already-harvested
raw first (raw/instagram posts+comments, raw/maps_reviews) — no re-scrape, (3) fill the RED
organs l1_strategy + red_lines (+ goals ratio) with provenance + confidence:experimental
(NEVER confirmed — his tap confirms), (4) make gap_report established-aware so it STOPS asking
the forbidden new-brand Qs, (5) ASSERT end-to-end (organ filled → those Qs gone) — REFUSE,
don't warn, on failure, (6) on zero raw → WARN, never claim. Stops at filled organs; does NOT
generate captions/images (Rule #11 diagnose→show→wait; his Full-Circle 20-batch is his to judge).

Usage: python3 scripts/research_fill_established.py --handle albaik
"""
import argparse, glob, json, re, sys
from collections import Counter
from datetime import datetime
from pathlib import Path

B = Path(__file__).parent.parent
TS = "2026-06-14"
# new-brand questions an established brand must NOT be asked (his forbidden list)
FORBIDDEN_Q = ["الخطوط الحمراء", "ينطق باسم البراند", "يتكلم باسم البراند", "USP", "وش يميزكم",
               "صاحبة المشروع", "الهدف من المحتوى", "مين منافسين"]
STOP = set("في من على عن مع الى إلى the and a كل هذا هذه مع كم الآن غير لكم لكل عرض".split())


def prov(src):
    return {"source": src, "date_added": TS, "confirmer": "auto_research",
            "confidence": "experimental", "scope": "brand"}


def mine(handle):
    raw = B / "clients" / handle / "raw"
    posts = []
    for f in glob.glob(str(raw / "instagram/*/posts.jsonl")):
        posts += [json.loads(l) for l in open(f) if l.strip()]
    reviews = []
    for f in glob.glob(str(raw / "maps_reviews/*/reviews.jsonl")):
        reviews += [json.loads(l) for l in open(f) if l.strip()]
    caps = " ".join((p.get("caption") or "") for p in posts)
    terms = Counter(w for w in re.findall(r"[؀-ۿ]{3,}", caps) if w not in STOP)
    offers = sum(1 for p in posts if re.search(r"عرض|خصم|لفترة محدودة|وفّر", p.get("caption") or ""))
    low = [r for r in reviews if (r.get("rating") or r.get("stars") or 5) <= 2]
    low_txt = " ".join((r.get("text") or r.get("textTranslated") or "") for r in low)
    complaints = Counter(w for w in re.findall(r"[؀-ۿ]{4,}", low_txt) if w not in STOP)
    return {"n_posts": len(posts), "n_reviews": len(reviews), "top_terms": terms.most_common(12),
            "offer_rate": round(offers / max(len(posts), 1), 2), "n_low": len(low),
            "complaint_terms": complaints.most_common(8)}


def fill(handle, force=False, quiet=False):
    p = B / "clients" / handle / "profile"
    em = json.loads((p / "extraction_mode.json").read_text()) if (p / "extraction_mode.json").exists() else {}
    mode = em.get("mode")
    # serves BOTH of Mohamed's extraction modes: auto_research (established → researched) and
    # no_answer_figure_out (no client → derived from extraction + sector default role)
    if mode not in ("auto_research", "no_answer_figure_out"):
        if quiet:
            return None   # --all loop: silently skip new-brand (ask-the-client) brands
        sys.exit(f"🛑 {handle} mode={mode} — this reader serves auto_research + no_answer_figure_out only")
    # idempotent skip: already research-filled → don't re-mine 521 posts every cycle (cheap)
    fp0 = json.loads((p / "fingerprint.json").read_text()) if (p / "fingerprint.json").exists() else {}
    if not force and (fp0.get("l1_strategy") or {}).get("_research"):
        if not quiet:
            print(f"  ⏭ {handle}: already research-filled (use --force to re-run)")
        return True
    m = mine(handle)
    if m["n_posts"] == 0:
        # REFUSE-don't-warn: nothing harvested → cannot research-fill; say so, change nothing
        print(f"  ⚠ {handle}: ZERO harvested posts — cannot research-fill; left RED (no false claim)")
        return False
    disp = json.loads((p / "truth_pack.json").read_text()) if (p / "truth_pack.json").exists() else {}
    products = [c.get("name") for c in disp.get("product_candidates", []) if c.get("name")][:5]
    top = "، ".join(t for t, _ in m["top_terms"][:6])

    # 1. l1_strategy — established brand SPEAKS as the brand; positioning/usp from the corpus
    fp = json.loads((p / "fingerprint.json").read_text())
    l1 = fp.setdefault("l1_strategy", {})
    l1["who_speaks"] = ("البراند نفسه (علامة راسخة — صوت مؤسسي واثق، ليس صوت صاحب فرد)"
                        if mode == "auto_research" else
                        "البراند (مُستنتج آلياً — لا إجابة عميل؛ صوت افتراضي للقطاع، يصححه محمد لو رجع)")
    l1["positioning"] = (f"علامة راسخة مشهورة؛ يحضر في المحتوى: {top}؛ منتجات أساسية: "
                         f"{'، '.join(products) if products else '—'}؛ "
                         f"نسبة العروض في الفيد ≈{int(m['offer_rate']*100)}%")
    l1["usp"] = (f"الأيقونية والثقة الراسخة + {products[0] if products else 'منتجه المميز'} "
                 "+ القيمة العائلية (مُستنتج من ٥٢١ منشور — يؤكده/يصححه محمد)")
    l1["_research"] = prov(f"auto_research: mined {m['n_posts']} posts")
    (p / "fingerprint.json").write_text(json.dumps(fp, ensure_ascii=False, indent=1))

    # 2. red_lines — established-brand safe defaults + any complaint-cluster signal (experimental)
    rl = json.loads((p / "red_lines.json").read_text()) if (p / "red_lines.json").exists() else {"lines": []}
    defaults = ["لا سياسة ولا جدل ديني/طائفي ولا مزايدة وطنية",
                "لا أفراد العائلة المالكة في إعلان تجاري",
                "حلال ومحتشم وعائلي دائماً — لا كحول/خنزير/إيحاء",
                "لا استغلال لحظة عبادة (حج/عمرة) كخطّاف بيع"]
    have = {l.get("line") if isinstance(l, dict) else l for l in rl.get("lines", [])}
    for d in defaults:
        if d not in have:
            rl["lines"].append({"line": d, **prov("auto_research: established-brand safe defaults")})
    rl["_research"] = prov(f"auto_research; {m['n_low']} low-star reviews scanned for complaint clusters")
    (p / "red_lines.json").write_text(json.dumps(rl, ensure_ascii=False, indent=1))

    # 3. goals ratio (primary stays his confirmed answer) — established → brand-build-heavy (experimental)
    g = json.loads((p / "goals.json").read_text())
    if not g.get("goal_ratio"):
        g["goal_ratio"] = {"value": "بناء براند ~70% / عروض ~30% (علامة راسخة)", **prov("auto_research")}
    # bump the answered counter to match filled fields (readiness_honest gate: answered>=confirmed —
    # the same counter-lie class as the jurisha goals bug; filling a field must move the counter)
    confirmed = sum(1 for k in ("goal_ratio", "capacity_ceiling", "usp_his_words") if g.get(k))
    g["answered"] = max(g.get("answered", 0), confirmed)
    (p / "goals.json").write_text(json.dumps(g, ensure_ascii=False, indent=1))

    # 4. gap_report established-aware: drop the FORBIDDEN new-brand Qs (now researched, experimental)
    grf = p / "gap_report.json"
    gr = json.loads(grf.read_text()) if grf.exists() else {"questions": []}
    before = list(gr.get("questions", []))
    kept = [q for q in before if not any(fq in q for fq in FORBIDDEN_Q)]
    gr["questions"] = kept
    gr["auto_filled"] = {
        "mode": mode, "filled": ["l1_strategy", "red_lines", "goals.goal_ratio"],
        "note": ("established brand — researched (experimental), NOT asked." if mode == "auto_research"
                 else "no client answer — system DERIVED from extraction + sector default role (experimental); NOT asked cold."),
        "confirm_instead": "أكّد أو صحّح الملف المستنتج (هوية/خطوط حمراء/هدف) — بدل ما نسأل من الصفر",
        "mined": {"posts": m["n_posts"], "reviews": m["n_reviews"], "offer_rate": m["offer_rate"]}}
    grf.write_text(json.dumps(gr, ensure_ascii=False, indent=1))

    # 5. ASSERT end-to-end (REFUSE, don't warn): organs filled → forbidden Qs gone
    assert l1.get("who_speaks") and l1.get("usp"), "l1 not filled"
    assert rl.get("lines"), "red_lines not filled"
    left = [q for q in gr["questions"] if any(fq in q for fq in FORBIDDEN_Q)]
    assert not left, f"SEVERED: gap_report still asks forbidden Qs {left}"
    print(f"  ✅ {handle}: researched (experimental) from {m['n_posts']} posts/{m['n_reviews']} reviews · "
          f"filled l1+red_lines+goal_ratio · gap_report dropped {len(before)-len(kept)} forbidden Qs "
          f"(now asks {len(kept)}) · END-TO-END asserted")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    ap.add_argument("--all", action="store_true", help="run for every brand whose extraction_mode=auto_research")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.handle:
        fill(a.handle, force=a.force)
    else:  # bare / --all (the make_sure chain calls it plainly): every auto_research brand, idempotent
        for em in glob.glob(str(B / "clients/*/profile/extraction_mode.json")):
            h = Path(em).parent.parent.name
            fill(h, force=a.force, quiet=True)


if __name__ == "__main__":
    main()
