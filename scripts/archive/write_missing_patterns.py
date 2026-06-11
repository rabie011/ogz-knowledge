#!/usr/bin/env python3
"""
write_missing_patterns.py
Defines all 46 pattern slugs that appear in obs but have no library file.
Uses same schema and pat() helper as write_all_new_patterns.py.
"""
import json, os
from pathlib import Path

BASE = Path(__file__).parent.parent
PATTERNS_ROOT = BASE / "11_who_to_learn_from" / "patterns"
DATE = "2026-05-24T00:00:00Z"

def pat(ulid, name, slug, subcat, description, sectors, account_count,
        recipe, why, caveats, chains, avg_eng, constraints=None, scope=None):
    obj = {
        "pattern_ulid": ulid,
        "pattern_name": name,
        "pattern_slug": slug,
        "schema_version": 1,
        "description": description,
        "observed_in_sectors": sectors,
        "observed_in_account_count": account_count,
        "structural_recipe": recipe,
        "why_it_works": why,
        "transplantation_caveats": caveats,
        "applicable_chains": chains,
        "avg_engagement_multiplier_observed": avg_eng,
        "cultural_constraints": constraints or [],
        "provenance": {
            "source": "corpus_synthesis_474_obs — referenced in obs but previously undefined",
            "date_added": DATE,
            "confirmer": "corpus_mining_pass_phase3",
            "confidence": "experimental",
            "scope": scope or "sector:f_and_b"
        }
    }
    path = PATTERNS_ROOT / subcat / f"{slug}.json"
    os.makedirs(path.parent, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2))
    return slug

written = []

