"""
WO-012 prototype driver: does Canny edge detection improve mask refinement on
a real emblem plate, compared to the existing GroundingDINO+SAM+OpenCV-morphology
baseline?

Plate: sources/claudiens/site/images/emblems/emblem-13.jpg (Atalanta Fugiens
emblem XIII), chosen because its existing object_catalog already has a clean
"athanor" detection (matching 3dprintlab's actual athanor generator, so a
reviewed result here is directly reusable by WO-013) plus a "tree" detection
(large, likely touching architecture/landscape -> a real bridge-severing test
case) and an "hourglass" detection (small, thin-lined -> a real erosion-guard
test case). All three objects come from the same single plate, per WO-012's
"one real emblem plate" scope.

For each object this script:
  1. Reproduces the EXISTING, UNMODIFIED pipeline exactly as
     extract_all_objects.py calls it (segment_from_bbox -> remove_paper_background
     -> remove_background_bridges -> select_figure_mask) as the control.
  2. Generates a Canny edge map (plain + adaptive) of the whole plate once.
  3. Applies ONE edge-informed refinement targeted at that object's likely
     failure mode, in a way that isolates just that one refinement for a fair
     before/after (see inline notes per object).
  4. Saves transparent-PNG cutouts for baseline and refined, a labeled
     side-by-side comparison image, and IoU/pixel-count deltas.

Nothing here writes into data/emblems.json, data/visual_elements.json, or sets
any review_status / identificationStatus. Output is a proposal for a human
(Ted) to look at and judge — per WO-012's explicit instruction, this script
never marks anything reviewed or accepted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image as PILImage

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.pipeline.segmenter import segment_from_bbox
from scripts.pipeline.postprocessor import (
    remove_paper_background,
    remove_background_bridges,
    select_figure_mask,
    apply_mask_to_image,
    _fill_holes_smart,
)
from scripts.pipeline import edge_refiner as er

IMAGE_PATH = str(REPO / "sources" / "claudiens" / "site" / "images" / "emblems" / "emblem-13.jpg")
OUT_DIR = REPO / "assets" / "wo012_prototype"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# [x, y, w, h] det_bbox, straight from data/emblems.json's object_catalog for AF_13
OBJECTS = {
    "athanor":   {"bbox": [345, 558, 731, 788], "test": "boundary_snap"},
    "tree":      {"bbox": [33, 35, 474, 828],   "test": "bridge_sever"},
    "hourglass": {"bbox": [544, 628, 99, 92],   "test": "erosion_guard"},
}


def iou(a: np.ndarray, b: np.ndarray) -> float:
    a_bool, b_bool = a > 0, b > 0
    inter = np.logical_and(a_bool, b_bool).sum()
    union = np.logical_or(a_bool, b_bool).sum()
    return float(inter) / float(union) if union else 1.0


def crop_for_display(mask_or_img, bbox, pad=40, is_mask=False, base_img=None):
    x, y, w, h = bbox
    H, W = (mask_or_img.shape[:2] if is_mask else mask_or_img.shape[:2])
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(W, x + w + pad), min(H, y + h + pad)
    return mask_or_img[y0:y1, x0:x1]


def save_mask_png(mask, path):
    cv2.imwrite(str(path), mask)


def make_comparison_sheet(panels: list[tuple[str, np.ndarray]], out_path: Path):
    """panels: list of (label, BGR or single-channel uint8 image), same crop region."""
    imgs = []
    for label, im in panels:
        if im.ndim == 2:
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2BGR)
        h = 320
        scale = h / im.shape[0]
        im = cv2.resize(im, (int(im.shape[1] * scale), h))
        im = cv2.copyMakeBorder(im, 30, 4, 4, 4, cv2.BORDER_CONSTANT, value=(30, 30, 30))
        cv2.putText(im, label, (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        imgs.append(im)
    sheet = np.hstack(imgs)
    cv2.imwrite(str(out_path), sheet)


def run_baseline(image_path, bbox):
    """Exactly extract_all_objects.py's per-object call sequence. Unmodified."""
    mask = segment_from_bbox(image_path, bbox)
    mask = remove_paper_background(image_path, mask)
    mask = remove_background_bridges(mask, bridge_width_px=10)
    mask = select_figure_mask(mask, core_bbox_xywh=bbox)
    return mask


