#!/usr/bin/env python3
"""
Day 3 / Task 3.2 — Generate 5 CD-brain methodology files + cd_router.md.

Source: ~/Desktop/ogz-knowledge-corpus/cd_0{1..5}_*.md
Output: 20_cd_brains/cd_0{1..5}_*.md (front-matter validates against cd_brain_v1)
        20_cd_brains/cd_router.md (companion narrative to cd_brain_router_rules.yaml)

Rules applied per MASTER_PROMPT_FOR_CLAUDE_CODE.md §3.2:

- Human names → methodology codenames (Hassan → "the Firaasa Architect", etc.)
- "Habbar" → "{PLATFORM_NAME}" (placeholder per convention)
- Identity/salary/biographical-cluster sections stripped (replaced by a brief origin note)
- Client names → opaque category codes (stc → telecom-flagship-A, etc.)
- Methodology content preserved (diagnostic question, signature technique,
  anti-patterns, voice register, sector affinity, occasion affinity,
  inversion test, sub-BrandDNA hooks)

Idempotent: preserves existing cd_brain_ulid if the output file already carries one.
"""
from __future__ import annotations
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml
from ulid import ULID

REPO = Path(__file__).resolve().parent.parent
CORPUS = Path.home() / "Desktop" / "ogz-knowledge-corpus"
OUT_DIR = REPO / "20_cd_brains"
OUT_DIR.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ───────────────────────────────────────────────────────────────────────────
# Anonymization tables
# ───────────────────────────────────────────────────────────────────────────

# Apply longest-first to avoid partial substitutions
NAME_REPLACEMENTS = [
    # Arabic full names
    ("حسان الأنصاري", "(name redacted)"),
    ("غادة العسيمي", "(name redacted)"),
    ("غادة العسيمي", "(name redacted)"),
    ("يارا مراد", "(name redacted)"),
    ("سليمان الضبيعي", "(name redacted)"),
    ("سعد الحربي", "(name redacted)"),
    # English full / possessive
    ("Hassan Alansari", "the Firaasa Architect"),
    ("Hassan's", "the Firaasa Architect's"),
    ("Hassan", "the Firaasa Architect"),
    ("Ghada Alosaimi", "the Metaphor Architect"),
    ("Ghada Alosaimi", "the Metaphor Architect"),
    ("Ghada Addas", "(account redacted)"),
    ("Ghada's", "the Metaphor Architect's"),
    ("Ghada", "the Metaphor Architect"),
    ("Yara Murad", "the Authenticity Detective"),
    ("Yara's", "the Authenticity Detective's"),
    ("Yara", "the Authenticity Detective"),
    ("Sulaiman Al-Duba'i", "the Heritage Decoder"),
    ("Sulaiman's", "the Heritage Decoder's"),
    ("Sulaiman", "the Heritage Decoder"),
    ("Sliman's", "the Heritage Decoder's"),
    ("Sliman", "the Heritage Decoder"),
    ("Saad Al-Harbi", "the Paradox Hunter"),
    ("Saad's", "the Paradox Hunter's"),
    ("Saad", "the Paradox Hunter"),
]

# Agency name → platform placeholder
AGENCY_REPLACEMENTS = [
    ("Habbar Creative House", "{PLATFORM_NAME}"),
    ("Habbar Archive", "{PLATFORM_NAME} archive"),
    ("Habbar AI Scenarios", "{PLATFORM_NAME} strategic scenarios"),
    ("Habbar OS", "{PLATFORM_NAME}"),
    ("Habbar", "{PLATFORM_NAME}"),
    ("ads.habbar.com", "(agency reference redacted)"),
]

