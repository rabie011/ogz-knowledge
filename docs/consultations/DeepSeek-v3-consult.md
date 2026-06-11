# DeepSeek — V3 Plan Consultation
# Date: 2026-06-07
# Question: Same consultation sent to GPT-4o and Gemini on V3 architecture + 3-phase plan

---

## QUESTION SENT

You are an AI systems consultant. A Saudi creative agency (OGZ Studios) is building an Arabic Instagram caption generator. Give your honest technical opinion.

WHAT WAS TESTED (13 briefs, 4 systems):
- System A: gpt-4o-mini + 7-section bloated prompt (current production)
- System B: gpt-4o-mini + 4-block XML prompt
- Jais 2: Arabic LLM 70B + System B prompt
- HUMAIN/ALLaM 34B: Saudi national LLM (SDAIA) + System B prompt

Baseline: 5/30 human approval (17%). Mohamed (CEO, native Saudi) rated 25/30 weak/fail.

KEY FINDINGS:
1. HUMAIN/ALLaM 34B produced the best outputs consistently
2. V3 prompt: 3 techniques + growing banned template list + "write 3, pick best"
3. Blocking banned templates forces creativity
4. Paradox Hunter copies exemplar verbatim when only 1 example given
5. Heritage Decoder repeats same sentence structure across brands
6. ALLaM 34B: no API yet (web UI only)

3-PHASE PLAN:
Phase 1: Deploy V3 to gpt-4o. Route ONE technique. Add Editor LLM. Target: 17% → 40-50%.
Phase 2: Swap to ALLaM API when available. Target: 60-65%.
Phase 3: LoRA fine-tune ALLaM on 6888 captions + 300 gold outputs. Target: 70%+.

---

## DEEPSEEK RESPONSE

**1. Phase sequence is correct, but shift Phase 2 left.**

Don't wait for formal ALLaM API. Use web UI via scripted automation (Selenium/Playwright) for a limited production volume now. That gets you real feedback before committing to LoRA.

**2. V3 architecture is smart except:**

- Routing ONE technique per call works, but you lose hybrid creativity. Add a 10% random "fusion" route (merge two techniques) to avoid over-constraint.
- Editor LLM is essential, but use gpt-4o (not mini) for judging — better at detecting "fake original" (recycled templates).
- Banned list will grow indefinitely. Switch to dynamic banning: after 3 similar structures from same technique, auto-block that pattern for next 5 calls.

**3. LoRA on ALLaM — maximize Saudi dialect quality by:**

- Not training on all 6888 raw captions (too much noise). Use them only for masked language modeling (20% of tokens).
- 300 gold outputs → prompt-response pairs for instruction tuning. Augment with back-translation (gold Saudi → MSA → Saudi) to boost robustness.
- Add explicit dialect markers: `<sa:riyadh>`, `<sa:jeddah>` in prompts to let LoRA learn regional variation.

**4. What you're missing:**

- **User control.** No feedback loop from Mohamed's ratings into prompt adjustment. Build a simple slider ("too creative / too literal") on each output → fine-tune technique weights per brand.
- **Hashtag collapse.** Arabic Instagram relies on hashtag blocks. Your prompts ignore them. Add a fourth technique: "Hashtag Weaver" (extract 3 niche tags from caption meaning).
- **Cost vs. latency.** gpt-4o + Editor LLM + ALLaM fallback = ~3s per caption. Test if users wait. If not, cache technique-banned list combinations.

**Final verdict:** Phase 1 achievable, but Phase 2 (ALLaM API) is the real unlock. Without it, LoRA is guesswork. Push SDAIA for early access — your 300 gold outputs are leverage.

---

## KEY NEW INSIGHTS FROM DEEPSEEK

1. **Shift ALLaM access left** — don't wait for API. Selenium automation of HUMAIN web UI = real production data now.
2. **10% fusion route** — don't lock to ONE technique 100% of the time. Small % of hybrid calls prevents creative rigidity.
3. **Dynamic banning** — auto-block repeated structures (not just fixed banned list) after 3 occurrences.
4. **6888 captions ≠ 6888 instruction pairs** — use raw captions for masked LM only. Gold outputs for instruction tuning.
5. **Dialect markers** — `<sa:riyadh>` vs `<sa:jeddah>` in LoRA training prompts for regional variation.
6. **Feedback slider** — per-brand creativity calibration dial is missing.
7. **300 gold outputs are leverage for SDAIA** — use them as the ask to get ALLaM API access.
