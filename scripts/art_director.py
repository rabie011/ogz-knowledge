#!/usr/bin/env python3
"""THE ART-DIRECTOR — the missing VISUAL mind (June 22).

OGZ's brainstorm named the gap: today the producer writes the post IDEA + caption
(the CEO brief + the 5 CD brains riff on it), the chain is picked content-aware but
MECHANICALLY (render_client_slot.pick_pro_chain / post_unit.chain_for), and
openclaw_convert turns (handle, chain, scene) → a v3.7 15-block prompt. Nobody
DELIBERATELY DESIGNS the photograph as a craft decision.

Mohamed's two directives:
  (1) «if it is photo they must write the brief AS A PHOTO» — a photo slot gets a
      VISUAL brief, not a generic text brief.
  (2) «who is writing the brief for the 5 brains?» — the CEO writes the brief the CD
      brains riff on; the ART-DIRECTOR is its VISUAL counterpart.

THE AD is a STAGE that WRITES a structured photo brief FROM THE ORGANS (Rule #12 —
the system produces; we never hand-author a brief). It DESIGNS the photograph:
  • a chosen CHAIN with a one-line REASON (why this chain serves THIS idea)
  • SCENE staging — setting, subjects, props
  • the PERSONA / reference choice — model-agnostic: a TEXT persona description +
    which CONFIRMED reference image (per brand_visual_dna_v37 schema), NEVER a
    model-locked id (Rule #4 / A4)
  • COMPOSITION, LIGHT, MOOD
  • MODESTY baked into the brief text (the render + pixel gate still enforce)

It CONSUMES the existing engines — it does NOT greenfield:
  • build_visual_dna_profiles output / the v37 schema → clients/<h>/profile/visual_dna.json
  • the v3.7 chain canon → 02_what_to_build/INDEX.json (+ data/openclaw_v37 via convert)
  • render_client_slot.pick_pro_chain → the content-aware chain candidate (the AD's
    default chain choice; the AD adds the DELIBERATE design layer + the WHY around it)
  • openclaw_convert.derive_visual_dna / pick_reference → the persona & reference pack
  • client_rules.violations → the cultural gate (Rule #6/#8 — reuse, never re-regex)

FORMAT-AWARE (directive 1): only photo/image formats get a photo brief. A reel routes
to reel_brief() (a thin stub that names the reel path) so the reel path is never broken.

THE LLM writes the brief FROM the organ inputs. In tests the call is STUBBED (zero
spend); a single real gpt-4o call is allowed only in the Prove phase. The deterministic
ORGAN SPINE (chain+reason+persona+reference+staging skeleton+modesty) is built WITHOUT
the LLM, so the brief is a real system artifact even when the pen is dark (Rule #12).

Usage:
  python3 scripts/art_director.py --handle albaik --date 2026-07-01 \
      --idea "family: الأخ الأكبر يجهّز بوكس البيك للعشا" [--fmt image] [--occasion ...] [--real]
"""
import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

# CONSUME the existing engines (never reimplement) ───────────────────────────────
import openclaw_convert as oc            # derive_visual_dna, pick_reference, resolve_chain, load_brand
import client_rules as cr                # violations() — the cultural gate (Rule #6/#8)


PHOTO_FORMATS = {"image", "photo", "carousel", "still", "post"}
REEL_FORMATS = {"reel", "video", "story_video", "motion"}


# ── format awareness (directive 1) ───────────────────────────────────────────────
def is_photo(fmt: str) -> bool:
    """A photo/image slot gets a PHOTO brief. A reel does not (it routes to reel_brief).
    Unknown/empty format defaults to PHOTO (the dominant year-map format, 329/365 image)."""
    f = (fmt or "").strip().lower()
    if f in REEL_FORMATS:
        return False
    return True  # image/photo/carousel/'' all take the photo path