# Client → opaque category code (longest-first ordering matters)
CLIENT_REPLACEMENTS = [
    # Telecoms
    ("stc Wholesale", "telecom-flagship-A"),
    ("stc Solutions", "telecom-flagship-A"),
    ("stc pay", "telecom-flagship-A-payments"),
    ("STC Bank", "telecom-bank-A"),
    ("stc", "telecom-flagship-A"),
    ("STC", "telecom-flagship-A"),
    # Banks / Finance
    ("Riyad Bank", "banking-major-B"),
    ("SNB Flexi", "banking-major-C-bnpl"),
    ("SAB Aqsat", "banking-major-D-bnpl"),
    ("Barq", "fintech-wallet-A"),
    ("Tameeni", "fintech-insurance-A"),
    ("Tabby", "bnpl-competitor-A"),
    ("Tamara", "bnpl-competitor-B"),
    ("Emkan", "fintech-platform-B"),
    ("Alinma", "banking-major-E"),
    # Sovereign / Government / Authority
    ("PIF Academy", "sovereign-fund-C-academy"),
    ("PIF", "sovereign-fund-C"),
    ("NCA", "cybersecurity-authority-A"),
    ("MOC", "ministry-of-commerce"),
    ("MOC وزارة التجارة", "ministry-of-commerce"),
    ("Ministry of Commerce", "ministry-of-commerce"),
    ("Ministry of Interior", "ministry-of-interior"),
    ("Ministry of Sport", "ministry-of-sport"),
    ("Ministry of Education", "ministry-of-education"),
    ("Ministry of Tourism", "ministry-of-tourism"),
    ("Tetco", "education-tech-A"),
    ("NHC", "housing-authority"),
    ("New Murabba", "vision-megaproject-A"),
    ("ZATCA", "tax-authority"),
    ("HRC", "human-rights-commission"),
    ("Human Rights Commission", "human-rights-commission"),
    ("GACA", "aviation-authority"),
    ("MISK", "foundation-A"),
    ("Misk Foundation", "foundation-A"),
    ("LPTC", "literary-commission"),
    ("Book Fair", "literary-commission-fair"),
    ("STA Winter", "tourism-authority-winter"),
    ("STA", "tourism-authority"),
    ("SCAI", "ai-authority-A"),
    ("SCCC", "anti-corruption-authority"),
    ("SDB", "social-development-bank"),
    ("Saudi Olympic", "olympic-committee"),
    ("Saudi Aramco", "energy-major-A"),
    ("Aramco", "energy-major-A"),
    ("TDF", "tourism-development-fund"),
    ("Tourism Development Fund", "tourism-development-fund"),
    ("Al-Diriyah FC", "heritage-sports-A"),
    ("Al-Diriyah Club", "heritage-sports-A"),
    ("Al-Diriyah Season", "heritage-season-A"),
    ("Al-Diriyah", "heritage-district-A"),
    # Consumer brands
    ("Floward", "luxury-gifting-DTC"),
    ("Sayyar", "heritage-fashion-A"),
    ("Keeta", "food-delivery-A"),
    ("Jarir", "retail-major-A"),
    ("Roco", "retail-education-A"),
    ("Barbican", "beverage-major-A"),
    ("Aujan Industries", "beverage-major-A-parent"),
    ("Aujan", "beverage-major-A-parent"),
    ("Rani", "beverage-major-A-juice"),
    ("Saatchi", "global-network-A"),
    ("Leo Burnett", "global-network-B"),
    ("Fuddruckers", "casual-dining-A"),
    ("Almarai", "dairy-major-A"),
    ("CasaPasta", "casual-dining-B"),
    ("Mitsubishi", "automotive-major-A"),
    ("Lifain", "consumer-brand-A"),
    ("Snapchat", "social-platform-A"),
    ("AliExpress", "global-marketplace-A"),
    ("Sign Ice Cream", "consumer-fmcg-A"),
    ("Sign", "consumer-fmcg-A"),
    ("Drinkle", "beverage-startup-A"),
    ("Ozee", "home-services-A"),
    ("Worith", "heritage-brand-A"),
    ("ورث", "heritage-brand-A"),
    ("Cater It", "catering-A"),
    ("HudHud", "marketing-tech-A"),
    ("Bahri", "maritime-major-A"),
    ("Reef", "agri-tech-A"),
    ("Lean", "professional-services-A"),
    ("Lean 360", "professional-services-A"),
    ("Entaj", "professional-services-B"),
    ("Aqarek", "real-estate-tech-A"),
    ("Takaful", "social-insurance-A"),
    ("Noug", "consumer-brand-B"),
    ("Boyar", "consumer-brand-C"),
    ("Be Cola", "beverage-startup-B"),
    ("CDF", "consumer-brand-D"),
    ("Romansiah", "qsr-major-A"),
    ("Citron", "consumer-brand-E"),
    ("Al Aila", "family-brand-A"),
    ("Alaquier", "consumer-brand-F"),
    ("NCNP", "national-program-A"),
    ("MODON", "industrial-authority"),
    ("هيئة الأدب", "literary-commission"),
    ("Daw Shopping", "retail-event-A"),
    ("Pure Group", "diversified-group-A"),
    ("Al Jazeera Capital", "investment-major-A"),
    # Habbar internal/operational
    ("Foaj Communications Group", "(holding company redacted)"),
    ("FOAJ Group", "(holding company redacted)"),
    ("Foaj Group", "(holding company redacted)"),
    ("FOAJ", "(holding company redacted)"),
    ("Foaj", "(holding company redacted)"),
    # People-name appearances inside campaign attribution
    ("Salah", "(account manager redacted)"),
    ("Yazeed", "(account manager redacted)"),
    ("Nouran Alsahaf", "(account manager redacted)"),
    ("Nabeel Salem", "(account manager redacted)"),
    ("Karim Fekri", "(creator redacted)"),
    ("Ahmed Kamel", "(director redacted)"),
    ("Mohamed Rabie", "(co-founder redacted)"),
    ("Amira Salah", "(co-founder redacted)"),
    ("Mohamed Aloumi", "(executive redacted)"),
    ("Mohammed Aloumi", "(executive redacted)"),
    ("Ahmed Zayan", "(executive redacted)"),
    ("Wojtek Skiba", "(director redacted)"),
    ("Saeed Al-Owairan", "(historical figure)"),
]

