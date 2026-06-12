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

from fastapi import FastAPI, HTTPException, Request
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

_intel_path = REPO / "11_who_to_learn_from" / "intelligence_layer.json"
intel: dict = json.loads(_intel_path.read_text()) if _intel_path.exists() else {}

# Arabic display names — used in prompts and cross-compare UI
BRAND_AR: dict = {
    'albaiik': 'البيك', 'albaik': 'البيك',
    'barns': 'بارنز', 'barnscoffee': 'بارنز',
    'almarai': 'المراعي',
    'roshn': 'روشن', 'roshnksa': 'روشن',
    'panda': 'بنده', 'pandaksa': 'بنده', 'pandasaudi': 'بنده',
    'starbucks': 'ستاربكس', 'starbucksar': 'ستاربكس',
    'jarir': 'جرير', 'jarirbooks': 'جرير',
    'aljazira_capital': 'الجزيرة كابيتال', 'aljaziracapital': 'الجزيرة كابيتال',
    'nivea': 'نيفيا', 'niveaarabia': 'نيفيا',
    'max_fashion': 'ماكس فاشون', 'maxfashion': 'ماكس فاشون', 'maxfashionmena': 'ماكس فاشون',
    'nhc': 'هيئة الإسكان', 'nhcksa': 'هيئة الإسكان',
    'sauditelecom': 'STC', 'stc': 'STC',
    'mobily': 'موبايلي',
    'tamimi': 'التميمي', 'tamimimarkets': 'التميمي',
    'extra': 'إكسترا',
    'xcite': 'اكسايت',
    'noon': 'نون',
    'namshi': 'نمشي',
    'ounass': 'أوناس',
    'mikyajy': 'مكياجي', 'mkj': 'مكياجي',
    'mcdonaldsksa': 'ماكدونالدز',
    'shawarmersa': 'شاورمر',
    'alromansiahksa': 'الرومانسية',
    'kuduksa': 'كودو',
    'niceonesa': 'نايس ون',
    'elixirbunn': 'إليكسير',
    'ajmalperfumes': 'عجمل',
    'bathandbodyworksarabia': 'باث آند بودي ووركس',
    'altazaj_fakieh': 'الطازج فاكيه',
    'riyadhfood': 'الرياض فود',
    'herfyfsc': 'هرفي',
    'hashibasha': 'هاشي باشا',
    'aseeb.najd': 'عصيب نجد',
    'mumzworld': 'مامز وورلد',
    'kiabiksa': 'كيابي',
    'prettynature.official': 'بريتي نيتشر',
    'asteribeautysa': 'أستيري',
    'pizzahutsaudi': 'بيتزا هت',
}


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
        sf = data.get("sector_facts", {}).get(sector)
        if not sf:
            raise HTTPException(status_code=404, detail=f"No data for sector: {sector}")
        aqr = data.get("arabic_quality_rules", {})
        return {
            "sector": sector,
            "sector_facts": sf,
            "cultural_guardrails": data.get("cultural_guardrails", {}),
            "overused_phrases_avoid": aqr.get("overused_phrases_to_avoid", []),
            "saudi_markers": aqr.get("saudi_markers", []),
            "caption_intelligence": data.get("caption_intelligence", {}),
            "visual_intelligence": data.get("visual_intelligence", {}),
            "occasion_calendar": data.get("occasion_calendar", {}),
            "brand_profiles": {k: v for k, v in data.get("brand_profiles", {}).items()
                               if v.get("sector") == sector},
        }
    return data


