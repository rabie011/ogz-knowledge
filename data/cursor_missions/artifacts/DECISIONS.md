# Decisions — 2026-06-30

## Mohamed confirmed

| Question | Choice |
|----------|--------|
| Repo home | **New clean repo** (not “keep ogz-knowledge only”) |
| First track | **Proposals** — Google Drive (Amira + quotations) then Slides |

## Architecture (recommended reconcile)

Two homes — avoids re-building the brain:

| Repo | Role |
|------|------|
| **`ogz-knowledge`** | THE BRAIN — `brain_api` :4140, 3 pilots, render, platform wire (stays) |
| **New repo (TBD name)** | Proposal engine — Drive, Slides, router, pipeline from `~/agents` |

`~/agents` is the current proposal/orchestra codebase (not a folder named `abraham-agents`). Archive after merge.

## Control surface

Cursor (mobile + Mac) — unchanged from Phase 0.

## Next step (waiting on **go**)

See `PROPOSAL_TRACK_PR_PLAN.md` — Step 1 = Google Drive service account + list Amira proposals + quotations.

## Advisor note

Other agent recommended keep single repo; Mohamed chose fresh repo for proposals. Brain stays in `ogz-knowledge` unless you explicitly want full migration.
