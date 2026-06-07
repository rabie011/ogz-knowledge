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
