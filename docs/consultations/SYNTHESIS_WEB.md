# Caption Consultation Round 2 — Web-Grounded (the reversal)
**Date:** 2026-06-07 · GPT-4o, Gemini, DeepSeek with live web search + citations

## THE HEADLINE — Round 2 contradicts Round 1 on the biggest question

| Question | Round 1 (training memory) | Round 2 (web evidence) |
|----------|--------------------------|------------------------|
| Model | Keep gpt-4o-mini, don't fine-tune | **Fine-tune a Saudi model (ALLaM-7B)** — proven |
| Method | Prompt engineering + few-shot | **Prompt engineering FAILS for dialect creativity** |
| Technique | Prioritize wordplay/paradox | **Cultural anchors/proverbs > abstract wordplay** |

All three searched and CONVERGED on: **the proven path to authentic Saudi dialect is a
fine-tuned Saudi-specific model on real Saudi data — not better prompting of GPT/Gemini.**

## THE EVIDENCE THEY FOUND (verify the papers before betting)
- **Saudi-Dialect-ALLaM** (LoRA fine-tune): dialect fidelity 47.97% → 84.21%; MSA leakage 32.63% → 6.21%
  (github.com/HasanBGit/Saudi-Dialect-ALLaM, arxiv 2508.13525)
- **ALLaM-7B-Instruct** (Saudi national LLM, by SDAIA) outperforms GPT-4 on Saudi dialect when fine-tuned
  (68.83% dialect accuracy vs 28.67% AceGPT)
- **Dialect-Token conditioning** — explicit <hijazi> / <najdi> tags beat generic models
- **Absher benchmark** (arxiv 2507.10216) — 18,000 Qs to evaluate Saudi dialect; Arabic-specific models win
- **Prompt engineering ceiling**: GPT-4o dialect prompts only ~45% accuracy
- **RAG limited** by sparse/noisy Saudi dialect corpora
- **Industry**: top Riyadh agencies use HYBRID — fine-tuned ALLaM for dialect + GPT for alignment;
  rate proverb adaptation + region-specific humor higher than abstract paradox

## WHY THIS MATTERS FOR OGZ SPECIFICALLY
The evidence says the moat is a fine-tuned Saudi model — and **OGZ already has the one thing it needs:
6,888 real Saudi captions with engagement.** That is exactly the training data ALLaM fine-tuning requires.
We are uniquely positioned to do what the research says works.

## THE REFRAMED PATH
- SHORT TERM (this week): keep improving the prompt (Round 1 fixes still valid — kill Authenticity
  Detective for captions, red lines, length, cultural anchors over abstract wordplay).
- REAL PATH (the moat): fine-tune ALLaM-7B (LoRA) on our 6,888 Saudi captions with dialect tokens,
  evaluate with Absher-style dialect-density + cultural-safety checks, measure against Mohamed.
- Use a HYBRID: ALLaM for Saudi-dialect generation + the CD methodology layer for creative structure.

## HONEST CAVEAT
LLM-cited URLs can be fabricated — verify arxiv 2508.13525 / 2507.10216 and the ALLaM numbers
before committing budget. But the DIRECTION (Arabic-specific fine-tune beats generic prompting for
dialect) is well-established and ALLaM is real (SDAIA). The conclusion is sound; verify the specifics.
