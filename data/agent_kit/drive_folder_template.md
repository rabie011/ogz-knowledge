# Google Drive — create once

Share each folder with the service account email.

```
OGZ Agents/                          ← drive_root (save folder ID in _manifest.json)
├── _manifest.json
├── PROPOSALS/
│   ├── templates/
│   ├── quotations/
│   └── archive/
│       └── {client_slug}/
│           └── {yyyy-mm}/
├── CREATIVE/
│   └── archive/
└── SHARED/
    ├── brand/
    └── clients/
```

After creation, run on Mac:

```bash
cd ~/Desktop/ogz-proposals
python3 scripts/drive_list.py
```

Writes `data/drive_manifest.json` with file IDs only.
