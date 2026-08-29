"""
WO-012 prototype driver, part 2: one SAM automatic-mask-generation (AMG) pass
on emblem-13.jpg, for comparison against the prompt-driven (GroundingDINO ->
SAM box prompt) baseline used everywhere else in this pipeline.

AMG runs SAM unconditionally over a grid of point prompts and returns every
mask it proposes, with no text label attached to any of them -- this is the
literal "segmentation / object proposals" step the WO-012 brief asks for,
independent of whatever GroundingDINO already knows to look for. It's also
the only pass in this whole pipeline that could surface a region with no good
name in the controlled vocabulary yet.

Scoping note (disclosed, not hidden): full-plate AMG at SAM's default point
density is expensive on CPU (one forward pass per grid point). This script
runs AMG on a CROP around the athanor detection (the same bbox used
elsewhere in this prototype, padded), not the whole 1600x1418 plate, and uses
a coarser point grid than SAM's default. That keeps it CPU-tractable for a
prototype; a full-plate, full-density AMG pass is a scale decision for a
later work order if this one is judged useful, not attempted here.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image as PILImage

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

IMAGE_PATH = str(REPO / "sources" / "claudiens" / "site" / "images" / "emblems" / "emblem-13.jpg")
OUT_DIR = REPO / "assets" / "wo012_prototype"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ATHANOR_BBOX = [345, 558, 731, 788]  # x, y, w, h -- same detection as wo012_prototype.py
CROP_PAD = 120


def main():
    from transformers import pipeline

    x, y, w, h = ATHANOR_BBOX
    img = PILImage.open(IMAGE_PATH).convert("RGB")
    W, H = img.size
    x0, y0 = max(0, x - CROP_PAD), max(0, y - CROP_PAD)
    x1, y1 = min(W, x + w + CROP_PAD), min(H, y + h + CROP_PAD)
    crop = img.crop((x0, y0, x1, y1))
    crop_path = OUT_DIR / "athanor_amg_crop_source.png"
    crop.save(crop_path)
    print(f"AMG crop region: ({x0},{y0})-({x1},{y1}), {crop.size[0]}x{crop.size[1]} px")

    print("Loading SAM mask-generation pipeline (facebook/sam-vit-base) ...")
    generator = pipeline("mask-generation", model="facebook/sam-vit-base", device="cpu")

    print("Running AMG (coarse grid, points_per_side=16) -- this can take a few minutes on CPU ...")
    t0 = time.time()
    outputs = generator(str(crop_path), points_per_side=16, pred_iou_thresh=0.86)
    dt = time.time() - t0
    masks = outputs["masks"]
    scores = outputs.get("scores", [None] * len(masks))
    print(f"AMG done in {dt:.1f}s: {len(masks)} raw proposals before any filtering")

    # Drop tiny/whole-crop degenerate proposals for a legible overview.
    crop_area = crop.size[0] * crop.size[1]
    kept = []
    for m, s in zip(masks, scores):
        m = np.array(m).astype(np.uint8) * 255
        area_frac = float((m > 0).sum()) / crop_area
        if 0.003 < area_frac < 0.85:
            kept.append((m, s, area_frac))
    kept.sort(key=lambda t: t[2], reverse=True)
    print(f"{len(kept)} proposals kept after dropping specks (<0.3% area) and whole-crop blobs (>85% area)")

    # Overlay every kept proposal's boundary in a distinct color for one legible figure.
    crop_bgr = cv2.cvtColor(np.array(crop), cv2.COLOR_RGB2BGR)
    overlay = crop_bgr.copy()
    rng = np.random.default_rng(0)
    for m, s, frac in kept:
        color = tuple(int(c) for c in rng.integers(60, 255, size=3))
        contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contours, -1, color, 2)
    blended = cv2.addWeighted(crop_bgr, 0.5, overlay, 0.5, 0)
    cv2.imwrite(str(OUT_DIR / "athanor_amg_overlay.png"), blended)

    report = {
        "crop_bbox_in_plate": [x0, y0, x1, y1],
        "points_per_side": 16,
        "raw_proposal_count": len(masks),
        "kept_proposal_count": len(kept),
        "runtime_seconds": round(dt, 1),
        "top_proposals_by_area": [
            {"score": (float(s) if s is not None else None), "area_fraction": round(frac, 4)}
            for m, s, frac in kept[:10]
        ],
    }
    with open(OUT_DIR / "wo012_amg_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))
    print(f"\nOverlay saved to {OUT_DIR / 'athanor_amg_overlay.png'}")


if __name__ == "__main__":
    main()
