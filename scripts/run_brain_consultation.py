"""
Round 3 Consultation — Is the Full Brain Architecture Right?
Queries GPT-4o and Gemini with the same brief. Saves responses to docs/consultations/.
"""

import os, pathlib, textwrap

ROOT = pathlib.Path(__file__).parent.parent

# Load API keys from file
env = {}
with open(os.path.expanduser("~/.abraham_env")) as f:
    for line in f:
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

OPENAI_KEY = env.get("OPENAI_API_KEY", "")
GEMINI_KEY = env.get("GEMINI_API_KEY", "") or env.get("GOOGLE_AI_STUDIO_KEY", "")

BRIEF = textwrap.dedent("""
You are advising a Saudi content generation platform (B2B SaaS, serving creative agencies in Riyadh).

## Context
The platform generates Arabic Instagram captions for Saudi brands across sectors: F&B, Real Estate, Occasions, FMCG, Retail, Corporate.

The current system has a "5 CD Brain" (Creative Director methodology) architecture. Each generation call is assigned one of 5 methodologies that inject creative direction into the prompt:
1. Firaasa Architect — human truth detection, Saudi behavioral insight
2. Metaphor Architect — visual metaphors from everyday objects
3. Authenticity Detective — performance vs reality contrast (built for VIDEO scripts)
4. Heritage Decoder — double-meaning Arabic words (one modern, one classical reading)
5. Paradox Hunter — counter-intuitive contrasts, "العكس هو الصحيح" style

On top of the CD Brain, the system also has:
- 80-field Cultural Spec per brand (modesty thresholds, dialect, forbidden elements)
- 88 Chain library (proven content formulas: problem→solution, before→after, etc.)
- 5,014 Arabic caption templates extracted from top Saudi Instagram accounts
- 6,888 real Saudi caption observations with engagement data (engagement rate, saves, comments)
- ML engagement predictor trained on the above

## Problem
Human review (Mohamed, the creative director, native Saudi) rated 25/30 outputs weak or fail. Key complaints:
- Captions too long (300-400 chars when they should be 120-160)
- Cultural violations: veil references, bed scenes, exploiting emotions — Authenticity Detective caused these
- Generic MSA Arabic instead of Najdi/Gulf dialect
- "Instruction bloat" — prompt is too dense, model ignores red lines

Previous round of consultation (3 LLMs) concluded:
- Kill Authenticity Detective for captions (video technique only)
- Rebuild prompt: XML-tagged sections + negative few-shot
- Round 2 (web-grounded): real moat is fine-tuning ALLaM-7B (Saudi national LLM) on our 6,888 captions

## Question (Round 3 — Architectural)
This round we're asking a MORE FUNDAMENTAL question:

**Q1: Is the 5-methodology CD Brain architecture the RIGHT way to structure creative direction for an AI content system targeting Saudi brands?**
- What are the alternatives? (e.g., single unified style guide, persona-based, constraint-only, retrieval-based)
- What does research say about multi-technique routing vs simpler approaches for domain-specific creative generation?

**Q2: Is the full multi-layer brain needed?** The system has 5 layers: CD methodologies + cultural specs + chain library + templates + engagement data.
- Which layers genuinely add value vs which are complexity for its own sake?
- What's the minimum viable brain that reaches >70% human approval for Saudi Instagram content?
- Is there a simpler architecture that outperforms this multi-layer approach?

**Q3: Given we're heading toward a fine-tuned Saudi LLM (ALLaM-7B + LoRA on our 6,888 captions) — what role, if any, does the CD Brain play AFTER the model is fine-tuned?**
- Does a fine-tuned domain model make the methodology injection layer obsolete?
- Or is there a role for the brain as a post-fine-tune creative direction layer?

**Q4: What is the SIMPLEST architecture that would work at >70% human approval for Saudi Instagram captions, starting from today?**

Be direct. If the CD Brain is over-engineered, say so. If it's the right structure with the wrong implementation, say so. Ground your answer in what actually works for domain-specific Arabic creative content generation — not generic best practices.
""").strip()


def query_gpt4o(brief):
    import urllib.request, json
    payload = json.dumps({
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": brief}],
        "temperature": 0.7,
        "max_tokens": 2000
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def query_gemini(brief):
    import urllib.request, json
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": brief}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2000}
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["candidates"][0]["content"]["parts"][0]["text"]


out_dir = ROOT / "docs" / "consultations"
out_dir.mkdir(parents=True, exist_ok=True)

print("=== Round 3 Brain Architecture Consultation ===\n")
print("Querying GPT-4o...")
gpt_response = query_gpt4o(BRIEF)
print("GPT-4o done.\n")

(out_dir / "GPT-4o-brain.md").write_text(
    f"# GPT-4o — Brain Architecture Consultation (Round 3)\n\n{gpt_response}\n"
)
print("Saved: GPT-4o-brain.md")
print("\n--- GPT-4o RESPONSE (preview) ---")
print(gpt_response[:800])
print("...")
