#!/usr/bin/env python3
"""build_caption_patterns.py — Weiblocks §5.5 caption_pattern records (contract weiblocks-knowledge-spec-v1).

TWO honest layers (the audit-scoped plan; Layer C occasion_plays CUT — 84% n<=2):

  LAYER A — 11_who_to_learn_from/patterns/caption_structure/*.json (13 corpus-mined structural
    patterns). ONE record per (pattern x folded SHIPPED observed sector): fold f_and_b->F&B,
    retail/fashion->Retail (deduped), beauty->Beauty_Wellness; healthcare_wellness is HELD
    (Mohamed's locked sector decision) -> never emitted, recorded in extra.sectors_held.

  LAYER B — logs/arabic_copywriting_by_sector.json (REAL Apify Arabic corpus, 4,903 captions).
    ONE record per (opener formula x observed source sector), excluding the "other" residual
    bucket (not a pattern) and real_estate (HELD). fashion + retail_lifestyle both fold to
    Retail but ship as SEPARATE records (their observed counts are separately real; merging
    would manufacture a number) — extra.source_sector disambiguates.
    + 4 cross-sector records under sector_key="Other" (formulas confirmed in >=2 sectors —
    exactly the content the spec §6 Other fallback pool exists for).

HONESTY (Rules #9/#12/#16 + the DeepSeek consult on THIS implementation, C-jul1):
  - NO engagement claims anywhere in why_it_works: the source lift/high_engagement_rate/
    multiplier numbers key on a RETIRED signal-free label (see the log's own confound_warnings).
    why_it_works is descriptive PREVALENCE only. The original claims are kept VERBATIM in
    extra.retired_engagement_claims with do_not_use=true (nothing lost, nothing endorsed).
  - NO machine-written Arabic, ever. structure_ar = null + extra.translation_needed=true on
    EVERY record (no Arabic structural formula exists in any source; DeepSeek ruling: a verbatim
    example line in structure_ar would misrepresent the field to the partner parser).
    example_skeleton_ar = VERBATIM Arabic extracted from the source (Layer A: the longest Arabic
    span in structural_recipe; Layer B: the highest-frequency real top_opener line that the SAME
    deterministic classifier — imported, not copied — assigns to that formula), else null.
  - observed_count: per-record-true numbers ONLY (DeepSeek: a pattern-level count on a
    per-sector record is a lie by implication). Layer A: the account count ONLY when the
    pattern was observed in exactly one source sector; multi-sector patterns -> null +
    extra.observed_count_note (per-sector split was never counted). Layer B: the real
    per-sector formula count. Cross-sector: the SUM of real per-sector counts (arithmetic on
    real numbers; per-sector rows verbatim in extra).
  - dialect: null unless the source DECLARES one. formal_dignified declares "full Arabic
    sentences in formal register ... tashkeel" -> "Fusha (MSA)" (DeepSeek: unambiguous).
    Register mentions like "warm colloquial Najdi or semi-formal" are NOT single-dialect
    declarations -> null + verbatim extra.register_note.
  - occasion_key: null on every record (Layer C cut). DISPUTED BACK vs the consult's "assign
    occasion_key where clusters are strong": the classifier's heritage_occasion bucket is
    multi-occasion BY CONSTRUCTION (markers span ramadan+eid+national_day+founding_day) and no
    per-formula x occasion count exists in the source — a single key would fabricate an
    association. Sector occasion clusters ride in extra via the SHARED occasion_keys module.
  - length / emoji_guidance / hashtag_guidance: VERBATIM phrases extracted from the source
    (description "Length:" sentences, recipe sentences naming emoji/hashtag), never authored;
    absent -> null.
  - provenance.source = the TRUE repo-relative source path (+ the source's own pass label);
    confirmer passed through where the source has one; confidence=experimental everywhere
    (corpus-mined synthesis / deterministic classification — never human-verified).

Native Arabic raw (ensure_ascii=False). Empty over missing (null/[]). Deterministic: sorted
globs, stable sort keys, stamped date. Nothing dropped -> extra.
"""
import glob
import json
import re
import sys
from pathlib import Path

from occasion_keys import SHIPPED_KEYS, normalize_list  # the ONE shared occasion vocab

ROOT = Path(__file__).resolve().parents[2]
SRC_PATTERNS_DIR = ROOT / "11_who_to_learn_from" / "patterns" / "caption_structure"
SRC_COPY_FP = ROOT / "logs" / "arabic_copywriting_by_sector.json"
OUT = ROOT / "exports" / "weiblocks_v1"
DATE_ADDED = "2026-07-01"  # stamped, deterministic — never now()

