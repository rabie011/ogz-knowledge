#!/usr/bin/env python3
"""
humain_collector.py — Automated HUMAIN/ALLaM 34B gold output collector
Playwright opens chat.humain.ai, sends each brief, captures response.
Mohamed picks the best output interactively → saved to GOLD_OUTPUTS_HUMAIN.md

Usage:
  python3 scripts/humain_collector.py              # run all 18 briefs
  python3 scripts/humain_collector.py --from 5     # resume from brief #5
  python3 scripts/humain_collector.py --dry-run    # print prompts only, no browser
  python3 scripts/humain_collector.py --id 3       # run single brief by id
"""

import asyncio
import argparse
import sys
import re
import json
from datetime import datetime
from pathlib import Path

BASE      = Path(__file__).parent.parent
GOLD_FILE = BASE / "docs/consultations/GOLD_OUTPUTS_HUMAIN.md"
LOG_FILE  = BASE / "logs/humain_collector.log"
HUMAIN    = "https://chat.humain.ai"

# ── Sector display names ───────────────────────────────────────────────────────
SECTOR_AR = {
    "f_and_b":              "مطاعم وكافيهات",
    "fashion":              "أزياء وموضة",
    "real_estate":          "عقارات",
    "retail_lifestyle":     "تجزئة",
    "beauty_personal_care": "جمال وعناية",
    "healthcare_wellness":  "صحة ولياقة",
}

OCCASION_AR = {
    "national_day":   "اليوم الوطني",
    "ramadan":        "رمضان",
    "eid_al_fitr":    "عيد الفطر",
    "eid_al_adha":    "عيد الأضحى",
    "founding_day":   "يوم التأسيس",
    "riyadh_season":  "موسم الرياض",
    "white_friday":   "الجمعة البيضاء",
    "singles_day":    "يوم العزاب",
}

MAX_CHARS = {
    "f_and_b":              140,
    "fashion":              220,
    "real_estate":          200,
    "retail_lifestyle":     160,
    "beauty_personal_care": 150,
    "healthcare_wellness":  150,
}

# ── All 3 technique blocks (same for every brief — HUMAIN picks best) ─────────
TECHNIQUES_BLOCK = """أ. Paradox Hunter — قلب التوقع (استلهم الفكرة، لا تنسخ القالب)
← ناجح 1: "البروستد اللي ما ينتظره اليوم الوطني — اليوم الوطني ينتظره"
← ناجح 2 (مختلف تماماً): "التوفير اللي ما يحتاج تفكر مرتين"
← فاشل: "استمتع" / "لا تفوت" / "أجواء مميزة" / "عرض لفترة محدودة"
← ممنوع: نسخ أي مثال كما هو مع تغيير الكلمات فقط

ب. Heritage Decoder — جملة قصيرة تحمل كلمة بمعنيين في آنٍ واحد
← ناجح (مالية): الذكاء يستثمر فيك
← ناجح (أزياء): ترتدين المناسبة
← ناجح (غذاء): اللبن اللي يروبك
← فاشل وممنوع: اكتب الجملة فقط، بدون علامات اقتباس، بدون شرح للمعنى
← فاشل وممنوع: X معك في كل خطوة

ج. Firaasa — ملاحظة سلوكية محددة لهذا المنتج تحديداً
← ناجح: "الأم ما تدور على حليب — تدور على طمأنينة"
← فاشل وممنوع: "الناس ما تدور على X — تدور على Y"
← فاشل وممنوع: "في لحظة X، Y هو اللي..." أو "لحظة هدوء، تكتشف فيها..."
← الصحيح: لحظة حقيقية خاصة بهذا المنتج، مو جملة عامة لأي منتج"""

