# Mac Bridge — cloud ↔ Mac diagnostics (`:4150`)

**Status:** Documented from Mac wire session · verify files on GitHub `main`  
Updated: 2026-07-01

---

## Purpose

HTTP bridge on the Mac Mini so cloud conductor (and tailnet devices) can read **Mac environment diagnostics** without SSH or API keys in the cloud repo.

| Port | Service |
|------|---------|
| `:4140` | Brain API (`brain_api.py`) |
| `:4141` | Live feed (Mac debug) |
| `:4150` | **Mac Bridge** — diagnostics, queue snapshot, key *presence* only |

---

## Endpoint manifest

After wire: `data/mac_status/remote_endpoint.json`

```json
{
  "host": "abarihms-mac-mini.tail174530.ts.net",
  "ports": { "brain": 4140, "feed": 4141, "bridge": 4150 }
}
```

Auth: `Authorization: Bearer <MAC_BRIDGE_TOKEN>` from `~/.abraham_env` on Mac — **never commit**.

---

## Cloud conductor usage

1. Read `data/mac_status/remote_endpoint.json` from GitHub after Mac sync
2. Read `data/cursor_missions/artifacts/mac_diagnostic_latest.json` (pushed each sync)
3. Queue missions — do not call bridge directly from cloud unless cloud joins tailnet

---

## Mac scripts (when present on Mac)

- `scripts/mac_bridge.py` — bridge server
- `deploy/launchagents/com.ogz.mac-bridge.plist` — LaunchAgent
- Diagnostics land in `data/cursor_missions/artifacts/mac_diagnostic_latest.json`

If these files are missing on `main`, Mac agent must commit and push from local wire session.

---

## Related

- [TAILSCALE_WIRE.md](TAILSCALE_WIRE.md)
- [CURSOR_ONLY.md](CURSOR_ONLY.md)
- [CONNECT_THE_BRAIN.md](CONNECT_THE_BRAIN.md)
