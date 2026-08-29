"""
Deterministic geometric QC for extracted cutouts.

Answers one question, purely from pixels, with no AI call and no dependency
on whether the label is right: is this cutout a SINGLE connected figure, or
does it drag in a second, disconnected (or barely-connected) blob of noise
from elsewhere on the plate?

This is a distinct failure mode from label accuracy (see
scripts/pipeline/relabel.py) -- a mask can be perfectly clean and singular
while carrying a completely wrong label (the GroundingDINO "figures" category
prompt hallucinating "angel herphrodite skeleton" onto a correctly, tightly
cut pair of fighting lions, emblem-00, is exactly this: geometry fine, label
garbage). The two checks are independent and both required before a cutout
is trustworthy.

Runs against the ALREADY-EXTRACTED transparent PNG's alpha channel -- no
mask file is stored separately by the pipeline, so the alpha channel *is*
the mask of record for QC purposes.
"""
from __future__ import annotations

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

# A secondary component below this fraction of the total mask area is
# treated as dust/antialiasing noise, not a real second subject.
DUST_FRACTION = 0.01

# If the largest component holds less than this fraction of the total mask
# area, real mass sits outside it -> flag as fragmented/noisy.
CLEAN_THRESHOLD = 0.97


def load_alpha_mask(transparent_png_path: str | Path) -> np.ndarray | None:
    """Read a transparent PNG's alpha channel as a 0/255 uint8 mask."""
    im = cv2.imread(str(transparent_png_path), cv2.IMREAD_UNCHANGED)
    if im is None or im.shape[-1] != 4:
        return None
    alpha = im[:, :, 3]
    # Binarize: alpha is often anti-aliased at edges; treat >127 as "in mask".
    return (alpha > 127).astype(np.uint8) * 255


def analyze_mask_geometry(mask: np.ndarray) -> dict:
    """
    Connected-component analysis of a binary mask.

    Returns a dict:
      component_count          significant components (>= DUST_FRACTION of total area)
      largest_component_frac   largest component's area / total mask area
      total_mask_px            total foreground pixel count
      flag                     "clean" | "fragmented" | "empty"
      note                     one-line human-readable explanation
    """
    total = int((mask > 0).sum())
    if total == 0:
        return {
            "component_count": 0, "largest_component_frac": 0.0,
            "total_mask_px": 0, "flag": "empty",
            "note": "Mask is empty -- extraction produced nothing.",
        }

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    areas = sorted((int(stats[i, cv2.CC_STAT_AREA]) for i in range(1, num_labels)), reverse=True)
    significant = [a for a in areas if a / total >= DUST_FRACTION]
    largest_frac = (significant[0] / total) if significant else 0.0

    if len(significant) <= 1 or largest_frac >= CLEAN_THRESHOLD:
        flag = "clean"
        note = (f"Single connected figure ({len(significant)} significant "
                f"component(s), largest covers {largest_frac:.0%} of the mask).")
    else:
        flag = "fragmented"
        secondary_frac = 1.0 - largest_frac
        note = (f"{len(significant)} disconnected components of meaningful size; "
                f"{secondary_frac:.0%} of the mask sits outside the largest blob -- "
                f"likely noise or a second, unrelated figure dragged in from "
                f"elsewhere on the plate.")

    return {
        "component_count": len(significant),
        "largest_component_frac": round(largest_frac, 4),
        "total_mask_px": total,
        "flag": flag,
        "note": note,
    }


def qc_object(obj: dict) -> dict | None:
    """
    Run geometry QC on one object_catalog-style dict (must have
    'transparent_png'). Returns the qc result dict, or None if the PNG is
    missing/unreadable (does not raise -- QC is best-effort over a large,
    occasionally-incomplete corpus).
    """
    png = obj.get("transparent_png")
    if not png or not Path(png).exists():
        return None
    mask = load_alpha_mask(png)
    if mask is None:
        return None
    result = analyze_mask_geometry(mask)
    result["qc_checked_at"] = datetime.now(timezone.utc).isoformat()
    return result
