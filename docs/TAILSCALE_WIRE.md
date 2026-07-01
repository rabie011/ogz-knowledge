# Tailscale wire — Mac Mini ↔ tailnet (and optional cloud)

**Status:** Mohamed said **wire** (2026-07-01) · Mac mission `wire-go` queued  
Updated: 2026-07-01

---

## Goal

Let trusted devices on your **Tailscale tailnet** reach the brain API (`:4140`) without exposing it to the public internet.

| Device | How it talks to brain |
|--------|------------------------|
| **Your phone / Mac (on tailnet)** | `http://<mac-mini>.tailXXXX.ts.net:4140/health` + Bearer token |
| **Cursor cloud agent (this chat)** | **Not automatic** — cloud VM is not on your tailnet unless you add it |
| **Default control loop** | Still **GitHub** missions + `mac_sync` (works without Tailscale) |

---

## Security (locked)

- Brain stays bound to **`127.0.0.1`** on the Mac.
- Tailscale **`serve`** proxies tailnet → localhost only.
- **`BRAIN_API_TOKEN`** required for real routes (see `CONNECT_THE_BRAIN.md`).
- **No** `tailscale funnel` / public internet without Mohamed **`wire`** gate.

---

## Mac one-time wire (automatic via mission)

Mission: `data/cursor_missions/pending/tailscale-brain-wire.json`

Or run once on Mac:

```bash
cd ~/Desktop/ogz-knowledge
./scripts/mac_tailscale_wire.sh
MAC_SYNC_PUSH=1 python3 scripts/mac_sync.py --push
```

**Writes:** `data/brain_remote_endpoint.json` (hostname, port — **no secrets**)

---

## Cloud Cursor agent on Tailscale (optional — your gate)

Cursor cloud agents run on a **Linux VM** with **no Tailscale** today.

To let **this chat** call the Mac brain directly (faster than GitHub for health/consult):

1. Tailscale admin → **Settings → Keys** → generate **ephemeral** auth key  
2. Add to Mac `~/.abraham_env` (never commit): document only — cloud may need Cursor **Secrets** if supported  
3. On a machine you control, test:  
   `curl -sf -H "Authorization: Bearer $BRAIN_API_TOKEN" "http://<mac-mini-ts-name>:4140/health"`

**Until cloud joins tailnet:** I manage everything via **GitHub** (current model). Tailscale wires **you** and **future cloud node** to brain; it does not replace the mission bus.

---

## Verify

```bash
# On any tailnet device:
curl -sf -H "Authorization: Bearer <token>" "http://<mac-mini>:4140/health"
```

In Cursor: say **status** — read `data/brain_remote_endpoint.json` after Mac pushes.

---

## Related

- [CURSOR_ONLY.md](CURSOR_ONLY.md) — you talk only in Cursor  
- [CONNECT_THE_BRAIN.md](CONNECT_THE_BRAIN.md) — API contracts + token  
- [MOBILE_CONTROL.md](MOBILE_CONTROL.md) — phone uses GitHub status, not raw brain