@app.get("/api/intelligence/rules/{sector}")
def get_sector_rules(sector: str):
    """Get actionable rules for one sector — always/never, cultural guardrails, brand voice."""
    intel_path = REPO / "11_who_to_learn_from" / "intelligence_layer.json"
    data = json.loads(intel_path.read_text())
    sf = data.get("sector_facts", {}).get(sector, {})
    cg = data.get("cultural_guardrails", {})
    aqr = data.get("arabic_quality_rules", {})
    brand_profiles = {k: v for k, v in data.get("brand_profiles", {}).items()
                      if v.get("sector") == sector}
    return {
        "sector": sector,
        "sector_facts": sf,
        "always_use": aqr.get("saudi_markers", []),
        "overused_avoid": aqr.get("overused_phrases_to_avoid", []),
        "cultural_forbidden": {
            "props": cg.get("forbidden_props", []),
            "behaviors": cg.get("forbidden_behaviors", []),
            "visuals": cg.get("forbidden_visuals", []),
        },
        "brand_profiles": brand_profiles,
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
    """Search observations by natural language similarity using pgvector."""
    try:
        import openai

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
        query_vec = resp.data[0].embedding
        vec_str = f"[{','.join(str(x) for x in query_vec)}]"

        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Use pgvector cosine similarity — filters work natively in SQL
        sector_filter = "AND sector = %(sector)s" if req.sector else ""
        cur.execute(f"""
            SELECT observation_ulid, account_handle_normalized, sector, content_type,
                   voice_observations->>'caption_text' as caption_text,
                   content_ref->>'source_url' as source_url,
                   1 - (embedding <=> %(vec)s::vector) as similarity
            FROM observations
            WHERE embedding IS NOT NULL
            {sector_filter}
            ORDER BY embedding <=> %(vec)s::vector
            LIMIT %(limit)s
        """, {"vec": vec_str, "sector": req.sector, "limit": req.top_n})

        rows = cur.fetchall()
        cur.close()
        conn.close()

        results = [
            {
                "observation_ulid": r["observation_ulid"],
                "account": r["account_handle_normalized"],
                "sector": r["sector"],
                "content_type": r["content_type"],
                "source_url": r.get("source_url", ""),
                "similarity": round(float(r["similarity"]), 4),
                "caption_preview": (r.get("caption_text") or "")[:150],
            }
            for r in rows
        ]

        return {"query": req.query, "results": results}

    except ImportError:
        raise HTTPException(status_code=500, detail="openai not installed")


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

@app.get("/api/templates")
def get_templates(sector: str = None, occasion: str = None, tier: str = None, limit: int = 5):
    """Get scored templates from template library."""
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    tlib_path = REPO / "11_who_to_learn_from" / "template_library.json"
    if not tlib_path.exists():
        raise HTTPException(status_code=404, detail="Template library not built yet. Run: python3 scripts/build_template_library.py")
    data = json.loads(tlib_path.read_text())
    templates = data.get('templates', [])
    if sector:
        templates = [t for t in templates if t.get('sector') == sector]
    if occasion:
        templates = [t for t in templates if t.get('occasion') == occasion]
    if tier:
        templates = [t for t in templates if t.get('tier') == tier]
    # Sort: gold first
    tier_order = {'gold': 0, 'silver': 1, 'bronze': 2, 'unverified': 3, 'generated': 4}
    templates.sort(key=lambda t: tier_order.get(t.get('tier', 'generated'), 99))
    return {
        'total': len(templates),
        'returned': min(limit, len(templates)),
        'templates': templates[:limit],
    }


class CheckRequest(BaseModel):
    text: str
    brand: str = None
    occasion: str = 'evergreen'

@app.post("/api/check")
def check_content(req: CheckRequest):
    """Run quality gate checks on a caption."""
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    from lib.quality_gate import check, auto_fix
    result = check(req.text, brand=req.brand, occasion=req.occasion)
    fixed = None
    if result['fixes_needed']:
        brand_profiles = intel.get('brand_profiles', {})
        sector = brand_profiles.get(req.brand, {}).get('sector', '') if req.brand else ''
        fixed = auto_fix(req.text, brand=req.brand, sector=sector)
    return {**result, 'fixed_text': fixed}


class CreateRequest(BaseModel):
    brand: str
    product: str
    occasion: str = 'evergreen'
    language: str = 'arabic'  # 'arabic' | 'english'


def _try_create_v6(req) -> dict | None:
    """The de-poisoned generation path (doctrine). None => caller falls back to legacy."""
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        from v5_prompt import build_messages_v5
        from caption_filter import filter_options
        from scorer_v2 import pick_best, score_v2
        from humain_collector import parse_response, OCCASION_AR, MAX_CHARS
    except Exception:
        return None
    if req.language != "arabic":
        return None
    briefs = json.loads((REPO / "data" / "brief_matrix.json").read_text())
    brief = next((b for b in briefs if b["brand"] == req.brand or b.get("brand_en") == req.brand), None)
    if brief is None:
        return None
    brief = dict(brief)
    if req.occasion:
        brief["occasion"] = req.occasion
    if req.product:
        brief["product"] = req.product
    occ_ar = OCCASION_AR.get(brief.get("occasion", ""), brief.get("occasion", ""))
    # ARMOR PORT step 2 (D4): sector×occasion lens into the brief — the coffee×ramadan
    # fix reaches all 41 brands (lens moments ground the scene, kills sector-blind drift)
    try:
        _facts = json.loads((REPO / "data" / "occasion_facts.json").read_text())
        _okey = {"national_day": "saudi_national_day"}.get(brief.get("occasion", ""), brief.get("occasion", ""))
        _lens = (_facts.get(_okey, {}).get("sector_lenses") or {}).get(brief.get("sector", ""))
        if _lens and _lens.get("moments"):
            # ARMOR PORT step 5: date-hashed rotation — static [:3] fed every call
            # the same scene (template farm at scale)
            from gen_fatigue import rotate_moments as _rot
            brief["lens_moments"] = _rot(req.brand, _lens["moments"])
            brief["lens_product_role"] = _lens.get("product_role", "")
    except Exception:
        pass
    msgs = build_messages_v5(brief, occ_ar, MAX_CHARS.get(brief.get("sector", ""), 160))
    # lens injection into the user message (v5_prompt unaware of lenses — append-safe)
    if msgs and brief.get("lens_moments"):
        try:
            msgs[-1]["content"] += ("\n\nلحظات حقيقية لهذه المناسبة في هذا القطاع (المشهد يعيش داخل واحدة منها): "
                                      + " · ".join(brief["lens_moments"]))
        except Exception:
            pass
    # ARMOR PORT step 4b: G9-lite catchphrase fatigue — worn 3-grams from this
    # brand's recent generations banned in the prompt (renderer parity)
    if msgs:
        try:
            from gen_fatigue import worn_grams as _wg
            _worn = _wg(req.brand)
            if _worn:
                msgs[-1]["content"] += ("\n\nعبارات مستهلكة هذا الشهر — ممنوع تكرارها، قلها بطريقة أخرى: "
                                          + " · ".join(_worn))
        except Exception:
            pass
    if not msgs:
        return None  # no DNA -> legacy
    api_key = get_openai_key()
    if not api_key:
        return None
    import urllib.request as _ur
    body = {"model": "gpt-4o", "temperature": 0.9, "max_tokens": 800,
            "messages": msgs}
    rq = _ur.Request("https://api.openai.com/v1/chat/completions",
                     data=json.dumps(body).encode(),
                     headers={"Authorization": f"Bearer {api_key}",
                              "Content-Type": "application/json"})
    try:
        raw = json.loads(_ur.urlopen(rq, timeout=60).read())["choices"][0]["message"]["content"]
    except Exception:
        return None
    parsed = parse_response(raw)
    survivors, dropped = filter_options(parsed.get("options", {}))
    if not survivors:
        return None
    # ARMOR PORT (D4, June 12): the week's 8 laws guard the main pipeline too.
    # corpus = brief gold/exemplars (no client corpus here — G3 partially blind, honest).
    try:
        from truth_guards import apply_guards
        _corpus = " ".join([brief.get("brand", ""), brief.get("brand_en", "")]
                            + [g for g in brief.get("gold", [])][:10])
        _slot = {"occasion": brief.get("occasion")}
        _surv, _kills = apply_guards(list(survivors.values()), _corpus, _slot)
        if _surv:
            survivors = {f"g{i}": s for i, s in enumerate(_surv)}
    except ImportError:
        pass
    best, scores = pick_best(survivors, brief.get("brand_en", ""), brief.get("brand", ""))
    best_score = max(scores.values()) if scores else 50
    # ARMOR PORT step 4a: the generation log is the fatigue armor's memory
    try:
        from gen_fatigue import append_generation as _ag
        _ag(req.brand, brief.get("occasion") or "", list(survivors.values()), gen="v6")
    except Exception:
        pass
    return {
        "brand": req.brand,
        "product": req.product,
        "occasion": brief.get("occasion"),
        "content": {
            "caption": best,
            "hashtags": [w for w in (best or "").split() if w.startswith("#")],
            "options": survivors,
        },
        "quality": {
            "score": best_score,
            "confidence": "high" if best_score >= 80 else "medium" if best_score >= 60 else "low",
            "template_tier": "dna_v3_feed",
            "fixes_applied": [],
            "passed": best_score >= 60,
            "filter_dropped": list(dropped.keys()),
        },
        "creative_director": {"primary": "cd_06_feed_cloner", "technique": "feed", "scores": scores},
        "visual_chain": None,
        "proof": {"generation": "v6", "judge": "scorer_v2", "few_shot": "dna_v3+gold"},
        "context_tokens": 0,
    }



class AnglesRequest(BaseModel):
    brand: str
    occasion: str = "national_day"


@app.post("/api/angles")
def api_angles(req: AnglesRequest):
    """THE CREATIVE LINE surface (P2, June 11): truth pack -> 5 ranked angles (ideas).
    Idea-first: founder gates angles (cheap) before render (expensive). Cached if built."""
    import subprocess, sys as _sys
    m = json.loads((REPO / "data/brief_matrix.json").read_text())
    b = next((x for x in m if x.get("brand_en") == req.brand or x.get("brand") == req.brand), None)
    if not b:
        raise HTTPException(status_code=404, detail=f"brand not in matrix: {req.brand}")
    brand_en = b["brand_en"]
    cards = REPO / "data/angle_cards" / f"{brand_en}__{req.occasion}.json"
    if not cards.exists():
        env = dict(**__import__("os").environ)
        for step in (["build_truth_pack.py"], ["build_angle_cards.py"]):
            r = subprocess.run([_sys.executable, str(REPO / "scripts" / step[0]),
                                "--brand", brand_en, "--occasion", req.occasion],
                               capture_output=True, text=True, cwd=str(REPO), env=env)
            if r.returncode != 0:
                raise HTTPException(status_code=500, detail=f"{step[0]}: {(r.stderr or r.stdout)[-200:]}")
    data = json.loads(cards.read_text())
    return {"brand": req.brand, "occasion": req.occasion,
            "angles": data.get("angles", []),
            "truth_pack": json.loads((REPO / "data/truth_packs" / f"{brand_en}__{req.occasion}.json").read_text())}



@app.get("/rate20")
def rate20_page():
    from fastapi.responses import FileResponse
    return FileResponse(REPO / "api" / "static" / "rate20.html",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/api/rate20/items")
def rate20_items():
    f = REPO / "logs" / "test20_v2.json"
    return json.loads(f.read_text()) if f.exists() else []


class Rate20Save(BaseModel):
    ratings: list  # [{i, brand, occasion, caption, score, note}]


@app.post("/api/rate20/save")
def rate20_save(req: Rate20Save):
    out = REPO / "logs" / "test20_v2_ratings.json"
    out.write_text(json.dumps(req.ratings, ensure_ascii=False, indent=2))
    # ratings >=4 also flow to GOLD (the loop), via the same store shape gold_from_ratings reads
    gold_dir = REPO / "logs" / "brand_gold"; gold_dir.mkdir(exist_ok=True)
    promoted = 0
    for r in req.ratings:
        if (r.get("score") or 0) >= 4 and r.get("caption"):
            # map brand_ar -> brand_en via matrix
            m = json.loads((REPO / "data/brief_matrix.json").read_text())
            be = next((b["brand_en"] for b in m if b["brand"] == r.get("brand")), None)
            if not be: continue
            gf = gold_dir / f"{be}_gold.json"
            g = json.loads(gf.read_text()) if gf.exists() else []
            if r["caption"] not in [x.get("caption") for x in g]:
                g.append({"caption": r["caption"], "occasion": r.get("occasion",""),
                          "rating": r["score"], "model": "v6", "ts": "2026-06-11-rate20"})
                gf.write_text(json.dumps(g, ensure_ascii=False, indent=2)); promoted += 1
    return {"saved": len(req.ratings), "promoted_to_gold": promoted}


@app.post("/api/create")
def create_content(req: CreateRequest):
    """Unified content creation pipeline.
    JUNE 11: v6 FAST PATH first — DNA-covered Arabic brands get the de-poisoned
    mind (feed few-shot + occasion facts + GOLD + code filter + DNA judge).
    Legacy V3 path remains ONLY as fallback for brands without DNA.
    JUNE 12 (B136): blackout gate guards ALL creation — the negative-space law
    holds the main pipeline exactly like the client pipeline."""
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        from blackout_gate import check as _blackout_check
        _g = _blackout_check()
        if not _g["publish_allowed"]:
            return {"error": "BLACKOUT — all content creation halted",
                    "reason": _g["hard_block"]["reason"], "since": _g["hard_block"]["since"],
                    "law": "negative-space gate (FLANK-02), human-hands-only switch"}
    except ImportError:
        pass  # gate module missing = fail open, never break creation

    v6 = _try_create_v6(req)
    if v6 is not None:
        return v6

    from lib.quality_gate import check, auto_fix, log_mistake, get_recent_mistakes
    from lib.chain_router import get_visual_direction
    from build_agent_context import build_context

    api_key = get_openai_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    # 1. Load brain context
    try:
        context, token_count = build_context(req.brand, req.occasion)
    except Exception as e:
        context = f"Brand: {req.brand}, Occasion: {req.occasion}"
        token_count = 0

    # 2. Get templates — Arabic-only filter
    import re as _re
    ARABIC_RE = _re.compile(r'[؀-ۿ]')

    tlib_path = REPO / "11_who_to_learn_from" / "template_library.json"
    templates = []
    template_tier = 'none'
    if tlib_path.exists():
        tlib = json.loads(tlib_path.read_text())
        brand_profiles = intel.get('brand_profiles', {})
        brand_profile = brand_profiles.get(req.brand, {})
        sector = brand_profile.get('sector', '')

        # If brand posts in English, use sector defaults instead of brand-specific profile
        posting_lang = brand_profile.get('posting_language', 'arabic')
        use_sector_defaults = brand_profile.get('use_sector_defaults', False) or posting_lang == 'english'

        all_templates = tlib.get('templates', [])

        # Always filter to Arabic-only captions — English templates never used for Arabic generation
        arabic_templates = [t for t in all_templates if ARABIC_RE.search(t.get('caption', ''))]

        for tier in ['gold', 'silver', 'bronze', 'unverified', 'generated']:
            filtered = [t for t in arabic_templates
                        if t.get('sector') == sector and t.get('tier') == tier
                        and t.get('occasion') in (req.occasion, 'evergreen')]
            if filtered:
                templates.extend(filtered[:3])
                if not template_tier or template_tier == 'none':
                    template_tier = tier
            if len(templates) >= 3:
                break

    # 3. Get learning store mistakes
    recent_mistakes = get_recent_mistakes(req.brand, limit=5)

    # 4. Build prompt — sector-aware, Saudi-first, creativity-enforced
    templates_text = '\n'.join(f'- {t["caption"][:150]}' for t in templates[:5])
    mistakes_text = '\n'.join(f'- {m["mistake"][:80]}' for m in recent_mistakes) if recent_mistakes else 'لا يوجد'

    # Sector-specific length + style rules
    sector_rules = {
        'f_and_b':              'الطول: 80-150 حرف. أسلوب: حسّي مباشر. ابدأ باسم المنتج. مشاعر: شوق، جوع، فخر.',
        'fashion':              'الطول: 200-400 حرف. أسلوب: طموح وأنيق. بدون إيموجي أو بإيموجي واحد فقط. وصف تجربة الإطلالة.',
        'beauty_personal_care': 'الطول: 150-300 حرف. أسلوب: فائدة المنتج أولاً. 2-3 إيموجي مقبول. خاطبي المرأة السعودية.',
        'retail_lifestyle':     'الطول: 100-200 حرف. أسلوب: عروض وتوفير. ابدأ بالفائدة مش بالعلامة.',
        'real_estate':          'الطول: 150-250 حرف. أسلوب: فخر وطني + جودة حياة. اللغة رسمية أكثر.',
        'healthcare_wellness':  'الطول: 100-200 حرف. أسلوب: تحفيزي وصحي. ركّز على النتيجة.',
    }
    sector_rule = sector_rules.get(sector, 'الطول: 100-200 حرف.')
    max_chars = {
        'f_and_b': 140, 'fashion': 220, 'real_estate': 200,
        'retail_lifestyle': 160, 'beauty_personal_care': 150, 'finance': 180,
        'government': 200, 'food_manufacturing': 140, 'electronics': 160,
        'telecom': 160, 'healthcare_wellness': 180,
    }.get(sector, 180)

    # Brand-specific product names
    brand_pn = intel.get('brand_product_names', {}).get(req.brand, {})
    correct_product = brand_pn.get('correct', req.product)
    wrong_products = brand_pn.get('wrong', [])
    wrong_str = '، '.join(wrong_products[:3]) if wrong_products else 'لا يوجد'

    # Occasion-specific required words
    occ_words = intel.get('occasion_required_words', {}).get(req.occasion, [])
    occ_words_str = '، '.join(occ_words) if occ_words else 'لا يوجد كلمات مطلوبة'

    # Brand signature hashtags
    brand_sig = intel.get('brand_profiles', {}).get(req.brand, {}).get('signature_phrases', [])
    hashtag_str = ' '.join(brand_sig[:2]) if brand_sig else f'#{req.brand}'

    # Brand-specific caption intelligence — inject voice/openers/avoid into prompt
    # Falls back to sector-level entry (_sector_X) when no brand entry exists
    _ci_all = intel.get('caption_intelligence', {})
    cap_intel = _ci_all.get(req.brand, {}) or _ci_all.get(f'_sector_{sector}', {})
    brand_voice_block = ""
    if cap_intel:
        arabic_style = cap_intel.get('arabic_style', '')
        voice = cap_intel.get('voice', '') or cap_intel.get('high_engagement_style', '') or cap_intel.get('high_style', '')
        voice = voice[:80] if voice else ''
        # proven_openers: new format = designed hooks; old format = raw Instagram starters
        # Strip Unicode bidirectional/invisible control chars from auto-extracted openers
        import re as _re
        _ctrl_re = _re.compile('[\u200B-\u200F\u202A-\u202E\u2060-\u2069\uFEFF\t]')
        raw_openers = cap_intel.get('proven_openers', [])
        openers = [_ctrl_re.sub('', str(o)).strip() for o in raw_openers[:3]]
        openers = [o for o in openers if len(o) > 5][:3]
        # New format fields
        hooks = [h[:80] for h in cap_intel.get('real_hooks', [])[:1] if h]
        sigs = [s for s in cap_intel.get('signature_phrases', [])[:3] if s]
        avoid_new = [a for a in cap_intel.get('avoid_patterns', [])[:2] if a]
        # Old format fallbacks
        avoid_old = [a for a in cap_intel.get('avoid_topics', [])[:2] if a]
        avoids = avoid_new or avoid_old
        opt_len = cap_intel.get('optimal_length', '')
        # Prescription format (pizzahutsaudi-style)
        prescription = [p[:60] for p in cap_intel.get('prescription', [])[:2] if p]

        parts = []
        if arabic_style: parts.append(f"اللهجة: {arabic_style.replace('_', ' ')}")
        if voice: parts.append(f"الصوت: {voice.replace('_', ' ')}")
        if openers: parts.append(f"بدايات مثبتة: {' | '.join(str(o)[:50] for o in openers)}")
        if hooks: parts.append(f"خطاف: {hooks[0]}")
        if sigs: parts.append(f"عبارات مميزة: {' | '.join(sigs)}")
        if avoids: parts.append(f"تجنب: {' | '.join(str(a)[:40] for a in avoids)}")
        if prescription: parts.append(f"توجيه: {' | '.join(prescription)}")
        if opt_len: parts.append(f"الطول المثالي: {opt_len}")
        if parts:
            brand_voice_block = "\n" + "\n".join(parts)

    # Brand Arabic display names — what appears in the prompt and caption
    brand_display = BRAND_AR.get(req.brand.lower(), req.brand)

    # ── V3: Route to ONE technique (cd_03 Authenticity Detective excluded for captions) ──
    cd_primary, cd_scores = 'cd_05_paradox_hunter', {}
    try:
        from lib.cd_brains import route as cd_route
        _prim, _sec, cd_scores = cd_route(sector, req.occasion)
        # cd_03 is a video/script technique — removed from caption generation
        if _prim == 'cd_03_authenticity_detective':
            _prim = _sec if _sec and _sec != 'cd_03_authenticity_detective' else 'cd_05_paradox_hunter'
        cd_primary = _prim
    except Exception:
        pass

    # Map CD brain → V3 technique letter
    _TECH_MAP = {
        'cd_01_firaasa_architect':  'ج',
        'cd_02_metaphor_architect': 'أ',
        'cd_04_heritage_decoder':   'ب',
        'cd_05_paradox_hunter':     'أ',
    }
    tech_letter = _TECH_MAP.get(cd_primary, 'أ')

    _V3_TECHNIQUES = {
        'أ': """أ. Paradox Hunter — قلب التوقع (استلهم الفكرة، لا تنسخ القالب)
← ناجح: "التوفير اللي ما يحتاج تفكر مرتين"
← ناجح (مختلف): "قهوة تصحيك — حتى قبل ما تشربها"
← فاشل: "استمتع" / "لا تفوت" / "أجواء مميزة" / "عرض لفترة محدودة"
← ممنوع: نسخ أي مثال كما هو مع تغيير الكلمات فقط
← ممنوع تماماً: قالب "[المنتج] اللي ما ينتظر [المناسبة] — [المناسبة] ينتظره/ها" بأي شكل
← ممنوع تماماً: وضع رمضان/العيد/اليوم الوطني/يوم التأسيس في موقع الانتظار — المناسبة لا تنتظر المنتج""" + _get_learned_lines('أ'),

        'ب': """ب. Heritage Decoder — جملة قصيرة تحمل كلمة بمعنيين في آنٍ واحد
← ناجح (مالية): الذكاء يستثمر فيك
← ناجح (أزياء): ترتدين المناسبة
← ناجح (غذاء): اللبن اللي يروبك
← فاشل وممنوع: اكتب الجملة فقط، بدون علامات اقتباس، بدون شرح للمعنى
← فاشل وممنوع: X معك في كل خطوة
← تجنب: "يشبك" — معناه الثاني "يعقّد/يُربك" يعكس المقصود
← تجنب: "يطمن قلبك" في سياق منتج — حميمية غير مقصودة""" + _get_learned_lines('ب'),

        'ج': """ج. Firaasa — ملاحظة سلوكية محددة لهذا المنتج تحديداً
← ناجح: "اللبن هو اللي يختارك — مو العكس"
← ناجح: "الأكل اللي تفتح الباب لريحته — قبل ما تجلس"
← ممنوع تماماً: "الأم/الناس/الأسرة/العميل ما تدور/يدور على X — تدور/يدور على Y" — حتى مع تغيير الكلمات
← ممنوع تماماً: "اللي يدور على [X]" كبداية — مكررة 82 مرة في الكوربس (قالب باحث متعب)
← فاشل وممنوع: "مش بس لـ X، هي لحظة Y وسط الزحمة"
← فاشل وممنوع: "في لحظة X، Y هو اللي..." — لا تستخدم "في لحظة" كبداية
← فاشل وممنوع: "لحظة هدوء، تكتشف فيها..." — نفس القالب
← الصحيح: لحظة سلوكية حقيقية خاصة بهذا المنتج تحديداً — مو قالب يصلح لأي منتج""" + _get_learned_lines('ج'),
    }
    technique_block = _V3_TECHNIQUES[tech_letter]
    is_english = getattr(req, 'language', 'arabic').lower() == 'english'

    # V3 Prompt — 4-block XML structure
    if is_english:
        red_lines_block = f"""<RED_LINES>
Forbidden: beds, removing clothing/hijab, exploiting fear or weakness.
Forbidden: placing religious (Ramadan, Eid) or national (National Day, Founding Day) occasions in a waiting position for the product.
Always: natural Saudi/Gulf tone in English. Max {max_chars} characters. No Arabic.
</RED_LINES>"""
    else:
        red_lines_block = f"""<RED_LINES>
ممنوع: السرير، خلع الملابس أو الحجاب، استغلال ضعف الناس أو خوفهم.
ممنوع: وضع مناسبة دينية (رمضان، العيد) أو وطنية (اليوم الوطني، يوم التأسيس) في موقع الانتظار للمنتج.
دائماً: لهجة سعودية طبيعية. حد أقصى {max_chars} حرف. بدون إنجليزي.
</RED_LINES>"""

    prompt = f"""{red_lines_block}

<TECHNIQUES>
{technique_block}
</TECHNIQUES>

<BRAND>
العلامة: {brand_display} | القطاع: {sector} | المنتج: {req.product} | المناسبة: {req.occasion}
الهاشتاقات: {hashtag_str}{brand_voice_block}
</BRAND>

<TASK>
{"Write 3 captions — each applying the technique differently." if is_english else "اكتب 3 كابشنات — كل واحد يطبّق التقنية بطريقة مختلفة."}
{"Each caption: max " + str(max_chars) + " characters. Plain text only — no quotes, no explanation, no numbering." if is_english else "كل كابشن: حد أقصى " + str(max_chars) + " حرف. نص فقط — بدون علامات اقتباس، بدون شرح، بدون رقم، بدون اسم التقنية."}
{"Each caption must use a different sentence structure." if is_english else "البنية اللغوية لكل خيار يجب أن تختلف — لا تنسخ نفس القالب ثلاث مرات بكلمات مختلفة."}
{"Occasion vocabulary required (at least one caption must include one of): " + occ_words_str if is_english else "الكلمات المطلوبة للمناسبة (يجب أن تظهر في أحد الكابشنات على الأقل): " + occ_words_str}
{"Then choose the strongest and place it on the last line after: Best:" if is_english else "ثم اختر الأقوى وضعه في السطر الأخير بعد كلمة: الأفضل:"}
</TASK>"""

    import openai
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.chat.completions.create(
            model='gpt-4o',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=400,
            temperature=0.8,
        )
    except openai.RateLimitError as e:
        raise HTTPException(status_code=429, detail=f"OpenAI rate limit reached — try again in a few seconds. ({e})")
    except openai.APIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")

    raw_output = resp.choices[0].message.content.strip()

    # V3: parse الأفضل: selection from the 3-option output
    all_options_text = raw_output
    caption = raw_output
    if 'الأفضل:' in raw_output:
        parts = raw_output.split('الأفضل:', 1)
        all_options_text = parts[0].strip()
        caption = parts[1].strip().strip('"\'')

    caption = caption.strip().strip(chr(34)).strip(chr(39)).strip()
    caption = caption.replace(chr(8220),"").replace(chr(8221),"").replace(chr(8216),"").replace(chr(8217),"")

    # Editor LLM — second call to cross-check model's self-selection
    if all_options_text and all_options_text != raw_output:
        try:
            editor_prompt = f"""أنت محرر إبداعي سعودي. اختر الكابشن الأقوى من هذه الخيارات.

معايير الرفض الفوري:
- يحتوي "لا تفوت" أو "استمتع" أو "أجواء مميزة"
- "[المنتج] اللي ما ينتظر [المناسبة] — [المناسبة] ينتظره/ها" (قالب انتظار مكرر ومسيء للمناسبة)
- "اللي يدور على [X] — يلاقيه/يعرف عند [علامة]" (قالب الباحث — مكرر 61 مرة في الكوربس)
- "الأم/الناس/الأسرة ما تدور/يدور على X — تدور/يدور على Y" (قالب فراسة مكرر)
- "تخيل معي" كبداية للكابشن (مكرر 35 مرة)
- "X معك في كل خطوة — أنت الخطوة" (قالب مكرر)
- يحتوي "يشبك" أو "يطمن قلبك" في سياق منتج
- أطول من {max_chars} حرف

الخيارات:
{all_options_text}

أعد كتابة الأقوى كما هو بالضبط، بدون شرح:"""
            editor_resp = client.chat.completions.create(
                model='gpt-4o',
                messages=[{'role': 'user', 'content': editor_prompt}],
                max_tokens=150,
                temperature=0.2,
            )
            editor_pick = editor_resp.choices[0].message.content.strip().strip('"\'')
            editor_pick = editor_pick.replace(chr(8220),"").replace(chr(8221),"").replace(chr(8216),"").replace(chr(8217),"")
            if editor_pick and len(editor_pick) < max_chars * 1.5:
                caption = editor_pick
        except Exception:
            pass  # fall back to self-selected الأفضل

    # 5. Quality gate + refine loop
    best_caption = caption
    best_score = 0
    best_result = None

    for iteration in range(3):
        result = check(caption, brand=req.brand, occasion=req.occasion)
        if result['score'] > best_score:
            best_score = result['score']
            best_caption = caption
            best_result = result

        if result['score'] >= 80:
            break

        if result['fixes_needed']:
            brand_profiles = intel.get('brand_profiles', {})
            sector = brand_profiles.get(req.brand, {}).get('sector', '')
            caption = auto_fix(caption, brand=req.brand, sector=sector)
            result2 = check(caption, brand=req.brand, occasion=req.occasion)
            if result2['score'] > best_score:
                best_score = result2['score']
                best_caption = caption
                best_result = result2
            if best_score >= 80:
                break

        if iteration < 2 and best_score < 80:
            failures = [c['detail'] for c in (best_result or result)['checks'] if not c['passed']]
            retry_prompt = f"""كابشن سابق: {caption}

مشاكل: {', '.join(failures[:3])}

اكتب كابشن محسّن باللهجة السعودية فقط لنفس المنتج والمناسبة. Caption only:"""
            resp2 = client.chat.completions.create(
                model='gpt-4o',
                messages=[{'role': 'user', 'content': retry_prompt}],
                max_tokens=150,
            )
            caption = resp2.choices[0].message.content.strip().strip('"\'')

    # 6. Log mistake if score < 80
    if best_score < 80:
        failed_checks = [c['detail'] for c in (best_result or {}).get('checks', []) if not c.get('passed')]
        log_mistake(req.brand, best_score, '; '.join(failed_checks[:3]))

    # Clean any embedded stray quotes before final output
    import re as _re2; best_caption = _re2.sub(r'[\u0022\u201c\u201d\u2018\u2019]+(?=\s*#|\s*$)', '', best_caption).strip()

    # 7. Get proof
    proof = {}
    if templates:
        t = templates[0]
        proof = {
            'template_caption': t.get('caption', '')[:100],
            'template_likes': t.get('original_likes'),
            'template_url': t.get('original_url', ''),
            'template_tier': template_tier,
        }
    metrics = intel.get('real_metrics', {}).get(req.brand, {})
    if metrics:
        proof['brand_metrics'] = f"{metrics.get('obs_count',0)} verified posts, avg {metrics.get('avg_likes',0):,} likes"

    # ── Step 7: Visual chain selection (CD technique → TF family) ─────────────
    brand_profile = intel.get('brand_profiles', {}).get(req.brand, {})
    visual_dna = brand_profile.get('visual_dna', {})
    brand_color_hint = visual_dna.get('primary_color', '') if isinstance(visual_dna, dict) else ''
    brand_display_ar = BRAND_AR.get(req.brand.lower(), req.brand)
    try:
        visual_chain = get_visual_direction(
            cd_primary=cd_primary,
            sector=sector,
            occasion=req.occasion,
            brand=req.brand,
            product=req.product or brand_display_ar,
            brand_color=brand_color_hint,
            brand_display=brand_display_ar,
        )
    except Exception as _ve:
        visual_chain = {"error": str(_ve)}

    return {
        'brand': req.brand,
        'product': req.product,
        'occasion': req.occasion,
        'content': {
            'caption': best_caption,
            'hashtags': [w for w in best_caption.split() if w.startswith('#')],
        },
        'quality': {
            'score': best_score,
            'confidence': 'high' if best_score >= 80 else 'medium' if best_score >= 60 else 'low',
            'template_tier': template_tier,
            'fixes_applied': (best_result or {}).get('fixes_needed', []),
            'passed': best_score >= 70,
        },
        'creative_director': {
            'primary': cd_primary,
            'technique': tech_letter,
            'scores': cd_scores,
        },
        'visual_chain': visual_chain,
        'proof': proof,
        'context_tokens': token_count,
    }


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


# ═══════════════════════════════════════════════════════════
# HUMAN REVIEW — mobile-friendly review UI + save endpoint
# ═══════════════════════════════════════════════════════════

@app.get("/review")
def review_page():
    return FileResponse(STATIC_DIR / "review.html")

@app.get("/api/review/data")
def review_data():
    """Return parsed review entries for the mobile UI."""
    review_file = REPO / "logs" / "system" / "review_data.json"
    if not review_file.exists():
        raise HTTPException(status_code=404, detail="Review data not found. Run generate_human_review_set.py first.")
    return json.loads(review_file.read_text())

class ReviewSaveRequest(BaseModel):
    pass  # accepts any dict

@app.post("/api/review/save")
async def review_save(request: Request):
    """Save review ratings from mobile UI to disk."""
    ratings = await request.json()
    results_file = REPO / "logs" / "system" / "review_results.json"
    # Merge with existing if any
    existing = json.loads(results_file.read_text()) if results_file.exists() else {}
    existing.update(ratings)
    results_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2))

    # Also append to learning store — failed/weak outputs become content lessons
    learning_store = REPO / "logs" / "learning_store.jsonl"
    from datetime import datetime as _dt
    added = 0
    for item_id, r in ratings.items():
        if r.get("rating") in ("weak", "fail"):
            mistake = f"Human rated '{r['rating']}': @{r.get('brand','')} | {r.get('occasion','')} | score={r.get('score','')} | note: {r.get('note','no note')}"
            entry = {"handle": r.get("brand",""), "score": 0 if r["rating"]=="fail" else 40,
                     "mistake": mistake, "timestamp": _dt.now().isoformat(), "source": "human_review"}
            with learning_store.open("a") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            added += 1

    total = len(existing)
    rated = sum(1 for v in existing.values() if v.get("rating"))
    counts = {}
    for v in existing.values():
        r = v.get("rating","")
        counts[r] = counts.get(r, 0) + 1

    return {"saved": True, "total_rated": rated, "breakdown": counts,
            "learning_entries_added": added}


