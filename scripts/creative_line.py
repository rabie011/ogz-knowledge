#!/usr/bin/env python3
"""THE CREATIVE LINE (June 11) — idea first, voice second, critic always.
Born from the founder's 13 ratings: the feed-cloner writes correct-but-EMPTY captions
("very normal", "generic", "no creative"). A good post = IDEA × VOICE × CULTURE; the
idea organ existed (/api/angles) but never fed the captions. This is the kitchen:

  TRUTH PACK ─→ ANGLES (GPT = idea mind) ─→ ANGLE PICK (Sonnet critic + taste law)
      ─→ RENDER the chosen angle (Sonnet + GPT in parallel = two pens, voice few-shot)
      ─→ CRITIC (cross-model judge vs data/founder_taste.json + filter + scorer_v2)
      ─→ best caption · low scores regenerate ONCE with the critic's feedback

Usage: python3 scripts/creative_line.py --brand albaik --occasion national_day [--json]
"""
import argparse, json, os, subprocess, sys, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from caption_filter import filter_options, check
from scorer_v2 import score_v2
from v5_prompt import load_dna
from humain_collector import OCCASION_AR
from build_truth_pack import SCHEMA_VERSION as TRUTH_PACK_SCHEMA_VERSION

BASE = Path(__file__).parent.parent
TASTE = json.loads((BASE / "data/founder_taste.json").read_text())


def _env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit(f"no {k}")


def gpt(messages, temp=0.8, max_tokens=900, force_json=False):
    body = {"model": "gpt-4o", "temperature": temp, "max_tokens": max_tokens, "messages": messages}
    if force_json:
        body["response_format"] = {"type": "json_object"}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {_env('OPENAI_API_KEY')}",
                                         "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=90).read())["choices"][0]["message"]["content"]


def claude(system, messages, temp=0.8, max_tokens=900):
    body = {"model": "claude-sonnet-4-6", "max_tokens": max_tokens, "temperature": temp,
            "system": system, "messages": messages}
    rq = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                data=json.dumps(body).encode(),
                                headers={"x-api-key": _env("ANTHROPIC_API_KEY"),
                                         "anthropic-version": "2023-06-01",
                                         "content-type": "application/json"})
    r = json.loads(urllib.request.urlopen(rq, timeout=90).read())
    return r["content"][0]["text"]


def _angle_card_stale(f):
    """An angle card is STALE if it predates the B041 routed-brain schema (B065).
    Fresh cards (build_angle_cards.py from June 19 on) assign every angle a non-null
    'brain' — the routed CD-brain key, enforced at build_angle_cards.py:177. Pre-B041
    cards (June 11) carry brain=None with the old one-line lens labels (firaasa,
    paradox_hunter, …). ensure_assets only rebuilt on MISSING, so a stale card was read
    as-is and its dead ideation lenses fed straight to the render pen — a silent
    staleness consumption (Rule #6 consumer law). Detect it so the consumer auto-heals."""
    try:
        card = json.loads(f.read_text())
    except Exception:
        return True   # unreadable / corrupt → rebuild
    angles = card.get("angles") or []
    if not angles:
        return True
    return any(not a.get("brain") for a in angles)


def _truth_pack_stale(f):
    """A truth pack is STALE if its schema signature predates the current pack shape (B270).
    Fresh packs (build_truth_pack.py) stamp '_schema' = SCHEMA_VERSION; the constant is bumped
    whenever build() changes the pack shape. ensure_assets only rebuilt on MISSING, so a pack
    written before a shape change was read as-is and its pre-schema-change brief fed straight to
    the render pen — a silent staleness consumption (Rule #6 consumer law; the truth-pack mirror
    of _angle_card_stale / B065). All 20 pre-B270 packs carry no '_schema' and auto-heal lazily
    on their next real render — no speculative spend (money discipline)."""
    try:
        pack = json.loads(f.read_text())
    except Exception:
        return True   # unreadable / corrupt → rebuild
    return pack.get("_schema") != TRUTH_PACK_SCHEMA_VERSION


