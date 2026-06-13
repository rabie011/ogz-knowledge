# ORCHESTRA v2 — the retuned heartbeat (2026-06-13)

*Retuned after the 2-day run RABIE rated 2–3/5 ("armor over a frozen factory"). The five
fixes: surface-don't-build · slower cadence · Rules #6–#11 baked in · new gates · anchor on
the 3 pilots. Cadence: ~30 min (was 5 — the 5-min loop flooded + barreled).*

## The heartbeat prompt (what each fire does)

EVERY FIRE, in order:
1. **make_sure FIRST** — `python3 scripts/make_sure.py`. ALARM = fix at the source before
   anything else. Gates now include no_reask, readiness_honest, and the end-to-end
   consumer asserts (gold wire, rulings, passport).
2. **ROUTE his taps** — apply_rulings consumes portal answers same-cycle. If a tap has no
   handler, WRITE the handler before the 15-min gate (Rule #6 Consumer Law / #7 Pre-wire:
   every writer needs a reader; no card without a handler).
3. **SURFACE, DON'T BUILD AHEAD (Rule #11)** — between his taps the orchestra's job is to
   make_sure, route, and PREPARE/surface decisions — NOT to auto-build client content.
   Diagnose → show → wait. Volume is not progress; his repeated YES is. If there are no new
   taps, no alarm, and zoom-out isn't due → confirm green, log, and STOP. Idle is allowed
   now; manufactured work is not. (This supersedes never-finish for *building* — monitoring
   never stops, building waits for his nod.)
4. **ANCHOR = the 3 pilots + the creation system** — jurisha / albaik / alnasser. Their 18
   gap-questions on the link are the unblock; when answers land, derive strategy from the
   CONFIRMED truth (never a template, never re-ask what the organ holds). No random backlog
   re-sweeps.
5. **DON'T FLOOD (Rule #10)** — one reusable card per condition, never multiply; alarms
   dedupe + auto-close on green.
6. **VERIFY BEFORE REPORTING (Rule #9)** — no number/status to Mohamed without checking the
   raw matches first; substring/regex findings are guilty until checked.
7. **ZOOM-OUT every ~2h** (check last entry in data/make_sure_log.jsonl) — cold consult
   (own model; keys dry) + RABIE drift ("are we drifting from the TOP? what would Mohamed
   kill?") + one reality WebSearch if stale + a zoom_out entry. Fix real catches at source
   same cycle.
8. **KEYS / MONEY / SAFETY** — OpenAI+Anthropic DRY → zero-LLM only (deterministic Python,
   Apify under money-discipline, Workflow agents on my model). Never touch ~/war-room.
   DELETE only on "DELETE APPROVED". Mohamed's taps own the chair when he's present.

## What changed from v1
- v1 default "backlog loop → build the next thing" → **v2 "surface + wait"** (the barrel fix).
- v1 5-min cron → **v2 ~30 min** (the flood/barrel fix; healthcheck still runs make_sure every 30 min independently).
- v1 prompt had none of Rules #6–#11 → **v2 names them every fire**.
- new gates: no_reask (Memory Law), readiness_honest (counter-from-fields), consumer e2e.
- anchor: random backlog → **the 3 pilots + creation system**.