# ═══════════════════════════════════════════════════════════
# HUMAIN GOLD REVIEW — web review UI for ALLaM collected outputs
# ═══════════════════════════════════════════════════════════

HUMAIN_QUEUE  = REPO / "logs" / "humain_queue.json"
HUMAIN_GOLD   = REPO / "docs" / "consultations" / "GOLD_OUTPUTS_HUMAIN.md"
LEARNING_FILE = REPO / "logs" / "prompt_learning.json"

def _humain_learn(tech: str, caption: str, kind: str, reason: str = None, sector: str = None):
    """Persist one approved or rejected caption to the learning store."""
    data = json.loads(LEARNING_FILE.read_text()) if LEARNING_FILE.exists() else {
        "positive": {"أ": [], "ب": [], "ج": [], "د": [], "هـ": []},
        "negative": {"أ": [], "ب": [], "ج": [], "د": [], "هـ": []}
    }
    entry: dict = {"caption": caption, "sector": sector}
    if reason:
        entry["reason"] = reason
    bucket = data.setdefault(kind, {})
    bucket.setdefault(tech, []).append(entry)
    bucket[tech] = bucket[tech][-20:]   # keep last 20 per slot
    LEARNING_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

_REASON_LABELS = {
    "قالب_مكرر": "قالب مكرر", "معنى_مزدوج": "معنى مزدوج",
    "طويل": "طويل جداً",       "عام": "عام وغير محدد",
    "لهجة": "لهجة خاطئة",
}