def ensure_assets(brand_en, occasion):
    for script in ("build_truth_pack.py", "build_angle_cards.py"):
        is_angle = "angle" in script
        f = BASE / "data" / ("truth_packs" if "truth" in script else "angle_cards") / f"{brand_en}__{occasion}.json"
        stale = _angle_card_stale(f) if is_angle else _truth_pack_stale(f)
        if not f.exists() or stale:
            r = subprocess.run([sys.executable, str(BASE / "scripts" / script),
                                "--brand", brand_en, "--occasion", occasion],
                               capture_output=True, text=True, cwd=BASE)
            if r.returncode != 0:
                # Rule #8 — refuse, don't warn: never feed stale/absent ideation to the render pen.
                raise RuntimeError(f"{script}: {(r.stderr or r.stdout)[-150:]}")
    pack = json.loads((BASE / "data/truth_packs" / f"{brand_en}__{occasion}.json").read_text())
    cards = json.loads((BASE / "data/angle_cards" / f"{brand_en}__{occasion}.json").read_text())
    return pack, cards


OFFER_OCCASIONS = {"weekly_offer", "white_friday", "new_product", "summer_campaign", "daily_post"}


def gold_lead_voice(brand_en, occasion, dna, base=BASE, n=5):
    """Voice-reference few-shot for the render pen, GOLD FIRST (B040, Rule #6 consumer law).

    The founder's rating>=4 captions (logs/brand_gold/{brand}_gold.json) are his strongest
    taste signal — they must LEAD the voice reference, outranking engagement-ranked exemplars.
    Mirrors v5_prompt.py's gold-first + occasion-rotation so the angle-render path and the
    main-API path feed the pens the SAME founder-approved voice. Returns a list of caption
    strings, gold lines first, dna exemplars filling to n, de-duplicated.
    """
    gold_f = base / "logs" / "brand_gold" / f"{brand_en}_gold.json"
    all_gold = []
    if gold_f.exists():
        all_gold = [g["caption"] for g in json.loads(gold_f.read_text())
                    if g.get("rating", 0) >= 4 and g.get("caption")]
    # occasion-rotate the same way v5_prompt does so repeated requests don't fed-loop the
    # same 3 lines (the client-path top-6 staleness bug, June 12 armor port)
    if len(all_gold) > 3:
        h = sum(ord(c) for c in str(occasion or ""))
        gold = [all_gold[(h + j) % len(all_gold)] for j in range(3)]
    else:
        gold = all_gold
    lines = list(gold)
    for e in dna.get("exemplars", []):
        cap = e.get("caption", "")
        if cap and cap not in lines:
            lines.append(cap)
        if len(lines) >= n:
            break
    return lines[:n]


def pick_angle(cards, occasion):
    """Sonnet as CD: pick the least-generic, most concrete angle (taste law embedded)."""
    kills = "; ".join(k["name"] + ": " + k["why"][:90] for k in TASTE["kills"])
    angles = cards.get("angles", [])
    if not angles:
        return None
    listing = "\n".join(f"{a['id']}. [{a.get('formula')}·{a.get('lens')}] {a.get('insight_ar','')} → {a.get('approach_ar','')}" for a in angles)
    occ_rule = ("This is an OFFER occasion — clarity beats cleverness; pick the angle that makes the offer concrete."
                if occasion in OFFER_OCCASIONS else
                "This is an EMOTIONAL occasion — pick the angle with the most CONCRETE human scene; reject anything that smells like a formula.")
    sys_prompt = (f"You are the creative director. The founder's taste law — KILLS: {kills}. "
                  f"REWARDS: concrete warm scenes, real ideas nameable in one line. {occ_rule} "
                  "Reply with ONLY the number of the best angle.")
    # B064: pick_angle was the ONE unguarded LLM call in the creative_line path — it called
    # claude() with no fallback, so a dry Anthropic key raised here and killed the whole
    # producer at angle-selection, BEFORE the (already-guarded) render() pen could run. With
    # OpenAI funded and Anthropic dry, the producer couldn't run end-to-end at all. Cascade:
    # Claude pen → funded GPT pen → deterministic first angle. The pipeline now runs under
    # ANY key state (zero-LLM-first), never raising on a dry key.
    out = None
    try:
        out = claude(sys_prompt, [{"role": "user", "content": listing}], temp=0.2, max_tokens=10)
    except Exception:
        try:
            out = gpt([{"role": "system", "content": sys_prompt},
                       {"role": "user", "content": listing}], temp=0.2, max_tokens=10)
        except Exception:
            return angles[0]   # both pens dry → deterministic CD-pick (first/highest card)
    try:
        n = int("".join(c for c in out if c.isdigit())[:1] or "1")
        return next((a for a in angles if a.get("id") == n), angles[0])
    except Exception:
        return angles[0]