# import the EXACT deterministic classifier that produced the formula table (single source
# of truth — never a re-typed copy that could drift). Module is main-guarded (import-safe).
sys.path.insert(0, str(ROOT / "scripts"))
from build_arabic_copywriting_by_sector import _opener_formula  # noqa: E402

# ---------------------------------------------------------------------------
# sector fold — the SHIPPED map (build_sectors.py SECTOR_MAP + visual builder),
# vocab {F&B, Retail, Beauty_Wellness, Other}. Healthcare/Real_Estate are HELD
# (Mohamed's locked decision, July 1) — never emitted as sector_key.
# ---------------------------------------------------------------------------
SECTOR_KEY = {
    "f_and_b": "F&B",
    "retail": "Retail", "retail_lifestyle": "Retail", "fashion": "Retail",
    "beauty": "Beauty_Wellness", "beauty_personal_care": "Beauty_Wellness",
}
HELD_SECTORS = {"healthcare_wellness", "real_estate"}
SECTOR_VOCAB = {"F&B", "Retail", "Beauty_Wellness", "Other"}
ID_SLUG = {"F&B": "fnb", "Retail": "retail", "Beauty_Wellness": "beauty_wellness"}

# ---------------------------------------------------------------------------
# Arabic span extraction — VERBATIM contiguous slices only (any slice of the
# source string is by construction verbatim; the assert re-checks substring).
# span = starts+ends on an Arabic char/punct, may contain spaces/digits/common
# punctuation; must contain >= 2 Arabic words.
# ---------------------------------------------------------------------------
ARABIC_CHAR = re.compile(r"[؀-ۿ]")
ARABIC_SPAN = re.compile(
    r"[؀-ۿ](?:[؀-ۿ0-9\s.,،؛؟!…'’\"\-—:()«»|/]*[؀-ۿ؟!…])?"
)
BANNED_IN_WHY = ("lift", "engagement", "multiplier")  # + \d+x checked by regex in the assert


def arabic_spans(text, min_words=2):
    """All verbatim Arabic spans in text with >= min_words Arabic words, text order."""
    out = []
    for m in ARABIC_SPAN.finditer(text or ""):
        s = m.group().strip()
        if len([w for w in s.split() if ARABIC_CHAR.search(w)]) >= min_words:
            out.append(s)
    return out


def longest_span(spans):
    """Longest span; first-occurrence tie-break (list is in text order)."""
    return max(spans, key=len) if spans else None


def sentence_with(text, keyword):
    """First sentence of text containing keyword (verbatim, case-insensitive), else None."""
    for sent in re.split(r"(?<=[.!?])\s+", text or ""):
        if keyword in sent.lower():
            s = sent.strip()
            return s if s else None
    return None


LEN_PHRASE = r"(?:one|\d+(?:-\d+)?)\s+(?:sentences?|lines?|words?)(?:\s*\(\d+(?:-\d+)?\s*words\))?"


def extract_length(description, recipe):
    """VERBATIM length phrase, tried in order: (1) description ('... 3-6 sentences.'),
    (2) explicit 'Length: ...' marker in the recipe, (3) a count phrase in the recipe's
    own 'Caption: ...' opening sentence (e.g. 'Caption: one sentence (8-20 words)') —
    the sentence that describes the caption itself, so bracketed component lengths like
    '[Setting the scene in 1 sentence]' can never be picked up. Never invented."""
    m = re.search(r"\b" + LEN_PHRASE, description or "")
    if m:
        return m.group()
    m = re.search(r"Length:\s*([^.]+)", recipe or "")
    if m:
        return m.group(1).strip()
    m = re.match(r"Caption[^.\[]*?\b(" + LEN_PHRASE + r")", recipe or "")
    if m:
        return m.group(1)
    return None


def base_provenance(source_path, confidence, observed_count, scope, confirmer=None):
    p = {
        "source": source_path,
        "confidence": confidence,
        "observed_count": observed_count,
        "date_added": DATE_ADDED,
        "scope": scope,
    }
    if confirmer:
        p["confirmer"] = confirmer
    return p


