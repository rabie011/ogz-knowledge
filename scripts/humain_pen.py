#!/usr/bin/env python3
"""HUMAIN caption pen — drive chat.humain.ai (ALLaM 34B, Saudi-native Arabic) as a LIVE caption
generator for the orchestra. Reuses the proven humain_collector browser harness, but exposes a
SINGLE-PROMPT, SYNCHRONOUS call so the caption pipeline (render_client_slot.gpt/sonnet) can ask
HUMAIN inline — the model-diversity pen the dark Sonnet pen can no longer provide (Rule:
"minds run on DIFFERENT models"; ALLaM 34B is genuinely Saudi-native, not a translator).

  from humain_pen import humain_pen, humain_available
  if humain_available():
      text = humain_pen("اكتب 3 كابشن ...")   # raw model text, or None on failure

DESIGN
  • ONE persistent browser (login saved in ~/.humain_playwright_session); the page stays open
    across calls so the orchestra asks HUMAIN repeatedly without relaunching.
  • Playwright objects are event-loop-bound, and the caption pipeline is synchronous — so the
    browser lives on a DEDICATED background event loop in its own thread; sync calls submit
    coroutines to it via run_coroutine_threadsafe.
  • NEVER blocks the pipeline (Rule: never get stuck). A cold/expired session, a missing browser,
    or a timeout returns None — the caller falls back to GPT exactly like it falls back on a dark
    Sonnet. Set HUMAIN_PEN=0 to hard-disable (then humain_available() is False, $0, no browser).

LOGIN: the session expires (~hourly). probe_login() opens the browser and reports whether a
manual login is needed; warm_up(login_wait_minutes=N) opens it VISIBLE and waits for Mohamed.
"""
import asyncio
import json
import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import humain_collector as hc   # proven harness: find_chat_input, wait_for_response, dismiss_modal, selectors

ENABLED = os.environ.get("HUMAIN_PEN", "1") != "0"

# ── the dedicated background event loop (Playwright objects are loop-bound) ──────────────────
_loop = None
_thread = None
_ctx = None      # persistent browser context
_page = None     # the live chat page
_lock = threading.Lock()
_logged_in = False


def _start_loop():
    global _loop, _thread
    if _loop is not None:
        return
    _loop = asyncio.new_event_loop()

    def _run():
        asyncio.set_event_loop(_loop)
        _loop.run_forever()

    _thread = threading.Thread(target=_run, daemon=True, name="humain-pen-loop")
    _thread.start()


def _submit(coro, timeout):
    """Run a coroutine on the background loop, block up to `timeout` seconds for the result."""
    _start_loop()
    fut = asyncio.run_coroutine_threadsafe(coro, _loop)
    return fut.result(timeout=timeout)