def render(brand_en, brand_ar, occasion, angle, pack):
    """Two pens render the SAME chosen angle in the brand's voice."""
    dna = load_dna(brand_en) or {}
    openers = "، ".join(dna.get("proven_openers_ar", [])[:5])
    # GOLD FIRST (B040): founder rating>=4 captions lead the voice reference, then exemplars
    exemplars = "\n".join(f"- {c[:160]}" for c in gold_lead_voice(brand_en, occasion, dna))
    dialect = dna.get("dialect", "saudi")
    # bilingual ONLY when the feed is genuinely English-led (majority of exemplars
    # are >50% Latin) — not when one caption happens to have a hashtag. (mcdonalds
    # has Arabic hashtags but Arabic body → stays Arabic.) B043: the shared boundary.
    from truth_guards import is_en_led
    bilingual = is_en_led(exemplars=dna.get("exemplars", []))
    occ_ar = OCCASION_AR.get(occasion, occasion)
    lang_rule = ("This brand lives in BOTH languages: write a designed bilingual post — one short English hook line + one Arabic line that carries the idea (not a translation). Both halves must stand alone."
                 if bilingual else
                 f"Pure {dialect} Saudi Arabic. If a Saudi reads it, it must sound like home — وش/إيش/الحين energy where natural.")
    offer_rule = ("State the offer with full clarity: what, how much, until when, where." if occasion in OFFER_OCCASIONS
                  else "NO discount/urgency language — this occasion is about the moment, not the deal.")
    task = f"""THE BRAND'S REAL FEED (voice reference):
{exemplars}
Proven openers: {openers}

THE CHOSEN IDEA (render THIS — nothing else):
Insight: {angle.get('insight_ar','')}
Approach: {angle.get('approach_ar','')}
Post type: {angle.get('post_type','moment')}

Write 3 caption options for {brand_ar} for {occ_ar} that LAND this exact idea in this exact voice.
{lang_rule}
{offer_rule}
Short wins. The idea must be FELT in the words, not explained.
Format: numbered lines 1. 2. 3. — captions only, no commentary."""
    outs = {}
    try:
        outs["sonnet"] = claude("You are this brand's admin — you write real posts, never ad-copy.",
                                 [{"role": "user", "content": task}], temp=0.9)
    except Exception as e:
        outs["sonnet_err"] = str(e)[:80]
    try:
        outs["gpt"] = gpt([{"role": "system", "content": "You are this brand's admin — you write real posts, never ad-copy."},
                            {"role": "user", "content": task}], temp=0.9)
    except Exception as e:
        outs["gpt_err"] = str(e)[:80]
    # parse numbered lines
    options = {}
    import re as _re
    # B039: the whitelist must be the brand's REAL HASHTAGS — products/phrases alone
    # stripped every legit tag on the 41-brand path (a product name is not a hashtag).
    # Stored WITHOUT '#' and case-exact (Apify) — normalize both sides to compare.
    real_tags = {t.lstrip("#").casefold()
                 for t in (list(pack.get("real_hashtags", [])) + list(pack.get("real_products", []))
                           + list(dna.get("signature_phrases_ar", [])))}
    for src, txt in outs.items():
        if src.endswith("_err"):
            continue
        for ln in txt.split("\n"):
            ln = ln.strip()
            if ln[:2] in ("1.", "2.", "3.") and len(ln) > 8:
                cap = ln[2:].strip().strip('"').strip()
                # TRUTH GUARD (v2 #6 'ججك'): strip any hashtag the brand never used
                for tag in _re.findall(r"#[\w؀-ۿ_]+", cap):
                    bare = tag.lstrip("#").casefold()
                    if bare not in real_tags and not any(bare in t for t in real_tags):
                        cap = cap.replace(tag, "").strip()
                options[f"{src}{ln[0]}"] = " ".join(cap.split())
    return options


