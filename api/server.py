#!/usr/bin/env python3
"""
OGZ Content Intelligence API

Endpoints:
  POST /api/score       — Score a content idea 0-100 (heuristic + ML)
  POST /api/brief       — Generate a production brief (data-driven)
  POST /api/brief/ai    — AI-written Arabic creative brief (LLM-powered)
  POST /api/recommend   — Recommend what to post next
  POST /api/search      — Semantic search across observations
  POST /api/calendar    — Generate a month's content calendar
  POST /api/caption     — Generate Arabic captions
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
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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


REPO = Path(__file__).parent.parent
STATIC_DIR = Path(__file__).parent / "static"


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/proof/{ulid}")
def proof(ulid: str):
    """Verifiable proof for any observation — real metrics + clickable Instagram URL."""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT observation_ulid, account_handle_normalized, sector, content_type,
            engagement_potential, likes_count, comments_count, engagement_total,
            content_ref, quality_assessment, pattern_matches,
            emotion_primary, occasion, content_pillar
        FROM observations WHERE observation_ulid = %s
    """, (ulid,))
    obs = cur.fetchone()
    cur.close(); conn.close()

    if not obs:
        raise HTTPException(status_code=404, detail=f"Observation {ulid} not found")

    cr = obs.get("content_ref", {}) if isinstance(obs.get("content_ref"), dict) else json.loads(obs.get("content_ref", "{}"))
    qa = obs.get("quality_assessment", {}) if isinstance(obs.get("quality_assessment"), dict) else json.loads(obs.get("quality_assessment", "{}"))
    pm = obs.get("pattern_matches", []) if isinstance(obs.get("pattern_matches"), list) else json.loads(obs.get("pattern_matches", "[]"))

    likes = obs.get("likes_count", 0) or cr.get("likes_count", 0) or 0
    comments = obs.get("comments_count", 0) or cr.get("comments_count", 0) or 0
    source_url = cr.get("source_url", "")

    has_real_metrics = likes > 0 or comments > 0

    return {
        "observation_ulid": ulid,
        "account": obs.get("account_handle_normalized", ""),
        "sector": obs.get("sector", ""),
        "instagram_url": source_url,
        "verify": f"Click to verify: {source_url}" if source_url else "No URL available",
        "real_metrics": {
            "likes": likes,
            "comments": comments,
            "total": likes + comments,
            "has_real_data": has_real_metrics,
            "source": "instagram via Apify" if has_real_metrics else "AI-estimated (not verified)",
        },
        "engagement": {
            "tier": obs.get("engagement_potential", ""),
            "method": qa.get("engagement_method", "ai_estimated" if not has_real_metrics else "real_metrics"),
        },
        "content": {
            "type": obs.get("content_type", ""),
            "emotion": obs.get("emotion_primary", ""),
            "pillar": obs.get("content_pillar", ""),
            "occasion": obs.get("occasion", ""),
        },
        "ai_classification": {
            "patterns": [p.get("pattern_slug", "") if isinstance(p, dict) else p for p in pm[:3]],
            "confidence_note": "AI-classified by GPT-4o-mini — patterns and emotions are estimates, not verified facts",
        },
        "trust_level": "verified" if has_real_metrics else "estimated",
    }


@app.get("/presentation")
def presentation():
    return FileResponse(STATIC_DIR / "presentation.html")


@app.get("/report")
def latest_report():
    """Serve the latest intelligence report."""
    reports_dir = REPO / "logs" / "reports"
    if not reports_dir.exists():
        raise HTTPException(status_code=404, detail="No reports generated yet")
    reports = sorted(reports_dir.glob("*.html"), reverse=True)
    if not reports:
        raise HTTPException(status_code=404, detail="No reports found")
    return FileResponse(reports[0])


