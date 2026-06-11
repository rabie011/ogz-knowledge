#!/usr/bin/env python3
"""
write_all_new_patterns.py
Batch-write all 63 new pattern JSON files:
  - 12 missing patterns in existing subcategories (Part 1)
  - 8 lighting_moods patterns (Part 2a)
  - 10 color_palette_patterns (Part 2b)
  - 8 character_representation patterns (Part 2c)
  - 10 setting_environment patterns (Part 2d)
  - 7 hospitality_intensity patterns (Part 2e)
  - 8 caption_structure patterns (Part 2f)
"""
import json, os

PATTERNS_ROOT = os.path.expanduser(
    "~/Desktop/ogz-knowledge/11_who_to_learn_from/patterns"
)
PROVENANCE = {
    "source": "corpus_synthesis_474_obs — corpus_mining_pass May 2026",
    "date_added": "2026-05-24T00:00:00Z",
    "confirmer": "corpus_mining_pass",
    "confidence": "experimental",
    "scope": "sector:f_and_b+sector:beauty+sector:retail"
}

def pat(ulid, name, slug, subcat, description, sectors, account_count,
        recipe, why, caveats, chains, avg_eng, constraints=None, scope=None):
    p = {
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
        "provenance": {**PROVENANCE, "scope": scope or PROVENANCE["scope"]}
    }
    path = os.path.join(PATTERNS_ROOT, subcat, f"{slug}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)
    return slug

written = []

# ══════════════════════════════════════════════════════════
# PART 1 — 12 MISSING PATTERNS (existing subcategories)
# ══════════════════════════════════════════════════════════

written.append(pat(
    "01KSB9Y1W86W4GPBY6YA634EDY",
    "Occasion-Specific Greeting",
    "occasion_specific_greeting",
    "occasion_plays",
    "A direct, warm greeting posted on the first day or key moment of a religious or national occasion. The greeting is the entire post — there is no product or CTA. It signals that the brand pauses to mark the moment before resuming commerce.",
    ["f_and_b", "beauty", "retail"], 14,
    "Visual: occasion-themed graphic (crescent for Ramadan/Eid, Saudi green/gold for National Day). Copy: two to four lines of warm blessing in Arabic, often drawn from familiar Islamic greetings or national pride phrases. No pricing, no product, no discount. Sometimes a short brand tagline appears at the base. Posted within the first 2 hours of the occasion beginning.",
    "Earns cultural goodwill before any commercial ask. Saudi audiences notice brands that stop to mark a moment respectfully vs. brands that use the occasion purely as a promotional hook. A well-executed greeting generates comments and shares disproportionate to its production cost. Average engagement score: 1.00 (highest in corpus).",
    ["Copy must feel genuine — templated or copied blessings are immediately detected and dismissed.",
     "Do not attach a product link or discount code; it collapses the sincerity signal.",
     "Religious greetings require precise wording — wrong Arabic phrasing for Eid vs. Ramadan is jarring.",
     "International brands using colloquial Saudi Arabic for occasion greetings often sound inauthentic."],
    ["all"], "1.4x-1.8x",
    ["Islamic greetings must be spelled and used correctly — consult native Arabic speaker for review."]
))

written.append(pat(
    "01KSB9Y1W8JSSC4QWSDBAZ5WN0",
    "Seasonal Summer Heat Pivot",
    "seasonal_summer_heat",
    "occasion_plays",
    "Content that frames Saudi summer (May–September, 40-50°C) as the primary context — positioning the product as the cultural response to extreme heat. The summer is treated not as a limitation but as a shared Saudi experience worth acknowledging.",
    ["f_and_b", "retail"], 6,
    "Visual: warm outdoor light visible (but product is indoors/cool), or ice, condensation, cold temperatures prominently featured. Copy acknowledges the heat directly and contrasts it with the brand's cool/refreshing/indoors offer. Common phrases: 'الحر ما يوقفنا', 'تحدّ الصيف', cool-vibes Saudi summer colloquialisms. Often combined with welcoming_summer_indoor_pivot.",
    "Saudi summer is hyper-relatable. Any brand that names the shared experience of '45°C Riyadh summer' immediately earns connection. The heat acknowledgment + brand relief formula is simple, local, and high-trust. Average engagement score: 1.00.",
    ["Works only for brands with a genuine summer relevance — forced summer framing for irrelevant products feels desperate.",
     "Outdoor content during peak summer (June–August) requires studio-level heat management for talent.",
     "Avoid only showing suffering — Saudi audiences prefer the triumphant pivot ('despite the heat, we...') over pure complaint."],
    ["all"], "1.4x-1.7x",
    [], "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSB9Y1W8PZZYF3ZX82ZWT18Q",
    "Cultural Identity Marker",
    "cultural_identity_marker",
    "voice_techniques",
    "Copy that explicitly names or invokes a Saudi cultural identity signal — a regional tradition, a collective memory, a historical reference — as the anchor of the post. The marker is stated as shared fact, not explained for outsiders. Assumes the audience is an insider.",
    ["f_and_b", "retail"], 9,
    "Short declarative statement naming the cultural marker followed by the brand connection. Examples: 'القهوة العربية... أكثر من مشروب' | 'من عادات أهلنا في نجد...' | 'تراثنا يجمعنا'. The marker is stated with pride, never explained or translated. Register: semi-formal to warm-colloquial, Najdi-leaning. Product follows the marker, never precedes it.",
    "Identity-first copy creates tribal resonance. When a brand names a cultural fact without apology or explanation, it signals it belongs to that culture. Saudi audiences reward brands that speak as insiders. Average engagement score: 0.83.",
    ["International brands using this pattern without genuine Saudi heritage read as appropriation — avoid.",
     "The identity marker must be accurate and specific. Vague 'Arab tradition' without Saudi anchoring scores poorly.",
     "Must be paired with content that visually validates the claim — text without matching visual is hollow."],
    ["all"], "1.3x-1.7x",
    []
))

written.append(pat(
    "01KSB9Y1W8R1APAYCZ8QE9H7YX",
    "Returning Fan Favourite",
    "returning_fan_favourite",
    "voice_techniques",
    "Copy that frames a returning product, menu item, or seasonal offering as a long-awaited comeback — using nostalgia and fan loyalty as the engagement hook. The product's previous popularity is cited as social proof.",
    ["f_and_b", "retail"], 7,
    "Opening line announces the return with celebratory language ('رجع', 'عاد بكم طلبتم', 'انتظرتوه'). Body copy references the audience's past love for the item, possibly quoting DMs or comments as social proof. CTA creates urgency ('قبل ما ينتهي'). Warm, grateful, celebratory tone — never transactional.",
    "Nostalgia + social proof is a double engagement trigger. The fan-favourite framing tells potential buyers 'others loved this' while also rewarding loyal customers with acknowledgment. Average engagement score: 0.83.",
    ["Requires genuine product history — claiming a 'returning favourite' for a new product destroys credibility.",
     "Comment/DM quotes must be real; fabricated social proof is immediately detected by Saudi audiences.",
     "Works best when paired with a limited-time frame to create genuine scarcity."],
    ["all"], "1.3x-1.6x",
    []
))

written.append(pat(
    "01KSB9Y1W8PZWW44WMWEM64PVM",
    "Poll Engagement Mechanic",
    "poll_engagement_mechanic",
    "content_types",
    "A post built around an audience poll or binary choice — 'A or B?', 'which do you prefer?', 'vote in comments' — where the poll is the content, not a secondary CTA. The brand uses the poll to generate comments, gather preference data, and boost algorithmic reach simultaneously.",
    ["f_and_b", "retail"], 8,
    "Visual: two options presented side by side (product A vs. product B, flavour 1 vs. flavour 2, or abstract choice). Copy poses the question directly and simply. No long explanation. CTA: 'صوتوا' or emoji voting instructions (🍕 = A, 🌯 = B). Comments section becomes the engagement engine. Often used during campaign launches or to gauge audience preferences for new products.",
    "Polls reduce the friction of engagement to its minimum — one emoji comment. Saudi audiences enjoy opinionated interactions around food, taste, and preference. The binary choice format is universally understood and drives high comment volume. Average engagement score: 0.83.",
    ["Poll options must both be genuinely desirable — an unfair comparison produces lopsided results with low engagement.",
     "Must respond to poll results (even with a follow-up story) — silent polls feel extractive.",
     "Works best for products with clear sensory differentiation (hot vs. cold, spicy vs. mild) — abstract concept polls underperform."],
    ["all"], "1.3x-1.6x",
    [], "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSB9Y1W8RC7J4Y98K9H5DGK1",
    "Storytelling Sequence Grid",
    "storytelling_sequence_grid",
    "content_types",
    "A carousel post (or multi-image grid) where each slide advances a single narrative arc — a brand origin story, a product journey from farm to table, a day in the life of a craftsperson. The sequence is designed so that swiping feels like turning the pages of a story.",
    ["f_and_b", "retail", "beauty"], 7,
    "Slide 1: strong visual hook with minimal copy (the inciting moment). Slides 2-N: sequential story beats with images + short captions advancing the narrative. Final slide: resolution + brand connection + CTA. Typography, color palette, and framing must be consistent across all slides. Horizontal reading flow (left-to-right in the frame) or vertical reveal (top frame → bottom frame) creates continuity.",
    "Sequential storytelling rewards the audience for swiping all the way through — each slide is a micro-payoff. Saudi audiences respond strongly to craft origin stories and process revelations. The format signals premium positioning and transparency. Average engagement score: 1.00 (highest in corpus).",
    ["Requires strong creative direction across all slides — inconsistent production quality breaks the immersion.",
     "Story must have genuine narrative stakes — 'our journey' with no conflict or resolution scores poorly.",
     "First slide must be scroll-stopping enough to make someone begin swiping; the story only works if they start."],
    ["all"], "1.4x-1.9x",
    []
))

written.append(pat(
    "01KSB9Y1W8EWC44F75X3M5VD2E",
    "Giveaway / Contest Post",
    "giveaway_contest_post",
    "content_types",
    "A post structured around a prize giveaway or brand contest — the prize is the headline, participation mechanics are the body, and the CTA drives follows, tags, or comments. The giveaway is the content, not a sidebar to other content.",
    ["f_and_b", "retail", "beauty"], 10,
    "Visual: prize displayed prominently (product bundle, gift box, experience voucher). Copy structure: 1) What you can win. 2) How to enter (follow + tag + comment — keep to max 2 steps). 3) Deadline. 4) Winner announcement method. Tone: generous, excited, community-focused. Arabic copy preferred — 'اربح', 'فز', 'هديتنا لكم'. Brand positioning should be woven in: the prize is an expression of brand values.",
    "Giveaways are among the fastest reach-amplification mechanics on Instagram. Tags bring organic new followers; comments signal high engagement to the algorithm. When the prize is genuinely desirable and on-brand, the giveaway also communicates brand generosity — a Saudi cultural virtue. Average engagement score: 1.00.",
    ["Prize must be genuinely valuable — token prizes generate cynicism more than engagement.",
     "Entry mechanics must be simple (max 2 steps) — complex requirements collapse participation.",
     "Must follow Instagram's promotional guidelines — cannot require shares to Feed as entry condition.",
     "Non-Saudi brands running giveaways in Saudi market must ensure prize delivery is locally feasible."],
    ["all"], "1.4x-1.8x",
    []
))

written.append(pat(
    "01KSB9Y1W8YH2CD05FBHY8MK1F",
    "Sports Passion Peg",
    "sports_passion_peg",
    "occasion_plays",
    "Content tied to a major sporting event — Saudi Professional League (Roshn League), King's Cup, Gulf Cup, Champions League, or national sports pride — using the match/tournament as the occasion for a brand activation. The sports event is the peg; the brand is the companion for match-watching.",
    ["f_and_b", "retail"], 8,
    "Visual: stadium atmosphere, team colours, match countdown, or product positioned in a match-watching setting (couch, screen, delivery box). Copy uses football/sports vernacular: 'مباراة الليلة', 'ادعم الأزرق', 'الجمهور الكروي'. Saudi-specific teams and match references. Often includes limited-time offer tied to match timing ('اطلب قبل الكيك أوف').",
    "Football is the single most emotionally resonant cultural moment for Saudi male audiences (and increasingly female). Brands that acknowledge the match signal cultural awareness and social permission to be present in that moment. Can drive significant orders during pre-match delivery windows.",
    ["Sports passion pegs require speed — content must be published 2-4 hours before kick-off.",
     "Team-specific content risks alienating rival supporters — neutral 'Saudi football' framing is safer than Al-Hilal/Al-Nassr specific unless the brand has official partnership.",
     "Post-match loss content requires careful tonal calibration — celebratory content after a Saudi team loss generates backlash.",
     "International brands without Saudi football cultural equity look performative."],
    ["all"], "1.2x-1.5x",
    [], "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSB9Y1W8F7NPJPG5XDFJDSQD",
    "Trivia Engagement Mechanic",
    "trivia_engagement_mechanic",
    "content_types",
    "A post built around a brand or culture-adjacent trivia question — 'Do you know...?', 'What year did...?', 'True or false:' — where the question drives comments and the brand uses the answer reveal to educate the audience about its heritage, product, or category.",
    ["f_and_b"], 5,
    "Slide 1 (or caption): The question, posed directly. Visual is intriguing but does not answer it. Comments fill with guesses. Slide 2 or follow-up story: The answer reveal — extended with brand-relevant context. Example: 'هل تعرف لماذا سميت قهوة عربية؟' (Did you know why it's called Arabic coffee?) → answer reveals Saudi coffee culture history → brand connects its own coffee identity to that heritage.",
    "Trivia creates a low-stakes comment CTA (everyone knows or guesses without fear of being wrong) while simultaneously delivering educational content that builds brand authority. The two-step structure (question → answer) rewards engagement with payoff. Average engagement score: 0.50 — works better for awareness than conversion.",
    ["Trivia must be genuinely interesting and connected to brand — random trivia for its own sake builds no brand equity.",
     "Answer must add value beyond the bare fact — context and brand connection are the actual content.",
     "Avoid trivia that could be controversial or politically sensitive."],
    ["all"], "1.2x-1.5x",
    [], "sector:f_and_b"
))

written.append(pat(
    "01KSB9Y1W8CQC6CJB0DNWCCN3J",
    "Price Offer Graphic",
    "price_offer_graphic",
    "content_types",
    "A post where the primary content is a promotional price or discount — the number is the headline, the visual is designed to make the price the hero. No cultural storytelling, no hospitality frame. Pure commercial signal.",
    ["f_and_b", "retail"], 12,
    "Visual: bold price number in large type, product image secondary. Color: often brand-primary flood with contrasting price color. Copy: product name + price + validity window + how to order. No Arabic heritage language, no warmth framing. This is the lowest-engagement pattern in the corpus — it works for conversion in audiences already intending to purchase, but does not build brand equity.",
    "Functions as a bottom-of-funnel conversion tool for audiences that have already decided. Useful for limited time offers (White Friday, seasonal sales) but creates no emotional connection and does not attract new audiences. Average engagement score: 0.43 (below corpus median).",
    ["Overuse trains your audience to wait for discounts — erodes full-price buying behaviour.",
     "Saudi audiences respond well to 'value' framing rather than pure price — 'كاملة بسعر رائع' outperforms '30% off'.",
     "Should represent <20% of content mix — heavier use signals a brand that has nothing else to say.",
     "Tier 4 anti-pattern: when price dominates ALL content and no cultural identity is present."],
    ["all"], "1.0x-1.2x",
    []
))

written.append(pat(
    "01KSB9Y1W86Y9HJSWP432CMG1V",
    "Women Empowerment Day",
    "women_empowerment_day",
    "occasion_plays",
    "Content tied to International Women's Day (March 8), Saudi Women's Day, or Vision 2030 female workforce milestones — that celebrates female achievement and positions the brand as aligned with women's advancement in Saudi Arabia.",
    ["f_and_b", "beauty", "retail"], 8,
    "Visual: women in professional or active roles — in the brand's context (female baristas, female executives, female athletes, female artisans). Copy: celebratory, proud, specific to a female achievement or story within the brand's community. Avoid generic 'happy women's day' without substance. Vision 2030 language optional but resonant. Arabic copy: 'المرأة السعودية', 'قوتنا', 'نفخر بكم'.",
    "Vision 2030 has dramatically shifted Saudi social norms around female representation and women's professional identity. Brands that authentically celebrate female workforce participation earn cultural credit with both female audiences and the broader progressive Saudi demographic. Average engagement score: 0.75.",
    ["Must be authentic — brands without female representation in their actual operations ring hollow.",
     "Avoid 'inspiration porn' framing (generic empowerment clichés with no specific stories).",
     "Visual compliance: modest dress, appropriate context, no cross-gender physical contact.",
     "Performative one-day-only content is noticed and critiqued — sustained female representation throughout the year is more credible."],
    ["all"], "1.2x-1.6x",
    ["Female characters must be in culturally appropriate attire for the Saudi market context."]
))

written.append(pat(
    "01KSB9Y1W8KNXANE8A7XYMGMMA",
    "Product Bundle Offer",
    "product_bundle_offer",
    "content_types",
    "A post presenting two or more products together as a curated bundle — framed as a complete experience rather than individual items. The bundle logic (why these items go together) is the editorial hook.",
    ["f_and_b", "retail", "beauty"], 8,
    "Visual: all bundle components displayed together in a composed arrangement (flatlay, lifestyle, or boxed gift). Copy: names each component + explains why they belong together ('تكامل مثالي', 'مع بعض أحلى'). Price of bundle vs. individual items optional (works better for gifting occasions when value is secondary). Often tied to Eid, Mother's Day, or White Friday gifting context.",
    "Bundles elevate average order value and introduce customers to products they wouldn't have chosen individually. In a gifting culture like Saudi Arabia, bundles reduce the cognitive load of gift selection — 'buy this box, it's already curated.' Average engagement score: 0.33 — commercial pattern, low storytelling, better for conversion than discovery.",
    ["Bundle logic must be obvious and compelling — random item groupings confuse more than convert.",
     "Gifting bundles need gift-appropriate packaging — a bundle delivered in a plain bag after premium visual presentation disappoints.",
     "Price emphasis weakens the 'curated experience' positioning — lead with the experience, not the discount."],
    ["all"], "1.1x-1.4x",
    []
))

# ══════════════════════════════════════════════════════════
# PART 2a — LIGHTING MOODS (8 patterns)
# ══════════════════════════════════════════════════════════

written.append(pat(
    "01KSB9Y1W8C56S4N299TF8K7Q6",
    "Golden Hour Hero",
    "golden_hour_hero",
    "lighting_moods",
    "Warm late-afternoon or early-morning natural light (roughly 30 minutes after sunrise or before sunset) used as the primary lighting source. The warm color temperature (2500-3500K) casts long shadows, rich highlights, and a sense of time and place.",
    ["f_and_b", "beauty", "retail"], 28,
    "Shoot during the golden window (30-60 min post-sunrise or pre-sunset). Position the subject so warm light rakes across it — backlighting for silhouettes, side-lighting for texture depth. Embrace lens flare and soft halation. Colors read warm: oranges, golds, ambers dominate even neutral subjects. Outdoor settings preferred; can be simulated indoors with tungsten gels on softboxes.",
    "Golden hour light is universally perceived as emotionally warm, aspirational, and authentic. In the Saudi context, it also evokes specific landscape associations (desert at dusk, rooftop gatherings at Maghrib time) that create instant cultural belonging. Highest single lighting mood in the corpus for both frequency and heritage_vs_modern = blended scores.",
    ["Cannot be faked at the wrong time of day — wrong color temperature immediately reads as over-filtered.",
     "Works poorly for blue-coded or cool modern brands whose visual identity conflicts with warmth.",
     "Desert outdoor settings during summer months require extreme heat management for talent and product."],
    ["all"], "1.4x-1.8x",
    []
))

written.append(pat(
    "01KSB9Y1W8DMVNTJP4ZACK3KA5",
    "Amber Hospitality Light",
    "amber_hospitality_light",
    "lighting_moods",
    "Warm diffuse artificial lighting — from lanterns, candles, dallah warmers, or practical fixtures — that creates an intimate amber glow. The light source is often visible in frame. Associated strongly with majlis settings and iftar contexts.",
    ["f_and_b"], 18,
    "Practical light sources (lanterns, hanging bulbs, candles) provide the key light. Color temperature: 2000-2800K (deep amber/orange). Exposure is intentionally lower than studio bright — shadows are part of the composition. Dallah coffee warmers and bukhoor burners often appear as secondary light sources. Setting is interior, enclosed, intimate.",
    "Amber light is the visual shorthand for Saudi hospitality. It encodes كرم الضيافة without a single word of copy — the warm glow of a lantern-lit majlis is among the most powerful cultural triggers in the corpus. Highest co-occurrence with cultural_object_hero and high_hospitality_majlis_dense patterns.",
    ["Requires careful exposure management — underexposure destroys product visibility; overexposure destroys the mood.",
     "Does not work for modern/minimalist brand identities — the warmth conflicts with cool brand aesthetics.",
     "Product must still be clearly visible within the mood — invisible product = beautiful photography, zero conversion."],
    ["all"], "1.5x-2.0x",
    [], "sector:f_and_b"
))

written.append(pat(
    "01KSB9Y1W8DAEV1WXP7PZZ0B0T",
    "Studio Flat White",
    "studio_flat_white",
    "lighting_moods",
    "Even, shadowless white lighting — achieved via large softboxes, diffusion panels, or white-walled shooting environments — that places product in a clean, clinical, infinitely-white space. No visible light source; no directional shadow.",
    ["f_and_b", "beauty", "retail"], 32,
    "High-key studio setup: two large softboxes flanking subject at 45° or a large overhead diffusion panel. White sweep background, white bounce cards. Color temperature: daylight-balanced 5500-6500K. Shadows minimized or eliminated. Product is the only subject. Often used for product hero, split_screen_before_after, and educational_explainer content types.",
    "Studio flat white is the default production mode for product-first content. It removes all cultural context and distractions, putting the product's design, texture, and color at the center. Works well for clinical beauty brands, precision food photography, and catalogue-style retail. Average engagement: moderate — lower than lifestyle-integrated lighting but essential for certain content types.",
    ["Feels anonymous without strong product design to carry the visual — generic products on white background produce lowest engagement in corpus.",
     "Over-reliance on studio white signals 'catalogue mentality' rather than brand world — Saudi audiences connect more with context.",
     "Works best in combination with lifestyle-coded content in the same feed — pure white feeds read as sterile."],
    ["all"], "1.1x-1.4x",
    []
))

written.append(pat(
    "01KSB9Y1W8HS6JXTF3RPVTG775",
    "Candlelit Intimacy",
    "candlelit_intimacy",
    "lighting_moods",
    "Warm flickering light from candles or small practical flame sources creates an intimate, romantic, or contemplative atmosphere. Color temperature 1800-2200K (very warm orange-red). Associated with evening occasions, Ramadan nights, and personal ritual moments.",
    ["f_and_b", "beauty"], 12,
    "Single or multiple candles provide key light; camera aperture wide to create shallow depth of field and soft bokeh from the flames. Exposure balanced to show product detail while preserving candlelight mood. Background dark or deeply underexposed. Often combined with bukhoor incense smoke for olfactory-visual layering.",
    "Candlelight triggers intimacy and occasion-significance — it signals that this is a special moment. In the Saudi context, candlelight appears in iftar settings, luxury hospitality experiences, and personal skincare/beauty rituals. High co-occurrence with beauty sector transformation content.",
    ["Flame safety compliance in commercial photography contexts.",
     "Extremely low light requires high ISO or long exposure — handheld shooting produces blur.",
     "Does not transfer to F&B products that require colour-accurate representation (food colour looks wrong under orange candlelight)."],
    ["all"], "1.3x-1.7x",
    [], "sector:f_and_b+sector:beauty"
))

written.append(pat(
    "01KSB9Y1W8VV426KPYX0NNNZ0Q",
    "Natural Window Diffused",
    "natural_window_diffused",
    "lighting_moods",
    "Soft, directional natural light from a large window or open door — unmodified or lightly diffused with sheer fabric. Creates gentle gradients from highlight to shadow on one side of the subject. Feels authentic, unmanipulated, and domestic.",
    ["f_and_b", "beauty", "retail"], 15,
    "Position subject 1-3 feet from window, camera facing the window at an angle. Light falls across the subject from one side. No reflectors or a single white bounce card on the shadow side. Color temperature varies with sky conditions — overcast provides the most even diffusion; direct sun requires diffusion fabric. Gives depth and dimension to food, skincare, and handmade products.",
    "Window light is the most 'honest' light in photography. Audiences perceive it as unstaged, real, and trustworthy — a counter-signal to heavily produced brand imagery. In a market increasingly valuing authenticity, natural window diffused content earns trust. Works especially well for home-kitchen and behind-the-craft content types.",
    ["Direction-dependent — requires shooting facing towards the window which conflicts with many set designs.",
     "Variable with weather and time of day — consistency across a shoot day is challenging.",
     "Does not scale to large sets or multiple talent."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8CGKJ3542MFYSNK21",
    "Bright Minimalist High Key",
    "bright_minimalist_high_key",
    "lighting_moods",
    "Intentionally overexposed or near-overexposed lighting that creates a clean, almost ethereal brightness. Whites bloom slightly; shadows are very light or absent. Associated with clinical beauty, wellness, and luxury skincare brands.",
    ["beauty", "retail"], 14,
    "Large diffusion overhead (frame/fly diffusion or massive softbox) combined with white floor and background for total light wrap. Slight intentional overexposure (½-1 stop above metered exposure). Product or talent floats in white space with minimal shadow. Often combined with pastel color accents for brand identity markers.",
    "High-key brightness signals purity, cleanliness, and clinical precision — values that resonate strongly in beauty and wellness. In the beauty sector, it communicates product efficacy through aesthetic cleanliness. Opposite of the amber/candlelit warmth spectrum — deliberately cool and clinical.",
    ["Skin tones can blow out at extreme high-key — requires careful exposure control for talent.",
     "Products with subtle color or texture details can be washed out — test before committing.",
     "Conflict with Saudi heritage warmth aesthetic — avoid for heritage-positioned brands."],
    ["all"], "1.2x-1.5x",
    [], "sector:beauty+sector:retail"
))

written.append(pat(
    "01KSB9Y1W85KN6X9NHPXDS1XSM",
    "Blue Hour Cinematic",
    "blue_hour_cinematic",
    "lighting_moods",
    "The narrow window after sunset and before darkness (15-30 minutes) when the sky is a deep blue and artificial lights begin to appear, creating a two-tone luminescence of cool natural blue and warm artificial orange. Highly cinematic, moody, and aspirational.",
    ["f_and_b", "retail"], 5,
    "Shoot at dusk in an outdoor or semi-outdoor setting. Sky provides deep blue ambient fill; practical lights (street lamps, venue lighting, illuminated signage) create warm foreground accents. Camera balanced between natural and artificial (typically 3200-4500K). Wide establishing shots work well; product appears as part of an aspirational urban moment.",
    "Blue hour is among the most cinematically striking light conditions and consistently stops scroll on social media. In the Saudi context, it evokes evening in modern Riyadh or Jeddah — aspirational urban lifestyle positioning. Currently underused (only 5 accounts in corpus) — represents a significant visual differentiation opportunity.",
    ["Only 15-30 minute shooting window — requires meticulous pre-shoot planning.",
     "Weather-dependent; clouds can eliminate the blue sky required.",
     "Equipment must handle low light — requires fast lenses or large sensor cameras.",
     "Conflicts with pure heritage/traditional brand aesthetics."],
    ["all"], "1.4x-1.9x",
    []
))

written.append(pat(
    "01KSB9Y1W81DMF3EM51CJWCE3N",
    "Neon Urban Artificial",
    "neon_urban_artificial",
    "lighting_moods",
    "Deliberate use of colored artificial light — neon pink, blue, purple, or cyan — as the primary creative lighting tool. Associated with contemporary youth culture, nightlife-adjacent aesthetics, and modern urban Saudi identity.",
    ["f_and_b", "retail"], 4,
    "LED neon lights, colored gels on strobes, or commercial neon signage provide the key light. Color choices are bold and saturated. Product is bathed in single or complementary neon tones. Setting: contemporary urban, nightlife-adjacent (though content must remain culturally appropriate for Saudi market). Text overlays often match the neon color family.",
    "Neon aesthetics signal contemporary, urban, youth-coded brand identity. Currently one of the least-used lighting patterns in the Saudi brand corpus (only 4 accounts) — representing a major differentiation opportunity for brands targeting Gen Z and younger millennials. High visual distinctiveness potential.",
    ["Must remain culturally appropriate for Saudi market — neon nightlife aesthetics have limits.",
     "Does not work for heritage or traditional brand positioning.",
     "Colored light creates colour cast on product — test with actual products before committing.",
     "Can feel dated quickly as aesthetic trends shift — monitor lifespan carefully."],
    ["all"], "1.2x-1.6x",
    ["Neon aesthetics should not evoke nightclub/alcohol-adjacent contexts."]
))

# ══════════════════════════════════════════════════════════
# PART 2b — COLOR PALETTE PATTERNS (10 patterns)
# ══════════════════════════════════════════════════════════

written.append(pat(
    "01KSB9Y1W8WZPEMX1YNR0K7CJF",
    "Warm Earth Palette",
    "warm_earth_palette",
    "color_palette_patterns",
    "A palette built from the warm earth spectrum: browns, warm grays, golds, russets, tans, terracottas. Evokes sand, soil, coffee, spices, and traditional Saudi materials (clay, leather, wood). The dominant palette signal for heritage and hospitality positioning in the corpus.",
    ["f_and_b", "beauty", "retail"], 38,
    "Lead colors: burnt sienna, warm beige, cognac brown, antique gold, desert tan. Accent: deep olive green or dusty terracotta. Avoid: cool blues, bright pinks, stark whites. Warm earth works across product (coffee, dates, wood-fired bread), setting (clay-walled majlis, wooden furniture), and character (thobe in warm sand tones).",
    "Warm earth is the most natural palette for Saudi cultural authenticity — it literally maps to the colors of the Saudi landscape and heritage materials. Most frequent palette in the corpus (142+ obs), highest correlation with heritage_vs_modern = heritage and blended. Signals trust, depth, and rootedness.",
    ["Risks feeling generic if not differentiated with specific brand color accent.",
     "Can feel muddy or low-energy without careful color management and strong hero element.",
     "Western audiences sometimes read warm earth as 'dusty' — for Saudi-first content this is irrelevant."],
    ["all"], "1.3x-1.7x",
    []
))

written.append(pat(
    "01KSB9Y1W8E38FDACB2P8NM3Z8",
    "Cool Modern Palette",
    "cool_modern_palette",
    "color_palette_patterns",
    "A palette built from the cool modern spectrum: whites, cool grays, blacks, silvers, off-whites, light blues. Evokes clinical precision, luxury minimalism, and architectural modernity. Dominant palette for contemporary brand identities.",
    ["beauty", "retail", "f_and_b"], 24,
    "Lead colors: pure white, warm off-white, cloud gray, charcoal, silver. Accent: single bold brand color against neutral. Avoid: warm browns, earth tones, russets. Works across studio white photography, architectural interior shots, premium packaging design, and minimalist lifestyle content.",
    "Cool modern signals brand sophistication, international-level quality, and modernity — values that resonate with the aspirational urban Saudi consumer. Strong in beauty and luxury retail sectors. Presents a visual contrast to the warm-earth-dominant Saudi brand landscape — high differentiation potential.",
    ["Conflicts directly with heritage/hospitality brand positioning.",
     "Risk of looking 'cold' or uninviting — warm accent color (gold, blush) needed to humanize.",
     "Can look identical to international brand visual identities — requires distinctive brand element to own."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8QMX8KZ2HVQVZ0A8G",
    "Saudi Flag Palette",
    "saudi_flag_palette",
    "color_palette_patterns",
    "A palette anchored in the Saudi national colors: deep green, white, and gold/black accents. Used for national occasions, Vision 2030 content, institutional messaging, and brand expressions of Saudi pride.",
    ["f_and_b", "beauty", "retail"], 18,
    "Lead colors: Saudi green (Pantone 349C or similar), white, gold, black. Typography often white on green or green on white. May incorporate Arabic calligraphy, the Saudi emblem, or palm tree/swords motifs. Used on National Day (September 23), Founding Day (February 22), and Vision 2030 milestones.",
    "The Saudi flag palette is an instant occasion signal — audiences immediately decode it as a national moment. Brands that use it authentically and non-exploitatively (not slapping green on a product image and calling it National Day) earn cultural goodwill. Highest co-occurrence with national_day_pride and founding_day_heritage patterns.",
    ["Using green + white outside of national occasions can read as flag appropriation — context-specific use only.",
     "The Saudi flag itself (the shahada + sword) must not be distorted, placed on products, or used in ways that could be considered disrespectful.",
     "Generic green + white without Saudi-specific content elements scores poorly — the palette alone is not enough."],
    ["all"], "1.2x-1.6x",
    ["The Saudi national emblem (shahada + crossed swords) must be used respectfully and never placed on products."]
))

written.append(pat(
    "01KSB9Y1W8T1DNCDKG5X8SRS2B",
    "Berry and Wine Palette",
    "berry_wine_palette",
    "color_palette_patterns",
    "A palette built from deep rich purples, wines, berries, and magentas. Signals femininity, sophistication, luxury, and a certain aspirational sensuality. Dominant in the beauty sector, particularly for skincare, lip products, and perfumes.",
    ["beauty", "retail"], 18,
    "Lead colors: deep burgundy, plum, raspberry, muted mauve, deep rose. Accent: gold or cream. Avoid: harsh blacks or cool blues that flatten the richness. Works across product backgrounds, floral arrangements, fabric draping, and beauty lifestyle scenes. Often combined with soft-focus candlelit or studio-diffused lighting.",
    "Berry/wine tones are the dominant palette for premium Saudi beauty brands. They signal luxury and femininity while remaining culturally conservative — richness without exposure. High co-occurrence with model_centered_frontal_portrait and transformation_story patterns in the beauty sector.",
    ["Can feel heavy or claustrophobic without light-toned relief elements (cream, gold).",
     "Risk of matching competitor brand palettes — differentiation requires specific shade ownership.",
     "Does not transfer to F&B without careful product alignment (berries, dates, grape-derived products)."],
    ["all"], "1.3x-1.6x",
    [], "sector:beauty+sector:retail"
))

written.append(pat(
    "01KSB9Y1W8ASMERX7HX24QC9NJ",
    "Spice Bazaar Palette",
    "spice_bazaar_palette",
    "color_palette_patterns",
    "A palette of deep warm reds, ochres, deep oranges, dark burnt browns, and saffron yellows — evoking the colors of a traditional Saudi or Gulf spice market. Rich, warm, and saturated. Signals craft, tradition, and sensory abundance.",
    ["f_and_b", "retail"], 10,
    "Lead colors: saffron yellow, brick red, turmeric orange, dark burnt umber, paprika. Accent: deep teal or forest green for contrast. This palette works with actual spice products (photogenic in its own right) but also for traditional crafts, incense, and heritage food experiences. Works best with textural props (woven baskets, clay vessels, rough wooden surfaces).",
    "The spice bazaar palette instantly encodes Middle Eastern cultural authenticity and sensory richness. For F&B brands, it signals traditional flavour complexity. For retail brands selling heritage crafts or incense, it is the natural visual language. Strong resonance with Saudi audiences who recognise these colors from physical souk experiences.",
    ["Requires genuine product/thematic alignment — random use of these colors with non-heritage content looks like a cultural costume.",
     "Heavy saturation requires careful color management in post-production — over-saturation pushes into 'cartoon' territory.",
     "Does not work for modern, minimalist, or youth-coded brands."],
    ["all"], "1.3x-1.7x",
    [], "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSB9Y1W8GDA8BJHZ3FVXN4A1",
    "Monochrome Elegance",
    "monochrome_elegance",
    "color_palette_patterns",
    "A single-hue or near-single-hue palette where the entire frame operates within one color family — white-on-white, black-on-black, cream-on-cream, or a single saturated color as field. Signals extreme restraint, luxury, and editorial precision.",
    ["beauty", "retail"], 12,
    "The frame is dominated by a single color family (70%+ of the image). Texture and form create the visual interest within the monochrome field — gloss vs. matte, smooth vs. rough, light vs. shadow. A single accent element (product label, brand logo, gold trim) may introduce a contrasting color sparingly. Typography is often white or black depending on field color.",
    "Monochrome is among the most distinctive visual approaches in the corpus — it signals editorial-level confidence and luxury positioning. Saudi luxury audiences respond to this palette as international-quality content. Used by premium beauty and designer retail accounts. Requires strong product design to sustain interest within the single color constraint.",
    ["Requires genuine visual interest through texture/form — flat monochrome with no texture reads as empty.",
     "Product must be legible within the monochrome field — dark product on dark background loses the product.",
     "Risk of inaccessibility — some audiences find monochrome posts harder to parse on small screens."],
    ["all"], "1.3x-1.7x",
    [], "sector:beauty+sector:retail"
))

written.append(pat(
    "01KSB9Y1W893TQSG6BSVTHCVTF",
    "Brand Green Dominant",
    "brand_green_dominant",
    "color_palette_patterns",
    "A palette where the brand's primary green dominates the frame — used as background flood, product color, or environmental color. Most common for Saudi brands that use green as their primary brand color (aligned with Saudi national identity). The green carries both brand and national identity simultaneously.",
    ["f_and_b", "retail"], 14,
    "Brand green fills 50%+ of the frame. Product appears against the green field or within a green-coded environment. Typography is white or light cream on green. Logo is always present to anchor brand ownership of the color. Other colors: white (secondary), gold (accent). The green-white-gold combination is distinctly Saudi brand-coded.",
    "Green is among the most loaded colors in Saudi brand communication — it carries brand identity AND national identity simultaneously. For brands that have earned the color through consistent usage, green is an immediate scroll-stopper in a Saudi feed. Barnscoffee's green is the strongest example in the corpus.",
    ["Only works for brands that genuinely own green in their category — a new brand using green looks derivative of barnscoffee or the Saudi flag.",
     "Green on green (product + background) requires careful shade differentiation to avoid visual mud.",
     "Post-national-day content using green must clearly remain brand-coded, not occasion-coded."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8YJJ1MJZR209EYA27",
    "Desert Sand Palette",
    "desert_sand_palette",
    "color_palette_patterns",
    "A palette built from the natural desert spectrum: sandy beiges, warm yellows, dune golds, pale ochres, and bleached whites. Evokes the Saudi landscape with restraint and naturalness — quieter than warm earth palette, more open and arid.",
    ["f_and_b", "retail"], 10,
    "Lead colors: warm beige, sand yellow, pale ochre, dune white, bleached cream. Very low saturation — these are almost neutral colors with a warm temperature. Works with natural textile (undyed linen, cotton), natural stone surfaces, and outdoor Saudi landscape photography. Often combined with golden hour hero lighting for maximum landscape resonance.",
    "Desert sand palette is the most geographically specific palette in the Saudi brand lexicon — it literally maps the Saudi landscape. For brands selling into Saudi identity and pride (tourism, heritage crafts, national-occasion content), it signals authenticity and place. Quieter than spice bazaar — contemplative rather than sensory.",
    ["Requires high production quality — low saturation palettes look washed out on poorly calibrated screens.",
     "Products with warm earth or similar tones can disappear into the palette — need strong form/texture differentiation.",
     "Not suitable for urban-modern or youth-coded brand positioning."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8J5WGV9YFQEFCZ60M",
    "Tropical Escape Palette",
    "tropical_escape_palette",
    "color_palette_patterns",
    "A palette of bright turquoise, coral, lime green, orange, and warm white — evoking beach, summer escape, and energetic modernity. Currently underused in the Saudi brand corpus (12 obs) — represents a significant visual differentiation opportunity for youth-oriented brands.",
    ["f_and_b", "retail"], 5,
    "Lead colors: turquoise/teal, coral orange, lime green, bright white. High saturation, high energy. Works for summer campaigns (May-September), beverage brands, poolside or coastal content. Strongest for younger demographics. Saudi summer indoor pivot can use this palette to signal 'escape from the heat' via visual energy.",
    "Bright tropical palettes stand out dramatically against the earth-tone dominant Saudi brand landscape. In a feed of browns and greens, a turquoise-coral post is an immediate scroll-stopper. Underused = differentiation opportunity. Highest potential for youth F&B brands and summer-campaign retail.",
    ["Conflicts with heritage, formal, or traditional brand positioning.",
     "Requires genuine product/occasion relevance — random tropical palette without summer/beach context looks incongruous.",
     "Color accuracy management important — on-screen turquoise often looks very different in print."],
    ["all"], "1.3x-1.7x",
    []
))

written.append(pat(
    "01KSB9Y1W80HCB698WABQ6J0GT",
    "Ramadan Gold Purple",
    "ramadan_gold_purple",
    "color_palette_patterns",
    "A seasonal palette anchored in deep purples, rich golds, and warm night-sky blacks — the visual vocabulary of Ramadan and Eid celebration imagery. Signal of the holy month's visual language: lanterns, crescent moons, dates, and evening gatherings.",
    ["f_and_b", "beauty", "retail"], 18,
    "Lead colors: deep violet/purple, antique gold, warm black, ivory. Accent: burgundy or deep emerald. Often includes crescent moon motifs, lantern shapes, or ornate geometric overlays as design elements. Typography in gold or ivory. Photography: low-light evening scenes with warm practical lighting (lanterns, candles).",
    "Purple-gold is the established visual vocabulary for Ramadan and Eid in the Saudi brand landscape — audiences decode it instantly as the holy month. Brands that use this palette in-season signal cultural awareness and occasion-readiness. Highest usage in Ramadan and Eid window (March-April and June-July depending on year).",
    ["Using this palette outside of Ramadan/Eid season creates confusion — reserve it seasonally.",
     "Must include genuine Ramadan/Eid content, not just the palette — palette without appropriate messaging is hollow.",
     "Over-saturation of purple can read as tacky — requires restraint in color intensity."],
    ["all"], "1.3x-1.8x",
    ["Ramadan content must maintain respectful register — no satire or irreverence."]
))

# ══════════════════════════════════════════════════════════
# PART 2c — CHARACTER REPRESENTATION (8 patterns)
# ══════════════════════════════════════════════════════════

written.append(pat(
    "01KSB9Y1W8N1R8Z6ZZRWMG4EA2",
    "Hands Only (Implicit Character)",
    "hands_only_implicit",
    "character_representation",
    "Visual content featuring only hands — no face, no full body — as the character element. Hands hold, pour, serve, arrange, or create the product. The human presence is implied but not shown. A culturally conservative approach to human representation that still conveys warmth and craft.",
    ["f_and_b", "beauty", "retail"], 32,
    "Frame from wrist to fingertips. Right hand preferred and often required (left-hand serving is a hard block in compliance). Hands should be well-groomed, with appropriate accessories (no rings for conservative content; gold jewelry acceptable for female characters in female-coded brands). Action should look natural — mid-pour, mid-arrangement, presenting item. Close-up macro framing emphasizes craft.",
    "Hands-only is the most compliance-safe human representation pattern — no gender presentation issues, no face compliance review, no cross-gender contact risk. Yet it retains the warmth signal of human presence. The corpus shows strong co-occurrence with amber_hospitality_light and behind_the_craft patterns. High hospitality signal with minimal compliance risk.",
    ["Right-hand rule is strict — left hand serving is a hard block in many Saudi compliance frameworks.",
     "Hands must look like the brand's intended demographic — rough working hands vs. manicured hands send different signals.",
     "Avoid gestures that could be misread — pointing, open palm, finger count are culturally loaded."],
    ["all"], "1.3x-1.6x",
    ["Left hand must not be the primary serving/presenting hand — right hand rule applies."]
))

written.append(pat(
    "01KSB9Y1W8JB9DHBHPVDKV086R",
    "Solo Hero (Gender Neutral)",
    "solo_hero_neutral",
    "character_representation",
    "A single figure centered in frame, facing the camera with confidence. Gender may be ambiguous or clearly defined depending on brand context. The figure is the primary visual element — product is secondary or fully absent (brand presence rather than product sell).",
    ["beauty", "retail", "f_and_b"], 28,
    "Single subject, centered or rule-of-thirds positioned. Eye contact with camera (direct gaze) signals brand confidence. Clean background or blurred environment. Product integrated naturally (held, worn, adjacent). Wardrobe is brand-coded — reflects target audience's aspirational identity. Lighting: portrait-appropriate (beauty dish, large softbox).",
    "The solo hero portrait is the universal brand ambassador format. In Saudi content, it communicates brand confidence and personal endorsement simultaneously. Works for beauty (model as proof of product), retail (model as lifestyle aspirant), and F&B (ambassador as cultural familiar). Most frequent character pattern in the corpus.",
    ["Wardrobe must be culturally appropriate — coverage requirements vary by sector (beauty: more latitude; F&B: conservative).",
     "Direct eye contact (especially female models) should be calibrated for platform and audience — some conservative Saudi audiences respond better to averted gaze.",
     "Avoid over-retouching that makes subject look inhuman — Saudi audiences value relatable aspiration."],
    ["all"], "1.2x-1.5x",
    ["Female models must meet Saudi market modesty standards for the relevant sector."]
))

written.append(pat(
    "01KSB9Y1W8PNDV84YKNDZZG5K9",
    "Family Majlis (Hierarchical Gathering)",
    "family_majlis_hierarchical",
    "character_representation",
    "A multi-generational family scene (typically 3-7 people) in a majlis or family dining setting. An elder figure often anchors the composition. Gender-appropriate seating and spacing applies. The gathering signals Saudi family values, hospitality, and generational continuity.",
    ["f_and_b", "retail"], 18,
    "Wide or medium shot capturing the full gathering. Elder figure positioned at center or head position. Genders may be present together at a family table but not in physical contact. Warmth signals: food on table, shared drink (qahwa/tea), natural family posture (conversation, laughter). Setting: heritage interior or hybrid modern-heritage. Lighting: warm practical.",
    "The family gathering is the pinnacle Saudi social occasion — it signals belonging, tradition, and generosity. Brands that successfully show a family around a table immediately encode كرم الضيافة and communal warmth. High appeal across all demographics because it's the universal Saudi shared experience.",
    ["Cross-gender physical contact (touching, close proximity) is a compliance risk — ensure appropriate spacing.",
     "Non-Saudi family aesthetics (Western nuclear family formats) reduce authenticity.",
     "Elder figure representation requires dignity and respect — should not be secondary or background."],
    ["all"], "1.4x-1.8x",
    ["Mixed-gender family scenes must observe appropriate physical spacing between non-mahram individuals."]
))

written.append(pat(
    "01KSB9Y1W8CACF1C5BQAE3Q4PV",
    "Female-Forward Group",
    "female_forward_group",
    "character_representation",
    "A group of women (2-5) as the primary character element — in a social, professional, or lifestyle context. Used for brands targeting female audiences, Vision 2030 female workforce narratives, and beauty/wellness content where female community is the aspirational frame.",
    ["beauty", "retail", "f_and_b"], 16,
    "Group of 2-5 women, photographed in a shared activity (coffee, conversation, shopping, professional setting). All characters in culturally appropriate attire. Expressions: natural, joyful, confident — not performative or posed unnaturally. Setting: contemporary Saudi feminine spaces (modern café, boutique, professional environment). Avoid cross-gender contact or proximity.",
    "Female social groups are increasingly prominent in Saudi brand content following Vision 2030 shifts. They signal modernity, female friendship, and aspirational social life without transgressing cultural norms. Strong signal for female-targeted brands and any brand wanting to reach Saudi women 18-35.",
    ["Wardrobe compliance critical — all characters must meet coverage standards for the relevant sector/context.",
     "Group dynamics must feel natural — forced 'girls laughing at nothing' poses are immediately rejected by Saudi female audiences.",
     "Cross-gender contact must be absent — all-female groups avoid this complexity cleanly."],
    ["all"], "1.3x-1.6x",
    ["All female characters must wear culturally appropriate attire (abaya, hijab, or equivalent per sector norm)."],
    "sector:beauty+sector:retail+sector:f_and_b"
))

written.append(pat(
    "01KSB9Y1W8YFTW79T0V8FD5Y0D",
    "Uniform / Role-Coded Character",
    "uniform_role_coded",
    "character_representation",
    "A character whose identity is defined by their uniform, tools, or professional role — chef, barista, server, artisan, guide, delivery driver — rather than their personal identity. The role signals brand quality, craftsmanship, and service.",
    ["f_and_b", "beauty", "retail"], 22,
    "Character wears identifiable role uniform (chef coat, barista apron, branded delivery uniform). Face may be visible or partially obscured (hat, mask). Action is role-specific (plating food, pulling espresso, arranging products). Focus on the role performance rather than personal expression. Brand logo on uniform where possible.",
    "Role-coded characters communicate expertise and service quality without the compliance complexity of model representation. They signal that the brand employs skilled people — implying product quality through workforce pride. Low compliance risk. High co-occurrence with behind_the_craft pattern.",
    ["Uniform must look professional and well-maintained — a sloppy uniform sends the opposite brand signal.",
     "Face visibility optional but partial visibility (hat brim, profile shot) creates more warmth than full anonymity.",
     "Brand logo on uniform is a strong reinforcement opportunity — missing logo is a waste."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8KC1CV5PNTJD38PQ8",
    "Child-Inclusive Narrative",
    "child_inclusive_narrative",
    "character_representation",
    "A post where a child or youth character (typically 2-12 years old) is a core, active element of the scene — not background. Children signal family values, innocence, joy, and generational continuity. High emotional resonance in Saudi family-oriented brand content.",
    ["f_and_b", "retail"], 14,
    "Child is featured in an active, joyful moment — interacting with the product, in a family gathering, or as the POV subject. Camera at child's eye level for intimacy (rather than looking down). Expressions: natural joy, curiosity, wonder. Setting: home, family dining, occasion celebration. Adults present in background for family frame. Product must be child-appropriate.",
    "Children in Saudi brand content generate immediate warmth and emotional engagement — they are universally loved and signal brand alignment with family values, the most central Saudi cultural institution. High engagement in comment sections (parents tag each other, share for their own children).",
    ["Child safety compliance: parents/guardians must consent; faces should not be prominently featured without explicit consent management.",
     "Product must be genuinely child-appropriate — a child in an adult luxury context is jarring.",
     "Never use children in any content that could be considered distressing, forced, or uncomfortable."],
    ["all"], "1.4x-1.8x",
    ["Child character representation requires full parental consent compliance for commercial content."]
))

written.append(pat(
    "01KSB9Y1W887974MN3HHXQMKHM",
    "Professional Same-Gender Duo",
    "professional_same_gender_duo",
    "character_representation",
    "Two people of the same gender in a professional, collaborative, or peer moment — working together, in conversation, or sharing an experience. The pair dynamic signals teamwork, community, and peer validation without cross-gender compliance considerations.",
    ["f_and_b", "retail", "beauty"], 14,
    "Two figures, same gender, in a shared activity or conversation. Professional or lifestyle setting. Body language: collaborative (looking at the same thing), conversational (facing each other), or parallel (doing same activity side by side). Eye contact between characters preferred over looking at camera — suggests genuine interaction not posed advertising.",
    "The same-gender duo is the safest group character format in the Saudi market — it avoids all cross-gender compliance complexity while still showing human warmth and social aspiration. Works for professional brand stories (two colleagues), social moments (two friends at café), and mentor-mentee narratives.",
    ["Must feel like genuine human connection — identical-twin-styled forced symmetry looks artificial.",
     "Avoid romantic or affectionate sub-text even between same-gender pairs — keep context clearly professional/social.",
     "Character diversity within the pair (different ages, different roles) creates more visual interest."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W89TWF9M4E6YCTHQ7F",
    "Multicultural Casting",
    "multicultural_casting",
    "character_representation",
    "Content featuring characters whose visual identity signals non-Saudi or diaspora identity — South Asian, African, East Asian, Western expat, or Arab diaspora — as intentional representation of Saudi Arabia's diverse population.",
    ["f_and_b", "retail"], 5,
    "Characters whose appearance, dress, or accent clearly signals non-Saudi heritage. Framing is respectful and equal — not 'tourism gaze' or exotic othering. Content acknowledges the multicultural nature of Saudi society without calling attention to it as the primary message. Often appears in employer brand content (multinational team) or urban lifestyle content (diverse customer base).",
    "Saudi Arabia has a large expatriate and diverse population. Multicultural casting signals that a brand serves and respects all residents, not only nationals — an increasingly important signal in Riyadh and Jeddah urban markets. Currently one of the rarest character patterns in the corpus (5 obs) — significant gap opportunity for brands serving diverse audiences.",
    ["Must be genuinely respectful and equal — tokenistic or othering representations generate backlash.",
     "Diaspora and expat communities in Saudi Arabia are sophisticated audiences who detect inauthentic representation immediately.",
     "Cultural dress of represented groups must be accurate and respectful.",
     "Context must make sense — diverse casting for a heritage-only product is incongruous."],
    ["all"], "1.2x-1.6x",
    []
))

# ══════════════════════════════════════════════════════════
# PART 2d — SETTING / ENVIRONMENT (10 patterns)
# ══════════════════════════════════════════════════════════

written.append(pat(
    "01KSB9Y1W8Y96BF9XYGYCHY5MP",
    "Heritage Majlis Interior",
    "heritage_majlis_interior",
    "setting_environment",
    "A traditional Saudi sitting room (majlis) or heritage-coded interior featuring low seating with cushions, geometric-patterned carpets, lanterns, carved wood details, and cultural objects (dallah, misyar, incense burner). The setting encodes hospitality, tradition, and Saudi identity.",
    ["f_and_b", "retail"], 28,
    "Setting: low seating (floor cushions or traditional low-back sofas), woven or geometric-patterned carpet, warm wood or mud-brick wall textures, lanterns or practical warm lighting, Arabic geometric patterns on architectural elements. Props: dallah, finjan, bukhoor burner, dates, incense. Color palette: warm earth tones dominated by deep reds, browns, and golds.",
    "The majlis is the most iconic Saudi social space — it represents hospitality, community, and cultural continuity. Content set in a majlis-coded interior immediately signals that the brand understands and respects Saudi culture at its core. Highest co-occurrence with amber_hospitality_light, cultural_object_hero, and high_hospitality_majlis_dense patterns.",
    ["Setting must be authentic — a poorly executed 'Arabic' set from stock props reads immediately as inauthentic.",
     "Modern brands whose visual identity conflicts with the warm heritage aesthetic should use hybrid_modern_heritage instead.",
     "Over-use of this setting can feel formulaic — requires variation in shot angles, time of day, and props."],
    ["all"], "1.4x-1.8x",
    [], "sector:f_and_b+sector:retail"
))

written.append(pat(
    "01KSB9Y1W8DWRHR7NFZE4K2ZSE",
    "Modern Minimalist Interior",
    "modern_minimalist_interior",
    "setting_environment",
    "A contemporary interior designed around minimal furniture, neutral palette, clean lines, and architectural negative space. The setting communicates modernity, premium quality, and international design sensibility — the antithesis of heritage-coded settings.",
    ["beauty", "retail", "f_and_b"], 22,
    "Setting: low furniture-to-space ratio, visible architecture (high ceilings, large windows, concrete or marble surfaces), neutral or monochrome palette (whites, grays, blacks), concealed or minimal lighting fixtures. Props: single design object, brand product placed with spatial generosity. No clutter, no pattern, no warmth objects.",
    "Modern minimalist signals premium international positioning, brand confidence, and sophisticated taste. For Saudi brands targeting urban professional and luxury-conscious audiences, this setting communicates 'world-class' quality. Strong differentiation from the heritage-heavy brand landscape.",
    ["Cold and impersonal if not balanced with a warm brand element (product, accent color, human presence).",
     "Requires genuine location or set build quality — a budget studio that attempts minimalism looks empty, not minimal.",
     "Conflicts with heritage and hospitality-coded brand positioning."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8K8KPKD3ZVYJNBH5H",
    "Luxury Hospitality Space",
    "luxury_hospitality_space",
    "setting_environment",
    "A premium restaurant, hotel lobby, high-end café, or luxury hospitality venue used as the shooting environment. The space itself communicates quality — through design details, table settings, materials, and spatial generosity.",
    ["f_and_b"], 20,
    "Setting: professional table setting (linen, glassware, branded crockery), designed ambient lighting, architectural design details visible (custom furniture, art, branded materials). Props: food plated at restaurant standards, premium beverage service. Depth of field shows the dining room in background (soft). Logo/branding often visible in the environment (menu, branded items).",
    "The venue IS the brand promise. When a restaurant photographs in its own space, every design choice — the chairs, the lighting, the table set — is a brand signal. High-production venue photography tells the audience 'this is worth visiting.' Co-occurs strongly with invitation_to_witness pattern.",
    ["Venue must be genuinely well-designed — photographing a poorly designed space in high resolution amplifies the flaws.",
     "Avoid empty venue shots — the absence of people reads as 'nobody goes here.'",
     "Venue shots work for destination brands (dine-in) but poorly for delivery-only or product-only brands."],
    ["all"], "1.3x-1.7x",
    [], "sector:f_and_b"
))

written.append(pat(
    "01KSB9Y1W8EHTTPCWA4ZG0V5E5",
    "Studio White Void",
    "studio_white_void",
    "setting_environment",
    "A seamless white or near-white background that eliminates all setting context — the product floats in a clean, context-free space. The most common setting in product-hero and educational content.",
    ["beauty", "retail", "f_and_b"], 36,
    "Seamless white sweep background (paper or digital). No visible environmental context. Product centered or ruled-of-thirds. Sometimes a surface texture (marble, white wood, white fabric) appears as a minimal setting cue. Lighting calibrated for product color accuracy. Product is the only subject.",
    "Studio white void maximizes product clarity and minimizes visual distraction. Essential for catalogue, e-commerce, and product launch content. Works across all sectors as a utility format but scores lower than lifestyle-integrated settings for brand building. Most efficient for batch production.",
    ["Overuse creates a 'catalogue brand' perception — audience sees product, not brand world.",
     "Low engagement per post but high conversion utility for purchase-intent audiences.",
     "Must be paired with lifestyle and cultural content to maintain brand warmth."],
    ["all"], "1.1x-1.3x",
    []
))

written.append(pat(
    "01KSB9Y1W83QQJGCB605ZKRX1X",
    "Home Kitchen / Domestic",
    "home_kitchen_domestic",
    "setting_environment",
    "A domestic home kitchen, dining area, or family table setting — real or realistically staged to appear as a home environment. Signals authenticity, accessibility, and everyday life aspiration.",
    ["f_and_b"], 14,
    "Setting: domestic kitchen with lived-in details (appliances, family items, imperfect surfaces), or family dining table with home-scale settings (not restaurant). Props appropriate to home cooking and family dining. Lighting: natural window or warm domestic fixtures. People optional but enhance the domestic signal (mom cooking, family at table).",
    "Home setting is the authenticity signal — it says 'this food belongs in your home, not just at a restaurant.' For F&B brands, it creates aspirational domestic use cases. For recipe content and product demonstrations, the home kitchen is the logical natural setting. Counter-programs against the luxury-venue-only brand approach.",
    ["Setting must feel genuinely domestic — overly styled 'home' sets read as studio.",
     "Implies accessibility/affordability — luxury brands may want to avoid this setting.",
     "Cultural appropriateness of domestic interiors — Saudi home aesthetics vary by region and family type."],
    ["all"], "1.2x-1.5x",
    [], "sector:f_and_b"
))

written.append(pat(
    "01KSB9Y1W8NK6HNTYZCMDYDPRC",
    "Outdoor Saudi Landscape",
    "outdoor_saudi_landscape",
    "setting_environment",
    "The Saudi natural landscape — desert, wadis, rocky mountains, dunes, open sky — used as the primary setting or dramatic background. Connects product or brand to Saudi geography and national identity.",
    ["f_and_b", "retail"], 14,
    "Wide establishing shots showing Saudi landscape features (sand dunes, Hejaz mountains, Nejd plains, coastal Red Sea). Product or talent in foreground with landscape in background or mid-ground. Golden hour or magic hour lighting strongly preferred (transforms landscape into warm, evocative environment). Styling: Arabic/Saudi-themed elements (misyar, tents, traditional props) optional but reinforcing.",
    "The Saudi landscape is a powerful national identity signal — it evokes patriotism, natural heritage, and the unique geographical character of the Kingdom. Brands that use the landscape authentically communicate deep Saudi roots. High correlation with national_day_pride, founding_day_heritage, and warm_earth_palette patterns.",
    ["Requires genuine location shooting — fake desert backdrops are immediately obvious.",
     "Summer months make outdoor shooting physically challenging — safety planning essential.",
     "National park and heritage site photography may require permits."],
    ["all"], "1.3x-1.7x",
    []
))

written.append(pat(
    "01KSB9Y1W8BE61HZN9P4V9GCA4",
    "Urban Street / Market",
    "urban_street_market",
    "setting_environment",
    "A street-level urban environment — traditional souq/market, modern commercial street, food vendor strip, or urban neighborhood — used as a dynamic, authentic setting. The setting signals real-life vitality and community presence.",
    ["f_and_b", "retail"], 10,
    "Setting: actual urban or market environment with authentic activity (real vendors, real customers, real products in surrounding environment). Camera may be handheld for documentary feel. Crowd or activity in background adds depth and life. Product or brand visible in natural commercial context (product on market stall, food from street vendor, brand signage in street scene).",
    "Street and market settings signal that the brand is part of the real Saudi commercial world — not a distant luxury entity. Community presence is a hospitality signal. For traditional food brands, the street/market context authenticates heritage positioning. Strong for documentary content types.",
    ["Uncontrolled environment — other brands, faces, and visual elements are all in frame and require clearing.",
     "Saudi market settings (traditional souq) may require permission for commercial filming.",
     "Crowded settings require careful crowd management for halal/compliance purposes."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8CFRMWGP6XV15TMSJ",
    "Hybrid Modern-Heritage",
    "hybrid_modern_heritage",
    "setting_environment",
    "A setting that deliberately combines contemporary design elements with heritage materials, motifs, or objects — modern furniture with traditional textiles, minimalist space with a dallah on the shelf, clean architecture with Arabic geometric details. The hybrid signals cultural continuity through modernity.",
    ["f_and_b", "retail", "beauty"], 22,
    "Setting design: one dominant element from each register (e.g., concrete walls + handwoven carpet; modern sofa + lantern on side table; white marble table + brass dallah centrepiece). Color palette: typically warm earth or warm modern. The combination should feel intentional, not accidentally eclectic. Heritage objects should be placed with design intentionality.",
    "Hybrid modern-heritage is the fastest-growing setting type in the Saudi brand corpus — it reflects the lived reality of Saudi Vision 2030, where tradition and modernity are not opposites but complements. This setting appeals to the broadest Saudi demographic: traditionalists see their heritage honored; modernists see their aspiration reflected. Highest differentiation potential.",
    ["Hybridization must feel intentional and considered — random mixing reads as poor design.",
     "Heritage objects must be used respectfully, not as decoration/props stripped of meaning.",
     "The balance point matters — tipping too far to either end loses the hybrid signal."],
    ["all"], "1.4x-1.8x",
    []
))

written.append(pat(
    "01KSB9Y1W8ADE28Y009F22FWTD",
    "Architectural Landmark",
    "architectural_landmark",
    "setting_environment",
    "A recognizable architectural landmark — historic building, iconic modern structure, heritage site, or significant public space — used as backdrop or setting. The landmark carries place-identity and cultural significance beyond the brand's own assets.",
    ["f_and_b", "retail"], 10,
    "The landmark is clearly visible and identifiable (not merely hinted). Product or talent in foreground against the landmark. Photography must respect the landmark's scale and significance — never miniaturize an important site to serve product placement. Appropriate permits may be required. Best used for national occasions, brand milestone posts, or Vision 2030 content.",
    "Architectural landmarks transfer their cultural authority to the brand positioned before them. A brand photographed against Diriyah, Al-Ula, or a recognizable Riyadh skyline is claiming to be part of the Saudi story at that location's scale. Strong signal for national and heritage occasions.",
    ["Permits required for commercial filming at most Saudi heritage and public sites.",
     "Must not diminish the significance of the landmark by making it a mere backdrop for a product promotion.",
     "Location-specific content limits reach to audiences who recognize the landmark — consider regional resonance."],
    ["all"], "1.2x-1.6x",
    ["Heritage site photography must comply with SCTH (Saudi Commission for Tourism and National Heritage) regulations."]
))

written.append(pat(
    "01KSB9Y1W8N4CD3REVA6HTQ11Q",
    "Ramadan Decorated Night",
    "ramadan_decorated_night",
    "setting_environment",
    "An evening or nighttime setting decorated with Ramadan and Eid visual elements — lanterns, crescent moon motifs, star patterns, Islamic geometric lights, twinkling strings — creating the distinctive visual vocabulary of the holy month.",
    ["f_and_b", "retail", "beauty"], 16,
    "Setting: evening exterior or interior with Ramadan decorations (fanous lanterns, star-and-crescent motifs, string lights in warm amber/gold). Atmosphere is warm, intimate, and celebratory. Low ambient light with warm practicals. Product positioned in the decorated environment. Color palette: Ramadan gold purple dominant.",
    "Ramadan-decorated settings are an instant occasion signal — the audience immediately contextualizes the brand within the holy month. For F&B brands especially, the decorated setting signals that the brand is a fitting companion for the Ramadan evening ritual (iftar, suhoor, Ramadan nights). High recall value due to the emotional significance of the occasion.",
    ["Highly seasonal — this setting outside of Ramadan/Eid window creates confused messaging.",
     "Decorative Ramadan elements must be used respectfully — not in combination with product categories that conflict with the occasion (alcohol-adjacent, frivolous).",
     "The crescent-and-star motif is a powerful Islamic symbol — treat with visual respect."],
    ["all"], "1.4x-1.8x",
    ["Ramadan visual symbols must not be combined with any content that could be seen as disrespectful to the holy month."]
))

# ══════════════════════════════════════════════════════════
# PART 2e — HOSPITALITY INTENSITY (7 patterns)
# ══════════════════════════════════════════════════════════

written.append(pat(
    "01KSB9Y1W80RJSQC4GD6WBNZ5Y",
    "Zero Hospitality (Product Only)",
    "zero_hospitality",
    "hospitality_intensity",
    "Content with no hospitality cues — no service gesture, no cultural object, no abundance signal, no relational warmth. Pure product presentation in a neutral context. The hospitality score is zero. This is the lowest-intensity cultural positioning and the highest commercial signal.",
    ["f_and_b", "beauty", "retail"], 20,
    "Visual: product on neutral background or in clinical context. No dallah, no dates, no gathering, no service gesture. Copy: product name + attribute + CTA. No warmth language. This is price_offer_graphic and product_hero territory at its most stripped-down.",
    "Zero hospitality content functions as conversion tool for audiences already in buying mode. It has the lowest cultural engagement but the highest click-to-order efficiency. Should represent a minority of brand content (20% or less) — when overused, it signals a brand with no cultural identity. Useful for e-commerce performance campaigns.",
    ["Overuse destroys brand warmth — Saudi audiences bond with brands that show hospitality values.",
     "Brands in inherently hospitality-coded sectors (F&B, heritage retail) suffer more reputational cost from zero-hospitality content than neutral sectors.",
     "Should be clearly separated in content planning from cultural/hospitality content to avoid tonal inconsistency."],
    ["all"], "1.0x-1.2x",
    []
))

written.append(pat(
    "01KSB9Y1W8GADQCX02XDJ4XBBW",
    "Light Hospitality (Single Cue)",
    "light_hospitality_single",
    "hospitality_intensity",
    "Content with exactly one hospitality cue — a single hand gesture, one cultural object in frame, or one ambient warmth element. Product is still primary but the brand signals cultural awareness through a single deliberate cue.",
    ["f_and_b", "beauty", "retail"], 40,
    "One hospitality cue intentionally placed: either a hand presenting the product (gesture cue), a single dallah or cultural object visible in frame (object cue), or a warm-lit setting element that implies hospitality without a full environment (ambient cue). Product remains the visual hero. Copy may or may not reference the cue explicitly.",
    "Light hospitality is the most common pattern in the corpus — it sits at the practical production intersection of cultural awareness and commercial efficiency. One cue is enough to signal 'we understand your culture' without requiring a full majlis set or multi-prop production. Scalable for weekly content calendars.",
    ["Single cue must be genuinely cultural — a generic 'hand holding product' without cultural specificity is not hospitality signaling.",
     "The cue should reinforce the product positioning, not contradict it (a bukhoor burner next to a modern tech product is jarring).",
     "Light hospitality alone does not build the brand depth that medium or high hospitality creates — must be mixed with higher-intensity content."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W824VHDRAT5EV2JG93",
    "Medium Hospitality (Ambient)",
    "medium_hospitality_ambient",
    "hospitality_intensity",
    "Content with 2-3 hospitality cues creating an ambient warmth — a combination of setting warmth + service gesture + one cultural object, or a table setting with multiple food items implying abundance. Product is integrated into a warm hospitality environment.",
    ["f_and_b", "retail"], 55,
    "Environment reads warm without being specifically majlis-coded. Examples: a café interior (warm setting cue) with a coffee being poured (gesture cue) and dates on the side (food abundance cue). Or: a product presented in a warm-toned setting with textured props. The combination creates a hospitality atmosphere that feels real without requiring a full heritage production.",
    "Medium hospitality is the highest-frequency hospitality tier in the corpus — it balances cultural warmth with production practicality. It feels welcoming without demanding a complete heritage experience. Highest co-occurrence with lifestyle_environment_integration and amber_hospitality_light. Strong signal for brand cultural alignment.",
    ["The combination of cues must be coherent — random props that don't relate to each other or the product break the ambient warmth.",
     "Cues must be appropriate to the sector — F&B hospitality cues (dallah, dates) feel forced in beauty or retail contexts."],
    ["all"], "1.3x-1.7x",
    []
))

written.append(pat(
    "01KSB9Y1W8CM95AYDY9QBMHXT0",
    "High Hospitality (Majlis Dense)",
    "high_hospitality_majlis_dense",
    "hospitality_intensity",
    "Content with 4+ hospitality cues creating a full Saudi hospitality environment — dallah + cushion seating + multi-person gathering + table spread + warm lighting + service gesture. Every element of the frame reinforces كرم الضيافة.",
    ["f_and_b"], 18,
    "Full majlis or iftar table setting. Multiple food items creating abundance. Dallah and finjan visible and in use. Characters (2-5) gathered in genuine social warmth. Warm lighting (lanterns, practical amber). Cultural objects in foreground and background. Copy in warm hospitality register. This is the highest production-cost content type but also the highest cultural engagement.",
    "High hospitality is the peak expression of Saudi brand cultural identity — every element of the frame says 'we are a Saudi brand that honors كرم الضيافة.' This content type earns the deepest brand loyalty and generates the highest share and comment engagement. Highest co-occurrence with family_majlis_hierarchical, overhead_tabletop_spread, and ramadan_decorated_night.",
    ["Requires significant production investment — a poorly executed high-hospitality attempt with cheap props scores worse than light hospitality.",
     "Must be authentic — culturally incorrect prop usage or wrong occasion context destroys the signal.",
     "Frequency: high hospitality content should appear at key occasions (Ramadan, Eid, National Day) — weekly use dilutes its significance."],
    ["all"], "1.6x-2.0x",
    [], "sector:f_and_b"
))

written.append(pat(
    "01KSB9Y1W8AS4PEY4RA3GCV1X2",
    "Service-First Hospitality",
    "service_first_hospitality",
    "hospitality_intensity",
    "Hospitality cues centered on the act of service — the gesture of presenting, pouring, or offering the product is the primary hospitality signal. Whether light, medium, or high intensity, the service action is the dominant cue.",
    ["f_and_b", "beauty"], 28,
    "The service gesture is the visual hero: a hand presenting a coffee cup, a server placing a dish, a barista pulling espresso, a beauty advisor presenting a product. The service action is captured mid-motion for energy. Right hand always. Eye contact between server and camera or between server and recipient. Background setting secondary to the service moment.",
    "Service-focused hospitality communicates brand care and attentiveness — the brand's people are actively giving, not just displaying. In the Saudi cultural frame, service is an act of respect and generosity. Strongest engagement in F&B where the serving gesture is expected and valued. High co-occurrence with hand_in_motion_pour_or_place and uniform_role_coded.",
    ["Left hand rule: serving gesture must use right hand (hard block in Saudi cultural compliance).",
     "Service gesture must look natural — a forced or awkward presentation is worse than no gesture.",
     "Recipient of service: if shown, must be in appropriate proximity (no cross-gender physical contact)."],
    ["all"], "1.3x-1.7x",
    ["Right hand must be used for all presenting/serving gestures — left hand is a hard compliance block."],
    "sector:f_and_b+sector:beauty"
))

written.append(pat(
    "01KSB9Y1W8DE0TSXZAGQFSJ7DK",
    "Abundance Signaling Hospitality",
    "abundance_signaling_hospitality",
    "hospitality_intensity",
    "Hospitality cues centered on visual abundance — multiple dishes, overflowing plates, a fully laden table, stacked products, or a generous spread that signals generosity and plenty. The quantity of food/product is the primary hospitality signal.",
    ["f_and_b", "retail"], 30,
    "Table or surface laden with multiple items — food dishes, product variety, gift boxes. The frame communicates 'more than enough' — no empty space at the table. Overhead tabletop spread is the most common composition. Warm tones. Sometimes characters present at the table. Key phrase: 'الكرم يبدأ من هنا' or similar abundance language.",
    "Abundance is a core Saudi hospitality value — 'السخاء والكرم' is a cultural virtue. A brand that shows a table overflowing with food signals that it embodies this virtue. Particularly powerful during Ramadan and Eid when communal feasting is the central social ritual. Strong co-occurrence with overhead_tabletop_spread and family_majlis_hierarchical.",
    ["Abundance must look genuinely generous, not wasteful — Islamic values around not wasting food are relevant.",
     "Products must all be visible and identifiable even within abundance styling — hidden products waste production investment.",
     "Scales well with occasion content (Ramadan table spread) but can look excessive for everyday product content."],
    ["all"], "1.4x-1.8x",
    []
))

written.append(pat(
    "01KSB9Y1W84AHEBMXE5YEHND3T",
    "Relational Hospitality",
    "relational_hospitality",
    "hospitality_intensity",
    "Hospitality cues centered on human connection — eye contact, warm smiles, shared moments, and gestures of social belonging. The relationship between people (not the service or abundance) is the hospitality signal.",
    ["f_and_b", "retail", "beauty"], 26,
    "Characters in genuine social connection: looking at each other, laughing together, sharing a moment over a product. Product is the occasion for connection, not the subject. Warmth is conveyed through genuine expression rather than cultural object or service gesture. Settings can be modern or heritage — the human connection transcends setting.",
    "Relational hospitality is the most universally transferable hospitality type — it works across all sectors and all heritage-modern positions. It says 'our brand is the occasion for human warmth' which is simultaneously cultural (Saudi social values) and universal (human connection). Strong for brands building emotional loyalty rather than transactional repeat purchase.",
    ["Requires genuinely warm character dynamics — forced or posed 'happy people' reads as advertising and lowers authenticity score.",
     "Cross-gender relational content: must observe appropriate distance and context — non-mahram proximity is a compliance risk.",
     "The product must earn its place as the occasion for connection — gratuitous product placement in relational content feels forced."],
    ["all"], "1.3x-1.7x",
    ["Mixed-gender scenes must observe appropriate distance between non-mahram characters."]
))

# ══════════════════════════════════════════════════════════
# PART 2f — CAPTION STRUCTURE (8 patterns)
# ══════════════════════════════════════════════════════════

written.append(pat(
    "01KSB9Y1W8NSDANQ8D1PBKT8CT",
    "One-Liner Hook",
    "one_liner_hook",
    "caption_structure",
    "A single-sentence caption that leads with the brand's core message, emotional hook, or product truth — then stops. No elaboration, no secondary copy, no long CTA. The brevity is the confidence signal.",
    ["f_and_b", "beauty", "retail"], 28,
    "Caption: one sentence (8-20 words). Must be punchy, specific, and either emotionally resonant or surprisingly specific. Arabic preferred for Saudi audience. Examples: 'الضيف عندنا دايم كبير' | 'صنعناها عشانك' | 'أحلى لحظاتك تبدأ هنا'. CTA is embedded in the sentence or entirely absent (the visual carries the conversion). No hashtags or minimal branded hashtag only.",
    "Short captions consistently outperform long captions for initial scroll-stop and save rates. The one-liner signals brand confidence — 'we don't need to explain ourselves.' Works best for brands with established identity where the visual does the heavy lifting. High co-occurrence with cultural_object_hero and lifestyle_environment_integration.",
    ["Requires a strong visual to compensate for the absent copy explanation — the image must be self-sufficient.",
     "One-liner must be genuinely memorable — a mediocre one-liner is worse than a solid longer caption.",
     "Does not work well for educational or complex product content where context is required."],
    ["all"], "1.3x-1.7x",
    []
))

written.append(pat(
    "01KSB9Y1W8AV410W4FSD8T7WA7",
    "Story Arc Caption",
    "story_arc_caption",
    "caption_structure",
    "A caption structured as a mini-narrative: opening (situation/moment) → development (emotion/tension) → resolution (product/brand) → optional CTA. 3-6 sentences. Reads like the opening of a short story.",
    ["f_and_b", "beauty", "retail"], 22,
    "Structure: [Setting the scene in 1 sentence] → [The feeling/need/moment in 1-2 sentences] → [Product as the resolution in 1 sentence] → [Optional CTA]. Arabic register: warm colloquial Najdi or semi-formal. Examples: 'المساء تمشي على إيقاعه الهادئ... والقهوة تلوّن اللحظة... كوّن لحظتك اليوم.' The arc should feel like a breath taken and released.",
    "Narrative structure is one of the most powerful engagement mechanisms in written communication. A story arc caption gives the audience a complete emotional journey in 30-60 words. Highest word-for-word engagement among caption types for brand-building content. Co-occurs strongly with heritage_storytelling_hook and lifestyle_environment_integration.",
    ["Requires genuine craft — a poorly written story arc reads as pretentious or confused.",
     "Length must be appropriate to the visual — a heavy story arc caption on a simple product image is tonal mismatch.",
     "Arabic story arc copy requires native-level language skill — AI-generated Arabic narrative usually fails at emotional resonance."],
    ["all"], "1.4x-1.8x",
    []
))

written.append(pat(
    "01KSB9Y1W86Q700KPZZQE90CSC",
    "Question CTA",
    "question_cta",
    "caption_structure",
    "A caption that opens or closes with a direct question to the audience — inviting comment, opinion, or preference share. The question is the primary engagement mechanic. Works as a light poll without formal poll mechanics.",
    ["f_and_b", "retail", "beauty"], 18,
    "Caption includes an open or closed question directed at the audience: 'ما أكثر وقت تحبوا القهوة فيه؟' | 'وش تفضلون، الحار أو البارد؟' | 'شيروا علينا رأيكم 👇'. Question appears at caption end (most common) or as the caption opener for high-energy engagement. Arabic colloquial register. Emoji as punctuation is optional but common.",
    "Questions are the single most reliable comment-generation mechanic on Instagram. A genuine question that invites opinion (not just 'comment below') signals that the brand actually wants to hear from its audience — building community relationship. Average question-based captions generate 2-3x the comments of non-question captions in the corpus.",
    ["Question must be genuinely interesting to the audience — trivial questions generate hollow engagement.",
     "Brand must respond to top comments — asking a question and ignoring answers destroys the community signal.",
     "Closed questions (A or B) generate faster responses but limit insight; open questions generate richer data but require more effort from the audience."],
    ["all"], "1.3x-1.6x",
    []
))

written.append(pat(
    "01KSB9Y1W8A39APP66WQ3QCWGN",
    "Pure Witness (No CTA)",
    "pure_witness_no_cta",
    "caption_structure",
    "A caption that makes no ask of the audience — ambient, poetic, or observational copy that invites the audience to simply feel something. No CTA, no product pitch, no comment prompt. The brand is present but not selling.",
    ["f_and_b", "beauty"], 14,
    "Caption: 2-4 lines of evocative Arabic language that creates a mood or image rather than makes a point. May be a fragment of poetry, a sensory observation, or a brief cultural reflection. No 'اطلب الآن', no 'احجز', no question. Just presence. Register: poetic semi-formal or classical Arabic warmth. Examples: 'كل فنجان حكاية...' | 'اللقاءات الصغيرة هي الأعظم'.",
    "No-CTA content is counterintuitively powerful for brand-building. It signals brand confidence ('we don't need to sell you every post') and creates emotional deposits that make future CTAs more effective. Saudi audiences respond strongly to poetic Arabic copy — it signals cultural sophistication and heritage. High co-occurrence with cultural_object_hero and golden_hour_hero.",
    ["Requires strong visual to carry the post — ambient caption + weak visual produces nothing.",
     "Should not dominate the content mix — regular commercial asks are still necessary.",
     "Arabic poetic register requires genuine language skill — inauthentic 'poetic' copy produces cringe."],
    ["all"], "1.3x-1.7x",
    [], "sector:f_and_b+sector:beauty"
))

written.append(pat(
    "01KSB9Y1W8ZWND9MRE2ZBRT08N",
    "List / Educational Caption",
    "list_educational",
    "caption_structure",
    "A structured caption using a numbered list, bullet points, or 'reason N' format to deliver educational, advisory, or feature content. The list structure signals organization, expertise, and content generosity.",
    ["beauty", "f_and_b", "retail"], 16,
    "Caption structure: [Hook line] + [3-7 numbered or bulleted points] + [CTA or closing line]. Each point is short (5-12 words). Arabic or bilingual (Arabic header, English values). Examples: '3 أسباب تخلي البن السعودي مختلف:' followed by three differentiated points. The list format creates visual rhythm in the caption even before the audience reads each point.",
    "Lists are high-save content — audiences bookmark structured educational content for future reference. In the beauty and F&B categories, ingredient lists, preparation tips, and usage guides generate strong 'saves' metric which the Instagram algorithm values. High co-occurrence with educational_explainer content type.",
    ["Points must be genuinely informative — padding a list with obvious or generic points reduces credibility.",
     "Lists work poorly with emotional/heritage content — the structure is too clinical for warm storytelling.",
     "Arabic numbered lists require correct Arabic numerals and right-to-left flow management."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8MKNPS1TBPH7MEP05",
    "Emoji-Dense Playful",
    "emoji_dense_playful",
    "caption_structure",
    "A caption with high emoji-to-text ratio — emojis used as punctuation, sentence breaks, and emotional amplifiers. Signals casual, playful, and approachable brand personality. Youth and contemporary-skewing brand voice.",
    ["f_and_b", "retail"], 14,
    "Caption: short text with emoji integrated throughout, not just at the end. 1 emoji per 3-5 words minimum. Text is colloquial, light, and quick. Arabic preferred. Examples: '🍕 بيتزا تتطلع فيك 👀 وانت تنظر فيها 😍 لطلبك اضغط في البايو ☝️'. No formal language, no heritage register. Hashtags may appear at end.",
    "Emoji-rich captions signal brand accessibility and casual personality — 'we're not a formal institution, we're your friendly brand.' Works strongly for youth-oriented F&B and fast fashion retail. Generates reactions and shares among younger Saudi demographics (18-28). Highest comment count among caption types for casual purchase content.",
    ["Completely incompatible with heritage, formal, or premium brand positioning.",
     "Overuse creates brand personality fatigue — needs variety.",
     "Emoji meaning can be culture-specific — some emoji carry unintended connotations in Arabic contexts."],
    ["all"], "1.2x-1.5x",
    []
))

written.append(pat(
    "01KSB9Y1W8SKZV45ABKZS1TC4T",
    "Formal Dignified",
    "formal_dignified",
    "caption_structure",
    "A caption written in formal or semi-formal Modern Standard Arabic — no colloquial, no emoji, complete sentences, correct grammar. Signals institutional authority, national pride, or premium positioning.",
    ["f_and_b", "retail", "beauty"], 12,
    "Caption: full Arabic sentences in formal register. No emoji. Correct grammar and spelling (including tashkeel if appropriate). Vocabulary: elevated, precise, dignified. Register appropriate for official announcements, national occasion greetings, award acknowledgments, or brand values statements. Length: 2-5 sentences. Often closes with formal brand statement rather than CTA.",
    "Formal Arabic copy signals that the brand takes the occasion or message seriously — it elevates the post above commercial content. Saudi audiences respond strongly to formal Arabic for national occasions, religious moments, and institutional announcements. Co-occurs with saudi_flag_palette, national_day_pride, and occasion_specific_greeting.",
    ["Formal Arabic must be grammatically correct — errors in formal register are more jarring than errors in colloquial (experts notice).",
     "Formal tone is incompatible with playful or casual content types.",
     "Avoid over-formalizing routine content — reserve formal register for occasions that warrant it."],
    ["all"], "1.2x-1.6x",
    []
))

written.append(pat(
    "01KSB9Y1W8SQX4SXM1W3VNYF3Y",
    "Hashtag Discovery Heavy",
    "hashtag_discovery_heavy",
    "caption_structure",
    "A caption optimized for Instagram discoverability — featuring 5 or more branded, category, and occasion hashtags appended after the main copy. The hashtags extend reach to non-following audiences through hashtag search and explore page.",
    ["f_and_b", "retail", "beauty"], 18,
    "Main caption copy (1-4 lines) followed by line break and 5-15 hashtags in a structured cluster. Hashtag mix: brand-specific (e.g., #barnscoffee), category (e.g., #قهوة #coffee), occasion (e.g., #رمضان #رمضان2026), location (e.g., #الرياض #السعودية), and trending cultural tag if relevant. Arabic and English hashtags mixed for bilingual reach.",
    "Hashtag-optimized captions sacrifice brand polish for reach — the hashtag cluster is visually unelegant but algorithmically effective for accounts trying to grow beyond their current follower base. Most effective during high-search occasions (Ramadan, National Day) when audience search behavior spikes.",
    ["High hashtag count can look visually cluttered — separate from main copy with line break.",
     "Hashtags must be genuinely relevant — irrelevant hashtag stuffing reduces post quality score.",
     "Effectiveness is declining as Instagram shifts to AI-based discovery over hashtag search — verify with current platform data."],
    ["all"], "1.1x-1.4x",
    []
))

# ══════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════

print(f"Written {len(written)} pattern files:")
for s in written:
    print(f"  {s}")
