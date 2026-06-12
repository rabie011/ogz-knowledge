#!/usr/bin/env python3
"""SYSTEM-LAYER ASSERT: the gold wire, end to end (June 12 — the chair's law after the
wire shipped severed ×3 with green component-tests: "one fake approval through
mint→renderer would have caught all three breaks in 5 minutes").

Synthetic mohamed approval (★5) in a SANDBOX → gold_mint.mint() → assert the line is
readable through THE EXACT EXPRESSION the renderer uses (.get('gold')) AND that the
renderer source still uses that expression (contract lock). Also asserts the law-check:
a CTA-on-Eid approval must NOT mint (it stages a ruling instead). Exit 1 on any break.
Runs inside make_sure every cycle.
"""
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent.parent
SB = Path(tempfile.mkdtemp(prefix="ogz_goldwire_"))
os.environ["OGZ_BASE"] = str(SB)
sys.path.insert(0, str(REPO / "scripts"))


def main():
    # sandbox: one client + one approved card + the answer row
    (SB / "clients/testbrand/profile").mkdir(parents=True)
    (SB / "data").mkdir()
    shutil.copy(REPO / "data/producer_map.json", SB / "data/producer_map.json")
    (SB / "data/decision_queue.json").write_text(json.dumps({"items": [
        {"id": "g1", "handle": "testbrand", "caption": "سطر ذهبي للتجربة", "occasion": "evergreen",
         "made_by": "mind:firaasa", "status": "answered"},
        {"id": "g2", "handle": "testbrand", "caption": "عيد مبارك! اطلبوا الآن من التطبيق",
         "occasion": "eid_al_adha", "made_by": "mind:firaasa", "status": "answered"}]}))
    ts = datetime.now().isoformat(timespec="seconds")
    rows = [
        {"ts": ts, "judge": "mohamed", "auth": "key", "item_id": "g1", "answer": "approved",
         "rating": 5, "artifact_id": "card:g1", "source": "team_portal"},
        {"ts": ts, "judge": "mohamed", "auth": "key", "item_id": "g2", "answer": "approved",
         "rating": 5, "artifact_id": "card:g2", "source": "team_portal"},
    ]
    (SB / "data/mohamed_answers.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")

    import gold_mint
    minted = gold_mint.mint()

    # 1. the clean approval minted
    assert len(minted) == 1 and minted[0]["handle"] == "testbrand", f"mint count wrong: {minted}"
    gf = SB / "clients/testbrand/profile/gold.json"
    # 2. readable through THE RENDERER'S OWN expression
    gold_entries = json.loads(gf.read_text()).get("gold", [])
    assert any(e.get("caption") == "سطر ذهبي للتجربة" for e in gold_entries), \
        "minted line NOT visible through .get('gold') — the renderer would never see it"
    # 3. contract lock: the renderer still reads .get("gold")
    rsrc = (REPO / "scripts/render_client_slot.py").read_text()
    assert '.get("gold"' in rsrc, "renderer no longer reads the 'gold' key — wire severed again"
    # 4. the law-check held: the Eid CTA approval did NOT mint; a ruling card was staged
    q2 = json.loads((SB / "data/decision_queue.json").read_text())
    assert not any(e.get("caption", "").startswith("عيد مبارك") for e in gold_entries), \
        "law-violating caption minted into gold"
    assert any(i["id"] == "ruling_g2" for i in q2["items"]), "ruling card not staged on conflict"
    print("🟢 GOLD WIRE: end-to-end assert PASS (mint→renderer-expression + law-check + ruling)")


if __name__ == "__main__":
    try:
        main()
    finally:
        shutil.rmtree(SB, ignore_errors=True)
