#!/usr/bin/env bash
# Expose brain :4140 on the Tailscale tailnet (Mac only). Brain stays on 127.0.0.1 locally.
# Writes data/brain_remote_endpoint.json for Cursor / other tailnet devices.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$(command -v tailscale || true)"
OUT="$ROOT/data/brain_remote_endpoint.json"

if [[ -z "$TS" ]]; then
  echo "tailscale CLI not found — install Tailscale on Mac Mini first"
  exit 1
fi

if ! "$TS" status >/dev/null 2>&1; then
  echo "tailscale not connected — open Tailscale app and sign in"
  exit 1
fi

# Proxy tailnet TCP 4140 → local brain (idempotent; ignore if already set)
"$TS" serve --bg --tcp=4140 "tcp://127.0.0.1:4140" 2>/dev/null || \
  "$TS" serve status 2>/dev/null || true

DNS_NAME="$("$TS" status --json 2>/dev/null | /opt/homebrew/bin/python3 -c "
import json,sys
try:
    j=json.load(sys.stdin)
    self=j.get('Self',{})
    dns=self.get('DNSName','').rstrip('.')
    ips=self.get('TailscaleIPs') or []
    print(dns or (ips[0] if ips else ''))
except Exception:
    print('')
" 2>/dev/null || true)"

if [[ -z "$DNS_NAME" ]]; then
  DNS_NAME="$("$TS" ip -4 2>/dev/null | head -1 || true)"
fi

HEALTH="fail"
if curl -sf "http://127.0.0.1:4140/health" >/dev/null 2>&1; then
  HEALTH="ok"
fi

NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$(dirname "$OUT")"
/opt/homebrew/bin/python3 - <<PY
import json
from pathlib import Path
out = Path("$OUT")
payload = {
    "ok": True,
    "via": "tailscale serve tcp",
    "host": "$DNS_NAME",
    "port": 4140,
    "health_url": f"http://{$DNS_NAME}:4140/health" if "$DNS_NAME" else None,
    "local_health": "$HEALTH",
    "auth": "Authorization: Bearer <BRAIN_API_TOKEN from ~/.abraham_env>",
    "wired_at": "$NOW",
    "notes": "Tailnet only — not public internet. Cloud Cursor needs Tailscale on same tailnet to call this.",
}
out.write_text(json.dumps(payload, indent=2) + "\\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY

echo "Wrote $OUT"