# ── Brief matrix — 18 briefs across 6 sectors ────────────────────────────────
BRIEFS = [
    # F&B (4) — Paradox Hunter wins here (+35% engagement)
    {"id": 1,  "sector": "f_and_b",             "brand": "AlBaik",           "product": "بروستد",            "occasion": "national_day",  "hashtags": "#انتم_والبيك_جيران #صنع_في_السعودية"},
    {"id": 2,  "sector": "f_and_b",             "brand": "Barns Coffee",      "product": "قهوة مثلجة",       "occasion": "ramadan",       "hashtags": "#بارنز #مننا_ويفهم_جونا"},
    {"id": 3,  "sector": "f_and_b",             "brand": "McDonald's KSA",    "product": "حفلة ماك",          "occasion": "eid_al_fitr",   "hashtags": "#ماكدونالدز #بحب_ماك"},
    {"id": 4,  "sector": "f_and_b",             "brand": "Al Romansiah",      "product": "مشاوي وكبسة",      "occasion": "founding_day",  "hashtags": "#الرومانسية"},
    # Fashion (3)
    {"id": 5,  "sector": "fashion",             "brand": "Max Fashion",       "product": "عباءة كلاسيكية",   "occasion": "eid_al_fitr",   "hashtags": "#إطلالاتmena"},
    {"id": 6,  "sector": "fashion",             "brand": "H&M KSA",           "product": "كوليكشن شتاء",     "occasion": "riyadh_season", "hashtags": "#hm"},
    {"id": 7,  "sector": "fashion",             "brand": "Level Shoes",       "product": "صبابيط عيد",        "occasion": "eid_al_adha",   "hashtags": "#level_shoes"},
    # Real Estate (3) — only ROSHN in our data
    {"id": 8,  "sector": "real_estate",         "brand": "ROSHN",             "product": "فيلا عائلية",      "occasion": "national_day",  "hashtags": "#روشن #رؤية_2030"},
    {"id": 9,  "sector": "real_estate",         "brand": "ROSHN",             "product": "شقق رؤية",         "occasion": "founding_day",  "hashtags": "#روشن #رؤية_2030"},
    {"id": 10, "sector": "real_estate",         "brand": "ROSHN",             "product": "موقع في قلب الرياض","occasion": "riyadh_season", "hashtags": "#روشن"},
    # Retail (3)
    {"id": 11, "sector": "retail_lifestyle",    "brand": "Panda",             "product": "عروض أسبوعية",     "occasion": "ramadan",       "hashtags": "#باندا #بياع_المسرة"},
    {"id": 12, "sector": "retail_lifestyle",    "brand": "Noon.com",          "product": "أجهزة إلكترونية",  "occasion": "white_friday",  "hashtags": "#نون"},
    {"id": 13, "sector": "retail_lifestyle",    "brand": "Tamimi Markets",    "product": "منتجات طازجة",     "occasion": "national_day",  "hashtags": "#تميمي"},
    # Beauty (3)
    {"id": 14, "sector": "beauty_personal_care","brand": "Mikyajy",           "product": "مجموعة عيد",       "occasion": "eid_al_fitr",   "hashtags": "#ميكياجي"},
    {"id": 15, "sector": "beauty_personal_care","brand": "Nice One",          "product": "عطور رمضانية",     "occasion": "ramadan",       "hashtags": "#نايس_ون"},
    {"id": 16, "sector": "beauty_personal_care","brand": "Gissah Perfumes",   "product": "عطر محلي فاخر",    "occasion": "national_day",  "hashtags": "#قصة_عطر"},
    # Healthcare (2)
    {"id": 17, "sector": "healthcare_wellness", "brand": "My Fitness",        "product": "اشتراك رمضان",     "occasion": "ramadan",       "hashtags": "#مايفتنس"},
    {"id": 18, "sector": "healthcare_wellness", "brand": "Fitness First",     "product": "برنامج لياقة",     "occasion": "national_day",  "hashtags": "#فتنس_فيرست"},
]


def build_prompt(brief: dict) -> str:
    max_chars  = MAX_CHARS.get(brief["sector"], 160)
    sector_ar  = SECTOR_AR.get(brief["sector"], brief["sector"])
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])
    return f"""<RED_LINES>
ممنوع: السرير، خلع الملابس أو الحجاب، استغلال ضعف الناس أو خوفهم.
دائماً: لهجة سعودية طبيعية. حد أقصى {max_chars} حرف. بدون إنجليزي.
</RED_LINES>

<TECHNIQUES>
{TECHNIQUES_BLOCK}
</TECHNIQUES>

<BRAND>
العلامة: {brief['brand']} | القطاع: {sector_ar} | المنتج: {brief['product']} | المناسبة: {occasion_ar}
الهاشتاقات: {brief['hashtags']}
</BRAND>

<TASK>
اكتب 3 كابشنات — كل واحد يطبّق تقنية مختلفة (أ، ب، ج).
كل كابشن: حد أقصى {max_chars} حرف. نص فقط — بدون علامات اقتباس، بدون شرح، بدون رقم التقنية.
ثم اختر الأقوى وضعه في السطر الأخير بعد كلمة: الأفضل:
</TASK>"""


