#!/usr/bin/env bash
# launchctl helpers for modern macOS (bootstrap/bootout) with legacy load/unload fallback.
set -euo pipefail

mac_launchctl_domain() {
  echo "gui/$(id -u)"
}

# Disable (park) a LaunchAgent by label. plist path optional but helps legacy unload.
mac_launchctl_disable() {
  local label="$1"
  local plist="${2:-$HOME/Library/LaunchAgents/${label}.plist}"
  local domain
  domain="$(mac_launchctl_domain)"

  if launchctl print "${domain}/${label}" &>/dev/null; then
    launchctl bootout "${domain}" "$plist" 2>/dev/null || \
      launchctl bootout "${domain}/${label}" 2>/dev/null || true
  fi
  launchctl unload "$plist" 2>/dev/null || true
}

# Enable (load) a LaunchAgent. Copies plist to LaunchAgents if src provided.
mac_launchctl_enable() {
  local label="$1"
  local src_plist="${2:-}"
  local dest="$HOME/Library/LaunchAgents/${label}.plist"
  local domain
  domain="$(mac_launchctl_domain)"

  if [[ -n "$src_plist" && -f "$src_plist" ]]; then
    cp "$src_plist" "$dest"
  fi

  if [[ ! -f "$dest" ]]; then
    echo "WARN: missing plist for $label ($dest)" >&2
    return 1
  fi

  mac_launchctl_disable "$label" "$dest"

  if launchctl bootstrap "$domain" "$dest" 2>/dev/null; then
    return 0
  fi

  launchctl load "$dest"
}

mac_launchctl_loaded() {
  local label="$1"
  launchctl print "$(mac_launchctl_domain)/${label}" &>/dev/null
}
