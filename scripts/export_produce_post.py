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
    slot = {"occasion": occasion, "date": "2026-07-01", "type": "offer", "format": "image",
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


def rejudge(image_path, handle, product, caption):
    """Re-judge image+caption TOGETHER so the contract's caption_alignment refers to THIS caption
    (DeepSeek bite #4). GPT-4o vision (cheap, no fal). Returns the caption-judgment block or pending."""
    try:
        import rabie_judge as rj
        v = rj.judge(str(image_path), handle, product, caption)
        ca = v.get("caption_alignment_score")
        # ONE model is a single point of failure on Saudi creative (DeepSeek June 28 + Rule #13 +
        # "AI judge can't judge Saudi creative"). signals=1 → can never auto-approve; HUMAIN (when up)
        # or a 2nd judge is signal #2. Until then the post always routes to a human.
        return {"status": "judged", "passed": isinstance(ca, (int, float)) and ca >= 4,
                "score": round(ca / 5, 2) if isinstance(ca, (int, float)) else None,
                "signals": 1, "judges": ["gpt-4o"],
                "note": "single-model score — needs HUMAIN or a 2nd signal (CLIP/2nd LLM) to auto-approve",
                "source": "rabie_judge GPT-4o (image+caption)", "issues": v.get("what_is_wrong", [])}
    except Exception as e:
        return {"status": "pending", "reason": f"caption re-judge unavailable ({type(e).__name__}); "
                "HUMAIN Arabic judge is browser-gated — devs treat pending as awaiting review."}


def caption_block(caption):
    if not caption:
        return {"arabic": None, "english": None, "hashtags": [], "cta": None,
                "source": None, "status": "pending_generation"}
    tags = re.findall(r"#[\w؀-ۿ_]+", caption)
    return {"arabic": caption, "english": None, "hashtags": tags, "cta": None,
            "source": "ogz_caption_engine (render_client_slot, CD-brain panel)",
            "status": "pending_caption_review"}


def _ledger_get(post_id):
    if not LEDGER.exists():
        return None
    found = None
    for ln in LEDGER.read_text().splitlines():
        if ln.strip():
            try:
                r = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if r.get("post_id") == post_id:
                found = r
    return found


def _ledger_put(record):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def build(handle, product, chain, occasion="everyday", produce=False, regenerate=False):
    post_id = f"{handle}__{_slug(product)}__{chain}"
    prev = _ledger_get(post_id)
    if prev and not regenerate:                            # idempotency (DeepSeek #3)
        prev["_idempotent"] = "returned existing — pass --regenerate to rebuild"
        return prev

    image = find_image(handle, product, chain)
    if not image:
        return {"ok": False, "post_id": post_id, "error": f"no banked image "
                f"{handle}_{_slug(product)}_{chain}.jpg in renders_v37"}
    image_rel = image.relative_to(B).as_posix()
    vision = vision_judgment(image_rel)

    caption_text, cap_judge = None, {"status": "pending",
                                     "reason": "caption not generated (run with --produce)"}
    if produce:
        caption_text = gen_caption(handle, product, occasion)
        if caption_text:
            cap_judge = rejudge(image, handle, product, caption_text)  # caption ↔ judgment match

    cap = caption_block(caption_text)
    # status: rejected if image killed; else human-gated review. Auto-approve needs BOTH judges high
    # AND the caption judged by ≥2 agreeing signals (a single model can't ship Saudi creative).
    auto = bool(vision and vision.get("score", 0) and vision["score"] >= THRESHOLD
                and cap_judge.get("status") == "judged" and (cap_judge.get("score") or 0) >= THRESHOLD
                and cap_judge.get("signals", 0) >= 2)
    if vision and vision.get("verdict") == "kill":
        status = "rejected"
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
