#!/usr/bin/env python3
"""humain_watchdog — keep the HUMAIN/ALLaM Saudi pen ALIVE (Rule #18 hard-role self-heal, June 29 2026).

ROOT CAUSE (audit + live fix): the pen DRIFTS — /health stays logged_in:true but the scrape returns null
because the persistent Playwright page wandered off the chat. A service RESTART re-navigates to a fresh
chat and the scrape works again (verified: a fresh page wrote real Najdi Arabic about jareesh). This
watchdog probes the REAL /caption path (not just /health), and on null RESTARTS humain_service.py. The
moat is the Saudi pen — this keeps it firing without a human noticing it died. Run via launchd ~every 30min.
"""
import json
import subprocess
import time
import urllib.request

SVC = "http://127.0.0.1:4111"
PY = "/opt/homebrew/bin/python3"
SERVICE = "/Users/abarihm/Desktop/ogz-knowledge/scripts/humain_service.py"
LOG = "/Users/abarihm/logs/humain_service.log"


def _probe():
    """The REAL test: does /caption actually reply (not just /health logged_in)?"""
    try:
        body = json.dumps({"prompt": "رد بكلمة واحدة: تمام", "timeout_s": 45}).encode()
        rq = urllib.request.Request(f"{SVC}/caption", data=body, headers={"Content-Type": "application/json"})
        out = json.loads(urllib.request.urlopen(rq, timeout=55).read())
        return bool(out.get("reply"))
    except Exception:
        return False


def _restart():
    subprocess.run(["pkill", "-f", "humain_service.py"])
    time.sleep(2)
    subprocess.Popen([PY, SERVICE], stdout=open(LOG, "a"), stderr=subprocess.STDOUT)
    # give the Playwright session ~60s to restore login, then confirm
    for _ in range(12):
        time.sleep(5)
        if _probe():
            return True
    return False


if __name__ == "__main__":
    if _probe():
        print("✅ humain pen alive (scrape replies)")
    else:
        print("🔴 humain pen DRIFTED (scrape null) → restarting service for a fresh page")
        print("✅ recovered" if _restart() else "⚠️ still down after restart — may need Mohamed's browser login")
