#!/usr/bin/env python3
"""RENDER A YEAR-MAP SLOT → full post card, from the CLIENT PROFILE (pyramid path).
This is the pilot's point: generation powered by the organs, not the old corpus path.

Per slot: concrete-scene angle (doctrine rules) → two pens (Sonnet + GPT) → code filter
→ top 3 captions + phone shoot-card + pro chain ref. Voice = the client's own real
captions as few-shot (top-liked = style exemplars only, never a quality judgment).
Blackout gate consulted before anything renders (negative-space law).

Usage: python3 scripts/render_client_slot.py --handle albaik --date 2026-09-23
"""
import argparse, json, os, re, sys, urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from caption_filter import filter_options
from blackout_gate import check as blackout_check
from post_unit import chain_for
# CD-brain routing now lives in a shared module (B035) so the angle stage can route
# on the SAME logic without importing this heavy render module. Re-exported below for
# backward-compat (R.route_brain / rcs.brain_method / m.route_brain consumers).
from brain_router import BRAIN_FILES, route_brain, brain_method, route_decision, log_routing_decision
# MODEL REGISTRY — single source of truth for WHICH caption pens the moat sits on. The two API
# helpers below (gpt/sonnet) MUST read the model id from here, not hardcode a literal — else a
# registry swap would make the caption fingerprint (line ~1065) LIE about what produced the batch.
import model_registry as mr

# Standing cross-brand worn bans (law: no_template_bleed) — ALSO the gold quarantine:
# a gold entry carrying a banned formula must never reach few-shot, even before
# Mohamed rules on it (June 13: 4 conflicted golds sat in few-shot slot 3 for ~2h —
# his drop_conflicted ruling existed but no wire consumed it)
from caption_filter import STANDING_WORN  # single copy lives in the filter (June 13)

# TASTE GUARDS (June 13 — the write-only-organ catch): a client's kill_patterns organ
# must CHANGE the render, not decorate the profile. Lexicon per known pattern;
# unknown patterns still reach the pens as prompt bans (theme line below).
TASTE_GUARD_LEXICON = {
    "family_scene_overuse": re.compile(
        r"عائل|العيلة|عيلة|لمة|اللمة|جدتي|جدّ?ي\b|أمي\b|والدتي|والدي\b|أهل البيت|family"),
    # «من جاهز» (the app) not bare جاهز (= 'ready' — جريشة جاهزة is innocent)
    "delivery_app_cta_overuse": re.compile(
        r"(من|عبر|على)\s+جاهز|التطبيق|هنقرستيشن|حمّ?ل\s|app\b", re.I),
}


# SCENE CORES (June 13, his ruling n≥2: «We need to make the posts different so for
# example if the idea is family they can't use it for all the posts») — deterministic
# emotional-core classes. June 13 ZOOM-OUT CATCH (RABIE 2/5): the bare substring جري
# matched eatjurisha's dish جريش/جريشة → 48% of a FOOD brand tagged "sport" (a phantom
# I reported to Mohamed as fact). Two fixes: (1) the PLANNER'S OWN LABEL prefix is now
# authoritative — angle_themes are written 'family: …' / 'منتج حقيقي: …' / 'قناة: …' /
# 'eid: …', so the declared theme IS the core, no guessing; (2) the regex fallback (for
# free caption text + the 18 no-label slots) is anchored + sector-stopworded so a dish
# name can never read as a scene.
LABEL_CORES = {  # the planner's declared theme (before the first ':') — ground truth
    "family": "family", "eid": "occasion", "ramadan": "occasion",
    "national": "occasion", "founding": "occasion", "منتج حقيقي": "product_shoutout",
    "قناة": "channel_cta", "عرض": "offer", "offer": "offer", "greeting": "greeting",
}
# food-sector words that contain a sport substring but are NOT sport (the جريش scar)
_SCENE_STOPWORDS = ("جريش", "جريشة", "جريّش", "جريّشة")
SCENE_CORES = {
    "family": re.compile(r"عائل|العيلة|عيلة|لمة|اللمة|جدتي|جدّ?ي\b|أمي\b|والدتي|أهل البيت|الأجيال"),
    "nostalgia": re.compile(r"ذكريات|زمان|أيام أول|الطفولة|تتجدد"),
    "craving": re.compile(r"قرمشة|ريحة|رائحة|جوع|لقمة|قضمة|نكهة"),
    "weather": re.compile(r"برد|مطر|شتا|أمطار|أجواء"),
    "friends": re.compile(r"شلة|أصحاب|صحبة|قعدة"),
    "solo_calm": re.compile(r"هدوء|وحدك|استرخاء|مع نفسك"),
    "kids_hero": re.compile(r"بطل صغير|عيال|الصغير"),
    # anchored — explicit sport words only; bare جري/حركة dropped (matched dishes/everything)
    "energy_sport": re.compile(r"ركض|تمرين|لياقة|رياضة|نشاط بدني|خطوات|ماراثون|الجري\b"),
}


def scene_core(text: str, label_aware: bool = True) -> set:
    """The emotional-core class(es) of a slot idea or caption (empty set = unclassified).
    Authoritative path: the planner's label prefix ('family:' / 'منتج حقيقي:' …).
    Fallback: anchored regex over the body, with sector stopwords subtracted first."""
    t = (text or "").strip()
    if label_aware and ":" in t[:30]:
        pref = t.split(":", 1)[0].strip().lower()
        for k, core in LABEL_CORES.items():
            if pref.startswith(k):
                return {core}
    body = t
    for sw in _SCENE_STOPWORDS:
        body = body.replace(sw, " ")
    return {name for name, pat in SCENE_CORES.items() if pat.search(body)}


def diversity_prefer(options: list, recent_cores: list) -> list:
    """Reorder options so a FRESH core leads. recent_cores = list of core-sets from
    the client's last rendered slots (newest first). If the last 2 slots share a
    core, options repeating it sink. Never drops — only reorders (the guards kill,
    diversity ranks)."""
    if not options or len(recent_cores) < 2:
        return options
    worn_cores = recent_cores[0] & recent_cores[1]
    if not worn_cores:
        return options
    return sorted(options, key=lambda o: bool(scene_core(o) & worn_cores))


# ── CONTENT-AWARE CHAIN SELECTION (June 21 — the broken-chain root-fix) ──────────────
# THE BUG (Mohamed's brief): chain_for() returned cands[0] — the FIRST chain in the
# formula's families by INDEX order — so a FAMILY-DINNER scene drew tf02_01 «Splash Ring
# Around Product» and a GYM scene drew tf10_01 «Magazine Cover With Typography». The chain
# never looked at the SCENE. This is the computed fix (Rule #12: chosen by RULE, never a
# hand-authored per-post list): score every candidate chain by how well its PURPOSE fits
# the scene's emotional core + post_type + sector, and take the best (deterministic
# tie-break by chain id). The PURPOSE of a chain is read from its own name keywords +
# family — no curated chain→scene table.
#
# SCENE-NEED → the visual SHAPE the scene wants, derived from the same scene_core() the
# caption diversity gate already trusts + the angle's post_type. Each need lists the
# keyword signals (matched against a chain's name_en/name_ar/family) that SERVE it and
# the ones that BETRAY it (a product-splash for a human-meal scene).
_CHAIN_PURPOSE_SIGNALS = {
    # human-life scenes: people in a real moment (the lifestyle families, esp. TF23)
    "human_life": {
        "want": ["lifestyle", "moment", "gathering", "family", "friends", "café", "cafe",
                 "coffee moment", "office", "workplace", "outdoor", "mother", "woman",
                 "man ", "saudi", "أصحاب", "شلة", "عائلة", "لحظة", "كافيه", "مكتب",
                 "سعودي", "سعودية", "أم وبنت", "لايف ستايل", "ضيافة", "iftar", "إفطار",
                 "suhoor", "سحور", "ghabga", "غبقة", "hospitality"],
        "avoid": ["splash", "levitation", "floating", "silhouette", "magazine cover",
                  "billboard", "swatch", "dropper", "pedestal", "macro", "رذاذ", "طافي",
                  "ظلية", "غلاف مجلة", "بيلبورد", "ماكرو", "منصة"],
    },
    # product-hero scenes: the product is the subject (shoutout, launch reveal)
    "product_hero": {
        "want": ["product", "hero", "showcase", "reveal", "levitation", "silhouette",
                 "pedestal", "studio", "spotlight", "lineup", "display", "unboxing",
                 "منتج", "بطل", "عرض", "كشف", "منصة", "استوديو", "سبوت", "تشكيلة"],
        "avoid": ["lifestyle", "family", "gathering", "before / after service",
                  "menu price", "booking cta", "magazine cover", "عائلة", "لحظة قهوة"],
    },
    # craving/texture scenes: the food/material up close (the appetite shot)
    "craving_texture": {
        "want": ["splash", "macro", "texture", "pour", "drip", "asmr", "showcase",
                 "spread", "crown", "sauce", "رذاذ", "ماكرو", "تكستشر", "صب", "قطرة",
                 "سفرة", "صوص", "تاج"],
        "avoid": ["magazine cover", "billboard", "booking cta", "menu price",
                  "before / after", "غلاف مجلة", "بيلبورد", "بطاقة منيو"],
    },
    # offer/announcement scenes: a sell with a card/CTA/price
    "offer_announce": {
        "want": ["menu price", "price tag", "promotional", "offer", "booking cta",
                 "limited time", "new arrival", "launch", "drop", "countdown",
                 "magazine cover", "billboard", "announcement", "card", "عرض", "سعر",
                 "منيو", "حجز", "إطلاق", "تنازلي", "إعلان", "بطاقة"],
        "avoid": ["lifestyle moment", "gathering", "macro", "swatch", "لحظة", "ماكرو"],
    },
    # occasion scenes: the holiday spread/greeting
    "occasion": {
        "want": ["ramadan", "eid", "iftar", "suhoor", "ghabga", "national day",
                 "founding day", "hajj", "occasion", "greeting", "heritage", "cultural",
                 "رمضان", "عيد", "إفطار", "سحور", "غبقة", "وطني", "تأسيس", "حج",
                 "مناسبة", "تهنئة", "تراث", "ثقافي"],
        "avoid": ["booking cta", "menu price", "swatch", "حجز", "منيو"],
    },
}

