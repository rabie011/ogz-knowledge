#!/usr/bin/env python3
"""HUMAIN ARABIC JUDGE — the Saudi-native authority on the LANGUAGE half of a post.

Mohamed June 24: "you both are english base so you mistake the arabic — send the words to HUMAIN
with the context and understand what it means." RABIE (GPT) and Claude judge Arabic in a 2nd
language; they miss native-vs-translated feel, dialect, double-meaning, register. ALLaM 34B
(chat.humain.ai, via the local HUMAIN service) is Saudi-native — so it OWNS the caption verdict.

Ruling (Mohamed): HUMAIN wins on language, RABIE wins on the image; a post banks only if BOTH pass.

  from humain_judge import judge_caption
  v = judge_caption(caption, handle="albaik", product="دبل بيك", occasion="evergreen", scene="...")
  # -> {meaning, native_saudi, issues[], score 1-5, verdict bank|fix|kill, raw}

Uses the running HUMAIN service (scripts/humain_service.py, localhost:4111). If HUMAIN is down/
not-logged-in, returns verdict="unjudged" (NOT a pass — an Arabic post that HUMAIN could not read
must not be called clean; the caller treats unjudged as a HOLD, never a bank).
"""
import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

B = Path(__file__).parent.parent
HUMAIN_SVC = "http://127.0.0.1:4111"


def _brand_ar(handle):
    p = B / "clients" / handle / "profile" / "product_truth.json"
    if p.exists():
        d = json.loads(p.read_text())
        m = d.get("_meta", {})
        if m.get("brand"):
            return m["brand"]
    return handle


def _humain_up():
    try:
        out = json.loads(urllib.request.urlopen(f"{HUMAIN_SVC}/health", timeout=3).read())
        return bool(out.get("logged_in"))
    except Exception:
        return False


def _ask_humain(prompt, timeout_s=180):
    body = json.dumps({"prompt": prompt, "timeout_s": timeout_s}).encode()
    rq = urllib.request.Request(f"{HUMAIN_SVC}/caption", data=body,
                                headers={"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(rq, timeout=timeout_s + 30).read())
    return out.get("reply")


def _build_prompt(caption, brand_ar, product, occasion, scene):
    return f"""أنت مدقّق لغوي وثقافي سعودي خبير في اللهجة السعودية النجدية والتسويق. مهمتك تقييم
نص (كابشن) لإعلان على إنستقرام، بعين سعودي أصيل — لأن النماذج الإنجليزية تخطئ في فهم العربية.

البراند: {brand_ar}
المنتج: {product}
المناسبة: {occasion}
المشهد في الصورة: {scene}

الكابشن المطلوب تقييمه:
«{caption}»

قيّمه بصدق وحزم (3 = عادي، 4 = جيد بدليل، 5 = نادر وممتاز). افحص:
- المعنى الحقيقي (الحرفي + الضمني): ماذا يقول فعلاً؟ هل فيه معنى مزدوج أو غير مقصود؟
- هل يبدو سعودي أصيل أم ترجمة/ركيك/غير طبيعي؟
- أي خطأ لغوي أو نحوي أو إملائي، أو كلمة غير سعودية، أو نبرة خاطئة، أو مبالغة.
- هل يناسب البراند والمنتج والمناسبة؟

أجب بصيغة JSON فقط، بدون أي شرح خارج الـJSON:
{{
  "meaning": "المعنى الحقيقي للكابشن بالعربي (حرفي وضمني)",
  "native_saudi": true أو false,
  "issues": ["كل خطأ أو ملاحظة لغوية/ثقافية", "..."],
  "score": رقم من 1 إلى 5,
  "verdict": "bank" أو "fix" أو "kill"
}}"""


def judge_caption(caption, handle="", product="", occasion="evergreen", scene="", timeout_s=180):
    if not caption or not caption.strip():
        return {"verdict": "kill", "score": 1, "native_saudi": False,
                "issues": ["empty caption"], "meaning": "", "raw": ""}
    if not _humain_up():
        return {"verdict": "unjudged", "score": None, "native_saudi": None,
                "issues": ["HUMAIN service down / not logged in — Arabic NOT judged (HOLD, not a bank)"],
                "meaning": "", "raw": ""}
    brand_ar = _brand_ar(handle)
    prompt = _build_prompt(caption, brand_ar, product, occasion, scene)
    reply = _ask_humain(prompt, timeout_s=timeout_s)
    if not reply:
        return {"verdict": "unjudged", "score": None, "native_saudi": None,
                "issues": ["HUMAIN returned no reply (HOLD, not a bank)"], "meaning": "", "raw": ""}
    m = re.search(r"\{.*\}", reply, re.S)
    if not m:
        return {"verdict": "unjudged", "score": None, "native_saudi": None,
                "issues": [f"HUMAIN reply not JSON (HOLD): {reply[:120]}"], "meaning": "", "raw": reply}
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"verdict": "unjudged", "score": None, "native_saudi": None,
                "issues": [f"HUMAIN JSON parse failed (HOLD): {m.group(0)[:120]}"], "meaning": "", "raw": reply}
    d.setdefault("issues", [])
    d.setdefault("meaning", "")
    d.setdefault("native_saudi", None)
    score = d.get("score")
    if "verdict" not in d:
        d["verdict"] = "bank" if (isinstance(score, (int, float)) and score >= 4) else ("fix" if score == 3 else "kill")
    d["raw"] = reply
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caption", required=True)
    ap.add_argument("--handle", default="")
    ap.add_argument("--product", default="")
    ap.add_argument("--occasion", default="evergreen")
    ap.add_argument("--scene", default="")
    a = ap.parse_args()
    v = judge_caption(a.caption, a.handle, a.product, a.occasion, a.scene)
    emoji = {"bank": "✅", "fix": "🔧", "kill": "💀", "unjudged": "⏸"}.get(v["verdict"], "?")
    print(f"\n{'='*60}")
    print(f"HUMAIN (Saudi-native) says: {emoji} {v['verdict'].upper()}  (score {v.get('score')}/5)")
    print(f"  native_saudi: {v.get('native_saudi')}")
    print(f"  meaning: {v.get('meaning','')}")
    if v.get("issues"):
        print("  issues:")
        for i in v["issues"]:
            print(f"    - {i}")
    print(f"{'='*60}\n")
    print(json.dumps(v, ensure_ascii=False))


if __name__ == "__main__":
    main()
