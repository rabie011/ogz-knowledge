# HANDOVER — ogz-knowledge

Developer onboarding for the OGZ Studios Saudi creative-intelligence system. Read this first,
then `README.md` (build briefing) and `docs/` for deep dives. Last updated 2026-06-17.

---

## 1. What this is

A **file-first** knowledge base + content-creation system for Saudi-Arabic Instagram brands.
Files in this git repo are the **source of truth**; Postgres (`13_database/`) is an *index over*
the files, never the other way around. The system generates posts (caption + visual brief) for
pilot clients and captures the founder's creative **taste** as the moat.

**THE TOP (the one goal):** a creation system that (a) produces posts a client would publish and
(b) learns the founder's taste so the machine — not a human — picks what's good.

Three pilot clients: `eatjurisha`, `albaik`, `myfitness.sa` (+ `alnasserjewelry`, less complete),
under `clients/<handle>/`.

---

## 2. Quickstart

```bash
python3 -m pip install -r requirements.txt      # Python 3.11+ (built on 3.14)
python3 -m unittest discover -s scripts/tests -q # 106 tests, must stay green
python3 scripts/verify_ship_ready.py            # data-quality health check (see Known Issues #2)

# the feedback portal (the calibration UI the founder taps on):
python3 -m uvicorn api.portal_mini:app --port 4199 --host 127.0.0.1
#   → http://localhost:4199/approvals?k=<key>   (key lives in data/portal_team.json — see Security)
```

LLM keys are read from `~/.abraham_env` (NOT in this repo). OpenAI is the live pen; Anthropic
credits are depleted (see Known Issues #4). Most maintenance scripts are **zero-key** (pure Python).

---

## 3. Architecture — the loops

**Creation pipeline** (per client slot):
`client profile/organs` → `scripts/client_strategy.py` (CEO strategy) → `scripts/render_client_slot.py`
(the brain writes the caption, fed the client's confirmed organs) → `scripts/c_suite.py` /
`scripts/post_audit.py` (CCO judge + audits) → `scripts/produce_batch.py` (autonomous
pick→render→audit→backfill→select). Output: `clients/<handle>/posts/*.json`.

**The gates (armor)** — every post must pass, enforced at the source:
- `scripts/client_rules.py` — the client's confirmed organs as hard rules (cultural_overrides:
  no faces/family/real names, cloud-kitchen format, cross-brand bleed, brand-register, caption
  length drift-ceiling).
- `scripts/occasion_align.py` — caption must match the slot's occasion.
- `scripts/pre_ship_gate.py` — consumes the founder's learned rulings (`learned_gate_rules.json`).
- `scripts/make_sure.py` — the system-wide heartbeat health check (run it first, always).

**The taste-calibration loop (the moat)** — replaces a broken absolute 0-10 judge (it agreed with
the founder only 47%, below chance) with his own A-vs-B signal:
`scripts/pairwise.py` (forms/serves "which would you post?" pairs, **active-picks** the most
informative ones, consumes his taps) → `data/pairwise_prefs.jsonl` → `scripts/taste_elo.py`
(Bradley-Terry "Mohamed-Elo", pure numpy, no key) → `data/taste_elo.json`. The portal
(`api/portal_mini.py` + `api/static/approvals.html`) shows ONE pair at a time, in scene-context,
with instant honest feedback after each tap.

**The orchestra** — a persistent scheduled task (`~/.claude/scheduled-tasks/rabie-orchestra/`)
that works `data/backlog.json` (276 steps, ~123 todo) every 30 min: health-check → route taps →
do one backlog step → test → log. See `docs/ORCHESTRA_v2.md`.

---

## 4. Key files

| Path | Role |
|---|---|
| `scripts/render_client_slot.py` | the brain — generates a caption from the client's organs |
| `scripts/produce_batch.py` | autonomous batch producer (pick→render→audit→backfill→select) |
| `scripts/pairwise.py` | taste calibration: form/push/consume/active-pick |
| `scripts/taste_elo.py` | model-free Mohamed-Elo from his pairwise picks |
| `scripts/client_rules.py` | the organ gate (cultural/format/register/length rules) |
| `scripts/make_sure.py` | system heartbeat health check — **run first** |
| `scripts/verify_ship_ready.py` | data-quality ship gate (exit 0 = clean) |
| `api/portal_mini.py` + `api/static/approvals.html` | the feedback portal (FastAPI) |
| `scripts/tests/` | 106 unit tests — keep green |
| `12_data_shapes/` | **frozen v1 JSON schemas** (the contracts) — don't change without sign-off |
| `clients/<handle>/profile/` | per-client organs (the confirmed truth the brain uses) |
| `data/backlog.json` | the prioritized improvement backlog |

---

## 5. Known issues & gotchas (read before you trust anything)

1. **🔴 Secrets in git history.** `data/portal_team.json` (plaintext portal key) and
   `data/portal_keys.json` (hashes) were tracked and pushed; they're now gitignored + removed from
   the current tree, **but they remain in git history (2 commits).** The portal key MUST be rotated;
   consider a history scrub (`git filter-repo`) before widening access. Local copies are kept so the
   running portal still works.
2. **`verify_ship_ready.py` exits non-zero** — 18 client-organ schema-validation failures. The
   organs grew real fields (e.g. `kill_patterns`, which `render_client_slot.py` consumes) that the
   frozen `12_data_shapes` organ schemas don't allow. Fix = loosen the organ schemas to match the
   live organs (or move the fields). Frozen-schema change → needs the owner's sign-off.
3. **The `enricher` daemon auto-commits the whole repo hourly** (as the git user, `git add -A`
   style) and does NOT push. So local commits aren't gated; only `git push` is. Don't be surprised
   by "auto: enricher — analytics" commits you didn't make.
4. **Anthropic credits are depleted** — the 2nd caption pen (sonnet) is dark; the diversity engine
   runs on the one live pen (OpenAI/gpt) via the DOORS mechanism in `render_client_slot.py`. Prefer
   zero-LLM (pure Python) for maintenance.
5. **elo→creation is not wired yet.** `taste_elo.json` is computed and surfaced (instant tap
   feedback) but does not yet *steer* generation. That wire is the next milestone, gated on the
   founder finishing the calibration set (~17 pairwise picks).
6. **`held_out_agreement_pct` is degenerate** while the pilot pair-graph is disconnected (rescued
   seed pairs carry it to 100%). Use `held_out_live_pct` / `held_out_live_n_testable` — the honest
   live-only numbers. Never quote 100% as "the judge agrees with the founder."

---

## 6. Conventions

- Validate before commit: `python3 scripts/validate.py <record.json> <schema.json>`.
- Records carry provenance (source, date_added, confirmer, confidence, scope) and ULIDs.
- Append-only event logs; quarantine, not delete.
- Never hand-write output content (captions, hardcoded dates/selections) — the *system* produces;
  humans fix the machine and judge. See `~/CLAUDE.md` Rules #12/#13 if present.
- `~/war-room` is a separate project — never touched by this repo.
