#!/usr/bin/env python3
"""Send the caption consultation brief to GPT, Gemini, and DeepSeek. Collect advice."""
import os, json, urllib.request
from pathlib import Path

def load_env():
    env = {}
    for line in (Path.home() / ".abraham_env").read_text().splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.replace("export ", "").split("=", 1)
            env[k.strip()] = v.strip().strip('"\'')
    return env

env = load_env()
OUT = Path("/Users/abarihm/Desktop/ogz-knowledge/docs/consultations")
OUT.mkdir(exist_ok=True)

# ── The consultation brief ──────────────────────────────────────────
BRIEF = """You are a senior creative director AND AI prompt engineer specializing in Saudi Arabic social media marketing. Give honest, specific, actionable advice — not generic encouragement.

=== OUR SITUATION ===
We (OGZ Studios, a Saudi video production company) built a Saudi-native content intelligence platform that generates Arabic Instagram captions for Saudi brands.

ASSETS WE HAVE:
- 6,888 real, verified Saudi Instagram posts (captions + real likes), 3,077 with real engagement numbers
- 5,014 caption templates tiered by real engagement (gold/silver/bronze)
- Brand voice, correct product names, signature hashtags for 23+ Saudi brands
- Saudi dialect rules (Najdi/Hejazi markers to USE: وش، الحين، يالله، حلو، كذا; Gulf/MSA words to AVOID: شنو، جذي، زين، تفضلوا)
- 10 Saudi occasions with required words (Ramadan, founding day, national day, Eid, etc.)
- 5 "Creative Director brain" methodologies that route by sector + occasion:
  1. Firaasa Architect — name the Saudi cultural truth before the product (why-before-what)
  2. Metaphor Architect — build a full metaphor system, then a "but wait" reveal
  3. Authenticity Detective — two-scene contrast: how people PERFORM vs how they FEEL
  4. Heritage Decoder — a double-meaning Arabic word as the structural key (e.g. ترتوي = the land drinks / stories are told)
  5. Paradox Hunter — a counterintuitive flip; the product as the mechanism
- A quality gate with 11 automated checks (dialect, product name, cultural red lines, length)

HOW WE GENERATE A CAPTION NOW:
1. Route the brief (brand, product, occasion) to a CD methodology by sector+occasion affinity
2. Pull 3-5 real high-engagement Saudi captions (templates) for that sector+occasion
3. Build a prompt: brand voice + real templates + the CD technique + dialect rules + cultural red lines + length cap
4. Generate with an LLM (gpt-4o-mini; we tested gpt-4o and saw no consistent gain)
5. Screen through the quality gate

=== THE PROBLEM ===
A Saudi creative director rated 30 of our captions BLIND: only 1 excellent, 4 good, 13 weak, 12 fail. ~83% are not good enough by his eye.

His specific complaints (verbatim themes from his notes):
1. TOO LONG — the #1 complaint (10 of 18 notes were "too long / long and incoherent / boring"). Captions ran 300-400 characters. We have since capped length to ~120-170.
2. CULTURAL RED LINES VIOLATED (absolute, non-negotiable in Saudi content):
   - No reference to removing any clothing or the veil/khimar (ازالة ملابس، تفك الخمار)
   - No bed or bedroom scenes (السرير، غرفة النوم)
   - No exploiting people's vulnerability/weakness as a hook (استغلال ضعف الناس)
   We now hard-block these.
3. THE AUTHENTICITY DETECTIVE technique (the "performance vs reality" two-scene contrast) was the worst offender — it generated long, intimate, culturally-inappropriate scenes (removing a veil, family on a bed). We constrained it to public scenes.

A FAIL example (before fixes): "قهوة مختصة، لمّا تشعر بالجوع بعد يوم طويل من الصيام، تخيل اللحظة اللي تفك فيها الخمار وتقول: أخيرًا وقت الإفطار!"
An APPROVED example (excellent): "في مشروع سكني، يُستحضر التاريخ من عمق الأرض، حيث تُبنى البيوت لتكون ملاذًا وذكريات تُروى. في يوم التأسيس، نحتفل بجذورنا."

=== A CRITICAL FINDING ===
We built an AI "methodology judge" (gpt-4o) to auto-score caption quality. We validated it against the human's ratings: it scored ESSENTIALLY RANDOM (rank correlation +0.08, 47% agreement). It gave ~6/10 to everything regardless of quality — including the culturally-forbidden captions. CONCLUSION: automated AI scoring is NOT trustworthy for Saudi creative/cultural quality. Human review is our only ground truth — but it doesn't scale.

=== WHAT REAL SAUDI ENGAGEMENT TELLS US ===
We analyzed 300 highest-engagement real Saudi captions by technique:
- Counterintuitive flip: 19% usage, +35% above avg engagement (UNDERUSED, best performer)
- Plain marketing: 9%, +4%
- Double-meaning word: 10%, +1%
- Metaphor system: 13%, +1%
- Human-truth opening: 48% usage, -15% engagement (OVERUSED, worst performer)
91% of winning Saudi captions use a creative technique.

=== QUESTIONS FOR YOU ===
1. METHODOLOGY: Are these 5 CD techniques the right framework for SHORT social captions (~150 chars), or are some (like the two-scene Authenticity Detective) fundamentally better suited to VIDEO than to a caption?
2. PROMPTING: Given real templates + a named technique + dialect rules, what prompt architecture most reliably produces short, coherent, culturally-safe, genuinely-creative Saudi copy? Be specific.
3. LENGTH vs DEPTH: How do we keep a real creative technique (e.g. a double-meaning word) while staying under ~150 characters?
4. MODEL STRATEGY: gpt-4o didn't beat gpt-4o-mini with our prompt. Is that a prompt ceiling, or should we fine-tune a Saudi-dialect model? What would you do?
5. THE LEARNING LOOP: Human review is our only trusted signal but doesn't scale. How do we build a learning loop that improves quality WITHOUT a reliable automated judge?

Give your most specific, expert recommendations. Prioritize what would move our human-approval rate from 5/30 toward the majority. Concrete prompt structures, technique advice, and architecture changes are more valuable than general principles."""