def _get_learned_lines(tech: str) -> str:
    """Return extra few-shot lines for a technique from human-reviewed data."""
    try:
        if not LEARNING_FILE.exists():
            return ""
        data = json.loads(LEARNING_FILE.read_text())
        lines = []
        for p in data.get("positive", {}).get(tech, [])[-2:]:
            lines.append(f'← ناجح (معتمد بشرياً): "{p["caption"]}"')
        for n in data.get("negative", {}).get(tech, [])[-2:]:
            label = _REASON_LABELS.get(n.get("reason", ""), "ضعيف")
            lines.append(f'← مرفوض ({label}): "{n["caption"]}"')
        return ("\n" + "\n".join(lines)) if lines else ""
    except Exception:
        return ""

@app.get("/humain-review")
def humain_review_page():
    return FileResponse(STATIC_DIR / "humain_review.html")

@app.get("/api/humain/queue")
def humain_queue():
    if not HUMAIN_QUEUE.exists():
        return {"pending": [], "approved": [], "gold_count": 0}
    q = json.loads(HUMAIN_QUEUE.read_text())
    # Count gold from markdown
    gold_count = 0
    if HUMAIN_GOLD.exists():
        for line in HUMAIN_GOLD.read_text().splitlines():
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7 and parts[1].isdigit():
                gold_count += 1
    q["gold_count"] = gold_count
    return q