# ---------------------------------------------------------------------------
# LAYER A — structural patterns -> one record per (pattern x shipped sector)
# ---------------------------------------------------------------------------
def build_layer_a():
    records = []
    for fp in sorted(glob.glob(str(SRC_PATTERNS_DIR / "*.json"))):
        src = json.load(open(fp, encoding="utf-8"))
        rel = str(Path(fp).relative_to(ROOT))
        slug = src["pattern_slug"]
        recipe = src.get("structural_recipe") or ""
        desc = src.get("description") or ""

        raw_sectors = src.get("observed_in_sectors") or []
        held = sorted(set(raw_sectors) & HELD_SECTORS)
        shipped, seen = [], set()
        for s in raw_sectors:  # source order, fold, dedupe (fashion+retail -> one Retail)
            k = SECTOR_KEY.get(s)
            if k and k not in seen:
                seen.add(k)
                shipped.append(k)

        spans = arabic_spans(recipe)
        example_ar = longest_span(spans)
        n_accounts = src.get("observed_in_account_count")
        n_src_sectors = len(raw_sectors)
        single_sector = n_src_sectors == 1

        # dialect: ONLY an unambiguous source declaration maps (formal register -> Fusha)
        dialect, dialect_note = None, None
        if slug == "formal_dignified":
            dialect = "Fusha (MSA)"
            dialect_note = ("declared by the source recipe: 'full Arabic sentences in formal "
                            "register ... tashkeel if appropriate' — formal register = Fusha (MSA)")
        register_note = sentence_with(recipe, "register")
        if dialect is None and register_note:
            # DeepSeek verify-pass flag: a register mention inside structure_en next to
            # dialect=null reads as a contradiction. His fixes (set Najdi / strip the
            # sentence) both violate honesty invariants — the register is DISJUNCTIVE
            # ("Najdi OR semi-formal": not a single-dialect declaration) and structure_en
            # is verbatim-preserved. Third path: keep both, make the null self-explaining.
            dialect_note = (f"structure_en mentions a register ({register_note!r}) but it is "
                            f"disjunctive/ambiguous, not a single-dialect declaration -> "
                            f"dialect stays null (= all dialects per spec §5.5)")

        why = (f"Used by {n_accounts} account(s) across {n_src_sectors} observed sector(s) "
               f"in the OGZ Saudi Instagram corpus (corpus_synthesis_474_obs). "
               f"Descriptive prevalence only — the source's per-pattern performance numbers "
               f"were retired (sector-baseline confound).")

        for sector_key in shipped:
            rec = {
                "id": f"cap_{slug}__{ID_SLUG[sector_key]}",
                "entity": "caption_pattern",
                "sector_key": sector_key,
                "occasion_key": None,   # Layer C cut — occasion clusters live in extra only
                "dialect": dialect,
                "pattern_name": slug,
                "structure_ar": None,   # no Arabic structural formula exists in the source
                "structure_en": recipe, # the source's own structural recipe, verbatim
                "why_it_works": why,
                "length": extract_length(desc, recipe),
                "emoji_guidance": sentence_with(recipe, "emoji"),
                "hashtag_guidance": sentence_with(recipe, "hashtag"),
                "example_skeleton_ar": example_ar,  # VERBATIM Arabic from the recipe, else null
                "caveats": list(src.get("transplantation_caveats") or []),
                "provenance": base_provenance(
                    source_path=f"{rel} — corpus_synthesis_474_obs, corpus_mining_pass May 2026",
                    confidence="experimental",
                    observed_count=n_accounts if single_sector else None,
                    scope=f"sector:{sector_key}",
                    confirmer=(src.get("provenance") or {}).get("confirmer"),
                ),
                "extra": {
                    "source_path": rel,
                    "source_label": Path(fp).name,
                    "pattern_ulid": src.get("pattern_ulid"),
                    "source_pattern_name": src.get("pattern_name"),
                    "description": desc,
                    "observed_in_sectors_raw": raw_sectors,
                    "sectors_shipped": shipped,
                    "sectors_held": held,  # healthcare_wellness held per Mohamed's decision
                    "observed_count_note": (
                        None if single_sector else
                        f"pattern-level account count = {n_accounts} across {n_src_sectors} "
                        f"sectors; a per-sector split was never counted -> observed_count null "
                        f"on this per-sector record (no implied per-sector number)"),
                    "translation_needed": True,  # structure_ar has no real-source Arabic
                    "missing_ar_fields": (["structure_ar"] if example_ar
                                          else ["structure_ar", "example_skeleton_ar"]),
                    "example_skeleton_ar_note": (
                        "verbatim example line(s) extracted from structural_recipe — an example, "
                        "not a fill-in skeleton" if example_ar else None),
                    "arabic_snippets_all": spans,
                    "register_note": register_note,
                    "dialect_note": dialect_note,
                    "retired_engagement_claims": {
                        "do_not_use": True,
                        "reason": ("keyed on a RETIRED signal-free engagement label "
                                   "(sector-baseline confound — see "
                                   "logs/arabic_copywriting_by_sector.json confound_warnings)"),
                        "why_it_works_original": src.get("why_it_works"),
                        "avg_engagement_multiplier_observed": src.get(
                            "avg_engagement_multiplier_observed"),
                    },
                    "cultural_constraints": src.get("cultural_constraints"),
                    "applicable_chains": src.get("applicable_chains"),
                    "status": src.get("status"),
                    "obs_usage_count": src.get("obs_usage_count"),
                    "source_provenance": src.get("provenance"),
                },
            }
            records.append(rec)
    records.sort(key=lambda r: (r["pattern_name"], r["sector_key"]))
    return records


