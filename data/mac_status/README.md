# Mac status snapshots (pushed from Mac Mini)

Cloud agents and Cursor mobile read these files for **live Mac truth**.

| File | Purpose |
|------|---------|
| `sync_meta.json` | Last sync time, hostname, LaunchAgent states, git sha |
| `latest.txt` | Copy of `data/unified_status.txt` at last sync |

Updated by `scripts/mac_sync.py` on the Mac every 5 minutes (`com.ogz.mac-sync`).

If `sync_meta.json` is missing or older than ~15 minutes, the Mac is offline or sync is not installed.

Install: `./scripts/mac_onboard.sh` on the Mac.
