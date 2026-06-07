"""Tune bridge width for emblem-14 dragon serpent and check image size."""
import os, sys, warnings
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", category=FutureWarning)

import cv2
import numpy as np
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

PROJECT = Path(__file__).parent.parent
img_path = PROJECT / "sources/claudiens/site/images/emblems/emblem-14.jpg"

img = cv2.imread(str(img_path))
h, w = img.shape[:2]
print(f"Emblem-14 size: {w}x{h} = {w*h:,} total pixels")

# Load existing extraction
from pipeline.extractor import extract_element

result = extract_element(
    str(img_path),
    prompt="dragon serpent",
    output_dir=str(PROJECT / "assets/extracted"),
    use_paper_removal=True,
    save_review_overlay=False,
)

if result:
    arr = np.array(Image.open(result["transparent_png"]))
    opaque = (arr[:,:,3] == 255).sum()
    cov = opaque / (h * w)
    print(f"Coverage: {cov:.1%}  mask={result['mask_pixel_count']:,}px  score={result['score']:.3f}")
    print(f"Bbox: {result['bbox']}")
    bbox = result['bbox']
    bbox_area = bbox[2] * bbox[3]
    print(f"Bbox coverage: {bbox_area/(w*h):.1%}")
