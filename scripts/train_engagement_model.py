#!/usr/bin/env python3
"""
train_engagement_model.py — Train ML model to predict engagement potential.

Uses 2730 observations with features:
  - content_type (one-hot)
  - sector (one-hot)
  - occasion (one-hot)
  - top 3 pattern slugs (hashed)
  - lighting, setting (one-hot)
  - caption_length_bucket
  - dialect
  - has_emoji, has_hashtag
  - visual_complexity

Output: models/engagement_model.pkl + models/engagement_features.json
"""
import json, glob, os, pickle, sys
import numpy as np
from pathlib import Path
from collections import Counter

REPO = Path(__file__).parent.parent
OBS_DIR = REPO / "11_who_to_learn_from" / "observations"
MODEL_DIR = REPO / "models"
MODEL_DIR.mkdir(exist_ok=True)


def extract_features(obs: dict) -> dict:
    cr = obs.get("content_ref", {})
    qa = obs.get("quality_assessment", {})
    vo = obs.get("voice_observations", {})
    vis = obs.get("visual_observations", {})

    caption = vo.get("caption_text", "") or ""
    patterns = [pm.get("pattern_slug", "") for pm in obs.get("pattern_matches", [])[:3]]

    return {
        "content_type": cr.get("content_type", "unknown"),
        "sector": obs.get("sector", "unknown"),
        "occasion": obs.get("occasion", "evergreen"),
        "lighting": vis.get("lighting", "unknown"),
        "setting": vis.get("setting", "unknown"),
        "dialect": vo.get("dialect_detected", "unknown"),
        "caption_length": (
            "none" if not caption else
            "short" if len(caption) < 50 else
            "medium" if len(caption) < 200 else
            "long" if len(caption) < 500 else "very_long"
        ),
        "has_emoji": bool(any(ord(c) > 0x2600 for c in caption)),
        "human_presence": bool(vis.get("human_presence")),
        "pattern_0": patterns[0] if patterns else "none",
        "pattern_1": patterns[1] if len(patterns) > 1 else "none",
        "pattern_2": patterns[2] if len(patterns) > 2 else "none",
        "engagement": qa.get("engagement_potential", "medium"),
    }


def main():
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import LabelEncoder
    from sklearn.metrics import classification_report

    print("Loading observations...")
    obs_files = sorted(glob.glob(str(OBS_DIR / "*/*.json")))
    records = []
    for f in obs_files:
        with open(f) as fh:
            records.append(extract_features(json.load(fh)))

    print(f"  {len(records)} observations loaded")

    # Encode categorical features
    cat_features = ["content_type", "sector", "occasion", "lighting", "setting",
                     "dialect", "caption_length", "pattern_0", "pattern_1", "pattern_2"]
    bool_features = ["has_emoji", "human_presence"]

    encoders = {}
    X_parts = []

    for feat in cat_features:
        values = [r[feat] for r in records]
        le = LabelEncoder()
        le.fit(list(set(values)) + ["__unknown__"])
        encoded = le.transform(values)
        X_parts.append(encoded.reshape(-1, 1))
        encoders[feat] = {"classes": le.classes_.tolist()}

    for feat in bool_features:
        vals = np.array([int(r[feat]) for r in records]).reshape(-1, 1)
        X_parts.append(vals)

    X = np.hstack(X_parts)
    y_raw = [r["engagement"] for r in records]

    # Target: binary (high vs not-high)
    y = np.array([1 if e == "high" else 0 for e in y_raw])

    print(f"  Features: {X.shape[1]} | Samples: {X.shape[0]}")
    print(f"  Class balance: high={sum(y)}/{len(y)} ({100*sum(y)//len(y)}%)")

    # Train
    print("\nTraining GradientBoosting...")
    model = GradientBoostingClassifier(
        n_estimators=200, max_depth=5, learning_rate=0.1,
        subsample=0.8, random_state=42
    )

    # Cross-validation
    scores = cross_val_score(model, X, y, cv=5, scoring="f1")
    print(f"  5-fold CV F1: {scores.mean():.3f} ± {scores.std():.3f}")

    scores_acc = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    print(f"  5-fold CV Accuracy: {scores_acc.mean():.3f} ± {scores_acc.std():.3f}")

    # Train final model on all data
    model.fit(X, y)

    # Feature importance
    feature_names = cat_features + bool_features
    importances = model.feature_importances_
    print("\nFeature importance:")
    for name, imp in sorted(zip(feature_names, importances), key=lambda x: -x[1]):
        bar = "█" * int(imp * 50)
        print(f"  {name:20} {imp:.3f} {bar}")

    # Save model
    model_path = MODEL_DIR / "engagement_model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    # Save feature config
    config = {
        "cat_features": cat_features,
        "bool_features": bool_features,
        "encoders": encoders,
        "feature_names": feature_names,
        "cv_f1": round(scores.mean(), 3),
        "cv_accuracy": round(scores_acc.mean(), 3),
        "class_balance": {"high": int(sum(y)), "not_high": int(len(y) - sum(y))},
        "trained_at": __import__("datetime").datetime.now().isoformat(),
        "n_samples": len(records),
    }
    config_path = MODEL_DIR / "engagement_features.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n✅ Model saved: {model_path}")
    print(f"✅ Config saved: {config_path}")

    # Quick test
    print("\n── Quick prediction test:")
    test_cases = [
        {"content_type": "carousel_slide", "sector": "f_and_b", "occasion": "evergreen",
         "lighting": "dramatic_moody", "setting": "studio", "dialect": "gulf",
         "caption_length": "medium", "has_emoji": True, "human_presence": False,
         "pattern_0": "product_hero", "pattern_1": "heritage_storytelling_hook", "pattern_2": "none"},
        {"content_type": "image", "sector": "beauty_personal_care", "occasion": "evergreen",
         "lighting": "natural", "setting": "retail_store", "dialect": "unknown",
         "caption_length": "long", "has_emoji": False, "human_presence": True,
         "pattern_0": "influencer_collab", "pattern_1": "none", "pattern_2": "none"},
    ]
    for tc in test_cases:
        x_parts = []
        for feat in cat_features:
            val = tc[feat]
            classes = encoders[feat]["classes"]
            idx = classes.index(val) if val in classes else classes.index("__unknown__")
            x_parts.append(idx)
        for feat in bool_features:
            x_parts.append(int(tc[feat]))
        x = np.array(x_parts).reshape(1, -1)
        prob = model.predict_proba(x)[0][1]
        pred = "HIGH" if prob > 0.5 else "LOW"
        print(f"  {tc['content_type']} + {tc['sector']} + {tc['pattern_0']}: {pred} ({prob:.0%})")


if __name__ == "__main__":
    main()
