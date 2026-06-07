#!/usr/bin/env python3
"""Round 2: web-grounded consultation. Make GPT/Gemini/DeepSeek SEARCH and challenge."""
import json, urllib.request
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

PROMPT = """SEARCH THE INTERNET for the latest proven techniques, research, frameworks, and real case studies on generating HIGH-QUALITY SAUDI / GULF ARABIC social media marketing copy using LLMs. Cite your sources (URLs).

OUR GOAL: Generate Arabic Instagram captions for Saudi brands that a Saudi creative director rates "excellent/good" — short (<150 chars), in authentic Saudi dialect (Najdi/Hejazi, not Gulf-generic or stiff MSA), culturally safe, and genuinely creative. Today only 5 of 30 pass human review.

A PREVIOUS round of AI advice (from training knowledge, no search) recommended:
- Remove narrative/two-scene techniques from captions (keep for video)
- Use structured XML prompts + negative few-shot examples
- Prioritize wordplay/paradox techniques
- Keep a small model; don't fine-tune
- Use prompt engineering over fine-tuning

YOUR JOB: CHALLENGE this advice with REAL EVIDENCE from the internet. Don't just agree. Search for:
1. What does actual research / industry practice say about Arabic (esp. Saudi dialect) creative copy generation with LLMs in 2025-2026?
2. Are there proven Arabic-specific LLMs or fine-tunes (e.g. ALLaM, Jais, Fanar, AceGPT) that outperform GPT/Gemini for Saudi dialect creative writing? Should we use one?
3. Prompt engineering vs RAG vs fine-tuning — what does the evidence actually show works best for DIALECT-SPECIFIC creative quality?
4. What do the best Saudi/Gulf marketing agencies and Arabic AI content tools actually do?
5. Any frameworks, papers, or benchmarks specifically for evaluating/generating Saudi Arabic marketing copy?

Give evidence-based, specific, cited recommendations. Tell us if the previous advice is WRONG or incomplete based on what you find. Prioritize what would actually move our human-approval rate."""

results = {}

# ── GPT with web search (gpt-4o-search-preview) ─────────────────────
def ask_gpt_web():
    import openai
    c = openai.OpenAI(api_key=env["OPENAI_API_KEY"])
    # Try Responses API with web_search tool first, fall back to search-preview model
    try:
        r = c.responses.create(model="gpt-4o", tools=[{"type": "web_search_preview"}],
                               input=PROMPT)
        return r.output_text
    except Exception:
        r = c.chat.completions.create(model="gpt-4o-search-preview",
            messages=[{"role": "user", "content": PROMPT}], max_tokens=2500)
        return r.choices[0].message.content

# ── Gemini with Google Search grounding ─────────────────────────────
def ask_gemini_web():
    key = env.get("GEMINI_API_KEY") or env.get("GOOGLE_AI_STUDIO_KEY")
    for model in ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        body = json.dumps({
            "contents": [{"parts": [{"text": PROMPT}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"maxOutputTokens": 6000, "temperature": 0.7},
        }).encode()
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=180).read())
            cand = d["candidates"][0]
            txt = "".join(p.get("text", "") for p in cand["content"]["parts"])
            # Append grounding sources if present
            gm = cand.get("groundingMetadata", {})
            chunks = gm.get("groundingChunks", [])
            if chunks:
                txt += "\n\n## Sources (Google Search grounding):\n"
                for ch in chunks[:12]:
                    w = ch.get("web", {})
                    txt += f"- {w.get('title','')}: {w.get('uri','')}\n"
            return txt
        except Exception as e:
            last = f"{model}: {str(e)[:120]}"
    return f"[Gemini web failed: {last}]"

# ── DeepSeek via OpenRouter :online (web plugin) ────────────────────
def ask_deepseek_web():
    key = env.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_KEY_1")
    url = "https://openrouter.ai/api/v1/chat/completions"
    body = json.dumps({"model": "deepseek/deepseek-chat:online",
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 2500, "temperature": 0.7}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "HTTP-Referer": "https://ogzstudios.com", "X-Title": "OGZ Web Consultation"})
    d = json.loads(urllib.request.urlopen(req, timeout=180).read())
    return d["choices"][0]["message"]["content"]

for name, fn in [("GPT-4o-web", ask_gpt_web), ("Gemini-web", ask_gemini_web), ("DeepSeek-web", ask_deepseek_web)]:
    print(f"\n{'='*70}\n{name} (searching the web)...\n{'='*70}", flush=True)
    try:
        ans = fn()
    except Exception as e:
        ans = f"[{name} failed: {str(e)[:200]}]"
    results[name] = ans
    (OUT / f"{name}.md").write_text(f"# {name} — Web-Grounded Consultation\n\n{ans}\n")
    print(ans[:1600])
    print(f"\n... [saved to docs/consultations/{name}.md]")

combined = "# OGZ Caption Consultation — Round 2 (Web-Grounded)\n"
for name, ans in results.items():
    combined += f"\n\n{'='*72}\n# {name}\n{'='*72}\n\n{ans}\n"
(OUT / "ALL_RESPONSES_WEB.md").write_text(combined)
print(f"\n✅ Saved to docs/consultations/ (*-web.md + ALL_RESPONSES_WEB.md)")