# ─── VOICE TECHNIQUES ───────────────────────────────────────────────

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K0",
    "CSR Brand Story",
    "csr_brand_story",
    "voice_techniques",
    "Caption or video frames a brand's community contribution, environmental action, charitable giving, or social responsibility initiative as a narrative — not an announcement. The CSR action is the story, not the product.",
    ["f_and_b", "retail"], 5,
    "Structure: [Human impact moment — a person, a community, a place] → [What the brand did] → [Why this is core to who we are] → [Soft invitation to join/support]. No product price. No sales CTA. Tone: earnest, understated, authentic.",
    "Saudi audiences expect brands to contribute to community. When a brand shows it, not just says it, the response is deep loyalty. However, CSR content consistently underperforms on immediate engagement metrics (low like/comment rate) but overperforms on brand sentiment and long-term recall. Use it for relationship-building, not reach.",
    [
        "CSR claim must be verifiable — vague 'we care about the community' without specifics is immediately distrusted.",
        "Avoid CSR-washing: a single post on World Environment Day from a non-eco brand reads as opportunistic.",
        "Best for brands with established track record — new brands attempting CSR positioning before credibility is earned backfire.",
        "Keep the focus on the human impact, not the brand — too much brand presence undermines the authenticity."
    ],
    ["all"], "0.3x-0.5x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K1",
    "Urgency Without Pressure",
    "urgency_without_pressure",
    "voice_techniques",
    "Copy creates genuine desire and time-sensitivity without using pushy sales language. FOMO is implied through scarcity signals (limited availability, seasonal timing, unique experience) — never through countdown clocks or aggressive discount pressure.",
    ["f_and_b", "retail", "beauty"], 5,
    "Signal types: [Limited season] 'فقط في رمضان' — [Limited batch] 'عدد محدود' — [Experiential scarcity] 'لحظة لا تتكرر'. Tone: inviting, warm, wistful — never pushy. No 'اشتري الآن!' No percentage discounts in the scarcity frame. Pair with beautiful visual that makes the loss feel real.",
    "The highest-performing pattern in the corpus (1.0 avg engagement across all observations). Saudi audiences respond to genuine cultural scarcity (Ramadan specials, seasonal ingredients, harvest-timing) as an invitation, not a sales tactic. The pattern works because it respects the audience's intelligence — they know the product is available, but the framing elevates it to an experience not to be missed.",
    [
        "Scarcity must be real — fake urgency ('only 3 left!' on a mass-produced item) is immediately detected and damages trust.",
        "Works best for seasonal F&B specials and limited-run products. Doesn't work for permanently available items.",
        "Colloquial Najdi/Hejazi registers outperform MSA for this pattern — the warmth of dialect makes the invitation feel personal.",
        "Pair with rich sensory visuals — the image must make the audience feel what they'll miss."
    ],
    ["all"], "1.0x-1.4x",
    [],
    "sector:f_and_b+sector:retail+sector:beauty"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K2",
    "Brand Personality Voice",
    "brand_personality",
    "voice_techniques",
    "The brand speaks as a distinct personality — with its own opinions, preferences, and point of view — rather than as a neutral product announcer. The brand might express a food preference, take a playful stance, or voice a relatable opinion about life.",
    ["f_and_b", "retail"], 2,
    "Caption structure: brand expresses first-person opinion or preference. 'نحن ناس ما نتنازل عن...' / 'رأينا الصريح؟ القهوة بدون...' / 'لو سألتنا، الجواب دايماً...'. Tone: confident, warm, slightly playful. The personality must feel consistent across posts — not invented per-post.",
    "Accounts with distinct personalities consistently outperform generic brand voices in comment quality (not just quantity). When an audience feels they know the brand's 'character', they respond as they would to a person — with loyalty, affection, and defense of the brand. Most Saudi F&B brands are still product-focused; personality-led brands occupy clear mental real estate.",
    [
        "Personality must be consistent — a brand that is confident and opinionated in one post but neutral in the next feels schizophrenic.",
        "Opinions must be safe — brand personalities that take political or social stances are high-risk in Saudi context.",
        "Works best for independent/boutique brands. Large chains adopting strong personalities feel inauthentic.",
        "The personality must connect logically to the product — a dessert brand expressing love of sweetness works; a coffee brand expressing opinions on sleep cycles does not."
    ],
    ["all"], "0.8x-1.2x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K3",
    "Employee Pride Story",
    "employee_pride_story",
    "voice_techniques",
    "Content spotlights a team member — a chef, a barista, a craftsperson — as the human face of the brand. Their skill, passion, or story is the narrative. The product emerges from the person, not the other way around.",
    ["f_and_b", "retail"], 2,
    "Structure: [Person introduction — name, role, brief human detail] → [What they make/do and why they love it] → [Product connection as natural extension of their craft]. Visual: person in natural working context, not posed. Tone: pride, warmth, respect. Avoid corporate 'Employee of the Month' framing.",
    "Humanizing a brand through staff stories is proven in global markets but underutilized in Saudi brand content. When done authentically, it signals craft, care, and quality — all high-value signals in premium F&B. It also builds loyalty among staff (recruitment benefit). Best accounts use this as a recurring series, building audience attachment to specific team members.",
    [
        "Staff must consent and feel proud of the feature — forced or reluctant participation shows.",
        "Face visibility compliance applies — staff gender-appropriate presentation, wardrobe codes.",
        "The craft angle must be genuine — 'employee pride' for a low-skill role feels patronizing.",
        "Avoid using staff stories as a CSR substitute — it reads as exploitation."
    ],
    ["all"], "0.7x-1.1x",
    ["Staff wardrobe and presentation must comply with platform and cultural norms."],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K4",
    "Arabic Casual Mood Trigger",
    "arabic_casual_mood_trigger",
    "voice_techniques",
    "Caption opens or closes with a short colloquial Arabic phrase that immediately establishes an emotional mood — warmth, hunger, nostalgia, craving, ease — before any product reference. The phrase is designed to trigger a felt sense, not convey information.",
    ["f_and_b"], 1,
    "1-3 word colloquial opener/closer: 'ولا أطيب...' / 'يا ساتر...' / 'كفا وزيادة' / 'ما في أحسن'. Place at start to set tone, or at end as emotional punctuation. Must be dialect-native — not translated from English. No emoji buffer between phrase and caption body.",
    "Colloquial Arabic phrases activate an immediate cultural-emotional response that MSA or English cannot replicate. These are the phrases Saudi audiences use in real conversation — hearing them from a brand creates an instant sense of familiarity and belonging. The mood trigger primes the reader for the product message before their critical brain engages.",
    [
        "Phrase must be regionally appropriate — Najdi colloquialisms used by a Jeddah-focused brand feel foreign.",
        "Phrase must match the product's mood — a cozy phrase for a high-energy product creates cognitive dissonance.",
        "Avoid trendy phrases that will date quickly — stick to timeless colloquialisms.",
        "International brands attempting colloquial Arabic phrases read as performative and often get the register wrong."
    ],
    ["all"], "0.9x-1.3x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K5",
    "Sensory Irresistibility Copy",
    "sensory_irresistibility_copy",
    "voice_techniques",
    "Caption prioritizes sensory language — taste, texture, smell, sound, warmth — to make the audience physically feel the product through text alone. The copy is designed to trigger the imagination of taste and create involuntary craving.",
    ["f_and_b"], 1,
    "Trigger vocabulary: words like مقرمش، دافئ، ناعم، عطر، سخن، يذوب، طري، كاكاو، زبدة — rich sensory Arabic. Pair with close-up macro visual showing texture, steam, or pour. No generic descriptors ('delicious', 'amazing'). Specificity is required: 'عجينة ترجع إلى وصفة جدتنا' beats 'طعم لا يُنسى'.",
    "The body responds to sensory language before the rational mind engages. Studies show food descriptions with specific sensory words increase ordering intent significantly. In F&B social content, the caption that makes someone feel hungry is the one that drives visit/order intent — not the prettiest visual alone.",
    [
        "Specificity is mandatory — generic sensory language ('so delicious!') performs no better than product name alone.",
        "Must pair with matching visual — sensory copy next to a flat/clinical image creates disconnect.",
        "Avoid overloading — one or two strong sensory triggers outperform a paragraph of them.",
        "Seasonal sensory cues (warm soup in winter, cold drink in summer) amplify the effect significantly."
    ],
    ["all"], "0.8x-1.1x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K6",
    "Saudi Dining Ritual",
    "saudi_dining_ritual",
    "voice_techniques",
    "Content frames the act of eating or drinking as a specifically Saudi cultural ritual — not just a meal, but a practice embedded in hospitality, gathering, and tradition. The ritual framing elevates the product from food to cultural participation.",
    ["f_and_b"], 1,
    "Frame the meal as an event: 'جلسة القهوة' / 'سفرة العيد' / 'غبقة رمضان' / 'كيف الضيافة السعودية'. Reference specific rituals: the pouring of coffee, the arrangement of dates, the first bite after iftar. Visual shows the ritual context, not just the product. Tone: reverent, warm, celebratory.",
    "Saudi audiences deeply identify with their food rituals as cultural markers. Content that accurately represents and celebrates these rituals is received as recognition and validation — the brand understands us. It positions the product within a tradition the audience already loves, rather than asking them to adopt a new behavior.",
    [
        "Ritual must be accurately represented — misrepresentation of Saudi food traditions is a serious cultural offense.",
        "International brands using Saudi dining ritual framing without genuine Saudi roots read as appropriative.",
        "The ritual must be the focus — product placement within the ritual must feel natural, not forced.",
        "Avoid mixing rituals (e.g., Ramadan imagery with non-Ramadan food) — specificity matters."
    ],
    ["all"], "0.9x-1.3x",
    ["Must accurately represent Saudi cultural food practices."],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K7",
    "Nostalgia Cultural Reference",
    "nostalgia_cultural_reference",
    "voice_techniques",
    "Caption or visual invokes a specific shared Saudi cultural memory — a childhood food, a grandmother's recipe, a neighborhood bakery, a school canteen item — to create emotional resonance through collective nostalgia.",
    ["f_and_b", "retail"], 1,
    "Reference a specific shared memory: 'نكهة البطاطس المدرسية' / 'فطور الجمعة عند أمي' / 'طعم الصيف عند الجد'. Specificity is key — the more specific, the more universal the nostalgia paradoxically becomes. Visual: warm tones, soft focus, heritage aesthetic. Tone: wistful, warm, inviting.",
    "Nostalgia is among the most powerful emotional triggers for purchase intent across all markets. In Saudi Arabia, shared cultural memories are especially strong because of the rapid modernization over two generations — audiences have deep emotional attachment to 'the way things were.' Brands that authentically tap into these memories earn trust that no product feature can buy.",
    [
        "Nostalgia must be culturally specific — generic 'childhood memories' without Saudi anchoring is weak.",
        "The memory must connect logically to the product — a coffee brand referencing grandmother's coffee works; referencing her shawarma does not.",
        "International brands using Saudi nostalgia tropes without authentic connection read as hollow.",
        "Avoid over-romanticizing the past in ways that feel politically loaded."
    ],
    ["all"], "0.8x-1.2x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K8",
    "Emotional Brand Moment",
    "emotional_brand_moment",
    "voice_techniques",
    "A single post that captures a genuine emotional beat of the brand — a milestone, a human moment, a gratitude expression, or a behind-the-scenes vulnerability. Not a product post. Not a promotional post. A moment of brand humanity.",
    ["f_and_b", "retail", "beauty"], 1,
    "Structure: [Moment description] → [What it means to us] → [Soft connection to audience]. No CTA. No product price. Examples: first anniversary post, team photo on a hard day, gratitude for reaching a follower milestone, a message from the founder. Tone: genuine, understated, human.",
    "Brand emotional moments build the relationship equity that all commercial posts later draw on. When a brand occasionally shows vulnerability or genuine emotion, it breaks the transaction frame — the audience sees a human entity, not a company. This creates the loyalty that survives price competition and product comparison.",
    [
        "Emotion must be genuine — performative emotion (fake celebrations, manufactured vulnerability) is immediately detected.",
        "Use sparingly — more than 1-2 emotional brand moments per month dilutes the impact.",
        "Must connect to something real in the brand's story — invented emotional moments have no credibility.",
        "Avoid over-produced emotional content — authenticity > production quality for this pattern."
    ],
    ["all"], "0.8x-1.3x",
    [],
    "sector:f_and_b+sector:retail+sector:beauty"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8J9K9",
    "Emotional Brand Connection",
    "emotional_brand_connection",
    "voice_techniques",
    "Copy positions the brand as emotionally connected to the audience's life — not just a product they buy, but a presence in their meaningful moments (morning routines, family gatherings, celebrations, comfort seeking).",
    ["f_and_b"], 1,
    "Frame: 'كل صباح، في كل مجلس، في لحظات السكون'. The brand is woven into life moments, not sold as a product. Caption connects specific life moment → brand presence within it → emotional validation. Tone: intimate, warm, grateful.",
    "Brands that occupy emotional space in life moments are harder to replace than brands that only occupy product categories. The morning coffee brand becomes part of the morning ritual — even when a competitor has better pricing. This emotional stickiness is built post by post over time.",
    [
        "Life moments must resonate with the target audience's actual lifestyle — not aspirational moments they don't live.",
        "Cannot be forced — a brand that genuinely isn't part of people's emotional moments will sound hollow claiming it is.",
        "Works best for brands with high frequency of use (coffee, breakfast items, daily snacks) vs. occasional-use products."
    ],
    ["all"], "0.7x-1.1x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8JAKA",
    "Friendship Loyalty Content",
    "friendship_loyalty_content",
    "voice_techniques",
    "Content frames the brand as shared between friends — the coffee you go to together, the dessert you split, the restaurant that's 'your group's spot.' Friendship and social bonding are the primary value proposition.",
    ["f_and_b"], 1,
    "Visual: 2-3 people (same gender, casual setting), product shared between them. Caption: 'زين مع الأصحاب' / 'لجلساتكم' / 'مكانكم المفضل'. Tone: casual, warm, social. CTA: 'خبّر صديقك' — tag a friend. This pattern naturally generates tagging engagement.",
    "Social eating and drinking is a primary use case for F&B in Saudi Arabia. Framing the brand as the social glue earns both engagement (tagging) and real-world visit conversion (people actually bring friends). The friendship frame also bypasses individual purchase hesitation — people will try something they might not individually because a friend wants to.",
    [
        "Gender-appropriate casting — mixed-gender casual social contexts require careful execution.",
        "Friendship framing works better for casual/value brands than luxury/premium brands.",
        "Tag-a-friend CTAs can generate spam behavior — moderate and ensure genuine engagement quality."
    ],
    ["all"], "0.7x-1.0x",
    ["Social scenes must respect gender norms."],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8JAKB",
    "Brand Origin Positioning",
    "brand_origin_positioning",
    "voice_techniques",
    "Content tells or references the brand's origin story — where it started, why it was founded, what the founder believed. Origin positioning claims authenticity and intentionality before the audience can question it.",
    ["f_and_b", "retail"], 1,
    "Structure: [Where/when it began] → [What the founder believed or wanted to change] → [How the product is the expression of that belief]. One post, 3-4 sentences. Tone: proud, honest, grounded. Works best as a series anchor — returned to periodically.",
    "Origin stories are the most compressed form of brand authenticity signal. In a market saturated with new brands, a clear origin story differentiates and humanizes. Saudi audiences value genuine local origin stories especially — brand started in Riyadh, family recipe, local ingredients. The story doesn't need to be dramatic; it needs to be true.",
    [
        "Origin must be true — fabricated or embellished origin stories collapse when disproven.",
        "Local Saudi origin stories outperform generic entrepreneurship narratives.",
        "Must be genuinely tied to the product — an origin story that doesn't explain why this product exists feels irrelevant.",
        "Don't conflate origin with CSR — origin is about authenticity, CSR is about community contribution."
    ],
    ["all"], "0.7x-1.1x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8JAKC",
    "Saudi Food Heritage Pride",
    "saudi_food_heritage_pride",
    "voice_techniques",
    "Content positions the product within the heritage of Saudi cuisine — connecting it to the deep tradition of Saudi food culture, regional specialties, or generational recipes. The pride is Saudi, not just brand-level.",
    ["f_and_b"], 1,
    "Frame: the product as belonging to a food tradition that Saudis are proud of. Reference: كبسة، مندي، مجبوس، قهوة عربية، تمر، جريش — and connect the brand to this tradition as either a preserver or a modern expression. Tone: proud, warm, educational.",
    "Saudi food culture is experiencing a pride renaissance — Saudis are increasingly proud of their culinary heritage as a national identity marker. Brands that authentically participate in this pride wave earn cultural loyalty beyond product preference. This pattern performs especially well on National Day and founding day occasions but also evergreen.",
    [
        "Brand must have genuine connection to Saudi food heritage — an international franchise claiming Saudi food heritage is inauthentic.",
        "Regional specificity adds power — Najdi food heritage vs. Hejazi food heritage have distinct audiences.",
        "Avoid being preachy or educational in tone — pride, not lecture.",
        "Must not misrepresent traditional recipes or claim authenticity the brand doesn't have."
    ],
    ["all"], "0.8x-1.2x",
    ["Must accurately represent Saudi culinary traditions."],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8JAKD",
    "Indecision Hook",
    "indecision_hook",
    "voice_techniques",
    "Caption opens by voicing a relatable internal struggle about which product/flavor/option to choose — then positions the brand as the solution (or tells the audience to choose for them). The indecision is the audience's indecision, not the brand's.",
    ["f_and_b"], 1,
    "Opening: 'ما عرفنا نختار...' / 'في حيرة؟' / 'قلنا نسألكم'. The brand admits the variety is overwhelming (in a good way), invites audience to comment/vote, or reveals that the team solved the problem for you. Drives comment engagement naturally. Tone: warm, playful, inclusive.",
    "Indecision framing converts passive scrollers into active commenters — the audience has a clear simple task (vote/help decide). It also signals product abundance without sounding like a hard sell. The psychological driver is the commitment bias — once someone comments their preference, they're more likely to buy it.",
    [
        "The options presented must be genuinely appealing — forced indecision between bad options feels hollow.",
        "Don't overuse — more than once per month feels like a mechanic, not a genuine moment.",
        "Follow up with the 'answer' post — the audience expects resolution if you ask for their opinion."
    ],
    ["all"], "0.8x-1.1x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8JAKE",
    "Problem–Solution Hook",
    "problem_solution_hook",
    "voice_techniques",
    "Caption opens by naming a relatable problem (hunger at midnight, craving something specific, not knowing what to cook), then positions the brand as the effortless solution. The product is the answer, not the pitch.",
    ["f_and_b", "retail"], 1,
    "Structure: [Relatable problem statement] → ['عندنا الحل'] → [Product as solution with minimal friction CTA]. Problem must be specific and felt: 'الجوع الليلي' / 'ما تدري تطبخ إيش' / 'رهبة المطعم'. Solution must feel immediate and easy to access.",
    "Problem-solution is the most efficient persuasion frame — it meets the audience where they already are (experiencing the problem) rather than trying to create desire from scratch. In F&B, hunger problems are universal and immediate. The pattern works best when the problem is specifically Saudi-contextualized (not generic).",
    [
        "Problem must be genuinely relatable — not a made-up problem the brand invented to justify the solution.",
        "Solution must feel effortless — complex or expensive solutions undercut the hook.",
        "Avoid overused problems — 'don't know what to eat?' is saturated; more specific problems have higher resonance."
    ],
    ["all"], "0.8x-1.1x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A1B2C3D4E5F6G7H8JAKF",
    "Character Spokesperson",
    "character_spokesperson",
    "voice_techniques",
    "A recurring character — illustrated mascot, brand persona, or animated figure — speaks on behalf of the brand in a consistent voice. The character becomes the embodiment of the brand personality over time.",
    ["f_and_b", "retail"], 1,
    "Character appears in post frame (illustrated overlay, sticker, mascot photo) with speech bubble or caption in their voice. Character has consistent personality traits: curious, witty, warm, bold. Used for product announcements, audience engagement, light-hearted brand moments. Character must have a name and consistent visual identity.",
    "Brand mascots and characters dramatically increase recall and affection metrics. In Saudi content, characters that are authentically Saudi-designed (Arabic calligraphy stylization, traditional clothing references, Saudi cultural cues) perform significantly better than generic Western-style mascots. Characters also allow brands to communicate in more playful or bold tones than the brand itself might risk.",
    [
        "Character design must be culturally appropriate — avoid human-like characters that could violate representation guidelines.",
        "Character voice must be consistent — inconsistent character personalities undermine the archetype.",
        "Character must feel like a natural extension of the brand, not a bolt-on marketing device.",
        "Inanimate or abstract characters (a coffee cup, a teapot) are safer than humanoid characters for compliance."
    ],
    ["all"], "0.7x-1.0x",
    ["Character design must comply with Saudi visual representation guidelines."],
    "sector:f_and_b+sector:retail"
))

