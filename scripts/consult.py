#!/usr/bin/env python3
"""CONSULT — ask OTHER LLMs before doing (Mohamed June 23: "always ask other llm before doing").

The "never act alone" wire for the orchestra. RABIE runs on GPT (a different family from Claude);
this lets Claude + RABIE put any plan/fix/judgment in front of an INDEPENDENT panel — GPT-4o
(OpenAI), Gemini (Google AI Studio), Llama-3.3-70B (Groq) — before acting. Each model is isolated;
a dead key/quota returns an error string, never blocks the others (never get stuck).

Usage:
  python3 scripts/consult.py "should we X or Y? give a 2-line verdict"
  python3 scripts/consult.py --models gpt,gemini "..."
  from consult import consult; consult("...")  -> {model: answer}
"""
import argparse, json, os, sys, urllib.request, urllib.error

ENV = os.path.expanduser("~/.abraham_env")


def env(k):
    if not os.path.exists(ENV):
        return None
    for l in open(ENV):
        if l.startswith(k + "="):
            return l.split("=", 1)[1].strip().strip('"')
    return None


def _post(url, body, headers, timeout=60):
    rq = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers)
    return json.loads(urllib.request.urlopen(rq, timeout=timeout).read())


def ask_gpt(prompt, system="You are a sharp, independent advisor. Be concise and concrete."):
    key = env("OPENAI_API_KEY")
    if not key:
        return "(no OPENAI_API_KEY)"
    try:
        out = _post("https://api.openai.com/v1/chat/completions",
                    {"model": "gpt-4o", "temperature": 0.3, "max_tokens": 600,
                     "messages": [{"role": "system", "content": system},
                                  {"role": "user", "content": prompt}]},
                    {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        return out["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(gpt error: {type(e).__name__}: {str(e)[:120]})"


def ask_gemini(prompt):
    key = env("GEMINI_API_KEY") or env("GOOGLE_AI_STUDIO_KEY")
    if not key:
        return "(no GEMINI/GOOGLE key)"
    for model in ("gemini-2.5-flash", "gemini-2.0-flash"):  # 1.5-flash deprecated (404 on v1beta)
        try:
            out = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                        {"contents": [{"parts": [{"text": prompt}]}]},
                        {"Content-Type": "application/json"})
            return out["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            last = f"(gemini {model} error: {type(e).__name__}: {str(e)[:100]})"
    return last


def ask_groq(prompt, system="You are a sharp, independent advisor. Be concise and concrete."):
    key = env("GROQ_API_KEY")
    if not key:
        return "(no GROQ_API_KEY)"
    for model in ("llama-3.3-70b-versatile", "llama-3.1-70b-versatile"):
        try:
            out = _post("https://api.groq.com/openai/v1/chat/completions",
                        {"model": model, "temperature": 0.3, "max_tokens": 600,
                         "messages": [{"role": "system", "content": system},
                                      {"role": "user", "content": prompt}]},
                        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            return out["choices"][0]["message"]["content"].strip()
        except Exception as e:
            last = f"(groq {model} error: {type(e).__name__}: {str(e)[:100]})"
    return last


def ask_deepseek(prompt, system="You are a sharp, independent technical advisor. Challenge the plan, "
                 "find the gaps and risks, be concrete. If something is wrong, say so plainly.",
                 model="deepseek-chat", max_tokens=1100, timeout=120):
    """DeepSeek — the STANDING consult (Mohamed June 28: 'always consult him, make it a role').
    API key DEEPSEEK_API_KEY in ~/.abraham_env; OpenAI-compatible.
    model: 'deepseek-chat' (fast) or 'deepseek-reasoner' (deeper architecture/logic — slower)."""
    key = env("DEEPSEEK_API_KEY")
    if not key:
        return "(no DEEPSEEK_API_KEY)"
    try:
        out = _post("https://api.deepseek.com/chat/completions",
                    {"model": model, "temperature": 0.3, "max_tokens": max_tokens,
                     "messages": [{"role": "system", "content": system},
                                  {"role": "user", "content": prompt}]},
                    {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, timeout=timeout)
        return out["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"(deepseek error: {type(e).__name__}: {str(e)[:120]})"


def ask_deepseek_reasoner(prompt, **kw):
    """The reasoner model — for the hardest design/architecture calls (Mohamed: 'use his key a different way')."""
    return ask_deepseek(prompt, model="deepseek-reasoner", max_tokens=2000, timeout=240, **kw)


_PANEL = {"deepseek": ask_deepseek, "gpt": ask_gpt, "gemini": ask_gemini, "groq": ask_groq}


def consult(question, models=("deepseek", "gpt", "gemini")):
    """Ask the panel. Returns {model: answer}. A dead model returns an error string, never raises.
    DeepSeek is the STANDING consult (always first) — Mohamed's rule. gpt/gemini are the cross-check."""
    return {m: _PANEL[m](question) for m in models if m in _PANEL}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--models", default="deepseek,gpt,gemini")
    a = ap.parse_args()
    res = consult(a.question, tuple(m.strip() for m in a.models.split(",") if m.strip()))
    for m, ans in res.items():
        print(f"\n{'='*70}\n  🤖 {m.upper()}\n{'='*70}\n{ans}")


if __name__ == "__main__":
    main()
