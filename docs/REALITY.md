# OGZ AI — THE REALITY (June 29, 2026)

The honest one-pager. Written after the full-power audit + the orchestra's verdict on the 50-client
"Complete System Architecture" spec. That spec is a **north star, not a plan** — its values are right,
its scale/metrics/infra are pre-pivot fiction. This doc is what is TRUE.

## The three things — never conflate them
- **THE BRAIN** = `ogz-knowledge`: the produce pipeline (occasion → brief → CD-minds → 94-chain prompt →
  render → caption) + the judges + the 3 HTTP contracts (`/extract` `/produce` `/performance`). **This is
  what we ship.**
- **THE BUILD MACHINE** = RABIE(GPT-4o) + Claude + DeepSeek + make_sure + the orchestra. **This is HOW we
  build the brain. It is not shipped.** Claude is the builder; RABIE+DeepSeek judge; HUMAIN is the Saudi pen.
- **THE DEV PLATFORM** = the developer-built customer app (o-gz-studios-web). **The devs own infra,
  multi-tenant, scaling, accounts, dashboards.** NOT our problem (the June-27 pivot).

## What's REAL (audited June 29, verified)
- 3 pilot clients (albaik, eatjurisha, myfitness). **5/9 first posts orchestra-approved** (eatjurisha 3, albaik 2).
- Gates BITE (`pre_ship_gate` — **343/624 retrospective kill rate on historical captions**, exits
  non-zero). 94-chain prompts build from real organs (no stubs). The 5 CD brains fire
  (metaphor/paradox/firaasa/authenticity). Photo grounding correct.
- **Kills are a LEARNING signal, not just a filter** — they feed `kill_registry.py` (+ `competitor_request.py`
  rival-token kills), so each rejection teaches the brain what to avoid on the next run (Rule #14).
- The 3 contracts + `brain_api` + `openapi.yaml` + caption banking + e2e tests done (C201–C215).

## What's BROKEN (the honest gaps — don't paper over them)
- **Model fabric collapsed:** gemini 429-dead, groq 403-dead, Anthropic credits $0, **HUMAIN flaky →
  captions are GPT-only (the Arabic moat is at risk).** Fixed the false-green gate; reliability is the next fix.
- **4/9 posts render-money-blocked** (albaik 3rd needs a re-render; myfitness 3 need renders from scratch).
- No production infra (no Neo4j/Grafana/Prometheus/n8n) — **and we don't need it** (the devs own that).

## What to KEEP from the big spec
The **3-layer concept** (Knowledge/Intelligence/Action), the **5-gate philosophy**, **never-score-with-the-
generating-model** (Rule #13), **files-are-truth / DB-is-index**. We already built these in miniature.

## THE GOAL (the only mission)
**9 full approved posts** (3 each × albaik/eatjurisha/myfitness) → a **connectable, tested,
production-ready BRAIN** the devs plug into. Everything else is noise until the loop is proven.

## The trap
The 50-client spec is *seductive* — it would have us building Grafana dashboards and a knowledge graph
while HUMAIN still can't reliably write a Saudi caption. RABIE's words: a **credibility bomb**. Prove the
loop first.
