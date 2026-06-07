# Gemini (flash-latest) — Caption Consultation Response

Here is your strategic blueprint to overhaul the platform’s creative engine, fix the cultural and length failures, and build a scalable human-in-the-loop learning system.

---

### PART 1: Methodology Restructuring (Short-Form Optimization)

Your 83% failure rate is primarily a **format-to-technique mismatch**. You are trying to squeeze complex, narrative-driven video concepts into 150-character Instagram captions. 

#### 1. Retire "Authenticity Detective" for Captions
*   **Why it failed:** This technique requires setting up a scene ("performance") and subverting it ("reality"). In under 150 characters, this compression forces the LLM to use extreme, intimate short-hands (like "removing the veil" or "being in bed") to establish the "reality" instantly. It is highly suited for a 30-second reel script, but **unusable for short captions**.
*   **Action:** Remove it entirely from the caption engine. Keep it strictly for video script generation.

#### 2. Pivot "Firaasa Architect" (Human-Truth Hook)
*   **Why it is underperforming (-15% engagement):** When LLMs write "human truths," they default to cheesy, preachy, or overly dramatic clichés (e.g., "في عالم متسارع..." / "In a fast-paced world..."). 
*   **Action:** Restrict this technique to **Saudi-specific cultural micro-behaviors** (e.g., the struggle of finding a parking spot at a busy mall, the unspoken rule of who pays the bill, or the specific warmth of a grandmother’s living room). If it’s not highly specific to Saudi daily life, reject it.

#### 3. Double-Down on "Paradox Hunter" and "Heritage Decoder"
These two are your goldmines. They naturally fit the 120–170 character limit because they rely on wordplay, contrast, and punchy delivery.
*   **Paradox Hunter (+35% engagement):** Perfect for a quick, witty hook.
*   **Heritage Decoder (+1% engagement, but highly brand-safe):** Excellent for corporate, real estate, and seasonal occasions (Eid, Founding Day).

---

### PART 2: The "Saudi-Native" Prompt Architecture

The "kitchen-sink" prompting style (shoving brand voice, templates, dialect rules, and red lines into one long prompt) causes cognitive overload in LLMs. When overloaded, LLMs ignore negative constraints (like "do not mention beds") and default to generic MSA (Modern Standard Arabic).

You must use a **Highly Structured, Modular XML-Tagged Prompt with Negative Few-Shot Examples**.

#### The Production-Ready Prompt Template:

```xml
<system_role>
You are an elite Saudi Creative Director specializing in ultra-short, high-engagement Instagram copy for premium Saudi brands. You write with brevity, cultural sophistication, and natural Najdi/Hejazi dialect.
</system_role>

<creative_brief>
- Brand: [Insert Brand Name & Sector]
- Product/Service: [Insert Product]
- Occasion/Context: [Insert Occasion, e.g., Ramadan, Friday, Payday]
- Creative Technique: [Insert Paradox Hunter OR Heritage Decoder]
</creative_brief>

<structural_constraints>
- Max Length: 25 words (Strictly between 100 and 150 characters, including spaces).
- Structure: Exactly 1 or 2 short sentences. No paragraphs.
- Formatting: Start with a hook. End with a subtle brand/product integration. No generic call-to-actions (e.g., لا تفوتكم الفرصة).
- Emoji Limit: Maximum 1 highly relevant emoji, or none. No emoji spam.
</structural_constraints>

<dialect_and_tone_rules>
- Primary Dialect: Natural modern Saudi (Najdi/Hejazi mix).
- Words to USE: وش، الحين، يالله، حلو، كذا، وش دعوة، طيب.
- Words to AVOID (Strictly forbidden Gulf/MSA/Levantine words): شنو، جذي، زين، تفضلوا، حياكم، شو، كرمال، هيك.
- Tone: Natural, witty, respectful, never preachy.
</creative_brief>

<cultural_red_lines>
- CRITICAL: Never reference bedrooms, beds, sleeping, or waking up in bed.
- CRITICAL: Never reference removing, adjusting, or changing clothes, veils (خمار/عباية), or personal attire.
- CRITICAL: Never exploit vulnerability, fatigue, hunger, or weakness (e.g., do not describe how miserable someone is during fasting).
</cultural_red_lines>

<technique_instruction>
[IF PARADOX HUNTER]: Write a counterintuitive flip. The hook must state a paradox of Saudi daily life, and the product must be the elegant resolution.
[IF HERITAGE DECODER]: Select one double-meaning Arabic word related to the occasion/product (e.g., ترتوي, تجود, نلتقي). Use it to bridge Saudi heritage with the brand.
</technique_instruction>

<negative_few_shot_examples>
<!-- This teaches the model exactly what "Weak/Fail" looks like and how to fix it -->
Example 1 (FAIL - Too long, preachy, violates red line):
"قهوة مختصة، لمّا تشعر بالجوع بعد يوم طويل من الصيام، تخيل اللحظة اللي تفك فيها الخمار وتقول: أخيرًا وقت الإفطار!"
Correction (PASS - Short, punchy, culturally elegant, Paradox Hunter):
"ننتظر الأذان عشان نروي عطشنا، ومع أول رشفة من قهوتنا.. يبتدي اليوم من جديد. جربها اليوم."

Example 2 (FAIL - Uses non-Saudi Gulf dialect and is generic):
"شنو ناطرين؟ زين تفضلوا عندنا وجربوا العرض الجديد الحين بمناسبة يوم التأسيس!"
Correction (PASS - Authentic Najdi, Heritage Decoder, under 150 chars):
"من يوم تأسسنا والخير يجود بهالبلد. ومع قهوتنا، نجود بأفضل ما عندنا لنكمل لمتكم."
</negative_few_shot_examples>

<generation_instruction>
Generate exactly 1 option based on the instructions above. Do not include any explanations, intro text, or character counts. Output ONLY the raw Arabic caption.
</generation_instruction>
```

