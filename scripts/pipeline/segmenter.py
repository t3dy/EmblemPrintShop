"""
Segmenter using SAM 2 via HuggingFace transformers.

Takes a source image and a bounding box hint and returns a binary mask
at the same resolution as the source image.

Key design decisions to fix the 'clipped extremities' failure:
  1. The input bbox is expanded by BBOX_EXPAND_RATIO before being passed to SAM.
     This gives the model room to include tails, legs, ears that extend past
     the detection boundary.
  2. After SAM inference, the mask is dilated by DILATION_PX to catch stray
     edge pixels on limbs and fine details (hatched lines that form a tail tip).
  3. We request SAM's top N mask proposals and take the one with the best IOU
     prediction, since SAM 2 returns multiple interpretations of ambiguous regions.
"""
from __future__ import annotations

import cv2
import numpy as np
import torch
from pathlib import Path
from transformers import AutoProcessor, AutoModelForUniversalSegmentation, Sam2Model
from transformers import SamModel, SamProcessor

_SAM_MODEL_ID = "facebook/sam-vit-base"
_processor: SamProcessor | None = None
_model: SamModel | None = None

BBOX_EXPAND_RATIO = 0.20   # expand bbox by this fraction on each side
DILATION_PX = 8            # morphological dilation on final mask (pixels)
# When detected bbox covers more than this fraction of image, use point prompt
LARGE_BBOX_THRESHOLD = 0.35


def _load_model():
    global _processor, _model
    if _processor is None:
        _processor = SamProcessor.from_pretrained(_SAM_MODEL_ID)
        _model = SamModel.from_pretrained(_SAM_MODEL_ID)
        _model.eval()


def _expand_bbox(x: int, y: int, w: int, h: int, img_w: int, img_h: int) -> tuple[int, int, int, int]:
    """Expand a bbox by BBOX_EXPAND_RATIO, clamped to image bounds."""
    pad_x = int(w * BBOX_EXPAND_RATIO)
    pad_y = int(h * BBOX_EXPAND_RATIO)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(img_w, x + w + pad_x)
    y2 = min(img_h, y + h + pad_y)
    return x1, y1, x2, y2


def _pick_best_mask(
    masks_tensor,       # shape [num_masks, H, W] bool
    iou_scores: np.ndarray,
    center_x: int,
    center_y: int,
    img_area: int,
) -> np.ndarray:
    """
    Among SAM's multiple mask proposals, pick the best one for a figure extraction.

    SAM returns 3 masks at different scales (fine, medium, coarse). The highest
    IOU-predicted mask tends to be the largest/coarsest and often captures the
    whole scene. We instead prefer the SMALLEST mask whose coverage of the
    detection center region is >= 50%.

    Args:
        masks_tensor: bool array [num_masks, H, W]
        iou_scores: float array [num_masks]
        center_x, center_y: center of the GroundingDINO detection
        img_area: total pixel count of image

    Returns:
        Best mask as bool array [H, W]
    """
    num_masks = masks_tensor.shape[0]
    h, w = masks_tensor.shape[1], masks_tensor.shape[2]

    # Build a small center region (5% of each dimension)
    cr = max(20, int(min(h, w) * 0.05))
    cy1 = max(0, center_y - cr)
    cy2 = min(h, center_y + cr)
    cx1 = max(0, center_x - cr)
    cx2 = min(w, center_x + cr)
    center_area = (cy2 - cy1) * (cx2 - cx1)

    candidates = []
    for i in range(num_masks):
        m = masks_tensor[i]
        area = int(m.sum())
        if area == 0:
            continue
        center_coverage = float(m[cy1:cy2, cx1:cx2].sum()) / center_area if center_area > 0 else 0.0
        candidates.append((i, area, center_coverage, iou_scores[i]))

    # Require at least 50% center coverage to be considered a valid figure mask
    valid = [c for c in candidates if c[2] >= 0.50]

    if not valid:
        # Fall back to highest IOU if nothing covers the center
        return masks_tensor[int(iou_scores.argmax())]

    # Among valid candidates, prefer the smallest (most focused) mask
    valid.sort(key=lambda c: c[1])
    return masks_tensor[valid[0][0]]


def segment_from_bbox(
    image_path: str,
    bbox_xywh: list[int],
    expand: bool = True,
    dilate: bool = True,
) -> np.ndarray:
    """
    Segment the element described by bbox_xywh in the source image.

    When the detection bbox covers a large fraction of the image (whole-scene
    detection), we supplement with a point prompt at the bbox center so SAM
    produces a more focused mask. We then pick the smallest mask that still
    covers the detection center.

    Args:
        image_path: Path to source image.
        bbox_xywh: [x, y, w, h] bounding box in pixel coords (top-left origin).
        expand: Whether to expand the bbox before passing to SAM.
        dilate: Whether to apply morphological dilation to the output mask.

    Returns:
        Binary mask as uint8 numpy array of shape (H, W), values 0 or 255.
    """
    _load_model()

    from PIL import Image as PILImage

    pil_img = PILImage.open(image_path).convert("RGB")
    img_w, img_h = pil_img.size
    img_area = img_w * img_h
    x, y, w, h = bbox_xywh

    bbox_area = w * h
    bbox_fraction = bbox_area / img_area
    use_point_prompt = bbox_fraction > LARGE_BBOX_THRESHOLD

    if expand:
        x1, y1, x2, y2 = _expand_bbox(x, y, w, h, img_w, img_h)
    else:
        x1, y1, x2, y2 = x, y, x + w, y + h

    center_x = x + w // 2
    center_y = y + h // 2

    if use_point_prompt:
        # Use center point + bbox together for focused segmentation
        input_points = [[[center_x, center_y]]]
        input_labels = [[1]]  # 1 = foreground point
        input_boxes = [[[x1, y1, x2, y2]]]
        inputs = _processor(
            pil_img,
            input_points=input_points,
            input_labels=input_labels,
            input_boxes=input_boxes,
            return_tensors="pt",
        )
    else:
        input_boxes = [[[x1, y1, x2, y2]]]
        inputs = _processor(pil_img, input_boxes=input_boxes, return_tensors="pt")

    with torch.no_grad():
        outputs = _model(**inputs)

    # Post-process: returns masks at original image resolution
    masks = _processor.image_processor.post_process_masks(
        outputs.pred_masks.cpu(),
        inputs["original_sizes"].cpu(),
        inputs["reshaped_input_sizes"].cpu(),
    )

    # masks[0] shape: [1, num_masks, H, W] → [num_masks, H, W]
    masks_arr = masks[0][0].numpy().astype(bool)
    iou_scores = outputs.iou_scores[0, 0].cpu().numpy()

    best_mask = _pick_best_mask(masks_arr, iou_scores, center_x, center_y, img_area)

    # Convert to uint8
    mask_uint8 = (best_mask * 255).astype(np.uint8)

    if dilate:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (DILATION_PX * 2 + 1, DILATION_PX * 2 + 1)
        )
        mask_uint8 = cv2.dilate(mask_uint8, kernel, iterations=1)

    return mask_uint8
