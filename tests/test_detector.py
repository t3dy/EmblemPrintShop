"""
Tests for the GroundingDINO-based element detector.

These tests are behavioral: they assert that the detector returns plausible
detections for known images without asserting exact pixel coordinates, since
model outputs vary slightly and bbox precision is not the point here.

Run: python -m pytest tests/test_detector.py -v
"""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.detector import detect_elements

EMBLEM_37 = Path(__file__).parent.parent / "sources/claudiens/site/images/emblems/emblem-37.jpg"
EMBLEM_25 = Path(__file__).parent.parent / "sources/claudiens/site/images/emblems/emblem-25.jpg"
HP_P330 = Path(__file__).parent.parent / "sources/hypnerotomachia-polyphili/site/images/woodcuts_1499/hp1499_p330.jpg"


@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_detect_lion_in_emblem_37():
    """Detector should find at least one 'lion' region in emblem 37."""
    detections = detect_elements(str(EMBLEM_37), prompt="lion")
    assert len(detections) >= 1, "Expected at least one detection for 'lion'"
    for det in detections:
        assert "bbox" in det, "Detection must have a bbox"
        x, y, w, h = det["bbox"]
        assert w > 10 and h > 10, f"Bbox too small: {det['bbox']}"
        assert det["score"] >= 0.0, "Score must be non-negative"


@pytest.mark.skipif(not EMBLEM_25.exists(), reason="Test image not found")
def test_detect_dragon_in_emblem_25():
    """Detector should find at least one 'dragon' or 'serpent' region in emblem 25."""
    detections = detect_elements(str(EMBLEM_25), prompt="dragon serpent")
    assert len(detections) >= 1, "Expected at least one detection for 'dragon serpent'"


@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_detection_bbox_is_within_image_bounds():
    """All returned bboxes must lie within the image dimensions."""
    import cv2
    img = cv2.imread(str(EMBLEM_37))
    img_h, img_w = img.shape[:2]
    detections = detect_elements(str(EMBLEM_37), prompt="lion")
    for det in detections:
        x, y, w, h = det["bbox"]
        assert x >= 0 and y >= 0, f"Bbox starts outside image: {det['bbox']}"
        assert x + w <= img_w, f"Bbox exceeds image width: {det['bbox']} vs {img_w}"
        assert y + h <= img_h, f"Bbox exceeds image height: {det['bbox']} vs {img_h}"


@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_detection_returns_best_match_first():
    """Detections should be sorted by descending score."""
    detections = detect_elements(str(EMBLEM_37), prompt="lion")
    if len(detections) > 1:
        scores = [d["score"] for d in detections]
        assert scores == sorted(scores, reverse=True), "Detections not sorted by score"


@pytest.mark.skipif(not EMBLEM_37.exists(), reason="Test image not found")
def test_relevant_prompt_scores_higher_than_irrelevant():
    """
    'Lion' should score higher in emblem 37 than 'modern automobile'.
    This tests that the detector is semantically ranking prompts correctly,
    not just hallucinating equally on everything.
    GroundingDINO can return false positives for any text; the key property is
    that relevant prompts rank above irrelevant ones.
    """
    lion_detections = detect_elements(str(EMBLEM_37), prompt="lion", threshold=0.05)
    auto_detections = detect_elements(str(EMBLEM_37), prompt="modern automobile", threshold=0.05)

    lion_top_score = lion_detections[0]["score"] if lion_detections else 0.0
    auto_top_score = auto_detections[0]["score"] if auto_detections else 0.0

    assert lion_top_score > auto_top_score, (
        f"Expected lion ({lion_top_score:.3f}) to score higher than automobile ({auto_top_score:.3f})"
    )