def load_gold() -> list[dict]:
    """Parse existing gold entries from GOLD_OUTPUTS_HUMAIN.md."""
    if not GOLD_FILE.exists():
        return []
    text = GOLD_FILE.read_text()
    rows = []
    for line in text.splitlines():
        # table rows: | # | Brand | ...
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 7 and parts[1].isdigit():
            rows.append({
                "num": int(parts[1]),
                "brand": parts[2],
                "sector": parts[3],
                "occasion": parts[4],
                "technique": parts[5],
                "caption": parts[6],
            })
    return rows


def append_gold(num: int, brief: dict, caption: str, technique: str) -> None:
    """Append one approved output to GOLD_OUTPUTS_HUMAIN.md."""
    text = GOLD_FILE.read_text()
    # Update count
    count_match = re.search(r"## COUNT: (\d+) / 300", text)
    current = int(count_match.group(1)) if count_match else (num - 1)
    new_count = current + 1

    sector_ar  = SECTOR_AR.get(brief["sector"], brief["sector"])
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])

    # Replace placeholder row or append after last data row
    new_row = f"| {num} | {brief['brand']} | {sector_ar} | {occasion_ar} | {technique} | {caption} |"
    text = re.sub(r"\| — \| — \| — \| — \| — \| — \|", new_row, text, count=1)

    # If no placeholder was replaced, insert before COUNT line
    if new_row not in text:
        text = text.replace(
            f"| {num-1} |",
            f"| {num-1} |",  # no-op, find insertion point differently
        )
        # append before the COUNT line
        text = re.sub(
            r"(---\n\n## COUNT:)",
            f"{new_row}\n\n---\n\n## COUNT:",
            text
        )

    text = re.sub(r"## COUNT: \d+ / 300", f"## COUNT: {new_count} / 300", text)
    GOLD_FILE.write_text(text)
    print(f"\n  ✅ Saved #{num} to GOLD_OUTPUTS_HUMAIN.md (total: {new_count}/300)")


def log(msg: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")
    print(msg)


# ── Playwright automation ──────────────────────────────────────────────────────
CHAT_INPUT_SELECTORS = [
    "textarea",
    "[contenteditable='true']",
    "[role='textbox']",
    ".ProseMirror",
    "[data-placeholder*='message' i]",
    "[placeholder*='type' i]",
    "[placeholder*='اكتب' i]",
    "[placeholder*='أرسل' i]",
    "input[type='text']:not([type='email']):not([type='password'])",
    ".chat-input",
    "#chat-input",
    "div[data-testid='chat-input']",
]

SEND_BTN_SELECTORS = [
    "button[type='submit']",
    "button[aria-label*='send' i]",
    "button[aria-label*='إرسال']",
    "button[aria-label*='Submit' i]",
    "button svg[data-lucide='send']",
    ".send-button",
    "form button:last-child",
    "button:has(svg):last-of-type",
]

# Persistent session dir — so login is remembered between runs
SESSION_DIR = Path.home() / ".humain_playwright_session"


async def dismiss_modal(page) -> None:
    """Dismiss any onboarding/welcome modal that blocks the chat input."""
    modal_btns = [
        "button:has-text(\"Let's get started\")",
        "button:has-text('ابدأ')",
        "button:has-text('Continue')",
        "button:has-text('متابعة')",
        "button:has-text('Accept')",
        "button:has-text('موافق')",
        "[aria-label='Close']",
        "button.rounded-full svg[data-lucide='x']",
    ]
    for sel in modal_btns:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                await asyncio.sleep(1)
                return
        except Exception:
            pass


async def find_chat_input(page):
    await dismiss_modal(page)
    for sel in CHAT_INPUT_SELECTORS:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=1500):
                return el, sel
        except Exception:
            pass
    return None, None


async def wait_for_login(page) -> bool:
    """Poll until the login form disappears (user logged in). Returns True on success."""
    print("\n  🔐 HUMAIN requires login.")
    print("     → Log in via Google/Apple/Email in the browser window.")
    print("     → Script will continue automatically once you're in.\n")
    for _ in range(120):  # wait up to 4 minutes
        await asyncio.sleep(2)
        chat_input, _ = await find_chat_input(page)
        if chat_input:
            print("  ✅ Logged in — chat input detected.")
            return True
        # Also check if URL changed (away from login page)
        url = page.url
        if "chat.humain.ai" in url and "login" not in url and "auth" not in url:
            await asyncio.sleep(3)
            chat_input, _ = await find_chat_input(page)
            if chat_input:
                print("  ✅ Logged in (URL changed).")
                return True
    print("  ❌ Timed out waiting for login.")
    return False


