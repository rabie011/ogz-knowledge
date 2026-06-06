# BRAIN UPDATE PROPOSALS

Generated: 2026-06-06 13:48 UTC  
Source: `logs/learning_store.jsonl`  
Total entries analyzed: 514  
Total failures: 512  
Proposals generated: 2  

> **Workflow:** Mohamed reads this file, marks `[APPROVED]` or `[REJECTED]` on each proposal,
> then runs `python3 scripts/apply_brain_proposals.py --apply <ID>` to execute approved ones.
> The apply script prints what it will do before writing anything.

---

## PROPOSAL 001 — Uncategorized 

**Category:** `uncategorized`  
**Frequency:** 501 failure(s)  
**Brain path:** `arabic_quality_rules (review needed)`  

**Proposed change:**
> Review 501 uncategorized failures manually. Consider adding a new category rule to brain_update_from_learning.py if a clear pattern emerges.

**Rationale:**
> 501 failures could not be mapped to a known category. Affected: albaik (100), mcdonaldsksa (91), barnscoffee (48), roshnksa (44), asteribeautysa (43), pizzahutsaudi (40), randbfashion (34), tamimimarkets (31), mumzworld (29), mikyajy (23), pandasaudi (14), myfitness.sa (4). Sample: api_error:HTTP Error 500: Internal Server Error — pandasaudi/hajj_season

**Affected handles:** `albaik` (100), `mcdonaldsksa` (91), `barnscoffee` (48), `roshnksa` (44), `asteribeautysa` (43), `pizzahutsaudi` (40), `randbfashion` (34), `tamimimarkets` (31)  

**Evidence (up to 5 samples):**
1. `api_error:HTTP Error 500: Internal Server Error — pandasaudi/hajj_season`
2. `api_error:HTTP Error 500: Internal Server Error — pandasaudi/white_friday`
3. `api_error:HTTP Error 500: Internal Server Error — pandasaudi/white_friday`
4. `api_error:HTTP Error 500: Internal Server Error — pandasaudi/white_friday`
5. `api_error:HTTP Error 500: Internal Server Error — pandasaudi/white_friday`

**Status:** `[PENDING Mohamed approval]`

---

## PROPOSAL 002 — Pipeline Timeout [EXCEPTION-TYPE — runtime fix, not content fix]

**Category:** `timeout_error`  
**Frequency:** 9 failure(s)  
**Brain path:** `quality_gate → auto_fixes → timeout_retry`  

**Proposed change:**
> Add timeout_retry policy: max 2 retries with 5 s back-off before logging to learning_store. Currently there is NO retry — every timeout burns a learning entry.

**Rationale:**
> 9 timeout errors recorded across 7 account(s). All scored 0 and pollute failure stats without representing quality issues.

**Affected handles:** `maxfashionmena` (2), `randbfashion` (2), `pizzahutsaudi` (1), `altazaj_fakieh` (1), `barnscoffee` (1), `gissahperfumes` (1), `hashibasha` (1)  

**Evidence (up to 5 samples):**
1. `exception:TimeoutError:timed out — maxfashionmena/singles_day`
2. `exception:TimeoutError:timed out — pizzahutsaudi/national_day`
3. `exception:TimeoutError:timed out — randbfashion/founding_day`
4. `exception:TimeoutError:timed out — randbfashion/eid_al_adha`
5. `exception:TimeoutError:timed out — altazaj_fakieh/jeddah_season`

**Status:** `[PENDING Mohamed approval]`

---

## How to Apply

```bash
# Dry-run a specific proposal (shows what would change, no write):
python3 scripts/apply_brain_proposals.py --dry-run 001

# Apply a proposal:
python3 scripts/apply_brain_proposals.py --apply 001

# Apply all APPROVED proposals:
python3 scripts/apply_brain_proposals.py --apply-all
```
