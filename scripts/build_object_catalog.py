"""
Build or update the object_catalog field in each emblem record in data/emblems.json.

Reads comprehensive extraction results from assets/extracted_all/{stem}/summary.json
and adds a structured object_catalog to the matching emblem record. Each catalog entry
records what was found, which motif it maps to, the extraction file paths, and
placeholder fields for appearance (specific description in this emblem) and
iconographic_meaning (what this instance means in context).

The appearance and iconographic_meaning fields are seeded from the motifs.json
canonical descriptions and should be refined by a human reviewer or a secondary
AI annotation pass.

Usage:
    python -m scripts.build_object_catalog               # process all emblems
    python -m scripts.build_object_catalog --stem emblem-37
    python -m scripts.build_object_catalog --dry-run     # print without writing
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from scripts.pipeline.metadata import TERM_TO_MOTIF_ID

EMBLEMS_JSON     = ROOT / "data" / "emblems.json"
MOTIFS_JSON      = ROOT / "data" / "motifs.json"
EXTRACTED_ALL    = ROOT / "assets" / "extracted_all"
VISUAL_ELEM_JSON = ROOT / "data" / "visual_elements.json"


def _load_json(path: Path) -> list | dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: list | dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _motif_lookup(motifs: list[dict]) -> dict[str, dict]:
    return {m["id"]: m for m in motifs}


def _find_emblem_by_stem(emblems: list[dict], stem: str) -> dict | None:
    """Match an emblem record to an image file stem like 'emblem-37'."""
    for emb in emblems:
        img = emb.get("image_path", "")
        if Path(img).stem == stem or stem in img:
            return emb
    return None


def _build_catalog_entry(
    detection: dict,
    motif_db: dict[str, dict],
    extraction_files: dict,
    entry_type: str = "individual",
) -> dict:
    """
    Build a single object_catalog entry from a detection record.

    Args:
        detection: A dict from summary.json (individual or composite).
        motif_db: motif_id -> motif dict from motifs.json.
        extraction_files: Paths to the transparent_png, crop_jpg, etc.
        entry_type: "individual" or "composite".
    """
    # Resolve the detected label to a canonical motif id
    label = detection.get("label", "")
    motif_id = TERM_TO_MOTIF_ID.get(label.lower())

    # For composites, label field is absent; use labels list
    if not motif_id and entry_type == "composite":
        labels = detection.get("labels", [])
        motif_ids = list({TERM_TO_MOTIF_ID.get(l.lower()) for l in labels if l.lower() in TERM_TO_MOTIF_ID})
        motif_id = None  # composite; constituent motif ids listed separately
    else:
        motif_ids = [motif_id] if motif_id else []

    motif = motif_db.get(motif_id) if motif_id else None

    entry = {
        "type":              entry_type,
        "label":             label or " + ".join(detection.get("labels", [])),
        "motif_id":          motif_id,
        "constituent_motif_ids": motif_ids if entry_type == "composite" else None,
        "category":          detection.get("category") or (
                                 "/".join(detection.get("categories", [])) if entry_type == "composite" else None
                             ),
        "detection_score":   detection.get("score"),
        "detection_bbox":    detection.get("det_bbox") or detection.get("tight_bbox"),
        # appearance: placeholder — to be refined with specific description of how
        # this object looks in this particular emblem plate
        "appearance":        motif["appearance"] if motif else None,
        # iconographic_meaning: seeded from canonical motif description, to be
        # refined with emblem-specific interpretation
        "iconographic_meaning": motif["description"] if motif else None,
        "alchemical_valence":motif["alchemical_valence"] if motif else [],
        "review_status":     "auto",
        "transparent_png":   extraction_files.get("transparent_png"),
        "crop_jpg":          extraction_files.get("crop_jpg"),
        "review_overlay":    extraction_files.get("review_overlay"),
        "mask_pixel_count":  detection.get("mask_pixel_count"),
    }

    # Drop None constituent_motif_ids for individual entries
    if entry_type == "individual":
        del entry["constituent_motif_ids"]

    return entry


def build_object_catalog_for_emblem(
    stem: str,
    emblems: list[dict],
    motif_db: dict[str, dict],
) -> dict | None:
    """
    Read assets/extracted_all/{stem}/summary.json and build an object_catalog.

    Returns the updated emblem dict, or None if no extraction summary found.
    """
    summary_path = EXTRACTED_ALL / stem / "summary.json"
    if not summary_path.exists():
        return None

    with open(summary_path, encoding="utf-8") as f:
        summary = json.load(f)

    emb = _find_emblem_by_stem(emblems, stem)
    if emb is None:
        print(f"  [warn] no emblem record found for stem '{stem}'")
        return None

    catalog: list[dict] = []

    for ind in summary.get("individual", []):
        entry = _build_catalog_entry(ind, motif_db, ind, entry_type="individual")
        catalog.append(entry)

    for comp in summary.get("composites", []):
        entry = _build_catalog_entry(comp, motif_db, comp, entry_type="composite")
        catalog.append(entry)

    emb["object_catalog"] = catalog
    emb["object_catalog_extracted_at"] = summary.get("extracted_at")
    emb["object_catalog_count"] = {
        "individual": len(summary.get("individual", [])),
        "composite":  len(summary.get("composites", [])),
        "total":      len(catalog),
    }

    print(f"  {stem}: {len(catalog)} catalog entries "
          f"({emb['object_catalog_count']['individual']} individual, "
          f"{emb['object_catalog_count']['composite']} composite)")
    return emb


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build object_catalog fields in data/emblems.json from extraction results."
    )
    parser.add_argument(
        "--stem", default=None,
        help="Process only this emblem stem (e.g. 'emblem-37'). Default: all.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be written without writing anything.",
    )
    args = parser.parse_args()

    emblems  = _load_json(EMBLEMS_JSON)
    motifs   = _load_json(MOTIFS_JSON)
    motif_db = _motif_lookup(motifs)

    if not EXTRACTED_ALL.exists():
        print(f"No extracted_all directory at {EXTRACTED_ALL}. "
              "Run extract_all_objects.py first.")
        sys.exit(1)

    stems = (
        [args.stem] if args.stem
        else [d.name for d in sorted(EXTRACTED_ALL.iterdir()) if d.is_dir()]
    )

    updated = 0
    for stem in stems:
        result = build_object_catalog_for_emblem(stem, emblems, motif_db)
        if result is not None:
            updated += 1

    print(f"\nUpdated {updated}/{len(stems)} emblem records.")

    if args.dry_run:
        print("Dry run — nothing written.")
        return

    _save_json(EMBLEMS_JSON, emblems)
    print(f"Saved -> {EMBLEMS_JSON}")

    # Also update visual_elements.json: append new individual extractions
    # that don't yet have an entry
    visual_elems = _load_json(VISUAL_ELEM_JSON) if VISUAL_ELEM_JSON.exists() else []
    existing_pngs = {e.get("transparent_png") for e in visual_elems}

    new_entries = 0
    for emb in emblems:
        for entry in emb.get("object_catalog", []):
            png = entry.get("transparent_png")
            if png and png not in existing_pngs:
                ve = {
                    "id":              _make_ve_id(emb, entry),
                    "source_project":  "extracted_all",
                    "work_id":         emb.get("work_id"),
                    "emblem_id":       emb.get("id"),
                    "label":           entry.get("label"),
                    "motif_id":        entry.get("motif_id"),
                    "category":        entry.get("category"),
                    "type":            entry.get("type"),
                    "motif_candidates":[entry["motif_id"]] if entry.get("motif_id") else [],
                    "image_path":      emb.get("image_path"),
                    "transparent_png": png,
                    "crop_path":       entry.get("crop_jpg"),
                    "bbox":            entry.get("detection_bbox"),
                    "appearance":      entry.get("appearance"),
                    "iconographic_meaning": entry.get("iconographic_meaning"),
                    "alchemical_valence":   entry.get("alchemical_valence"),
                    "confidence":      _score_to_confidence(entry.get("detection_score")),
                    "detection_score": entry.get("detection_score"),
                    "method":          "comprehensive_extraction_v2",
                    "review_status":   "auto",
                    "provenance_url":  emb.get("provenance_url"),
                    "rights_note":     None,
                }
                visual_elems.append(ve)
                existing_pngs.add(png)
                new_entries += 1

    if new_entries:
        _save_json(VISUAL_ELEM_JSON, visual_elems)
        print(f"Added {new_entries} new entries -> {VISUAL_ELEM_JSON}")


def _make_ve_id(emb: dict, entry: dict) -> str:
    """Generate a unique visual_element id."""
    emb_id  = emb.get("id", "unknown").lower().replace(" ", "_")
    label   = entry.get("label", "unknown").lower()
    safe    = "".join(c if c.isalnum() or c == "_" else "_" for c in label)
    etype   = "comp" if entry.get("type") == "composite" else "ind"
    return f"{emb_id}_{safe}_{etype}"


def _score_to_confidence(score: float | None) -> str:
    if score is None:
        return "low"
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


if __name__ == "__main__":
    main()