# ─── CONTENT TYPES ───────────────────────────────────────────────────

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K0",
    "Trend Riding",
    "trend_riding",
    "content_types",
    "Content inserts the brand into an externally trending moment — a viral audio, a meme format, a cultural conversation or debate — while keeping the brand voice intact. The trend is the vehicle, not the destination.",
    ["f_and_b", "retail"], 5,
    "Structure: [Trending format/audio/meme adapted to brand context] → [Brand punchline or product tie-in]. Execution speed is critical — trend content posted 48+ hours late performs significantly below trend content posted within the first 24 hours. Keep the brand visible but not forced.",
    "Trend riding demonstrates cultural awareness and contemporary relevance without requiring large production budgets. When executed quickly and authentically, it generates massive reach because the audience is already primed to engage with the trend format. For Saudi brands, trend riding must filter international trends through Saudi cultural context — not all global trends transplant.",
    [
        "Speed is everything — if you can't produce in 24 hours, don't chase the trend.",
        "Brand must add something to the trend — lazy trend-riding with no brand angle feels opportunistic.",
        "Filter all trends through Saudi cultural compliance before executing — some global trends are inappropriate in Saudi context.",
        "Don't chase trends that conflict with brand positioning — a luxury brand doing a meme format can feel undignified."
    ],
    ["all"], "0.6x-1.5x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K1",
    "Curiosity Gap Question",
    "curiosity_gap_question",
    "content_types",
    "Caption opens with a question that creates an information gap — the audience needs to read further (or click) to close the gap. The question is specific enough to be intriguing but not answerable without engaging with the content.",
    ["f_and_b", "retail"], 2,
    "Opening question types: [Factual gap] 'هل تعرف ليش...?' — [Personal gap] 'إيش يختلف عندنا؟' — [Challenge gap] 'تقدر تفرق بين...?'. Never open with a yes/no question. The gap must close by end of caption. CTA: 'احفظ المنشور' (save post) or 'شاركنا رأيك'.",
    "The curiosity gap is one of the most reliable engagement triggers in content. Human brains are wired to close information gaps — an unanswered question creates mild anxiety that pushes continued reading. For F&B brands, curiosity questions about ingredients, processes, or origins work especially well because they add knowledge value alongside product promotion.",
    [
        "The gap must be genuinely interesting — trivial curiosity questions ('do you like coffee?') generate no tension.",
        "The answer must be satisfying — a disappointing payoff damages brand credibility.",
        "Don't use curiosity gaps for commercial announcements — the mismatch between intriguing question and sales pitch feels manipulative.",
        "Limit to once per 2 weeks — frequent curiosity gap openers become predictable and lose effect."
    ],
    ["all"], "0.8x-1.2x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K2",
    "Mystery Teaser Format",
    "mystery_teaser_format",
    "content_types",
    "Content deliberately obscures the full reveal — a blurred product, a partial image, a cryptic caption with minimal information — to generate speculation and return visits. The reveal comes in a follow-up post.",
    ["f_and_b", "retail", "beauty"], 1,
    "Post 1 (teaser): blurred/cropped/shadowed visual + minimal cryptic caption ('قريباً' / 'شيء مختلف يجي' / question mark). Post 2 (reveal): full product reveal with explanation. The gap between posts should be 24-72 hours. Comment section will self-fill with guesses — monitor and engage.",
    "Two-post sequences double the touchpoints with the audience. The teaser generates comments (speculation) that boost reach before the reveal posts. When the reveal lands, the audience feels rewarded for their attention. This format is especially effective for new product launches, seasonal specials, and brand collaborations.",
    [
        "The reveal must justify the anticipation — a disappointing reveal damages the next teaser's credibility.",
        "The mystery must be genuine — if the audience can easily guess, the teaser loses tension.",
        "Must follow up with the reveal — abandoned teasers damage trust.",
        "Works best for tangible product reveals, not abstract announcements."
    ],
    ["all"], "0.8x-1.3x",
    [],
    "sector:f_and_b+sector:retail+sector:beauty"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K3",
    "Brand Hashtag Series",
    "brand_hashtag_series",
    "content_types",
    "A recurring content series unified by a branded hashtag — each post adds to a themed collection that audiences can follow and participate in. The series creates appointment viewing and searchable content archives.",
    ["f_and_b", "retail"], 1,
    "Series elements: [Consistent branded hashtag] + [Recurring visual template or format] + [Invitation to audience participation or contribution]. Examples: #MomentBarnsCoffee (customer moments), #أطباق_هنا (dish of the week), #يوم_في_المطبخ (kitchen day). Post frequency: minimum weekly. Build a searchable content archive over time.",
    "Branded hashtags create searchable content collections that extend brand reach beyond the original post. When audiences contribute to a hashtag series (UGC), the brand benefits from organic reach multiplication. Series format also disciplines the content calendar — a series fills planning gaps and creates consistent audience expectations.",
    [
        "Series must have a clear theme that audiences understand immediately — ambiguous series concepts generate no participation.",
        "Commit to the cadence — an abandoned series damages credibility more than never starting one.",
        "Hashtag must be unique enough to not be polluted by unrelated content.",
        "Participation CTAs must be simple — complex participation requirements kill UGC generation."
    ],
    ["all"], "0.7x-1.1x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K4",
    "Interactive Question Post",
    "interactive_question_post",
    "content_types",
    "A post whose primary purpose is to generate audience responses — questions, polls embedded in caption, or direct comment solicitation. The brand recedes; the audience becomes the content.",
    ["f_and_b", "retail"], 1,
    "Types: [Direct question] 'ما رأيك في...?' — [Choice prompt] 'أ أو ب؟' — [Fill in blank] 'أفضل شيء في الشتاء هو...' — [Tag mechanic] 'وين تاخذ أصحابك؟'. Keep the question simple and answerable in 1-2 words. Image supports but doesn't dominate — the question is the product. Comment section becomes the value.",
    "Interactive posts generate comment volume that signals engagement quality to platform algorithms, boosting reach. More importantly, they create a two-way relationship — the audience feels heard and valued. Over time, this builds community rather than an audience. The comments themselves often generate valuable market research insights.",
    [
        "Questions must be genuinely interesting — 'do you like our food?' gets ignored.",
        "Must respond to comments — interactive posts that get no brand responses feel like a trap.",
        "Question must connect to the brand context — random questions feel unanchored.",
        "Don't over-use — more than weekly interactive posts can feel like engagement farming."
    ],
    ["all"], "0.7x-1.2x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K5",
    "Influencer Takeover Post",
    "influencer_takeover_post",
    "content_types",
    "A known Saudi influencer or personality is given the brand account (or co-creates content) for a post or series — their authentic voice and audience relationship are borrowed to build brand credibility and reach.",
    ["f_and_b", "retail", "beauty"], 1,
    "Content is co-branded: influencer's visual style + brand product in natural context. Caption in influencer's authentic voice (not brand voice). CTA: link to influencer's account. Must feel like the influencer chose the brand, not the other way around. Avoid script-reading, staged product holds, or promotional language that signals paid partnership.",
    "Influencer collaborations that feel authentic outperform both brand-only posts (more credible) and overt paid ads (more engagement). In Saudi Arabia, the right influencer carries deep community trust — their endorsement is a social proof signal that money alone cannot replicate. Best performance when the influencer has genuine category affinity (food influencer × food brand).",
    [
        "Influencer must have genuine Saudi audience relevance — large follower counts without Saudi cultural resonance add little signal.",
        "Paid partnership must be disclosed — undisclosed partnerships damage both brand and influencer credibility.",
        "Influencer content must be reviewed for compliance before posting.",
        "Category alignment is mandatory — mismatched influencers undermine the authenticity premise."
    ],
    ["all"], "0.9x-1.5x",
    [],
    "sector:f_and_b+sector:retail+sector:beauty"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K6",
    "Carousel Swipe Mechanic",
    "carousel_swipe_mechanic",
    "content_types",
    "A carousel post designed to maximize swipe-through rate — each slide is incomplete without the next, creating a visual or narrative chain that pulls the audience through all slides.",
    ["f_and_b", "retail", "beauty"], 1,
    "Design principles: [First slide hooks immediately — partial image, incomplete information, question] → [Middle slides deliver value — steps, comparisons, reveals] → [Final slide lands the punchline or CTA]. Arrow cues or 'اسحب' text guides the swipe. Content types that work: before/after, step-by-step recipe, multiple product reveal, quiz with answer on final slide.",
    "Instagram/TikTok algorithms reward carousel posts that complete all slides — the signal that audiences swiped through is a strong quality indicator. Well-designed carousel mechanics can 2-3x the time spent on content vs. single images, significantly boosting algorithmic distribution. The swipe mechanic also allows more complex storytelling than a single post.",
    [
        "First slide must be strong enough to earn the swipe — weak openers lose most audiences immediately.",
        "Each slide must justify its existence — padding a carousel with weak slides damages completion rate.",
        "Keep it under 8 slides — optimal completion rates drop significantly above 8.",
        "Visual consistency across slides is critical — disjointed design kills the swipe momentum."
    ],
    ["all"], "0.8x-1.2x",
    [],
    "sector:f_and_b+sector:retail+sector:beauty"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K7",
    "Loyalty Activation",
    "loyalty_activation",
    "content_types",
    "Content specifically designed to drive sign-ups, re-engagement, or milestone redemption within a brand loyalty program. The loyalty benefit is the content, not just a mention.",
    ["f_and_b", "retail"], 1,
    "Structure: [Loyalty benefit highlighted — specific reward, not generic promise] → [Simple action to unlock it] → [Urgency element if applicable]. Must name the specific benefit: 'اكسب 500 نقطة' beats 'انضم لبرنامجنا'. Visual: rewards interface or product reward image. CTA: app store link or QR code.",
    "Loyalty programs in Saudi F&B are among the highest-engagement mechanics when benefits are tangible and immediately actionable. Saudi audiences have high smartphone penetration and strong app adoption — digital loyalty mechanics translate well. The key is specificity: named rewards with clear paths outperform vague loyalty promises 3-to-1.",
    [
        "Benefit must be specific and achievable — vague points systems without clear redemption paths generate no action.",
        "App installation friction is a drop-off point — social post → app install → loyalty signup is a 3-step funnel that needs each step simplified.",
        "Loyalty content must be separate from product content — mixing the two dilutes both messages.",
        "Track-and-report loyalty content performance separately from regular content."
    ],
    ["all"], "0.6x-1.0x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K8",
    "Loyalty App Engagement",
    "loyalty_app_engagement",
    "content_types",
    "Content promotes a specific in-app feature, limited-time app offer, or app-exclusive deal to drive app opens and in-app engagement among existing loyalty members.",
    ["f_and_b", "retail"], 1,
    "Target: existing loyalty members, not new sign-ups. Content shows the in-app feature or deal prominently — screenshot or screen-record style visual. CTA: 'افتح التطبيق الآن' / 'متاح فقط على التطبيق'. Must create genuine in-app exclusivity — deals that are also available in-store undermine the app value proposition.",
    "App engagement retention is cheaper than app re-acquisition. Content that drives existing members back to the app maintains loyalty program health. Saudi F&B chains with strong apps (Starbucks SA, Herfy) show that app-exclusive offers generate significantly higher conversion rates than general social promotions.",
    [
        "App must actually have the exclusive benefit advertised — false exclusivity destroys trust.",
        "Content should not alienate non-app users — avoid making them feel excluded from the brand overall.",
        "App UX must be functional on day of promotion — broken app experiences following a promotion post are high-damage events.",
        "Track app opens as conversion metric for this content type, not likes."
    ],
    ["all"], "0.6x-1.0x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9J0K9",
    "Weekly Giveaway Mechanic",
    "weekly_giveaway_mechanic",
    "content_types",
    "A recurring weekly giveaway with consistent format, prize category, and entry mechanic — designed to create appointment engagement and follower habit rather than one-off giveaway spikes.",
    ["f_and_b", "retail"], 1,
    "Format consistency: same day each week, same entry mechanic (follow + comment + tag), same visual template. Prize should be brand product (not unrelated prizes that attract non-customers). Cadence: announce Monday, close Thursday, announce winner Friday. Winner announcement post generates second engagement wave.",
    "Weekly recurring giveaways build a habit loop — audiences return weekly because they expect the format. This is more valuable than a single large giveaway that attracts one-time participants. In Saudi F&B, product giveaways attract genuine customers (free product = trial opportunity) vs. cash giveaways that attract prize hunters.",
    [
        "Giveaway mechanics must comply with Saudi regulations on sweepstakes and competitions.",
        "Prize must be valuable enough to motivate participation — too small = no participation; too large = prize hunters, not customers.",
        "Winner announcement must be timely — delayed announcements damage credibility.",
        "Monitor for fake account entry — genuine customer participation is the goal."
    ],
    ["all"], "0.6x-1.1x",
    ["Must comply with Saudi Competition and Lottery regulations."],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKA",
    "Comment to Win",
    "comment_to_win",
    "content_types",
    "A giveaway mechanic where the primary entry action is commenting — commenting a specific word, answering a question, or tagging another account. Comment volume is the direct engagement metric.",
    ["f_and_b", "retail"], 1,
    "Entry types: [Answer question in comments] — [Comment specific word/emoji] — [Tag a friend]. Simple one-action entry outperforms multi-step entry 2:1. Caption must clearly state: prize, entry action, deadline, and selection method. Visual: prize product prominently displayed.",
    "Comment-to-win mechanics generate comment volume that signals high engagement to platform algorithms, dramatically boosting organic reach of the post. The tagging variant also expands reach to the tagged accounts' followers. Best for building brand awareness and growing follower count in Saudi market.",
    [
        "Entry mechanic must be genuinely simple — complex multi-step entries drop participation 60-70%.",
        "Prize must be the actual product or brand experience — unrelated prizes attract disloyal audiences.",
        "Must be able to execute winner selection visibly and fairly — audiences watch for favoritism.",
        "Comment management is critical — high comment volume requires active moderation."
    ],
    ["all"], "0.7x-1.2x",
    ["Giveaway mechanics must comply with Saudi commercial regulations."],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKB",
    "Food Preference Poll",
    "food_preference_poll",
    "content_types",
    "A post that polls the audience on a food preference — flavor A vs. flavor B, hot vs. cold, sweet vs. savory — using Instagram Stories poll sticker or comment-based voting in feed posts.",
    ["f_and_b"], 1,
    "Story poll format: two clear options with simple visual split. Feed poll format: comment A or comment B, with visual showing both options. Keep options genuinely contested — obvious answers generate no debate. Follow up: share results in Stories. Works best for: new product decisions, seasonal specials, regional variants.",
    "Food preference polls are among the highest-performing engagement formats in F&B social content because they are immediately participatory (1 tap) and the topic is inherently personal. They also generate genuine market research data — which flavor the audience prefers is valuable product intelligence beyond social performance.",
    [
        "Options must be genuinely contestable — if 95% will choose one answer, it's not a poll, it's a quiz.",
        "Follow up with results — abandoned polls damage trust.",
        "Use poll data for actual product decisions when possible — tell the audience their preference influenced a product choice.",
        "Don't use polls as a substitute for content — combine with product beauty shot."
    ],
    ["all"], "0.8x-1.2x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKC",
    "Prediction Engagement",
    "prediction_engagement",
    "content_types",
    "A post that asks the audience to predict an outcome — a match result, a product popularity ranking, a sales milestone — and then reveals the actual result. The gap between prediction and reveal drives return engagement.",
    ["f_and_b", "retail"], 1,
    "Two-post sequence: [Prediction post — ask audience to guess] → [Result post — reveal and celebrate closest prediction]. Works for: sports occasion predictions, giveaway draw results, 'which product will sell out first?' Tone: playful, participatory, celebratory on reveal. Comments become the competitive arena.",
    "Prediction mechanics create a commitment from the audience to return and check the result. This drives repeat profile visits — a valuable signal. The competitive element (who predicted correctly) generates comment debate. When combined with sports occasions (Saudi League, Arab Cup), prediction engagement can produce the highest comment volumes of any content type.",
    [
        "Must deliver the result — abandoned predictions damage credibility significantly.",
        "The predictable outcome should not be obvious — genuine uncertainty is the prerequisite for engagement.",
        "Sports-linked predictions must be timely — post before the event, reveal immediately after.",
        "Keep the stakes light — heavy stakes predictions feel out of brand character."
    ],
    ["all"], "0.7x-1.3x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKD",
    "App Loyalty Mechanic",
    "app_loyalty_mechanic",
    "content_types",
    "Content promotes a specific gamified mechanic within a loyalty app — challenges, streaks, bonus point events, or unlockable rewards — designed to drive daily active use of the app.",
    ["f_and_b", "retail"], 1,
    "Show the mechanic visually (screenshot/animation). Frame as a challenge or achievement: 'أكمل 5 زيارات هذا الشهر واكسب...' / 'فعّل تحديك'. Tone: energetic, achievement-oriented. Works best with visual progress bar or reward imagery. CTA: app open link.",
    "Gamification in loyalty apps dramatically increases daily active user rates and visit frequency. Saudi audiences — particularly younger demographics — respond to streak and achievement mechanics borrowed from gaming culture. Promoting these mechanics on social content reinforces the habit loop and reactivates dormant app users.",
    [
        "App mechanic must actually exist and be functional before promotion.",
        "Achievement framing must not feel manipulative — genuine reward for genuine engagement only.",
        "Must track app open rate as the conversion metric, not social engagement.",
        "Requires coordination between social and app product teams."
    ],
    ["all"], "0.6x-1.0x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKE",
    "Product Packaging Hero",
    "product_packaging_hero",
    "content_types",
    "The product packaging — box, bag, wrapper, cup, bottle — is the primary visual hero, treated with the same lighting, styling, and composition care as the product itself. The packaging becomes the object of desire.",
    ["f_and_b", "retail", "beauty"], 1,
    "Visual: packaging center-framed, close-up or medium distance, well-lit, premium styling. No hands holding unless intentional. Clean background or minimal environment. Caption: 0-2 lines — packaging speaks for itself. Works for: new packaging launches, seasonal packaging, premium gift sets.",
    "When packaging design is strong, featuring it as the hero communicates premium quality and design investment. Saudi audiences respond positively to beautiful packaging — it signals gift-worthiness and premium positioning. Packaging hero posts also serve as organic packaging reveals and PR moments for new design launches.",
    [
        "Only works when packaging design is genuinely premium — average packaging heroized looks like a commercial.",
        "New packaging launches deserve a dedicated reveal post sequence.",
        "Do not over-use — packaging hero posts work as 1 in 10-15 posts, not more.",
        "For Ramadan/Eid, special packaging is expected and should be featured."
    ],
    ["all"], "0.7x-1.0x",
    [],
    "sector:f_and_b+sector:retail+sector:beauty"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKF",
    "Meal Box Format",
    "meal_box_format",
    "content_types",
    "Content showcases a curated meal set, bundle, or box — multiple items presented together as a complete experience rather than individual items. The curation is the value proposition.",
    ["f_and_b"], 1,
    "Visual: overhead shot showing all items in the bundle together, arranged neatly. Caption: names all items + total bundle price vs. individual prices. Emphasizes the value calculation (saves X SAR) or the curation value (we chose these items together because...). Occasion tie-in optional but powerful: Ramadan suhoor box, family weekend box.",
    "Bundle content performs well because it simplifies the purchase decision (everything is chosen for you) while signaling value (bundle savings). In Saudi F&B, meal boxes also align with the cultural norm of sharing food — a box for a family gathering or friend group is a natural fit. Bundle formats also increase average order value.",
    [
        "Bundle must represent genuine value — if items are cheaper separately, the bundle damages trust.",
        "Curation must feel intentional — random bundles of unrelated items feel like upselling, not value.",
        "Occasion-specific bundles outperform generic bundles — Ramadan boxes, Eid boxes, Friday family boxes.",
        "Visual must show all items clearly — beauty and completeness are both required."
    ],
    ["all"], "0.6x-1.0x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKG",
    "Free Add-On Offer",
    "free_add_on_offer",
    "content_types",
    "Content promotes a free addition to a regular purchase — a free item with every order, a free upgrade, or a free gift with purchase — framed as a gift rather than a discount.",
    ["f_and_b", "retail"], 1,
    "Frame: 'هدية من عندنا' not 'خصم'. Show both the purchase and the free item. Caption clearly states: what, when, and how to get it. Urgency element optional: 'لفترة محدودة'. Tone: generous, warm, gift-giving. Avoid percentage framing — 'free item' outperforms '20% off' psychologically.",
    "Free gifts outperform equivalent discounts in conversion rate across virtually all consumer categories. The psychological mechanism is reciprocity — a gift creates a sense of obligation and warmth toward the brand. In Saudi culture, generosity (الكرم) is a deeply valued trait — framing a promotion as a gift aligns with this cultural value.",
    [
        "Gift must have perceived value — a trivial free item generates no positive response.",
        "Terms must be clear — hidden conditions on free items damage trust severely.",
        "Gift framing requires genuine generosity signal — stingy gifts backfire more than no gift.",
        "Seasonal gift framing (Ramadan: 'هدية إفطارنا') amplifies the cultural resonance."
    ],
    ["all"], "0.7x-1.1x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKH",
    "Limited Time Price Offer",
    "limited_time_price_offer",
    "content_types",
    "Content announces a specific price reduction or promotional pricing for a defined time window. The price point and deadline are the primary information.",
    ["f_and_b", "retail"], 1,
    "Visual: product image + price prominently displayed (large, readable). Caption: [Product name] + [Offer price] + [Original price struck through if applicable] + [Time window] + [CTA]. Clean, direct, no narrative padding. Tone: clear, urgent, simple. Does not need to be beautiful — clarity is the design goal.",
    "Price offer content performs lower on engagement metrics (likes/comments) than heritage or storytelling content, but higher on conversion (direct sales, footfall). It serves a different function — it activates the price-sensitive audience segment. Best used as 20-30% of content mix alongside richer brand content.",
    [
        "Price must be genuinely reduced — fake 'original prices' that are never charged at full rate are a compliance and trust risk.",
        "Time window must be real — expired offers that are not removed damage credibility.",
        "Avoid over-reliance on price offers — they train audiences to wait for discounts and erode perceived brand value.",
        "Saudi consumer protection law applies to advertised prices — accuracy is mandatory."
    ],
    ["all"], "0.4x-0.7x",
    ["Advertised prices must comply with Saudi Consumer Protection regulations."],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A2B3C4D5E6F7G8H9JAKI",
    "Delivery Value Proposition",
    "delivery_value_proposition",
    "content_types",
    "Content specifically promotes the brand's delivery offer — speed, packaging quality, app ordering convenience, delivery radius, or free delivery threshold — as the primary message rather than the product itself.",
    ["f_and_b"], 1,
    "Structure: [Delivery hero moment — product arriving, being unboxed, delivered to a scene] + [Specific delivery value claim] + [Ordering CTA with platform logos]. Claims: 'خلال 30 دقيقة' / 'توصيل مجاني فوق 50 ريال' / 'تتبع طلبك مباشرة'. Pair with unboxing visual showing packaging quality.",
    "Delivery occasions represent a distinct consumption context from dine-in. Content that specifically addresses the delivery moment — with its own social cues (eating at home, ordering for family, late-night delivery) — converts delivery-intent audiences more effectively than generic product content. Saudi delivery market is large and growing rapidly.",
    [
        "Delivery claims must be accurate — false delivery time claims are heavily penalized in Saudi market.",
        "Delivery platform partnerships must be disclosed where required.",
        "Packaging quality shown in content must match actual delivery packaging — expectation mismatch generates negative reviews.",
        "Delivery CTAs must be functional and up-to-date."
    ],
    ["all"], "0.6x-0.9x",
    [],
    "sector:f_and_b"
))