---

### PART 3: Length vs. Depth (Micro-Copywriting Strategies)

To keep creative depth (like a double-meaning word or paradox) under 150 characters, you must enforce **structural formulas** rather than numeric constraints. LLMs do not understand character counts, but they do understand line breaks and word limits.

#### 1. The "Two-Line Rule" Formula
Force the model to write in a strict two-line structure:
*   **Line 1 (The Hook):** The cultural paradox or double-meaning word (Max 8 words).
*   **Line 2 (The Brand Connection):** The resolution or product integration (Max 6 words).

#### 2. Concrete Examples under 130 Characters:

*   **Paradox Hunter (Specialty Coffee):**
    > "ندور الراحة، وما نرتاح إلا إذا تعبنا في تفاصيل قهوتنا. الروقان يبدأ من هنا."
    *(11 words, 76 characters - Sharp, relatable, hits the paradox of effort vs. relaxation).*

*   **Heritage Decoder (Real Estate / Founding Day):**
    > "بيوت تبنى من طين وعزم، وتبقى ملاذ لأجيال تروي التاريخ. في يوم التأسيس، نعتز بجذورنا."
    *(16 words, 92 characters - Uses "تروي" as both "watering the land/roots" and "telling stories").*

---

### PART 4: Model Strategy & Fine-Tuning

#### Why GPT-4o-mini performed similarly to GPT-4o:
Because your prompt was likely trying to teach the LLM *how to be Saudi* and *how to follow creative constraints* at the same time. In a base model, these instructions compete for attention.

#### The Action Plan: Fine-Tune GPT-4o-mini
Do not waste money on GPT-4o. **Fine-tune GPT-4o-mini.** It is incredibly cheap, fast, and highly effective once aligned.

1.  **Dataset Preparation (The "Golden 1,000"):**
    *   Take your 3,077 high-engagement posts.
    *   Have your human Creative Director select and manually polish the top **1,000 cleanest, most authentic, and culturally safe captions**.
    *   Ensure they are all under 150 characters and use correct Najdi/Hejazi markers.
2.  **Formatting for Fine-Tuning:**
    Create JSONL files where the system prompt is minimal, and the assistant output is the perfect, human-approved caption.
    ```json
    {"messages": [{"role": "system", "content": "You are a Saudi Creative Director. Write a short Instagram caption using [Technique] for [Brand] on [Occasion]."}, {"role": "user", "content": "Brand: Al-Musa Real Estate, Occasion: Founding Day, Technique: Heritage Decoder"}, {"role": "assistant", "content": "بيوت تبنى من طين وعزم، وتبقى ملاذ لأجيال تروي التاريخ. في يوم التأسيس، نعتز بجذورنا."}]}
    ```
3.  **The Result:** 
    Fine-tuning embeds the dialect, the length constraint, and the cultural safety directly into the model's weights. You can then remove 70% of the rules from your system prompt, making the generation incredibly fast, stable, and consistently high-quality.

---

### PART 5: The Learning Loop (Solving the Evaluation Problem)

Since LLM-based creative scoring (like your GPT-4o judge) has a near-zero correlation (+0.08) with human taste, you must build a **Deterministic Guardrail + Human-in-the-Loop (HITL)** system.

```
[Generation] ──> [Automated Deterministic Gate] ──> [Tinder-Style Human Swipe] ──> [Fine-Tuning Loop]
```

#### Step 1: The Automated Deterministic Gate (Hard Filters)
Do not ask an LLM to "rate the creativity on a scale of 1-10." Instead, use LLMs (or simple regex) for **binary, objective compliance checks only**:

*   **Length Check:** Is it > 170 characters? (Reject/Regenerate).
*   **Dialect Blacklist:** Does it contain *شنو، جذي، هيك، شو*? (Reject/Regenerate).
*   **Cultural Red-Line Filter:** Use a highly specific prompt to look *only* for violations: *"Does this text mention beds, sleeping, bedrooms, or removing/adjusting clothing? Answer only YES or NO."* (If YES, hard block and flag).

#### Step 2: The "Tinder-Swipe" Human Interface (Scalable HITL)
You cannot have a senior Creative Director write or edit everything—it doesn't scale. Instead, build a simple internal web interface for your junior copywriters or social media managers.

*   **The UI:** They see the prompt/brief on the left, and 3 generated options on the right.
*   **The Action:** They click **"Approved" (Swipe Right)** or **"Rejected" (Swipe Left)**. If they reject, they must click one quick-tag reason: *[Too Long] [Bad Dialect] [Cliche] [Incoherent]*.
*   **The Time Cost:** A human can evaluate a 120-character caption in **3 to 5 seconds**. 100 captions can be reviewed in under 10 minutes.

#### Step 3: Feeding the Flywheel
*   **The Approved Captions** go straight to the client/publishing queue and are automatically saved to your `fine_tuning_golden_dataset_v2.jsonl`.
*   **The Rejected Captions** (along with their rejection tags) are saved to a negative dataset. You can use these to update your prompt's `<negative_few_shot_examples>` block weekly.

By implementing this loop, your platform will systematically weed out the "weak" and "fail" generations, pushing your human approval rate past 80% within a few weeks of active fine-tuning.
