"""Free-first LLM router — replace with ~/agents/router.py on Mac."""
from __future__ import annotations

# TODO: copy from ~/agents/router.py when splitting repo
# Order: Groq → OpenRouter → Gemini → paid fallback


def route(prompt: str, task: str = "proposal") -> str:
    raise NotImplementedError(
        "Copy router.py from ~/agents into lib/router.py — see proposals/README.md"
    )
