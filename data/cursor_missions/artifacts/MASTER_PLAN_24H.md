# OGZ MASTER PLAN — 24/7 Autonomous System

> **Superseded by** [`MASTER_PLAN.md`](MASTER_PLAN.md) (2026-06-30). Kept for history.

Generated: 2026-06-30 · Cursor + DeepSeek + Claude history mining

## Mohamed's intent
Work **only from Cursor chat** with **Cursor + DeepSeek** running **24/7** until he texts.
Not one task — the **full system**: brain, platform, creative, knowledge, learning, agents.

---

## What 6 months of Claude Code built (extracted)

| Metric | Value |
|--------|-------|
| Commits (May–Jun 2026) | 832 |
| Backlog steps done | 291 / 347 |
| Three layers | BRAIN · BUILD MACHINE · DEV PLATFORM |
| Mission 9 posts | 9/9 HUMAIN-taste-grade (Jun 29) |
| Pilots ready | albaik · eatjurisha · myfitness (post render go) |
| Wire | Platform brain client + extraction-status route |

**Sources mined:** `claude-code-history-master.json`, `CURSOR.md`, `im_here.md`, `~/claude_operator_state/sessions/*`, `~/.claude/projects/.../memory/feedback_*.md`

---

## How you worked with Claude / GPT / DeepSeek

```
Mohamed (taste, money, wire)
    ↕
Cursor — plan, queue, status
    ↕
Claude Code — build on Mac Mini (code, organs, renders)
    ↔ RABIE (GPT-4o) — harsh taste proxy + vision judge
    ↔ DeepSeek — standing engineering consult (consult.py)
    ↔ HUMAIN — Saudi Arabic caption pen (:4111)
    ↕
make_sure → im_here → portal approvals
    ↕
backlog.json + rabie_verdicts.jsonl + orchestra_memory.json
```