async def wait_for_response(page, timeout_s: int = 180) -> str | None:
    """
    Wait for HUMAIN to finish generating a response.
    Strategy: count messages before send, wait for count+1, then wait for stable text.
    """
    # Step 1 — snapshot message count before waiting
    async def count_messages():
        for sel in ["[data-role='assistant']", ".assistant-message", "article", ".message"]:
            try:
                els = page.locator(sel)
                n = await els.count()
                if n > 0:
                    return n, sel
            except Exception:
                pass
        return 0, None

    before_count, msg_sel = await count_messages()
    deadline = asyncio.get_event_loop().time() + timeout_s

    # Step 2 — wait for a new message to appear
    if msg_sel:
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(2)
            after_count, _ = await count_messages()
            if after_count > before_count:
                break
        else:
            pass  # timed out — still try to read

    # Step 3 — wait for text to stabilise (model stops generating)
    prev_text = ""
    stable_rounds = 0
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(3)

        current = ""
        # Try structured assistant message selectors first
        for sel in [
            "[data-role='assistant']",
            "[data-message-author-role='assistant']",
            ".assistant-message",
            "article",
            ".message",
            "div.group",
        ]:
            try:
                els = page.locator(sel)
                n = await els.count()
                if n > 0:
                    last = els.nth(n - 1)
                    if await last.is_visible(timeout=1000):
                        t = (await last.inner_text()).strip()
                        # Skip if it looks like the user's own prompt
                        if t and "<RED_LINES>" not in t and "<TECHNIQUES>" not in t:
                            current = t
                            break
            except Exception:
                pass

        if not current:
            # Fallback: grab visible body text, skip lines that look like our prompt
            try:
                body = await page.inner_text("body")
                lines = [
                    l.strip() for l in body.splitlines()
                    if l.strip()
                    and "<RED_LINES>" not in l
                    and "<TECHNIQUES>" not in l
                    and "<BRAND>" not in l
                    and "<TASK>" not in l
                ]
                # Take last 30 lines (response area)
                current = "\n".join(lines[-30:]) if lines else ""
            except Exception:
                pass

        if current and current == prev_text:
            stable_rounds += 1
            if stable_rounds >= 2:
                return current
        else:
            stable_rounds = 0
            prev_text = current

    return prev_text or None