# ---------------------------------------------------------------------------
# LAYER B — opener formulas x observed sectors (+ cross-sector under Other)
# ---------------------------------------------------------------------------
# the classifier's own marker lists, quoted INTO structure_en as the definition.
# NOTE: kept as documentation strings; classification itself calls the imported
# _opener_formula so definition and behavior cannot drift apart.
FORMULA_DEF = {
    "question": ("caption head (first 120 chars) contains '?' or '؟', or starts with one of: "
                 "هل / ما / ماذا / من / أين / كيف / متى / لماذا"),
    "community_invite": ("caption head contains one of: حياكم / أهلاً / أهلا / تعالوا / تفضلوا / "
                         "عندنا / جربوا / اكتشف / شاركونا"),
    "sensory_emotive": ("caption head contains one of: طعم / رائحة / لذيذ / مميز / أحلى / ألذ / "
                        "الأجود / جمال / روعة / ذكريات"),
    "announcement": ("caption head contains one of: جديد / يتوفر / أطلقنا / إطلاق / الآن / "
                     "توفر / حصري / متاح"),
    "heritage_occasion": ("caption head contains one of: رمضان / العيد / اليوم الوطني / التأسيس / "
                          "الوطن / المملكة / تراث / أصيل"),
}
CLASSIFIER_NOTE = ("Deterministic marker classifier _opener_formula() in "
                   "scripts/build_arabic_copywriting_by_sector.py (checked in priority order: "
                   "question, community_invite, sensory_emotive, announcement, heritage_occasion)")
RETIRED_METRICS_CAVEAT = (
    "The source analysis's engagement metrics (high_engagement_rate / lift) were RETIRED as a "
    "quality signal (sector-baseline confound — see extra.confound_warnings); counts here are "
    "prevalence only, not proof the opener performs.")
CLASSIFIER_CAVEAT = (
    "Formula assignment is marker-based on the caption head — prevalence of a surface form, "
    "not a validated copywriting taxonomy.")


def formula_example(sector_analysis, formula):
    """Highest-frequency VERBATIM top_opener line the SAME classifier assigns to `formula`.
    Frequency = high_eng + low_eng (real corpus occurrence count of that opener).
    Deterministic tie-break: frequency desc, then opener string asc. None if no match.
    (top_openers are punctuation-stripped 5-word heads, so 'question' can only match via
    its Arabic interrogative startswith markers — an honest under-match, never a wrong one.)"""
    cands = []
    for o in sector_analysis.get("top_openers") or []:
        if _opener_formula(o["opener"]) == formula:
            freq = (o.get("high_eng") or 0) + (o.get("low_eng") or 0)
            cands.append((-freq, o["opener"], o))
    if not cands:
        return None, None
    cands.sort()
    _, opener, row = cands[0]
    return opener, row


def occasion_clusters_extra(sector_analysis):
    """sector occasion_keyword_clusters -> extra block via the SHARED occasion module.
    Cluster names normalize through occasion_keys (eid -> eid_fitr per shared ALIASES);
    unresolved names stay honestly unresolved. Keywords ride verbatim with real counts."""
    clusters = sector_analysis.get("occasion_keyword_clusters") or {}
    resolved, unresolved = {}, {}
    for name, kws in sorted(clusters.items()):
        keys, un = normalize_list([name])
        if keys:
            resolved[keys[0]] = kws
        else:
            unresolved[un[0] if un else name] = kws
    return {"resolved": resolved, "unresolved": unresolved,
            "note": "sector-level caption keyword clusters (real counts) — context only; "
                    "NOT a per-formula occasion association (occasion_key stays null)"}