# scene_core() class → the chain-need it implies (computed bridge, one hop)
_CORE_TO_NEED = {
    "family": "human_life", "friends": "human_life", "solo_calm": "human_life",
    "kids_hero": "human_life", "energy_sport": "human_life", "weather": "human_life",
    "nostalgia": "human_life", "craving": "craving_texture",
    "occasion": "occasion", "product_shoutout": "product_hero",
    "channel_cta": "offer_announce", "offer": "offer_announce", "greeting": "occasion",
}
# the angle's declared post_type → need (a weak prior under the scene-core signal)
_POSTTYPE_TO_NEED = {"announcement": "offer_announce", "offer": "offer_announce",
                     "greeting": "occasion", "moment": "human_life"}

# ── HUMAN-PRESENCE DETECTION (June 21 — the chain≠scene root-fix, BUG-1) ──────────────
# THE BUG (albaik 2026-12-15 dry-run): a scene FULL of people (الأخ الأكبر، طالب جامعي،
# الأم تدخل المطبخ) drew tf02_03 «Sauce Splash · No humans» because scene_core() saw only
# {craving} (جوع/رائحة الفلافل) — the human signal was INVISIBLE: the family regex wants
# عائل|أمي|والدتي, but a scene that NAMES people by role (الأخ، طالب، الأم) carries no such
# token, so the food signal won and a no-humans product splash shipped for a human moment.
# FIX: a SEPARATE human-presence detector over person/role + human-action tokens. When a
# person is present, the dominant need becomes human_life and the no-humans product families
# are HARD-EXCLUDED from the candidate pool (Rule #8: a human scene NEVER gets a no-humans
# chain). Computed — token sets only, no hand-authored per-post map (Rule #12).
_PERSON_TOKENS = re.compile(
    r"أب\b|الأب|أم\b|الأم|أمي|والد|والدة|أخ\b|الأخ|أخت|الأخت|إخوة|أطفال|طفل|الطفل|"
    r"طالب|الطالب|طالبة|أصدقاء|الأصدقاء|صديق|عائلة|العائلة|عيلة|أسرة|الأسرة|"
    r"رجل|الرجل|امرأة|المرأة|شاب|الشاب|شابة|فتاة|الفتاة|فتى|زوج|الزوج|زوجة|الزوجة|"
    r"جد\b|الجد|جدة|الجدة|جدي|جدتي|عامل|العامل|موظف|الموظف|ضيوف|الضيوف|ضيف|الضيف|"
    r"بنت\b|البنت|ابن\b|الابن|أولاد|الأولاد|شخص|الشخص|الناس|عميل|العميل|زبون|الزبون")
# human ACTIONS — a verb of a person doing something in the scene (a second signal so a bare
# role mention isn't required; «يذاكر/تدخل/يتناول» are unmistakably people in a moment)
_HUMAN_ACTION_TOKENS = re.compile(
    r"يجلس|تجلس|يجلسون|يدخل|تدخل|يدخلون|يتناول|تتناول|يأكل|تأكل|يلعب|تلعب|يذاكر|تذاكر|"
    r"يدرس|تدرس|يجتمع|تجتمع|يجتمعون|يبتسم|تبتسم|يضحك|تضحك|يمد يده|تمد يدها|يشرب|تشرب|"
    r"يقف|تقف|يمشي|تمشي|يحمل|تحمل|يراقب|تراقب|يستمتع|تستمتع|يحتفل|تحتفل")
# the families whose PURPOSE is a no-humans single-product shot (splash/levitation/spotlight/
# cosmetic-macro/pedestal). Named by family so the veto survives even though INDEX records
# carry no per-chain «no_humans» flag. A scene with people must NEVER resolve into one.
_NO_HUMANS_FAMILIES = {"TF01", "TF02", "TF03", "TF11", "TF12", "TF14"}


def _scene_has_human(scene_text: str) -> bool:
    """True when the scene depicts a PERSON in a real moment — a person/role noun OR a
    human-action verb. Used to force human_life as the dominant need and HARD-EXCLUDE the
    no-humans product families (BUG-1). Computed over token sets, never a per-post list."""
    t = scene_text or ""
    return bool(_PERSON_TOKENS.search(t) or _HUMAN_ACTION_TOKENS.search(t))


def _scene_needs(scene_text: str, post_type: str, occasion: str) -> list:
    """The ordered chain-needs this scene implies (strongest first). Built ONLY from the
    computed scene_core() + the angle's post_type + whether an occasion is live — never a
    per-post hand list. Returns e.g. ['human_life'] for a family dinner, ['offer_announce']
    for a price card, defaulting to product_hero when nothing classifies."""
    needs = []
    # HUMAN PRESENCE DOMINATES (BUG-1): a scene with people leads with human_life, ahead of
    # any craving/food signal — so a family-kitchen moment can never resolve to a no-humans
    # product splash. The food/craving signal still rides BEHIND it (a human eating food).
    if _scene_has_human(scene_text):
        needs.append("human_life")
    for core in scene_core(scene_text):
        nd = _CORE_TO_NEED.get(core)
        if nd and nd not in needs:
            needs.append(nd)
    if occasion and occasion not in ("evergreen", "daily") and "occasion" not in needs:
        needs.insert(0, "occasion")
    pt_need = _POSTTYPE_TO_NEED.get((post_type or "").lower())
    if pt_need and pt_need not in needs:
        needs.append(pt_need)
    if not needs:
        needs.append("product_hero")  # the safe default: the product is the subject
    return needs


def _chain_purpose_score(chain: dict, needs: list) -> int:
    """How well a chain's PURPOSE fits the scene-needs. Read from the chain's own
    name_en/name_ar/family text (no curated table). +2 per want-keyword hit on the TOP
    need, +1 for lower-ranked needs; -3 per avoid-keyword hit on the top need (a betrayer,
    e.g. a splash chain for a human-meal scene). Deterministic — the same chain+needs
    always scores the same."""
    blob = " ".join(str(chain.get(k, "")) for k in ("name_en", "name_ar", "family")).lower()
    score = 0
    for rank, need in enumerate(needs):
        sig = _CHAIN_PURPOSE_SIGNALS.get(need, {})
        weight = 2 if rank == 0 else 1
        for kw in sig.get("want", []):
            if kw.lower() in blob:
                score += weight
        if rank == 0:  # only the dominant need vetoes a betrayer
            for kw in sig.get("avoid", []):
                if kw.lower() in blob:
                    score -= 3
    return score


def pick_pro_chain(formula_id: str, sector: str, occasion: str,
                   scene_text: str = "", post_type: str = "") -> dict | None:
    """CONTENT-AWARE replacement for the bare chain_for(...)[0] pick. Resolves the same
    candidate pool chain_for() would (formula families ∩ sector/occasion allow-lists), then
    ranks by _chain_purpose_score against the scene's computed needs and returns the best
    fit — so a family-dinner scene gets a lifestyle chain, not a product splash, and a gym
    scene never gets a magazine-cover. Falls back to chain_for() if nothing scores (keeps
    the legacy behaviour as the floor). Rule #12: the chain is chosen by a COMPUTED rule
    over the chain's own purpose, never a hand-authored per-post mapping."""
    import yaml  # local (this module has no top-level yaml dep) — same loader post_unit uses
    from post_unit import chain_for  # the candidate-pool resolver (formula→families ∩ allow)
    forms = yaml.safe_load((BASE / "21_strategy_frameworks/creative_formulas.yaml").read_text())
    fams = []
    for v in forms.get("formulas", {}).values():
        if v.get("id") == formula_id:
            fams = v.get("chain_families", [])
    idx = json.load(open(BASE / "02_what_to_build/INDEX.json"))
    chains = idx if isinstance(idx, list) else idx.get("chains", [])

    def _sector_occ_ok(c):
        sa = c.get("sectors_allowed") or []
        oa = c.get("occasions_allowed") or []
        s_ok = not sa or sector in sa or "all" in sa
        o_ok = not oa or occasion in oa or "all" in oa or "evergreen" in oa or "*" in oa
        return s_ok and o_ok

    def _allowed(c):  # in-pool: formula family AND sector/occasion
        return c.get("family") in fams and _sector_occ_ok(c)
    cands = [c for c in chains if _allowed(c)] or [c for c in chains if c.get("family") in fams]
    if not cands:
        return chain_for(formula_id, sector, occasion)  # legacy floor
    needs = _scene_needs(scene_text, post_type, occasion)

    # BUG-1 HARD VETO: when the scene depicts PEOPLE, the no-humans product families
    # (TF01 levitation / TF02 splash / TF03 spotlight / TF11-TF12 cosmetic-macro / TF14
    # pedestal) are EXCLUDED from BOTH pools — a human moment never resolves to a single-
    # product studio shot, no matter how strong the food/craving signal scores. Computed
    # over the family classification (Rule #12), not a per-post list.
    human_scene = _scene_has_human(scene_text)

    def _human_ok(c):
        return (not human_scene) or (c.get("family") not in _NO_HUMANS_FAMILIES)
    cands = [c for c in cands if _human_ok(c)]

    def _best(pool):
        return max(pool, key=lambda c: (_chain_purpose_score(c, needs),
                                        -_chain_index(c, chains)))
    # POOL-ESCAPE (the family-dinner-as-splash-ring case): the formula's families may not
    # contain ANY chain that serves the scene's dominant need (CF_07's [TF18,TF02,TF11,TF17]
    # holds zero human-life chains, so a family dinner was stuck on a product splash). Two
    # triggers now open the wider pool: (a) the in-pool was emptied by the human veto, or
    # (b) the best in-pool chain still NEGATIVELY fits (betrays the scene more than serves).
    # The wider pool is every sector/occasion-allowed chain whose OWN purpose serves the
    # dominant need AND clears the same human veto. Still a computed rule (Rule #12).
    best = _best(cands) if cands else None
    if best is None or _chain_purpose_score(best, needs) <= 0:
        wide = [c for c in chains
                if _sector_occ_ok(c) and _human_ok(c) and _chain_purpose_score(c, needs) > 0]
        if wide:
            best = _best(wide)
    # Rule #8 — REFUSE, don't ship a wrong chain: a human scene with NO eligible human-capable
    # chain (every candidate was a no-humans family and none scored positive in the wide pool)
    # HOLDS (returns None) rather than handing back a no-humans product chain. render_via_master
    # / the card then carries no pro_chain, and the image step refuses (it never guesses a chain).
    if best is None:
        return None
    if human_scene and best.get("family") in _NO_HUMANS_FAMILIES:
        return None
    return best


