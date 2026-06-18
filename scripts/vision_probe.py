#!/usr/bin/env python3
"""VISION PROBE (June 18) — mine the LOCAL reference media with gpt-4o-mini vision to ground the
pilots' visual_dna in what the brand's real high-engagement posts actually look like. Money-
disciplined: cheapest model, detail='low' (flat 85 img tokens ≈ $0.0002/image), media is LOCAL
(no Apify, no download). Output goes through the EXISTING apply_grounded_v37.py contract — every
value stays YELLOW/candidate (Rules #9/#13). Helpers only here; run_vision_probe.py orchestrates.
"""
import base64, glob, json, os
from pathlib import Path

B = Path(__file__).parent.parent


def _load_env():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def top_posts_with_local_media(handle, n=8):
    """Rank the DOWNLOADED media for a client by the post's likesCount (within the local pool — the
    scraper saved recent posts, not all-time top, so we rank what we actually have). Returns
    [(shortCode, likes, path)] newest-strongest first, plus the coverage count."""
    raws = sorted(glob.glob(str(B / f"clients/{handle}/raw/instagram/*/posts.jsonl")))
    by_sc = {}
    if raws:
        for line in Path(raws[-1]).read_text().splitlines():
            try:
                p = json.loads(line)
            except Exception:
                continue
            if p.get("shortCode"):
                by_sc[p["shortCode"]] = p
    media = glob.glob(str(B / f"clients/{handle}/media/*.jpg"))
    ranked = []
    for m in media:
        sc = Path(m).stem
        likes = (by_sc.get(sc) or {}).get("likesCount", 0) or 0
        ranked.append((sc, likes, m))
    ranked.sort(key=lambda t: t[1], reverse=True)
    return ranked[:n], len(media)


VISION_PROMPT = (
    "You are a brand visual analyst. Look at this Saudi Instagram brand photo and return ONLY JSON "
    "with these keys (plain words, base it strictly on what you SEE, no guessing fine print):\n"
    '{"palette_primary":"the single dominant brand color (words + hex if obvious)",'
    '"background_tone":"the background/setting tone",'
    '"color_field_palette":"the overall 2-4 color field",'
    '"lighting":"lighting style","composition":"framing/composition",'
    '"product_guess":"the product shown in plain words, or null if unclear"}'
)


def vision_describe(image_path, model="gpt-4o-mini", max_tokens=300):
    """One cheap vision read of a LOCAL image → dict. Verbatim pattern from overnight_full_rebuild.py
    PHASE 2 (gpt-4o-mini, detail='low'), but reads bytes from disk and forces JSON output."""
    import openai
    client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    resp = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": [
            {"type": "text", "text": VISION_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "low"}},
        ]}],
        max_tokens=max_tokens,
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {}


if __name__ == "__main__":
    import sys
    _load_env()
    h = sys.argv[1] if len(sys.argv) > 1 else "albaik"
    tops, cov = top_posts_with_local_media(h, 8)
    print(f"{h}: {cov} local media · top {len(tops)} by likes (within local pool):")
    for sc, likes, path in tops:
        print(f"  {likes:>6} likes · {sc} · {Path(path).name}")
