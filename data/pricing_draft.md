# FLANK-03 — PRICING PACK (DRAFT)
*Prepared 2026-06-12 for approval card A-12. EVERY NUMBER IN THIS FILE IS **PROPOSED** — nothing is law until Mohamed pins it. Sources: market fact sheet (Saudi/MENA 2025–26, SAR @ 3.75/USD) + THE_CLIENT_PYRAMID.md (states §3, trust ladder §229, unit-economics ledger §250).*

---

## 1. THE THREE TIERS

### TIER 1 — STARTER (self-serve, Pipeline A)
**PROPOSED: SAR 500–900/mo** *(pin one number)*

| What's included | PROPOSED spec |
|---|---|
| Posts | 3/week (≈12/mo), caption + visual card |
| Picks | Client picks winner from 3-candidate pick-sets (self-serve UI) |
| Voice | Voice BIRTH ritual (3 personas, client picks) or extraction |
| Human gates | Cultural gate + red-lines armor automatic; client is the approver (trust ladder L0 — every piece clicked before posting) |
| Reporting | Monthly receipt (counts, not vanity) |
| NOT included | Year map, majors/occasion arcs, OGZ human review, posting on their behalf |

**Fits:** NEWBORN state (posts < 30 — jurisha profile: birth + launch arc).
**Market anchor:** sits ABOVE DIY AI tools (Predis/Araby/Katteb ≈ SAR 75–375/mo, generic Arabic, zero Saudi-dialect QA) and INSIDE the freelancer-gamble band (Arabic-market basic management $150–400/mo = SAR ~560–1,500) while undercutting the KSA "Basic" agency package (SAR 1,500–2,500/mo, static-only). This is the whitespace the fact sheet names: SAR ~500–2,500 has no productized competitor.

### TIER 2 — GROWTH (managed, Pipeline B — the pyramid)
**PROPOSED: SAR 1,800–3,500/mo** *(pin one number)*

| What's included | PROPOSED spec |
|---|---|
| Posts | 4–5/week (≈18/mo) |
| Picks | Year map + MAJORS occasion picks staged for the client; pick-sets curated, not raw |
| Voice | Full profile→year-map→post-cards pyramid; state-routed plays (birth / extraction / revival) |
| Human gates | OGZ human gate (Mohamed/Mira taste pass) BEFORE client sees anything; trust ladder L0→L1 (batch consent after 10 unchanged approvals) |
| Reporting | Monthly receipt + churn-risk/outcome events |
| Extras | One revival or launch arc per year included |

**Fits:** ACTIVE (messy or strong — albaik-like: year map + majors picks) AND DORMANT (myfitness: revival arc is the entry play).
**Market anchor:** sits just UNDER the credible-Saudi-agency floor (KSA Medium package SAR 3,000–5,000/mo; agency retainer floor SAR 3k–6k) and ABOVE the professional-freelancer band ($400–1,200/mo = SAR 1,500–4,500) — agency-grade consistency at near-freelancer price, with human gates the freelancers don't have.

### TIER 3 — ENTERPRISE (managed+, Pipeline B)
**PROPOSED: SAR 6,000–12,000/mo** *(pin one number)*

| What's included | PROPOSED spec |
|---|---|
| Posts | 5–7/week, multi-account / multi-brand allowed |
| Picks | Full year map + all 16 occasion arcs + campaign arcs; dedicated quarterly strategy pass |
| Human gates | Named OGZ account owner (card A-16) + SLA on verdict latency (card A-15 numbers); trust ladder through L2 (offers join batch approval, 24h preview) |
| Reporting | Monthly receipts + quarterly business review |
| Extras | Brand-isolation guarantees in writing (RLS), priority rendering |

**Fits:** ACTIVE-STRONG at scale, multi-brand owners, the ROSHN/NHC-shaped logos later.
**Market anchor:** bottom of the KSA "Advanced" agency band (SAR 6,000–15,000/mo) and the SME retainer band (SAR 6k–25k one-off pack equivalent) — we enter the agency comparison set at its floor, with AI margins underneath.

---

## 2. REVENUE PROJECTION (mid-range, PROPOSED)

Mid-range price points used: Starter **SAR 700**, Growth **SAR 2,650**, Enterprise **SAR 9,000**.
PROPOSED mix assumption: 50% Starter / 40% Growth / 10% Enterprise.

| Clients | Starter (50%) | Growth (40%) | Enterprise (10%) | **MRR (SAR)** | **ARR (SAR)** |
|---|---|---|---|---|---|
| 10 | 5 × 700 = 3,500 | 4 × 2,650 = 10,600 | 1 × 9,000 = 9,000 | **23,100** | ~277k |
| 50 | 25 × 700 = 17,500 | 20 × 2,650 = 53,000 | 5 × 9,000 = 45,000 | **115,500** | ~1.39M |
| 200 | 100 × 700 = 70,000 | 80 × 2,650 = 212,000 | 20 × 9,000 = 180,000 | **462,000** | ~5.54M |