async def run_browser(briefs: list[dict]) -> None:
    from playwright.async_api import async_playwright

    gold_entries = load_gold()
    done_ids = set()
    next_num = len(gold_entries) + 1

    SESSION_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        # Persistent context — login saved between runs
        ctx = await pw.chromium.launch_persistent_context(
            str(SESSION_DIR),
            headless=False,
            slow_mo=80,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        log(f"\n{'='*60}")
        log(f"  HUMAIN Collector — {len(briefs)} briefs")
        log(f"  Gold so far: {len(gold_entries)}/300")
        log(f"{'='*60}\n")

        await page.goto(HUMAIN, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)

        # Check if login needed
        chat_input, sel = await find_chat_input(page)
        if chat_input is None:
            ok = await wait_for_login(page)
            if not ok:
                print("  Could not detect login. Press ENTER to retry once more, or Ctrl+C.")
                input()
                chat_input, sel = await find_chat_input(page)

        if chat_input is None:
            log("❌ Cannot find chat input after login. Exiting.")
            await ctx.close()
            return

        log(f"  Chat input found: {sel}\n")

        for brief in briefs:
            if brief["id"] in done_ids:
                continue

            prompt = build_prompt(brief)
            sector_ar   = SECTOR_AR.get(brief["sector"], brief["sector"])
            occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])

            print(f"\n{'─'*60}")
            print(f"  Brief #{brief['id']}/{len(BRIEFS)} — {brief['brand']} / {brief['product']} / {occasion_ar}")
            print(f"  Sector: {sector_ar}")
            print(f"{'─'*60}")

            # Re-find chat input (may shift after navigation)
            chat_input, sel = await find_chat_input(page)
            if chat_input is None:
                log("  ⚠️  Lost chat input — reloading page...")
                await page.goto(HUMAIN, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(3)
                chat_input, sel = await find_chat_input(page)
                if chat_input is None:
                    log("  ❌  Still no input. Skipping.")
                    continue

            # Set clipboard and paste (most reliable across editor types)
            await page.evaluate(f"navigator.clipboard.writeText({json.dumps(prompt)})")
            await chat_input.click()
            await page.keyboard.press("Meta+a")   # select all (Mac)
            await asyncio.sleep(0.2)
            await page.keyboard.press("Meta+v")   # paste
            await asyncio.sleep(1)

            # Send — button first, fallback Enter
            sent = False
            for btn_sel in SEND_BTN_SELECTORS:
                try:
                    btn = page.locator(btn_sel).last
                    if await btn.is_enabled(timeout=1200):
                        await btn.click()
                        sent = True
                        break
                except Exception:
                    pass
            if not sent:
                await page.keyboard.press("Enter")

            log(f"  Prompt sent. Waiting for ALLaM 34B response (up to 3 min)...")
            response = await wait_for_response(page, timeout_s=180)

            if not response:
                log("  ❌  No response captured.")
                print("  Press ENTER to skip to next brief, or Ctrl+C to quit.")
                input()
                continue

            # Print response for Mohamed
            print(f"\n  ── ALLaM Response {'─'*40}")
            print(response)
            print(f"  {'─'*57}")

            # Identify "الأفضل" line automatically
            best_line = ""
            for line in response.splitlines():
                if "الأفضل" in line:
                    best_line = re.sub(r"الأفضل\s*:\s*", "", line).strip()
                    break

            if best_line:
                print(f"\n  Auto-detected الأفضل: {best_line}")

            print(f"\n  [1] Save الأفضل line above   [2] Enter custom caption   [s] Skip   [q] Quit")
            pick = input("  → ").strip().lower()

            if pick == "q":
                log("  Quit requested. Progress saved.")
                break
            if pick == "s":
                log(f"  Brief #{brief['id']} skipped.")
                done_ids.add(brief["id"])
                continue

            if pick == "1" and best_line:
                chosen = best_line
                technique = input("  Technique (أ/ب/ج — which won?): ").strip() or "الأفضل"
            else:
                chosen = input("  Paste the winning caption: ").strip()
                technique = input("  Technique (أ/ب/ج): ").strip() or "؟"

            if chosen:
                append_gold(next_num, brief, chosen, technique)
                next_num += 1
                done_ids.add(brief["id"])

            # Start new chat to avoid context contamination between briefs
            try:
                new_btn = page.locator(
                    "button[aria-label*='new chat' i], "
                    "button[title*='new' i], "
                    "a[href='/']:not([aria-label]), "
                    "button:has-text('New chat'), "
                    "button:has-text('محادثة جديدة')"
                ).first
                if await new_btn.is_visible(timeout=2000):
                    await new_btn.click()
                    await asyncio.sleep(2)
                else:
                    raise Exception("no new-chat button")
            except Exception:
                await page.goto(HUMAIN, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)

        await ctx.close()
        total = len(load_gold())
        log(f"\n{'='*60}")
        log(f"  Session complete. Total gold: {total}/300")
        log(f"  Run again to continue from where you left off.")
        log(f"{'='*60}\n")


def dry_run(briefs: list[dict]) -> None:
    """Print all prompts without opening browser — for review."""
    for brief in briefs:
        sector_ar   = SECTOR_AR.get(brief["sector"], brief["sector"])
        occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])
        prompt = build_prompt(brief)
        print(f"\n{'='*70}")
        print(f"BRIEF #{brief['id']} — {brief['brand']} / {occasion_ar} / {sector_ar}")
        print(f"{'='*70}")
        print(prompt)
    print(f"\n\nTotal: {len(briefs)} briefs")


def main():
    parser = argparse.ArgumentParser(description="HUMAIN gold output collector")
    parser.add_argument("--from",    dest="from_id", type=int, default=1, help="Resume from brief id")
    parser.add_argument("--id",      type=int, default=None, help="Run single brief id")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts only")
    args = parser.parse_args()

    if args.id:
        briefs = [b for b in BRIEFS if b["id"] == args.id]
    else:
        briefs = [b for b in BRIEFS if b["id"] >= args.from_id]

    if not briefs:
        print(f"No briefs found for given arguments.")
        sys.exit(1)

    if args.dry_run:
        dry_run(briefs)
        return

    asyncio.run(run_browser(briefs))


if __name__ == "__main__":
    main()
