# PRE-FLIGHT REPORT — KHWILA_PRESENTATION.md (B188)

Verified: 2026-06-12 · Verifier: Claude (RABIE-directed, PROVISIONAL — pending Mohamed)
Target: `clients/eatjurisha/KHWILA_PRESENTATION.md`
Raw intake: `clients/eatjurisha/raw/instagram/2026-06-11/` (profile.json · posts.jsonl · comments.jsonl · website.html) — extracted 2026-06-11, **1 day old at verification** ✅ fresh.

---

## 1. Fact-by-fact verification

| # | Claim in presentation | Verdict | Evidence |
|---|---|---|---|
| F1 | المنتجات: جريشة + رز كابلي | ✅ | profile.json `biography` line 1: «جريش • رز كابلي»; posts DXFEJbnjCms («الرز الكابلي وصل») + DXW5KvBDFpe |
| F2 | إضافة دجاج | ✅ | post DV63TOKDCmy: «وإذا تحبونها أغنى، تقدرون تضيفون الدجاج عليها 🤍» |
| F3 | جريشة بالحجم **العائلي** | ✅ | post DWFL8-wjPCJ: «جريشة بالحجم العائلي تكفي الكل» |
| F4 | جريشة **فردي** | ⚠️ | **No raw evidence anywhere** (not in bio, posts, comments, linktree). Inference from "family size exists". Covered by the B186 truth-confirm card — see FIX-3 |
| F5 | القنوات: جاهز وهنقرستيشن من البيو | ✅ | profile.json `biography` line 2: «تلقونا الآن على تطبيق جاهز وهنقرستيشن»; linktree (website.html) carries live `jahez.link/gibHIjukr2b` + `hungerstation.go.link` links; truth_pack.json channels = confirmed |
| F6 | مطبخ سحابي — توصيل فقط، الرياض | ✅ (inference, strong) | bio «📍الرياض»; delivery apps are the ONLY order paths in bio+linktree; zero dine-in signal in all 8 posts. Same reading RABIE used to kill the «زورونا» truth error (ledger 2026-06-11) |
| F7 | أقوى منشور: جريشة العيد العائلية — **31 إعجاب من 28 متابع** | ✅ | post DWFL8-wjPCJ («جمعة العيد ما تكمل بدونها 🤍 جريشة بالحجم العائلي…») `likesCount: 31` — max across all 8 posts (next best 25); profile.json `followersCount: 28`. Mirrored in profile/moments_bank.json (engagement 31, confidence confirmed) |
| F8 | الحساب صامت من **20 أبريل** | ✅ | latest timestamp across posts.jsonl = 2026-04-20T15:06:48Z (post DXW5KvBDFpe); matches profile/state.json (`last_post: 2026-04-20`, `silent_days: 52` at intake) |
| F9 | شكوى توصيل في التعليقات (تأخر مندوب) | ✅ | comments.jsonl, user rm.00p on post DWFL8-wjPCJ (2026-03-19): «لي ساعه طالبه والى الان ما تم تعيين مندوب !!! ومحد يرد علي» + the brand's own apology reply confirms it was real |
| F10 | مشروع أم وبنتها / نكهة نجدية بيتية | ⚠️ ✅ | «نجدية» evidenced (captions «النكهة النجدية», hashtags اكل_نجدي). «أم وبنتها» is **NOT in the intake** — it traces to Mohamed's founder brief (`~/agents/rabie/sessions/2026-06-11.jsonl` 20:20:13: "Khwila — Alhareth's sister … mother+daughter heritage food business"). Traceable, but provenance = founder brief, not scrape. The «صحّحينا لو غلطنا» framing already invites her correction. Non-blocking |

**Homework law:** ≥5 facts each traceable — **7 fully traceable** (F1, F2, F3, F5, F7, F8, F9) ✅ PASS.

## 2. Voice check vs `voice_birth_week.json` (current state)

Voice C was regenerated 2026-06-11 after RABIE rated the original 2/5 («زورونا» truth error — delivery-only brand).

