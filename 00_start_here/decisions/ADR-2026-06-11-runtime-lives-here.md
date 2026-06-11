# ADR: The runtime lives in ogz-knowledge (not a separate repo)
Date: 2026-06-11 · Status: DRAFT — awaiting Mohamed's confirm note
Reality vs docs: README/AGENT_MANIFEST describe a separate ogz-runtime repo + a
"Memory Controller" single-write-path + a 6-agent C-Suite. NONE exist. The actual
runtime is HERE: api/server.py (FastAPI :4100), scripts/ pipelines, the enricher
daemon (auto-commits to main, gated on validate_all). git log --merges = 0 (all
commits land on main directly). Decision: document the real architecture; the
C-Suite agent prompts (10_agent_brains/) are PLATFORM-SPEC-ONLY orphans, kept for
the future managed-services platform, consumed by nothing today.