async def _open_browser(login_wait_minutes: int):
    """Open the persistent context + page; ensure a chat input is reachable (login restored)."""
    global _ctx, _page, _logged_in
    if _page is not None:
        return True
    from playwright.async_api import async_playwright
    import os as _os
    global _pw
    _pw = await async_playwright().start()
    # CONNECT to Mohamed's ALREADY-OPEN, already-logged-in browser via CDP (June 29 — "humain is working on
    # the browser, you open it in a new one and it's already opened"). Our own Chrome-for-Testing context has
    # a separate cookie jar and CANNOT see his real-browser HUMAIN session. Attaching to a debug-port browser
    # he keeps open reuses HIS login forever (DeepSeek consult: more robust than launch_persistent_context,
    # which profile-locks against his running Chrome). Try CDP first; fall back to our own window only if no
    # debug browser is up on the port. Launcher: scripts/open_humain_browser.sh.
    _cdp = _os.environ.get("HUMAIN_CDP", "http://127.0.0.1:9222")
    try:
        _browser = await _pw.chromium.connect_over_cdp(_cdp, timeout=4000)
        _ctx = _browser.contexts[0] if _browser.contexts else await _browser.new_context()
        _page = next((p for c in _browser.contexts for p in c.pages if "humain" in (p.url or "").lower()), None)
        if _page is None:
            _page = _ctx.pages[0] if _ctx.pages else await _ctx.new_page()
            await _page.goto(hc.HUMAIN, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        _ci, _ = await hc.find_chat_input(_page)
        _logged_in = _ci is not None
        if _logged_in:
            print(f"   ✅ connected to your EXISTING browser via CDP {_cdp} — no new window", flush=True)
            return True
        print(f"   (CDP browser on {_cdp} reachable but HUMAIN not logged in there — falling back)", flush=True)
    except Exception:
        pass  # no debug browser on the port → our own persistent-context window below
    hc.SESSION_DIR.mkdir(parents=True, exist_ok=True)
    _ctx = await _pw.chromium.launch_persistent_context(
        str(hc.SESSION_DIR),
        headless=False,
        slow_mo=60,
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
    )
    _page = _ctx.pages[0] if _ctx.pages else await _ctx.new_page()
    await _page.goto(hc.HUMAIN, wait_until="domcontentloaded", timeout=30000)
    await asyncio.sleep(5)
    chat_input, _ = await hc.find_chat_input(_page)
    if chat_input is None and login_wait_minutes > 0:
        ok = await hc.wait_for_login(_page, max_minutes=login_wait_minutes)
        if ok:
            chat_input, _ = await hc.find_chat_input(_page)
    _logged_in = chat_input is not None
    return _logged_in


async def _ask(prompt: str, timeout_s: int):
    """Send one prompt to the open page, return the model's stabilised reply text (or None)."""
    global _page
    if _page is None:
        return None
    chat_input, sel = await hc.find_chat_input(_page)
    if chat_input is None:
        # try a reload once (session/page may have drifted)
        await _page.goto(hc.HUMAIN, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(3)
        chat_input, sel = await hc.find_chat_input(_page)
        if chat_input is None:
            return None

    # paste via clipboard (most reliable across editor types — same as the collector)
    await _page.evaluate(f"navigator.clipboard.writeText({json.dumps(prompt)})")
    await chat_input.click()
    await _page.keyboard.press("Meta+a")
    await asyncio.sleep(0.2)
    await _page.keyboard.press("Meta+v")
    await asyncio.sleep(0.8)

    sent = False
    for btn_sel in hc.SEND_BTN_SELECTORS:
        try:
            btn = _page.locator(btn_sel).last
            if await btn.is_enabled(timeout=1000):
                await btn.click()
                sent = True
                break
        except Exception:
            pass
    if not sent:
        await _page.keyboard.press("Enter")

    return await _capture_reply(prompt, timeout_s)


async def _capture_reply(prompt, timeout_s):
    """Capture ALLaM's actual reply (June 24 DOM-verified fix). The current turn lives in the LAST
    [class*='message'] element as "{prompt}\\n\\n{reply}" — so we target THAT (NOT div.group/article,
    which match the 'Recent Chats' SIDEBAR = stale prompts, the echo bug), wait for it to stabilise,
    and STRIP the prompt prefix to return only the model's answer."""
    p = (prompt or "").strip()
    deadline = asyncio.get_event_loop().time() + timeout_s
    prev, stable = "", 0
    sels = ["[class*='message']", ".prose", "[class*='markdown']", "[data-message-author-role='assistant']"]
    while asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(3)
        full = ""
        for s in sels:
            try:
                loc = _page.locator(s)
                n = await loc.count()
                if n:
                    t = (await loc.nth(n - 1).inner_text()).strip()
                    if t:
                        full = t
                        break
            except Exception:
                pass
        if not full:
            continue
        # strip the prompt prefix → ALLaM's answer only
        reply = full
        if p and p in full:
            reply = full.split(p)[-1].strip()
        # ignore sidebar/pen-prompt echoes that slipped in
        if not reply or "<RED_LINES>" in reply or "You write Instagram captions" in reply:
            reply = ""
        if reply and reply == prev:
            stable += 1
            if stable >= 2:   # text settled → ALLaM finished
                return reply
        else:
            stable = 0
            prev = reply
    return prev or None


async def _new_chat():
    """Start a fresh chat so each caption ask is independent (no context bleed)."""
    if _page is None:
        return
    for sel in ["button:has-text('New chat')", "button:has-text('محادثة جديدة')",
                "a:has-text('New chat')", "[aria-label*='new chat' i]"]:
        try:
            b = _page.locator(sel).first
            if await b.is_visible(timeout=800):
                await b.click()
                await asyncio.sleep(1.5)
                return
        except Exception:
            pass


async def _debug_dump(prompt, wait_s=25):
    """DOM inspector — send a distinctive prompt, wait, then report what each candidate selector
    actually matches so we can find the REAL assistant-reply element (fixing the prompt-echo bug)."""
    if _page is None:
        return {"error": "no page"}
    # send the prompt
    chat_input, sel = await hc.find_chat_input(_page)
    if chat_input is None:
        return {"error": "no chat input"}
    await _page.evaluate(f"navigator.clipboard.writeText({json.dumps(prompt)})")
    await chat_input.click()
    await _page.keyboard.press("Meta+a")
    await asyncio.sleep(0.2)
    await _page.keyboard.press("Meta+v")
    await asyncio.sleep(0.6)
    sent = False
    for btn_sel in hc.SEND_BTN_SELECTORS:
        try:
            btn = _page.locator(btn_sel).last
            if await btn.is_enabled(timeout=1000):
                await btn.click()
                sent = True
                break
        except Exception:
            pass
    if not sent:
        await _page.keyboard.press("Enter")
    await asyncio.sleep(wait_s)  # let ALLaM answer
    # dump candidate selectors
    out = {"input_selector": sel, "sent_via": "button" if sent else "enter", "selectors": {}}
    cands = ["[data-role='assistant']", "[data-message-author-role='assistant']", ".assistant-message",
             "article", ".message", "div.group", ".prose", "[class*='markdown']", "[class*='assistant']",
             "[class*='message']", "main div", "p"]
    for s in cands:
        try:
            loc = _page.locator(s)
            n = await loc.count()
            texts = []
            for i in range(max(0, n - 3), n):  # last 3
                try:
                    t = (await loc.nth(i).inner_text()).strip()
                    if t:
                        texts.append(t[:200])
                except Exception:
                    pass
            if n:
                out["selectors"][s] = {"count": n, "last_texts": texts}
        except Exception as e:
            out["selectors"][s] = {"error": str(e)[:60]}
    try:
        body = await _page.inner_text("body")
        out["body_tail"] = body[-1500:]
    except Exception:
        out["body_tail"] = ""
    return out


# ── public sync API ───────────────────────────────────────────────────────────────────────
def humain_available() -> bool:
    return ENABLED


def debug_dump(prompt="قل كلمة: تجربة_فحص_دوم_١٢٣", timeout=90):
    if not ENABLED:
        return {"error": "disabled"}
    with _lock:
        try:
            if _page is None and not _submit(_open_browser(login_wait_minutes=0), timeout=120):
                return {"error": "not logged in"}
            return _submit(_debug_dump(prompt), timeout=timeout)
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)[:100]}"}