def _chain_index(chain: dict, chains: list) -> int:
    """Stable index of a chain in INDEX order — the deterministic tie-break (lower wins),
    so when two chains tie on purpose the original chain_for() order is preserved."""
    cid = chain.get("chain_id_short")
    for i, c in enumerate(chains):
        if c.get("chain_id_short") == cid:
            return i
    return len(chains)


def _chain_card(chain: dict | None) -> dict | None:
    """The card's visual.pro_chain shape from an INDEX chain dict (the mechanical pick)."""
    if not chain:
        return None
    return {"id": chain.get("chain_id_short"), "name_ar": chain.get("name_ar"),
            "family": chain.get("family")}


def resolve_visual(brief: dict | None, mechanical: dict | None) -> tuple:
    """ART-DIRECTOR wiring (June 22, Rule #8/#12) — decide the card's (pro_chain, art_brief,
    hold_reason) from the Art-Director brief. `brief` = art_director.art_direct(...) output, or
    None when the AD wasn't run (a reel, or it errored). `mechanical` = pick_pro_chain(...)'s
    INDEX chain dict — the legacy floor kept as the FALLBACK.

      • no photo brief (reel / AD skipped / AD errored) → the mechanical chain, NO art_brief —
        the existing path is left exactly as it was.
      • photo brief with a cultural BLOCK (gate.blocking) → HOLD (Rule #8): pro_chain=None,
        hold_reason set. The refused brief is still stored so the gate is VISIBLE and
        render_via_master refuses on the missing chain — we NEVER fall back to the mechanical
        chain on a red-line scene (that would render the wrong shot).
      • photo brief, clean WITH a chosen chain → the AD's DELIBERATE chain becomes pro_chain.
      • photo brief, clean but NO chain → the mechanical fallback (the scene is culturally fine;
        the AD simply didn't deliberately pick a chain — the legacy floor stands).

    Pure (no LLM, no I/O) so the wiring is unit-testable at $0."""
    if not brief or brief.get("kind") != "photo_brief":
        return _chain_card(mechanical), None, None
    gate = brief.get("gate") or {}
    if gate.get("blocking"):
        return None, brief, (gate.get("reason") or "cultural red-line in the photo brief")
    ad_chain = brief.get("chain") or {}
    if ad_chain.get("id"):
        return ({"id": ad_chain.get("id"), "name_ar": ad_chain.get("name_ar"),
                 "family": ad_chain.get("family")}, brief, None)
    return _chain_card(mechanical), brief, None


def batch_diversity_check(slots: list, ceiling: float = 0.30) -> dict:
    """B_div_gate (June 13 — RABIE's #1 unbuilt; the hard answer to his 06-13 scar
    «still family / make them different»). diversity_prefer only soft-reorders within
    ONE slot's options and wakes on a last-2 collision — a 6th family idea across a
    batch passed untouched. THIS is the batch-scoped HARD gate: count scene_core() over
    every slot's idea text + count recipe (formula) usage across the whole batch; any
    core or recipe exceeding `ceiling` of the batch is a VIOLATION, with the offending
    slots named for re-roll. Deterministic, zero-LLM (reads planned angle_theme/formula).

    slot fields read: 'angle_theme' or 'scene_ar' (the idea text) + 'formula' (recipe).
    Returns {ok, n, ceiling_count, violations:[{kind,key,count,pct,slots:[dates]}]}.
    """
    import collections as _c
    n = len(slots)
    if n == 0:
        return {"ok": True, "n": 0, "violations": [], "coverage": 1.0}
    cap = int(n * ceiling)  # the most of one core/recipe that may SHIP (≤30%)
    core_slots, formula_slots = _c.defaultdict(list), _c.defaultdict(list)
    classified = 0
    for s in slots:
        ident = s.get("date") or s.get("id") or "?"
        idea = s.get("angle_theme") or s.get("scene_ar") or s.get("idea") or ""
        cores = scene_core(idea)
        if cores:
            classified += 1
        for core in cores:
            core_slots[core].append(ident)
        f = s.get("formula")
        if f:
            formula_slots[f].append(ident)
    violations = []
    for kind, mapping in (("scene_core", core_slots), ("recipe", formula_slots)):
        for key, ids in mapping.items():
            if len(ids) > cap:  # strictly over the ≤30% cap
                violations.append({"kind": kind, "key": key, "count": len(ids),
                                   "pct": round(len(ids) / n * 100, 1),
                                   "slots": ids[cap:]})  # hold the excess DOWN TO the cap
    # coverage: the 52-92% blind-spot must be VISIBLE, never a silent green (RABIE catch)
    coverage = round(classified / n, 2)
    return {"ok": not violations and coverage >= 0.5, "n": n, "cap": cap,
            "ceiling_pct": round(ceiling * 100), "violations": violations,
            "coverage": coverage,
            "low_coverage": coverage < 0.5}


def taste_guard(options: list, kill_patterns: list) -> tuple[list, list]:
    """Returns (kept, killed). Rule #8 — REFUSE, don't warn: if EVERY option carries a
    founder taste-kill ruling, kept is EMPTY. The caller REGENERATES with the kill reasons
    fed back, or HOLDS the slot — a ruled-against caption NEVER ships.
    (June 14 root-hunt of Mohamed's 'all the same / repetition' complaint: the old
    `kept=[options[0]]` re-admitted a caption his ruling had JUST killed — so when the pen
    produced only delivery-CTA/family-scene formulas, the gauntlet correctly killed all 3
    and this line shipped the killed one anyway. THE leak that shipped his repetitive
    patterns. Proven on a live test slot 2026-06-14.)"""
    active = [k.get("pattern") for k in kill_patterns if isinstance(k, dict)]
    kept, killed = [], []
    for o in options:
        hit = next((p for p in active
                    if p in TASTE_GUARD_LEXICON and TASTE_GUARD_LEXICON[p].search(o)), None)
        (killed if hit else kept).append((o, hit) if hit else o)
    return kept, killed


def env(k):
    # ~/.abraham_env first, then the shell env (June 17 handover fix: a dev sets OPENAI_API_KEY /
    # ANTHROPIC_API_KEY in their shell and has no .abraham_env — don't force them to create one).
    p = os.path.expanduser("~/.abraham_env")
    if os.path.exists(p):
        for l in open(p):
            if l.startswith(k + "="):
                return l.split("=", 1)[1].strip().strip('"')
    v = os.environ.get(k)
    if v:
        return v
    sys.exit(f"no {k} (set it in ~/.abraham_env or export it as an env var)")


def gpt(messages, temp=0.7, max_tok=900, fmt_json=True):
    body = {"model": mr.CAPTION_MODEL_PRIMARY, "temperature": temp, "max_tokens": max_tok, "messages": messages}
    if fmt_json:
        body["response_format"] = {"type": "json_object"}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=120).read())["choices"][0]["message"]["content"]