@app.post("/api/report/generate")
def generate_report():
    """Generate a fresh intelligence report."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "scripts/generate_weekly_report.py"],
        capture_output=True, text=True, timeout=30, cwd=str(REPO)
    )
    if result.returncode == 0:
        return {"status": "generated", "output": result.stdout.strip()}
    raise HTTPException(status_code=500, detail=result.stderr[:500])


@app.get("/api/intelligence")
def get_intelligence(sector: str = None):
    """The Holy Book — complete intelligence layer. Every agent reads this."""
    intel_path = REPO / "11_who_to_learn_from" / "intelligence_layer.json"
    if not intel_path.exists():
        raise HTTPException(status_code=404, detail="Intelligence layer not built yet")
    data = json.loads(intel_path.read_text())
    if sector:
        playbook = data.get("sector_playbooks", {}).get(sector)
        if not playbook:
            raise HTTPException(status_code=404, detail=f"No playbook for sector: {sector}")
        return {
            "sector": sector,
            "playbook": playbook,
            "universal_rules": data["universal_rules"],
            "anti_patterns": data["anti_patterns"][:10],
            "visual_rules": [r for r in data["visual_rules"] if r["type"] == "preferred"],
            "caption_rules": data["caption_rules"],
            "occasion_rules": data["occasion_rules"],
            "format_rules": data["format_rules"],
        }
    return data


@app.get("/api/intelligence/rules/{sector}")
def get_sector_rules(sector: str):
    """Get just the rules for one sector — what to ALWAYS do and NEVER do."""
    intel_path = REPO / "11_who_to_learn_from" / "intelligence_layer.json"
    data = json.loads(intel_path.read_text())
    pb = data.get("sector_playbooks", {}).get(sector, {})
    return {
        "sector": sector,
        "must_use": pb.get("must_use", []),
        "never_use": pb.get("never_use", []),
        "winning_formulas": pb.get("winning_formulas", []),
        "visual_dna": pb.get("visual_dna", []),
        "universal_always": data["universal_rules"],
        "universal_never": data["anti_patterns"][:10],
    }


class ContextRequest(BaseModel):
    brand: str = ""
    sector: str = ""
    occasion: str = "evergreen"


@app.post("/api/intelligence/context")
def intelligence_context(req: ContextRequest):
    """Thin brain context — real data for LLM prompts.
    Provides cultural guardrails, real metrics, brand voice. No scores or prescriptions."""
    sys.path.insert(0, str(REPO / "scripts"))
    from build_agent_context import build_context
    brand = req.brand or req.sector
    ctx, tokens = build_context(brand, req.occasion)
    return {
        "context_block": ctx,
        "token_count": tokens,
        "brand": req.brand,
        "occasion": req.occasion,
        "philosophy": "Context only. No scores. No prescriptions. Let the LLM be creative.",
    }


def get_db():
    return psycopg2.connect(DB_URL)


def get_openai_key():
    env_path = Path.home() / ".abraham_env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "OPENAI_API_KEY" in line and "=" in line:
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


# Load ML model at startup
_ml_model = None
_ml_config = None
try:
    import pickle, numpy as np
    model_path = REPO / "models" / "engagement_model.pkl"
    config_path = REPO / "models" / "engagement_features.json"
    if model_path.exists():
        with open(model_path, "rb") as f:
            _ml_model = pickle.load(f)
        with open(config_path) as f:
            _ml_config = json.load(f)
except Exception:
    pass


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

class AIBriefRequest(BaseModel):
    sector: str
    brand_name: str = "Brand"
    occasion: str = "evergreen"
    content_type: str = "carousel_slide"
    language: str = "arabic"

class CalendarRequest(BaseModel):
    sector: str
    month: int = 0
    year: int = 0
    posts_per_week: int = 3

class CaptionRequest(BaseModel):
    sector: str
    pattern: str
    occasion: str = "evergreen"
    tone: str = "inviting"
    language: str = "arabic"
    count: int = 3


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
        "ml_score": _ml_predict(req) if _ml_model else None,
        "data_points": ct_row["total"],
    }


def _ml_predict(req: ScoreRequest) -> dict | None:
    """Run ML model prediction if available."""
    if not _ml_model or not _ml_config:
        return None
    try:
        import numpy as np
        cat_features = _ml_config["cat_features"]
        bool_features = _ml_config["bool_features"]
        encoders = _ml_config["encoders"]

        vals = {
            "content_type": req.content_type, "sector": req.sector,
            "occasion": req.occasion, "lighting": req.lighting or "unknown",
            "setting": req.setting or "unknown", "dialect": "unknown",
            "caption_length": "medium",
            "pattern_0": req.patterns[0] if req.patterns else "none",
            "pattern_1": req.patterns[1] if len(req.patterns) > 1 else "none",
            "pattern_2": req.patterns[2] if len(req.patterns) > 2 else "none",
            "has_emoji": False, "human_presence": False,
        }
        x_parts = []
        for feat in cat_features:
            classes = encoders[feat]["classes"]
            val = vals.get(feat, "unknown")
            idx = classes.index(val) if val in classes else classes.index("__unknown__") if "__unknown__" in classes else 0
            x_parts.append(idx)
        for feat in bool_features:
            x_parts.append(int(vals.get(feat, False)))

        x = np.array(x_parts).reshape(1, -1)
        prob = float(_ml_model.predict_proba(x)[0][1])
        return {"high_probability": round(prob * 100), "prediction": "high" if prob > 0.5 else "not_high"}
    except Exception:
        return None


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
                "account": entry.get("handle", entry.get("account", "")),
                "sector": entry.get("sector", ""),
                "content_type": entry.get("content_type", ""),
                "source_url": entry.get("source_url", ""),
                "similarity": round(float(scores[idx]), 4),
                "caption_preview": entry.get("text_snippet", entry.get("caption", ""))[:150],
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
# 7. AI BRIEF WRITER — POST /api/brief/ai
# ═══════════════════════════════════════════════════════════

@app.post("/api/brief/ai")
def ai_brief(req: AIBriefRequest):
    """Generate a full Arabic creative brief using LLM + data insights."""
    api_key = get_openai_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    # Get top winning formulas from DB
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT pm->>'pattern_slug' as pattern,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct,
            count(*) as obs
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        WHERE sector = %s
        GROUP BY pm->>'pattern_slug' HAVING count(*) >= 5
        ORDER BY high_pct DESC LIMIT 5
    """, (req.sector,))
    top_patterns = cur.fetchall()

    cur.execute("""
        SELECT visual_observations->>'lighting' as lighting,
               visual_observations->>'setting' as setting,
               round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct
        FROM observations WHERE sector = %s
        GROUP BY 1, 2 HAVING count(*) >= 5
        ORDER BY high_pct DESC LIMIT 3
    """, (req.sector,))
    top_visuals = cur.fetchall()

    cur.execute("""
        SELECT voice_observations->>'notable_phrases' as phrases
        FROM observations
        WHERE sector = %s AND engagement_potential = 'high'
          AND voice_observations->>'notable_phrases' IS NOT NULL
        ORDER BY random() LIMIT 5
    """, (req.sector,))
    sample_phrases = [r["phrases"][:100] for r in cur.fetchall()]
    cur.close(); conn.close()

    import openai
    client = openai.OpenAI(api_key=api_key)

    patterns_text = "\n".join(f"- {p['pattern']} ({p['high_pct']}% high engagement, {p['obs']} examples)" for p in top_patterns)
    visuals_text = "\n".join(f"- {v['lighting']} + {v['setting']} = {v['high_pct']}% high" for v in top_visuals)

    prompt = f"""You are a Saudi creative director writing a production brief for {req.brand_name} in the {req.sector} sector.

Occasion: {req.occasion}
Content type: {req.content_type}
Language: {req.language}

DATA FROM 4315 BENCHMARK OBSERVATIONS:
Top performing patterns in this sector:
{patterns_text}

Best visual combinations:
{visuals_text}

Sample high-engagement Arabic phrases from this sector:
{chr(10).join(sample_phrases)}

Write a complete production brief in {req.language} with:
1. CONCEPT: One-line creative concept
2. VISUAL DIRECTION: Specific lighting, setting, composition instructions
3. CAPTION: 3 Arabic caption options (different tones: inviting, proud, excited)
4. HASHTAGS: 5 recommended Arabic hashtags
5. SHOT LIST: 3-5 specific shots to capture
6. DO NOT: 2-3 things to avoid based on low-performing patterns

Keep it practical and specific. This is for a production team."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )

    return {
        "brief": resp.choices[0].message.content,
        "data_backing": {
            "top_patterns": top_patterns,
            "top_visuals": top_visuals,
        },
        "generated_at": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════
# 8. CONTENT CALENDAR — POST /api/calendar
# ═══════════════════════════════════════════════════════════

@app.post("/api/calendar")
def content_calendar(req: CalendarRequest):
    """Generate a month's content calendar based on winning formulas + occasions."""
    import calendar as cal
    now = datetime.now()
    month = req.month or now.month
    year = req.year or now.year

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get top formulas
    cur.execute("""
        SELECT content_type, pm->>'pattern_slug' as pattern,
            round(100.0 * count(*) FILTER (WHERE engagement_potential = 'high') / count(*)) as high_pct,
            count(*) as obs
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        WHERE sector = %s
        GROUP BY content_type, pm->>'pattern_slug'
        HAVING count(*) >= 3
        ORDER BY high_pct DESC, obs DESC LIMIT 20
    """, (req.sector,))
    formulas = cur.fetchall()
    cur.close(); conn.close()

    # Map month to occasion
    occasion_map = {
        1: "evergreen", 2: "founding_day", 3: "ramadan", 4: "ramadan",
        5: "eid_al_fitr", 6: "evergreen", 7: "hajj_season", 8: "evergreen",
        9: "national_day", 10: "riyadh_season", 11: "riyadh_season", 12: "jeddah_season",
    }
    primary_occasion = occasion_map.get(month, "evergreen")

    # Generate calendar entries
    num_days = cal.monthrange(year, month)[1]
    posts_per_week = req.posts_per_week
    post_days = []
    # Distribute posts across the month (Sun/Tue/Thu pattern — best engagement days)
    preferred_weekdays = [6, 1, 3]  # Sun, Tue, Thu
    for day in range(1, num_days + 1):
        dt = datetime(year, month, day)
        if dt.weekday() in preferred_weekdays:
            post_days.append(day)

    entries = []
    for i, day in enumerate(post_days[:posts_per_week * 4]):
        formula = formulas[i % len(formulas)] if formulas else {"content_type": "image", "pattern": "product_hero", "high_pct": 30}
        occasion = primary_occasion if i % 3 == 0 else "evergreen"
        entries.append({
            "date": f"{year}-{month:02d}-{day:02d}",
            "day_of_week": datetime(year, month, day).strftime("%A"),
            "content_type": formula["content_type"],
            "pattern": formula["pattern"],
            "occasion": occasion,
            "expected_engagement": formula["high_pct"],
        })

    return {
        "sector": req.sector,
        "month": f"{year}-{month:02d}",
        "primary_occasion": primary_occasion,
        "total_posts": len(entries),
        "calendar": entries,
    }


