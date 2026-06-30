#!/usr/bin/env python3
"""Seed synthetic per-sector fake clients for brain + fake-platform testing.

Reads data/fake_clients/manifest.yaml and writes clients/{handle}/ with organs,
synthetic IG harvest, and (ready tier) a copied banked render — no FAL spend.

Usage:
  python3 scripts/seed_fake_sector_client.py --all
  python3 scripts/seed_fake_sector_client.py --handle fake_beauty
  python3 scripts/seed_fake_sector_client.py --all --json
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/fake_clients/manifest.yaml"
RENDERS = ROOT / "api/static/renders_v37"
SECTOR_YAML = {
    "f_and_b": ROOT / "05_sector_defaults/f_and_b.yaml",
    "beauty_personal_care": ROOT / "05_sector_defaults/beauty.yaml",
    "retail_lifestyle": ROOT / "05_sector_defaults/retail.yaml",
    "fashion": ROOT / "05_sector_defaults/retail.yaml",
    "real_estate": ROOT / "05_sector_defaults/real_estate.yaml",
    "healthcare_wellness": ROOT / "05_sector_defaults/healthcare_wellness.yaml",
}

import sys

sys.path.insert(0, str(ROOT / "scripts"))
from organ_write import write_organ
import export_prefill as ep


def _prov():
    return {
        "source": "synthetic_fixture",
        "date_added": time.strftime("%Y-%m-%d"),
        "confirmer": "system",
        "confidence": "experimental",
        "scope": "brand",
    }


def _wrap(value):
    return {"value": value, "status": "YELLOW", "provenance": _prov()}


def _slug(s: str) -> str:
    return (s or "").replace(" ", "_")


def _load_manifest() -> dict:
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    return data.get("clients") or {}


def _load_sector_yaml(sector: str) -> dict:
    path = SECTOR_YAML.get(sector)
    if not path or not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _client_root(handle: str) -> Path:
    return ROOT / "clients" / handle


def _write_marker(handle: str, spec: dict) -> None:
    p = _client_root(handle) / "profile" / ".synthetic_fixture.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    write_organ(
        p,
        {
            "handle": handle,
            "tier": spec["tier"],
            "sector": spec["sector"],
            "purpose": "fake_platform_sector_coverage",
            "do_not_aggregate": True,
            "_prov": _prov(),
        },
    )


def _write_organs_ready(handle: str, spec: dict) -> None:
    prof = _client_root(handle) / "profile"
    prof.mkdir(parents=True, exist_ok=True)
    sec = _load_sector_yaml(spec["sector"])
    dv = sec.get("default_visual") or {}
    palette = (dv.get("primary_palette") or ["#C9472B", "#E8D5B4"])[:4]
    product = spec["product"]
    chain = spec["chain"]

    write_organ(
        prof / "product_truth.json",
        {
            "_meta": {
                "organ": "product_truth",
                "handle": handle,
                "brand": spec.get("brand_en"),
                "_prov": _prov(),
            },
            "products": {
                product: {
                    "identity_dna": f"{spec['brand_ar']} — {product}",
                    "components": [product],
                    "signature": product,
                    "texture": (dv.get("texture_default") or "matte")[:80],
                    "format": "product",
                }
            },
        },
    )

    write_organ(
        prof / "visual_dna.json",
        {
            "schema_version": "brand_visual_dna_v37_v1",
            "brand_ulid": f"vdna_{handle}",
            "brand_name_normalized": spec.get("brand_en", handle),
            "sector": spec["sector"],
            "brand": {
                "region": _wrap(f"KSA — {spec.get('dialect_register', 'najdi')} register"),
                "tone_register": _wrap((sec.get("default_voice") or {}).get("register", "warm")),
                "quality_tier": _wrap("universal"),
                "price_position": _wrap("mid-market"),
                "modesty_register": _wrap("conservative"),
                "palette": {"primary": _wrap(f"{palette[0]} · neutral")},
                "color_field_palette": _wrap(", ".join(palette)),
                "style_descriptor": _wrap((dv.get("composition_default") or "clean_studio")[:60]),
                "lighting": _wrap((dv.get("lighting_default") or "soft natural")[:60]),
                "capture_character": _wrap("clean_studio"),
                "caption_style": _wrap("short_warm"),
                "sub_sector": _wrap(sec.get("sector_name_en") or spec["sector"]),
                "humor_tolerance": _wrap((sec.get("default_cultural_spec") or {}).get("humor_tolerance", "minimal")),
            },
            "_meta": {"organ": "visual_dna", "handle": handle, "_prov": _prov()},
        },
    )

    write_organ(
        prof / "cultural_overrides.json",
        {
            "_meta": {"organ": "cultural_overrides", "handle": handle, "_prov": _prov()},
            "face_visibility": "never",
            "mixed_gender_scenes": False,
            "modesty_dress": "conservative",
            "dialect_register": spec.get("dialect_register", "najdi"),
        },
    )

    write_organ(
        prof / "red_lines.json",
        {
            "_meta": {"organ": "red_lines", "handle": handle, "_prov": _prov()},
            "lines": [
                {"text": "لا كحول ولا محتوى غير لائق", "_prov": _prov()},
                {"text": "لا أسعار وهمية", "_prov": _prov()},
            ],
        },
    )

    write_organ(
        prof / "passport.json",
        {
            "_meta": {"organ": "passport", "handle": handle, "_prov": _prov()},
            "answers": {
                "brand_name_ar": spec["brand_ar"],
                "city": spec["city"],
                "founded_year": 2020,
            },
        },
    )

    write_organ(
        prof / "goals.json",
        {
            "_meta": {"organ": "goals", "handle": handle, "_prov": _prov()},
            "primary": "awareness",
            "goal_ratio": "60% awareness · 40% engagement",
            "capacity_ceiling": "4 posts/week",
        },
    )

    write_organ(
        prof / "fingerprint.json",
        {
            "_meta": {"organ": "fingerprint", "handle": handle, "_prov": _prov()},
            "l1_strategy": {
                "usp": f"تميز {spec['brand_ar']} في {spec['city']}",
                "who_speaks": "brand",
                "positioning": "local_favorite",
            },
            "l2_voice": {
                "dialect": spec.get("dialect_register", "najdi"),
                "tone": "warm",
                "register": "conversational",
            },
        },
    )

    write_organ(
        prof / "truth_pack.json",
        {
            "_meta": {"organ": "truth_pack", "handle": handle, "_prov": _prov()},
            "real_hashtags": [f"#{handle}", "#تجريبي", "#السعودية"],
            "recurring_caption_terms": [spec["brand_ar"], product],
            "brand_language": "arabic_primary",
            "channels": ["instagram"],
        },
    )

    write_organ(
        prof / "audience_mirror.json",
        {
            "_meta": {"organ": "audience_mirror", "handle": handle, "_prov": _prov()},
            "female_pct": 55,
            "male_pct": 45,
            "comments_count": 12,
            "maps_signals": {
                "formatted_address": f"{spec['city']}, Saudi Arabia",
                "stars": {"5": 80, "4": 15, "3": 5},
            },
        },
    )

    _write_synthetic_ig(handle, spec, rich=True)
    _bank_render(handle, spec)


def _write_organs_sparse(handle: str, spec: dict) -> None:
    prof = _client_root(handle) / "profile"
    prof.mkdir(parents=True, exist_ok=True)

    write_organ(
        prof / "product_truth.json",
        {
            "_meta": {"organ": "product_truth", "handle": handle, "_prov": _prov()},
            "products": {
                spec.get("product", "منتج"): {
                    "identity_dna": "",
                    "components": [],
                    "signature": "",
                    "texture": "",
                    "format": "",
                }
            },
        },
    )

    write_organ(
        prof / "visual_dna.json",
        {
            "_meta": {"organ": "visual_dna", "handle": handle, "_prov": _prov()},
            "sector": spec["sector"],
            "brand": {},
        },
    )

    write_organ(
        prof / "cultural_overrides.json",
        {
            "_meta": {"organ": "cultural_overrides", "handle": handle, "_prov": _prov()},
            "face_visibility": "never",
        },
    )

    write_organ(
        prof / "red_lines.json",
        {
            "_meta": {"organ": "red_lines", "handle": handle, "_prov": _prov()},
            "lines": [],
        },
    )

    _write_synthetic_ig(handle, spec, rich=False)


def _write_synthetic_ig(handle: str, spec: dict, rich: bool) -> None:
    day = time.strftime("%Y-%m-%d")
    raw = _client_root(handle) / "raw" / "instagram" / day
    raw.mkdir(parents=True, exist_ok=True)

    if rich:
        posts = []
        base = datetime.now(timezone.utc)
        for i in range(8):
            ts = (base - timedelta(days=i * 4)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            posts.append(
                {
                    "shortCode": f"FAKE{i:02d}",
                    "caption": f"{spec['brand_ar']} — منشور تجريبي {i}",
                    "likesCount": 20 + i,
                    "commentsCount": 2 + i % 3,
                    "displayUrl": f"https://example.com/fake/{handle}/{i}.jpg",
                    "timestamp": ts,
                }
            )
        profile = {
            "username": handle,
            "fullName": spec.get("brand_en", handle),
            "biography": f"{spec['brand_ar']} — حساب تجريبي للاختبار",
            "followersCount": 1200,
            "followsCount": 180,
            "postsCount": len(posts),
            "verified": False,
            "isBusinessAccount": True,
            "businessCategoryName": spec.get("sector", "business"),
            "externalUrl": f"https://example.com/{handle}",
            "profilePicUrl": f"https://example.com/fake/{handle}/avatar.jpg",
        }
        (raw / "posts.jsonl").write_text(
            "\n".join(json.dumps(p, ensure_ascii=False) for p in posts) + "\n",
            encoding="utf-8",
        )
    else:
        profile = {
            "username": handle,
            "fullName": spec.get("brand_en", handle),
            "followersCount": 50,
            "postsCount": 1,
        }

    (raw / "profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def _bank_render(handle: str, spec: dict) -> None:
    src_name = spec.get("render_source") or "albaik_T03.jpg"
    src = RENDERS / src_name
    if not src.exists():
        alt = next(RENDERS.glob("albaik_*.jpg"), None)
        if not alt:
            raise FileNotFoundError(f"No render template in {RENDERS}")
        src = alt
    product = spec["product"]
    chain = spec["chain"]
    dst = RENDERS / f"{handle}_{_slug(product)}_{chain}.jpg"
    RENDERS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _remove_render(handle: str, spec: dict) -> None:
    product = spec.get("product", "منتج")
    chain = spec.get("chain", "U01")
    p = RENDERS / f"{handle}_{_slug(product)}_{chain}.jpg"
    if p.exists():
        p.unlink()


def seed_one(handle: str, spec: dict) -> dict:
    _client_root(handle).mkdir(parents=True, exist_ok=True)
    _write_marker(handle, spec)
    tier = spec.get("tier", "ready")
    if tier == "ready":
        _write_organs_ready(handle, spec)
    else:
        _write_organs_sparse(handle, spec)
        _remove_render(handle, spec)

    exported = ep.export(handle)
    cov = (exported.get("_coverage") or {}).get("pct", 0)
    ready = exported.get("ready")
    return {
        "handle": handle,
        "sector": spec["sector"],
        "tier": tier,
        "coverage_pct": cov,
        "ready": ready,
        "banked_renders": (exported.get("readiness") or {}).get("banked_renders", 0),
        "product": spec.get("product"),
        "chain": spec.get("chain"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    manifest = _load_manifest()
    if args.all:
        handles = list(manifest.keys())
    elif args.handle:
        handles = [args.handle]
    else:
        ap.error("pass --all or --handle")

    results = []
    for h in handles:
        if h not in manifest:
            print(f"unknown handle: {h}", file=sys.stderr)
            return 1
        results.append(seed_one(h, manifest[h]))

    report = {
        "id": "sector-fake-clients-seed",
        "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "clients": results,
        "ready_count": sum(1 for r in results if r.get("ready")),
        "sparse_count": sum(1 for r in results if r.get("tier") == "sparse"),
    }
    out = ROOT / "data/cursor_missions/done/sector-fake-clients-seed.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.json:
        print(out)
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    ok = True
    for r in results:
        if r["tier"] == "ready" and not r["ready"]:
            ok = False
        if r["tier"] == "sparse" and r["ready"]:
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