@app.post("/api/humain/approve")
async def humain_approve(request: Request):
    body = await request.json()
    brief_id  = body.get("brief_id")
    caption   = body.get("caption", "").strip()
    technique = body.get("technique", "؟").strip()
    rating    = body.get("rating", "gold")   # gold | weak | skip
    reason    = body.get("reason", "")       # for weak: قالب_مكرر | معنى_مزدوج | طويل | عام | لهجة

    if not caption or not brief_id:
        raise HTTPException(status_code=400, detail="brief_id and caption required")

    # Load queue and move item from pending → approved/stale based on rating
    q = json.loads(HUMAIN_QUEUE.read_text()) if HUMAIN_QUEUE.exists() else {"pending": [], "approved": [], "stale_v1": []}
    brief_data = {}
    remaining_pending = []
    for item in q["pending"]:
        if item["brief_id"] == brief_id:
            item["status"]      = rating
            item["chosen"]      = caption
            item["technique"]   = technique
            item["approved_at"] = datetime.now().isoformat()
            brief_data = item
            # Route to correct bucket
            if rating == "gold":
                q.setdefault("approved", []).append(item)
            elif rating == "weak":
                q.setdefault("stale_v1", []).append(item)
            # skip: drop entirely (not re-queued)
        else:
            remaining_pending.append(item)
    q["pending"] = remaining_pending
    HUMAIN_QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2))

    # Feed learning store — approved becomes positive example, weak becomes negative
    if rating == "gold" and brief_data:
        _humain_learn(technique, caption, "positive", sector=brief_data.get("sector"))
    elif rating == "weak" and caption:
        _humain_learn(technique, caption, "negative", reason=reason or "عام", sector=brief_data.get("sector"))

    # Feed routing manager — every decision trains the technique router
    if brief_data and technique and technique != "؟":
        try:
            import sys as _sys; _sys.path.insert(0, str(REPO / "scripts"))
            from routing_manager import record as _record
            _record(
                technique=technique,
                sector=brief_data.get("sector", ""),
                occasion=brief_data.get("occasion", ""),
                approved=(rating == "gold"),
            )
        except Exception:
            pass

    if rating != "gold" or not brief_data:
        return {"saved": False, "reason": "skipped or weak"}

    # Append to GOLD_OUTPUTS_HUMAIN.md
    gold_text  = HUMAIN_GOLD.read_text() if HUMAIN_GOLD.exists() else ""
    # Count current entries
    gold_rows  = [l for l in gold_text.splitlines() if "|" in l and l.strip().split("|")[1].strip().isdigit()]
    next_num   = len(gold_rows) + 1
    sector_ar  = brief_data.get("sector_ar", brief_data.get("sector",""))
    occasion_ar = brief_data.get("occasion_ar", brief_data.get("occasion",""))
    new_row    = f"| {next_num} | {brief_data['brand']} | {sector_ar} | {occasion_ar} | {technique} | {caption} |"

    import re as _re
    # Replace placeholder row or append
    if "| — | — |" in gold_text:
        gold_text = gold_text.replace("| — | — | — | — | — | — |", new_row, 1)
    else:
        gold_text = _re.sub(r"(---\n\n## COUNT:)", f"{new_row}\n\n---\n\n## COUNT:", gold_text)

    # Update count
    gold_text = _re.sub(r"## COUNT: \d+ / 300", f"## COUNT: {next_num} / 300", gold_text)
    HUMAIN_GOLD.write_text(gold_text)

    return {"saved": True, "num": next_num, "caption": caption}

