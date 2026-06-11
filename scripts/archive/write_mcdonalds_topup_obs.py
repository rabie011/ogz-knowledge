#!/usr/bin/env python3
"""Write 38 new observations for @mcdonaldsksa (OGZ-F-AND-B-Reference-039).
Brings total from 12 → 50 obs. Covers May 7–24 2026.
Content pillars: employee_pride(7) + product_promo(7) + value_deals(5) +
  sports_giveaway(6) + jjk_collab(5) + csr(3) + delivery_promo(3) + engagement(2)
"""
import json, pathlib

REPO = pathlib.Path('/Users/abarihm/Desktop/ogz-knowledge')
OUT  = REPO / '11_who_to_learn_from' / 'observations' / 'f_and_b'
OUT.mkdir(parents=True, exist_ok=True)

ACCOUNT_NORM = "OGZ-F-AND-B-Reference-039"
ACCOUNT_ULID = "01KS5XZ114TEWH0AVNH9DN65R6"
SECTOR       = "f_and_b"
NOW          = "2026-05-25T10:00:00Z"

# 38 pre-assigned observation ULIDs (Crockford base32, 26 chars each)
ULIDS = [
    "01KSFBW3ED4N8SPVHX3J6K7Y00","01KSFBW3ED4N8SPVHX3J6K7Y01",
    "01KSFBW3ED4N8SPVHX3J6K7Y02","01KSFBW3ED4N8SPVHX3J6K7Y03",
    "01KSFBW3ED4N8SPVHX3J6K7Y04","01KSFBW3ED4N8SPVHX3J6K7Y05",
    "01KSFBW3ED4N8SPVHX3J6K7Y06","01KSFBW3ED4N8SPVHX3J6K7Y07",
    "01KSFBW3ED4N8SPVHX3J6K7Y08","01KSFBW3ED4N8SPVHX3J6K7Y09",
    "01KSFBW3ED4N8SPVHX3J6K7Y0A","01KSFBW3ED4N8SPVHX3J6K7Y0B",
    "01KSFBW3ED4N8SPVHX3J6K7Y0C","01KSFBW3ED4N8SPVHX3J6K7Y0D",
    "01KSFBW3ED4N8SPVHX3J6K7Y0E","01KSFBW3ED4N8SPVHX3J6K7Y0F",
    "01KSFBW3ED4N8SPVHX3J6K7Y0G","01KSFBW3ED4N8SPVHX3J6K7Y0H",
    "01KSFBW3ED4N8SPVHX3J6K7Y0J","01KSFBW3ED4N8SPVHX3J6K7Y0K",
    "01KSFBW3ED4N8SPVHX3J6K7Y0M","01KSFBW3ED4N8SPVHX3J6K7Y0N",
    "01KSFBW3ED4N8SPVHX3J6K7Y0P","01KSFBW3ED4N8SPVHX3J6K7Y0Q",
    "01KSFBW3ED4N8SPVHX3J6K7Y0R","01KSFBW3ED4N8SPVHX3J6K7Y0S",
    "01KSFBW3ED4N8SPVHX3J6K7Y0T","01KSFBW3ED4N8SPVHX3J6K7Y0V",
    "01KSFBW3ED4N8SPVHX3J6K7Y0W","01KSFBW3ED4N8SPVHX3J6K7Y0X",
    "01KSFBW3ED4N8SPVHX3J6K7Y0Y","01KSFBW3ED4N8SPVHX3J6K7Y0Z",
    "01KSFBW3ED4N8SPVHX3J6K7Y10","01KSFBW3ED4N8SPVHX3J6K7Y11",
    "01KSFBW3ED4N8SPVHX3J6K7Y12","01KSFBW3ED4N8SPVHX3J6K7Y13",
    "01KSFBW3ED4N8SPVHX3J6K7Y14","01KSFBW3ED4N8SPVHX3J6K7Y15",
]

def obs(i, shortcode, content_type, capture_date, day_of_week, aspect_ratio,
        composition_style, lighting, colors, setting, visual_complexity,
        language, register, tone, notable_phrases, cta, caption_text,
        hashtag_count, has_emoji, soft_flags, compliance,
        occasion, heritage, hosp_cues, free_notes,
        patterns, engagement_potential):
    ct = "carousel_slide" if content_type == "carousel" else content_type
    cap = caption_text.strip() if caption_text else None
    return {
        "observation_ulid": ULIDS[i],
        "schema_version": 1,
        "account_handle_normalized": ACCOUNT_NORM,
        "account_ulid": ACCOUNT_ULID,
        "sector": SECTOR,
        "content_ref": {
            "filename": f"{shortcode}.jpg",
            "platform": "instagram",
            "content_type": ct,
            "capture_date": capture_date,
            "source_url": f"https://www.instagram.com/p/{shortcode}/",
            "aspect_ratio": aspect_ratio,
            "day_of_week": day_of_week,
        },
        "visual_observations": {
            "composition_style": composition_style,
            "lighting": lighting,
            "color_palette_dominant": colors,
            "setting": setting,
            "visual_complexity": visual_complexity,
        },
        "voice_observations": {
            "language": language,
            "dialect_detected": "saudi_colloquial",
            "register": register,
            "tone": tone,
            "notable_phrases": notable_phrases,
            "call_to_action_present": cta,
            "caption_text": cap,
            "caption_word_count": len(cap.split()) if cap else None,
            "hashtag_count": hashtag_count,
            "has_emoji": has_emoji,
        },
        "compliance_check": {
            "hard_blocks_triggered": [],
            "soft_flags": soft_flags,
            "overall_compliance": compliance,
        },
        "cultural_notes": {
            "regional_orientation_detected": "general_saudi",
            "occasion_relevance": occasion,
            "hospitality_cues": hosp_cues,
            "heritage_vs_modern": heritage,
            "free_notes": free_notes,
        },
        "pattern_matches": patterns,
        "quality_assessment": {
            "production_quality": "professional",
            "brand_consistency_with_account": "strong",
            "engagement_potential": engagement_potential,
        },
        "provenance": {
            "source": f"benchmark:@mcdonaldsksa; content:{shortcode}.jpg",
            "date_added": NOW,
            "confirmer": "claude_code_extraction",
            "confidence": "inferred",
            "scope": "sector:f_and_b",
        },
        "occasion": occasion,
    }

