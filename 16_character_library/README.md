# 16_character_library/

Visual content reference library for character / wardrobe / architecture / props / gestures / rituals.

**Status:** Stub structure for v1.0.0. Actual reference content lives in object storage with LFS pointers; this folder holds the organizational manifest.

## Subfolders

| Folder | Contents |
|---|---|
| `faces/` | Reference face crops by region (Najdi / Hejazi / Eastern / Southern) and age bracket |
| `wardrobe/` | Reference thobe / abaya / accessory / fabric crops by sector × region |
| `architecture/` | Reference architectural elements (Najdi mud-brick arches, Hejazi rawasheen, modern Riyadh) |
| `props/` | Reference props (dallah, fenjan, mabkhara, sadu, modern tech) |
| `gestures/` | Reference gesture stills (right-hand-only serving, hand-on-heart, etc.) |
| `rituals/` | Reference ritual scene stills (iftar moment, Eid greeting, prayer-on-camera-pause) |

## Each subfolder contains

- `MANIFEST.md` — what goes in this folder
- `.gitkeep` — preserves folder in git when empty

## What goes in vs object storage

- **In git** (this repo): manifest + .gitkeep + small reference thumbnails (<100KB each)
- **In object storage**: full-resolution reference images; URIs tracked in `frame_v1.schema.json` records
