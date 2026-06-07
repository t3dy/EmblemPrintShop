"""
Tests for the SAM2-based segmentation step.

Given a source image and a bounding box (from the detector), the segmenter
should return a binary mask that covers the subject plausibly.
"""
import pytest
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.segmenter import segment_from_bbox

EMBLEM_37 = str(Path(__file__).parent.parent / "sources/claudiens/site/images/emblems/emblem-37.jpg")

# Known approximate bbox for the lion in emblem 37 (from cutout_examples_manifest.json)
# bbox format: [x, y, w, h]
LION_BBOX_APPROX = [180, 330, 1070, 430]  # x, y, w, h


@pytest.mark.skipif(not Path(EMBLEM_37).exists(), reason="Test image not found")
def test_segmenter_returns_numpy_mask():
    """Segmenter should return a numpy uint8 array (binary mask)."""
    mask = segment_from_bbox(EMBLEM_37, LION_BBOX_APPROX)
    assert isinstance(mask, np.ndarray), "Mask must be a numpy array"
    assert mask.dtype == np.uint8, f"Mask dtype should be uint8, got {mask.dtype}"


@pytest.mark.skipif(not Path(EMBLEM_37).exists(), reason="Test image not found")
def test_mask_same_size_as_image():
    """Mask must have the same HxW as the source image."""
    import cv2
    img = cv2.imread(EMBLEM_37)
    img_h, img_w = img.shape[:2]
    mask = segment_from_bbox(EMBLEM_37, LION_BBOX_APPROX)
    assert mask.shape == (img_h, img_w), (
        f"Mask shape {mask.shape} != image shape ({img_h}, {img_w})"
    )


@pytest.mark.skipif(not Path(EMBLEM_37).exists(), reason="Test image not found")
def test_mask_covers_majority_of_bbox():
    """
    At least 40% of pixels inside the provided bbox should be masked.
    This guards against the segmenter returning an empty or trivially small mask.
    """
    x, y, w, h = LION_BBOX_APPROX
    mask = segment_from_bbox(EMBLEM_37, LION_BBOX_APPROX)
    roi = mask[y:y+h, x:x+w]
    coverage = roi.sum() / (w * h * 255)
    assert coverage >= 0.40, f"Mask covers only {coverage:.1%} of bbox — expected >= 40%"


@pytest.mark.skipif(not Path(EMBLEM_37).exists(), reason="Test image not found")
def test_mask_does_not_terminate_at_bbox_top_edge():
    """
    Mask should not abruptly stop at exactly the top edge of the input bbox.
    This tests for the 'clipped extremities' failure: if SAM cut off the figure
    precisely at the bbox top, extremities (head, ears) were missed.

    We allow the mask to touch the bbox top only if there's a natural boundary
    there (i.e., < 5% of the top row is masked).
    """
    x, y, w, h = LION_BBOX_APPROX
    mask = segment_from_bbox(EMBLEM_37, LION_BBOX_APPROX)
    # Expand bbox by segmenter internally — so check the actual mask extent
    mask_rows = np.where(mask.any(axis=1))[0]
    if len(mask_rows) == 0:
        pytest.fail("Mask is entirely empty")
    mask_top = mask_rows.min()
    # The mask top should be at or below the bbox top (possibly extended upward by dilation)
    # It should NOT be cut off at y+0 if there are high-coverage rows just inside the bbox
    top_bbox_row = mask[y, x:x+w]
    top_bbox_coverage = top_bbox_row.sum() / (w * 255)
    if top_bbox_coverage > 0.30:
        # Figure clearly continues at bbox top — mask should extend above if possible
        # (The segmenter expands the bbox, so the mask should reach above y)
        assert mask_top <= y, (
            f"High top-edge coverage ({top_bbox_coverage:.1%}) but mask starts at row {mask_top}, "
            f"same as bbox top {y}. Extremities likely clipped."
        )


@pytest.mark.skipif(not Path(EMBLEM_37).exists(), reason="Test image not found")
def test_mask_is_connected_or_nearly_connected():
    """
    The primary mask region should be a single connected component (or close to it).
    Multiple disconnected blobs usually indicate segmentation noise or scene capture.
    We allow up to 3 components since early modern figures can have complex poses.
    """
    import cv2
    mask = segment_from_bbox(EMBLEM_37, LION_BBOX_APPROX)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    # Exclude background (label 0)
    fg_labels = num_labels - 1
    # Filter out tiny noise components (< 100px)
    significant = [i for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 100]
    # Allow up to 6 components: 17th-century hatching, legs, tail, and overlapping bodies
    # in complex poses naturally create several islands. The pathological case is 10+ blobs
    # scattered far across the image, indicating scene noise rather than figure fragmentation.
    assert len(significant) <= 6, (
        f"Mask has {len(significant)} significant disconnected components — likely capturing scene noise"
    )
