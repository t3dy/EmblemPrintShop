"""
Emblem Print Shop — Element Extractor CLI

Usage:
  python scripts/extract_element.py <image> [--prompt TEXT] [--output DIR] [--threshold FLOAT]

Examples:
  python scripts/extract_element.py sources/claudiens/site/images/emblems/emblem-37.jpg --prompt "lion"
  python scripts/extract_element.py sources/claudiens/site/images/emblems/emblem-25.jpg --prompt "dragon serpent"
  python scripts/extract_element.py sources/hypnerotomachia-polyphili/site/images/woodcuts_1499/hp1499_p330.jpg --prompt "amphora vessel"

If --prompt is omitted, the script reads the emblem's metadata record from the
source project JSON files and builds a prompt automatically.

Outputs (written to --output dir, default assets/extracted/):
  <stem>_transparent.png  — RGBA cutout on transparent background
  <stem>_crop.jpg         — tight rectangular crop
  <stem>_review.jpg       — side-by-side: original | mask overlay (for human review)
  <stem>_meta.json        — extraction metadata record
"""
import argparse
import json
import os
import sys
import warnings
from pathlib import Path

# Suppress HuggingFace model-loading progress bars and deprecation noise
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")

# Add scripts/ to path so pipeline package resolves
sys.path.insert(0, str(Path(__file__).parent))
from pipeline.extractor import extract_element, DEFAULT_OUTPUT_DIR


def main():
    parser = argparse.ArgumentParser(
        description="Extract a visual element from an emblem/woodcut image.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("image", help="Path to source emblem or woodcut image (JPG/PNG)")
    parser.add_argument(
        "--prompt", "-p", default=None,
        help="Text description of the element to find (e.g. 'lion', 'dragon serpent'). "
             "If omitted, auto-reads from emblem metadata."
    )
    parser.add_argument(
        "--output", "-o", default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for extracted files (default: {DEFAULT_OUTPUT_DIR})"
    )
    parser.add_argument(
        "--threshold", "-t", type=float, default=0.25,
        help="Detection confidence threshold 0.0–1.0 (default: 0.25)"
    )
    parser.add_argument(
        "--no-paper-removal", action="store_true",
        help="Skip the paper background removal step (faster, less refined mask)"
    )
    parser.add_argument(
        "--no-review", action="store_true",
        help="Skip saving the review overlay image"
    )
    parser.add_argument(
        "--show-all-detections", action="store_true",
        help="Print all detector hits before extraction (useful for tuning threshold)"
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    if args.show_all_detections:
        from pipeline.detector import detect_elements
        prompt = args.prompt
        if not prompt:
            from pipeline.metadata import get_prompt_for_image
            prompt = get_prompt_for_image(str(image_path)) or "figure"
        hits = detect_elements(str(image_path), prompt, threshold=0.05)
        print(f"\nAll detections for '{prompt}' (threshold=0.05):")
        for i, h in enumerate(hits):
            print(f"  [{i+1}] score={h['score']:.3f}  bbox={h['bbox']}  label={h['label']}")
        print()

    print(f"Extracting element from: {image_path}")
    print(f"Prompt: {args.prompt or '(auto from metadata)'}")
    print(f"Output dir: {args.output}")

    result = extract_element(
        str(image_path),
        prompt=args.prompt,
        output_dir=args.output,
        detection_threshold=args.threshold,
        use_paper_removal=not args.no_paper_removal,
        save_review_overlay=not args.no_review,
    )

    if result is None:
        print("\nNo element detected. Try:")
        print("  - Lowering --threshold (e.g. --threshold 0.1)")
        print("  - Using a more specific --prompt")
        print("  - Using --show-all-detections to see what the model found")
        sys.exit(1)

    print("\nExtraction complete:")
    print(f"  Transparent PNG : {result['transparent_png']}")
    print(f"  Crop JPG        : {result['crop_jpg']}")
    if result.get("review_overlay"):
        print(f"  Review overlay  : {result['review_overlay']}")
    print(f"  Detection score : {result['score']:.3f}")
    print(f"  Bounding box    : {result['bbox']}")
    print(f"  Mask pixels     : {result['mask_pixel_count']:,}")


if __name__ == "__main__":
    main()