@app.get("/api/humain/learning")
def humain_learning():
    if not LEARNING_FILE.exists():
        return {"positive": {}, "negative": {}, "total_examples": 0}
    data = json.loads(LEARNING_FILE.read_text())
    pos = {t: len(v) for t, v in data.get("positive", {}).items()}
    neg = {t: len(v) for t, v in data.get("negative", {}).items()}
    return {
        "positive": pos,
        "negative": neg,
        "total_examples": sum(pos.values()) + sum(neg.values()),
    }


@app.get("/api/humain/routing")
def humain_routing():
    try:
        import sys as _sys; _sys.path.insert(0, str(REPO / "scripts"))
        from routing_manager import summary as _summary, load_scores as _load
        return {"summary": _summary(), "raw_scores": _load()}
    except Exception as e:
        return {"error": str(e), "summary": {}}


PAIRWISE_FILE = REPO / "logs" / "pairwise_comparisons.json"

@app.get("/api/humain/pairs")
def humain_pairs():
    """Return two random pending captions for pairwise comparison."""
    import random
    q = json.loads(HUMAIN_QUEUE.read_text()) if HUMAIN_QUEUE.exists() else {}
    pending = [p for p in q.get("pending", []) if p.get("status") == "pending"]
    # Collect all individual caption options
    candidates = []
    for item in pending:
        for tech, cap in (item.get("options") or {}).items():
            if cap and len(cap) > 10:
                candidates.append({
                    "brief_id": item["brief_id"],
                    "brand":    item.get("brand", ""),
                    "sector":   item.get("sector", ""),
                    "occasion": item.get("occasion", ""),
                    "technique": tech,
                    "caption":  cap,
                })
    if len(candidates) < 2:
        return {"error": "not_enough_candidates", "count": len(candidates)}
    a, b = random.sample(candidates, 2)
    return {"a": a, "b": b}


