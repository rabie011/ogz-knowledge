# AGENTS.md — ogz-proposals

**Control:** Cursor (mobile + Mac). **Brain:** `ogz-knowledge` on Mac :4140 (optional).

## Run on Mac

```bash
cd ~/Desktop/ogz-proposals
./scripts/setup_dev_env.sh
python3 scripts/drive_auth_check.py   # after SA key installed
```

## Credentials (never commit)

- `~/.config/ogz/google_sa.json` — Google service account
- `~/.abraham_env` — API keys for router (Groq, etc.)

## Output

Google Slides URL returned in Cursor chat — Mohamed approves before client send.

## Do not copy from old `~/agents`

- Qdrant/mem0 empire
- Telegram delivery
- Orchestra daemons
