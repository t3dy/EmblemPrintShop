"""
Exhaustive object extraction: detect and segment every visual object in an emblem.

For each detected object:
  - saves a transparent PNG cutout (RGBA, background removed)
  - saves a rectangular crop JPG
  - saves a side-by-side review overlay JPG
  - saves a JSON metadata sidecar

For every cluster of overlapping objects (e.g. man + sword he is holding):
  - saves all of the above for the INDIVIDUAL objects separately
  - ALSO saves a composite transparent PNG and crop of the whole cluster together

Outputs are written to a per-emblem subdirectory:
  {output_dir}/{emblem_stem}/
      individual/
          {label}_{idx:02d}_transparent.png
          {label}_{idx:02d}_crop.jpg
          {label}_{idx:02d}_review.jpg
          {label}_{idx:02d}_meta.json
      composites/
          {label_a}+{label_b}_composite_transparent.png
          {label_a}+{label_b}_composite_crop.jpg
          {label_a}+{label_b}_composite_review.jpg
          {label_a}+{label_b}_composite_meta.json
      summary.json

Usage:
    python -m scripts.extract_all_objects path/to/emblem.jpg
    python -m scripts.extract_all_objects path/to/emblem.jpg --output-dir assets/extracted_all
    python -m scripts.extract_all_objects path/to/emblem.jpg --threshold 0.20 --categories figures animals
    python -m scripts.extract_all_objects path/to/emblem.jpg --overlap-threshold 0.10
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# Ensure scripts package is importable when run as __main__
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.pipeline.comprehensive_detector import detect_all_objects, CATEGORY_PROMPTS
from scripts.pipeline.overlap_analyzer import (
    find_overlap_groups, build_composite_mask, overlap_summary
)
from scripts.pipeline.segmenter import segment_from_bbox
from scripts.pipeline.postprocessor import (
    apply_mask_to_image, remove_paper_background,
    remove_background_bridges, select_figure_mask,
    build_review_overlay,
)

DEFAULT_OUTPUT_DIR = str(Path(__file__).parent.parent / "assets" / "extracted_all")


# ---------------------------------------------------------------------------
# Core extraction helpers
# ---------------------------------------------------------------------------

def _safe_label(label: str, max_len: int = 20) -> str:
    """Make a label filesystem-safe."""
    safe = label.lower().strip()
    safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in safe)
    return safe[:max_len].strip("_")


def _bbox_from_mask(mask: np.ndarray) -> list[int]:
    """Return the tight [x, y, w, h] bounding box of the non-zero region."""
    ys, xs = np.where(mask > 0)
    if len(xs) == 0:
        return [0, 0, mask.shape[1], mask.shape[0]]
    x1, x2 = int(xs.min()), int(xs.max())
    y1, y2 = int(ys.min()), int(ys.max())
    return [x1, y1, x2 - x1 + 1, y2 - y1 + 1]


def _save_crop(image_path: str, bbox_xywh: list[int], out_path: str) -> None:
    img = cv2.imread(image_path)
    x, y, w, h = bbox_xywh
    h_img, w_img = img.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(w_img, x + w), min(h_img, y + h)
    cv2.imwrite(out_path, img[y1:y2, x1:x2])


def _process_mask(image_path: str, bbox_xywh: list[int]) -> np.ndarray:
    """Full SAM + post-processing pipeline for a single detection bbox."""
    mask = segment_from_bbox(image_path, bbox_xywh)
    mask = remove_paper_background(image_path, mask)
    mask = remove_background_bridges(mask, bridge_width_px=10)
    mask = select_figure_mask(mask, core_bbox_xywh=bbox_xywh)
    return mask


def _save_extraction(
    image_path: str,
    mask: np.ndarray,
    out_dir: Path,
    stem: str,
    meta_extra: dict,
) -> dict:
    """Save transparent PNG, crop JPG, review overlay, and metadata JSON for one mask."""
    out_dir.mkdir(parents=True, exist_ok=True)

    transparent_path = str(out_dir / f"{stem}_transparent.png")
    crop_path        = str(out_dir / f"{stem}_crop.jpg")
    review_path      = str(out_dir / f"{stem}_review.jpg")
    meta_path        = str(out_dir / f"{stem}_meta.json")

    # Transparent PNG
    rgba = apply_mask_to_image(image_path, mask)
    rgba.save(transparent_path)

    # Crop (tight bbox of the mask, not the detection bbox)
    tight_bbox = _bbox_from_mask(mask)
    _save_crop(image_path, tight_bbox, crop_path)

    # Review overlay
    review = build_review_overlay(image_path, mask)
    review.save(review_path)

    record = {
        "source_image": image_path,
        "transparent_png": transparent_path,
        "crop_jpg": crop_path,
        "review_overlay": review_path,
        "mask_pixel_count": int((mask > 0).sum()),
        "tight_bbox": tight_bbox,
        "extracted_at": datetime.utcnow().isoformat(),
        **meta_extra,
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    return record


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def extract_all_objects(
    image_path: str,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    detection_threshold: float = 0.25,
    overlap_threshold: float = 0.15,
    categories: list[str] | None = None,
    nms_iou_threshold: float = 0.50,
) -> dict:
    """
    Run comprehensive object extraction on a single emblem image.

    Detects every visual object across six semantic categories, segments each
    with SAM, post-processes masks, saves individual cutouts, then finds
    overlapping clusters and saves composite cutouts for each cluster.

    Args:
        image_path: Path to the emblem JPG or PNG.
        output_dir: Root output directory. Results go into a subdirectory
                    named after the image stem.
        detection_threshold: GroundingDINO minimum confidence.
        overlap_threshold: Minimum containment ratio to merge two objects
                           into a composite group.
        categories: Subset of category keys to run (default: all six).
        nms_iou_threshold: IoU threshold for cross-category NMS deduplication.

    Returns:
        Summary dict with 'individual' and 'composites' lists plus counts.
    """
    image_path = str(Path(image_path).resolve())
    stem = Path(image_path).stem
    emblem_dir = Path(output_dir) / stem
    indiv_dir  = emblem_dir / "individual"
    comp_dir   = emblem_dir / "composites"

    print(f"\n=== Extracting all objects from: {Path(image_path).name} ===")

    # ------------------------------------------------------------------
    # 1. Comprehensive detection
    # ------------------------------------------------------------------
    detections = detect_all_objects(
        image_path,
        threshold=detection_threshold,
        categories=categories,
        nms_iou_threshold=nms_iou_threshold,
    )

    if not detections:
        print("No objects detected.")
        return {"source_image": image_path, "individual": [], "composites": [], "total": 0}

    print(f"\nSegmenting {len(detections)} detected objects...")

    # ------------------------------------------------------------------
    # 2. Segment each detection
    # ------------------------------------------------------------------
    masks: list[np.ndarray] = []
    valid_detections: list[dict] = []

    for idx, det in enumerate(detections):
        label = det["label"]
        print(f"  [{idx+1:02d}/{len(detections)}] {label} (score={det['score']:.2f})")
        try:
            mask = _process_mask(image_path, det["bbox"])
            if (mask > 0).sum() < 100:
                print(f"       -> mask too small, skipping")
                continue
            masks.append(mask)
            valid_detections.append(det)
        except Exception as exc:
            print(f"       -> ERROR: {exc}")

    if not masks:
        print("No usable masks produced.")
        return {"source_image": image_path, "individual": [], "composites": [], "total": 0}

    # ------------------------------------------------------------------
    # 3. Save individual extractions
    # ------------------------------------------------------------------
    print(f"\nSaving {len(masks)} individual extractions...")
    individual_results: list[dict] = []

    # Track per-label counts to generate unique filenames when the same label
    # appears multiple times (e.g. two eagles in one emblem)
    label_counters: dict[str, int] = {}

    for idx, (det, mask) in enumerate(zip(valid_detections, masks)):
        label = det["label"]
        safe  = _safe_label(label)
        label_counters[safe] = label_counters.get(safe, 0) + 1
        count = label_counters[safe]
        file_stem = f"{safe}_{count:02d}" if count > 1 else safe

        result = _save_extraction(
            image_path, mask, indiv_dir, file_stem,
            meta_extra={
                "label":    label,
                "category": det["category"],
                "score":    det["score"],
                "det_bbox": det["bbox"],
                "type":     "individual",
                "det_index": idx,
            },
        )
        individual_results.append(result)
        print(f"  -> saved: {Path(result['transparent_png']).name}")

    # ------------------------------------------------------------------
    # 4. Find overlapping groups and save composites
    # ------------------------------------------------------------------
    print(f"\nAnalysing overlaps (threshold={overlap_threshold})...")
    groups = find_overlap_groups(masks, overlap_threshold=overlap_threshold)
    ov_summary = overlap_summary(valid_detections, masks, overlap_threshold=overlap_threshold)

    composite_results: list[dict] = []

    if not groups:
        print("  No overlapping object groups found.")
    else:
        print(f"  Found {len(groups)} overlapping group(s):")
        for grp_info in ov_summary:
            label_str = " + ".join(grp_info["labels"])
            print(f"    {label_str}  (max overlap={grp_info['max_overlap_score']:.2f})")

        for group_indices in groups:
            composite_mask = build_composite_mask(masks, group_indices)

            # Build a readable name from the labels of the constituent objects
            group_labels = [valid_detections[i]["label"] for i in group_indices]
            safe_names = [_safe_label(lbl) for lbl in group_labels]
            comp_stem = "+".join(safe_names)[:60] + "_composite"

            result = _save_extraction(
                image_path, composite_mask, comp_dir, comp_stem,
                meta_extra={
                    "labels":          group_labels,
                    "categories":      [valid_detections[i]["category"] for i in group_indices],
                    "constituent_indices": group_indices,
                    "type":            "composite",
                },
            )
            composite_results.append(result)
            print(f"  -> composite saved: {Path(result['transparent_png']).name}")

    # ------------------------------------------------------------------
    # 5. Write per-emblem summary JSON
    # ------------------------------------------------------------------
    summary = {
        "source_image":        image_path,
        "emblem_stem":         stem,
        "detection_threshold": detection_threshold,
        "overlap_threshold":   overlap_threshold,
        "total_detections":    len(detections),
        "total_valid_masks":   len(masks),
        "individual_count":    len(individual_results),
        "composite_count":     len(composite_results),
        "individual":          individual_results,
        "composites":          composite_results,
        "overlap_groups":      ov_summary,
        "extracted_at":        datetime.utcnow().isoformat(),
    }
    emblem_dir.mkdir(parents=True, exist_ok=True)
    summary_path = emblem_dir / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    total = len(individual_results) + len(composite_results)
    print(f"\nDone. {len(individual_results)} individual + {len(composite_results)} composite = {total} extractions")
    print(f"Summary: {summary_path}")
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract every individual object from an emblem image, "
                    "plus composites for overlapping object clusters.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("image_path", help="Path to emblem image (JPG or PNG).")
    parser.add_argument(
        "--output-dir", default=DEFAULT_OUTPUT_DIR,
        help=f"Root output directory (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.25,
        help="GroundingDINO detection confidence threshold (default: 0.25)."
    )
    parser.add_argument(
        "--overlap-threshold", type=float, default=0.15,
        help="Containment ratio threshold for grouping overlapping objects (default: 0.15)."
    )
    parser.add_argument(
        "--categories", nargs="+", choices=list(CATEGORY_PROMPTS.keys()),
        default=None,
        help="Which category groups to run (default: all six)."
    )
    parser.add_argument(
        "--nms-iou", type=float, default=0.50,
        help="IoU threshold for cross-category NMS deduplication (default: 0.50)."
    )
    args = parser.parse_args()

    summary = extract_all_objects(
        image_path=args.image_path,
        output_dir=args.output_dir,
        detection_threshold=args.threshold,
        overlap_threshold=args.overlap_threshold,
        categories=args.categories,
        nms_iou_threshold=args.nms_iou,
    )

    print(f"\nTotal files written: {summary['individual_count']} individual, "
          f"{summary['composite_count']} composite")


if __name__ == "__main__":
    main()