def sonnet(system, messages, max_tok=900):
    body = {"model": mr.CAPTION_MODEL_FALLBACK, "max_tokens": max_tok, "system": system, "messages": messages}
    rq = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                headers={"x-api-key": env("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01",
                                         "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=120).read())
    return out["content"][0]["text"]


HUMAIN_SVC = "http://127.0.0.1:4111"


def humain(system, user, timeout_s=180):
    """The DIVERSITY pen — ALLaM 34B (Saudi-native) via the local HUMAIN service. Replaces the
    dark Sonnet pen (Anthropic credits dry). POSTs to humain_service; returns the raw model text.
    Raises on any failure so the caller's try/except falls back to GPT-only (Rule: never stuck)."""
    prompt = (system + "\n\n" + user +
              '\n\nأرجع فقط كائن JSON بالشكل: {"options": ["...", "...", "..."]} بدون أي شرح.')
    body = json.dumps({"prompt": prompt, "timeout_s": timeout_s}).encode()
    rq = urllib.request.Request(f"{HUMAIN_SVC}/caption", data=body,
                                headers={"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=timeout_s + 30).read())
    reply = out.get("reply")
    if not reply:
        raise RuntimeError("humain returned no reply (not logged in / timeout)")
    return reply


def humain_up() -> bool:
    """True if the HUMAIN service is running AND logged in (cheap /health check)."""
    try:
        out = json.loads(urllib.request.urlopen(f"{HUMAIN_SVC}/health", timeout=3).read())
        return bool(out.get("logged_in"))
    except Exception:
        return False


def load_client(handle: str) -> dict:
    from truth_guards import is_en_led  # B043: ONE EN-led boundary shared with creative_line
    cdir = BASE / "clients" / handle
    p = lambda n: json.loads((cdir / "profile" / f"{n}.json").read_text())
    profile_raw = sorted((cdir / "raw/instagram").iterdir())[-1]
    posts = [json.loads(l) for l in (profile_raw / "posts.jsonl").read_text().strip().split("\n") if l.strip()]
    prof = json.loads((profile_raw / "profile.json").read_text())
    # voice exemplars: client's own top-liked real captions (style only)
    real = sorted([x for x in posts if x.get("caption")], key=lambda x: -(x.get("likesCount") or 0))[:5]
    exemplars = [x["caption"][:300] for x in real]
    # jurisha special: provisional voice A from the birth week (RABIE 5/5, stamped provisional)
    vb = cdir / "voice_birth_week.json"
    if vb.exists():
        v = json.loads(vb.read_text())
        va = next((x for x in v.get("voices", []) if x.get("id") in ("A", "voice_a")), None)
        if va:
            exemplars = va.get("posts", [])[:3] + exemplars[:2]
    # FEW-SHOT QUARANTINE (June 14 root-hunt of Mohamed's 'all the same / repetition'):
    # a few-shot example matching an ACTIVE kill_pattern TEACHES the pen the exact formula
    # he banned. All 6 jurisha gold AND many corpus top-liked captions were delivery-CTA or
    # family-scene → the pen reproduced his banned cores. NO few-shot source (gold, corpus,
    # voice-birth) may carry an active-banned formula.
    _tf = cdir / "profile/taste.json"
    _active = [k.get("pattern") for k in (json.loads(_tf.read_text()).get("kill_patterns", [])
               if _tf.exists() else []) if isinstance(k, dict)]
    _teaches_banned = lambda ln: (any(w in ln for w in STANDING_WORN)
                                  or any(pp in TASTE_GUARD_LEXICON and TASTE_GUARD_LEXICON[pp].search(ln)
                                         for pp in _active))
    # GOLD first (June 12, the ceiling stretch): lines the chair rated >=4 are the
    # strongest few-shot signal — they lead, corpus exemplars fill behind
    gold_entries = []
    gf = cdir / "profile/gold.json"
    if gf.exists():
        gold_entries = [g for g in json.loads(gf.read_text()).get("gold", [])
                        if not _teaches_banned(g.get("line", ""))]
        gold_lines = [g["line"] for g in gold_entries]
        if gold_lines:
            exemplars = gold_lines[:3] + [e for e in exemplars if e not in gold_lines][:2]
    # final sweep across ALL sources — formula-teaching lines never reach the pen
    exemplars = [e for e in exemplars if not _teaches_banned(e)]
    truth = p("truth_pack")
    # grounding corpus for the noun guard: everything the client has actually said
    corpus_text = " ".join([x.get("caption") or "" for x in posts] + [prof.get("biography", "")]
                            + [x["name"] for x in truth["product_candidates"]]
                            + truth.get("recurring_caption_terms", []))
    # G9-lite (June 12, cold-eyes round 4): the pen develops catchphrases («ما يكتمل إلا»)
    # — mine the client's RECENT rendered captions for worn phrases, ban them this render
    import glob as _g, collections as _c, re as _re
    recent = sorted(_g.glob(str(cdir / "posts/*__v5.json")),
                     key=lambda f: -Path(f).stat().st_mtime)[:20]
    grams = _c.Counter()
    n_cards = 0
    for _f in recent:
        try:
            _caps = json.loads(open(_f).read()).get("captions") or []
        except Exception:
            continue
        if not _caps:
            continue
        n_cards += 1
        words = _re.findall(r"[ء-ي]+", " ".join(_caps))
        for j in range(len(words) - 2):
            grams[" ".join(words[j:j+3])] += 1
    worn = [g for g, c in grams.most_common(8) if n_cards >= 5 and c >= max(3, n_cards * 0.25)]
    # CROSS-BRAND universals (law: no_template_bleed; measured June 12 cold consult:
    # لحظة in 19.8% of 3,323 captions across ALL brands, يجمعنا across 4 minds,
    # «له طعم ثاني» skeleton 29×) — per-client mining can't see cross-client bleed,
    # so these are banned standing, every client, every render
    worn += STANDING_WORN
    taste_f = cdir / "profile/taste.json"
    kill_patterns = (json.loads(taste_f.read_text()).get("kill_patterns", [])
                     if taste_f.exists() else [])
    recent_cores = []
    for _f in recent[:6]:
        try:
            _caps2 = json.loads(open(_f).read()).get("captions") or []
        except Exception:
            continue
        if _caps2:
            recent_cores.append(scene_core(" ".join(_caps2)))
    return {"handle": handle, "worn_phrases": worn, "gold_entries": gold_entries,
            "kill_patterns": kill_patterns, "recent_cores": recent_cores,
            "brand_ar": prof.get("fullName") or handle,
            "bio": prof.get("biography", ""), "truth": truth,
            "moments": p("moments_bank")["moments"], "fingerprint": p("fingerprint"),
            "state": p("state"), "exemplars": exemplars, "corpus_text": corpus_text,
            "visual_dna": (json.loads((cdir / "profile/visual_dna.json").read_text())
                           if (cdir / "profile/visual_dna.json").exists() else None),
            "en_led": is_en_led(fingerprint=p("fingerprint"))}


def rank_gold_exemplars(gold_entries: list, occasion: str, corpus_exemplars: list) -> list:
    """B181: gold few-shot is occasion-aware — an eid slot few-shots from eid gold.
    Order: occasion-matching gold → Mohamed-confirmed gold → other gold → corpus fill."""
    occ = occasion or ""
    match = [g["line"] for g in gold_entries if g.get("occasion") == occ]
    moh = [g["line"] for g in gold_entries
           if g.get("confirmer") == "mohamed" and g["line"] not in match]
    rest = [g["line"] for g in gold_entries if g["line"] not in match and g["line"] not in moh]
    ranked = list(dict.fromkeys(match + moh + rest))[:3]
    return ranked + [e for e in corpus_exemplars if e not in ranked][:2]


LIFE_CONTEXTS = ["عائلة في البيت", "أصدقاء وشلة", "شخص وحده — هدوء مع نفسه",
                  "يوم عمل ودوام", "الشارع والحي والسوق", "حركة ورياضة وطلعة",
                  "ضيوف ومناسبة اجتماعية"]


def life_context(handle: str, date: str) -> str:
    """zoom-r8: 93% of albaik's year was family-themed — the pen's default context.
    Date-hashed rotation forces the scene into different LIVES (the brand is eaten
    by students, workers, singles — not only families)."""
    import hashlib
    return LIFE_CONTEXTS[int(hashlib.md5(f"{handle}{date}ctx".encode()).hexdigest(), 16) % len(LIFE_CONTEXTS)]


def angle_prompt(c: dict, slot: dict, sector: str, brain: str | None = None) -> tuple[str, str, str | None]:
    """Build the (system, user, brain) prompt for ONE concrete-scene angle (pure, no LLM call).

    Extracted from make_angle (June 23) so BOTH the single-pen make_angle AND the multi-model
    CD-brain PANEL (cd_panel.py — W1/W3) build the SAME prompt from the same organs: the methodology
    BODY injection, the CEO strategy frame, the occasion-truth rule, the client-rules armor, the
    sector/food guards, the real-moments seed. The panel then fans the SAME prompt across GPT/Gemini/
    Groq (the minds on DIFFERENT models) — one source of truth for what a CD brain is asked.

    Returns (sys_p, user, brain) — brain is returned because the heritage→firaasa Arabic-root guard
    may swap it; callers must use the returned brain for provenance.
    """
    import occasion_align as _oa
    import client_rules as _cr
    _ov = _cr._overrides(c["handle"])
    _ab = []
    if _ov.get("real_person_mentions") == "off":
        _ab.append("NO named real person (roles only — never «الكابتن عادل»)")
    if str(_ov.get("family_voice_lines", "")).startswith("blocked"):
        _ab.append("NO family member speaking/quoted")
    if _ov.get("face_visibility") == "never" or _ov.get("family_member_visibility") == "never":
        _ab.append("the scene must work with NO visible faces/family (hands/food/objects/place)")
    if _cr._is_cloud_kitchen(c["handle"]):
        _ab.append("DELIVERY-ONLY — never a dine-in/restaurant/cart scene; the food arrives")
    if sector in _cr.FOOD_SECTORS:
        _ab.append("NO gym/workout setting (food brand)")
    organ_rule = ("\nCLIENT RULES (confirmed — never break): " + "؛ ".join(_ab) + ".") if _ab else ""
    # CEO STRATEGY BRIEF (Phase 2, June 14): the CD brain produces INSIDE the C-suite frame —
    # the strategy stage already analysed the full client organs; the angle pursues its pillars/angles.
    _sb = BASE / "clients" / c["handle"] / "profile" / "strategy_brief.json"
    strat_rule = ""
    if _sb.exists():
        _s = json.loads(_sb.read_text())
        _pil = (_s.get("everyday_pillars") or [])[:6]
        _ang = (_s.get("angles_to_pursue") or [])[:5]
        if _pil or _ang:
            strat_rule = ("\nCEO STRATEGY (produce inside this): positioning «" + (_s.get("positioning") or "")[:80]
                          + "»; everyday pillars " + json.dumps(_pil, ensure_ascii=False)
                          + ("; pursue an angle like: " + json.dumps(_ang, ensure_ascii=False)[:400] if _ang else "") + ".")
    facts = json.loads((BASE / "data/occasion_facts.json").read_text())
    occ = slot.get("occasion", "")
    key = {"saudi_national_day": "saudi_national_day"}.get(occ, occ)
    lens = (facts.get(key, {}).get("sector_lenses") or {}).get(sector, {})
    products = [x["name"] for x in c["truth"]["product_candidates"]] + c["truth"]["recurring_caption_terms"][:5]
    channels = [x["name"] for x in c["truth"]["channels"] if x["name"] != "linktree"]
    if brain == "heritage" and not any(ch in c["brand_ar"] for ch in "ءاأبتثجحخدذرزسشصضطظعغفقكلمنهوي"):
        brain = "firaasa"  # heritage needs an Arabic root to work with (RABIE: jurisha national-day drift)
    method = ""
    if brain:
        m = brain_method(brain)
        if m:
            method = f"\n\nYOUR METHODOLOGY (you are the {brain} CD brain — apply this method to find the angle):\n{m}\n"
    # OCCASION TRUTH at the ANGLE layer (RABIE 2026-06-14 — the visual leaks because the ANGLE
    # invented a holiday, then shot_card built the brief from that angle). A daily scene has NO
    # holiday; example moments that show one are filtered OUT so the pen isn't seeded with it.
    daily = _oa.is_daily(slot)
    occ_rule = ("\nTHIS IS AN EVERYDAY SCENE — there is NO holiday. The scene must NOT be set in or "
                "reference Eid, Ramadan, National Day, Founding Day, Hajj, or Mother's Day — even if an "
                "example moment below shows one. A plain ordinary day." if daily else
                f"\nTHE SCENE IS DURING «{_oa.slot_occ_key(slot) or occ}» — live inside THAT occasion, no other.")
    moments_pool = [m for m in c["moments"]
                    if not (daily and _oa.occ_hits(m.get("evidence") or ""))]  # drop occasion moments on daily
    ex = [m["evidence"][:70] for m in (lambda ms, d: [ms[(sum(ord(ch) for ch in d) + j) % len(ms)]
          for j in range(min(3, len(ms)))])(moments_pool, slot.get("date", ""))] if moments_pool else []
    sys_p = ("You are a Saudi creative director generating ONE angle (idea), not a caption. "
             "An angle is a CONCRETE SCENE: WHO (specific person/role) + WHEN (specific beat) + WHAT (specific gesture) "
             "+ where the product sits naturally inside that exact moment. BANNED: brand-as-bridge/symbol/soul metaphors, "
             "abstract culture/heritage sentences, anything a TV voiceover could say. "
             + occ_rule + organ_rule + strat_rule + method +
             'Return JSON: {"scene_ar": "...", "why_it_lands": "...", "post_type": "moment|announcement|offer|greeting"}')
    user = (f"البراند: {c['brand_ar']} (bio: {c['bio'][:150]})\n"
            f"المنتجات الحقيقية: {products[:8]}\nالقنوات: {channels or 'غير معروفة — لا تخترع قناة'}\n"
            f"السياق: {slot.get('occasion') or slot.get('angle_theme','')} · beat: {slot.get('beat','evergreen')}\n"
            + (f"عدسة القطاع×المناسبة: {json.dumps(lens, ensure_ascii=False)[:600]}\n" if lens else "")
            + (f"لحظات حقيقية من منشوراتهم: {json.dumps(ex, ensure_ascii=False)}\n" if ex else "")
            + ("NOTE: this brand speaks English-first — the scene may be EN-hook + AR-idea bilingual.\n" if c["en_led"] else "")
            + f"سياق الحياة لهذا اليوم — المشهد يعيش داخله (مو شرط عائلة!): {life_context(c['handle'], slot['date'])}\n"
            + f"التاريخ الفعلي للنشر: {slot['date']}")
    return sys_p, user, brain


def make_angle(c: dict, slot: dict, sector: str, brain: str | None = None,
               panel: bool = False) -> dict:
    """ONE angle (idea) for a slot, born from a CD-brain methodology.

    Default (panel=False): the single-pen path — GPT-4o, Sonnet fallback (back-compat).
    panel=True (W3, June 23 — "the full system must work, all agents and minds"): the angle is
    born from the 5-CD-BRAIN PANEL (cd_panel.run_panel) — the routed brains each run on a DIFFERENT
    model (GPT/Gemini/Groq via consult.py) and the lead brain's angle is returned, with the rival
    angles attached as `panel_alts` so the caption pen is SEEDED by the minds (not invented
    mechanically). A dead model/key falls back inside the panel — never blocks the pipeline.
    """
    if panel:
        try:
            import cd_panel
            picked = cd_panel.run_panel(c, slot, sector, lead_brain=brain)
            if picked:
                return picked
        except Exception as _pe:
            print(f"  panel failed ({type(_pe).__name__}: {str(_pe)[:60]}) — single-pen fallback", file=sys.stderr)
    sys_p, user, brain = angle_prompt(c, slot, sector, brain=brain)
    # quota-resilience (June 12, the day OpenAI ran dry mid-regen): the angle falls
    # back to the Anthropic pen — degraded single-pen mode beats a dead pipeline
    try:
        out = json.loads(gpt([{"role": "system", "content": sys_p}, {"role": "user", "content": user}], temp=0.8, max_tok=400))
    except Exception as _e:
        print(f"  gpt angle failed ({str(_e)[:40]}) — sonnet fallback", file=sys.stderr)
        raw = sonnet(sys_p, [{"role": "user", "content": user + "\n\nأجب بكائن JSON فقط، بدون أي نص خارجه."}], max_tok=500)
        i, j = raw.find("{"), raw.rfind("}")
        out = json.loads(raw[i:j + 1])
    out.setdefault("brain", brain)
    out.setdefault("by_model", "gpt")
    return out


CTA_PUSH_TYPES = {"weekly_offer", "white_friday", "11_11_shopping", "singles_day_11_11"}


CTA_EMOTIONAL = {"ramadan", "eid_al_fitr", "eid_al_adha", "arab_mothers_day", "hajj_season"}


def cta_allowed(handle: str, slot: dict) -> bool:
    """The 80/20 law in code (zoom-out June 12: 300/356 jurisha cards = 84% order-tails,
    the inverse of the standard; Mohamed's wrong_goal code says it himself: «صفر طاقة
    بيع — اللحظة فقط»). Push slots sell; evergreen sells ~1 day in 4, date-hashed."""
    # gold-seed r1 (June 12): emotional occasions NEVER sell — G2's spirit at the
    # gate, not only the guard (the mothers-day هنقرستيشن seed exposed the hash gap)
    if slot.get("occasion") in CTA_EMOTIONAL:
        return False
    if slot.get("occasion") in CTA_PUSH_TYPES or slot.get("type") == "offer":
        return True
    import hashlib
    return int(hashlib.md5(f"{handle}{slot.get('date','')}cta".encode()).hexdigest(), 16) % 4 == 0


def _bilingual_clause(en_led: bool) -> str:
    """The EN-hook+AR-idea language bar for the producing pen (B044, a CONFIRMED taste reward:
    'EN hook + AR idea, NOT translation'). en_led brands get the bilingual instruction with the
    validated bar example + the fitness-filler ban; everyone else is held to Saudi Arabic only.
    Pure + named so the gate is regression-locked (the inline string was untestable)."""
    if en_led:
        return ("Write EN hook + Arabic idea (bilingual, NOT translation). "
                "English lines carry a CONCRETE moment or real instruction — never fitness-influencer filler "
                "('Feeling strong!', 'Ready for more!', 'New week, new you'). The bar: "
                "'Your Friday just got better — تحرّك مع لياقتي، الكابتن في جيبك'.")
    return "Write Saudi Arabic only."


def render_captions(c: dict, slot: dict, angle: dict) -> list[str]:
    import occasion_align as _oa
    import client_rules as _cr
    # the client's CONFIRMED organs, fed to the pen so it produces clean (not produce→block→waste)
    _ov = _cr._overrides(c["handle"])
    _organ_bits = []
    if _ov.get("real_person_mentions") == "off":
        _organ_bits.append("NEVER name a real person (no «الكابتن عادل», no «أبو فلان») — roles only, never names")
    if str(_ov.get("family_voice_lines", "")).startswith("blocked"):
        _organ_bits.append("NEVER put words in a family member's mouth (no «أختي تقول:…», no «الجد يهمس»)")
    if _cr._is_cloud_kitchen(c["handle"]):
        _organ_bits.append("DELIVERY-ONLY cloud kitchen — never a restaurant/cafe/dine-in/food-cart/branch scene")
    if _cr._sector(c["handle"]) in _cr.FOOD_SECTORS:
        _organ_bits.append("NEVER a gym/workout setting or post-workout framing (this is a food brand)")
    organ_clause = ("CLIENT RULES (the founder confirmed these — breaking one kills the post): "
                    + "؛ ".join(_organ_bits) + ". " if _organ_bits else "")
    taste = json.loads((BASE / "data/founder_taste.json").read_text())
    products = [x["name"] for x in c["truth"]["product_candidates"]][:5]
    channels = [x["name"] for x in c["truth"]["channels"] if x["name"] != "linktree"]
    # LEARNED phrase-bans (Mohamed's prior 'no's) — fed to the pen so it AVOIDS them upfront,
    # not produces→blocks→wastes (June 14 Consumer-Law gap: the bans had a reader in
    # pre_ship_gate but the PRODUCER never saw them, so 6/8 fresh posts blocked on «أول لقمة»).
    _lf = BASE / "data/learned_gate_rules.json"
    _lg = json.loads(_lf.read_text()) if _lf.exists() else {}
    learned_bans = sorted(set([p for p in _lg.get("phrase_bans", []) if p]
                          + [r.get("phrase_ban") for r in _lg.get("rules", []) if r.get("phrase_ban")]))
    # FOUNDER TASTE LAW (June 18 — severed-wire fix, Rule #6): founder_taste.json was loaded
    # above and THROWN AWAY — the producing pen never saw his confirmed taste law, though the
    # file IS the bar ("the critic mind judges against it"). creative_line.py used it; this
    # production renderer (the grinder's pen) didn't. Now woven into sys_p so the pen AVOIDS his
    # kills and aims for his rewards UPFRONT, instead of produce→critic-kill→regenerate (the same
    # consumer-law gap that lost the learned phrase-bans, June 14).
    _tk = "؛ ".join(f"{k['name']} ({k['why'][:70]})" for k in taste.get("kills", [])[:8])
    _tr = "؛ ".join(f"{r['name']} ({r['why'][:70]})" for r in taste.get("rewards", [])[:4])
    taste_clause = ((f"THE FOUNDER'S TASTE LAW — he KILLS these, never produce them: {_tk}. " if _tk else "")
                    + (f"He REWARDS these, aim for them: {_tr}. " if _tr else ""))
    # MEASUREMENT-ONLY toggle (June 18, taste_clause_ab.py eyes-test): when OGZ_TASTE_OFF=1 the pen
    # runs WITHOUT his taste law — the "before" arm of the before/after the wire fix needs to prove
    # it sharpens output (Rule #13: connected ≠ better). Default unset → law ON, zero production change.
    if os.environ.get("OGZ_TASTE_OFF") == "1":
        taste_clause = ""
    # OCCASION TRUTH (June 14 — "confirmed with occasion, everything aligned"): tell the pen the
    # slot's REAL calendar status. A daily slot has NO occasion → forbid all holiday words; an
    # occasion slot must live inside THAT occasion only. The gauntlet below enforces it.
    if _oa.is_daily(slot):
        occ_clause = ("THIS IS AN EVERYDAY POST — there is NO holiday today. NEVER mention or imply "
                      "Eid, Ramadan, National Day, Founding Day, Hajj, or Mother's Day. Just the ordinary "
                      "everyday moment (a regular day, a meal, a workout, a craving). ")
    else:
        _ok = _oa.slot_occ_key(slot) or slot.get("occasion")
        occ_clause = (f"TODAY'S OCCASION IS «{_ok}» — the caption must live inside THAT occasion and NO other "
                      "(never blend a different holiday into it). ")
    bilingual = _bilingual_clause(c["en_led"])
    sys_p = (f"You write Instagram captions for {c['brand_ar']}. ONE angle, given below — every caption is that angle. "
             f"Always write the brand name in Arabic exactly as «{c['brand_ar']}» — NEVER transliterate it into Latin "
             "letters (no 'Liaqti', no 'Liaqti.tu') — a mangled Latin name reads as a fake and gets killed. "
             "The caption LIVES INSIDE the scene: write from inside that exact moment (its person, its time, its gesture). "
             "The PHOTO already shows the scene — so the caption NEVER narrates it (never 'الأم تضغط الزر، الجد يملأ الأطباق'). "
             "Write what the person in that moment would SAY or feel — the voice FROM the scene, not a description OF it. "
             + occ_clause + organ_clause + taste_clause +
             f"{bilingual} Short captions. Concrete and warm. Offers need what/how-much/where clarity. "
             f"Use ONLY these real facts — products: {products}, channels: {channels or 'NONE — never invent ordering channels'}. "
             + ("Speak only of what the reader can DO today with these real products and channels. "
                if cta_allowed(c["handle"], slot) else
                "TODAY IS A BRAND-BUILD DAY: zero selling energy, NO ordering CTA, do NOT mention "
                "delivery apps or ordering — the moment only (the channels above exist; just don't push them today). ")
             + (f"WORN OUT this month — find another way to say it: {c.get('worn_phrases')}. " if c.get("worn_phrases") else "")
             + (f"FORBIDDEN PHRASES — the founder rejected these exact phrasings; NEVER use them: {learned_bans}. "
                if learned_bans else "")
             + (("BANNED THEMES for this client (the founder's explicit ruling — find a different "
                 "emotional core): " + ", ".join(k.get("pattern", "") for k in c.get("kill_patterns", [])) + ". ")
                if c.get("kill_patterns") else "")
             + "When the brand has a signature product NAME in its own words (recurring terms), USE it — never genericize it away. "
             "No invented hashtags. Return JSON: {\"options\": [\"...\", \"...\", \"...\"]}")
    few = []
    for ex in c["exemplars"][:3]:
        few += [{"role": "user", "content": "اكتب بصوت البراند"}, {"role": "assistant", "content": ex}]
    user = f"الفكرة (الزاوية): {angle['scene_ar']}\nالسياق: {slot.get('occasion') or slot.get('angle_theme','')} في {slot['date']}\nاكتب 3 خيارات."
    # DOORS — structural variety so the 3 options can't collapse into ONE shape (June 14
    # root-hunt: the #1 repetition driver was one formula echoed 3×). Each option enters
    # the scene through a DIFFERENT door. Moved onto the LIVE pen (gpt): the 2nd pen
    # (sonnet) is DARK — Anthropic credit balance too low, HTTP 400, verified 2026-06-14 —
    # so the diversity engine had been off entirely; the one live pen now carries it.
    DOORS = ["the SOUND of the moment (what you hear before you see)",
             "the SIDE CHARACTER (the little sister, the neighbor, the delivery man)",
             "the second AFTER the expected moment (the empty plate, the closed door)",
             "the OBJECT's point of view (the pot, the box, the doorbell)",
             "a SENSORY detail — steam, texture, a smell — with no person named",
             "a QUESTION the reader is already asking themselves"]
    base = sum(ord(ch) for ch in slot.get("date", ""))
    doors3 = [DOORS[(base + j) % len(DOORS)] for j in range(3)]

    def _gen(extra: str = "") -> list:
        """One generation pass (reused by the regen loop). extra = kill-feedback directive."""
        directive = ("\n\nThe 3 options MUST be structurally different from each other — "
                     f"option 1 enters the scene through {doors3[0]}; option 2 through {doors3[1]}; "
                     f"option 3 through {doors3[2]}. None may read like a delivery-app push or a "
                     "generic family-gathering line." + extra)
        got = []
        try:
            got += json.loads(gpt([{"role": "system", "content": sys_p + directive}] + few
                                  + [{"role": "user", "content": user}], temp=0.95)).get("options", [])
        except Exception as e:
            print(f"  gpt pen failed: {str(e)[:60]}", file=sys.stderr)
        # 2nd pen — HUMAIN (ALLaM 34B, Saudi-native) via the local service: the model-diversity
        # pen (Mohamed June 24: "for the captions try humain"). Replaces the dark Sonnet pen.
        # FAST GUARD: only call if the service is up AND logged in (3s health check), else a
        # not-logged-in HUMAIN would block 180s on every caption — skip instantly instead.
        try:
            if not humain_up():
                raise RuntimeError("service down / not logged in")
            h_sys = (sys_p + f"\nYOUR PEN'S TEMPERAMENT: enter through {DOORS[(base + 3) % len(DOORS)]}." + extra)
            txt = humain(h_sys, user)
            m = re.search(r"\{.*\}", txt, re.S)
            if m:
                got += json.loads(m.group(0)).get("options", [])
            else:
                # ALLaM may answer in plain Arabic lines — harvest non-empty lines as options
                got += [ln.strip(" -•—\t") for ln in txt.splitlines()
                        if ln.strip() and len(ln.strip()) > 12][:3]
        except Exception as e:
            print(f"  humain pen unavailable ({str(e)[:50]}) — gpt-only this slot", file=sys.stderr)
        # 3rd pen — Sonnet, only if Anthropic has credits (silent + harmless when dark)
        try:
            txt = sonnet(sys_p + f"\nYOUR PEN'S TEMPERAMENT: enter through {DOORS[(base + 4) % len(DOORS)]}."
                         + extra + "\nReturn ONLY the JSON object.", few + [{"role": "user", "content": user}])
            m = re.search(r"\{.*\}", txt, re.S)
            if m:
                got += json.loads(m.group(0)).get("options", [])
        except Exception as e:
            print(f"  sonnet pen dark ({str(e)[:40]}) — skipped", file=sys.stderr)
        return got

    opts = _gen()
    # truth guard 1: strip hashtags that aren't the client's real ones
    # truth guard 2 (June 11, RABIE-ruled): kill EVENT CLAIMS — inviting people to a
    # gathering/session that isn't in the truth pack is a fabricated fact ("join us in
    # Tabbouk's park for a yoga session" — no such event exists). Bans live in code.
    real_tags = set(c["truth"].get("real_hashtags", []))
    # B033 (June 12): the law lives in ONE module — the renderer's frozen local copy
    # let the career-story claim through while truth_guards had already evolved.
    from truth_guards import EVENT_CLAIM
    # truth guard 3: offer energy on emotional occasions = founder kill (code-level)
    EMOTIONAL = {"ramadan", "eid_al_fitr", "eid_al_adha", "saudi_national_day", "saudi_founding_day", "arab_mothers_day"}
    OFFER = re.compile(r"عرض|خصم|تخفيض|كود|discount|offer|% ?off|promo", re.I)
    is_emotional = slot.get("occasion") in EMOTIONAL
    # truth guard 4 (June 11, RABIE-ruled): NOUN GROUNDING — invented product/promo NAMES
    # («التوأم كرسبي بيك x2», mangled app names) must trace to the client's own corpus.
    # Deterministic: suspect tokens = Latin names with digits/dots/caps, or Arabic promo-name
    # constructions; killed unless the client's real captions/bio/truth pack contain them.
    corpus = (c.get("corpus_text") or "").lower()
    # PRODUCT NAMES are grounded truth (June 23 — the producer↔render product-name wire): the brand's
    # real products (the product_truth organ + visual_dna products) are CONFIRMED, so a caption naming
    # دبل بيك / سوبر رول / جريش must NOT be killed as an "ungrounded" promo name. The render already
    # grounds them (product_truth); now the caption gate does too, so a product post can name its hero.
    try:
        _ptf = Path(__file__).parent.parent / "clients" / c.get("handle", "") / "profile" / "product_truth.json"
        if _ptf.exists():
            corpus = corpus + " " + " ".join(json.loads(_ptf.read_text()).keys()).lower()
    except Exception:
        pass
    corpus = corpus + " " + " ".join(str(p) for p in (c.get("products") or [])).lower()
    from truth_guards import PROMO_AR, LATIN_NAME
    # truth guard 5 (June 11 — the hallucinated prince): NAMED PEOPLE die unless the
    # client's corpus contains them. Inventing a person's presence is the worst truth
    # violation possible («بحضور الأمير سعود بن عبدالله بن جلوي» — never happened).
    from truth_guards import PERSON_AR, PERSON_EN  # B034: EN-led feeds leak named people too

    strip_punct = lambda s: re.sub(r"[^\wء-ي\s]", "", s).strip()  # «دبل القرمشة،» == «دبل القرمشة»

    # person-event law (June 11, RABIE-accepted): real-person mentions live ONLY on
    # documented-moment slots; fictional/evergreen scenes are PERSON-FREE. A corpus-real
    # person in an invented scene = real prince, fabricated ribbon-cutting (the nuance
    # under false-flag #2). Corpus-grounded mentions surviving here still get a
    # REQUIRES-HUMAN-VERIFY line on the visual gate.
    slot_is_documented = bool(slot.get("documented_moment"))

    def ungrounded(text: str) -> str | None:
        for m in list(PERSON_AR.finditer(text)) + list(PERSON_EN.finditer(text)):
            if not slot_is_documented:
                return m.group(0) + " (person in fictional scene)"
            if strip_punct(m.group(0)).lower() not in corpus:
                return m.group(0)
        for m in PROMO_AR.finditer(text):
            if strip_punct(m.group(0)).lower() not in corpus:
                return m.group(0)
        for m in LATIN_NAME.finditer(text):
            t = strip_punct(m.group(0)).lower()
            if t and t not in corpus and t not in {"x", "ksa"} and not t.isdigit():
                return m.group(0)
        return None

    _clean_reasons = []  # why _clean dropped lines this pass (for regen feedback)

    def _clean(raw: list) -> list:
        out = []
        _clean_reasons.clear()
        for o in raw:
            o = re.sub(r"#([\wء-ي_]+)", lambda m: m.group(0) if m.group(1) in real_tags else "", o).strip()
            # JSON-artifact strip (June 14): the pen sometimes returns a string carrying its own
            # closing quote/comma/brace («...والدعم.',») — scrub trailing structural junk, then
            # if a stray UNBALANCED double-quote remains (odd count → dangling dialogue), drop the
            # naked quote chars so the line reads clean (balanced dialogue quotes are left intact).
            o = re.sub(r"""['"`]*\s*[,}\]]+\s*$""", "", o).strip().strip('"“”').strip()
            if o.count('"') % 2 == 1:
                o = o.replace('"', "").strip()
            if not o:
                continue
            if EVENT_CLAIM.search(o):
                print(f"  ✂️ event-claim killed: {o[:60]}…", file=sys.stderr)
                continue
            if any(b in o for b in learned_bans):
                hit = next(b for b in learned_bans if b in o)
                print(f"  ✂️ learned-ban killed [{hit}]: {o[:50]}…", file=sys.stderr)
                _clean_reasons.append("learned")
                continue
            # CLIENT-RULES caption-level kill (real-person/family-voice/brand-register/cross-brand) —
            # the confirmed organs; visual-level rules (faces/family) are enforced in shot_card + gate.
            _cv = [(k, det) for k, sev, det in _cr.violations({"captions": [o]}, c["handle"]) if sev == "block"]
            if _cv:
                print(f"  ✂️ client-rule killed [{_cv[0][0]}]: {o[:50]}…", file=sys.stderr)
                _clean_reasons.append("organ")
                continue
            # OCCASION ALIGNMENT (June 14 — "confirmed with occasion"): a daily caption that
            # invents a holiday, or an occasion caption that wanders to another holiday, is
            # killed → the regen loop feeds the reason back. NEVER ships misaligned.
            mis = _oa.caption_misaligned(slot, o)
            if mis:
                print(f"  ✂️ occasion-misalign killed [{mis}]: {o[:50]}…", file=sys.stderr)
                _clean_reasons.append("occasion")
                continue
            if is_emotional and OFFER.search(o):
                print(f"  ✂️ offer-on-emotional killed: {o[:60]}…", file=sys.stderr)
                continue
            bad = ungrounded(o)
            if bad:
                print(f"  ✂️ ungrounded name killed [{bad}]: {o[:50]}…", file=sys.stderr)
                _clean_reasons.append("ungrounded")
                continue
            out.append(o)
        return out

    cleaned = _clean(opts)
    kept, taste_killed = taste_guard(cleaned, c.get("kill_patterns", []))
    for o, hit in taste_killed:
        print(f"  ✂️ taste-kill [{hit}] (his ruling): {o[:50]}…", file=sys.stderr)
    # REGEN, don't re-admit (Rule #8 + the June 14 root-hunt fix): if EVERYTHING was killed —
    # by his taste rulings OR by occasion-misalignment OR by an ungrounded name — the pen is
    # stuck on a shape it can't ship; feed the exact reason back and try again. NEVER re-admit
    # a killed caption; hold the slot if the pen still can't escape (zero-caption path catches it).
    tries = 0
    while not kept and (taste_killed or _clean_reasons) and tries < 2:
        tries += 1
        banned_cores = "، ".join(sorted({h for _, h in taste_killed if h}))
        forbidden = "؛ ".join(o[:40] for o, _ in taste_killed[:4])
        bits = []
        if banned_cores:
            bits.append(f"the founder's rulings [{banned_cores}] (FORBIDDEN shapes: «{forbidden}»)")
        if "occasion" in _clean_reasons:
            bits.append("inventing a HOLIDAY/occasion — this slot has none; write a plain everyday moment with NO eid/ramadan/national-day/hajj")
        if "ungrounded" in _clean_reasons:
            bits.append("an invented name — use only the real brand/products in Arabic")
        if "learned" in _clean_reasons:
            bits.append(f"a phrase the founder explicitly rejected before — avoid these exact phrasings: {learned_bans}")
        if "organ" in _clean_reasons:
            bits.append("breaking a confirmed client rule — " + ("؛ ".join(_organ_bits) if _organ_bits else "no named person / no family voice line / no cross-brand frame"))
        extra = ("\n\nREGENERATE — your last attempt was REJECTED for: " + "؛ ".join(bits) +
                 ". Find a COMPLETELY different angle on the same scene.")
        print(f"  ↻ regen {tries}: rejected ({'; '.join(bits)[:80]}) — feeding back", file=sys.stderr)
        cleaned = _clean(_gen(extra))
        kept, taste_killed = taste_guard(cleaned, c.get("kill_patterns", []))
        for o, hit in taste_killed:
            print(f"  ✂️ taste-kill [{hit}] (regen {tries}): {o[:50]}…", file=sys.stderr)
    cleaned = kept
    surv, dropped_reasons = filter_options({f"opt_{i}": o for i, o in enumerate(cleaned)})
    if surv:
        final = list(surv.values())[:3]
    else:
        # ALL options filter-killed (zoom-out catch June 13: the old fallback silently
        # re-admitted them — including CULTURAL hard kills like dua+brand). Hard kills
        # (cultural/dialect) may NEVER ship; soft style kills (worn/cliche) re-admit
        # least-bad, flagged loudly — eyes decide downstream.
        HARD = ("cultural:", "dialect:")
        soft_only = [o for i2, o in enumerate(cleaned)
                     if not any(r.startswith(HARD)
                                for r in dropped_reasons.get(f"opt_{i2}", []))]
        for i2, o in enumerate(cleaned):
            print(f"  ✂️ filter-kill {dropped_reasons.get(f'opt_{i2}', [])}: {o[:50]}…",
                  file=sys.stderr)
        final = soft_only[:3]
        if final:
            print(f"  ⚠️ ALL options filter-killed — {len(final)} soft-killed re-admitted "
                  "FLAGGED (least-bad; hard cultural/dialect kills stayed dead)", file=sys.stderr)
        else:
            print("  🛑 every option carried a HARD kill — slot renders with zero captions, "
                  "regen needed", file=sys.stderr)
    # his diversity ruling: a fresh emotional core leads when recent slots repeat one
    final = diversity_prefer(final, c.get("recent_cores", []))
    # CTA-density rule (June 11, RABIE-ruled): a feed that sells in every line reads like
    # a flyer. Of the 3 options, at most ONE keeps an order-CTA tail — the rest stand on
    # the scene. Deterministic: keep the first CTA, strip CTA sentences from the others.
    CTA = re.compile(r"[^.!؟\n]*\b(اطلب(?:وا|ها|وه)?|حمّ?ل التطبيق|اطلبيها?)\b[^.!؟\n]*[.!؟]?")
    # bilingual filler ban — CANONICAL copy lives in truth_guards (B038, the
    # one-module law: the renderer's frozen FILLER would drift exactly like its
    # frozen EVENT_CLAIM did this morning)
    from truth_guards import FILLER
    cleaned2 = [o for o in final if not FILLER.search(o)]
    if not cleaned2 and final:
        print(f"  ⚠️ all options carry FILLER — least-bad re-admitted FLAGGED: "
              f"{final[0][:50]}…", file=sys.stderr)
        cleaned2 = final[:1]
    final = cleaned2
    kept_cta = False
    out = []
    import re as _re
    dedupe = lambda s: _re.sub(r"\b(\S+)\s+\1\b", r"\1", s)  # «جاهز جاهز» collision
    for o in final:
        if CTA.search(o):
            if kept_cta:
                stripped = CTA.sub("", o).strip(" -–—·,،\n")
                o = stripped if len(stripped) > 15 else o  # never strip a caption to nothing
            kept_cta = True
        out.append(dedupe(o))
    return out


def _visual_ref(c: dict) -> str:
    """Grounding clause from the brand's visual_dna (June 18): real palette/background/color-field so
    the shoot-card matches how the brand actually looks. Colors/setting only — no people/face language,
    so it never conflicts with the HARD CLIENT RULES or the occasion gate. Empty if no visual_dna."""
    vd = (c.get("visual_dna") or {}).get("brand", {})
    def _v(*path):
        x = vd
        for k in path:
            x = (x or {}).get(k, {}) if isinstance(x, dict) else {}
        return x.get("value") if isinstance(x, dict) else None
    bits = [f"dominant brand color {_v('palette','primary')}" if _v('palette','primary') else "",
            f"typical background {_v('palette','background_tone')}" if _v('palette','background_tone') else "",
            f"color field {_v('color_field_palette')}" if _v('color_field_palette') else ""]
    bits = [b for b in bits if b]
    return ("REAL BRAND LOOK (match it in the framing/props/setting — do NOT name colors in any caption): "
            + "; ".join(bits) + ". ") if bits else ""


def shot_card(c: dict, angle: dict, ground: bool = False) -> list[str]:
    # the VISUAL door respects the confirmed organs (RABIE 2026-06-14: shot-cards directed visible
    # faces/family/children on brands whose cultural_overrides forbid them, and the gate caught it
    # only after). Source-fix: never DIRECT what the client forbids.
    import client_rules as _cr
    _ov = _cr._overrides(c["handle"])
    rules = ["NO visible human faces, expressions, smiles, or eye-contact directions — hands/food/objects/place only"
             if _ov.get("face_visibility") == "never" else "",
             "NO family members or children in frame"
             if _ov.get("family_member_visibility") == "never" else "",
             "show DELIVERY — packaging/box/the food arriving; never a restaurant/dine-in/cart/branch setting"
             if _cr._is_cloud_kitchen(c["handle"]) else ""]
    rules = " · ".join(r for r in rules if r)
    sysp = ("You write PHONE shoot-cards for Saudi SME owners — 3 numbered instructions in simple Saudi Arabic, "
            "each doable at home with a phone in 2 minutes. Conservative cultural defaults (hands/food/place safe). "
            + (f"HARD CLIENT RULES (never break): {rules}. " if rules else "no faces unless the scene demands. ")
            + (_visual_ref(c) if ground else "")
            + 'Return JSON: {"shots": ["...", "...", "..."]}')
    out = gpt([{"role": "system", "content": sysp},
               {"role": "user", "content": f"البراند: {c['brand_ar']}\nالمشهد: {angle['scene_ar']}"}], temp=0.5, max_tok=300)
    return [re.sub(r"^\s*\d+[\.\)]\s*", "", s).strip() for s in json.loads(out).get("shots", [])[:3]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--brain", default=None, choices=list(BRAIN_FILES) + ["auto"],
                    help="route the angle through a full CD-brain methodology (auto = slot-type routing)")
    ap.add_argument("--suffix", default="", help="output filename suffix (e.g. __v2_brain)")
    ap.add_argument("--ground", action="store_true", help="ground the shoot-card in the brand's real visual_dna (June 18)")
    ap.add_argument("--panel", action="store_true",
                    help="run the 5-CD-brain PANEL on DIFFERENT models (GPT/Gemini/Groq via consult.py); "
                         "the lead brain's angle leads + rivals seed the caption pen (W1/W3, June 23)")
    a = ap.parse_args()
    gate = blackout_check()
    if not gate["publish_allowed"]:
        sys.exit(f"BLACKOUT — rendering parked: {gate['hard_block']['reason']}")
    # B002 (Growth Law tooth): push-energy slots need a declared capacity ceiling —
    # a viral offer could break a 2-woman kitchen. Block PUSH types, allow the rest.
    _goals = json.loads((BASE / "clients" / a.handle / "profile/goals.json").read_text())
    _slot_probe = None  # resolved after slot lookup below
    ymap = json.loads((BASE / "clients" / a.handle / "year_map.json").read_text())
    slot = next((s for mm in ymap["months"].values() for s in mm if s["date"] == a.date), None)
    if not slot:
        sys.exit(f"no slot {a.date} in {a.handle} year map")
    # B053b: the render path's route_decision() reads slot['sector'] to fire the sector
    # safety-lock (e.g. healthcare_wellness forbids paradox), but slot from the year map
    # carries no sector — only ymap['sector'] does. Inject it here so the lock that already
    # guards the ANGLE path (make_angle) also guards the RENDER path. Same source the rest
    # of this function already trusts (lines below pass ymap['sector'] to make_angle/chain_for).
    slot.setdefault("sector", ymap["sector"])
    # (wired below after client load — B181 needs both slot and client)
    # B072: every render that consults red_lines counts a TOUCH (5th-touch reconfirm law)
    _rlf = BASE / "clients" / a.handle / "profile/red_lines.json"
    _rl = json.loads(_rlf.read_text())
    if _rl.get("lines"):
        _rl["touches_since_confirm"] = _rl.get("touches_since_confirm", 0) + 1
        _rlf.write_text(json.dumps(_rl, ensure_ascii=False, indent=2))
    PUSH_TYPES = {"weekly_offer", "white_friday", "11_11_shopping", "singles_day_11_11"}
    if (slot.get("occasion") in PUSH_TYPES or slot.get("type") == "offer") and _goals.get("capacity_ceiling") is None:
        sys.exit(f"CAPACITY BLOCK (B002): push slot {slot.get('occasion') or slot.get('type')} needs a declared "
                  f"capacity_ceiling in goals.json — a viral push without capacity = broken kitchen. Ask the client.")
    c = load_client(a.handle)
    # B181: re-rank few-shot for THIS slot — occasion gold leads
    if c.get("gold_entries"):
        c["exemplars"] = rank_gold_exemplars(c["gold_entries"], slot.get("occasion"), c["exemplars"])
    if a.brain == "auto":
        _alt = int(a.date.replace("-", ""))
        _decision = route_decision(slot, alt=_alt)
        brain = _decision["primary"]
        try:  # B051: observe every routing call — best-effort, never break a render
            log_routing_decision({**_decision, "handle": a.handle, "date": a.date},
                                 run_id=f"{a.handle}:{a.date}")
        except Exception:
            pass
    else:
        brain = a.brain
    angle = make_angle(c, slot, ymap["sector"], brain=brain, panel=a.panel)
    captions = render_captions(c, slot, angle)
    # CONTENT-AWARE chain pick (June 21 fix): the chain now fits the SCENE (the angle's
    # scene + post_type + occasion), not just the formula's family order — so a family
    # dinner draws a lifestyle chain, a gym never draws a magazine cover. Falls back to the
    # legacy chain_for() floor inside pick_pro_chain if nothing scores. Rule #12: computed.
    # This is now the AD's FALLBACK floor (the mechanical pick); the Art-Director below makes
    # the DELIBERATE chain choice for photo slots.
    mechanical = pick_pro_chain(slot.get("formula", "CF_01"), ymap["sector"],
                                slot.get("occasion", "evergreen"),
                                scene_text=" ".join([angle.get("scene_ar", ""),
                                                     slot.get("angle_theme", "")]),
                                post_type=angle.get("post_type", ""))
    # ART-DIRECTOR (June 22 — the missing VISUAL mind, Rule #12): for a PHOTO slot the AD
    # DESIGNS the photograph FROM THE ORGANS (chosen chain + WHY + staging + modesty), and its
    # deliberate chain + composed scene REPLACE the bare scene_ar + mechanical pick downstream
    # (render_via_master reads visual.art_brief). The mechanical pick above stays as the FALLBACK
    # when the AD returns no chain on a culturally-clean scene. A culturally-REFUSED brief HOLDS
    # the slot — pro_chain=None so the image render REFUSES (Rule #8: never fall through to a
    # wrong render). Reels are untouched (is_photo False → no AD; the mechanical chain stands).
    # $0: the AD runs organ-derived (no LLM pen) here; the gpt-4o pen is a later gated step.
    import art_director as ad
    fmt = slot.get("format", "image")
    brief = None
    if ad.is_photo(fmt):
        try:
            brief = ad.art_direct(angle.get("scene_ar", ""), a.handle, fmt,
                                  occasion=slot.get("occasion", ""),
                                  formula_id=slot.get("formula", "CF_01"))
        except Exception as _e:
            print(f"  ⚠ art-director failed ({str(_e)[:60]}) — mechanical chain fallback", file=sys.stderr)
            brief = None
    chain_card, art_brief, hold_reason = resolve_visual(brief, mechanical)
    shots = shot_card(c, angle, ground=a.ground)
    # CAPTION-MODEL FINGERPRINT (I2): stamp which caption model produced this batch so a silent
    # caption-model swap is detectable (the taste-Elo is calibrated on captions; check_model_drift
    # watches this). The fallback pen (sonnet) is dark on credits, so the live pen is the primary.
    import model_registry as _mr
    visual = {"phone_shoot_card": shots, "pro_chain": chain_card}
    if art_brief is not None:                       # the AD's designed photo brief (Rule #6: render_via_master reads it)
        visual["art_brief"] = art_brief
    card = {"handle": a.handle, "date": a.date, "slot": slot, "brain": brain,
            "idea": angle, "captions": captions,
            "caption_model_fingerprint": _mr.fingerprint_caption()["model_fingerprint"],
            "visual": visual,
            "provenance": {"source": "client_profile_path", "rendered": __import__("datetime").date.today().isoformat(),
                            "confirmer": "pending", "stamp": "PROVISIONAL — pending Mohamed",
                            # freshness law (RABIE-ruled): deep-dormant truth is expired —
                            # these are voice-revival drafts, unpublishable until client confirms
                            "truth_status": ("EXPIRED — voice draft only, client must confirm today's products"
                                              if (c["state"].get("silent_days") or 0) > 90 else "within_ttl")}}
    out = BASE / "clients" / a.handle / "posts"
    out.mkdir(exist_ok=True)
    fn = out / f"{a.date}__{slot.get('occasion') or 'evergreen'}{a.suffix}.json"
    fn.write_text(json.dumps(card, ensure_ascii=False, indent=2))
    print(f"✓ {a.handle} {a.date} [{slot.get('occasion') or slot.get('angle_theme','')[:40]}]")
    if hold_reason:
        # Rule #8 — the Art-Director refused this VISUAL (a red-line scene). The card keeps its
        # caption + the refused brief (gate visible), but pro_chain is None so the image step
        # REFUSES (render_via_master never guesses a chain) — never a wrong render. Loud, not silent.
        print(f"  🛑 ART-DIRECTOR HOLD (Rule #8): photo brief refused — {hold_reason}. "
              f"pro_chain=None; the image render will REFUSE.", file=sys.stderr)
    elif art_brief is not None:
        _ac = art_brief.get("chain") or {}
        print(f"  🎨 art-director: «{_ac.get('name_en') or _ac.get('id')}» — {(_ac.get('reason') or '')[:90]}")
    # B048: surface the moonsighting recheck at render time too (the visual gate is the
    # enforcing consumer; this is the loud heads-up so it's not discovered only at publish).
    if slot.get("moonsighting_check"):
        print(f"  🌙 REQUIRES-HUMAN-VERIFY: «{slot.get('occasion')}» date {a.date} is moon-dependent "
              "— confirm the official sighting before publish (may shift ±1-2 days)", file=sys.stderr)
    print(f"  💡 {angle['scene_ar'][:110]}")
    for i, cap in enumerate(captions, 1):
        print(f"  ✍️ {i}. {cap[:110]}")


if __name__ == "__main__":
    main()
