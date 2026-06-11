#!/usr/bin/env python3
"""THE POST UNIT (June 12) — image+caption as ONE idea. Born from Mohamed's five
"needs an image" notes: a caption is half a post.

POST CARD = { scene (the angle), visual: {phone_shot_list, chain_ref}, captions }
- phone shot-list → the SME shoot-card ("صوّر كذا بجوالك") — the tier-2 promise
- chain_ref → the pro/fal production path (Ahmed's 88-chain library, matched via
  the Mohamed-confirmed formula→chain_families map)
- captions → the creative line's render of the SAME angle (idea consistency)

Usage: python3 scripts/post_unit.py --brand albaik --occasion national_day
"""
import argparse, json, os, re, sys, urllib.request
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from creative_line import ensure_assets, pick_angle, render
from caption_filter import filter_options
from scorer_v2 import score_v2

BASE = Path(__file__).parent.parent


def env(k):
    for l in open(os.path.expanduser("~/.abraham_env")):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    sys.exit(f"no {k}")


def chain_for(formula_id: str, sector: str, occasion: str) -> dict | None:
    forms = yaml.safe_load((BASE / "21_strategy_frameworks/creative_formulas.yaml").read_text())
    fams = []
    for v in forms.get("formulas", {}).values():
        if v.get("id") == formula_id:
            fams = v.get("chain_families", [])
    idx = json.load(open(BASE / "02_what_to_build/INDEX.json"))
    chains = idx if isinstance(idx, list) else idx.get("chains", [])
    def ok(c):
        if c.get("family") not in fams:
            return False
        sa = c.get("sectors_allowed") or []
        oa = c.get("occasions_allowed") or []
        s_ok = not sa or sector in sa or "all" in sa
        o_ok = not oa or occasion in oa or "all" in oa or "evergreen" in oa
        return s_ok and o_ok
    cands = [c for c in chains if ok(c)]
    if not cands:
        cands = [c for c in chains if c.get("family") in fams]
    return cands[0] if cands else None


def shot_list(scene: str, brand_ar: str, products: list) -> list[str]:
    """3-line phone shoot-card from the scene — GPT, concrete and doable at home."""
    body = {"model": "gpt-4o", "temperature": 0.5, "max_tokens": 300,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content":
                 "You write PHONE shoot-cards for Saudi SME owners — 3 numbered instructions in simple Saudi Arabic, "
                 "each one doable at home with a phone in 2 minutes: position, light, the one action to capture. "
                 "Concrete, warm, zero jargon. Cultural defaults conservative (no faces unless the scene demands; hands/food/place are safe). "
                 'Return JSON: {"shots": ["...", "...", "..."]}'},
                {"role": "user", "content": f"البراند: {brand_ar} · المنتجات: {', '.join(products[:3])}\nالمشهد المطلوب تصويره:\n{scene}"}]}
    rq = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                data=json.dumps(body).encode(),
                                headers={"Authorization": f"Bearer {env('OPENAI_API_KEY')}",
                                         "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=90).read())["choices"][0]["message"]["content"]
    shots = json.loads(out).get("shots", [])[:3]
    return [re.sub(r"^\s*\d+[\.\)]\s*", "", sh).strip() for sh in shots]


def build_post_card(brand_en: str, occasion: str) -> dict:
    m = json.loads((BASE / "data/brief_matrix.json").read_text())
    b = next((x for x in m if x.get("brand_en") == brand_en), None)
    if not b:
        raise RuntimeError(f"not in matrix: {brand_en} (newborn clients: use --client mode, coming next)")
    pack, cards = ensure_assets(brand_en, occasion)
    angle = pick_angle(cards, occasion)
    scene = angle.get("insight_ar", "")
    chain = chain_for(angle.get("formula", ""), b["sector"], occasion)
    shots = shot_list(scene, b["brand"], pack.get("real_products", []))
    opts = render(brand_en, b["brand"], occasion, angle, pack)
    surv, _ = filter_options(opts)
    ranked = sorted(surv.items(), key=lambda kv: score_v2(kv[1], brand_en, b["brand"]), reverse=True)
    return {
        "brand": b["brand"], "brand_en": brand_en, "occasion": occasion,
        "idea": {"scene": scene, "formula": angle.get("formula"), "lens": angle.get("lens")},
        "visual": {
            "phone_shoot_card": shots,
            "pro_chain": {"id": chain.get("chain_id_short"), "name_ar": chain.get("name_ar"),
                           "family": chain.get("family"), "output": chain.get("output_type")} if chain else None,
        },
        "captions": [c for _, c in ranked[:3]],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--occasion", default="national_day")
    a = ap.parse_args()
    card = build_post_card(a.brand, a.occasion)
    out = BASE / "data" / "post_cards"
    out.mkdir(exist_ok=True)
    (out / f"{a.brand}__{a.occasion}.json").write_text(json.dumps(card, ensure_ascii=False, indent=2))
    print(f"💡 IDEA: {card['idea']['scene']}")
    print(f"\n📱 SHOOT CARD (بجوالك):")
    for i, s in enumerate(card["visual"]["phone_shoot_card"], 1):
        print(f"   {i}. {s}")
    pc = card["visual"]["pro_chain"]
    if pc:
        print(f"\n🎬 PRO PATH: chain {pc['id']} — {pc['name_ar']} ({pc['output']})")
    print(f"\n✍️ CAPTIONS:")
    for i, c in enumerate(card["captions"], 1):
        print(f"   {i}. {c}")


if __name__ == "__main__":
    main()
