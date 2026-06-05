# OGZ CONTENT INTELLIGENCE — SYSTEM MAP
# The master overview. Each branch links to its own deep tree.
# Open this first. Then open the branch you need today.
# Last updated: 2026-06-05

---

## THE SYSTEM IN ONE SENTENCE
Saudi creative intelligence platform — proprietary real data + cultural knowledge
that makes Saudi brands produce better Arabic Instagram content, faster.

## THE MOAT
Real Saudi Instagram data (verified likes) + Saudi cultural intelligence
→ No competitor can buy this. It's built observation by observation.

---

## 14 BRANCHES — CLICK TO OPEN

| # | Branch | What's in it | Status |
|---|--------|-------------|--------|
| 01 | [DATA](00_system/01_DATA.md) | 3,816 obs, 61 brands, real metrics, coverage matrix | ✅ |
| 02 | [BRAIN](00_system/02_BRAIN.md) | intelligence_layer.json — all 18 sections deep | ✅ |
| 03 | [ARABIC](00_system/03_ARABIC.md) | Saudi dialect, markers, style transfer, emoji/length rules | ✅ |
| 04 | [BRANDS](00_system/04_BRANDS.md) | 39 profiles, DNA, product names, onboarding | ✅ |
| 05 | [OCCASIONS](00_system/05_OCCASIONS.md) | 8 Saudi occasions, timing, required words, coverage | ✅ |
| 06 | [VISUALS](00_system/06_VISUALS.md) | Colors, composition, lighting, content type performance | ✅ |
| 07 | [TEMPLATES](00_system/07_TEMPLATES.md) | 1,301 templates (148 gold, 378 silver, 656 bronze, 119 generated) | ✅ |
| 08 | [ENGINE](00_system/08_ENGINE.md) | POST /api/create — 48/48 sector×occasion combos pass | ✅ |
| 09 | [QUALITY](00_system/09_QUALITY.md) | scripts/lib/quality_gate.py — 21/21 brands pass | ✅ |
| 10 | [API](00_system/10_API.md) | 21 endpoints total (18 + /api/templates, /api/check, /api/create) | ✅ |
| 11 | [INFRA](00_system/11_INFRA.md) | 223 scripts, DB, schemas, ML model, lib modules | ✅ |
| 12 | [ARCHIVE](00_system/12_ARCHIVE.md) | 4-tier storage, 61 brands, reprocessing | ✅ |
| 13 | [PROBLEMS](00_system/13_PROBLEMS.md) | 10 broken things — exact location + fix | 🚨 read this |
| 14 | [BUILD ORDER](00_system/14_BUILD_ORDER.md) | What to build next, in order, with time estimates | 🔧 start here |

---

## CURRENT STATE (June 5, 2026)

```
DATA:       3,816 obs | 61 brands archived | 23 with real metrics | all fields ≥90%
BRAIN:      82KB | 18 sections | v3.0 | 52 profiles | 23 product name lists
TEMPLATES:  ✅ 1,301 templates (148 gold | 378 silver | 656 bronze | 119 generated)
ENGINE:     ✅ POST /api/create — 48/48 sector×occasion combos tested
QUALITY:    ✅ scripts/lib/quality_gate.py — 21/21 brands pass
API:        21 endpoints on port 4100 (+/api/templates, /api/check, /api/create)
DB:         Postgres Docker + pgvector running | 3,816 obs synced
TESTS:      phase1_test_loop.py — 100/100 × 5 consecutive iterations
```

## TODAY'S SESSION — WHERE TO START

If **fixing broken things** → open [13_PROBLEMS](00_system/13_PROBLEMS.md)
If **building something new** → open [14_BUILD_ORDER](00_system/14_BUILD_ORDER.md)
If **working on Arabic quality** → open [03_ARABIC](00_system/03_ARABIC.md)
If **working on a specific brand** → open [04_BRANDS](00_system/04_BRANDS.md)
If **working on templates** → open [07_TEMPLATES](00_system/07_TEMPLATES.md)

---

## THE 5 RULES (never skip)

1. Read this map before starting any work
2. Run `python3 scripts/verify_ship_ready.py` before claiming done
3. Update memory + operator state before ending session
4. Never delete without "DELETE APPROVED" from Mohamed
5. Every pipeline runs via orchestrator_daemon.py (never direct)
