# Caption Consultation — Synthesis of GPT-4o, Gemini & DeepSeek
**Date:** 2026-06-07 · Three independent expert LLMs, same brief

## The headline
All three converged on the SAME diagnosis — and it confirms Mohamed's human review.
Our 83% fail rate is a **format-to-technique mismatch + prompt overload**, not a model problem.

## CONSENSUS — what all three agree on

### 1. Kill the Authenticity Detective for captions (UNANIMOUS)
All three say remove it from caption generation. It's a VIDEO technique — its "performance vs
reality" two-scene contrast can't compress into 150 chars without forcing extreme intimate
short-hands (the veil/bed scenes Mohamed flagged). Keep it ONLY for video scripts.
→ This independently confirms Mohamed's finding that cd_03 was the worst offender.

### 2. Prioritize Paradox Hunter + Heritage Decoder for captions (UNANIMOUS)
These fit short form naturally — wordplay, contrast, punch. Paradox Hunter is the +35%
engagement winner (and underused). Heritage Decoder is brand-safe gold for corporate/real-estate/occasions.

### 3. Constrain the Firaasa / human-truth technique (Gemini + DeepSeek)
It's overused (48%) and underperforms (-15%) because LLMs default to preachy clichés
("في عالم متسارع..."). Restrict it to SPECIFIC Saudi micro-behaviors (the majlis warmth,
who pays the bill, mall parking) — reject anything generic. Max 1 line, no preamble.

### 4. The prompt architecture is broken — "instruction bloat" (UNANIMOUS)
Our "kitchen-sink" prompt (brand voice + templates + dialect + red lines + technique, all in one)
causes cognitive overload. When overloaded, the LLM IGNORES negative constraints (the red lines)
and defaults to generic MSA. This explains BOTH the cultural violations AND the stiffness.
→ Fix: structured XML-tagged prompt + NEGATIVE few-shot examples (show it what NOT to write).

### 5. Force brevity structurally (UNANIMOUS)
Rigid 1-2 line cap, hard ≤150 chars, technique expressed in ONE move not a paragraph.

## THE ACTION PLAN (derived from consensus)
1. Re-route: Authenticity Detective → video only. Captions use Paradox Hunter, Heritage Decoder,
   constrained Firaasa, simplified Metaphor.
2. Rebuild the prompt: XML-tagged sections + negative few-shot (real fails as "never do this").
3. Constrain Firaasa to Saudi-specific micro-behaviors.
4. Keep gpt-4o-mini (all agree the gain is in prompt+technique, not model).
5. Measure only against Mohamed's human review (the AI judge is confirmed unreliable).