# ── chain pick (consume pick_pro_chain; chain_for as the fallback, Rule #6) ───────
def _pick_chain(handle: str, idea: str, fmt: str, occasion: str, sector: str,
                formula_id: str = "") -> dict | None:
    """The AD's chain candidate. CONSUMES render_client_slot.pick_pro_chain (the content-
    aware picker) when a formula is known, else the chain's own purpose score over the idea.
    Keeps the MECHANICAL pick reachable as the FALLBACK (A2): if pick_pro_chain returns None
    or errors, fall back to post_unit.chain_for. Returns the INDEX chain dict (or None)."""
    try:
        import render_client_slot as rcs
    except Exception:
        rcs = None
    chain = None
    if rcs is not None and formula_id:
        try:
            chain = rcs.pick_pro_chain(formula_id, sector, occasion or "", scene_text=idea)
        except Exception:
            chain = None
    if chain is None:
        # No formula on the slot (or the picker held): score every eligible chain by its own
        # purpose against the scene's computed needs — the SAME computed logic, applied to the
        # full pool (Rule #12, a computed rule, not a per-post map).
        if rcs is not None:
            try:
                idx = json.load(open(BASE / "02_what_to_build/INDEX.json"))
                chains = idx if isinstance(idx, list) else idx.get("chains", [])
                needs = rcs._scene_needs(idea, "", occasion or "")
                human = rcs._scene_has_human(idea)

                def _ok(c):
                    sa = c.get("sectors_allowed") or []
                    oa = c.get("occasions_allowed") or []
                    s_ok = not sa or sector in sa or "all" in sa
                    o_ok = (not oa or (occasion or "") in oa or "all" in oa
                            or "evergreen" in oa or "*" in oa)
                    h_ok = (not human) or (c.get("family") not in rcs._NO_HUMANS_FAMILIES)
                    return s_ok and o_ok and h_ok
                pool = [c for c in chains if _ok(c)]
                scored = [(rcs._chain_purpose_score(c, needs), -rcs._chain_index(c, chains), c)
                          for c in pool]
                scored = [t for t in scored if t[0] > 0] or scored
                if scored:
                    chain = max(scored, key=lambda t: (t[0], t[1]))[2]
            except Exception:
                chain = None
    if chain is None and formula_id:
        # the LEGACY mechanical floor (A2 fallback): post_unit.chain_for
        try:
            from post_unit import chain_for
            chain = chain_for(formula_id, sector, occasion or "")
        except Exception:
            chain = None
    return chain


def _chain_reason(chain: dict, needs: list, human: bool) -> str:
    """ONE line: why THIS chain serves THIS idea (the deliberate design decision, not a
    mechanical pick). Computed from the chain's own purpose + the scene's needs — a real
    rationale the eye can check, never invented prose."""
    if not chain:
        return ("no eligible chain serves this scene — the AD HOLDS (Rule #8): a human "
                "moment with no human-capable chain renders nothing rather than a wrong shot")
    name = chain.get("name_en") or chain.get("name_ar") or chain.get("family") or "?"
    need = (needs or ["product_hero"])[0]
    NEED_WHY = {
        "human_life": "the scene puts a PERSON in a real moment — a lifestyle frame holds the human, "
                      "a no-humans product splash would betray it",
        "product_hero": "the product is the subject — a hero/studio frame lets it carry the post",
        "craving_texture": "the appetite is in the material up close — a texture/macro frame sells the craving",
        "offer_announce": "this is a sell with a card/CTA — an announcement frame gives the offer a place to land",
        "occasion": "the moment is a holiday spread/greeting — an occasion frame carries the cultural beat",
    }
    why = NEED_WHY.get(need, "it best fits the scene's dominant visual need")
    h = " (human present → no-humans families vetoed)" if human else ""
    return f"«{name}» — {why}{h}"


