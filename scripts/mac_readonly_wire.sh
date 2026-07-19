#!/usr/bin/env bash
# Expose the read-only gate :4160 (Mac only). Gate stays on 127.0.0.1 locally.
# Default: tailnet-only (tailscale serve). Public funnel ONLY with OGZ_FUNNEL_GO=1 —
# that flag is Mohamed's gate; do not set it from a mission without his explicit go.
# Writes data/readonly_endpoint.json for cloud/tailnet readers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TS="$(command -v tailscale || true)"
OUT="$ROOT/data/readonly_endpoint.json"
MODE="tailnet"
[[ "${OGZ_FUNNEL_GO:-0}" == "1" ]] && MODE="funnel"

if [[ -z "$TS" ]]; then
  echo "tailscale CLI not found — install Tailscale on Mac Mini first"
  exit 1
fi

if ! "$TS" status >/dev/null 2>&1; then
  echo "tailscale not connected — open Tailscale app and sign in"
  exit 1
fi

if [[ "$MODE" == "funnel" ]]; then
  # Public HTTPS at https://<mac>.tailXXXX.ts.net → 127.0.0.1:4160 (GET-only gate)
  "$TS" funnel --bg 4160 2>/dev/null || "$TS" funnel status 2>/dev/null || true
else
  # Tailnet-only TCP proxy (idempotent; ignore if already set)
  "$TS" serve --bg --tcp=4160 "tcp://127.0.0.1:4160" 2>/dev/null || \
    "$TS" serve status 2>/dev/null || true
fi

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
if curl -sf "http://127.0.0.1:4160/health" >/dev/null 2>&1; then
  HEALTH="ok"
fi

NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$(dirname "$OUT")"
MODE="$MODE" DNS_NAME="$DNS_NAME" HEALTH="$HEALTH" NOW="$NOW" OUT="$OUT" /opt/homebrew/bin/python3 - <<'PY'
import json, os
from pathlib import Path
mode, dns = os.environ["MODE"], os.environ["DNS_NAME"]
base = (f"https://{dns}" if mode == "funnel" else f"http://{dns}:4160") if dns else None
payload = {
    "ok": True,
    "readonly": True,
    "via": "tailscale funnel https" if mode == "funnel" else "tailscale serve tcp",
    "mode": mode,
    "host": dns,
    "port": 4160,
    "base_url": base,
    "health_url": f"{base}/health" if base else None,
    "routes": ["GET /health (open)", "GET /status (Bearer)", "GET /job/<id> (Bearer)"],
    "local_health": os.environ["HEALTH"],
    "auth": "Authorization: Bearer <BRAIN_API_TOKEN from ~/.abraham_env>",
    "wired_at": os.environ["NOW"],
    "notes": "GET-only gate; all writes refused. Funnel mode is public internet — Mohamed's gate (OGZ_FUNNEL_GO=1).",
}
out = Path(os.environ["OUT"])
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
PY

echo "Wrote $OUT ($MODE)"
