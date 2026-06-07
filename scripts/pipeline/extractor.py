"""
Top-level extraction orchestrator: detect → segment → postprocess → save.

Combines detector, segmenter, and postprocessor into a single callable
that the CLI and batch scripts use.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

from .detector import detect_elements
from .segmenter import segment_from_bbox
from .postprocessor import (
    apply_mask_to_image, remove_paper_background, build_review_overlay,
    select_figure_mask, remove_background_bridges,
)
from .metadata import get_prompt_for_image

DEFAULT_OUTPUT_DIR = str(Path(__file__).parent.parent.parent / "assets" / "extracted")


def extract_element(
    image_path: str,
    prompt: str | None = None,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    detection_threshold: float = 0.25,
    use_paper_removal: bool = True,
    save_review_overlay: bool = True,
    top_k: int = 1,
) -> dict | None:
    """
    Run the full extraction pipeline on a single image for a single prompt.

    If prompt is None, attempts to auto-derive it from source project metadata.

    Args:
        image_path: Path to emblem/woodcut image.
        prompt: Element to find, e.g. "lion". None = auto from metadata.
        output_dir: Where to write output files.
        detection_threshold: Minimum detection confidence.
        use_paper_removal: Whether to refine mask by removing paper background.
        save_review_overlay: Whether to save a side-by-side review PNG.
        top_k: How many detections to process (default 1 = best match only).

    Returns:
        Dict with extraction metadata and output paths, or None if nothing detected.
    """
    if prompt is None:
        prompt = get_prompt_for_image(image_path)
    if not prompt:
        raise ValueError(
            f"No prompt provided and no metadata found for {image_path}. "
            "Pass --prompt explicitly."
        )

    detections = detect_elements(image_path, prompt, threshold=detection_threshold)
    if not detections:
        return None

    best = detections[0]
    bbox = best["bbox"]

    # Segment
    mask = segment_from_bbox(image_path, bbox)

    # Optionally refine by removing paper background
    if use_paper_removal:
        mask = remove_paper_background(image_path, mask)

    # 1. Sever thin bridges to background scenery (mountain behind lion, etc.)
    #    Uses morphological opening to cut connections narrower than ~10px.
    mask = remove_background_bridges(mask, bridge_width_px=10)

    # 2. Select figure-relevant components from the core detection bbox
    #    (discards peripheral landscape/scene fragments not connected to subject)
    mask = select_figure_mask(mask, core_bbox_xywh=bbox)

    # Build outputs
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = _output_stem(image_path, prompt)
    transparent_png_path = str(out_dir / f"{stem}_transparent.png")
    crop_jpg_path = str(out_dir / f"{stem}_crop.jpg")
    review_path = str(out_dir / f"{stem}_review.jpg") if save_review_overlay else None

    # Save transparent PNG
    rgba_img = apply_mask_to_image(image_path, mask)
    rgba_img.save(transparent_png_path)

    # Save crop JPG (tight bbox crop)
    _save_crop(image_path, bbox, crop_jpg_path)

    # Save review overlay
    if save_review_overlay:
        review_img = build_review_overlay(image_path, mask)
        review_img.save(review_path)

    result = {
        "source_image": image_path,
        "prompt": prompt,
        "bbox": bbox,
        "score": best["score"],
        "label": best.get("label", prompt),
        "transparent_png": transparent_png_path,
        "crop_jpg": crop_jpg_path,
        "review_overlay": review_path,
        "mask_pixel_count": int((mask > 0).sum()),
        "extracted_at": datetime.utcnow().isoformat(),
    }

    # Save metadata sidecar
    meta_path = str(out_dir / f"{stem}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result


def extract_all(
    image_paths: list[str],
    prompts: list[str | None] | None = None,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    **kwargs,
) -> list[dict]:
    """
    Batch extraction: run extract_element over multiple images.
    prompts[i] corresponds to image_paths[i]; None = auto from metadata.
    """
    if prompts is None:
        prompts = [None] * len(image_paths)

    results = []
    for i, (img_path, prompt) in enumerate(zip(image_paths, prompts)):
        print(f"[{i+1}/{len(image_paths)}] {Path(img_path).name} | prompt: {prompt or 'auto'}")
        try:
            result = extract_element(img_path, prompt=prompt, output_dir=output_dir, **kwargs)
            if result:
                results.append(result)
                print(f"  -> saved: {result['transparent_png']}")
            else:
                print(f"  -> no detection")
        except Exception as exc:
            print(f"  -> ERROR: {exc}")

    return results


def _output_stem(image_path: str, prompt: str) -> str:
    """Build a filesystem-safe output filename stem."""
    src_stem = Path(image_path).stem
    safe_prompt = "_".join(prompt.lower().split()[:3])
    safe_prompt = "".join(c if c.isalnum() or c == "_" else "" for c in safe_prompt)
    return f"{src_stem}_{safe_prompt}"


def _save_crop(image_path: str, bbox_xywh: list[int], out_path: str):
    """Save a rectangular crop of the source image."""
    img = cv2.imread(image_path)
    x, y, w, h = bbox_xywh
    h_img, w_img = img.shape[:2]
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(w_img, x + w)
    y2 = min(h_img, y + h)
    crop = img[y1:y2, x1:x2]
    cv2.imwrite(out_path, crop)
