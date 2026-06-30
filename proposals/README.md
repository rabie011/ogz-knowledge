# ogz-proposals (scaffold)

**Status:** scaffold in `ogz-knowledge` — split to `~/Desktop/ogz-proposals` on Mac when ready.

Proposal engine separate from THE BRAIN. Control = Cursor mobile/Mac.

## Split to new repo (on Mac)

```bash
cd ~/Desktop
cp -R ~/Desktop/ogz-knowledge/proposals ogz-proposals
cd ogz-proposals
git init
git add .
git commit -m "feat: initial ogz-proposals scaffold"
```

Then copy live code from `~/agents`:

| From `~/agents` | To `ogz-proposals` |
|-----------------|-------------------|
| `router.py` | `lib/router.py` |
| `proposal_agent.py` | `scripts/proposal_agent.py` |
| `knowledge/clients/*.md` | `knowledge/clients/` |
| `prompts/proposal_agent.md` | `prompts/` |
| `OGZ-Reference-Proposals/` | `knowledge/reference/` (subset) |

## PR plan

See `../data/cursor_missions/artifacts/PROPOSAL_TRACK_PR_PLAN.md`

## Layout

```
proposals/
├── AGENTS.md
├── requirements.txt
├── lib/router.py          # stub — replace from ~/agents
├── scripts/
│   ├── setup_dev_env.sh
│   ├── drive_auth_check.py
│   ├── drive_list.py
│   └── proposal_to_slides.py
├── knowledge/clients/     # client bibles
├── prompts/
└── data/                  # drive_manifest.json (gitignored secrets)
```

## Brain link (optional)

`BRAIN_API_URL=http://127.0.0.1:4140` for brand DNA during proposals.
