#!/usr/bin/env python3
"""
deepen_brand_profiles.py — Mine top observations per brand and enrich intelligence_layer.json.

For each of 52 brands in intelligence_layer.json:
  - Pulls top 30 obs from DB (by engagement_total)
  - Extracts: proven_openers, real_hooks, winning_formats, top_cta_types, avoid_patterns
  - Updates intelligence_layer.json brand_profiles in-place

Uses GPT-4o-mini for extraction. Outputs a backup before modifying.

Usage:
  python3 scripts/deepen_brand_profiles.py             # enrich all brands
  python3 scripts/deepen_brand_profiles.py --dry-run   # show what would change
  python3 scripts/deepen_brand_profiles.py --brand albaik  # single brand
  python3 scripts/deepen_brand_profiles.py --verify    # show gap report
"""

import os, sys, json, time, argparse, shutil
from pathlib import Path
from collections import Counter

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

import psycopg2
import openai

DB_URL = "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge"
IL_PATH = BASE / "11_who_to_learn_from" / "intelligence_layer.json"
MODEL = "gpt-4o-mini"

def load_key():
    env = {}
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")

def fetch_brand_obs(conn, handle, limit=30):
    cur = conn.cursor()
    cur.execute("""
        SELECT voice_observations, visual_observations, content_type,
               engagement_total, likes_count, occasion, content_pillar, emotion_primary
        FROM observations
        WHERE account_handle_normalized = %s
        ORDER BY engagement_total DESC NULLS LAST
        LIMIT %s
    """, (handle, limit))
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return rows

def extract_captions(obs):
    caps = []
    for r in obs:
        v = r.get("voice_observations") or {}
        cap = v.get("caption_text") or v.get("hook_text") or ""
        if cap and len(cap) > 10:
            caps.append(cap[:400])
    return caps

def extract_hooks(obs):
    hooks = []
    for r in obs:
        v = r.get("voice_observations") or {}
        h = v.get("hook_text") or ""
        if h and len(h) > 5:
            hooks.append(h[:150])
    return hooks

def extract_formats(obs):
    counts = Counter()
    for r in obs:
        ct = r.get("content_type") or ""
        if ct:
            counts[ct] += 1
    return dict(counts.most_common(5))

def extract_ctas(obs):
    counts = Counter()
    for r in obs:
        v = r.get("voice_observations") or {}
        cta = v.get("cta_type") or ""
        if cta and cta != "none":
            counts[cta] += 1
    return dict(counts.most_common(5))

EXTRACT_SYSTEM = """You are an Arabic content analyst. Given the top-performing captions from a Saudi brand's Instagram account, extract:

1. proven_openers: list of 3-5 actual opening phrases or patterns that appear in high-engagement posts (Arabic preferred)
2. real_hooks: list of 3-5 specific hooks or lines that worked well (actual text from captions)
3. high_engagement_style: 1-2 sentence description of the style/approach that drives engagement for this brand
4. avoid_patterns: list of 2-3 patterns/phrases to avoid (what appears in low-quality posts or never appears in their best work)

Return ONLY valid JSON (no markdown):
{
  "proven_openers": [...],
  "real_hooks": [...],
  "high_engagement_style": "...",
  "avoid_patterns": [...]
}"""

def gpt_extract(client, brand, sector, captions, hooks):
    if not captions:
        return {}

    user_msg = f"Brand: {brand} | Sector: {sector}\n\nTop captions (highest engagement first):\n\n"
    for i, cap in enumerate(captions[:20], 1):
        user_msg += f"{i}. {cap[:300]}\n\n"

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": EXTRACT_SYSTEM},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=600,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                raw = "\n".join(lines).strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            if attempt == 2:
                return {}
        except openai.RateLimitError:
            wait = 20 * (attempt + 1)
            print(f"  Rate limit — waiting {wait}s")
            time.sleep(wait)
        except Exception as e:
            print(f"  GPT error: {e}")
            if attempt == 2:
                return {}
    return {}

