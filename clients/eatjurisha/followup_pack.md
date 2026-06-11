# KHWILA FOLLOW-UP PACK — her answers → organs (B189)

Built: 2026-06-12 · PROVISIONAL — pending Mohamed · Companion to `KHWILA_PRESENTATION.md` + `PREFLIGHT_REPORT.md`
**Memory law: discovered = written.** When her answer lands on WhatsApp, run the matching capture below — her words hit the organ + the ledger within minutes. All snippets are run from repo root (`~/Desktop/ogz-knowledge`). Confirmer is always `khwila_client`, stamp `CLIENT — via Mohamed's WhatsApp` (recording an answer is not a send; sends stay Mohamed-only).

---

## 0. THE HEADLINE — voice pick (A / B / C)

**Target organs:** `profile/fingerprint.json` → `l2_voice` (dialect/register/tone + `love_lines` = her chosen voice's 3 lines, verbatim) **+** `profile/gold.json` (3 lines promoted) · **Events:** `pick_selected` + `client_approved`
**⚠️ Gate:** if she picks **C**, PREFLIGHT FIX-1 (voice-C sync) must already be landed — the organ and the presentation must hold identical lines before promotion.

```bash
python3 - <<'PY'
import json, datetime; from pathlib import Path
PICK = "A"   # <-- EDIT: A / B / C
HER_WORDS = ""  # <-- EDIT optional: her exact wording of the pick
P = Path("clients/eatjurisha")
vb = json.loads((P/"voice_birth_week.json").read_text())
key = [k for k in vb if k.startswith(PICK)][0]
lines = list(vb[key]["posts"].values())
persona = {"A": {"dialect":"najdi","register":"home-warm","tone":"دفء البيت — صوت العائلة والسفرة"},
           "B": {"dialect":"najdi-light","register":"clean-craft","tone":"نظيف ومدروس — صوت من يعرف صنعته"},
           "C": {"dialect":"najdi","register":"playful","tone":"شبابية، كرافينج، ابتسامة"}}[PICK]
fp = json.loads((P/"profile/fingerprint.json").read_text())
fp["l2_voice"].update(persona); fp["l2_voice"]["love_lines"] = lines
fp["l2_voice"]["_status"] = f"GREEN — voice {PICK} BORN by client pick"
fp["l2_voice"]["provenance"] = {"source":"khwila_voice_pick","date_added":str(datetime.date.today()),
    "confirmer":"khwila_client","confidence":"confirmed","scope":"brand"}
(P/"profile/fingerprint.json").write_text(json.dumps(fp, ensure_ascii=False, indent=2))
g = json.loads((P/"profile/gold.json").read_text())
g["gold"] += [{"line":l,"rating":5,"source":f"voice_birth_week_pick_{PICK}","occasion":None} for l in lines]
(P/"profile/gold.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
ts = str(datetime.date.today())
with (P/"events/ledger.jsonl").open("a") as f:
    for ev in [{"ts":ts,"type":"pick_selected","subject":f"voice_{key}","note":HER_WORDS or f"Khwila picked voice {PICK}"},
               {"ts":ts,"type":"client_approved","subject":"voice_birth_week","rating":5}]:
        ev.update({"confirmer":"khwila_client","stamp":"CLIENT — via Mohamed's WhatsApp"})
        f.write(json.dumps(ev, ensure_ascii=False)+"\n")
print(f"voice {PICK} -> fingerprint l2 (love_lines) + gold (3 lines) + 2 ledger events")
PY
```

## The 5 questions → organ + event map

### Q1 — وش أهدافكم الجاية؟ (أصناف جديدة، مواسم مهمة، توسّع؟)
**Organ:** `profile/goals.json` → `forward_calendar` (seasons/dates) — new dishes also append to `truth_pack.json.product_candidates` (confidence `client_stated`) · **Event:** `goal_declared`

```bash
python3 - <<'PY'
import json, datetime; from pathlib import Path
ANSWER = ""                    # <-- EDIT: her words verbatim
CALENDAR = []                  # <-- EDIT e.g. ["ramadan_2027", "national_day_2026"]
P = Path("clients/eatjurisha"); ts = str(datetime.date.today())
g = json.loads((P/"profile/goals.json").read_text())
g["forward_calendar"] = sorted(set(g["forward_calendar"] + CALENDAR)); g["answered"] += 1
(P/"profile/goals.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
with (P/"events/ledger.jsonl").open("a") as f:
    f.write(json.dumps({"ts":ts,"type":"goal_declared","subject":"forward_goals","note":ANSWER,
        "confirmer":"khwila_client","stamp":"CLIENT — via Mohamed's WhatsApp"}, ensure_ascii=False)+"\n")
print("goals.forward_calendar updated + goal_declared logged")
PY
```

### Q2 — الخطوط الحمراء: وش ما ننشر أبداً؟
**Organ:** `profile/red_lines.json` → `lines[]` (currently EMPTY — «cannot exist without the client») · **Event:** `red_line_added` (ONE event PER line)

```bash
python3 - <<'PY'
import json, datetime; from pathlib import Path
LINES = []   # <-- EDIT: her red lines verbatim, e.g. ["وجه الوالدة لا يظهر أبداً", "ما نذكر الأسعار في المنشورات"]
P = Path("clients/eatjurisha"); ts = str(datetime.date.today())
r = json.loads((P/"profile/red_lines.json").read_text())
prov = {"source":"khwila_whatsapp","date_added":ts,"confirmer":"khwila_client","confidence":"confirmed","scope":"brand"}
r["lines"] += [{"line":l,"provenance":prov} for l in LINES]
(P/"profile/red_lines.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))
with (P/"events/ledger.jsonl").open("a") as f:
    for l in LINES:
        f.write(json.dumps({"ts":ts,"type":"red_line_added","subject":l,
            "confirmer":"khwila_client","stamp":"CLIENT — via Mohamed's WhatsApp"}, ensure_ascii=False)+"\n")
print(f"{len(LINES)} red lines -> red_lines.json + {len(LINES)} red_line_added events")
PY
```

### Q3 — مين يتكلم باسم جريشة؟ (صوتك / صوت العائلة / محايد)
**Organ:** `profile/fingerprint.json` → `l1_strategy.who_speaks` · **Event:** `intake_answer` (subject `who_speaks`)

```bash
python3 - <<'PY'
import json, datetime; from pathlib import Path
ANSWER = ""   # <-- EDIT: e.g. "صوت خويلة نفسها" / "صوت العائلة" / "محايد"
P = Path("clients/eatjurisha"); ts = str(datetime.date.today())
fp = json.loads((P/"profile/fingerprint.json").read_text())
fp["l1_strategy"]["who_speaks"] = ANSWER
(P/"profile/fingerprint.json").write_text(json.dumps(fp, ensure_ascii=False, indent=2))
with (P/"events/ledger.jsonl").open("a") as f:
    f.write(json.dumps({"ts":ts,"type":"intake_answer","subject":"who_speaks","note":ANSWER,
        "confirmer":"khwila_client","stamp":"CLIENT — via Mohamed's WhatsApp"}, ensure_ascii=False)+"\n")
print("fingerprint l1.who_speaks set + intake_answer logged")
PY
```

### Q4 — وش يميز جريشتكم بكلماتك أنتِ؟ (USP)
**Organ:** `profile/fingerprint.json` → `l1_strategy.positioning` (her words VERBATIM — never paraphrase the USP) + mirror to `profile/goals.json.usp_his_words` · **Event:** `intake_answer` (subject `usp_verbatim`)

```bash
python3 - <<'PY'
import json, datetime; from pathlib import Path
ANSWER = ""   # <-- EDIT: her words verbatim, untouched
P = Path("clients/eatjurisha"); ts = str(datetime.date.today())
fp = json.loads((P/"profile/fingerprint.json").read_text())
fp["l1_strategy"]["positioning"] = ANSWER
(P/"profile/fingerprint.json").write_text(json.dumps(fp, ensure_ascii=False, indent=2))
g = json.loads((P/"profile/goals.json").read_text()); g["usp_his_words"] = ANSWER; g["answered"] += 1
(P/"profile/goals.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
with (P/"events/ledger.jsonl").open("a") as f:
    f.write(json.dumps({"ts":ts,"type":"intake_answer","subject":"usp_verbatim","note":ANSWER,
        "confirmer":"khwila_client","stamp":"CLIENT — via Mohamed's WhatsApp"}, ensure_ascii=False)+"\n")
print("fingerprint l1.positioning + goals.usp_his_words set + intake_answer logged")
PY
```

### Q5 — الهدف: مبيعات مباشرة، بناء براند، ولا الاثنين؟ (كم نسبة العروض؟)
**Organ:** `profile/goals.json` → `goal_ratio` · **Event:** `goal_declared` (subject `goal_ratio`)

```bash
python3 - <<'PY'
import json, datetime; from pathlib import Path
ANSWER = ""        # <-- EDIT: her words verbatim
RATIO = ""         # <-- EDIT structured, e.g. "70_brand/30_offers"
P = Path("clients/eatjurisha"); ts = str(datetime.date.today())
g = json.loads((P/"profile/goals.json").read_text())
g["goal_ratio"] = RATIO or ANSWER; g["answered"] += 1
(P/"profile/goals.json").write_text(json.dumps(g, ensure_ascii=False, indent=2))
with (P/"events/ledger.jsonl").open("a") as f:
    f.write(json.dumps({"ts":ts,"type":"goal_declared","subject":"goal_ratio","note":ANSWER,
        "confirmer":"khwila_client","stamp":"CLIENT — via Mohamed's WhatsApp"}, ensure_ascii=False)+"\n")
print("goals.goal_ratio set + goal_declared logged")
PY
```

## Riders (capture if they come up in the same chat)

- **Capacity (كم طلب باليوم تقدرون تستوعبون؟** — gap_report Q, not in the 5): → `goals.json.capacity_ceiling` + event `capacity_declared`. Reuse the Q5 snippet with `g["capacity_ceiling"] = ...` and `"type":"capacity_declared","subject":"orders_per_day"`.
- **Truth-confirm (المنتجات/الأسعار/فردي):** her ✓/✗ on the candidates → move items from `truth_pack.json.product_candidates` to `confirmed` (provenance confirmer `khwila_client`, confidence `confirmed`) + event `truth_confirmed`. This is the only legal way «فردي» and any price enter the system (PREFLIGHT FIX-2 / B186 card).
- **Complaint-monitoring offer (الملاحظة):** her yes/no → event `intake_answer`, subject `review_monitoring_consent`. The scrape mechanics stay gated behind A-17 (FLANK-05) — consent recorded here does NOT switch monitoring on.

## First week after her answers

**Day 0 — capture (minutes, same day as her WhatsApp):** run the snippets above. Result: `red_lines`, `goals`, `l1_strategy`, `l2_voice` go RED→GREEN (clears gap_report.organs_red); ledger holds her words verbatim.
**Day 1 — gold promotion + ratify:** voice-pick snippet already promoted her 3 chosen lines to `gold.json` (rating 5, source `voice_birth_week_pick_*`). Mohamed's A-30 tap ratifies; RABIE sanity-checks the 5 pre-existing gold lines against her new red lines — any collision → quarantine the line + ledger note.
**Day 2 — render her launch arc (3 posts, her voice now in the organs):**
```bash
python3 scripts/render_slots_batch.py --handle eatjurisha --type evergreen --suffix __launch1 --limit 3
```
Fresh suffix forces re-render of the first 3 slots (2026-07-03 / 07-07 / 07-10) through the full armored pipeline, now reading her l2 love_lines + gold. Arc shape mirrors her proven winner (the 31/28 Eid family post): ① comeback («رجعنا») ② product scene (جريشة/كابلي + جاهز/هنقرستيشن only — confirmed channels) ③ family/Friday sufra.
**Day 3 — RABIE provisional ratings** on the 3 renders (0–5, ledger `version_verdict`); anything <4 re-renders.
**Day 4-5 — the batch gate:** Mohamed reviews → sends the 3-post arc to Khwila → **she clicks once on the full batch BEFORE anything posts** (per-batch consent law, A-19). Her click = `client_approved` event; then scheduling.

**Standing laws over this whole flow:** client-facing sends are Mohamed's hands only (A-22/A-23 gates precede everything) · all my/RABIE entries stay PROVISIONAL until his return ritual · majors are never single-shot (arc is all evergreen — law not triggered) · only confirmed truth in captions (no prices until `truth_confirmed`).
