"""
Post-processing: transparent PNG generation and paper background removal.

Two operations:
  1. apply_mask_to_image: composites source image with binary mask → RGBA PNG.
  2. remove_paper_background: trims paper-colored regions from mask edges.

For 'remove_paper_background': early modern prints have a characteristic light-
cream paper tone. We use Otsu thresholding to find the ink/paper boundary, then
AND this map with the SAM mask to trim regions that are pure paper (no ink).
The core figure is ink-heavy so it survives; loose scenic hatching around the
edges is more paper-heavy and gets trimmed.
"""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image as PILImage
from pathlib import Path


def apply_mask_to_image(image_path: str, mask: np.ndarray) -> PILImage.Image:
    """
    Apply a binary mask to a source image to create a transparent-background PNG.

    Args:
        image_path: Path to source image (JPG or PNG).
        mask: uint8 array of shape (H, W), values 0 or 255.

    Returns:
        PIL RGBA image: masked pixels are opaque, rest are transparent.
    """
    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Build alpha channel from mask
    alpha = mask.copy()

    # Stack into RGBA
    rgba = np.dstack([img_rgb, alpha])
    return PILImage.fromarray(rgba, mode="RGBA")


def remove_paper_background(
    image_path: str,
    mask: np.ndarray,
    ink_threshold: int | None = None,
    edge_erosion_px: int = 4,
) -> np.ndarray:
    """
    Refine a SAM mask by removing paper-background regions.

    Strategy:
      - Convert image to grayscale.
      - Find ink pixels using Otsu threshold (ink is dark, paper is light).
      - Dilate the ink map to preserve fine lines and hatching.
      - AND the ink map with the original mask so only ink-touching regions survive.
      - Erode slightly to remove single-pixel noise on edges.

    This addresses the 'too loose' failure: the SAM mask may include large swaths
    of scene background (sky, landscape hatching) that are mostly paper tone.

    Args:
        image_path: Path to source image.
        mask: uint8 array of shape (H, W), values 0 or 255.
        ink_threshold: Manual Otsu override (0-255). None = auto.
        edge_erosion_px: Final erosion to clean mask border noise.

    Returns:
        Refined uint8 mask of same shape.
    """
    img_bgr = cv2.imread(image_path)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Detect ink pixels: dark regions on light paper
    if ink_threshold is None:
        _, ink_map = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, ink_map = cv2.threshold(gray, ink_threshold, 255, cv2.THRESH_BINARY_INV)

    # Dilate ink map to pull in fine lines and hatching surrounding figures
    dil_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    ink_dilated = cv2.dilate(ink_map, dil_kernel, iterations=2)

    # Refine: keep only mask pixels that are near ink
    refined = cv2.bitwise_and(mask, ink_dilated)

    # Fill holes inside the refined mask (connected interior regions of the figure)
    # This prevents internal paper patches from becoming transparent
    flood_filled = _fill_holes(refined)

    # Light erosion to remove fringe noise on edges
    if edge_erosion_px > 0:
        erode_kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (edge_erosion_px * 2 + 1, edge_erosion_px * 2 + 1)
        )
        flood_filled = cv2.erode(flood_filled, erode_kernel, iterations=1)

    return flood_filled


def _fill_holes(mask: np.ndarray) -> np.ndarray:
    """Fill enclosed interior holes in a binary mask — size-limited version.

    Delegates to _fill_holes_smart with default threshold.
    Only fills holes smaller than 1% of image area, so large enclosed regions
    (e.g. the background pool inside a looping dragon or ouroboros coil) remain
    transparent rather than being incorrectly treated as figure interior.
    """
    return _fill_holes_smart(mask, max_hole_fraction=0.01)


def _fill_holes_smart(
    mask: np.ndarray,
    max_hole_fraction: float = 0.01,
) -> np.ndarray:
    """
    Fill enclosed interior holes in a binary mask, but only small ones.

    Problem this solves — the 'donut hole' failure:
      A dragon serpent (or ouroboros) coils around itself, enclosing a region
      of background. That region is not connected to the image border, so naive
      flood-fill from corners treats it as a 'hole' and fills it — incorrectly
      marking background sky as foreground figure.

    Fix:
      Label every background (inverse-mask) connected component. If a component
      does not touch the image border AND is smaller than max_hole_fraction of
      image area, it is a genuine small interior gap (paper showing through
      hatching, etc.) and gets filled. Large enclosed regions are left
      transparent.

    Args:
        mask: uint8 binary mask (0 or 255).
        max_hole_fraction: Holes larger than this fraction of total image area
                           are kept transparent. Default 1% — anything bigger
                           than ~25k px in a typical emblem is real background.
    """
    h, w = mask.shape
    max_hole_area = max_hole_fraction * h * w

    inv = cv2.bitwise_not(mask)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inv, connectivity=8)

    filled = mask.copy()
    for lbl in range(1, num_labels):
        area = int(stats[lbl, cv2.CC_STAT_AREA])
        lx  = int(stats[lbl, cv2.CC_STAT_LEFT])
        ly  = int(stats[lbl, cv2.CC_STAT_TOP])
        lcw = int(stats[lbl, cv2.CC_STAT_WIDTH])
        lch = int(stats[lbl, cv2.CC_STAT_HEIGHT])
        touches_border = (lx == 0 or ly == 0 or lx + lcw >= w or ly + lch >= h)
        if not touches_border and area <= max_hole_area:
            filled[labels == lbl] = 255

    return filled


