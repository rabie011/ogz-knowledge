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


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit(f"no {k}")


def gpt(messages, temp=0.7, max_tok=900, fmt_json=True):
    body = {"model": "gpt-4o", "temperature": temp, "max_tokens": max_tok, "messages": messages}
    if fmt_json:
        body["response_format"] = {"type": "json_object"}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=120).read())["choices"][0]["message"]["content"]


def sonnet(system, messages, max_tok=900):
    body = {"model": "claude-sonnet-4-6", "max_tokens": max_tok, "system": system, "messages": messages}
    rq = urllib.request.Request("https://api.anthropic.com/v1/messages", data=json.dumps(body).encode(),
                                headers={"x-api-key": env("ANTHROPIC_API_KEY"), "anthropic-version": "2023-06-01",
                                         "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=120).read())
    return out["content"][0]["text"]


def load_client(handle: str) -> dict:
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
    # GOLD first (June 12, the ceiling stretch): lines the chair rated >=4 are the
    # strongest few-shot signal — they lead, corpus exemplars fill behind
    gf = cdir / "profile/gold.json"
    if gf.exists():
        gold_lines = [g["line"] for g in json.loads(gf.read_text()).get("gold", [])]
        if gold_lines:
            exemplars = gold_lines[:3] + [e for e in exemplars if e not in gold_lines][:2]
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
    return {"handle": handle, "worn_phrases": worn,
            "brand_ar": prof.get("fullName") or handle,
            "bio": prof.get("biography", ""), "truth": truth,
            "moments": p("moments_bank")["moments"], "fingerprint": p("fingerprint"),
            "state": p("state"), "exemplars": exemplars, "corpus_text": corpus_text,
            "en_led": (p("fingerprint")["l2_voice"].get("dialect") == "non_arabic")}


BRAIN_FILES = {"firaasa": "cd_01_firaasa_architect.md", "metaphor": "cd_02_metaphor_architect.md",
                "authenticity": "cd_03_authenticity_detective.md", "heritage": "cd_04_heritage_decoder.md",
                "paradox": "cd_05_paradox_hunter.md"}


def route_brain(slot: dict, alt: int = 0) -> str:
    """Deterministic CD-brain routing per slot type (Phase B, June 11 — Floward proved
    the full methodologies beat the salvaged one-liners). alt flips the pair for variety."""
    occ = slot.get("occasion") or ""
    if occ in ("saudi_national_day", "saudi_founding_day"):
        return "heritage"  # NOTE: make_angle falls back to firaasa when no root material — guard below
    if occ in ("ramadan", "eid_al_fitr", "eid_al_adha", "arab_mothers_day", "hajj_season"):
        return ("firaasa", "authenticity")[alt % 2]
    if slot.get("type") == "competitor_reference":
        return "paradox"
    return ("metaphor", "paradox")[alt % 2]


def brain_method(brain: str) -> str:
    f = BASE / "20_cd_brains" / BRAIN_FILES[brain]
    return f.read_text()[:2800] if f.exists() else ""


def make_angle(c: dict, slot: dict, sector: str, brain: str | None = None) -> dict:
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
    sys_p = ("You are a Saudi creative director generating ONE angle (idea), not a caption. "
             "An angle is a CONCRETE SCENE: WHO (specific person/role) + WHEN (specific beat) + WHAT (specific gesture) "
             "+ where the product sits naturally inside that exact moment. BANNED: brand-as-bridge/symbol/soul metaphors, "
             "abstract culture/heritage sentences, anything a TV voiceover could say. "
             + method +
             'Return JSON: {"scene_ar": "...", "why_it_lands": "...", "post_type": "moment|announcement|offer|greeting"}')
    user = (f"البراند: {c['brand_ar']} (bio: {c['bio'][:150]})\n"
            f"المنتجات الحقيقية: {products[:8]}\nالقنوات: {channels or 'غير معروفة — لا تخترع قناة'}\n"
            f"السياق: {slot.get('occasion') or slot.get('angle_theme','')} · beat: {slot.get('beat','evergreen')}\n"
            + (f"عدسة القطاع×المناسبة: {json.dumps(lens, ensure_ascii=False)[:600]}\n" if lens else "")
            + (f"لحظات حقيقية من منشوراتهم: {json.dumps([m['evidence'][:70] for m in (lambda ms, d: [ms[(sum(ord(ch) for ch in d) + j) % len(ms)] for j in range(min(3, len(ms)))])(c['moments'], slot.get('date',''))], ensure_ascii=False)}\n" if c["moments"] else "")
            + ("NOTE: this brand speaks English-first — the scene may be EN-hook + AR-idea bilingual.\n" if c["en_led"] else "")
            + f"التاريخ الفعلي للنشر: {slot['date']}")
    return json.loads(gpt([{"role": "system", "content": sys_p}, {"role": "user", "content": user}], temp=0.8, max_tok=400))


CTA_PUSH_TYPES = {"weekly_offer", "white_friday", "11_11_shopping", "singles_day_11_11"}


def cta_allowed(handle: str, slot: dict) -> bool:
    """The 80/20 law in code (zoom-out June 12: 300/356 jurisha cards = 84% order-tails,
    the inverse of the standard; Mohamed's wrong_goal code says it himself: «صفر طاقة
    بيع — اللحظة فقط»). Push slots sell; evergreen sells ~1 day in 4, date-hashed."""
    if slot.get("occasion") in CTA_PUSH_TYPES or slot.get("type") == "offer":
        return True
    import hashlib
    return int(hashlib.md5(f"{handle}{slot.get('date','')}cta".encode()).hexdigest(), 16) % 4 == 0


def render_captions(c: dict, slot: dict, angle: dict) -> list[str]:
    taste = json.loads((BASE / "data/founder_taste.json").read_text())
    products = [x["name"] for x in c["truth"]["product_candidates"]][:5]
    channels = [x["name"] for x in c["truth"]["channels"] if x["name"] != "linktree"]
    bilingual = ("Write EN hook + Arabic idea (bilingual, NOT translation). "
                 "English lines carry a CONCRETE moment or real instruction — never fitness-influencer filler "
                 "('Feeling strong!', 'Ready for more!', 'New week, new you'). The bar: "
                 "'Your Friday just got better — تحرّك مع لياقتي، الكابتن في جيبك'."
                 if c["en_led"] else "Write Saudi Arabic only.")
    sys_p = (f"You write Instagram captions for {c['brand_ar']}. ONE angle, given below — every caption is that angle. "
             "The caption LIVES INSIDE the scene: write from inside that exact moment (its person, its time, its gesture). "
             "The PHOTO already shows the scene — so the caption NEVER narrates it (never 'الأم تضغط الزر، الجد يملأ الأطباق'). "
             "Write what the person in that moment would SAY or feel — the voice FROM the scene, not a description OF it. "
             "The occasion appears only THROUGH the scene — the scene IS the celebration. "
             f"{bilingual} Short captions. Concrete and warm. Offers need what/how-much/where clarity. "
             f"Use ONLY these real facts — products: {products}, channels: {channels or 'NONE — never invent ordering channels'}. "
             + ("Speak only of what the reader can DO today with these real products and channels. "
                if cta_allowed(c["handle"], slot) else
                "TODAY IS A BRAND-BUILD DAY: zero selling energy, NO ordering CTA, do NOT mention "
                "delivery apps or ordering — the moment only (the channels above exist; just don't push them today). ")
             + (f"WORN OUT this month — find another way to say it: {c.get('worn_phrases')}. " if c.get("worn_phrases") else "")
             + "When the brand has a signature product NAME in its own words (recurring terms), USE it — never genericize it away. "
             "No invented hashtags. Return JSON: {\"options\": [\"...\", \"...\", \"...\"]}")
    few = []
    for ex in c["exemplars"][:3]:
        few += [{"role": "user", "content": "اكتب بصوت البراند"}, {"role": "assistant", "content": ex}]
    user = f"الفكرة (الزاوية): {angle['scene_ar']}\nالسياق: {slot.get('occasion') or slot.get('angle_theme','')} في {slot['date']}\nاكتب 3 خيارات."
    opts = []
    try:
        opts += json.loads(gpt([{"role": "system", "content": sys_p}] + few + [{"role": "user", "content": user}], temp=0.85)).get("options", [])
    except Exception as e:
        print(f"  gpt pen failed: {e}", file=sys.stderr)
    try:
        # pen diversity (June 12): the second pen enters the scene from its least
        # obvious angle — different DOOR, same truth. Two pens, two temperaments.
        DOORS = ["the SOUND of the moment (what you hear before you see)",
                 "the SIDE CHARACTER (the little sister, the neighbor, the delivery man)",
                 "the second AFTER the expected moment (the empty plate, the closed door)",
                 "the OBJECT's point of view (the pot, the box, the doorbell)"]
        door = DOORS[sum(ord(ch) for ch in slot.get("date", "")) % 4]
        diversity = (f"\nYOUR PEN'S TEMPERAMENT: enter the scene through {door}. "
                     "Same scene, same truth, unexpected entry.")
        txt = sonnet(sys_p + diversity + "\nReturn ONLY the JSON object.", few + [{"role": "user", "content": user}])
        m = re.search(r"\{.*\}", txt, re.S)
        if m:
            opts += json.loads(m.group(0)).get("options", [])
    except Exception as e:
        print(f"  sonnet pen failed: {e}", file=sys.stderr)
    # truth guard 1: strip hashtags that aren't the client's real ones
    # truth guard 2 (June 11, RABIE-ruled): kill EVENT CLAIMS — inviting people to a
    # gathering/session that isn't in the truth pack is a fabricated fact ("join us in
    # Tabbouk's park for a yoga session" — no such event exists). Bans live in code.
    real_tags = set(c["truth"].get("real_hashtags", []))
    EVENT_CLAIM = re.compile(
        r"(join us|تعالوا|انضم|سجلوا?|احجز مقعد|نلتقي|حضور|invite you|تحدي|challenge)"
        r".{0,60}(session|event|class|workshop|gathering|جلسة|فعالية|ورشة|لقاء|تجمع)|"
        r"(session|class|جلسة|فعالية|ورشة)\s.{0,40}(في|at|@)\s|"
        r"(ابدأ|انضم|join)\s.{0,20}(التحدي|تحدي|challenge)", re.I)
    # truth guard 3: offer energy on emotional occasions = founder kill (code-level)
    EMOTIONAL = {"ramadan", "eid_al_fitr", "eid_al_adha", "saudi_national_day", "saudi_founding_day", "arab_mothers_day"}
    OFFER = re.compile(r"عرض|خصم|تخفيض|كود|discount|offer|% ?off|promo", re.I)
    is_emotional = slot.get("occasion") in EMOTIONAL
    # truth guard 4 (June 11, RABIE-ruled): NOUN GROUNDING — invented product/promo NAMES
    # («التوأم كرسبي بيك x2», mangled app names) must trace to the client's own corpus.
    # Deterministic: suspect tokens = Latin names with digits/dots/caps, or Arabic promo-name
    # constructions; killed unless the client's real captions/bio/truth pack contain them.
    corpus = (c.get("corpus_text") or "").lower()
    PROMO_AR = re.compile(r"(التوأم|كومبو|دبل|ميجا|تريبل)\s+\S+")
    LATIN_NAME = re.compile(r"\b([A-Za-z]+\.[A-Za-z]+|[A-Za-z]*\d+[A-Za-z]*|[A-Z]{3,})\b")
    # truth guard 5 (June 11 — the hallucinated prince): NAMED PEOPLE die unless the
    # client's corpus contains them. Inventing a person's presence is the worst truth
    # violation possible («بحضور الأمير سعود بن عبدالله بن جلوي» — never happened).
    PERSON_AR = re.compile(r"(الأمير|الأميرة|الشيخ|الشيخة|الدكتور(?:ة)?|معالي|سمو)\s+\S+(?:\s+بن\s+\S+)*")

    strip_punct = lambda s: re.sub(r"[^\wء-ي\s]", "", s).strip()  # «دبل القرمشة،» == «دبل القرمشة»

    # person-event law (June 11, RABIE-accepted): real-person mentions live ONLY on
    # documented-moment slots; fictional/evergreen scenes are PERSON-FREE. A corpus-real
    # person in an invented scene = real prince, fabricated ribbon-cutting (the nuance
    # under false-flag #2). Corpus-grounded mentions surviving here still get a
    # REQUIRES-HUMAN-VERIFY line on the visual gate.
    slot_is_documented = bool(slot.get("documented_moment"))

    def ungrounded(text: str) -> str | None:
        for m in PERSON_AR.finditer(text):
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

    cleaned = []
    for o in opts:
        o = re.sub(r"#([\wء-ي_]+)", lambda m: m.group(0) if m.group(1) in real_tags else "", o).strip()
        if not o:
            continue
        if EVENT_CLAIM.search(o):
            print(f"  ✂️ event-claim killed: {o[:60]}…", file=sys.stderr)
            continue
        if is_emotional and OFFER.search(o):
            print(f"  ✂️ offer-on-emotional killed: {o[:60]}…", file=sys.stderr)
            continue
        bad = ungrounded(o)
        if bad:
            print(f"  ✂️ ungrounded name killed [{bad}]: {o[:50]}…", file=sys.stderr)
            continue
        cleaned.append(o)
    surv, _ = filter_options({f"opt_{i}": o for i, o in enumerate(cleaned)})
    final = list(surv.values())[:3] if surv else cleaned[:3]
    # CTA-density rule (June 11, RABIE-ruled): a feed that sells in every line reads like
    # a flyer. Of the 3 options, at most ONE keeps an order-CTA tail — the rest stand on
    # the scene. Deterministic: keep the first CTA, strip CTA sentences from the others.
    CTA = re.compile(r"[^.!؟\n]*\b(اطلب(?:وا|ها|وه)?|حمّ?ل التطبيق|اطلبيها?)\b[^.!؟\n]*[.!؟]?")
    # bilingual filler ban (June 12, RABIE law: journey leaked as رحلة — ban both twins)
    FILLER = re.compile(r"(journey|unleash|conquer|roar|new heights|stronger than ever|"
                         r"رحلة(?!\s+لسوق)|أطلق(?:وا)? العنان|نقهر|القمم الجديدة|أقوى من أي وقت|لحظات لا تُنسى)", re.I)
    cleaned2 = [o for o in final if not FILLER.search(o)] or final[:1]  # never return zero
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


def shot_card(c: dict, angle: dict) -> list[str]:
    out = gpt([{"role": "system", "content":
                "You write PHONE shoot-cards for Saudi SME owners — 3 numbered instructions in simple Saudi Arabic, "
                "each doable at home with a phone in 2 minutes. Conservative cultural defaults (hands/food/place safe, "
                'no faces unless the scene demands). Return JSON: {"shots": ["...", "...", "..."]}'},
               {"role": "user", "content": f"البراند: {c['brand_ar']}\nالمشهد: {angle['scene_ar']}"}], temp=0.5, max_tok=300)
    return [re.sub(r"^\s*\d+[\.\)]\s*", "", s).strip() for s in json.loads(out).get("shots", [])[:3]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--brain", default=None, choices=list(BRAIN_FILES) + ["auto"],
                    help="route the angle through a full CD-brain methodology (auto = slot-type routing)")
    ap.add_argument("--suffix", default="", help="output filename suffix (e.g. __v2_brain)")
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
    brain = route_brain(slot, alt=int(a.date.replace("-", "")) ) if a.brain == "auto" else a.brain
    angle = make_angle(c, slot, ymap["sector"], brain=brain)
    captions = render_captions(c, slot, angle)
    chain = chain_for(slot.get("formula", "CF_01"), ymap["sector"], slot.get("occasion", "evergreen"))
    shots = shot_card(c, angle)
    card = {"handle": a.handle, "date": a.date, "slot": slot, "brain": brain,
            "idea": angle, "captions": captions,
            "visual": {"phone_shoot_card": shots,
                        "pro_chain": {"id": chain.get("chain_id_short"), "name_ar": chain.get("name_ar"),
                                       "family": chain.get("family")} if chain else None},
            "provenance": {"source": "client_profile_path", "rendered": "2026-06-11",
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
    print(f"  💡 {angle['scene_ar'][:110]}")
    for i, cap in enumerate(captions, 1):
        print(f"  ✍️ {i}. {cap[:110]}")


if __name__ == "__main__":
    main()