@app.post("/api/humain/prefer")
async def humain_prefer(request: Request):
    """Record which caption won a pairwise comparison. Updates Elo scores."""
    body = await request.json()
    winner = body.get("winner")  # {"brief_id","technique","sector","occasion","caption"}
    loser  = body.get("loser")

    if not winner or not loser:
        raise HTTPException(status_code=400, detail="winner and loser required")

    comp = {
        "winner_tech":    winner["technique"],
        "loser_tech":     loser["technique"],
        "winner_sector":  winner["sector"],
        "winner_occ":     winner["occasion"],
        "winner_brand":   winner.get("brand", ""),
        "loser_brand":    loser.get("brand", ""),
        "winner_caption": winner["caption"][:300],
        "loser_caption":  loser["caption"][:300],
        "ts": datetime.now().isoformat(),
    }

    data = json.loads(PAIRWISE_FILE.read_text()) if PAIRWISE_FILE.exists() else {"comparisons": [], "elo": {}}
    data["comparisons"].append(comp)

    # Elo update (K=32)
    elo = data.setdefault("elo", {})
    wk = winner["technique"]
    lk = loser["technique"]
    elo.setdefault(wk, 1000)
    elo.setdefault(lk, 1000)
    ew = 1 / (1 + 10 ** ((elo[lk] - elo[wk]) / 400))
    elo[wk] = round(elo[wk] + 32 * (1 - ew))
    elo[lk] = round(elo[lk] + 32 * (0 - (1 - ew)))

    PAIRWISE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    # Also feed routing manager
    try:
        import sys as _sys; _sys.path.insert(0, str(REPO / "scripts"))
        from routing_manager import record as _record
        _record(winner["technique"], winner["sector"], winner["occasion"], approved=True)
        _record(loser["technique"],  loser["sector"],  loser["occasion"],  approved=False)
    except Exception:
        pass

    return {"elo": elo, "total_comparisons": len(data["comparisons"])}


@app.get("/humain-compare")
def humain_compare_page():
    from fastapi.responses import FileResponse
    return FileResponse(REPO / "api" / "static" / "humain_compare.html")


# ═══════════════════════════════════════════════════════════
# CROSS-MODEL COMPARISON — HUMAIN vs GPT-4o vs Claude
# Generates preference pairs for DPO fine-tuning
# ═══════════════════════════════════════════════════════════

_CROSS_QUEUES = {
    "humain": REPO / "logs" / "humain_queue.json",
    "gpt-4o": REPO / "logs" / "gpt4o_queue.json",
    "claude":  REPO / "logs" / "claude_queue.json",
}
_CROSS_PREFS_FILE = REPO / "logs" / "cross_preferences.json"

def _load_cross_queue(model: str) -> list:
    path = _CROSS_QUEUES.get(model)
    if not path or not path.exists():
        return []
    q = json.loads(path.read_text())
    return q.get("pending", []) + q.get("approved", [])


def _brief_key(item: dict) -> str:
    return f"{item.get('brand','')}|{item.get('occasion','')}"


