#!/usr/bin/env python3
"""
refresh_instagram_cookies.py
Export Instagram cookies from Chrome Profile 1 to Netscape format.
Run this whenever cookies expire or before a caption/transcription batch.

Output: logs/.instagram_cookies.txt
"""
import sys
from pathlib import Path

BASE        = Path(__file__).parent.parent
COOKIE_OUT  = BASE / "logs" / ".instagram_cookies.txt"
COOKIE_OUT.parent.mkdir(exist_ok=True)

# Chrome profiles to try in order
CHROME_BASE = Path.home() / "Library/Application Support/Google/Chrome"
PROFILES    = ["Profile 1", "Profile 2", "Default", "Profile 3", "Profile 4"]

def export_cookies() -> int:
    try:
        import browser_cookie3
    except ImportError:
        print("ERROR: browser_cookie3 not installed")
        sys.exit(1)

    for profile in PROFILES:
        cookie_db = CHROME_BASE / profile / "Cookies"
        if not cookie_db.exists():
            continue
        try:
            cj = browser_cookie3.chrome(
                cookie_file=str(cookie_db),
                domain_name="instagram.com"
            )
            cookies = list(cj)
            if not cookies:
                continue

            lines = ["# Netscape HTTP Cookie File"]
            for c in cookies:
                secure = "TRUE" if c.secure else "FALSE"
                exp    = int(c.expires) if c.expires else 0
                lines.append(
                    f".instagram.com\tTRUE\t/\t{secure}\t{exp}\t{c.name}\t{c.value}"
                )
            COOKIE_OUT.write_text("\n".join(lines))
            print(f"  Cookies refreshed from {profile} — {len(cookies)} cookies → {COOKIE_OUT}")
            return len(cookies)
        except Exception as e:
            continue

    print("ERROR: No Instagram cookies found in any Chrome profile. Log into Instagram in Chrome first.")
    sys.exit(1)


if __name__ == "__main__":
    n = export_cookies()
    print(f"  ✅ {n} Instagram cookies ready")
