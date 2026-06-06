# OGZ CONTENT INTELLIGENCE — SYSTEM MAP
# The master overview. Each branch links to its own deep tree.
# Open this first. Then open the branch you need today.
# Last updated: 2026-06-06 | Brain v4.0 | Foundation complete

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
| 01 | [DATA](00_system/01_DATA.md) | 3,816 obs, 61 brands, 23 with real metrics | ✅ |
| 02 | [BRAIN](00_system/02_BRAIN.md) | v4.0 — 18 sections, 52 profiles, 7 brand caption intelligence | ✅ |
| 03 | [ARABIC](00_system/03_ARABIC.md) | Saudi dialect, markers, style transfer, emoji/length rules | ✅ |
| 04 | [BRANDS](00_system/04_BRANDS.md) | 52 profiles, all 23 verified brands have product names | ✅ |
| 05 | [OCCASIONS](00_system/05_OCCASIONS.md) | 10 Saudi occasions (incl. white_friday, singles_day) | ✅ |
| 06 | [VISUALS](00_system/06_VISUALS.md) | Colors, composition, lighting, content type performance | ✅ |
| 07 | [TEMPLATES](00_system/07_TEMPLATES.md) | 1,383 templates (148 gold, 378 silver, 656 bronze, 201 generated) | ✅ |
| 08 | [ENGINE](00_system/08_ENGINE.md) | POST /api/create — 99.9% pass rate across 7,596 real runs | ✅ |
| 09 | [QUALITY](00_system/09_QUALITY.md) | scripts/lib/quality_gate.py — 10 checks, all 23 brands pass | ✅ |
| 10 | [API](00_system/10_API.md) | 21 endpoints on port 4100 | ✅ |
| 11 | [INFRA](00_system/11_INFRA.md) | 226 scripts, DB, schemas, ML model, tracking system | ✅ |
| 12 | [ARCHIVE](00_system/12_ARCHIVE.md) | 4-tier storage, 61 brands, reprocessing | ✅ |
| 13 | [PROBLEMS](00_system/13_PROBLEMS.md) | All P1-P18 resolved or accepted | ✅ |
| 14 | [BUILD ORDER](00_system/14_BUILD_ORDER.md) | Foundation complete — 6-month roadmap next | ✅ |

---

## CURRENT STATE (June 6, 2026)

```
DATA:        3,816 obs | 61 brands archived | 23 with real metrics | validate_all 0 errors
BRAIN:       v4.0 | 18 sections | 52 profiles | 7 caption intelligence | 10 occasions
TEMPLATES:   1,383 templates (148 gold | 378 silver | 656 bronze | 201 generated)
             Occasions: evergreen, ramadan, eid×2, hajj, national_day, founding_day,
                        riyadh_season, jeddah_season, white_friday, singles_day
ENGINE:      POST /api/create — 99.9% pass (7,596 runs, Pass 1 complete)
QUALITY:     scripts/lib/quality_gate.py — 10 checks, all 23 brands pass
API:         21 endpoints on port 4100
DB:          Postgres Docker + pgvector | 3,816 obs synced
TRACKING:    logs/system/ — TEST_RESULTS.jsonl, MISTAKE_LOG.md, IMPROVEMENT_DELTA.md
TAG:         v1.0.0-seed-week1 — pending Pass 2 approval by Mohamed
```

---

## SESSION START — WHERE TO BEGIN

If **starting fresh** → read `logs/system/PLAN_STATUS.md` first
If **fixing broken things** → open [13_PROBLEMS](00_system/13_PROBLEMS.md)
If **building something new** → open [14_BUILD_ORDER](00_system/14_BUILD_ORDER.md)
If **checking test results** → `python3 scripts/deep_test_loop.py --report`
If **working on Arabic quality** → open [03_ARABIC](00_system/03_ARABIC.md)
If **working on a specific brand** → open [04_BRANDS](00_system/04_BRANDS.md)

---

## THE 5 RULES (never skip)

1. Read this map before starting any work
2. Run `python3 scripts/verify_ship_ready.py` before claiming done
3. Update memory + operator state before ending session
4. Never delete without "DELETE APPROVED" from Mohamed
5. Claude never says "done" — Mohamed runs verify commands himself
