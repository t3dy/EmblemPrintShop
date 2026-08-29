"""
Build or update the object_catalog field in each emblem record in data/emblems.json.

Reads every object's *_meta.json under assets/extracted_all/{stem}/{individual,
composites}/ directly (NOT assets/extracted_all/{stem}/summary.json -- a
re-extraction run overwrites summary.json wholesale rather than merging, so it
can describe far fewer objects than actually exist on disk; see
docs/QUALITY_AND_REVIEW_SYSTEM.md) and adds a structured object_catalog to the
matching emblem record. Each catalog entry records what was found, which motif
it maps to, the extraction file paths, and placeholder fields for appearance
(specific description in this emblem) and iconographic_meaning (what this
instance means in context).

The appearance and iconographic_meaning fields are seeded from the motifs.json
canonical descriptions and should be refined by a human reviewer or a secondary
AI annotation pass.

Reviewer corrections (prototype/review_decisions.json, written by review.html)
and geometry QC flags (prototype/geometry_qc.json, scripts/run_geometry_qc.py)
are applied automatically, keyed by object_stem -- run those first if you want
their results reflected here.

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
REVIEW_DECISIONS_JSON = ROOT / "prototype" / "review_decisions.json"
GEOMETRY_QC_JSON = ROOT / "prototype" / "geometry_qc.json"


def load_review_decisions() -> dict:
    """
    Keyed exactly like review.html/build_catalog.py: f"{stem}__{object_stem}".
    A human decision here outranks the raw detector label -- see
    docs/QUALITY_AND_REVIEW_SYSTEM.md for why this must be object_stem, not
    the (often shared) label.
    """
    if not REVIEW_DECISIONS_JSON.exists():
        return {}
    try:
        return json.loads(REVIEW_DECISIONS_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def load_geometry_qc() -> dict:
    if not GEOMETRY_QC_JSON.exists():
        return {}
    try:
        return json.loads(GEOMETRY_QC_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


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
    object_stem: str | None = None,
    correction: dict | None = None,
    qc: dict | None = None,
) -> dict:
    """
    Build a single object_catalog entry from a detection record.

    Args:
        detection: A dict read from one object's *_meta.json.
        motif_db: motif_id -> motif dict from motifs.json.
        extraction_files: Paths to the transparent_png, crop_jpg, etc.
        entry_type: "individual" or "composite".
        object_stem: unique per-object filename stem (e.g. "philosophical_egg"
            or "bridge+athanor+..._composite") -- the review-state identity key,
            per docs/QUALITY_AND_REVIEW_SYSTEM.md. Always set for objects
            discovered by globbing *_meta.json (the normal path); may be None
            only for legacy callers that still pass raw summary.json dicts.
        correction: this object's entry from review_decisions.json, if any.
        qc: this object's entry from geometry_qc.json, if any.
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
    original_label = label or " + ".join(detection.get("labels", []))

    # A human reviewer's correction (review.html) outranks the detector and
    # any motif-vocabulary lookup -- same precedence rule as build_catalog.py.
    display_label = original_label
    label_source = "detector"
    review_status = "auto"
    if correction:
        review_status = correction.get("status", "auto")
        if correction.get("corrected_label"):
            display_label = correction["corrected_label"]
            label_source = "human-corrected"

    entry = {
        "type":              entry_type,
        "object_stem":       object_stem,
        "label":             display_label,
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
        "review_status":     review_status,
        "label_source":      label_source,
        "transparent_png":   extraction_files.get("transparent_png"),
        "crop_jpg":          extraction_files.get("crop_jpg"),
        "review_overlay":    extraction_files.get("review_overlay"),
        "mask_pixel_count":  detection.get("mask_pixel_count"),
    }
    if label_source == "human-corrected":
        entry["original_label"] = original_label  # audit trail, never silently dropped
    if correction and correction.get("note"):
        entry["reviewer_note"] = correction["note"]
    if qc:
        entry["qc_flag"] = qc.get("flag")
        entry["qc_note"] = qc.get("note")

    # Drop None constituent_motif_ids for individual entries
    if entry_type == "individual":
        del entry["constituent_motif_ids"]

    return entry


def build_object_catalog_for_emblem(
    stem: str,
    emblems: list[dict],
    motif_db: dict[str, dict],
    corrections: dict,
    qc_by_key: dict,
) -> dict | None:
    """
    Build an object_catalog for one emblem by globbing every *_meta.json file
    under assets/extracted_all/{stem}/{individual,composites}/ directly.

    Deliberately does NOT read summary.json as the object list: a
    re-extraction run overwrites summary.json wholesale rather than merging,
    so for at least one emblem (emblem-13) it ends up describing far fewer
    objects than actually exist on disk. build_catalog.py already works
    around this by globbing *_meta.json; this does the same, for the same
    reason -- see docs/QUALITY_AND_REVIEW_SYSTEM.md.

    Returns the updated emblem dict, or None if no extraction directory found.
    """
    emblem_dir = EXTRACTED_ALL / stem
    if not emblem_dir.exists():
        return None

    emb = _find_emblem_by_stem(emblems, stem)
    if emb is None:
        print(f"  [warn] no emblem record found for stem '{stem}'")
        return None

    catalog: list[dict] = []
    latest_extracted_at = None
    n_individual = n_composite = 0

    for entry_type, subdir in (("individual", "individual"), ("composite", "composites")):
        d = emblem_dir / subdir
        if not d.exists():
            continue
        for meta_path in sorted(d.glob("*_meta.json")):
            try:
                detection = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            object_stem = meta_path.stem[:-5] if meta_path.stem.endswith("_meta") else meta_path.stem
            key = f"{stem}__{object_stem}"
            entry = _build_catalog_entry(
                detection, motif_db, detection, entry_type=entry_type,
                object_stem=object_stem,
                correction=corrections.get(key),
                qc=qc_by_key.get(key),
            )
            catalog.append(entry)
            if entry_type == "individual":
                n_individual += 1
            else:
                n_composite += 1
            ea = detection.get("extracted_at")
            if ea and (latest_extracted_at is None or ea > latest_extracted_at):
                latest_extracted_at = ea

    emb["object_catalog"] = catalog
    emb["object_catalog_extracted_at"] = latest_extracted_at
    emb["object_catalog_count"] = {
        "individual": n_individual,
        "composite":  n_composite,
        "total":      len(catalog),
    }

    n_corrected = sum(1 for e in catalog if e.get("label_source") == "human-corrected")
    print(f"  {stem}: {len(catalog)} catalog entries "
          f"({n_individual} individual, {n_composite} composite"
          f"{f', {n_corrected} human-corrected' if n_corrected else ''})")
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
    corrections = load_review_decisions()
    qc_by_key   = load_geometry_qc()
    if corrections:
        print(f"Loaded {len(corrections)} review decision(s) from {REVIEW_DECISIONS_JSON}")
    if qc_by_key:
        print(f"Loaded {len(qc_by_key)} geometry QC result(s) from {GEOMETRY_QC_JSON}")

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
        result = build_object_catalog_for_emblem(stem, emblems, motif_db, corrections, qc_by_key)
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
