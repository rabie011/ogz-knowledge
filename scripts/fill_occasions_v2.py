#!/usr/bin/env python3
"""
fill_occasions_v2.py — Classify occasions for observations where occasion IS NULL.

Uses GPT-4o-mini. Falls back to 'evergreen' when no clear occasion marker.

Allowed occasions (from existing DB values):
  evergreen, riyadh_season, ramadan, eid_al_fitr, jeddah_season,
  leap_conference, hajj_season, national_day, eid_al_adha, white_friday,
  founding_day, summer_campaign, sporting_event, brand_campaign,
  winter_seasonal, graduation_season, vision_2030, day_of_arafah

Usage:
  python3 scripts/fill_occasions_v2.py            # run all
  python3 scripts/fill_occasions_v2.py --dry-run  # show prompt sample
  python3 scripts/fill_occasions_v2.py --verify   # show distribution
  python3 scripts/fill_occasions_v2.py --limit 60 # test on 60
"""

import os, sys, json, time, argparse
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

import psycopg2
import openai

DB_URL = "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge"
MODEL = "gpt-4o-mini"
BATCH = 30

OCCASIONS = [
    "evergreen", "riyadh_season", "ramadan", "eid_al_fitr", "jeddah_season",
    "leap_conference", "hajj_season", "national_day", "eid_al_adha", "white_friday",
    "founding_day", "summer_campaign", "sporting_event", "brand_campaign",
    "winter_seasonal", "graduation_season", "vision_2030", "day_of_arafah",
]

SYSTEM_PROMPT = """You classify Saudi Instagram posts by occasion/season context.

Occasions: evergreen, riyadh_season, ramadan, eid_al_fitr, jeddah_season, leap_conference, hajj_season, national_day, eid_al_adha, white_friday, founding_day, summer_campaign, sporting_event, brand_campaign, winter_seasonal, graduation_season, vision_2030, day_of_arafah

Rules:
- ramadan: mentions fasting, iftar, suhoor, رمضان, Ramadan
- eid_al_fitr: عيد, Eid, after-Ramadan celebration
- eid_al_adha: عيد الأضحى, hajj season offers
- national_day: 23 September, اليوم الوطني, Saudi flag
- founding_day: 22 February, يوم التأسيس
- riyadh_season: موسم الرياض, Riyadh Season
- jeddah_season: موسم جدة, Jeddah Season
- white_friday: جمعة البيضاء, Black Friday equivalent
- leap_conference: مؤتمر ليب, LEAP tech conference
- hajj_season: حج, pilgrim-related
- summer_campaign: صيف, summer sale/campaign
- winter_seasonal: شتاء, winter theme
- sporting_event: كأس, World Cup, دوري, league match
- graduation_season: تخرج, graduation
- vision_2030: Vision 2030 explicit mention
- day_of_arafah: يوم عرفة
- brand_campaign: named brand campaign (not tied to calendar occasion)
- evergreen: no occasion signal at all

Return ONLY a JSON array, one object per post in order:
[{"ulid": "...", "occasion": "..."}]

No markdown. No explanation. Raw JSON only."""

def load_key():
    env = {}
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")

def fetch_missing(conn, limit=None):
    q = """
        SELECT observation_ulid, account_handle_normalized, sector,
               voice_observations, content_ref
        FROM observations
        WHERE occasion IS NULL
        ORDER BY engagement_total DESC NULLS LAST
    """
    if limit:
        q += f" LIMIT {limit}"
    cur = conn.cursor()
    cur.execute(q)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return rows

def build_prompt(rows):
    parts = []
    for r in rows:
        voice = r.get("voice_observations") or {}
        ref = r.get("content_ref") or {}
        caption = (voice.get("caption_text") or voice.get("hook_text") or "")[:250]
        capture_date = ref.get("capture_date", "unknown")
        parts.append(
            f'ulid:{r["observation_ulid"]} | account:{r["account_handle_normalized"]} '
            f'| sector:{r["sector"]} | date:{capture_date}\n'
            f'caption: {caption}'
        )
    return "\n\n---\n\n".join(parts)

def classify_batch(client, rows):
    user_msg = build_prompt(rows)
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0,
                max_tokens=2000,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                raw = "\n".join(lines).strip()
            return json.loads(raw)
        except json.JSONDecodeError:
            if attempt == 3:
                return []
        except openai.RateLimitError:
            wait = 15 * (attempt + 1)
            print(f"  Rate limit — waiting {wait}s")
            time.sleep(wait)
        except Exception as e:
            print(f"  Error: {e}")
            if attempt == 3:
                return []
    return []

def save_occasions(conn, results, rows):
    row_map = {r["observation_ulid"]: r for r in rows}
    updates = []
    for item in results:
        ulid = item.get("ulid", "")
        occ = item.get("occasion", "evergreen")
        if ulid in row_map:
            updates.append((occ if occ in OCCASIONS else "evergreen", ulid))
    if not updates:
        return 0
    cur = conn.cursor()
    cur.executemany("UPDATE observations SET occasion = %s WHERE observation_ulid = %s", updates)
    conn.commit()
    cur.close()
    return len(updates)

def verify(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM observations WHERE occasion IS NULL")
    null_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM observations")
    total = cur.fetchone()[0]
    cur.execute("SELECT occasion, COUNT(*) FROM observations GROUP BY occasion ORDER BY COUNT(*) DESC")
    dist = cur.fetchall()
    cur.close()
    print(f"\n  occasion=NULL: {null_count}/{total}")
    print("  Distribution:")
    for r in dist:
        print(f"    {r[0]}: {r[1]}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--batch", type=int, default=BATCH)
    args = parser.parse_args()

    conn = psycopg2.connect(DB_URL)

    if args.verify:
        verify(conn)
        conn.close()
        return

    missing = fetch_missing(conn, limit=args.limit)
    print(f"Observations with NULL occasion: {len(missing)}")

    if args.dry_run:
        print("\nSample prompt (first 3):")
        print(build_prompt(missing[:3])[:600])
        conn.close()
        return

    if not missing:
        print("No NULL occasions — all done.")
        verify(conn)
        conn.close()
        return

    api_key = load_key()
    client = openai.OpenAI(api_key=api_key)

    total = len(missing)
    done = 0
    start = time.time()
    bs = args.batch

    print(f"Classifying {total} obs in batches of {bs}...\n")

    for i in range(0, total, bs):
        chunk = missing[i:i + bs]
        results = classify_batch(client, chunk)
        if results:
            saved = save_occasions(conn, results, chunk)
            done += saved
        elapsed = time.time() - start
        rate = (i + len(chunk)) / max(elapsed, 1)
        eta = (total - i - len(chunk)) / max(rate, 0.01)
        print(f"  [{i + len(chunk)}/{total}] saved={done} — ETA {eta:.0f}s")

    print(f"\nDone. {done} records updated.")
    print("\nVerification:")
    verify(conn)
    conn.close()

if __name__ == "__main__":
    main()
