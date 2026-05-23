#!/usr/bin/env python3
"""
build_voice_positioning.py
Map each account to a 4-dimension brand voice space.
Dimensions: Formal↔Casual, Warm↔Cool, Earnest↔Playful, Heritage↔Modern-voice
Output: logs/voice_positioning_map.json
"""
import json
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).parent.parent
OBS_ROOT = BASE / "11_who_to_learn_from" / "observations"
LOGS = BASE / "logs"

# Dimension scoring helpers
FORMAL_REGISTER = {"msa", "formal", "semi_formal", "classical"}
CASUAL_REGISTER = {"colloquial", "colloquial_arabic", "colloquial_najdi",
                   "informal", "playful", "english_arabic_mixed", "spanish_colloquial"}

WARM_TONES = {"warm", "welcoming", "celebratory", "nostalgic", "appreciative",
              "heartfelt", "inviting", "friendly", "communal", "emotional"}
COOL_TONES = {"authoritative", "confident", "professional", "clinical",
              "minimalist", "aspirational", "neutral"}

EARNEST_TONES = {"earnest", "sincere", "heartfelt", "educational", "informative",
                 "documentary", "appreciative", "nostalgic"}
PLAYFUL_TONES = {"playful", "humorous", "witty", "teasing", "energetic",
                 "vibrant", "youthful", "casual"}

HERITAGE_PHRASES = ["تراث", "أصالة", "جدودنا", "موروث", "توارثنا", "من زمان",
                    "heritage", "traditional", "ancestral", "كرم", "ضيافة"]
MODERN_PHRASES = ["اكتشف", "جديد", "حديث", "عصري", "innovation", "modern",
                  "launch", "new", "contemporary", "trend"]

def score_text_for_keywords(texts, positive_kw, negative_kw):
    """Return score in [-1, 1] where +1 = all positive, -1 = all negative."""
    pos = sum(1 for t in texts for kw in positive_kw if kw.lower() in str(t).lower())
    neg = sum(1 for t in texts for kw in negative_kw if kw.lower() in str(t).lower())
    total = pos + neg
    if total == 0:
        return 0.0
    return round((pos - neg) / total, 3)

