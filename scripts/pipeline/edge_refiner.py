"""
Edge-detection experiments for mask refinement (WO-012 prototype).

Tests whether Canny edge maps can improve on the existing SAM + hand-tuned
OpenCV morphology pipeline (postprocessor.py) for engraved line art. Nothing
in this file is wired into the default extraction pipeline — every function
here is independently callable and OFF by default everywhere it could be
used. See docs/EXTRACTION_PROTOTYPE_REPORT.md (this repo) for what actually
helped on the test plate, and 3dprintlab/docs/EXTRACTION.md section C for the
architectural rationale behind each of these three refinements.

Five functions, in the order a caller would reach for them:

  canny_edges            plain cv2.Canny on the source image
  adaptive_canny_edges    per-tile, median-derived thresholds (uneven-
                          illumination scans can defeat a single global
                          threshold)
  snap_boundary_to_edges  trims soft/blobby mask overreach that isn't near a
                          drawn edge, and recovers thin bits that are near
                          both the mask and a strong edge
  sever_bridges_by_contour  alternative to postprocessor.remove_background_
                          bridges' blind fixed-radius morphological opening:
                          only severs a thin connector where a strong drawn
                          contour actually crosses it
  erosion_guard           alternative to a plain cv2.erode: restores
                          eroded-away pixels that sit near a strong edge, so
                          uniform erosion doesn't eat a beak tip or antenna
"""
from __future__ import annotations

import cv2
import numpy as np