def build_layer_b():
    data = json.load(open(SRC_COPY_FP, encoding="utf-8"))
    rel = str(SRC_COPY_FP.relative_to(ROOT))
    per_sector = data["per_sector_analysis"]
    confounds = data.get("confound_warnings") or []

    records = []
    for source_sector in sorted(per_sector):
        if source_sector in HELD_SECTORS:  # real_estate: HELD — never shipped
            continue
        sa = per_sector[source_sector]
        sector_key = SECTOR_KEY[source_sector]
        n_obs = sa.get("arabic_caption_obs")
        clusters = occasion_clusters_extra(sa)
        for row in sa.get("opener_formula_table") or []:
            formula = row["formula"]
            if formula == "other":  # residual bucket, not a pattern
                continue
            example, example_row = formula_example(sa, formula)
            rec = {
                "id": f"cap_opener_{formula}__{source_sector}",
                "entity": "caption_pattern",
                "sector_key": sector_key,
                "occasion_key": None,
                "dialect": None,  # the corpus analysis never declares a dialect
                "pattern_name": f"opener_{formula}",
                "structure_ar": None,
                "structure_en": (f"Opener formula '{formula}': {FORMULA_DEF[formula]}. "
                                 f"[{CLASSIFIER_NOTE}]"),
                "why_it_works": (f"Opener formula observed on {row['count']} of {n_obs} analyzed "
                                 f"Arabic captions in the {source_sector} corpus "
                                 f"(deterministic marker classifier; descriptive prevalence only)."),
                "length": None,
                "emoji_guidance": None,
                "hashtag_guidance": None,
                "example_skeleton_ar": example,  # VERBATIM real opener line, else null
                "caveats": [RETIRED_METRICS_CAVEAT, CLASSIFIER_CAVEAT],
                "provenance": base_provenance(
                    source_path=f"{rel} — deterministic Arabic corpus analysis, "
                                f"generated {data.get('generated_at')}",
                    confidence="experimental",
                    observed_count=row["count"],  # real per-sector formula count
                    scope=f"sector:{sector_key}",
                ),
                "extra": {
                    "source_path": rel,
                    "source_label": "arabic_copywriting_by_sector.json",
                    "source_sector": source_sector,  # fashion vs retail_lifestyle stay distinct
                    "sector_arabic_caption_obs": n_obs,
                    "translation_needed": True,
                    "missing_ar_fields": (["structure_ar"] if example
                                          else ["structure_ar", "example_skeleton_ar"]),
                    "example_skeleton_ar_note": (
                        "verbatim highest-frequency real opener line (first-5-Arabic-words head) "
                        "that the same classifier assigns to this formula" if example else
                        "no top_opener line in this sector classifies to this formula -> null "
                        "(never hand-picked)"),
                    "example_opener_row": example_row,  # the real source row, verbatim
                    "retired_engagement_claims": {
                        "do_not_use": True,
                        "reason": "sector-baseline confound (see confound_warnings)",
                        "opener_formula_row": row,  # verbatim incl. retired rate/lift numbers
                    },
                    "sector_occasion_clusters": clusters,
                    "confound_warnings": confounds,
                    "methodology_note": data.get("methodology_note"),
                },
            }
            records.append(rec)
    records.sort(key=lambda r: (r["pattern_name"], r["extra"]["source_sector"]))

    # --- cross-sector formulas -> sector_key="Other" (the §6 fallback pool) ---
    cross = []
    for sig in data.get("cross_sector_formula_signals") or []:
        formula = sig["formula"]
        total = sum(r["count"] for r in sig["per_sector"])  # arithmetic on real counts
        # deterministic example: best match across confirmed SHIPPED sectors, global
        # frequency desc then opener asc then sector asc
        best = None
        for sec in sorted(sig["confirmed_sectors"]):
            if sec in HELD_SECTORS or sec not in per_sector:
                continue
            ex, ex_row = formula_example(per_sector[sec], formula)
            if ex:
                freq = (ex_row.get("high_eng") or 0) + (ex_row.get("low_eng") or 0)
                key = (-freq, ex, sec)
                if best is None or key < best[0]:
                    best = (key, ex, ex_row, sec)
        rec = {
            "id": f"cap_opener_{formula}__cross_sector",
            "entity": "caption_pattern",
            "sector_key": "Other",  # cross-sector = the neutral fallback home (§6)
            "occasion_key": None,
            "dialect": None,
            "pattern_name": f"opener_{formula}",
            "structure_ar": None,
            "structure_en": (f"Opener formula '{formula}': {FORMULA_DEF[formula]}. "
                             f"[{CLASSIFIER_NOTE}]"),
            "why_it_works": (f"Opener formula observed across {len(sig['confirmed_sectors'])} "
                             f"sectors ({total} classified captions total) — one of the few "
                             f"opener shapes that recurs beyond a single sector; shipped under "
                             f"Other as cross-sector fallback knowledge."),
            "length": None,
            "emoji_guidance": None,
            "hashtag_guidance": None,
            "example_skeleton_ar": best[1] if best else None,
            "caveats": [RETIRED_METRICS_CAVEAT, CLASSIFIER_CAVEAT,
                        "Cross-sector recurrence is prevalence across sector corpora, not a "
                        "universality guarantee."],
            "provenance": base_provenance(
                source_path=f"{rel} — cross_sector_formula_signals, deterministic Arabic corpus "
                            f"analysis, generated {data.get('generated_at')}",
                confidence="experimental",
                observed_count=total,
                scope="universal",
            ),
            "extra": {
                "source_path": rel,
                "source_label": "arabic_copywriting_by_sector.json",
                "source_sector": "cross_sector",
                "cross_sector": True,
                "confirmed_sectors_raw": sig["confirmed_sectors"],
                "per_sector_counts": [{"sector": r["sector"], "count": r["count"]}
                                      for r in sig["per_sector"]],
                "observed_count_note": ("observed_count = sum of the real per-sector formula "
                                        "counts (includes held sectors' observations — the "
                                        "captions are real even where the sector record is held)"),
                "translation_needed": True,
                "missing_ar_fields": (["structure_ar"] if best
                                      else ["structure_ar", "example_skeleton_ar"]),
                "example_skeleton_ar_note": (
                    f"verbatim real opener from the {best[3]} corpus (highest-frequency "
                    f"classifier match across confirmed shipped sectors)" if best else
                    "no top_opener across confirmed shipped sectors classifies to this formula"),
                "example_opener_row": best[2] if best else None,
                "retired_engagement_claims": {
                    "do_not_use": True,
                    "reason": "sector-baseline confound (see confound_warnings)",
                    "cross_sector_signal_row": sig,  # verbatim incl. retired lift numbers
                },
                "confound_warnings": confounds,
                "methodology_note": data.get("methodology_note"),
            },
        }
        cross.append(rec)
    cross.sort(key=lambda r: r["pattern_name"])
    return records + cross


