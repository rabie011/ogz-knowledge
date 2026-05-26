#!/usr/bin/env python3
"""
enrich_obs_openai.py — Enrich existing obs with OpenAI Batch API

Phase 1: Pattern slug assignment  → 1,808 obs with empty pattern_matches
Phase 2: Caption deep parse       → 2,743 obs (hook_type, cta_type, arabic_technique)
Phase 3: Visual enrichment        → 2,498 obs (og:image fetch → GPT-4o-mini vision)

Usage:
  python3 scripts/enrich_obs_openai.py --phase 1
  python3 scripts/enrich_obs_openai.py --phase 2
  python3 scripts/enrich_obs_openai.py --phase 3
  python3 scripts/enrich_obs_openai.py --all
  python3 scripts/enrich_obs_openai.py --all --dry-run
  python3 scripts/enrich_obs_openai.py --status      # check batch job status
"""

import argparse, json, os, pathlib, re, sys, time, requests
import numpy as np
from datetime import datetime

REPO = pathlib.Path(__file__).parent.parent
OBS_ROOT  = REPO / "11_who_to_learn_from/observations"
PAT_ROOT  = REPO / "11_who_to_learn_from/patterns"
STATE_FILE = REPO / "logs/enrichment_state.json"
BATCH_DIR  = REPO / "logs/enrichment_batches"
BATCH_DIR.mkdir(parents=True, exist_ok=True)

# ── OpenAI client ──────────────────────────────────────────────────────────────
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
except ImportError:
    print("ERROR: openai not installed — pip install openai", file=sys.stderr)
    sys.exit(1)
except KeyError:
    print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
    sys.exit(1)

MODEL = "gpt-4o-mini"

# ── State helpers ──────────────────────────────────────────────────────────────
def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Pattern matching via embeddings (no batch quota issues)
# ══════════════════════════════════════════════════════════════════════════════
EMBED_MODEL   = "text-embedding-3-small"
PAT_CACHE     = REPO / "logs/pattern_embeddings.json"
EMBED_BATCH   = 500   # embed this many texts per API call

