# 🚨 PROBLEMS TREE
# All P1-P10 resolved or accepted
# Last updated: 2026-06-06
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

## STATUS: ALL RESOLVED ✅

| # | Problem | Status | Fix |
|---|---------|--------|-----|
| P1 | Template library didn't exist | ✅ FIXED | `scripts/build_template_library.py` → 1,383 templates |
| P2 | No unified content pipeline | ✅ FIXED | `POST /api/create` — brain + templates + quality gate + proof |
| P3 | Quality gate not a module | ✅ FIXED | `scripts/lib/quality_gate.py` — importable, 10 checks |
| P4 | Sector names inconsistent | ✅ FIXED | All brand_profiles use canonical names |
| P5 | Brand profiles missing for 8 brands | ✅ FIXED | All 23 verified brands have profiles |
| P6 | Product names: only 3 of 23 | ✅ FIXED | `scripts/build_product_names.py` → all 23 brands |
| P7 | Sector facts stale | ✅ FIXED | `scripts/rebuild_sector_facts.py` — counts match files |
| P8 | 2 sectors have zero real data | ✅ ACCEPTED | Generated templates only for real_estate + healthcare |
| P9 | Fashion + retail in same folder | ✅ ACCEPTED | Keep structure — sector field in JSON is correct |
| P10 | Only 31 reel observations | ✅ ACCEPTED | Documented in honest_gaps |

---

## NEWLY FOUND + FIXED (2026-06-06)

| # | Problem | Status | Fix |
|---|---------|--------|-----|
| P11 | 40 obs files failing validate_all | ✅ FIXED | Added 8 fields to observation_v1.schema.json |
| P12 | white_friday + singles_day missing from system | ✅ FIXED | Added to occasion_calendar, required_words, template_library |
| P13 | Caption intelligence only 2 brands | ✅ FIXED | Expanded to 7 brands (+ barnscoffee, tamimimarkets, mikyajy, mcdonaldsksa, hashibasha) |
| P14 | founding_day had only 1 gold template | ✅ FIXED | Extracted 16 more from real obs → 2 gold total |
| P15 | hajj_season had only 2 gold templates | ✅ FIXED | Extracted 46 more from real obs → 4 gold total |
| P16 | API running old binary after commits | ✅ DOCUMENTED | Always kill+restart after api/server.py changes |
| P17 | BASE not defined in /api/create | ✅ FIXED | commit cbfb98c1 |
| P18 | intel not module-level in server.py | ✅ FIXED | commit cbfb98c1 |

---

*See [14_BUILD_ORDER](14_BUILD_ORDER.md) — foundation complete.*