def raw_ink_map_before_erosion(image_path, mask):
    """
    Reproduce remove_paper_background's internal steps up to (but not
    including) its final erosion, so erosion_guard can be compared against
    that exact same fixed-radius erosion in isolation -- postprocessor.py
    does not expose this intermediate value directly.
    """
    img_bgr = cv2.imread(image_path)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    _, ink_map = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    dil_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    ink_dilated = cv2.dilate(ink_map, dil_kernel, iterations=2)
    refined = cv2.bitwise_and(mask, ink_dilated)
    return _fill_holes_smart(refined, max_hole_fraction=0.01)


def main():
    print(f"Loading plate: {IMAGE_PATH}")
    img = cv2.imread(IMAGE_PATH)
    if img is None:
        raise SystemExit(f"could not load {IMAGE_PATH}")
    print(f"  size: {img.shape[1]}x{img.shape[0]}")

    print("Generating edge maps (plain Canny + adaptive per-tile Canny) ...")
    edges_plain = er.canny_edges(IMAGE_PATH)
    edges_adaptive = er.adaptive_canny_edges(IMAGE_PATH)
    save_mask_png(edges_plain, OUT_DIR / "emblem-13_canny_plain.png")
    save_mask_png(edges_adaptive, OUT_DIR / "emblem-13_canny_adaptive.png")
    print(f"  plain Canny: {int((edges_plain > 0).sum())} edge px")
    print(f"  adaptive Canny: {int((edges_adaptive > 0).sum())} edge px")

    report = {
        "plate": "emblem-13.jpg (Atalanta Fugiens XIII)",
        "edge_maps": {
            "plain_canny_px": int((edges_plain > 0).sum()),
            "adaptive_canny_px": int((edges_adaptive > 0).sum()),
        },
        "objects": {},
    }

    for label, spec in OBJECTS.items():
        bbox = spec["bbox"]
        test = spec["test"]
        print(f"\n--- {label} (test: {test}) ---")

        print("  running baseline (unmodified pipeline) ...")
        raw_mask = segment_from_bbox(IMAGE_PATH, bbox)
        after_paper = remove_paper_background(IMAGE_PATH, raw_mask)
        after_bridges_baseline = remove_background_bridges(after_paper, bridge_width_px=10)
        baseline_final = select_figure_mask(after_bridges_baseline, core_bbox_xywh=bbox)
        baseline_px = int((baseline_final > 0).sum())
        print(f"  baseline final mask: {baseline_px} px")

        entry = {"baseline_mask_px": baseline_px, "test": test}

        # Use the plate-wide adaptive edge map for all refinements -- it's the
        # more defensible default given uneven scan illumination; plain Canny
        # is saved separately above for the report to also inspect.
        edges = edges_adaptive

        crop_bgr = crop_for_display(img, bbox, is_mask=False)
        crop_baseline_mask = crop_for_display(baseline_final, bbox, is_mask=True)

        if test == "boundary_snap":
            refined = er.snap_boundary_to_edges(baseline_final, edges)
            refined_px = int((refined > 0).sum())
            score = iou(baseline_final, refined)
            entry.update({"refined_mask_px": refined_px, "iou_vs_baseline": round(score, 4)})
            print(f"  boundary-snapped mask: {refined_px} px, IoU vs baseline = {score:.4f}")

            crop_refined = crop_for_display(refined, bbox, is_mask=True)
            make_comparison_sheet(
                [
                    ("source crop", crop_bgr),
                    ("baseline mask", crop_baseline_mask),
                    ("adaptive canny", crop_for_display(edges, bbox, is_mask=True)),
                    ("boundary-snapped", crop_refined),
                    ("diff (red=changed)", _diff_overlay(crop_bgr, crop_baseline_mask, crop_refined)),
                ],
                OUT_DIR / f"{label}_comparison.png",
            )

            rgba = apply_mask_to_image(IMAGE_PATH, refined)
            rgba.save(OUT_DIR / f"{label}_boundary_snapped_transparent.png")

        elif test == "bridge_sever":
            # Isolate the bridge-severing step: run BOTH baseline severing and
            # contour-informed severing on the exact same pre-severing mask
            # (after_paper), then finish with the same select_figure_mask so
            # the two are compared on equal footing all the way to a final
            # cutout, not just at the intermediate step.
            baseline_severed = remove_background_bridges(after_paper, bridge_width_px=10)
            baseline_severed_final = select_figure_mask(baseline_severed, core_bbox_xywh=bbox)

            contour_severed = er.sever_bridges_by_contour(after_paper, edges, bridge_width_px=10)
            contour_severed_final = select_figure_mask(contour_severed, core_bbox_xywh=bbox)

            b_px = int((baseline_severed_final > 0).sum())
            c_px = int((contour_severed_final > 0).sum())
            score = iou(baseline_severed_final, contour_severed_final)
            entry.update({
                "baseline_severed_px": b_px,
                "contour_severed_px": c_px,
                "iou_vs_baseline": round(score, 4),
            })
            print(f"  baseline bridge-sever: {b_px} px; contour-informed: {c_px} px; IoU = {score:.4f}")

            make_comparison_sheet(
                [
                    ("source crop", crop_bgr),
                    ("baseline (fixed-radius sever)", crop_for_display(baseline_severed_final, bbox, is_mask=True)),
                    ("adaptive canny", crop_for_display(edges, bbox, is_mask=True)),
                    ("contour-informed sever", crop_for_display(contour_severed_final, bbox, is_mask=True)),
                    ("diff (red=changed)", _diff_overlay(
                        crop_bgr,
                        crop_for_display(baseline_severed_final, bbox, is_mask=True),
                        crop_for_display(contour_severed_final, bbox, is_mask=True),
                    )),
                ],
                OUT_DIR / f"{label}_comparison.png",
            )

            rgba = apply_mask_to_image(IMAGE_PATH, contour_severed_final)
            rgba.save(OUT_DIR / f"{label}_contour_severed_transparent.png")

        elif test == "erosion_guard":
            # Isolate the erosion step: reproduce remove_paper_background's
            # internal state just before its own fixed-radius erosion, then
            # compare plain erosion (matching its default edge_erosion_px=4)
            # against erosion_guard on that exact same input.
            pre_erosion = raw_ink_map_before_erosion(IMAGE_PATH, raw_mask)
            k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (4 * 2 + 1, 4 * 2 + 1))
            plain_eroded = cv2.erode(pre_erosion, k)
            guarded = er.erosion_guard(pre_erosion, edges, erosion_px=4, protect_px=3)

            plain_final = select_figure_mask(
                remove_background_bridges(plain_eroded, bridge_width_px=10), core_bbox_xywh=bbox
            )
            guarded_final = select_figure_mask(
                remove_background_bridges(guarded, bridge_width_px=10), core_bbox_xywh=bbox
            )

            p_px = int((plain_final > 0).sum())
            g_px = int((guarded_final > 0).sum())
            score = iou(plain_final, guarded_final)
            entry.update({
                "plain_erosion_px": p_px,
                "guarded_erosion_px": g_px,
                "iou_vs_baseline": round(score, 4),
            })
            print(f"  plain erosion: {p_px} px; edge-guarded: {g_px} px; IoU = {score:.4f}")

            make_comparison_sheet(
                [
                    ("source crop", crop_bgr),
                    ("baseline (plain erosion)", crop_for_display(plain_final, bbox, is_mask=True)),
                    ("adaptive canny", crop_for_display(edges, bbox, is_mask=True)),
                    ("erosion-guarded", crop_for_display(guarded_final, bbox, is_mask=True)),
                    ("diff (red=changed)", _diff_overlay(
                        crop_bgr,
                        crop_for_display(plain_final, bbox, is_mask=True),
                        crop_for_display(guarded_final, bbox, is_mask=True),
                    )),
                ],
                OUT_DIR / f"{label}_comparison.png",
            )

            rgba = apply_mask_to_image(IMAGE_PATH, guarded_final)
            rgba.save(OUT_DIR / f"{label}_erosion_guarded_transparent.png")

        # Always also save the plain baseline cutout for this object, for
        # side-by-side reference regardless of which refinement was tested.
        rgba_baseline = apply_mask_to_image(IMAGE_PATH, baseline_final)
        rgba_baseline.save(OUT_DIR / f"{label}_baseline_transparent.png")

        report["objects"][label] = entry

    with open(OUT_DIR / "wo012_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nDone. Outputs in {OUT_DIR}")
    print(json.dumps(report, indent=2))


def _diff_overlay(crop_bgr, mask_a, mask_b):
    """Red where mask_b differs from mask_a, over the source crop, for a fast visual read."""
    a_bool = mask_a > 0
    b_bool = mask_b > 0
    diff = np.logical_xor(a_bool, b_bool)
    overlay = crop_bgr.copy()
    overlay[diff] = [0, 0, 255]  # BGR red
    return overlay


if __name__ == "__main__":
    main()
