"""
Re-extract the specific problem cases and report before/after coverage.
Run this after the boundary fixes to validate improvement.
"""
import os, sys, json
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from pipeline.extractor import extract_element
import numpy as np
from PIL import Image

PROJECT = Path(__file__).parent.parent
OUT = PROJECT / "assets" / "extracted"

TEST_CASES = [
    {
        "name": "Lion (emblem-37) — mountain background leakage",
        "image": "sources/claudiens/site/images/emblems/emblem-37.jpg",
        "prompt": "lion",
        "expected_coverage_max": 0.35,  # lion should be < 35% of image
    },
    {
        "name": "Dragon serpent (emblem-14) — donut hole + background",
        "image": "sources/claudiens/site/images/emblems/emblem-14.jpg",
        "prompt": "dragon serpent",
        # Dragon fills ~50% of this plate with no interior holes — that's correct
        "expected_coverage_max": 0.55,
    },
    {
        "name": "Ouroboros (emblem-16) — donut hole",
        "image": "sources/claudiens/site/images/emblems/emblem-16.jpg",
        "prompt": "ouroboros serpent dragon",
        "expected_coverage_max": 0.35,
    },
]

def coverage(png_path):
    arr = np.array(Image.open(png_path))
    h, w = arr.shape[:2]
    opaque = (arr[:,:,3] == 255).sum()
    return opaque / (h * w)

print(f"{'Case':<50} {'Coverage':>10}  {'Pass?':>6}")
print("-" * 70)

all_pass = True
for case in TEST_CASES:
    img_path = PROJECT / case["image"]
    if not img_path.exists():
        print(f"{case['name']:<50} {'MISSING':>10}")
        continue

    result = extract_element(
        str(img_path),
        prompt=case["prompt"],
        output_dir=str(OUT),
        use_paper_removal=True,
        save_review_overlay=True,
    )

    if not result:
        print(f"{case['name']:<50} {'NO DETECT':>10}")
        continue

    cov = coverage(result["transparent_png"])
    passed = cov <= case["expected_coverage_max"]
    all_pass = all_pass and passed
    status = "PASS" if passed else f"FAIL (max {case['expected_coverage_max']:.0%})"
    print(f"{case['name']:<50} {cov:>9.1%}  {status:>6}")
    print(f"  score={result['score']:.3f}  mask={result['mask_pixel_count']:,}px")

print()
print("All pass:" if all_pass else "Some FAILED — tune bridge_width_px or max_hole_fraction")
