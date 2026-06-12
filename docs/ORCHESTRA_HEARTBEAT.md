# THE ORCHESTRA HEARTBEAT (B245, June 12)
*Doc-truth: written from the running mechanism, not from intention.*

## What it is
A CronCreate heartbeat (~5 min, session-scoped) re-fires the week-mode prompt into the
live Claude session. Born June 11 from Mohamed's correction («i didnt text for 10 mintus
why you did not keep working») then tightened to 5 minutes by his order: intention is not
a machine — the heartbeat is.

## What every fire does, in order
1. **make_sure.py FIRST** — hard evidence (grinder/coverage, guards gauntlet, portal 200,
   commits flowing, orchestrator_alive). ALARM = fix before anything; it also refreshes
   the im-here package every cycle.
2. **Mid-cycle work continues** (a running regen/build owns the slot).
3. Otherwise **BACKLOG LOOP**: RABIE picks (visible dialogue, he owns WHAT), Claude
   executes with asserted plants, numbered verdict (builds clamp to 3 without
   Mohamed-eyes), backlog updated, commit.
4. **Every ~2h**: zoom-out ritual — cold_consult (outside eyes) → triage with RABIE
   (real = fix at source; noise = log) → drift question → optional reality search →
   zoom_out entry in make_sure_log.jsonl.

## Degraded modes (all proven live, June 12)
- **done ≠ dead**: full year-map coverage ends the grinder honorably (no false alarm).
- **zero-LLM mode** (both keys dry): guards/tests/metrics/portal/telegram keep running;
  renders + RABIE + cold eyes park; key probes every fire; refill resumes automatically
  from the parked retry queue. Chair offline → solo picks logged PROVISIONAL-pending-chair.
- **Mohamed-musts never block**: anything needing his hands becomes a portal card and
  work moves on (the classifier-walled launchctl installs are the canonical example).

## Session-independence (the heartbeat's own safety net)
The heartbeat dies with the session. What survives it:
- com.abraham.orchestrator (queue + schedule incl. 05:30 crystallize harvest) — plist
  staged, Mohamed's paste installs.
- com.ogz.healthcheck — make_sure every 30 min with NO session; alarms reach the portal
  and Telegram regardless. Same paste.

## Recovery
New session → read ~/claude_operator_state/CURSOR.md (live state, updated mid-session) →
the week-mode prompt re-enters the loop. The backlog, queues, and logs are all on disk;
the heartbeat has no memory of its own by design.
