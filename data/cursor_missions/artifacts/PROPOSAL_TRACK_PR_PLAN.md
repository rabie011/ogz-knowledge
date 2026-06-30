# Proposal Track — PR Plan (draft)

**Status:** waiting on Mohamed **go**  
**Decision:** proposals first · new clean repo for proposal tooling · brain stays in `ogz-knowledge`

---

## Source inventory (`~/agents` — merge into new repo)

| Asset | Path | Notes |
|-------|------|-------|
| Free-first router | `~/agents/router.py` | Groq → OpenRouter → Gemini → paid |
| Proposal pipeline | `~/agents/proposal_agent.py` | strategy → proposal → quality gate |
| PPTX generator | `~/agents/proposal_pptx.py` | ROSHN template — migrate to **Slides** |
| Client knowledge | `~/agents/knowledge/clients/*.md` | ROSHN, NHC, etc. |
| Gold proposals | `~/agents/OGZ-Reference-Proposals/` | Amira-quality reference JSON |
| Brand extracts | `~/agents/knowledge/ogz_brand/full_*.json` | Parsed proposal structures |
| Prompts | `~/agents/prompts/proposal_agent.md` | |
| Orchestrator hook | `~/agents/orchestrator_daemon.py` | `run_proposal()` — simplify for Cursor on-demand |

**Do not copy:** Qdrant/mem0 empire, Telegram delivery, old orchestra daemons (Cursor = control).

---

## PR 0 — Create new repo (after you name it)

Suggested: `ogz-proposals` under `~/Projects/` or `~/Desktop/`

- [ ] `git init`, `AGENTS.md`, `requirements.txt` (router + google-api deps)
- [ ] `scripts/setup_dev_env.sh` (mirror ogz-knowledge pattern)
- [ ] Copy + adapt: `router.py`, `proposal_agent.py` (strip Telegram, add Cursor output)
- [ ] `knowledge/` — client bibles + reference proposals (subset)
- [ ] Link to brain: `BRAIN_API_URL=http://127.0.0.1:4140` optional for brand context

---

## PR 1 — Google Drive (Step 1 unlock)

- [ ] Google Cloud project + service account
- [ ] Share Drive folders with SA email:
  - Amira proposal templates
  - Quotations / pricing sheets
- [ ] Scopes: Drive read + Google Slides create/edit
- [ ] `scripts/drive_list.py` — list folders, print file IDs
- [ ] `scripts/drive_auth_check.py` — verify access (no secrets in repo)
- [ ] Credentials path: `~/.abraham_env` or `~/.config/ogz/google_sa.json` (gitignored)

**Deliverable:** markdown manifest `data/drive_manifest.json` — file names, IDs, types.

---

## PR 2 — Slides output (replace PPTX path)

- [ ] `scripts/proposal_to_slides.py` — copy Amira template deck by ID, fill placeholders
- [ ] Output: Slides URL returned to Cursor chat (not Telegram)
- [ ] Mohamed approves in Cursor before share

---

## PR 3 — End-to-end on-demand loop

```
Cursor: "ROSHN Q3 campaign proposal"
  → read Drive manifest + quotations
  → router.py (free-first)
  → proposal_agent (adapted)
  → Slides link
  → Mohamed approves in Cursor
```

---

## PR 4 — Archive `~/agents`

- [ ] README in `~/agents`: ARCHIVED — see `ogz-proposals` + `ogz-knowledge`
- [ ] Unload any `~/agents` launchd jobs not already parked

---

## Mohamed gates

- Drive folder IDs / SA key share
- **go** per PR
- Approve Slides before client send
- No autonomous client email

---

## ogz-knowledge unchanged in PR 1–2

Brain, pilots, render stay. New repo calls brain only if we want brand DNA in proposals (optional PR 3b).