def remove_background_bridges(
    mask: np.ndarray,
    bridge_width_px: int = 10,
) -> np.ndarray:
    """
    Sever thin connections between the primary figure and peripheral background.

    Problem this solves — the 'mountain behind the lion' failure:
      Dense hatching in early modern prints creates a continuous ink surface
      across both the lion body and the mountain behind it. SAM follows the
      ink density and extends its mask across a thin bridge of hatching into
      the background scenery, pulling in mountain pixels that belong to a
      different spatial region.

    Fix — morphological opening:
      1. Erode the mask by bridge_width_px. This removes thin connections
         (bridges narrower than the kernel) while shrinking the main body.
      2. Dilate back by the same amount. The main body is restored; the
         thin bridges that were severed during erosion cannot grow back
         because the eroded version has no seed pixels there.

    The net effect: large compact regions (lion body) survive, while thin
    appendages connecting them to distant background patches are severed.

    Args:
        mask: uint8 binary mask (0 or 255).
        bridge_width_px: Half-width of connections to sever. Tune upward
                         if background is still bleeding in; tune downward
                         if fine figure details (tail tips, antennae) are
                         being removed.
    """
    if int(mask.sum()) == 0:
        return mask

    k = bridge_width_px * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    eroded = cv2.erode(mask, kernel, iterations=1)
    opened = cv2.dilate(eroded, kernel, iterations=1)

    # Safety: if opening erased everything, return original
    if int(opened.sum()) == 0:
        return mask

    return opened


def select_figure_mask(
    mask: np.ndarray,
    core_bbox_xywh: list[int],
    max_coverage: float = 0.45,
    min_coverage: float = 0.003,
) -> np.ndarray:
    """
    From a SAM mask that may cover the whole scene, select only the connected
    components that plausibly belong to the target figure.

    Strategy:
      1. Find all connected components in the mask.
      2. Score each by how much it overlaps the CORE detection bbox (not the
         expanded bbox passed to SAM). Components that overlap the core bbox
         are foreground figure parts; distant landscape fragments are not.
      3. Keep components whose score is >= 15% of the best component's score.
      4. If the result still exceeds max_coverage of image area, iteratively
         drop the lowest-scoring peripheral components.

    This is the key fix for the 'too loose' failure where the whole scenic
    plate gets masked instead of just the lion/dragon.

    Args:
        mask: Binary uint8 mask from SAM+dilation (values 0 or 255).
        core_bbox_xywh: The ORIGINAL (pre-expansion) GroundingDINO bbox [x,y,w,h].
        max_coverage: Maximum fraction of total image area allowed in result mask.
        min_coverage: Minimum fraction; if result is smaller, return raw mask.

    Returns:
        Refined uint8 mask with only figure-relevant components retained.
    """
    h, w = mask.shape
    img_area = h * w
    cx, cy, cw, ch = core_bbox_xywh

    # Build a weight map: pixels in core bbox score 1.0, fading to 0.1 outside
    weight_map = np.full((h, w), 0.1, dtype=np.float32)
    weight_map[cy:cy+ch, cx:cx+cw] = 1.0

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)

    if num_labels <= 1:  # only background
        return mask

    component_scores = []
    for lbl in range(1, num_labels):
        area = stats[lbl, cv2.CC_STAT_AREA]
        if area < 50:  # skip dust
            continue
        comp_mask = (labels == lbl).astype(np.float32)
        score = float((comp_mask * weight_map).sum()) / area  # avg weight in component
        component_scores.append((lbl, score, area))

    if not component_scores:
        return mask

    component_scores.sort(key=lambda x: x[1], reverse=True)
    best_score = component_scores[0][1]
    threshold_score = best_score * 0.15

    kept = np.zeros_like(mask)
    kept_area = 0
    for lbl, score, area in component_scores:
        if score < threshold_score:
            break
        # Stop adding if we'd exceed max_coverage (add largest contributors first)
        if kept_area + area > max_coverage * img_area and kept_area > min_coverage * img_area:
            break
        kept[labels == lbl] = 255
        kept_area += area

    # If result is too small (< min_coverage), return original mask rather than nothing
    if kept_area < min_coverage * img_area:
        return mask

    return kept


def build_review_overlay(image_path: str, mask: np.ndarray) -> PILImage.Image:
    """
    Create a side-by-side review image: original | mask overlay.
    Useful for the human review queue to quickly assess segmentation quality.
    """
    img_bgr = cv2.imread(image_path)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

    # Create semi-transparent red overlay where mask is active
    overlay = img_rgb.copy()
    red = np.zeros_like(img_rgb)
    red[:, :, 0] = 255
    mask_bool = mask > 0
    overlay[mask_bool] = (overlay[mask_bool] * 0.5 + red[mask_bool] * 0.5).astype(np.uint8)

    combined = np.hstack([img_rgb, overlay])
    return PILImage.fromarray(combined)