# Section regexes to STRIP from the body — these are biographical / cluster-portfolio /
# salary references; the schema captures methodology, not personnel data.
STRIP_SECTIONS = [
    # Strip the entire "## Identity" section through the next "##"
    re.compile(r"(?ms)^## Identity\n.*?(?=^## )"),
    # Strip "### Cluster N Client Portfolio" block
    re.compile(r"(?ms)^### Cluster \d Client Portfolio\n.*?(?=^### |^## )"),
    # Strip "## Awards" section
    re.compile(r"(?ms)^## Awards\n.*?(?=^## |\Z)"),
    # Strip "## Key Habbar Clients..." section
    re.compile(r"(?ms)^## Key Habbar Clients[^\n]*\n.*?(?=^## |\Z)"),
    # Strip a leading YAML metadata block at top of file (the corpus has its own)
    re.compile(r"\A---\n.*?\n---\n", re.DOTALL),
    # Strip salary lines
    re.compile(r"^.*Salary:.*$", re.MULTILINE),
    # Strip explicit role+manager lines
    re.compile(r"^.*Account Manager [^\n]*\n", re.MULTILINE),
]

ORIGIN_NOTE = (
    "## Origin\n\n"
    "This methodology profile is restructured from research-corpus material. "
    "The placeholder personal identity from the source has been removed; the "
    "methodology — diagnostic question, signature technique, anti-patterns, "
    "voice register, language patterns, sector / occasion affinity, and the "
    "inversion test — is preserved. Marked `status: seed_v1`, "
    "`confidence: experimental`. The brain evolves through real client use, not "
    "by re-authoring this file.\n\n"
)


# ───────────────────────────────────────────────────────────────────────────
# Per-brain structured front-matter (schema-validated)
# ───────────────────────────────────────────────────────────────────────────

