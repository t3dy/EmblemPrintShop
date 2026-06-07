"""
Tests for the two new boundary-quality fixes:
  1. _fill_holes_smart  — donut hole: large enclosed background stays transparent
  2. remove_background_bridges — mountain behind lion: thin hatching bridges severed

These address the specific failures the user reported:
  - Lion mask including mountain background (background leakage via bridges)
  - Dragon serpent mask filling the enclosed loop interior (donut hole)

Run: python -m pytest tests/test_boundary_fixes.py -v
"""
import numpy as np
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.postprocessor import _fill_holes_smart, remove_background_bridges


# ── _fill_holes_smart ─────────────────────────────────────────────────────────

def make_donut_mask(h: int = 200, w: int = 200, outer_r: int = 80, inner_r: int = 40) -> np.ndarray:
    """Circular ring — mimics a dragon coiled around itself."""
    mask = np.zeros((h, w), dtype=np.uint8)
    cy, cx = h // 2, w // 2
    for y in range(h):
        for x in range(w):
            d = ((y - cy)**2 + (x - cx)**2) ** 0.5
            if inner_r < d <= outer_r:
                mask[y, x] = 255
    return mask


def test_small_holes_are_filled():
    """Small interior patches (hatching gaps) should be filled."""
    mask = np.ones((100, 100), dtype=np.uint8) * 255
    # Punch a small 5×5 hole in the middle
    mask[47:52, 47:52] = 0
    result = _fill_holes_smart(mask, max_hole_fraction=0.01)
    assert result[49, 49] == 255, "Small interior hole should be filled"


def test_large_donut_interior_stays_transparent():
    """
    The interior of a dragon coil (large enclosed background pool) must NOT
    be filled — it is background, not figure interior.
    """
    mask = make_donut_mask(h=400, w=400, outer_r=150, inner_r=70)
    # The interior disc is 70px radius ≈ π*70² ≈ 15,400px ≈ 9.6% of 400×400
    # With max_hole_fraction=0.01 (1%), the interior should NOT be filled
    result = _fill_holes_smart(mask, max_hole_fraction=0.01)
    # Center pixel should remain 0 (transparent — genuine background)
    assert result[200, 200] == 0, (
        "Large enclosed interior (donut hole) must stay transparent — it is background"
    )


def test_medium_hole_threshold_respected():
    """Hole just above threshold is preserved; hole just below is filled."""
    h, w = 300, 300
    img_area = h * w  # 90,000

    # Build mask with a 30×30 hole = 900px = 1.0% of image
    mask_below = np.ones((h, w), dtype=np.uint8) * 255
    mask_below[130:159, 130:159] = 0  # 29×29 = 841px < 1%

    mask_above = np.ones((h, w), dtype=np.uint8) * 255
    mask_above[120:160, 120:160] = 0  # 40×40 = 1600px > 1%

    result_below = _fill_holes_smart(mask_below, max_hole_fraction=0.01)
    result_above = _fill_holes_smart(mask_above, max_hole_fraction=0.01)

    assert result_below[144, 144] == 255, "Hole below threshold should be filled"
    assert result_above[140, 140] == 0,   "Hole above threshold should stay transparent"


# ── remove_background_bridges ─────────────────────────────────────────────────

def make_bridge_mask(h: int = 200, w: int = 400) -> np.ndarray:
    """
    Two large blobs connected by a thin bridge.
    Mimics: lion body (left blob) connected to mountain (right blob)
    via a thin band of hatching.
    """
    mask = np.zeros((h, w), dtype=np.uint8)
    # Left blob (lion body) — large, 80×80
    mask[60:140, 20:100] = 255
    # Right blob (mountain background) — large, 80×80
    mask[60:140, 300:380] = 255
    # Thin bridge, 5px tall — the hatching connection
    mask[97:103, 100:300] = 255
    return mask


def test_bridge_removal_severs_thin_connection():
    """After opening, the thin bridge connecting lion to mountain is severed."""
    mask = make_bridge_mask()
    # Bridge is 6px tall; opening with 10px kernel should sever it
    result = remove_background_bridges(mask, bridge_width_px=10)

    # The bridge midpoint should now be 0 (severed)
    bridge_center = result[100, 200]
    assert bridge_center == 0, (
        f"Thin bridge at (100, 200) should be severed after opening, got {bridge_center}"
    )


def test_bridge_removal_preserves_main_body():
    """The large lion-body blob should survive bridge removal."""
    mask = make_bridge_mask()
    result = remove_background_bridges(mask, bridge_width_px=10)

    # Left blob core (lion) should survive
    lion_core = result[100, 60]
    assert lion_core == 255, (
        f"Main figure body should survive bridge removal, got {lion_core}"
    )


def test_bridge_removal_empty_mask_safe():
    """Empty mask should return unchanged without errors."""
    mask = np.zeros((100, 100), dtype=np.uint8)
    result = remove_background_bridges(mask)
    assert result.sum() == 0


def test_bridge_removal_solid_mask_safe():
    """Solid mask should not be destroyed by opening."""
    mask = np.ones((100, 100), dtype=np.uint8) * 255
    result = remove_background_bridges(mask, bridge_width_px=5)
    # Core should remain masked (may shrink at edges but center should survive)
    assert result[50, 50] == 255
