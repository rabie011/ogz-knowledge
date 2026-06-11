# Consultation Synthesis — V3 Plan Validation
# Date: 2026-06-07
# Models consulted: GPT-4o (API) + Gemini Flash (web) + DeepSeek (web)

---

## WHAT THEY AGREE ON

1. **Phase sequence is correct** — fix now, swap model, fine-tune. Right order.
2. **The banned template list is the right quality lever** — both confirmed it
3. **Fine-tuning is the real moat** — 6,888 captions is a serious asset
4. **50 approved outputs is not enough for fine-tuning** — need more quality signal

---

## THE SHARPEST NEW INSIGHTS (Gemini — things we hadn't thought of)

### 1. gpt-4o-mini is too weak for Phase 1 — upgrade the model first
"gpt-4o-mini will struggle with deep Saudi cultural nuance. Test Claude Sonnet or GPT-4o in Phase 1 — their advanced reasoning handles the complex constraints of V3 far better than mini."

→ **Action: Test V3 prompt on gpt-4o (not mini) before deploying. Cost difference is worth it if approval rate jumps.**

### 2. Don't let the model self-select — use an Editor LLM
"LLMs are terrible self-critics in a single generation."
Current approach: model generates 3 + picks الأفضل itself.
Better approach: generate 3 → run a SECOND dedicated "Editor" call that scores against banned list and picks the winner. Separates generation from evaluation.

→ **Action: Add an Editor LLM step as a second API call. Cost: +1 call per caption. Quality: removes the bias where models self-select their "safest" output.**

### 3. Route to ONE technique, not 3 simultaneously
"Run a lightweight classification prompt first to choose ONE technique based on the brand brief, then route to that specific dedicated prompt."
Current: show all 3 techniques, ask model to do all 3.
Better: classify → route → generate 1 technique only (deeply).

→ **Action: This is the cd_brains.py router doing its job properly. The classifier picks ONE technique, the prompt only shows that technique's exemplars (not all 3). Paradox Hunter stops copying itself if it's the only technique in the prompt.**

### 4. Synthesize 300-500 gold outputs before fine-tuning
"Your data ratio (7,000 raw vs. 50 approved) will cause the model to mimic bad habits. Synthesize quality using ALLaM web UI now — generate 300-500 gold-standard outputs."

→ **Action: Run HUMAIN systematically on all OGZ sectors + occasions. Build a proper gold dataset BEFORE the fine-tune. This is the pre-work for Phase 3.**

### 5. The multimodal gap (biggest thing we missed)
"Instagram is visual. A caption depends entirely on the image. Without multi-modal input, your system is flying blind."

→ **This is real. Right now the system gets: brand + product + occasion. It does NOT get the actual image. A photo of an AlBaik meal in green for National Day context changes the caption completely. This is a missing input that no prompt trick can fix.**

---

## UPDATED PLAN (incorporating both consultations)

### Phase 1 — Fix production (this week)
- Kill Authenticity Detective for captions
- Deploy V3 prompt — but use **gpt-4o** (not mini) and route ONE technique (not 3)
- Add Editor LLM second call to pick the winner instead of self-selection
- Test 30 outputs → Mohamed rates → measure

### Phase 1b — Build gold dataset (parallel, ongoing)
- Run HUMAIN web UI systematically on all sectors/occasions
- Target: 300 approved outputs (from the 3-option prompt, Mohamed picks)
- These become the fine-tune training set

### Phase 2 — ALLaM API
- Swap gpt-4o for ALLaM when API available
- Same V3 prompt, same Editor LLM, same routing
- Target: 60-65%

### Phase 3 — Fine-tune
- LoRA on ALLaM using 300 gold outputs + cleaned 6,888 captions
- LoRA Rank R=32, Alpha=64 for deep dialect embedding
- Target: 70%+

### Phase 4 — Multimodal (future)
- Feed actual image to the model at caption generation time
- This unlocks image-aware captions — biggest quality jump after dialect

