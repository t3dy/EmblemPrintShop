"""
Element detector using GroundingDINO via HuggingFace transformers.

Takes a source image and a text prompt (e.g. "lion", "dragon serpent") and
returns a list of detected bounding boxes sorted by confidence score.

GroundingDINO is an open-vocabulary detector: it can find arbitrary objects
described in natural language, which is ideal for early modern emblem motifs
where subject matter doesn't map to standard COCO/ImageNet classes.
"""
from __future__ import annotations

import cv2
import numpy as np
import torch
from pathlib import Path
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

_MODEL_ID = "IDEA-Research/grounding-dino-tiny"
_processor: AutoProcessor | None = None
_model: AutoModelForZeroShotObjectDetection | None = None


def _load_model():
    global _processor, _model
    if _processor is None:
        _processor = AutoProcessor.from_pretrained(_MODEL_ID)
        _model = AutoModelForZeroShotObjectDetection.from_pretrained(_MODEL_ID)
        _model.eval()


def detect_elements(
    image_path: str,
    prompt: str,
    threshold: float = 0.25,
    box_threshold: float = 0.25,
    text_threshold: float = 0.20,
) -> list[dict]:
    """
    Detect visual elements in an emblem image matching the given text prompt.

    Args:
        image_path: Path to source image (JPG or PNG).
        prompt: Natural-language description of the element to find,
                e.g. "lion", "dragon", "hermaphrodite figure", "alchemical vessel".
        threshold: Minimum confidence score to include a detection.
        box_threshold: GroundingDINO box confidence threshold.
        text_threshold: GroundingDINO text matching threshold.

    Returns:
        List of dicts, sorted descending by score:
            {
                "bbox": [x, y, w, h],   # pixel coords, top-left origin
                "score": float,          # detection confidence 0..1
                "label": str,            # matched text label
            }
    """
    _load_model()

    from PIL import Image as PILImage

    pil_img = PILImage.open(image_path).convert("RGB")
    img_w, img_h = pil_img.size

    # GroundingDINO expects period-terminated prompts
    clean_prompt = prompt.strip().rstrip(".") + "."

    inputs = _processor(images=pil_img, text=clean_prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = _model(**inputs)

    results = _processor.post_process_grounded_object_detection(
        outputs,
        inputs["input_ids"],
        threshold=box_threshold,
        text_threshold=text_threshold,
        target_sizes=[(img_h, img_w)],
    )

    detections = []
    if results and len(results[0]["boxes"]) > 0:
        boxes = results[0]["boxes"].cpu().numpy()    # [x1, y1, x2, y2] in pixels
        scores = results[0]["scores"].cpu().numpy()
        # Prefer text_labels (transformers ≥4.51) over labels which may return
        # integer IDs or raw WordPiece sub-tokens containing ## markers.
        raw_labels = results[0].get("text_labels", results[0].get("labels", []))

        for box, score, label in zip(boxes, scores, raw_labels):
            if score < threshold:
                continue
            x1, y1, x2, y2 = box
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            # Clamp to image bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(img_w, x2)
            y2 = min(img_h, y2)
            # Strip WordPiece continuation markers (## prefix on sub-tokens)
            clean_label = " ".join(
                tok.lstrip("#") for tok in str(label).split()
            ).strip()
            detections.append({
                "bbox": [x1, y1, x2 - x1, y2 - y1],  # [x, y, w, h]
                "bbox_xyxy": [x1, y1, x2, y2],
                "score": float(score),
                "label": clean_label,
            })

    detections.sort(key=lambda d: d["score"], reverse=True)
    return detections
