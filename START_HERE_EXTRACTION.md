# START_HERE_EXTRACTION.md
# The exact steps to begin building the corpus.
# Mohamed reads this. Claude Code reads this.

---

## The State of the Repo

ogz-knowledge v1.0.0 is complete:
- 88 chains across 23 families
- 5 sector defaults
- 5 Saudi occasion files
- 5 CD brain files
- 5 strategy framework files (new in v1.1)
- All schemas locked in 12_data_shapes/
- All scripts ready in scripts/
- CLAUDE.md at repo root

**What is empty:** `11_who_to_learn_from/`

This is where the corpus lives. It is empty because nothing has been extracted yet. Building it is the next job.

---

## The Two Jobs — Mohamed's Job and Claude Code's Job

**Mohamed's job:** Decide which accounts are worth learning from.
He is the cultural filter. Nothing enters the corpus that he has not seen and approved.

**Claude Code's job:** Extract structured records from the content Mohamed curates.
Mechanical observation, schema conformance, compliance checking.

These two jobs never mix. Mohamed does not extract. Claude Code does not curate.

---

## Mohamed's Job — Step by Step

### Step 1: Create your first picks file

Go to: `11_who_to_learn_from/source_library/my_picks/`
Copy `MY_PICKS_TEMPLATE.yaml` and rename it: `f_and_b.yaml`

Fill in the accounts you know personally for F&B. Start with 5-10 accounts. Do not try to cover everything in the first session.

For each account write:
- The handle (exact, as it appears on the platform)
- The platform (instagram / tiktok / snapchat)
- The tier (1 = gold standard you trust completely, 2 = good coverage, 4 = bad example)
- Why you picked it — in your own words, Arabic or English
- What Claude Code should pay attention to
- Any red flags you noticed

The most important entry in every picks file is **at least one Tier 4 account** — an account that gets Saudi culture wrong. Claude Code must learn what failure looks like, not just what success looks like.

### Step 2: Download the content you want extracted

For each account in your picks file:
- Go to the account
- Download or screenshot the posts you want Claude Code to analyse
- For Tier 1 accounts: download their 10 best posts + all Ramadan/Eid/National Day posts
- For Tier 4 accounts: download the posts with the specific violations you want documented

Put the files here:
```
11_who_to_learn_from/_inbox/@account_handle/
```

Use the exact handle as the folder name (with the @ symbol).

### Step 3: The calibration set (do this before anything else)

Before Claude Code extracts a single real corpus record, you must test that it extracts correctly.

Go to: `11_who_to_learn_from/_calibration_set/`

Pick 10 pieces of content you know perfectly:
- item_01: A post with correct qahwa service (everything right)
- item_02: **A post with a LEFT-HAND SERVING violation** — this is the critical test
- item_03: A video with clear pacing you can describe
- item_04-10: A mix of your choice (see CALIBRATION_SETUP_GUIDE.md)

Save these to: `_calibration_set/content/item_01.jpg` etc.

Open `GROUND_TRUTH.yaml` and fill in the correct answers for each item. Be honest — if you are not sure about a field, leave it null.

**Do not show GROUND_TRUTH.yaml to Claude Code before it extracts.**

### Step 4: Run Claude Code on the calibration set

In Claude Code:
```
Read CLAUDE.md completely.
Then: run the calibration test on the 10 items in _calibration_set/content/
Save extractions to _calibration_set/claude_extractions/
Do not look at GROUND_TRUTH.yaml until extraction is complete.
```

### Step 5: Check the results

```bash
python3 scripts/test_extraction_accuracy.py
```

**If item_02 (the left-hand violation) is NOT detected: STOP.**
Do not run the extraction on any real corpus content.
Fix the extraction prompt and re-run the calibration until item_02 is caught.

**If all three levels pass:** proceed to Step 6.

### Step 6: Run the full extraction

```bash
python3 scripts/extract_from_picks.py --sector f_and_b --queue-only
```

Review the queue. When ready:

In Claude Code:
```
Read CLAUDE.md completely.
Read EXTRACTION_PROMPT_FOR_CLAUDE_CODE.md.
Process the extraction queue at 11_who_to_learn_from/_extraction_queue.json.
For each item: analyse with vision, fill extraction record, validate, save.
Report when complete.
```

---

## Claude Code's Job — What to Do When Running Extraction

Read CLAUDE.md before starting. It contains everything.

**The short version:**

1. Read all picks files in `my_picks/`
2. For each account: create account record → save to `source_library/accounts/`
3. For each content item in `_inbox/`: observe → extract → validate → save to `observations/`
4. Extract patterns per account → save to `patterns/`
5. Update indexes
6. Run `python3 scripts/validate_all.py` — must exit 0
7. Print the extraction report

**The most important rule:**

Item_02 in any calibration set must show a compliance violation. If you extract from item_02 and do not trigger `hard_blocks_triggered`, stop immediately. Tell Mohamed. Do not continue to corpus extraction.

---

## What the First Extraction Session Should Produce

Target for the first session (F&B sector, 5-10 accounts):

| Output | Target |
|---|---|
| Account records | 5-10 |
| Extraction records (observations) | 50-100 |
| Pattern records | 5-15 |
| Hard blocks found | At least 1 (from Tier 4 accounts) |
| Validation | All pass |

After the first session, Mohamed reviews 5 random extraction records and asks:
"Does this match what I see when I look at the same content?"

If yes → corpus extraction is working. Continue with next sector.
If no → identify which fields are consistently wrong → fix extraction prompt → re-run calibration.

---

## The Build Order for the Corpus

Run sectors in this order. Do not move to the next until the current one passes calibration and Mohamed has reviewed sample records.

```
Phase 1 (build these first):
  1. F&B Najdi      — Mohamed knows this best, best calibration
  2. F&B Hejazi     — Different enough to test regional extraction
  3. Retail Najdi   — Second sector

Phase 2 (after Phase 1 is solid):
  4. Beauty
  5. Real Estate

Phase 3 (later):
  6. Healthcare
  7. Any new sector needed for specific client
```

Within each sector, always have:
- Minimum 3 Tier 1 (exemplar) accounts
- Minimum 3 Tier 2 (coverage) accounts
- Minimum 1 Tier 4 (anti-pattern) account

The Tier 4 account is not optional. You cannot build a forbidden pattern library without negative examples.

---

## The Files That Go Into the Repo After Each Session

After Claude Code finishes an extraction session and validation passes:

```bash
cd ~/Desktop/ogz-knowledge
git add 11_who_to_learn_from/
git status  # Review what changed
git commit -m "extraction: [sector] - [number] records from [number] accounts"
git push origin main
```

Tag when a sector reaches 50+ confirmed records:
```bash
git tag v1.1.0-f-and-b-50-records
git push origin --tags
```

---

## What Matters Most

The corpus is not the files. The corpus is the cultural intelligence those files represent.

A file that passes schema validation but contains wrong cultural observations is worse than no file at all — it teaches the system incorrect things about Saudi content.

Mohamed's eyes on the right accounts and Claude Code's honest extraction of what is actually observable are the only two things that build a corpus worth trusting.

Everything else is infrastructure. The intelligence comes from these two jobs done carefully.
