"""
Unit tests for overlap_analyzer — overlap matrix, group finding, composite masks.
All tests use synthetic numpy masks; no model inference required.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.pipeline.overlap_analyzer import (
    build_composite_mask,
    compute_overlap_matrix,
    find_overlap_groups,
    overlap_summary,
)


def _blank(h: int = 100, w: int = 100) -> np.ndarray:
    return np.zeros((h, w), dtype=np.uint8)


def _filled(h: int = 100, w: int = 100, x: int = 0, y: int = 0,
            bw: int | None = None, bh: int | None = None) -> np.ndarray:
    mask = _blank(h, w)
    bw = bw or w
    bh = bh or h
    mask[y:y+bh, x:x+bw] = 255
    return mask


class TestComputeOverlapMatrix:
    def test_non_overlapping_masks(self):
        a = _filled(100, 100, x=0,  y=0,  bw=40, bh=40)
        b = _filled(100, 100, x=60, y=60, bw=40, bh=40)
        mat = compute_overlap_matrix([a, b])
        assert mat[0, 1] == pytest.approx(0.0)
        assert mat[1, 0] == pytest.approx(0.0)

    def test_identical_masks_score_one(self):
        a = _filled(100, 100, x=10, y=10, bw=50, bh=50)
        mat = compute_overlap_matrix([a, a])
        assert mat[0, 1] == pytest.approx(1.0)

    def test_symmetric(self):
        a = _filled(100, 100, x=0,  y=0, bw=60, bh=60)
        b = _filled(100, 100, x=30, y=0, bw=60, bh=60)
        mat = compute_overlap_matrix([a, b])
        assert mat[0, 1] == pytest.approx(mat[1, 0])

    def test_small_box_inside_large_box(self):
        large = _filled(100, 100, x=0,  y=0, bw=80, bh=80)
        small = _filled(100, 100, x=10, y=10, bw=20, bh=20)
        mat = compute_overlap_matrix([large, small])
        # intersection = 400 (all of small), min_area = 400 → ratio = 1.0
        assert mat[0, 1] == pytest.approx(1.0)

    def test_diagonal_is_zero(self):
        a = _filled()
        mat = compute_overlap_matrix([a, a, a])
        assert mat[0, 0] == 0.0
        assert mat[1, 1] == 0.0

    def test_empty_mask_handled(self):
        a = _filled(100, 100, x=0, y=0, bw=50, bh=50)
        b = _blank()  # all zeros
        mat = compute_overlap_matrix([a, b])
        assert mat[0, 1] == pytest.approx(0.0)


class TestFindOverlapGroups:
    def test_no_overlaps_returns_empty(self):
        a = _filled(100, 100, x=0,  y=0,  bw=30, bh=30)
        b = _filled(100, 100, x=70, y=70, bw=30, bh=30)
        groups = find_overlap_groups([a, b])
        assert groups == []

    def test_two_overlapping_masks_form_group(self):
        a = _filled(100, 100, x=0,  y=0, bw=60, bh=60)
        b = _filled(100, 100, x=30, y=0, bw=60, bh=60)
        groups = find_overlap_groups([a, b])
        assert len(groups) == 1
        assert sorted(groups[0]) == [0, 1]

    def test_three_way_chain(self):
        # a overlaps b, b overlaps c → all three in one group
        a = _filled(100, 100, x=0,  y=0, bw=40, bh=100)
        b = _filled(100, 100, x=30, y=0, bw=40, bh=100)
        c = _filled(100, 100, x=60, y=0, bw=40, bh=100)
        groups = find_overlap_groups([a, b, c])
        assert len(groups) == 1
        assert sorted(groups[0]) == [0, 1, 2]

    def test_two_separate_pairs(self):
        a = _filled(200, 200, x=0,   y=0,   bw=60, bh=60)
        b = _filled(200, 200, x=30,  y=0,   bw=60, bh=60)
        c = _filled(200, 200, x=140, y=140, bw=60, bh=60)
        d = _filled(200, 200, x=170, y=140, bw=60, bh=60)
        groups = find_overlap_groups([a, b, c, d])
        assert len(groups) == 2

    def test_small_sword_inside_large_man(self):
        man   = _filled(200, 200, x=10, y=10, bw=100, bh=180)
        sword = _filled(200, 200, x=50, y=30, bw=20,  bh=120)
        groups = find_overlap_groups([man, sword], overlap_threshold=0.15)
        assert len(groups) == 1
        assert sorted(groups[0]) == [0, 1]


class TestBuildCompositeMask:
    def test_union_covers_both_regions(self):
        a = _filled(100, 100, x=0,  y=0,  bw=50, bh=50)
        b = _filled(100, 100, x=50, y=50, bw=50, bh=50)
        comp = build_composite_mask([a, b], [0, 1])
        assert comp[25, 25] == 255   # in a
        assert comp[75, 75] == 255   # in b
        assert comp[0, 99] == 0      # outside both

    def test_composite_has_same_shape(self):
        a = _filled(80, 120)
        b = _filled(80, 120, x=30, y=20, bw=40, bh=40)
        comp = build_composite_mask([a, b], [0, 1])
        assert comp.shape == (80, 120)

    def test_single_index_equals_original(self):
        a = _filled(100, 100, x=10, y=10, bw=30, bh=30)
        b = _filled(100, 100, x=60, y=60, bw=30, bh=30)
        comp = build_composite_mask([a, b], [0])
        assert np.array_equal(comp, a)


class TestOverlapSummary:
    def test_returns_labels(self):
        man   = _filled(200, 200, x=10, y=10, bw=100, bh=180)
        sword = _filled(200, 200, x=50, y=30, bw=20,  bh=120)
        dets = [
            {"label": "man",   "category": "figures"},
            {"label": "sword", "category": "objects"},
        ]
        summary = overlap_summary(dets, [man, sword], overlap_threshold=0.15)
        assert len(summary) == 1
        assert set(summary[0]["labels"]) == {"man", "sword"}
        assert summary[0]["max_overlap_score"] > 0.15
