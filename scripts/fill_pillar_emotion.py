#!/usr/bin/env python3
"""
fill_pillar_emotion.py — Fill content_pillar + emotion_primary for ~4,000 empty obs.

Uses GPT-4o-mini to classify 20 observations per API call.
Only uses values that already exist in the DB (no new categories invented).

content_pillar: product | community | lifestyle | entertainment | educational
emotion_primary: appetite | aspiration | anticipation | warmth | pride | urgency | trust | joy | surprise

Usage:
  python3 scripts/fill_pillar_emotion.py            # run all missing
  python3 scripts/fill_pillar_emotion.py --dry-run  # show sample prompt
  python3 scripts/fill_pillar_emotion.py --verify   # show fill rates
  python3 scripts/fill_pillar_emotion.py --limit 60 # test on 60 obs
"""

import os, sys, json, time, argparse
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

import psycopg2
from psycopg2.extras import execute_values
import openai

DB_URL = "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge"
MODEL = "gpt-4o-mini"
BATCH = 20

PILLARS = ["product", "community", "lifestyle", "entertainment", "educational"]
EMOTIONS = ["appetite", "aspiration", "anticipation", "warmth", "pride", "urgency", "trust", "joy", "surprise"]

SYSTEM_PROMPT = f"""You classify Saudi Instagram posts by content_pillar and emotion_primary.

content_pillar options (pick exactly one):
- product: showcases a specific product/service/offer
- community: builds connection, user-generated, cultural moments, togetherness
- lifestyle: aspirational living, experiences, routines not tied to a product
- entertainment: humor, behind-the-scenes, games, challenges
- educational: how-to, tips, information, ingredients, process

emotion_primary options (pick exactly one):
- appetite: food/beauty desire, craving, wanting to try
- aspiration: wanting to be/have/achieve something better
- anticipation: excitement about what's coming, launches, events
- warmth: comfort, nostalgia, belonging, family
- pride: Saudi identity, national pride, achievement
- urgency: limited time, FOMO, act now
- trust: reliability, quality proof, credentials
- joy: happiness, fun, celebration
- surprise: unexpected, wow factor, discovery

Return ONLY a JSON array, one object per post, in the same order as input:
[{{"ulid": "...", "pillar": "...", "emotion": "..."}}]

No explanation. No markdown. Raw JSON only."""

def load_key():
    env = {}
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")

def fetch_missing(conn, field="both", limit=None):
    if field == "both":
        where = "content_pillar IS NULL OR emotion_primary IS NULL"
    elif field == "pillar":
        where = "content_pillar IS NULL"
    else:
        where = "emotion_primary IS NULL"

    q = f"""
        SELECT observation_ulid, account_handle_normalized, sector, occasion,
               content_pillar, emotion_primary, voice_observations, visual_observations
        FROM observations
        WHERE {where}
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

def build_user_prompt(rows: list[dict]) -> str:
    posts = []
    for r in rows:
        voice = r.get("voice_observations") or {}
        visual = r.get("visual_observations") or {}
        caption = (voice.get("caption_text") or voice.get("hook_text") or "")[:300]
        tone = voice.get("tone", "")
        setting = visual.get("setting", "")
        human = visual.get("human_presence", "")
        posts.append(
            f'ulid:{r["observation_ulid"]} | sector:{r["sector"]} | occasion:{r.get("occasion","?")} '
            f'| tone:{tone} | setting:{setting} | human:{human}\n'
            f'caption: {caption}'
        )
    return "\n\n---\n\n".join(posts)

def classify_batch(client, rows: list[dict]) -> list[dict]:
    user_msg = build_user_prompt(rows)
    for attempt in range(4):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0,
                max_tokens=1500,
            )
            raw = resp.choices[0].message.content.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                raw = "\n".join(lines).strip()
            results = json.loads(raw)
            return results
        except json.JSONDecodeError as e:
            print(f"  JSON parse error attempt {attempt+1}: {e}")
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

def validate_and_save(conn, results: list[dict], rows: list[dict]):
    # Index input rows by ulid
    row_map = {r["observation_ulid"]: r for r in rows}
    updates = []

    for item in results:
        ulid = item.get("ulid", "")
        pillar = item.get("pillar", "")
        emotion = item.get("emotion", "")

        if ulid not in row_map:
            continue

        row = row_map[ulid]
        new_pillar = pillar if pillar in PILLARS else row.get("content_pillar")
        new_emotion = emotion if emotion in EMOTIONS else row.get("emotion_primary")

        if new_pillar or new_emotion:
            updates.append((new_pillar, new_emotion, ulid))

    if not updates:
        return 0

    cur = conn.cursor()
    cur.executemany(
        """UPDATE observations
           SET content_pillar = COALESCE(%s, content_pillar),
               emotion_primary = COALESCE(%s, emotion_primary)
           WHERE observation_ulid = %s""",
        updates
    )
    conn.commit()
    cur.close()
    return len(updates)

def verify(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM observations")
    total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM observations WHERE content_pillar IS NOT NULL")
    p = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM observations WHERE emotion_primary IS NOT NULL")
    e = cur.fetchone()[0]
    cur.execute("SELECT content_pillar, COUNT(*) FROM observations WHERE content_pillar IS NOT NULL GROUP BY content_pillar ORDER BY COUNT(*) DESC")
    p_dist = cur.fetchall()
    cur.execute("SELECT emotion_primary, COUNT(*) FROM observations WHERE emotion_primary IS NOT NULL GROUP BY emotion_primary ORDER BY COUNT(*) DESC")
    e_dist = cur.fetchall()
    cur.close()

    print(f"\n  content_pillar:  {p}/{total} ({100*p//total}%)")
    for row in p_dist:
        print(f"    {row[0]}: {row[1]}")
    print(f"\n  emotion_primary: {e}/{total} ({100*e//total}%)")
    for row in e_dist:
        print(f"    {row[0]}: {row[1]}")

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
    print(f"Observations missing pillar or emotion: {len(missing)}")

    if args.dry_run:
        sample = missing[:3] if missing else []
        print("\nSample prompt (first 3 obs):")
        print(build_user_prompt(sample)[:800])
        conn.close()
        return

    if not missing:
        print("Nothing to fill — all done.")
        verify(conn)
        conn.close()
        return

    api_key = load_key()
    client = openai.OpenAI(api_key=api_key)

    total = len(missing)
    done = 0
    start = time.time()
    bs = args.batch

    print(f"Classifying {total} obs in batches of {bs} using {MODEL}...\n")

    for i in range(0, total, bs):
        chunk = missing[i:i + bs]
        results = classify_batch(client, chunk)

        if results:
            saved = validate_and_save(conn, results, chunk)
            done += saved
        else:
            print(f"  Batch {i//bs + 1}: no results returned")

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
