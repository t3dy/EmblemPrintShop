"""
Unit tests for comprehensive_detector — NMS logic and category prompt structure.
No model inference is performed; GroundingDINO calls are mocked.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.pipeline.comprehensive_detector import (
    CATEGORY_PROMPTS,
    _iou,
    _nms,
)


class TestIou:
    def test_no_overlap(self):
        assert _iou([0, 0, 10, 10], [20, 20, 10, 10]) == pytest.approx(0.0)

    def test_identical_boxes(self):
        assert _iou([5, 5, 20, 20], [5, 5, 20, 20]) == pytest.approx(1.0)

    def test_partial_overlap(self):
        # Two 10x10 boxes offset by 5px share a 5x10=50px intersection
        # union = 100+100-50 = 150
        score = _iou([0, 0, 10, 10], [5, 0, 10, 10])
        assert pytest.approx(score, abs=0.01) == 50 / 150

    def test_contained_box_has_low_iou(self):
        # Small box fully inside large box: IoU = small_area / large_area
        # large 100x100, small 10x10 fully inside → intersection=100, union=9900+100=10000
        score = _iou([0, 0, 100, 100], [10, 10, 10, 10])
        assert score == pytest.approx(100 / 10000, rel=0.01)

    def test_touching_edges_no_overlap(self):
        assert _iou([0, 0, 10, 10], [10, 0, 10, 10]) == pytest.approx(0.0)


class TestNms:
    def _det(self, x, y, w, h, score, label="obj"):
        return {"bbox": [x, y, w, h], "score": score, "label": label, "category": "test"}

    def test_keeps_single_detection(self):
        dets = [self._det(0, 0, 50, 50, 0.9)]
        result = _nms(dets)
        assert len(result) == 1

    def test_deduplicates_identical_boxes(self):
        dets = [
            self._det(0, 0, 50, 50, 0.9, "lion"),
            self._det(0, 0, 50, 50, 0.7, "animal"),
        ]
        result = _nms(dets, iou_threshold=0.5)
        assert len(result) == 1
        assert result[0]["score"] == pytest.approx(0.9)

    def test_keeps_non_overlapping(self):
        dets = [
            self._det(0, 0, 50, 50, 0.9, "lion"),
            self._det(200, 200, 50, 50, 0.8, "eagle"),
        ]
        result = _nms(dets, iou_threshold=0.5)
        assert len(result) == 2

    def test_man_and_sword_not_suppressed(self):
        # Man bbox is large; sword bbox is small and largely contained within.
        # IoU ≈ sword_area / man_area = 2500 / 40000 = 0.0625 → well below 0.5
        man  = self._det(0, 0, 200, 200, 0.85, "man")
        sword = self._det(80, 60, 50, 100, 0.70, "sword")
        result = _nms([man, sword], iou_threshold=0.5)
        assert len(result) == 2

    def test_sorted_by_score_descending(self):
        dets = [
            self._det(0, 0, 50, 50, 0.6, "a"),
            self._det(100, 0, 50, 50, 0.9, "b"),
            self._det(200, 0, 50, 50, 0.75, "c"),
        ]
        result = _nms(dets)
        assert [d["score"] for d in result] == pytest.approx([0.9, 0.75, 0.6])


class TestCategoryPrompts:
    def test_all_six_categories_present(self):
        expected = {"figures", "animals", "plants", "landscape", "architecture", "objects"}
        assert set(CATEGORY_PROMPTS.keys()) == expected

    def test_prompts_are_period_separated(self):
        for cat, prompt in CATEGORY_PROMPTS.items():
            assert " . " in prompt, f"{cat} prompt lacks period separators"

    def test_prompts_not_empty(self):
        for cat, prompt in CATEGORY_PROMPTS.items():
            assert len(prompt.strip()) > 0
            terms = [t.strip() for t in prompt.split(" . ") if t.strip()]
            assert len(terms) >= 5, f"{cat} has fewer than 5 terms"
