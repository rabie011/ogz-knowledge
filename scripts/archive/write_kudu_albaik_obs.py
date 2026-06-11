#!/usr/bin/env python3
"""Write 15 @kuduksa and 15 @albaik observation JSONs from API-collected post data."""
import json, random, time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OBS_DIR = REPO / "11_who_to_learn_from" / "observations" / "f_and_b"
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_offset = 0

def make_ulid():
    global _offset
    t = int(time.time() * 1000) + _offset; _offset += 1
    t_part = ""; v = t
    for _ in range(10): t_part = CROCKFORD[v & 0x1F] + t_part; v >>= 5
    r = random.getrandbits(80); r_part = ""
    for _ in range(16): r_part = CROCKFORD[r & 0x1F] + r_part; r >>= 5
    return t_part + r_part

NOW = datetime.now(timezone.utc).isoformat()

# ── KUDU (@kuduksa) ──────────────────────────────────────────────────────────

KUDU_POSTS = [
    {
        "shortcode": "DYmaOm-CRmG", "capture_date": "2026-05-21",
        "content_type": "video", "likes": 383,
        "caption": "العيد يكمل مع وجبة اللحم من كودو 😋🔥 طعم غني ومع شباب البومب، أجواء العيد تصير أحلى",
        "visual": {
            "composition_style": "event collab — Eid meat meal with Bomba Youth influencer group",
            "lighting": "warm vibrant, festive",
            "color_palette_dominant": ["red", "gold", "brown", "white"],
            "props_visible": ["Kudu lamb/meat meal box", "Bomba Youth branding", "Eid decorative elements"],
            "setting": "festive Eid setting, celebratory atmosphere",
            "characters_visible": {"count": 3},
            "text_overlays": [
                {"language": "arabic", "content_summary": "العيد يكمل مع وجبة اللحم — Eid is complete with Kudu meat meal"},
                {"language": "bilingual", "content_summary": "Kudu x Bomba Youth co-branding"}
            ],
            "notable_visual_elements": ["Eid occasion + influencer collab (Bomba Youth)", "meat meal emphasises Eid lamb tradition"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "celebratory",
                  "notable_phrases": ["العيد يكمل مع وجبة اللحم", "أجواء العيد تصير أحلى"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Eid Al-Adha / Eid season",
            "hospitality_cues": ["meat meal — Eid sacrifice tradition"],
            "heritage_vs_modern": "blended",
            "free_notes": "Meat meal for Eid ties to qurbani/sacrifice tradition. Bomba Youth collab targets Saudi Gen-Z. 383 likes is decent for Eid occasion content."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Eid occasion hook with relevant product (meat meal = qurbani resonance)"},
            {"pattern_slug": "collab_campaign_reveal", "confidence": "strong", "notes": "Bomba Youth influencer group collab"}
        ]
    },
    {
        "shortcode": "DYkgJQmEdqZ", "capture_date": "2026-05-20",
        "content_type": "video", "likes": 87,
        "caption": "جاي من الدوام؟ طالع مشوار؟ 🚙 خلّ وجبتك أوفر مع وجبة كودو دجاج بالحجم الكبير",
        "visual": {
            "composition_style": "lifestyle moment — commuter grabbing a meal on the go",
            "lighting": "natural daylight, outdoor/car setting",
            "color_palette_dominant": ["red", "white", "grey", "yellow"],
            "props_visible": ["Kudu chicken meal large size", "car interior", "branded packaging"],
            "setting": "drive-through / car setting, on-the-go lifestyle",
            "characters_visible": {"count": 1},
            "text_overlays": [
                {"language": "arabic", "content_summary": "جاي من الدوام؟ طالع مشوار؟ — Coming from work? Going out? Value meal offer"}
            ],
            "notable_visual_elements": ["commuter lifestyle positioning", "drive-through Saudi car culture", "value offer integrated into relatable moment"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "relatable",
                  "notable_phrases": ["جاي من الدوام؟ طالع مشوار؟", "وجبتك أوفر"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Saudi car culture: 'دوام' (work hours), 'مشوار' (errand) are everyday Saudi vernacular. Drive-through is a dominant consumption context in Riyadh. Value messaging embedded in relatable daily narrative."
        },
        "patterns": [
            {"pattern_slug": "lifestyle_embed", "confidence": "strong", "notes": "Commuter lifestyle moment — product embedded in daily routine narrative"},
            {"pattern_slug": "price_offer_graphic", "confidence": "moderate", "notes": "Value deal integrated into narrative, not standalone graphic"}
        ]
    },
    {
        "shortcode": "DYj0KFPjb5h", "capture_date": "2026-05-20",
        "content_type": "carousel", "likes": 149,
        "caption": "رحلة بدأت بالشغف… ووصلت إلى منصة عالمية 🌍✨ نبارك للمياء الزبيدي حصولها على الميدالية الفضية",
        "visual": {
            "composition_style": "employee pride story — achievement carousel with photos",
            "lighting": "varied — event + portrait photography",
            "color_palette_dominant": ["red", "gold", "white", "navy"],
            "props_visible": ["WorldSkills Malaysia 2026 medal", "Kudu uniform/branding", "competition stage"],
            "setting": "international competition stage, Kudu branded materials",
            "characters_visible": {"count": 2},
            "text_overlays": [
                {"language": "arabic", "content_summary": "رحلة بدأت بالشغف — journey that started with passion, WorldSkills silver medal celebration"},
                {"language": "bilingual", "content_summary": "WorldSkills + Kudu branding"}
            ],
            "notable_visual_elements": ["employee story as brand content — people-first strategy", "international achievement elevates brand pride", "silver medal = Saudi talent on world stage"]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "proud",
                  "notable_phrases": ["رحلة بدأت بالشغف", "منصة عالمية"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "WorldSkills 2026 Malaysia",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Employee achievement content is a key Kudu brand pillar — aligns with Saudi Vision 2030 youth empowerment narrative. Publishing employee success on brand account builds culture-brand identity."
        },
        "patterns": [
            {"pattern_slug": "employee_pride_story", "confidence": "strong", "notes": "Employee international achievement used as brand storytelling"},
            {"pattern_slug": "vision_2030_alignment", "confidence": "moderate", "notes": "Saudi youth talent development narrative resonates with V2030 messaging"}
        ]
    },
    {
        "shortcode": "DYjxFTiFhpt", "capture_date": "2026-05-20",
        "content_type": "image", "likes": 43,
        "caption": "خلّوا الإجازة ألذ مع كودو 🍦✨ اطلبوا وجبة أطفال وخذوا آيس كريم مجاني للصغار",
        "visual": {
            "composition_style": "product offer — kids meal with free ice cream add-on graphic",
            "lighting": "bright, colorful, child-friendly",
            "color_palette_dominant": ["red", "white", "pink", "yellow"],
            "props_visible": ["kids meal box", "ice cream cone", "free badge graphic", "Kudu branding"],
            "setting": "branded graphic background",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "خلّوا الإجازة ألذ — make the holiday sweeter, kids meal + free ice cream offer"}
            ],
            "notable_visual_elements": ["holiday season kids offer", "free add-on as purchase incentive", "ice cream = child delight trigger"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "playful",
                  "notable_phrases": ["خلّوا الإجازة ألذ", "مجاني للصغار"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "school holiday season",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Kids meals are a family dining pillar in Saudi. School holiday period = high family dining opportunity. Free ice cream drives family visit decision."
        },
        "patterns": [
            {"pattern_slug": "price_offer_graphic", "confidence": "strong", "notes": "Free ice cream add-on offer for kids meal"},
            {"pattern_slug": "occasion_peg", "confidence": "moderate", "notes": "School holiday season hook"}
        ]
    },
    {
        "shortcode": "DYiCr1yufpQ", "capture_date": "2026-05-19",
        "content_type": "video", "likes": 216,
        "caption": "من كودو إلى ماليزيا 🇲🇾✨ نفخر اليوم بلمياء الزبيدي، إحدى أفراد فريق كودو",
        "visual": {
            "composition_style": "employee pride video — journey from Kudu to international stage",
            "lighting": "warm narrative, mixed indoor/event lighting",
            "color_palette_dominant": ["red", "white", "gold"],
            "props_visible": ["Kudu uniform", "Malaysia setting", "WorldSkills competition elements"],
            "setting": "from Kudu kitchen to international competition stage",
            "characters_visible": {"count": 1},
            "text_overlays": [
                {"language": "arabic", "content_summary": "من كودو إلى ماليزيا — from Kudu to Malaysia, employee success story video"}
            ],
            "notable_visual_elements": ["narrative arc: local job → world stage", "Saudi female employee achievement", "brand as launchpad for talent"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "proud",
                  "notable_phrases": ["من كودو إلى ماليزيا", "نفخر اليوم"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "WorldSkills 2026 Malaysia",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Second post about same employee suggests a planned campaign. Saudi female employee on world stage resonates with Vision 2030 women empowerment narrative. Brand positions itself as employer that develops talent."
        },
        "patterns": [
            {"pattern_slug": "employee_pride_story", "confidence": "strong", "notes": "Video format of Lamia Al-Zubaidi's journey — companion to carousel post"},
            {"pattern_slug": "vision_2030_alignment", "confidence": "strong", "notes": "Saudi female talent, international stage, youth empowerment theme"}
        ]
    },
    {
        "shortcode": "DYhT7MwFnty", "capture_date": "2026-05-19",
        "content_type": "carousel", "likes": 50,
        "caption": "صباحك يستاهل بداية تضبط مزاجك ☀️ ابدأ يومك بفطور كودو اللي على كيفك",
        "visual": {
            "composition_style": "menu showcase carousel — breakfast options grid",
            "lighting": "bright morning, warm white",
            "color_palette_dominant": ["warm white", "red", "brown", "yellow"],
            "props_visible": ["multiple breakfast dishes", "coffee cups", "egg dishes", "sandwiches", "Kudu branded trays"],
            "setting": "bright cafe/table setting, morning ambiance",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "صباحك يستاهل — your morning deserves it, breakfast menu reveal"}
            ],
            "notable_visual_elements": ["carousel format shows menu breadth", "morning light aesthetic", "variety = choice positioning for breakfast segment"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "warm",
                  "notable_phrases": ["صباحك يستاهل", "على كيفك"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["breakfast spread", "qahwa adjacent"],
            "heritage_vs_modern": "modern",
            "free_notes": "Kudu is running a sustained breakfast campaign. 'على كيفك' (your way/at your pace) is a strong Saudi localisation of the breakfast-on-demand concept. Carousel format ideal for menu browsing."
        },
        "patterns": [
            {"pattern_slug": "product_hero", "confidence": "moderate", "notes": "Carousel menu showcase — multiple product heroes in sequence"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "moderate", "notes": "Breakfast spread with coffee — morning hospitality positioning"}
        ]
    },
    {
        "shortcode": "DYfCLAsDDGi", "capture_date": "2026-05-18",
        "content_type": "video", "likes": 74,
        "caption": "وجبتهم المفضلة… ومعها لعبة يحبونها أكثر! 🍔🌀 مع كل وجبة أطفال من كودو، سبينر يضيف لهم لحظات مميزة",
        "visual": {
            "composition_style": "kids product demo — spinner toy with kids meal action video",
            "lighting": "bright, playful",
            "color_palette_dominant": ["red", "yellow", "blue", "white"],
            "props_visible": ["kids meal box", "spinner toy", "child hands playing with spinner"],
            "setting": "table / home setting, child-friendly",
            "characters_visible": {"count": 1},
            "text_overlays": [
                {"language": "arabic", "content_summary": "سبينر يضيف لهم لحظات مميزة — spinner adds special moments, kids meal + toy"}
            ],
            "notable_visual_elements": ["toy demo video — engagement through play", "spinner = trending toy mechanic", "child interaction = emotional parent trigger"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "playful",
                  "notable_phrases": ["وجبتهم المفضلة", "لعبة يحبونها أكثر"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Spinner toys were trending in Saudi in 2026. Kudu riding the trend to drive kids meal sales. Parents decide, kids demand — toy mechanic targets child influence on family dining decision."
        },
        "patterns": [
            {"pattern_slug": "product_bundle_offer", "confidence": "strong", "notes": "Meal + trending toy bundle — drives kids meal demand"},
            {"pattern_slug": "trend_riding", "confidence": "strong", "notes": "Spinner toy riding trending fidget/spinner toy wave"}
        ]
    },
    {
        "shortcode": "DYecnZXlYSu", "capture_date": "2026-05-18",
        "content_type": "video", "likes": 172,
        "caption": "ما تدرون وش تاكلون على الفطور؟ 😋 ما فيه ألذ من فطور كودو 🤍",
        "visual": {
            "composition_style": "problem-solution video — breakfast indecision → Kudu breakfast solution",
            "lighting": "warm morning",
            "color_palette_dominant": ["warm white", "red", "brown"],
            "props_visible": ["Kudu breakfast spread", "coffee", "breakfast sandwich", "branded packaging"],
            "setting": "morning kitchen/dining setting",
            "characters_visible": {"count": 1},
            "text_overlays": [
                {"language": "arabic", "content_summary": "ما تدرون وش تاكلون؟ — don't know what to eat? Kudu breakfast is the answer"}
            ],
            "notable_visual_elements": ["relatability hook — breakfast indecision", "problem framing in copy before product solution", "warm morning palette"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "warm",
                  "notable_phrases": ["ما تدرون وش تاكلون على الفطور؟", "ما فيه ألذ من فطور كودو"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["breakfast = family/morning gathering"],
            "heritage_vs_modern": "modern",
            "free_notes": "Problem-solution format with colloquial Najdi hook. 'ما تدرون وش تاكلون' is very natural Riyadhi vernacular. Kudu's breakfast campaign uses multiple relatable 'morning problem' hooks."
        },
        "patterns": [
            {"pattern_slug": "problem_solution_hook", "confidence": "strong", "notes": "Breakfast indecision as relatable problem, Kudu as easy solution"},
            {"pattern_slug": "lifestyle_embed", "confidence": "strong", "notes": "Product embedded in morning routine narrative"}
        ]
    },
    {
        "shortcode": "DYc_szXAdDc", "capture_date": "2026-05-17",
        "content_type": "video", "likes": 76,
        "caption": "بداية اليوم تصير الذ لما تكون على كيفك ☀️ وفطور كودو يعطيك خيارات تناسب صباحك",
        "visual": {
            "composition_style": "morning routine video — customised breakfast choice",
            "lighting": "warm morning, natural light",
            "color_palette_dominant": ["warm white", "red", "gold"],
            "props_visible": ["multiple breakfast options", "Kudu branded cups", "pastry items"],
            "setting": "morning table setting, relaxed domestic",
            "characters_visible": {"count": 1},
            "text_overlays": [
                {"language": "arabic", "content_summary": "بداية اليوم تصير الذ على كيفك — the day starts better your way, breakfast options CTA"}
            ],
            "notable_visual_elements": ["'على كيفك' (your way) personalisation positioning", "choice/variety as key breakfast message", "third video in breakfast campaign — consistent messaging"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "warm",
                  "notable_phrases": ["على كيفك", "خيارات تناسب صباحك"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["morning food gathering"],
            "heritage_vs_modern": "modern",
            "free_notes": "'على كيفك' is a powerful Saudi localisation — personal choice/pace is culturally resonant. This is the 3rd breakfast video in the sequence, showing Kudu's sustained breakfast campaign strategy."
        },
        "patterns": [
            {"pattern_slug": "lifestyle_embed", "confidence": "strong", "notes": "Morning personalisation narrative — your breakfast, your way"},
            {"pattern_slug": "product_hero", "confidence": "moderate", "notes": "Breakfast items shown as choice range"}
        ]
    },
    {
        "shortcode": "DYbeNxLIh7r", "capture_date": "2026-05-17",
        "content_type": "video", "likes": 44,
        "caption": "صباحات كودو غير 😋☀️ خصوصًا لما فطورك يعطيك دبل النقاط على كل طلب 🔥✨",
        "visual": {
            "composition_style": "loyalty program activation — double points with breakfast",
            "lighting": "bright, energetic morning",
            "color_palette_dominant": ["red", "gold", "white"],
            "props_visible": ["Kudu breakfast items", "double points badge", "loyalty points graphic"],
            "setting": "branded promotional, morning context",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "دبل النقاط على كل طلب — double loyalty points on every breakfast order"}
            ],
            "notable_visual_elements": ["loyalty program as breakfast incentive", "double points gamification", "4th breakfast content piece — campaign depth"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "energetic",
                  "notable_phrases": ["صباحات كودو غير", "دبل النقاط"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Loyalty program (نقاط) is a major engagement driver in Saudi F&B. Kudu leverages breakfast as a loyalty point accelerator — drives daily visit habit formation."
        },
        "patterns": [
            {"pattern_slug": "loyalty_activation", "confidence": "strong", "notes": "Double loyalty points as breakfast purchase incentive"},
            {"pattern_slug": "occasion_peg", "confidence": "weak", "notes": "Breakfast daypart as occasion for loyalty bonus"}
        ]
    },
    {
        "shortcode": "DYZUCy0kjTx", "capture_date": "2026-05-16",
        "content_type": "video", "likes": 234,
        "caption": "جاهزين للمفاجآت مع كودو؟ 🍔 الآن كل وجبة أطفال معها لعبة مفاجأة 🎁😄",
        "visual": {
            "composition_style": "kids campaign launch video — mystery toy reveal with kids meal",
            "lighting": "bright, colorful, playful",
            "color_palette_dominant": ["red", "yellow", "green", "white"],
            "props_visible": ["kids meal box", "mystery gift bag", "surprise toy reveal", "Kudu logo"],
            "setting": "playful branded environment, child-centric",
            "characters_visible": {"count": 2},
            "text_overlays": [
                {"language": "arabic", "content_summary": "لعبة مفاجأة — surprise toy with every kids meal, mystery mechanic"}
            ],
            "notable_visual_elements": ["mystery mechanic = 'لعبة مفاجأة' drives excitement", "child reaction (delight) is the hero visual", "surprise element drives repeat visit behavior"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "playful",
                  "notable_phrases": ["جاهزين للمفاجآت؟", "لعبة مفاجأة"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Mystery toy mechanic (like Happy Meal) drives repeat visits as children collect different toys. 234 likes is good for a product-mechanics post. Surprise/mystery format generates UGC potential."
        },
        "patterns": [
            {"pattern_slug": "product_bundle_offer", "confidence": "strong", "notes": "Mystery surprise toy with kids meal — collectible/repeat-visit mechanic"},
            {"pattern_slug": "poll_engagement_mechanic", "confidence": "moderate", "notes": "Mystery element generates curiosity and anticipation"}
        ]
    },
    {
        "shortcode": "DYXUhLQoe52", "capture_date": "2026-05-15",
        "content_type": "image", "likes": 44,
        "caption": "البرانش صار أحلى 😋 اطلب صحنين فطور من كودو وخذ وافل مجانًا 🧇 العرض متوفر الجمعة والسبت",
        "visual": {
            "composition_style": "weekend brunch offer — breakfast + free waffle graphic",
            "lighting": "warm weekend morning",
            "color_palette_dominant": ["warm white", "red", "golden brown"],
            "props_visible": ["waffle with toppings", "breakfast plates", "coffee cup", "free offer badge"],
            "setting": "brunch table setting, weekend relaxed",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "البرانش صار أحلى — brunch just got better, 2 breakfast plates + free waffle, Fri-Sat only"}
            ],
            "notable_visual_elements": ["weekend-only daypart targeting", "waffle as hero premium item", "برانش (brunch) is a Saudi social ritual, especially Fridays"]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "warm",
                  "notable_phrases": ["البرانش صار أحلى", "وافل مجانًا"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Saudi weekend (Friday-Saturday)",
            "hospitality_cues": ["brunch = family/friends gathering"],
            "heritage_vs_modern": "modern",
            "free_notes": "Friday brunch is a major Saudi social occasion — the Saudi weekend (Thu-Fri or Fri-Sat) means Friday brunch is peak family gathering time. Kudu's برانش offer targets this weekly cultural ritual."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Saudi weekend (Fri-Sat) brunch as weekly cultural occasion"},
            {"pattern_slug": "price_offer_graphic", "confidence": "strong", "notes": "Free waffle with 2 breakfast plates — bundle deal"}
        ]
    },
    {
        "shortcode": "DYWpCuLDcAW", "capture_date": "2026-05-15",
        "content_type": "image", "likes": 14,
        "caption": "ما فيه شيء يبقى على حاله 🌿 خصوصًا مع رؤية واضحة للمستقبل 👌 من مصدر واحد، طلعت قصص كثيرة",
        "visual": {
            "composition_style": "sustainability story — coffee sourcing origins",
            "lighting": "natural, earthy, warm",
            "color_palette_dominant": ["green", "brown", "earth tones", "cream"],
            "props_visible": ["coffee beans", "farm setting", "natural materials"],
            "setting": "coffee farm / natural environment",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "رؤية واضحة للمستقبل — clear vision for the future, sustainability coffee origin narrative"}
            ],
            "notable_visual_elements": ["farm-to-cup storytelling", "green/earth tones signal sustainability", "lowest engagement in set (14 likes) — CSR content under-performs product content"]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "thoughtful",
                  "notable_phrases": ["ما فيه شيء يبقى على حاله", "رؤية واضحة للمستقبل"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["coffee origin — qahwa cultural connection"],
            "heritage_vs_modern": "modern",
            "free_notes": "Part of a Saudi Environment Fund partnership campaign. Very low engagement (14 likes) vs product content (44-383 likes) — confirms CSR content significantly underperforms in F&B on Instagram. Kudu still runs it for brand values positioning."
        },
        "patterns": [
            {"pattern_slug": "csr_brand_story", "confidence": "strong", "notes": "Sustainability sourcing narrative — Saudi Environment Fund collab"},
            {"pattern_slug": "product_hero", "confidence": "weak", "notes": "Coffee beans featured but not as commercial product"}
        ]
    },
    {
        "shortcode": "DYWoq9YjH8q", "capture_date": "2026-05-15",
        "content_type": "video", "likes": 50,
        "caption": "من حبة بسيطة، بدأت قصتهم.. بالتعاون مع صندوق البيئة كشريك استراتيجي، نكمّل رحلة القهوة",
        "visual": {
            "composition_style": "documentary video — coffee origin story with Saudi Environment Fund",
            "lighting": "natural, cinematic field photography",
            "color_palette_dominant": ["green", "brown", "sunlight gold"],
            "props_visible": ["coffee plants", "Saudi Environment Fund branding", "coffee beans in hands"],
            "setting": "coffee farm, outdoor natural environment",
            "characters_visible": {"count": 2},
            "text_overlays": [
                {"language": "arabic", "content_summary": "من حبة بسيطة — from a simple bean, coffee origin story with Saudi Environment Fund partnership"}
            ],
            "notable_visual_elements": ["documentary film style", "government partnership (Saudi Environment Fund) adds credibility", "coffee origin story elevates brand above fast food positioning"]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "storytelling",
                  "notable_phrases": ["من حبة بسيطة، بدأت قصتهم", "صندوق البيئة كشريك استراتيجي"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["qahwa — Saudi coffee cultural identity"],
            "heritage_vs_modern": "blended",
            "free_notes": "Saudi coffee origin story ties to national identity (Year of Saudi Coffee legacy). Government partnership with صندوق البيئة = Vision 2030 alignment. Brand elevating itself through sustainability narrative."
        },
        "patterns": [
            {"pattern_slug": "csr_brand_story", "confidence": "strong", "notes": "Coffee sustainability documentary with government partnership"},
            {"pattern_slug": "vision_2030_alignment", "confidence": "strong", "notes": "Saudi Environment Fund partnership + coffee heritage = V2030 signaling"}
        ]
    },
    {
        "shortcode": "DYWn9hzjYhe", "capture_date": "2026-05-15",
        "content_type": "image", "likes": 37,
        "caption": "لكل حبة بن قصة تبدا من الأرض لين ما توصل لك… وأكثر 🍂",
        "visual": {
            "composition_style": "product origin close-up — coffee bean macro photography",
            "lighting": "warm, natural, macro/close detail",
            "color_palette_dominant": ["deep brown", "earth tones", "amber"],
            "props_visible": ["raw coffee beans", "hands holding beans", "natural textures"],
            "setting": "close-up of coffee beans in hands, natural/earthy",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "لكل حبة بن قصة — every coffee bean has a story, from earth to cup"}
            ],
            "notable_visual_elements": ["macro photography elevates coffee to artisan level", "earthy palette = organic/natural brand signal", "third piece in coffee sustainability series"]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "poetic",
                  "notable_phrases": ["لكل حبة بن قصة", "من الأرض لين ما توصل لك"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["qahwa heritage — coffee as Saudi national identity"],
            "heritage_vs_modern": "blended",
            "free_notes": "Poetic register ('قصة' — story, 'من الأرض' — from the earth) is unusual for fast food. Kudu using coffee as a brand elevation tool to move from fast food to 'quality casual'. Saudi coffee cultural identity is a strong hook."
        },
        "patterns": [
            {"pattern_slug": "product_hero", "confidence": "moderate", "notes": "Coffee bean as artisan product hero — farm-to-cup macro"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "strong", "notes": "Coffee bean story ties to Saudi qahwa heritage and national coffee identity"}
        ]
    }
]

# ── ALBAIK (@albaik) ─────────────────────────────────────────────────────────

ALBAIK_POSTS = [
    {
        "shortcode": "DXzkeYyjdUb", "capture_date": "2026-05-07",
        "content_type": "video", "likes": 8173,
        "caption": "دبل كرسبي بيك الجديد قرمشة أكثر.. ومتعة أكبر😋 جربه الآن",
        "visual": {
            "composition_style": "product launch hero video — Double Crispy Bik close-up reveal",
            "lighting": "dramatic product studio, warm glow",
            "color_palette_dominant": ["golden brown", "red", "white", "orange"],
            "props_visible": ["Double Crispy Bik sandwich", "AlBaik branded packaging", "crispy texture close-up"],
            "setting": "studio product shot with atmospheric glow",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "دبل كرسبي بيك الجديد — new Double Crispy Bik, more crunch, more enjoyment"},
                {"language": "bilingual", "content_summary": "ALBAIK logo"}
            ],
            "notable_visual_elements": [
                "8173 likes — highest engagement in entire set, exceptional performance",
                "product close-up texture focus — crunch is the sensory hook",
                "simple copy: 'قرمشة أكثر ومتعة أكبر' (more crunch, more fun) — extreme brevity"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "bold",
                  "notable_phrases": ["قرمشة أكثر", "ومتعة أكبر", "جربه الآن"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "AlBaik's most-liked post in the dataset. Ultra-minimal copy (7 words + CTA) with maximum product focus. AlBaik's audience is so strong that product-first content achieves mass engagement without occasion hooks or storytelling."
        },
        "patterns": [
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Ultra-clean product hero — close-up texture focus, minimal copy"},
            {"pattern_slug": "product_launch_reveal", "confidence": "strong", "notes": "New product launch content — highest engagement justifies hero treatment"}
        ]
    },
    {
        "shortcode": "DXc6nXjCMLa", "capture_date": "2026-04-30",
        "content_type": "video", "likes": 1308,
        "caption": "صلصة البيك الجديدة… لهاليبو 😋 حامض، حلو وحرّاق🌶️ثلاث نكهات في صلصة واحدة جربها الآن",
        "visual": {
            "composition_style": "new product teaser — sauce reveal with flavour profile",
            "lighting": "moody, dramatic sauce pour",
            "color_palette_dominant": ["red", "orange", "yellow", "white"],
            "props_visible": ["new sauce bottle", "sauce drizzle", "AlBaik chicken piece", "Lahalybu branding"],
            "setting": "studio product close-up, dark background with light on sauce",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "لهاليبو — new sauce name, حامض + حلو + حراق (sour + sweet + spicy) three flavours in one"},
            ],
            "notable_visual_elements": [
                "sauce named 'لهاليبو' — playful invented name",
                "triple flavour profile communicated visually and verbally",
                "sauce drizzle = classic food porn technique"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "playful",
                  "notable_phrases": ["لهاليبو", "حامض، حلو وحرّاق", "ثلاث نكهات في صلصة واحدة"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "'لهاليبو' is a made-up playful name — brand identity naming that creates memorability. Sauce launches are high-engagement for AlBaik because the brand's loyal following tracks new menu additions closely."
        },
        "patterns": [
            {"pattern_slug": "product_launch_reveal", "confidence": "strong", "notes": "New sauce with invented name — AlBaik menu launch"},
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Sauce drizzle close-up — food porn texture technique"}
        ]
    },
    {
        "shortcode": "DWzRYzqjc-L", "capture_date": "2026-04-16",
        "content_type": "video", "likes": 5364,
        "caption": "التوأم المحبوب من البيك رجع 😋 اطلبه الآن.. لفترة محدودة فقط!",
        "visual": {
            "composition_style": "returning product hero — The Twin (التوأم) dual-item announcement",
            "lighting": "warm product spotlight",
            "color_palette_dominant": ["golden brown", "red", "cream", "white"],
            "props_visible": ["two Crispy Bik pieces (التوأم — the twin)", "AlBaik tray", "branded packaging"],
            "setting": "clean product display setting",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "التوأم المحبوب رجع — the beloved Twin is back, limited time CTA"}
            ],
            "notable_visual_elements": [
                "التوأم (The Twin) is an AlBaik signature — dual chicken product",
                "5364 likes — second highest in set, 'returning favourite' format",
                "limited time urgency — FOMO mechanic",
                "'المحبوب' (the beloved) confirms emotional attachment to this product"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "excited",
                  "notable_phrases": ["التوأم المحبوب رجع", "لفترة محدودة فقط"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "'التوأم' (The Twin) is one of AlBaik's most recognisable limited-time offers. 'رجع' (came back) triggers immediate loyalty response from AlBaik devotees. Limited availability = scarcity + FOMO = 5364 likes."
        },
        "patterns": [
            {"pattern_slug": "returning_fan_favourite", "confidence": "strong", "notes": "الـتوأم المحبوب returning product — highest engagement format for AlBaik"},
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Clean product hero for returning item"}
        ]
    },
    {
        "shortcode": "DWb2w60jdAY", "capture_date": "2026-04-08",
        "content_type": "video", "likes": 2737,
        "caption": "ساعة واحدة تصنع الفرق 🌍",
        "visual": {
            "composition_style": "Earth Hour awareness video — minimal, atmospheric",
            "lighting": "dark, candlelight/minimal light — Earth Hour theme",
            "color_palette_dominant": ["dark blue", "black", "warm amber/candle glow"],
            "props_visible": ["city skyline lights turning off", "candle/warm glow", "AlBaik subtle branding"],
            "setting": "environmental/global awareness visual — lights off Earth Hour moment",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "ساعة واحدة تصنع الفرق — one hour makes the difference (Earth Hour message)"}
            ],
            "notable_visual_elements": [
                "Earth Hour global sustainability moment",
                "5-word copy — ultra-minimal for maximum impact",
                "2737 likes — high engagement for a CSR post (unusual in F&B)"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "thoughtful",
                  "notable_phrases": ["ساعة واحدة تصنع الفرق"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Earth Hour 2026 (March/April)",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "AlBaik's Earth Hour post gets 2737 likes — unusually high for CSR content. AlBaik's brand loyalty is so strong that any content gets high baseline engagement. Minimal copy with global occasion hook is effective."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Earth Hour global occasion used for brand values statement"},
            {"pattern_slug": "csr_brand_story", "confidence": "strong", "notes": "Minimal-copy sustainability moment — brand character expressed through occasion"}
        ]
    },
    {
        "shortcode": "DWJzHH7DPwl", "capture_date": "2026-04-03",
        "content_type": "video", "likes": 1953,
        "caption": "معايدة من القلب… وفرحة العيد تكبر ❤️ مع كوبونات البيك، عايد من تحب 🎉",
        "visual": {
            "composition_style": "Eid greeting + coupon activation video",
            "lighting": "warm festive, golden Eid tones",
            "color_palette_dominant": ["gold", "red", "white", "green"],
            "props_visible": ["Eid greeting visual elements", "AlBaik coupon graphic", "festive decorative elements"],
            "setting": "festive Eid branded environment",
            "characters_visible": {"count": 2},
            "text_overlays": [
                {"language": "arabic", "content_summary": "معايدة من القلب — Eid greetings from the heart, coupon gifting mechanic for Eid"}
            ],
            "notable_visual_elements": [
                "coupon as Eid gifting mechanic — give AlBaik to loved ones",
                "'عايد من تحب' — gift Eid to those you love (with AlBaik coupons)",
                "Eid gifting frame elevates coupons to emotional gift"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "warm",
                  "notable_phrases": ["معايدة من القلب", "فرحة العيد تكبر", "عايد من تحب"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Eid Al-Fitr 2026",
            "hospitality_cues": ["Eid gifting tradition"],
            "heritage_vs_modern": "blended",
            "free_notes": "Gifting coupons for Eid is a clever mechanic — reframes commercial coupons as emotional gifts. 'عايد من تحب' (give Eid to those you love) is a powerful copy frame. Eid gifting is a deeply important Saudi social ritual."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Eid Al-Fitr occasion with coupon-as-gift emotional mechanic"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "moderate", "notes": "Eid gifting tradition — coupon as culturally appropriate gift frame"}
        ]
    },
    {
        "shortcode": "DWHTU0qDSDh", "capture_date": "2026-04-02",
        "content_type": "video", "likes": 709,
        "caption": "عيدكم مبارك وكل عام وأنتم بخير #البيك",
        "visual": {
            "composition_style": "Eid greeting — branded occasion card video",
            "lighting": "warm gold, festive",
            "color_palette_dominant": ["gold", "white", "red"],
            "props_visible": ["AlBaik logo", "Eid crescent/star motifs", "festive calligraphy"],
            "setting": "branded Eid greeting graphic",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "عيدكم مبارك وكل عام وأنتم بخير — Eid Mubarak blessing"}
            ],
            "notable_visual_elements": [
                "pure occasion greeting — no product",
                "classic 'عيدكم مبارك وكل عام وأنتم بخير' = traditional Saudi Eid formula",
                "709 likes for non-product content — AlBaik brand equity drives engagement"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "warm",
                  "notable_phrases": ["عيدكم مبارك", "كل عام وأنتم بخير"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Eid Al-Fitr 2026",
            "hospitality_cues": [],
            "heritage_vs_modern": "heritage",
            "free_notes": "'عيدكم مبارك وكل عام وأنتم بخير' is the canonical Saudi Eid greeting formula — timeless, expected. AlBaik keeps it simple and traditional. No product. Pure community greeting from a beloved brand."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Pure Eid greeting — no product, community connection play"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "strong", "notes": "Eid blessing formula — traditional Saudi occasion ritual"}
        ]
    },
    {
        "shortcode": "DWHG8zREwPl", "capture_date": "2026-04-02",
        "content_type": "video", "likes": 2686,
        "caption": "عيدكم غير مع التوأم كرسبي بيك x2 دبل القرمشة ودبل المتعة 😋 اطلبه الآن",
        "visual": {
            "composition_style": "Eid product activation — Double Crispy Twin Eid offer",
            "lighting": "warm festive product glow",
            "color_palette_dominant": ["gold", "red", "brown", "white"],
            "props_visible": ["Crispy Bik x2 Twin", "Eid decoration elements", "AlBaik branded packaging", "double product display"],
            "setting": "Eid festive + product hero combination",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "عيدكم غير مع التوأم — your Eid is different with the Twin, double crunch + double fun"}
            ],
            "notable_visual_elements": [
                "Eid + product hero combination — occasion meets product",
                "'عيدكم غير' (your Eid is different/special) positions AlBaik as Eid upgrade",
                "دبل = double formula used (دبل القرمشة ودبل المتعة) — copy pattern from Double Crispy campaign"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "celebratory",
                  "notable_phrases": ["عيدكم غير", "دبل القرمشة ودبل المتعة"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Eid Al-Fitr 2026",
            "hospitality_cues": ["Eid feasting tradition"],
            "heritage_vs_modern": "modern",
            "free_notes": "AlBaik runs multiple Eid posts — pure greeting + product activation. 2686 likes on the product post vs 709 on the pure greeting shows product content still outperforms even on Eid for this brand."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Eid occasion used to push Twin product — occasion + product hybrid"},
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Twin Crispy Bik as Eid hero product — double mechanic"}
        ]
    },
    {
        "shortcode": "DVwE1fqjeoE", "capture_date": "2026-02-26",
        "content_type": "video", "likes": 1019,
        "caption": "رايتنا العز 🇸🇦 ومجدنا هويتنا #يوم_العلم_السعودي",
        "visual": {
            "composition_style": "Saudi national occasion — Flag Day tribute video",
            "lighting": "dramatic, flag-lit green and white",
            "color_palette_dominant": ["green", "white", "black (sword)"],
            "props_visible": ["Saudi flag", "AlBaik branding (subtle)"],
            "setting": "national/patriotic visual — Saudi flag imagery",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "رايتنا العز ومجدنا هويتنا — our flag is our glory, our identity #Saudi_Flag_Day"}
            ],
            "notable_visual_elements": [
                "Saudi Flag Day (يوم العلم السعودي) — national occasion content",
                "green/white Saudi flag colors dominate",
                "no product shown — pure national identity content",
                "'رايتنا العز' — poetic national pride formula"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "patriotic",
                  "notable_phrases": ["رايتنا العز", "مجدنا هويتنا"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Saudi Flag Day — يوم العلم السعودي (February 26)",
            "hospitality_cues": [],
            "heritage_vs_modern": "heritage",
            "free_notes": "Saudi Flag Day is a key national occasion. AlBaik as a Saudi brand naturally participates. 'رايتنا العز' (our flag is glory) is the standard patriotic copy formula. No product — pure brand-nation alignment."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Saudi Flag Day national occasion — brand-nation alignment content"},
            {"pattern_slug": "cultural_identity_marker", "confidence": "strong", "notes": "Saudi flag as identity — brand participates in national identity moment"}
        ]
    },
    {
        "shortcode": "DVvj6u8FUZg", "capture_date": "2026-02-25",
        "content_type": "video", "likes": 216,
        "caption": "رمضان شهر العبادة والعطاء، لنشارك أيامه المليئة بالمشاركة والمحبة🌙 مع كوبونات البيك",
        "visual": {
            "composition_style": "Ramadan charity activation — share/give coupons campaign",
            "lighting": "warm Ramadan amber/golden moonlight tones",
            "color_palette_dominant": ["gold", "dark blue", "cream", "red"],
            "props_visible": ["Ramadan crescent moon", "AlBaik coupon cards", "gifting imagery"],
            "setting": "Ramadan atmospheric visual with sharing/charity theme",
            "characters_visible": {"count": 2},
            "text_overlays": [
                {"language": "arabic", "content_summary": "مع كوبونات البيك، شارك — share with AlBaik coupons during Ramadan charity month"}
            ],
            "notable_visual_elements": [
                "Ramadan زكاة/صدقة (charity) theme — giving AlBaik coupons as charity",
                "sharing/gifting mechanism tied to Ramadan spiritual value",
                "lower engagement (216 likes) vs product posts — contextual"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "spiritual",
                  "notable_phrases": ["رمضان شهر العبادة والعطاء", "المشاركة والمحبة"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Ramadan 2026",
            "hospitality_cues": ["Ramadan iftar tradition", "charity/sadaqah during Ramadan"],
            "heritage_vs_modern": "heritage",
            "free_notes": "Ramadan charitable giving (صدقة) is a core Islamic value. AlBaik frames coupons as acts of charity/sharing — deeply resonant in Ramadan context. Spiritual tone ('العبادة والعطاء') fits Ramadan mood."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Ramadan charity/giving occasion — coupon as sadaqah mechanic"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "strong", "notes": "Ramadan sharing culture — giving food as spiritual act"}
        ]
    },
    {
        "shortcode": "DVRXKGplejk", "capture_date": "2026-02-10",
        "content_type": "video", "likes": 1746,
        "caption": "رمضان شهر العبادة والعطاء، لنشارك أيامه المليئة بالمشاركة والمحبة🌙 مع كوبونات البيك، شارك",
        "visual": {
            "composition_style": "Ramadan sharing launch video — Ramadan campaign activation",
            "lighting": "warm Ramadan golden atmosphere",
            "color_palette_dominant": ["gold", "dark blue", "white", "red"],
            "props_visible": ["Ramadan lantern/fanoos", "AlBaik branded coupons", "family gathering imagery"],
            "setting": "Ramadan evening / iftar gathering ambiance",
            "characters_visible": {"count": 3},
            "text_overlays": [
                {"language": "arabic", "content_summary": "رمضان شهر العبادة والعطاء — Ramadan campaign launch video, coupon sharing mechanic"}
            ],
            "notable_visual_elements": [
                "Ramadan lantern visual = peak occasion signal",
                "1746 likes — campaign launch gets higher engagement than follow-up posts",
                "family gathering setting = Ramadan iftar hospitality"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "spiritual",
                  "notable_phrases": ["رمضان شهر العبادة والعطاء", "شارك الفرحة"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Ramadan 2026 — first night/launch",
            "hospitality_cues": ["iftar gathering", "Ramadan lantern", "family sharing"],
            "heritage_vs_modern": "heritage",
            "free_notes": "Ramadan campaign launch post. Ramadan lantern (فانوس) is the universal Arabic symbol for the holy month. Family iftar setting maximises Ramadan hospitality cues. 'شارك' (share) activates Islamic giving values."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Ramadan campaign launch — lantern + family + sharing = peak occasion signal"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "strong", "notes": "Ramadan iftar gathering + family sharing = Saudi hospitality heart"}
        ]
    },
    {
        "shortcode": "DVCIqF_jQbK", "capture_date": "2026-02-22",
        "content_type": "video", "likes": 597,
        "caption": "حكاية وطن بدأت بعزم… وتستمر بقلب واحد #يوم_التأسيس 🇸🇦",
        "visual": {
            "composition_style": "Saudi Foundation Day heritage video — national identity tribute",
            "lighting": "cinematic, warm heritage tones",
            "color_palette_dominant": ["green", "gold", "brown", "cream"],
            "props_visible": ["Saudi Heritage imagery", "AlBaik subtle branding", "historical Najdi elements"],
            "setting": "historical Saudi landscape/architecture",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "حكاية وطن بدأت بعزم — a nation's story began with resolve, Saudi Foundation Day"}
            ],
            "notable_visual_elements": [
                "يوم التأسيس (Foundation Day) = Saudi national occasion, February 22",
                "cinematic historical storytelling style",
                "'حكاية وطن' (a nation's story) = AlBaik as part of Saudi's identity",
                "no product shown — pure national identity brand positioning"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "patriotic",
                  "notable_phrases": ["حكاية وطن بدأت بعزم", "بقلب واحد"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Saudi Foundation Day — يوم التأسيس (February 22)",
            "hospitality_cues": [],
            "heritage_vs_modern": "heritage",
            "free_notes": "يوم التأسيس (Saudi Foundation Day, Feb 22) marks the founding of the first Saudi state in 1727. AlBaik participates as a Saudi institution. 'حكاية وطن' positions AlBaik as part of the Saudi story. High cultural prestige content."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Saudi Foundation Day — brand-nation identity alignment, no product"},
            {"pattern_slug": "cultural_identity_marker", "confidence": "strong", "notes": "Saudi heritage storytelling — AlBaik as Saudi institution narrative"}
        ]
    },
    {
        "shortcode": "DU6UivyDVQ5", "capture_date": "2026-02-28",
        "content_type": "video", "likes": 636,
        "caption": "مبارك عليكم الشهر، تقبل الله طاعاتكم وصالح اعمالكم.",
        "visual": {
            "composition_style": "Ramadan welcome greeting — pure occasion greeting video",
            "lighting": "warm crescent moon/night sky Ramadan atmosphere",
            "color_palette_dominant": ["deep blue", "gold", "white"],
            "props_visible": ["Ramadan crescent moon", "stars", "AlBaik subtle logo"],
            "setting": "atmospheric night sky, Ramadan visual",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "مبارك عليكم الشهر — blessed Ramadan greeting, traditional Islamic formula"}
            ],
            "notable_visual_elements": [
                "pure Islamic greeting formula — 'مبارك عليكم الشهر' + 'تقبل الله طاعاتكم'",
                "no product — pure community/spiritual greeting",
                "crescent moon = universal Ramadan visual signal"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "spiritual",
                  "notable_phrases": ["مبارك عليكم الشهر", "تقبل الله طاعاتكم وصالح اعمالكم"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Ramadan 2026 — first night greeting",
            "hospitality_cues": [],
            "heritage_vs_modern": "heritage",
            "free_notes": "'مبارك عليكم الشهر' is the first-night Ramadan greeting formula. 'تقبل الله طاعاتكم وصالح اعمالكم' is a standard dua/blessing. AlBaik uses pure Islamic formula — establishes brand as part of the community's spiritual life, not just a fast food chain."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Ramadan first night welcome — pure Islamic greeting formula"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "strong", "notes": "Ramadan spiritual greeting — brand as community member, not advertiser"}
        ]
    },
    {
        "shortcode": "DU3auXNjSAH", "capture_date": "2026-03-01",
        "content_type": "image", "likes": 988,
        "caption": "مبارك عليكم الشهر، تقبل الله طاعاتكم وصالح اعمالكم. نسعد بخدمتكم من بعد صلاة العشاء",
        "visual": {
            "composition_style": "Ramadan service announcement — post-Isha prayer opening hours graphic",
            "lighting": "warm evening, Ramadan atmospheric",
            "color_palette_dominant": ["deep blue", "gold", "red", "white"],
            "props_visible": ["Ramadan crescent", "mosque silhouette hint", "AlBaik branding", "service hours graphic"],
            "setting": "Ramadan evening atmospheric with service hours announcement",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "نسعد بخدمتكم من بعد صلاة العشاء — we serve you after Isha prayer (AlBaik Ramadan hours)"}
            ],
            "notable_visual_elements": [
                "Ramadan operational hours anchored to prayer time (Isha prayer)",
                "Framing service hours around Islamic prayer time = deep cultural authenticity",
                "'نسعد بخدمتكم' (we are happy to serve you) — warm hospitality framing"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "standard", "register": "formal", "tone": "warm",
                  "notable_phrases": ["نسعد بخدمتكم", "من بعد صلاة العشاء"], "call_to_action_present": False},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Ramadan 2026 — operating hours announcement",
            "hospitality_cues": ["post-prayer iftar/suhoor service tradition"],
            "heritage_vs_modern": "heritage",
            "free_notes": "AlBaik frames its Ramadan hours around prayer time rather than clock time — 'من بعد صلاة العشاء' (after Isha prayer). This is deeply culturally authentic. It signals that AlBaik operates within Islamic rhythms, not just business rhythms. Exemplary Saudi market adaptation."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Ramadan service hours announced via prayer time reference — Islamic time anchoring"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "strong", "notes": "Prayer time service — AlBaik operating within Islamic temporal structure"}
        ]
    },
    {
        "shortcode": "DUYuWzmjQVQ", "capture_date": "2026-03-15",
        "content_type": "video", "likes": 2529,
        "caption": "التوأم المحبوب من البيك مكمل معاك😋 اطلبه الآن! العرض لفترة محدودة فقط.",
        "visual": {
            "composition_style": "returning product continuation — Twin still available, limited time urgency",
            "lighting": "warm product spotlight",
            "color_palette_dominant": ["golden brown", "red", "cream"],
            "props_visible": ["Crispy Bik Twin pieces", "AlBaik packaging", "limited time badge"],
            "setting": "clean product display",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "التوأم المحبوب مكمل معاك — the beloved Twin continues with you, still available limited time"}
            ],
            "notable_visual_elements": [
                "'مكمل معاك' (continues with you) = extending campaign, riding momentum",
                "2529 likes — 'continuation' post maintains strong engagement",
                "limited time urgency maintained throughout campaign"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "warm",
                  "notable_phrases": ["مكمل معاك", "التوأم المحبوب", "لفترة محدودة فقط"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Ramadan 2026 season (Twin campaign extension)",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "'مكمل معاك' (still with you / continues with you) is a clever copy choice — positions product as companion. Campaign extension during Ramadan maintains Twin product momentum. Ramadan + fan favourite = sustained high engagement."
        },
        "patterns": [
            {"pattern_slug": "returning_fan_favourite", "confidence": "strong", "notes": "Twin campaign extension — 'still with you' prolonging the return"},
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Clean product hero, consistent with Twin campaign visual style"}
        ]
    },
    {
        "shortcode": "DTsJWGkjHuK", "capture_date": "2026-03-01",
        "content_type": "video", "likes": 807,
        "caption": "توأم الشاورما من البيك... خفيف، لذيذ ويضبطك😋 اطلبه الآن - العرض لفترة محدودة",
        "visual": {
            "composition_style": "shawarma product hero video — Shawarma Twin lightweight product reveal",
            "lighting": "warm appetising food lighting",
            "color_palette_dominant": ["golden brown", "cream", "red", "green"],
            "props_visible": ["AlBaik Shawarma wrap pieces (x2)", "fresh ingredients visible", "AlBaik branding"],
            "setting": "product close-up, warm appetising lighting",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "توأم الشاورما — Shawarma Twin, light/delicious/satisfying — limited time"}
            ],
            "notable_visual_elements": [
                "Shawarma Twin = lighter alternative to Crispy Bik Twin",
                "'خفيف، لذيذ ويضبطك' — light, delicious, satisfying (3-word flavour profile formula)",
                "same Twin mechanic applied to a different product (shawarma)"
            ]
        },
        "voice": {"language": "arabic", "dialect_detected": "najdi", "register": "casual", "tone": "playful",
                  "notable_phrases": ["خفيف، لذيذ ويضبطك", "توأم الشاورما"], "call_to_action_present": True},
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Ramadan 2026 (lighter meal preference during fasting)",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Shawarma is a beloved Saudi street food. AlBaik's 'Shawarma Twin' applies the successful Twin mechanic to a different product line. 'خفيف' (light) is strategic — Ramadan fasting = preference for lighter iftar meals."
        },
        "patterns": [
            {"pattern_slug": "product_launch_reveal", "confidence": "strong", "notes": "Shawarma Twin product launch — Twin mechanic applied to shawarma"},
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Shawarma wrap close-up hero shot"}
        ]
    }
]


def build_obs(post, handle_norm, account_ulid, sector="f_and_b"):
    vis = post["visual"]
    return {
        "observation_ulid": make_ulid(),
        "schema_version": 1,
        "account_handle_normalized": handle_norm,
        "account_ulid": account_ulid,
        "sector": sector,
        "content_ref": {
            "filename": f"{post['shortcode']}.jpg",
            "platform": "instagram",
            "content_type": post["content_type"],
            "capture_date": post["capture_date"],
            "source_url": f"https://www.instagram.com/p/{post['shortcode']}/"
        },
        "visual_observations": {
            "composition_style": vis["composition_style"],
            "lighting": vis["lighting"],
            "color_palette_dominant": vis["color_palette_dominant"],
            "props_visible": vis["props_visible"],
            "setting": vis["setting"],
            "characters_visible": vis["characters_visible"],
            "text_overlays": vis["text_overlays"],
            "notable_visual_elements": vis["notable_visual_elements"]
        },
        "voice_observations": post["voice"],
        "compliance_check": {
            "hard_blocks_triggered": [],
            "soft_flags": [],
            "overall_compliance": "clean"
        },
        "cultural_notes": post["cultural_notes"],
        "pattern_matches": post["patterns"],
        "quality_assessment": {
            "production_quality": "professional",
            "brand_consistency_with_account": "strong",
            "engagement_potential": "high" if post["likes"] >= 500 else "medium" if post["likes"] >= 100 else "low"
        },
        "provenance": {
            "source": f"benchmark:@{handle_norm.lower().replace('ogz-f-and-b-reference-','ref')}; content:{post['shortcode']}; browser_collected:2026-05-21",
            "date_added": NOW,
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:f_and_b"
        }
    }


def main():
    OBS_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    for account, posts, handle_norm, account_ulid in [
        ("kuduksa", KUDU_POSTS, "OGZ-F-AND-B-Reference-007", "01KS8MQHR1WGRTDFZ2NDA3YT7Q"),
        ("albaik", ALBAIK_POSTS, "OGZ-F-AND-B-Reference-008", "01KS8MQHR2XHSUEGZ3OEB4ZU8R"),
    ]:
        written = 0
        for post in posts:
            obs = build_obs(post, handle_norm, account_ulid)
            (OBS_DIR / f"{obs['observation_ulid']}.json").write_text(
                json.dumps(obs, ensure_ascii=False, indent=2)
            )
            written += 1
        print(f"  @{account}: {written} observations written")
        total += written
    print(f"\nTotal: {total} observations written to {OBS_DIR}")


if __name__ == "__main__":
    main()