### Cost basis — stated honestly (all ESTIMATES, not measured)
- **Per rendered card:** ~5 LLM calls (brief→candidates→armor→cultural gate→assembly). At Sonnet-class pricing (~$3/M in, $15/M out), ~3k in + ~800 out tokens per call ≈ **$0.10/card ≈ SAR 0.38/card**.
- **Per PUBLISHED post:** pick-sets render 3 candidates + regen buffer ×2 ≈ 6 cards ≈ SAR 2.3 caption-side; + fal.ai visual $0.05–0.15 ≈ SAR 0.2–0.6; call it **SAR 2–4 all-in per published post (PROPOSED estimate)**.
- **Per client per month (API only):** Starter ~SAR 50 · Growth ~SAR 100 · Enterprise ~SAR 300.
- **At 200 clients:** API COGS ≈ SAR 20–25k/mo against 462k MRR ≈ **~5% — gross margin >90% on compute.**
- **The REAL cost is human minutes** (Mohamed/Mira gate time + Apify scrape credits) — already instrumented in `logs/unit_economics/{month}.jsonl` (pyramid §250: cost-per-YES, human minutes, days-to-first-YES). Trust-ladder L1 batch consent is the margin lever: gate minutes per client must FALL as approvals compound, or Growth tier doesn't scale past ~30 clients per human gate-keeper.
- **NOT measured yet:** actual token counts per card. Pre-build Q5 applies — measure on the 3 pilots in month 1 and replace these estimates.

---

## 3. SEGMENTATION — the 3 states → tier map

| State (state.json, §3 thresholds) | Pilot example | Entry play | Natural tier |
|---|---|---|---|
| **NEWBORN** (posts < 30, countable) | jurisha (8 posts, 28 followers; also dormant since Apr 20 → newborn-dormant) | Voice BIRTH (3 personas, client picks) + launch/return arc | **STARTER** (upgrade path: launch succeeds → Growth) |
| **ACTIVE** (strong or messy; messy/strong split human-confirmed) | albaik-like (164 obs, ACTIVE-STRONG pending checkpoint A-28) | Year map + MAJORS occasion picks; voice extracted from their real captions | **GROWTH** (multi-brand/scale → Enterprise) |
| **DORMANT** (last post > 90d, countable) | myfitness.sa (4.7y dormant) | Revival arc, NOT continuation; facts demoted to "still true?"; «وش تغير من يوم وقفتو؟» first | **GROWTH** (revival is managed work — self-serve can't carry a revival; PROPOSED: revival arc priced inside Growth, no separate SKU) |

State transitions are appended events — dormant→active on our watch is the receipt that justifies the Growth price.

---

## 4. COMPLIANCE / CONTRACT CHECKLIST (line items — each needs a yes before first paid invoice)

- [ ] **VAT 15%:** registration mandatory once taxable revenue > SAR 375,000/12mo (we cross this between the 10- and 50-client rows). Decide now: prices quoted **exclusive of VAT** (PROPOSED) — state it on every quote.
- [ ] **ZATCA e-invoicing (FATOORA):** compliant invoice format from invoice #1; Phase-2 integration when revenue thresholds hit.
- [ ] **Contract term:** PROPOSED monthly rolling with 3-month minimum on Growth/Enterprise (year map is a 12-month artifact; 3-mo floor protects the setup cost). Starter: pure monthly.
- [ ] **Consent clauses must mirror the trust ladder:** L1 batch-consent wording in the contract = the L1 paragraph in THE_CLIENT_PYRAMID.md (card A-19); no standing "auto" grant exists at any level — contract may not promise one.
- [ ] **Posting access + credentials policy:** contract clause = whatever A-18 rules (access model + revocation spec).
- [ ] **Scraping/processing consent (PDPL):** explicit consent to scrape and process their account data + review-monitoring consent (A-17 template).
- [ ] **Refund/offboarding — PDPL tie-in:** offboarding = data export + 90-day quarantine (quarantine-never-delete rule), EXCEPT where PDPL erasure right overrides — precedence is exactly card **A-14** and must be ruled BEFORE the first paid contract is signed. Refund: PROPOSED pro-rata on unposted batches, no refund on posted/approved batches (their click = acceptance).
- [ ] **Commercial event types in the ledger:** the pyramid names this hole (no commercial events yet — FLANK-03). `commercial_terms.json` + invoice/payment events must land in the ledger schema before invoice #1.
- [ ] **Payment rails:** SAR invoicing, bank transfer + Mada; PROPOSED net-15.

---

## 5. ROLLOUT — pilots first, list price later

**Phase 0 (now):** Mohamed pins the 3 numbers (card A-12) → fill `commercial_terms.json` stubs.

**Phase 1 — pilot pricing (3 clients, 3 months, PROPOSED):**
- Founding-pilot rate = **50% of pinned tier price**, locked for 6 months. NOT free — they must pay something or their verdicts are decoration (the eye test needs skin in the game).
- jurisha → STARTER pilot (PROPOSED ~SAR 350/mo at 50%): voice birth + launch/return arc.
- albaik-like → GROWTH pilot (PROPOSED ~SAR 1,325/mo): year map + majors picks. (Contingent on A-27 outreach ruling + A-28 state checkpoint.)
- myfitness → GROWTH pilot (PROPOSED ~SAR 1,325/mo): revival arc entry. (Contingent on A-26 contact-path ruling.)
- Pilot contract: month-to-month, both sides can exit, all compliance line items above already in force.

**Phase 2 (after 3 paid months):** replace estimated COGS with measured unit-economics numbers; confirm gate-minutes-per-client trend; THEN publish list prices and open Pipeline A self-serve.

**Phase 3:** referral engine (A-13) fires only after 2 of 3 pilots renew at full rate.

---
*Every number above is PROPOSED. The tap that makes them real is card A-12.*
