#!/usr/bin/env python3
"""
fix_embeddings.py — Build OpenAI embeddings for all 6,888 observations.

Embeds: caption_text + sector + occasion + account (context string)
Model: text-embedding-3-small (1536 dims, cheapest, strong)
Batch: 100 obs per API call, concurrent batches
After: creates IVFFlat index for fast cosine similarity search

Usage:
  python3 scripts/fix_embeddings.py             # run all
  python3 scripts/fix_embeddings.py --dry-run   # show counts only
  python3 scripts/fix_embeddings.py --batch 50  # smaller batches
  python3 scripts/fix_embeddings.py --verify    # check after run
"""

import os, sys, json, time, argparse
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(BASE))

import psycopg2
from psycopg2.extras import execute_values
import openai

DB_URL = "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge"
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
BATCH_SIZE = 100
PROGRESS_FILE = BASE / "logs" / "embedding_progress.json"

def load_key():
    env = {}
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    key = env.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not found in ~/.abraham_env")
    return key

def build_embed_text(row: dict) -> str:
    """Build the text string we embed per observation."""
    parts = []
    sector = row.get("sector", "")
    account = row.get("account_handle_normalized", "")
    occasion = row.get("occasion") or "evergreen"
    voice = row.get("voice_observations") or {}
    visual = row.get("visual_observations") or {}

    caption = voice.get("caption_text", "") or voice.get("hook_text", "")
    tone = voice.get("tone", "")
    format_type = row.get("content_type", "")
    setting = visual.get("setting", "")
    content_pillar = row.get("content_pillar", "")
    emotion = row.get("emotion_primary", "")

    if caption:
        parts.append(caption[:400])
    parts.append(f"sector:{sector}")
    parts.append(f"account:{account}")
    parts.append(f"occasion:{occasion}")
    if tone:
        parts.append(f"tone:{tone}")
    if format_type:
        parts.append(f"format:{format_type}")
    if setting:
        parts.append(f"setting:{setting}")
    if content_pillar:
        parts.append(f"pillar:{content_pillar}")
    if emotion:
        parts.append(f"emotion:{emotion}")

    return " | ".join(parts)

def fetch_missing(conn, limit=None):
    cur = conn.cursor()
    q = """
        SELECT observation_ulid, account_handle_normalized, sector, occasion,
               content_type, content_pillar, emotion_primary,
               voice_observations, visual_observations
        FROM observations
        WHERE embedding IS NULL
        ORDER BY created_at DESC
    """
    if limit:
        q += f" LIMIT {limit}"
    cur.execute(q)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    cur.close()
    return rows

def embed_batch(client, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in resp.data]

def save_embeddings(conn, pairs: list[tuple]):
    """pairs: list of (ulid, embedding_list)"""
    cur = conn.cursor()
    # Use pgvector format: '[0.1, 0.2, ...]'
    execute_values(
        cur,
        "UPDATE observations SET embedding = data.emb::vector FROM (VALUES %s) AS data(ulid, emb) WHERE observation_ulid = data.ulid",
        [(ulid, f"[{','.join(str(x) for x in emb)}]") for ulid, emb in pairs],
        template="(%s, %s)"
    )
    conn.commit()
    cur.close()

def ensure_vector_index(conn):
    cur = conn.cursor()
    cur.execute("SELECT indexname FROM pg_indexes WHERE tablename='observations' AND indexname='idx_obs_embedding_cosine'")
    if not cur.fetchone():
        print("  Creating IVFFlat index for cosine similarity...")
        cur.execute(f"""
            CREATE INDEX idx_obs_embedding_cosine
            ON observations USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """)
        conn.commit()
        print("  Index created.")
    else:
        print("  IVFFlat index already exists.")
    cur.close()

def verify(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM observations WHERE embedding IS NOT NULL")
    filled = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM observations")
    total = cur.fetchone()[0]
    cur.close()
    print(f"\n  Embeddings: {filled}/{total} ({100*filled//max(total,1)}%)")
    if filled == total:
        print("  ALL DONE ✅")
    else:
        print(f"  Still missing: {total - filled}")
    return filled, total

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", type=int, default=BATCH_SIZE)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Only process N obs (for testing)")
    args = parser.parse_args()

    conn = psycopg2.connect(DB_URL)

    if args.verify:
        verify(conn)
        conn.close()
        return

    missing = fetch_missing(conn, limit=args.limit)
    print(f"Observations missing embeddings: {len(missing)}")

    if args.dry_run:
        sample = missing[0] if missing else {}
        if sample:
            print(f"\nSample embed text ({sample['account_handle_normalized']}):")
            print(f"  {build_embed_text(sample)[:200]}")
        conn.close()
        return

    if not missing:
        print("Nothing to embed — all done.")
        ensure_vector_index(conn)
        conn.close()
        return

    api_key = load_key()
    client = openai.OpenAI(api_key=api_key)

    total = len(missing)
    done = 0
    errors = 0
    start = time.time()

    print(f"Embedding {total} observations in batches of {args.batch}...")
    print(f"Model: {EMBED_MODEL} ({EMBED_DIM} dims)\n")

    for i in range(0, total, args.batch):
        chunk = missing[i:i + args.batch]
        texts = [build_embed_text(r) for r in chunk]
        ulids = [r["observation_ulid"] for r in chunk]

        for attempt in range(3):
            try:
                embeddings = embed_batch(client, texts)
                pairs = list(zip(ulids, embeddings))
                save_embeddings(conn, pairs)
                done += len(chunk)
                elapsed = time.time() - start
                rate = done / max(elapsed, 1)
                eta = (total - done) / max(rate, 0.01)
                print(f"  [{done}/{total}] batch {i//args.batch + 1} — {rate:.1f} obs/s — ETA {eta:.0f}s")
                break
            except openai.RateLimitError:
                wait = 10 * (attempt + 1)
                print(f"  Rate limit — waiting {wait}s...")
                time.sleep(wait)
            except Exception as e:
                print(f"  ERROR batch {i//args.batch + 1}: {e}")
                errors += 1
                break

    print(f"\nDone. {done} embedded, {errors} errors.")

    print("\nBuilding vector index...")
    ensure_vector_index(conn)

    print("\nVerification:")
    verify(conn)
    conn.close()

if __name__ == "__main__":
    main()