# ═══════════════════════════════════════════════════════════
# 9. ARABIC CAPTION GENERATOR — POST /api/caption
# ═══════════════════════════════════════════════════════════

@app.post("/api/caption")
def generate_caption(req: CaptionRequest):
    """Generate Arabic captions based on high-engagement patterns."""
    api_key = get_openai_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Get sample high-engagement captions for this pattern + sector
    cur.execute("""
        SELECT voice_observations->>'caption_text' as caption,
               voice_observations->>'dialect_detected' as dialect
        FROM observations, jsonb_array_elements(pattern_matches) as pm
        WHERE pm->>'pattern_slug' = %s AND sector = %s
          AND engagement_potential = 'high'
          AND length(voice_observations->>'caption_text') > 20
        ORDER BY random() LIMIT 5
    """, (req.pattern, req.sector))
    samples = cur.fetchall()
    cur.close(); conn.close()

    samples_text = "\n".join(f"- {s['caption'][:200]}" for s in samples if s["caption"])

    import openai
    client = openai.OpenAI(api_key=api_key)

    prompt = f"""You are a Saudi social media copywriter. Generate {req.count} Arabic captions for Instagram.

Sector: {req.sector}
Pattern: {req.pattern}
Occasion: {req.occasion}
Tone: {req.tone}
Language: {req.language}

Here are examples of HIGH-ENGAGEMENT captions from this sector and pattern:
{samples_text}

Write {req.count} new captions that:
1. Match the {req.tone} tone
2. Are written in Gulf Arabic dialect (not formal MSA)
3. Include 1-2 relevant emojis
4. Are 50-200 characters (the sweet spot for engagement)
5. End with a soft call-to-action (question, invitation, or community statement)
6. Feel natural for Saudi Instagram, not translated

Return ONLY the captions, one per line, numbered."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )

    captions = resp.choices[0].message.content.strip().split("\n")
    captions = [c.strip() for c in captions if c.strip() and not c.strip().startswith("---")]

    return {
        "captions": captions,
        "pattern": req.pattern,
        "sector": req.sector,
        "tone": req.tone,
        "samples_used": len(samples),
        "generated_at": datetime.now().isoformat(),
    }


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
