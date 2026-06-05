# 📅 OCCASIONS TREE
# 8 Saudi occasions, timing, required words, coverage
# ← Back to [SYSTEM_MAP](../SYSTEM_MAP.md)

---

```
🌳 OCCASIONS
│
├── 🕌 RELIGIOUS OCCASIONS (4)
│   │
│   ├── ramadan
│   │   ├── Type: religious
│   │   ├── Duration: 29-30 days
│   │   ├── Month: varies (Islamic calendar)
│   │   ├── Content: spiritual, community, family, suhoor/iftar
│   │   ├── Required Arabic: [رمضان, إفطار, سحور]
│   │   ├── Colors: gold, cream, crescent motifs
│   │   ├── FORBIDDEN: eating daylight shots, alcohol, commercial prayer
│   │   ├── Best formats: carousel (iftar spread), video (suhoor vibe)
│   │   └── Our data: 468 obs tagged ramadan (12% of total)
│   │       F&B gold: 12 | silver: 27 | bronze: 25
│   │
│   ├── eid_al_fitr
│   │   ├── Type: religious
│   │   ├── Duration: 3 days
│   │   ├── Content: joy, celebration, gifts, sweets, family gatherings
│   │   ├── Required Arabic: [عيد, الفطر, عيدكم]
│   │   ├── Retail is strong (gifting season)
│   │   └── Our data: 82 obs
│   │       Retail gold: 1 | Fashion gold: 3
│   │
│   ├── eid_al_adha
│   │   ├── Type: religious
│   │   ├── Duration: 4 days
│   │   ├── Content: sacrifice, generosity, family, travel
│   │   ├── Required Arabic: [عيد, الأضحى]
│   │   ├── Retail is STRONGEST (eid gifting + meat season)
│   │   └── Our data: 58 obs
│   │       Retail gold: 7 | F&B gold: 4 ← retail wins this occasion
│   │
│   └── hajj_season
│       ├── Type: religious
│       ├── Duration: ~10 days
│       ├── Required Arabic: [حج, الحرم]
│       ├── ⚠️ RULE: Minimal promotion. Warm, subtle content only.
│       ├── Pull back all commercial messages
│       └── Our data: 57 obs
│           F&B gold: 1 ← almost nothing
│
├── 🇸🇦 NATIONAL OCCASIONS (2)
│   │
│   ├── national_day
│   │   ├── Type: national
│   │   ├── Date: September 23 (fixed)
│   │   ├── Content: green theme, Saudi pride, heritage + modern fusion
│   │   ├── Required Arabic: [اليوم الوطني, الوطن]
│   │   ├── Colors: green, white, gold
│   │   ├── Hashtags: #اليوم_الوطني_السعودي, #همة_حتى_القمة
│   │   └── Our data: 46 obs
│   │       F&B gold: 3 | silver: 7 ← weak coverage
│   │
│   └── founding_day
│       ├── Type: national
│       ├── Date: February 22 (fixed)
│       ├── Content: deep heritage, roots, historical pride (not modern)
│       ├── Required Arabic: [تأسيس, يوم التأسيس]
│       ├── Colors: dark green, heritage tones
│       └── Our data: 26 obs
│           F&B gold: 1 | silver: 3 ← very weak coverage
│
├── 🎉 ENTERTAINMENT OCCASIONS (2)
│   │
│   ├── riyadh_season
│   │   ├── Type: entertainment
│   │   ├── Months: October → March (6 months)
│   │   ├── Content: energy, events, nightlife, entertainment
│   │   ├── Key: this is when KSA is most active socially
│   │   └── Our data: 681 obs (18% of total) ← BIG opportunity
│   │       F&B gold: 21 | silver: 39 ← strong
│   │
│   └── jeddah_season
│       ├── Type: entertainment
│       ├── Months: June-July (summer)
│       ├── Content: coastal, relaxed, summer vibes
│       └── Our data: 95 obs
│           F&B gold: 14 | silver: 16 ← surprisingly strong
│
├── 📆 MONTH → OCCASION MAP (for calendar generation)
│   ├── January:   evergreen
│   ├── February:  founding_day (Feb 22) + evergreen
│   ├── March-Apr: ramadan (varies by year)
│   ├── May:       eid_al_fitr
│   ├── June:      jeddah_season + eid_al_adha (varies)
│   ├── July:      jeddah_season
│   ├── August:    evergreen
│   ├── September: national_day (Sep 23)
│   ├── October:   riyadh_season begins
│   ├── November:  riyadh_season
│   └── December:  riyadh_season + jeddah_season (varies)
│
├── ✅ COVERAGE STRENGTH BY SECTOR × OCCASION
│   │
│   │  ✅ = 3+ gold captions | ⚡ = 1-2 gold | ❌ = 0 gold
│   │
│   │                 F&B   Fashion  Retail  Beauty  RE  HC
│   │  evergreen:     ✅     ✅       ⚡      ⚡     ❌  ❌
│   │  riyadh_season: ✅     ❌       ❌      ❌     ❌  ❌
│   │  ramadan:       ✅     ❌       ❌      ❌     ❌  ❌
│   │  jeddah_season: ✅     ❌       ❌      ❌     ❌  ❌
│   │  eid_al_adha:   ⚡     ❌       ✅      ❌     ❌  ❌
│   │  eid_al_fitr:   ⚡     ⚡       ⚡      ❌     ❌  ❌
│   │  national_day:  ⚡     ❌       ❌      ❌     ❌  ❌
│   │  founding_day:  ⚡     ❌       ❌      ❌     ❌  ❌
│   │  hajj_season:   ⚡     ⚡       ❌      ❌     ❌  ❌
│
└── 🔑 OCCASION REQUIRED WORDS (enforced in quality gate)
    ├── founding_day:  [تأسيس, يوم التأسيس]
    ├── national_day:  [اليوم الوطني, الوطن]
    ├── ramadan:       [رمضان, إفطار, سحور]
    ├── eid_al_fitr:   [عيد, الفطر, عيدكم]
    ├── eid_al_adha:   [عيد, الأضحى]
    └── hajj_season:   [حج, الحرم]
```

---
*See [07_TEMPLATES](07_TEMPLATES.md) for coverage matrix and gaps.*
*See [09_QUALITY](09_QUALITY.md) for how required words are enforced.*