**Standing method (Rules #2, #19):** THINK → SEARCH → PLAN → **CONSULT** → PLAN AGAIN → WORK → TEST → SAVE

---

## Top mistakes (scars) — never repeat

1. **Severed wires** — built but not consumed (Rule #6)
2. **Cards with no handler** — portal taps dead-end (Rule #7)
3. **Gates that whisper** — warn instead of refuse (Rule #8)
4. **Hand-curated posts** — system must produce (Rule #12)
5. **False "approved"** — verbal ≠ passed gate (Rule #13)
6. **Judge with no memory** — verdicts not persisted (Rule #14)
7. **Consult after build** — not before (Rule #19)
8. **Prose to DeepSeek** — until file-eyes (orchestra_tools)
9. **Hallucinated metrics** — verify numbers (Rule #9)
10. **Flooded Mohamed** — 20 urgent cards (Rule #10)
11. **Readiness hallucination** — 39/44 false PREPARED
12. **Session leak** — 174 headless claude processes
13. **iTerm / headless confusion** — executor visibility vs reasoning
14. **Home glob scan** — hung mission (never scan ~)
15. **Shell executor** — can't fix code when `fix_allowed` (naming lie)

---

## Honest gap today

**The executor is a shell runner, not a thinking agent.**

`executor_daemon` runs `commands[]` from JSON. It cannot intelligently fix failures.
True 24/7 **building** still needs either:
- **Live Claude Code** for `type: agent` missions, OR
- **Cursor Cloud Agent** / API executor with reasoning

**New split:**

| Mission type | Who runs it |
|--------------|-------------|
| `health` / `test` / `curl` | Shell executor (24/7 OK) |
| `agent` / `fix_allowed` code | Live Claude Code session OR future reasoning executor |
| `consult` / `plan` | Cursor + DeepSeek (every 15 min shift) |
| `creative` / `render` | RABIE + render pipeline (money-gated) |
| `research` | Search agent → staged knowledge |

---

## 24/7 architecture (target)

### Always-on daemons (Mac Mini)

| Daemon | Role | Interval |
|--------|------|----------|
| `com.ogz.orchestra` | Health, queue board, context refresh | 5 min |
| `com.ogz.executor` | Drain shell missions | 15 sec poll |
| `com.ogz.brain-api` | Brain contracts | always |
| `com.ogz.live-feed` | Mohamed's one tab :4141 | always |
| **`com.ogz.consult-shift`** (NEW) | DeepSeek shift plan → missions | 15 min |
| **`com.ogz.memory-keeper`** (NEW) | Daily history mine + scar index | 6 h |

### 24h shift (what runs when)

| Block | Hours | Focus |
|-------|-------|-------|
| Night | 00–06 | Memory mine, knowledge index, batch tests |
| Morning | 06–12 | Creative queue prep, consult panel, pilot quality |
| Afternoon | 12–18 | Execution missions, platform, handoff |
| Evening | 18–24 | Judge review, digest, next-day queue |

---

## Agent roster (full system)

| Agent | Model/runtime | Purpose | Output folder |
|-------|---------------|---------|---------------|
| **ORCHESTRA** | Cursor | Plan, queue, never shell-execute | `data/cursor_missions/` |
| **CONSULT** | DeepSeek + GPT panel | Challenge every big move | `data/consult_logs/` |
| **EXECUTOR-SHELL** | Python daemon | Tests, health, scripted | `done/*.log` |
| **BUILDER** | Claude Code live | Code, organs, fixes | git commits |
| **RABIE** | GPT-4o | Taste proxy, harsh judge | `data/rabie_verdicts.jsonl` |
| **HUMAIN** | Browser :4111 | Saudi Arabic authority | humain scores |
| **CREATIVE** | CD panel + render path | Posts, concepts | `data/creative_outputs/` |
| **SEARCH** | Web + citations | Internet facts | `data/knowledge/raw/` |
| **LEARNER** | Staged indexer | Domains (cinema, etc.) | `data/knowledge/indexed/` |
| **MEMORY** | cursor_mine_history | Claude 6mo extraction | `artifacts/memory/` |
| **WATCHDOG** | make_sure | Alarms, im_here | `data/im_here.md` |

### Knowledge anti-pollution

```
SEARCH → raw/ → CONSULT reviews → staged/ → LEARNER indexes → domains/
                                              ↑
                         ORCHESTRA approves only ↑
                         Never raw into ogz-knowledge organs
```

**Domain examples:** `domains/cinematography/`, `domains/filmmaking/`, `domains/saudi_ad_culture/`

---

## Cursor + DeepSeek 24h loop (every 15 min)

1. Read: queue, LIVE_STATUS, im_here, last consult
2. **DeepSeek shift brief:** "Given state X, what 1–3 missions next? What NOT to do?"
3. Cursor drops missions (shell vs agent typed)
4. Shell executor drains health missions
5. If `agent` mission → wake Claude Code live (or block until Mohamed)
6. Append plain summary to live feed :4141
7. On failure → **mistake registry** line (auto)

---

## Mohamed gates (never automate)

- render go / FAL spend
- Production wire / Vercel promote
- Taste pairs / portal DELETE
- Cultural law / permanent rulings
- "stop" / لخ

---

## Phase rollout

### Phase 0 — Week 1 (NOW)
- [x] Refresh `claude-code-history-master.json` daily
- [x] `AGENT_REGISTRY.json` manifest
- [x] Mission types: `shell` vs `agent`
- [x] `consult_shift.py` daemon (15 min DeepSeek)
- [x] `data/mistake_registry.jsonl` auto-append on fail
- [x] Live feed v2: Arabic + digest + "waiting on Mohamed"

### Phase 1 — Week 2
- [x] Knowledge staging folders + SEARCH agent v1
- [x] Domain seed: cinematography (10 sources, indexed)
- [x] Unified status dashboard (one JSON, no contradictions)
- [x] Claude live wake only for `agent` missions

### Phase 2 — Month 1
- [x] Creative agent loop (RABIE → render prep, no FAL without gate)
- [x] Platform tunnel prep checklist
- [x] Memory search for agents (`scripts/memory_search.py`)
- [ ] 30-day metric: 20 perfect posts banked OR platform wire live

---

## What NOT to build

- Another chat UI
- SQLite empire (JSONL + files OK)
- Autonomous FAL spend
- 50 agents day one
- Replacing Mohamed's taste

---

## One blunt risk

**24h agents without consult + mistake registry = repeating the same scars automatically** (severed wires, false ready, session leaks) at machine speed.

---

## Success at 30 days

- Mohamed opens **one tab** (:4141) and **one chat** (Cursor) — knows system state in 30 sec
- Zero repeated scar classes from registry
- 3+ knowledge domains indexed and retrievable
- Brain + platform wire stable
- He says "go" less — system proposes, he approves gates only

---

## Your command cheat sheet

| You say | System does |
|---------|-------------|
| **go** | Consult DeepSeek → queue wave → feed updates |
| **stop** / **لخ** | Pause consult-shift + queue |
| **status** | Read artifacts + feed summary |
| **learn cinema** | Queue SEARCH+LEARNER domain mission |
| **render go** | FAL mission (explicit) |
