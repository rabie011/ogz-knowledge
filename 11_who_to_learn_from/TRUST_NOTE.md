# TRUST NOTE — accounts layer (2026-06-12)

handles in account files came from the benchmarks xlsx and include sub_category_template provenance — part-synthetic, NEVER live-verified (5/5 shortlist picks failed live checks; mangling pattern: leading chars stripped). Treat handle_internal as UNVERIFIED until a live verification record exists. The 6,888 obs layer is real (scrape provenance).

## Verification sweep results (2026-06-12 ~23:45)
- 109 internal handles checked LIVE: **63 verified · 46 DEAD (42%)** — the mangling
  signature corpus-wide (donalds_sa = mcdonalds, bare `_`, `---`, prefix-eaten names).
- Obs cross-check: of the obs-bearing brands that map to internal handles (15/60 — the
  normalized↔internal join is itself lossy), **zero are dead**. The obs layer keeps its
  trust; the accounts layer keeps its quarantine; the join needs repair on key refill.
- Full verdicts: handle_verification.json