@app.get("/cross-compare")
def cross_compare_page():
    from fastapi.responses import FileResponse
    return FileResponse(REPO / "api" / "static" / "cross_compare.html",
                        headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/api/cross/stats")
def cross_stats():
    """Return counts per model and overall preference win-rates."""
    counts = {}
    for model in _CROSS_QUEUES:
        items = _load_cross_queue(model)
        counts[model] = len(items)

    prefs = {"comparisons": [], "win_rates": {}}
    if _CROSS_PREFS_FILE.exists():
        prefs = json.loads(_CROSS_PREFS_FILE.read_text())

    wins = {}
    losses = {}
    for c in prefs.get("comparisons", []):
        w = c.get("winner_model", "")
        l = c.get("loser_model", "")
        wins[w] = wins.get(w, 0) + 1
        losses[l] = losses.get(l, 0) + 1

    win_rates = {}
    for m in set(list(wins.keys()) + list(losses.keys())):
        total = wins.get(m, 0) + losses.get(m, 0)
        win_rates[m] = round(100 * wins.get(m, 0) / max(total, 1))

    # SCOREBOARD (June 11): both-bad rate + ratings + prompt-version breakdown
    comps = prefs.get("comparisons", [])
    rated = [c for c in comps if c.get("rating")]
    both_bad = [c for c in comps if c.get("verdict") == "both_bad"]
    ratings_by_model = {}
    for c in rated:
        m = c.get("winner_model", "?")
        ratings_by_model.setdefault(m, []).append(c["rating"])
    version_counts = {}
    for model in _CROSS_QUEUES:
        for it in _load_cross_queue(model):
            v = it.get("prompt_version", "v3-era")
            version_counts.setdefault(v, {}).setdefault(model, 0)
            version_counts[v][model] += 1
    scoreboard = {
        "judged": len(comps),
        "both_bad": len(both_bad),
        "both_bad_rate_pct": round(100 * len(both_bad) / max(len(comps), 1)),
        "avg_rating_by_model": {m: round(sum(r) / len(r), 2) for m, r in ratings_by_model.items()},
        "queue_by_prompt_version": version_counts,
    }

    return {
        "scoreboard": scoreboard,
        "counts": counts,
        "total_comparisons": len(prefs.get("comparisons", [])),
        "win_rates": win_rates,
        "wins": wins,
    }


@app.get("/api/cross/pairs")
def cross_pairs(model_a: str = "claude", model_b: str = "gpt-4o", technique: str = "", version: str = "v6"):
    """Return one brief that has outputs from both models — for pairwise comparison."""
    def _vfilter(items):
        # June 11: founder taps must judge ONLY the new mind (440 v3-era zombies
        # polluted the queue and his GOLD). version="all" restores old behavior.
        if version == "all":
            return items
        return [i for i in items if i.get("prompt_version") == version]
    items_a = {_brief_key(i): i for i in _vfilter(_load_cross_queue(model_a))}
    items_b = {_brief_key(i): i for i in _vfilter(_load_cross_queue(model_b))}

    # Exclude already-compared briefs
    prefs = {"comparisons": []}
    if _CROSS_PREFS_FILE.exists():
        prefs = json.loads(_CROSS_PREFS_FILE.read_text())
    compared = {c["brief_key"] for c in prefs.get("comparisons", [])
                if c.get("model_a") == model_a and c.get("model_b") == model_b}

    # Filter: at least one option must have real Arabic content (not parse-failure garbage)
    def _has_valid_cap(item):
        import re as _re
        opts = item.get("options", {})
        for v in (opts.values() if isinstance(opts, dict) else []):
            text = str(v).strip() if v else ""
            if len(text) < 10: continue
            # Must contain ≥2 Arabic words of length 3+ (catches "ب. . ج. . هـ." failures)
            arabic_words = _re.findall(r'[؀-ۿ]{3,}', text)
            if len(arabic_words) >= 2:
                return True
        return False

    overlap = [
        k for k in items_a
        if k in items_b and k not in compared
        and _has_valid_cap(items_a[k]) and _has_valid_cap(items_b[k])
    ]
    if not overlap:
        return {"done": True, "remaining": 0}

    # Sort by score gap (highest gap = clearest DPO signal = review first)
    def _gap(k):
        sa = items_a[k].get("scores", {})
        sb = items_b[k].get("scores", {})
        ma = max((v for v in sa.values() if isinstance(v, (int, float))), default=0)
        mb = max((v for v in sb.values() if isinstance(v, (int, float))), default=0)
        return abs(ma - mb)
    overlap.sort(key=_gap, reverse=True)

    key = overlap[0]
    ia = items_a[key]
    ib = items_b[key]

    # Pick best caption from each model (source-aware: HUMAIN uses ALLaM's own pick)
    def _best_cap(item: dict, preferred_tech: str = None) -> tuple[str, str]:
        source = item.get("source", "humain")
        opts   = item.get("options", {})
        scores = item.get("scores", {})
        best_stored = item.get("best", "")

        # HUMAIN: use ALLaM's own pick (الأفضل field) — not auto-score
        if source == "humain" and best_stored and len(best_stored) > 5:
            for k, v in opts.items():
                if v and v.strip()[:40] == best_stored.strip()[:40]:
                    return k, best_stored
            return "—", best_stored

        # Specific technique requested (same-technique comparison mode)
        if preferred_tech and preferred_tech in opts and opts[preferred_tech] and len(opts[preferred_tech]) > 5:
            return preferred_tech, opts[preferred_tech]

        # API models: rotate through techniques to avoid ج always winning
        # Use a score-weighted random among top-2 instead of always max
        if scores:
            sorted_techs = sorted(scores, key=lambda k: scores.get(k, 0), reverse=True)
            top2 = [t for t in sorted_techs[:2] if opts.get(t) and len(opts.get(t, "")) > 5]
            if top2:
                import random
                winner = random.choice(top2)
                return winner, opts[winner]
            best_k = sorted_techs[0]
            return best_k, opts.get(best_k, best_stored)

        return "—", best_stored

    tech_a, cap_a = _best_cap(ia, technique or None)
    tech_b, cap_b = _best_cap(ib, technique or None)

    return {
        "done": False,
        "remaining": len(overlap),
        "brief_key": key,
        "brand": ia.get("brand"),
        "occasion": ia.get("occasion"),
        "sector": ia.get("sector"),
        "model_a": model_a,
        "model_b": model_b,
        "caption_a": cap_a,
        "caption_b": cap_b,
        "tech_a": tech_a,
        "tech_b": tech_b,
        "technique_mode": technique,
        "all_options_a": ia.get("options", {}),
        "all_options_b": ib.get("options", {}),
        "scores_a": ia.get("scores", {}),
        "scores_b": ib.get("scores", {}),
        "brand_display": BRAND_AR.get((ia.get("brand") or "").lower(), ia.get("brand", "")),
        "sector_emoji": {"f_and_b": "🍔", "fashion": "👗", "beauty_personal_care": "💄",
                         "retail_lifestyle": "🛍️", "healthcare_wellness": "💪", "real_estate": "🏠"
                         }.get(ia.get("sector", ""), ""),
        "score_gap": round(_gap(key), 1),
    }


@app.post("/api/cross/prefer")
async def cross_prefer(request: Request):
    """Record which model's caption was preferred for a brief."""
    body = await request.json()
    brief_key   = body.get("brief_key", "")
    winner      = body.get("winner_model", "")
    loser       = body.get("loser_model", "")
    win_cap     = body.get("winner_caption", "")
    lose_cap    = body.get("loser_caption", "")
    model_a     = body.get("model_a", "")
    model_b     = body.get("model_b", "")

    prefs = {"comparisons": []}
    if _CROSS_PREFS_FILE.exists():
        prefs = json.loads(_CROSS_PREFS_FILE.read_text())

    prefs["comparisons"].append({
        "brief_key":      brief_key,
        "model_a":        model_a,
        "model_b":        model_b,
        "winner_model":   winner,
        "loser_model":    loser,
        "winner_caption": win_cap,
        "loser_caption":  lose_cap,
        # June 10: founder review upgrade — "both bad" verdict + 1-5 winner rating
        "verdict":        body.get("verdict", ""),       # "" | "both_bad"
        "rating":         body.get("rating", None),       # 1-5 of the winner (None = unrated)
        "timestamp":      datetime.now().isoformat(),
    })
    _CROSS_PREFS_FILE.write_text(json.dumps(prefs, ensure_ascii=False, indent=2))

    # Tally win rates
    wins = {}
    for c in prefs["comparisons"]:
        w = c.get("winner_model", "")
        wins[w] = wins.get(w, 0) + 1

    return {"total_comparisons": len(prefs["comparisons"]), "wins": wins}


# ═══════════════════════════════════════════════════════════════════
# MOHAMED'S DECISION PORTAL (June 12 v2 — "one link always live, pages,
# phone, share, emergency"). Queue-driven: the pair pushes decisions into
# data/decision_queue.json (scripts/queue_decision.py); Mohamed answers
# page by page; emergencies jump the line. Key-protected (?k=).
# ═══════════════════════════════════════════════════════════════════
_ANSWERS_FILE = REPO / "data" / "mohamed_answers.jsonl"
_QUEUE_FILE = REPO / "data" / "decision_queue.json"


def _approvals_key():
    for l in open(Path.home() / ".abraham_env"):
        if l.startswith("APPROVALS_KEY="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def _key_ok(k: str | None) -> bool:
    real = _approvals_key()
    return bool(real) and k == real


@app.get("/approvals")
def approvals_page(k: str = ""):
    if not _key_ok(k):
        return {"error": "key required — open the link Claude gave you (with ?k=)"}
    return FileResponse(STATIC_DIR / "approvals.html",
                        headers={"Cache-Control": "no-store"})


@app.get("/api/approvals/items")
def approvals_items(k: str = ""):
    if not _key_ok(k):
        return []
    q = json.loads(_QUEUE_FILE.read_text()) if _QUEUE_FILE.exists() else {"items": []}
    items = q["items"]
    items.sort(key=lambda x: (x.get("status") == "answered",
                               0 if x.get("priority") == "urgent" else 1,
                               x.get("created", "")))
    return items


@app.post("/api/approvals/answer")
async def approvals_answer(request: Request, k: str = ""):
    if not _key_ok(k):
        return {"ok": False, "error": "bad key"}
    body = await request.json()
    _ANSWERS_FILE.parent.mkdir(exist_ok=True)
    entry = {"ts": datetime.now().isoformat(timespec="seconds"),
              "item_id": body.get("item_id"), "answer": str(body.get("answer", "")),
              "note": body.get("note", ""), "source": "decision_portal"}
    with open(_ANSWERS_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if _QUEUE_FILE.exists():
        q = json.loads(_QUEUE_FILE.read_text())
        for it in q["items"]:
            if it["id"] == entry["item_id"]:
                it["status"] = "answered"
                it["answered"] = entry["answer"][:60]
        _QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return {"ok": True}


@app.post("/api/approvals/reverse")
async def approvals_reverse(request: Request, k: str = ""):
    """Mohamed reverses a decision — comment REQUIRED (reversals retrain the system)."""
    if not _key_ok(k):
        return {"ok": False, "error": "bad key"}
    body = await request.json()
    if not (body.get("note") or "").strip():
        return {"ok": False, "error": "reversal needs a reason"}
    entry = {"ts": datetime.now().isoformat(timespec="seconds"),
              "item_id": body.get("item_id"), "answer": "REVERSED",
              "note": body.get("note", ""), "source": "decision_portal"}
    with open(_ANSWERS_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if _QUEUE_FILE.exists():
        q = json.loads(_QUEUE_FILE.read_text())
        for it in q["items"]:
            if it["id"] == entry["item_id"]:
                it["status"] = "open"
                it.pop("answered", None)
        _QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=1))
    return {"ok": True}