def main():
    accounts = defaultdict(lambda: {
        "sector": None,
        "obs_count": 0,
        "registers": [],
        "tones": [],
        "notable_phrases": [],
        "heritage_vs_modern_raw": []
    })

    for obs_file in sorted(OBS_ROOT.rglob("*.json")):
        if "_vision" in obs_file.name or "index" in obs_file.name.lower():
            continue
        try:
            data = json.loads(obs_file.read_text())
        except Exception:
            continue

        account = data.get("account_handle_normalized", "unknown")
        accounts[account]["sector"] = data.get("sector")
        accounts[account]["obs_count"] += 1

        vo = data.get("voice_observations", {})
        register = vo.get("register", "")
        tone = vo.get("tone", "")
        phrases = vo.get("notable_phrases", [])
        if isinstance(phrases, str):
            phrases = [phrases]

        if register:
            accounts[account]["registers"].append(str(register).lower())
        if tone:
            accounts[account]["tones"].append(str(tone).lower())
        accounts[account]["notable_phrases"].extend([str(p) for p in phrases])

        hvm = data.get("cultural_notes", {}).get("heritage_vs_modern")
        if hvm:
            accounts[account]["heritage_vs_modern_raw"].append(str(hvm).lower())

    # Position each account in voice-space
    voice_map = {}
    for account, info in accounts.items():
        registers = info["registers"]
        tones = info["tones"]
        phrases = info["notable_phrases"]
        hvm_values = info["heritage_vs_modern_raw"]

        # Dim 1: Formal (1.0) ↔ Casual (-1.0)
        formal_count = sum(1 for r in registers if any(f in r for f in FORMAL_REGISTER))
        casual_count = sum(1 for r in registers if any(c in r for c in CASUAL_REGISTER))
        total_r = formal_count + casual_count
        formal_casual = round((formal_count - casual_count) / total_r, 3) if total_r else 0.0

        # Dim 2: Warm (1.0) ↔ Cool (-1.0)
        warm_count = sum(1 for t in tones if any(w in t for w in WARM_TONES))
        cool_count = sum(1 for t in tones if any(c in t for c in COOL_TONES))
        total_t = warm_count + cool_count
        warm_cool = round((warm_count - cool_count) / total_t, 3) if total_t else 0.0

        # Dim 3: Earnest (1.0) ↔ Playful (-1.0)
        earnest_count = sum(1 for t in tones if any(e in t for e in EARNEST_TONES))
        playful_count = sum(1 for t in tones if any(p in t for p in PLAYFUL_TONES))
        total_ep = earnest_count + playful_count
        earnest_playful = round((earnest_count - playful_count) / total_ep, 3) if total_ep else 0.0

        # Dim 4: Heritage-voice (1.0) ↔ Modern-voice (-1.0)
        # Use both phrase keywords AND heritage_vs_modern field
        phrase_score = score_text_for_keywords(phrases, HERITAGE_PHRASES, MODERN_PHRASES)
        heritage_obs = sum(1 for v in hvm_values if "heritage" in v or "traditional" in v)
        modern_obs = sum(1 for v in hvm_values if "modern" in v or "contemporary" in v)
        blended_obs = sum(1 for v in hvm_values if "blend" in v)
        total_hvm = heritage_obs + modern_obs + blended_obs
        hvm_score = round((heritage_obs - modern_obs) / total_hvm, 3) if total_hvm else 0.0
        heritage_modern = round((phrase_score + hvm_score) / 2, 3)

        # Quadrant labels
        quadrant_fm = "formal" if formal_casual > 0 else "casual"
        quadrant_wc = "warm" if warm_cool > 0 else "cool"
        quadrant_ep = "earnest" if earnest_playful > 0 else "playful"
        quadrant_hm = "heritage" if heritage_modern > 0 else "modern"

        voice_map[account] = {
            "account": account,
            "sector": info["sector"],
            "obs_count": info["obs_count"],
            "dimensions": {
                "formal_casual": {
                    "score": formal_casual,
                    "label": quadrant_fm,
                    "note": "1.0 = fully formal, -1.0 = fully casual"
                },
                "warm_cool": {
                    "score": warm_cool,
                    "label": quadrant_wc,
                    "note": "1.0 = warm/welcoming, -1.0 = cool/clinical"
                },
                "earnest_playful": {
                    "score": earnest_playful,
                    "label": quadrant_ep,
                    "note": "1.0 = earnest/sincere, -1.0 = playful/witty"
                },
                "heritage_modern_voice": {
                    "score": heritage_modern,
                    "label": quadrant_hm,
                    "note": "1.0 = heritage-rooted voice, -1.0 = modern/contemporary voice"
                }
            },
            "voice_fingerprint": f"{quadrant_fm}/{quadrant_wc}/{quadrant_ep}/{quadrant_hm}",
            "dominant_registers": sorted(set(registers)),
            "dominant_tones": sorted(set(tones))
        }

    # Find overcrowded and vacant quadrants
    fingerprint_counts = defaultdict(list)
    for acc, info in voice_map.items():
        fingerprint_counts[info["voice_fingerprint"]].append(acc)

    out = {
        "schema_version": 1,
        "generated_at": "2026-05-24T00:00:00Z",
        "dimensions_explained": {
            "formal_casual": "1.0 = formal/MSA, -1.0 = casual/colloquial",
            "warm_cool": "1.0 = warm/welcoming, -1.0 = cool/clinical/authoritative",
            "earnest_playful": "1.0 = earnest/sincere, -1.0 = playful/witty",
            "heritage_modern_voice": "1.0 = heritage phrase patterns, -1.0 = modern/contemporary"
        },
        "quadrant_density": {
            fingerprint: {"accounts": accs, "count": len(accs)}
            for fingerprint, accs in sorted(fingerprint_counts.items(), key=lambda x: -len(x[1]))
        },
        "overcrowded_quadrants": [fp for fp, accs in fingerprint_counts.items() if len(accs) >= 4],
        "vacant_quadrant_examples": ["casual/cool/playful/modern", "formal/warm/earnest/modern",
                                      "formal/cool/playful/heritage"],
        "accounts": voice_map
    }

    LOGS.mkdir(exist_ok=True)
    (LOGS / "voice_positioning_map.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"Mapped {len(voice_map)} accounts to voice-space")
    print(f"\nQuadrant density (top):")
    for fp, data in sorted(fingerprint_counts.items(), key=lambda x: -len(x[1]))[:8]:
        print(f"  {fp}: {len(data['accounts']) if isinstance(data, dict) else len(data)} accounts")
    print(f"Output: logs/voice_positioning_map.json")

if __name__ == "__main__":
    main()
