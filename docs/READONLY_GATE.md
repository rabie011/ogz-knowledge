# Read-only gate — cloud reads brain state, never writes (`:4160`)

**Status:** Mohamed said **read only** (2026-07-19) · wire mission `readonly-wire-go` queued
Updated: 2026-07-19

---

## Purpose

Give cloud sessions (and tailnet devices) a way to **read** Mac brain state without any
mutation surface. The gate is a GET-only proxy in front of the brain — decision **RO1**.

| Port | Service |
|------|---------|
| `:4140` | Brain API (`brain_api.py`) — local + tailnet, full surface |
| `:4150` | Mac Bridge — diagnostics (see [MAC_BRIDGE.md](MAC_BRIDGE.md)) |
| `:4160` | **Read-only gate** (`readonly_gate.py`) — GET-only, this doc |

## Surface (complete)

| Route | Auth | Source |
|-------|------|--------|
| `GET /health` | open (liveness) | gate + brain `/health` |
| `GET /status` | Bearer | `data/unified_status.json` from disk |
| `GET /job/<id>` | Bearer | proxied to brain `:4140` |

**Refused, always:** every POST/PUT/DELETE/PATCH, `/produce`, `/performance`, and
`/extract` (extract can trigger intake work — not read-only). Token does not matter;
writes are refused before auth is even considered.

Auth: `Authorization: Bearer <BRAIN_API_TOKEN>` from `~/.abraham_env` on Mac — **never commit**.
Token unset → gate fails closed (A7 pattern: random token, authed routes unusable).

## Exposure modes

The gate binds `127.0.0.1:4160` only. `scripts/mac_readonly_wire.sh` chooses exposure:

| Mode | Command | Who can reach it |
|------|---------|------------------|
| **tailnet** (default) | `./scripts/mac_readonly_wire.sh` | tailnet devices only |
| **funnel** (public HTTPS) | `OGZ_FUNNEL_GO=1 ./scripts/mac_readonly_wire.sh` | anyone with the URL (GET-only, token-gated beyond `/health`) |

**Funnel stays behind Mohamed's explicit "funnel go"** — the locked
[TAILSCALE_WIRE.md](TAILSCALE_WIRE.md) rule that public internet needs his gate is
unchanged. "Read only" (2026-07-19) authorized the read-only *surface*; tailnet-only
is the default wire until he says funnel.

Wire writes `data/readonly_endpoint.json` (host, mode, base_url — **no secrets**),
pushed via `mac_sync` so cloud sessions can discover the endpoint from the repo.

## Verify

```bash
# On the Mac:
curl -sf http://127.0.0.1:4160/health

# From cloud/tailnet after Mac pushes the manifest:
python3 scripts/readonly_probe.py            # /health
python3 scripts/readonly_probe.py /status    # needs BRAIN_API_TOKEN in env
```

## Pieces

- `scripts/readonly_gate.py` — the GET-only proxy server
- `scripts/mac_readonly_wire.sh` — tailscale serve (default) / funnel (gated) + manifest
- `scripts/readonly_probe.py` — cloud/tailnet-side probe via the manifest
- `deploy/launchagents/com.ogz.readonly-gate.plist` — KeepAlive LaunchAgent
- `data/cursor_missions/pending/readonly-wire-go.json` — one-shot wire mission

## Related

- [TAILSCALE_WIRE.md](TAILSCALE_WIRE.md) — tailnet wiring + the funnel gate rule
- [MAC_BRIDGE.md](MAC_BRIDGE.md) — diagnostics bridge `:4150`
- [CONNECT_THE_BRAIN.md](CONNECT_THE_BRAIN.md) — full brain API contracts + token