NO_FLAGS = []
CLEAN    = "clean"
SOFT_WRN = [{"flag_type": "western_collab_no_saudi_frame",
             "description": "anime_collab_western_ip_without_local_cultural_anchor"}]

records = [

  # 0 — DYuzUOMO1Pb — May 24 Sun — video landscape_16x9 — employee Rashid proud family
  obs(0,"DYuzUOMO1Pb","video","2026-05-24","sunday","landscape_16x9",
      "narrative","natural",["warm_tones","red","yellow"],"documentary","moderate",
      "arabic","conversational","warm",
      ["فخورين بولدنا","نكبر مع بعض","ما يعرف المستحيل"],False,
      "فخورين بولدنا راشد، اللي ما يعرف المستحيل ✨💪\n\nمن أول خطوة بدأها … لين حقق الإنجازات ❤️👏\nوحنا في ماكدونالدز نؤمن بطموح عيالنا، ونفتخر بنجاحهم في كل خطوة 😍❤️\n\n#نكبر_مع_بعض\n#ماك_منكم_وفيكم",
      2,True,NO_FLAGS,CLEAN,
      "evergreen","modern",["فخورين بولدنا"],
      "Employee pride campaign #نكبر_مع_بعض. Emotional narrative video of employee Rashid's journey.",
      [{"pattern_slug":"employee_pride_campaign","confidence":"strong","notes":"#نكبر_مع_بعض series"}],
      "high"),

  # 1 — DYumim3o1Hh — May 24 Sun — video vertical_9x16 — new branch Dammam road
  obs(1,"DYumim3o1Hh","video","2026-05-24","sunday","vertical_9x16",
      "wide_shot","natural",["red","yellow","white"],"restaurant_exterior","simple",
      "arabic","casual","warm",
      ["حياكم الله","المكان مكانكم","تنورونا"],True,
      "حياكم الله… وترا المكان مكانكم 😍🍔\nننتظركم تنورونا في فرعنا الجديد على طريق الدمام - الرياض السريع📍\n\nخلونا نشوفكم 🥳❤️",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",["حياكم الله","تنورونا","المكان مكانكم"],
      "New branch opening on Dammam-Riyadh highway. Warm invitation using traditional Saudi hospitality language.",
      [{"pattern_slug":"new_location_announcement","confidence":"strong","notes":"hospitality openers"}],
      "medium"),

  # 2 — DYt6B8ZuR5a — May 24 Sun — image square_1x1 — food safety global award
  obs(2,"DYt6B8ZuR5a","image","2026-05-24","sunday","square_1x1",
      "text_graphic","artificial",["red","white","gold"],"studio","simple",
      "arabic","formal","informative",
      ["سلامة الغذاء هي أولويتنا","جائزة سلامة الغذاء العالمية"],False,
      "سلامة الغذاء هي أولويتنا الأولى دائماً\nفي ماكدونالدز السعودية وفخورون بحصولنا على جائزة سلامة الغذاء العالمية من ماكدونالدز عشان عيوننا دائماً على سلامة أطعمتنا وجودتها ونفخر بتطبيقنا لأعلى معايير سلامة الغذاء في كل خطوة بدءاً من مزارع مختارة وموردين معتمدين إلى أن يتم تحضيرها في مطاعمنا",
      0,False,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Global food safety award announcement. Formal tone, long educational caption. Trust-building content pillar.",
      [{"pattern_slug":"csr_food_safety","confidence":"strong","notes":"global award, supply chain transparency"}],
      "medium"),

  # 3 — DYrmcyRoY5i — May 23 Sat — video landscape_16x9 — employee Mansour journey
  obs(3,"DYrmcyRoY5i","video","2026-05-23","saturday","landscape_16x9",
      "narrative","artificial",["yellow","red","warm_tones"],"restaurant_interior","moderate",
      "arabic","conversational","warm",
      ["فخورين بولدنا","النجاح مع ماك يبدأ بخطوة","نكبر مع بعض"],False,
      "فخورين بولدنا منصور ورحلته اللي تكبر يوم بعد يوم ✨\nلأن النجاح مع ماك يبدأ بخطوة \nويكبر بالشغف والدعم والطموح 💪❤️\nودعم عيالنا وبناتنا هو أكبر إنجاز نفتخر فيه كل يوم عشاننا دايم #نكبر_مع_بعض\n#ماك_منكم_وفيكم",
      2,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Employee Mansour narrative video. #نكبر_مع_بعض campaign. Career growth messaging.",
      [{"pattern_slug":"employee_pride_campaign","confidence":"strong","notes":"Mansour career story"}],
      "high"),

  # 4 — DYrR2WuuzKH — May 23 Sat — image portrait_4x5 — Grand Chicken Special product
  obs(4,"DYrR2WuuzKH","image","2026-05-23","saturday","portrait_4x5",
      "product_hero","artificial",["red","gold","brown"],"studio","simple",
      "arabic","casual","enthusiastic",
      ["كافي ووافي","طعم رهيب","اكبر من جوعك"],False,
      "جراند تشيكن سبيشل كافي ووافي! طعم رهيب ومميز مع دجاج مقرمش وغرقان بصوصه الديجون. راح يشبعك أكيد! 🍔✨\n#اكبر_من_جوعك",
      1,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Grand Chicken Special product spotlight. Taste-focused short caption. #اكبر_من_جوعك brand tagline.",
      [{"pattern_slug":"product_spotlight","confidence":"strong","notes":"taste description, single hashtag"}],
      "medium"),

  # 5 — DYpQm2_o3A9 — May 22 Fri — image portrait_4x5 — 4 McNuggets for 1 SAR deal
  obs(5,"DYpQm2_o3A9","image","2026-05-22","friday","portrait_4x5",
      "product_hero","artificial",["red","yellow","white"],"studio","moderate",
      "arabic","casual","playful",
      ["وش يجيب لك الريال","4 = 1","ماك ناجتس بريال"],True,
      "وش يجيب لك الريال هالأيام؟ يجيب لك 4 حبات ماك ناجتس تقرمشها وتضبط جوك! 🤩🍟\nقفلنا ملف الأسعار في تطبيق ماكدونالدز وصنعنا المعادلة الصعبة: 4 = 1 🎯\nحصرياً من تطبيق ماكدونالدز\nمن الساعة 6م الى 11م 🥳\n#ماك_ناجتس_بريال",
      1,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "4 McNuggets for 1 SAR — app exclusive 6–11PM deal. Question opener. Strong value equation mechanic.",
      [{"pattern_slug":"value_deal_activation","confidence":"strong","notes":"1 SAR price anchor, app exclusive"},
       {"pattern_slug":"app_exclusive_offer","confidence":"strong","notes":"time-limited 6PM-11PM"}],
      "high"),

  # 6 — DYpMMEqiAde — May 22 Fri — carousel landscape_16x9 — Down Syndrome CSR 1.1M SAR
  obs(6,"DYpMMEqiAde","carousel","2026-05-22","friday","landscape_16x9",
      "documentary","natural",["red","white","warm_tones"],"event","moderate",
      "arabic","formal","grateful",
      ["كل مساهمة منكم صنعت فرق","بفضل الله","شركاء في صنع كل فرحة"],False,
      "كل مساهمة منكم صنعت فرق ❤️✨\nبفضل الله ثم مساندتكم لحملة #دعمك_يكمل_قصتهم\nدعمنا 6 برامج بالتعاون مع الجمعيات\nوبمبلغ 1,132,800 ريال ووصل أثرها لـ 145 طفل من ذوي #متلازمة_داون 😍❤️\n\nشكرًا لأنكم شركاء في صنع كل فرحة وابتسامة 💪\n#منكم__وفيكم",
      3,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "CSR campaign results: 1,132,800 SAR raised, 145 Down Syndrome children supported. Community co-ownership framing.",
      [{"pattern_slug":"csr_community_impact","confidence":"strong","notes":"Down Syndrome charity, specific SAR amount builds trust"}],
      "high"),

  # 7 — DYnQ5_Ru5_Y — May 21 Thu — image portrait_4x5 — Al Nassr wins Saudi League
  obs(7,"DYnQ5_Ru5_Y","image","2026-05-21","thursday","portrait_4x5",
      "graphic_text","artificial",["yellow","blue","red"],"graphic","moderate",
      "arabic","casual","celebratory",
      ["رسمياً","ألف مبروك","هاردلك","الوجبات المجانية"],True,
      "رسمياً.. النصر بطل الدوري السعودي! 🟡👑\nألف مبروك لجماهير النصر اللقب المستحق. وهاردلك لجماهير الهلال احتفلوا، والسحب على الوجبات المجانية بالخاص بعد شوي! 🏆🍔\n#الدوري_السعودي #النصر #الهلال #ديربي_ماك",
      4,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Al Nassr Saudi League title. Playful bilingual tone (هاردلك = hard luck). Free meal giveaway teaser. High cultural moment.",
      [{"pattern_slug":"sports_cultural_moment","confidence":"strong","notes":"Al Nassr title, Al-Hilal consolation joke"},
       {"pattern_slug":"giveaway_mechanic","confidence":"strong","notes":"free meals via DM"}],
      "high"),

  # 8 — DYXTyvAoN6a — May 15 Fri — video vertical_9x16 — Little Tasty 17 SAR
  obs(8,"DYXTyvAoN6a","video","2026-05-15","friday","vertical_9x16",
      "product_hero","artificial",["red","white","gold"],"studio","simple",
      "arabic","casual","casual",
      ["طعم تعرفه وسعر يعجبك","ليتل تايستي"],False,
      "طعم تعرفه وسعر يعجبك 😎\nليتل تايستي بـ 17 ريال بس 🔥",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Little Tasty 17 SAR vertical video. Short punchy copy. Taste familiarity + price value positioning.",
      [{"pattern_slug":"product_value_positioning","confidence":"strong","notes":"familiar taste + low price"}],
      "medium"),

  # 9 — DYWv5ntCNiz — May 15 Fri — image portrait_4x5 — Friday family + Jalapeño Bites deal
  obs(9,"DYWv5ntCNiz","image","2026-05-15","friday","portrait_4x5",
      "lifestyle","natural",["warm_tones","red","gold"],"lifestyle","moderate",
      "arabic","casual","warm",
      ["لمه الاهل","شباك السعادة","جمعة","تستاهله"],True,
      "جمعة، لمه الاهل، ومتضبط ومتَبخر 📿، كملها ومر شباك السعادة وخل الغدا عليك، وابشر بعرض الويكند اللي تستاهله 🔥😎\nجالابينو تشيز بايتس بـ 5 ريال بس مع أي وجبة 🍔🥤🍟",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","blended",["شباك السعادة"],
      "Friday jumaa cultural moment activation. Rich Saudi dialect, bakhoor reference (📿), family gathering framing. Jalapeño Bites 5 SAR offer woven in naturally.",
      [{"pattern_slug":"cultural_moment_activation","confidence":"strong","notes":"jumaa family gathering, bakhoor reference"},
       {"pattern_slug":"weekend_deal","confidence":"strong","notes":"5 SAR deal embedded in cultural frame"}],
      "high"),

  # 10 — DYVTexzDgz5 — May 14 Thu — carousel square_1x1 — weekend Jalapeño deal
  obs(10,"DYVTexzDgz5","carousel","2026-05-14","thursday","square_1x1",
      "product_hero","artificial",["red","yellow","white"],"drive_thru","simple",
      "arabic","casual","casual",
      ["شباك السعادة","خلها ألذ","فره الويكند"],True,
      "فره الويكند المعتادة؟\nخلها ألذ مع #العرض الحصري جالابينو تشيز بايتس بـ 5 ريال بس مع أي وجبة من #شباك_السعادة 🚗",
      2,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Weekend drive-thru deal. Question opener. #شباك_السعادة = branded drive-thru name.",
      [{"pattern_slug":"weekend_deal","confidence":"strong","notes":"5 SAR jalapeño bites, drive-thru framing"}],
      "medium"),

  # 11 — DYVOlJ6OdeL — May 14 Thu — image portrait_4x5 — employee Ziad #1 award
  obs(11,"DYVOlJ6OdeL","image","2026-05-14","thursday","portrait_4x5",
      "portrait","artificial",["red","gold","white"],"studio","simple",
      "arabic","conversational","proud",
      ["فخورين بولدنا البطل","المساهمة المتميزة","نكبر مع بعض"],False,
      "فخورين بولدنا البطل زياد مدير إدارة المنيو، لفوزه بالمركز الأول بجائزة المساهمة المتميزة على مستوى ماكدونالدز السعودية 💪🤩\nنجاح نفخر فيه، وإنجاز يعكس شغف وطموح عيالنا اللي نكبر ونفتخر فيهم كل يوم ❤️\n#ماك_منكم_وفيكم\n#نكبر_مع_بعض",
      2,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Employee spotlight: Ziad wins #1 outstanding contribution award Saudi-wide. Achievement highlight in #نكبر_مع_بعض series.",
      [{"pattern_slug":"employee_pride_campaign","confidence":"strong","notes":"award spotlight, Ziad menu manager"}],
      "high"),

  # 12 — DYUjfOsjGQS — May 14 Thu — image square_1x1 — weekend deal launch
  obs(12,"DYUjfOsjGQS","image","2026-05-14","thursday","square_1x1",
      "product_hero","artificial",["red","yellow","white"],"studio","simple",
      "arabic","casual","enthusiastic",
      ["عرض الويكند وصل","شباك السعادة"],True,
      "عرض الويكند وصل! 📣🧀\n\nجالابينو تشيز بايتس بـ 5 ريال بس مع أي وجبة من شباك السعادة 🚗💨",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Weekend deal arrival announcement. Short punchy format. Drive-thru call to action.",
      [{"pattern_slug":"weekend_deal_announcement","confidence":"strong","notes":"jalapeño 5 SAR, drive-thru"}],
      "medium"),

  # 13 — DYSljJ8o1x7 — May 13 Wed — video landscape_16x9 — employee Ashjan female story
  obs(13,"DYSljJ8o1x7","video","2026-05-13","wednesday","landscape_16x9",
      "narrative","artificial",["red","yellow","warm_tones"],"restaurant_interior","moderate",
      "arabic","conversational","inspiring",
      ["فخورين ببنتنا","قصة نجاح مع ماك تبدأ بخطوة","نكبر مع بعض"],False,
      "فخورين ببنتنا أشجان وقصتها الملهمة\nلأن كل قصة نجاح مع ماك تبدأ بخطوة 💪\nاستثمارنا ودعم عيالنا وبناتنا هو مصدر فخر نعيشه كل يوم❤️\nعشاننا #نكبر_مع_بعض\n#ماك_منكم_وفيكم",
      2,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Female employee Ashjan inspiring story video. Explicit 'daughters' mention — Vision 2030 female empowerment alignment.",
      [{"pattern_slug":"employee_pride_campaign","confidence":"strong","notes":"female employee, Ashjan story"},
       {"pattern_slug":"female_empowerment","confidence":"moderate","notes":"بناتنا explicit, Vision 2030 echo"}],
      "high"),

  # 14 — DYSGnC2ooyP — May 13 Wed — video vertical_9x16 — Little Tasty equation
  obs(14,"DYSGnC2ooyP","video","2026-05-13","wednesday","vertical_9x16",
      "product_hero","artificial",["red","white","gold"],"studio","simple",
      "arabic","casual","playful",
      ["طعم أسطوري + سعر رهيب","بلا منازع","ليتل تايستي"],False,
      "ليتل تايستي طعم أسطوري + سعر رهيب = غداء اليوم (أو عشاء متأخر) بلا منازع! 🍔🔥",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Little Tasty humor equation format: taste + price = unbeatable. Very short playful caption.",
      [{"pattern_slug":"product_value_positioning","confidence":"strong","notes":"equation format humor, Little Tasty"}],
      "medium"),

  # 15 — DYR85d0IFlJ — May 13 Wed — image portrait_4x5 — JJK spot-the-error trivia
  obs(15,"DYR85d0IFlJ","image","2026-05-13","wednesday","portrait_4x5",
      "graphic_text","artificial",["dark_purple","white","red"],"graphic","moderate",
      "arabic","casual","playful",
      ["ماك مع ججك","وبنعشيهم","لو تذكر"],True,
      "لو تذكر احداث النزال اللي صار بين ايتادوري ونانامي ضد ماهيتو راح تعرف وش المعلومة الخطأ بالصورة 👌👀\n\nفولو ولايك وعلمنا وش الخطأ بالجملة وبنختار 20 شخص من اللي صادوها صح بنعشيهم🍔❤️\n\n#ماك_مع_ججك",
      1,True,SOFT_WRN,"soft_flagged",
      "evergreen","neutral",[],
      "JJK (Jujutsu Kaisen) anime collab. Spot-the-error trivia mechanic with free meal prize for 20 correct answers. Strong engagement mechanic.",
      [{"pattern_slug":"entertainment_collab","confidence":"strong","notes":"JJK/Jujutsu Kaisen IP"},
       {"pattern_slug":"trivia_giveaway","confidence":"strong","notes":"20 winners free meal, spot the error"}],
      "high"),

  # 16 — DYPhVBWohUm — May 12 Tue — image portrait_4x5 — contest winners, derby tickets
  obs(16,"DYPhVBWohUm","image","2026-05-12","tuesday","portrait_4x5",
      "announcement","artificial",["yellow","blue","red"],"graphic","moderate",
      "arabic","casual","celebratory",
      ["جهزوا الأطقم","الوعد في الملعب","مسابقات ماك وعيدياته ما تخلص"],False,
      "جهزوا الأطقم.. الوعد في الملعب! 💙💛\n\nالف مبروك للي حالفهم الحظ معنا بـ تذاكر لمباراة #النصر_الهلال في مسابقة #تابع_ماك\n\nشكرًا لكل اللي شاركوا وتفاعلوا.. تابعونا، مسابقات ماك وعيدياته ما تخلص! 😉🎈🎁",
      2,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Contest winners announcement for derby tickets. Excitement build. Teases ongoing giveaway series.",
      [{"pattern_slug":"giveaway_winner_announcement","confidence":"strong","notes":"derby tickets, Al Nassr vs Al Hilal"},
       {"pattern_slug":"sports_tie_in","confidence":"strong","notes":"Saudi Pro League final"}],
      "high"),

  # 17 — DYPQLAfoJg9 — May 12 Tue — video vertical_9x16 — Little Tasty Chicken 17 SAR
  obs(17,"DYPQLAfoJg9","video","2026-05-12","tuesday","vertical_9x16",
      "product_hero","artificial",["red","white","gold"],"studio","simple",
      "arabic","casual","casual",
      ["ليتل تايستي","يسكت جوعك"],False,
      "ليتل تايستي دجاج… طعم كبير يسكت جوعك بـ 17 ريال بس 😋🍔",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Little Tasty Chicken vertical video. Ultra-short copy. يسكت جوعك = silences your hunger.",
      [{"pattern_slug":"product_value_positioning","confidence":"strong","notes":"Little Tasty 17 SAR"}],
      "medium"),

  # 18 — DYPDinHM1EE — May 12 Tue — image square_1x1 — halal beef quality trust
  obs(18,"DYPDinHM1EE","image","2026-05-12","tuesday","square_1x1",
      "product_hero","artificial",["red","white","natural"],"studio","simple",
      "arabic","conversational","trustworthy",
      ["لذة الطعم تبدأ من لحم البقر الحلال","صافي وبدون أي مواد حافظه"],True,
      "لذة الطعم تبدأ من لحم البقر الحلال ✨🥩\nولذة الطعم بكل التفاصيل هي بسبب أنه صافي وبدون أي مواد حافظه💯💪\nزور موقعنا واعرف أكثر عن أسرار الأكل اللذيذ اللي تحبه❤️",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","blended",[],
      "Halal beef quality messaging. No preservatives claim. Website CTA. Trust-building pillar aligned to Saudi Islamic values.",
      [{"pattern_slug":"halal_trust_messaging","confidence":"strong","notes":"halal certification, no preservatives"}],
      "medium"),

  # 19 — DYNNhk1iOiN — May 11 Mon — image square_1x1 — Chicken Burger 1 SAR pre-order
  obs(19,"DYNNhk1iOiN","image","2026-05-11","monday","square_1x1",
      "product_hero","artificial",["red","yellow","white"],"studio","simple",
      "arabic","casual","casual",
      ["من جدنا","بريال واحد بس"],True,
      "ترا من جدنا بـ 1 ريال بس!! 🍔🔥\nاطلب مسبقاً تشيكن برجر بريال واحد بس 🤭 مرّنا الحين 📲",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Chicken Burger 1 SAR via app pre-order. من جدنا = Saudi casual intensifier. Strong value anchor.",
      [{"pattern_slug":"value_deal_activation","confidence":"strong","notes":"1 SAR chicken burger, pre-order mechanic"},
       {"pattern_slug":"app_exclusive_offer","confidence":"strong","notes":"app pre-order required"}],
      "high"),

  # 20 — DYNH9h_DMIy — May 11 Mon — image portrait_4x5 — derby tickets giveaway mechanics
  obs(20,"DYNH9h_DMIy","image","2026-05-11","monday","portrait_4x5",
      "graphic_text","artificial",["yellow","blue","red"],"graphic","moderate",
      "arabic","casual","exciting",
      ["جهزوا الأعلام","تذاكر الديربي وصلت","انطلقوا"],True,
      "جهزوا الأعلام.. تذاكر الديربي وصلت! 🚩🏟️\nشخصين محظوظين بيحضرون مباراة #النصر_الهلال بكرة مع مسابقة #تابع_ماك\n\nكيف تدخل السحب؟\n🔹 فولو + لايك.\n🔹 منشن اثنين من اخوياك يشاركون.\n🔹 علق ب ايموجي يمثل فريقك 💛💙\n\nالفرصة قدامك والسحب بكرة.. انطلقوا! 🚀🥳",
      2,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Derby ticket giveaway full mechanics reveal. Three-step engagement ladder (follow+like, tag 2, team emoji). High engagement mechanic.",
      [{"pattern_slug":"sports_giveaway","confidence":"strong","notes":"Al Nassr vs Al Hilal derby tickets"},
       {"pattern_slug":"engagement_mechanics","confidence":"strong","notes":"3-step entry: follow, tag, emoji"}],
      "high"),

  # 21 — DYNGnEMiEJe — May 11 Mon — image portrait_4x5 — derby teaser follow bell
  obs(21,"DYNGnEMiEJe","image","2026-05-11","monday","portrait_4x5",
      "graphic_text","artificial",["yellow","blue","red"],"graphic","simple",
      "arabic","casual","teasing",
      ["ديربي حسم الدوري","خلك قريّب"],True,
      "تبي تحضر ديربي حسم الدوري ؟🏆\n\nفولو وفعل الجرس وخلك قريّب 🫡",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Derby giveaway teaser post. Minimal copy, maximum suspense. Follow + bell CTA.",
      [{"pattern_slug":"sports_teaser","confidence":"strong","notes":"teaser for derby ticket giveaway"},
       {"pattern_slug":"follow_cta","confidence":"strong","notes":"follow + notification bell"}],
      "medium"),

  # 22 — DYM_lK1CCOK — May 11 Mon — image portrait_4x5 — meme engagement caption
  obs(22,"DYM_lK1CCOK","image","2026-05-11","monday","portrait_4x5",
      "graphic_text","artificial",["red","white","yellow"],"graphic","simple",
      "arabic","casual","playful",
      ["وش تقولون","منشن لخويك","ابداعاتكم"],True,
      "وانتم وش تقولون 😎\nمنشن لخويك خلنا نشوف ابداعاتكم في الوصف 😂",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Meme/reaction engagement post. Tag a friend mechanic. Very short, high comment volume likely.",
      [{"pattern_slug":"engagement_mechanic","confidence":"strong","notes":"caption contest, tag-a-friend"}],
      "high"),

  # 23 — DYMxeGZiAeR — May 11 Mon — image square_1x1 — 438 branches Oxford Economics report
  obs(23,"DYMxeGZiAeR","image","2026-05-11","monday","square_1x1",
      "graphic_infographic","artificial",["red","white","gray"],"graphic","moderate",
      "arabic","formal","informative",
      ["نقرب منكم ونكبر معكم","438 فرع","أثر ماك واصل"],True,
      "نقرب منكم ونكبر معكم ونفخر بخدمتكم\n\nوفق تقرير شركة Oxford Economics المستقلة للفترة أبريل 2024 إلى مارس 2025، وصل عدد فروع ماكدونالدز حول السعودية إلى 438 فرع خلال سنة واحدة ونطمح لأكثر!\n\n#أثر_ماك_واصل",
      1,False,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Oxford Economics impact report: 438 KSA branches in one year. Third-party credibility. Scale and ambition messaging.",
      [{"pattern_slug":"csr_impact_reporting","confidence":"strong","notes":"438 branches, Oxford Economics citation"},
       {"pattern_slug":"brand_scale_communication","confidence":"strong","notes":"national footprint, ambitious tone"}],
      "medium"),

  # 24 — DYMnG2NjAAq — May 11 Mon — image square_1x1 — employee Mansour first-person story
  obs(24,"DYMnG2NjAAq","image","2026-05-11","monday","square_1x1",
      "portrait","artificial",["red","warm_tones","white"],"studio","simple",
      "arabic","conversational","inspiring",
      ["أنا منصور","خطوة بعد خطوة","عائلة ماكدونالدز","كبرت مع التجربة"],False,
      "\"أنا منصور، بديت رحلتي مع عائلة ماكدونالدز كطاقم خدمة، ومن أول يوم لقيت دعم كبير بالعمل خلاني أستمر وأتطور ❤️\n\nخطوة بعد خطوة، قطعت مراحل كثيرة في رحلتي وقدرت أحقق ترقيات كثيرة، وكل مرحلة كانت تعلمني شي جديد وتكبرني بالمعرفة أكثر\nكبرت مع التجربة\"",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Employee Mansour first-person long-form story. Service crew to manager. عائلة ماكدونالدز = 'McDonald's family' branding.",
      [{"pattern_slug":"employee_story_first_person","confidence":"strong","notes":"Mansour, crew to multiple promotions"},
       {"pattern_slug":"employee_pride_campaign","confidence":"strong","notes":"#نكبر_مع_بعض series"}],
      "high"),

  # 25 — DYMVXGyDr95 — May 11 Mon — image portrait_4x5 — Chicken Burger 1 SAR pre-order
  obs(25,"DYMVXGyDr95","image","2026-05-11","monday","portrait_4x5",
      "product_hero","artificial",["red","yellow","white"],"studio","simple",
      "arabic","casual","exciting",
      ["بريال بس","الطلبات المسبقة"],True,
      "بريااااااال بس 🤑\nالتشيكن برجر صارت بريال بس من الطلبات المسبقة من تطبيقنا",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Chicken Burger 1 SAR pre-order. Extended vowel spelling (بريااال) for excitement. App pre-order mechanic.",
      [{"pattern_slug":"value_deal_activation","confidence":"strong","notes":"1 SAR chicken burger"},
       {"pattern_slug":"app_exclusive_offer","confidence":"strong","notes":"pre-order app required"}],
      "high"),

  # 26 — DYKTWdAjAMW — May 10 Sun — image portrait_4x5 — open kitchen tour
  obs(26,"DYKTWdAjAMW","image","2026-05-10","sunday","portrait_4x5",
      "lifestyle","artificial",["red","white","stainless_steel"],"restaurant_kitchen","simple",
      "arabic","conversational","inviting",
      ["فتحنا لك مطبخنا","تعيش التجربة من الداخل","حياك"],True,
      "تبي تشوف الذ برجر كيف يتحضر 🍔\nفتحنا لك مطبخنا، عشان تعيش التجربة من الداخل 👀✨\n\nسجّل جولتك من الرابط وحياك في الوقت اللي يناسبك\nmcdopendoor.com",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",["حياك"],
      "Open kitchen transparency initiative. mcdopendoor.com registration. Trust and authenticity pillar.",
      [{"pattern_slug":"transparency_initiative","confidence":"strong","notes":"open kitchen tour, mcdopendoor.com"},
       {"pattern_slug":"brand_trust_building","confidence":"strong","notes":"show how the burger is made"}],
      "medium"),

  # 27 — DYKMceGCHaG — May 10 Sun — image portrait_4x5 — JJK character road trip
  obs(27,"DYKMceGCHaG","image","2026-05-10","sunday","portrait_4x5",
      "graphic_text","artificial",["dark_purple","white","red"],"graphic","moderate",
      "arabic","casual","playful",
      ["ماك مع ججك","تعاون ماك","وبتمسك خط"],True,
      "لو عندك سفرة مستعجلة وبتمسك خط مين الشخصية من الشخصيات الـ 8 اللي ودك تخاويك؟ 🚘🧐\n\nفولو ولايك واكتب اسم الشخصية اللي تبيها😍😎\n\n#ماك_مع_ججك\n#تعاون_ماك",
      2,True,SOFT_WRN,"soft_flagged",
      "evergreen","neutral",[],
      "JJK (Jujutsu Kaisen) collab engagement post. Road trip hypothetical: choose 1 of 8 characters. Comment activation.",
      [{"pattern_slug":"entertainment_collab","confidence":"strong","notes":"JJK 8-character lineup"},
       {"pattern_slug":"engagement_mechanic","confidence":"strong","notes":"choose character comment mechanic"}],
      "high"),

  # 28 — DYKC7F-iDOI — May 10 Sun — image square_1x1 — employee Rashid operations consultant
  obs(28,"DYKC7F-iDOI","image","2026-05-10","sunday","square_1x1",
      "portrait","artificial",["red","warm_tones","white"],"studio","simple",
      "arabic","conversational","inspiring",
      ["أنا راشد","مدير مطعم تحت التدريب","استشاري عمليات"],False,
      "\"أنا راشد، كانت بدايتي مع عائلة ماكدونالدز في برنامج طموح كـ مدير مطعم تحت التدريب، وكنت في كل يوم اتعلم شي جديد، وكل خطوة وترقية في رحلتي معهم كانت تطورني وتخليني أقوى💪\nواللي شجعني هو الدعم الكبير اللي لقيته في العمل\nواليوم أفتخر إني وصلت لمنصب استشاري عمليات\"",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Employee Rashid first-person story. Restaurant manager trainee to operations consultant. Structured career progression narrative.",
      [{"pattern_slug":"employee_story_first_person","confidence":"strong","notes":"Rashid, trainee to consultant"},
       {"pattern_slug":"employee_pride_campaign","confidence":"strong","notes":"#نكبر_مع_بعض series"}],
      "high"),

  # 29 — DYINvd6Dsf5 — May 9 Sat — carousel portrait_4x5 — JJK tag-a-friend resembles character
  obs(29,"DYINvd6Dsf5","carousel","2026-05-09","saturday","portrait_4x5",
      "graphic_text","artificial",["dark_purple","white","red"],"graphic","moderate",
      "arabic","casual","playful",
      ["ماك مع ججك","منشن خويك","فيه صفة من صفات"],True,
      "فولو ولايك ومنشن خويك اللي فيه صفة من صفات شخصيات ججك وقوله مين يشبهه 😉🏃‍♂️🏃‍♂️\n\n#تعاون_ماك\n#ماك_مع_ججك",
      2,True,SOFT_WRN,"soft_flagged",
      "evergreen","neutral",[],
      "JJK collab carousel. Tag-a-friend resembles anime character. High comment/tag volume mechanic.",
      [{"pattern_slug":"entertainment_collab","confidence":"strong","notes":"JJK characters carousel"},
       {"pattern_slug":"tag_a_friend","confidence":"strong","notes":"tag friend who resembles character"}],
      "high"),

  # 30 — DYHdBORCFz_ — May 10 Sun — image square_1x1 — employee Omar restaurant manager
  obs(30,"DYHdBORCFz_","image","2026-05-10","sunday","square_1x1",
      "portrait","artificial",["red","warm_tones","white"],"studio","simple",
      "arabic","conversational","inspiring",
      ["أنا عمر","مدير مطعم تحت التدريب","الحمدلله","كبرت مع التجربة"],False,
      "\"أنا عمر، بديت رحلتي مع ماكدونالدز في برنامج طموح كـ مدير مطعم تحت التدريب، والحمدلله لقيت مرونة ودعم كبير بالعمل\nكان طموحي كبير وكل يوم كان فرصة أتعلم شي جديد في ماكدونالدز\nكبرت مع التجربة، ومع الناس اللي حولي والدعم اللي شفته من ماك\"",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Employee Omar first-person story. Restaurant manager trainee program. Flexibility and support messaging.",
      [{"pattern_slug":"employee_story_first_person","confidence":"strong","notes":"Omar, manager trainee program"},
       {"pattern_slug":"employee_pride_campaign","confidence":"strong","notes":"#نكبر_مع_بعض series"}],
      "high"),

  # 31 — DYFflDyCDP_ — May 8 Thu — image portrait_4x5 — free delivery Thu–Sat
  obs(31,"DYFflDyCDP_","image","2026-05-08","thursday","portrait_4x5",
      "graphic_text","artificial",["red","yellow","white"],"graphic","simple",
      "arabic","casual","direct",
      ["التوصيل مجاني","حصرياً عبر تطبيق ماكدونالدز"],True,
      "التوصيل مجاني 🚘👀\n\nمن اليوم الى يوم السبت اطلب كل اللي تبيه واستمتع بتوصيل مجاني حصرياً عبر تطبيق ماكدونالدز 🤩📲",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Free delivery app offer Thu–Sat. Short direct copy. 🚘 emoji signals delivery theme.",
      [{"pattern_slug":"delivery_promo","confidence":"strong","notes":"free delivery 3-day window, app only"},
       {"pattern_slug":"app_exclusive_offer","confidence":"strong","notes":"app exclusive framing"}],
      "medium"),

  # 32 — DYFcFK_DPna — May 8 Thu — image portrait_4x5 — King's Cup Final giveaway iPhone17+PS5
  obs(32,"DYFcFK_DPna","image","2026-05-08","thursday","portrait_4x5",
      "graphic_text","artificial",["yellow","blue","white"],"graphic","moderate",
      "arabic","casual","exciting",
      ["اغلى الكؤوس","ايفون 17","ديربي ماك","توقع مين بطل"],True,
      "جاهزين لتوقعات اغلى الكؤوس؟🔥🔥🔥⚽️\n\nفولو ولايك وتوقع مين بطل نهائى كأس الملك 🏆\nوبنسحب بشكل عشوائي على\nايفون 17 📱\nوبلايستيشن 5 🎮\n\n#ديربي_ماك #الهلال_الخلود #كاس_الملك",
      3,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "King's Cup Final prediction giveaway. iPhone 17 + PS5 prizes. High-value incentive. Al Hilal vs Al Khulood.",
      [{"pattern_slug":"sports_giveaway","confidence":"strong","notes":"King's Cup Final, iPhone 17 + PS5"},
       {"pattern_slug":"high_value_prize","confidence":"strong","notes":"premium tech prizes drive engagement"}],
      "high"),

  # 33 — DYFGGROCEKx — May 8 Thu — image portrait_4x5 — JJK character power transfer
  obs(33,"DYFGGROCEKx","image","2026-05-08","thursday","portrait_4x5",
      "graphic_text","artificial",["dark_purple","white","red"],"graphic","moderate",
      "arabic","casual","playful",
      ["ماك مع ججك","تعاون ماك","تشيل قوة","الباندا"],True,
      "لو يمديك تشيل قوة من شخصية الباندا وتضيفها لشخصية ثانيه من شخصيات #ججك ⚡️🐼\n\nمين الشخصية اللي بتختارها؟👀\n\n#تعاون_ماك\n#ماك_مع_ججك",
      3,True,SOFT_WRN,"soft_flagged",
      "evergreen","neutral",[],
      "JJK collab: hypothetical power transfer between characters (Panda's power to another). Anime fan engagement.",
      [{"pattern_slug":"entertainment_collab","confidence":"strong","notes":"JJK Panda character power mechanics"},
       {"pattern_slug":"engagement_mechanic","confidence":"strong","notes":"hypothetical fan discussion prompt"}],
      "high"),

  # 34 — DYE-LE7CNjG — May 8 Thu — image portrait_4x5 — Little Tasty taste+savings
  obs(34,"DYE-LE7CNjG","image","2026-05-08","thursday","portrait_4x5",
      "product_hero","artificial",["red","white","gold"],"studio","simple",
      "arabic","casual","casual",
      ["طعم رهيب + توفير","ليتل تايستي","تسكت جوعك"],False,
      "إذا تبي طعم رهيب + توفير 🤑👀\nليتل تايستي تسكت جوعك\nوتوفر ميزانيتك 😎🍔",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Little Tasty taste+savings dual benefit framing. Short formula copy. تسكت جوعك = silences your hunger.",
      [{"pattern_slug":"product_value_positioning","confidence":"strong","notes":"Little Tasty dual benefit: taste + savings"}],
      "medium"),

  # 35 — DYDUcn-DhpT — May 7 Wed — image portrait_4x5 — JJK enter the world engagement
  obs(35,"DYDUcn-DhpT","image","2026-05-07","wednesday","portrait_4x5",
      "graphic_text","artificial",["dark_purple","white","red"],"graphic","moderate",
      "arabic","casual","playful",
      ["ماك مع ججك","تدخل عالم ججك","فولو ولايك"],True,
      "لو عندك فرصة تدخل عالم #ججك👀🔥\n\nفولو ولايك واكتب لنا مين أول شخصية\nبتروح لها ووش راح تقول له؟ 😎\n\n#ماك_مع_ججك\n#تعاون_ماك",
      3,True,SOFT_WRN,"soft_flagged",
      "evergreen","neutral",[],
      "JJK collab: enter the anime world hypothetical. High comment activation. Which character would you visit first?",
      [{"pattern_slug":"entertainment_collab","confidence":"strong","notes":"JJK world entry hypothetical"},
       {"pattern_slug":"comment_activation","confidence":"strong","notes":"character + quote comment mechanic"}],
      "high"),

  # 36 — DYC5n-7DpmA — May 7 Wed — image portrait_4x5 — free delivery extension
  obs(36,"DYC5n-7DpmA","image","2026-05-07","wednesday","portrait_4x5",
      "graphic_text","artificial",["red","yellow","white"],"graphic","simple",
      "arabic","casual","warm",
      ["كلمتكم ماتتثنى","التوصيل المجاني مستمر","مكملين معكم"],True,
      "كلمتكم ماتتثنى\nالتوصيل المجاني مستمر! 😎\n\nمكملين معكم بالتوصيل المجاني من اليوم إلى السبت حصرياً عبر تطبيق ماكدونالدز اطلب الحين 🚘📲",
      0,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "Free delivery extension. كلمتكم ماتتثنى = 'your word is unrefusable' — community responsiveness framing. Warm tone.",
      [{"pattern_slug":"delivery_promo","confidence":"strong","notes":"free delivery extended through Saturday"},
       {"pattern_slug":"community_responsiveness","confidence":"moderate","notes":"responding to customer demand"}],
      "medium"),

  # 37 — DYC4SsLDpA6 — May 7 Wed — image portrait_4x5 — King's Cup giveaway teaser
  obs(37,"DYC4SsLDpA6","image","2026-05-07","wednesday","portrait_4x5",
      "graphic_text","artificial",["yellow","blue","white"],"graphic","simple",
      "arabic","casual","teasing",
      ["اغلى الكؤوس","ايفون 17 وبلايستيشن 5","فعلوا التنبيهات"],True,
      "ايفون 17 وبلايستيشن 5...\nللي يتوقع بطل الكأس📱🎮\nباقي تكّة ونعلن عن مسابقة نهائي أغلى الكؤوس 🏆\nالهلال 🆚 الخلود\n\nفعلوا التنبيهات وخلّكم قريّبين منا 🔥🔥\n\n#الهلال #الخلود\n#كاس_الملك",
      3,True,NO_FLAGS,CLEAN,
      "evergreen","modern",[],
      "King's Cup Final giveaway teaser. iPhone 17 + PS5 teased before full reveal. Notification bell CTA to build anticipation.",
      [{"pattern_slug":"sports_giveaway_teaser","confidence":"strong","notes":"King's Cup Final, Al Hilal vs Al Khulood"},
       {"pattern_slug":"high_value_prize","confidence":"strong","notes":"iPhone 17 + PS5 prize reveal teaser"}],
      "high"),

]  # end records


def main():
    written = 0
    for i, record in enumerate(records):
        uid  = record["observation_ulid"]
        path = OUT / f"{uid}.json"
        if path.exists():
            print(f"  skip (exists): {uid}")
            continue
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2))
        written += 1
    print(f"\n✅  Written {written} new obs for {ACCOUNT_NORM}")
    print(f"   Files in {OUT}")


if __name__ == "__main__":
    main()
