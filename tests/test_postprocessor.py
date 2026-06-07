"""
Tests for the post-processing step: transparent PNG generation and background removal.

The post-processor takes a source image + binary mask and produces a transparent PNG
where non-masked pixels are fully transparent.
"""
import pytest
import numpy as np
from pathlib import Path
from PIL import Image
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.postprocessor import apply_mask_to_image, remove_paper_background

EMBLEM_37 = str(Path(__file__).parent.parent / "sources/claudiens/site/images/emblems/emblem-37.jpg")
OUTPUT_DIR = Path(__file__).parent / "output"


def _make_test_mask(img_h, img_w, x, y, w, h):
    """Create a simple rectangular mask for testing."""
    mask = np.zeros((img_h, img_w), dtype=np.uint8)
    mask[y:y+h, x:x+w] = 255
    return mask


def test_apply_mask_returns_rgba_image():
    """Output of apply_mask_to_image must be a PIL Image in RGBA mode."""
    import cv2
    img = cv2.imread(EMBLEM_37)
    h, w = img.shape[:2]
    mask = _make_test_mask(h, w, 100, 100, 200, 200)
    result = apply_mask_to_image(EMBLEM_37, mask)
    assert isinstance(result, Image.Image), "Result must be a PIL Image"
    assert result.mode == "RGBA", f"Result mode must be RGBA, got {result.mode}"


def test_masked_pixels_are_opaque():
    """Pixels inside the mask should have alpha=255 (fully opaque)."""
    import cv2
    img = cv2.imread(EMBLEM_37)
    h, w = img.shape[:2]
    mask = _make_test_mask(h, w, 100, 100, 200, 200)
    result = apply_mask_to_image(EMBLEM_37, mask)
    arr = np.array(result)
    roi_alpha = arr[100:300, 100:300, 3]
    assert roi_alpha.min() == 255, "Masked region should be fully opaque (alpha=255)"


def test_unmasked_pixels_are_transparent():
    """Pixels outside the mask should have alpha=0 (fully transparent)."""
    import cv2
    img = cv2.imread(EMBLEM_37)
    h, w = img.shape[:2]
    mask = _make_test_mask(h, w, 100, 100, 200, 200)
    result = apply_mask_to_image(EMBLEM_37, mask)
    arr = np.array(result)
    # Check top-left corner (definitely outside the 100,100 bbox)
    corner_alpha = arr[0:50, 0:50, 3]
    assert corner_alpha.max() == 0, "Unmasked region should be fully transparent (alpha=0)"


def test_transparent_png_saves_correctly(tmp_path):
    """Output PNG should be saveable and reload correctly with alpha channel."""
    import cv2
    img = cv2.imread(EMBLEM_37)
    h, w = img.shape[:2]
    mask = _make_test_mask(h, w, 100, 100, 200, 200)
    result = apply_mask_to_image(EMBLEM_37, mask)
    out_path = tmp_path / "test_output.png"
    result.save(str(out_path))
    reloaded = Image.open(str(out_path))
    assert reloaded.mode == "RGBA", "Saved PNG must preserve RGBA mode"


def test_remove_paper_background_reduces_noise():
    """
    Paper background removal should reduce the number of masked pixels by trimming
    light-colored (paper-tone) regions from the edge of the mask — not the core.

    This guards against the 'too loose' failure mode.
    """
    import cv2
    img = cv2.imread(EMBLEM_37)
    h, w = img.shape[:2]
    # Create a mask that includes some paper area (a wide region)
    raw_mask = _make_test_mask(h, w, 50, 200, 1300, 600)
    refined_mask = remove_paper_background(EMBLEM_37, raw_mask)
    raw_count = int(raw_mask.sum() / 255)
    refined_count = int(refined_mask.sum() / 255)
    # After paper removal, the refined mask should be smaller than the raw mask
    # (some background was trimmed) but should retain most of the ink-heavy core
    assert refined_count < raw_count, (
        "Paper removal did not reduce mask size — background trimming may not be working"
    )
    assert refined_count > raw_count * 0.3, (
        f"Paper removal removed too much ({refined_count}/{raw_count} pixels remain) — "
        "core figure may have been erased"
    )