SYSTEM = "You are a world-class creative director and AI engineer specializing in Saudi/Gulf Arabic advertising and LLM prompt design."

results = {}

# ── GPT (OpenAI gpt-4o) ─────────────────────────────────────────────
def ask_gpt():
    import openai
    c = openai.OpenAI(api_key=env["OPENAI_API_KEY"])
    r = c.chat.completions.create(model="gpt-4o",
        messages=[{"role":"system","content":SYSTEM},{"role":"user","content":BRIEF}],
        max_tokens=2000, temperature=0.7)
    return r.choices[0].message.content

# ── Gemini (Google AI Studio) ───────────────────────────────────────
def ask_gemini():
    key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_AI_STUDIO_KEY")
    for model in ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        body = json.dumps({"contents":[{"parts":[{"text":SYSTEM+"\n\n"+BRIEF}]}],
                           "generationConfig":{"maxOutputTokens":2000,"temperature":0.7}}).encode()
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=90).read())
            return d["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            last = f"{model}: {str(e)[:120]}"
    return f"[Gemini failed: {last}]"

# ── DeepSeek (via OpenRouter) ───────────────────────────────────────
def ask_deepseek():
    key = env.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_KEY_1")
    url = "https://openrouter.ai/api/v1/chat/completions"
    body = json.dumps({"model":"deepseek/deepseek-chat",
        "messages":[{"role":"system","content":SYSTEM},{"role":"user","content":BRIEF}],
        "max_tokens":2000,"temperature":0.7}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization":f"Bearer {key}","Content-Type":"application/json",
        "HTTP-Referer":"https://ogzstudios.com","X-Title":"OGZ Caption Consultation"})
    d = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return d["choices"][0]["message"]["content"]

for name, fn in [("GPT-4o", ask_gpt), ("Gemini", ask_gemini), ("DeepSeek", ask_deepseek)]:
    print(f"\n{'='*70}\nConsulting {name}...\n{'='*70}", flush=True)
    try:
        ans = fn()
    except Exception as e:
        ans = f"[{name} failed: {str(e)[:200]}]"
    results[name] = ans
    (OUT / f"{name}.md").write_text(f"# {name} — Caption Consultation Response\n\n{ans}\n")
    print(ans[:1500])
    print(f"\n... [full response saved to docs/consultations/{name}.md]")

# Combined file
combined = "# OGZ Caption Consultation — Three LLM Responses\n\n"
for name, ans in results.items():
    combined += f"\n\n{'='*70}\n# {name}\n{'='*70}\n\n{ans}\n"
(OUT / "ALL_RESPONSES.md").write_text(combined)
print(f"\n\n✅ All saved to docs/consultations/ (GPT-4o.md, Gemini.md, DeepSeek.md, ALL_RESPONSES.md)")