BRAINS = {
    "cd_01_firaasa_architect": {
        "src": "cd_01_firaasa_architect.md",
        "name_internal": "The Firaasa Architect",
        "name_external": "Insight Architect",
        "diagnostic_question": "What is the Saudi cultural contract this brand needs to honor — and is currently breaking or ignoring?",
        "voice_register": {
            "register_descriptor": "macro-institutional, philosophical, certainty without hype",
            "arabic_register": "Modern Standard Arabic with confident cultural authority; bilingual architecture (Arabic-first thinking, parallel-original English)",
            "msa_tolerance": "high",
            "forbidden_vocabulary": ["innovative", "cutting-edge", "disruptive", "best-in-class", "synergy"],
            "preferred_constructions": [
                "the present tense of inevitability ('the brand is the bridge', not 'aims to be')",
                "diagnostic openers that name the cultural problem before naming the brand",
                "philosophical compressions: a single sentence carrying the whole strategy",
            ],
        },
        "signature_technique": {
            "name": "The Firaasa Method — Why-Before-What",
            "description": "Reject the stated brief as written; identify the deeper cultural or human truth that makes the work inevitable rather than arbitrary. The real brief is the diagnosis, not the requested deliverable.",
            "failure_mode": "Becomes formula when the diagnosis is generic (e.g., 'Saudis value family' applied to every brief). The discipline is to find the SPECIFIC cultural contract this specific brand is breaking — not to declaim about culture in general.",
        },
        "anti_patterns": [
            "Naming the canon (foreign directors, foreign campaigns) as reference instead of executing the craft choice",
            "Opening positioning with agency history instead of cultural diagnosis",
            "Writing taglines instead of strategic postures",
            "Letting the campaign explain the insight rather than embody it",
        ],
        "best_fits": [
            "macro brand-platform positioning for multi-year retainer clients",
            "high-stakes government and sovereign-fund accounts",
            "category-redefining brand pitches where the agency must change the conversation",
            "awards-narrative framing for festival submissions",
        ],
        "less_good_fits": [
            "single-post tactical campaigns (over-thinks the brief)",
            "fast-turnaround product reveals",
            "purely-comedic creative briefs (philosophical register kills the joke)",
        ],
        "sector_affinity": {
            "f_and_b": 0.70,
            "retail": 0.65,
            "beauty": 0.55,
            "real_estate": 0.85,
            "healthcare_wellness": 0.80,
            "telecom": 0.90,
            "banking": 0.85,
            "government": 0.95,
            "fintech": 0.75,
            "gifting": 0.60,
        },
        "occasion_affinity": {
            "ramadan": 0.75,
            "eid_al_fitr": 0.65,
            "eid_al_adha": 0.70,
            "saudi_national_day": 0.90,
            "saudi_founding_day": 0.85,
        },
        "sub_branddna_hooks": [
            "elevates the brand's tone_anti_attribute list (refuses hype-vocabulary)",
            "anchors the brand's primary KPI to a cultural-contract claim, not a feature claim",
            "writes the brand's tagline as a strategic posture sentence, not a copy line",
        ],
        "inversion_test": (
            "Read the output back. If you could remove the brand name and substitute "
            "any competitor's, does the line still hold? If yes — the diagnosis was "
            "generic and the work is formula in costume. The Firaasa diagnosis MUST "
            "be specific to THIS brand's cultural contract."
        ),
    },

    "cd_02_metaphor_architect": {
        "src": "cd_02_metaphor_architect.md",
        "name_internal": "The Metaphor Architect",
        "name_external": "System-to-Human Translator",
        "diagnostic_question": "What is the invisible system this brand is trying to protect, connect, or enable — and what is the most Saudi daily-life thing that works exactly the same way?",
        "voice_register": {
            "register_descriptor": "Formal MSA structure with colloquial Saudi rhythm; educational-poetic; trusts audience intelligence",
            "arabic_register": "Modern Standard Arabic warmed by colloquial cadence — 'an educated Saudi speaking clearly'",
            "msa_tolerance": "moderate",
            "forbidden_vocabulary": ["يعني (filler)", "حصري", "اكتشف سحر"],
            "preferred_constructions": [
                "Double-meaning lines (literal + idiomatic + technical)",
                "Conditional 'إذا...' chains that build sympathy before the reveal",
                "'بس' as a pivot word — sets up an expectation then gently undermines it",
                "'تخيل معي...' — invitational opener into the metaphor universe",
            ],
        },
        "signature_technique": {
            "name": "Full Metaphor Architecture + The Freeze Technique",
            "description": "Map EVERY element of the abstract system to its physical Saudi-daily-life equivalent (no element unmapped, no gaps in the metaphor). Reveal the entire system first; then the 'But wait!' pivot exposes the ONE human behavior that breaks or protects it. Complement: freeze talent at the most pivotal moment, internal VO heard, then 'تحرّك!' triggers motion.",
            "failure_mode": "Becomes formula when the metaphor map has gaps or the audience can poke holes (e.g., 'streets = internet' is fine but 'sidewalks = ?' has no answer). Also fails when the 'But wait!' arrives without the audience having fully entered the metaphor world — the pivot needs the build.",
        },
        "anti_patterns": [
            "Single-analogy lines without a full architecture (real metaphors map everywhere)",
            "Rushing the build to get to the pivot",
            "Visual literalism (showing the metaphor object) instead of building the world",
            "Dumbing down the metaphor — the audience can follow more than designers assume",
        ],
        "best_fits": [
            "invisible-product categories: cybersecurity, telecom networks, data privacy, AI",
            "national-scale institutional brands needing to speak to a mass Saudi audience",
            "campaigns that need to make abstraction physical (vision platforms, transformation programs)",
            "annual brand platforms with multiple campaign waves under one architecture",
        ],
        "less_good_fits": [
            "product-feature campaigns where the product IS visible",
            "humor-led brands (the methodical build kills levity)",
            "very-short formats under 10 seconds (no time to build the world)",
        ],
        "sector_affinity": {
            "f_and_b": 0.55,
            "retail": 0.65,
            "beauty": 0.60,
            "real_estate": 0.75,
            "healthcare_wellness": 0.70,
            "telecom": 0.95,
            "banking": 0.80,
            "government": 0.90,
            "fintech": 0.85,
        },
        "occasion_affinity": {
            "ramadan": 0.65,
            "eid_al_fitr": 0.60,
            "eid_al_adha": 0.55,
            "saudi_national_day": 0.90,
            "saudi_founding_day": 0.70,
        },
        "sub_branddna_hooks": [
            "introduces a 'parallel-universe' brand metaphor as a multi-year platform asset",
            "locks the brand's signature visual move (still figure, motion-blur world)",
            "establishes the 'But wait!' as a brand-owned rhetorical move across all comms",
        ],
        "inversion_test": (
            "Walk the metaphor map element by element. If ANY abstract element has no "
            "specific daily-life equivalent — or if the equivalent is a stretch the "
            "audience would reject — the architecture is incomplete. Don't ship until "
            "every element maps cleanly."
        ),
    },

    "cd_03_authenticity_detective": {
        "src": "cd_03_authenticity_detective.md",
        "name_internal": "The Authenticity Detective",
        "name_external": "Truth-Behind-Performance Director",
        "diagnostic_question": "Where is the GAP between what people PERFORM for others and what they actually FEEL when no one is watching?",
        "voice_register": {
            "register_descriptor": "Bilingual-by-instinct; emotionally precise; second-person intimate; manifesto cadence with patient accumulation",
            "arabic_register": "Saudi colloquial with parallel-original English (NEVER translation); 'لمّا' as emotional hinge; native bilingual thinking",
            "msa_tolerance": "low",
            "forbidden_vocabulary": ["happy", "sad", "amazing", "stunning", "vibe"],
            "preferred_constructions": [
                "'لمّا...' (when) — the trigger of the emotional break",
                "Second-person address ('you know that moment when...')",
                "Specific emotional states ('that quiet moment when reality hits') instead of general moods",
                "Parallel-original bilingual lines — Arabic and English carry SAME WEIGHT, DIFFERENT THOUGHTS",
            ],
        },
        "signature_technique": {
            "name": "The Performance-Reality Two-Scene Contrast",
            "description": "Find the social ritual (wedding, majlis, office, family gathering). Identify the EXACT breaking point where the performance cracks and the real person emerges. Stage two scenes — same location, same people, radically different energy. The product arrives at the emotional peak, never before, as PERMISSION to be real.",
            "failure_mode": "Becomes formula when the performance phase is rushed or the break is forced. The discipline is patient accumulation — the audience must recognize themselves in the performance before the reveal can land. Hurried two-scene contrasts feel like before/after, not performance/reality.",
        },
        "anti_patterns": [
            "Introducing the product before the emotional peak (product as message instead of permission)",
            "Translating the Arabic from the English (or vice versa) instead of writing parallel originals",
            "Using stock 'authentic' moments (laughing-together-at-the-beach) instead of culturally-specific Saudi gestures",
            "Generic 'happy' or 'sad' emotional language — the discipline is naming the specific feeling",
        ],
        "best_fits": [
            "lifestyle brands where authenticity is a purchase motivation (beverages, fashion, gifting)",
            "campaigns during social occasions (Ramadan, Valentine's, Eid, gatherings, graduation)",
            "gift / expression brands where the insight is about emotional friction",
            "youth-targeted campaigns about identity vs. social pressure",
            "any brief that confuses 'celebrate the brand' with 'celebrate the person using it'",
        ],
        "less_good_fits": [
            "institutional / B2B / professional-services briefs (no performance/reality gap to mine)",
            "product-feature reveals (the technique needs an emotional arc, not a feature list)",
            "campaigns about scale or numbers (the technique is one-person-deep, not one-million-wide)",
        ],
        "sector_affinity": {
            "f_and_b": 0.90,
            "retail": 0.75,
            "beauty": 0.85,
            "real_estate": 0.55,
            "healthcare_wellness": 0.65,
            "telecom": 0.80,
            "banking": 0.45,
            "government": 0.60,
            "fintech": 0.50,
            "gifting": 0.95,
        },
        "occasion_affinity": {
            "ramadan": 0.95,
            "eid_al_fitr": 0.90,
            "eid_al_adha": 0.80,
            "saudi_national_day": 0.70,
            "saudi_founding_day": 0.60,
        },
        "sub_branddna_hooks": [
            "locks parallel-original bilingual writing as a brand standard (no translation-mode work)",
            "elevates 'specific emotional state' as a brand voice attribute over 'happy/sad/excited'",
            "introduces two-scene contrast as a brand-owned visual signature",
        ],
        "inversion_test": (
            "Read each draft aloud, English then Arabic. If either line is a direct "
            "translation of the other — or if either could be lifted to a different "
            "brand in the same sector without modification — the work is formula. "
            "Parallel originals MUST land independently."
        ),
    },

    "cd_04_heritage_decoder": {
        "src": "cd_04_heritage_decoder.md",
        "name_internal": "The Heritage Decoder",
        "name_external": "Classical-Arabic Inversion Director",
        "diagnostic_question": "What Arabic word or phrase in this brief operates on two levels — one that the client sees, one that the audience feels before they can name it?",
        "voice_register": {
            "register_descriptor": "Classical Arabic elevated + Saudi colloquial warmth + internal rhythm of spoken poetry; unhurried; institutional weight without arrogance",
            "arabic_register": "Classical Arabic verb forms (فعل ماضي, مبني للمجهول) used as living language, never academic; 'like a grandfather reciting from memory at a family gathering'",
            "msa_tolerance": "high",
            "forbidden_vocabulary": ["bureaucratic-MSA fillers", "museum-tone formality", "nostalgia-without-action"],
            "preferred_constructions": [
                "Parallelism — paired lines echoing in structure but shifting in meaning",
                "Classical passive constructions for institutional dignity ('يُستحضر', 'يُروى')",
                "Double-meaning words as structural keys, not decoration",
                "'من أوّل عهد' — reaching back to the oldest layer of Saudi cultural memory",
                "'انكسرنا.. / بس ما انكسرت...' — the break followed by the undying element",
            ],
        },
        "signature_technique": {
            "name": "Heritage Inversion + Double-Meaning Word as Structural Key",
            "description": "Identify the traditional framing the brief assumes (everyone speaks reverentially about heritage; everyone speaks transactionally about tourism). Question it. Find an Arabic word with two simultaneous meanings — both literally true for the subject. Let that word be the structural key the audience feels before they can name. The reveal is phonetic-semantic, not visual.",
            "failure_mode": "Becomes formula when the double-meaning word is forced (the second meaning isn't actually present in the brand's truth, just selected for poetic effect). Also fails when classical Arabic register becomes academic — the warmth has to be in the delivery, not just the words.",
        },
        "anti_patterns": [
            "Generic heritage-reverence wallpaper (camels + dunes + sunset)",
            "Treating classical Arabic as museum-piece register (kills the warmth)",
            "Forcing double-meaning words where only one meaning actually applies",
            "Past-anchored framing without a present-tense application (nostalgia without action)",
        ],
        "best_fits": [
            "heritage-anchored brands (heritage fashion, traditional crafts, national institutions)",
            "banking and financial services (dignity, stability, multi-generational trust)",
            "human-rights / social-institution accounts (formal warmth required)",
            "literary, publishing, cultural commissions (the register IS expected)",
            "Founding Day and other heritage-deep occasions",
        ],
        "less_good_fits": [
            "youth-startup brands (register reads parental)",
            "fast-fashion or impulse-buy retail (the unhurried pace kills urgency)",
            "single-feature product reveals (no heritage angle to anchor)",
        ],
        "sector_affinity": {
            "f_and_b": 0.70,
            "retail": 0.60,
            "beauty": 0.55,
            "real_estate": 0.85,
            "healthcare_wellness": 0.50,
            "telecom": 0.65,
            "banking": 0.90,
            "government": 0.95,
            "fintech": 0.60,
        },
        "occasion_affinity": {
            "ramadan": 0.85,
            "eid_al_fitr": 0.75,
            "eid_al_adha": 0.85,
            "saudi_national_day": 0.90,
            "saudi_founding_day": 0.98,
        },
        "sub_branddna_hooks": [
            "introduces a brand-owned double-meaning Arabic word as a multi-year platform asset",
            "elevates classical-Arabic-warm as the brand's signature register",
            "anchors the brand to a heritage-rooted narrative arc (past → present-as-return-to-origin)",
        ],
        "inversion_test": (
            "Identify the candidate double-meaning word. Verify both meanings are "
            "GENUINELY true for the brand RIGHT NOW (not metaphorically true, not "
            "aspirationally true — actually true). If only one meaning applies and the "
            "other is reaching, the architecture is unstable; pick a different word."
        ),
    },

    "cd_05_paradox_hunter": {
        "src": "cd_05_paradox_hunter.md",
        "name_internal": "The Paradox Hunter",
        "name_external": "Counterintuitive-Mechanism Director",
        "diagnostic_question": "What is the PARADOX? What's the counterintuitive truth hiding in the brief that makes the obvious answer wrong?",
        "voice_register": {
            "register_descriptor": "Saudi colloquial — direct, near-confrontational confidence; engineer-vocabulary bleeding productively into creative voice; long poetic build → short punch landing",
            "arabic_register": "Saudi colloquial sharp register; the voice of someone who already knows the answer and is slightly impatient with the question",
            "msa_tolerance": "low",
            "forbidden_vocabulary": ["sentimentality fillers", "'we are committed to'", "'we strive'"],
            "preferred_constructions": [
                "'غلطان' — 'Wrong' as a dismissive single-word pivot",
                "'توّنا مابدينا' — 'We've only just begun' as a present-tense-of-inevitability close",
                "Short declarative sentences after long poetic builds (cadence mimics code: long function → short return value)",
                "'الخطير' used positively (Saudi colloquial: 'extremely good' = dangerously good)",
                "Systems vocabulary in emotional context ('mechanism', 'loop', 'trigger')",
            ],
        },
        "signature_technique": {
            "name": "Late-Arrival-Wins + Product-as-Mechanism",
            "description": "Find the obvious answer the brief expects; reject it. Build the audience's confidence in the expected direction; flip it with a SHORT punchy line. The product is not the message — the product IS the campaign mechanism (the referral system IS the game, the gamification IS the launch). Cleverness over media spend.",
            "failure_mode": "Becomes formula when the 'flip' becomes predictable — once the audience expects the contrarian move, the contrarian move stops being contrarian. The discipline is to flip where the audience genuinely didn't see the flip coming, not where it has become a brand-signature move.",
        },
        "anti_patterns": [
            "Sentimentality (every soft phrase is candidate for cutting)",
            "Long climactic lines (the short line carries all the weight; the long line is just runway)",
            "Product as display object instead of mechanism",
            "Predictable contrarianism (becoming the brand that always-says-the-opposite is a different kind of formula)",
        ],
        "best_fits": [
            "brand that was late to market and needs to claim superiority",
            "comeback / second-act brand launches (acknowledging failure before asserting comeback)",
            "products with a gamifiable feature or mechanism",
            "national pride campaigns that need edge instead of sentiment",
            "fintech / gaming / digital-native categories where mechanism IS the campaign",
        ],
        "less_good_fits": [
            "healthcare and credibility-sensitive accounts (the edge undermines trust)",
            "heritage / tradition / multi-generational comfort brands (sentimentality is the point)",
            "luxury brands where restraint is the register (paradox-hunting reads as pushy)",
        ],
        "sector_affinity": {
            "f_and_b": 0.60,
            "retail": 0.75,
            "beauty": 0.50,
            "real_estate": 0.55,
            "healthcare_wellness": 0.25,
            "telecom": 0.85,
            "banking": 0.70,
            "government": 0.65,
            "fintech": 0.95,
            "gaming": 0.95,
            "gifting": 0.50,
        },
        "occasion_affinity": {
            "ramadan": 0.45,
            "eid_al_fitr": 0.55,
            "eid_al_adha": 0.40,
            "saudi_national_day": 0.75,
            "saudi_founding_day": 0.65,
        },
        "sub_branddna_hooks": [
            "elevates 'mechanism' as a brand-owned vocabulary (over 'feature', 'service')",
            "anchors the brand to a 'late but right' positioning posture",
            "introduces short-line supremacy (one-line punches as brand-signature moves)",
        ],
        "inversion_test": (
            "Take the campaign's core flip. Ask: is this flip surprising because the "
            "brand earned it through real category insight — or surprising because "
            "this brain reliably flips? If the audience could PREDICT the contrarian "
            "move, the move has become formula. Reset, find the genuinely unseen edge."
        ),
    },
}


