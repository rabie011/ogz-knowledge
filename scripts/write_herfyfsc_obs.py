#!/usr/bin/env python3
"""
Write 15 @herfyfsc observation JSONs from browser-collected post data.
Posts are from the Spacetoon 'وجبة شباب المستقبل' campaign (April 29 – May 6, 2026).
"""
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OBS_DIR = REPO / "11_who_to_learn_from" / "observations" / "f_and_b"

CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_offset = 0


def make_ulid() -> str:
    global _offset
    t = int(time.time() * 1000) + _offset
    _offset += 1
    t_part = ""
    v = t
    for _ in range(10):
        t_part = CROCKFORD[v & 0x1F] + t_part
        v >>= 5
    r = random.getrandbits(80)
    r_part = ""
    for _ in range(16):
        r_part = CROCKFORD[r & 0x1F] + r_part
        r >>= 5
    return t_part + r_part


ACCOUNT_ULID = "01KS8MQHR0SVWGFRK2NDA3YT6P"
HANDLE_NORM = "OGZ-F-AND-B-Reference-006"
NOW = datetime.now(timezone.utc).isoformat()

# 15 posts collected via browser — April 29 to May 6, 2026
POSTS = [
    {
        "shortcode": "DX_qeWDmh9J",
        "capture_date": "2026-05-06",
        "content_type": "image",
        "likes": 29,
        "caption": "يحلي جلستك",
        "visual": {
            "composition_style": "product hero — churros in branded cup with Arabic coffee service items",
            "lighting": "warm studio",
            "color_palette_dominant": ["gold", "brown", "cream", "white"],
            "props_visible": ["churros in branded cup", "Arabic dallah (coffee pot)", "small fenjan cups", "marble table surface"],
            "setting": "cafe table, marble surface",
            "characters_visible": {"count": 0},
            "text_overlays": [{"language": "arabic", "content_summary": "يحلي جلستك — sweetens your gathering, product tagline"}],
            "notable_visual_elements": ["Arabic hospitality props (dallah + fenjan) paired with churros product", "warm amber lighting"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "warm", "notable_phrases": ["يحلي جلستك"], "call_to_action_present": False
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["dallah", "fenjan", "qahwa setting"],
            "heritage_vs_modern": "blend",
            "free_notes": "Arabic coffee service (dallah/fenjan) used as hospitality signifier alongside Western product (churros) — classic localisation bridge"
        },
        "patterns": [
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Churros centered with hospitality props as supporting frame"},
            {"pattern_slug": "arabic_hospitality_cue", "confidence": "strong", "notes": "Dallah + fenjan = qahwa hospitality signal"},
        ]
    },
    {
        "shortcode": "DX9TYFKE7WO",
        "capture_date": "2026-05-05",
        "content_type": "image",
        "likes": 62,
        "caption": "بعض الذكريات ما تتكرر! وجبة شباب المستقبل منها",
        "visual": {
            "composition_style": "retro object-on-white — VHS cassette tape with branded campaign design",
            "lighting": "flat studio white",
            "color_palette_dominant": ["black", "white", "red", "yellow"],
            "props_visible": ["VHS cassette tape", "Spacetoon logo", "Herfy logo", "retro label design"],
            "setting": "studio white background",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "وجبة شباب المستقبل — Youth of the Future Meal label on VHS"},
                {"language": "bilingual", "content_summary": "Herfy + Spacetoon co-brand logos"}
            ],
            "notable_visual_elements": ["VHS format as nostalgia signifier for 90s/2000s childhood", "Spacetoon x Herfy collaboration branding"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "nostalgic", "notable_phrases": ["بعض الذكريات ما تتكرر", "شباب المستقبل"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy nostalgia campaign",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "VHS tape as a cultural artifact for the Saudi Spacetoon generation (80s-90s born). Spacetoon was the Arabic animation channel that defined childhood for this demographic."
        },
        "patterns": [
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "VHS as retro childhood symbol, Spacetoon generation targeting"},
            {"pattern_slug": "collab_campaign_reveal", "confidence": "strong", "notes": "Spacetoon x Herfy co-branded campaign content"},
        ]
    },
    {
        "shortcode": "DX7APMGE2_M",
        "capture_date": "2026-05-04",
        "content_type": "image",
        "likes": 694,
        "caption": "لأنكم خريجين 2026🎓 خلّينا لكم وجبتين برجر الدجاج + ميني تورتيلا بـ 26 ريال بس",
        "visual": {
            "composition_style": "graphic design — promotional price-offer layout with graduation theme",
            "lighting": "flat graphic",
            "color_palette_dominant": ["navy", "gold", "white", "red"],
            "props_visible": ["graduation cap icon", "burger graphic", "tortilla graphic", "price callout 26 SAR"],
            "setting": "graphic/designed background",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "خريجين 2026 — Class of 2026 graduation offer, 2 meals for 26 SAR"},
                {"language": "bilingual", "content_summary": "Herfy logo + graduation cap graphics"}
            ],
            "notable_visual_elements": ["price-offer prominently displayed", "graduation cap motif signals occasion", "26 SAR = clever 2026 graduation year tie-in"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "celebratory", "notable_phrases": ["لأنكم خريجين 2026", "بـ 26 ريال"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "graduation season 2026",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Graduation season (May-June) is a major occasion in Saudi. Price 26 SAR mirrors graduation year 2026 — clever numeric branding. High engagement (694 likes) confirms occasion resonance."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Graduation 2026 occasion hook with price tied to year"},
            {"pattern_slug": "price_offer_graphic", "confidence": "strong", "notes": "Promotional deal prominently designed into graphic"},
        ]
    },
    {
        "shortcode": "DX60YwVk2mo",
        "capture_date": "2026-05-04",
        "content_type": "image",
        "likes": 889,
        "caption": "الخريجين يستاهلون أكثر 😍 وجبة بيج تشيكن مع قطعتين ستريبس بـ 21 ريال بس 🎓",
        "visual": {
            "composition_style": "graphic design — graduation promotion with product imagery",
            "lighting": "flat graphic",
            "color_palette_dominant": ["navy", "gold", "white"],
            "props_visible": ["graduation cap", "Big Chicken sandwich graphic", "strips graphic", "price callout 21 SAR"],
            "setting": "graphic/designed background",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "خريجين — graduates deserve more, Big Chicken + 2 strips 21 SAR"},
            ],
            "notable_visual_elements": ["companion piece to 26 SAR graduation post", "product photos integrated into graphic design"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "celebratory", "notable_phrases": ["الخريجين يستاهلون أكثر"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "graduation season 2026",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Second graduation post same day — Herfy ran a graduation bundle campaign for class of 2026. Higher likes (889) than companion post (694) — product imagery may have driven engagement."
        },
        "patterns": [
            {"pattern_slug": "occasion_peg", "confidence": "strong", "notes": "Graduation season occasion hook — second execution same day"},
            {"pattern_slug": "price_offer_graphic", "confidence": "strong", "notes": "21 SAR deal graphic — companion to 26 SAR post"},
        ]
    },
    {
        "shortcode": "DX4bYVHE_X-",
        "capture_date": "2026-05-03",
        "content_type": "image",
        "likes": 1282,
        "caption": "الفرصة الأخيرة لكم يا شباب المستقبل",
        "visual": {
            "composition_style": "interactive poll graphic — Hiya doll with hair color options",
            "lighting": "bright graphic",
            "color_palette_dominant": ["pink", "purple", "white", "yellow"],
            "props_visible": ["Hiya (هيا) Spacetoon doll character", "hair color swatches", "competition/giveaway visual"],
            "setting": "designed promotional graphic background",
            "characters_visible": {"count": 1, "description": "Hiya (هيا) animated character from Spacetoon"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "ما لون شعر الدمية هيا؟ — What color is Hiya doll's hair? Poll/competition"},
                {"language": "arabic", "content_summary": "الفرصة الأخيرة — Last chance, competition deadline"}
            ],
            "notable_visual_elements": ["Hiya character is Spacetoon animated girl", "hair color poll drives engagement", "competition mechanic"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "playful", "notable_phrases": ["الفرصة الأخيرة", "شباب المستقبل"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy campaign giveaway",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Interactive poll mechanic with giveaway prize drives high engagement (1282 likes). Hiya is a beloved Spacetoon character for Saudi millennial generation."
        },
        "patterns": [
            {"pattern_slug": "poll_engagement_mechanic", "confidence": "strong", "notes": "Hair color poll drives comments + engagement, giveaway prize"},
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Hiya doll from Spacetoon targets nostalgic Saudi audience"},
        ]
    },
    {
        "shortcode": "DX33QjaDUqf",
        "capture_date": "2026-05-03",
        "content_type": "video",
        "likes": 149,
        "caption": "لحظة الفوز تغيّر كل شي! والفرصة ممكن تكون لك 🔥 الكورة أحلى مع بيبسي ⚽",
        "visual": {
            "composition_style": "reel — Champions League football + Pepsi collab moment-of-victory",
            "lighting": "stadium/event lighting",
            "color_palette_dominant": ["blue", "red", "white", "black"],
            "props_visible": ["football/soccer ball", "Pepsi can/cup", "stadium lights", "Herfy + Pepsi co-branding"],
            "setting": "stadium atmosphere, football celebration",
            "characters_visible": {"count": 1, "description": "person celebrating football win"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "لحظة الفوز تغيّر كل شي — moment of victory changes everything"},
                {"language": "bilingual", "content_summary": "Herfy + Pepsi + Champions League logos"}
            ],
            "notable_visual_elements": ["Pepsi sponsor tie-in with Champions League", "victory/winning emotion arc"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "energetic", "notable_phrases": ["لحظة الفوز تغيّر كل شي", "الكورة أحلى مع بيبسي"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Champions League season + Pepsi partnership",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Football is the dominant Saudi passion point. Herfy x Pepsi collab rides the Champions League energy. Victory emotion arc (winning = Herfy + Pepsi) follows Saudi sports sponsorship pattern."
        },
        "patterns": [
            {"pattern_slug": "sports_passion_peg", "confidence": "strong", "notes": "Champions League football as cultural passion hook"},
            {"pattern_slug": "collab_campaign_reveal", "confidence": "strong", "notes": "Pepsi + Herfy co-branded campaign activation"},
        ]
    },
    {
        "shortcode": "DX31OLOmufm",
        "capture_date": "2026-05-03",
        "content_type": "image",
        "likes": 103,
        "caption": "سؤال اليوم تتذكرون مين كان صديق روميو المقرّب؟👀 #شباب_المستقبل",
        "visual": {
            "composition_style": "trivia card — question on solid color background",
            "lighting": "flat graphic",
            "color_palette_dominant": ["blue", "white", "yellow"],
            "props_visible": ["question mark graphic", "Spacetoon show imagery", "Romeo character reference"],
            "setting": "solid blue background, graphic design",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "سؤال اليوم — daily quiz question about Romeo's best friend in Spacetoon"},
            ],
            "notable_visual_elements": ["trivia format designed to drive comments", "blue background creates visual pause in feed", "references عهد الأصدقاء (Romeo) Spacetoon series"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "playful", "notable_phrases": ["سؤال اليوم", "تتذكرون"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy campaign",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Romeo's Friends (عهد الأصدقاء) is one of the most beloved Spacetoon shows in Saudi. Trivia mechanic designed to generate comments — brand as memory curator for the nostalgia generation."
        },
        "patterns": [
            {"pattern_slug": "trivia_engagement_mechanic", "confidence": "strong", "notes": "Spacetoon trivia question drives comment engagement"},
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Romeo's Friends — iconic Spacetoon show for Saudi millennials"},
        ]
    },
    {
        "shortcode": "DX1lNeBERdI",
        "capture_date": "2026-05-02",
        "content_type": "image",
        "likes": 380,
        "caption": "طعم الذكريات والطفولة الجميلة التي لاتنسى💖🤩 #سبيستون #spacetoon",
        "visual": {
            "composition_style": "campaign poster — collectible Spacetoon character toys with meal",
            "lighting": "bright promotional",
            "color_palette_dominant": ["red", "yellow", "pink", "white"],
            "props_visible": ["Spacetoon character collectible figures", "Herfy meal box", "Herfy branded packaging"],
            "setting": "branded promotional backdrop, product display",
            "characters_visible": {"count": 3, "description": "Spacetoon animated characters as collectible figures"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "اطلبها الآن! واحصل على مجسمك المفضل — order now, get your favorite collectible figure"},
                {"language": "bilingual", "content_summary": "Spacetoon x Herfy co-brand logos"}
            ],
            "notable_visual_elements": ["collectible toy mechanics drive repeat purchase", "Spacetoon characters create emotional pull", "meal + collectible bundle offer"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "nostalgic", "notable_phrases": ["طعم الذكريات", "الطفولة الجميلة"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy campaign — collectible campaign mechanic",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Collectible toy mechanic (مجسم) drives repeat visits — each purchase may come with different characters. Happy Meal equivalent with Saudi cultural IP. Strong 380 likes engagement."
        },
        "patterns": [
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Childhood characters as collectibles reactivate nostalgia"},
            {"pattern_slug": "product_bundle_offer", "confidence": "strong", "notes": "Meal + collectible figure bundle CTA"},
        ]
    },
    {
        "shortcode": "DX1GIE2mkFX",
        "capture_date": "2026-05-02",
        "content_type": "image",
        "likes": 79,
        "caption": "فلونة كانت جزء من أيامنا… وأبسط لحظاتنا كانت تسعدنا! اليوم نعيش هالإحساس من جديد",
        "visual": {
            "composition_style": "lifestyle nostalgia — Herfy meal box on traditional setting with old TV",
            "lighting": "warm amber, soft indoor",
            "color_palette_dominant": ["red", "brown", "warm orange", "beige"],
            "props_visible": ["Herfy meal box", "old CRT television", "Arabic rug/carpet (سجادة)", "traditional room setting"],
            "setting": "living room with traditional Arabic furnishings, old TV playing Spacetoon",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "فلونة — Flona character name from Spacetoon visible on TV screen"},
            ],
            "notable_visual_elements": ["CRT TV playing Spacetoon = childhood memory trigger", "Arabic rug/traditional setting = Saudi home", "Herfy meal placed in nostalgic Saudi domestic scene"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "nostalgic", "notable_phrases": ["فلونة كانت جزء من أيامنا", "أبسط لحظاتنا كانت تسعدنا", "نعيش هالإحساس من جديد"], "call_to_action_present": False
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy nostalgia campaign",
            "hospitality_cues": ["traditional living room setting"],
            "heritage_vs_modern": "blend",
            "free_notes": "Flona (فلونة) from Heidi/Alps is one of the most beloved Spacetoon characters. CRT TV + Arabic rug creates authentic Saudi living room nostalgia. Herfy placed in that memory = emotional brand association."
        },
        "patterns": [
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Old TV + Arabic rug + Spacetoon character = Saudi childhood memory reconstruction"},
            {"pattern_slug": "lifestyle_embed", "confidence": "strong", "notes": "Brand product embedded in nostalgic domestic scene rather than product shot"},
        ]
    },
    {
        "shortcode": "DXyroUMGhec",
        "capture_date": "2026-05-01",
        "content_type": "image",
        "likes": 132,
        "caption": "شخصيات من أيام ما تنسى… تذكّرتوهم؟🤩 #شباب_المستقبل #سبيستون",
        "visual": {
            "composition_style": "silhouette recognition graphic — multiple Spacetoon character silhouettes",
            "lighting": "flat graphic, backlit silhouette style",
            "color_palette_dominant": ["dark blue", "purple", "white", "orange"],
            "props_visible": ["anime character silhouettes (multiple)", "Spacetoon visual style"],
            "setting": "graphic background with atmospheric glow/backlight",
            "characters_visible": {"count": 6, "description": "Spacetoon character silhouettes (multiple shows)"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "تذكّرتوهم؟ — do you remember them? Recognition caption"},
            ],
            "notable_visual_elements": ["silhouette format creates mystery/recognition challenge", "multiple characters from different shows", "designed to trigger memory and drive comments"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "nostalgic", "notable_phrases": ["شخصيات من أيام ما تنسى", "تذكّرتوهم"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy campaign",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Silhouette recognition mechanic is a proven engagement driver — forces the audience to name characters in comments. Multiple shows represented broadens nostalgia reach."
        },
        "patterns": [
            {"pattern_slug": "trivia_engagement_mechanic", "confidence": "strong", "notes": "Silhouette recognition drives identification comments"},
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Multiple Spacetoon show characters targeted at Saudi millennial audience"},
        ]
    },
    {
        "shortcode": "DXw-jOhkZjC",
        "capture_date": "2026-04-30",
        "content_type": "image",
        "likes": 103,
        "caption": "مستعدّين للجاي؟ ترقبوا المفاجآت🤩 #هرفي #Herfy #بيبسي #Pepsi",
        "visual": {
            "composition_style": "teaser — store exterior with anticipation graphic, Champions League trophy hint",
            "lighting": "outdoor daylight, bright",
            "color_palette_dominant": ["red", "white", "silver", "blue"],
            "props_visible": ["Herfy restaurant exterior", "Champions League trophy visual", "Pepsi branding elements"],
            "setting": "Herfy restaurant exterior / branded teaser graphic",
            "characters_visible": {"count": 0},
            "text_overlays": [
                {"language": "arabic", "content_summary": "مستعدّين للجاي؟ ترقبوا المفاجآت — are you ready for what's coming? Watch for surprises"},
                {"language": "bilingual", "content_summary": "Herfy + Pepsi logos"}
            ],
            "notable_visual_elements": ["teaser format — campaign not yet revealed", "Champions League + Pepsi = upcoming sports collab", "anticipation-building content type"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "teasing", "notable_phrases": ["مستعدّين للجاي؟", "ترقبوا المفاجآت"], "call_to_action_present": False
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Pepsi x Herfy Champions League campaign teaser",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Teaser post before Champions League / Pepsi campaign reveal. 'ترقبوا' (watch out / stay tuned) is a standard Saudi social media teaser phrase. Builds anticipation before campaign launch."
        },
        "patterns": [
            {"pattern_slug": "campaign_teaser", "confidence": "strong", "notes": "Anticipation-building before campaign reveal"},
            {"pattern_slug": "sports_passion_peg", "confidence": "moderate", "notes": "Champions League trophy hint at upcoming sports activation"},
        ]
    },
    {
        "shortcode": "DXwb2X7CENo",
        "capture_date": "2026-04-30",
        "content_type": "image",
        "likes": 2334,
        "caption": "ومن لا يعرف سالي🤩🥺 الجائزة تعتمد على إجاباتكم❗👌 شروط المسابقة: متابعة حسابات",
        "visual": {
            "composition_style": "competition graphic — Sally (سالي) Spacetoon character with language quiz",
            "lighting": "bright graphic",
            "color_palette_dominant": ["pink", "white", "yellow", "red"],
            "props_visible": ["Sally (سالي) animated character", "language flag icons", "competition mechanics visual", "Spacetoon + Herfy logos"],
            "setting": "promotional graphic background",
            "characters_visible": {"count": 1, "description": "Sally (سالي) — iconic Spacetoon animated girl character"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "أي اللغات تتقنها سالي بطلاقة؟ — what languages does Sally speak fluently? Trivia competition"},
                {"language": "bilingual", "content_summary": "Spacetoon x Herfy competition branding"}
            ],
            "notable_visual_elements": ["Sally is one of the most beloved Spacetoon characters in Saudi Arabia", "language question tests fan depth knowledge", "competition prize drives massive engagement — 2334 likes highest in set"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "playful", "notable_phrases": ["ومن لا يعرف سالي", "الجائزة تعتمد على إجاباتكم"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy campaign competition",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Highest-engagement post in set (2334 likes). Sally (سالي) is arguably the most beloved Spacetoon character in Saudi — Japanese anime Mahou no Tenshi Creamy Mami equivalent. Competition mechanic + beloved character = maximum virality."
        },
        "patterns": [
            {"pattern_slug": "poll_engagement_mechanic", "confidence": "strong", "notes": "Trivia competition with prize — highest engagement post in set"},
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Sally is the peak nostalgia character for Saudi Spacetoon generation"},
        ]
    },
    {
        "shortcode": "DXwKRPEDlfr",
        "capture_date": "2026-04-30",
        "content_type": "image",
        "likes": 274,
        "caption": "كل شي تغيّر… إلا هالإحساس #وجبة_شباب_المستقبل #هرفي #سبيستون",
        "visual": {
            "composition_style": "lifestyle — Saudi boy in white thobe hugging Herfy meal box, nostalgic Spacetoon background",
            "lighting": "warm, soft ambient",
            "color_palette_dominant": ["white", "red", "warm beige", "cream"],
            "props_visible": ["Herfy meal box", "Spacetoon TV backdrop", "white thobe (traditional Saudi attire)"],
            "setting": "nostalgic Saudi living room / Spacetoon TV setting",
            "characters_visible": {"count": 1, "description": "Saudi boy/young man in white thobe holding Herfy meal box with joy"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "كل شي تغيّر… إلا هالإحساس — everything changed… except this feeling"},
            ],
            "notable_visual_elements": [
                "white thobe = unmistakably Saudi cultural identity marker",
                "boy hugging meal box = emotional product love gesture",
                "Spacetoon backdrop bridges past and present",
                "copy 'كل شي تغيّر إلا هالإحساس' — classic nostalgic framing"
            ]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "emotional", "notable_phrases": ["كل شي تغيّر… إلا هالإحساس", "وجبة شباب المستقبل"], "call_to_action_present": False
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy campaign emotional peak",
            "hospitality_cues": ["Saudi domestic setting"],
            "heritage_vs_modern": "blend",
            "free_notes": "Peak emotional execution in campaign. White thobe + Herfy meal + Spacetoon = Saudi identity, childhood, and brand memory unified. The copy 'كل شي تغيّر إلا هالإحساس' is the campaign's emotional thesis. Character is clearly Saudi — strong cultural identity signal."
        },
        "patterns": [
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Saudi boy in thobe + Spacetoon + Herfy = Saudi identity × childhood memory"},
            {"pattern_slug": "emotional_brand_moment", "confidence": "strong", "notes": "Emotional peak of campaign — copy is the thesis statement"},
            {"pattern_slug": "cultural_identity_marker", "confidence": "strong", "notes": "White thobe as unmistakable Saudi identity visual"},
        ]
    },
    {
        "shortcode": "DXt99sgAX6Y",
        "capture_date": "2026-04-29",
        "content_type": "video",
        "likes": 1164,
        "caption": "واليوم أتيت لأخبركم عن هذه الوجبة الشهيّة😋🤩 #سبيستون #spacetoon",
        "visual": {
            "composition_style": "animated character narrates — Hiya doll clip presenting the meal",
            "lighting": "animation scene lighting",
            "color_palette_dominant": ["purple", "pink", "white", "red"],
            "props_visible": ["Hiya (هيا) animated character", "Herfy meal elements", "Spacetoon branded graphics"],
            "setting": "animated scene / Spacetoon show-style presentation",
            "characters_visible": {"count": 1, "description": "Hiya (هيا) animated character from Spacetoon acting as brand narrator"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "واليوم أتيت لأخبركم عن هذه الوجبة الشهيّة — and today I came to tell you about this delicious meal"},
            ],
            "notable_visual_elements": ["animated character as brand spokesperson", "Spacetoon animation style maintained", "character narrates in-universe — maintains illusion"]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "standard", "register": "formal",
            "tone": "enthusiastic", "notable_phrases": ["واليوم أتيت لأخبركم", "الوجبة الشهيّة"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": "Spacetoon x Herfy campaign — animated character activation",
            "hospitality_cues": [],
            "heritage_vs_modern": "modern",
            "free_notes": "Hiya character speaks in fusha/standard Arabic (as she does in the show) — maintains authenticity with the source IP. Very high engagement (1164 likes) — character-first content outperforms standard brand posts."
        },
        "patterns": [
            {"pattern_slug": "character_spokesperson", "confidence": "strong", "notes": "Animated character as brand narrator in their original voice/style"},
            {"pattern_slug": "nostalgia_play", "confidence": "strong", "notes": "Hiya character speaks in-universe — Spacetoon generation activation"},
            {"pattern_slug": "collab_campaign_reveal", "confidence": "strong", "notes": "Campaign peak — character directly promotes the meal"},
        ]
    },
    {
        "shortcode": "DXtKd57EftP",
        "capture_date": "2026-04-29",
        "content_type": "video",
        "likes": 202,
        "caption": "دبلنا لكم الجامبو!! وجبتين بـ 30 ريال بس 😏 لطلبات السيارة فقط 🚗",
        "visual": {
            "composition_style": "drive-through POV — hand passing tray through window with Jumbo meal",
            "lighting": "natural daylight, outdoor",
            "color_palette_dominant": ["red", "yellow", "white", "silver"],
            "props_visible": ["Jumbo burger (جامبو)", "fries container", "Pepsi cup", "Herfy branded tray/bag", "car window frame"],
            "setting": "drive-through window, outdoor daylight",
            "characters_visible": {"count": 1, "description": "Herfy staff hand passing tray through drive-through window (hand only visible)"},
            "text_overlays": [
                {"language": "arabic", "content_summary": "دبلنا لكم الجامبو — we dubbed/upgraded the Jumbo for you, 2 meals 30 SAR"},
            ],
            "notable_visual_elements": [
                "drive-through as content format (Saudi car culture)",
                "hand pass through window = service moment",
                "Jumbo product hero in hands",
                "drive-through only offer restricts to car culture usage"
            ]
        },
        "voice": {
            "language": "arabic", "dialect_detected": "najdi", "register": "casual",
            "tone": "playful", "notable_phrases": ["دبلنا لكم الجامبو", "وجبتين بـ 30 ريال", "لطلبات السيارة فقط"], "call_to_action_present": True
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": None,
            "hospitality_cues": ["drive-through service hand-off"],
            "heritage_vs_modern": "modern",
            "free_notes": "Drive-through culture is extremely prominent in Saudi (Riyadh especially) — car-centric city design means drive-through is premium. 'دبلنا' (we dubbed) is a clever wordplay — also means 'we upgraded'. Car-only offer aligns with Saudi mobility culture."
        },
        "patterns": [
            {"pattern_slug": "price_offer_graphic", "confidence": "strong", "notes": "30 SAR dual meal deal prominently called out"},
            {"pattern_slug": "product_hero", "confidence": "strong", "notes": "Jumbo burger centered in drive-through hand-pass moment"},
        ]
    },
]


def build_observation(post: dict) -> dict:
    vis = post["visual"]
    return {
        "observation_ulid": make_ulid(),
        "schema_version": 1,
        "account_handle_normalized": HANDLE_NORM,
        "account_ulid": ACCOUNT_ULID,
        "sector": "f_and_b",
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
            "source": f"benchmark:@herfyfsc; content:{post['shortcode']}; browser_collected:2026-05-21",
            "date_added": NOW,
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:f_and_b"
        }
    }


def main():
    OBS_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for post in POSTS:
        obs = build_observation(post)
        out_path = OBS_DIR / f"{obs['observation_ulid']}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(obs, f, ensure_ascii=False, indent=2)
        written += 1
        print(f"  wrote {obs['observation_ulid']} — {post['shortcode']}")
    print(f"\nDone: {written} observations written to {OBS_DIR}")


if __name__ == "__main__":
    main()
