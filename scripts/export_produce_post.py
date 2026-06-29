#!/usr/bin/env python3
"""EXPORT PRODUCE_POST (June 28, 2026) — ogz-knowledge → the platform's CONTENT-PRODUCTION contract.

The second half of the connection. After the brand profile is set (export_prefill.py), the platform's
post-onboarding pipeline needs POSTS (photo + caption). This emits the `produce_post` contract the devs
connect to — analogous to the pre_fill exporter, for content.

Designed WITH DeepSeek (June 28 consult, Rule #15). Its rulings, honored here:
- STATIC wrap of BANKED artifacts — never burn a fal render to serve the contract (money gate).
- NEVER block on HUMAIN — the Arabic caption judge is browser-gated; caption-judgment tolerates `pending`.
- DURABLE, IDEMPOTENT post ledger keyed by post_id=(brand,product,slot) → never duplicate/regenerate.
- THE BITE (#4): the `caption` in the contract is the EXACT string that was judged. We re-judge
  image+caption TOGETHER (rabie_judge) so caption ↔ caption-judgment can never drift to a stale mismatch.

Sources: api/static/renders_v37/{handle}_{product}_{chain}.jpg (banked images) · data/rabie_verdicts.jsonl
(vision judge ledger) · render_client_slot (the SYSTEM caption engine — Rule #12, never hand-written) ·
data/openclaw_v37/samples (the v3.7 prompt provenance).

Usage:
  python3 scripts/export_produce_post.py --handle eatjurisha --product جريش --chain G03         # wrap (fast)
  python3 scripts/export_produce_post.py --handle eatjurisha --product جريش --chain G03 --produce  # + live caption
  python3 scripts/export_produce_post.py --handle albaik --list                                  # banked posts
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

B = Path(__file__).parent.parent
sys.path.insert(0, str(B / "scripts"))

RENDERS = B / "api" / "static" / "renders_v37"
VERDICTS = B / "data" / "rabie_verdicts.jsonl"
LEDGER = B / "data" / "produced_posts.jsonl"          # durable idempotent post record
THRESHOLD = 0.85                                        # auto-approve bar (both judges)


def _slug(s):
    return (s or "").replace(" ", "_")


def find_image(handle, product, chain):
    p = RENDERS / f"{handle}_{_slug(product)}_{chain}.jpg"
    return p if p.exists() else None


def list_banked(handle=None):
    out = []
    for p in sorted(RENDERS.glob("*.jpg")):
        stem = p.stem
        if handle and not stem.startswith(handle + "_"):
            continue
        out.append(stem)
    return out


def vision_judgment(image_rel):
    """The image-only judge scores from the ledger (product_truth/composition/cultural/brand —
    these don't depend on the caption, so the banked verdict is valid). Returns a normalized block."""
    if not VERDICTS.exists():
        return None
    latest = None
    for ln in VERDICTS.read_text().splitlines():
        if not ln.strip():
            continue
        try:
            r = json.loads(ln)
        except json.JSONDecodeError:
            continue
        if r.get("image", "").endswith(image_rel):
            latest = r  # last match wins (newest)
    if not latest:
        return None
    sc = latest.get("scores", {})
    overall = latest.get("overall")
    return {
        "passed": latest.get("verdict") == "bank",
        "score": round(overall / 5, 2) if isinstance(overall, (int, float)) else None,
        "verdict": latest.get("verdict"),
        "axes": {k: sc.get(k) for k in ("product_truth_score", "composition_score",
                                        "cultural_fit_score", "brand_system_score")},
        "flags": latest.get("what_is_wrong", []),
        "rabie_note": latest.get("rabie_note", ""),
        "source": "rabie_verdicts.jsonl (GPT-4o vision)",
    }


def gen_caption(handle, product, occasion):
    """THE SYSTEM produces the caption (Rule #12 — never hand-written). Mirrors produce_complete_post:
    load_client → slot → CD-brain panel angle → render_captions, keep one that names the product."""
    import render_client_slot as rcs
    try:
        import openclaw_convert as oc
    except Exception:
        oc = None
    c = rcs.load_client(handle)
    slot = {"occasion": occasion, "date": time.strftime("%Y-%m-%d"), "type": "offer", "format": "image",
            "formula": "CF_01", "beat": occasion, "angle_theme": product, "product_name": product}
    sector = ""
    try:
        sector = oc.load_brand(handle).get("sector", "") if oc else ""
    except Exception:
        pass
    angle = {}
    try:
        angle = rcs.make_angle(c, slot, sector, panel=True) or {}
    except Exception as e:
        sys.stderr.write(f"angle panel failed ({type(e).__name__}) — product-hero fallback\n")
    if not isinstance(angle, dict):
        angle = {}
    angle.setdefault("brain", "firaasa")
    angle.setdefault("post_type", "product")
    angle.setdefault("core", "product")
    angle["scene_ar"] = f"{product}: لقطة بطل للمنتج"
    cap = ""
    for _ in range(3):
        try:
            caps = rcs.render_captions(c, slot, angle)
            opts = caps if isinstance(caps, list) else caps.get("options", caps)
            for opt in (opts if isinstance(opts, list) else [opts]):
                txt = opt.get("caption") if isinstance(opt, dict) else opt
                if txt and product in txt:
                    cap = txt
                    break
            if not cap and opts:
                first = opts[0]
                cap = (first.get("caption") if isinstance(first, dict) else first) or ""
        except Exception as e:
            sys.stderr.write(f"caption gen error: {type(e).__name__}: {str(e)[:80]}\n")
        if cap and product in cap:
            break
    return cap or None


def rejudge(image_path, handle, product, caption, occasion="everyday"):
    """Judge the caption with TWO signals on the EXACT caption shown (DeepSeek bite #4):
    HUMAIN (ALLaM, Saudi-native — OWNS the Arabic verdict) + GPT-4o (image↔caption cross-check).
    Auto-approve needs ≥2 signals that AGREE (a single model can't ship Saudi creative — Rule #13).
    HUMAIN down → only GPT scores → signals=1 → always human review. Cheap (no fal)."""
    judges = {}
    # 1. HUMAIN — the Arabic authority (chat.humain.ai via local service)
    try:
        import humain_judge as hj
        if hj._humain_up():
            h = hj.judge_caption(caption, handle=handle, product=product, occasion=occasion)
            hs = h.get("score")
            if isinstance(hs, (int, float)):
                judges["humain"] = {"score": round(hs / 5, 2), "verdict": h.get("verdict"),
                                    "native_saudi": h.get("native_saudi"), "issues": h.get("issues", [])}
    except Exception as e:
        sys.stderr.write(f"humain judge error: {type(e).__name__}: {str(e)[:70]}\n")
    # 2. GPT-4o — image+caption alignment cross-check
    try:
        import rabie_judge as rj
        v = rj.judge(str(image_path), handle, product, caption)
        ca = v.get("caption_alignment_score")
        if isinstance(ca, (int, float)):
            judges["gpt"] = {"score": round(ca / 5, 2), "issues": v.get("what_is_wrong", [])}
    except Exception as e:
        sys.stderr.write(f"gpt caption judge error: {type(e).__name__}: {str(e)[:70]}\n")

    # 3. SAUDI-FLOOR — rule-based, MODALITY-DIFFERENT from the LLM judges (DeepSeek's Rule #13 design,
    # June 29: 'make the 2nd signal modality-different, not another LLM'). cliche/non-Saudi-dialect/
    # cultural/worn floor. Lets a floor-clean + GPT-aligned caption PASS without HUMAIN — Mohamed's ruling
    # 'we pass the captions; if HUMAIN is down we use it as Arabic CONSULTANT only'. This is a FLOOR, not a
    # taste-ceiling: HUMAIN (when up, the authoritative Arabic signal + advisory) and Mohamed's portal
    # verdict remain the quality consultant. So GPT(alignment) + saudi_floor(rule-based Arabic) = 2
    # independent MODALITIES (honors Rule #13's intent: not a single KIND of judgment).
    try:
        import caption_filter as cf
        ok, reasons = cf.check(caption)
        judges["saudi_floor"] = {"score": 1.0 if ok else 0.0, "issues": reasons, "modality": "rule_based"}
    except Exception as e:
        sys.stderr.write(f"saudi_floor judge error: {type(e).__name__}: {str(e)[:70]}\n")

    if not judges:
        return {"status": "pending", "reason": "all caption judges unavailable (HUMAIN down + GPT error + filter error)"}

    def _good(name, j):
        if name == "humain":
            return j.get("verdict") == "bank" or (j.get("score") or 0) >= 0.8
        return (j.get("score") or 0) >= 0.8
    scores = [j["score"] for j in judges.values() if j.get("score") is not None]
    signals = len(judges)
    all_good = all(_good(n, j) for n, j in judges.items())
    names = list(judges.keys())
    src = (f"{'+'.join(names)} ({signals} independent signals)" if signals >= 2
           else f"{names[0] if names else 'no'} only — needs a 2nd independent signal to auto-approve")
    if "humain" not in judges and signals >= 2:
        src += " · HUMAIN down → floor-passed (rule-based Saudi floor + GPT alignment); HUMAIN/Mohamed = taste consultant"
    return {"status": "judged", "signals": signals, "judges": judges,
            "score": round(min(scores), 2) if scores else None,        # conservative (weakest signal)
            "passed": signals >= 2 and all_good,                       # agreement of ≥2 judges
            "source": src}


def caption_block(caption):
    if not caption:
        return {"arabic": None, "english": None, "hashtags": [], "cta": None,
                "source": None, "status": "pending_generation"}
    tags = re.findall(r"#[\w؀-ۿ_]+", caption)
    return {"arabic": caption, "english": None, "hashtags": tags, "cta": None,
            "source": "ogz_caption_engine (render_client_slot, CD-brain panel)",
            "status": "pending_caption_review"}


# ── IDEMPOTENCY INDEX (C204) ─────────────────────────────────────────────────────────────────────
# The ledger is append-only and the brain_api is a long-lived process: re-scanning the whole file on
# every _ledger_get was O(n) per produce → O(n²) over a brand's lifetime. Build a post_id→record index
# ONCE (on first touch / process startup) and keep it warm. Appends update it in place; an external
# writer is caught by an mtime guard that rebuilds. Semantics preserved exactly: last record wins.
_LEDGER_INDEX = {}                       # post_id → record (latest)
_LEDGER_SIG = None                       # (st_mtime_ns, st_size) of the file the index reflects


def _ledger_sig():
    try:
        st = LEDGER.stat()
        return (st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        return None


def _ledger_build_index():
    """Full scan → index. Called once on startup, and again only if an external write is detected."""
    global _LEDGER_INDEX, _LEDGER_SIG
    idx = {}
    if LEDGER.exists():
        # ERROR BOUNDARY (C209, DeepSeek gap #4): JSONDecodeError is tolerated per-line below, but an
        # OSError on the whole-file read (perms, disk full, file vanished between .exists() and
        # .read_text()) would otherwise crash the /produce hot path. Degrade gracefully — empty index +
        # stderr warn — so a read fault costs idempotency memory for this run (re-produce), never a crash.
        try:
            lines = LEDGER.read_text().splitlines()
        except OSError as e:
            sys.stderr.write(f"ledger read failed ({type(e).__name__}: {str(e)[:80]}) — "
                             f"degrading to empty index; idempotency offline this run\n")
            lines = []
        for ln in lines:
            if ln.strip():
                try:
                    r = json.loads(ln)
                except json.JSONDecodeError:
                    continue           # tolerate a torn/partial line, same as the old scan
                pid = r.get("post_id")
                if pid is not None:
                    idx[pid] = r       # last wins — matches the old scan's `found = r`
    _LEDGER_INDEX = idx
    _LEDGER_SIG = _ledger_sig()


def _ledger_get(post_id):
    # mtime/size guard: our own appends keep _LEDGER_SIG in lock-step, so this only rebuilds when
    # another process wrote to the ledger — the index never goes stale, and the hot path is a dict get.
    if _LEDGER_SIG is None or _ledger_sig() != _LEDGER_SIG:
        _ledger_build_index()
    return _LEDGER_INDEX.get(post_id)


# C209 (RABIE's beat-6 pick): GROWTH CEILING. produced_posts.jsonl is append-only and would grow
# unbounded. When it crosses MAX_PRODUCED_LINES, archive the FULL history to data/archive/ and keep
# only the most recent KEEP_RECENT lines active. Keeping the recent tail (not a naive truncate-all,
# which DeepSeek's first spec proposed) preserves RECENT idempotency — old archived posts could
# otherwise re-produce. The index rebuilds from the trimmed active file.
MAX_PRODUCED_LINES = 50_000               # active-ledger line ceiling
KEEP_RECENT        = 10_000               # recent lines retained on rotation (idempotency window)
ARCHIVE_DIR        = B / "data" / "archive"


def _rotate_if_needed():
    """Cap produced_posts.jsonl growth: archive full history, retain the most recent KEEP_RECENT lines."""
    global _LEDGER_SIG
    if not LEDGER.exists():
        return
    try:
        lines = [l for l in LEDGER.read_text().splitlines() if l.strip()]
    except OSError:
        return                            # read fault → skip rotation (never block a produce on it)
    if len(lines) < MAX_PRODUCED_LINES:
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive = ARCHIVE_DIR / f"produced_posts_{time.strftime('%Y%m%d_%H%M%S')}.jsonl"
    archive.write_text("\n".join(lines) + "\n")          # full history preserved before trimming
    keep = lines[-KEEP_RECENT:]
    LEDGER.write_text("\n".join(keep) + "\n")            # active ledger = recent tail
    _LEDGER_SIG = None                                   # force index rebuild from the trimmed file
    sys.stderr.write(f"ledger rotated: {len(lines)}→{len(keep)} lines, archived {archive.name}\n")


def _ledger_put(record):
    global _LEDGER_SIG
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed()                   # C209: cap growth BEFORE appending
    if _LEDGER_SIG is None:                # ensure the index exists before we mutate it
        _ledger_build_index()
    with open(LEDGER, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    pid = record.get("post_id")
    if pid is not None:
        _LEDGER_INDEX[pid] = record       # keep the index hot without a re-scan
    _LEDGER_SIG = _ledger_sig()           # adopt the new file signature so _ledger_get won't rebuild


def build(handle, product, chain, occasion="everyday", produce=False, regenerate=False):
    post_id = f"{handle}__{_slug(product)}__{chain}"
    prev = _ledger_get(post_id)
    if prev and not regenerate:                            # idempotency (DeepSeek #3)
        prev["_idempotent"] = "returned existing — pass --regenerate to rebuild"
        return prev

    image = find_image(handle, product, chain)
    if not image:
        # clean STRUCTURED refusal (DeepSeek): a sparse/not-produce-ready brand must refuse clearly,
        # never crash or fake a post. The devs key off status="refused" + reason.
        return {"ok": False, "status": "refused", "post_id": post_id,
                "reason": f"no banked render for {handle} · {product} · {chain} — brand not produce-ready",
                "suggestion": "complete the brand's product_truth organ + run the render pipeline, then retry /produce"}
    image_rel = image.relative_to(B).as_posix()
    vision = vision_judgment(image_rel)

    caption_text, cap_judge = None, {"status": "pending",
                                     "reason": "caption not generated (run with --produce)"}
    if produce:
        # SERVE FROM THE CAPTION BANK first — no live HUMAIN in the request path (DeepSeek SPOF fix).
        banked = None
        try:
            import bank_captions as bc
            banked = bc.bank_lookup(handle, product, chain)
        except Exception:
            pass
        _ban_ok, _ban_hits = (True, [])
        if banked and banked.get("fresh") and banked.get("caption"):
            try:
                import caption_filter as cf
                _ban_ok, _ban_hits = cf.kill_ban_check(banked["caption"], handle)  # bans evolve AFTER banking
            except Exception:
                pass
        if banked and banked.get("fresh") and banked.get("caption") and _ban_ok:
            caption_text = banked["caption"]
            cap_judge = dict(banked.get("judge") or {})
            cap_judge["served_from"] = "caption_bank"           # fast path: pre-judged offline
        elif banked and banked.get("caption") and not _ban_ok:
            # a ban was added AFTER this caption was banked → never serve it; force a re-bank (DeepSeek A1)
            caption_text = None
            cap_judge = {"status": "banking_queued", "stale": True,
                         "reason": f"banked caption now hits a ban {_ban_hits} — re-bank required"}
        else:
            # NOT freshly banked → NEVER block on live HUMAIN in the serve path (DeepSeek: bank-exhaustion
            # → live-HUMAIN timeout is the new first-fail). Return queued; the OFFLINE bank fills it.
            caption_text = None
            cap_judge = {"status": "banking_queued",
                         "reason": ("bank was STALE (brand drifted) — re-bank needed" if banked
                                    else "not in caption bank yet — run bank_captions for this post (offline)"),
                         "stale": bool(banked and not banked.get("fresh"))}

    cap = caption_block(caption_text)
    # status: rejected if image killed; else human-gated review. Auto-approve needs the image high AND
    # the caption passed by ≥2 AGREEING judges (HUMAIN + GPT) — never a single model on Saudi creative.
    auto = bool(vision and (vision.get("score") or 0) >= THRESHOLD
                and cap_judge.get("status") == "judged" and cap_judge.get("passed"))
    if vision and vision.get("verdict") == "kill":
        status = "rejected"
    elif cap_judge.get("status") == "banking_queued":
        status = "banking_queued"          # image ready; caption being banked offline — retry shortly
    elif auto:
        status = "approved"
    else:
        status = "pending_review"

    record = {
        "ok": True,
        "schema_version": "ogz-produce-post-1.0",
        "post_id": post_id,
        "brand": handle, "product": product, "slot": chain,
        "status": status,
        "content": {"image_url": image_rel, "caption": cap},
        "provenance": {"image": image_rel, "model": "flux-2-pro/edit", "chain": chain,
                       "occasion": occasion, "generation_attempts": 1,
                       "produced_by": "ogz-knowledge produce pipeline"},
        "judgments": {"vision": vision or {"status": "pending", "reason": "no verdict in ledger"},
                      "caption": cap_judge},
        "review": {"required": status == "pending_review", "threshold": THRESHOLD,
                   "auto_approved": auto,
                   "human_review_url": None},
        "created_at": int(time.time()),
    }
    _ledger_put(record)
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    ap.add_argument("--product", default="")
    ap.add_argument("--chain", default="")
    ap.add_argument("--occasion", default="everyday")
    ap.add_argument("--produce", action="store_true", help="generate the caption live (system) + re-judge")
    ap.add_argument("--regenerate", action="store_true", help="rebuild even if post_id exists")
    ap.add_argument("--list", action="store_true", help="list banked posts (optionally for --handle)")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    if a.list:
        for s in list_banked(a.handle):
            print(s)
        return
    if not (a.handle and a.product and a.chain):
        sys.exit("need --handle --product --chain (or --list)")

    rec = build(a.handle, a.product, a.chain, a.occasion, produce=a.produce, regenerate=a.regenerate)
    out = Path(a.out) if a.out else B / "clients" / a.handle / f"post_{_slug(a.product)}_{a.chain}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=2))
    if rec.get("ok"):
        v = rec["judgments"]["vision"]
        print(f"✅ {rec['post_id']}: status={rec['status']} → {out}")
        print(f"   vision: {v.get('verdict')} ({v.get('score')}) · caption: "
              f"{rec['content']['caption']['status']} / judge={rec['judgments']['caption']['status']}")
    else:
        print(f"⚠ {rec.get('error')}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
