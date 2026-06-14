# Root-hunt: "captions all look the same / repetition / quality down" (2026-06-14)

Trigger: Mohamed, after 34 portal verdicts + 2 notes — "same patterns, same creative, why
everything home and food, lots of repetition, which LLM, why not HUMAIN."

## The 5 root causes (each verified with evidence, not assumed)

1. **CD-brain methods never reached the pen.** `brain_method()` returned `read_text()[:2800]`
   — only the YAML front-matter (firaasa file is 12,832 chars; front-matter ends ~char 3,395).
   So the creative METHODOLOGY of every brain was truncated off; the angle fell back to a
   generic "concrete scene." **Fix:** inject the method BODY (after the 2nd `---`). Verified:
   the angle is now a specific Firaasa persona-scene, not a formula.

2. **The taste_guard re-admit leak (THE repetition leak).** When the pen produced only the
   formulas he ruled against (delivery-CTA, family-scene), the gauntlet correctly KILLED all
   of them — then `if not kept: kept=[options[0]]` re-admitted the killed one. His own rulings
   were honored, then overridden at ship time. **Proven** on a live slot: 3 delivery/family
   options taste-killed, the delivery-CTA shipped as caption #1. **Fix (Rule #8):** taste_guard
   returns EMPTY when all are killed; the caller regenerates with the kill reasons fed back, or
   holds the slot — a ruled-against caption never ships.

3. **The gold few-shot taught the banned formula.** All 6 jurisha gold lines were delivery
   (`جاهز`/`هنقرستيشن`) or family (`الجد`/`الجدة`) — the exact two cores he's tired of. The pen
   few-shots from gold, so it reproduced his banned patterns. **Fix:** quarantine any few-shot
   line (gold OR corpus) matching an active kill_pattern — a line teaching a banned formula
   can't lead the few-shot.

4. **The 2nd pen has been dark.** Anthropic returns HTTP 400: "Your credit balance is too low."
   The system's two-pen diversity design (gpt-4o + claude-sonnet, "two temperaments") has been
   running on gpt-4o ALONE — half the diversity engine off. **Fix (free):** moved the DOORS
   structural-diversity (sound / side-character / empty-plate / object-POV / sensory / question)
   onto the LIVE gpt pen — the 3 options now each enter the scene through a different door, so
   they can't collapse into one shape. **DECISION FOR MOHAMED:** top up Anthropic credits to
   restore the 2nd pen, or keep running gpt-only (now diversified by doors+regen).

5. **The portal judge queue excluded the only non-food pilot.** `seed_judge_cards.pick_posts`
   was hardcoded to pull from `eatjurisha` + `albaik` only — both food. `myfitness.sa` (fitness)
   was never staged → his queue was 100% food. A direct cause of "why everything home and food."
   **Fix:** myfitness now LEADS the rotation.

## Proof (before → after, same jurisha slot 2026-07-01)
- BEFORE: "العيد يبدأ بجريّشة... اطلبوا من هنقرستيشن اليوم" (a ruled-against delivery-CTA, shipped
  despite being taste-killed).
- AFTER (regen escaped the formula): "صوت الرياح في المدينة يهمس بأسرار الراحة..." + "الطبق الآن
  فارغ، لكن الراحة باقية..." — fresh cores, no delivery push, no family gathering.
- 3 slots compared (07-01 / 07-15 / 08-10): a "simple-meal-as-inspiration" question, a
  "steam + summer breeze" sensory open, an "after the plates emptied" aftermath — genuinely varied.

## Tests
60 green. The old `test_never_empties` (which guarded the leaky re-admit) was rewritten to assert
the correct refuse-don't-readmit contract. New `TestFewShotNotPoisonedByBannedGold` locks the
quarantine so the formula-teaching gold can't return.

## Still open
- myfitness slots 2026-09-11 / 10-11 hit HARD cultural/dialect kills → zero captions. Needs a
  look at what hard-kill fires on the English-led fitness brand.
- The corpus only yields ~6 gold-tier jurisha posts (homogeneous) — the deeper fix is more
  diverse gold, which comes from Mohamed's judgments on the new varied batch (the Full Circle).