# ── the deterministic ORGAN SPINE (built WITHOUT the LLM — Rule #12) ──────────────
def _organ_spine(handle: str, idea: str, occasion: str, product: str = "") -> dict:
    """Read the brand's visual_dna organ (v37) + the reference pack, with ZERO spend.
    Returns the model-agnostic persona/reference block (A4) + the brand visual fields the
    brief stages against. Uses openclaw_convert's own derivation so the AD and the converter
    agree on every value (Rule #3 consistency)."""
    brand = oc.load_brand(handle)
    chain_hint = {"family": "", "name_en": "", "quality_tier": ""}  # derive is chain-light here
    fields = oc.derive_visual_dna(brand, chain_hint)
    reference = oc.pick_reference(handle, product=product)  # matched to the post's product

    def v(key, default=""):
        f = fields.get(key) or {}
        return f.get("value", default) if isinstance(f, dict) else default

    # PERSONA — model-agnostic: a TEXT description + which reference image (Rule #4 / A4).
    # NEVER a model-locked artifact (no flux seed, no generation id). The persona is whether
    # a HUMAN appears at all (modesty-bounded) and, if so, who — read from the brand's tone +
    # the scene; the reference pack anchors the PRODUCT identity, not a face.
    try:
        import render_client_slot as rcs
        human = rcs._scene_has_human(idea)
    except Exception:
        human = bool(re.search(r"عائل|أم\b|الأم|أب\b|الأب|أخ|طالب|أصدقاء|طفل|رجل|امرأة|شاب|فتاة", idea or ""))
    modesty = v("brand.modesty_register",
                "STRICT (Saudi default — modest, no skin, no mixed-gender intimacy)")
    if human:
        persona_text = (f"a single modest Saudi figure in role only (no named real person), {modesty}; "
                        "framed by hands/gesture/posture, faces only where the brand's organ permits")
    else:
        persona_text = ("PRODUCT-ONLY — no human figure; the hero is the product itself, "
                        "staged with its own world of companion objects")

    return {
        "persona": {
            "_model_agnostic": True,            # A4: text + reference-pack, never a model id
            "text": persona_text,
            "reference_image": reference,        # CONFIRMED clean-product shot (the v37 identity anchor)
            "modesty_register": modesty,
            "human_present": human,
        },
        "brand_visual": {
            "palette_primary": v("brand.palette.primary"),
            "color_field": v("brand.color_field_palette"),
            "capture_character": v("brand.aesthetic.capture_character"),
            "anti_attributes": v("brand.anti_attributes"),
            "tone_register": v("brand.tone_register"),
            "quality_tier": v("brand.quality_tier"),
        },
        "product": {
            "name": v("product.name"),
            "material_texture": v("product.material_texture"),
            "companion_elements": v("product.companion_elements"),
            "dimensions": v("product.dimensions"),
        },
        "_sector": brand.get("sector", ""),
    }


# ── the LLM brief (STUBBED in tests; real only in Prove) ──────────────────────────
def _ad_pen(idea: str, occasion: str, spine: dict, chain: dict, reason: str,
            llm=None) -> dict:
    """The Art-Director's PEN: writes the photograph's DESIGN (setting/subjects/props,
    composition, light, mood) FROM the organ spine + the chosen chain (Rule #12 — produced
    from organs, never hand-authored). `llm` is an injectable callable(messages)->str so the
    test stubs it ($0) and Prove passes the real gpt-4o caller. Default llm=None → the
    deterministic organ-derived staging (so the AD always yields a real brief, pen dark or not)."""
    bv, pr, pe = spine["brand_visual"], spine["product"], spine["persona"]
    if llm is None:
        # ORGAN-DERIVED staging (no spend): a real, defensible photo design built from the
        # organs alone. The pen (when present) enriches this; it never replaces the spine.
        subj = pe["text"]
        setting = (f"an authentic contemporary Saudi setting true to «{bv.get('capture_character') or 'clean studio'}», "
                   f"the {pr.get('name') or 'product'} placed naturally inside the moment")
        props = pr.get("companion_elements") or "one restrained, category-true companion object"
        composition = (f"the {pr.get('name') or 'hero'} reads at honest scale ({pr.get('dimensions') or 'real-world size'}); "
                       "one clear focal subject, restrained negative space, no clutter")
        light = (f"capture character «{bv.get('capture_character') or 'clean studio'}»; "
                 f"a warm color-field drawn from the brand's own palette ({bv.get('color_field') or bv.get('palette_primary') or 'brand palette'})")
        mood = (f"tone «{bv.get('tone_register') or 'warm'}», quality tier «{bv.get('quality_tier') or 'universal'}» — "
                "appetite-forward and honest, never plastic/CGI")
        return {
            "subjects": subj,
            "setting": setting,
            "props": props,
            "composition": composition,
            "light": light,
            "mood": mood,
            "_source": "organ_derived",
        }
    # the LLM path (Prove): the pen designs the photo from the organ spine
    sys_p = (
        "You are a Saudi ART DIRECTOR. You DESIGN a single photograph as a craft decision — "
        "you do NOT write a caption and you do NOT invent facts. Work ONLY from the organ inputs "
        "given (brand visual DNA, product truth, the chosen chain + why). Bake MODESTY into the "
        "brief (modest Saudi dress, no skin, no mixed-gender intimacy, roles not named people). "
        "Design: SETTING, SUBJECTS, PROPS, COMPOSITION, LIGHT, MOOD — concrete, shootable, true to "
        "the brand. Return JSON: "
        '{"subjects":"...","setting":"...","props":"...","composition":"...","light":"...","mood":"..."}'
    )
    user = (
        f"THE IDEA (the post's scene): {idea}\n"
        f"OCCASION: {occasion or 'everyday — no holiday'}\n"
        f"CHOSEN CHAIN: {(chain or {}).get('name_en') or '(none)'} — REASON: {reason}\n"
        f"PERSONA (model-agnostic, modesty-bounded): {pe['text']}\n"
        f"REFERENCE IMAGE (product identity anchor): {pe.get('reference_image') or '(none)'}\n"
        f"BRAND VISUAL DNA: {json.dumps(bv, ensure_ascii=False)}\n"
        f"PRODUCT: {json.dumps(pr, ensure_ascii=False)}\n"
        "Design the photograph. JSON only."
    )
    raw = llm([{"role": "system", "content": sys_p}, {"role": "user", "content": user}])
    raw = re.sub(r"^```(?:json)?\s*", "", (raw or "").strip())
    raw = re.sub(r"\s*```$", "", raw)
    m = re.search(r"\{.*\}", raw, re.S)
    out = json.loads(m.group(0) if m else raw)
    out["_source"] = "llm"
    return out