# ─── OCCASION PLAYS ──────────────────────────────────────────────────

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K0",
    "Football Occasion Tie-In",
    "football_occasion_tie_in",
    "occasion_plays",
    "Content inserts the brand into a Saudi football cultural moment — Saudi Pro League matches, national team games, Roshn Saudi League fixtures, or major Arab football events. The brand becomes part of the viewing/gathering occasion.",
    ["f_and_b", "retail"], 2,
    "Post types: [Pre-match] 'ليلة المباراة معانا' + match viewing food/drink offer — [During match] real-time product CTA — [Post-match] result-acknowledgment with brand. Tone: passionate but not partisan (avoid supporting specific team unless brand has official partnership). Delivery + ordering CTAs perform well in this context.",
    "Football occasions in Saudi Arabia generate extremely high-intensity social engagement — audiences are fully active on their phones before, during, and after matches. Brands that show up in this context authentically (not just slapping a ball logo on their product) become part of the cultural ritual. Match-day delivery offers and viewing party food content are high-conversion contexts.",
    [
        "Do not take partisan team positions unless the brand has official team partnership.",
        "Content must be timely — pre-match posts after kick-off are ignored.",
        "Delivery mechanics tied to football occasions have significantly higher conversion than general football content.",
        "Saudi national team games carry more cultural weight than club games — allocate proportionally."
    ],
    ["all"], "0.6x-1.2x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K1",
    "Winter Comfort Cozy",
    "winter_comfort_cozy",
    "occasion_plays",
    "Content frames the brand as the perfect companion for the Saudi winter — cool evenings, family gatherings, slower pace — particularly in the Najd highland regions where winters are genuinely cold. The cozy winter context is the occasion.",
    ["f_and_b"], 1,
    "Visual: warm indoor setting, soft lighting, product associated with warmth (soup, hot drinks, comfort food). Caption: winter sensory language — 'برد الشتاء' / 'دفا المنزل' / 'ليلة هادية'. Tone: warm, slow, inviting. Works from November to February in Saudi context. Elevated response in Riyadh/Najd region.",
    "Saudi winters — particularly in Riyadh and highland areas — are genuinely cold (5-15°C evenings) and represent a distinct cultural moment where consumption patterns shift toward warmth and gathering. Brands that activate this seasonal shift with appropriate warm-comfort content align with real behavioral changes. The winter cozy frame is underutilized relative to the summer heat frame.",
    [
        "Winter in coastal regions (Jeddah, Eastern Province) is mild — cozy framing is less resonant there.",
        "Content should feature warm foods/drinks with genuine seasonal relevance — don't stretch products into the frame artificially.",
        "Winter content performs best in December-January when temperature shift is most pronounced.",
        "Pair with evening/nighttime visual timing — Saudi winters feel most distinct in the evening."
    ],
    ["all"], "0.7x-1.1x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K2",
    "Lunch Daypart Prompt",
    "lunch_daypart_prompt",
    "occasion_plays",
    "Content specifically targets the pre-lunch or lunchtime window — typically 11AM-1PM Saudi time — with messaging that acknowledges the midday meal occasion and provides a timely ordering or visit CTA.",
    ["f_and_b"], 1,
    "Post timing: 10:30-11:30AM Saudi time. Caption: 'وقت الغدا وين؟' / 'غداك جاهز؟' / 'يلا الغدا'. Urgency: 'تحكم قبل ما تخلص'. Tone: casual, practical, hunger-activating. Visual: lunch-specific dishes or full meals. Works best as Stories content paired with quick ordering CTA.",
    "Daypart targeting is among the most efficient conversion tactics in F&B social marketing. A post about lunch, posted at lunchtime, reaches people who are actively thinking about their midday meal — the intent-to-purchase moment. Saudi lunchtime is a compressed decision window (12-1PM) — being present in that window with a clear offering is high-value.",
    [
        "Timing is critical — a lunch post at 2PM misses the decision window entirely.",
        "Content must be actionable — 'where are you going for lunch?' prompts decision; 'we have great lunch options' does not.",
        "Delivery ordering CTAs are highest-converting for this daypart.",
        "Don't apply lunch framing to products not appropriate for lunch occasions."
    ],
    ["all"], "0.7x-1.0x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K3",
    "World Food Heritage Day",
    "world_food_heritage_day",
    "occasion_plays",
    "Content connects the brand to an international food-related awareness day — World Coffee Day, World Food Day, World Chocolate Day — filtered through Saudi cultural context and brand relevance.",
    ["f_and_b"], 1,
    "Structure: [Day acknowledgment] + [Brand's authentic connection to the day's theme] + [Saudi cultural angle]. Example: World Coffee Day → Saudi coffee heritage → brand's expression of that heritage. Do not just post 'it's World Coffee Day' — the brand angle must add meaning. Light offer or CTA optional.",
    "International food days provide a built-in narrative context and are heavily searched on social platforms on their dates. For Saudi brands, the opportunity is to take the global occasion and give it a Saudi lens — making it both relevant (international legitimacy) and local (Saudi cultural specificity). This pattern works best for brands with genuine category depth.",
    [
        "Brand must have genuine connection to the day — World Chocolate Day content from a non-chocolate brand reads as trend-chasing.",
        "Saudi cultural angle is the differentiator — without it, the content is indistinguishable from every other brand posting the same day.",
        "Plan 3-4 weeks in advance — these days are calendared and can't be executed last minute.",
        "The day should add value to the brand story, not just provide a content hook."
    ],
    ["all"], "0.6x-1.0x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K4",
    "Delivery Promo Sport",
    "delivery_promo_sport",
    "occasion_plays",
    "A delivery-specific promotion activated during a live sporting event — typically a Saudi Pro League match or national team game — with match-timing urgency and ordering CTA designed to convert the viewing occasion into delivery intent.",
    ["f_and_b"], 1,
    "Timing: post 30-60 min before kick-off. Content: product image + match reference + delivery urgency + 'اطلب قبل المباراة'. Offer: free delivery or bundled deal for match viewing. Visual: match viewing context (couch, TV, snacks). Must name the specific match — generic 'watch party' content underperforms.",
    "Sports occasions create a predictable high-engagement window with delivery intent — people watching at home want food delivered. Brands that activate this occasion with timely, relevant delivery content convert at significantly higher rates than normal delivery posts. The combination of social occasion (match) + consumption occasion (delivery food) + urgency (kick-off) is a high-conversion triangle.",
    [
        "Must be timed precisely to kick-off — too early or too late misses the decision window.",
        "Delivery lead time must be realistic — promising 30-min delivery that takes 60 min damages trust on a time-critical occasion.",
        "Avoid partisan team support — delivery offer should be neutral and welcoming to all fans.",
        "Coordinate with delivery platform on event-specific demand spikes."
    ],
    ["all"], "0.6x-1.1x",
    [],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K5",
    "Saudi Sports Rivalry",
    "saudi_sports_rivalry",
    "occasion_plays",
    "Content activates a specific Saudi football rivalry moment — Al Hilal vs. Al Nassr, Al Ahli vs. Al Ittihad — creating playful brand participation in the cultural debate without taking sides.",
    ["f_and_b", "retail"], 1,
    "Frame: the brand serves all fans equally, or playfully refuses to take sides. 'عندنا لكل الجماهير' / 'ما نفرق: هلالي أو نصراوي، الكل أهلنا.' Visual: product with neutral presentation or split/paired presentation. Engagement mechanic: comment your team → winner gets free product. Tone: playful, inclusive, community-spirited.",
    "Saudi football rivalries are among the most intense cultural moments in the kingdom's social calendar. Brands that navigate these moments with playful neutrality become cultural participants without the partisan risk. The comment engagement generated by team-debate mechanics can be extraordinarily high — top rivalry posts generate 10x normal comment volumes.",
    [
        "Never take a partisan position unless the brand has an official team sponsorship.",
        "The humor and playfulness must be genuine — corporate attempts at sports banter are cringeworthy.",
        "Rivalry content timing must be exact — pre-match window is 2-6 hours before kick-off.",
        "Saudi football rivalries carry genuine emotional intensity — missteps are punished publicly and loudly."
    ],
    ["all"], "0.6x-1.4x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K6",
    "Global Event Saudi Lens",
    "global_event_saudi_lens",
    "occasion_plays",
    "Content uses a major global event (World Cup, Olympics, Formula 1 Saudi GP, Expo) as the occasion hook but filters it through Saudi cultural perspective and brand relevance — making a global moment feel local and personal.",
    ["f_and_b", "retail"], 1,
    "Structure: [Global event acknowledgment] → [Saudi community's experience of it / how Saudis are participating] → [Brand's place within that experience]. Example: F1 Saudi GP → Jeddah as global racing capital → brand as the Jeddah brand that locals are proud of. Tone: proud, culturally grounded, celebratory.",
    "Saudi Arabia is hosting an increasing number of global events (Formula 1, World Cup 2034, Expo, concerts) — each creates a compressed cultural moment where national pride and global identity merge. Brands that participate in this pride wave authentically earn the loyalty of audiences who see the brand as 'one of us' celebrating Saudi Arabia's global moment.",
    [
        "The Saudi lens must be genuine — a global event post without the Saudi angle is just trend chasing.",
        "Brand connection must be logical — reaching for a connection that doesn't exist reads as desperate.",
        "For major events, plan 2-4 weeks in advance — real-time content without preparation often misses the mark.",
        "Be aware that major global events may also carry geo-political sensitivities — navigate carefully."
    ],
    ["all"], "0.7x-1.2x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K7",
    "Family Gathering Angle",
    "family_gathering_angle",
    "occasion_plays",
    "Content frames the product as central to a family gathering moment — weekend lunch, after-Jumu'ah meal, Eid family visit, or multigenerational dinner table. The family occasion is the context; the product is the natural presence within it.",
    ["f_and_b"], 1,
    "Visual: table set for multiple people, family-scale portions, warm domestic setting. Caption: family gathering language — 'سفرة العيلة' / 'جمعة جلستنا' / 'زيارة الأهل'. Sizes and portions should reflect family scale. Tone: warm, welcoming, generous. Avoid individual-serving framing in this context.",
    "Family gathering is one of the highest-frequency consumption occasions in Saudi Arabia. Friday family lunches, Eid visits, and celebration meals are deeply embedded cultural practices. Brands that position themselves as the natural choice for these occasions earn usage occasions that competitors find hard to displace — family tradition is stickier than individual preference.",
    [
        "Family imagery must be gender-appropriate — mixed-gender family scenes with appropriate distance/context.",
        "Portion and product scale must match the family occasion — individual-size items in a family gathering context feel mismatched.",
        "The warmth of the family moment should not be overshadowed by product promotion.",
        "Do not conflate family gathering with official occasions (weddings, funerals) — keep the register social and warm."
    ],
    ["all"], "0.7x-1.1x",
    ["Family imagery must respect Saudi cultural norms for gender representation."],
    "sector:f_and_b"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K8",
    "Family Occasion Appeal",
    "family_occasion_appeal",
    "occasion_plays",
    "Content targets a specific named family occasion — Eid gathering, graduation family dinner, National Day family celebration, or first-day-of-school family breakfast — and positions the brand as the occasion's food/drink choice.",
    ["f_and_b", "retail"], 1,
    "Structure: [Named occasion] + [Family moment description] + [Brand as the natural choice for this moment]. Example: Graduation season → the family dinner to celebrate → 'كيف تحتفلون بالخريجين؟' with restaurant recommendation or catering offer. Include occasion-specific CTA: reservation, catering inquiry, group order.",
    "Named occasions create a natural content peg that resonates with audiences living that occasion. Parents of graduates, families celebrating Eid, households preparing for National Day — these are audience segments with specific immediate needs. Brands that address those needs with specific offers and messaging convert at much higher rates than generic family content.",
    [
        "Must name the specific occasion — 'family occasion' without specificity is too vague.",
        "The offer or CTA must match the occasion's practical needs — graduation needs group bookings; Eid needs special menus.",
        "Timing must match the occasion window — graduation content in February is irrelevant.",
        "Don't over-commercialize sacred occasions — Eid content with heavy discount messaging feels inappropriate."
    ],
    ["all"], "0.7x-1.1x",
    [],
    "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSD0A3B4C5D6E7F8G9H0J1K9",
    "Social Dining",
    "social_dining",
    "occasion_plays",
    "Content frames dining as a specifically social act — going out with friends, the group dinner, the late-night gathering — distinct from family dining or individual consumption. The social occasion is the appeal.",
    ["f_and_b"], 1,
    "Visual: group of friends (same gender, casual setting), restaurant or café ambiance, multiple dishes shared. Caption: social dining language — 'خرجة الأصحاب' / 'يلا نشوف وين نروح' / 'أفضل جلسة تجمع'. Tone: casual, energetic, inviting. Tag-a-friend CTA natural in this context.",
    "Social dining is a primary use case for Saudi F&B — the group outing (خرجة) is a deeply embedded social practice, particularly among younger demographics. Content that speaks to this occasion captures the planning stage (where are we going?) as well as the FOMO stage (they went there, I want to go). Tag-a-friend CTAs in this context generate genuine peer-to-peer recommendation.",
    [
        "Group composition must be gender-appropriate — same-gender social groups are safest for this context.",
        "Setting must be appropriate for the social occasion — family restaurants vs. younger-skewing cafés have different audiences.",
        "Tag-a-friend CTAs generate the highest peer-recommendation value from this pattern.",
        "Avoid alcohol-adjacent or inappropriate social contexts."
    ],
    ["all"], "0.7x-1.1x",
    ["Social group imagery must comply with gender representation norms."],
    "sector:f_and_b"
))

