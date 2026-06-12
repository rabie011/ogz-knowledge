#!/usr/bin/env python3
"""Minds obey the registry: the runtime law-injection exists, the registry carries
Mohamed's June-12 laws, and the corrected methodology files hold the brand-exactness rule."""
import json
from pathlib import Path
B = Path(__file__).parent.parent
src = (B / "scripts/minds.py").read_text()
assert "law_registry.json" in src and "law_lines" in src, "runtime law injection missing"
laws = {l["id"] for l in json.loads((B / "data/law_registry.json").read_text())["laws"]}
for need in ("short_captions", "no_sexual_innuendo_or_humiliation", "brand_never_invites_comparison"):
    assert need in laws, f"law {need} missing from registry"
for f in ("cd_02_metaphor_architect.md", "cd_03_authenticity_detective.md", "cd_04_heritage_decoder.md"):
    assert "MOHAMED'S CORRECTIONS" in (B / "20_cd_brains" / f).read_text(), f"{f} missing the corrections block"
print("ok: laws injected at runtime + corrections stamped in 3 methodology files")
