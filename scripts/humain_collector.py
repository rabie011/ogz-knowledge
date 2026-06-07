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

BASE       = Path(__file__).parent.parent
GOLD_FILE  = BASE / "docs/consultations/GOLD_OUTPUTS_HUMAIN.md"
QUEUE_FILE = BASE / "logs/humain_queue.json"
LOG_FILE      = BASE / "logs/humain_collector.log"
LEARNING_FILE = BASE / "logs/prompt_learning.json"
HUMAIN        = "https://chat.humain.ai"
REVIEW_URL = "http://localhost:4100/humain-review"

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
← ناجح: "التوفير اللي ما يحتاج تفكر مرتين"
← ناجح (مختلف): "قهوة تصحيك — حتى قبل ما تشربها"
← فاشل: "استمتع" / "لا تفوت" / "أجواء مميزة" / "عرض لفترة محدودة"
← ممنوع: نسخ أي مثال كما هو مع تغيير الكلمات فقط
← ممنوع تماماً: قالب "[المنتج] اللي ما ينتظر [المناسبة] — [المناسبة] ينتظره/ها" بأي شكل
← ممنوع تماماً: وضع رمضان/العيد/اليوم الوطني/يوم التأسيس في موقع الانتظار — المناسبة لا تنتظر المنتج

ب. Heritage Decoder — جملة قصيرة تحمل كلمة بمعنيين في آنٍ واحد
← ناجح (مالية): الذكاء يستثمر فيك
← ناجح (أزياء): ترتدين المناسبة
← ناجح (غذاء): اللبن اللي يروبك
← فاشل وممنوع: اكتب الجملة فقط، بدون علامات اقتباس، بدون شرح للمعنى
← فاشل وممنوع: X معك في كل خطوة
← تجنب: "يشبك" — معناه الثاني "يعقّد/يُربك" يعكس المقصود
← تجنب: "يطمن قلبك" في سياق منتج — حميمية غير مقصودة

ج. Firaasa — ملاحظة سلوكية محددة لهذا المنتج تحديداً
← ناجح: "اللبن هو اللي يختارك — مو العكس"
← ناجح: "اللي يدور على صحة يدور على راحة بال"
← ممنوع تماماً: "الأم/الناس/الأسرة/العميل ما تدور/يدور على X — تدور/يدور على Y" — حتى مع تغيير الكلمات
← فاشل وممنوع: "في لحظة X، Y هو اللي..." أو "لحظة هدوء، تكتشف فيها..."
← الصحيح: لحظة سلوكية حقيقية خاصة بهذا المنتج تحديداً — مو قالب يصلح لأي منتج"""

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


_REASON_LABELS_COLLECTOR = {
    "قالب_مكرر": "قالب مكرر", "معنى_مزدوج": "معنى مزدوج",
    "طويل": "طويل جداً",       "عام": "عام وغير محدد",
    "لهجة": "لهجة خاطئة",
}

def _build_learned_addition() -> str:
    """Read human-reviewed examples and return extra prompt lines."""
    try:
        if not LEARNING_FILE.exists():
            return ""
        ld = json.loads(LEARNING_FILE.read_text())
        lines = []
        for tech in ("أ", "ب", "ج"):
            for p in ld.get("positive", {}).get(tech, [])[-2:]:
                lines.append(f'[{tech}] ناجح (معتمد بشرياً): "{p["caption"]}"')
            for n in ld.get("negative", {}).get(tech, [])[-2:]:
                label = _REASON_LABELS_COLLECTOR.get(n.get("reason", ""), "ضعيف")
                lines.append(f'[{tech}] مرفوض ({label}): "{n["caption"]}"')
        if not lines:
            return ""
        return "\n\n## أمثلة متعلَّمة من مراجعة بشرية:\n" + "\n".join(lines)
    except Exception:
        return ""


def build_prompt(brief: dict) -> str:
    max_chars  = MAX_CHARS.get(brief["sector"], 160)
    sector_ar  = SECTOR_AR.get(brief["sector"], brief["sector"])
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])
    learned_addition = _build_learned_addition()
    return f"""<RED_LINES>
ممنوع: السرير، خلع الملابس أو الحجاب، استغلال ضعف الناس أو خوفهم.
ممنوع: وضع مناسبة دينية (رمضان، العيد) أو وطنية (اليوم الوطني، يوم التأسيس) في موقع الانتظار للمنتج.
دائماً: لهجة سعودية طبيعية. حد أقصى {max_chars} حرف. بدون إنجليزي.
</RED_LINES>

<TECHNIQUES>
{TECHNIQUES_BLOCK}{learned_addition}
</TECHNIQUES>

<BRAND>
العلامة: {brief['brand']} | القطاع: {sector_ar} | المنتج: {brief['product']} | المناسبة: {occasion_ar}
الهاشتاقات: {brief['hashtags']}
</BRAND>

<TASK>
اكتب 3 كابشنات — كل واحد يطبّق تقنية مختلفة (أ، ب، ج).
كل كابشن: حد أقصى {max_chars} حرف. نص فقط — بدون علامات اقتباس، بدون شرح، بدون رقم التقنية، بدون اسم التقنية.
البنية اللغوية لكل خيار يجب أن تختلف — لا تنسخ نفس القالب ثلاث مرات بكلمات مختلفة.
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


_TECH_PREFIXES = re.compile(
    r"^(Paradox Hunter|Heritage Decoder|Firaasa|قلب التوقع|أ\.|ب\.|ج\.)"
    r"[\s\-—–:،.]*"
    r"(قلب التوقع|Heritage Decoder|Firaasa|Paradox Hunter)?"
    r"[\s\-—–:،.]*",
    re.IGNORECASE,
)
_QUOTE_STRIP = re.compile(r'^["\'""«»]+|["\'""«»]+$')


