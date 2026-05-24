#!/usr/bin/env python3
"""
fill_opener_formula.py
Derive opener_formula from the first 1-3 words of caption_text.
Types: question | command | name_drop | number | emoji_open | statement

Adds to schema + fills all obs that have caption_text.
"""
import json
import re
from pathlib import Path

BASE        = Path(__file__).parent.parent
OBS_ROOT    = BASE / "11_who_to_learn_from" / "observations"
SCHEMA_PATH = BASE / "12_data_shapes" / "observation_v1.schema.json"
LOGS        = BASE / "logs"

OPENER_TYPES = ["question","command","name_drop","number","emoji_open","statement"]

# Arabic question words
AR_QUESTION = re.compile(r'^(هل|لماذا|ما |ماذا|كيف|متى|أين|من |ايش|وش|ليش|وين|كم |هل)', re.UNICODE)
# Arabic command verbs (common openers)
AR_COMMAND  = re.compile(r'^(جرّب|جرب|اطلب|اكتشف|شوف|حضّر|حضر|استمتع|لا تفوّت|لا تفوت|تعال|تعالى|انضم|سجّل|سجل|احصل|اضغط|اشتري|اشتر|اطبخ|جهّز|جهز)', re.UNICODE)
# Brand name drop (all-caps word or known brand)
NAME_DROP   = re.compile(r'^[A-Z]{2,}|^@')
# Number opener
NUMBER      = re.compile(r'^\d|^[٠-٩]')
# Emoji at start
EMOJI       = re.compile(r'^[\U0001F300-\U0001FFFF☀-➿]')
# EN question
EN_QUESTION = re.compile(r'^(what|when|where|who|why|how|do you|did you|have you|are you|is it|can you)', re.IGNORECASE)
# EN command
EN_COMMAND  = re.compile(r'^(try|get|order|discover|meet|introducing|shop|join|save|watch|taste|experience|grab|enjoy)', re.IGNORECASE)


def classify_opener(caption: str) -> str:
    cap = caption.strip()
    if not cap:
        return "statement"
    # Emoji first
    if EMOJI.match(cap):
        return "emoji_open"
    # Number
    if NUMBER.match(cap):
        return "number"
    # Question
    if AR_QUESTION.match(cap) or EN_QUESTION.match(cap) or cap.endswith("؟") or cap.endswith("?"):
        return "question"
    # Command
    if AR_COMMAND.match(cap) or EN_COMMAND.match(cap):
        return "command"
    # Name drop
    if NAME_DROP.match(cap):
        return "name_drop"
    return "statement"


def _ensure_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    vo_props = schema["properties"]["voice_observations"]["properties"]
    if "opener_formula" not in vo_props:
        vo_props["opener_formula"] = {
            "type": ["string","null"],
            "enum": OPENER_TYPES + [None],
            "description": "Opening pattern of caption: question/command/name_drop/number/emoji_open/statement"
        }
        SCHEMA_PATH.write_text(json.dumps(schema, ensure_ascii=False, indent=2))
        print("  Schema updated: added voice_observations.opener_formula")


def main():
    _ensure_schema()
    from collections import Counter
    updated = skipped = no_cap = 0
    dist = Counter()

    for f in OBS_ROOT.rglob("*.json"):
        d  = json.loads(f.read_text())
        vo = d.get("voice_observations", {})
        if vo.get("opener_formula") is not None:
            skipped += 1
            continue
        cap = vo.get("caption_text")
        if not cap:
            no_cap += 1
            continue
        formula = classify_opener(cap)
        vo["opener_formula"] = formula
        d["voice_observations"] = vo
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2))
        updated += 1
        dist[formula] += 1

    print(f"opener_formula filled: {updated}  |  skipped: {skipped}  |  no caption: {no_cap}")
    print("Distribution:")
    for k, v in dist.most_common():
        print(f"  {k:<15} {v}")

    LOGS.mkdir(exist_ok=True)
    (LOGS / "fill_opener_formula_report.json").write_text(
        json.dumps({"updated": updated, "skipped": skipped, "no_caption": no_cap,
                    "distribution": dict(dist)}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