# ── modesty baked into the brief TEXT (the render/pixel gate still enforces) ──────
def _modesty_line(spine: dict) -> str:
    reg = spine["persona"].get("modesty_register") or "STRICT (Saudi default)"
    base = (f"MODESTY (baked, non-negotiable): {reg}. Modest Saudi dress where any person appears "
            "(thobe/abaya), no skin, no mixed-gender intimacy, no named real person — roles only. "
            "Right-hand interaction. The render and pixel gate enforce this downstream.")
    anti = spine["brand_visual"].get("anti_attributes")
    if anti:
        base += f" NEVER render: {anti}"
    return base


def _brief_as_post(brief: dict) -> dict:
    """Map the AD photo brief into the post shape client_rules.violations() reads, so the
    cultural gate (the EXISTING engine) scans the brief's staging text — A3, Rule #6: reuse
    the gate, don't re-regex the red lines here.

    The brief is a VISUAL brief, NOT a caption — so EVERY line (idea + staging + persona) goes
    into the visual lane (visual.phone_shoot_card), and captions stays EMPTY. This is deliberate:
    the gate's VISUAL-relevant rules — named real person, mixed-gender/dine-in (cloud kitchen),
    gym frame on a food brand, and (via the no-face marker) face/family visibility — all scan the
    visual lane (`allt`/`vis`), so they BITE on the brief. The CAPTION-only rules (the 220-char
    SHORT drift-ceiling, the ®/legal-name register rule, the family-VOICE speech rule) read
    `caps` only and would FALSE-FIRE on a long visual-design paragraph, so they correctly do not
    apply to a photo brief (a brief is not a caption; its length is irrelevant)."""
    d = brief["design"]
    lines = [brief.get("idea", ""),
             d.get("setting", ""), d.get("subjects", ""), d.get("props", ""),
             d.get("composition", ""), d.get("light", ""), d.get("mood", ""),
             brief.get("persona", {}).get("text", ""), brief.get("modesty", "")]
    return {
        "captions": [],
        "visual": {"phone_shoot_card": [v for v in lines if v]},
    }


def gate_brief(brief: dict, handle: str) -> list:
    """A3 — check the AD brief against the client's CONFIRMED organs via the EXISTING cultural
    gate (client_rules.violations). Returns the list of (kind, severity, detail). A brief that
    stages a red-line scene (named real person, mixed-gender, immodest face/family on a
    face_visibility:never brand, dine-in on a cloud kitchen, a gym frame on a food brand) is
    REFUSED upstream by the caller (Rule #8). Reuses the gate — never reimplements its regexes."""
    return cr.violations(_brief_as_post(brief), handle)


# ── reel path (directive 1 — don't break it) ─────────────────────────────────────
def reel_brief(handle: str, idea: str, occasion: str, fmt: str) -> dict:
    """A reel does NOT get a photo brief. This names the reel/motion path so the reel slot is
    never broken (it routes to the native-video chain canon). A FIRST stub — the motion AD is a
    later mind; for now it carries the idea + format so produce_batch can route it onward."""
    return {
        "kind": "reel_brief",
        "format": fmt,
        "handle": handle,
        "idea": idea,
        "occasion": occasion,
        "note": ("reel/motion slot — the PHOTO art-director does not author this; route to the "
                 "native-video chain path (5-block v3.7 video). Motion-AD is a later mind."),
    }