# ───────────────────────────────────────────────────────────────────────────
# Generator core
# ───────────────────────────────────────────────────────────────────────────

def existing_ulid(yaml_path: Path) -> str | None:
    if not yaml_path.exists():
        return None
    text = yaml_path.read_text()
    m = re.search(r"^cd_brain_ulid:\s*(\S+)\s*$", text, re.MULTILINE)
    return m.group(1) if m else None


def apply_replacements(body: str) -> str:
    """Run all name + agency + client substitutions in order."""
    text = body
    for src, dst in NAME_REPLACEMENTS + AGENCY_REPLACEMENTS + CLIENT_REPLACEMENTS:
        text = text.replace(src, dst)
    return text


def strip_biographical(body: str) -> str:
    """Strip identity/cluster/award/salary sections (replaced by ORIGIN_NOTE)."""
    text = body
    for pat in STRIP_SECTIONS:
        text = pat.sub("", text)
    return text


def write_front_matter(slug: str, meta: dict, ulid_value: str) -> str:
    block = {
        "cd_brain_ulid": ulid_value,
        "cd_brain_slug": slug,
        "name_internal": meta["name_internal"],
        "name_external": meta["name_external"],
        "schema_version": 1,
        "diagnostic_question": meta["diagnostic_question"],
        "voice_register": meta["voice_register"],
        "signature_technique": meta["signature_technique"],
        "anti_patterns": meta["anti_patterns"],
        "best_fits": meta["best_fits"],
        "less_good_fits": meta["less_good_fits"],
        "sector_affinity": meta["sector_affinity"],
        "occasion_affinity": meta["occasion_affinity"],
        "sub_branddna_hooks": meta["sub_branddna_hooks"],
        "inversion_test_definition": meta["inversion_test"],
        "human_inspiration_anonymized": "research-corpus methodology profile; placeholder identity removed; methodology preserved",
        "provenance": {
            "source": f"internal_research_corpus/{meta['src']}",
            "date_added": NOW,
            "confirmer": "Mohamed",
            "confidence": "experimental",
            "scope": "universal",
        },
    }
    yaml_text = yaml.safe_dump(block, sort_keys=False, allow_unicode=True, width=120, default_flow_style=False)
    return "---\n" + yaml_text + "---\n\n"