def critic(caption, brand_ar, occasion, angle):
    """GPT judges vs the founder taste law (cross-model from the Sonnet pick)."""
    kills = json.dumps([k["name"] for k in TASTE["kills"]], ensure_ascii=False)
    out = gpt([{"role": "system", "content":
                f"You judge Saudi Instagram captions for a founder with sharp taste. Score 0-10. "
                f"KILL (score <=4): generic celebration+CTA templates, 'very normal' safe lines that any brand could post, "
                f"engagement bait, offer/discount energy on emotional occasions, non-Saudi/MSA phrasing, brand-as-symbol metaphors. "
                f"REWARD (score >=7): a SPECIFIC scene you can SEE (a named person, a time of day, a real gesture), the product sitting "
                f"naturally inside that moment, brand-true Saudi voice. A theme is not a scene. "
                'Return JSON: {"score": n, "fix": "ARABIC, one concrete instruction to make the NEXT version more specific — name a person/time/gesture to add. Empty if score>=7."}'}],
               temp=0.1, max_tokens=160, force_json=True)
    try:
        d = json.loads(out)
        return int(d.get("score", 5)), d.get("fix", "")
    except Exception:
        return 5, ""


def run(brand_en, occasion, n_angles=2):
    """Generate from N angles, two pens each, filter deterministically, rank by DNA fit.
    The GPT critic is BLIND (calibration: scores 3 for the founder's 5s AND 0s) — proven
    June 11, matching the standing lesson 'AI judge can't judge Saudi creative'. So no AI
    gate: deterministic filter + DNA-fit rank, then a human (Claude in-context, or Mohamed)
    is the only judge. Returns the full ranked candidate set per chosen angle."""
    m = json.loads((BASE / "data/brief_matrix.json").read_text())
    b = next((x for x in m if x.get("brand_en") == brand_en), None)
    if not b:
        raise RuntimeError(f"not in matrix: {brand_en}")
    pack, cards = ensure_assets(brand_en, occasion)
    angles = cards.get("angles", [])
    # pick the top N most-concrete angles (the CD pick + variety)
    chosen = []
    if angles:
        top = pick_angle(cards, occasion)
        chosen.append(top)
        for a in angles:
            if a.get("id") != top.get("id") and len(chosen) < n_angles:
                chosen.append(a)
    results = []
    for angle in chosen:
        opts = render(brand_en, b["brand"], occasion, angle, pack)
        survivors, _ = filter_options(opts)
        for k, cap in survivors.items():
            results.append({"caption": cap, "angle_scene": angle.get("insight_ar", ""),
                             "formula": angle.get("formula", ""), "lens": angle.get("lens", ""),
                             "dna_fit": score_v2(cap, brand_en, b["brand"]), "pen": k[:6]})
    # rank by DNA fit; dedup identical
    seen, ranked = set(), []
    for r in sorted(results, key=lambda x: x["dna_fit"], reverse=True):
        kk = r["caption"][:30]
        if kk in seen:
            continue
        seen.add(kk); ranked.append(r)
    return {"brand": b["brand"], "brand_en": brand_en, "occasion": occasion, "candidates": ranked}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--occasion", default="national_day")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = run(a.brand, a.occasion)
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        for c in r["candidates"][:6]:
            print(f"  [{c['dna_fit']}|{c['formula']}] {c['caption']}")


if __name__ == "__main__":
    main()