def canny_edges(image_path: str, low: int = 50, high: int = 150) -> np.ndarray:
    """Plain Canny edge map. uint8, values 0 or 255."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.Canny(gray, low, high)


def adaptive_canny_edges(image_path: str, tile: int = 200, sigma: float = 0.33) -> np.ndarray:
    """
    Canny with per-tile, median-derived thresholds instead of one global
    pair. Early modern paper scans have uneven illumination across a plate
    (foxing, uneven lighting at scan time, vignetting); a single global
    threshold either misses faint hatching in shadowed corners or drowns in
    noise in bright ones. Each tile gets its own auto-threshold
    (the standard "auto Canny" trick: low = (1-sigma)*median,
    high = (1+sigma)*median, computed from that tile's own pixel median)
    before Canny runs on it, and the boundary between tiles is not
    smoothed, so a strong global edge does not stop at a tile seam.
    """
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    h, w = gray.shape
    out = np.zeros((h, w), dtype=np.uint8)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            y1, x1 = min(y0 + tile, h), min(x0 + tile, w)
            patch = gray[y0:y1, x0:x1]
            med = float(np.median(patch))
            lo = int(max(0, (1.0 - sigma) * med))
            hi = int(min(255, (1.0 + sigma) * med))
            if hi <= lo:
                hi = lo + 1
            out[y0:y1, x0:x1] = cv2.Canny(patch, lo, hi)
    return out


def snap_boundary_to_edges(
    mask: np.ndarray,
    edges: np.ndarray,
    band_px: int = 6,
    edge_search_px: int = 3,
) -> np.ndarray:
    """
    Refit a mask's boundary toward the nearest strong Canny edge within a
    small band, instead of trusting SAM's (often soft/dilated) contour as-is.

    Two moves, both confined to a `band_px`-wide annulus straddling the
    current boundary:
      - TRIM: mask pixels inside the band that are NOT near any edge are
        dropped — likely soft SAM overreach rather than a drawn boundary.
      - RECOVER: non-mask pixels inside the band that ARE near an edge and
        adjacent to the existing mask are added back — likely a thin drawn
        extremity (tail tip, spout) the mask undershot.

    Args:
        mask: uint8 binary mask (0/255).
        edges: uint8 edge map (0/255), same shape as mask.
        band_px: half-width of the boundary annulus to operate on.
        edge_search_px: how far from an edge pixel counts as "near an edge".

    Returns:
        Refined uint8 mask.
    """
    k_band = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band_px * 2 + 1, band_px * 2 + 1))
    dilated = cv2.dilate(mask, k_band)
    eroded = cv2.erode(mask, k_band)
    band = cv2.subtract(dilated, eroded)  # annulus straddling the boundary

    k_edge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (edge_search_px * 2 + 1, edge_search_px * 2 + 1))
    edge_near = cv2.dilate(edges, k_edge)

    refined = mask.copy()

    trim = cv2.bitwise_and(band, mask)
    trim = cv2.bitwise_and(trim, cv2.bitwise_not(edge_near))
    refined[trim > 0] = 0

    mask_near = cv2.dilate(mask, k_edge)
    recover = cv2.bitwise_and(band, cv2.bitwise_not(mask))
    recover = cv2.bitwise_and(recover, edge_near)
    recover = cv2.bitwise_and(recover, mask_near)
    refined[recover > 0] = 255

    return refined


def sever_bridges_by_contour(
    mask: np.ndarray,
    edges: np.ndarray,
    bridge_width_px: int = 10,
    edge_search_px: int = 2,
) -> np.ndarray:
    """
    Alternative to postprocessor.remove_background_bridges. That function
    erodes-then-dilates by a fixed radius everywhere, which cannot tell "a
    real gap between two figures" from "a thin drawn connection that is
    genuinely part of one figure" (a retort's neck, a dragon's tail) — it
    just cuts anything narrower than bridge_width_px.

    This version finds the same candidate thin connectors (via the same
    erode/dilate operation, so it locates identical candidates) but only
    actually severs a candidate where a strong Canny edge crosses it — i.e.
    where the engraver actually drew a boundary there, not just a
    thin-and-therefore-suspicious region.

    Args:
        mask: uint8 binary mask (0/255).
        edges: uint8 edge map (0/255), same shape as mask.
        bridge_width_px: half-width of connections to consider severing
                         (same meaning as postprocessor's parameter, so the
                         two are a fair comparison).
        edge_search_px: how far from an edge pixel counts as "crossed by"
                        the connector.

    Returns:
        Refined uint8 mask.
    """
    if int(mask.sum()) == 0:
        return mask

    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (bridge_width_px * 2 + 1, bridge_width_px * 2 + 1))
    eroded = cv2.erode(mask, k)
    restored = cv2.dilate(eroded, k)
    candidate_bridge = cv2.bitwise_and(mask, cv2.bitwise_not(restored))

    if int(candidate_bridge.sum()) == 0:
        return mask  # nothing thin enough to be a candidate bridge at all

    k_edge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (edge_search_px * 2 + 1, edge_search_px * 2 + 1))
    edge_near = cv2.dilate(edges, k_edge)

    sever_here = cv2.bitwise_and(candidate_bridge, edge_near)

    refined = mask.copy()
    refined[sever_here > 0] = 0
    return refined


def erosion_guard(
    mask: np.ndarray,
    edges: np.ndarray,
    erosion_px: int = 4,
    protect_px: int = 3,
) -> np.ndarray:
    """
    Alternative to a plain cv2.erode (as used e.g. by postprocessor.
    remove_paper_background's fixed edge_erosion_px, and implicitly by
    segmenter's fixed dilation working in the other direction). Uniform
    erosion is a blunt instrument sized for the general case, and can eat a
    genuinely thin drawn feature (a beak tip, an antenna, a tool handle) as
    readily as it cleans real fringe noise.

    This version erodes normally, then restores any pixel the erosion
    removed IF that pixel sits near a strong Canny edge — the reasoning
    being that fringe noise (paper texture, hatching artifacts) has no
    coherent edge behind it, while a genuine thin drawn feature does.

    Args:
        mask: uint8 binary mask (0/255).
        edges: uint8 edge map (0/255), same shape as mask.
        erosion_px: half-width of the erosion kernel (compare directly to
                    postprocessor's edge_erosion_px, default 4).
        protect_px: how far from an edge pixel counts as "protected".

    Returns:
        Refined (guarded) uint8 mask.
    """
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erosion_px * 2 + 1, erosion_px * 2 + 1))
    eroded = cv2.erode(mask, k)
    lost = cv2.bitwise_and(mask, cv2.bitwise_not(eroded))

    if int(lost.sum()) == 0:
        return eroded  # erosion removed nothing; guard has nothing to do

    k_edge = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (protect_px * 2 + 1, protect_px * 2 + 1))
    edge_near = cv2.dilate(edges, k_edge)

    restore = cv2.bitwise_and(lost, edge_near)

    guarded = cv2.bitwise_or(eroded, restore)
    return guarded
