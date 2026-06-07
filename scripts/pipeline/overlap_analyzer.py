"""
Overlap analysis between segmentation masks.

After individually segmenting every detected object in an emblem, this module
finds which objects physically overlap — a man holding a sword, a figure
standing on a rock, a dragon coiled around a tree. Overlapping objects are
grouped using union-find so that the extractor can save both the individual
cutouts AND a composite cutout of the whole overlapping cluster.

Overlap metric: containment ratio = intersection_pixels / min(area_a, area_b).
This catches the key case where one object is largely inside another (sword
inside man's bbox). Two identical masks score 1.0; non-overlapping masks
score 0.0. IoU alone would undercount containment of small objects inside
large ones.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np


def compute_overlap_matrix(masks: list[np.ndarray]) -> np.ndarray:
    """
    Compute pairwise containment-overlap between binary masks.

    Args:
        masks: List of uint8 (H, W) arrays with values 0 or 255.

    Returns:
        Float32 array of shape (n, n). Entry [i, j] is the containment ratio
        between masks[i] and masks[j]: intersection / min(area_i, area_j).
        Diagonal is 0.
    """
    n = len(masks)
    matrix = np.zeros((n, n), dtype=np.float32)
    areas = [int((m > 0).sum()) for m in masks]

    for i in range(n):
        if areas[i] == 0:
            continue
        for j in range(i + 1, n):
            if areas[j] == 0:
                continue
            intersection = int(((masks[i] > 0) & (masks[j] > 0)).sum())
            if intersection == 0:
                continue
            ratio = intersection / min(areas[i], areas[j])
            matrix[i, j] = ratio
            matrix[j, i] = ratio

    return matrix


def find_overlap_groups(
    masks: list[np.ndarray],
    overlap_threshold: float = 0.15,
) -> list[list[int]]:
    """
    Find clusters of overlapping objects using union-find.

    Two masks are considered overlapping when their containment ratio exceeds
    overlap_threshold (default 15%). This is deliberately generous: a sword
    inside a man's silhouette, a crown on a head, a key in a hand — all read
    as overlapping even when small relative to the enclosing figure.

    Args:
        masks: List of uint8 segmentation masks.
        overlap_threshold: Minimum containment ratio to merge two objects.

    Returns:
        List of groups. Each group is a sorted list of mask indices. Only groups
        with 2+ members are returned — singletons (objects that don't overlap
        anything) are excluded.
    """
    n = len(masks)
    matrix = compute_overlap_matrix(masks)

    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        parent[find(x)] = find(y)

    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i, j] > overlap_threshold:
                union(i, j)

    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)

    return [sorted(g) for g in groups.values() if len(g) >= 2]


def build_composite_mask(masks: list[np.ndarray], indices: list[int]) -> np.ndarray:
    """
    Build a composite mask as the pixel-wise union of the masks at the given indices.

    Args:
        masks: Full list of segmentation masks.
        indices: Which masks to union.

    Returns:
        uint8 (H, W) mask: pixel is 255 if it is foreground in ANY of the
        selected masks, 0 otherwise.
    """
    composite = np.zeros_like(masks[0])
    for i in indices:
        composite = np.maximum(composite, masks[i])
    return composite


def overlap_summary(
    detections: list[dict],
    masks: list[np.ndarray],
    overlap_threshold: float = 0.15,
) -> list[dict]:
    """
    Build a human-readable summary of which objects overlap.

    Returns:
        List of dicts:
            {
                "group_indices": [i, j, ...],
                "labels": ["man", "sword", ...],
                "categories": ["figures", "objects", ...],
                "max_overlap_score": float,
            }
    """
    groups = find_overlap_groups(masks, overlap_threshold=overlap_threshold)
    matrix = compute_overlap_matrix(masks)
    summary = []
    for group in groups:
        max_score = max(matrix[i, j] for i in group for j in group if i != j)
        summary.append({
            "group_indices": group,
            "labels": [detections[i]["label"] for i in group],
            "categories": [detections[i]["category"] for i in group],
            "max_overlap_score": float(max_score),
        })
    return summary