# ── THE STAGE ─────────────────────────────────────────────────────────────────────
def art_direct(post_idea: str, handle: str, fmt: str = "image",
               occasion: str = "", formula_id: str = "", llm=None, product: str = "") -> dict:
    """A1 — THE ART-DIRECTOR STAGE. (post_idea, handle, fmt) → a structured PHOTO BRIEF.

    FORMAT-AWARE (directive 1): a reel routes to reel_brief() (the photo path is skipped);
    only photo/image formats get the photo brief.

    The photo brief DESIGNS the photograph deliberately, FROM THE ORGANS (Rule #12):
      • chosen CHAIN + a one-line REASON (why this chain serves this idea)
      • model-agnostic PERSONA + which CONFIRMED reference image (A4 / v37 schema)
      • SCENE staging (setting, subjects, props), COMPOSITION, LIGHT, MOOD
      • MODESTY baked into the brief text

    GATED (A3): the brief is checked against the client's confirmed organs (the cultural gate).
    A brief that stages a hard red line is marked refused=True (the caller HOLDS — Rule #8).
    The chain has a READER (A2): openclaw_convert consumes brief['chain']['id'] + the composed
    scene → render_via_master. `llm` is injectable (test stub = $0; Prove = real gpt-4o)."""
    if not is_photo(fmt):
        return reel_brief(handle, post_idea, occasion, fmt)

    brand = oc.load_brand(handle)
    sector = brand.get("sector", "")
    chain = _pick_chain(handle, post_idea, fmt, occasion, sector, formula_id)
    try:
        import render_client_slot as rcs
        needs = rcs._scene_needs(post_idea, "", occasion or "")
        human = rcs._scene_has_human(post_idea)
    except Exception:
        needs, human = ["product_hero"], False
    reason = _chain_reason(chain, needs, human)

    spine = _organ_spine(handle, post_idea, occasion, product=product)
    design = _ad_pen(post_idea, occasion, spine, chain, reason, llm=llm)
    modesty = _modesty_line(spine)

    # the COMPOSED SCENE the converter will use (A2): the AD's deliberate staging, woven into
    # one prose seed openclaw_convert.fill() drops into the [SCENE] block. This REPLACES the
    # bare scene_ar for photo posts — the photograph is now DESIGNED, not just described.
    composed_scene = " · ".join(s for s in [
        post_idea.strip(),
        design.get("setting", ""),
        design.get("subjects", ""),
        f"props: {design.get('props','')}" if design.get("props") else "",
        f"composition: {design.get('composition','')}" if design.get("composition") else "",
        f"light: {design.get('light','')}" if design.get("light") else "",
        f"mood: {design.get('mood','')}" if design.get("mood") else "",
    ] if s)

    brief = {
        "kind": "photo_brief",
        "schema": "art_director_brief_v1",
        "handle": handle,
        "format": fmt,
        "occasion": occasion,
        "idea": post_idea,
        "chain": {
            "id": (chain or {}).get("chain_id_short"),
            "family": (chain or {}).get("family"),
            "name_en": (chain or {}).get("name_en"),
            "name_ar": (chain or {}).get("name_ar"),
            "reason": reason,
        },
        "persona": spine["persona"],          # A4 — model-agnostic (text + reference image)
        "brand_visual": spine["brand_visual"],
        "product": spine["product"],
        "design": design,
        "modesty": modesty,
        "composed_scene": composed_scene,     # A2 — the reader is openclaw_convert
        "needs": needs,
        "human_present": human,
    }

    # A3 — GATE against the client's confirmed organs (Rule #8: a red-line brief is REFUSED).
    viols = gate_brief(brief, handle)
    blocking = [v for v in viols if len(v) >= 2 and v[1] == "block"]
    brief["gate"] = {
        "violations": viols,
        "blocking": blocking,
        "refused": bool(blocking) or chain is None,
        "reason": (
            "; ".join(v[2] for v in blocking) if blocking else
            ("no eligible chain — held" if chain is None else "clean")
        ),
    }
    return brief


# ── A2 — the brief feeds openclaw_convert (the reader, Rule #6) ───────────────────
def to_converter_args(brief: dict) -> dict | None:
    """A2 — turn the AD brief into the args openclaw_convert.derive_visual_dna/fill consume:
    the AD's CHOSEN chain (resolved to a v3.7 id) + the COMPOSED scene REPLACE the mechanical
    pick_pro_chain/chain_for + bare scene for photo posts. Returns None for a refused/reel brief
    (Rule #8 — a refused brief never reaches the renderer; the caller holds)."""
    if brief.get("kind") != "photo_brief":
        return None
    if brief.get("gate", {}).get("refused"):
        return None
    cid = (brief.get("chain") or {}).get("id")
    if not cid:
        return None
    try:
        v37_id = oc.resolve_chain(cid)
    except SystemExit:
        return None
    return {
        "handle": brief["handle"],
        "chain": v37_id,
        "scene": brief["composed_scene"],
        "occasion": brief.get("occasion", ""),
        "product": (brief.get("product") or {}).get("name", ""),
    }