def verify_gaps(conn, il):
    brands = il.get("brand_profiles", {})
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT account_handle_normalized, COUNT(*), MAX(engagement_total) FROM observations GROUP BY account_handle_normalized ORDER BY COUNT(*) DESC")
    db_brands = {r[0]: {"count": r[1], "max_eng": r[2]} for r in cur.fetchall()}
    cur.close()

    print(f"\n{'Brand':<30} {'DB obs':>8} {'Max eng':>10} {'In IL':>6} {'Has openers':>12}")
    print("-" * 70)
    for handle, stats in sorted(db_brands.items(), key=lambda x: -x[1]["count"])[:30]:
        in_il = handle in brands
        has_openers = bool(brands.get(handle, {}).get("proven_openers"))
        print(f"  {handle:<28} {stats['count']:>8} {(stats['max_eng'] or 0):>10} {str(in_il):>6} {str(has_openers):>12}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--brand", type=str, default=None, help="Single brand handle to process")
    args = parser.parse_args()

    conn = psycopg2.connect(DB_URL)
    il = json.loads(IL_PATH.read_text())

    if args.verify:
        verify_gaps(conn, il)
        conn.close()
        return

    brands = il.get("brand_profiles", {})
    if args.brand:
        target_brands = {args.brand: brands.get(args.brand, {})}
    else:
        target_brands = brands

    # Also check DB for accounts not yet in intelligence_layer
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT account_handle_normalized, COUNT(*) FROM observations GROUP BY account_handle_normalized HAVING COUNT(*) >= 5 ORDER BY COUNT(*) DESC")
    db_accounts = {r[0]: r[1] for r in cur.fetchall()}
    cur.close()

    # Add DB accounts missing from IL
    for handle, count in db_accounts.items():
        if handle not in target_brands and not args.brand:
            target_brands[handle] = {}

    if args.dry_run:
        print(f"Would process {len(target_brands)} brands")
        for h, profile in list(target_brands.items())[:5]:
            obs_count = db_accounts.get(h, 0)
            has_openers = bool(profile.get("proven_openers"))
            print(f"  {h}: {obs_count} obs | has_openers={has_openers}")
        conn.close()
        return

    api_key = load_key()
    client = openai.OpenAI(api_key=api_key)

    # Backup before modifying
    backup_path = IL_PATH.parent / f"intelligence_layer_backup_{int(time.time())}.json"
    shutil.copy(IL_PATH, backup_path)
    print(f"Backup: {backup_path.name}")

    updated = 0
    skipped = 0

    for handle, profile in target_brands.items():
        obs = fetch_brand_obs(conn, handle)
        if len(obs) < 3:
            print(f"  {handle}: only {len(obs)} obs — skipping")
            skipped += 1
            continue

        sector = profile.get("sector", "")
        if not sector:
            # Try to get from DB
            cur = conn.cursor()
            cur.execute("SELECT sector FROM observations WHERE account_handle_normalized=%s LIMIT 1", (handle,))
            row = cur.fetchone()
            cur.close()
            sector = row[0] if row else "unknown"

        captions = extract_captions(obs)
        hooks = extract_hooks(obs)
        formats = extract_formats(obs)
        ctas = extract_ctas(obs)

        # GPT extraction for semantic fields
        extracted = gpt_extract(client, handle, sector, captions, hooks)

        # Merge into profile
        updated_profile = dict(profile)
        updated_profile["sector"] = sector

        # From data (no GPT needed)
        updated_profile["obs_count"] = len(obs)
        updated_profile["best_format"] = max(formats, key=formats.get) if formats else profile.get("best_format", "")
        updated_profile["format_distribution"] = formats
        updated_profile["top_cta_types"] = list(ctas.keys())[:3]
        updated_profile["sample_real_hooks"] = hooks[:5]

        # From GPT
        if extracted:
            updated_profile["proven_openers"] = extracted.get("proven_openers", [])
            updated_profile["real_hooks"] = extracted.get("real_hooks", [])
            updated_profile["high_engagement_style"] = extracted.get("high_engagement_style", "")
            updated_profile["avoid_patterns"] = extracted.get("avoid_patterns", [])

        il["brand_profiles"][handle] = updated_profile
        updated += 1

        openers_count = len(updated_profile.get("proven_openers", []))
        print(f"  ✓ {handle}: {len(obs)} obs | {openers_count} openers | format={updated_profile.get('best_format','?')}")

        time.sleep(0.5)  # gentle rate limiting

    # Save
    IL_PATH.write_text(json.dumps(il, ensure_ascii=False, indent=2))
    print(f"\nSaved. Updated {updated} brands, skipped {skipped}.")
    print(f"intelligence_layer.json: {len(il.get('brand_profiles', {}))} brand profiles")

    conn.close()

if __name__ == "__main__":
    main()
