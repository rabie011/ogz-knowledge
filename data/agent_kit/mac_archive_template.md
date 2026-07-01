# Mac archive — create once

```bash
mkdir -p ~/OGZ-Archive/agents/{PROPOSALS,CREATIVE}
```

Per run (automated by `archive_run.py`):

```
~/OGZ-Archive/agents/PROPOSALS/2026-07-01_{run_ulid}/
├── manifest.json
├── inputs/
├── outputs/
└── events.jsonl
```

`manifest.json` links to Google Drive folder when uploaded.