def _clean_caption(text: str) -> str:
    """Strip technique name prefixes and surrounding quotes from a caption."""
    text = text.strip()
    text = _TECH_PREFIXES.sub("", text).strip()
    text = _QUOTE_STRIP.sub("", text).strip()
    return text


def parse_response(raw: str) -> dict:
    """
    Extract the 3 technique options (أ, ب, ج) and الأفضل from ALLaM's response.
    Handles multiple output formats ALLaM uses:
      Format A: "أ. caption"  "ب. caption"  "ج. caption"
      Format B: "Paradox Hunter: caption"  "Heritage Decoder: caption"  "Firaasa: caption"
      Format C: unlabeled Arabic lines
    """
    options = {"أ": "", "ب": "", "ج": ""}
    best = ""

    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    # Strip UI chrome (chat sidebar text) from beginning
    start = 0
    for i, l in enumerate(lines):
        if any(x in l for x in ["Recent Chats", "Chat history", "MO\n", "New Chat"]):
            start = i + 1
    lines = lines[start:]

    # Extract الأفضل line
    for line in lines:
        if "الأفضل" in line:
            raw_best = re.sub(r"الأفضل\s*:\s*", "", line).strip()
            best = _clean_caption(raw_best)
            break

    # Format A: أ. / ب. / ج. labels
    for line in lines:
        for key in ("أ", "ب", "ج"):
            if re.match(rf"^{key}[\.\-\:]\s*", line):
                text = _clean_caption(re.sub(rf"^{key}[\.\-\:]\s*", "", line))
                if text and not options[key]:
                    options[key] = text
                break

    # Format B: Technique name labels → map to أ/ب/ج
    if not any(options.values()):
        tech_map = {
            "Paradox Hunter": "أ",
            "Heritage Decoder": "ب",
            "Firaasa": "ج",
        }
        for line in lines:
            for tech, key in tech_map.items():
                if line.startswith(tech):
                    text = _clean_caption(re.sub(rf"^{tech}\s*:\s*", "", line))
                    if text and not options[key]:
                        options[key] = text
                    break

    # Format C: unlabeled Arabic lines fallback
    if not any(options.values()):
        arabic_lines = [
            _clean_caption(l) for l in lines
            if any("؀" <= c <= "ۿ" for c in l)
            and "الأفضل" not in l
            and "<" not in l
        ]
        arabic_lines = [l for l in arabic_lines if l and len(l) > 5]
        for i, key in enumerate(("أ", "ب", "ج")):
            if i < len(arabic_lines):
                options[key] = arabic_lines[i]

    if not best and options["أ"]:
        best = options["أ"]

    return {"options": options, "best": best}


def load_queue() -> dict:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return {"pending": [], "approved": []}


def save_to_queue(brief: dict, raw_response: str) -> None:
    """Save a collected HUMAIN response to the review queue."""
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    queue = load_queue()

    parsed = parse_response(raw_response)
    sector_ar   = SECTOR_AR.get(brief["sector"], brief["sector"])
    occasion_ar = OCCASION_AR.get(brief["occasion"], brief["occasion"])

    # Remove any existing entry for this brief_id (allow re-collection)
    queue["pending"] = [p for p in queue["pending"] if p.get("brief_id") != brief["id"]]

    queue["pending"].append({
        "brief_id":    brief["id"],
        "brand":       brief["brand"],
        "sector":      brief["sector"],
        "sector_ar":   sector_ar,
        "occasion":    brief["occasion"],
        "occasion_ar": occasion_ar,
        "product":     brief["product"],
        "hashtags":    brief["hashtags"],
        "raw":         raw_response,
        "options":     parsed["options"],
        "best":        parsed["best"],
        "collected_at": datetime.now().isoformat(),
        "status":      "pending",
    })

    QUEUE_FILE.write_text(json.dumps(queue, ensure_ascii=False, indent=2))
    log(f"  💾 Saved to queue: Brief #{brief['id']} — {brief['brand']}")


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
                log(f"  ❌  No response for Brief #{brief['id']} — skipping.")
                continue

            # Parse and queue — no terminal input needed
            save_to_queue(brief, response)
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
        queue = load_queue()
        pending = len([p for p in queue["pending"] if p["status"] == "pending"])
        gold    = len(load_gold())
        log(f"\n{'='*60}")
        log(f"  Collection complete!")
        log(f"  {pending} responses queued for review.")
        log(f"  Gold approved so far: {gold}/300")
        log(f"\n  ✨ Open review page: {REVIEW_URL}")
        log(f"{'='*60}\n")


def reparse_queue() -> None:
    """Re-run parse_response on all queue entries — fixes earlier parser bugs."""
    if not QUEUE_FILE.exists():
        print("No queue file found.")
        return
    q = load_queue()
    fixed = 0
    for item in q["pending"]:
        raw = item.get("raw", "")
        if raw:
            parsed = parse_response(raw)
            item["options"] = parsed["options"]
            item["best"]    = parsed["best"]
            fixed += 1
    QUEUE_FILE.write_text(json.dumps(q, ensure_ascii=False, indent=2))
    print(f"Re-parsed {fixed} queue entries.")


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
    parser.add_argument("--reparse",  action="store_true", help="Re-parse existing queue entries with improved parser")
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

    if args.reparse:
        reparse_queue()
        return

    asyncio.run(run_browser(briefs))


if __name__ == "__main__":
    main()