def probe_login(timeout=90) -> bool:
    """Open the browser (no login wait) and report whether HUMAIN is already logged in."""
    if not ENABLED:
        return False
    with _lock:
        try:
            return bool(_submit(_open_browser(login_wait_minutes=0), timeout=timeout))
        except Exception as e:
            print(f"  humain probe failed: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
            return False


def warm_up(login_wait_minutes=15, timeout=None) -> bool:
    """Open the browser VISIBLE and wait up to N minutes for Mohamed to log in if needed."""
    if not ENABLED:
        return False
    timeout = timeout or (login_wait_minutes * 60 + 60)
    with _lock:
        try:
            return bool(_submit(_open_browser(login_wait_minutes=login_wait_minutes), timeout=timeout))
        except Exception as e:
            print(f"  humain warm_up failed: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
            return False


def humain_pen(prompt: str, timeout_s: int = 180, fresh_chat: bool = True) -> str | None:
    """Ask HUMAIN one prompt; return raw reply text or None. Never raises (Rule: never stuck)."""
    if not ENABLED:
        return None
    with _lock:
        try:
            if _page is None and not _submit(_open_browser(login_wait_minutes=0), timeout=120):
                return None
            if fresh_chat:
                try:
                    _submit(_new_chat(), timeout=20)
                except Exception:
                    pass
            return _submit(_ask(prompt, timeout_s), timeout=timeout_s + 30)
        except Exception as e:
            print(f"  humain pen failed: {type(e).__name__}: {str(e)[:80]}", file=sys.stderr)
            return None


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true", help="open browser, report login state")
    ap.add_argument("--warm", action="store_true", help="open browser, wait for manual login")
    ap.add_argument("--ask", default="", help="send a test prompt and print the reply")
    a = ap.parse_args()
    if a.probe:
        print("logged_in:", probe_login())
    elif a.warm:
        print("logged_in after warm_up:", warm_up())
    elif a.ask:
        print("REPLY:\n", humain_pen(a.ask))
    else:
        ap.print_help()
