#!/usr/bin/env python3
"""
semantic_search.py
Semantic (embedding-based) search over all OGZ observations using OpenAI
text-embedding-3-small.

Modes
-----
Build / update index (only embeds new obs since last run):
    python3 scripts/semantic_search.py --build

Rebuild everything from scratch:
    python3 scripts/semantic_search.py --build --force

Search (prints top 10 results):
    python3 scripts/semantic_search.py "ramadan food photography"
    python3 scripts/semantic_search.py "minimalist beauty reel"
    python3 scripts/semantic_search.py "price promotion arabic" --top 20

Index files written to logs/:
    logs/obs_search_index.json   — metadata list (ulid, handle, sector, …)
    logs/obs_embeddings.npy      — float32 array, shape N×1536
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS_DIR = BASE / "logs"
INDEX_PATH = LOGS_DIR / "obs_search_index.json"
EMBEDDINGS_PATH = LOGS_DIR / "obs_embeddings.npy"

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
BATCH_SIZE = 500
# Approximate cost per token for text-embedding-3-small (USD per 1K tokens)
COST_PER_1K_TOKENS = 0.00002
AVG_TOKENS_PER_OBS = 200  # conservative estimate for the embedding text


# ---------------------------------------------------------------------------
# Helpers — obs loading
# ---------------------------------------------------------------------------

def _str(val) -> str:
    """Coerce any value to a stripped string, returning '' for None/falsy."""
    if val is None:
        return ""
    if isinstance(val, list):
        return " ".join(str(v) for v in val if v)
    return str(val).strip()


def build_embedding_text(obs: dict) -> str:
    """
    Compose a single embedding string that captures the semantic content of
    an observation.

    Format:
        {content_type} | {sector} | {caption[:300]} | patterns: {slugs} |
        {composition_style} | {hook_type}
    """
    cr = obs.get("content_ref") or {}
    vv = obs.get("visual_observations") or {}
    vo = obs.get("voice_observations") or {}

    content_type = _str(cr.get("content_type"))
    sector = _str(obs.get("sector"))
    caption = _str(vo.get("caption_text"))[:300]
    composition = _str(vv.get("composition_style"))
    hook_type = _str(vo.get("hook_type"))  # field may not exist; graceful

    pattern_slugs = []
    for pm in obs.get("pattern_matches") or []:
        if isinstance(pm, dict):
            slug = _str(pm.get("pattern_slug"))
        else:
            slug = _str(pm)
        if slug:
            pattern_slugs.append(slug)
    patterns_str = " ".join(pattern_slugs)

    parts = [
        content_type,
        sector,
        caption,
        f"patterns: {patterns_str}" if patterns_str else "",
        composition,
        hook_type,
    ]
    return " | ".join(p for p in parts if p)


def build_metadata_record(obs: dict) -> dict:
    """Return the lightweight metadata dict stored in obs_search_index.json."""
    cr = obs.get("content_ref") or {}
    vo = obs.get("voice_observations") or {}
    caption = _str(vo.get("caption_text"))
    return {
        "ulid": obs.get("observation_ulid", ""),
        "handle": obs.get("account_handle_normalized", ""),
        "sector": obs.get("sector", ""),
        "content_type": _str(cr.get("content_type")),
        "text_snippet": caption[:120] + ("…" if len(caption) > 120 else ""),
        "source_url": _str(cr.get("source_url")),
    }


def load_all_obs() -> list[dict]:
    """Load every observation JSON file, returning raw dicts."""
    obs_list = []
    for path in sorted(OBS_ROOT.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("observation_ulid"):
                obs_list.append(data)
        except Exception as exc:
            print(f"  [warn] could not parse {path.name}: {exc}", file=sys.stderr)
    return obs_list


# ---------------------------------------------------------------------------
# Embedding via OpenAI
# ---------------------------------------------------------------------------

def get_openai_client():
    """Return an OpenAI client (B258 factory — timeout/retries baked in), failing loudly if key is missing."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from lib.openai_client import make_client
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai", file=sys.stderr)
        sys.exit(1)
    try:
        return make_client(os.environ.get("OPENAI_API_KEY"))
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def embed_texts(client, texts: list[str]) -> np.ndarray:
    """
    Embed a list of strings in batches of BATCH_SIZE.
    Returns float32 array of shape (len(texts), EMBED_DIM).
    """
    all_vecs: list[list[float]] = []
    total = len(texts)
    for start in range(0, total, BATCH_SIZE):
        batch = texts[start : start + BATCH_SIZE]
        end = min(start + BATCH_SIZE, total)
        print(f"  Embedding {start + 1}–{end} of {total}…")
        # Retry with back-off on rate-limit errors
        for attempt in range(5):
            try:
                response = client.embeddings.create(model=EMBED_MODEL, input=batch)
                break
            except Exception as exc:
                if attempt == 4:
                    raise
                wait = 2 ** (attempt + 1)
                print(f"  [warn] API error ({exc}), retrying in {wait}s…", file=sys.stderr)
                time.sleep(wait)
        # response.data is ordered by index
        sorted_data = sorted(response.data, key=lambda x: x.index)
        all_vecs.extend(item.embedding for item in sorted_data)

    return np.array(all_vecs, dtype=np.float32)


def embed_query(client, query: str) -> np.ndarray:
    """Embed a single query string. Returns shape (1536,) float32."""
    response = client.embeddings.create(model=EMBED_MODEL, input=[query])
    return np.array(response.data[0].embedding, dtype=np.float32)


# ---------------------------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------------------------