- **Voice A (بنت نجد الدافئة):** ✅ posts 1–2 byte-identical; post 3 identical except presentation drops «#جريشة #نجدي».
- **Voice B (الحرفية الأنيقة):** ✅ wording identical; presentation drops hashtags on all 3 posts.
- **Voice C (خفيفة الدم):** ❌ **DRIFT.** The presentation DOES hold the FIXED version (no «زورونا»; regenerated opener «رجعنا بقوة» present) — the truth error is gone. But all 3 lines differ in wording from the organ's current text:

| Post | voice_birth_week.json (organ) | KHWILA_PRESENTATION.md |
|---|---|---|
| C1 | …اشتقتوا لها. **اشتقتوا للأكل اللي يحسسك إنك في حضن الرياض؟** خلو الجريشة تطرق الباب! #الجريشة #جاهز | …اشتقتوا لها. خلو الجريشة تطرق الباب! |
| C2 | الجريشة، كل ملعقة **تأخذك في رحلة إلى** سوق التوابل… **هل أنت جاهز للتذوق؟ #رز_كابلي** | الجريشة — كل ملعقة رحلة لسوق التوابل… |
| C3 | …ولا تنتظروا **سوى** صوت الجرس. الجريشة **ستحضر البهجة وتملأ السفرة بالحب والنكهات.** #الجمعة | …ولا تنتظروا إلا صوت الجرس. الجريشة **تعبّي السفرة حب ونكهة.** |

Why it matters: her pick becomes seed DNA (fingerprint l2 love_lines + gold, verbatim). If she picks C off the presentation while the organ holds different words, the promoted lines are words she never saw. One source of truth must hold the exact lines before send.

Side note: the organ's C2 tags **#رز_كابلي on a جريشة caption** — a `hallucinated_product_tags` kill (taste.json); the presentation's C-lines are also more dialect-true (organ's «ستحضر البهجة وتملأ» is MSA drift). The presentation's lines are the better text.

## 3. Minor flags (non-blocking, for Mohamed's eye)

1. **«ريحة الهيل»** (voice A2): cardamom never appears in any real caption — an unverified sensory detail in a voice sample. Same class the truth-gate crystallize card (A-09 #2) targets. Low risk; flag only.
2. **Hashtag policy inconsistent:** presentation strips hashtags from A3/B1/B2/B3 but the organ keeps them. Decide once: presentation shows clean lines + hashtags are render-time (recommended), and note it.
3. comments.jsonl shows 5 «HTTP 404 / no_items» rows — these are the 5 posts with `commentsCount: 0`; expected scraper behavior, coverage is real (manifest: 100%).

## 4. Staleness clock (homework law)

- Intake 2026-06-11 → fresh now. **If send slips past 2026-07-11 (30d), all facts must be re-verified first** (products TTL 30d per the TTL registry; prices 7d — none cited ✅).
- **Send-morning re-check regardless of date** (live numbers can break the text): followers (28), best-post likes (31), bio/channels unchanged, and **whether she has posted** — one new post breaks «صامت من 20 أبريل».

## 5. VERDICT: **FIX-FIRST** (1 blocking fix)

- **FIX-1 (BLOCKING):** Sync voice C between `voice_birth_week.json` and the presentation — byte-identical before send. **Recommended direction: update `voice_birth_week.json` C-posts to the presentation's exact lines** (kills the #رز_كابلي mis-tag and the MSA drift in the same stroke); log a `version_verdict` ledger event for the sync.
- **FIX-2 (should-fix):** «فردي» (F4) — add «؟» or fold into the truth-confirm question (B186 card covers it); don't state unevidenced size as understood fact.
- **FIX-3 (should-fix):** Pin the hashtag policy (minor flag 2) so A3/B/C presentation-vs-organ diffs are zero or documented.

After FIX-1 lands (+ Mohamed's A-22 yes), this pack is SEND-READY within the staleness clock above.