# ─── VISUAL COMPOSITIONS (1 remaining) ─────────────────────────────

written.append(pat(
    "01KSD0A4B5C6D7E8F9G0H1J2K0",
    "Golden Color Food Aesthetic",
    "golden_color_food_aesthetic",
    "visual_compositions",
    "The visual is dominated by golden, amber, and warm yellow tones — honey drizzle, golden-fried texture, caramelized edges, warm cheese pull — creating an immediate appetite-triggering warmth through color alone.",
    ["f_and_b"], 1,
    "Achieve through: natural golden-hour lighting on warm-toned food, selective styling of golden-hued ingredients (honey, saffron, dates, cream, crispy fried textures), warm white balance in post-processing. The golden tone should feel natural, not filtered. Works exceptionally with F&B products that have inherent golden/warm tones.",
    "The color gold carries multiple simultaneous associations in Saudi context: premium quality (gold the metal), warmth and hospitality, and food appeal (golden-brown = perfectly cooked). Visual stimulation from warm golden tones triggers appetite and premium perception simultaneously. This color palette consistently performs in the top tier of F&B engagement data.",
    [
        "Golden tone must be achieved through food/lighting, not heavy filter application — over-filtering looks artificial.",
        "Works best for foods with inherent warm tones — doesn't transplant to cold/blue-toned foods.",
        "Avoid pushing golden tones so far that the food looks overcooked — realism is the boundary.",
        "Works exceptionally for Ramadan/Eid content where golden tones align with the seasonal visual language."
    ],
    ["all"], "0.8x-1.2x",
    [],
    "sector:f_and_b"
))

# ─── Print summary ──────────────────────────────────────────────────

print(f"Written {len(written)} missing pattern files:")
for s in written:
    print(f"  {s}")
