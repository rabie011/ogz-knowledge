# OGZ Caption Consultation — GPT-4o · Gemini · DeepSeek
# (sent 2026-06-07, all three independent)


========================================================================
# GPT-4o — Caption Consultation Response

To improve the quality of your AI-generated captions and move towards a higher human-approval rate, let's address each of your questions with specific and actionable recommendations.

### 1. METHODOLOGY: Suitability for Short Captions
**Recommendation:**
- **Remove "Authenticity Detective"**: This technique relies heavily on narrative depth and emotional nuance, which are challenging to convey effectively in short captions. It's more suitable for longer formats like video.
- **Focus on "Paradox Hunter"**: This technique showed the highest engagement and is well-suited for short, impactful captions. Exploit its counterintuitive nature for brevity and punch.
- **Simplify "Metaphor Architect"**: Use concise metaphors that can be captured in a single, vivid sentence. Avoid complex metaphor systems unless they can be distilled into a single, powerful image or idea.
- **Leverage "Heritage Decoder"**: Double-meaning words can be powerful in short captions if they are immediately clear and culturally resonant. Ensure the word choice is intuitive to the target audience.

### 2. PROMPTING: Reliable Architecture for Saudi Copy
**Specific Prompt Structure:**
- **Template Selection**: Choose 2-3 high-engagement templates that align closely with the brand and occasion.
- **Cultural and Dialect Filters**: Explicitly state dialect preferences and red lines at the start of the prompt.
- **Technique Integration**: Clearly define the chosen technique and provide a concise example of its application.
- **Brevity Focus**: Instruct the model to prioritize impact over detail, emphasizing the need for a single clear idea.
- **Prompt Example:**
  ```
  أنتج تعليقًا قصيرًا وجذابًا لعلامة سعودية لعيد الوطني باستخدام تقنية "الصياد المتناقض". استخدم النجدية وتجنب الكلمات المحظورة. اختر فكرة مستفزة ومرحة مثل "العكس هو الصحيح". الطول الأقصى: 150 حرف. 
  ```

### 3. LENGTH vs DEPTH: Balancing Technique with Brevity
**Recommendation:**
- **Focus on a Single Element**: For techniques like "Heritage Decoder," choose a word that naturally encapsulates the essence of the message.
- **Use Implied Meaning**: Allow cultural context to fill in gaps, relying on shared cultural knowledge to convey depth without extra words.
- **Prioritize Emotional Impact**: Ensure that the primary feeling or insight is immediately clear—this can often convey more than detailed explanation.

### 4. MODEL STRATEGY: Evaluating GPT-4o-mini vs. Fine-Tuning
**Recommendation:**
- **Fine-Tune on Saudi Dialect**: Fine-tuning a model specifically on Saudi dialect and cultural nuances could improve performance significantly. It allows the model to better understand subtle linguistic and cultural cues.
- **Use a Hybrid Approach**: Integrate the fine-tuned model with your existing platform to test against current outputs, focusing on the areas where the present model underperforms.

### 5. THE LEARNING LOOP: Building a Scalable Quality Feedback System
**Recommendation:**
- **Crowdsource Human Review**: Develop a structured feedback system using a small panel of culturally aware reviewers, possibly crowdsourced within the region. Use a scoring system that identifies specific strengths and weaknesses.
- **Iterative Testing**: Implement A/B testing with real audiences to gather engagement metrics directly from the platform.
- **Feedback-Driven Iteration**: Use this data to iteratively refine prompts and techniques. Prioritize changes based on which aspects most consistently enhance engagement and cultural alignment.

### Implementation Plan
- **Short-term**: Refine your existing prompt structures according to the above recommendations. Remove "Authenticity Detective" from caption generation.
- **Medium-term**: Begin fine-tuning a model with Saudi-specific data and dialect nuances. Set up a feedback loop with a small panel of reviewers.
- **Long-term**: Scale reviewer feedback by building a community of brand advocates or influencers who can provide ongoing qualitative insights.

By implementing these targeted changes, you should be able to significantly enhance the cultural appropriateness, creativity, and engagement of your AI-generated captions.



========================================================================
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



========================================================================
# DeepSeek — Caption Consultation Response

Here’s your **actionable, specific roadmap** to improve human approval rates, based on your data and constraints:

---

