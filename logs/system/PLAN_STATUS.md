# PLAN STATUS — OGZ Knowledge Foundation + Deep Test Loop
# Updated by Claude. Verified by Mohamed.
# Source of truth: logs/system/
# Rule: Claude marks [DONE] only after verify command exits 0.
#       Mohamed marks [APPROVED] after reading the result himself.

---

PHASE A: FIX FOUNDATION
  [DONE 2026-06-06] A1: Schema fix — validate_all exits 0 (exit code: 0, 0 error lines)
                        Verify: cd ~/Desktop/ogz-knowledge && python3 scripts/validate_all.py 2>&1 | tail -3
  [DONE 2026-06-06] A2: Product names — all 23 brands have correct/wrong lists
                        Verify: python3 scripts/build_product_names.py --verify
  [PENDING]         A3: sync_to_supabase.py committed to git

PHASE B: DEEP TEST LOOP
  [DONE 2026-06-06] B1: scripts/deep_test_loop.py written + smoke-tested (6 runs, 100% pass)
  [RUNNING]         B2: Pass 1 — full run in background (7,590 calls)
  [PENDING]         B3: Pass 2 — after brain updates from Pass 1 failures
  [PENDING]         B4: Pass 3 — all 14 occasions ≥150 passing tests

PHASE C: TAG
  [PENDING]         C1: verify_ship_ready exits 0
  [PENDING]         C2: validate_all exits 0
  [NEEDS HUMAN]     C3: Mohamed reads MISTAKE_LOG.md + IMPROVEMENT_DELTA.md
  [PENDING]         C4: git tag v1.0.0-seed-week1  ← Claude does NOT do this automatically

PHASE D: DOCS
  [PENDING]         D1: SYSTEM_MAP.md updated
  [PENDING]         D2: 00_system/13_PROBLEMS.md — all marked resolved
  [PENDING]         D3: 00_system/14_BUILD_ORDER.md — FOUNDATION COMPLETE