def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float32)
    vb = np.array(b, dtype=np.float32)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb) + 1e-9))

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts in batches. Returns list of embedding vectors."""
    all_vecs = []
    for i in range(0, len(texts), EMBED_BATCH):
        chunk = texts[i:i + EMBED_BATCH]
        resp  = client.embeddings.create(model=EMBED_MODEL, input=chunk)
        all_vecs.extend([r.embedding for r in resp.data])
    return all_vecs

def load_pattern_index() -> tuple[list[str], list[str], list[list[float]]]:
    """Load (slugs, texts, embeddings) — generate and cache on first run."""
    # Build slug list + text for embedding
    slugs, texts, names = [], [], []
    for cat_dir in sorted(PAT_ROOT.iterdir()):
        if not cat_dir.is_dir():
            continue
        for pf in sorted(cat_dir.glob("*.json")):
            d     = json.loads(pf.read_text())
            slug  = d.get("pattern_slug", "")
            name  = d.get("pattern_name", "")
            desc  = d.get("description", "")[:120]
            if slug:
                slugs.append(slug)
                names.append(name)
                texts.append(f"{name}: {desc}" if desc else name)

    # Check cache validity
    if PAT_CACHE.exists():
        cached = json.loads(PAT_CACHE.read_text())
        if len(cached.get("slugs", [])) == len(slugs):
            return slugs, names, cached["embeddings"]

    # Generate embeddings
    print(f"  Embedding {len(slugs)} patterns (one-time, ~$0.01)...")
    vecs = embed_texts(texts)
    PAT_CACHE.write_text(json.dumps({"slugs": slugs, "embeddings": vecs}, ensure_ascii=False))
    print(f"  Pattern embeddings cached → {PAT_CACHE}")
    return slugs, names, vecs

def run_phase1_embeddings(obs_list: list[dict], dry_run: bool) -> int:
    """Match patterns to obs using cosine similarity on embeddings."""
    state    = load_state()
    ph       = state.setdefault("phases", {}).setdefault("1", {"done_ulids": [], "total_written": 0})
    already  = set(ph.get("done_ulids", []))

    # Filter obs that need patterns
    needed = [d for d in obs_list
              if not d.get("pattern_matches")
              and pathlib.Path(d["_path"]).stem not in already]

    if not needed:
        print("  Phase 1: nothing to do ✅")
        return 0

    print(f"  {len(needed)} obs need pattern matching")
    if dry_run:
        print(f"  [DRY RUN] Would embed {len(needed)} obs captions. Estimated cost: ${len(needed) * 200 * 0.00002 / 1000:.4f}")
        return 0

    # Load pattern index
    pat_slugs, pat_names, pat_vecs = load_pattern_index()
    pat_matrix = np.array(pat_vecs, dtype=np.float32)  # (N_patterns, dim)

    # Build obs texts for embedding
    obs_texts = []
    for d in needed:
        vo      = d.get("voice_observations", {})
        cr      = d.get("content_ref", {})
        caption = (vo.get("caption_text") or "").strip()[:400]
        sector  = cr.get("sector") or d.get("sector") or ""
        ct      = cr.get("content_type", "")
        obs_texts.append(f"{ct} post in {sector} sector. Caption: {caption}" if caption
                         else f"{ct} post in {sector} sector")

    print(f"  Embedding {len(obs_texts)} obs texts...")
    obs_vecs = embed_texts(obs_texts)

    # Match each obs to top-5 patterns
    written = 0
    for d, obs_vec in zip(needed, obs_vecs):
        ov  = np.array(obs_vec, dtype=np.float32)
        # Cosine similarity to all patterns
        norms = np.linalg.norm(pat_matrix, axis=1) * np.linalg.norm(ov) + 1e-9
        sims  = (pat_matrix @ ov) / norms
        top5  = np.argsort(sims)[-5:][::-1]

        patterns = []
        for idx in top5:
            score = float(sims[idx])
            if score < 0.30:  # below threshold → skip
                break
            conf = "strong" if score > 0.55 else "moderate" if score > 0.40 else "weak"
            patterns.append({"pattern_slug": pat_slugs[idx], "confidence": conf})

        if not patterns:
            continue

        fpath = pathlib.Path(d["_path"])
        obs   = json.loads(fpath.read_text())
        if obs.get("pattern_matches"):
            continue  # filled by another run
        obs["pattern_matches"] = patterns
        fpath.write_text(json.dumps(obs, ensure_ascii=False, indent=2))
        written += 1

        ulid = pathlib.Path(d["_path"]).stem
        ph["done_ulids"].append(ulid)

    ph["total_written"] = ph.get("total_written", 0) + written
    ph["last_run"]      = datetime.now().isoformat()
    save_state(state)

    print(f"  ✅ Phase 1 complete — {written} obs updated with pattern_matches")
    return written

# ── Load all obs ──────────────────────────────────────────────────────────────
def load_all_obs() -> list[dict]:
    obs = []
    for f in OBS_ROOT.rglob("*.json"):
        try:
            d = json.loads(f.read_text())
            d["_path"] = str(f)
            obs.append(d)
        except Exception:
            pass
    return obs

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Pattern slug assignment
# ══════════════════════════════════════════════════════════════════════════════
PHASE1_SYSTEM = """You are a Saudi Instagram content pattern matcher.
Given a post's metadata, identify the 2–5 best matching pattern slugs from the vocabulary below.
Return ONLY a JSON array of objects: [{{"pattern_slug": "slug", "confidence": "strong"|"moderate"|"weak"}}]
No explanation. No extra keys. Empty array [] if truly nothing matches.

