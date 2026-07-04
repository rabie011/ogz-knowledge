#!/usr/bin/env python3
"""Generate a canonical WORKFLOW.md per mind from its AGENT.md `## Method` (append-only mirror).
Mohamed's order (2026-07-04): show each agent's step-by-step workflow. Source of truth stays the
AGENT.md Method; this writes a clean, parseable numbered file the control center reads. No delete."""
import re
from pathlib import Path

R = Path.home() / "OGZ-System"
MINDS = [
    ("CEO", "orchestrator/minds/ceo"),
    ("COO", "orchestrator/minds/coo"),
    ("CFO", "orchestrator/minds/cfo"),
    ("CCO", "02-Platform-AI/Knowledge/minds/cco"),
    ("Creative Director", "02-Platform-AI/Knowledge/minds/creative-director"),
    ("Copywriter", "02-Platform-AI/Knowledge/minds/copywriter"),
    ("Caption Writer", "02-Platform-AI/Knowledge/minds/caption-writer"),
    ("Scriptwriter", "02-Platform-AI/Knowledge/minds/scriptwriter"),
    ("Designer", "02-Platform-AI/Design/minds/designer"),
    ("Treatment / Cinematography", "02-Platform-AI/Design/minds/treatment-cinematography"),
    ("Marketing Strategist", "01-OGZ-Studios/Emails/minds/marketing-strategist"),
    ("Data / Insight Analyst", "02-Platform-AI/Knowledge/minds/data-analyst"),
]


def steps_from_method(txt: str):
    m = re.search(r"^##+\s*Method.*?$(.*?)(?=^##\s|\Z)", txt, re.S | re.M)
    if not m:
        return []
    body = re.sub(r"\s+", " ", m.group(1)).strip()
    # split on "N. " boundaries (inline or multiline)
    parts = re.split(r"(?:^|\s)(\d+)\.\s+", body)
    steps = []
    # parts = ['', '1', 'step1', '2', 'step2', ...]
    for i in range(1, len(parts) - 1, 2):
        s = parts[i + 1].strip().rstrip(".")
        if s:
            steps.append(s)
    return steps


def role_line(txt: str):
    m = re.search(r"^#\s*MIND\s*[—-]\s*[^(]*\(\*(.+?)\*\)", txt, re.M)
    return m.group(1).strip() if m else ""


written = 0
for name, rel in MINDS:
    if rel.startswith("01-OGZ-Studios"):
        print("skip (out-of-umbrella, backend reads Method live):", rel)
        continue
    ag = R / rel / "AGENT.md"
    if not ag.exists():
        print("skip (no AGENT.md):", rel)
        continue
    txt = ag.read_text(encoding="utf-8", errors="replace")
    steps = steps_from_method(txt)
    role = role_line(txt)
    if not steps:
        print("WARN no steps:", name)
        continue
    out = [f"# WORKFLOW — {name}"]
    if role:
        out.append(f"> {role}")
    out.append("> Runs locally on the brain · reads know-how + writes learnings every cycle.\n")
    out.append("## Steps")
    for i, s in enumerate(steps, 1):
        out.append(f"{i}. {s}")
    out.append("\n## Live signal")
    out.append("Active when the live pipeline / journal shows this mind's stage; otherwise idle "
               "(last output = newest dated entry in `memory.md`).\n")
    out.append("*Source: this mind's `AGENT.md` `## Method` — canonical mirror, append-only. "
               "Edit AGENT.md then regenerate; never silently rewritten.*")
    (R / rel / "WORKFLOW.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    written += 1
    print(f"✓ {name}: {len(steps)} steps → {rel}/WORKFLOW.md")

print(f"\nDONE — {written} WORKFLOW.md written")