### 1. **METHODOLOGY: Prune or Adapt Techniques for Short-Form**
- **KILL** the *Authenticity Detective* (two-scene contrast) for captions.  
  - It’s inherently long and culturally risky (private scenes). Reserve for video scripts.  
- **PRIORITIZE** these 3 for captions:  
  - **Paradox Hunter** (counterintuitive flip): Your data shows it’s underused and high-performing.  
  - **Heritage Decoder** (double-meaning word): Works in short form if the word is punchy (e.g., "ترتوي" = land drinks/stories told).  
  - **Firaasa Architect** (cultural truth): BUT **constrain it to 1 line max** (no preamble).  
- **Metaphor Architect**: Only if the metaphor is **1-step** (e.g., "مثل قهوة الصباح، بدايتك الجديدة") — no "but wait" reveals.  

---

### 2. **PROMPTING: Rigid Scaffolding + Forced Brevity**
**Prompt Architecture:**  
```markdown
ROLE: Saudi Creative Director specializing in [sector].  
TASK: Write a 1-2 line Instagram caption (MAX 150 chars) using the [TECHNIQUE].  

INPUTS:  
- BRAND VOICE: [3 bullet points, e.g., "formal but warm", "uses desert metaphors"].  
- TECHNIQUE: [Paradox Hunter/Heritage Decoder/etc.] + [1-sentence definition].  
- REAL EXAMPLES: [3 high-engagement captions from your gold tier].  
- SAUDI DIALECT RULES: Use [وش، الحين، يالله] / Avoid [شنو، جذي].  
- CULTURAL RED LINES: ABSOLUTELY NO [bedrooms, vulnerability, clothing].  

OUTPUT RULES:  
1. FIRST 5 WORDS must hook (no filler like "يسرنا أن").  
2. If using Heritage Decoder, the double-meaning word MUST appear in first 10 words.  
3. END with a product call-to-action or hashtag (no open-ended reflections).  
```  
**Why this works:** Forces conciseness by design. Real examples anchor quality; dialect rules are non-negotiable.

---

### 3. **LENGTH vs DEPTH: Creative Compression**  
- **Heritage Decoder**:  
  - Bad: "في رمضان، الأرض ترتوي بالماء وقلوبنا ترتوي بالذكريات الجميلة مع العائلة حول المائدة" (too long).  
  - Good: "رمضان يروي الأرض.. وقهوتنا تروي لحظاتك" (48 chars).  
- **Paradox Hunter**:  
  - Bad: "عادةً الدفايات تمنحك الدفء، لكن دفايتنا الجديدة تعطيك الإحساس بالصحراء الحارّة في الشتاء!" (verbose).  
  - Good: "دفاية تشعرك بحَرّ الصيف.. في الشتاء!" (45 chars).  

**Rule:** If the technique can’t fit in 150 chars, it’s the wrong technique for captions.

---

### 4. **MODEL STRATEGY: Optimize Prompting First**  
- **Forget fine-tuning** (for now). Your issue is prompt control, not model knowledge.  
- **Test Claude 3 Haiku** (better at brevity than GPT-4) with your scaffolded prompt.  
- **Add negative examples**: Feed the model your FAIL cases with explanations (e.g., "This violated red lines by mentioning bedrooms").  

---

### 5. **LEARNING LOOP: Human-in-the-Light (Not Dark)**  
- **Label 500 human-approved captions** with:  
  - Technique used (e.g., Paradox Hunter).  
  - Hook structure (e.g., "question", "cultural truth").  
  - Hashtag/CTA pattern.  
- **Train a classifier** to predict human approval **based on STRUCTURE, not content** (e.g., "captions starting with a question + Paradox Hunter have 80% approval").  
- **Automate structural checks**:  
  - "Does the first 10 words contain a dialect marker?"  
  - "Is the technique detectable?"  
  - "Is CTA present?"  

---

### **PRIORITY ORDER**  
1. Kill Authenticity Detective for captions; prioritize Paradox Hunter.  
2. Implement the scaffolded prompt with **strict length hooks**.  
3. Build a structural classifier (not content scorer) to approximate human judgment.  

**Expected outcome:** Shift from 5/30 to ~15/30 approval by eliminating length/technique mismatches and enforcing structural rules. No magic — just ruthless constraints.