PATTERN VOCABULARY (slug: name — description):
{vocab}"""

PHASE1_USER = """Content type: {content_type}
Sector: {sector}
Caption: {caption}
Engagement potential: {engagement}
Return matching pattern slugs."""

def build_phase1_requests(obs_list: list[dict], already_done: set) -> list[dict]:
    requests_out = []
    vocab = get_pattern_vocab()
    system = PHASE1_SYSTEM.format(vocab=vocab)

    for d in obs_list:
        ulid = d.get("observation_ulid") or d.get("ulid") or pathlib.Path(d["_path"]).stem
        if ulid in already_done:
            continue
        pm = d.get("pattern_matches", [])
        if pm:  # already has patterns
            continue

        cr  = d.get("content_ref", {})
        vo  = d.get("voice_observations", {})
        caption = (vo.get("caption_text") or "").strip()[:500]
        if not caption:
            caption = "(no caption)"

        sector = cr.get("sector") or d.get("sector") or "unknown"
        ct = cr.get("content_type", "image")
        eng = d.get("engagement_potential") or d.get("classification", {}).get("engagement_potential", "medium")

        requests_out.append({
            "custom_id": f"p1_{ulid}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "max_tokens": 300,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": PHASE1_USER.format(
                        content_type=ct, sector=sector,
                        caption=caption, engagement=eng
                    )}
                ]
            }
        })
    return requests_out

def apply_phase1_results(results: list[dict]) -> int:
    written = 0
    # Build ulid → file path index
    path_index = {}
    for f in OBS_ROOT.rglob("*.json"):
        path_index[f.stem] = f

    for r in results:
        if r.get("error"):
            continue
        cid = r["custom_id"]           # p1_{ulid}
        ulid = cid[3:]                  # strip "p1_"
        content = r["response"]["body"]["choices"][0]["message"]["content"].strip()
        try:
            patterns = json.loads(content)
            if not isinstance(patterns, list):
                continue
            # Normalise
            cleaned = []
            for p in patterns:
                if isinstance(p, dict) and p.get("pattern_slug"):
                    cleaned.append({
                        "pattern_slug": p["pattern_slug"].lower().replace(" ", "_"),
                        "confidence":   p.get("confidence", "moderate")
                    })
            if not cleaned:
                continue
        except Exception:
            continue

        fpath = path_index.get(ulid)
        if not fpath:
            continue
        d = json.loads(fpath.read_text())
        if d.get("pattern_matches"):  # already filled by another run
            continue
        d["pattern_matches"] = cleaned
        fpath.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        written += 1

    return written

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Caption deep parse
# ══════════════════════════════════════════════════════════════════════════════
PHASE2_SYSTEM = """You are an Arabic/Saudi social media caption analyst.
Analyse the Instagram caption and return ONLY this JSON (no extra text):
{
  "hook_type": "question"|"statement"|"command"|"emoji_led"|"arabic_idiom"|"price_anchor"|"occasion_reference"|"none",
  "hook_text": "<first line or sentence, max 60 chars>",
  "cta_type": "visit_store"|"order_now"|"follow"|"tag_someone"|"comment"|"none",
  "arabic_technique": "colloquial_gulf"|"colloquial_levantine"|"msa_formal"|"bilingual_mix"|"english_only"|"none",
  "emotion_words": ["word1","word2"],
  "language": "arabic"|"english"|"bilingual"|"none"
}"""

def build_phase2_requests(obs_list: list[dict], already_done: set) -> list[dict]:
    requests_out = []
    for d in obs_list:
        ulid = d.get("observation_ulid") or d.get("ulid") or pathlib.Path(d["_path"]).stem
        if ulid in already_done:
            continue
        vo = d.get("voice_observations", {})
        caption = (vo.get("caption_text") or "").strip()
        if not caption or vo.get("hook_type") is not None:
            continue  # no caption or already parsed

        requests_out.append({
            "custom_id": f"p2_{ulid}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "max_tokens": 200,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": PHASE2_SYSTEM},
                    {"role": "user",   "content": f"Caption:\n{caption[:800]}"}
                ]
            }
        })
    return requests_out

def apply_phase2_results(results: list[dict]) -> int:
    written = 0
    path_index = {}
    for f in OBS_ROOT.rglob("*.json"):
        path_index[f.stem] = f

    for r in results:
        if r.get("error"):
            continue
        cid  = r["custom_id"]
        ulid = cid[3:]
        content = r["response"]["body"]["choices"][0]["message"]["content"].strip()
        try:
            parsed = json.loads(content)
        except Exception:
            # Try to extract JSON from text
            m = re.search(r"\{.*\}", content, re.DOTALL)
            if not m:
                continue
            try:
                parsed = json.loads(m.group())
            except Exception:
                continue

        fpath = path_index.get(ulid)
        if not fpath:
            continue
        d = json.loads(fpath.read_text())
        vo = d.setdefault("voice_observations", {})
        if vo.get("hook_type") is not None:
            continue  # already done

        vo["hook_type"]        = parsed.get("hook_type")
        vo["hook_text"]        = parsed.get("hook_text")
        vo["cta_type"]         = parsed.get("cta_type")
        vo["arabic_technique"] = parsed.get("arabic_technique")
        vo["emotion_words"]    = parsed.get("emotion_words", [])
        # Update language if not set
        if not vo.get("language") and parsed.get("language"):
            vo["language"] = parsed["language"]

        fpath.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        written += 1

    return written

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Visual enrichment (og:image → GPT-4o-mini vision)
# ══════════════════════════════════════════════════════════════════════════════
PHASE3_SYSTEM = """You are a visual content analyst for Saudi/Middle East Instagram.
Analyse the image and return ONLY this JSON:
{
  "composition_style": "product_hero"|"lifestyle_integrated"|"editorial"|"overhead_spread"|"face_forward"|"text_dominant"|"behind_the_scenes"|"mixed",
  "human_presence": "none"|"partial"|"full",
  "text_overlay_visible": true|false,
  "arabic_text_visible": true|false,
  "product_visible": true|false,
  "brand_logo_visible": true|false,
  "dominant_color": "<one color name>",
  "scene_type": "indoor"|"outdoor"|"studio"|"graphic"|"mixed"
}"""

IG_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def fetch_og_image(source_url: str) -> str | None:
    """Fetch og:image CDN URL from an Instagram post page."""
    try:
        r = requests.get(source_url, headers=IG_HEADERS, timeout=8)
        if r.status_code != 200:
            return None
        m = re.search(r'property="og:image"\s+content="([^"]+)"', r.text)
        if not m:
            m = re.search(r'content="([^"]+)"\s+property="og:image"', r.text)
        return m.group(1) if m else None
    except Exception:
        return None

def build_phase3_requests(obs_list: list[dict], already_done: set,
                          img_cache: dict, dry_run: bool) -> list[dict]:
    requests_out = []
    fetch_errors  = 0
    dry_run_candidates = 0

    for d in obs_list:
        ulid = d.get("observation_ulid") or d.get("ulid") or pathlib.Path(d["_path"]).stem
        if ulid in already_done:
            continue
        vis = d.get("visual_observations", {})
        # Skip if both key fields already filled
        if vis.get("composition_style") and vis.get("human_presence") is not None:
            continue
        cr = d.get("content_ref", {})
        ct = cr.get("content_type", "")
        # Only image and carousel (video thumbnails less reliable)
        if ct not in ("image", "carousel_slide"):
            continue

        source_url = cr.get("source_url", "")
        if not source_url:
            continue

        # Dry run: just count candidates without fetching
        if dry_run:
            dry_run_candidates += 1
            continue

        # Check cache first
        img_url = img_cache.get(ulid)
        if not img_url:
            img_url = fetch_og_image(source_url)
            if img_url:
                img_cache[ulid] = img_url
            else:
                fetch_errors += 1
                if fetch_errors > 20:  # stop if Instagram is blocking
                    print(f"  ⚠ Too many og:image fetch errors — stopping Phase 3 fetch")
                    break
                continue
            time.sleep(0.3)  # gentle rate limit

        if not img_url:
            continue

        dry_run_candidates += 1
        requests_out.append({
            "custom_id": f"p3_{ulid}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": MODEL,
                "max_tokens": 200,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": PHASE3_SYSTEM},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": img_url, "detail": "low"}},
                        {"type": "text", "text": "Analyse this Saudi Instagram post image."}
                    ]}
                ]
            }
        })

    if dry_run:
        # Return a fake list just to report the count
        return [None] * dry_run_candidates
    return requests_out

def apply_phase3_results(results: list[dict]) -> int:
    written = 0
    path_index = {}
    for f in OBS_ROOT.rglob("*.json"):
        path_index[f.stem] = f

    for r in results:
        if r.get("error"):
            continue
        cid  = r["custom_id"]
        ulid = cid[3:]
        content = r["response"]["body"]["choices"][0]["message"]["content"].strip()
        try:
            parsed = json.loads(content)
        except Exception:
            m = re.search(r"\{.*\}", content, re.DOTALL)
            if not m:
                continue
            try:
                parsed = json.loads(m.group())
            except Exception:
                continue

        fpath = path_index.get(ulid)
        if not fpath:
            continue
        d   = json.loads(fpath.read_text())
        vis = d.setdefault("visual_observations", {})

        if not vis.get("composition_style"):
            vis["composition_style"] = parsed.get("composition_style")
        if vis.get("human_presence") is None:
            vis["human_presence"] = parsed.get("human_presence")
        # New fields
        vis["text_overlay_visible"] = parsed.get("text_overlay_visible", False)
        vis["arabic_text_visible"]  = parsed.get("arabic_text_visible", False)
        vis["product_visible"]      = parsed.get("product_visible", False)
        vis["brand_logo_visible"]   = parsed.get("brand_logo_visible", False)
        if parsed.get("dominant_color"):
            vis["dominant_color"]   = parsed["dominant_color"]
        if parsed.get("scene_type"):
            vis["scene_type"]       = parsed["scene_type"]

        fpath.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        written += 1

    return written

# ══════════════════════════════════════════════════════════════════════════════
# BATCH JOB RUNNER
# ══════════════════════════════════════════════════════════════════════════════
def submit_batch(requests_list: list[dict], phase_label: str) -> str:
    """Write JSONL, upload, submit batch. Returns batch_id."""
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = BATCH_DIR / f"{phase_label}_{ts}.jsonl"
    with open(jsonl_path, "w") as fh:
        for req in requests_list:
            fh.write(json.dumps(req, ensure_ascii=False) + "\n")
    print(f"  Uploading {len(requests_list)} requests ({jsonl_path.stat().st_size // 1024} KB)...")
    with open(jsonl_path, "rb") as fh:
        file_obj = client.files.create(file=fh, purpose="batch")
    batch = client.batches.create(
        input_file_id=file_obj.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )
    print(f"  Batch submitted: {batch.id} (status: {batch.status})")
    return batch.id

def poll_batch(batch_id: str, label: str, timeout_s: int = 7200) -> list[dict]:
    """Poll until complete, return parsed results."""
    start = time.time()
    while True:
        elapsed = time.time() - start
        if elapsed > timeout_s:
            print(f"  ⚠ Batch {batch_id} timed out after {timeout_s}s")
            return []
        batch = client.batches.retrieve(batch_id)
        done  = batch.request_counts.completed if batch.request_counts else 0
        total = batch.request_counts.total     if batch.request_counts else "?"
        print(f"  [{label}] status={batch.status} completed={done}/{total} elapsed={int(elapsed)}s")
        if batch.status == "completed":
            # Download results
            out_file_id = batch.output_file_id
            raw = client.files.content(out_file_id).text
            results = [json.loads(line) for line in raw.strip().splitlines() if line.strip()]
            print(f"  ✅ Batch complete — {len(results)} results")
            return results
        if batch.status in ("failed", "expired", "cancelled"):
            print(f"  ❌ Batch {batch_id} ended with status={batch.status}")
            return []
        sleep_s = 30 if elapsed < 120 else 60
        time.sleep(sleep_s)

# ══════════════════════════════════════════════════════════════════════════════
# STATUS COMMAND
# ══════════════════════════════════════════════════════════════════════════════
def print_status():
    state = load_state()
    print("\n── Enrichment State ──────────────────────────────")
    for phase, info in state.get("phases", {}).items():
        print(f"  Phase {phase}: {info}")
    print()
    obs = load_all_obs()
    p1_needed = sum(1 for d in obs if not d.get("pattern_matches"))
    p2_needed = sum(1 for d in obs
                    if (d.get("voice_observations", {}).get("caption_text") or "").strip()
                    and d.get("voice_observations", {}).get("hook_type") is None)
    p3_needed = sum(1 for d in obs
                    if d.get("content_ref", {}).get("content_type") in ("image", "carousel_slide")
                    and not (d.get("visual_observations", {}).get("composition_style")
                             and d.get("visual_observations", {}).get("human_presence") is not None))
    print(f"  Phase 1 remaining: {p1_needed} obs need pattern_matches")
    print(f"  Phase 2 remaining: {p2_needed} obs need caption parse")
    print(f"  Phase 3 remaining: {p3_needed} image/carousel obs need visual enrichment")
    print()

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def run_phase(phase_num: int, obs_list: list, state: dict, dry_run: bool):
    label_map = {1: "pattern_assignment (embeddings)", 2: "caption_parse", 3: "visual_enrichment"}
    label = label_map[phase_num]
    print(f"\n{'='*60}")
    print(f"  PHASE {phase_num} — {label.upper()}")
    print(f"{'='*60}")

    # Phase 1 uses embeddings — separate path
    if phase_num == 1:
        run_phase1_embeddings(obs_list, dry_run)
        return

    phases = state.setdefault("phases", {})
    ph_key = str(phase_num)
    ph     = phases.setdefault(ph_key, {"done_ulids": [], "last_run": None, "total_written": 0})
    already_done = set(ph["done_ulids"])

    # Resume existing batch if one is active
    if ph.get("active_batch_id") and not dry_run:
        print(f"  Resuming existing batch {ph['active_batch_id']}...")
        results = poll_batch(ph["active_batch_id"], label)
        if results:
            written = apply_phase2_results(results) if phase_num == 2 else apply_phase3_results(results)
            done_ids = [r["custom_id"].split("_", 1)[1] for r in results if not r.get("error")]
            ph["done_ulids"].extend(done_ids)
            ph["total_written"] = ph.get("total_written", 0) + written
            ph.pop("active_batch_id", None)
            ph["last_run"] = datetime.now().isoformat()
            save_state(state)
            print(f"\n  ✅ Phase {phase_num} complete — {written} obs updated")
        return

    # Build requests
    img_cache = {}
    if phase_num == 2:
        reqs = build_phase2_requests(obs_list, already_done)
    else:
        print(f"  Fetching og:image URLs (this may take a few minutes)...")
        reqs = build_phase3_requests(obs_list, already_done, img_cache, dry_run)
        # Save img_cache
        cache_path = BATCH_DIR / "img_url_cache.json"
        existing = json.loads(cache_path.read_text()) if cache_path.exists() else {}
        existing.update(img_cache)
        cache_path.write_text(json.dumps(existing, indent=2))

    if not reqs:
        print(f"  Nothing to do for phase {phase_num} ✅")
        return

    print(f"  {len(reqs)} requests to process")

    # Estimate cost
    if phase_num == 1:
        est_cost = len(reqs) * (7000 * 0.075 + 300 * 0.300) / 1_000_000
    elif phase_num == 2:
        est_cost = len(reqs) * (600  * 0.075 + 200 * 0.300) / 1_000_000
    else:
        est_cost = len(reqs) * (1000 * 0.075 + 200 * 0.300) / 1_000_000
    print(f"  Estimated cost: ${est_cost:.3f}")

    if dry_run:
        print(f"  [DRY RUN] Would submit {len(reqs)} requests. Exiting.")
        return

    # Submit batch
    batch_id = submit_batch(reqs, f"phase{phase_num}_{label}")
    ph["active_batch_id"] = batch_id
    ph["last_run"] = datetime.now().isoformat()
    save_state(state)

    # Poll
    results = poll_batch(batch_id, label)
    if not results:
        print(f"  ❌ Phase {phase_num} failed — check batch {batch_id}")
        return

    # Apply
    if phase_num == 1:
        written = apply_phase1_results(results)
    elif phase_num == 2:
        written = apply_phase2_results(results)
    else:
        written = apply_phase3_results(results)

    # Update state
    done_ids = [r["custom_id"].split("_", 1)[1] for r in results if not r.get("error")]
    ph["done_ulids"].extend(done_ids)
    ph["total_written"] += written
    ph["last_run"] = datetime.now().isoformat()
    ph.pop("active_batch_id", None)
    save_state(state)

    print(f"\n  ✅ Phase {phase_num} complete — {written} obs updated")


def main():
    parser = argparse.ArgumentParser(description="Enrich obs with OpenAI")
    parser.add_argument("--phase",   type=int, choices=[1, 2, 3])
    parser.add_argument("--all",     action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status",  action="store_true")
    args = parser.parse_args()

    if args.status:
        print_status()
        return

    if not args.phase and not args.all:
        parser.print_help()
        return

    print(f"\n🔬 OGZ Obs Enricher — OpenAI Batch API")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"   Model: {MODEL}")

    state    = load_state()
    obs_list = load_all_obs()
    print(f"   Loaded {len(obs_list)} obs files")

    phases_to_run = [args.phase] if args.phase else [1, 2, 3]
    for ph in phases_to_run:
        run_phase(ph, obs_list, state, args.dry_run)

    print(f"\n✅ All done. Results written to obs files.")


if __name__ == "__main__":
    main()