def build():
    layer_a = build_layer_a()
    layer_b = build_layer_b()
    records = layer_a + layer_b

    OUT.mkdir(parents=True, exist_ok=True)
    outfp = OUT / "caption_patterns.json"
    with open(outfp, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    # --- audit to stdout (numbers, not feelings) ---
    from collections import Counter
    n_a, n_b = len(layer_a), len(layer_b)
    n_cross = sum(1 for r in layer_b if r["extra"].get("cross_sector"))
    n_ex = sum(1 for r in records if r["example_skeleton_ar"])
    n_obsc = sum(1 for r in records if r["provenance"]["observed_count"] is not None)
    n_dialect = sum(1 for r in records if r["dialect"])
    print(f"wrote {len(records)} caption_pattern records -> {outfp}")
    print(f"  layer A (structural x sector): {n_a} | layer B (opener x sector): {n_b - n_cross} "
          f"| cross-sector Other: {n_cross}")
    print(f"  example_skeleton_ar present: {n_ex}/{len(records)} (verbatim source Arabic only)")
    print(f"  structure_ar: 0/{len(records)} (no source Arabic structural formula exists — "
          f"all null + translation_needed)")
    print(f"  observed_count non-null: {n_obsc}/{len(records)} | dialect declared: {n_dialect}")
    print(f"  sector dist: {dict(Counter(r['sector_key'] for r in records))}")
    print(f"  occasion_key: all null (Layer C cut): "
          f"{all(r['occasion_key'] is None for r in records)}")
    return records


if __name__ == "__main__":
    build()
