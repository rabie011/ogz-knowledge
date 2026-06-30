#!/bin/bash
# Source ~/.abraham_env into the current shell (export all KEY=VALUE lines).
set -a
ENV_FILE="${HOME}/.abraham_env"
if [[ -f "$ENV_FILE" ]]; then
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *"="* ]] && continue
    line="${line#export }"
    key="${line%%=*}"
    key="${key#export }"
    val="${line#*=}"
    val="${val%\"}"; val="${val#\"}"
    export "$key=$val"
  done < "$ENV_FILE"
fi
set +a
