"""
enrich_briefs.py — inject brand intelligence from KB into brief_matrix.json

Sources (in priority order):
  1. intelligence_layer.json → caption_intelligence (7 brands, richest)
  2. intelligence_layer.json → brand_profiles (52 brands)
  3. _inbox/@{handle}/account_summary.json → bio tagline
  4. observations/{sector}/*.json → real hook texts (top 5 per brand)

Output: data/brief_matrix.json gains `brand_context` per brief.
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent

BRIEFS_FILE  = BASE / "data" / "brief_matrix.json"
IL_FILE      = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
INBOX_DIR    = BASE / "11_who_to_learn_from" / "_inbox"
OBS_ROOT     = BASE / "11_who_to_learn_from" / "observations"


# ── helpers ──────────────────────────────────────────────────────────────────

def _load(path):
    with open(path) as f:
        return json.load(f)


def _load_inbox_summaries():
    """Returns dict: real_handle -> summary dict (with bio, normalized handle)."""
    out = {}
    for entry in INBOX_DIR.iterdir():
        summary_path = entry / "account_summary.json"
        if not summary_path.exists():
            continue
        try:
            s = _load(summary_path)
        except Exception:
            continue
        handle = s.get("handle") or entry.name.lstrip("@")
        out[handle] = s
    return out


def _build_norm_map(inbox: dict) -> dict:
    """Returns: real_handle -> account_handle_normalized (OGZ-Reference-XXX)."""
    return {
        h: s["account_handle_normalized"]
        for h, s in inbox.items()
        if s.get("account_handle_normalized")
    }


def _load_hooks(norm_handle: str, sector: str) -> list[str]:
    """Extract up to 5 distinctive Arabic hook texts for a brand from observations."""
    obs_dir = OBS_ROOT / sector
    if not obs_dir.exists():
        return []

    hooks = []
    GENERIC = {"شاركنا", "اطلب", "متوفر", "جديد", "تابع", "فولو", "منشن",
               "مسابقة", "اشترك", "سجل", "احجز", "فوز"}

    for fpath in obs_dir.iterdir():
        if not fpath.suffix == ".json":
            continue
        try:
            obs = _load(fpath)
        except Exception:
            continue
        if obs.get("account_handle_normalized") != norm_handle:
            continue

        hook = obs.get("voice_observations", {}).get("hook_text", "").strip()
        if not hook or len(hook) < 8:
            continue
        # skip hooks dominated by generic giveaway language
        if any(g in hook for g in GENERIC):
            continue
        # Arabic content only
        arabic_chars = sum(1 for c in hook if "؀" <= c <= "ۿ")
        if arabic_chars < 5:
            continue
        hooks.append(hook)
        if len(hooks) >= 8:
            break

    # deduplicate, return top 5
    seen = set()
    out = []
    for h in hooks:
        k = re.sub(r"\s+", " ", h)[:40]
        if k not in seen:
            seen.add(k)
            out.append(h)
        if len(out) >= 5:
            break
    return out


# ── main enrichment ───────────────────────────────────────────────────────────

def build_brand_context(handle: str, sector: str,
                        brand_profiles: dict,
                        caption_intel: dict,
                        inbox: dict,
                        norm_map: dict) -> dict:

    ctx = {}

    # 1. Brand profile (voice, tone, dialect, signature phrases)
    bp = brand_profiles.get(handle, {})
    if bp:
        ctx["voice"]            = bp.get("voice", "")
        ctx["tone"]             = bp.get("tone", [])
        ctx["arabic_style"]     = bp.get("arabic_style", "")
        ctx["signature_phrases"]= bp.get("signature_phrases", [])

    # 2. Caption intelligence (richest — only 7 brands)
    ci = caption_intel.get(handle, {})
    if ci:
        ctx["high_engagement_style"] = ci.get("high_engagement_style", "")
        ctx["proven_openers"]        = ci.get("proven_openers", [])
        ctx["avoid_topics"]          = ci.get("avoid_topics", [])
        ctx["optimal_length"]        = ci.get("optimal_length", "")

    # 3. Bio tagline from account summary
    s = inbox.get(handle, {})
    bio = s.get("profile", {}).get("biography", "").strip()
    if bio:
        # keep first line only (short bio tagline)
        ctx["bio_tagline"] = bio.splitlines()[0].strip()

    # 4. Real hooks from observations
    # Some brands store observations under real handle, others under OGZ-Reference-XXX
    norm = norm_map.get(handle, handle)
    ctx["real_hooks"] = _load_hooks(norm, sector)

    return ctx


def main():
    briefs = _load(BRIEFS_FILE)
    il     = _load(IL_FILE)

    brand_profiles = il.get("brand_profiles", {})
    caption_intel  = il.get("caption_intelligence", {})
    inbox          = _load_inbox_summaries()
    norm_map       = _build_norm_map(inbox)

    enriched = 0
    for brief in briefs:
        handle = brief["brand_en"]
        sector = brief["sector"]
        ctx = build_brand_context(handle, sector, brand_profiles,
                                  caption_intel, inbox, norm_map)
        if ctx:
            brief["brand_context"] = ctx
            enriched += 1

    with open(BRIEFS_FILE, "w") as f:
        json.dump(briefs, f, ensure_ascii=False, indent=2)

    print(f"Enriched {enriched}/{len(briefs)} briefs")

    # Coverage report
    no_ctx = [b["brand_en"] for b in briefs if "brand_context" not in b]
    if no_ctx:
        print(f"No context found for: {sorted(set(no_ctx))}")
    else:
        print("Full coverage — all brands have context")

    # Sample
    sample = next(b for b in briefs if b.get("brand_context"))
    print(f"\nSample — {sample['brand_en']} / {sample['occasion']}:")
    ctx = sample["brand_context"]
    print(f"  voice: {ctx.get('voice','')[:80]}")
    print(f"  arabic_style: {ctx.get('arabic_style','')}")
    print(f"  bio_tagline: {ctx.get('bio_tagline','')}")
    print(f"  signature_phrases: {ctx.get('signature_phrases','')}")
    print(f"  real_hooks ({len(ctx.get('real_hooks',[]))}): {ctx.get('real_hooks',[][:2])}")


if __name__ == "__main__":
    main()