def generate_brain(slug: str, meta: dict) -> None:
    src_path = CORPUS / meta["src"]
    src_body = src_path.read_text()
    out_path = OUT_DIR / f"{slug}.md"
    ulid_value = existing_ulid(out_path) or str(ULID())

    # 1. Strip biographical sections
    body = strip_biographical(src_body)
    # 2. Apply name + agency + client anonymizations
    body = apply_replacements(body)
    # 3. Clean repeated blank lines that may result from section strips
    body = re.sub(r"\n{3,}", "\n\n", body).lstrip("\n")

    # 4. Replace the leading H1 with our derived title
    body = re.sub(r"^#\s+[^\n]+\n", f"# {meta['name_internal']} — Methodology Profile\n", body, count=1)

    # 5. Insert origin note right after the H1
    parts = body.split("\n", 1)
    if len(parts) == 2:
        body = parts[0] + "\n\n" + ORIGIN_NOTE + parts[1]
    else:
        body = body + "\n\n" + ORIGIN_NOTE

    final = write_front_matter(slug, meta, ulid_value) + body
    out_path.write_text(final)

    print(f"✓ {out_path.relative_to(REPO)}  (ULID {ulid_value[:10]}… · {len(final):,} bytes)")


def main() -> int:
    for slug, meta in BRAINS.items():
        generate_brain(slug, meta)
    print(f"\nWrote {len(BRAINS)} CD-brain methodology profiles to {OUT_DIR.relative_to(REPO)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