---

## DECISION TABLE

| Question | GPT-4o | Gemini | Verdict |
|---|---|---|---|
| Phase sequence right? | Yes | Yes, but API risk | Deploy Phase 1 now |
| gpt-4o-mini OK? | Not mentioned | Too weak — upgrade | Use gpt-4o instead |
| V3 architecture right? | Yes + update banned list | Partially — route ONE technique | Route → ONE technique |
| Self-selection OK? | Not flagged | Wrong — use Editor LLM | Add Editor LLM call |
| Fine-tune data enough? | Need more quality signal | Synthesize 300-500 gold first | Build gold set first |
| Multimodal? | Not mentioned | Critical gap | Future phase |

---

## BOTTOM LINE

The plan is right. Two architectural upgrades before deploying:
1. **gpt-4o instead of mini** — better reasoning for Saudi dialect constraints
2. **Route ONE technique → Editor LLM picks winner** — separates generation from evaluation

And one pre-work task before Phase 3:
3. **Build 300 gold outputs via HUMAIN** — systematic collection, Mohamed approves each

Everything else confirmed.

---

## DEEPSEEK ADDITIONS (new insights beyond GPT-4o + Gemini)

### 1. Don't wait for ALLaM API — automate the web UI NOW
"Use Selenium/Playwright on chat.humain.ai for limited production volume now. Real feedback before committing to LoRA."
→ **Action: Build a Playwright script to run HUMAIN web UI systematically for gold dataset collection. This is Phase 2 moved left, not delayed.**

### 2. 10% fusion route — don't over-constrain to ONE technique
"Add 10% random fusion route (merge two techniques). Routing ONE technique 100% creates creative rigidity over time."
→ **Action: Keep ONE technique as the default (95% of calls), but allow occasional technique fusion to prevent stagnation.**

### 3. Dynamic banning — auto-block after 3 repetitions
"Banned list will grow indefinitely. Switch to dynamic banning: after 3 similar structures from same technique, auto-block for next 5 calls."
→ **Action: Add a session-level counter per technique structure. Block automatically, not just on hard-coded list.**

### 4. 6888 raw captions ≠ instruction pairs — split their use
"Don't train LoRA on all 6888 raw captions as instruction pairs (too much noise). Use them for masked language modeling (20% token masking). Use 300 gold outputs as prompt-response pairs for instruction tuning."
→ **Action: Fine-tune plan updated — two-track training: MLM on 6888 + instruction tuning on 300 gold.**

### 5. Dialect markers for LoRA — regional specificity
"Add `<sa:riyadh>` / `<sa:jeddah>` markers in training prompts so LoRA learns regional variation."
→ **Action: When building gold outputs, tag by dialect region. Most OGZ clients are Riyadh-based.**

### 6. 300 gold outputs are leverage for SDAIA API access
"Push SDAIA for early access — your 300 gold outputs are the negotiation asset."
→ **Action: Build the 300 gold dataset AND use it as the pitch to get ALLaM API access.**

---

## FINAL DECISION TABLE (all 3 models)

| Question | GPT-4o | Gemini | DeepSeek | Verdict |
|---|---|---|---|---|
| Phase sequence right? | Yes | Yes, API risk | Yes, but shift Phase 2 left | Deploy Phase 1 + automate web UI |
| gpt-4o-mini OK? | Not mentioned | Too weak — upgrade | Use gpt-4o for Editor LLM | Use gpt-4o |
| Route ONE technique? | Not mentioned | Yes — route ONE | 95% ONE + 5% fusion | ONE technique + rare fusion |
| Editor LLM needed? | Not flagged | Yes — add it | Yes — must be gpt-4o not mini | Add Editor LLM (gpt-4o) |
| LoRA data enough? | Need more quality | 300-500 gold first | Split: MLM on raw + instruction on gold | Two-track training |
| Missing anything? | Dynamic banned list | Multimodal gap | Feedback slider + hashtag weaver + automate web UI | All three valid |