def print_brief(brief: dict):
    if brief.get("kind") == "reel_brief":
        print(f"\n🎬 REEL BRIEF — {brief['handle']} ({brief['format']})")
        print(f"   idea: {brief['idea']}")
        print(f"   {brief['note']}")
        return
    g = brief.get("gate", {})
    flag = "🛑 REFUSED" if g.get("refused") else "✅ clean"
    ch = brief.get("chain", {})
    pe = brief.get("persona", {})
    d = brief.get("design", {})
    W = 78
    print(f"\n{'='*W}")
    print(f"  ART-DIRECTOR PHOTO BRIEF — {brief['handle']}  ({brief['format']})  {flag}")
    print(f"{'='*W}")
    print(f"  IDEA:    {brief['idea']}")
    print(f"  CHAIN:   [{ch.get('id')}] {ch.get('name_en')} — {ch.get('family')}")
    print(f"  WHY:     {ch.get('reason')}")
    print(f"  PERSONA: {pe.get('text')}")
    print(f"  REF IMG: {pe.get('reference_image') or '⚠ none — run classify_media.py'}")
    print(f"  SETTING: {d.get('setting')}")
    print(f"  SUBJECT: {d.get('subjects')}")
    print(f"  PROPS:   {d.get('props')}")
    print(f"  COMPO:   {d.get('composition')}")
    print(f"  LIGHT:   {d.get('light')}")
    print(f"  MOOD:    {d.get('mood')}")
    print(f"  MODESTY: {brief.get('modesty')}")
    print(f"  {'─'*(W-2)}")
    print(f"  GATE:    {g.get('reason')}")
    if g.get("violations"):
        for v in g["violations"]:
            print(f"           [{v[1]}] {v[0]}: {v[2]}")
    print(f"  → converter args (the reader): {json.dumps(to_converter_args(brief), ensure_ascii=False) if to_converter_args(brief) else '(held — refused/reel)'}")
    print(f"{'='*W}\n")


def _real_gpt(messages):
    """The ONE real gpt-4o caller — used ONLY by --real (the Prove phase). $0 in tests
    (never imported there). Reads OPENAI_API_KEY from ~/.abraham_env or the shell env."""
    import urllib.request
    key = None
    p = os.path.expanduser("~/.abraham_env")
    if os.path.exists(p):
        for l in open(p):
            if l.startswith("OPENAI_API_KEY="):
                key = l.split("=", 1)[1].strip().strip('"')
    key = key or os.environ.get("OPENAI_API_KEY")
    if not key:
        sys.exit("no OPENAI_API_KEY (set it in ~/.abraham_env or export it)")
    body = {"model": "gpt-4o", "temperature": 0.6, "max_tokens": 600,
            "response_format": {"type": "json_object"}, "messages": messages}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {key}",
                                         "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=120).read())["choices"][0]["message"]["content"]


def main():
    ap = argparse.ArgumentParser(description="The Art-Director stage — a structured PHOTO brief from organs")
    ap.add_argument("--handle", required=True)
    ap.add_argument("--idea", required=True, help="the post idea/scene the CD brains produced")
    ap.add_argument("--fmt", default="image", help="image|photo|carousel|reel (format-aware)")
    ap.add_argument("--occasion", default="")
    ap.add_argument("--formula", default="", help="the slot's creative formula id (for pick_pro_chain)")
    ap.add_argument("--real", action="store_true",
                    help="PROVE phase ONLY — make the ONE real gpt-4o call (~$0.01). Default: organ-derived ($0).")
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()

    llm = _real_gpt if a.real else None
    brief = art_direct(a.idea, a.handle, a.fmt, a.occasion, a.formula, llm=llm)
    print_brief(brief)
    if a.save:
        out = BASE / "data/art_director_briefs"
        out.mkdir(exist_ok=True)
        fn = out / f"{a.handle}_{re.sub(r'[^0-9a-zA-Z]', '_', a.idea)[:30]}.json"
        fn.write_text(json.dumps(brief, ensure_ascii=False, indent=2))
        print(f"  saved → {fn.relative_to(BASE)}")


if __name__ == "__main__":
    main()
