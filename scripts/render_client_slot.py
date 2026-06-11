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
    return {"handle": handle, "brand_ar": prof.get("fullName") or handle,
            "bio": prof.get("biography", ""), "truth": p("truth_pack"),
            "moments": p("moments_bank")["moments"][:6], "fingerprint": p("fingerprint"),
            "state": p("state"), "exemplars": exemplars,
            "en_led": (p("fingerprint")["l2_voice"].get("dialect") == "non_arabic")}


def make_angle(c: dict, slot: dict, sector: str) -> dict:
    facts = json.loads((BASE / "data/occasion_facts.json").read_text())
    occ = slot.get("occasion", "")
    key = {"saudi_national_day": "saudi_national_day"}.get(occ, occ)
    lens = (facts.get(key, {}).get("sector_lenses") or {}).get(sector, {})
    products = [x["name"] for x in c["truth"]["product_candidates"]] + c["truth"]["recurring_caption_terms"][:5]
    channels = [x["name"] for x in c["truth"]["channels"] if x["name"] != "linktree"]
    sys_p = ("You are a Saudi creative director generating ONE angle (idea), not a caption. "
             "An angle is a CONCRETE SCENE: WHO (specific person/role) + WHEN (specific beat) + WHAT (specific gesture) "
             "+ where the product sits naturally inside that exact moment. BANNED: brand-as-bridge/symbol/soul metaphors, "
             "abstract culture/heritage sentences, anything a TV voiceover could say. "
             'Return JSON: {"scene_ar": "...", "why_it_lands": "...", "post_type": "moment|announcement|offer|greeting"}')
    user = (f"البراند: {c['brand_ar']} (bio: {c['bio'][:150]})\n"
            f"المنتجات الحقيقية: {products[:8]}\nالقنوات: {channels or 'غير معروفة — لا تخترع قناة'}\n"
            f"السياق: {slot.get('occasion') or slot.get('angle_theme','')} · beat: {slot.get('beat','evergreen')}\n"
            + (f"عدسة القطاع×المناسبة: {json.dumps(lens, ensure_ascii=False)[:600]}\n" if lens else "")
            + (f"لحظات حقيقية من منشوراتهم: {json.dumps([m['evidence'][:70] for m in c['moments'][:3]], ensure_ascii=False)}\n" if c["moments"] else "")
            + ("NOTE: this brand speaks English-first — the scene may be EN-hook + AR-idea bilingual.\n" if c["en_led"] else "")
            + f"التاريخ الفعلي للنشر: {slot['date']}")
    return json.loads(gpt([{"role": "system", "content": sys_p}, {"role": "user", "content": user}], temp=0.8, max_tok=400))


def render_captions(c: dict, slot: dict, angle: dict) -> list[str]:
    taste = json.loads((BASE / "data/founder_taste.json").read_text())
    products = [x["name"] for x in c["truth"]["product_candidates"]][:5]
    channels = [x["name"] for x in c["truth"]["channels"] if x["name"] != "linktree"]
    bilingual = "Write EN hook + Arabic idea (bilingual, NOT translation)." if c["en_led"] else "Write Saudi Arabic only."
    sys_p = (f"You write Instagram captions for {c['brand_ar']}. ONE angle, given below — every caption is that angle. "
             "The caption LIVES INSIDE the scene: write from inside that exact moment (its person, its time, its gesture). "
             "The occasion appears only THROUGH the scene — the scene IS the celebration. "
             f"{bilingual} Short captions. Concrete and warm. Offers need what/how-much/where clarity. "
             f"Use ONLY these real facts — products: {products}, channels: {channels or 'NONE — never invent ordering channels'}. "
             "Speak only of what the reader can DO today with these real products and channels. "
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
        txt = sonnet(sys_p + "\nReturn ONLY the JSON object.", few + [{"role": "user", "content": user}])
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
        r"(join us|تعالوا|انضم|سجلوا?|احجز مقعد|نلتقي|حضور|invite you)"
        r".{0,60}(session|event|class|workshop|gathering|جلسة|فعالية|ورشة|لقاء|تجمع)|"
        r"(session|class|جلسة|فعالية|ورشة)\s.{0,40}(في|at|@)\s", re.I)
    # truth guard 3: offer energy on emotional occasions = founder kill (code-level)
    EMOTIONAL = {"ramadan", "eid_al_fitr", "eid_al_adha", "saudi_national_day", "saudi_founding_day", "arab_mothers_day"}
    OFFER = re.compile(r"عرض|خصم|تخفيض|كود|discount|offer|% ?off|promo", re.I)
    is_emotional = slot.get("occasion") in EMOTIONAL
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
        cleaned.append(o)
    surv, _ = filter_options({f"opt_{i}": o for i, o in enumerate(cleaned)})
    return list(surv.values())[:3] if surv else cleaned[:3]


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
    a = ap.parse_args()
    gate = blackout_check()
    if not gate["publish_allowed"]:
        sys.exit(f"BLACKOUT — rendering parked: {gate['hard_block']['reason']}")
    ymap = json.loads((BASE / "clients" / a.handle / "year_map.json").read_text())
    slot = next((s for mm in ymap["months"].values() for s in mm if s["date"] == a.date), None)
    if not slot:
        sys.exit(f"no slot {a.date} in {a.handle} year map")
    c = load_client(a.handle)
    angle = make_angle(c, slot, ymap["sector"])
    captions = render_captions(c, slot, angle)
    chain = chain_for(slot.get("formula", "CF_01"), ymap["sector"], slot.get("occasion", "evergreen"))
    shots = shot_card(c, angle)
    card = {"handle": a.handle, "date": a.date, "slot": slot,
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
    fn = out / f"{a.date}__{slot.get('occasion') or 'evergreen'}.json"
    fn.write_text(json.dumps(card, ensure_ascii=False, indent=2))
    print(f"✓ {a.handle} {a.date} [{slot.get('occasion') or slot.get('angle_theme','')[:40]}]")
    print(f"  💡 {angle['scene_ar'][:110]}")
    for i, cap in enumerate(captions, 1):
        print(f"  ✍️ {i}. {cap[:110]}")


if __name__ == "__main__":
    main()
