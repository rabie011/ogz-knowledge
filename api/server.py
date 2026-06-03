#!/usr/bin/env python3
"""
OGZ Content Intelligence API

Endpoints:
  POST /api/score       — Score a content idea 0-100
  POST /api/brief       — Generate a production brief
  POST /api/recommend   — Recommend what to post next
  POST /api/search      — Semantic search across observations
  GET  /api/benchmark/{sector} — Sector benchmark report
  GET  /api/patterns/{sector}  — Top patterns for a sector
  GET  /api/health      — API health check

Run:
  cd ~/Desktop/ogz-knowledge && python3 -m uvicorn api.server:app --port 4100 --reload
"""
from __future__ import annotations
import json, os, sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import psycopg2
import psycopg2.extras

DB_URL = os.environ.get("DATABASE_URL", "postgresql://ogz:ogz_local_dev@localhost:5432/ogz_knowledge")

app = FastAPI(
    title="OGZ Content Intelligence",
    description="AI-powered content scoring, brief generation, and recommendations from 4315 Saudi benchmark observations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    return psycopg2.connect(DB_URL)


# ═══════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════

class ScoreRequest(BaseModel):
    sector: str
    content_type: str
    patterns: list[str] = []
    occasion: str = "evergreen"
    lighting: Optional[str] = None
    setting: Optional[str] = None

class BriefRequest(BaseModel):
    sector: str
    occasion: str = "evergreen"
    content_type: Optional[str] = None
    count: int = 3

class RecommendRequest(BaseModel):
    sector: str
    exclude_patterns: list[str] = []
    occasion: Optional[str] = None
    count: int = 5

class SearchRequest(BaseModel):
    query: str
    sector: Optional[str] = None
    top_n: int = 10


# ═══════════════════════════════════════════════════════════
# 1. CONTENT SCORER — POST /api/score
# ═══════════════════════════════════════════════════════════

@app.post("/api/score")
def score_content(req: ScoreRequest):
    """Score a content idea 0-100 based on historical engagement data."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Base score from content_type × sector
    cur.execute("""
        SELECT count(*) as total,
               count(*) FILTER (WHERE engagement_potential = 'high') as high
        FROM observations
        WHERE sector = %s AND content_type = %s
    """, (req.sector, req.content_type))
    ct_row = cur.fetchone()
    ct_score = (ct_row["high"] / ct_row["total"] * 100) if ct_row["total"] > 0 else 25

    # Pattern score (average of matched patterns)
    pattern_scores = []
    for slug in req.patterns:
        cur.execute("""
            SELECT count(*) as total,
                   count(*) FILTER (WHERE engagement_potential = 'high') as high
            FROM observations, jsonb_array_elements(pattern_matches) as pm
            WHERE pm->>'pattern_slug' = %s AND sector = %s
        """, (slug, req.sector))
        row = cur.fetchone()
        if row["total"] >= 3:
            pattern_scores.append(row["high"] / row["total"] * 100)
    pattern_score = sum(pattern_scores) / len(pattern_scores) if pattern_scores else ct_score

    # Occasion boost
    cur.execute("""
        SELECT count(*) as total,
               count(*) FILTER (WHERE engagement_potential = 'high') as high
        FROM observations
        WHERE occasion = %s AND sector = %s
    """, (req.occasion, req.sector))
    occ_row = cur.fetchone()
    occasion_score = (occ_row["high"] / occ_row["total"] * 100) if occ_row["total"] >= 3 else 30

    # Visual boost
    visual_boost = 0
    if req.lighting and req.setting:
        cur.execute("""
            SELECT count(*) as total,
                   count(*) FILTER (WHERE engagement_potential = 'high') as high
            FROM observations
            WHERE visual_observations->>'lighting' = %s
              AND visual_observations->>'setting' = %s
              AND sector = %s
        """, (req.lighting, req.setting, req.sector))
        vis_row = cur.fetchone()
        if vis_row["total"] >= 5:
            visual_boost = (vis_row["high"] / vis_row["total"] * 100) - 30

    # Weighted final score
    final = round(0.3 * ct_score + 0.4 * pattern_score + 0.15 * occasion_score + 0.15 * max(0, visual_boost + 30))
    final = max(0, min(100, final))

    cur.close()
    conn.close()

    return {
        "score": final,
        "breakdown": {
            "content_type_score": round(ct_score),
            "pattern_score": round(pattern_score),
            "occasion_score": round(occasion_score),
            "visual_boost": round(visual_boost),
        },
        "interpretation": (
            "Excellent — strong historical engagement" if final >= 75 else
            "Good — above average engagement expected" if final >= 50 else
            "Moderate — consider adjusting patterns or format" if final >= 30 else
            "Weak — high risk of low engagement"
        ),
        "data_points": ct_row["total"],
    }


# ═══════════════════════════════════════════════════════════
# 2. BRIEF GENERATOR — POST /api/brief
# ═══════════════════════════════════════════════════════════

@app.post("/api/brief")
def generate_brief(req: BriefRequest):
    """Generate production briefs based on winning formulas."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Find top winning formulas for this sector + occasion
    cur.execute("""
        WITH formulas AS (
            SELECT content_type, occasion, pm->>'pattern_slug' as pattern,
                count(*) as obs_count,
                round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
            FROM observations, jsonb_array_elements(pattern_matches) as pm
            WHERE sector = %s AND (occasion = %s OR %s = 'any')
            GROUP BY content_type, occasion, pm->>'pattern_slug'
            HAVING count(*) >= 3
        )
        SELECT * FROM formulas ORDER BY high_pct DESC, obs_count DESC LIMIT %s
    """, (req.sector, req.occasion, req.occasion, req.count * 2))
    formulas = cur.fetchall()

    # Get visual DNA for top formulas
    briefs = []
    seen = set()
    for f in formulas:
        key = f"{f['content_type']}_{f['pattern']}"
        if key in seen:
            continue
        seen.add(key)

        cur.execute("""
            SELECT visual_observations->>'lighting' as lighting,
                   visual_observations->>'setting' as setting,
                   count(*) as cnt
            FROM observations, jsonb_array_elements(pattern_matches) as pm
            WHERE pm->>'pattern_slug' = %s AND sector = %s AND engagement_potential = 'high'
            GROUP BY 1, 2
            ORDER BY cnt DESC LIMIT 1
        """, (f["pattern"], req.sector))
        vis = cur.fetchone()

        # Get sample caption style
        cur.execute("""
            SELECT voice_observations->>'dialect_detected' as dialect,
                   length(voice_observations->>'caption_text') as caption_len
            FROM observations, jsonb_array_elements(pattern_matches) as pm
            WHERE pm->>'pattern_slug' = %s AND sector = %s AND engagement_potential = 'high'
              AND voice_observations->>'caption_text' IS NOT NULL
            ORDER BY random() LIMIT 1
        """, (f["pattern"], req.sector))
        cap = cur.fetchone()

        briefs.append({
            "content_type": f["content_type"],
            "pattern": f["pattern"],
            "occasion": f["occasion"],
            "engagement_rate": f["high_pct"],
            "data_points": f["obs_count"],
            "visual_direction": {
                "lighting": vis["lighting"] if vis else None,
                "setting": vis["setting"] if vis else None,
            },
            "caption_guidance": {
                "dialect": cap["dialect"] if cap else None,
                "recommended_length": "medium (50-200 chars)" if cap and cap["caption_len"] and cap["caption_len"] < 200 else "long (200-500 chars)",
            },
        })
        if len(briefs) >= req.count:
            break

    cur.close()
    conn.close()

    return {
        "sector": req.sector,
        "occasion": req.occasion,
        "briefs": briefs,
        "generated_at": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════
# 3. WHAT TO POST NEXT — POST /api/recommend
# ═══════════════════════════════════════════════════════════

@app.post("/api/recommend")
def recommend_content(req: RecommendRequest):
    """Recommend what to post next based on sector benchmarks and gaps."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Top patterns by engagement in this sector
    exclude_clause = ""
    params = [req.sector]
    if req.exclude_patterns:
        exclude_clause = "AND pm->>'pattern_slug' NOT IN %s"
        params.append(tuple(req.exclude_patterns))

    cur.execute(f"""
        SELECT pm->>'pattern_slug' as pattern, content_type,
            count(*) as total,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        WHERE sector = %s {exclude_clause}
        GROUP BY pm->>'pattern_slug', content_type
        HAVING count(*) >= 5
        ORDER BY high_pct DESC, total DESC
        LIMIT %s
    """, params + [req.count])
    recs = cur.fetchall()

    # Get current occasion (simple calendar logic)
    month = datetime.now().month
    if month == 3 or month == 4:
        current_occasion = "ramadan"
    elif month == 9:
        current_occasion = "national_day"
    elif month == 2:
        current_occasion = "founding_day"
    else:
        current_occasion = "evergreen"

    # Underserved content types in this sector
    cur.execute("""
        SELECT content_type, count(*) as cnt
        FROM observations WHERE sector = %s
        GROUP BY content_type ORDER BY cnt ASC LIMIT 2
    """, (req.sector,))
    gaps = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "sector": req.sector,
        "current_occasion": current_occasion,
        "recommendations": [
            {
                "pattern": r["pattern"],
                "content_type": r["content_type"],
                "engagement_rate": r["high_pct"],
                "confidence": "high" if r["total"] >= 20 else "medium" if r["total"] >= 10 else "low",
                "data_points": r["total"],
            }
            for r in recs
        ],
        "content_gaps": [
            {"content_type": g["content_type"], "current_obs": g["cnt"], "opportunity": "underserved — more content here could differentiate"}
            for g in gaps
        ],
    }


# ═══════════════════════════════════════════════════════════
# 4. SEMANTIC SEARCH — POST /api/search
# ═══════════════════════════════════════════════════════════

@app.post("/api/search")
def semantic_search(req: SearchRequest):
    """Search observations by natural language similarity."""
    try:
        import openai
        import numpy as np

        env_path = Path.home() / ".abraham_env"
        api_key = None
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if "OPENAI_API_KEY" in line and "=" in line:
                    api_key = line.split("=", 1)[1].strip().strip('"').strip("'")

        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not found")

        client = openai.OpenAI(api_key=api_key)

        # Embed query
        resp = client.embeddings.create(model="text-embedding-3-small", input=req.query)
        query_vec = np.array(resp.data[0].embedding, dtype=np.float32)

        # Load index
        repo = Path(__file__).parent.parent
        index_path = repo / "logs" / "obs_search_index.json"
        emb_path = repo / "logs" / "obs_embeddings.npy"

        with open(index_path) as f:
            index = json.load(f)
        embeddings = np.load(emb_path)

        # Cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1
        normed = embeddings / norms
        query_normed = query_vec / (np.linalg.norm(query_vec) or 1)
        scores = normed @ query_normed

        # Filter by sector if specified
        top_indices = np.argsort(scores)[::-1]
        results = []
        for idx in top_indices:
            entry = index[idx]
            if req.sector and entry.get("sector") != req.sector:
                continue
            results.append({
                "observation_ulid": entry.get("ulid", ""),
                "account": entry.get("account", ""),
                "sector": entry.get("sector", ""),
                "content_type": entry.get("content_type", ""),
                "engagement": entry.get("engagement", ""),
                "similarity": round(float(scores[idx]), 4),
                "caption_preview": entry.get("caption", "")[:150],
            })
            if len(results) >= req.top_n:
                break

        return {"query": req.query, "results": results}

    except ImportError:
        raise HTTPException(status_code=500, detail="openai/numpy not installed")


# ═══════════════════════════════════════════════════════════
# 5. SECTOR BENCHMARK — GET /api/benchmark/{sector}
# ═══════════════════════════════════════════════════════════

@app.get("/api/benchmark/{sector}")
def sector_benchmark(sector: str):
    """Get sector benchmark report with engagement rates by content type, top patterns, and visual DNA."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Content type breakdown
    cur.execute("""
        SELECT content_type, count(*) as total,
            count(*) FILTER (WHERE engagement_potential = 'high') as high,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations WHERE sector = %s
        GROUP BY content_type ORDER BY high_pct DESC
    """, (sector,))
    content_types = cur.fetchall()

    # Top patterns
    cur.execute("""
        SELECT pm->>'pattern_slug' as pattern, count(*) as total,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        WHERE sector = %s
        GROUP BY pm->>'pattern_slug'
        HAVING count(*) >= 5
        ORDER BY high_pct DESC LIMIT 10
    """, (sector,))
    top_patterns = cur.fetchall()

    # Visual DNA
    cur.execute("""
        SELECT visual_observations->>'lighting' as lighting,
               visual_observations->>'setting' as setting,
               count(*) as total,
               round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations WHERE sector = %s
        GROUP BY 1, 2
        HAVING count(*) >= 5
        ORDER BY high_pct DESC LIMIT 5
    """, (sector,))
    visual_dna = cur.fetchall()

    # Occasion performance
    cur.execute("""
        SELECT occasion, count(*) as total,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations WHERE sector = %s AND occasion IS NOT NULL
        GROUP BY occasion HAVING count(*) >= 3
        ORDER BY high_pct DESC
    """, (sector,))
    occasions = cur.fetchall()

    # Account leaderboard
    cur.execute("""
        SELECT account_handle_normalized as account, count(*) as total,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations WHERE sector = %s
        GROUP BY account_handle_normalized
        HAVING count(*) >= 10
        ORDER BY high_pct DESC
    """, (sector,))
    accounts = cur.fetchall()

    total_obs = sum(ct["total"] for ct in content_types)
    total_high = sum(ct["high"] for ct in content_types)

    cur.close()
    conn.close()

    return {
        "sector": sector,
        "total_observations": total_obs,
        "overall_high_engagement_pct": round(100 * total_high / total_obs) if total_obs else 0,
        "content_types": content_types,
        "top_patterns": top_patterns,
        "visual_dna": visual_dna,
        "occasions": occasions,
        "account_leaderboard": accounts,
    }


# ═══════════════════════════════════════════════════════════
# 6. PATTERNS — GET /api/patterns/{sector}
# ═══════════════════════════════════════════════════════════

@app.get("/api/patterns/{sector}")
def sector_patterns(sector: str, min_obs: int = 5):
    """Get all patterns for a sector with engagement rates."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT pm->>'pattern_slug' as pattern, content_type,
            count(*) as total,
            count(*) FILTER (WHERE engagement_potential = 'high') as high,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        WHERE sector = %s
        GROUP BY pm->>'pattern_slug', content_type
        HAVING count(*) >= %s
        ORDER BY high_pct DESC, total DESC
    """, (sector, min_obs))
    patterns = cur.fetchall()

    cur.close()
    conn.close()

    return {"sector": sector, "patterns": patterns}


# ═══════════════════════════════════════════════════════════
# HEALTH — GET /api/health
# ═══════════════════════════════════════════════════════════

@app.get("/api/health")
def health():
    """API health check with database stats."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM observations")
        obs = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM account_patterns")
        patterns = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM chains")
        chains = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {
            "status": "healthy",
            "database": "connected",
            "observations": obs,
            "patterns": patterns,
            "chains": chains,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