def cosine_similarity_matrix(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    query_vec : (D,) float32
    matrix    : (N, D) float32
    Returns   : (N,) float32 cosine similarities
    """
    q_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    # Row-normalise the matrix
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-10
    m_norm = matrix / norms
    return m_norm @ q_norm  # shape (N,)


# ---------------------------------------------------------------------------
# Build command
# ---------------------------------------------------------------------------

def cmd_build(force: bool = False) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Loading observations from {OBS_ROOT}…")
    all_obs = load_all_obs()
    print(f"Found {len(all_obs)} observation files.")

    if not all_obs:
        print("No observations found. Nothing to do.")
        return

    # ---- Load existing index + embeddings (resume-safe) -------------------
    existing_ulids: set[str] = set()
    existing_index: list[dict] = []
    existing_embeddings: Optional[np.ndarray] = None

    if not force and INDEX_PATH.exists() and EMBEDDINGS_PATH.exists():
        try:
            existing_index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
            existing_embeddings = np.load(str(EMBEDDINGS_PATH))
            existing_ulids = {r["ulid"] for r in existing_index}
            print(
                f"Loaded existing index: {len(existing_index)} obs, "
                f"embeddings shape {existing_embeddings.shape}."
            )
        except Exception as exc:
            print(f"[warn] Could not load existing index ({exc}). Rebuilding from scratch.", file=sys.stderr)
            existing_index = []
            existing_embeddings = None
            existing_ulids = set()
    elif force:
        print("--force: rebuilding from scratch.")

    # ---- Determine new obs -----------------------------------------------
    new_obs = [o for o in all_obs if o.get("observation_ulid") not in existing_ulids]

    if not new_obs:
        print(f"Index is up to date — no new observations to embed.")
        print(f"Index: {len(existing_index)} obs | {EMBEDDINGS_PATH}")
        return

    # ---- Cost estimate ---------------------------------------------------
    estimated_tokens = len(new_obs) * AVG_TOKENS_PER_OBS
    estimated_cost = estimated_tokens * COST_PER_1K_TOKENS / 1000
    print(
        f"\nNew obs to embed: {len(new_obs)}"
        f"\nEstimated tokens: ~{estimated_tokens:,}"
        f"\nEstimated cost:   ~${estimated_cost:.4f} USD\n"
    )

    # ---- Build embedding texts + metadata --------------------------------
    texts = [build_embedding_text(o) for o in new_obs]
    new_meta = [build_metadata_record(o) for o in new_obs]

    # ---- Embed -----------------------------------------------------------
    client = get_openai_client()
    new_vecs = embed_texts(client, texts)  # (len(new_obs), 1536)

    # ---- Merge with existing ---------------------------------------------
    if existing_embeddings is not None and len(existing_index) > 0:
        merged_index = existing_index + new_meta
        merged_embeddings = np.concatenate([existing_embeddings, new_vecs], axis=0)
    else:
        merged_index = new_meta
        merged_embeddings = new_vecs

    # ---- Save ------------------------------------------------------------
    INDEX_PATH.write_text(
        json.dumps(merged_index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    np.save(str(EMBEDDINGS_PATH), merged_embeddings)

    print(
        f"\nIndex built: {len(merged_index)} obs, saved to logs/"
        f"\n  {INDEX_PATH}"
        f"\n  {EMBEDDINGS_PATH}  (shape {merged_embeddings.shape})"
    )


# ---------------------------------------------------------------------------
# Search command
# ---------------------------------------------------------------------------

def cmd_search(query: str, top_k: int = 10) -> None:
    # ---- Load index + embeddings -----------------------------------------
    if not INDEX_PATH.exists() or not EMBEDDINGS_PATH.exists():
        print(
            "Index not found. Run first:\n"
            "  python3 scripts/semantic_search.py --build",
            file=sys.stderr,
        )
        sys.exit(1)

    index: list[dict] = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    embeddings: np.ndarray = np.load(str(EMBEDDINGS_PATH))

    if len(index) != embeddings.shape[0]:
        print(
            f"[warn] Index length ({len(index)}) != embeddings rows ({embeddings.shape[0]}). "
            "Run --build to fix.",
            file=sys.stderr,
        )

    # ---- Embed query -------------------------------------------------------
    client = get_openai_client()
    print(f'Searching {len(index)} obs for: "{query}"\n')
    q_vec = embed_query(client, query)

    # ---- Score + rank -------------------------------------------------------
    scores = cosine_similarity_matrix(q_vec, embeddings)
    top_k = min(top_k, len(index))
    top_indices = np.argsort(scores)[::-1][:top_k]

    # ---- Print results ------------------------------------------------------
    width = len(str(top_k))
    for rank, idx in enumerate(top_indices, 1):
        rec = index[idx]
        score = scores[idx]
        snippet = rec.get("text_snippet", "").replace("\n", " ")
        url = rec.get("source_url", "")
        handle = rec.get("handle", "")
        ctype = rec.get("content_type", "")
        sector = rec.get("sector", "")

        print(
            f"{rank:{width}}. [{score:.4f}] @{handle}  {ctype}  [{sector}]"
        )
        if snippet:
            print(f"   {snippet}")
        if url:
            print(f"   {url}")
        print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Semantic search over OGZ observation corpus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Search query string (omit when using --build).",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build or update the embedding index.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force a full rebuild (only valid with --build).",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Number of results to return (default: 10).",
    )

    args = parser.parse_args()

    if args.build:
        cmd_build(force=args.force)
    elif args.query:
        cmd_search(args.query, top_k=args.top)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
